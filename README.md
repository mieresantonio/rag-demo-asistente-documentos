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
fragmentos más parecidos (suelo mínimo de similitud 0,30; si ni el mejor
fragmento llega a 0,50, la API responde «sin resultados claros» y no
devuelve fuentes — ver «Límites honestos»)
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
  con pruebas reales sobre este corpus (2026-11-02): ningún fragmento por
  debajo de 0,30 entra nunca, y si la mejor similitud de la consulta queda
  por debajo de 0,50 la API responde «sin resultados claros en tus
  documentos», con `confianza: "baja"` y `fuentes` vacía. En las pruebas,
  las preguntas dentro de tema puntuaron 0,44–0,74 y las de fuera de tema
  o de texto basura 0,41–0,46: la zona 0,44–0,50 se solapa, así que se
  trata como «no clara» y puede tocar reformular alguna pregunta legítima
  mal planteada. La calibración tampoco es perfecta: un texto de relleno
  en latín (lorem ipsum) alcanzó 0,52 en las pruebas y se cuela como
  «claro»; ningún umbral único separa limpiamente con este modelo pequeño.
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
