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
