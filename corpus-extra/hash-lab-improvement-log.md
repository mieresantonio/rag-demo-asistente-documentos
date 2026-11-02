# Improvement log — hash-lab

## 2026-11-02 · Fase 2, Ciclo 1

### HASH-A1 (H-1 + H-3 del diagnóstico) — Validez transitiva y Restaurar honesto
- **Hallazgo:** al manipular un bloque, solo el siguiente inmediato se marcaba
  ROTO y los posteriores seguían «Válido» (el README afirmaba lo contrario);
  además, «Restaurar cadena» solo re-enlazaba los hashes y re-legitimaba el
  dato manipulado sin avisar.
- **Cambio:**
  - `src/App.jsx`: `statuses` ahora es transitivo — un bloque queda ROTO si
    su enlace directo falla **o** si cualquier bloque anterior ya está roto.
    Se distingue rotura directa de heredada: el aviso del bloque y la etiqueta
    del enlace dicen la verdad en cada caso («enlace roto» frente a «la cadena
    ya viene rota desde un bloque anterior»; el bloque heredado aclara que su
    enlace inmediato todavía coincide).
  - `restoreChain` ahora restaura el contenido original de ejemplo
    (`setChain(initialChain())`): descarta las ediciones en vez de re-enlazar
    el dato manipulado. Nota visible junto al botón que lo explica, y README
    alineado (la afirmación «todos los posteriores se marcan ROTO» ahora es
    lo que el código hace, y Restaurar se describe como vuelta a los datos
    originales).
  - Estilo menor: clase `.restore-note` en `src/index.css`.
- **Verificaciones (triple):**
  1. `npm run build` ✅ (Vite 8, sin errores) y `npx oxlint` ✅ 0 avisos /
     0 errores (tras reescribir el cálculo en forma funcional sin mutación,
     el lint volvió a su estado original).
  2. Smoke funcional en Node ✅: con el `sha256.js` real y las funciones de
     cadena extraídas del propio `App.jsx`, manipular el bloque 0 deja
     `[ok, roto-directo, roto-heredado]` (antes el bloque 2 quedaba válido);
     manipular el bloque 1 deja el 2 roto; Restaurar devuelve el dato original
     («Bloque génesis — ejemplo de inicio de cadena»), no el manipulado, y la
     cadena vuelve a ser válida. Textos nuevos presentes en el bundle `dist/`.
  3. Checklist de detalle ✅: ortografía de los textos tocados revisada
     (tildes y concordancia), README veraz tras el cambio, sin regresiones
     (la calculadora SHA-256 no se tocó; ningún servidor quedó corriendo).

## 2026-11-02 · Fase 2, Ciclo 2

### HASH-C2-1 (H-2) — SHA-256 estándar también con surrogados solitarios
- **Hallazgo:** `utf8Bytes` divergía del estándar con surrogados
  solitarios o parejas inválidas: un surrogado alto sin pareja baja
  consumía igualmente el carácter siguiente y fabricaba un code point,
  y un surrogado bajo solitario se codificaba en CESU-8 en vez de U+FFFD.
  Verificado en el diagnóstico: `"\uD800"`, `"\uDC00"` y `"\uD800x"`
  daban hashes distintos a `node:crypto`.
- **Cambio (acotado, solo `src/sha256.js`):** el surrogado alto solo
  forma pareja si el siguiente código es un surrogado bajo válido; en
  caso contrario se codifica U+FFFD (EF BF BD) **sin consumir** el
  carácter siguiente, y el surrogado bajo solitario también se codifica
  como U+FFFD — el comportamiento estándar de `TextEncoder` /
  `node:crypto`. No se toca el núcleo SHA-256.
- **Verificaciones (triple):**
  1. `npm run build` ✅ y `npx oxlint` ✅ 0 avisos / 0 errores.
  2. Smoke en Node ✅: `sha256Hex` coincide con `node:crypto` en 19/19
     casos: vacía, «abc», acentos, emoji 🚀, bordes de padding
     55/56/64/1000, y los casos límite `"\uD800"`, `"\uDC00"`,
     `"\uD800x"`, `"x\uDC00y"`, `"\uD800\uD800"`, `"\uDC00\uD800"`,
     `"a\uDFFFb"`, alto solitario al final y las parejas válidas.
  3. Detalle/contenido ✅: README actualizado (la codificación se
     describe como estándar y verificada también en esos casos);
     comparación contra el build anterior conocido-bueno de HASH-A1
     (JS 237.025 B): JS nuevo 237.401 B (+376 B, explicado por la rama
     U+FFFD y el tope de HASH-C2-2) y misma estructura (index.html +
     1 JS + 1 CSS + favicon/icons, mismas dos vistas: calculadora y
     cadena). Sin dependencias de variables de entorno
     (`import.meta.env`/`VITE_*` = 0 en la app): no aplica el riesgo de
     build dependiente de variables no documentadas.

### HASH-C2-2 (H-4) — Tope de longitud: el recálculo por tecla no congela la pestaña
- **Hallazgo:** ningún textarea tenía límite y SHA-256 (JS puro) se
  recalcula completo en cada tecla: pegar varios MB podía congelar la
  pestaña, sin aviso ni tope.
- **Cambio:** constante `MAX_TEXT_LENGTH = 5000` aplicada con
  `maxLength` a los 3 textarea del código (los dos de la calculadora y
  el dato de bloque, que se renderiza en cada uno de los 3 bloques),
  nota visible en la calculadora que explica el límite
  y su motivo, y sección «Límites conocidos» en el README que lo
  documenta como límite de la demo, no del algoritmo.
- **Verificaciones (triple):**
  1. `npm run build` ✅ y `oxlint` ✅ limpio.
  2. Smoke/lógica ✅: el tope está en el código de los 3 campos y los
     textos de ejemplo y vectores habituales (≤1.000 caracteres) quedan
     muy por debajo; la cadena de HASH-A1 no se ve afectada (sus textos
     decisivos siguen en el bundle: «descarta tus ediciones», 1).
  3. Detalle/contenido ✅: cadenas decisivas dentro del bundle —
     «Límite de la demo» (1), «5.000 caracteres» (1) y `maxLength`
     presente ×3 con la constante compilada `5e3` (= 5.000) ×3;
     ortografía de la nota revisada; build servida un momento: HTTP 200
     y asset nuevo referenciado; sin servidores al final.

> Medias del diagnóstico que quedan fuera de este ciclo en hash-lab:
> ninguna otra MEDIA seguía abierta tras HASH-A1 (H-1/H-3 cerrados en
> el Ciclo 1). Las BAJA de hash-lab no entraban en el alcance.

## 2026-11-02 · Fase 2, Ciclo 3

### HASH-C3-1 (H-5 + H-6 + H-7) — Copia honesta, placeholder legible y botones distinguibles
- **Cambio:** el placeholder pasa de `#5b6378` (3,07:1) a `#8b93a7`
  (5,98:1 calculado sobre `#10141f`, ≥4,5:1). `CopyButton` solo muestra el
  ✓ si la copia tuvo éxito de verdad (comprueba también el retorno de
  `execCommand`); si falla, el botón indica «No se pudo copiar» en su
  título. Los dos botones de copiar llevan etiquetas distintas («Copiar
  hash del primer texto» / «…del segundo texto») y el veredicto de
  comparación lleva `aria-live="polite"`.
- **Verificaciones (triple):** 1) `npm run build` ✅ y `npx oxlint` ✅
  0 avisos / 0 errores. 2) Smoke ✅: regresión HASH-C2-1 ejecutada —
  `sha256Hex` coincide con `node:crypto` en vacía, «abc», acentos/emoji,
  1000 caracteres y los surrogados solitarios; contraste del placeholder
  recalculado en Node = 5,98:1; cadenas decisivas en el bundle — ambas
  etiquetas de copiar (1 cada una), «descarta tus ediciones» (1, regresión
  HASH-A1) y «Límite de la demo» (1, regresión HASH-C2-2); el color nuevo
  está en el CSS del bundle (1). 3) Detalle ✅: comparación V3 contra el
  último build conocido-bueno (JS 237.401 B): JS nuevo 237.610 B (+209 B)
  y misma estructura de vistas; `VITE_*` = 0 en `src/`; README actualizado.

### HASH-C3-2 (H-8, parcial) — Favicon propio y fuera la plantilla sin uso
- **Cambio:** `public/favicon.svg` ya no es el logotipo morado de Vite:
  es una `#` cian sobre el fondo de la app. Retirados los recursos de
  plantilla no referenciados en ningún archivo (verificado por grep):
  `public/icons.svg`, `src/assets/react.svg` y `src/assets/vite.svg`
  (la carpeta `src/assets/` queda eliminada). No se tocaron los
  `@types/*` de `package.json`: retirarlos exige regenerar el lockfile y
  no aporta nada visible; queda anotado como resto cosmético de H-8.
- **Verificaciones (triple):** 1) Build ✅: el nuevo `dist/` ya no contiene
  `icons.svg` y su `favicon.svg` pesa 241 B (antes 9.522 B, el de Vite).
  2) Smoke ✅: grep de `react.svg`/`vite.svg`/`icons.svg` en `src/`,
  `index.html` y README = 0 antes de borrar y el build posterior no los
  echa en falta. 3) Detalle ✅: ortografía revisada; sin regresiones en la
  calculadora ni en la cadena (verificado en HASH-C3-1); sin servidores
  al final.

## 2026-11-02 · Fase 2, Ciclo 4 — Coherencia visual (GR-1): firma de cabecera

- **Gesto:** tira de hashes monoespaciada protagonista en el hero (`.sig-hashline`, `aria-hidden`): `0000…0000 → 9f2c…a41b → 51d8…07e3 → c4aa…b920` en cian, bajo la fila marca/badget. Solo presentación: 1 elemento JSX decorativo + 1 regla CSS; lógica, datos y textos funcionales intactos.
- **Verificación 1 (build):** `npm run build` → exit 0.
- **Verificación 2 (sirve + smoke):** `dist/` servido en local → index 200 y asset JS 200. Smoke de lógica: `sha256Hex` ejecutado en Node coincide con `node:crypto` en `""`, `"abc"` y texto con acentos («Bloque génesis — ejemplo»).
- **Verificación 3 (contenido + comparación):** bundle con `sig-hashline` ×2 (JS+CSS) y cadenas decisivas intactas («Datos de ejemplo», «SHA-256»). JS 237.610 → 237.744 B (+134 B, +0,06 %, la línea decorativa) y CSS 6.790 → 6.997 B. `VITE_*` = 0.

## 2026-11-02 · Fase 2, Ciclo 5 — Alineación de versiones del conjunto web3 (GR-2): bajada a React 18 / Vite 6

- **Resultado: ALINEADA** (la verificación completa pasa; no hizo falta revertir).
- **Referencia (hermana gas-calc, leída de su `package.json` y su lockfile):**
  rangos `react ^18.3.1`, `react-dom ^18.3.1`, `vite ^6.0.7`,
  `@vitejs/plugin-react ^4.3.4`, `lucide-react ^0.469.0`; resueltos en su
  lockfile: react 18.3.1, react-dom 18.3.1, vite 6.4.5,
  `@vitejs/plugin-react` 4.7.0, lucide-react 0.469.0.
- **Antes → después en hash-lab** (rangos en `package.json` → resuelto en el lockfile nuevo):
  - `react`: `^19.3.1` (19.3.1) → `^18.3.1` (**18.3.1**, igual que gas-calc)
  - `react-dom`: `^19.3.1` (19.3.1) → `^18.3.1` (**18.3.1**)
  - `vite`: `^8.3.4` (8.3.5) → `^6.0.7` (**6.4.5**, igual que gas-calc)
  - `@vitejs/plugin-react`: `^6.1.2` (6.1.2) → `^4.3.4` (**4.7.0**, igual que gas-calc)
  - `lucide-react`: `^1.61.0` (1.61.0) → `^0.469.0` (**0.469.0**) — también
    parte de la fragmentación GR-2; los 16 iconos usados existen en la
    0.469 (verificado contra el `.d.ts` de gas-calc antes de bajar).
  - Sin tocar: `oxlint ^1.88.0` (resuelto 1.89.0, necesario para la
    verificación de lint) y `@types/react` / `@types/react-dom ^19.3.0`
    (proyecto JS sin TypeScript, sin `peerDependencies` que choquen;
    resto cosmético ya anotado en el Ciclo 3). `npm install` regeneró el
    lockfile sin errores ni conflictos de peer deps (exit 0).
  - Viabilidad previa: el código no usa ninguna API exclusiva de
    React 19 (solo `useState`, `useMemo`, `StrictMode`, `createRoot`);
    `vite.config.js` es el mismo patrón que el de gas-calc.
- **Verificaciones (triple reforzada):**
  1. **Build + lint ✅:** `npm run build` exit 0 con Vite 6.4.5 y
     `npx oxlint` 0 avisos / 0 errores. Servido un momento: index 200
     y asset JS 200; sin servidores al final.
  2. **Regresión funcional completa ✅:** `sha256Hex` (con el
     `src/sha256.js` real) coincide con `node:crypto` en **19/19**
     casos: vacía, «abc», acentos, emoji 🚀, bordes de padding
     55/56/64/1000, surrogados solitarios e inválidos (`"\uD800"`,
     `"\uDC00"`, `"\uD800x"`, `"x\uDC00y"`, `"\uD800\uD800"`,
     `"\uDC00\uD800"`, `"a\uDFFFb"`, alto solitario al final) y parejas
     válidas. Cadena transitiva de HASH-A1 ✅: manipular el bloque 0
     deja `[ok, roto-directo, roto-heredado]`; manipular el bloque 1
     deja el 2 roto-directo; Restaurar devuelve el dato original
     («Bloque génesis — ejemplo de inicio de cadena») y la cadena
     vuelve a ser válida. Tope ✅: `MAX_TEXT_LENGTH = 5000` en el
     código y `maxLength` en los 3 textarea.
  3. **V3 por contenido ✅:** cadenas decisivas en el bundle nuevo —
     «descarta tus ediciones» (1), «Límite de la demo» (1),
     «5.000 caracteres» (1), firma `.sig-hashline` del Ciclo 4
     (JS 1 + CSS 1, la clase `.sig-hashline` en el CSS), etiquetas
     «Copiar hash del primer/segundo texto» (1 cada una); `maxLength`
     ×3 con la constante compilada `5e3` ×3; `VITE_*` = 0 en `src/`.
     **Tamaño, con desviación explicada:** JS 237.744 B (Ciclo 4,
     React 19 + Vite 8/Rolldown + lucide 1.61) → **162.247 B**
     (−75.497 B, −31,8 %): es el efecto esperado del cambio de
     framework — el bundle nuevo queda dentro del rango de las
     hermanas en React 18 / Vite 6 (token-explorer 162.061 B,
     wallet-sim 163.425 B, gas-calc 164.386 B, contract-play
     170.458 B), no es una pérdida de contenido (todas las cadenas
     decisivas están). CSS 6.997 → 7.148 B (+151 B, +2,2 %: cambia el
     procesador CSS, de Lightning CSS en Vite 8 al de Vite 6) e
     `index.html` intacto (481 B).
- **README:** solo se tocó la línea de Stack («React 18 + Vite 6»),
  conforme al cambio consumado.
