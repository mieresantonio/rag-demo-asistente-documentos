# Improvement log — wallet-sim

> Nota: esta app no tuvo entrada en el Ciclo 1 (en el grupo A solo hash-lab
> cerró un hallazgo, HASH-A1). Este fichero nace con el Ciclo 2.

## 2026-11-02 · Fase 2, Ciclo 2

### WALLET-C2-1 (W-1 del diagnóstico) — Estado guardado validado: nada de pantalla en blanco
- **Hallazgo:** `load()` devolvía cualquier JSON parseable de `localStorage`
  sin validar forma; datos corruptos o heredados (objeto suelto, `[]`,
  saldos como texto, transacciones sin `time`) rompían el render o el
  ordenado del historial.
- **Cambio:** nueva `src/state.js` (lógica pura, sin React ni DOM) con
  validadores de esquema (`isValidWallet(s)`, `isValidTx(s)`) y
  `loadStoredState(getItem)`: si el estado guardado no cumple el esquema,
  se descarta TODO, se arranca limpio con las carteras de ejemplo y la UI
  muestra un aviso visible (`role="alert"`: «Los datos guardados… no
  tenían el formato esperado… se han descartado»). Un estado válido se
  conserva intacto.
- **Verificaciones (triple):**
  1. `npm run build` ✅.
  2. Smoke en Node ✅ (13 bloques): 6 variantes corruptas descartadas con
     arranque limpio y carteras renderizables (saldo numérico, historial
     ordenable); sin estado → semillas sin aviso; estado válido → se
     conserva tal cual. Build servida un momento: HTTP 200 y asset nuevo
     referenciado.
  3. Detalle/contenido ✅: cadenas decisivas dentro del bundle —
     «no tenían el formato esperado» (1), «walletsim-wallets» (1);
     comparación contra el build anterior conocido-bueno (JS 160.419 B):
     JS nuevo 162.452 B (+2.033 B, explicado por `state.js`: validación +
     aritmética entera) y misma estructura (index.html + 1 JS + 1 CSS,
     misma única vista). Sin dependencias de variables de entorno
     (`import.meta.env`/`VITE_*` = 0 en la app): no aplica el riesgo de
     build dependiente de variables no documentadas.

### WALLET-C2-2 (W-3) — Cartera nueva a 0; faucet explícito y etiquetado
- **Hallazgo:** crear una cartera la dotaba de un saldo aleatorio de
  0,5–5 test ETH, concepto falso (una cartera real nace a 0) y sin
  explicar en la UI ni en el README.
- **Cambio:** `createWalletData()` crea siempre con `balance: 0`. Textos
  alineados: pista bajo el formulario («Una cartera nueva empieza con
  0 test ETH…»), mensaje de creación («creada con 0 test ETH…») y el botón
  de recepción pasa a llamarse «Recibir fondos de ejemplo (faucet
  simulado)», única vía de saldo para carteras creadas. README actualizado.
- **Verificaciones (triple):**
  1. `npm run build` ✅.
  2. Smoke en Node ✅: cartera nueva = 0 exacto; el faucet suma lo
     esperado (0 + 0,35 + 0,35 = 0,7 exactos vía `applyCredit`).
  3. Detalle/contenido ✅: cadenas en el bundle — «Recibir fondos de
     ejemplo (faucet simulado)» (1), «creada con 0 test ETH» (1),
     «Una cartera nueva empieza con 0 test ETH» (1), «Fondos de ejemplo
     recibidos» (1); ausencias verificadas: «creada con saldo de ejemplo»
     (0) y el texto viejo del botón (0); sin resto del patrón
     `0.5 + Math.random() * 4.5` en el código.

### WALLET-C2-3 (W-4) — Precisión interna entera: enviar/recibir conserva el total
- **Hallazgo:** origen y destino se ajustaban con `toFixed(4)` pero la
  transacción guardaba el importe sin redondear: enviar 0,12345 creaba
  0,0001 test ETH de la nada y el movimiento mostrado no cuadraba.
- **Cambio:** la aritmética se hace en subunidades enteras (10¹² por
  test ETH, como wei/ETH) en `applyTransfer`/`applyCredit` de
  `state.js`; el importe efectivo aplicado es idéntico en origen,
  destino y registro de la transacción. El redondeo queda SOLO en la
  presentación (`toFixed(4)` en saldos mostrados). La comprobación de
  fondos insuficientes también compara en subunidades.
- **Verificaciones (triple):**
  1. `npm run build` ✅.
  2. Smoke en Node ✅: caso del diagnóstico (2,45 → enviar 0,12345 →
     0,75) deja 2,32655 / 0,87345 con total 3,2 exacto (antes 3,2001);
     enviar el saldo completo deja exactamente 0 (`Object.is(…, 0)`);
     envío a destino externo descuenta el importe exacto.
  3. Detalle/contenido ✅: `state.js` no contiene ningún `toFixed` sobre
     saldos (los 4 `toFixed(4)` restantes en `App.jsx` son solo de
     visualización); ortografía de los textos tocados revisada; README
     con sección nueva «Precisión y estado guardado» veraz; sin
     servidores al final.

## 2026-11-02 · Fase 2, Ciclo 3

### WALLET-C3-1 (W-5 + W-6 + W-7 + W-9) — Feedback y estados que dicen la verdad
- **Cambio:** `createMsg` pasa a `{kind, text}`: el error de crear sin
  nombre se pinta con `.msg.error` y `role="alert"` (antes siempre en
  verde `.msg.ok`); el éxito usa `role="status"` (W-5). `copy()` solo
  muestra «Copiada» si el portapapeles aceptó el texto; si no hay API o
  falla, muestra «No se pudo copiar» (W-6). Cartera seleccionada y filtros
  del historial llevan `aria-pressed` (W-7). El mensaje de creación anuncia
  que la cartera nueva «queda seleccionada y también como cartera origen
  del formulario de envío» (W-9, antes era un cambio silencioso).
- **Verificaciones (triple):** 1) `npm run build` ✅. 2) Smoke ✅: regresión
  del Ciclo 2 ejecutando `state.js` en Node — enviar 0,12345 conserva el
  total 3,2 exacto, cartera nueva = 0 y estado corrupto descartado;
  `aria-pressed` ×2 en el código (carteras y filtros) y textos nuevos en
  el bundle («No se pudo copiar» 1, «Queda seleccionada y también como
  cartera origen» 1). 3) Detalle ✅: comparación V3 contra el último build
  conocido-bueno (JS 162.452 B): JS nuevo 163.139 B (+687 B) y misma
  estructura + favicon nuevo; sin restos de «creada con saldo de ejemplo»
  (0); `VITE_*` = 0 en `src/`; README actualizado; sin servidores.

### WALLET-C3-2 (W-8 + W-10) — Formato uniforme del historial e higiene
- **Cambio:** los importes del historial se muestran con formato español
  uniforme (`toLocaleString('es-ES')`, 2–5 decimales: «0,25», «1,00»,
  «0,12345») y la cabecera del historial aclara que el historial inicial es
  ilustrativo y no reconstruye los saldos de ejemplo sumando solo sus dos
  movimientos. Favicon propio y `.gitignore` añadidos (W-10).
- **Verificaciones (triple):** 1) Build ✅. 2) Smoke ✅: el formato
  ejecutado en Node produce «0,25» / «1,00» / «0,12345». 3) Detalle ✅:
  ortografía revisada; el cálculo interno no se tocó (la precisión entera
  del Ciclo 2 queda intacta, verificado en WALLET-C3-1); favicon en
  `dist/` y enlazado. Pendiente no abordado: W-2 (MEDIA, direcciones con
  formato válido) — fuera del alcance de bajas de este ciclo.

## 2026-11-02 · Fase 2, Ciclo 4

### WALLET-C4-1 (W-2) — Etiqueta «demo» persistente junto a cada dirección
- **Hallazgo:** `fakeAddress()`/`fakeHash()` generan cadenas con formato
  plenamente válido (`0x` + 40/64 hex): fuera de contexto (captura,
  portapapeles) el dato perdía su etiqueta de simulado y podía parecer
  una dirección operativa. No se falsea el formato (la enseñanza es que
  se vea cómo es una dirección), así que la mitigación es de
  presentación, no de datos.
- **Cambio:** etiqueta visible y persistente «Dirección demo — generada
  localmente, no operativa» (clase `.demo-note`, en dorado) pegada a la
  dirección en los tres sitios donde la UI muestra direcciones: la lista
  de carteras (dentro de cada tarjeta-cartera, bajo la dirección
  completa), el detalle de la cartera seleccionada (junto a la dirección
  y al botón de copiar, que ya se llamaba «Copiar dirección simulada») y
  el historial (sufijo «— dirección demo» tras cada contraparte). En la
  lista se usa un `<span>` (contenido fraseado) para no añadir más
  elementos de bloque dentro del `<button>` de cartera. La dirección se
  sigue mostrando completa y el banner global de simulación no cambia.
  README alineado (sección de seguridad).
- **Verificaciones (triple):**
  1. `npm run build` ✅ (build repetido a `/tmp` con hash idéntico al
     `dist/` en disco: el `dist/` presente está al día con el `src/`).
  2. Smoke en Node ✅ (regresión de `state.js`, 11/11): enviar 0,12345
     conserva el total 3,2 exacto (2,32655 / 0,87345); enviar el saldo
     completo deja exactamente 0 (`Object.is`); cartera nueva = 0;
     faucet 0 + 0,35 + 0,35 = 0,7; estado corrupto descartado con
     arranque limpio; estado válido conservado. La lógica de saldos no
     se tocó en este ciclo.
  3. Detalle/contenido ✅: cadenas en el bundle en disco — «Dirección
     demo» (2: lista y detalle), «generada localmente, no operativa»
     (2), «dirección demo» (1: historial), «demo-note» (2 entre JS/CSS).
     Comparación V3 contra el build del Ciclo 3 (JS 163.139 B): JS nuevo
     163.425 B (+286 B) y misma estructura (index.html + 1 JS + 1 CSS +
     favicon). Nota: durante este ciclo el frente paralelo de
     cabecera/hero reconstruyó la app, así que parte del delta de tamaño
     (sobre todo en CSS: 4.168 → 4.585 B) es suyo; las cadenas decisivas
     de este cambio están verificadas en el bundle final. `VITE_*` = 0
     en `src/`; sin servidores al final. Alcance: no se tocaron estilos
     ni estructura de cabecera/hero.

## 2026-11-02 · Fase 2, Ciclo 4 — Coherencia visual (GR-1): firma de cabecera

- **Gesto:** chip tipo tarjeta bancaria junto al logo de la cabecera (`.sig-chip`, `aria-hidden`): rectángulo dorado con marco interior, el objeto que una wallet custodia. Solo presentación: 1 elemento JSX vacío + 2 reglas CSS; lógica, datos y textos funcionales intactos por este frente.
- **Verificación 1 (build):** `npm run build` → exit 0.
- **Verificación 2 (sirve + smoke):** `dist/` servido en local → index 200 y asset JS 200; la funcionalidad (carteras, envíos, historial) no se tocó en este frente.
- **Verificación 3 (contenido + comparación):** bundle con `sig-chip` ×3 y cadenas decisivas intactas («SIMULADO», «Datos de ejemplo»). JS 163.139 → 163.425 B (+286 B) y CSS 4.168 → 4.585 B: la desviación incluye, además del chip, cambios concurrentes de otro frente detectados por diff en el mismo ciclo (notas «Dirección demo» de W-2), no atribuibles a esta firma. `VITE_*` = 0.
