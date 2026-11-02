# Registro de mejoras — NFT Studio

## 2026-11-02 · Fase 2, Ciclo 3

### [N-M1 · MEDIA · Lógica/UX] El resultado del minteo ya no se pierde al cerrar el modal con la X

- **Hallazgo:** el botón X del `MintModal` estaba activo también tras el «¡Minteado (simulado)!» y cerraba con `onClose` a secas: la pieza **no** quedaba minteada, el hash ficticio se perdía y la app ya había dicho que sí se minteó. Solo el botón «Ver en la galería» (`onDone`) confirmaba el resultado.
- **Cambio:** en `src/App.jsx`, tras completarse el minteo la X pasa a cerrar **confirmando** (`done ? () => onDone(txHash) : onClose`, con `aria-label` «Cerrar y guardar en la galería»), de modo que cerrar con la X y pulsar «Ver en la galería» tienen el mismo efecto: la pieza queda en la colección con la marca «Minteado (simulado)» y su hash ficticio en la tarjeta. Antes de completarse, la X sigue cancelando como antes. El resultado del modal lo dice explícitamente con una nota nueva: la pieza «queda guardada en tu colección de la galería… aunque cierres esta ventana con la X».
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 8, JS 244,49 kB).
- **Verificación 2 (smoke con lógica ejecutada):** en Node, patrón de código comprobado (`done ? onDone(txHash) : onClose`) y simulación de la expresión real de `completarMint`: tras «cerrar con la X» post-minteo, la pieza #1001 queda `minteado: true` con su `txHash` guardado en la colección y la pieza vecina intacta.
- **Verificación 3 (checklist + contenido del bundle + comparación):** ortografía revisada; sin regresiones (flujo de pasos, copia de hash y creación de NFT intactos). **Bundle verificado por cadenas decisivas**: «queda guardada en tu colección» ×1, «Cerrar y guardar en la galería» ×1, «Ver en la galería» ×1, «Minteado (simulado)» ×3. **Comparación contra el último build conocido** (diagnóstico Fase 1: 243,91 kB en disco): 244,50 kB, **+0,24 %**, explicado por la nota y la lógica de cierre nuevas. Sin variables `VITE_*` en `src/` ni en `vite.config.js`: build autónomo.

### [N-M2 · MEDIA · Diseño] Una decisión visual acotada: serif editorial de galería para los títulos

- **Hallazgo:** diseño genérico de plantilla (tipografía de sistema sin jerarquía propia como uno de los síntomas).
- **Cambio (una sola decisión, sin rediseño):** token `--serif` (Georgia) aplicado **solo** a los títulos con función de «cartela de sala»: nombre del estudio en la cabecera, nombre de cada obra en su tarjeta, título de la pestaña Crear, nombre en la vista previa y título del modal de minteo. Layout, paleta, rejilla y texto funcional (sans) no cambian.
- **Verificaciones:** build ✅ (misma build de N-M1); el bundle CSS contiene la familia Georgia (×1 token, reutilizado por las 5 reglas); checklist: ninguna otra decisión visual se tocó en este ciclo.

### Bajas seguras del diagnóstico

- **[N-B1 · ortografía]** «minterarlo» → «mintearlo» en los 2 sitios (`src/App.jsx`: aviso tras crear y párrafo de la pestaña Crear). Bundle: «mintearlo» ×2, «minterarlo» ×0.
- **[N-B3 · higiene]** Eliminado `public/icons.svg` (huérfano, símbolos de plantilla, sin ninguna referencia) y sustituido el favicon-rayo de la plantilla de Vite por un favicon propio (fondo de panel con los tres círculos de color de las obras); el `#863bff` de Vite ya no aparece en ningún archivo del proyecto.
- **[N-B5 parcial · accesibilidad]** `aria-pressed` añadido a todos los controles de selección: pestañas Galería/Crear, segmento Todos/Minteados/Sin mintear y chips de Fondo/Forma/Rareza del formulario. Bundle: `aria-pressed` ×6 puntos de render. (Quedan fuera, no tocados: trampa de foco/Escape del modal.)
- **[N-B7 parcial · dato muerto]** El campo `creador`, que existía en las 12 semillas y en el alta pero nunca se renderizaba, ahora se usa: cada tarjeta muestra «Creador: Autor de ejemplo» (semillas) o «Tú (ejemplo)» (obras creadas por el usuario), que es la procedencia que un NFT declara. Bundle: «Creador» ×1, «Tú (ejemplo)» ×1.

## 2026-11-02 · Fase 2, Ciclo 4

### [N-B5 resto · accesibilidad] El modal de minteo atrapa el foco, cierra con Escape y devuelve el foco al abrirse

- **Cambio (`src/App.jsx`, `MintModal`):** (1) al montarse, el foco entra en el modal (primer elemento enfocable, el botón de cierre) y una trampa de foco hace que Tab/Shift+Tab ciclen solo entre los controles del modal; (2) tecla Escape con la **misma semántica del Ciclo 3 que la X**: tras «¡Minteado!», cerrar con Escape CONFIRMA (`onDone(txHash)`, la pieza queda en la galería); antes de completar, cancela (`onClose`); (3) al desmontarse, el foco vuelve al elemento que abrió el modal (capturado en el primer render, antes de mover el foco: la tarjeta/botón «Mintear» de origen).
- **Verificación 1 (build):** `npm run build` → exit 0 (JS 245,70 kB).
- **Verificación 2 (smoke con lógica ejecutada):** simulación en Node de las expresiones reales: Escape pre-minteo cancela sin mintear; **Escape tras completar deja la pieza #1001 `minteado: true` con su `txHash` en la colección** y la vecina intacta; wrap de la trampa (Tab en el último → primero; Shift+Tab en el primero → último; en el medio no interviene): 10/10 PASS junto con las bajas de abajo.
- **Verificación 3 (contenido del bundle + comparación + checklist):** bundle nuevo JS 245 696 B contra el último bueno (Ciclo 3: 244 495 B): **+1 201 B, +0,49 %**, explicado por el handler de teclado, la trampa y el estado de error de copia. Cadenas decisivas en el JS: «Escape» ×3 (handler), «No se pudo copiar» ×1, «Cerrar y guardar en la galería» ×1, «queda guardada en tu colección» ×1, «Ver en la galería» ×1, «Minteado (simulado)» ×3, «mintearlo» ×2 / «minterarlo» ×0, `aria-pressed` ×6 (sin regresiones de ciclos anteriores). Ortografía de textos nuevos revisada («No se pudo copiar»).

### Bajas seguras del diagnóstico incluidas

- **[N-B4 · lógica] «Copiado» solo si el portapapeles copia de verdad:** `copy()` ya solo pone «Copiado» cuando `navigator.clipboard.writeText` resuelve; si rechaza, el botón muestra «No se pudo copiar» durante 2 s. Verificado en la simulación (éxito → Copiado; fallo → no afirma copia) y por la cadena en el bundle.
- **[N-B7 resto · código borde] Guarda en `nextToken`:** con la galería vacía (o sin ids válidos) el siguiente token es `#1001` en vez de «#-Infinity» (`Math.max()` de lista vacía). Verificado en la simulación: vacío → `#1001`; semillas → `#1013`.
- **[N-B2 parcial · código] Parámetro muerto `rnd` en `shapePath`** (`src/artwork.jsx`): eliminada la firma y las dos llamadas que lo pasaban (el arte no cambia: la función nunca lo usaba). `oxlint`: de 5 avisos a **4** (quedan el `Date.now()` impuro del hash —deliberado, da unicidad al hash ficticio— y los 3 `only-export-components` de `artwork.jsx`, estructurales de la plantilla, sin tocar).
- **[T-5/N · movimiento] `prefers-reduced-motion`:** con movimiento reducido, la animación `spin` del paso de firma se detiene (regla nueva en `index.css`; cadena `prefers-reduced-motion` ×1 en el CSS compilado, token Georgia ×1 intacto).

### Pendiente (con motivo, sin forzar)

- **N-B6 (stats a 360 px):** cambiar la rejilla de estadísticas en móvil es una decisión visual sin verificación de render disponible en esta pasada; queda sin tocar.
- **N-B8 (README/stack divergente):** la divergencia de stack es un hecho de la serie, no un arreglo de código seguro en esta app; el README no se tocó en este ciclo.

## 2026-11-02 · Fase 2, Ciclo 4 — Coherencia visual (GR-1): firma de cabecera

- **Gesto:** tres mini-marcos de galería en la cabecera (`.sig-frames`, `aria-hidden`, visibles ≥700 px): marcos dorados con degradado violeta→cian, el central más alto y los laterales inclinados ±7°, como cuadros colgados. Solo presentación: 1 span JSX decorativo + reglas CSS; lógica, datos y textos funcionales intactos por este frente.
- **Verificación 1 (build):** `npm run build` → exit 0.
- **Verificación 2 (sirve + smoke):** `dist/` servido en local → index 200 y asset JS 200; galería, crear y minteo sin tocar en este frente.
- **Verificación 3 (contenido + comparación):** bundle con `sig-frames` ×7 y cadenas decisivas intactas («Datos de ejemplo», «NFT Studio»). JS 244.495 → 245.696 B (+1.201 B): incluye cambios concurrentes de otro frente detectados por diff en el mismo ciclo (foco/Escape del modal, N-B5), además de los marcos. CSS 9.827 → 10.337 B. `VITE_*` = 0.

## 2026-11-02 · Fase 2, Ciclo 5

### [N-B6 · BAJA · Diseño/responsive] Estadísticas a 360 px: la fila envuelve en pantallas muy estrechas

- **Hallazgo (pendiente desde el Ciclo 4):** a 360 px la fila de estadísticas (`.stats`) se quedaba en la rejilla fija de 3 columnas con celdas apretadas; quedó fuera del Ciclo 4 por ser «una decisión visual sin verificación de render».
- **Cambio (conservador, solo `src/index.css`):** media query nueva `@media (max-width: 420px)` al final de la hoja: `.stats` pasa a `display: flex; flex-wrap: wrap` y cada celda a `flex: 1 1 120px` — a 360 px (contenido útil ≈328 px tras el padding de `.main`) las tres celdas ya no caben en una fila (3 × 120 px + huecos > 328 px) y la fila **envuelve** a la siguiente línea en vez de apretarse. Sin tocar la rejilla de escritorio ni los breakpoints existentes (900/560 px): por encima de 420 px el diseño es exactamente el de antes. Ningún cambio en JSX, lógica ni textos.
- **Verificación declarada (estándar posible en esta VM):** revisión de código + bundle compilado, **sin** verificación de render/píxeles (no hay navegador de render disponible en esta VM para esta pasada); es el mismo estándar declarado en ciclos anteriores para cambios sin lógica.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 8.3.5).
- **Verificación 2 (smoke con lógica ejecutada):** el minteo sigue guardando en la galería tras Escape y tras la X — simulación en Node sobre los patrones reales de `src/App.jsx` (`done ? onDone(txHash) : onClose` en la X; `if (done) onDone(txHash) else onClose()` en Escape; `completarMint` marca `minteado: true` y guarda el `txHash` por `tokenId`): **11/11 PASS** (pieza #1001 queda minteada con su hash tras X y tras Escape, vecina intacta, modal cerrado; Escape pre-minteo sigue cancelando sin mintear).
- **Verificación 3 (contenido del bundle + comparación contra conocido-bueno):** la media query nueva está en el CSS compilado como `@media (width<=420px){.stats{flex-wrap:wrap;display:flex}.stats>div{flex:120px}}` (forma minificada de las reglas nuevas; `flex:120px` es la forma corta de `flex: 1 1 120px`). JS **245.696 B, idéntico byte a byte en tamaño al conocido-bueno del Ciclo 4** (245.696 B): el cambio es solo CSS, como corresponde. CSS 10.337 → 10.417 B (+80 B compilados), explicado por la media query nueva. Sin variables `VITE_*`.

### Pendiente (con motivo, sin forzar)

- **N-B8 (README/stack divergente):** sigue sin tocar, mismo motivo del Ciclo 4: es un hecho de la serie, no un arreglo de código seguro en esta app.

## 2026-11-02 · Fase 2, Ciclo 6 — Alineación de versiones del conjunto web3: bajada a React 18 / Vite 6

### [N-B8 · BAJA · Stack/README] nft-studio alineada a la línea de sus hermanas (misma operación que hash-lab en el Ciclo 5)

- **Resultado: ALINEADA** (la triple verificación reforzada pasa completa; no hizo falta revertir).
- **Referencia (hermana gas-calc, leída de su `package.json` y su lockfile):** rangos `react ^18.3.1`, `react-dom ^18.3.1`, `vite ^6.0.7`, `@vitejs/plugin-react ^4.3.4`, `lucide-react ^0.469.0`; resueltos en su lockfile: react 18.3.1, react-dom 18.3.1, vite 6.4.5, `@vitejs/plugin-react` 4.7.0, lucide-react 0.469.0.
- **Estado previo registrado (antes de tocar nada):** `package.json` y `package-lock.json` respaldados fuera del proyecto; bundle conocido-bueno del Ciclo 5 en disco: JS 245.696 B / CSS 10.417 B.
- **Antes → después en nft-studio** (rangos en `package.json` → resuelto en el lockfile nuevo):
  - `react`: `^19.3.1` (19.3.1) → `^18.3.1` (**18.3.1**, igual que gas-calc)
  - `react-dom`: `^19.3.1` (19.3.1) → `^18.3.1` (**18.3.1**)
  - `vite`: `^8.3.4` (8.3.5) → `^6.0.7` (**6.4.5**, igual que gas-calc)
  - `@vitejs/plugin-react`: `^6.1.2` (6.1.2) → `^4.3.4` (**4.7.0**, igual que gas-calc)
  - `lucide-react`: `^1.61.0` (1.61.0) → `^0.469.0` (**0.469.0**) — los 14 iconos usados existen en la 0.469.0, verificado antes de bajar contra la hermana ya alineada (`Loader2` incluido: en 0.469.0 es alias ESM de `LoaderCircle`, presente en el entry point aunque no como `declare const` en el `.d.ts`).
  - Sin tocar: `oxlint ^1.88.0` (resuelto 1.89.0, necesario para la verificación de lint) y `@types/react` / `@types/react-dom ^19.3.0` (proyecto JS sin TypeScript, sin `peerDependencies` que choquen; mismo criterio que en hash-lab). `npm install` regeneró el lockfile sin errores ni conflictos de peer deps (exit 0; 53 paquetes añadidos, 8 retirados, 7 cambiados).
  - Viabilidad previa: el código no usa ninguna API exclusiva de React 19 (solo `useState`, `useEffect`, `useMemo`, `useRef`, `StrictMode`, `createRoot`); `vite.config.js` es el mismo patrón que el de gas-calc.
- **Verificación 1 (build + lint):** `npm run build` → exit 0 con Vite 6.4.5. `npm run lint` (oxlint) → exit 0, **0 errores y los mismos 4 avisos conocidos** del Ciclo 4 (el `Date.now()` impuro deliberado del hash ficticio y los 3 `only-export-components` estructurales de `artwork.jsx`). No existe script `test` en la app. Servida un momento desde `dist/`: index 200, asset JS 200 y asset CSS 200; sin servidores al final.
- **Verificación 2 (humo funcional con lógica ejecutada):** simulación en Node sobre los patrones reales de `src/App.jsx` (presencia de las expresiones comprobada en el fuente) usando el `fakeTxHash` y las semillas reales de `src/data.js`: **16/16 PASS** — hash ficticio con formato `0x`+64 hex y determinista; minteo + cierre con la X post-minteo deja la pieza #1001 `minteado: true` con su `txHash` en la galería y la vecina #1002 intacta; minteo + Escape post-minteo, la misma persistencia (vía `onDone`); Escape y X pre-minteo siguen cancelando sin mintear; trampa de foco intacta (Tab en el último → primero, Shift+Tab en el primero → último, en el medio no interviene); `nextToken` con semillas → `#1013` y con galería vacía → `#1001`.
- **Verificación 3 (contenido del bundle + comparación contra conocido-bueno):** cadenas decisivas en el JS nuevo, con los mismos conteos que el bundle bueno del Ciclo 5: «queda guardada en tu colección» ×1, «Cerrar y guardar en la galería» ×1, «Ver en la galería» ×1, «Minteado (simulado)» ×3, «mintearlo» ×2 / «minterarlo» ×0, «Escape» ×3, «No se pudo copiar» ×1, `aria-pressed` ×6, «Datos de ejemplo» ×1, «Creador» ×1, «Tú (ejemplo)» ×1, `sig-frames` ×1 en JS (+×6 en CSS). En el CSS: token Georgia ×1, `prefers-reduced-motion` ×1 y **la media query del Ciclo 5 presente** como `@media(max-width:420px){.stats{display:flex;flex-wrap:wrap}.stats>div{flex:1 1 120px}}` (forma literal de la fuente; en Vite 8/Lightning CSS salía minificada como `(width<=420px)` y `flex:120px`, mismo significado). **Tamaños, con desviación explicada:** JS 245.696 → **169.645 B (−76.051 B, −30,95 %)**: es el efecto esperado del cambio de framework (en hash-lab la misma bajada fue −31,8 %, de 237.744 a 162.247 B) y el bundle queda dentro del rango de las hermanas en React 18 / Vite 6 (gas-calc 164.386 B, contract-play 170.458 B según el registro del Ciclo 5 de hash-lab); no es pérdida de contenido: todas las cadenas decisivas están. CSS 10.417 → 10.495 B (+78 B, +0,75 %: cambia el procesador CSS, de Lightning CSS en Vite 8 al de Vite 6, mismo patrón que el +151 B de hash-lab). Sin variables de entorno de build: `VITE_*` = 0 y `process.env` = 0 en `src/`, `vite.config.js` e `index.html`; build autónomo, sin hallazgo en este frente.
- **README:** la introducción ya dice «React 18 + Vite 6» y se añadió la sección «Stack» con las versiones exactas resueltas y sus rangos. **N-B8 queda CERRADO.**
