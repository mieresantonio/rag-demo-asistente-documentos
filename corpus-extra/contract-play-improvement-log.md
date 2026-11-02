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
