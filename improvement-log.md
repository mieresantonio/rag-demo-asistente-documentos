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

## 2026-11-02 · Fase 2, Ciclo 7 (segundo refresco del corpus: las entradas del Ciclo 6)

### Segundo refresco — las copias de nft-studio, tx-builder y block-explorer al día

- **Objetivo:** tras la copia del Ciclo 5, los registros de
  nft-studio, tx-builder y block-explorer recibieron sus entradas del
  Ciclo 6 (alineaciones de versiones y bajas E-B2/B4/B7), así que sus
  copias en `corpus-extra/` estaban desactualizadas respecto a los
  originales. Este ciclo las refresca con el mismo mecanismo del
  Ciclo 5, sin tocar código.
- **Refresco (`refresh_corpus_extra.py`, idempotente, con
  verificación MD5 de cada copia contra su original):** cambiaron
  **exactamente las tres copias esperadas** —comparación MD5 de toda
  la carpeta contra el estado del Ciclo 5, las otras 12 copias
  quedaron byte-idénticas—:
  - `nft-studio-improvement-log.md`: `71bb67da…` → `13b09e70…`
    (entrada N-B8: alineación a React 18.3.1 / Vite 6.4.5).
  - `tx-builder-improvement-log.md`: `defe7bab…` → `3d78a61b…`
    (alineación de Vite 5.4.21 → 6.4.5, GR-2).
  - `block-explorer-improvement-log.md`: `5fd1de92…` → `35d4bf4d…`
    (bajas E-B2, E-B4 y E-B7).
  La exclusión del registro propio del rag-demo se mantiene, por el
  motivo documentado en el Ciclo 5 (autorreferencia).
- **Re-ingesta:** mismos 27 documentos, **409 → 432 fragmentos**
  (+23), con el delta explicado por archivo y solo por archivo
  (verificado contra `data/chunks.json`): block-explorer 12 → 22
  (+10), nft-studio 18 → 25 (+7), tx-builder 12 → 18 (+6); los
  fragmentos de los otros 24 archivos son idénticos a los del
  Ciclo 5, y dentro de los tres archivos actualizados los fragmentos
  previos también son idénticos: los nuevos son solo las secciones
  del Ciclo 6 añadidas al final de cada registro.
- **Verificaciones (triple reforzada):**
  1. `py_compile` limpio en `app.py`, `rag_core.py`, `ingest.py` y
     `refresh_corpus_extra.py`.
  2. Batería completa por la API real, con el servidor levantado
     (modelo cargado en el arranque en 24,5 s): `/api/health` →
     `estado: "ok"`, `modelo_cargado: true`, **27 documentos,
     432 fragmentos**, coherentes con `data/meta.json`. Resultados,
     todos con el patrón conocido-bueno del Ciclo 5:
     - REA → `ingenieria-inversa.md` en 1.ª posición, 0,526, alta.
     - Automatizaciones → las 4 fuentes de
       `automatizaciones-analisis.md`, máxima 0,699, alta.
     - 45/90 → las 4 fuentes de `comparacion-prompts-45-vs-90.md`,
       máxima 0,669, alta.
     - Despliegue → `despliegue.md` en las posiciones **1–3**
       (invariante crítico intacto), 4.ª fuente de `analisis.md`,
       máxima 0,502, alta.
     - Barbería (Ciclo 1) → las 4 fuentes de su registro en
       `corpus-extra/`, máxima 0,557, alta (recuperación a nivel de
       documento, como ya se documentó en el Ciclo 5).
     - Tx-builder → posiciones 1–3 en su sección exacta (T-A1,
       direcciones), máxima 0,522, alta; la 4.ª fuente es ahora la
       sección nueva del Ciclo 6 del mismo registro (esperado: es
       contenido nuevo del documento correcto, no una degradación).
     - Fuera de tema: capital de Francia → baja, sin fuentes
       (ningún fragmento ≥ 0,30); clima → baja, máxima 0,320, sin
       fuentes.
     - NUEVA · Ciclo 6 («¿A qué versiones se alineó nft-studio en
       el Ciclo 6?») → las 4 fuentes son el registro de nft-studio,
       posiciones 1, 2 y 4 en su sección exacta del Ciclo 6 (N-B8),
       máxima 0,570, alta, y la respuesta contiene las versiones
       alineadas (react/react-dom 18.3.1, vite 6.4.5,
       plugin-react 4.7.0, lucide-react 0.469.0). Matiz honesto: la
       3.ª fuente es la sección «Pendiente» del mismo registro, que
       mencionaba N-B8 como pendiente en un ciclo anterior; la
       recuperación es del documento correcto.
     Sin degradación en ninguna pregunta: **no hizo falta revertir**
     la re-ingesta. Servidor apagado al terminar (puerto 5057 sin
     respuesta, comprobado).
  3. Por contenido (V3): artefactos nuevos — `data/index.faiss`
     `51893148864f5422f7927db17420ed3a`, `data/chunks.json`
     `cd09ca8226b9c689214b331c5005b9d8`, `data/meta.json`
     `5da6eb6b9457673f3902add0b14819ae` — frente a los del Ciclo 5
     (`94294e24…`, `5a58d3e4…`, `2a280426…`), con el delta explicado
     solo por las tres copias actualizadas (suma de fragmentos por
     archivo, arriba). El fragmento [1] de tx-builder en
     `chunks.json` sigue conteniendo la dirección nueva de Ana
     (`0x48227ad1…4678`) de la sección T-A1, idéntico al del Ciclo 5
     (el extracto renderizado en la respuesta empieza a media altura
     del fragmento, como ya hacía la composición extractiva). Sin
     cambios en `rag_core.py` ni en `app.py`: solo las tres copias
     de `corpus-extra/`, los artefactos de `data/`, el README
     (conteos 27/432 y calibración re-verificada) y este registro.
     Nota de publicación: `data/index.faiss` no se publica (binario);
     se regenera con `python ingest.py`.

## 2026-11-02 · Fase 2, Ciclo 9 (tercer refresco del corpus: las entradas de los Ciclos 7 y 8)

### Tercer refresco — seis copias al día: tres del Ciclo 7 y tres del Ciclo 8

- **Objetivo:** tras la copia del Ciclo 7, varios registros recibieron
  entradas nuevas de los Ciclos 7 y 8, así que sus copias en
  `corpus-extra/` estaban desactualizadas respecto a los originales.
  Este ciclo las refresca con el mismo mecanismo de los Ciclos 5 y 7,
  sin tocar código.
- **Refresco (`refresh_corpus_extra.py`, idempotente, con
  verificación MD5 de cada copia contra su original):** cambiaron
  **exactamente las seis copias esperadas** —comparación MD5 de toda
  la carpeta contra el estado del Ciclo 7; las otras 9 copias
  quedaron byte-idénticas y cada copia nueva coincide por MD5 con
  su original—:
  - `api-segundo-yo-improvement-log.md`: `9eb07f47…` → `848d8e2e…`
    (Ciclo 7: documentación integrada — los errores 405 y 500 que
    faltaban en el `DOCS_HTML` que sirve la propia app). Nota: esta
    app SÍ forma parte de `corpus-extra/` —está en la lista
    `SOURCES` del script desde el Ciclo 5—; lo que no tiene es un
    corpus propio que ingerir, y eso no la excluye del refresco.
  - `nft-studio-improvement-log.md`: `13b09e70…` → `8d0d698b…`
    (Ciclo 7: suelo de tests de la capa de datos,
    `scripts/verify-data.mjs` con 155 comprobaciones).
  - `block-explorer-improvement-log.md`: `35d4bf4d…` → `5e701d51…`
    (Ciclo 7: suelo de tests de la capa de datos,
    `scripts/verify-data.mjs` con 157 comprobaciones).
  - `gas-calc-improvement-log.md`: `6c830f1c…` → `263aead9…`
    (Ciclo 8: suelo de tests para el cálculo de gas,
    `scripts/verify-data.mjs` con 47 comprobaciones).
  - `hash-lab-improvement-log.md`: `66a8cf83…` → `faf6350c…`
    (Ciclo 8: suelo de tests para el hash y la mini-cadena,
    `scripts/verify-data.mjs` con 54 comprobaciones).
  - `mundo-vida-ia-improvement-log.md`: `5524cc17…` → `2e56bd99…`
    (Ciclo 8: suite permanente con `unittest`, 20 tests en 6 clases
    que fijan los invariantes de los Ciclos 1–5; en este registro la
    entrada nueva va al principio, no al final).
  Los seis cambios son añadidos puros de la sección de su ciclo
  (verificado por `diff` contra las copias del Ciclo 7): ningún
  original perdió ni alteró contenido previo, y no cambió ninguna
  copia inesperada. La exclusión del registro propio del rag-demo
  se mantiene, por el motivo documentado en el Ciclo 5
  (autorreferencia).
- **Re-ingesta:** mismos 27 documentos, **432 → 467 fragmentos**
  (+35), con el delta explicado por archivo y solo por archivo
  (verificado contra `data/chunks.json`): api-segundo-yo 23 → 28
  (+5), block-explorer 22 → 26 (+4), nft-studio 25 → 30 (+5),
  gas-calc 10 → 16 (+6), hash-lab 20 → 26 (+6), mundo-vida-ia
  24 → 33 (+9); los fragmentos de los otros 21 archivos son
  idénticos en número a los del Ciclo 7.
- **Verificaciones (triple reforzada):**
  1. `py_compile` limpio en `app.py`, `rag_core.py`, `ingest.py` y
     `refresh_corpus_extra.py`.
  2. Batería completa por la API real, con el servidor levantado
     (modelo cargado en el arranque en 29,5 s): `/api/health` →
     `estado: "ok"`, `modelo_cargado: true`, **27 documentos,
     467 fragmentos**, coherentes con `data/meta.json`. Resultados,
     todos con el patrón conocido-bueno de los Ciclos 5 y 7:
     - REA → `ingenieria-inversa.md` en 1.ª posición, 0,526, alta.
     - Automatizaciones → las 4 fuentes de
       `automatizaciones-analisis.md`, máxima 0,699, alta.
     - 45/90 → las 4 fuentes de `comparacion-prompts-45-vs-90.md`,
       máxima 0,669, alta.
     - Despliegue → `despliegue.md` en las posiciones **1–3**
       (invariante crítico intacto), 4.ª fuente de `analisis.md`,
       máxima 0,502, alta.
     - Barbería (Ciclo 1) → las 4 fuentes de su registro en
       `corpus-extra/`, máxima 0,557, alta (recuperación a nivel
       de documento, como ya se documentó en el Ciclo 5).
     - Tx-builder → posiciones 1–3 en su sección exacta (T-A1,
       direcciones), máxima 0,522, alta; la 4.ª fuente sigue
       siendo la sección del Ciclo 6 del mismo registro.
     - Nft-studio (Ciclo 6) → las 4 fuentes son su registro,
       máxima 0,570, alta; posiciones 1–2 en su sección exacta
       (N-B8) y la 4.ª la sección «Pendiente» que ya daba la
       máxima en el Ciclo 7. Matiz honesto: la 3.ª fuente es
       ahora la sección nueva del Ciclo 7 (suelo de tests) del
       mismo registro —contenido nuevo del documento correcto,
       no una degradación—.
     - Fuera de tema: capital de Francia → baja, sin fuentes
       (ningún fragmento ≥ 0,30); clima → baja, máxima 0,320,
       sin fuentes.
     - NUEVA · Ciclo 8 («¿Qué tests se añadieron a mundo-vida-ia
       en el Ciclo 8?») → las 4 fuentes son el registro de
       mundo-vida-ia, las 4 en su sección exacta del Ciclo 8
       («La suite — los invariantes de los ciclos 1-5…»),
       máxima 0,562, alta, y la respuesta cita la suite
       (`unittest`, 20 tests).
     Sin degradación en ninguna pregunta: **no hizo falta
     revertir** la re-ingesta. Servidor apagado al terminar
     (puerto 5057 sin respuesta, comprobado).
  3. Por contenido (V3): artefactos nuevos — `data/index.faiss`
     `927ef91306ec7d766f65f482b536e19b`, `data/chunks.json`
     `416b9ac777a24dbb02633ff12806f2e1`, `data/meta.json`
     `a2652889734194e41b03e85817e36803` — frente a los del Ciclo 7
     (`51893148…`, `cd09ca82…`, `5da6eb6b…`), con el delta
     explicado solo por las seis copias actualizadas (suma de
     fragmentos por archivo, arriba). El fragmento de tx-builder
     con la dirección nueva de Ana (`0x48227ad1…4678`) de la
     sección T-A1 sigue presente en `chunks.json`, idéntico al de
     los Ciclos 5 y 7. Sin cambios en `rag_core.py` ni en
     `app.py`: solo las seis copias de `corpus-extra/`, los
     artefactos de `data/`, el README (conteos 27/467, calibración
     re-verificada y la pregunta nueva del Ciclo 8) y este
     registro. Nota de publicación: `data/index.faiss` no se
     publica (binario); se regenera con `python ingest.py`.

- **Lista para publicar (la publica el coordinador):**
  `corpus-extra/api-segundo-yo-improvement-log.md`,
  `corpus-extra/block-explorer-improvement-log.md`,
  `corpus-extra/gas-calc-improvement-log.md`,
  `corpus-extra/hash-lab-improvement-log.md`,
  `corpus-extra/mundo-vida-ia-improvement-log.md`,
  `corpus-extra/nft-studio-improvement-log.md`,
  `data/chunks.json`, `data/meta.json`, `README.md` e
  `improvement-log.md`. `data/index.faiss` NO viaja (binario; se
  regenera con `python ingest.py`).

## 2026-11-02 · Fase 2, Ciclo 10 (cuarto refresco del corpus: las entradas del Ciclo 9)

### Cuarto refresco — cinco copias al día: el suelo de tests web3 del Ciclo 9

- **Objetivo:** tras la copia del Ciclo 9, los registros de las cinco
  web3 restantes recibieron sus entradas del Ciclo 9 (suelo de tests
  permanente en cada una), así que sus copias en `corpus-extra/`
  estaban desactualizadas respecto a los originales. Este ciclo las
  refresca con el mismo mecanismo de los Ciclos 5, 7 y 9, sin tocar
  código. Respaldo previo del estado del Ciclo 9 (artefactos de
  `data/`, las 15 copias de `corpus-extra/`, README y este registro)
  en `/tmp/rag-demo-ciclo10-backup/`, antes de tocar nada.
- **Refresco (`refresh_corpus_extra.py`, idempotente, con
  verificación MD5 de cada copia contra su original):** cambiaron
  **exactamente las cinco copias esperadas** —comparación MD5 de
  toda la carpeta contra el estado del Ciclo 9 y contraste previo
  copia↔original archivo a archivo; las otras 10 copias quedaron
  byte-idénticas y cada copia nueva coincide por MD5 con su
  original—:
  - `wallet-sim-improvement-log.md`: `7ec9d23d…` → `dde6c1d9…`
    (Ciclo 9: WALLET-C9-1, suelo de tests `scripts/verify-data.mjs`
    con 60 comprobaciones, importando el módulo real `src/state.js`).
  - `token-explorer-improvement-log.md`: `7b049628…` → `2c1de334…`
    (Ciclo 9: TOKEN-C9-1, suelo de tests con 137 comprobaciones
    sobre el módulo real `src/data.js`).
  - `contract-play-improvement-log.md`: `b437628f…` → `087489fc…`
    (Ciclo 9: suelo de tests con 43 comprobaciones, extrayendo y
    ejecutando el simulador real desde `src/App.jsx`).
  - `dao-vote-improvement-log.md`: `5ebbd4d7…` → `0e52d126…`
    (Ciclo 9: suelo de tests con 54 comprobaciones sobre el módulo
    real `src/data.js` y anclas en `src/App.jsx`).
  - `anti-phishing-improvement-log.md`: `7b3b94d1…` → `43c94ac8…`
    (Ciclo 9: suelo de tests con 62 comprobaciones sobre el módulo
    real `src/data.js` y anclas en `src/App.jsx`).
  Los cinco cambios son añadidos puros de la sección de su ciclo al
  final de cada registro (verificado por `diff` contra las copias
  del Ciclo 9 antes del refresco): ningún original perdió ni alteró
  contenido previo, y no cambió ninguna copia inesperada. Las tres
  entradas de contract-play, dao-vote y anti-phishing traen además
  la nota de conteo del Ciclo 9: con ellas son **9 de 10** las web3
  con suelo de tests, porque tx-builder no tiene `scripts/` ni
  `test` en su `package.json` (queda constancia; no es un arreglo de
  este ciclo). La exclusión del registro propio del rag-demo se
  mantiene, por el motivo documentado en el Ciclo 5
  (autorreferencia).
- **Re-ingesta:** mismos 27 documentos, **467 → 498 fragmentos**
  (+31), con el delta explicado por archivo y solo por archivo
  (verificado contra `data/chunks.json`): anti-phishing 19 → 26
  (+7), contract-play 10 → 17 (+7), dao-vote 12 → 19 (+7),
  token-explorer 17 → 22 (+5), wallet-sim 16 → 21 (+5); los
  fragmentos de los otros 22 archivos son idénticos en número y en
  contenido a los del Ciclo 9, y dentro de los cinco archivos
  actualizados los fragmentos previos son un prefijo exacto de los
  nuevos: los nuevos son solo las secciones del Ciclo 9 añadidas.
- **Verificaciones (triple reforzada):**
  1. `py_compile` limpio en `app.py`, `rag_core.py`, `ingest.py` y
     `refresh_corpus_extra.py`.
  2. Batería completa por la API real, con el servidor levantado
     (modelo cargado en el arranque en 24,7 s): `/api/health` →
     `estado: "ok"`, `modelo_cargado: true`, **27 documentos,
     498 fragmentos**, coherentes con `data/meta.json`. Resultados,
     todos con el patrón conocido-bueno de los Ciclos 5, 7 y 9:
     - REA → `ingenieria-inversa.md` en 1.ª posición, 0,526, alta.
     - Automatizaciones → las 4 fuentes de
       `automatizaciones-analisis.md`, máxima 0,699, alta.
     - 45/90 → las 4 fuentes de `comparacion-prompts-45-vs-90.md`,
       máxima 0,669, alta.
     - Despliegue → `despliegue.md` en las posiciones **1–3**
       (invariante crítico intacto), 4.ª fuente de `analisis.md`,
       máxima 0,502, alta.
     - Barbería (Ciclo 1) → las 4 fuentes de su registro en
       `corpus-extra/`, máxima 0,557, alta (recuperación a nivel
       de documento, como ya se documentó en el Ciclo 5).
     - Tx-builder → posiciones 1–3 en su sección exacta (T-A1,
       direcciones), máxima 0,522, alta; la 4.ª fuente sigue
       siendo la sección del Ciclo 6 del mismo registro.
     - Nft-studio (Ciclo 6) → máxima 0,570, alta, con las
       posiciones 1–2 en su sección exacta (N-B8). Matiz honesto:
       la 3.ª fuente es ahora la sección del Ciclo 7 (suelo de
       tests) del mismo registro —ya ocupaba ese lugar en el
       Ciclo 9— y la 4.ª es la sección nueva del Ciclo 9 de
       anti-phishing, cuyo encabezado de tests es casi idéntico al
       de nft-studio; es contenido vecino del tema, no una
       degradación de la respuesta principal.
     - Mundo-vida-ia (Ciclo 8) → las 4 fuentes son su registro,
       las 4 en su sección exacta del Ciclo 8, máxima 0,562, alta.
     - Fuera de tema: capital de Francia → baja, sin fuentes
       (ningún fragmento ≥ 0,30); clima → baja, máxima 0,320,
       sin fuentes.
     - NUEVA · Ciclo 9, el 9/10 («¿Qué app web3 no tiene suelo de
       tests en el Ciclo 9?») → las 4 fuentes son el registro de
       anti-phishing, las 4 en su sección exacta del Ciclo 9,
       máxima 0,675, alta, y la respuesta [1] contiene literal la
       explicación veraz: son 9 de 10 las web3 con suelo de tests
       porque tx-builder no tiene `scripts/` ni `test` en su
       `package.json`. Matiz honesto, medido y no escondido: la
       formulación literal «¿Por qué el conjunto web3 quedó 9/10
       y no 10/10 en el Ciclo 9?» NO recupera esa sección (trae
       fragmentos de tx-builder del Ciclo 6 y de hash-lab del
       Ciclo 5, cuyos títulos contienen «conjunto web3», máxima
       0,514, sin la explicación); la pregunta que funciona es la
       de la app que falta, y así queda documentada.
     - NUEVA · Ciclo 9, anti-phishing («¿Cuántas comprobaciones
       tiene el test de anti-phishing?») → las 4 fuentes son su
       registro, las 4 en su sección exacta del Ciclo 9, máxima
       0,597, alta; la cifra —62 comprobaciones— está en el
       fragmento completo de la fuente 4, aunque la composición
       extractiva que encabeza la respuesta no la incluye en su
       extracto (recuperación a nivel de sección, el mismo matiz
       ya documentado para la barbería).
     Sin degradación en ninguna pregunta de la batería previa:
     **no hizo falta revertir** la re-ingesta. Servidor apagado
     al terminar (puerto 5057 sin respuesta, comprobado).
  3. Por contenido (V3): artefactos nuevos — `data/index.faiss`
     `4853e88ff9377f7cdcf7c4951b6cd366`, `data/chunks.json`
     `79b732a6030e2546548d1e9c84a62a24`, `data/meta.json`
     `4a91622aa8c79333d7ad4809ab213e4e` — frente a los del Ciclo 9
     (`927ef913…`, `416b9ac7…`, `a2652889…`), con el delta
     explicado solo por las cinco copias actualizadas (suma de
     fragmentos por archivo, arriba), medidos por `md5sum` directo
     sobre los artefactos ingeridos en esta sesión. El fragmento
     de tx-builder con la dirección nueva de Ana
     (`0x48227ad1…4678`) de la sección T-A1 sigue presente en
     `chunks.json`, idéntico al de los Ciclos 5, 7 y 9. Sin
     cambios en `rag_core.py` ni en `app.py`: solo las cinco
     copias de `corpus-extra/`, los artefactos de `data/`, el
     README (conteos 27/498 y calibración re-verificada, con las
     dos preguntas nuevas del Ciclo 9 medidas) y este registro.
     Nota de publicación: `data/index.faiss` no se publica
     (binario); se regenera con `python ingest.py`.

- **Nota de concurrencia (verificada y acotada, no escondida):**
  tras la ingesta y la batería, una segunda ejecución de control
  del script detectó que dos originales habían recibido entradas
  nuevas DURANTE este ciclo (trabajo concurrente del coordinador,
  mtimes 23:17 UTC, posteriores a la ingesta de las 23:16 UTC):
  la barbería (`9e51b62d…` → `cdb05120…`: su entrada del **Ciclo
  10**, smoke permanente `scripts/smoke.py` con 56 comprobaciones)
  y tx-builder (`3d78a61b…` → `b96e9f43…`: su entrada del **Ciclo
  10**, suelo de tests con 87 comprobaciones, con la que el
  conjunto web3 pasa a 10/10). Ambas verificadas contra su
  original por `diff`: añadidos puros al final, sin pérdida de
  contenido previo. **Decisión:** quedan FUERA de este refresco —
  su alcance son las entradas del Ciclo 9, y estas dos son del
  Ciclo 10: son el material del próximo refresco (Ciclo 11)— y
  las dos copias se restauraron al estado exacto ingerido, así
  que `corpus-extra/` y el índice quedan en coherencia total
  (MD5 de las 15 copias = los de la ingesta de este ciclo). Que
  conste para el coordinador: la afirmación «9/10» de este
  registro es la veraz del Ciclo 9; a fecha de cierre de este
  ciclo ya existe la entrada que lo lleva a 10/10, aún sin
  ingerir.

- **Lista para publicar (la publica el coordinador):**
  `corpus-extra/wallet-sim-improvement-log.md`,
  `corpus-extra/token-explorer-improvement-log.md`,
  `corpus-extra/contract-play-improvement-log.md`,
  `corpus-extra/dao-vote-improvement-log.md`,
  `corpus-extra/anti-phishing-improvement-log.md`,
  `data/chunks.json`, `data/meta.json`, `README.md` e
  `improvement-log.md`. `data/index.faiss` NO viaja (binario; se
  regenera con `python ingest.py`).

## 2026-11-02 · Fase 2, Ciclo 11 (quinto refresco del corpus: las entradas del Ciclo 10)

### Quinto refresco — dos copias al día: el smoke de la barbería y el 10/10 de tx-builder

- **Objetivo:** las entradas del Ciclo 10 de la barbería y de
  tx-builder quedaron fuera del refresco del Ciclo 10 por
  concurrencia (llegaron durante aquel ciclo, con mtimes
  posteriores a su ingesta; así quedó documentado en su nota de
  concurrencia). Este ciclo las incorpora con el mismo mecanismo
  de los Ciclos 5, 7, 9 y 10, sin tocar código. Respaldo previo
  del estado del Ciclo 10 (artefactos de `data/`, las 15 copias
  de `corpus-extra/`, README y este registro) en
  `/tmp/rag-demo-ciclo11-backup/`, antes de tocar nada.
- **Refresco (`refresh_corpus_extra.py`, idempotente, con
  verificación MD5 de cada copia contra su original):** cambiaron
  **exactamente las dos copias esperadas** —contraste previo
  copia↔original archivo a archivo y comparación MD5 de toda la
  carpeta contra el estado del Ciclo 10; las otras 13 copias ya
  coincidían con su original y quedaron byte-idénticas, y cada
  copia nueva coincide por MD5 con su original—:
  - `barberia-improvement-log.md`: `9e51b62d…` → `cdb05120…`
    (Ciclo 10: smoke permanente `scripts/smoke.py` con 56
    comprobaciones contra el backend real).
  - `tx-builder-improvement-log.md`: `3d78a61b…` → `b96e9f43…`
    (Ciclo 10: suelo de tests `scripts/verify-data.mjs` con 87
    comprobaciones; era la única web3 sin suelo, así que con
    esta entrada el conjunto web3 queda 10/10).
  Los dos cambios son añadidos puros de la sección de su ciclo
  al final de cada registro (verificado por `diff` contra las
  copias del Ciclo 10 antes del refresco): ningún original
  perdió ni alteró contenido previo, y no cambió ninguna copia
  inesperada. La exclusión del registro propio del rag-demo se
  mantiene, por el motivo documentado en el Ciclo 5
  (autorreferencia).
- **Re-ingesta:** mismos 27 documentos, **498 → 513 fragmentos**
  (+15), con el delta explicado por archivo y solo por archivo
  (verificado contra `data/chunks.json`): barbería 53 → 60 (+7),
  tx-builder 18 → 26 (+8); los fragmentos de los otros 25
  archivos son idénticos en número y en contenido a los del
  Ciclo 10, y dentro de tx-builder los previos son un prefijo
  exacto de los nuevos. Matiz de troceado en la barbería,
  medido y explicado: 52 de sus 53 fragmentos previos están
  verbatim en los nuevos y el último es un prefijo estricto del
  nuevo correspondiente —solo crece 5 caracteres, el separador
  «\n\n---» que precede a la sección nueva y queda adosado al
  fragmento anterior—; no hay pérdida ni alteración de contenido.
- **Verificaciones (triple reforzada):**
  1. `py_compile` limpio en `app.py`, `rag_core.py`, `ingest.py` y
     `refresh_corpus_extra.py`.
  2. Batería completa por la API real, con el servidor levantado
     (modelo cargado en el arranque en 21,5 s): `/api/health` →
     `estado: "ok"`, `modelo_cargado: true`, **27 documentos,
     513 fragmentos**, coherentes con `data/meta.json`. Resultados,
     todos con el patrón conocido-bueno de los Ciclos 5, 7, 9 y 10:
     - REA → `ingenieria-inversa.md` en 1.ª posición, 0,526, alta.
     - Automatizaciones → las 4 fuentes de
       `automatizaciones-analisis.md`, máxima 0,699, alta.
     - 45/90 → las 4 fuentes de `comparacion-prompts-45-vs-90.md`,
       máxima 0,669, alta.
     - Despliegue → `despliegue.md` en las posiciones **1–3**
       (invariante crítico intacto), 4.ª fuente de `analisis.md`,
       máxima 0,502, alta.
     - Barbería (Ciclo 1) → las 4 fuentes de su registro en
       `corpus-extra/`, máxima 0,557, alta (recuperación a nivel
       de documento, como ya se documentó en el Ciclo 5; la
       sección nueva del Ciclo 10 entra entre las fuentes por
       relevancia, sin desplazar la máxima).
     - Tx-builder → posiciones 1–3 en su sección exacta (T-A1,
       direcciones), máxima 0,522, alta; la 4.ª fuente sigue
       siendo la sección del Ciclo 6 del mismo registro.
     - Nft-studio (Ciclo 6) → máxima 0,570, alta, con las
       posiciones 1–2 en su sección exacta (N-B8); la 3.ª sigue
       siendo la sección del Ciclo 7 del mismo registro y la 4.ª
       la del Ciclo 9 de anti-phishing, igual que en el Ciclo 10.
     - Mundo-vida-ia (Ciclo 8) → las 4 fuentes son su registro,
       las 4 en su sección exacta del Ciclo 8, máxima 0,562, alta.
     - Fuera de tema: capital de Francia → baja, sin fuentes
       (ningún fragmento ≥ 0,30); clima → baja, máxima 0,320,
       sin fuentes.
     - Oficiales del Ciclo 10, historia recuperada igual: «¿Qué
       app web3 no tiene suelo de tests en el Ciclo 9?» → las 4
       fuentes son el registro de anti-phishing en su sección
       exacta del Ciclo 9, máxima 0,675, alta, y la respuesta [1]
       contiene literal la explicación histórica (9 de 10 porque
       tx-builder no tenía `scripts/` ni `test`): es la respuesta
       del Ciclo 9 y se sigue recuperando igual, como historia,
       no como presente. «¿Cuántas comprobaciones tiene el test
       de anti-phishing?» → las 4 fuentes de su registro en la
       misma sección, máxima 0,597, alta; la cifra —62
       comprobaciones— está en los fragmentos completos de esa
       sección (verificado en `data/chunks.json`), aunque la
       composición extractiva no la encabeza, el mismo matiz ya
       documentado en el Ciclo 10.
     - NUEVA · Ciclo 10, barbería («¿Cuántas comprobaciones
       tiene el smoke de la barbería?») → las 4 fuentes son su
       registro, máxima 0,530, alta, con las fuentes 2 y 4 en su
       sección exacta del Ciclo 10 («Smoke ejecutable — los
       humos manuales de los Ciclos 1–3, fijados», 0,505), cuyo
       fragmento completo contiene las 56 comprobaciones
       (verificado en `data/chunks.json`); la máxima es de una
       sección de regresión del mismo documento, no de la del
       smoke: recuperación del documento correcto con la sección
       exacta en el top-4.
     - NUEVA · Ciclo 10, tx-builder: matiz honesto, medido y no
       escondido, en la línea del anotado en el Ciclo 10 para su
       propia formulación literal. Las dos formulaciones
       genéricas ensayadas primero NO recuperan el registro de
       tx-builder: «¿Qué app web3 completó el suelo de tests en
       el Ciclo 10?» y «¿Cuántas comprobaciones tiene el test de
       tx-builder?» traen las 4 fuentes del registro de
       anti-phishing (máximas 0,673 y 0,650), cuya nota de conteo
       del Ciclo 9 habla precisamente de tx-builder y compite
       por esas palabras. La pregunta que funciona es la que
       nombra el suelo y la app: «¿Qué suelo de tests se añadió
       a tx-builder en el Ciclo 10?» → las 4 fuentes son el
       registro de tx-builder, las 4 en su sección exacta del
       Ciclo 10, máxima 0,674, alta, y la respuesta contiene el
       10/10 y las 87 comprobaciones; también funciona «¿Qué se
       hizo en tx-builder en el Ciclo 10?» (0,513, con 87 y
       10/10 en la respuesta). Así quedan documentadas.
     Sin degradación en ninguna pregunta de la batería previa:
     **no hizo falta revertir** la re-ingesta. Servidor apagado
     al terminar (puerto 5057 sin respuesta, comprobado).
  3. Por contenido (V3): artefactos nuevos — `data/index.faiss`
     `c149c69f411c00e453b5414d4e166efb`, `data/chunks.json`
     `125903a77fc797d2244032c51d378912`, `data/meta.json`
     `20ebca631fd2770a7e509d694569afee` — frente a los del
     Ciclo 10 (`4853e88f…`, `79b732a6…`, `4a91622a…`), con el
     delta explicado solo por las dos copias actualizadas (suma
     de fragmentos por archivo, arriba), medidos por `md5sum`
     directo sobre los artefactos ingeridos en esta sesión. El
     fragmento de tx-builder con la dirección nueva de Ana
     (`0x48227ad1…4678`) de la sección T-A1 sigue presente en
     `chunks.json`, idéntico al de los Ciclos 5, 7, 9 y 10. Sin
     cambios en `rag_core.py` ni en `app.py`: solo las dos
     copias de `corpus-extra/`, los artefactos de `data/`, el
     README (conteos 27/513 y calibración re-verificada, con las
     preguntas nuevas del Ciclo 10 medidas) y este registro.
     Nota de publicación: `data/index.faiss` no se publica
     (binario); se regenera con `python ingest.py`.

- **Nota de concurrencia (verificada y acotada, no escondida):**
  tras la ingesta y la batería, la segunda ejecución de control
  del script detectó que el original de la barbería había
  recibido una entrada nueva DURANTE este ciclo (trabajo
  concurrente del coordinador, mtime 23:24 UTC, posterior a la
  copia ingerida): su entrada del **Ciclo 11** (verificación
  cruzada frontend↔backend, `scripts/verify-catalog.py` con 20
  comprobaciones), `cdb05120…` → `406fca2f…`. Verificado contra
  su original: añadido puro al final —el contenido ingerido es
  un prefijo byte-exacto de 35 996 bytes del original actual
  (43 051)— y ningún fragmento de esa entrada está en el índice
  (0 apariciones de `verify-catalog` en `data/chunks.json`).
  **Decisión:** queda FUERA de este refresco —su alcance son las
  entradas del Ciclo 10, y esta es del Ciclo 11: es material del
  próximo refresco (Ciclo 12)— y la copia se restauró al estado
  exacto ingerido (restauración probada por MD5: la copia vuelve
  a ser `cdb05120…`), así que `corpus-extra/` y el índice quedan
  en coherencia total (MD5 de las 15 copias = los de la ingesta
  de este ciclo). Que conste para el coordinador: a fecha de
  cierre de este ciclo ya existe la entrada del Ciclo 11 de la
  barbería, aún sin ingerir.

- **Lista para publicar (la publica el coordinador):**
  `corpus-extra/barberia-improvement-log.md`,
  `corpus-extra/tx-builder-improvement-log.md`,
  `data/chunks.json`, `data/meta.json`, `README.md` e
  `improvement-log.md`. `data/index.faiss` NO viaja (binario; se
  regenera con `python ingest.py`).

## 2026-11-02 · Fase 2, Ciclo 12 (sexto refresco del corpus: la entrada del Ciclo 11 de la barbería)

### Sexto refresco — una copia al día: la verificación cruzada de la barbería

- **Objetivo:** la entrada del Ciclo 11 de la barbería quedó fuera
  del refresco del Ciclo 11 por concurrencia (llegó durante aquel
  ciclo, con mtime posterior a su ingesta; así quedó documentado
  en su nota de concurrencia, con la copia restaurada al estado
  del Ciclo 10). Este ciclo la incorpora con el mismo mecanismo
  de los Ciclos 5, 7, 9, 10 y 11, sin tocar código. Respaldo
  previo del estado del Ciclo 11 (artefactos de `data/`, las 15
  copias de `corpus-extra/`, README y este registro) en
  `/tmp/rag-demo-ciclo12-backup/`, antes de tocar nada.
- **Refresco (`refresh_corpus_extra.py`, idempotente, con
  verificación MD5 de cada copia contra su original):** cambió
  **exactamente la única copia esperada** —contraste previo
  copia↔original archivo a archivo: las otras 14 copias ya
  coincidían con su original antes del refresco; ninguna otra app
  recibió entradas en el Ciclo 11—:
  - `barberia-improvement-log.md`: `cdb05120…` → `406fca2f…`
    (Ciclo 11: verificación cruzada frontend↔backend,
    `scripts/verify-catalog.py` permanente con 20
    comprobaciones; conclusión del registro: deriva real
    ninguna).
  El cambio es un añadido puro de la sección de su ciclo al
  final del registro (verificado por `diff` contra la copia del
  Ciclo 11 antes del refresco y por prefijo byte-exacto: el
  contenido ingerido en el Ciclo 11 son los primeros 35 996
  bytes del original actual, de 43 051): ningún original perdió
  ni alteró contenido previo, y no cambió ninguna copia
  inesperada. La exclusión del registro propio del rag-demo se
  mantiene, por el motivo documentado en el Ciclo 5
  (autorreferencia).
- **Re-ingesta:** mismos 27 documentos, **513 → 527 fragmentos**
  (+14), con el delta explicado por archivo y solo por archivo
  (verificado contra `data/chunks.json`): barbería 60 → 74
  (+14); los fragmentos de los otros 26 archivos son idénticos
  en número y en contenido a los del Ciclo 11, y dentro de la
  barbería los 60 fragmentos previos están verbatim en los
  nuevos: los 14 nuevos son solo la sección del Ciclo 11
  añadida. Nota de proceso, verificada y sin efecto en el
  resultado: la primera ingesta de este ciclo corrió en segundo
  plano y su salida no se capturó, así que se lanzó una segunda;
  ambas escribieron artefactos idénticos bit a bit (mismos MD5,
  comprobados entre una y otra), la ingesta es determinista
  sobre el mismo corpus.
- **Verificaciones (triple reforzada):**
  1. `py_compile` limpio en `app.py`, `rag_core.py`, `ingest.py` y
     `refresh_corpus_extra.py`.
  2. Batería completa por la API real, con el servidor levantado
     (modelo cargado en el arranque en 25,4 s): `/api/health` →
     `estado: "ok"`, `modelo_cargado: true`, **27 documentos,
     527 fragmentos**, coherentes con `data/meta.json`.
     Resultados, todos con el patrón conocido-bueno de los
     Ciclos 5, 7, 9, 10 y 11:
     - REA → `ingenieria-inversa.md` en 1.ª posición, 0,526, alta.
     - Automatizaciones → las 4 fuentes de
       `automatizaciones-analisis.md`, máxima 0,699, alta.
     - 45/90 → las 4 fuentes de `comparacion-prompts-45-vs-90.md`,
       máxima 0,669, alta.
     - Despliegue → `despliegue.md` en las posiciones **1–3**
       (invariante crítico intacto), 4.ª fuente de `analisis.md`,
       máxima 0,502, alta.
     - Barbería (Ciclo 1) → las 4 fuentes de su registro en
       `corpus-extra/`, máxima 0,557, alta (recuperación a nivel
       de documento, como ya se documentó en el Ciclo 5; la
       sección nueva del Ciclo 11 entra entre las fuentes por
       relevancia, sin desplazar la máxima).
     - Tx-builder → posiciones 1–3 en su sección exacta (T-A1,
       direcciones), máxima 0,522, alta; la 4.ª fuente sigue
       siendo la sección del Ciclo 6 del mismo registro.
     - Nft-studio (Ciclo 6) → máxima 0,570, alta, con las
       posiciones 1–2 en su sección exacta (N-B8); la 3.ª sigue
       siendo la sección del Ciclo 7 del mismo registro y la 4.ª
       la del Ciclo 9 de anti-phishing, igual que en los
       Ciclos 10 y 11.
     - Mundo-vida-ia (Ciclo 8) → las 4 fuentes son su registro,
       las 4 en su sección exacta del Ciclo 8, máxima 0,562,
       alta.
     - Fuera de tema: capital de Francia → baja, sin fuentes
       (ningún fragmento ≥ 0,30); clima → baja, máxima 0,320,
       sin fuentes.
     - Oficiales de ciclos previos, recuperadas igual: «¿Qué
       app web3 no tiene suelo de tests en el Ciclo 9?» → las 4
       fuentes son el registro de anti-phishing en su sección
       exacta del Ciclo 9, máxima 0,675, alta (historia del
       Ciclo 9: 9/10 porque tx-builder no tenía suelo).
       «¿Cuántas comprobaciones tiene el test de
       anti-phishing?» → las 4 fuentes de su registro en la
       misma sección, máxima 0,597, alta; la cifra —62
       comprobaciones— está en los fragmentos completos de esa
       sección (verificado en `data/chunks.json`), el mismo
       matiz ya documentado en los Ciclos 10 y 11. «¿Cuántas
       comprobaciones tiene el smoke de la barbería?» → las 4
       fuentes son su registro, máxima 0,530, alta, con las
       fuentes 2 y 4 en su sección exacta del Ciclo 10 (0,505),
       cuyo fragmento completo contiene las 56 comprobaciones
       (verificado en `data/chunks.json`), igual que en el
       Ciclo 11. «¿Qué suelo de tests se añadió a tx-builder
       en el Ciclo 10?» (formulación oficial) → las 4 fuentes
       son el registro de tx-builder, las 4 en su sección
       exacta del Ciclo 10, máxima 0,674, alta, y la respuesta
       contiene el 10/10 y las 87 comprobaciones.
     - NUEVA · Ciclo 11, barbería («¿Qué verifica el script
       verify-catalog de la barbería?») → las 4 fuentes son su
       registro, todas en secciones de su entrada del Ciclo 11
       («Cambio — `scripts/verify-catalog.py` permanente» y
       «Triple verificación reforzada» de ese ciclo), máxima
       0,581, alta, y la respuesta [1] contiene las **20
       comprobaciones** numeradas del script. Matiz honesto,
       medido y no escondido: la frase veraz de la deriva
       («Deriva real hoy: NINGUNA») está en el fragmento
       completo de la fuente [1] en `data/chunks.json`
       (verificado), aunque el extracto que encabeza la
       composición extractiva no la incluye —recuperación a
       nivel de sección, el mismo matiz ya documentado para
       la barbería y anti-phishing—. Y la formulación
       alternativa ensayada, «¿Se encontró deriva entre el
       frontend y el backend de la barbería?», NO supera la
       puerta de claridad (máxima 0,366, `confianza: "baja"`,
       sin fuentes): la pregunta que funciona es la que nombra
       el script, y así queda documentada.
     Sin degradación en ninguna pregunta de la batería previa:
     **no hizo falta revertir** la re-ingesta. Servidor apagado
     al terminar (puerto 5057 sin respuesta, comprobado).
  3. Por contenido (V3): artefactos nuevos — `data/index.faiss`
     `e2f45d0869059b4db1099e07d2c057d5`, `data/chunks.json`
     `d6a836c94dc2b318f38674526bac830e`, `data/meta.json`
     `1daa24cc7ec45960e5fc5d703ea08155` — frente a los del
     Ciclo 11 (`c149c69f…`, `125903a7…`, `20ebca63…`), con el
     delta explicado solo por la copia actualizada (suma de
     fragmentos por archivo, arriba), medidos por `md5sum`
     directo sobre los artefactos ingeridos en esta sesión. El
     fragmento de tx-builder con la dirección nueva de Ana
     (`0x48227ad1…4678`) de la sección T-A1 sigue presente en
     `chunks.json`, idéntico al de los Ciclos 5, 7, 9, 10 y 11.
     Sin cambios en `rag_core.py` ni en `app.py`: solo la copia
     de la barbería en `corpus-extra/`, los artefactos de
     `data/`, el README (conteos 27/527 y calibración
     re-verificada, con la pregunta nueva del Ciclo 11 medida)
     y este registro. Nota de publicación: `data/index.faiss`
     no se publica (binario); se regenera con `python ingest.py`.

- **Nota de concurrencia:** la segunda ejecución de control del
  script tras la batería no detectó deriva alguna: las 15
  copias coinciden por MD5 con sus originales (15/15), así que
  a diferencia de los Ciclos 10 y 11 ningún original recibió
  entradas nuevas durante este ciclo y no queda material
  pendiente para un próximo refresco.

- **Lista para publicar (la publica el coordinador):**
  `corpus-extra/barberia-improvement-log.md`,
  `data/chunks.json`, `data/meta.json`, `README.md` e
  `improvement-log.md`. `data/index.faiss` NO viaja (binario; se
  regenera con `python ingest.py`).

## 2026-11-16 · Interfaz web mínima (segunda mitad de la ruta de mejora nº 5)

### RAG-UI — la demo solo se podía probar con curl

- **Hallazgo:** la demo no tenía ninguna interfaz visual: para
  probarla había que conocer la API y usar curl. La ruta de mejora
  nº 5 del README pedía «despliegue y una interfaz web mínima de
  chat» y la interfaz seguía pendiente.
- **Cambio:** `GET /` sirve una sola página autocontenida
  (`templates/index.html`, sin recursos externos: cero URLs
  absolutas, CSS y JS en línea) que pregunta desde el navegador y
  muestra la respuesta extractiva con sus fuentes citadas, la
  confianza y la similitud máxima. La página lee `/api/health` al
  cargar y muestra el estado real del índice (documentos,
  fragmentos, modelo); sin índice avisa y desactiva el formulario.
  El botón «Preguntar» se deshabilita con el campo vacío, hay
  contador de caracteres (máx. 1000, igual que la API), estado de
  carga, caja de error con el mensaje JSON de la API y respeto a
  `prefers-reduced-motion`. Los fragmentos se escapan antes de
  insertarlos en el DOM (vienen de los documentos). `app.py` solo
  gana la ruta y su docstring; la API no cambia: `GET /` era 404
  y ahora es la interfaz, el resto de rutas y errores en JSON
  quedan iguales. El README documenta la interfaz, la tabla de
  piezas y la ruta nº 5 (queda solo el despliegue).
- **Verificaciones:**
  1. `py_compile` limpio en `app.py`, `rag_core.py` y
     `tests_regresion_api.py`.
  2. Smoke real con el servidor levantado: `GET /` 200
     `text/html`, 12.841 bytes, cero URLs absolutas;
     `/api/health` «ok», 27/527; `POST /preguntar` con
     «¿Qué es REA y para qué sirve?» → confianza alta,
     similitud máxima 0,526 (el valor calibrado del README);
     `POST /` → 405 en JSON.
  3. Interacción real con Playwright (Chromium headless,
     script desechable): escritorio 1280×800 y móvil 390×844 —
     estado de salud visible, botón deshabilitado en vacío y
     habilitado con texto, contador 29/1000, respuesta con
     «Confianza alta», similitud 0,526 y 4 fuentes; cero errores
     de JavaScript. Capturas revisadas: un defecto visual
     corregido (el punto de estado saltaba a su propia línea
     en móvil; `#estado-texto` ahora ocupa el ancho restante
     con `min-width: 0`) y re-verificado tras reiniciar el
     servidor (Flask cachea la plantilla sin modo debug).
  4. Suite de regresión ampliada con `bateria_interfaz` (6
     comprobaciones por modo: 200 en HTML, formulario,
     cero URLs absolutas, llamadas relativas, sección de
     fuentes, POST / 405) y el chequeo de 404 de `GET /`
     retirado (ya no es 404): **54/54 comprobaciones
     superadas, 0 falladas**, `data/` con los MD5 intactos
     (los del Ciclo 12).
- **Lista para publicar:** `app.py`, `templates/index.html`,
  `tests_regresion_api.py`, `README.md` e `improvement-log.md`.
  `data/index.faiss` NO viaja (binario; se regenera con
  `python ingest.py`).

## 2026-11-16 · Fase 2, Ciclo 13 (séptimo refresco del corpus: la síntesis de CenteIA + los registros del 9-10 nov)

### Séptimo refresco — la síntesis que faltaba y 8 registros al día

- **Objetivo:** dos deudas en una. (1) La síntesis de los vídeos
  de CenteIA (`sintesis-videos-2026-11-04.md`, 29 fragmentos)
  nunca se había ingerido: se creó el 4 nov, después de la
  ingesta del Ciclo 12, y la pregunta «¿Qué es el segundo yo
  24/7 de CenteIA?» seguía sin respuesta clara por eso —era el
  ejemplo bajo umbral de la suite—. (2) Ocho registros de
  `corpus-extra/` quedaron desactualizados por el trabajo de
  mejora del 9-10 nov (pasada de inmutabilidad en las apps web3
  y resto de entradas). Sin tocar código de la app: solo
  refresco, ingesta, batería y documentación.
- **Refresco (`refresh_corpus_extra.py`, idempotente, con
  verificación MD5 de cada copia contra su original):** cambiaron
  exactamente las 8 copias que el contraste previo copia↔original
  marcaba desactualizadas (las otras 7 ya coincidían):
  `segundo-yo` (`1d80e35b…` → `f5a021f7…`),
  `wallet-sim` (`dde6c1d9…` → `a78b8780…`),
  `token-explorer` (`2c1de334…` → `327d4bc2…`),
  `tx-builder` (`b96e9f43…` → `f12bae31…`),
  `block-explorer` (`5e701d51…` → `327d79b6…`),
  `hash-lab` (`faf6350c…` → `e6bed7cd…`),
  `contract-play` (`087489fc…` → `9f6307a5…`) y
  `dao-vote` (`0e52d126…` → `1d923dbd…`). Tras el refresco, las
  15 copias coinciden por MD5 con sus originales (15/15). La
  exclusión del registro propio del rag-demo se mantiene, por el
  motivo documentado en el Ciclo 5 (autorreferencia).
- **Re-ingesta:** 27 → **28 documentos, 527 → 568 fragmentos**
  (+41), con el delta explicado por archivo y solo por archivo
  (verificado contra `data/chunks.json`): la síntesis nueva
  (+29); block-explorer 26 → 29 (+3), hash-lab 26 → 27 (+1),
  token-explorer 22 → 26 (+4), tx-builder 26 → 27 (+1),
  wallet-sim 21 → 24 (+3). Segundo-yo, contract-play y dao-vote
  cambiaron contenido sin cambiar su conteo de fragmentos.
- **Nota de proceso (honesta, con efecto documentado):** la
  ingesta corrió desde el clon de trabajo y no desde la semilla,
  así que `rag_core.py` calculó las rutas citadas de
  `corpus-extra/` relativas a `~/workspace` con el prefijo largo
  del clon (`mejora-repos-2026-11-16/clones/rag-demo-
  asistente-documentos/corpus-extra/...`) en vez de la forma
  canónica (`rag-demo/corpus-extra/...`). La ruta citada forma
  parte de la bonificación léxica de la búsqueda, así que no era
  solo cosmética: se corrigió con un script desechable que solo
  reescribe ese prefijo en `chunks.json` y `meta.json` (423
  fragmentos + 15 entradas de meta), con el mismo formato de
  escritura de `build_index` (chunks sin indent, meta con
  indent=2) y verificando antes de escribir que textos,
  secciones y orden no cambiaban y que no quedaba ninguna ruta
  del clon (0 restantes). El índice FAISS no guarda rutas, así
  que no se tocó. La próxima ingesta desde la semilla
  reproducirá el mismo contenido sin este paso.
- **Verificaciones:**
  1. `py_compile` limpio en `app.py`, `rag_core.py`,
     `ingest.py`, `refresh_corpus_extra.py` y
     `tests_regresion_api.py`.
  2. Batería completa por la API real, con el servidor levantado
     (modelo cargado en el arranque en ~30 s): `/api/health` →
     `estado: "ok"`, `modelo_cargado: true`, **28 documentos,
     568 fragmentos**, coherentes con `data/meta.json`. Las 16
     preguntas conocidas-buenos, **idénticas** (REA 0,526 ·
     automatizaciones 0,699 · 45/90 0,669 · despliegue 0,502 ·
     barbería Ciclo 1 0,557 · direcciones tx-builder 0,522 ·
     capital de Francia sin fragmentos ≥ 0,30 · clima 0,320 ·
     nft-studio 0,570 · mundo-vida-ia 0,562 · 9/10 0,675 ·
     anti-phishing 0,597 · smoke barbería 0,530 · suelo
     tx-builder 0,674 · verify-catalog 0,581 · blockchain y
     web3 0,799): cero degradación. Dos preguntas nuevas:
     - NUEVA · Segundo yo («¿Qué es el segundo yo 24/7 de
       CenteIA?») → `confianza: "alta"`, máxima **0,545**, 3
       de las 4 fuentes son la síntesis (top: su sección del
       directo extra «Haz visible el valor de tu segundo yo»).
       Era el ejemplo bajo umbral de la suite hasta el Ciclo
       12; el refresco lo convierte en respuesta clara, que es
       exactamente lo que debía pasar.
     - NUEVA · toReversed («¿Qué cambió toReversed en
       block-explorer?») → alta, máxima **0,538**, las 4
       fuentes son el registro de block-explorer, 3 en su
       sección exacta del Ciclo 12. (La formulación genérica
       «¿Qué cambio de inmutabilidad se aplicó a las apps
       web3?» recupera `blockchain-web3.md`, no los registros:
       la pregunta que funciona es la que nombra el método y
       la app, y así queda documentada.)
  3. Por contenido (V3): artefactos nuevos — `data/index.faiss`
     `610d0527256873c305926d849f572cb0`, `data/chunks.json`
     `526c73b5b0ee07c19d27e878e83c1bfa`, `data/meta.json`
     `5ce87e3859c465f06838dabf9ae456cd` — frente a los del
     Ciclo 12 (`e2f45d08…`, `d6a836c9…`, `1daa24cc…`), con el
     delta explicado solo por la síntesis y los 8 registros
     (arriba). Matiz honesto, medido y no escondido: la
     dirección nueva de Ana (`0x48227ad1…4678`) sigue en 2
     fragmentos de la sección T-A1, pero en la pregunta de
     direcciones ahora aparece en la fuente **[3]** (similitud
     0,433) en vez de la [1] como en los ciclos anteriores:
     el re-troceado tras el refresco del registro reordenó
     los fragmentos dentro de la misma sección. La
     recuperación sigue siendo correcta (documento y sección
     exactos, dirección en el top-4 citado), no es una
     pérdida.
  4. Suite de regresión actualizada al Ciclo 13 (conteos
     28/568; el clima como pregunta bajo umbral, 0,320 exacto;
     dos comprobaciones nuevas del segundo yo: alta, 0,545 y
     top la síntesis): **56/56 comprobaciones superadas, 0
     falladas**, `data/` con los MD5 intactos tras la suite.
     El README actualiza los conteos, la calibración (Ciclo 13
     re-verificado, preguntas nuevas, cambio del ejemplo bajo
     umbral) y la sección del corpus.
- **Lista para publicar (la publica el coordinador):**
  `corpus-extra/` (8 registros actualizados), `data/chunks.json`,
  `data/meta.json`, `tests_regresion_api.py`, `README.md` e
  `improvement-log.md`. `data/index.faiss` NO viaja (binario; se
  regenera con `python ingest.py`).

## 2026-11-16 · Interfaz web: sin índice, el campo también se deshabilita

### RAG-UI-2 — el campo invitaba a escribir una pregunta que no se podía enviar

- **Hallazgo:** con el índice ausente, la interfaz mostraba el
  aviso y deshabilitaba el botón «Preguntar», pero el campo de
  texto seguía habilitado: se podía escribir una pregunta (con
  su contador 12/1000) que no había forma de enviar. El estilo
  `textarea:disabled` ya existía desde la creación de la
  interfaz; faltaba aplicarlo.
- **Cambio:** `templates/index.html` (+6/−0): en la rama
  «sin índice» de la lectura de `/api/health`, `campo.disabled
  = true`. Solo esa rama cambia; con índice el campo sigue
  habilitado como siempre.
- **Verificaciones:**
  1. Navegador real con la app levantada sin `index.faiss`
     (escritorio 1280×800 y móvil 390×844): estado «Sin índice
     cargado» con punto rojo, aviso visible con la instrucción
     de ingesta, campo Y botón deshabilitados, cero errores de
     JavaScript. La captura muestra el campo visiblemente
     atenuado con el contador en 0/1000.
  2. Ruta normal intacta tras el cambio (índice restaurado,
     MD5 `610d0527…` del Ciclo 13): campo habilitado, botón
     deshabilitado en vacío, REA → confianza alta, similitud
     0,526, 4 fuentes, cero errores de JavaScript.
  3. Suite de regresión: **56/56 comprobaciones superadas, 0
     falladas**, `data/` con los MD5 del Ciclo 13 intactos.
- **Lista para publicar:** `templates/index.html` e
  `improvement-log.md`.

## 2026-11-16 · Fase 2, Ciclo 14 (octavo refresco del corpus: mundo-vida-ia al día + el renombre publicado)

### Octavo refresco — una copia al día y el corpus al día con el renombre

- **Objetivo:** el contraste copia↔original previo al refresco
  encontró **1 de 15 copias desactualizada**: la de mundo-vida-ia
  (`2e56bd99…` frente al original `75eb8184…`). Su original
  recibió el 16 nov la entrada de la ronda 2 de la operación de
  mejora (el arreglo UnicodeEncodeError en consolas ASCII,
  suite 114/114), posterior a la ingesta del Ciclo 13. Las
  otras 14 copias ya coincidían con su original. Sin tocar
  código de la app: solo refresco, ingesta, batería y
  documentación. Respaldo previo del estado del Ciclo 13
  (artefactos de `data/`, las 15 copias de `corpus-extra/`,
  README y este registro) en `/tmp/rag-demo-ciclo14-backup/`,
  antes de tocar nada.
- **Refresco (`refresh_corpus_extra.py`, idempotente, con
  verificación MD5 de cada copia contra su original):** cambió
  **exactamente la única copia esperada**:
  - `mundo-vida-ia-improvement-log.md`: `2e56bd99…` →
    `75eb8184…` (16 nov 2026: la demo ya no muere en consolas
    ASCII — `asegurar_salida_utf8()` al inicio de `main()`,
    regresión con `PYTHONIOENCODING=ascii`, suite 114/114).
  El cambio es un añadido puro de la sección nueva al
  principio del registro (verificado por `diff` contra la
  copia del Ciclo 13): ningún contenido previo se perdió ni se
  alteró. Tras el refresco, las 15 copias coinciden por MD5
  con sus originales (15/15). La exclusión del registro propio
  del rag-demo se mantiene, por el motivo documentado en el
  Ciclo 5 (autorreferencia).
- **Re-ingesta:** mismos 28 documentos, **568 → 572 fragmentos**
  (+4), con el delta explicado por archivo y solo por archivo
  (verificado contra `data/chunks.json`): mundo-vida-ia 33 →
  35 (+2, la entrada nueva) y portafolio-y-empleo 9 → 11 (+2,
  la sección nueva «Actualización 16 nov 2026 — portafolio
  publicado y repos ordenados» del archivo vivo, que la
  ingesta recoge porque el material de `mundo-dirsi/aprendido`
  se lee directo de su carpeta). Los fragmentos de los otros
  26 archivos son idénticos en número a los del Ciclo 13.
- **El renombre, recogido por la ingesta (no a mano):** la
  ingesta del Ciclo 13 corrió antes de que el renombre
  Blockali → Block Ethos se publicara en los archivos vivos de
  `mundo-dirsi/aprendido`, así que esta re-ingesta lo recoge
  por primera vez: 3 fragmentos de blockchain-web3.md y 2 de
  despliegue.md cambian SOLO por el renombre (verificado por
  comparación con el renombre normalizado: las diferencias
  residuales son desplazamientos de ±3 caracteres en los
  bordes de troceado, consecuencia directa de que «Block
  Ethos» tiene 3 caracteres más que «Blockali»; ningún otro
  contenido cambia). Las menciones de «Blockali» en
  `data/chunks.json` pasan de 8 a **1**, y la que queda es la
  nota histórica del propio archivo vivo («renombrado desde
  Blockali por orden de Antonio», en la sección nueva de
  portafolio-y-empleo): contenido actual, no residuo.
- **Nota de proceso (misma que en el Ciclo 13):** la ingesta
  corrió desde el clon de trabajo, así que las rutas citadas
  de `corpus-extra/` salieron con el prefijo largo del clon;
  se corrigieron a la forma canónica `rag-demo/corpus-extra/`
  con un script desechable (`/tmp/rag-ciclo14-arreglar-rutas.py`,
  solo reescribe ese prefijo: 425 fragmentos + 15 entradas de
  meta), mismo formato que `build_index`, con verificación de
  que textos, secciones y orden no cambiaban (0 rutas del clon
  restantes). El índice FAISS no guarda rutas, así que no se
  tocó. La próxima ingesta desde la semilla reproducirá el
  mismo contenido sin este paso.
- **Verificaciones:**
  1. `py_compile` no aplica: este ciclo no toca código (solo
     corpus, artefactos, README y este registro).
  2. Batería completa por la API real, con el servidor levantado
     en el puerto 5058 (modelo cargado en el arranque en 16,9 s):
     `/api/health` → `estado: "ok"`, `modelo_cargado: true`,
     **28 documentos, 572 fragmentos**, coherentes con
     `data/meta.json`. Las 16 preguntas conocidas-buenos,
     **idénticas** (REA 0,526 · automatizaciones 0,699 · 45/90
     0,669 · despliegue 0,502 con despliegue.md en las
     posiciones 1–3 · barbería Ciclo 1 0,557 · direcciones
     tx-builder 0,522 · capital de Francia sin fragmentos ≥
     0,30 · clima 0,320, baja · nft-studio 0,570 ·
     mundo-vida-ia 0,562 · 9/10 0,675 · anti-phishing 0,597 ·
     smoke barbería 0,530 · suelo tx-builder 0,674 ·
     verify-catalog 0,581 · blockchain y web3 0,799, ahora con
     la sección «Block Ethos: un producto real, no una demo»
     entre sus fuentes), y las 2 preguntas nuevas del Ciclo 13
     también idénticas (segundo yo 0,545 · toReversed 0,538):
     cero degradación. Dos preguntas nuevas:
     - NUEVA · ASCII («¿Qué se arregló en mundo-vida-ia para
       las consolas ASCII?») → `confianza: "alta"`, máxima
       **0,545**, las 4 fuentes son el registro de
       mundo-vida-ia, las 2 primeras en su sección exacta de
       la entrada nueva («El fallo — UnicodeEncodeError en el
       primer print con «ñ»»).
     - NUEVA · Portafolio («¿Dónde está publicado el
       portafolio de Antonio?») → alta, máxima **0,513**, las
       fuentes 1, 2 y 4 son portafolio-y-empleo.md, las 2
       primeras en su sección exacta de la actualización del
       16 nov. Matiz honesto: la formulación alternativa
       «¿Qué pasa con mundo-vida-ia en una consola ASCII?»
       NO supera la puerta de claridad (máxima 0,489,
       `confianza: "baja"`, sin fuentes): la pregunta que
       funciona es la que nombra el arreglo, y así queda
       documentada.
     Servidor apagado al terminar (puerto 5058 sin respuesta,
     comprobado).
  3. Por contenido (V3): artefactos nuevos — `data/index.faiss`
     `225b78dce24f1cc7f12bb3b84f304937`, `data/chunks.json`
     `5c2feef58338c5ed4c73b4e176cc7e39`, `data/meta.json`
     `fc10ab6cf1b72ae1bf9dd4054a665d6e` — frente a los del
     Ciclo 13 (`610d0527…`, `526c73b5…`, `5ce87e38…`), con el
     delta explicado solo por el refresco, la sección nueva
     de portafolio-y-empleo y el renombre (arriba). La
     dirección nueva de Ana (`0x48227ad1…4678`) sigue en 2
     fragmentos de la sección T-A1 de tx-builder. Sin cambios
     en `rag_core.py` ni en `app.py`: solo la copia de
     mundo-vida-ia en `corpus-extra/`, los artefactos de
     `data/`, el README (conteos 28/572, calibración
     re-verificada, preguntas nuevas) y este registro. Nota
     de publicación: `data/index.faiss` no se publica
     (binario); se regenera con `python ingest.py`.
  4. Suite de regresión: **55/56 comprobaciones superadas**;
     el único fallo es el esperado: la comprobación que fija
     568 fragmentos (`health 28 documentos / 568 fragmentos
     (Ciclo 13)`) ahora ve 572. La actualización de esa
     constante a 572 es del trabajador de código (la suite
     es suya); el resto de la suite —incluidas las
     comprobaciones del segundo yo, la interfaz y el cierre
     con MD5 de `data/` intactos— sigue en verde. El README
     ya no afirma 568 en ningún sitio.
- **Lista para publicar (la publica el coordinador):**
  `corpus-extra/mundo-vida-ia-improvement-log.md`,
  `data/chunks.json`, `data/meta.json`, `README.md` e
  `improvement-log.md`. `data/index.faiss` NO viaja (binario; se
  regenera con `python ingest.py`).

## 2026-11-16 · Mapa de cobertura: una pregunta canario por documento (2ª tanda)

### Cobertura demostrada — los 28 documentos, uno a uno

- **Objetivo:** la batería solo vigilaba 13 de los 28 documentos
  (REA, automatizaciones, 45/90, despliegue, barbería,
  tx-builder, nft-studio, mundo-vida-ia, anti-phishing,
  blockchain-web3, síntesis de CenteIA, block-explorer y
  portafolio-y-empleo —este último desde la pregunta nueva del
  Ciclo 14—). Los otros 15 no tenían ninguna pregunta que
  demostrara que son recuperables: el corpus podía contener
  documentos que ninguna pregunta alcanza jamás y nadie lo
  sabría. Este mapa formula una pregunta canario por cada uno
  de esos 15 y la mide contra la API real: debe recuperar ESE
  documento en el top-4 con `confianza: "alta"`.
- **Resultado: 15 de 15 recuperables, todos en 1.ª posición.**
  Ningún documento muerto. La tabla registra la formulación
  que funciona, la similitud máxima medida y la posición del
  documento objetivo entre las fuentes (top-4).

  | Documento | Pregunta canario | Sim. máx. | Pos. |
  |---|---|---|---|
  | `analisis.md` | ¿Cuáles son las 25 tareas que la IA ya puede hacer por ti según los materiales de CenteIA? | 0,694 | 1.ª (3 de 4 fuentes) |
  | `guia-diseno-web-centeia-evaluacion.md` | ¿Qué herramientas recomienda la guía de diseño web de CenteIA para diseñar con Claude Code? | 0,696 | 1.ª (las 4 fuentes) |
  | `regalo-1-trabajo-delegado-evaluacion.md` | ¿Cuál es la regla de oro anti-invención del primer trabajo delegado a la IA? | 0,580 | 1.ª (3 de 4 fuentes) |
  | `api-segundo-yo-improvement-log.md` | ¿Qué validación real de payloads se añadió a la API del segundo yo? | 0,569 | 1.ª (3 de 4 fuentes) |
  | `biblioteca-prompts-improvement-log.md` | ¿Qué pasó con los 15 roles anunciados en la biblioteca de prompts si solo 8 tenían prompt? | 0,637 | 1.ª (las 4 fuentes) |
  | `contract-play-improvement-log.md` | ¿Qué cambió en el simulador de contratos de contract-play para alinearse con los fragmentos? | 0,614 | 1.ª (las 4 fuentes) |
  | `dao-vote-improvement-log.md` | ¿Por qué los filtros Activas y Cerradas de DAO Vote devolvían siempre 0? | 0,693 | 1.ª (las 4 fuentes) |
  | `gas-calc-improvement-log.md` | ¿Qué corrigió gas-calc sobre el wei exacto y EIP-1559? | 0,710 | 1.ª (las 4 fuentes) |
  | `hash-lab-improvement-log.md` | ¿Qué es la validez transitiva en hash-lab y qué cambió en Restaurar? | 0,707 | 1.ª (las 4 fuentes) |
  | `segundo-yo-improvement-log.md` | ¿Qué decisión visual fuerte se tomó en la app segundo-yo con la ficha como tarjeta de identidad? | 0,706 | 1.ª (las 4 fuentes) |
  | `token-explorer-improvement-log.md` | ¿Por qué se renombró un token en token-explorer? | 0,538 | 1.ª (las 4 fuentes) |
  | `wallet-sim-improvement-log.md` | ¿Por qué la cartera nueva de wallet-sim empieza a 0 y qué hace el faucet? | 0,512 | 1.ª (las 4 fuentes) |
  | `agentes-e-ia.md` | ¿Qué es un agente de código en la práctica? | 0,821 | 1.ª (3 de 4 fuentes) |
  | `desarrollo-web.md` | ¿Qué principio de desarrollo web dice que cada app debe tener una sola especialización? | 0,665 | 1.ª (3 de 4 fuentes) |
  | `herramientas-y-conexiones.md` | ¿Por qué el conector de GitHub no crea repositorios? | 0,713 | 1.ª (3 de 4 fuentes) |

- **Matices honestos, medidos y no escondidos:**
  - `analisis.md` fue el único que resistió la primera
    formulación: la pregunta sobre la ficha
    «Cuando ____, me gustaría que mi segundo yo ____» NO
    supera la puerta de claridad (máxima 0,403,
    `confianza: "baja"`, sin fuentes): los huecos en blanco
    de la plantilla no son un buen texto de consulta. Las
    otras cuatro formulaciones probadas sí recuperan el
    documento en 1.ª posición (25 tareas 0,694 · glosario
    IA sin jerga 0,553 · los 4 documentos analizados 0,580 ·
    pre-diseñar tu segundo yo 0,558),
    así que el documento no es contenido muerto: es la
    formulación con huecos la que falla. La canario que
    queda es la de las 25 tareas (la más alta y la que
    más fuentes del documento reúne).
  - Los canarios más justos son los de `wallet-sim`
    (0,512) y `token-explorer` (0,538): pasan la puerta
    0,50 con poco margen. Son los primeros candidatos a
    vigilar si el corpus crece o se re-trocea; si alguno
    cae bajo 0,50 en un refresco futuro, la regresión se
    verá aquí antes que en ningún otro sitio.
  - Los canarios de los registros de mejora funcionan
    porque nombran el hallazgo concreto de cada registro
    (el filtro que devolvía 0, el wei exacto, los 15
    roles): la pregunta genérica («¿qué se arregló en
    X?») no se probó y no se promete. Igual que con
    toReversed en el Ciclo 13, la pregunta que funciona
    es la que nombra el método y la app.
- **Verificaciones:**
  1. Batería completa de los 15 canarios por la API real,
     servidor levantado en el puerto 5059 con el índice
     del Ciclo 14 (`/api/health` → `estado: "ok"`,
     `modelo_cargado: true`, 28 documentos, 572
     fragmentos): cada cifra de la tabla es la respuesta
     real, copiada tal cual, con su confianza y sus
     fuentes registradas. Segunda corrida completa de la
     batería (servidor re-levantado): idéntica en confianza,
     similitud y posición en los 15 canarios. Servidor
     apagado al terminar
     (puerto 5059 sin respuesta, comprobado).
  2. Controles de no-regresión (4 preguntas conocidas
     de la batería, mismas respuestas que en el Ciclo
     14): REA 0,526 · blockchain y web3 0,799 · clima
     0,320, baja · segundo yo 0,545. Cero degradación,
     como corresponde a una tanda que no toca el índice.
  3. Solo lectura + documentación: **sin re-ingesta**.
     `data/` queda intacto: MD5 de `chunks.json`
     (`5c2feef58338c5ed4c73b4e176cc7e39`) y `meta.json`
     (`fc10ab6cf1b72ae1bf9dd4054a665d6e`) idénticos antes
     y después de la tanda (los del Ciclo 14). Ningún
     archivo del corpus cambió.
- **Lista para publicar (la publica el coordinador):**
  `README.md` (puntero al mapa en la sección del corpus) e
  `improvement-log.md` (esta entrada). Nada más: `data/`,
  `corpus-extra/` y el código no cambian en esta tanda.

## 2026-11-16 · Auditoría de frontera: qué NO está en el corpus y por qué (2ª tanda)

### La frontera, decidida por escrito — insumo para el Ciclo 15

- **Objetivo:** el corpus crece por inercia (lo que cae en tres
  carpetas) sin que nadie haya decidido su frontera. Esta
  auditoría clasifica cada documento vecino con una decisión
  explícita — ingerir, excluir o pendiente de Antonio — con su
  motivo, citando el contenido real de cada archivo. **Nada se
  ingiere en esta tanda:** la auditoría es el entregable; la
  ingesta que de ella salga sería el Ciclo 15.
- **Criterio que manda (no negociable):** `data/chunks.json` se
  publica en el repo del rag-demo, así que ingerir un documento
  es publicarlo por la puerta de atrás. Todo lo que contenga
  perfil personal, inventario de accesos o criterios de
  evaluación que el solucionador no debe ver queda fuera
  aunque tenga valor consultivo. Y todo lo que sea plantilla
  con huecos, índice o diario de trabajo queda fuera porque
  contamina la recuperación (precedente: la exclusión del
  registro propio en el Ciclo 5, y el canario de la ficha de
  `analisis.md` de esta misma tanda, que no supera la puerta
  con sus huecos en blanco).
- **Candidatos:** los 11 `.md` de la raíz de `mundo-dirsi/`
  (lista generada por `ls`, no de memoria) más el segundo
  anillo (subcarpetas de `mundo-dirsi/`). `centeia-materiales/`
  no aporta candidatos: sus 5 archivos ya están todos en el
  corpus (verificado por `ls`).

  | Documento (raíz de `mundo-dirsi/`) | Decisión | Motivo |
  |---|---|---|
  | `MANUAL-AGENTES.md` (16,6 KB) | **Ingerir** | Método portable y público por declaración propia («no contiene la memoria personal completa… este manual es solo el método, que sí es portable y público»). Cubre skills, Cowork, Codex, Claude Code y ChatGPT Work: material nuevo frente a `agentes-e-ia.md`. |
  | `METODO-CLAUDE.md` (12,3 KB) | **Ingerir** | Destilación a procedimiento con redacción propia; solo método (revisión de sistemas, filtro de selección, prueba de «realmente hecho»). Sin datos personales. |
  | `METODO-GROK.md` (19,7 KB) | **Ingerir** | Igual que el de Claude, con su advertencia de origen declarada (método declarado por el modelo, débil como testimonio). Aporta lo único: cuándo usar el instrumento de Grok y cuándo el de Claude. |
  | `PROTOCOLO-REFUTACION.md` (8,7 KB) | **Ingerir** | Método (pasada adversarial antes de entregar lo decisivo), sin datos personales. Los errores que cita son del trabajo del agente, ya públicos en `mundo-dirsi`. |
  | `DESTILADO-LOVABLE-GPTENGINEER.md` (10,5 KB) | **Ingerir** | Investigación leída de primera mano, redacción propia, repo MIT; destila método, no republica código. Todo el contenido es información pública. |
  | `METODO-CLAUDE-PLAYBOOK.md` (11,1 KB) | **Pendiente de Antonio** | Solo método, sin datos personales («destilación con redacción propia»), así que por contenido podría ingerirse — pero su propia publicación en `mundo-dirsi` está pendiente de su aprobación (bandeja del 15 nov, ítem 6). Ingerirlo aquí antes lo publicaría por la puerta de atrás. Se ingiere solo cuando él apruebe su publicación. |
  | `RECOPILACION-MATERIALES.md` (72 KB, 1.150 líneas) | **Pendiente de Antonio** | Tres problemas a la vez: (1) su §2 es «Quién es Antonio (10 líneas)» — perfil personal en un corpus público; (2) su §3 duplica material ya ingerido (P1–P3 resumen los mismos documentos que `analisis.md`, la guía de diseño y el regalo-1); (3) con 72 KB sería el documento más grande del corpus (el mayor hoy es el registro de la barbería, 43 KB), con riesgo de dominar la recuperación. Lo valioso es solo su §4 (conocimiento destilado usable: criterio anti-genérico, mapa de delegación, estructuras del segundo yo). Propuesta: ingerir solo el §4 recortado, si Antonio lo aprueba. |
  | `CALIBRACION.md` (12 KB) | **Excluir** | Registro de medición interno: afirmaciones decisivas entregadas a Antonio con sus veredictos. No es conocimiento consultable; ingerirlo expondría su historial de decisiones y haría que la demo respondiera sobre Antonio mismo. Además es vivo: cada veredicto lo cambia. |
  | `BANCO-DE-PRUEBAS.md` (13,7 KB) | **Excluir** | Por diseño, «el solucionador no recibe los criterios»: ingerir las fichas con sus criterios de aprobado en un corpus público pondría las respuestas del examen al alcance del examinado. |
  | `INVENTARIO-CAPACIDADES.md` (6,4 KB) | **Excluir** | Inventario operativo: máquina, herramientas, accesos y automatismos. Dos motivos: expone accesos, y caduca con cada despliegue de la VM («una foto vieja no describe la máquina de hoy») — ingerirlo congelaría datos que se vuelven falsos. |
  | `README.md` de `mundo-dirsi` (5,9 KB) | **Excluir** | Es un índice con punteros, no contenido consultable: sus fragmentos de navegación competirían con los documentos reales que describe. |

  Segundo anillo (subcarpetas de `mundo-dirsi/`, mismo criterio):

  | Documento | Decisión | Motivo |
  |---|---|---|
  | `consultas/` (4 plantillas/checklists, 19–43 líneas) | **Excluir** | Plantillas con huecos por rellenar y listas de verificación de trabajo: la demo citaría casillas vacías como respuesta. |
  | `crecimiento/log.md` (313 líneas) | **Excluir** | Bitácora de trabajo interno, autorreferente como el registro propio del Ciclo 5; vivo y creciente. |
  | `herramientas/README.md` (100 líneas) | **Excluir** | Describe herramientas propias (un scaffolder de código): código y uso interno, no documento consultable. |
  | `herramientas/sitios-40-evaluacion.md` (54 líneas) | **Excluir** | Lista de enlaces externos evaluada una vez (27 oct): se desactualiza y no es conocimiento propio duradero. Si Antonio quiere que la demo responda sobre herramientas web, se re-evalúa primero. |
  | `por-aprender/preguntas-abiertas.md` (253 líneas) | **Excluir** | Es el anti-corpus por definición: preguntas que Dirsi todavía NO puede responder. Ingerirlas haría que la demo citara sus propias ignorancias como si fueran respuestas. |
  | `por-aprender/rutas.md` (619 líneas) | **Excluir** | Plan de aprendizaje interno, aspiracional («por aprender»): no son hechos verificados sino caminos por construir. |

- **La frontera, medida (sondeo contra la API real, índice del
  Ciclo 14, servidor levantado en el puerto 5059):** cinco
  preguntas que hoy caen fuera del corpus, con su respuesta
  real tal cual:
  - «¿Cómo se monta un agente con el método de Antonio?» →
    alta 0,518, pero las fuentes son genéricas (síntesis y
    `agentes-e-ia.md`): el corpus responde el *tema* pero
    no el *método* — las skills, Cowork y Codex del Manual
    no están. Ingerir el Manual cierra este hueco.
  - «¿Qué es gpt-engineer y qué tiene que ver con
    Lovable?» → **baja 0,466, sin fuentes.** Hueco limpio
    y demostrado: el destilado no está y nada lo cubre.
  - «¿Qué es la regla de tres del playbook del ingeniero
    senior?» → alta 0,515, pero las fuentes son
    documentos equivocados (sala limpia de
    `ingenieria-inversa.md`, catálogo de la síntesis):
    **falso positivo con confianza alta.** La demo
    responde con seguridad algo que no sabe. Ingerir el
    Playbook (cuando Antonio apruebe su publicación)
    corrige exactamente este caso.
  - «¿Cómo se intenta refutar algo antes de entregárselo
    a Antonio?» → **baja 0,313, sin fuentes.** Hueco
    limpio: el protocolo no está y nada lo cubre.
  - «¿Qué afirmaciones refutadas hay en el registro de
    calibración?» → alta 0,580, con fuentes equivocadas
    (un caso de anti-phishing, una entrada de
    mundo-vida-ia): **falso positivo con confianza alta
    sobre un documento excluido a propósito.** Excluir
    `CALIBRACION.md` no hace que la demo se niegue a
    responder sobre calibración; hace que responda desde
    vecinos sin relación. Es un límite de la puerta de
    honestidad (0,50), no de la frontera: queda anotado
    como trabajo futuro de código, fuera de esta tanda.
- **Verificaciones:**
  1. Lista de candidatos generada por `ls`/`find` (11 en la
     raíz, 9 en el segundo anillo); cada decisión cita el
     contenido real leído del archivo (tamaño, secciones,
     citas literales donde importan).
  2. Sondeo de 5 preguntas por la API real con el servidor
     levantado (puerto 5059, índice del Ciclo 14):
     cifras y fuentes copiadas tal cual. Servidor apagado
     al terminar (puerto 5059 sin respuesta, comprobado).
  3. Solo lectura + documentación: **sin re-ingesta, sin
     cambios en el corpus.** `data/` intacto: MD5 de
     `chunks.json` (`5c2feef58338c5ed4c73b4e176cc7e39`) y
     `meta.json` (`fc10ab6cf1b72ae1bf9dd4054a665d6e`)
     idénticos antes y después de la tanda (los del
     Ciclo 14).
- **Lista para publicar (la publica el coordinador):**
  `README.md` (puntero a la auditoría en la sección del
  corpus) e `improvement-log.md` (esta entrada). Nada más:
  `data/`, `corpus-extra/` y el código no cambian en esta
  tanda.

## 2026-11-16 · «Pruébala en 2 minutos»: preguntas guiadas en el README (2ª tanda, vuelta extra)

### La demo se presenta sola

- **Objetivo:** el README explicaba la API pero no invitaba a
  probarla: un visitante tenía que leer el registro de mejoras
  para saber qué preguntar. Nueva sección «Pruébala en 2
  minutos» con 6 comandos `curl` copiables, cada uno con lo
  que debe responder (confianza, similitud máxima medida,
  fuente que debe encabezar).
- **Las 6 preguntas (cifras medidas el 16 nov 2026 contra la
  API real, índice del Ciclo 14):** REA 0,526, alta, top
  `ingenieria-inversa.md` · blockchain y web3 0,799, alta, 4
  fuentes de `blockchain-web3.md` · despliegue 0,502, alta,
  top `despliegue.md` · segundo yo 0,545, alta, top la
  síntesis de CenteIA · gas-calc 0,710, alta, 4 fuentes de su
  registro · clima 0,320, baja, sin fuentes (la API dice que
  no tiene resultados claros en vez de rellenar).
- **Verificaciones:**
  1. Los 6 comandos `curl` se ejecutaron contra el servidor
     levantado (puerto 5059, índice del Ciclo 14; en la
     sección van con el puerto 5057, el de por defecto — el
     puerto no afecta a las respuestas): cada cifra de la
     sección es la respuesta real, copiada tal cual. Servidor
     apagado al terminar (puerto 5059 sin respuesta,
     comprobado).
  2. Solo documentación: `data/` intacto (MD5 de
     `chunks.json` y `meta.json`, los del Ciclo 14,
     idénticos antes y después).
- **Lista para publicar (la publica el coordinador):**
  `README.md` (sección nueva) e `improvement-log.md` (esta
  entrada). Nada más.
