# RAG demo — asistente que responde desde documentos, citando fuentes

Proyecto de portafolio de **Antonio José Mieres Garabote** (Full Stack Developer con IA).
Demuestra el patrón RAG (*Retrieval-Augmented Generation*) en su forma más
honesta y verificable: un asistente que responde preguntas **solo desde un
corpus de documentos propios** y **cita la fuente exacta** de cada fragmento
que usa (archivo y sección).

No usa claves de API ni servicios de pago: los embeddings se calculan
localmente y la respuesta es **extractiva** — se compone desde los fragmentos
recuperados, ningún modelo de lenguaje la redacta. Eso es una decisión
deliberada para la demo: todo lo que responde se puede verificar contra la
fuente citada.

## Cómo correrlo

```bash
cd rag-demo-asistente-documentos   # nombre del repo en GitHub; en el
                                   # workspace del autor la carpeta se
                                   # llama rag-demo (ver las rutas de
                                   # la ingesta de aquí abajo)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python refresh_corpus_extra.py   # corpus-extra/ al día (ver abajo)
.venv/bin/python ingest.py ~/workspace/centeia-materiales \
    ~/workspace/mundo-dirsi/aprendido ~/workspace/rag-demo/corpus-extra
.venv/bin/python app.py        # API en http://127.0.0.1:5057
```

Abre **http://127.0.0.1:5057/** en el navegador: la interfaz web mínima
(una sola página, sin recursos externos) pregunta desde el navegador
y muestra la respuesta con sus fuentes citadas, la confianza y la
similitud máxima; si el índice aún no existe, avisa y desactiva el
formulario hasta que se ejecute la ingesta. La API de abajo sigue
igual y es lo que usa la página.

El arranque de `app.py` no es instantáneo: antes de aceptar peticiones
carga el modelo de embeddings en memoria (medido el 2026-11-02:
~24 s de carga del modelo, ~25 s en total hasta que la API responde).
Ese es el precio que antes pagaba la primera pregunta en silencio;
ahora forma parte del arranque y la primera pregunta responde en
menos de un segundo. `/api/health` refleja el estado real:
`estado: "ok"` solo con el modelo ya cargado (`modelo_cargado: true`);
si la app se sirve por otra vía sin ese arranque en caliente, dirá
`"calentando"` hasta la primera búsqueda, y `"sin_indice"` si todavía
no se ha ejecutado la ingesta. En esa vía, si varias peticiones
llegan a la vez con el modelo aún sin cargar, una cerradura con
doble comprobación hace que se cargue una sola vez y las demás
esperen a esa carga. Además de `estado` y `modelo_cargado`,
`/api/health` devuelve `documentos` y `fragmentos` (los conteos del
índice cargado; sin índice dice 0 y 0, aunque `data/meta.json` conserve
los de la última ingesta), `modelo_embeddings` y `tipo_respuesta`.

Probar:

```bash
curl http://127.0.0.1:5057/api/health

curl -X POST http://127.0.0.1:5057/preguntar \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué es REA y para qué sirve?"}'
```

La respuesta incluye `pregunta` (el eco de la pregunta ya limpia),
`tipo_respuesta`, `respuesta` (extractiva, con citas `[1]`, `[2]`…),
`fuentes`, la lista de fragmentos usados —cada uno con su número (`n`),
su archivo, su sección, su similitud y el texto del fragmento— y dos
campos de control: `confianza` (`alta` o `baja`) y `similitud_maxima`.
La petición admite además un campo opcional `k` con el número de
fragmentos a devolver: por defecto vale 4, cualquier valor se ajusta al
rango 1–8 y un `k` no numérico se ignora en favor del defecto. El campo `pregunta` debe ser una cadena de texto no
vacía de como máximo 1000 caracteres; cualquier otro tipo de valor (un
número, una lista, un campo ausente…) recibe un `400` con el error en JSON.
Si el índice aún no existe (todavía no se ha ejecutado la ingesta),
`/preguntar` responde `503` con el error en JSON —«El índice no existe
todavía. Ejecuta primero: python ingest.py»— y `/api/health` lo refleja
con `estado: "sin_indice"`. El mismo estado —y el mismo `503`—
aparece si el conjunto de artefactos existe pero no es servible:
un fichero corrupto o truncado, o un desacuerdo entre el número
de vectores del índice, el de fragmentos y el que declara
`meta.json`. La app arranca en ese estado y registra el motivo,
en vez de no arrancar o de responder según la pregunta.

Dos notas de arranque que no se ven en los comandos de arriba:

- **Un clon recién hecho no trae índice.** `data/index.faiss` no está
  en el repositorio (lo genera `ingest.py` en local y está en
  `.gitignore`); el clon trae `data/chunks.json` y `data/meta.json`,
  pero hasta que no se ejecute la ingesta la API responde como se
  describe arriba: `sin_indice` en `/api/health` y `503` en
  `/preguntar`.
- **Todos los errores llegan en JSON**, con la forma
  `{"error": "..."}`: también la ruta desconocida (`404`), el método
  no permitido en una ruta (`405`, que además lleva la cabecera
  `Allow` con los métodos válidos de esa ruta), el cuerpo
  demasiado grande (`413`; el techo es de 32 KB, muy por encima
  de lo que ocupa una pregunta válida) y un fallo interno (`500`).
  El host y el puerto se pueden cambiar con las variables de
  entorno `RAG_DEMO_HOST` y
  `RAG_DEMO_PORT`; sin ellas se sirve en `127.0.0.1:5057`, como siempre.

## Pruébala en 2 minutos

Con el servidor levantado y el índice del Ciclo 14 (28
documentos, 572 fragmentos), estos seis `curl` muestran lo que
la demo hace — y lo que no hace. Cada cifra es la respuesta
real medida el 16 nov 2026, no un ejemplo inventado (el puerto
aquí es 5057, el de por defecto; si lo levantaste en otro,
cámbialo en el comando).

```bash
# 1. REA — confianza alta, similitud 0,526, primera fuente
#    ingenieria-inversa.md («Qué es REA»)
curl -s -X POST http://127.0.0.1:5057/preguntar \
  -H 'Content-Type: application/json' \
  -d '{"pregunta": "¿Qué es REA y para qué sirve?"}'

# 2. Blockchain y web3 — confianza alta, similitud 0,799, las 4
#    fuentes son blockchain-web3.md
curl -s -X POST http://127.0.0.1:5057/preguntar \
  -H 'Content-Type: application/json' \
  -d '{"pregunta": "¿Qué es blockchain y la web3?"}'

# 3. Despliegue — confianza alta, similitud 0,502, primera
#    fuente despliegue.md (el caso difícil del Ciclo 2: ver
#    «Límites honestos» y la entrada RAG-M2 del registro)
curl -s -X POST http://127.0.0.1:5057/preguntar \
  -H 'Content-Type: application/json' \
  -d '{"pregunta": "¿Cómo se despliega una aplicación?"}'

# 4. Segundo yo — confianza alta, similitud 0,545, primera
#    fuente la síntesis de CenteIA (esta pregunta era el ejemplo
#    bajo umbral hasta el Ciclo 13)
curl -s -X POST http://127.0.0.1:5057/preguntar \
  -H 'Content-Type: application/json' \
  -d '{"pregunta": "¿Qué es el segundo yo 24/7 de CenteIA?"}'

# 5. Un registro de mejora — confianza alta, similitud 0,710,
#    las 4 fuentes son el registro de gas-calc (la demo también
#    responde sobre el trabajo de mejora, no solo sobre los
#    materiales del curso)
curl -s -X POST http://127.0.0.1:5057/preguntar \
  -H 'Content-Type: application/json' \
  -d '{"pregunta": "¿Qué corrigió gas-calc sobre el wei exacto y EIP-1559?"}'

# 6. Fuera de tema — confianza baja, similitud 0,320, SIN
#    fuentes: la API dice que no tiene resultados claros en vez
#    de rellenar con fragmentos sin relación
curl -s -X POST http://127.0.0.1:5057/preguntar \
  -H 'Content-Type: application/json' \
  -d '{"pregunta": "¿Qué tiempo hará mañana?"}'
```

Si alguna cifra cambia en un refresco futuro, es una regresión
o una mejora medible, no un error del ejemplo: el registro de
mejoras anota la calibración de cada ciclo.

## Corpus

Documentos propios de Antonio, ya existentes en su workspace
(**28 documentos, 572 fragmentos** en la ingesta del Ciclo 14,
2026-11-16; el Ciclo 13 dejó 568: el octavo refresco actualiza
el registro de mundo-vida-ia (+2 fragmentos) y la ingesta
recoge la sección nueva de portafolio-y-empleo (+2) y el
renombre Block Ethos ya publicado en el material de aprendido):

- `centeia-materiales/` — análisis y evaluaciones de los materiales del
  curso «Tu segundo yo 24/7» (CenteIA), incluida la síntesis de los
  vídeos (2026-11-04, 29 fragmentos, desde el Ciclo 13). *(13
  documentos entre esta carpeta y la siguiente: 12 del corpus
  inicial + la síntesis del Ciclo 13.)*
- `mundo-dirsi/aprendido/` — notas de aprendizaje (agentes e IA, blockchain,
  despliegue, ingeniería inversa, portafolio y empleo…).
- `corpus-extra/` — **desde el Ciclo 5**: los registros de mejora
  (`improvement-log.md`) de las apps trabajadas en la Fase 2
  (portfolio-apps ×3, la demo de barbería, web3-apps ×10 y
  mundo-vida-ia), para que la demo también responda sobre ese trabajo:
  qué se arregló en cada ciclo y por qué. Son **copias exactas** de los
  originales en el momento de cada refresco, generadas por el script reproducible
  `refresh_corpus_extra.py` (que verifica cada copia por MD5 y borra
  las que ya no estén en su lista) con un nombre por app
  (`barberia-improvement-log.md`, `tx-builder-improvement-log.md`, …):
  la ingesta solo lee el primer nivel de cada carpeta y todos los
  originales se llaman igual. Si un registro cambia en su app, se
  vuelve a ejecutar el script y la ingesta.
  - **Excluido a propósito:** el `improvement-log.md` del propio
    rag-demo. Es autorreferente —su sección RAG-M2 se titula
    literalmente con la pregunta de la batería «¿Cómo se despliega
    una aplicación?»— y al ingerirlo desplazaba a `despliegue.md`
    de las posiciones 1–3 a las 3–4 (medido en el Ciclo 5): el
    refresco no puede empeorar lo que ya funcionaba, así que queda
    fuera y el ajuste está documentado en el registro del proyecto.

**Mapa de cobertura (2ª tanda, 2026-11-16):** cada uno de los 28
documentos tiene una pregunta medida que lo recupera en el top-4
con confianza alta: los 13 que ya vigilaba la batería más los 15
restantes, auditados en esta tanda con su pregunta canario — los
15 en 1.ª posición (tabla completa en el registro de mejoras,
entrada «Mapa de cobertura»). Ningún documento muerto; los
canarios más justos son wallet-sim (0,512) y token-explorer
(0,538), los primeros a vigilar si el corpus crece.

**Auditoría de frontera (2ª tanda, 2026-11-16):** lo que hoy NO
está en el corpus está decidido por escrito (registro de
mejoras, entrada «Auditoría de frontera»): 5 documentos
recomendados para ingerir en el Ciclo 15 (el manual de agentes,
los dos métodos destilados, el protocolo de refutación y el
destilado Lovable/gpt-engineer), 2 pendientes de Antonio
(el playbook y la recopilación de materiales) y el resto
excluidos con motivo (calibración, banco de pruebas, inventario
de capacidades, plantillas, preguntas abiertas). Sondeo medido:
gpt-engineer y la refutación hoy no se responden (baja, sin
fuentes); la «regla de tres» y la calibración reciben hoy
falsos positivos con confianza alta desde documentos vecinos.

La ingesta acepta carpetas a medida: `python ingest.py carpeta1 carpeta2`.
Formatos: Markdown (`.md`, troceado respetando encabezados) y PDF (`.pdf`,
una sección por página).

La ingesta no escribe sobre los artefactos en uso: compone
`index.faiss`, `chunks.json` y `meta.json` completos en ficheros
temporales del mismo directorio y los publica con tres renombres
en ese orden (fragmentos, índice, metadatos). Un corte durante la
escritura deja intacto el conjunto anterior; solo queda la ventana
de esos tres renombres encadenados, sin escrituras de datos entre
ellos.

Los dos scripts de mantenimiento son seguros de consultar:
`ingest.py --help` y `refresh_corpus_extra.py --help` solo muestran
la ayuda y no ejecutan nada, y una bandera desconocida sale con
error (código 2) sin tocar nada; sin argumentos, cada uno hace su
trabajo de siempre.

## Cómo funciona

```
documentos (.md/.pdf)
      │  ingest.py
      ▼
troceado por secciones → fragmentos de ~900 caracteres con solape de
~180, cada uno con el título del documento y el de su sección
antepuestos (ese contexto también se vectoriza y se cita)
      │
      ▼
embeddings locales — sentence-transformers
  (paraphrase-multilingual-MiniLM-L12-v2, 384 dimensiones, multilingüe)
      │
      ▼
índice FAISS (IndexFlatIP = similitud coseno sobre vectores normalizados)
  data/index.faiss + data/chunks.json (fragmentos y metadatos de fuente)
      │
      │  POST /preguntar
      ▼
la pregunta se vectoriza con el mismo modelo → candidatos sobre el
suelo mínimo de similitud semántica 0,30, reordenados por relevancia
híbrida (la similitud más una bonificación léxica acotada por
coincidencia de raíces con el archivo, la sección y el texto) → k=4
fragmentos; si la mejor similitud semántica de la consulta no llega
a 0,50, la API responde «sin resultados claros» y devuelve la lista de
fuentes vacía — ver «Límites honestos»
      │
      ▼
respuesta extractiva: los fragmentos, ordenados por relevancia y citados
[1..n], + lista de fuentes (archivo, sección, similitud)
```

Piezas:

| Archivo | Qué hace |
|---|---|
| `rag_core.py` | Troceado, embeddings, construcción y carga del índice, búsqueda y composición de la respuesta |
| `ingest.py` | Script de ingesta reproducible (CLI) |
| `refresh_corpus_extra.py` | Refresca `corpus-extra/` desde los registros originales (copia por app, verificación MD5) |
| `app.py` | API Flask + interfaz web: `GET /`, `GET /api/health`, `POST /preguntar` |
| `templates/index.html` | La interfaz web: una sola página autocontenida, sin recursos externos |
| `tests_regresion_api.py` | Suite de regresión de la API: 56 comprobaciones (ver abajo) |
| `data/` | Índice FAISS (generado por la ingesta, no versionado), fragmentos y metadatos |

La suite de regresión levanta la app en un puerto libre y
comprueba la API con y sin índice (salud, preguntas válidas y
bajo umbral, validación de entradas, errores en JSON, límites
de `k`, interfaz web) y que `data/` queda intacta tras correr:

```bash
.venv/bin/python tests_regresion_api.py   # 56 comprobaciones
```

Cada ciclo de refresco actualiza sus conteos esperados
(documentos y fragmentos) y sus preguntas de referencia; el
registro de mejoras anota el resultado de cada corrida.

## Límites honestos

- **Sin generación**: la respuesta es una composición de fragmentos, no un
  texto redactado. Responde «con las palabras del corpus»: si el corpus no
  lo dice, no lo inventa — pero tampoco parafrasea ni conecta ideas de
  varios documentos.
- **Calidad ligada al corpus**: con 28 documentos pequeños, una pregunta
  fuera de tema no debe rellenar la respuesta. La política está calibrada
  con pruebas reales sobre este corpus (2026-11-02, recalculada en el
  Ciclo 2 tras el troceado con títulos y la reordenación híbrida,
  re-verificada en el Ciclo 5 sobre el corpus ampliado, de nuevo en
  el Ciclo 7 tras el segundo refresco, en el Ciclo 9 tras el
  tercero, en el Ciclo 10 tras el cuarto, en el Ciclo 11 tras
  el quinto, en el Ciclo 12 tras el sexto, en el Ciclo 13 tras
  el séptimo y en el Ciclo 14 tras el octavo, 2026-11-16):
  ningún fragmento por debajo de 0,30 entra nunca, y si la mejor
  similitud semántica de la consulta queda por debajo de 0,50 la API
  responde «sin resultados claros en tus documentos», con
  `confianza: "baja"` y `fuentes` vacía. Similitudes semánticas máximas
  medidas en el Ciclo 5 y reproducidas idénticas en los Ciclos 7, 9,
  10, 11, 12, 13 y 14:
  dentro de tema, REA 0,526 · blockchain y web3 0,799 ·
  automatizaciones
  0,699 · 45 frente a 90 prompts 0,669 · barbería (Ciclo 1) 0,557 ·
  direcciones de tx-builder 0,522 · despliegue 0,502 (ver el caso
  especial de abajo) · versiones de nft-studio (Ciclo 6, pregunta
  nueva del Ciclo 7) 0,570 · tests de mundo-vida-ia (Ciclo 8, pregunta
  nueva del Ciclo 9) 0,562 · app web3 sin suelo de tests en el
  Ciclo 9 —tx-builder— (pregunta nueva del Ciclo 10) 0,675 ·
  comprobaciones del test de anti-phishing (Ciclo 9, también nueva
  del Ciclo 10) 0,597 · suelo de tests de tx-builder (Ciclo 10,
  pregunta nueva del Ciclo 11, con la formulación «¿Qué suelo de
  tests se añadió a tx-builder en el Ciclo 10?») 0,674 · smoke de
  la barbería (Ciclo 10, también nueva del Ciclo 11) 0,530 ·
  verificación cruzada de la barbería (Ciclo 11, pregunta nueva
  del Ciclo 12, «¿Qué verifica el script verify-catalog de la
  barbería?») 0,581 · segundo yo 24/7 (pregunta nueva del
  Ciclo 13, «¿Qué es el segundo yo 24/7 de CenteIA?») 0,545 ·
  toReversed en block-explorer (pregunta nueva del Ciclo 13,
  «¿Qué cambió toReversed en block-explorer?») 0,538 ·
  consolas ASCII en mundo-vida-ia (pregunta nueva del
  Ciclo 14, «¿Qué se arregló en mundo-vida-ia para las
  consolas ASCII?») 0,545 · portafolio publicado (pregunta
  nueva del Ciclo 14, «¿Dónde está publicado el portafolio
  de Antonio?») 0,513; fuera
  de tema, la capital de Francia no devuelve
  ningún fragmento ≥ 0,30 y el clima 0,320. La pregunta del
  segundo yo fue el ejemplo bajo umbral de la suite hasta el
  Ciclo 12; desde el Ciclo 13 la síntesis la responde (0,545) y
  el ejemplo bajo umbral pasó a ser el clima (0,320). El margen sigue siendo
  estrecho (en el Ciclo 1, con otro corpus, un lorem ipsum llegó a
  0,52 y se colaba como «claro») y ningún umbral único separa
  limpiamente con este modelo pequeño.
- **Recuperación a nivel de documento, no siempre de sección**: la
  pregunta «¿Qué se arregló en el Ciclo 1 de la barbería?» recupera el
  registro correcto (sus 4 fuentes son la barbería), pero los
  fragmentos que encabezan no son los de los arreglos del Ciclo 1:
  en ese registro los arreglos viven en secciones tituladas por su
  código (A1, A2, A3…) sin la frase «Ciclo 1», y la reordenación
  premia otras secciones del mismo documento. La pregunta de
  tx-builder sí encabeza con su sección exacta (T-A1, las direcciones).
- **Caso especial, el despliegue**: «¿Cómo se despliega una
  aplicación?» recupera `despliegue.md` en las posiciones 1–3, pero
  hay que saber por qué: la similitud semántica pura de su mejor
  fragmento es solo 0,371, porque el documento trata el despliegue
  como doctrina (tarjetas, costes, runbook) y su vocabulario no
  coincide con la pregunta. Lo rescata la reordenación híbrida (el
  archivo y las secciones se llaman «despliegue»), y la puerta de
  claridad se supera por la similitud máxima de la consulta (0,502,
  de un fragmento de otro documento que además entra como cuarta
  fuente sin ser del tema). La recuperación acierta; la composición
  extractiva todavía puede arrastrar un fragmento vecino así.
- **Búsqueda semántica, no exacta**: el modelo de embeddings es pequeño y
  multilingüe; nombres propios o siglas muy específicas pueden recuperar
  peor que una búsqueda por palabras clave.
- **Índice estático**: si cambia el corpus hay que re-ejecutar `ingest.py`.
- Todo corre en CPU y en local: pensado como demo y pieza de portafolio,
  no como servicio de producción.

## Ruta de mejora

1. **Conectar un LLM** (p. ej. vía OpenRouter) como paso de generación
   *después* de la recuperación: el modelo redactaría la respuesta usando
   solo los fragmentos recuperados, manteniendo las citas. La recuperación
   y las fuentes no cambian; solo cambia quién redacta.
2. Búsqueda híbrida completa (p. ej. BM25 + semántica) para nombres y
   siglas: hoy la recuperación ya reordena los candidatos semánticos
   con una bonificación léxica acotada por coincidencia con el
   archivo, la sección y el texto; un BM25 de verdad seguiría siendo
   más robusto, sobre todo si el corpus crece (la reordenación actual
   examina todos los fragmentos, viable a esta escala de demo).
3. Re-troceado adaptativo y metadatos por página en PDF.
4. Evaluación con un set fijo de preguntas/respuestas esperadas.
5. Despliegue (p. ej. PythonAnywhere). La interfaz web mínima ya existe
   desde el 2026-11-16 (`GET /`, una sola página autocontenida que
   pregunta y muestra respuesta + fuentes); queda el despliegue.

## Stack

Python · Flask · sentence-transformers · FAISS · pypdf — todo local,
sin claves de API.
