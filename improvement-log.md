# Registro de mejoras — rag-demo

## 2026-11-02 · Fase 2, Ciclo 3 (hallazgos MEDIA restantes de la revisión 2026-11-02)

### RAG-M3 — `requirements.txt` con rangos abiertos y numpy sin declarar

- **Hallazgo:** las cuatro dependencias iban con rangos abiertos
  (`flask>=3.0`, `sentence-transformers>=3.0`, `faiss-cpu>=1.8`,
  `pypdf>=4.0`): dos instalaciones en fechas distintas podían resolver
  versiones distintas y la demo dejaba de ser reproducible. Además,
  `rag_core.py` importa `numpy` directamente (en `build_index()` y en
  `_embed()`) y no estaba declarado: llegaba solo como dependencia
  transitiva de otros paquetes.
- **Cambio:** `requirements.txt` fija con `==` las versiones reales
  instaladas y verificadas en el `.venv` (consultadas con `pip show`):
  `flask==3.1.3`, `sentence-transformers==6.2.0`, `faiss-cpu==1.15.1`,
  `pypdf==6.21.4` y se declara `numpy==2.5.4`. Se mantiene la nota
  sobre la build solo-CPU de PyTorch. No se tocó código: el límite de
  longitud de la pregunta (máx. 1000, Ciclo 1) y el arranque en
  caliente (Ciclo 2) no se reabrieron.
- **Verificaciones:**
  1. `py_compile` limpio en `app.py`, `rag_core.py` e `ingest.py`.
  2. Smoke real con el servidor levantado: `/api/health` respondió
     `estado: "ok"`, `modelo_cargado: true`, 12 documentos y
     116 fragmentos; la carga del modelo en el arranque tardó esta
     vez 38,9 s (más que los 24,1 s medidos en el Ciclo 2: varía con
     la máquina, pero sigue pagándose en el arranque y no en la
     pregunta). Batería idéntica al estado conocido-bueno del Ciclo 2:
     despliegue → `despliegue.md` en las posiciones 1–3,
     `confianza: "alta"`, similitud máxima 0,502 y primera pregunta
     en 0,17 s; REA → `ingenieria-inversa.md` en 1.ª posición
     (0,526, alta); 45 frente a 90 → `comparacion-prompts-45-vs-90.md`
     con las 4 fuentes (0,588, alta); fuera de tema (capital de
     Francia) → `confianza: "baja"`, sin fuentes. Servidor apagado al
     terminar (puerto 5057 sin respuesta, comprobado).
  3. Por contenido y comparación contra lo instalado: el archivo ya no
     contiene ningún rango abierto en todo su texto; las cinco
     fijaciones coinciden una a una con la versión instalada en el
     `.venv` (comprobado vía `importlib.metadata`), `numpy` es
     importable en el `.venv` (2.5.4) y `pip check` no reporta
     requisitos rotos. Los artefactos del índice no cambiaron (MD5
     `08a10a5845fcbbb662e67933d1fb7e38`, `3574cc228e222a3c876a95c4c2edbbea`
     y `4659fa0322ea6b52f859d75b112e2bd2`, los del Ciclo 2).

## 2026-11-02 · Fase 2, Ciclo 2 (hallazgos MEDIA de la revisión 2026-11-02)

### RAG-M1 — Arranque en frío: la primera pregunta pagaba la carga del modelo

- **Hallazgo:** el modelo de embeddings se cargaba perezosamente en la
  primera búsqueda (medido en este ciclo: 26,0 s la primera búsqueda
  en frío en proceso) mientras `/api/health` ya decía «ok» desde el
  primer segundo, porque solo comprobaba que existiera el índice.
- **Cambio:**
  - `rag_core.py`: nuevo `RagStore.warmup()` (carga el modelo y hace
    una vectorización de calentamiento) y propiedad `model_loaded`.
  - `app.py`: al arrancar con `python app.py` se llama a `warmup()`
    ANTES de servir y se imprime el tiempo de carga; `/api/health`
    ahora dice «ok» solo con índice y modelo listos, «calentando»
    con el índice pero sin el modelo (p. ej. si la app se sirve por
    otra vía) y «sin_indice» si falta la ingesta, y expone
    `modelo_cargado`.
  - `README.md`: describe el arranque real con los tiempos medidos.
- **Verificaciones:**
  1. `py_compile` limpio en `app.py`, `rag_core.py` e `ingest.py`.
  2. Smoke real con el servidor levantado: arranque hasta que
     `/api/health` respondió = 25,1 s, con el mensaje «Modelo de
     embeddings cargado en 24,1 s» en el log del servidor; health en
     ese momento: `estado: "ok"`, `modelo_cargado: true`,
     12 documentos, 116 fragmentos. La primera pregunta (la de
     despliegue) tardó 0,90 s y las siguientes 0,04–0,41 s. Sin el
     arranque en caliente (cliente de pruebas sobre el módulo), el
     health dice honestamente `estado: "calentando"`,
     `modelo_cargado: false`. Servidor apagado al terminar (puerto
     5057 sin respuesta, comprobado).
  3. Checklist de detalle: sin regresiones del Ciclo 1 — los casos de
     validación de `/preguntar` (entero, ausente, vacío, lista,
     1001 caracteres) siguen devolviendo 400 en JSON; el README y el
     comportamiento coinciden; ortografía revisada en los textos
     nuevos.

### RAG-M2 — «¿Cómo se despliega una aplicación?» no recuperaba despliegue.md

- **Diagnóstico (por contenido, contra el índice anterior):** la
  pregunta no metía a `despliegue.md` ni en el top-8 semántico. Tres
  causas encadenadas, medidas sobre los artefactos:
  1. *Troceado:* 16 de 135 fragmentos eran de solo encabezado (el
     título quedaba aislado en un fragmento inútil) y 78 de 135
     fragmentos no contenían el título de su sección: del segundo
     fragmento en adelante, cada sección perdía su contexto al
     vectorizarse. El título del documento («Despliegue — lo
     aprendido») no llegaba a ningún fragmento.
  2. *Vocabulario:* el documento trata el despliegue como doctrina
     (tarjetas, costes, WSGI, runbook); la mejor similitud semántica
     pura de cualquiera de sus fragmentos frente a la pregunta es
     0,371, frente a 0,502 del fragmento ganador de otro documento.
     Verificado que no era un desajuste índice/fragmentos: un
     re-cálculo manual de cosenos sobre los textos guardados
     reproduce exactamente el ranking de FAISS.
  3. *Descartadas con experimento previo (no a ciegas):* cambiar el
     tamaño de trozo a 600/450/350 caracteres no corrige el fallo
     (despliegue no alcanza ni el top-12 a ningún tamaño y el resto
     de la batería apenas se mueve: en la re-comprobación limpia de
     600 y 350, REA se queda en 0,526–0,528 y el clima en 0,445), y
     repetir los títulos ×2/×3 en el embedding tampoco (despliegue
     seguía fuera del top-12 y REA caía a 0,465 con ×3), así que no
     se aplicaron. Corrección de este mismo registro: una primera
     corrida de este experimento devolvió cifras distintas (clima
     0,565 a 350, REA 0,485 a 600) que NO se reprodujeron al
     repetirlo de forma limpia; valen las de la re-comprobación.
- **Cambio (dos piezas acotadas):**
  - `rag_core.py` · troceado: la línea de encabezado se separa del
    cuerpo antes de trocear y cada fragmento Markdown lleva
    antepuestos el título del documento y el de su sección (contexto
    que se vectoriza y se cita). Re-ingesta: 135 → 116 fragmentos
    (0 de solo encabezado; el 100 % contiene su título de sección);
    nuevos MD5: `data/index.faiss`
    `08a10a5845fcbbb662e67933d1fb7e38`, `data/chunks.json`
    `3574cc228e222a3c876a95c4c2edbbea`, `data/meta.json`
    `4659fa0322ea6b52f859d75b112e2bd2` (antes `5673a3c0…`,
    `93a2488f…`, `eaacd28b…`); mismos 12 documentos.
  - `rag_core.py` · recuperación híbrida acotada: sobre los
    candidatos que superan el suelo semántico 0,30 (se examinan
    todos los fragmentos) se reordena sumando coincidencia léxica de
    raíces entre la pregunta y los metadatos (archivo + sección,
    peso 0,30) y el texto (peso 0,10). La `similitud` devuelta sigue
    siendo la semántica pura, cada resultado lleva además
    `relevancia` y `similitud_maxima`, y la puerta de claridad 0,50
    del Ciclo 1 no cambia: `app.py` la aplica a la mejor similitud
    semántica de la consulta en todo el corpus (antes era la del
    primer resultado, equivalente cuando no había reordenación).
- **Verificaciones:**
  1. `py_compile` limpio en los 3 módulos.
  2. Smoke real (batería completa por la API, servidor levantado y
     apagado después): despliegue → `despliegue.md` en las
     posiciones 1–3 de las fuentes, `confianza: "alta"`,
     `similitud_maxima` 0,502; REA → `ingenieria-inversa.md` 1.ª
     (0,526, alta); automatizaciones → su análisis, las 4 fuentes
     (0,697, alta); 45/90 → `comparacion-prompts-45-vs-90.md`, las
     4 fuentes (0,588, alta — antes de este ciclo esta formulación
     puntuaba 0,463 y quedaba bajo la puerta). Controles extra:
     diseño CenteIA (0,707) y agentes (0,736) recuperan su documento
     en 1.er lugar. Fuera de tema, todo sigue «sin resultados
     claros»: capital de Francia → `confianza: "baja"` sin fuentes
     (ningún fragmento ≥ 0,30); clima → baja (0,445); texto basura →
     baja (0,342); lorem ipsum → baja (0,496; en el Ciclo 1 se
     colaba con 0,52).
  3. Checklist de detalle y comparación contra el estado anterior:
     los artefactos se verificaron por contenido (conteos de
     fragmentos por documento coherentes, 0 fragmentos de solo
     encabezado, títulos presentes en el 100 % de los fragmentos) y
     no solo por MD5; el README se reescribió con la calibración
     nueva y el caso especial del despliegue explicado; sin
     regresiones en la validación del Ciclo 1 (ver RAG-M1).
- **Hallazgo / riesgo anotado (severidad baja, mitigado):** la
  reordenación depende de los metadatos —si un documento se
  renombra o sus secciones se retitulan, su recuperación léxica
  cambia aunque el contenido sea el mismo— y examina todos los
  fragmentos en cada pregunta, viable con 116 fragmentos pero no a
  escala grande. Mitigación: pesos y criterio están documentados en
  `rag_core.py` y en el README (la «Ruta de mejora» pide ya un BM25
  completo si el corpus crece), la puerta de claridad sigue siendo
  puramente semántica, y la batería de preguntas de este ciclo queda
  como referencia para detectar regresiones. Residuo honesto: la
  respuesta de despliegue incluye como 4.ª fuente un fragmento de
  `analisis.md` (0,502) que no es del tema; las posiciones 1–3 ya
  son el documento correcto.

## 2026-11-02 · Fase 2, Ciclo 1 (hallazgos ALTA de la revisión 2026-11-02)

### RAG-A1 — `/preguntar` devolvía 500 HTML con `pregunta` no-string

- **Hallazgo:** `app.py` hacía `(data.get("pregunta") or "").strip()` sin
  validar el tipo: un entero, una lista o un cuerpo que no fuera un
  objeto JSON provocaban una excepción y un 500 en HTML. La validación
  solo cubría vacío/ausente.
- **Cambio:** validación completa antes de tocar el índice, siempre con
  `400` y error en JSON: cuerpo que no es un objeto JSON → 400; campo
  ausente o `null` → 400 «Falta el campo 'pregunta'.»; tipo distinto de
  cadena → 400 «debe ser una cadena de texto»; cadena vacía o solo
  espacios → 400; longitud mayor de 1000 caracteres (`MAX_PREGUNTA`) →
  400 «demasiado larga».
- **Verificaciones:**
  1. `py_compile` limpio en `app.py`, `rag_core.py` e `ingest.py`.
  2. Smoke real con el servidor levantado: `pregunta` entera, ausente,
     vacía, como lista, cuerpo JSON como lista, cuerpo sin JSON y
     pregunta de 1001 caracteres → los 7 casos devolvieron `400` con
     `Content-Type: application/json` y mensaje claro; ningún 500.
     Servidor apagado al terminar (puerto 5057 sin respuesta).
  3. Checklist de detalle: mensajes nuevos con ortografía cuidada
     («vacío», «máximo», «cadena de texto»); el README documenta ahora
     el tipo exigido y el límite de 1000 caracteres; sin regresiones en
     `/api/health` ni en las preguntas válidas.

### RAG-A2 — El umbral 0,20 rellenaba respuestas fuera de tema

- **Hallazgo:** el README prometía que una pregunta fuera de tema no
  rellena («hay umbral de similitud, y por debajo de él la API lo dice»),
  pero con el umbral en 0,20 el texto basura puntuaba 0,35–0,41 y se
  devolvían fragmentos sin relación como si fueran la respuesta.
- **Calibración (pruebas reales sobre el corpus, similitud máxima por
  consulta):** dentro de tema 0,44–0,74 (REA 0,636; diseño CenteIA
  0,744; agentes 0,595); fuera de tema y basura 0,41–0,46 (basura
  0,414–0,437; clima 0,457; capital de Francia 0,262); un lorem ipsum
  llegó a 0,522. Conclusión: ningún umbral único separa limpiamente, así
  que se aplica una política de dos niveles y se documenta el límite.
- **Cambio:**
  - `rag_core.py`: constantes `UMBRAL_SIMILITUD = 0.30` (suelo duro de
    fragmentos, antes 0,20) y `UMBRAL_CLARO = 0.50` (puerta de claridad
    sobre la mejor similitud), con el criterio y las mediciones en un
    comentario; nueva función `compose_sin_resultados_claros()` con el
    texto «Sin resultados claros en tus documentos para esa pregunta…»
    y el detalle de la similitud alcanzada.
  - `app.py`: si no hay resultados o la similitud máxima es < 0,50, la
    respuesta es ese texto honesto, con `fuentes: []`,
    `confianza: "baja"` y `similitud_maxima`; si es ≥ 0,50, respuesta
    normal con `confianza: "alta"`.
  - `README.md`: diagrama actualizado (0,30 / 0,50) y el apartado
    «Límites honestos» reescrito con la política real, el solape medido
    0,44–0,50 y el contraejemplo del lorem ipsum (0,52).
- **Verificaciones:**
  1. `py_compile` limpio en los 3 módulos (repetido tras el ajuste
     ortográfico de decimales con coma en los textos nuevos).
  2. Smoke real con el servidor levantado: pregunta válida conocida
     («¿Qué es REA y para qué sirve?») → 200, `confianza: "alta"`,
     similitud máxima 0,636 y 4 fuentes con la fuente correcta citada;
     «¿Cuál es la capital de Francia?» → `confianza: "baja"`, sin
     fuentes y texto «sin resultados claros»; texto basura
     («asdf qwer zxcv jkl», 0,407) → lo mismo; el antiguo falso positivo
     del clima (0,457) → también «baja», sin rellenar. Servidor apagado
     al terminar (puerto 5057 sin respuesta, comprobado).
  3. Checklist de detalle: ortografía y decimales con coma («0,407»,
     «0,50») en los textos nuevos; README y comportamiento coinciden;
     la respuesta válida de REA conserva sus 4 fragmentos (el suelo
     0,30 no recorta el contexto útil) y no se detectaron regresiones.

## 2026-11-02 · Fase 2, Ciclo 5 (refresco del corpus: los registros de mejora de la Fase 2)

### Refresco del corpus — la demo ya responde también sobre el trabajo de mejora

- **Objetivo:** el corpus eran 12 documentos (materiales CenteIA +
  aprendido de mundo-dirsi). Este ciclo suma los `improvement-log.md`
  de las apps mejoradas en la Fase 2, para que el proyecto de
  portafolio responda también sobre ese trabajo.
- **Mecanismo (sin re-arquitectura):** la ingesta ya aceptaba carpetas
  a medida (`ingest.py carpeta1 carpeta2…`), pero solo lee el primer
  nivel de cada carpeta y los 16 registros viven en carpetas distintas
  con el mismo nombre de archivo. Solución: carpeta `corpus-extra/`
  dentro del proyecto, generada por el script reproducible nuevo
  **`refresh_corpus_extra.py`**: copia cada registro con un nombre por
  app (`barberia-improvement-log.md`, `tx-builder-improvement-log.md`,
  … —el nombre forma parte de los metadatos citados y de la
  coincidencia léxica de títulos—), verifica cada copia por MD5 contra
  su original y borra de la carpeta cualquier `.md` que ya no esté en
  su lista (idempotente, sin acumulación manual). El README documenta
  cómo se generó y cómo se refresca. Ingesta ejecutada con las tres
  carpetas (las dos por defecto + `corpus-extra/`).
- **Ajuste por degradación (medido, no a ciegas):** la primera
  re-ingesta incluyó los 16 registros (28 documentos, 402 fragmentos)
  y la batería detectó la regresión prevista: «¿Cómo se despliega una
  aplicación?» bajó a despliegue.md a las posiciones 3–4, porque el
  fragmento ganador pasaba a ser el del **propio registro del
  rag-demo** —su sección RAG-M2 se titula literalmente con esa
  pregunta y se llevaba la bonificación máxima de título (relevancia
  0,77 frente a 0,57 de despliegue.md)—. Es un documento
  autorreferente: indexarlo contamina la batería que él mismo
  documenta. **Ajuste aplicado:** el registro propio queda EXCLUIDO
  de `corpus-extra/` (decisión y motivo escritos en el propio script
  y en el README); su trabajo se sigue contando en este registro,
  solo no se auto-indexa. Re-ingesta final: **27 documentos,
  409 fragmentos** (116 del corpus inicial + 293 de los 15 registros;
  conteos por archivo verificados contra `data/chunks.json`).
  Nota de proceso: entre la primera y la segunda copia, registros de
  otras apps recibieron sus entradas del Ciclo 5 (trabajo concurrente
  del coordinador, mtimes 22:28–22:30 UTC); la segunda copia los
  recogió y una tercera ejecución del script confirmó «sin deriva»
  (copias idénticas a los originales ingeridos).
- **Verificaciones:**
  1. `py_compile` limpio en `app.py`, `rag_core.py`, `ingest.py` y
     `refresh_corpus_extra.py`.
  2. Smoke real con el servidor levantado (modelo cargado en el
     arranque en 23,5 s): `/api/health` → `estado: "ok"`,
     `modelo_cargado: true`, **27 documentos, 409 fragmentos**,
     coherentes con `data/meta.json` y con los documentos realmente
     ingeridos. **Batería completa por la API:**
     - REA («¿Qué es REA y para qué sirve?») → `ingenieria-inversa.md`
       en 1.ª posición, similitud 0,526, `confianza: "alta"` —idéntica
       a la del conocido-bueno—.
     - Automatizaciones («¿Qué automatizaciones presenta la guía de
       CenteIA y cómo se venden?») → las 4 fuentes de
       `automatizaciones-analisis.md`, similitud máxima 0,699, alta.
     - 45/90 («¿Los 45 prompts son un subconjunto de los 90
       prompts?») → las 4 fuentes de
       `comparacion-prompts-45-vs-90.md`, máxima 0,669, alta.
     - Despliegue («¿Cómo se despliega una aplicación?») →
       `despliegue.md` en las posiciones **1–3** (patrón exacto del
       conocido-bueno de los Ciclos 2–3, con la 4.ª fuente de
       `analisis.md` y máxima 0,502), alta. La degradación de la
       primera re-ingesta quedó revertida con el ajuste de arriba.
     - NUEVA · Barbería («¿Qué se arregló en el Ciclo 1 de la
       barbería?») → las 4 fuentes son
       `corpus-extra/barberia-improvement-log.md`, máxima 0,557,
       alta. Matiz honesto (también en el README): la recuperación es
       a nivel de documento; los fragmentos que encabezan son de
       otras secciones del mismo registro (los arreglos del Ciclo 1
       viven en secciones A1/A2/A3… sin la frase «Ciclo 1»).
     - NUEVA · Tx-builder («¿Qué direcciones se cambiaron en
       tx-builder?») → las 4 fuentes de
       `corpus-extra/tx-builder-improvement-log.md`, posiciones 1–3
       en su sección exacta (T-A1, direcciones canónicas), máxima
       0,522, alta.
     - Fuera de tema: capital de Francia → `confianza: "baja"`, sin
       fuentes (ningún fragmento ≥ 0,30); clima («¿Qué tiempo hará
       mañana?») → baja, máxima 0,320, sin fuentes. Ambos con el
       texto «sin resultados claros».
     Servidor apagado al terminar (puerto 5057 sin respuesta,
     comprobado).
  3. Por contenido (V3) y comparación contra conocidos-buenos: la
     respuesta de tx-builder **cita el registro correcto y el
     fragmento citado [1] contiene la dirección nueva de Ana**
     (`0x48227ad1…4678`) de la sección T-A1; la de la barbería cita su
     registro en las 4 fuentes. Artefactos: los MD5 nuevos
     (`data/index.faiss` `94294e24d43bc9bb65f69d7692e84050`,
     `data/chunks.json` `5a58d3e49f59aefab327d75fd948993d`,
     `data/meta.json` `2a280426fda50d3f7dbf523ef8b78bd0`) difieren de
     los de los Ciclos 2–3 (`08a10a58…`, `3574cc22…`, `4659fa03…`)
     exactamente por la re-ingesta con 15 documentos más, verificado
     por contenido (27 archivos en `meta.json`, 409 fragmentos que
     suman por archivo: 116 originales + 293 nuevos). Sin cambios en
     `rag_core.py` ni en `app.py` en este ciclo: solo corpus, script
     de refresco, README y este registro.

- **Cierre de ciclo (coordinación):** la auditoría de veracidad de
  README del Ciclo 5 anotó sin corregir que el `503` de `/preguntar`
  sin índice no estaba documentado (omisión, no afirmación falsa).
  Corregido en el README: `/preguntar` responde `503` en JSON si el
  índice no existe y `/api/health` lo refleja con
  `estado: "sin_indice"` (comportamiento verificado en `app.py`).
  Nota de publicación: `data/index.faiss` es binario y el conector de
  GitHub solo admite instantáneas UTF-8, así que el índice no viaja en
  el commit; se regenera con `python ingest.py` (chunks.json y
  meta.json sí se publican).
