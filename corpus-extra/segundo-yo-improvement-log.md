# Improvement log — segundo-yo

## 2026-11-02 · Fase 2, Ciclo 1

### SEG-M4 / higiene (media) — `.gitignore`
- **Hallazgo:** sin `.gitignore`, con `node_modules/` y `dist/` presentes y versionables (mismo defecto transversal en las tres apps de portfolio-apps).
- **Cambio:** creado `.gitignore` con `node_modules/`, `dist/`, `*.local` y `.DS_Store`. En este ciclo no se tocó ningún otro archivo de esta app: sus hallazgos restantes (SEG-M1 a SEG-M3 y las bajas) quedan para ciclos posteriores.
- **Verificaciones:**
  1. Build: `npm run build` OK (Vite 5.4.21, JS 165,58 kB y CSS 12,98 kB, idénticos a los del diagnóstico de Fase 1: sin regresión).
  2. Smoke funcional: no aplica cambio funcional; la build completa y el tamaño idéntico confirman que la app sigue como estaba.
  3. Checklist: contenido del `.gitignore` revisado contra los artefactos reales de la carpeta.

## 2026-11-02 · Fase 2, Ciclo 2

### Diseño (medias de diseño del diagnóstico) — Una decisión visual fuerte: la ficha como tarjeta de identidad
- **Hallazgo:** la app más cercana al diseño genérico del portafolio: 1 síntoma pleno (rejilla doble de tarjetas iguales en tareas y glosario) + 3 parciales (sistema violeta con degradados recurrentes — 5 degradados decorativos contados en el CSS: hero, tarjeta resumen, formularios de alta, barra de progreso y tarjeta de método completo —; CTA primarios idénticos en secciones con objetivos distintos; cuerpo en `system-ui`).
- **Cambio (solo CSS/estructura mínima, cero lógica ni datos):** el color pasa a ser sistema con roles — violeta = identidad/estructura, ámbar = acción y avance, tinta = la ficha — y la ficha se convierte en el bloque protagonista:
  - Hero: de lavado degradado violeta a panel tinta plano (`--ink-deep`) con tipografía mayor y franja de datos reales de la app (25 tareas en 5 grupos · 5 pasos · 24 términos, derivados de las constantes, no escritos a mano).
  - Tarjeta resumen de la ficha: misma tinta que el hero (se lee como la tarjeta del segundo yo, no como una tarjeta más), y la rejilla de la ficha pasa a asimétrica 1,15fr/0,85fr.
  - CTA diferenciados: el primario sólido violeta queda SOLO para «Copiar ficha» (la acción principal); los envíos de alta (tarea/término) usan la nueva clase `.btn.action` ámbar.
  - Degradados decorativos eliminados: progreso en ámbar plano, `add-form` y `done-card` en fondos planos. Quedan 2 `linear-gradient` funcionales (chevron del select y máscara de scroll de pestañas), que no son decoración.
  - Quiebre de rejilla: en escritorio (≥701 px) la 5ª tarjeta de cada grupo de tareas ocupa 2 columnas (cada grupo tiene exactamente 5: es ritmo, no azar).
  - Tipografía: el cuerpo pasa a Sora (se añaden pesos 400/500 a la carga de Google Fonts); jerarquía real entre hero (clamp hasta 3rem), secciones y cuerpo.
  - Impresión: añadidos ajustes en `@media print` para que hero y tarjeta resumen (ahora oscuros) impriman en tinta sobre blanco.
- **Síntomas CenteIA antes/después:** plenos 1 → 0; parciales 3 → 1 (la rejilla del glosario se mantiene uniforme, propio de una lista de definiciones; el violeta sigue siendo el color de identidad, pero ya plano y con rol, sin degradado). Degradados decorativos: 5 → 0.
- **Verificaciones:**
  1. Build: `npm run build` OK (Vite 5.4.21). Comparación contra el último build bueno (Fase 1/Ciclo 1): JS 165,58 → 166,03 kB (+0,45: el marcado de la franja de datos del hero) y CSS 12,98 → 13,97 kB (+0,99: reglas del panel protagonista, `.btn.action`, `.hero-meta` y ajustes de impresión). Desviaciones explicadas por los cambios; sin sorpresas.
  2. Smoke: `vite preview` sirve la app (HTTP 200, título correcto) y los datos se ejecutaron con Node desde `src/data.js`: 25 tareas / 5 grupos / 5 pasos / 24 términos, intactos. Contenido del bundle verificado por dentro: el JS construido contiene `hero-meta` y `btn action` (×2, los dos formularios de alta) — el build promete lo que el código dice.
  3. Checklist: media queries intactas (cortes de 700 px y 480 px y bloque de impresión presentes; se añade solo el quiebre ≥701 px); textos nuevos con ortografía correcta («tareas en 5 grupos», «pasos de método», «términos sin jerga»); contraste revisado en código (texto sobre tinta `#cfc9e6`/`#f4f1fa` sobre `#17122b`, ámbar de datos `#fbbf24` sobre tinta, texto `#431407` sobre ámbar en `.btn.action`). Factor invisible de build: ninguno — no hay `import.meta.env` ni variables `VITE_*` en la app; el build es reproducible sin entorno.
- **Fuera de alcance a propósito:** SEG-M1/M2/M3 no se tocan en este ciclo: el encargo de segundo-yo era diseño con cero cambios de lógica/datos, y los tres son de lógica/accesibilidad funcional. Quedan para un ciclo posterior.

## 2026-11-02 · Fase 2, Ciclo 3

### SEG-M1 (media) — Persistencia: lo creado ya no se pierde al recargar
- **Hallazgo:** ficha, tareas propias, términos propios, selecciones y avance del método vivían solo en `useState`: un recarga accidental lo borraba todo, sin aviso; el README lo cubría con la fórmula ambigua «viven en la sesión del navegador» (no había ni `sessionStorage`), mientras la app hermana sí persiste en `localStorage`.
- **Cambio:** persistencia en `localStorage` con el mismo patrón de claves con prefijo que biblioteca-prompts (`segundo-yo:ficha`, `:seleccion`, `:tareas-propias`, `:metodo`, `:terminos-propios`). Lectura validada (la ficha debe ser objeto y se fusiona con la ficha vacía; el resto deben ser arrays: un valor corrupto o editado a mano cae al valor por defecto, nunca rompe el render) y escritura con `try/catch` (cuota llena o almacenamiento no disponible: la app sigue en memoria). El pie de la app y el README ahora dicen la verdad: qué se guarda, dónde y que no sale del navegador; el README gana además el `cd segundo-yo` que le faltaba (SEG-B9).
- **Hallazgo con mitigación (riesgo nuevo del propio cambio):** la persistencia depende de que el navegador permita `localStorage`. Mitigación aplicada: toda lectura/escritura va envuelta en `try/catch` con degradación a sesión en memoria; verificado por lectura de código (no hay ninguna ruta de `localStorage` sin protección).

### SEG-M2 (media) — El skip-link ya salta de verdad
- **Hallazgo:** el enlace apuntaba a `#contenido`, pero ese `id` estaba en el propio `<main>` que envuelve toda la página (enlace, hero y pestañas incluidos): activarlo llevaba al principio del documento, no al contenido.
- **Cambio:** el `id="contenido"` (con `tabIndex={-1}`) pasa a la sección activa, que se monta tras el hero y las pestañas; solo se monta una sección a la vez, así el `id` nunca se duplica. El `<main>` pierde el `id`. Añadido `.section:focus { outline: none }` para que el salto no dibuje contorno sobre todo el bloque.

### SEG-M3 (media) — Glosario sin claves duplicadas
- **Hallazgo:** las tarjetas usaban `key={e.term}` y `addTerm` no impedía repetir un término ya existente («Agente»): claves duplicadas, warning de React y reutilización incorrecta de nodos.
- **Cambio (tres capas):** (1) `addTerm` rechaza duplicados contra el glosario y los propios, sin distinguir mayúsculas ni espacios, con aviso visible (`.form-error`, `role="alert"`) y anuncio de lector de pantalla, conservando lo escrito en el formulario; (2) la clave pasa a ser `base-…`/`propio-…` + término; (3) la carga persistida (SEG-M1) descarta duplicados heredados de sesiones anteriores a esta validación.

### Bajas de este ciclo
- **SEG-B1:** el chip «Todas (25 + las tuyas)» llevaba el 25 a mano y no reflejaba el total al añadir tareas; ahora calcula el total real desde `allGroups`.
- **SEG-B2:** la pestaña del método componía su contador con un `/5` a mano; ahora usa `METHOD_STEPS.length`, como ya hacía la barra de progreso.
- **SEG-B3:** «Usar la primera en mi ficha» usaba la primera **pulsada** (`selected[0]`, orden de clic); ahora recorre grupos y tareas en orden visual y toma la primera seleccionada visible.
- **SEG-B4:** el foco al cambiar de pestaña ya no manipula el DOM (`querySelector('.section h2')` + `setAttribute('tabindex')` fuera de React): cada `<h2>` declara `tabIndex={-1}` y recibe una `ref` (`headingRef`) que el efecto enfoca.
- **SEG-B5:** la ficha gana «Limpiar ficha» (con anuncio), como el constructor de la app hermana; deshabilitado cuando la ficha ya está vacía.
- **SEG-B6:** `package.json` pasa de `disena-tu-segundo-yo` a `segundo-yo`, el nombre de la carpeta.
- **SEG-B7:** placeholders unificados al estilo de la app hermana («Ej.: …», 9 placeholders entre ficha, alta de tarea, alta de término y buscador).
- **Favicon/meta (transversal de pulido):** la app no tenía favicon de ningún tipo (el navegador pedía `/favicon.ico` y recibía 404); creado `public/favicon.svg` propio (tinta `#17122b` con los dos círculos violeta/ámbar del sistema de color), enlazado en `index.html` junto a `<meta name="theme-color" content="#17122b">`. El título y la meta descripción ya eran específicos y correctos; no se tocaron.

### Verificaciones (triple, con artefacto por contenido)
1. **Build y comparación:** `npm run build` OK (Vite 5.4.21, 32 módulos). Contra el último build bueno (Ciclo 2): JS 166.299 → 168.306 B (+2.007: persistencia, validación de duplicados, orden visual, botón Limpiar y textos) y CSS 13.973 → 14.157 B (+184: `.form-error` y `.section:focus`). Desviaciones explicadas; `dist/` contiene además `favicon.svg` (244 B) y el `index.html` construido enlaza `favicon.svg` y `theme-color` (verificado en el HTML de salida, no solo en el fuente).
2. **Smoke:** `vite preview` sirve la app con HTTP 200 y título correcto, y `/favicon.svg` responde 200. Datos ejecutados con Node desde `src/data.js`: 25 tareas / 5 grupos / 5 pasos / 24 términos, intactos. Contenido del bundle verificado por dentro: el JS construido contiene las claves `segundo-yo:ficha`, `segundo-yo:tareas-propias` y `segundo-yo:terminos-propios`, `localStorage` ×3 contextos, «Limpiar ficha» y «ya está en el glosario» ×2 (aviso visible + anuncio), y sin regresión del Ciclo 2 (`hero-meta` ×1, `btn action` ×2). Sin `querySelector`/`setAttribute` en `App.jsx` (B4), sin `selected[0]` (B3) y sin los literales «25 + las tuyas» ni `/5` (B1/B2), comprobado por búsqueda en el fuente.
3. **Checklist:** ortografía de los textos nuevos revisada («Ej.: ¿cómo evito que se pierda un compromiso?», «ya está en el glosario: no se ha añadido un duplicado», nota de persistencia del pie con «localStorage»); síntomas CenteIA sin regresión: degradados decorativos siguen en 0 (los 4 `linear-gradient` del CSS construido son los funcionales ya conocidos: 2 del chevron del select y 2 de la máscara de pestañas —webkit y estándar—), plenos se quedan en 0; media queries intactas (no se tocó ninguna salvo los dos añadidos citados). Factor invisible de build: ninguno — sin `import.meta.env` ni variables `VITE_*` en la app (re-verificado este ciclo).
- **Pendiente con motivo — SEG-B8** (sin tests ni lint): crear la infraestructura de tests es un cambio de tooling que excede las bajas de pulido de este ciclo; queda como estaba, anotado.

## 2026-11-02 · Fase 2, Ciclo 4

### SEG-B8 (baja, parte de tests) — Suelo de calidad verificable: script de datos sin dependencias
- **Hallazgo:** sin tests ni lint (SEG-B8): los invariantes de contenido (25/5/5/24) y la unicidad del glosario que SEG-M3 protege en la UI no tenían ninguna red automática; una edición de `src/data.js` podía reintroducir un duplicado o perder una tarea sin que nada lo detectara hasta una revisión manual.
- **Cambio:** `scripts/verify-data.mjs`, Node puro sin framework ni dependencias nuevas, registrado como `"test": "node scripts/verify-data.mjs"` en `package.json` (sin tocar `dev`/`build`/`preview`). Verifica: 25 tareas en 5 grupos con 5 por grupo, 5 pasos de método, 24 términos de glosario, claves de glosario únicas incluso sin distinguir mayúsculas ni espacios extremos, ids de grupo únicos y nombres/descripciones/definiciones no vacíos. Sale con código ≠0 si algo se rompe. Documentado en el README («Verificación automática»).
- **Verificaciones (triple):**
  1. Build: `npm run build` OK tras añadir el script; artefacto idéntico al último build bueno (Ciclo 3): JS 168.306 B y CSS 14.157 B, byte a byte — el script vive fuera de `src/` y no entra en el bundle.
  2. Script ejecutado contra el estado actual: `npm test` → código 0, 125 comprobaciones en verde, cierre «OK: todos los invariantes… (25 tareas / 5 grupos / 5 pasos / 24 términos, glosario sin duplicados)».
  3. Prueba de fuego: en una COPIA temporal en `/tmp` se sustituyó «Uso de herramientas» por un duplicado `agente` en minúscula (colisión con «Agente» solo visible sin distinguir mayúsculas, manteniendo el total en 24); el script salió con código 1 y señaló el duplicado (`agente` ×2, 23 distintos). Copia eliminada; los datos reales no se tocaron.
- **Pendiente con motivo — lint (resto de SEG-B8):** no se instala ESLint en este ciclo, por el mismo motivo que en la app hermana: tooling pesado para dos apps y riesgo histórico concentrado en datos, ya cubierto. SEG-B8 queda cerrado en tests y pendiente solo en lint, anotado en el README.

## 2026-11-02 · Fase 2, Ciclo 5

### SEG-B8 (baja, resto: lint) — ESLint flat instalado y limpio; SEG-B8 cerrado
- **Hallazgo:** quedaba el resto de SEG-B8: sin lint, el código no tenía ninguna red automática frente a errores reales (variables no usadas, claves duplicadas, hooks mal llamados), solo el script de datos del Ciclo 4.
- **Cambio (solo tooling, cero `src/`):** instalados como devDependencies `eslint@^9.39.5` + `@eslint/js@^9.39.5` + `eslint-plugin-react@^7.37.5` + `eslint-plugin-react-hooks@^7.1.1` + `globals@^17.14.0`, con `eslint.config.js` flat mínimo y moderno, idéntico al de la app hermana (recomendados de `@eslint/js`, React y React Hooks vía sus configs flat; `dist` ignorado; globals de navegador para la app y de Node para `scripts/`/`vite.config.js`; `react/react-in-jsx-scope` y `react/prop-types` desactivadas con motivo escrito en la config) y script `"lint": "eslint ."` en `package.json`.
- **Conflicto resuelto sin pelea:** igual que en la app hermana, `eslint@*` resolvía ESLint 10.x, incompatible con el peer de `eslint-plugin-react@7.37.5` (hasta `^9.7`); se fijó directamente la línea 9.x, compatible con Vite 5, y la instalación cerró limpia a la primera. Nota: npm marca `eslint@9.39.5` como versión sin soporte activo; queda registrado para cuando el plugin amplíe su rango.
- **Resultado del lint:** `npm run lint` → código 0, sin errores ni warnings. No hizo falta corregir ningún error real ni dejar warnings documentados: el código de los Ciclos 1–4 ya pasaba las reglas recomendadas tal cual. Sin reformateo ni renombrados.
- **Verificaciones (triple reforzada):**
  1. Build y tests: `npm run build` OK y `npm test` → código 0, 125 comprobaciones en verde (sin regresión).
  2. Smoke: `vite preview` sirve la app con HTTP 200 (título correcto), `/favicon.svg` y el asset JS también 200; datos intactos (25 tareas / 5 grupos / 5 pasos / 24 términos, verificados por el propio `npm test`). Servidor cerrado al terminar.
  3. V3 por contenido y bytes: el bundle construido es BYTE A BYTE idéntico al del Ciclo 4 — JS 168.306 B (sha256 `baef1e5f…e319`) y CSS 14.157 B (sha256 `1f6e6c69…7b66`), mismos nombres de archivo con hash: el lint no toca `src/` y el bundle lo demuestra. Cadenas decisivas presentes: `hero-meta` ×1, «Limpiar ficha» ×1, `btn action` ×2.
- **README:** la sección de verificación documenta ahora `npm run lint` junto a `npm test` (sección «Lint») y el pendiente de SEG-B8 desaparece: queda cerrado en tests (Ciclo 4) + lint (este ciclo).
