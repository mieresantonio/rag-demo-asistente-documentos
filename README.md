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
cd rag-demo
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python ingest.py     # ingesta: trocea, vectoriza e indexa
.venv/bin/python app.py        # API en http://127.0.0.1:5057
```

El arranque de `app.py` no es instantáneo: antes de aceptar peticiones
carga el modelo de embeddings en memoria (medido el 2026-11-02:
~24 s de carga del modelo, ~25 s en total hasta que la API responde).
Ese es el precio que antes pagaba la primera pregunta en silencio;
ahora forma parte del arranque y la primera pregunta responde en
menos de un segundo. `/api/health` refleja el estado real:
`estado: "ok"` solo con el modelo ya cargado (`modelo_cargado: true`);
si la app se sirve por otra vía sin ese arranque en caliente, dirá
`"calentando"` hasta la primera búsqueda, y `"sin_indice"` si todavía
no se ha ejecutado la ingesta.

Probar:

```bash
curl http://127.0.0.1:5057/api/health

curl -X POST http://127.0.0.1:5057/preguntar \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué es REA y para qué sirve?"}'
```

La respuesta incluye `respuesta` (extractiva, con citas `[1]`, `[2]`…),
`fuentes`, la lista de fragmentos usados con su archivo, su sección y su
similitud, y dos campos de control: `confianza` (`alta` o `baja`) y
`similitud_maxima`. El campo `pregunta` debe ser una cadena de texto no
vacía de como máximo 1000 caracteres; cualquier otro tipo de valor (un
número, una lista, un campo ausente…) recibe un `400` con el error en JSON.

## Corpus inicial

Documentos propios de Antonio, ya existentes en su workspace:

- `centeia-materiales/` — análisis y evaluaciones de los materiales del
  curso «Tu segundo yo 24/7» (CenteIA).
- `mundo-dirsi/aprendido/` — notas de aprendizaje (agentes e IA, blockchain,
  despliegue, ingeniería inversa, portafolio y empleo…).

La ingesta acepta carpetas a medida: `python ingest.py carpeta1 carpeta2`.
Formatos: Markdown (`.md`, troceado respetando encabezados) y PDF (`.pdf`,
una sección por página).

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
a 0,50, la API responde «sin resultados claros» y no devuelve
fuentes — ver «Límites honestos»
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
| `app.py` | API Flask: `GET /api/health`, `POST /preguntar` |
| `data/` | Índice FAISS, fragmentos y metadatos generados por la ingesta |

## Límites honestos

- **Sin generación**: la respuesta es una composición de fragmentos, no un
  texto redactado. Responde «con las palabras del corpus»: si el corpus no
  lo dice, no lo inventa — pero tampoco parafrasea ni conecta ideas de
  varios documentos.
- **Calidad ligada al corpus**: con 12 documentos pequeños, una pregunta
  fuera de tema no debe rellenar la respuesta. La política está calibrada
  con pruebas reales sobre este corpus (2026-11-02, recalculada en el
  Ciclo 2 tras el troceado con títulos y la reordenación híbrida):
  ningún fragmento por debajo de 0,30 entra nunca, y si la mejor
  similitud semántica de la consulta queda por debajo de 0,50 la API
  responde «sin resultados claros en tus documentos», con
  `confianza: "baja"` y `fuentes` vacía. Similitudes semánticas máximas
  medidas: dentro de tema, REA 0,526 · automatizaciones 0,697 ·
  45 frente a 90 prompts 0,588 · diseño CenteIA 0,707 · agentes 0,736;
  fuera de tema, la capital de Francia no devuelve ningún fragmento
  ≥ 0,30, el clima 0,445, el texto basura 0,342 y un lorem ipsum 0,496
  (esta vez bajo la puerta, pero por poco: en el Ciclo 1 llegó a 0,52
  y se colaba como «claro»; el margen sigue siendo estrecho y ningún
  umbral único separa limpiamente con este modelo pequeño).
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
5. Despliegue (p. ej. PythonAnywhere) y una interfaz web mínima de chat.

## Stack

Python · Flask · sentence-transformers · FAISS · pypdf — todo local,
sin claves de API.
