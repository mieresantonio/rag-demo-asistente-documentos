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
