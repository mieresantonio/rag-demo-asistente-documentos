# Registro de mejoras — DAO Vote

## 2026-11-02 · Fase 2, Ciclo 1

### [D-A1 · ALTA · Lógica] Filtros «Activas»/«Cerradas» corregidos: devolvían siempre 0

- **Hallazgo:** las claves de filtro en `src/App.jsx` eran plurales (`'activas'`, `'cerradas'`) y `filtered` las comparaba contra `p.status`, cuyos valores en `src/data.js` son singulares (`'activa'`, `'cerrada'`). Al pulsar «Activas» o «Cerradas» siempre se mostraba el estado vacío, aunque el README anuncia los filtros como función entregada.
- **Cambio:** claves de filtro igualadas a los valores reales de `status`: `['activa', 'Activas']` y `['cerrada', 'Cerradas']`. Las etiquetas visibles («Todas», «Activas», «Cerradas») no cambian; tampoco se tocaron los datos ni el resto de la lógica.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 166,61 kB); `node --check` de `data.js` correcto.
- **Verificación 2 (smoke funcional):** lógica ejecutada en Node contra los datos reales de la app: filtro `todas` → 6 propuestas; `activa` → 3 (p1, p2, p3); `cerrada` → 3 (p4, p5, p6). Con las claves antiguas, la misma expresión devolvía 0 y 0, lo que reproduce el fallo original. El bundle de `dist/` contiene las claves corregidas (`"activa","Activas"` / `"cerrada","Cerradas"`).
- **Verificación 3 (checklist):** sin regresiones (resumen, votación y creación de propuestas intactos; la creación sigue fijando el filtro en `todas`); ortografía sin cambios, ya correcta; el README vuelve a ser veraz en lo que anuncia de los filtros sin necesidad de editarlo.

## 2026-11-02 · Fase 2, Ciclo 3

### [D-M1 · MEDIA · Diseño] Paleta diferenciada de tx-builder (acotada) + [D-B4] contraste ≥4,5:1

- **Hallazgo:** paleta clónica con tx-builder (`--violet #8b5cf6` idéntico, dorados y fondos casi iguales) y, a la vez, texto `#f2f0fa` sobre ese violeta a 3,75:1 en chip de filtro activo y botón primario (por debajo de AA).
- **Cambio:** un solo gesto resuelve ambas cosas: el acento pasa a un rosa oscuro propio `#be185d` (token `--violet` conservado de nombre para no tocar el resto de reglas), con su fondo suave `#3d1226`, el degradado del hero en la misma familia (`#3a0f24`) y el texto claro de categoría/eyebrow a `#fbcfe8`. tx-builder conserva su violeta: las dos apps ya no comparten acento.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 166,89 kB).
- **Verificación 2 (smoke):** contraste calculado con la fórmula WCAG sobre los hex finales: texto `#f2f0fa` sobre `#be185d` = **5,35:1** (≥4,5 ✅; antes 3,75:1); categoría `#fbcfe8` sobre panel = 13,19:1; eyebrow sobre fondo suave = 11,57:1.
- **Verificación 3 (checklist + bundle + comparación):** bundle CSS con `#be185d` ×1 y `#8b5cf6` ×0; sin cambios de layout ni de textos. **Comparación contra el último build conocido-bueno** (Ciclo 1: 166,61 kB): 166,89 kB, **+0,17 %**, explicado por los textos de empate/Subvenciones de este ciclo. Sin variables `VITE_*`: build autónomo.

### [D-B1 · BAJA · Contenido] El texto de «rechazada» ya no miente en caso de empate

- **Hallazgo:** con quórum y `favor === contra`, `outcome()` devuelve 'rechazada' y la tarjeta afirmaba «rechazada (más votos en contra)», falso en el empate.
- **Cambio:** el veredicto distingue según los datos reales de la propuesta: si hay empate muestra «Resultado: no aprobada por empate (X VP a favor y X VP en contra; sin mayoría a favor no se aprueba)»; el texto «más votos en contra» solo aparece cuando en efecto `contra > favor`. Comentario en `data.js` que deja constancia de la regla. `outcome()` y los conteos del resumen no cambian (el empate sigue sin aprobarse).
- **Verificación 2 (smoke con lógica ejecutada):** cerradas reales contrastadas — p4 aprobada (2100/150), p5 rechazada con más en contra (400/980, su texto sigue siendo el de «más votos en contra»), p6 sin quórum (700/690, 1.430 < 1.500) — y caso sintético de empate con quórum (800/800, total 1.700 ≥ 1.500): `outcome` = no aprobada y la rama visible seleccionada es la de empate, no la de «más votos en contra». Filtros sin regresión: **todas 6 / activas 3 / cerradas 3** (D-A1 de Ciclo 1 intacto).
- **Verificación 3:** bundle con «no aprobada por empate» ×1, «sin mayoría a favor no se aprueba» ×1 y «rechazada (más votos en contra)» ×1 (solo para el caso real); ortografía revisada.

### [D-B3 · BAJA · Localización] «Grants» → «Subvenciones»

- **Cambio:** categoría renombrada en `CATEGORIES`, en la propuesta p6, en la clave de icono de `App.jsx`, en el título de p1 («fondo comunitario para subvenciones») y en el README. Las cinco categorías quedan en español.
- **Verificaciones:** build ✅; bundle JS con «Subvenciones» ×3 y «Grants» ×0; grep en `src/` y README sin restos en inglés para esta categoría.

## 2026-11-02 · Fase 2, Ciclo 4 — Coherencia visual (GR-1): sin cambio, identidad suficiente

- **Decisión:** no se toca. La diferenciación pedida por este frente ya existe y fue cerrada en el Ciclo 3: acento rosa oscuro `#be185d` (bundle CSS ×1, `#8b5cf6` ×0, verificado hoy sin rebuild), hero asimétrico con tarjeta de poder de voto a la derecha — composición distinta de la columna centrada del resto — y barras de resultados/quórum como recurso visual propio por tarjeta. Añadir otro gesto forzaría la cabecera y arriesgaría lo cerrado; se anota y no se fuerza, según el criterio del ciclo.
- **Verificación:** `dist/` vigente servido en local → index 200 y asset JS 200. Smoke de datos en Node: 6 propuestas, 3 activas y 3 cerradas (filtros de D-A1 operativos sobre los datos). Sin build nuevo: ningún archivo de la app se modificó en este frente.

## 2026-11-02 · Fase 2, Ciclo 5

### [D-B2 · BAJA · Etiquetado] Cantidades en USDC marcadas como de ejemplo donde se vota

- **Hallazgo:** las propuestas p1 («Destinar 120.000 USDC…») y p6 («Asignar 50.000 USDC…») citaban un token real y cifras de tesorería sin marca local: el texto de la propuesta, citado fuera de contexto, se leía como fondos reales (la cabecera y el pie sí declaran la simulación, por eso era baja).
- **Cambio:** marca local en los dos únicos sitios con USDC de `src/` (grep previo: solo p1 y p6; el README no menciona USDC): p1 → «120.000 USDC de ejemplo (simulados, sin valor real)»; p6 → «50.000 USDC de ejemplo (simulados)». Ningún otro texto se tocó.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 167,05 kB).
- **Verificación 2 (smoke):** filtros intactos sobre los datos reales — todas 6 / activas 3 / cerradas 3 — y empate veraz intacto: caso sintético con quórum y 800/800 → `outcome` no aprobada y texto «no aprobada por empate» presente en el bundle ×1.
- **Verificación 3 (contenido + comparación):** bundle con «USDC de ejemplo» ×2 (ambas ocurrencias marcadas) y patrón sin marca «120.000 USDC de la» ×0; «Subvenciones» ×3 (Ciclo 3 intacto). **Comparación contra el último build conocido-bueno** (Ciclo 3: 166.885 B): 167.054 B, **+0,10 %**, explicado por las marcas USDC y la defensa de `vote()` de D-B6. Sin variables `VITE_*`.

### [D-B6 parcial · BAJA · Código] Memo real y voto con defensa

- **Cambios seguros aplicados:** (a) `closed` se calcula ahora dentro del `useMemo` de `summary` (fuera se recreaba en cada render y entraba como dependencia: la memoización nunca reutilizaba nada); la dependencia queda solo en `proposals` y el resumen calculado es idéntico. (b) `vote()` ya no confía solo en la UI: busca la propuesta y devuelve sin votar si no existe, si no está `'activa'` o si la opción no es una de `favor`/`contra`/`abstencion`.
- **Subparte no aplicada, con motivo:** el retorno silencioso de `createProposal` con título/descripción vacíos queda como está: es inalcanzable desde la UI (botón `disabled` + campos `required`), y mostrar un mensaje nuevo exigiría estado y texto nuevos — cambio de UX, no corrección segura.
- **Verificación:** misma build y mismo smoke de D-B2 (resumen y filtros sin cambios: 6/3/3); bundle con el resumen y los textos de siempre.

### [D-B7 · BAJA · Lógica] PENDIENTE — exige decisión, no corrección segura

- **Motivo:** derivar el estado de `deadline` (o cerrar propuestas con un temporizador) es una decisión de modelo de gobernanza — cuándo y cómo se cierra una propuesta activa en mitad de una sesión, qué pasa con la creada por el usuario y cómo se anuncia el cierre —, no un arreglo mecánico verificable. Aplicarlo sin esa decisión arriesga los smokes cerrados (filtros 6/3/3 y conteos del resumen). Queda anotado para decisión de Antonio/coordinador.
- **También queda sin tocar:** D-B5 (sin `.gitignore`), fuera del alcance enumerado de este ciclo.
- **Nota para el frente de READMEs (paralelo):** el README de esta app no se editó en este ciclo y no lo necesita por D-B2 (no cita cantidades en USDC).

## 2026-11-02 · Fase 2, Ciclo 9 — Suelo de tests para filtros, veredictos y defensa de voto

### [Tests · Red permanente] `scripts/verify-data.mjs` + «npm test» (patrón de block-explorer/nft-studio, Ciclo 7, y hash-lab/gas-calc, Ciclo 8). Nota de conteo verificada en este ciclo: con estas tres apps son **9 de 10** las web3 con suelo de tests — tx-builder no tiene `scripts/` ni `test` en su `package.json` (comprobado hoy; queda fuera del alcance de este ciclo, se deja constancia para el coordinador)

- **Adaptación honesta del patrón:** la app tiene las dos naturalezas. Los datos y la regla de decisión SÍ viven en un módulo importable (`src/data.js`) y el script lo importa de verdad (`INITIAL_PROPOSALS`, `CATEGORIES`, `USER_VP`, `totalVotes`, `quorumReached`, `outcome`). Lo que vive en `src/App.jsx` (claves de filtro, rama visible del empate, defensa de `vote()`, resumen y creación) se verifica con el patrón de ancla: el fuente debe contener las claves, ramas y guardas exactas, las claves de filtro se **extraen** del fuente y la expresión de filtrado anclada se aplica a los datos reales importados. Todo declarado en la cabecera del script.
- **Cambio:** creado `scripts/verify-data.mjs`, que comprueba en **54 comprobaciones**: integridad de las 6 propuestas importadas (ids p1..p6, campos, categorías válidas, quórum); categorías = las 5 en español con **«Subvenciones»** y sin restos de «Grants» en datos ni en App.jsx (Ciclo 3); **filtros de D-A1 como regresión permanente** (claves extraídas del fuente = todas/activa/cerrada en singular; expresión anclada sobre los datos reales → todas 6, activa p1/p2/p3, cerrada p4/p5/p6); regla de aprobación ejecutada con el módulo real (totales 1670/1590/660/2330/1490/1430 VP y quórums; cerradas → p4 aprobada, p5 rechazada, p6 sin quórum con 1.430 < 1.500; sintéticos de abstención: cuenta para el quórum —600/500/400 = 1.500— pero no inclina —500/600/400 manda el contra—); resumen derivado 6/3/1/2 con la fórmula del `useMemo` anclado; **empate veraz de D-B1** (sintético 800/800/100 con quórum → `outcome()` lo agrupa en 'rechazada' solo a efectos de conteo, y las anclas fijan que el texto visible es la rama «no aprobada por empate… sin mayoría a favor no se aprueba», con «más votos en contra» solo como la otra rama; empate sin quórum → 'sin-quorum'); **USDC de D-B2** (los 2 únicos sitios que lo citan —p1 en la descripción y p6 en el título— llevan «USDC de ejemplo (simulados…)»); y **defensa de `vote()` de D-B6** (anclas: no vota dos veces, no vota si no existe o no está 'activa', no vota con opción inválida, suma exactamente `USER_VP` = 100; creación activa con 0 votos, quórum 1.000, plazo 7 días y filtro a «todas»). Añadido `"test": "node scripts/verify-data.mjs"` a `package.json`. Sin dependencias nuevas. El script sale con código 0 si todo pasa y ≠0 nombrando cada invariante roto.
- **Verificación 1 (tests + build + comparación):** `npm test` → exit 0 (54/54). `npm run build` → exit 0 y bundles **byte-idénticos** a los conocidos-buenos del Ciclo 5, registrados antes de empezar: JS 167.054 B, sha256 `e7763df7…` (mismo asset `index-C7NUuoWH.js`); CSS 7.448 B, sha256 `1eb816ca…`; `index.html` 443 B, sha256 `ebf41b20…`. Delta cero, como corresponde: este frente no toca `src/` ni estilos (sha256 de todo `src/` idénticos antes, después y tras la prueba de fuego).
- **Verificación 2 (prueba de fuego en copia):** app copiada a `/tmp` (solo `src/`, `scripts/` y `package.json`). Control con la copia sana: `npm test` → exit 0. Rotura deliberada en la copia (reintroducido el bug original de D-A1: clave de filtro `'activa'` → `'activas'` en la barra de App.jsx): `npm test` → **exit 1, 1 fallo** que nombra el problema exacto (claves extraídas «actual: todas, activas, cerrada» contra las esperadas en singular). Copia destruida al terminar; la app real queda intacta (sha256 de `src/` verificados tras la prueba y `npm test` real → exit 0).
- **Verificación 3 (invariantes contra el código real):** todas las cifras del script se derivaron de primera mano en esta sesión ejecutando el módulo real `src/data.js` en Node (totales y quórum por propuesta, outcomes de las cerradas, resumen, empate sintético con y sin quórum) y leyendo las ramas/guardas en `App.jsx`, no copiadas de memoria ni de los logs de ciclos anteriores.
- **D-B7 sigue ABIERTA:** derivar el estado de la propuesta desde su fecha límite es una decisión de gobernanza pendiente de Antonio. Este ciclo **no la implementa ni la fija como resuelta**: el script comprueba solo el comportamiento actual documentado (el estado es el campo `status` almacenado y los filtros cuentan sobre ese campo) y deja la nota impresa en su salida y en su cabecera. Nada en este frente prejuzga esa decisión.
- **README:** añadida la verificación con `npm test` a «Cómo ejecutarlo», con lo que comprueba. Sin cambios en el resto del README.
