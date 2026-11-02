# Improvement log — api-segundo-yo

## 2026-11-02 · Fase 2, Ciclo 1

### API-A1 (alta) — Validación real de payloads
- **Hallazgo:** un `title` de 250 caracteres se aceptaba con 201 contra una columna `String(200)` y una `category` numérica (`12345`) se aceptaba coaccionada a texto, en `_prompt_payload` (`app.py`).
- **Cambio:** validación estricta en `_prompt_payload` con ayudante `_check_text`: todo campo de texto debe ser cadena (`title`, `block`, `category`, `action`, `persona`, `context`, `restrictions`, `template`) y respetar la longitud de su columna según `TEXT_LIMITS` (title ≤ 200, block ≤ 50, category ≤ 100; las columnas `Text` solo exigen tipo). `steps` debe ser lista de textos (una cadena suelta sigue convirtiéndose en lista de un elemento, como promete el README). Todo rechazo es 400 con JSON claro (`title no puede superar los 200 caracteres`, `category debe ser texto`, …); nada se coacciona en silencio y ningún caso probado da 500. Aplica igual a POST y a PUT parcial.
- **Verificaciones:**
  1. `py_compile` de `app.py` y `seed_data.py`: OK.
  2. Smoke `curl` real con `PORT=5001` (el 5000 sigue ocupado por un servicio ajeno, no tocado): título de 250 → 400 JSON; categoría numérica → 400 JSON; título numérico → 400; `action` numérica → 400; categoría de 101 → 400; `steps` con números → 400; `steps: 123` → 400; `block` inválido → 400; sin `title` → 400; título de exactamente 200 → 201 (límite correcto); CRUD completo POST→GET→PUT→DELETE→GET 404 OK; PUT con título de 250 y con categoría numérica → 400. Recuento final tras limpiar la prueba: 14/25/24, servidor apagado.
  3. Checklist: mensajes nuevos con ortografía correcta («debe ser texto», «no puede superar los … caracteres»); sin regresiones: health, filtros (`block=otro` 400, `q` sin resultados 200 `[]`, tareas por grupo = 5, glosario `q=token` = 1) y la página de documentación en `/` siguen respondiendo igual (200 HTML, 20.542 bytes).

### API-M1 (media) — Errores 404/405 en JSON
- **Hallazgo:** una ruta inexistente devolvía la página 404 HTML de Flask y un método no permitido devolvía 405 HTML, contra la promesa «todas las respuestas son JSON» del README y de la documentación.
- **Cambio:** manejadores `@app.errorhandler` para 404 («ruta no encontrada»), 405 («método no permitido en esta ruta») y 500 («error interno del servidor», con `rollback` de la sesión), todos con `jsonify({"error": …})`.
- **Verificaciones:**
  1. `py_compile`: OK.
  2. Smoke `curl`: `GET /api/no-existe` → 404 `application/json`; `POST /api/tasks` → 405 JSON; `DELETE /api/glossary/1` → 405 JSON; `GET /api/prompts/abc` → 404 JSON; el 404 de recurso (`/api/prompts/999`) mantiene su mensaje específico. Servidor apagado al terminar.
  3. Checklist: la ruta `/` sigue sirviendo la documentación HTML con 200 (el handler no la afecta); mensajes en español correcto.

### API-M4 / higiene (media) — `.gitignore`
- **Hallazgo:** sin `.gitignore`, con `venv/`, `__pycache__/` y `app.db` presentes y versionables.
- **Cambio:** creado `.gitignore` con `venv/`, `__pycache__/`, `*.py[cod]`, `*.db`, `.env` y `.DS_Store`.
- **Verificaciones:** (1) `py_compile` OK tras el cambio; (2) la batería `curl` completa corrió sin relación con este archivo y pasó; (3) contenido del `.gitignore` revisado línea por línea contra los artefactos reales de la carpeta.

## 2026-11-02 · Fase 2, Ciclo 2

### API-M2 (media) — Vocabulario de bloques incompatible entre apps hermanas
- **Hallazgo:** la API solo aceptaba `block` = `negocio` | `productividad`, pero biblioteca-prompts llama al segundo bloque `profesional`: conectado tal cual, cada filtro o guardado de ese bloque recibiría un 400.
- **Cambio:** alias normalizado, sin renombrar el contrato ni el seed: `BLOCK_ALIASES = {"profesional": "productividad"}` y ayudante `_normalize_block`, aplicados en el filtro `GET /api/prompts?block=` y en `_prompt_payload` (POST y PUT). Lo guardado queda siempre con el valor canónico `productividad` y las respuestas no cambian para los clientes actuales. El mensaje de error pasa a documentar el alias («block debe ser 'negocio' o 'productividad' (se acepta 'profesional' como alias de 'productividad')») y el README (tabla de filtros, tabla de campos y tabla de errores) y la documentación servida en `/` (fila de filtros y ejemplo de error) dicen lo mismo que el código.
- **Verificaciones:**
  1. `py_compile` de `app.py` y `seed_data.py`: OK.
  2. Smoke `curl` real con `PORT=5001` (el 5000 sigue ocupado por el servicio ajeno, no tocado): `?block=profesional` → 7 prompts, todos con `block: "productividad"` (idéntico resultado que `?block=productividad`); `?block=otro` → 400 con el mensaje nuevo; POST con `block: "profesional"` → 201 guardado como `productividad`; PUT con el alias → 200 canónico; PUT con `block: "otro"` → 400. Sin regresiones de ciclos anteriores: título de 250 → 400 (API-A1), ruta inexistente → 404 `application/json` (API-M1), filtros intactos (tareas por grupo = 5, glosario `q=token` = 1, `q` sin resultados → 200). Prompt de prueba borrado; recuento final 14/25/24; servidor apagado.
  3. Checklist: contenido verificado, no solo estado — la página de documentación servida contiene el texto del alias en 2 sitios y mide 20.720 bytes frente a los 20.542 del último build bueno conocido: +178 bytes, exactamente las dos menciones añadidas. Ortografía de los textos nuevos correcta («se acepta 'profesional' como alias de 'productividad'»). Factor invisible: la API solo lee `PORT` del entorno, con defecto 5000 documentado; nada más condiciona el arranque.
- **No hecho — API-M3 (media), con motivo:** el glosario de la API diverge del de la app web (definiciones distintas, capitalización opuesta, «token»/«ventana de contexto» separados aquí y combinados allí). Unificarlo exige decidir una única fuente de verdad y REEMPLAZAR datos ya sembrados: la siembra solo corre con la base vacía, así que cambiar `seed_data.py` no corregiría la `app.db` existente sin migración o resembrado. Es un cambio de datos con decisión editorial previa, no un borde de validación acotado; queda anotado para un ciclo con esa decisión tomada.

## 2026-11-02 · Fase 2, Ciclo 3

### API-B1 (baja) — Adiós a la API legada `Query.get()`
- **Hallazgo:** los 5 endpoints de detalle usaban `Query.get()`, que en SQLAlchemy 2.0 emite `LegacyAPIWarning` y desaparecerá en una versión futura.
- **Cambio:** los 5 pasan a `db.session.get(Modelo, id)` (`Prompt` ×3, `Task`, `GlossaryTerm`). Mismo comportamiento (objeto o `None` → 404 actual).

### API-B2 (baja) — Dependencias fijadas
- **Hallazgo:** `requirements.txt` declaraba rangos (`Flask>=3.0`, …): una instalación futura podía traer cambios incompatibles sin anunciarlo.
- **Cambio:** versiones exactas, las verificadas en el `venv` del proyecto (`pip freeze`): `Flask==3.1.3`, `Flask-SQLAlchemy==3.1.1`, `Flask-CORS==6.0.5`, con comentario que explica el porqué.

### API-B4 (baja) — La búsqueda de texto ya es literal
- **Hallazgo:** los comodines de `LIKE` no se escapaban en ningún filtro (`q`, `category`, `group`): buscar `%` equivalía a «todo» y `_` actuaba como comodín de un carácter, sin que se documentara.
- **Cambio:** ayudante `_like()` que escapa `\`, `%` y `_` y envuelve en `%…%`, aplicado con `escape="\\"` en los 8 `ilike` de la API (categoría y los 4 campos de `q` en prompts, etiqueta de grupo en tareas, término y definición en glosario). Sin impacto de seguridad antes ni después (el ORM ya parametrizaba); lo que cambia es la semántica: la búsqueda es literal.

### API-B5 (baja) — Siembra por tabla, sin KeyError latente
- **Hallazgo:** `seed_if_empty` era todo-o-nada: si cualquiera de las tres tablas tenía filas, abandonaba, y un estado parcial (siembra interrumpida) nunca se reparaba solo; además, un `group_key` del seed ausente de `TASK_GROUPS` habría matado el arranque con `KeyError`.
- **Cambio:** cada dominio se siembra solo si su tabla está vacía, y la etiqueta de grupo usa `GROUP_LABELS.get(group_key, group_key)`. La base real (14/25/24) no se toca: con las tres tablas llenas, la función no siembra nada. README y documentación servida ajustados a la nueva semántica («se siembran de nuevo solo las tablas que estén vacías») en los 4 sitios donde se describía la regeneración del seed.

### API-B8 (baja) — «Rearrancar» fuera
- **Hallazgo:** «rearrancar» (README y notas de la documentación servida) no es la forma estándar para volver a arrancar el servidor; era el único desliz léxico de la API.
- **Cambio:** sustituido por «volver a arrancar» / «vuelve a arrancar» en `app.py` (documentación) y en el README (2 sitios, incluida la forma «rearranca» de Solución de problemas). Verificado por búsqueda: no queda ninguna forma de «rearranc*» en la app.
- **Pulido transversal:** la página de documentación no tenía favicon (el navegador pedía `/favicon.ico` a una ruta HTML); se añade un icono SVG propio en línea (`data:` URI, teal `#12312e`/`#0f766e` de su paleta) en el `<head>` de `DOCS_HTML`. Título y meta descripción de la documentación ya eran específicos y correctos.

### Nota sobre API-B3
El diagnóstico lo dejó como «los elementos de `steps` no se validan», pero el arreglo de API-A1 (Ciclo 1) ya exige que cada paso sea texto («steps debe ser una lista de pasos de texto»); este ciclo se re-verificó en el código y en la batería histórica: queda cerrado sin cambio nuevo.

### Verificaciones (triple, con artefacto por contenido)
1. **Compilación y comparación:** `py_compile` de `app.py` y `seed_data.py` OK. Contenido comparado contra el último estado bueno (Ciclo 2): la página de documentación servida mide 20.960 bytes frente a 20.720 (+240 exactos, que son el delta medido de la cadena `DOCS_HTML` entre la copia previa y la nueva: enlace de favicon + «volver a arrancar» + la frase de siembra por tabla). El log del servidor de la batería no contiene ningún `LegacyAPIWarning` (antes aparecía al ejecutar los endpoints de detalle).
2. **Smoke `curl` real con `PORT=5001`** (el 5000 sigue ocupado por el servicio ajeno, no tocado): health inicial y final 14/25/24 con el prompt de prueba borrado y el servidor apagado al terminar. Batería: B4 — `q=%` → 0, `q=_` → 0, glosario `q=%` → 0, tareas `group=%` → 0 (antes `%` devolvía todo); sin regresión — glosario `q=token` = 1, tareas `group=seguimiento` = 5, `q` sin resultados → 200 `[]`, alias `block=profesional` → 7 prompts todos canónicos `productividad`, `block=otro` → 400 con el mensaje de API-M2; sin regresión de ciclos anteriores — ruta inexistente → 404 `application/json` (API-M1), título de 250 → 400 (API-A1); CRUD completo sobre los endpoints migrados (POST 201 → GET 200 → PUT 200 → DELETE 200 → GET 404; `GET /api/tasks/1` y `/api/glossary/1` → 200). B5 verificado aparte en una copia aislada en `/tmp` con base propia (la real no se tocó): estado parcial 14/25/0 → `seed_if_empty()` → 14/25/24, sin duplicar las tablas que ya tenían datos; copia eliminada tras la prueba.
3. **Checklist:** la documentación servida contiene el enlace `rel="icon"` ×1 y el alias documentado ×2 (contenido, no solo estado); ortografía de los textos nuevos correcta («se siembran de nuevo solo las tablas que estén vacías», «volver a arrancar»); `seed_data.py` y los datos sembrados intactos (API-M3 no tocado, por decisión editorial pendiente: sigue fuera, sin cambios en este ciclo). Factor invisible: la API solo lee `PORT` del entorno, con defecto 5000 documentado; nada más condiciona el arranque.
- **Pendientes con motivo:** API-B6 (listados sin paginación: añadirla cambia el contrato público de las respuestas —«sin filtros, cada lista devuelve el contenido completo» está documentado así—; exige decisión, no es un arreglo seguro) y API-B7 (la documentación como cadena de ~320 líneas dentro de `app.py`: extraerla es una refactorización sin ganancia visible y con riesgo de romper la página; se deja).

## 2026-11-02 · Fase 2, Ciclo 4

### Suelo de calidad verificable — Smoke test automático de la API
- **Hallazgo:** transversal de la revisión («ninguna de las tres tiene tests»): la batería de esta API se había ejecutado a mano con `curl` en cada ciclo (Ciclos 1–3); nada la repetía automáticamente y una regresión de validación (API-A1), de errores JSON (API-M1) o del alias (API-M2) solo se detectaría en la siguiente revisión manual.
- **Cambio:** `scripts/smoke.py`, solo librería estándar de Python (`urllib`, `subprocess`, `json`): levanta la app él solo en el puerto 5001 por defecto (`PORT` configurable; el 5000 sigue ocupado por el servicio ajeno y no se toca), comprueba health inicial 14/25/24, un CRUD completo (POST 201 → GET 200 → PUT 200 → DELETE 200 → GET 404), los rechazos clave (título de 250 → 400 JSON; ruta inexistente → 404 `application/json` con campo `error`) y el alias `block=profesional` → 7 prompts todos con `block` canónico `productividad`; cierra con health final 14/25/24 y apaga el servidor siempre (`terminate` en `finally`, con borrado previo del prompt de prueba si hubiera quedado). Sale con código ≠0 si algo se rompe. Documentado en el README («Verificación automática» y en la estructura del proyecto) y en la cabecera del propio script.
- **Verificaciones (triple):**
  1. Compilación: `py_compile` de `app.py`, `seed_data.py` y `scripts/smoke.py` OK. Sin cambios en `app.py`/`seed_data.py` este ciclo: la página de documentación y el contrato no se tocan.
  2. Script ejecutado contra el estado actual: `./venv/bin/python scripts/smoke.py` → código 0, 26 comprobaciones en verde, health inicial y final 14/25/24, servidor apagado al terminar (sin proceso en 5001 tras la corrida) y datos de prueba limpios.
  3. Prueba de fuego: en una COPIA temporal aislada en `/tmp` (con su propia `app.db` copiada y `venv` enlazado) se borró 1 prompt de la base copiada (14 → 13); el smoke de la copia (puerto 5002) salió con código 1 y señaló exactamente el daño (health inicial y final de prompts = 13). Copia eliminada; la base real no se tocó — la corrida real posterior volvió a dar 14/25/24.
- **Sin cambios de lint/tooling en esta app:** la API no tenía hallazgo de lint pendiente; el equivalente pragmático era este smoke, que es lo que queda corriendo.
- **API-M3 sigue fuera:** sin cambios en `seed_data.py` ni en el glosario sembrado, por decisión editorial pendiente de Antonio.
