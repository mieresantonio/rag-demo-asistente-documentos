# Registro de mejoras — Tx Builder

## 2026-11-02 · Fase 2, Ciclo 1

### [T-A1 · ALTA · Regla dura] Direcciones canónicas de documentación sustituidas por direcciones ficticias

- **Hallazgo:** `WALLETS` y `RECIPIENTS` en `src/App.jsx` usaban direcciones canónicas de la documentación de Ethereum/ethers que existen en mainnet (`0x71C7656…`, `0x3f5CE5…`, `0xde0B29…`, `0x742d35…`, `0xAb5801…`), presentadas como carteras y destinatarios de ejemplo sin advertir que son direcciones reales ajenas.
- **Cambio:** sustituidas las 5 direcciones (revisado todo el archivo de datos de la app; no había ninguna otra dirección completa) por direcciones generadas al azar para esta demo, con formato válido y sin copiar de documentación conocida:
  - Ana: `0x48227ad1d403f5c7786e9c84b0fe4553039f4678`
  - Bruno: `0x268b35c1b380c79846bcec0c8f841b89754ae498`
  - Carla: `0x4ac639dfad73e6e775c789a8cf06fa24295aded5`
  - Tienda ejemplo: `0xbc3564bffaa8d358f9dbb123526e21e8d0a0db3d`
  - Amigo ejemplo: `0x06edac506aef40e6b0e3242c67aa98f0813cba5f`
  - Añadido comentario en el código y advertencia visible de que son direcciones de ejemplo sin fondos ni uso real: en el aviso principal («Las direcciones de ejemplo de esta demo son inventadas: no tienen fondos ni uso real; no envíes fondos reales a ninguna de ellas») y en las ayudas de los pasos 1 y 2.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 5.4.21, JS 167,10 kB).
- **Verificación 2 (smoke funcional):** grep de las 5 direcciones antiguas en `src/` = 0 resultados, también 0 en el bundle de `dist/`; las 5 nuevas pasan la regex de la propia app (`0x` + 40 hex) y ninguna coincide con las canónicas conocidas (comprobado por comparación directa en Node); el bundle contiene las 5 nuevas.
- **Verificación 3 (checklist):** ortografía de los textos nuevos revisada (acentos correctos); sin regresiones (saldos, pasos y validaciones intactos); el README no menciona direcciones concretas, así que sigue siendo veraz.

### [T-M2 parcial · etiquetado] La etiqueta «Datos de ejemplo · Simulado» ahora aparece en cada paso y en el historial

- **Hallazgo:** el README afirmaba que la etiqueta está «en la cabecera, en el aviso principal, en cada paso y en el historial», pero en el código solo aparecía en la cabecera.
- **Cambio:** etiqueta añadida al aviso principal (inicio del párrafo), como distintivo fijo dentro de la tarjeta del constructor — visible en los 5 pasos, incluido el paso 5 de revisión — y en el panel del historial (nueva clase CSS `.sim-in-card` en `src/styles.css`).
- **Verificación 1 (build):** `npm run build` → exit 0 (misma build anterior).
- **Verificación 2 (smoke funcional):** la cadena «Datos de ejemplo» pasa de 1 a 4 apariciones en `src/App.jsx` (cabecera, aviso, tarjeta de pasos e historial) y el distintivo de la tarjeta se renderiza fuera de los condicionales de paso, por lo que se ve también en Revisión.
- **Verificación 3 (checklist):** con este cambio la afirmación del README sobre la etiqueta ya es cierta tal como está escrita; no hizo falta tocar el README. Sin cambios visuales fuera del distintivo añadido.

## 2026-11-02 · Fase 2, Ciclo 2

### [T-M1 · MEDIA · Lógica/contenido] La validación ya incluye el gas: el total (valor + gas) no puede superar el saldo sin aviso y bloqueo

- **Hallazgo:** `amountValid` solo comparaba el importe con el saldo (`amountNum <= sender.balance`); el gas se sumaba solo para mostrarlo. Con el atajo «100 % del saldo» (saldo 0,85 ETH, gas 21.000 × 20 gwei = 0,00042 ETH) el total era 0,85042 ETH > 0,85 ETH y la Revisión no avisaba ni bloqueaba, enseñando mal justo el concepto del paso 4.
- **Cambio:** en `src/App.jsx` se añaden `amountRawValid`, `exceedsBalance` (total > saldo), `missingForTotal`, `maxSendable` (saldo − gas) y `canSign` (todo válido **y** sin exceso). El paso 3 avisa en cuanto el importe + gas estimado supera el saldo y muestra el máximo enviable; el paso 4 muestra valor, gas, total y saldo en la caja de cálculo con error si hay exceso; el paso 5 (Revisión) muestra el desglose explícito «importe + gas = total» junto al saldo disponible y, si el total supera el saldo, un aviso destacado (`role="alert"`, nueva clase `.over-balance` en `src/styles.css`) con lo que falta y cómo corregirlo, con el botón «Firmar (simulado)» deshabilitado (`disabled={!canSign}`) y guarda en `sign()`. README actualizado: la sección «Validación» ahora incluye el control del total.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 5.4.21, JS 168,72 kB).
- **Verificación 2 (smoke con lógica ejecutada):** en Node con saldo 0,85, importe 0,85 y gas por defecto: coste de gas = 0,00042 ETH, total = **0,85042 ETH**, `exceedsBalance = true`, faltan 0,00042 ETH, máximo enviable = 0,84958 ETH y `canSign = false` (firma bloqueada). Caso de control: importe 0,5 ETH → total 0,50042 ETH, sin exceso.
- **Verificación 3 (checklist + contenido del bundle + comparación):** ortografía de los textos nuevos revisada (acentos correctos: «superaría», «máximo»); sin regresiones (pasos, saldos e historial intactos; navegación hasta Revisión permitida para poder ver el aviso, el bloqueo actúa sobre la firma). **Contenido del bundle verificado por cadenas decisivas** en `dist/assets/*.js`: «Saldo insuficiente para el total» ×1, «Total estimado (valor + gas)» ×2, «Saldo disponible» ×2, «La firma está bloqueada» ×1, y vistas presentes («Revisa antes de firmar», «Historial local», «Firmar (simulado)», «Transmitir (simulado)» ×1 cada una). **Comparación contra el último build conocido-bueno** (Ciclo 1: 167,10 kB): 168,82 kB en disco, **+1,03 %**, explicado por la lógica y los textos nuevos de T-M1; sin desviaciones sin explicación. Sin variables de entorno en `src/` ni en `vite.config.js`: el build es autónomo y no depende de ninguna variable no documentada.

## 2026-11-02 · Fase 2, Ciclo 3

### [T-B4 · BAJA · Lógica] «¡Copiado!» solo si la copia tuvo éxito + [T-B3] `.gitignore`

- **Hallazgo:** `copy()` tragaba el error del portapapeles (`catch(() => {})`) y confirmaba «¡Copiado!» siempre; además la app no tenía `.gitignore` (mismo patrón transversal T-2/T-3 del diagnóstico).
- **Cambio:** `copy()` es ahora asíncrona y solo marca `copied` tras un `writeText` resuelto; sin portapapeles o con error, no se muestra ninguna confirmación. Añadido `.gitignore` estándar (el mismo de nft-studio: `node_modules`, `dist`, logs y editores).
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 5.4.21, JS 168,74 kB).
- **Verificación 2 (smoke):** bundle con «¡Copiado!» ×1 (la confirmación sigue existiendo para el éxito) y el patrón viejo `catch(()=>{})` ×0; la guarda `if (!navigator.clipboard) return` está en el código.
- **Verificación 3 (checklist + comparación):** sin regresiones (T-A1 y T-M1 de Ciclos 1–2 intactos: el aviso de saldo/total y las direcciones inventadas no se tocaron). **Comparación contra el último build conocido-bueno** (Ciclo 2: 168,72 kB): 168,74 kB, **+0,01 %**, explicado por la guarda de copia. Sin variables `VITE_*`: build autónomo.

## 2026-11-02 · Fase 2, Ciclo 4 — Coherencia visual (GR-1): firma de cabecera

- **Gesto:** ruta origen→destino en la cabecera (`.sig-route`, `aria-hidden`, oculta ≤560 px): punto violeta, línea punteada y punto dorado de llegada — el viaje de la transacción que la app construye paso a paso. Solo presentación: 1 span JSX decorativo + reglas CSS; lógica, datos y textos funcionales intactos.
- **Verificación 1 (build):** `npm run build` → exit 0.
- **Verificación 2 (sirve + smoke):** `dist/` servido en local → index 200 y asset JS 200; el constructor de 5 pasos no se tocó.
- **Verificación 3 (contenido + comparación):** bundle con `sig-route` ×10 y cadenas decisivas intactas: «Datos de ejemplo» ×4 y la dirección inventada de Ciclo 1 `0x48227ad1…4678` ×1 (sin direcciones canónicas de mainnet). JS 168.836 → 169.053 B (+217 B) y CSS 8.385 → 8.842 B. `VITE_*` = 0.
