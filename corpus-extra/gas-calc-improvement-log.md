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
