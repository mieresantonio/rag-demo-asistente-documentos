# Improvement log — biblioteca-prompts

## 2026-11-02 · Fase 2, Ciclo 1

### BIB-A1 (alta) — 15 roles anunciados, solo 8 con prompt
- **Hallazgo:** el filtro anunciaba «Productividad profesional (15 roles)», pero 7 roles devolvían siempre 0 resultados: `contable`, `asistente de dirección`, `psicología organizacional`, `logística` y `RRHH`/`operaciones`/`legal` en su variante profesional.
- **Cambio:** añadidos los 7 prompts que faltan (p9–p15) en `src/data/prompts.js`, con redacción original y exactamente la misma estructura de 6 campos (ACCIÓN, PASOS, PERSONA, CONTEXTO, RESTRICCIONES, PLANTILLA) y el mismo tono que los existentes: conciliación bancaria (contable), resumen previo de reunión de dirección (asistente de dirección), encuesta de clima a plan de mejora (psicología organizacional), plan de acogida de 30 días (RRHH), pase de turno (operaciones), ruta de reparto (logística) y control de plazos legales (legal). La UI no cambia su promesa: ahora la cumple. Total de ejemplos: 30 (15 de negocio + 15 profesionales).
- **Verificaciones:**
  1. Build: `npm run build` OK (Vite 5.4.21, JS 181,31 kB; crece desde 173,29 kB por el contenido nuevo, sin errores ni warnings).
  2. Smoke funcional: conteo ejecutado con Node sobre los datos reales — los 15 roles profesionales tienen exactamente 1 prompt cada uno y las 15 categorías de negocio siguen con 1 cada una; los 7 prompts nuevos tienen los 6 campos no vacíos. Ningún filtro de rol/categoría devuelve 0 por falta de contenido.
  3. Checklist: textos nuevos re-leídos, ortografía y acentuación correctas («psicólogo organizacional», «conciliación», «puntuación», «cercanía», signos y tildes revisados); IDs previos intactos (b1–b15, p1–p8 sin cambios) y orden p1–p15 secuencial.

### BIB-M1 (media) — Confirmación de guardado invisible
- **Hallazgo:** `saveCustom` escribía «Guardado en tu biblioteca…» en `builderNote`, que solo se renderiza en el constructor, y cambiaba al instante a la biblioteca; además el prompt nuevo quedaba tras las tarjetas de ejemplo.
- **Cambio:** en `src/App.jsx`, al guardar: el aviso pasa a `libraryNote`, que sí se renderiza en la vista de biblioteca (`role="status"`, con botón «Entendido»); el prompt queda expandido, con desplazamiento hasta su tarjeta, insignia «Recién guardado» y resaltado (`.card.saved` en `App.css`); y `allPrompts` pone los prompts propios primero (`[...custom, ...EXAMPLE_PROMPTS]`), así el nuevo es la primera tarjeta. Al eliminar ese prompt, el aviso y el resaltado se limpian.
- **Verificaciones:**
  1. Build: `npm run build` OK; el bundle construido contiene las cadenas «Guardado en tu biblioteca» y «Recién guardado».
  2. Smoke funcional: revisión del flujo en el código compilado — `saveCustom` fija vista `biblioteca` sin filtros, `savedId`/`expandedId` al nuevo id, la tarjeta lleva `id="prompt-<id>"` y el efecto de desplazamiento la localiza; el conteo de datos no cambia por este arreglo (30 ejemplos verificados aparte).
  3. Checklist: textos nuevos re-leídos («Está el primero de la lista, marcado como recién guardado.», «Entendido», «Recién guardado») con ortografía correcta; sin regresiones: favoritos, copiar, constructor y filtros mantienen su código y el build pasa.

### BIB-M3 / higiene (media) — `.gitignore`
- **Hallazgo:** sin `.gitignore`, con `node_modules/` y `dist/` presentes y versionables.
- **Cambio:** creado `.gitignore` con `node_modules/`, `dist/`, `*.local` y `.DS_Store`.
- **Verificaciones:** (1) build OK tras el cambio; (2) conteo de prompts sin cambios (30); (3) contenido revisado contra los artefactos reales de la carpeta.

## 2026-11-02 · Fase 2, Ciclo 2

### BIB-M2 (media) — Patrón de pestañas ARIA completo
- **Hallazgo:** había `role="tablist"` y `role="tab"` con `aria-selected`, pero ningún `role="tabpanel"`, ni `aria-controls`, ni navegación con flechas: un lector de pantalla anunciaba pestañas sin panel asociado.
- **Cambio:** en `src/App.jsx`, patrón ARIA completo: cada pestaña lleva `id` (`tab-biblioteca`/`tab-constructor`) y `aria-controls` a su panel; cada vista (`<main>`) es ahora `role="tabpanel"` con `id` propio (`panel-biblioteca`/`panel-constructor`), `aria-labelledby` a su pestaña y `tabIndex={0}`; el skip-link apunta al panel activo (antes a `#contenido`, que era el propio `<main>`; el destino sigue existiendo y sigue tras la navegación). Navegación con teclado en el `tablist`: ←/→ mueven y activan con activación automática (el mismo comportamiento que el clic), Inicio/Fin saltan a los extremos, y el foco sigue a la pestaña activada (refs).
- **Verificaciones:**
  1. Build: `npm run build` OK. Contenido del bundle verificado por dentro (no basta que compile): el JS construido contiene `tabpanel` ×2, `aria-controls` ×2, `panel-biblioteca`/`panel-constructor` ×3 cada uno (id del panel, `aria-controls` y destino del skip-link), `tab-biblioteca`/`tab-constructor` ×2 y los manejadores `ArrowRight`/`ArrowLeft`. Comparación contra el último build bueno (Ciclo 1): JS 181,31 → 182,06 kB (+0,75, el manejador de teclado y los atributos ARIA); CSS sin cambios este ciclo (9,01 kB). Desviación explicada.
  2. Smoke: `vite preview` sirve la app (HTTP 200, título correcto); conteo de datos ejecutado con Node: 30 prompts (15 negocio + 15 profesional), los 15 roles y las 15 categorías con exactamente 1 prompt cada uno — sin regresión de BIB-A1/BIB-M1 (el bundle sigue conteniendo «Recién guardado» y «Guardado en tu biblioteca»).
  3. Checklist: ids cruzados a mano en el código (tab ↔ panel ↔ skip-link forman un triángulo consistente, sin ids duplicados: solo se monta una vista a la vez); ortografía sin cambios (no se añadió texto visible nuevo, solo atributos); media queries intactas (5 bloques `@media` en el CSS, sin tocar). Factor invisible de build: ninguno — sin `import.meta.env` ni variables `VITE_*`.

## 2026-11-02 · Fase 2, Ciclo 3

### BIB-B6 (baja) — Meta descripción y favicon, por fin
- **Hallazgo:** `index.html` no tenía `<meta name="description">` ni favicon de ningún tipo (la app hermana sí traía descripción): el navegador pedía `/favicon.ico` y recibía 404, y los buscadores/previsualizaciones no tenían descripción que mostrar.
- **Cambio:** descripción específica añadida (nombra los 30 prompts y la estructura de 6 campos), `<meta name="theme-color" content="#2a2560">` y favicon propio `public/favicon.svg` (índigo `#2a2560` del hero con libro abierto crema/ámbar), enlazado como `image/svg+xml`. El título ya era específico («Biblioteca de Prompts — Negocio y productividad profesional»); no se tocó. No quedaba ningún favicon de plantilla de Vite que retirar: simplemente no había icono.

### Bajas seguras de este ciclo
- **BIB-B7 (contraste):** el placeholder (`#9a958a`, 2,98:1 sobre blanco) pasa a `#68645a` (5,90:1) y la estrella de favorito inactiva (`#b8b3a8`, 2,09:1), cuyo único indicador es el glifo, pasa a `#6f6a5e` (5,39:1). Ratios calculados con la fórmula WCAG sobre blanco, antes y después.
- **BIB-B4:** el detalle expandido mostraba las 6 etiquetas aunque el campo estuviera vacío (etiqueta con párrafo en blanco) mientras el «prompt armado» de debajo omitía los vacíos: dos representaciones contradictorias en la misma tarjeta. La lista de campos ahora filtra los vacíos, igual que `assemblePrompt`.
- **BIB-B2:** `loadJson` no validaba que lo parseado fuera un array (un `localStorage` corrupto o editado rompía `favorites.includes`/`custom`) y las escrituras no capturaban errores. Ahora la lectura exige `Array.isArray` (si no, valor por defecto) y la escritura va en `saveJson` con `try/catch`: con la cuota llena la app sigue en memoria.
- **BIB-B3:** «Eliminar» un prompt propio actuaba al instante, sin copia fuera del navegador. Ahora pide confirmación (`window.confirm` con el título del prompt y el aviso de que no se puede deshacer); si se cancela, no se borra nada.
- **BIB-B9:** el `setTimeout` que apaga «¡Copiado!» no se guardaba: copiar dos prompts en menos de 2 s apagaba el segundo aviso con el temporizador del primero. El temporizador vive ahora en una `ref` y se limpia antes de crear el siguiente.
- **BIB-B1:** eliminado `FIELD_KEYS`, código muerto exportado y no importado en ningún sitio (comprobado por búsqueda antes de borrar).
- **Texto (veracidad):** el README seguía anunciando «23 prompts de ejemplo — 15 de negocio y 8 de productividad profesional» tras el Ciclo 1: corregido a 30 (15 + 15) con la lista completa de los 15 roles, tal como quedó la app. Era el texto desactualizado más visible para un reclutador.

### Verificaciones (triple, con artefacto por contenido)
1. **Build y comparación:** `npm run build` OK. Contra el último build bueno (Ciclo 2): JS 182.665 → 182.965 B (+300: confirmación de borrado, `saveJson`, temporizador en ref y filtro de campos vacíos) y CSS 9.010 → 9.010 B (idéntico: los cambios de contraste son valores del mismo tamaño). El `dist/index.html` construido contiene `description`, `theme-color` y `favicon.svg`, y `dist/favicon.svg` existe (272 B): verificado en el artefacto, no solo en el fuente.
2. **Smoke:** `vite preview` sirve la app con HTTP 200 y título correcto, y `/favicon.svg` responde 200. Conteo de datos ejecutado con Node: 30 prompts y 6 etiquetas de campo, intactos. Bundle verificado por dentro: `tabpanel` ×2 y «Recién guardado» ×1 / «Guardado en tu biblioteca» ×2 (sin regresión de los Ciclos 1–2) y «¿Eliminar» ×1 (la confirmación nueva llegó al bundle).
3. **Checklist:** ortografía de los textos nuevos revisada («¿Eliminar «…»? No se puede deshacer: solo existe en este navegador.», descripción meta sin errores); contraste recalculado (ver BIB-B7); README releído contra los datos reales (30 = 15 + 15, roles completos). Factor invisible de build: ninguno — sin `import.meta.env` ni variables `VITE_*` (re-verificado este ciclo).
- **Pendientes con motivo:** BIB-B5 (el `execCommand('copy')` es solo el respaldo cuando `navigator.clipboard` no está disponible; retirarlo dejaría sin copiado los contextos no seguros — se mantiene a propósito), BIB-B8 (nombres de categoría compartidos entre bloques —«RRHH», «operaciones», «legal»—: desambiguarlos exige una decisión de datos/etiquetado, no un arreglo de pulido) y BIB-B10 (sin tests ni lint: infraestructura fuera del alcance de bajas de este ciclo).

## 2026-11-02 · Fase 2, Ciclo 4

### BIB-B10 (baja, parte de tests) — Suelo de calidad verificable: script de datos sin dependencias
- **Hallazgo:** sin tests ni lint (BIB-B10): nada detectaba automáticamente una regresión de datos como la de BIB-A1 (roles anunciados sin prompt). Toda la verificación de los Ciclos 1–3 fue conteo manual con Node repetido a mano.
- **Cambio:** `scripts/verify-data.mjs`, Node puro sin framework ni dependencias nuevas, registrado como `"test": "node scripts/verify-data.mjs"` en `package.json` (sin tocar `dev`/`build`/`preview`). Verifica los invariantes que los ciclos fijaron a mano: 30 prompts (15 negocio + 15 profesional), ids únicos, los 6 campos de `FIELD_LABELS` no vacíos en cada prompt, título/descripción/categoría no vacíos, y exactamente 1 prompt por cada una de las 15 categorías de negocio y los 15 roles profesionales. Sale con código ≠0 si algo se rompe. Documentado en el README («Verificación automática»).
- **Verificaciones (triple):**
  1. Build: `npm run build` OK tras añadir el script; artefacto idéntico al último build bueno (Ciclo 3): JS 182.965 B y CSS 9.010 B, byte a byte — el script vive fuera de `src/` y no entra en el bundle.
  2. Script ejecutado contra el estado actual: `npm test` → código 0, 338 comprobaciones en verde, cierre «OK: todos los invariantes… (30 prompts, 15+15, 6 campos, ids únicos)».
  3. Prueba de fuego: en una COPIA temporal en `/tmp` se borró el prompt `p15` del `prompts.js` copiado; el script salió con código 1 y señaló exactamente el daño (total 29, profesional 14, «legal» = 0; 3 comprobaciones fallidas). Copia eliminada; los datos reales no se tocaron. Un test que no puede fallar no es un test: este sí falla.
- **Pendiente con motivo — lint (resto de BIB-B10):** no se instala ESLint en este ciclo: añadirlo a las dos apps React es un cambio de tooling pesado (instalación + config + revisión de falsos positivos) y los fallos históricos de esta app han sido de datos, ya cubiertos por el script. Queda anotado en el README para un ciclo de tooling.

## 2026-11-02 · Fase 2, Ciclo 5

### BIB-B10 (baja, resto: lint) — ESLint flat instalado y limpio; BIB-B10 cerrado
- **Hallazgo:** quedaba el resto de BIB-B10: sin lint, el código no tenía ninguna red automática frente a errores reales (variables no usadas, claves duplicadas, hooks mal llamados), solo el script de datos del Ciclo 4.
- **Cambio (solo tooling, cero `src/`):** instalados como devDependencies `eslint@^9.39.5` + `@eslint/js@^9.39.5` + `eslint-plugin-react@^7.37.5` + `eslint-plugin-react-hooks@^7.1.1` + `globals@^17.14.0`, con `eslint.config.js` flat mínimo y moderno (recomendados de `@eslint/js`, React y React Hooks vía sus configs flat; `dist` ignorado; globals de navegador para la app y de Node para `scripts/`/`vite.config.js`; `react/react-in-jsx-scope` y `react/prop-types` desactivadas con motivo escrito en la config) y script `"lint": "eslint ."` en `package.json`.
- **Conflicto resuelto sin pelea:** el primer intento con `eslint@*` resolvió ESLint 10.14.0 + `@eslint/js@10.0.1`, incompatibles con `eslint-plugin-react@7.37.5` (su peer llega hasta ESLint `^9.7`) — ERESOLVE sin tocar `package.json`. Se fijó la línea 9.x, compatible con Vite 5 y con ambos plugins, y la instalación cerró limpia. Nota: npm marca `eslint@9.39.5` como versión sin soporte activo; es el precio de la compatibilidad con el plugin de React y queda registrado para cuando este amplíe su rango.
- **Resultado del lint:** `npm run lint` → código 0, sin errores ni warnings. No hizo falta corregir ningún error real ni dejar warnings documentados: el código de los Ciclos 1–4 ya pasaba las reglas recomendadas tal cual. Sin reformateo ni renombrados.
- **Verificaciones (triple reforzada):**
  1. Build y tests: `npm run build` OK y `npm test` → código 0, 338 comprobaciones en verde (sin regresión).
  2. Smoke: `vite preview` sirve la app con HTTP 200 (título correcto), `/favicon.svg` y el asset JS también 200; datos intactos (30 prompts, verificados por el propio `npm test`). Servidor cerrado al terminar.
  3. V3 por contenido y bytes: el bundle construido es BYTE A BYTE idéntico al del Ciclo 4 — JS 182.965 B (sha256 `148aeadf…e58b`) y CSS 9.010 B (sha256 `3dae95d1…a2c`), mismos nombres de archivo con hash: el lint no toca `src/` y el bundle lo demuestra. Cadenas decisivas presentes: «Recién guardado» ×1, `tabpanel` ×2, «Guardado en tu biblioteca» ×2.
- **README:** la sección de verificación documenta ahora `npm run lint` junto a `npm test` (sección «Lint») y el pendiente de BIB-B10 desaparece: queda cerrado en tests (Ciclo 4) + lint (este ciclo).
