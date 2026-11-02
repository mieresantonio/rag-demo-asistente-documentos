# Improvement log — contract-play

## 2026-11-02 · Fase 2, Ciclo 1

### CONTRACT-A1 (C-1 + C-2 + C-3) — Simulador alineado con los fragmentos
- **Hallazgo:** el simulador exigía valor > 0 también para `retirar()`,
  cuando el fragmento enseñado no es `payable` (en Solidity real, enviarle
  valor revertiría y su llamada normal es con valor 0); la traza juzgaba
  todas las reglas aunque el texto afirmaba que la ejecución se detiene en
  la primera que falla; y al tocar cualquier control tras ejecutar, el
  resultado obsoleto seguía presentado como actual, mezclado con la traza
  en vivo.
- **Cambio (`src/App.jsx`, `src/App.css`, README):**
  - Regla de valor **según la acción** (`buildChecks`): `depositar()` es
    `payable` y exige valor > 0 (depositar sí mueve valor); `retirar()` no
    es `payable` y exige valor **0** — enviarle valor revierte con el mensaje
    «retirar() no acepta valor: no es payable». Valor inicial y de
    Restablecer: 0 (la llamada normal de `retirar()`). La regla del owner
    sigue aplicando solo a `retirar()` (en `depositar()` aparece como no
    aplicable). La caja de reglas **dice expresamente** de dónde sale cada
    regla: el contrato del simulador combina el patrón pausable
    (`cuandoNoPausado`) con la caja con owner, y las reglas de valor/owner
    siguen tal cual al fragmento de la caja.
  - Traza fiel a la parada en el primer fallo (`buildTrace`): `ejecutar()`
    guarda una **foto** de la traza en el momento de ejecutar; tras el primer
    fallo, las reglas posteriores aparecen como **«no revisadas»**, nunca
    como pasadas o falladas. La nota de revert ya no atribuye todo a un
    `require()` (el caso no-`payable` no lo es).
  - Sin resultados obsoletos: todos los controles usan handlers
    `cambiar…` que **descartan el resultado** (`setResult(null)`); el estado
    vacío lo explica («el resultado anterior se descarta: pulsa Ejecutar»).
    El texto de éxito ahora describe la regla que realmente pasó según la
    acción.
  - Ortografía de los textos tocados: «El contrato **está** pausado»,
    «esta **función**» y grafía «ERC-**20**» (fragmentos, reglas, README).
    Estilos nuevos: `.rules-note` y `.trace-item.not-reviewed`.
- **Verificaciones (triple):**
  1. `npm run build` ✅ (Vite 6, sin errores).
  2. Smoke funcional en Node ✅ ejecutando `buildChecks`/`buildTrace`
     **extraídos del propio `App.jsx`**: retirar/owner/valor 0/activo →
     **éxito**; retirar con valor 1 → revert en la regla de valor («no es
     payable»); retirar/otro/valor 0 → revert en owner con traza
     `[pasó, pasó, FALLÓ]`; depositar/otro/valor 1 → éxito con la regla del
     owner «no aplica»; depositar con valor 0 → revert en valor; con el
     contrato pausado la traza es `[FALLÓ, no revisada, no revisada]`.
     Grep del formulario: los 6 controles usan los handlers `cambiar…` y los
     textos nuevos están en el bundle `dist/`.
  3. Checklist ✅: ortografía revisada en todos los textos tocados; README
     reescrito para describir las reglas reales (valor por acción, traza con
     parada, descarte del resultado al tocar controles); import `useMemo`
     retirado al dejar de usarse; sin regresiones en fragmentos ni enlace a
     Remix; ningún servidor quedó corriendo.

## 2026-11-02 · Fase 2, Ciclo 3

### CONTRACT-C3-1 (C-4, MEDIA) — `transfer` con advertencia, sin cambiar su semántica
- **Cambio:** el fragmento «Control de acceso con owner» lleva ahora en su
  propio código un comentario de precaución: `transfer` impone un stipend
  fijo de 2300 gas y hoy está desaconsejado; se indica la alternativa actual
  (`call{value: …}` comprobando el éxito con `require`). La línea de código
  no cambia y la explicación del fragmento repite la cautela. La semántica
  corregida en CONTRACT-A1 no se reabrió.
- **Verificaciones (triple):** 1) `npm run build` ✅. 2) Smoke ✅: regresión
  completa de `buildChecks`/`buildTrace` extraídos del propio `App.jsx` —
  retirar/owner/valor 0 → éxito; retirar con valor 1 → fallo en valor y
  resto «no revisada»; pausado → fallo en pausa y resto no revisado;
  depositar con owner «no aplica». 3) Detalle ✅: cadenas decisivas en el
  bundle — «2300 gas» (1), «desaconsejado» (2), «no es payable» (6),
  «El contrato está pausado» (3); comparación V3 contra el último build
  conocido-bueno (JS 169.171 B): JS nuevo 170.277 B (+1.106 B, comentarios
  y textos nuevos) y misma estructura + favicon nuevo. `VITE_*` = 0.

### CONTRACT-C3-2 (C-5 + C-7 + C-9 parcial) — Matices de fragmentos y copia honesta
- **Cambio:** textos de los fragmentos completados sin tocar su código
  salvo el comentario de C-4: `leer()` solo es gratis como llamada externa
  (desde otro contrato consume gas) y `transferir()` no comprueba la
  dirección cero (enviar a `address(0)` quemaría el saldo) ni emite eventos.
  `SnippetCard.copy` solo muestra «¡Copiado!» si la copia tuvo éxito
  (comprueba también el retorno de `execCommand`); si falla, muestra
  «No se pudo copiar» (C-7). Favicon propio y `.gitignore` (parte de C-9;
  la mezcla de idiomas en identificadores internos queda pendiente por ser
  cosmética y con riesgo de regresión sin beneficio visible).
- **Verificaciones (triple):** 1) Build ✅. 2) Smoke ✅: patrón de copia
  ejecutado en Node (portapapeles ok → confirma; reserva con retorno
  `true` → confirma; ambos fallan → no confirma); cadenas en el bundle —
  «dirección cero» (1), «es gratis solo como llamada externa» (1),
  «No se pudo copiar» (1). 3) Detalle ✅: sin restos de «funcion»/«esta
  pausado» sin tilde en los textos visibles (los dos «funciones» son el
  plural correcto) ni de «ERC20» sin guion; README actualizado; enlace a
  Remix y su mitigación (C-8) intactos; sin servidores al final.

## 2026-11-02 · Fase 2, Ciclo 4 — Coherencia visual (GR-1): firma de cabecera

- **Gesto:** barra de ventana de editor de código sobre el título del hero (`.sig-codebar`, `aria-hidden`): tres puntos rojo/dorado/verde y la línea monoespaciada `contract Ejemplo { … }`, como la pestaña del editor donde vive un contrato. Solo presentación: 1 div JSX decorativo + reglas CSS; lógica, datos y textos funcionales intactos.
- **Verificación 1 (build):** `npm run build` → exit 0.
- **Verificación 2 (sirve + smoke):** `dist/` servido en local → index 200 y asset JS 200; fragmentos y simulador de reglas sin tocar.
- **Verificación 3 (contenido + comparación):** bundle con `sig-codebar` ×6 y cadenas decisivas intactas («Datos de ejemplo», «Fragmentos de Solidity»). JS 170.277 → 170.458 B (+181 B) y CSS 7.882 → 8.381 B, explicados por la barra y su CSS. `VITE_*` = 0.

## 2026-11-02 · Fase 2, Ciclo 9 — Suelo de tests para el simulador y los fragmentos

### [Tests · Red permanente] `scripts/verify-data.mjs` + «npm test» (patrón de block-explorer/nft-studio, Ciclo 7, y hash-lab/gas-calc, Ciclo 8). Nota de conteo verificada en este ciclo: con estas tres apps son **9 de 10** las web3 con suelo de tests — tx-builder no tiene `scripts/` ni `test` en su `package.json` (comprobado hoy; queda fuera del alcance de este ciclo, se deja constancia para el coordinador)

- **Adaptación honesta del patrón:** en esta app NO hay módulo importable: toda la lógica vive en `src/App.jsx`. El simulador (`RULES`, `buildChecks`, `buildTrace`) es JavaScript puro sin JSX, así que el script lo **extrae del propio `App.jsx` y lo ejecuta de verdad** (con las constantes `OWNER`/`OTRO` extraídas del mismo fuente): no hay réplica de `buildChecks`/`buildTrace`. Si las marcas de extracción desaparecen del fuente, el script falla nombrándolo. Los fragmentos de Solidity son texto en `SNIPPETS`: se verifican con anclas exactas, y la aritmética de saldos del fragmento ERC-20 se aplica como réplica declarada sobre la guarda anclada. Matiz declarado en la cabecera del script: el simulador **no maneja saldos** — la semántica de saldo vive solo en los fragmentos (`transferir()` con su `require` de saldo; `retirar()` del fragmento transfiere exactamente `address(this).balance`), y así se comprueba, sin inventarle un saldo al simulador.
- **Cambio:** creado `scripts/verify-data.mjs`, que comprueba en **43 comprobaciones**: extracción ejecutable del simulador real; orden de reglas pausa/valor/owner y sus mensajes; **la corrección del Ciclo 1 ejecutada con el código real** — retirar/owner/valor 0/activo → éxito [pasó, pasó, pasó]; retirar con valor 1 → revert en valor («retirar() no acepta valor: no es payable») y la regla del owner queda «no revisada»; retirar/otro → revert en owner con traza [pasó, pasó, FALLÓ]; retirar con valor no numérico → revert en valor; depositar/otro/valor 1 → éxito con la regla del owner «skipped» (no aplica); depositar con 0 o negativo → revert «El valor debe ser mayor que 0»; pausado aunque también fallen valor y owner → el revert es el de pausa y el resto queda no revisado —; estado inicial y de Restablecer (retirar/owner/0/activo), foto `snapshot` al ejecutar y los 4 handlers `cambiar…` descartando el resultado (`setResult(null)`); los 4 fragmentos con sus guardas (guardar/leer, `require(saldos[msg.sender] >= _cantidad, "Saldo insuficiente")` con resta y suma de la misma cantidad, `depositar() public payable`, `retirar() public soloOwner` transfiriendo exactamente el saldo, la precaución de `transfer`/2300 gas del Ciclo 3, `soloOwner` ×2, `cambiarPausa` soloOwner, `operar` cuandoNoPausado); saldo aplicado: transferir 4 de 10 → 6/7 con total conservado (13 = 13) y transferir 6 teniendo 5 → «Saldo insuficiente» sin mover nada; y la copia honesta del Ciclo 3 (solo confirma si `execCommand` devuelve `true`, si no «No se pudo copiar»). Añadido `"test": "node scripts/verify-data.mjs"` a `package.json`. Sin dependencias nuevas. El script sale con código 0 si todo pasa y ≠0 nombrando cada invariante roto.
- **Verificación 1 (tests + build + comparación):** `npm test` → exit 0 (43/43). `npm run build` → exit 0 y bundles **byte-idénticos** a los conocidos-buenos del Ciclo 4, registrados antes de empezar: JS 170.458 B, sha256 `d86a772d…` (mismo asset `index-UuT7X8iz.js`); CSS 8.381 B, sha256 `296f59fc…`; `index.html` 683 B, sha256 `e500679b…`; favicon 242 B. Delta cero, como corresponde: este frente no toca `src/` ni estilos (sha256 de todo `src/` idénticos antes, después y tras la prueba de fuego).
- **Verificación 2 (prueba de fuego en copia):** app copiada a `/tmp` (solo `src/`, `scripts/` y `package.json`; el test no necesita `node_modules`). Control con la copia sana: `npm test` → exit 0. Rotura deliberada en la copia (la guarda de valor de `retirar()` en `buildChecks`: `!Number.isNaN(v) && v === 0` → `true`, es decir, retirar aceptando valor siendo no payable): `npm test` → **exit 1, 3 fallos** que nombran el problema exacto (retirar con valor 1 ya no revierte «no es payable», la traza pasa entera en vez de detenerse, y el valor no numérico ya no revierte). Copia destruida al terminar; la app real queda intacta (sha256 de `src/` verificados tras la prueba y `npm test` real → exit 0).
- **Verificación 3 (invariantes contra el código real):** todas las cifras del script se derivaron de primera mano en esta sesión **ejecutando el `buildChecks`/`buildTrace` extraídos del propio `App.jsx`** (matriz completa de las 9 llamadas: éxitos, reverts por regla con su mensaje y estados de traza) y leyendo las guardas de los fragmentos en el fuente, no copiadas de memoria ni de los logs de ciclos anteriores.
- **README:** añadida la verificación con `npm test` a «Cómo ejecutarla», con lo que comprueba. Sin cambios en el resto del README.
