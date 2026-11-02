# Registro de mejoras — Explorador de bloques

## 2026-11-02 · Fase 2, Ciclo 2

### [E-M1 · MEDIA · Contenido] Ninguna transacción «pendiente» dentro de bloques ya minados

- **Hallazgo:** `STATUSES` en `src/data.js` incluía `'pendiente'` y lo asignaba al azar a transacciones ya incluidas en bloques minados (~20 %). Una transacción incluida en un bloque no puede estar pendiente: está confirmada (o fallida si su ejecución revirtió); «pendiente» es el estado de la mempool antes de ser incluida, y esta app no muestra mempool.
- **Cambio:** `STATUSES` pasa a `['confirmada' ×4, 'fallida']` (se mantiene la proporción de fallidas, que sí son posibles dentro de un bloque), con comentario explicativo en el código. Retirada también la píldora «pendiente» de `StatusPill` en `src/App.jsx` y el icono `Hourglass`, ya sin uso (en `src/` la palabra solo queda en comentarios que explican por qué no se usa).
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 164,53 kB); `node --check` de `data.js` correcto.
- **Verificación 2 (smoke con lógica ejecutada):** cadena generada en Node desde los datos reales: 25 bloques, 88 transacciones → **74 confirmadas, 14 fallidas, 0 pendientes (proporción 0 %)** dentro de bloques minados.
- **Verificación 3 (checklist + contenido del bundle + comparación):** ortografía revisada; sin regresiones (búsqueda, detalle de bloque y de transacción intactos). **Contenido del bundle verificado por cadenas decisivas**: «pendiente» = **0** en `dist/assets/*.js`; «confirmada» ×5 y «fallida» ×2 presentes; vistas presentes («Explorador de bloques», «Últimos bloques», «Bloque #», «Volver a la lista»). **Comparación contra el último build conocido-bueno** (diagnóstico Fase 1: 165,1 kB): 164,53 kB, **−0,34 %**, explicado por la retirada de la píldora «pendiente» y su icono. Sin variables de entorno: build autónomo, sin dependencia no documentada.

### [E-M2 · MEDIA · README/datos] Determinismo: el README ahora dice la verdad (decisión anotada)

- **Hallazgo:** el README afirmaba «generador determinista (misma semilla = misma cadena en cada carga)», pero las marcas de tiempo nacían de `Date.now()` (`src/data.js`), así que fechas, horas y «hace X min» cambiaban en cada carga.
- **Decisión:** se elige la vía del **README veraz** y no la de la cadena totalmente determinista. Motivo: fijar las marcas de tiempo a una época fija haría que `relativeTime()` mostrara valores cada vez más antiguos («hace X d» creciendo con el calendario) y rompería la experiencia de explorador «en vivo» (último bloque «hace unos segundos», intervalos de ~30 s), es decir, desestabilizaría lo que la app enseña. El anclaje a la carga es intencional y ahora se declara.
- **Cambio:** sección «Datos» del README reescrita: hashes, direcciones, valores, mineros y número de transacciones sí son idénticos en cada carga (semilla fija); las marcas de tiempo se anclan al momento de cargar la página y cambian en cada carga a propósito, para que los tiempos relativos se vean siempre recientes. La misma corrección se aplicó al comentario de cabecera de `src/data.js`. Sin cambios de lógica.
- **Verificación 1 (build):** `npm run build` → exit 0 (misma build de E-M1).
- **Verificación 2 (smoke con lógica ejecutada):** dos importaciones independientes de los datos en Node producen el **mismo hash del bloque 25** (`0xc1d37dab…f814a4d`) — la parte determinista es real — y la marca de tiempo del último bloque queda ~90 s antes del instante de carga, confirmando el anclaje declarado.
- **Verificación 3 (checklist):** README y comentario de código dicen ahora exactamente lo que el código hace; afirmación sobre estados («confirmada»/«fallida») añadida al README en coherencia con E-M1; ortografía revisada; ninguna otra afirmación del README queda contradicha por estos cambios.

## 2026-11-02 · Fase 2, Ciclo 3

### [E-B3 · BAJA · Lógica] Buscar «0x» ya no devuelve los 25 bloques + [E-B1] posición desde 1 + [E-B5] copia honesta + [E-B6 parcial] `.gitignore`

- **Hallazgos:** `searchBlocks('0x')` coincidía con todos los hashes (todos empiezan por «0x») y devolvía la cadena entera como «coincidencias»; el detalle de transacción mostraba «posición 0» para la primera transacción; `CopyBtn` confirmaba la copia aunque el portapapeles fallara; la app no tenía `.gitignore`.
- **Cambios:** en `src/data.js`, un prefijo sin contenido (`0x` a secas, longitud ≤2 tras normalizar) devuelve `[]`; en `src/App.jsx`, la posición mostrada es `tx.index + 1` y `CopyBtn` solo confirma tras un `writeText` resuelto (sin portapapeles o con error, sin confirmación). Añadido `.gitignore` estándar (el mismo de nft-studio). El favicon de E-B6 queda pendiente (no se tocó `index.html` en este ciclo).
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 164,58 kB); `node --check` implícito vía importación de datos en el smoke.
- **Verificación 2 (smoke con lógica ejecutada):** datos reales en Node: 25 bloques; `searchBlocks('0x')` → **0** (antes 25); búsqueda por altura «7» → 1; prefijo real de hash → 1; primera transacción de un bloque: índice interno 0 → posición mostrada **1**.
- **Verificación 3 (checklist + bundle + comparación):** sin regresiones de E-M1/E-M2 (bundle: «pendiente» ×0, «confirmada» ×5); ortografía revisada. **Comparación contra el último build conocido-bueno** (Ciclo 2: 164,53 kB): 164,58 kB, **+0,03 %**, explicado por la guarda de búsqueda y de copia. Sin variables `VITE_*`: build autónomo.

## 2026-11-02 · Fase 2, Ciclo 4 — Coherencia visual (GR-1): firma de cabecera

- **Gesto:** rejilla de bloques enlazados en el hero, sobre el buscador (`.sig-blockrow`, `aria-hidden`): 5 cuadrados teal unidos por conectores, con desplazamiento vertical alterno — la cadena misma como firma. Solo presentación: 1 div JSX decorativo + reglas CSS; lógica, datos y textos funcionales intactos.
- **Verificación 1 (build):** `npm run build` → exit 0.
- **Verificación 2 (sirve + smoke):** `dist/` servido en local → index 200 y asset JS 200. Smoke de datos en Node: 25 bloques, 88 transacciones, 0 «pendiente» y 74 «confirmada» (corrección E-M1 de Ciclo 2 intacta).
- **Verificación 3 (contenido + comparación):** bundle con `sig-blockrow` ×7; «pendiente» = **0** en el JS y «confirmada» ×5 en cadenas, como en el build conocido-bueno. JS 164.580 → 164.738 B (+158 B) y CSS 7.026 → 7.560 B. `VITE_*` = 0.

## 2026-11-02 · Fase 2, Ciclo 5

### [E-B6 resto · BAJA · Higiene] Favicon propio (el pendiente declarado del Ciclo 3)

- **Hallazgo:** la app no declaraba favicon: el navegador pedía `/favicon.ico` y recibía 404. El `.gitignore` de E-B6 ya se cerró en el Ciclo 3; quedaba solo esto.
- **Cambio:** creado `public/favicon.svg` propio y coherente con el gesto visual de la app (la firma de bloques enlazados del Ciclo 4): tres bloques con relleno `#134e4a` y borde teal `#5eead4` (su `--accent`) unidos por conectores, sobre fondo `#0b0e14`. Referenciado en `index.html` con `<link rel="icon" type="image/svg+xml" href="/favicon.svg" />`. Sin cambios de JS/CSS/lógica.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5).
- **Verificación 2 (smoke):** datos reales en Node, dos cargas independientes: 25 bloques, 88 transacciones, 0 «pendiente»; **determinismo parcial confirmado — mismo hash del bloque 25 en ambas cargas** (`0xc1d37dab…f814a4d`, idéntico al del Ciclo 2). Servido `dist/` en local: index 200, `/favicon.svg` 200 y asset JS 200.
- **Verificación 3 (contenido + comparación):** `dist/index.html` contiene la referencia `rel="icon" … href="/favicon.svg"` y `dist/favicon.svg` existe como archivo (569 B, con `#5eead4`). Bundle JS **idéntico** al build conocido-bueno del Ciclo 4: 164.738 B, mismo hash de archivo (el cambio no toca el JS; solo crecen `index.html` por la línea del enlace y el nuevo asset). Bundle: «pendiente» ×0, «confirmada» ×5 (E-M1 intacto). Sin variables `VITE_*`.
- **Pendientes de esta app (no tocados en este ciclo, fuera del alcance enumerado):** E-B2 (variable `prevHash` muerta e import sin extensión), E-B4 (red de seguridad ante datos fuera de catálogo) y E-B7 (nota de génesis en el bloque 1) siguen como se diagnosticaron.

## 2026-11-02 · Fase 2, Ciclo 6 — Bajas residuales: E-B2, E-B4 y E-B7 (las tres aplicadas)

### [E-B2 · BAJA · Código muerto] Variable `prevHash` abandonada e import sin extensión

- **Hallazgo:** `buildChain()` declaraba `let prevHash = '0x' + '0'.repeat(64)` y nunca la leía (el enlace real se hace con `prev` al final); `src/App.jsx` importaba `from './data'` sin extensión, el único import de datos del grupo sin `.js`.
- **Cambio:** retirada la variable muerta de `src/data.js` (quedan solo la propiedad `prevHash` de cada bloque y su asignación `b.prevHash = prev`) y el import pasa a `'./data.js'`. Sin cambios de lógica: la variable muerta no consumía el generador, así que la cadena generada es idéntica.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 165,58 kB); `node --check` de `data.js` correcto. No existen scripts `test`/`lint` en esta app (solo `build`/`dev`/`preview`).
- **Verificación 2 (smoke con lógica ejecutada):** cadena generada en Node desde los datos reales tras el cambio: 25 bloques, 88 transacciones, hash del bloque 25 **idéntico** al de los Ciclos 2 y 5 (`0xc1d37dab…f814a4d`) y cadena correctamente enlazada (prevHash del bloque n = hash del n−1, verificado bloque a bloque).
- **Verificación 3 (contenido + comparación):** ver V3 global del ciclo, abajo.

### [E-B4 · BAJA · Robustez] Red de seguridad ante datos fuera de catálogo

- **Hallazgo:** `StatusPill` hacía `map[status]` sin valor por defecto (un estado no previsto rompía el render al leer `s.cls` de `undefined`) y, si `view` apuntaba a una altura o hash inexistentes, `block`/`tx` eran `null` y `<main>` quedaba vacío sin mensaje. Inalcanzable desde la UI actual, pero sin estado de error.
- **Cambio (solo reutiliza piezas existentes, sin CSS nuevo ni diseño nuevo):** `StatusPill` gana un valor por defecto `{ ShieldAlert, cls: 'warn' }` — la clase `.pill.warn` ya existía en `styles.css` sin uso desde que se retiró «pendiente» —; y se añade una vista «NO ENCONTRADO» que se muestra cuando la vista no es la lista y falta el bloque o la transacción, construida con las clases ya existentes (`.empty`, `SearchX`, `.btn primary`) y botón de vuelta a la lista.
- **Verificación 1 (build):** misma build del ciclo, exit 0.
- **Verificación 2 (smoke con lógica ejecutada):** gatillos reales comprobados en Node con los datos de la app: `getBlock(999)` → `null`, `getBlock(26)` → `null` y búsqueda de un hash inexistente dentro de un bloque existente → `null`; son exactamente las condiciones que ahora disparan la vista de error en vez del `<main>` vacío. Los flujos normales no la disparan (las 25 alturas y todas las transacciones de la cadena resuelven).
- **Verificación 3 (contenido + comparación):** bundle con las cadenas decisivas de la vista («La altura o el hash indicados no existen» ×1, «esta transacción» ×1, «este bloque» ×1) y `warn` presente en el JS compilado (la rama por defecto). Ver V3 global.

### [E-B7 · BAJA · Contenido] El bloque 1 ya explica su «hash anterior» de ceros (génesis)

- **Hallazgo:** el detalle del bloque 1 mostraba «Hash del bloque anterior: `0x000…000`» con botón de copiar y sin ninguna nota de que ese bloque no tiene anterior ni de qué significan los ceros, en una app cuyo fin es explicar la cadena.
- **Cambio:** dentro del mismo campo, y solo cuando `block.height === 1`, una nota con la clase ya existente `.muted`: «Bloque génesis: es el primero de la cadena y no tiene bloque anterior; los ceros son el marcador que lo indica, no un hash real.» Sin CSS nuevo; el resto de bloques no muestra la nota.
- **Verificación 1 (build):** misma build del ciclo, exit 0.
- **Verificación 2 (smoke con lógica ejecutada):** condición de la nota verificada contra los datos reales: bloque de altura 1 con `prevHash === '0x' + '0'.repeat(64)` → `true`, y es el único bloque con ese `prevHash` (los demás enlazan al hash del bloque anterior).
- **Verificación 3 (contenido + comparación):** bundle con «Bloque génesis» ×1, «no tiene bloque» ×1 y «los ceros son el marcador» ×1. Ver V3 global.

### Verificación 3 global del ciclo (contenido del bundle + comparación)

- **Línea base conocida-buena (Ciclos 4–5):** JS 164.738 B, sha256 `d52ce435…`, byte-idéntico entre Ciclo 4 y Ciclo 5; CSS 7.560 B, sha256 `c822110b…`.
- **Tras el Ciclo 6:** JS **165.581 B (+843 B, +0,51 %)**, sha256 `375ce363…`. Delta explicado **solo** por los tres cambios: vista «no encontrado» y valor por defecto de `StatusPill` (E-B4) + nota de génesis (E-B7), menos la variable muerta retirada (E-B2). **CSS byte-idéntico** (mismo sha256 y mismo nombre de asset `index-BvaUszU8.css`): no se tocó ningún estilo. El `dist/index.html` solo cambia por el nuevo nombre hasheado del asset JS; el `index.html` fuente no se tocó (favicon del Ciclo 5 intacto).
- **Invariantes previos en el bundle:** «pendiente» ×0 y «confirmada» ×5 (E-M1, Ciclo 2, intacto); `sig-blockrow` presente (firma del Ciclo 4).
- **Invariantes previos en ejecución (V2):** 25 bloques, 88 transacciones (74 confirmadas, 14 fallidas, **0 pendientes**); búsqueda «0x» → **0** resultados (E-B3, Ciclo 3, intacto); búsqueda por altura «7» → 1; prefijo real de hash → 1; posición de la primera transacción mostrada como 1 (E-B1 intacto). Servido `dist/` en local: index 200, asset JS 200 y `/favicon.svg` 200 (E-B6 intacto); servidor apagado al terminar.
- **Sin variables de entorno de build:** `VITE_*` = 0 en `src/`, `vite.config.js`, `index.html`, `package.json` y en el bundle; build autónomo, sin dependencia no documentada.
- **README:** no se tocó — ninguna afirmación suya queda falsa tras estos cambios (la búsqueda y su estado vacío, los datos y los estados «confirmada»/«fallida» siguen describiendo lo que el código hace).
- **Pendientes de esta app tras este ciclo:** ninguna de las bajas E-B* queda pendiente; quedan fuera de este alcance las medias ya cerradas y la nota de diseño E-B8, que no era objeto de este ciclo.
