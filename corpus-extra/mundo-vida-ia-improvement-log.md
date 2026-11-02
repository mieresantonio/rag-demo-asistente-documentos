# Registro de mejoras — mundo-vida-ia

## 2026-11-02 · Fase 2, Ciclo 4 (medias estructurales M-M3 y M-M4 de la revisión 2026-11-02)

### MUNDO-M3 — Nombres duplicados corrompían el índice por nombre

- **Hallazgo:** `Mundo.agregar_agente()` no comprobaba unicidad: dos
  agentes con el mismo nombre quedaban en `self.agentes`, pero
  `_por_nombre` apuntaba solo al segundo, así que `hablar`/`colaborar`
  y `lugar_de()` resolvían siempre al equivocado y `agentes_en()`
  devolvía el nombre dos veces. El protocolo ya exigía «nombre único
  dentro del mundo» (`como-unirse.md` §1), pero el motor no lo hacía
  cumplir.
- **Opción elegida y por qué:** rechazar el duplicado con `ValueError`
  al registrar, en vez de reindexar por una identidad distinta del
  nombre. Es la opción coherente con el resto del motor: es el mismo
  patrón que dejó el Ciclo 1 (MUNDO-A2) para lugares y acciones
  inválidas —lo inválido se rechaza con `ValueError` y mensaje claro—,
  y todo el motor se apoya en el nombre como identidad (percepción,
  relaciones, eventos y el contrato del visor usan el nombre), así que
  cambiar la clave habría sido un cambio mucho mayor sin promesa
  documental que lo pidiera. Con el rechazo, código y documento
  coinciden.
- **Cambio:** `agregar_agente()` comprueba `agente.nombre in
  self._por_nombre` ANTES de registrar y lanza
  `ValueError: Nombre duplicado: '…'. Cada agente debe tener un
  nombre único dentro del mundo; ya hay un agente registrado con ese
  nombre.` El agente rechazado no queda en la lista ni toca el índice:
  el ya registrado queda intacto. En `como-unirse.md`, la regla del
  campo `nombre` (§1) ahora dice explícitamente que el motor rechaza
  el duplicado con `ValueError`, y §5 lo reitera entre los límites.
- **Verificaciones:** dos agentes llamados «Test» → `ValueError` con
  ese mensaje, por las dos vías de import (paquete y módulo suelto);
  tras el rechazo hay 1 solo agente, el índice sigue apuntando al
  primero, `agentes_en("plaza")` lo devuelve una sola vez y el mundo
  sigue corriendo ticks; re-registrar el mismo objeto también se
  rechaza; duplicar un ejemplo cargado de `ejemplos/` también se
  rechaza. Los 3 ejemplos válidos siguen cargando, agregándose (Nia,
  Tomas, Lia, cada uno resoluble por su nombre) y ejecutando ticks.
  Sin regresión del Ciclo 1: un `lugar_inicial` inventado sigue
  lanzando su `ValueError`.

### MUNDO-M4 — Imports absolutos sin paquete: el motor solo corría vía la demo

- **Hallazgo:** `mundo.py` hacía `from agente import Agente` etc. sin
  paquete y solo `demo.py` metía su carpeta en `sys.path`; no había
  `__init__.py`. Desde la raíz del repo, `import simulacion.mundo` o
  `python3 -m simulacion.demo` daban `ModuleNotFoundError`.
- **Cambio:** `simulacion/` ahora es paquete (nuevo `__init__.py`,
  solo docstring, sin imports al cargarse) y los dos módulos con
  imports internos, `mundo.py` y `demo.py`, eligen la forma según
  `__package__`: con paquete, imports relativos (`from .agente
  import Agente`…); sin paquete (script suelto), los absolutos de
  siempre, con la misma inserción en `sys.path` en `demo.py`.
  `agente.py`, `experiencia.py` e `interaccion.py` no importan
  módulos propios y no necesitaron cambios. El README documenta las
  dos formas de correr la demo y `como-unirse.md` §4 documenta las
  dos vías de import; la estructura del README incluye `__init__.py`.
- **Verificaciones (triple, reforzada):**
  1. `py_compile` limpio en los 6 archivos de `simulacion/` (los 5
     módulos + `__init__.py`).
  2. Smoke real por AMBAS vías en una copia en `/tmp/mundo-c4`:
     `python3 simulacion/demo.py` y `python3 -m simulacion.demo`
     completan los 30 ticks con salida de consola idéntica entre sí
     («Ticks: 30 | Diálogos: 70 | Eventos de caos: 11») y registro
     idéntico al conocido-bueno en raíz y en `visor/`; de propina,
     `python3 demo.py` desde dentro de `simulacion/` y los imports
     `from simulacion.… import …` / sueltos desde la raíz y desde
     `simulacion/` también funcionan, y la vía módulo se ejecutó
     además en el proyecto real con el mismo resultado.
  3. Por contenido y comparación: el registro NO cambia con este
     ciclo —MD5 `b56a5a928fcf5a2722665c8251a5aa7b` antes y después,
     en las dos vías—, con 375 eventos y la misma distribución
     (150 pensamiento · 80 acción · 70 diálogo · 64 crecimiento ·
     11 caos) y los mismos recuerdos por agente (45/39/44/41/42);
     las tildes del Ciclo 2 intactas en los textos (`energía` ×335,
     `Así que` ×230, `compañía` ×53, `últimamente` ×30; formas sin
     tilde en textos, 0). Ninguna verificación falló, así que no
     hubo que revertir nada. Los `__pycache__` generados por las
     comprobaciones se eliminaron al terminar (proyecto y copia).

## 2026-11-02 · Fase 2, Ciclo 3 (hallazgos MEDIA restantes de la revisión 2026-11-02)

### MUNDO-M1 — Sin `.gitignore` en todo el proyecto

- **Hallazgo:** no existía `.gitignore`: en cuanto se generara un
  `__pycache__` (basta un `py_compile` o un import) entraría en el repo
  público.
- **Cambio:** creado `.gitignore` con `__pycache__/` y `*.pyc`, el mismo
  criterio que ya usa rag-demo.
- **Verificaciones:** el archivo existe con ese contenido exacto; tras
  las comprobaciones de este ciclo, el proyecto quedó sin ningún
  `__pycache__` ni `.pyc` (los generados por los smokes se eliminaron).

### MUNDO-M2 — El README afirmaba una variabilidad que el determinismo desmiente

- **Hallazgo:** el README decía que con semilla 42 «el conteo exacto de
  eventos puede variar ligeramente entre corridas». Demostrado lo
  contrario: no hay ninguna fuente de entropía fuera de
  `random.Random(42)` y las corridas producen el registro idéntico byte
  a byte.
- **Cambio:** el punto de «Límites honestos» ahora dice la verdad: la
  demo es completamente determinista sin cambios de código ni de datos
  (los mismos 375 eventos con el mismo desglose), y el conteo solo
  cambia si cambia el código o los datos — la diferencia histórica de
  377 frente a 375 de `log.md` vino de una corrección de código
  anterior, no de variabilidad.
- **Verificaciones:** por contenido, el README contiene «completamente
  determinista» y «byte a byte» y ya no contiene la frase vieja; la
  afirmación se contrastó ejecutando la demo dos veces en este ciclo
  (copia y proyecto): mismo MD5 en ambas, `b56a5a928fcf5a2722665c8251a5aa7b`.

### Visor — diseño genérico: una decisión visual acotada

- **Hallazgo:** el visor presentaba los tres síntomas de diseño genérico:
  tipografía por defecto en todo, tarjetas de agente idénticas entre sí
  y ritmo uniforme entre secciones.
- **Cambio (una sola decisión coherente, solo en la hoja de estilos de
  `visor/index.html`):** dos voces. Lo narrativo —titulares, nombres de
  agente y pensamientos— va en serif del sistema (Georgia; sin fuentes
  externas, el visor sigue funcionando sin red, como el proyecto) y con
  ritmo amplio (titulares mayores, secciones más separadas,
  pensamientos con interlineado 1,75 y filete dorado); lo informativo
  —tablas de rasgos, eventos, filtros— sigue en sans compacta. De la
  misma decisión sale que las tarjetas dejen de ser idénticas: cada una
  lleva como acento superior un color de la paleta que el visor ya usa
  para los tipos de evento, en rotación por posición (`nth-child`).
  No se tocó ni el HTML ni el script.
- **Verificaciones:**
  1. `py_compile` limpio en los 5 módulos de `simulacion/` (el visor no
     tiene Python, pero la demo que lo alimenta sí se recompiló).
  2. Smoke real: demo de 30 ticks en una copia en `/tmp` y en el propio
     proyecto, con registro coherente en ambos (las dos rutas de
     guardado dentro de la copia/proyecto, como dejó el Ciclo 1); el
     visor servido por HTTP respondió 200 en `/visor/` y en
     `/registro.json`, con la CSS nueva servida. Servidor apagado al
     terminar.
  3. Por contenido y comparación contra el estado conocido-bueno: el
     bloque `<script>` del visor es byte a byte idéntico al de antes
     del cambio (mismo MD5, `fefa115bdf5e9f33bfce24bb7fcfb177`), así
     que sigue leyendo las mismas claves del registro (`meta.ticks`,
     `meta.semilla`, `rasgos_iniciales/finales`, `animo`, `energia`,
     `metas`, `recuerdos`; eventos con `tick/tipo/agente/texto` y las
     rutas `../registro.json` / `registro.json`); la hoja de estilos
     contiene las cadenas decisivas de la decisión (`--serif: Georgia`,
     acentos `nth-child(5n+2…5)`, interlineado 1,75 en pensamientos).
     El registro no cambió: MD5 `b56a5a928fcf5a2722665c8251a5aa7b` en
     raíz y en `visor/`, 30 ticks y 375 eventos con la misma
     distribución (150 pensamiento · 80 acción · 70 diálogo ·
     64 crecimiento · 11 caos) y los mismos recuerdos por agente
     (45/39/44/41/42); las tildes del Ciclo 2 intactas en los textos
     (`energía` ×335, `Así que` ×230, `compañía` ×53, `últimamente`
     ×30; formas sin tilde, 0 — la clave JSON `"energia"` sigue
     apareciendo ×5, una por agente, como manda el contrato).

## 2026-11-02 · Fase 2, Ciclo 2 (hallazgos MEDIA de la revisión 2026-11-02)

### MUNDO-M5 — El texto generado salía sistemáticamente sin tildes

- **Hallazgo:** todo el texto que produce la simulación (pensamientos,
  diálogos, caos, crecimiento, consola) iba sin acentuar mientras el
  README y el protocolo sí acentúan. Conteo en el registro anterior:
  `energia` ×340, `Asi que` ×230, `compania` ×53, `ultimamente` ×30.
- **Cambio:** acentuado el español en las plantillas y textos de los
  cinco módulos de `simulacion/` (pensar y razones de `agente.py`,
  textos de caos y descripciones de `mundo.py`, cuerpos de diálogo de
  `interaccion.py`, metas derivadas de `experiencia.py` y textos de
  consola de `demo.py`), incluidos comentarios y docstrings visibles
  en el repo. En `mundo.py`, los textos de crecimiento muestran el
  rasgo y el tipo acentuados («su ambición…», «tras vivir 'diálogo'»)
  mediante mapas de visualización, y en el visor las etiquetas de
  rasgos, tipos y distintivos se acentúan igual al pintarlas. Las
  claves internas NO cambian: las claves JSON del registro
  (`energia`, `animo`), los valores de `tipo` (`dialogo`, `accion`),
  los nombres de rasgo (`ambicion`) y los tipos de experiencia son
  identificadores que usan el código y el contrato del visor, y van
  sin tilde a propósito. Ninguna comprobación lógica depende de las
  formas acentuadas (las palabras clave internas —tormenta, escasez,
  descubrimiento— conservan su raíz sin tilde), y `_clasificar()` en
  `experiencia.py` acepta además las formas acentuadas devolviendo
  siempre el identificador canónico.
- **El registro cambia por la corrección ortográfica:** regenerado
  ejecutando la demo en el propio proyecto (30 ticks). MD5 anterior
  `415bad5ef0a6e8880af712bc7f245743` → MD5 nuevo
  `b56a5a928fcf5a2722665c8251a5aa7b` (idéntico en raíz y en `visor/`,
  y reproducible: dos ejecuciones seguidas dan el mismo MD5 y la
  misma salida). Tamaño: 142 961 → 144 419 bytes (la diferencia es el
  coste UTF-8 de las tildes, sin eventos de más ni de menos).
- **Verificaciones:**
  1. `py_compile` limpio en los 5 módulos.
  2. Smoke real y comparación contra el último estado conocido-bueno
     (verificación por contenido, no por nombre): 30 ticks, 375
     eventos con la misma distribución que antes (150 pensamiento ·
     80 acción · 70 diálogo · 64 crecimiento · 11 caos), misma
     secuencia tick/tipo/agente, mismos rasgos finales, mismos
     ánimos/energías finales, mismas metas y mismos conteos de
     recuerdos por agente (45/39/44/41/42). Solo cambian los textos.
     En los textos del registro nuevo (eventos + recuerdos + metas):
     `energia` = 0, `Asi que` = 0, `compania` = 0, `ultimamente` = 0
     (y las formas acentuadas aparecen en espejo de los conteos
     viejos: `energía` ×335, `Así que` ×230, `compañía` ×53,
     `últimamente` ×30). En el archivo completo, `energia` aparece
     ×5: son las claves JSON estructurales, una por agente, que el
     visor lee como `a.energia`. En la salida de consola, 0 líneas
     con las formas sin tilde objetivo.
  3. Checklist de detalle: el contrato del visor se verificó campo a
     campo sobre el registro nuevo (`meta.ticks/semilla`, por agente
     `rasgos_iniciales/finales`, `animo`, `energia`, `metas`,
     `recuerdos`; eventos con `tick/tipo/agente/texto` y los 5 tipos
     dentro de los filtros del visor) y las dos copias del registro
     son idénticas; ortografía revisada en todo el texto tocado
     (incluidos «¿tú cómo lo llevas?», «gustaría» y las cabeceras
     «Código… estándar» de los cinco módulos); sin regresiones en la
     lógica (la demo produce exactamente la misma simulación).

## 2026-11-02 · Fase 2, Ciclo 1 (hallazgos ALTA de la revisión 2026-11-02)

### MUNDO-A1 — La demo escribía en una ruta absoluta fija

- **Hallazgo:** `simulacion/demo.py` usaba
  `os.path.expanduser("~/workspace/mundo-vida-ia")` como base para guardar
  `registro.json` y `visor/registro.json`: ejecutada desde cualquier clon
  en otra ruta, escribía fuera de ese clon (demostrado en la revisión:
  corría en `/tmp` y escribía en el repo real).
- **Cambio:** la base ahora es la raíz del proyecto calculada desde la
  ubicación del propio script
  (`os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`:
  `demo.py` vive en `simulacion/`, la raíz es su carpeta padre). No se
  tocó la lógica de la simulación.
- **Verificaciones:**
  1. `py_compile` limpio en los 5 módulos de `simulacion/`.
  2. Smoke real desde una copia en `/tmp/mundo-copia`: la demo corrió
     los 30 ticks completos (70 diálogos, 11 eventos de caos, como en la
     corrida documentada) e imprimió «Registro guardado en:
     /tmp/mundo-copia/…» para ambas rutas; el MD5 del `registro.json`
     del repo real fue idéntico antes y después
     (`415bad5ef0a6e8880af712bc7f245743`), y el registro generado en la
     copia salió byte a byte idéntico al versionado (mismo MD5), así
     que la reproducibilidad determinista se mantiene.
  3. Checklist de detalle: sin rutas absolutas ni referencias a
     `~/workspace` en el código de `simulacion/`; el README ya describía
     este comportamiento («guarda el registro en `registro.json` y en
     `visor/registro.json`» desde el repo), así que ahora es veraz sin
     cambios.

### MUNDO-A2 — El motor no rechazaba lugares ni acciones inválidas

- **Hallazgo:** `como-unirse.md` §5 afirma «cualquier otro valor de
  `lugar_inicial` o `accion` es inválido y el motor lo rechaza», pero era
  falso: un lugar inventado se aceptaba (la guarda de
  `Mundo.agregar_agente()` era un no-op) y una acción fuera del catálogo
  se convertía en silencio a «observar» en `Agente.actuar()`.
- **Cambio (el código ahora cumple lo que el documento promete):**
  - `agente.py`: nueva constante `LUGARES_VALIDOS` (los 5 lugares, en
    sincronía con `LUGARES` de `mundo.py`); el constructor lanza
    `ValueError` con mensaje claro si `lugar_inicial` no está en la
    lista. `actuar()` lanza `ValueError` si la acción falta o no está
    en `ACCIONES_VALIDAS` (ya no hay conversión silenciosa).
  - `mundo.py`: `agregar_agente()` comprueba el lugar ANTES de registrar
    al agente y lanza `ValueError` si no existe en el mundo (segunda
    línea de defensa, p. ej. si el lugar se mutó tras construir).
- **Verificaciones:**
  1. `py_compile` limpio en los 5 módulos.
  2. Smoke real en la copia de `/tmp`: `Agente(..., "castillo_inventado")`
     → `ValueError: Lugar inicial no válido…`; lugar mutado +
     `agregar_agente()` → `ValueError` y el agente NO queda registrado
     (0 agentes); `actuar()` con `"volar"` → `ValueError: Acción no
     válida…`; acción ausente → `ValueError`. Los 3 ejemplos de
     `ejemplos/` se cargan, se agregan y actúan con acciones válidas, y
     un mundo normal corre ticks sin error. La demo completa (30 ticks)
     también corrió sin cambios en su salida ni en su registro.
  3. Checklist de detalle: textos de error nuevos con ortografía
     cuidada (tildes en «no válido», «Acción»); `como-unirse.md` no
     necesita cambios porque su afirmación ahora es cierta; sin
     regresiones en el flujo normal.
