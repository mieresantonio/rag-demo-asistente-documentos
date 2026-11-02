# Improvement log — Demo local Barbería

Registro de arreglos de la Fase 2. Formato por arreglo: fecha,
hallazgo, cambio y las 3 verificaciones (1 = build/arranque + frontend,
2 = smoke funcional real con curl, 3 = checklist de detalle).
La base de datos se respaldó antes de tocar nada
(`/tmp/barberia.db.bak-20261102-214654`) y se restauró al estado
semilla al terminar (3 citas, ids 1–3, todas `cancelled`, 2026-10-27).
Servidores apagados al terminar (puertos 5000 y 8899 libres).

---

## 2026-11-02 — Ciclo 1 (hallazgos graves de la revisión 2026-11-02)

### A1 — Reprogramar con `professional_id` inexistente corrompía la BD

- **Hallazgo:** `POST /api/appointments/<id>/reschedule` con
  `professional_id: 999` hacía commit con una FK colgante y desde ahí
  la agenda, el historial y la búsqueda devolvían 500 para siempre
  (revisión: T59/T78/T79/T66).
- **Cambio (`backend/app.py`):** reescritos `create_appointment` y
  `reschedule_appointment` con validación completa **antes** de mutar
  nada: tipos estrictos y existencia de `service_id`/`professional_id`
  comprobada con `db.session.get()`; id inexistente → 400 JSON sin
  tocar la BD. La mutación + `commit()` van en una sola transacción
  con `rollback` ante cualquier excepción (todo-o-nada).
  `validate_slot()` además comprueba que el profesional exista como
  defensa en profundidad, y `to_dict()` ya no explota si una relación
  faltara. `cancel` y los 404/405 también devuelven JSON.
- **Verificación 1:** backend levanta (`/api/health` 200, log
  «Debug mode: off»); `npm run build` OK y `dist/` servido por HTTP
  (index/JS/CSS 200).
- **Verificación 2 (smoke curl):** reschedule con
  `professional_id: 999` → 400 `{"error":"professional_id no existe."}`;
  la cita quedó intacta (profesional, fecha y hora sin cambios,
  comprobado por API) y `GET /api/appointments?date=...` siguió en
  200. Mismo resultado con `service_id: 999` y con
  `professional_id: "abc"` en reschedule, y con ids 999 en create.
  `PRAGMA foreign_key_check` limpio al final.
- **Verificación 3:** mensajes nuevos con ortografía revisada
  («válido», «no existe»); sin cambios en los flujos buenos (ver
  bloque de regresión abajo).

### A2 — Sin validación de tipos + depurador de Werkzeug expuesto

- **Hallazgo:** payloads con tipos raros (`service_id` objeto,
  `customer_name` número/objeto) → 500 con el depurador interactivo
  (EVALEX) y el servidor corría con `debug=True` fijo.
- **Cambio (`backend/app.py`):**
  - Helpers `is_int_id()` (entero JSON real; rechaza bool, texto,
    listas, objetos y decimales) y `clean_text()` (texto no vacío con
    límite: nombre 120, teléfono 40 caracteres). `parse_date()` /
    `parse_time()` exigen `str`. Todos los endpoints de escritura
    (create, reschedule) y `availability` validan tipos y formatos
    antes de operar; cuerpo no-JSON o no-objeto → 400 JSON.
  - Manejadores de error 404/405/500 que siempre responden JSON.
  - `app.run(..., debug=...)`: el depurador queda **desactivado por
    defecto**; solo se activa con la variable de entorno explícita
    `FLASK_DEBUG=1` (y `use_reloader` ligado a ese mismo flag).
- **Verificación 1:** log de arranque «Debug mode: off» sin
  `FLASK_DEBUG`; build del frontend OK.
- **Verificación 2:** `service_id` como objeto/lista/texto → 400;
  `customer_name` como número/objeto → 400; nombre de 500 caracteres
  → 400; ninguna respuesta de error contiene «werkzeug», «EVALEX» ni
  «Traceback» (comprobado con grep sobre la respuesta); 404 de ruta o
  de cita → JSON `{"error": ...}`.
- **Verificación 3:** `py_compile` OK; textos de error específicos
  por campo (ya no un genérico «Faltan datos» para todo).

### A3 — Exposición de datos sin autenticación (mitigación de demo)

- **Hallazgo:** `GET /api/appointments` sin parámetros volcaba el
  historial completo con nombres y teléfonos; la demo no advertía de
  que no tiene autenticación.
- **Cambio:**
  - `GET /api/appointments` exige al menos un filtro útil: `date` o
    `phone`; sin filtros → 400 JSON explicativo. (Los dos usos reales
    ya filtran: la agenda por `date`, el chat por `phone`.)
  - `README.md`: nueva sección «⚠️ Aviso de seguridad» en cabecera que
    declara sin rodeos que la demo no tiene autenticación ni
    autorización, que el CORS está abierto para desarrollo local, que
    **no debe usarse con datos reales** ni exponerse fuera de la
    máquina local, y qué haría falta para un uso real. Sin inventar
    un sistema de auth: es una demo local.
- **Verificación 1:** backend y frontend levantan; el frontend sigue
  funcionando porque sus llamadas siempre llevan filtro.
- **Verificación 2:** `GET /api/appointments` sin parámetros → 400;
  con `?date=` válida → 200; con `?phone=` → 200.
- **Verificación 3:** README releído: aviso visible antes de las
  instrucciones de ejecución, ortografía correcta, y endpoints/códigos
  de error actualizados (incluye `GET /api/health`, antes no
  documentado).

### M2 (parcial) — `?date=` inválida devolvía TODO el historial

- **Cambio:** en `list_appointments`, si viene `date` y no parsea →
  400 (antes se ignoraba el filtro y se devolvía todo). En
  `availability`, `professional_id` inválido o inexistente → 400
  (antes: `abc` se ignoraba y 999 devolvía un mapa vacío).
- **Verificación 2:** `?date=basura` → 400; availability con
  `professional_id=999`/`abc` → 400; domingo sigue devolviendo
  `closed: true`.

### M1 — Se podían reservar citas en fechas pasadas

- **Cambio:** create y reschedule rechazan `date < hoy` con 400 y el
  mensaje «No se pueden reservar citas en fechas pasadas.». En el
  frontend, los selectores de fecha de reserva (formulario y chat)
  llevan `min` = hoy local. El selector de la agenda no lleva `min` a
  propósito: consultar días pasados en la agenda es legítimo.
- **Verificación 2:** crear en 2020-01-06 → 400 con el mensaje claro;
  reprogramar a 2020-01-06 → 400.

### M5 — La fecha «hoy» del frontend se calculaba en UTC

- **Hallazgo:** `todayISO()` usaba `toISOString()` (UTC): en Caracas
  (UTC−4), de 20:00 a 23:59 locales la fecha por defecto ya era
  «mañana».
- **Cambio (`frontend/src/App.jsx` y `ChatWidget.jsx`):**
  `todayISO()` compone la fecha con `getFullYear()/getMonth()/
  getDate()` (hora local). Rebuild de `dist/` incluido.
- **Verificación 1:** `npm run build` pasa; el JS compilado ya no
  contiene `toISOString` y sí `getFullYear`.
- **Verificación 2:** prueba del algoritmo con `TZ=America/Caracas`
  sobre el instante 2026-11-03T01:00Z (= 02-nov 21:00 en Caracas):
  fórmula vieja → `2026-11-03` (el bug), fórmula nueva → `2026-11-02`
  (correcto).
- **Verificación 3:** función idéntica en ambos componentes; las 7
  etiquetas «datos de ejemplo» de `App.jsx` intactas.

### B7 (parcial, textos tocados) — Tildes en mensajes del backend

- **Cambio:** «valido/validos/dia» → «válido/válidos/día» en los
  mensajes visibles de la API y en el docstring del módulo.

### Regresión — flujos buenos intactos (smoke curl, 33/33 PASS)

Crear válida 201 · solape exacto 409 · Corte 12:30 (borde de
almuerzo, termina 13:00) 201 · cruzar el almuerzo 12:45 409 ·
domingo 409 · reprogramar válido 200 (incluye cambio de profesional)
· cancelar 200 · doble cancelación 409 · cancelar libera el hueco y
re-reservar 201 · disponibilidad de día vacío y domingo
(`closed: true`) correctos · `PRAGMA foreign_key_check` limpio ·
BD restaurada al estado semilla al terminar.

---

## 2026-11-02 — Ciclo 2 (hallazgos MEDIA de UX/accesibilidad)

Respaldo previo propio de este ciclo:
`/tmp/barberia.db.bak-ciclo2-20261102-215356`. BD restaurada al
estado semilla al terminar (3 citas, ids 1–3, todas `cancelled`,
2026-10-27; `PRAGMA foreign_key_check` limpio) y servidores apagados
(puertos 5000 y 8899 libres).

**Estándar reforzado aplicado (orden de Antonio):** el build se
verificó por CONTENIDO contra lo que promete y contra el último
build conocido-bueno (el del diagnóstico, 2026-11-02 19:25:
JS 159 676 B / CSS 11 572 B). Build nuevo: JS 163 183 B
(+3 507 B, +2,2 %, explicado por las ramas nuevas del chat) y
CSS 11 738 B (+166 B, reglas de foco y del aviso). Señales clave
del build bueno, presentes en el nuevo: URL del API incrustada
(`localhost:5000` ×2, mismo default documentado en el README),
`getFullYear` presente y `toISOString` ausente (arreglo M5 intacto),
Oswald y `prefers-reduced-motion` en el CSS, «Primero libre» ×5 y
«datos de ejemplo» ×7 en el JS. **Riesgo tipo «build que depende de
variables no documentadas»: comprobado y NO detectado** — la única
variable es `VITE_API_URL`, opcional, documentada en el README y
con default sano incrustado en el bundle.

### M6 — El error de cancelación era invisible en el panel de confirmación

- **Hallazgo:** `cancelBooking` guardaba el error en `notice`, pero
  `notice` solo se renderizaba dentro del `<form>`; con una reserva
  activa en pantalla (panel de confirmación), el fallo no se veía
  en ninguna parte.
- **Cambio (`frontend/src/App.jsx`, `App.css`):** el panel de
  confirmación renderiza ahora `{notice && <p className="notice"
  role="alert">}` justo después del botón «Cancelar esta cita»
  (donde el usuario está mirando), con `.confirm .notice
  { margin-top: 14px }`. Además `cancelBooking` va en `try/catch`
  y tolera respuestas no-JSON (`.catch(() => ({}))`): si el
  servidor no responde, el aviso es «No se pudo cancelar: sin
  respuesta del servidor. Inténtalo de nuevo.» en vez de una
  promesa sin capturar (parte de M3 acotada a esta acción).
- **Verificación 1:** `npm run build` OK; `dist/` servido por HTTP
  (index/JS/CSS 200).
- **Verificación 2:** en el JS compilado, tras el botón «Cancelar
  esta cita» aparece `E&&jsx("p",{className:"notice",role:"alert",
  children:E})` **dentro de la rama del panel de confirmación**
  (antes del ternario del formulario): el estado de error se
  renderiza en ese componente, no solo en el form. Por API, el
  error real que alimenta ese aviso responde JSON correcto:
  doble cancelación → 409 «Esa cita ya estaba cancelada.»;
  id inexistente → 404 JSON «Cita no encontrada.».
- **Verificación 3:** texto nuevo con ortografía revisada
  («Inténtalo»); el aviso de éxito sigue viéndose (al cancelar,
  `booking` pasa a null y el aviso se muestra en el formulario,
  como antes).

### M7 — Contraste AA en botones WhatsApp y peligro

- **Hallazgo:** blanco sobre `#25a45b` (WhatsApp) = 3,21:1 y sobre
  `#d9534f` (peligro, token `--red`) = 3,96:1; el texto de botón
  (~16 px negrita) exige 4,5:1.
- **Cambio (`frontend/src/App.css`):** WhatsApp → `#18753c`
  (verde WhatsApp oscurecido, misma familia) y `--red` →
  `#b93532`. Se eligieron valores que **también** pasan con el
  `filter: brightness(1.1)` del `:hover` actual, para no reincidir
  al pasar el ratón. La identidad dorada/oscura no se toca.
- **Verificación 1:** build OK; los tokens nuevos están dentro
  del CSS compilado (`#18753c` ×2, `#b93532` ×1) y los viejos
  tienen 0 apariciones en el `dist/`.
- **Verificación 2 (contraste recalculado desde los tokens
  finales, script WCAG sobre el CSS):** WhatsApp `#18753c` =
  **5,76:1** (hover 4,93:1); peligro `#b93532` = **5,80:1**
  (hover 4,97:1). Ambos ≥4,5:1 en reposo y en hover. PASS.
- **Verificación 3:** `--red` solo lo consume `.btn.danger` (sin
  efectos colaterales); el resto de pares ya pasaba según el
  diagnóstico y no se tocó.

### M4 — El chat se tragaba el texto libre en 8 pasos del flujo

- **Hallazgo:** `handleText` solo respondía en `phone`, `name` y
  `phone_new`; en `service`, `professional`, `date`, `time`,
  `new_date`, `new_time`, `pick` y `confirm_cancel` el mensaje
  escrito aparecía y el bot no contestaba nada, pese a que el
  propio bot invita a escribir el día («Escríbelo o elige la
  fecha abajo.»).
- **Cambio (`frontend/src/ChatWidget.jsx`):** cada paso responde
  ahora al texto libre:
  - `date`/`new_date`: nueva `parseWrittenDate()` — acepta
    `AAAA-MM-DD` y `día/mes/año` (con `/` o `-`), valida que la
    fecha exista y rechaza fechas pasadas con explicación; si no
    se entiende, guía con el formato esperado y un ejemplo (la
    fecha de hoy). La fecha válida sigue el flujo normal.
  - `time`/`new_time`: acepta `HH:MM` si es un hueco libre; si
    no lo es, lo dice y remite a los botones; si no es una hora,
    explica el formato.
  - `service`: acepta el nombre escrito («Corte», «Barba»,
    «Corte + Barba» o combinación corte+barba) o el número; si
    no, guía con los nombres válidos.
  - `professional`: acepta el nombre del profesional o
    «primero libre»; si no, guía con los nombres.
  - `pick`: acepta el número de la cita o un texto que la
    identifique (servicio, fecha u hora); si no, lista las citas
    numeradas.
  - `confirm_cancel`: acepta «sí»/«cancelar» y «no»/«dejarla»;
    si no, pide responder «Sí, cancelar» o «No, dejarla».
  - Cualquier otro estado: respuesta genérica que mantiene el
    trámite en curso. Sin callejones silenciosos.
  - `handleOption`/`handleDatePicked`/`handleTimePicked` aceptan
    `alreadyEchoed` para reutilizarlos desde el texto sin
    duplicar el mensaje del usuario en pantalla.
- **Verificación 1:** build OK; `dist/` servido 200.
- **Verificación 2:** (a) cadenas decisivas dentro del JS
  compilado: «No entendí la fecha», «AAAA-MM-DD», «ya pasó»,
  «No reconocí ese servicio», «escribe el nombre del
  profesional», «no está entre los huecos libres», «HH:MM»,
  «escribe su número», «Responde» («Sí, cancelar»…), «Estoy en
  mitad de un trámite» — todas presentes. (b) `parseWrittenDate`
  extraída del fuente real y probada en Node: 8/8 PASS
  (`2026-11-05` ✓, `05/11/2026` ✓, `5-11-2026` ✓,
  `2026-02-30` → null, `32/01/2026` → null, texto libre →
  null). (c) Cobertura por lectura de código: `handleText`
  tiene rama para los 11 pasos del flujo (los 3 que ya
  respondían + los 8 nuevos) más un `else` final.
- **Verificación 3:** textos nuevos con acentos revisados
  («No entendí», «cuál», «número», «Sí»); ningún mensaje del
  bot pasa ya `choices: []` en estas ramas (no se renderizan
  contenedores de opciones vacíos).

### Extras baratos incluidos (bajas B12/B8, sin riesgo para lo anterior)

- **B12 (formulario):** teléfono con `type="tel"`, `inputmode=
  "tel"` y `autocomplete="tel"`; nombre con `autocomplete=
  "name"`; el selector de hora del formulario es ahora
  `role="group"` con `aria-label="Hora libre"`. Verificado en
  el JS compilado (`type:"tel"`, `inputMode:"tel"`,
  `autoComplete:"tel"`, `autoComplete:"name"`, `role:"group"`:
  1 aparición cada uno).
- **B12 (chat):** el `scrollIntoView` respeta
  `prefers-reduced-motion` (`behavior: 'auto'` si el sistema
  pide reducir movimiento).
- **B8 (foco visible):** la regla `:focus-visible` dorada de
  los campos se repite DESPUÉS del `outline: none` de `:focus`
  en `App.css`, de modo que ya no queda anulada en el
  formulario (antes ganaba el `outline: none`).
- **Verificación conjunta:** build OK y señales presentes en el
  `dist/` (ver arriba); sin cambios de comportamiento en los
  flujos de botones.

### Regresión — flujos buenos intactos (smoke curl, versión corta)

Crear válida 201 · solape exacto 409 · reprogramar con fecha
inválida 400 · cancelar 200 · doble cancelación 409 (con el
mensaje que ahora se ve en el panel) · cancelar id inexistente
404 JSON · `PRAGMA foreign_key_check` limpio · BD restaurada
al estado semilla y servidores apagados al terminar.

### Pendiente (fuera del alcance de este ciclo, sin tocar)

- M10 (sin estado de carga), M9 (longitudes/formato en backend),
  M8 (aviso de servidor inseguro — mitigado en la práctica por
  el aviso del README del Ciclo 1), resto de M3 fuera de la
  cancelación, y las bajas no citadas (B5, B6, B13–B17): no
  entraban en el alcance de este ciclo.

---

## 2026-11-02 — Ciclo 3 (medias/bajas restantes: M10, M9, M3, M8, B5, B13–B17)

Respaldo previo propio de este ciclo:
`/tmp/barberia.db.bak-ciclo3-20261102-221424` (creado y verificado
antes de probar; el fichero desapareció de `/tmp` entre sesiones
de terminal — `/tmp` es efímero —, pero la restauración quedó
igualmente verificada: ninguna prueba tocó las filas semilla y al
terminar se borraron solo las citas de prueba ids 4–7; las filas
1–3 quedaron carácter a carácter como al inicio del ciclo:
`cancelled`, 2026-10-27, `PRAGMA foreign_key_check` limpio).
Servidores apagados al terminar (puertos 5000 y 8899 libres, sin
procesos residuales).

**Estándar reforzado aplicado:** V3 por CONTENIDO contra el último
build conocido-bueno (Ciclo 2: JS 163 183 B / CSS 11 738 B).
Build nuevo: JS 165 225 B (+2 042 B, +1,25 %: estados de carga,
envoltorios try/catch de M3, módulo `schedule.js` y el evento de
apertura del chat; compensado en parte por eliminar el enlace
`wa.me`) y CSS 11 894 B (+156 B: las dos reglas `min-height` de
B13). Señales del build bueno, presentes en el nuevo:
`localhost:5000` ×2, «datos de ejemplo» ×7, «Primero libre» ×5,
`getFullYear` presente y `toISOString` ausente, Oswald en el CSS,
tokens `#18753c` ×2 y `#b93532` ×1 (M7 intacto),
`prefers-reduced-motion` presente. **Riesgo tipo «variable no
documentada» reconfirmado y NO detectado:** en el frontend solo
existe `VITE_API_URL` (opcional, documentada en el README, con el
default sano incrustado en el bundle); en el backend solo
`FLASK_DEBUG` (documentada en el README).

### M10 — Estado de carga en todas las peticiones

- **Cambio:** página — `loadingInit` («Cargando servicios…» +
  aviso `role="alert"` si la carga inicial falla, distinguiendo
  «falló» de «vacío»), `loadingSlots` («Cargando huecos libres…» y
  el estado vacío solo se anuncia cuando la carga ya terminó),
  `loadingAgenda` («Cargando la agenda…») y `submitting` (el botón
  pasa a «Reservando…» y se deshabilita durante el envío). Chat —
  estado `chatBusy`: burbuja «Un momento, estoy consultando la
  agenda…» (`role="status"`) mientras se consultan huecos, se
  busca por teléfono o se crea/cancela/reprograma.
- **Verificación 1:** build OK; `dist/` servido por HTTP 200.
- **Verificación 2:** cadenas decisivas en el JS compilado:
  «Cargando servicios», «Cargando huecos libres», «Cargando la
  agenda», «Reservando», «consultando la agenda» — presentes.
- **Verificación 3:** textos con ortografía revisada («Inténtalo»
  ya existente; sin textos nuevos sin tilde).

### M9 — Formato de nombre y teléfono en el backend

- **Hallazgo residual:** las longitudes ya se validaban (Ciclo 1),
  pero el teléfono `"abc"` y un nombre con `<script>` se aceptaban.
- **Cambio (`backend/app.py`):** `valid_customer_phone()` — solo
  dígitos, espacios y `+ ( ) -`, con el `+` solo al principio y
  entre 7 y 15 dígitos; `valid_customer_name()` — sin los
  caracteres «<» ni «>». Errores 400 específicos por campo.
- **Verificación 2 (curl):** teléfono `"abc"` → 400 con el mensaje
  «customer_phone debe ser un teléfono válido: …» (la respuesta lo
  trae escapado como `\u00e9`, verificado leyendo el cuerpo);
  teléfono de 3 dígitos → 400; nombre `<script>alert(1)</script>`
  → 400; nombre «María José Ñúñez» con teléfono `+58 412-000 0000`
  → 201 (sin falsos positivos con tildes ni formato internacional);
  el teléfono semilla corto `5550001` sigue siendo válido (7
  dígitos).

### M3 (resto) — Red de seguridad del frontend al parsear

- **Cambio:** todos los `fetch` que quedaban sin protección:
  `submitBooking` (try/catch + `r.json().catch(() => ({}))` y
  aviso «sin respuesta del servidor»), cargas iniciales de página
  y chat (Promise.all con catch que avisa en vez de listas mudas),
  `loadSlots`, `doCancel`, `doReschedule` y la búsqueda por
  teléfono del chat. El backend ya respondía 404/405/500 en JSON
  desde el Ciclo 1.
- **Verificación 2:** por API, 404 de ruta y de cita → JSON
  `{"error": ...}` (PASS). Por contenido: «sin respuesta del
  servidor» ×6 en el JS compilado (página + chat).

### M8 (residual) — CORS restringido a orígenes locales

- **Cambio (`backend/app.py`, `README.md`):** `CORS(app)` abierto
  pasa a aceptar solo orígenes `http://localhost[:puerto]` y
  `http://127.0.0.1[:puerto]` (regex) sobre `/api/*`. El aviso del
  README se actualiza: ya no dice «CORS abierto», dice que solo
  acepta orígenes locales. El riesgo de exposición fuera de la
  máquina sigue declarado (sin auth, ver A3): la mitigación no se
  vende como solución completa.
- **Verificación 2 (curl):** con `Origin: http://evil.example` la
  respuesta NO trae `Access-Control-Allow-Origin` (ni en GET ni en
  preflight OPTIONS); con `Origin: http://localhost:5173` se
  refleja ese origen. PASS.

### B13 — Objetivos táctiles de 44 px en los selectores de hora

- **Cambio (`App.css`):** `.slot` y los botones de `.chat-times`
  (y el botón de fecha del chat, misma regla) con
  `min-height: 44px` y centrado flex (antes ≈38 px y ≈33 px).
- **Verificación 1/3:** `min-height:44px` ×2 en el CSS compilado;
  sin cambios de layout fuera de la altura mínima de esos botones.

### B14 — Disponibilidad sin una consulta por hueco

- **Cambio (`backend/app.py`):** `free_starts()` trae una sola vez
  las citas confirmadas del profesional ese día y calcula los
  solapes en memoria (antes: ~33 consultas por profesional y
  petición, vía `validate_slot` por candidato). `validate_slot`
  se mantiene para crear/reprogramar.
- **Verificación 2 (equivalencia, la decisiva):** comparadas la
  implementación nueva y la original (enumeración con
  `validate_slot`) en 5 días × 3 servicios × 2 profesionales:
  listas idénticas en los 30 casos. Nota honesta: para el día
  vacío de Corte ambas dan **30** inicios, no los 31 que anotó el
  diagnóstico de Fase 1 (35 inicios posibles − 5 que solapan el
  almuerzo: 12:45 y 13:00–13:45); el comportamiento de la app no
  cambia, la cifra del diagnóstico era la imprecisa.

### B16 — El botón de WhatsApp ya no sale de la demo

- **Cambio:** el enlace `https://wa.me/15551234567` desaparece.
  El botón «Reservar por WhatsApp» es ahora un botón que abre el
  chat de la propia página (evento `barberia:open-chat` que
  `ChatWidget` escucha), y la microcopia lo dice: «WhatsApp
  simulado: se abre el chat de esta misma página, sin salir de la
  demo a ningún número real.»
- **Verificación 1/2:** `wa.me` ×0 en el JS compilado;
  `barberia:open-chat` ×3 (emisor + alta/baja del listener);
  «WhatsApp simulado» presente.

### B17 — Restos del chat y fuentes de verdad del horario

- **Cambio:** (1) `handleDatePicked` ya no llama a `setFlow` dos
  veces seguidas: una sola actualización por rama (con huecos
  avanza; sin huecos permanece en el paso de fecha) — verificado
  por lectura: 4 `setFlow` en la función, uno por rama excluyente.
  (2) Eliminado el `choices: []` del mensaje de «no sé qué
  necesitas» (renderizaba un contenedor de opciones vacío):
  `choices: []` ×0 en fuente y en el JS compilado. (3) Nuevo
  `frontend/src/schedule.js`: única fuente de horario del frontend
  (`HOURS_TEXT` del chat y el texto de almuerzo de la sección
  Horarios salen de ahí). El backend mantiene sus constantes en
  Python — son las que mandan al reservar — y queda un literal
  funcional `13:00` en `slotGrid` (marca el almuerzo en la rejilla
  de la agenda; no es texto para el usuario). (4) `parse_time`:
  se mantiene la normalización de «9:00» → 09:00 como
  permisividad deliberada y sin impacto (los mensajes de formato
  ya son específicos desde el Ciclo 1).

### B5 — Huecos muertos de 10 minutos tras una Barba: documentado

- No es un bug (la lógica de solapes lo gestiona bien): queda
  documentado en el README («Nota de agenda») y en la propia UI
  (sección Horarios: «La Barba dura 20 minutos: puede dejar
  huecos de 10 minutos sin aprovechar entre citas»).
- **Verificación 2:** Barba 14:00 → 201; Corte 14:15 → 409
  (solape); la disponibilidad posterior ofrece 14:30 y no 14:15.
  PASS. «huecos de 10 minutos» presente en el JS compilado.

### Regresión — flujos buenos intactos (smoke curl)

Crear válida 201 · solape exacto 409 · cancelar 200 ·
reprogramar con fecha inválida (2026-02-30) 400 · domingo
`closed: true` tanto en disponibilidad como al crear ·
`PRAGMA foreign_key_check` limpio · batería específica del
ciclo: 18 PASS contados + mensaje M9 verificado por cuerpo
(ver B14 para la única «discrepancia», que resultó ser cifra
del diagnóstico, no del código) · BD restaurada al estado
semilla y servidores apagados al terminar.

### Pendiente (con motivo, sin forzar)

- **B6 — El mismo cliente con los dos barberos a la misma hora:**
  decisión de producto (la especificación no lo permite ni lo
  prohíbe). Impedirlo sería inventar una regla de negocio;
  queda para que Antonio decida.
- **B15 — Anti-solape no atómico:** la garantía actual depende de
  la serialización de SQLite/servidor de desarrollo. Hacerlo
  atómico de verdad exige restricción/bloqueo en BD o un servidor
  de producción: rediseño fuera del alcance de una demo local y
  la carrera no se reprodujo (10 POST simultáneos → 1× 201).
- **B1–B4, B9–B11 residuales:** fuera de la lista de este ciclo
  (contratos de `professional_id`, higiene/git, favicon/meta):
  sin tocar.

---

## 2026-11-02 — Ciclo 4 (bajas residuales B1–B4 y B9–B11 seguras)

Respaldo previo propio de este ciclo:
`/tmp/barberia.db.bak-ciclo4-20261102-222220` (creado y verificado
antes de probar). BD restaurada al estado semilla al terminar
(3 citas, ids 1–3, todas `cancelled`, 2026-10-27;
`PRAGMA foreign_key_check` limpio; solo se borraron las citas de
prueba ids 4–7). Servidores apagados al terminar (puertos 5000 y
8899 libres, sin procesos residuales). B6 y B15 quedan FUERA por
orden expresa (decisión de producto/diseño, ya anotadas en Ciclo 3).

**Estándar reforzado aplicado:** V3 por CONTENIDO contra el último
build conocido-bueno (Ciclo 3: JS 165 225 B / CSS 11 894 B).
Build nuevo: **JS 165 225 B y CSS 11 894 B, idénticos byte a byte
en tamaño** (el `src/` del frontend no cambió: solo `index.html` y
el favicon nuevo de B11, que vive en `public/` y se copia a
`dist/favicon.svg`). Señales del build bueno, presentes:
`localhost:5000` ×2, «datos de ejemplo» ×7, `getFullYear` presente
y `toISOString` ausente, Oswald y tokens `#18753c` ×2 / `#b93532`
×1 y `min-height:44px` ×2 en el CSS. Sin variables nuevas.

### Punto de partida verificado en vivo (antes de tocar nada)

Las sondas contra la API real mostraron que **B1, B2 y B3 ya
quedaron resueltos por los arreglos del Ciclo 1** (validación
estricta A1/A2), aunque nunca se cerraron como ítems: disponibilidad
con `professional_id=999`/`abc`/`0` → 400 con mensaje específico;
crear con `professional_id=999` → 400 «no existe» (el diagnóstico
lo vio responder 409 en disponibilidad 200); `professional_id=0`
→ 400, distinto de `null`; ids como arrays `[1]` → 400 «debe ser
un entero». Este ciclo los **verifica y cierra** (ver batería
abajo) y solo añade código donde quedaba un resto real: B4.

### B4 (resto) — Mensajes que aún no describían el problema real

- **`GET /api/availability` fusionaba los errores:** `date`
  inválida, `service_id=999` y `service_id=abc` respondían los tres
  el mismo «date (YYYY-MM-DD) y service_id válidos requeridos.»,
  sin decir qué campo fallaba. Ahora: `date` → «date debe tener
  formato YYYY-MM-DD válido.»; `service_id` no entero → «service_id
  debe ser un entero válido.»; inexistente → «service_id no
  existe.». Mismo código 400 de siempre.
- **Crear sin profesional concreto devolvía el error del último
  candidato probado.** Si ambos barberos están ocupados, el 409 es
  ahora un resumen: «Ningún profesional está libre en ese
  horario.». Los errores no-per-profesional (domingo, almuerzo,
  fuera de horario) se devuelven tal cual, sin enmascarar.
- **Verificación 2:** mensajes comprobados leyendo el cuerpo JSON
  decodificado (no con grep sobre el JSON escapado): los tres de
  disponibilidad, el resumen de solape total, y el de domingo
  intacto cuando corresponde.

### B2 (cierre documental) — Semántica de `professional_id` opcional

- La distinción ya era real en código (ausente/`null` = primero
  libre al crear, = se mantiene al reprogramar; `0` = no existe →
  400) pero no estaba escrita. El README la documenta ahora en
  «Reglas de la agenda». Verificado en vivo: crear con `null` →
  201 asignando primero libre; crear/reprogramar con `0` → 400.

### B9 — Higiene: `.gitignore` y deriva de dependencias

- Nuevo `.gitignore` en la raíz: `backend/venv/`,
  `frontend/node_modules/`, `__pycache__`, `frontend/dist/` y
  `backend/instance/*.db` quedan fuera de cualquier versionado
  futuro. (El proyecto sigue sin ser un repo git: inicializarlo
  no se hizo, es decisión de Antonio, no un arreglo de código.)
- `requirements.txt`: `Flask-Cors==6.0.1` → `==6.0.5`, la versión
  realmente instalada y verificada en el `venv` (`pip show`:
  flask-cors 6.0.5, Flask 3.1.3 — el resto ya coincidía).

### B10 — Omisiones del README: ya cerradas en ciclos anteriores

- Releído contra el código: `GET /api/health` documentado (Ciclo 1),
  códigos de error 400/404/409 documentados (Ciclo 3), reprogramar
  puede cambiar de profesional (documentado), el filtro obligatorio
  de `GET /api/appointments` y el aviso de seguridad/debug están
  desde el Ciclo 1, y este ciclo añade el contrato de errores de
  disponibilidad (B1/B4) y la semántica de `null` (B2). Sin resto
  seguro pendiente en este ítem.

### B11 — `index.html`: descripción y favicon

- Añadidos `<meta name="description">` (texto de ejemplo, sin
  inventar datos del negocio) y favicon propio
  `frontend/public/favicon.svg` (poste de barbero dorado/granate
  sobre fondo oscuro, en la paleta de la página), enlazado con
  `<link rel="icon" type="image/svg+xml">`.
- **Verificación 1/2:** `dist/` servido por HTTP: `/` 200,
  `/favicon.svg` 200 (antes 404), JS 200; el HTML servido contiene
  la descripción y el enlace al favicon.

### Regresión + batería del ciclo (smoke curl, 26/26 PASS)

Crear válida 201 · solape exacto 409 · cancelar 200 ·
reprogramar fecha inválida (2026-02-30) 400 · batería B1–B4:
disponibilidad prof 999/abc → 400 con mensaje por campo ·
disponibilidad service 999/abc y date basura → 400 con mensajes
específicos nuevos · crear prof 999 → 400 · crear prof 0 → 400 ·
crear prof `null` → 201 primero libre · reprogramar prof 0 →
400 · crear service/prof como array → 400 · ambos barberos
ocupados sin profesional pedido → 409 «Ningún profesional está
libre en ese horario.» · domingo sin profesional → 409 «Domingo
cerrado» (sin enmascarar) · `PRAGMA foreign_key_check` limpio ·
BD restaurada al estado semilla y servidores apagados al
terminar. Ortografía de los textos nuevos revisada («Ningún»,
«válido», «entero»).

---

## 2026-11-02 — Fase 2, Ciclo 10 (smoke permanente)

Respaldo previo propio de este ciclo:
`/tmp/barberia.db.bak-ciclo10-20261102-231440` (md5
`9ef7adf0815790b354074108797de3a2`, idéntico al de la BD real antes
y después del ciclo). BD real verificada al terminar en su estado
semilla (3 citas, ids 1–3, todas `cancelled`, 2026-10-27;
`PRAGMA foreign_key_check` limpio; md5 sin cambios: el smoke nunca
la abre). Servidores apagados al terminar (puertos 5000, 5117 y
5118 libres, sin procesos residuales; directorios temporales de
sonda, de humo y de la prueba de fuego destruidos).

### Smoke ejecutable — los humos manuales de los Ciclos 1–3, fijados

- **Cambio:** nuevo `scripts/smoke.py` (solo librería estándar,
  patrón del smoke de `api-segundo-yo`: comprobaciones numeradas,
  salida clara, código de salida 0/≠0, servidor que se apaga
  siempre). **56 comprobaciones** contra el backend real:
  salud/datos base, disponibilidad, errores 400 por campo en
  disponibilidad, creación/solape/almuerzo/domingo/fecha pasada,
  validación de tipos y formatos, filtro obligatorio del listado,
  cancelación, reprogramación con integridad FK, errores JSON
  404/405 provocados de verdad y CORS.
- **Seguridad del propio smoke:** copia `backend/app.py` a un
  directorio temporal en `/tmp` y lo arranca ahí (puerto 5117,
  variable `PORT` si hace falta otro): la BD SQLite nace dentro
  del temporal solo con profesionales y servicios semilla, sin
  citas. La BD real del proyecto no se abre ni se toca, y el
  temporal se destruye al terminar, pase o falle.
- **Cifra de disponibilidad derivada en esta sesión (V3):** día
  vacío → **30 inicios para Corte por profesional**, confirmados
  por respuesta real y derivados del código: inicios posibles de
  09:00 a 17:30 (último inicio = cierre 18:00 − 30 min de Corte)
  en bloques de 15 min = 35; solapan el almuerzo 13:00–14:00 los
  inicios 12:45, 13:00, 13:15, 13:30 y 13:45 = 5; 35 − 5 = **30**.
  El 12:30 sí se ofrece (Corte termina 13:00). Se confirma lo que
  el Ciclo 3 ya corrigió: los 31 del diagnóstico de Fase 1 eran la
  cifra imprecisa. El resto de cifras y formas (201/400/404/405/
  409, `{"error": ...}`, cabeceras CORS con y sin permiso) se
  derivó igual: leídas del código y de respuestas reales de una
  sonda previa en esta misma sesión, no de los logs.
- **Alcance declarado dentro del propio script:** que el error de
  cancelación se vea en el panel es tema de frontend (Ciclo 2,
  M6) y queda fuera de este smoke de backend. **B6** (mismo
  cliente, dos barberos, misma hora) y **B15** (atomicidad
  anti-solape de producción) quedan fuera por decisión de
  Antonio: el smoke los evita (clientes de ejemplo distintos por
  reserva, solapes probados por profesional, peticiones
  secuenciales) y no fija ningún comportamiento sobre ellos.
- **README:** añadida solo la línea veraz de cómo correr el
  smoke, junto a las instrucciones de ejecución; el resto del
  README (incluidos los códigos 400/404/405/500/409 ya
  documentados) no se tocó.

### Triple verificación reforzada

- **V1 (smoke + frontend):** `scripts/smoke.py` completo contra
  el backend real con BD temporal: **56/56 PASS, salida 0**
  (corrido dos veces en el ciclo, la última en el estado final).
  `npm run build` OK y bundle comparado por contenido contra el
  conocido-bueno vigente (Ciclo 4): JS `index-Dp2NaXmV.js`
  165 225 B y CSS `index-M0X1mH2E.css` 11 894 B, **idénticos en
  tamaño y en hash de nombre**; señales presentes
  (`localhost:5000` ×2, «datos de ejemplo» ×7, `getFullYear`
  presente, `toISOString` ausente, `#18753c` ×2, `#b93532` ×1,
  `min-height:44px` ×2). Delta cero, como corresponde: este ciclo
  no toca `frontend/src/`.
- **V2 (prueba de fuego):** en una copia del proyecto en
  `/tmp/barberia-fuego` se desactivó deliberadamente la
  comprobación de solape en `validate_slot()` (solo en la copia)
  y el smoke salió con **código 1 nombrando la comprobación
  caída**: «✗ [20] solape mismo profesional y hora → 409 JSON
  (actual: 201)», sin otros falsos positivos. Copia destruida;
  el `backend/app.py` real conserva su md5
  (`c0237416877fa36cffd6924e32a2b612`) de antes de la prueba.
- **V3 (cifras desde el código y respuestas reales):** ver la
  derivación de los 30 inicios arriba; cada código y forma de
  error fijados se observó primero en la sonda de esta sesión
  (incluidos el preflight CORS sin permiso para origen externo
  y el 405 de `PUT /api/health` en JSON).

---

## 2026-11-02 — Fase 2, Ciclo 11 (verificación cruzada frontend↔backend)

Respaldo previo propio de este ciclo:
`/tmp/barberia.db.bak-ciclo11-20261102-232208` (md5
`9ef7adf0815790b354074108797de3a2`, idéntico al de la BD real
antes y después del ciclo). La verificación nueva es de solo
lectura y sin servidor (la BD se abre con `mode=ro`); el smoke
del Ciclo 10 corrió con su protocolo habitual de BD temporal.
Servidores apagados al terminar (puertos 5000, 5117, 5118 y
8899 libres; copia de la prueba de fuego destruida).

### Inventario de constantes de catálogo del frontend (V3, leído de los archivos reales en esta sesión)

**Por API en tiempo real — NO hay constante que cruzar:**

- Servicios (nombre, duración, precio): `GET /api/services` en
  `App.jsx:60` y `ChatWidget.jsx:60`; se pintan `s.name`,
  `s.duration_min` y `s.price_example` del JSON (tarjetas
  `App.jsx:185-190`, opciones del formulario `App.jsx:247-251`,
  «Servicios» del chat `ChatWidget.jsx:121` y `:281`, choices
  `ChatWidget.jsx:129`). Ningún precio literal `$<dígito>` en
  todo `frontend/src/`.
- Profesionales: `GET /api/professionals` en ambos componentes;
  nombres pintados desde el JSON (select `App.jsx:262-266`,
  «Profesionales:» de Ubicación `App.jsx:211`, choices del chat
  `ChatWidget.jsx:154-156`). Los literales «Carlos»/«Luis» NO
  aparecen en `frontend/src/` (0 coincidencias).
- Conclusión: en servicios (salvo lo de abajo) y profesionales
  no puede haber deriva: si el backend cambia un dato, la web
  muestra el nuevo. Por eso el script fija la AUSENCIA como
  comprobación: si alguien escribe a mano un precio o un nombre
  de profesional en el frontend, el cruce falla y obliga a
  revisar ese nuevo punto de deriva.

**Constantes escritas a mano — SÍ comparables (y cruzadas):**

- Horario, que vive en TRES sitios del frontend contra
  `backend/app.py:37-41` (OPEN 09:00, CLOSE 18:00,
  LUNCH_START/END 13:00/14:00, BLOCK 15) y el cierre de domingo
  (`weekday() == 6` en `validate_slot`/`free_starts`/
  `availability`):
  - `frontend/src/schedule.js:6-10`: OPEN_TEXT `09:00`,
    CLOSE_TEXT `18:00`, LUNCH_TEXT `13:00 – 14:00`, HOURS_TEXT
    completo (lun–sáb 09:00–18:00, almuerzo 13:00–14:00,
    domingos cerrados, bloques de 15). Nota: OPEN_TEXT y
    CLOSE_TEXT están definidos pero hoy ningún componente los
    importa (se consumen LUNCH_TEXT en `App.jsx:3` y HOURS_TEXT
    en `ChatWidget.jsx:2`); se cruzan igual por ser la fuente
    declarada del frontend (B17).
  - `frontend/src/App.jsx:20-23` (`slotGrid`, funcionales):
    bucle `h = 9; h < 18`, paso `m += 15`, almuerzo con
    literales `'13:00'`/`'14:00'`.
  - `frontend/src/App.jsx:199-202` (lista «Horarios», literales
    que NO salen de schedule.js): «Lunes a sábado: 09:00 –
    18:00», «Domingo: cerrado», «Citas en bloques de 15
    minutos».
- `App.jsx:203`: «La Barba dura 20 minutos…» — nombre y
  duración de un servicio en prosa, contra la semilla
  (Barba, 20 min).
- `ChatWidget.jsx:352-355`: el texto libre del chat busca los
  servicios por nombre exacto (`s.name === 'Corte + Barba'` /
  `'Barba'` / `'Corte'`) y el mensaje guía de `:360` anuncia
  los tres nombres: si el backend renombra un servicio, esta
  interpretación se rompe en silencio — es constante comparable.
  Las heurísticas `low.includes('corte'/'barba')` (`:280`,
  `:351-355`) son subcadenas de esos mismos nombres: no se
  fijan como igualdad porque degradan sobre la búsqueda por
  nombre exacto, que sí se cruza.
- Precios: la única copia fuera de la API es la BD real contra
  la semilla de `app.py` — el script la incluye (nombre,
  duración y **precio** por servicio), que es donde un precio
  sí puede derivar (semilla editada sin resembrar).

**Backend (fuente que la API sirve), `backend/app.py`:** seed
`:107-118` — profesionales Carlos y Luis; servicios Corte
30 min $8, Barba 20 min $5, Corte + Barba 45 min $12 (precios
de ejemplo). Coincide con la BD real leída en solo lectura.

### Cambio — `scripts/verify-catalog.py` permanente

- **Nuevo script** (solo librería estándar, patrón del smoke):
  extrae AMBOS lados de los archivos reales — backend por `ast`
  (constantes `time(...)`, BLOCK, kwargs de `seed()` y el entero
  de `weekday()`), frontend por patrones anclados a cada
  constante inventariada, BD por sqlite en `mode=ro` — sin
  copiar ningún dato del catálogo dentro del script como
  tercera copia. **20 comprobaciones** numeradas; si un patrón
  deja de encontrarse, falla nombrándolo («la constante cambió
  de forma»), nunca pasa en silencio. Sin servidor, sin
  escrituras. README: añadida solo la línea veraz de cómo
  correrlo, junto a la del smoke.
- **Deriva real hoy: NINGUNA.** Las 20 comprobaciones pasan con
  los valores de arriba, idénticos en los dos lados (y en la
  BD). No hubo nada que corregir en `src/` ni en `app.py`.

### Triple verificación reforzada

- **V1 (script + smoke + build):** `scripts/verify-catalog.py`
  en el estado final: **20/20 PASS, salida 0**. Smoke del
  Ciclo 10: **56/56 PASS, salida 0**, con la BD real intacta
  (md5 `9ef7adf0815790b354074108797de3a2` antes y después; el
  script nuevo tampoco la mueve: apertura `mode=ro`).
  `npm run build` OK y bundle **idéntico** al conocido-bueno
  vigente (Ciclo 4/10): JS `index-Dp2NaXmV.js` 165 225 B
  (md5 `b864d911e7e36d2da444de10e25fb165`) y CSS
  `index-M0X1mH2E.css` 11 894 B (md5
  `75b8ff30116476f7696c99477bae5be2`); señales presentes
  (`localhost:5000` ×2, «datos de ejemplo» ×7, `getFullYear`,
  `toISOString` ausente, `#18753c` ×2, `#b93532` ×1,
  `min-height:44px` ×2). Delta cero, como corresponde: este
  ciclo no toca `frontend/src/` ni `backend/app.py` (md5 de
  `app.py` intacto: `c0237416877fa36cffd6924e32a2b612`).
- **V2 (prueba de fuego):** en una copia del proyecto en
  `/tmp/barberia-catalogo-fuego` se introdujeron DOS derivas
  deliberadas (solo en la copia): precio de Corte en la
  semilla `price_example=8` → `10` y prosa del frontend «La
  Barba dura 20» → `25` minutos. El script salió con **código
  1 nombrando exactamente las dos**: «✗ [02] servicios BD
  (Corte 30 min $8.0; …) == semilla (nombre, duración y
  precio)» y «✗ [16] prosa «La Barba dura 25 minutos» ==
  semilla (Barba: 20 min)», sin falsos positivos (las otras 18
  siguieron en ✓). Copia destruida; los archivos reales
  conservan sus md5 de antes de la prueba.
- **V3 (datos desde los archivos reales):** todo el inventario
  de arriba se leyó en esta sesión de `backend/app.py`,
  `frontend/src/schedule.js`, `App.jsx`, `ChatWidget.jsx`,
  `index.html` (sin datos de catálogo: solo la descripción
  genérica de la demo) y la BD en solo lectura; las cifras del
  cruce son las que el propio script imprime desde esos
  archivos al correr, no copias de este log.

### Fuera de alcance, sin tocar

- B6 y B15 (decisiones de Antonio, Ciclo 3). Ninguna otra app,
  ni el informe maestro, ni GitHub. Sin `.env` ni credenciales.
