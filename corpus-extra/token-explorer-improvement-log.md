# Improvement log — token-explorer

> Nota: esta app no tuvo entrada en el Ciclo 1 (en el grupo A solo hash-lab
> cerró un hallazgo, HASH-A1). Este fichero nace con el Ciclo 2. Los
> nombre/símbolo anteriores del token renombrado no se reproducen aquí a
> propósito: el grep del símbolo viejo debe seguir dando 0 en toda la app.

## 2026-11-02 · Fase 2, Ciclo 2

### TOKEN-C2-1 (T-1) — Renombrado el token que colisionaba con uno real
- **Hallazgo:** el token nº 9 usaba el nombre y el símbolo de un token
  real y conocido (Quant), pese a declararse inventado: un alumno que lo
  buscara aterrizaba en el activo real creyendo que era este.
- **Cambio:** token nº 9 renombrado a **Zorqbix (ZQBX)**, nombre y símbolo
  inventados sin colisión conocida: comprobado con búsquedas públicas
  dirigidas al símbolo exacto en índices de criptomonedas (sin resultados
  para ese símbolo; los candidatos alternativos descartados sí mostraron
  colisiones o parecidos con tickers existentes). Precio, suministro,
  capitalización y demás datos simulados no cambian (la coherencia
  precio × suministro = capitalización se mantiene). README alineado.
- **Verificaciones (triple):**
  1. `npm run build` ✅.
  2. Smoke en Node ✅: `TOKENS` sigue teniendo 12 entradas, el nº 9 es
     Zorqbix/ZQBX y la coherencia numérica se mantiene en los 12; grep
     del símbolo y del nombre viejos = **0** en `src/`, `README.md`,
     `index.html` y en el bundle `dist/` construido.
  3. Detalle/contenido ✅: cadenas decisivas dentro del bundle —
     «ZQBX» (1) y «Zorqbix» (1) presentes, símbolo/nombre viejos (0);
     comparación contra el build anterior conocido-bueno (JS 161.218 B):
     JS nuevo 161.586 B (+368 B, explicado por la función de contraste
     de TOKEN-C2-2) y misma estructura (index.html + 1 JS + 1 CSS, misma
     única vista). Build servida un momento: HTTP 200 y asset nuevo
     referenciado. Sin dependencias de variables de entorno
     (`import.meta.env`/`VITE_*` = 0 en la app).

### TOKEN-C2-2 (T-3) — Contraste de avatares ≥4,5:1 en los 12 tokens
- **Hallazgo:** `.avatar` fijaba texto blanco sobre los colores de cada
  token; 5 de los 12 quedaban entre 1,92:1 y 2,28:1, por debajo incluso
  del 3:1 de texto grande.
- **Cambio:** `avatarTextColor(bg)` en `src/data.js` calcula la
  luminancia relativa (WCAG) del color del token y elige texto negro o
  blanco, el de mayor contraste (matemáticamente, el mejor de ambos
  extremos siempre alcanza ≥4,5:1; los colores de marca no se tocan).
  Aplicado en la lista y en el detalle. `contrastRatio` queda exportada
  para poder verificarlo.
- **Verificaciones (triple):**
  1. `npm run build` ✅.
  2. Smoke en Node ✅: recalculados los 12 pares (fondo, texto elegido):
     **12/12 ≥4,5:1**, mínimo 4,96:1 (W3C); los 5 señalados quedan en
     9,78:1 (SLN), 9,22:1 (ECO), 10,95:1 (VELA), 9,80:1 (BRS) y
     10,63:1 (TRR) con texto negro.
  3. Detalle/contenido ✅: README con sección «Accesibilidad» veraz con
     las cifras anteriores y posteriores; ortografía revisada; sin
     regresiones (filtros, ordenación y gráfica no se tocaron); sin
     servidores al final.

## 2026-11-02 · Fase 2, Ciclo 3

### TOKEN-C3-1 (T-4 + T-6c + T-7) — Sin copiar la dirección falsa, gráfica y reparto claros
- **Cambio:** retirada de la ficha el botón «Copiar dirección de ejemplo»
  que contradecía su propio aviso «EJEMPLO FALSO, no usar», con una nota que
  lo explica («Sin botón de copiar a propósito…»); con ello desaparece
  también su confirmación de copia sin comprobar (patrón H-5/W-6). La
  sparkline recibe el nombre del token y su `aria-label` lo incluye.
  La distribución de tenedores añade la nota de reparto ilustrativo por
  grupos que pueden solaparse en un token real.
- **Verificaciones (triple):** 1) `npm run build` ✅. 2) Smoke en Node ✅:
  12 tokens, coherencia precio×suministro = capitalización en los 12
  (con tolerancia de coma flotante) y contrastes de avatar 12/12 ≥4,5:1
  (regresión TOKEN-C2-2). 3) Detalle ✅: cadenas en el bundle —
  «Sin botón de copiar a propósito» (1), «Reparto ilustrativo» (1),
  «Copiar dirección de ejemplo» (0); imports `Copy`/`Check` y el estado
  `copied` retirados al quedar sin uso; README actualizado; sin servidores.

### TOKEN-C3-2 (T-8 + T-9 + T-10) — «mil millones», «Órbita» e higiene
- **Cambio:** `fmtCompact` ya no produce «$3,32 mil M»: para ≥10⁹ devuelve
  «$3,32 mil millones» con decimales en formato español (vía
  `toLocaleString('es')`). El token 8 pasa de «Orbita» a «Órbita».
  Favicon propio y `.gitignore` añadidos (T-10).
- **Verificaciones (triple):** 1) Build ✅. 2) Smoke ✅: `fmtCompact` sobre
  la capitalización total real de los datos = «$3,32 mil millones»;
  símbolo del token 9 sigue siendo ZQBX (regresión TOKEN-C2-1: nombre y
  símbolo viejos = 0 en el bundle). 3) Detalle ✅: comparación V3 contra
  el último build conocido-bueno (JS 161.586 B): JS nuevo 161.440 B
  (−146 B, explicado: se retira más código de copia del que se añade) y
  misma estructura + favicon nuevo; «mil M» (0) y «Orbita» sin tilde (0)
  en el bundle; «Órbita» (1); `VITE_*` = 0. Pendientes: T-2 (MEDIA, foco al
  entrar/salir del detalle) y T-5 (tarjetas-`<button>` con `<div>`) —
  fuera del alcance de bajas seguras de este ciclo.

## 2026-11-02 · Fase 2, Ciclo 4

### TOKEN-C4-1 (T-2) — El foco entra al detalle y vuelve a su tarjeta
- **Hallazgo:** `select()` desmontaba la tarjeta pulsada y el foco caía
  al `body` al entrar en el detalle, y lo mismo al volver: un usuario de
  teclado/lector tenía que re-recorrer la página en cada ida y vuelta.
- **Cambio:** gestión explícita del foco en `App.jsx`. Al abrir, un
  `useEffect` sobre `selected` lleva el foco al título del detalle
  (`detailTitleRef` sobre el nombre del token, con `tabIndex={-1}`).
  `select(t)` guarda el id del token en `returnToIdRef`, y cada botón
  «Ver detalle» se registra en `triggerRefs` (Map id → elemento): como
  la tarjeta se desmonta en el detalle, al volver (`goBack`) el efecto
  localiza el botón recién remontado de esa misma tarjeta y le devuelve
  el foco — no se guarda el nodo DOM, que quedaría obsoleto. README
  alineado (sección «Accesibilidad»).
- **Verificaciones (triple):** 1) `npm run build` ✅ (ver TOKEN-C4-2).
  2) Smoke en Node ✅: comprobación en código de la navegación ida y
  vuelta (17/17 en total con T-5 y datos): refs declarados
  (`detailTitleRef`, `triggerRefs`, `returnToIdRef`), título enfocable
  y enfocado al abrir, `select` guarda el id, `goBack` deselecciona y el
  efecto enfoca el disparador guardado; datos: 12 tokens y coherencia
  precio × suministro = capitalización en los 12; regresión de
  contraste de avatar 12/12 ≥4,5:1. 3) Detalle ✅: ver TOKEN-C4-2.

### TOKEN-C4-2 (T-5) — Tarjetas `<article>` con botón interno válido
- **Hallazgo:** cada tarjeta era un `<button>` que contenía múltiples
  `<div>` y un `<svg>`: contenido de un botón debe ser solo fraseado, y
  el nombre accesible salía de todo el texto de la tarjeta.
- **Cambio:** la tarjeta pasa a `<article className="card">` con el
  mismo contenido y las mismas clases (avatar, precio, variación, meta
  y sparkline intactos) y un único elemento interactivo al pie: un
  botón «Ver detalle» (clase `.card-detail`, solo texto fraseado) con
  `aria-label="Ver detalle de {token}"`, que es además el disparador al
  que regresa el foco de TOKEN-C4-1. El aspecto no cambia salvo ese
  botón al pie, en el estilo de los paneles existentes. Verificado en
  código que ningún `<button>` de la app contiene ya un `<div>`
  (volver, chips, limpiar y «Ver detalle»: todos solo texto/icono).
- **Verificaciones (triple):** 1) `npm run build` ✅ (build repetido a
  `/tmp` con hash idéntico al `dist/` en disco). 2) Smoke ✅ (ver
  TOKEN-C4-1). 3) Detalle ✅: cadenas en el bundle en disco — «Ver
  detalle» (2), «Ver detalle de» (1), «card-detail» (1). Comparación V3
  contra el build del Ciclo 3 (JS 161.440 B): JS nuevo 162.061 B
  (+621 B) y misma estructura (index.html + 1 JS + 1 CSS + favicon).
  Nota: durante este ciclo el frente paralelo de cabecera/hero
  reconstruyó la app, así que parte del delta (sobre todo en CSS:
  4.164 → 5.106 B) es suyo; las cadenas decisivas de estos cambios
  están verificadas en el bundle final. `VITE_*` = 0 en `src/`; sin
  servidores al final. Alcance: no se tocaron estilos ni estructura de
  cabecera/hero.

## 2026-11-02 · Fase 2, Ciclo 4 — Coherencia visual (GR-1): firma de cabecera

- **Gesto:** tira de velas de precio (candlesticks) en el hero, sobre las estadísticas (`.sig-candles`, `aria-hidden`): 8 velas verdes/rojas de alturas variables con mecha, el lenguaje visual de un explorador de mercados. Solo presentación: 1 div JSX decorativo + reglas CSS; lógica, datos y textos funcionales intactos por este frente.
- **Verificación 1 (build):** `npm run build` → exit 0.
- **Verificación 2 (sirve + smoke):** `dist/` servido en local → index 200 y asset JS 200; búsqueda, ordenación y detalle no se tocaron en este frente.
- **Verificación 3 (contenido + comparación):** bundle con `sig-candles` ×12 y cadenas decisivas intactas: `ZQBX` ×1 (símbolo sustituto de Ciclo 2) y «Datos de ejemplo» ×2. JS 161.440 → 162.061 B (+621 B): incluye cambios concurrentes de otro frente detectados por diff en el mismo ciclo (gestión de foco del detalle, T-2), además de las velas. CSS 4.164 → 5.106 B. `VITE_*` = 0.
