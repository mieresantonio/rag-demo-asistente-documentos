# Improvement log — gas-calc

## 2026-11-02 · Fase 2, Ciclo 1

### GAS-A1 (G-1 + G-3 + G-4) — Wei exacto, fórmula verdadera, magnitudes y EIP-1559
- **Hallazgo:** el resultado «en wei» era `unidades × gwei` (faltaba ×10⁹):
  con los valores por defecto mostraba 3.750.000 wei en vez de
  3.750.000.000.000.000, y la fórmula impresa era aritméticamente falsa.
  Además, «un ETH son mil billones de wei» es magnitud equivocada en español
  (10¹⁸ = un trillón) y el modelo de subasta pre-EIP-1559 se presentaba como
  vigente.
- **Cambio (`src/App.jsx`):**
  - `result.wei` se calcula como `BigInt(round(u × g)) × 10⁹` (exacto para
    valores enteros, sin pérdida de precisión al formatear en es-ES). La
    fórmula impresa ahora es verdadera en los tres pasos y coherente con el
    ETH/USD mostrado (paso 2: wei ÷ 10¹⁸ = el mismo ETH de la cabecera).
  - Nota de magnitudes corregida: «Un gwei **equivale a** mil millones de wei
    (10⁹); un ETH **equivale a un trillón** de wei (10¹⁸)».
  - La explicación etiqueta el modelo como **simplificado y anterior a
    EIP-1559** y aclara el modelo actual (tarifa base que se quema, ajustada
    por bloque ~12 s, más propina de prioridad). README actualizado en el
    mismo sentido. Concordancia de la comparativa corregida («velocidades
    lenta, estándar y rápida»; también en el README, G-9) y retirado el import
    sin uso `Minus` (G-6).
- **Verificaciones (triple):**
  1. `npm run build` ✅ (Vite 6, sin errores).
  2. Smoke funcional en Node ✅: 150.000 × 25 gwei = **3.750.000.000.000.000
     wei** exactos (formato es-ES verificado); caso conocido 1 ETH = 10¹⁸ wei
     exacto (1.000.000 gas × 1.000 gwei); 1 × 1 gwei = 10⁹ wei; el paso 2
     (wei ÷ 10¹⁸) da el mismo 0,00375 ETH que muestra la UI. Textos nuevos
     («un trillón de wei», «anterior a EIP-1559») presentes en el bundle.
  3. Checklist ✅: sin restos de «mil billones» ni de la fórmula falsa;
     ortografía de textos tocados correcta; README veraz; sin servidores.

### GAS-A2 (G-2) — Campo «Unidades de gas» editable al teclear
- **Hallazgo:** el `clamp` aplicado en cada `onChange` sustituía la primera
  tecla por el mínimo (21.000) y hacía impracticable escribir un valor.
- **Cambio (`src/App.jsx`):** los handlers de tecleo (gas, ETH y unidades)
  guardan el valor en crudo, **sin clamp**; el componente `Field` valida
  **al salir del campo** (`onBlur`): vacío/inválido → mínimo, fuera de rango
  → cota más cercana. La pista del campo de unidades lo explica.
- **Verificaciones (triple):**
  1. `npm run build` ✅ (el mismo build de arriba, con ambos arreglos).
  2. Smoke en Node ✅: simulando el handler nuevo, teclear «50000» produce la
     secuencia 5 → 50 → 500 → 5.000 → 50.000 sin ningún salto a 21.000; al
     salir del campo, 50.000 queda intacto, 5 se ajusta a 21.000 y un valor
     por encima del máximo se ajusta a 5.000.000. En el código, `clamp` solo
     queda en la definición y en el `onBlur`.
  3. Checklist ✅: los presets, el deslizador y «Restablecer» siguen fijando
     valores dentro de rango (sin regresión); el resto de campos comparte el
     mismo mecanismo mejorado; ningún servidor quedó corriendo.

## 2026-11-02 · Fase 2, Ciclo 3

### GAS-C3-1 (G-5) — HTML válido en la explicación y resultado con región viva
- **Cambio:** el `<h2>` ya no va dentro del `<button>` desplegable: el botón
  va dentro del encabezado (`aria-expanded` conservado, estilo equivalente
  con `.explain-title`/`.explain-head-text`). Los totales del resultado
  llevan `aria-live="polite"`.
- **Verificaciones (triple):** 1) `npm run build` ✅. 2) Smoke/estructura ✅:
  en el código, el segmento del botón ya no contiene ningún `<h2>` y los
  totales llevan la región viva (presente en el bundle); regresión GAS-A1/A2:
  wei ejecutado en Node = 3.750.000.000.000.000 exactos para 150.000×25 y
  paso 2 = 0,00375 ETH. 3) Detalle ✅: cadenas decisivas en el bundle —
  «un trillón de wei» (1), «anterior a EIP-1559» (1), «mil billones» (0);
  comparación V3 contra el último build conocido-bueno (JS 163.185 B):
  JS nuevo 164.069 B (+884 B, textos y estructura nuevos) y misma
  estructura + favicon nuevo. `VITE_*`/`import.meta.env` = 0 en `src/`
  (reconfirmado; no se tocaron configs).

### GAS-C3-2 (G-7 + G-8 + G-10) — Iconos distintos, comparativa coherente, higiene
- **Cambio:** cada operación tiene un icono distinto (el swap pasa de
  `ArrowRightLeft`, duplicado con la transferencia, a `Repeat`); la sección
  1 usa `ListChecks` en vez de `Wallet` y la comparativa `Scale` en vez de
  `TrendingDown`. Si faltan unidades o precio de ETH, la comparativa muestra
  el estado vacío en vez de operaciones a 0 ETH/$0,00. Favicon propio y
  `.gitignore` añadidos (G-10).
- **Verificaciones (triple):** 1) Build ✅ (el mismo de GAS-C3-1).
  2) Smoke ✅: iconos de `OPERATIONS` extraídos del código = 5 distintos;
  texto del estado vacío de la comparativa presente en el bundle (1).
  3) Detalle ✅: ortografía de los textos nuevos revisada; README con
  sección «Mejoras de detalle (Ciclo 3)» veraz; favicon presente en `dist/`
  y enlazado en `index.html`; sin servidores al final.
  Medias restantes de gas-calc tras este ciclo: ninguna (G-3/G-4/G-9/G-6 ya
  cerradas en el Ciclo 1, G-2 en GAS-A2; GR-1/GR-2 de grupo quedan fuera).

## 2026-11-02 · Fase 2, Ciclo 4 — Coherencia visual (GR-1): firma de cabecera

- **Gesto:** curva de precio del gas en el hero (`.sig-gascurve`): SVG decorativo `aria-hidden` con polilínea violeta y punto dorado en el pico, entre el párrafo del hero y la nota. Solo presentación: 1 SVG JSX + 3 reglas CSS; lógica, datos y textos funcionales intactos.
- **Verificación 1 (build):** `npm run build` → exit 0.
- **Verificación 2 (sirve + smoke):** `dist/` servido en local → index 200 y asset JS 200. Smoke aritmético del flujo principal: 150.000 gas × 25 gwei × 10⁹ = 3.750.000.000.000.000 wei = 0,00375 ETH (corrección de Ciclo 1 intacta).
- **Verificación 3 (contenido + comparación):** bundle con `sig-gascurve` ×4 y «un trillón de wei» ×1 y «Datos de ejemplo» ×1 intactos. JS 164.069 → 164.386 B (+317 B, el SVG) y CSS 6.548 → 6.708 B. `VITE_*` = 0.

## 2026-11-02 · Fase 2, Ciclo 8 — Suelo de tests para el cálculo de gas

### [Tests · Red permanente] `scripts/verify-data.mjs` + «npm test» (patrón de block-explorer/nft-studio, Ciclo 7)

- **Adaptación honesta del patrón:** en esta app NO hay módulo de datos importable: toda la lógica (resultado, comparativa, `clamp`, `Field`) vive en `src/App.jsx`. El script aplica el patrón de ancla de nft-studio sin fingir ningún import: (1) el fuente debe contener las fórmulas y guardas exactas (`wei = BigInt(Math.round(u * g)) * 1000000000n`, `eth = (u * g) / 1e9`, `usd: eth * e`, la fórmula de la comparativa, la definición de `clamp` y las dos ramas del `onBlur` del `Field`, con el `onChange` en crudo sin clamp); (2) los datos de operaciones, presets, rangos de campos y **el propio factor wei/gwei se extraen del fuente** con expresiones regulares y alimentan los cálculos — si el factor cambia en la app, las cifras dejan de cuadrar además de romperse el ancla —; y (3) el `clamp` anclado se aplica a valores de borde. Todo declarado en la cabecera del script.
- **Cambio:** creado `scripts/verify-data.mjs`, que comprueba en **47 comprobaciones**: las 8 anclas de fórmulas/guardas; datos extraídos del fuente íntegros (5 operaciones —transfer, token, swap, mint, deploy— con 21.000/65.000/150.000/120.000/800.000 gas; 3 presets con 12/25/45 gwei; rangos UI: gas 1–300, ETH 1–100.000 USD, unidades 21.000–5.000.000); **wei exacto con el factor ×10⁹** (corrección GAS-A1 del Ciclo 1 como red permanente: por defecto 150.000 × 25 = **3.750.000.000.000.000 wei** con su formato es-ES, 1 × 1 gwei = 10⁹ wei, 1.000.000 × 1.000 gwei = 10¹⁸ wei = 1 ETH exacto); coherencia ETH/USD (0,00375 ETH y 9 $ por defecto; el paso 2 impreso, wei ÷ 10¹⁸, da el mismo ETH); matriz completa operaciones × presets (15 combinaciones coherentes en wei/ETH/USD); **sin desbordes en los rangos de la UI** (esquina mínima 21.000 × 1 gwei = 21.000.000.000.000 wei; esquina máxima 5.000.000 × 300 gwei = 1.500.000.000.000.000.000 wei exactos en BigInt = 1,5 ETH, por debajo de 2⁶³); y el ajuste al salir del campo (5 → 21.000, 6.000.000 → 5.000.000, 50.000 intacto, gas ajustado a 1–300; regresión permanente de GAS-A2). Añadido `"test": "node scripts/verify-data.mjs"` a `package.json`. Sin dependencias nuevas. El script sale con código 0 si todo pasa y ≠0 nombrando cada invariante roto.
- **Verificación 1 (tests + build + comparación):** `npm test` → exit 0 (47/47). `npm run build` → exit 0 (Vite 6.4.5) y bundles **byte-idénticos** a los conocidos-buenos del Ciclo 4, registrados antes de empezar: JS 164.386 B, sha256 `cad53b76…` (mismo asset `index-C4DzZdZC.js`); CSS 6.708 B, sha256 `f7fc46fc…`; `index.html` 496 B, sha256 `f5418375…`. Delta cero, como corresponde: este frente no toca `src/` ni estilos (sha256 de todo `src/` idénticos antes y después del ciclo).
- **Verificación 2 (prueba de fuego en copia):** app copiada a `/tmp` (sin `node_modules`/`dist`; el test no los necesita). Control con la copia sana: `npm test` → exit 0. Rotura deliberada en la copia (factor wei de `src/App.jsx`: `* 1000000000n` → `* 1000000n`, el error original del Ciclo 1): `npm test` → **exit 1, 24 fallos** que nombran el problema exacto (el ancla del factor ×10⁹, el factor extraído «actual: 1000000», el wei por defecto «actual: 3750000000000», el formato es-ES, 1 gwei = 10⁹, 10¹⁸ = 1 ETH, el paso 2 y la matriz). Copia destruida al terminar; la app real queda intacta (sha256 de `src/` verificados tras la prueba).
- **Verificación 3 (invariantes contra el código real):** todas las cifras del script se derivaron de primera mano ejecutando las fórmulas y extrayendo los datos del propio `App.jsx` antes de escribirlo (operaciones/presets/rangos parseados del fuente, wei/ETH/USD por defecto y de las esquinas, comportamiento del `clamp`), no copiadas de memoria ni de los logs.
- **README:** añadida la verificación con `npm test` a «Cómo ejecutar», con lo que comprueba. Sin etiquetas falsas: el README sigue declarando «diseño responsive con base de escritorio» (gas-calc NO es mobile-first, auditoría del Ciclo 5) y no se ha tocado esa línea.
