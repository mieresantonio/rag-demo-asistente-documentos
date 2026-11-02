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

Probar:

```bash
curl http://127.0.0.1:5057/api/health

curl -X POST http://127.0.0.1:5057/preguntar \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué es REA y para qué sirve?"}'
```

La respuesta incluye `respuesta` (extractiva, con citas `[1]`, `[2]`…) y
`fuentes`, la lista de fragmentos usados con su archivo, su sección y su
similitud.

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
troceado por secciones → fragmentos de ~900 caracteres con solape de ~180
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
la pregunta se vectoriza con el mismo modelo → se recuperan los k=4
fragmentos más parecidos (umbral mínimo de similitud 0,20)
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
  fuera de tema devuelve fragmentos poco relevantes o ninguno (hay umbral de
  similitud, y por debajo de él la API lo dice en vez de rellenar).
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
2. Búsqueda híbrida (semántica + palabras clave) para nombres y siglas.
3. Re-troceado adaptativo y metadatos por página en PDF.
4. Evaluación con un set fijo de preguntas/respuestas esperadas.
5. Despliegue (p. ej. PythonAnywhere) y una interfaz web mínima de chat.

## Stack

Python · Flask · sentence-transformers · FAISS · pypdf — todo local,
sin claves de API.
