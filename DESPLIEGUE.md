# Despliegue — RAG demo

Guía para poner la demo en un servidor. Preparada el 2026-11-23
(Ciclo 15): los pasos locales que cita (ingesta, arranque, suite de
regresión) están verificados en el entorno de referencia; el primer
despliegue en un servidor real queda pendiente de ejecutar, y esta
guía es el procedimiento a seguir entonces.

## Lo que hay que saber antes de empezar

- **Sin claves de API ni servicios de pago.** Todo corre en local:
  embeddings con sentence-transformers y búsqueda con FAISS.
- **El índice NO está en el repo y nunca se versiona.**
  `data/index.faiss` está en `.gitignore`; el clon trae
  `data/chunks.json` y `data/meta.json`, pero hasta que no se
  ejecuta la ingesta en el servidor la API responde `sin_indice`
  en `/api/health` (con 0 documentos y 0 fragmentos) y `503` en
  `/preguntar`. Quien despliegue **debe regenerar el índice con
  `ingest.py` en el propio servidor** (paso 3 de abajo). No sirve
  copiar el `index.faiss` de otra máquina como atajo habitual:
  el índice va ligado a los fragmentos y los metadatos del
  conjunto, y `RagStore` rechaza el conjunto si no cuadra.
- **El corpus debe estar en el servidor.** La ingesta sin
  argumentos lee las tres carpetas por defecto: los materiales
  de CenteIA, las notas de mundo-dirsi y `corpus-extra/` (esta
  última vive dentro del repo, así que el clon ya la trae). Las
  dos primeras son carpetas del workspace del autor y hay que
  copiarlas al servidor (o ingerir solo con `corpus-extra/`, que
  cubre 15 de los 28 documentos).
- **Huella medida en el entorno de referencia** (Python 3.12.3,
  2026-11-23): el `.venv` con las dependencias ocupa **1,3 GB**
  (PyTorch solo-CPU, 773 MB) y los pesos del modelo de
  embeddings **458 MB** en la caché de Hugging Face. En total,
  la instalación ronda **1,8 GB** en disco antes de contar el
  corpus y el índice (~2 MB). El arranque carga el modelo en
  memoria (~24 s medidos el 2026-11-02).
- **Un solo worker.** El modelo de embeddings se carga por
  proceso: cada worker pagaría su propia carga (~25 s) y su
  propia memoria. Con gunicorn, `-w 1` (con hilos si hace
  falta concurrencia: `--threads 4`).

## Opción A — Servidor genérico con gunicorn (VPS, Render, Railway…)

```bash
git clone https://github.com/mieresantonio/rag-demo-asistente-documentos.git
cd rag-demo-asistente-documentos
python3 -m venv .venv
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install gunicorn
```

1. **Corpus:** copia las carpetas del corpus al servidor en las
   rutas por defecto (`~/workspace/centeia-materiales` y
   `~/workspace/mundo-dirsi/aprendido`), o ingiere con las rutas
   que uses: `python ingest.py carpeta1 carpeta2`.
2. **Índice:** `.venv/bin/python ingest.py` — debe terminar con
   `Documentos ingeridos: 28` y `Fragmentos indexados: 572` si el
   corpus está completo (si solo está `corpus-extra/`, 15
   documentos). Sin este paso, la app arranca en `sin_indice`.
3. **Prueba local:** `.venv/bin/python app.py` y, en otra
   terminal, `curl http://127.0.0.1:5057/api/health` (debe
   decir `"estado": "ok"`, 28 documentos, 572 fragmentos) y una
   pregunta de la sección «Pruébala en 2 minutos» del README.
4. **Servir:** `.venv/bin/gunicorn -w 1 --threads 4
   -b 127.0.0.1:5057 wsgi:application`. Con
   `RAG_DEMO_WARMUP=1` el worker carga el modelo al arrancar
   (la primera pregunta no paga la carga); sin ella, la primera
   pregunta tarda ~25 s y `/api/health` dice `calentando` hasta
   entonces. Detrás de un proxy inverso (nginx, Caddy) o del
   enrutado de la plataforma, se sirve como cualquier app WSGI.
5. **Variables de entorno útiles:** `RAG_DEMO_HOST` y
   `RAG_DEMO_PORT` solo afectan a `python app.py` (el puerto de
   gunicorn lo fija `-b`). `RAG_DEMO_WARMUP=1` activa el
   calentamiento en `wsgi.py`.

Notas por plataforma:

- **Render (plan gratuito):** el servicio duerme por inactividad
  y tarda en despertar; la primera petición tras el despertar
  paga además la carga del modelo (~25 s). El plan gratuito pide
  una verificación de 1 USD con tarjeta. Viable como demo, no
  como «siempre disponible».
- **PythonAnywhere:** ver la opción B.

## Opción B — PythonAnywhere

Límites del plan gratuito Beginner, verificados el 2026-11-23
en la ayuda oficial de PythonAnywhere
(`help.pythonanywhere.com/pages/FreeAccountsFeatures`): 1
aplicación web con 1 worker, **512 MB de disco**, 100
CPU-segundos al día, 2 consolas, salida a internet restringida
a una lista de sitios permitidos, y la app caduca al mes si no
se usa. El plan Developer cuesta 10 USD/mes y sube el disco a
5 GB.

**Consecuencia medida: el plan gratuito no cabe para esta demo.**
La instalación ronda 1,8 GB (ver arriba) frente a los 512 MB
del plan gratuito. Además, la cuenta BC123 ya aloja una
aplicación web (Block Ethos) y el plan gratuito solo permite
una. Desplegar aquí exige una decisión previa de Antonio: una
segunda cuenta gratuita no resuelve el disco, así que la ruta
realista es el plan Developer (10 USD/mes, 5 GB) o la opción A.

Pasos en PythonAnywhere (con un plan con disco suficiente):

1. Consola Bash: clonar el repo, crear el `.venv` e instalar
   como en la opción A (primero la build solo-CPU de PyTorch,
   después `requirements.txt`).
2. Copiar las carpetas del corpus al servidor (pestaña
   *Files* o `git`/descarga) y ejecutar la ingesta:
   `.venv/bin/python ingest.py`. Comprobar los conteos (28
   documentos, 572 fragmentos con el corpus completo).
3. Pestaña *Web*: crear la aplicación web manual (no el
   asistente de Flask) con la versión de Python del `.venv`,
   indicar la ruta del virtualenv, y editar el archivo WSGI
   para que importe esta app:
   ```python
   import sys
   sys.path.insert(0, '/home/<usuario>/rag-demo-asistente-documentos')
   from wsgi import application
   ```
   (sustituir `<usuario>` por el nombre de la cuenta).
4. *Reload* y comprobar: abrir la URL de la app y
   `https://<usuario>.pythonanywhere.com/api/health` (debe decir
   `"estado": "ok"` con 28/572; si dice `calentando`, la
   primera pregunta tardará ~25 s; si dice `sin_indice`, falta
   la ingesta del paso 2). Para que el worker caliente el
   modelo al arrancar, añadir `RAG_DEMO_WARMUP=1` en el archivo
   WSGI antes del import (`os.environ["RAG_DEMO_WARMUP"] = "1"`).
5. **Descarga del modelo:** la primera ejecución descarga los
   pesos (~458 MB) desde Hugging Face. En una cuenta gratuita
   la salida a internet está restringida a una lista de sitios
   permitidos; si la descarga falla por eso, la alternativa es
   subir los pesos por la pestaña *Files* a la caché
   (`~/.cache/huggingface`). Verificarlo en el primer
   despliegue.

## Comprobación post-despliegue

Con la app sirviendo, desde cualquier máquina:

```bash
curl https://<tu-dominio>/api/health
# -> "estado": "ok", 28 documentos, 572 fragmentos

curl -X POST https://<tu-dominio>/preguntar \
  -H 'Content-Type: application/json' \
  -d '{"pregunta": "¿Qué es REA y para qué sirve?"}'
# -> confianza alta, similitud máxima 0,526, primera fuente
#    ingenieria-inversa.md («Qué es REA»)
```

La sección «Pruébala en 2 minutos» del README trae seis
comprobaciones con sus cifras esperadas; si alguna cambia, es
una regresión o una mejora medible, no un error del ejemplo.

## Mantenimiento

- **Si cambia el corpus**, hay que volver a ejecutar la
  ingesta en el servidor (`refresh_corpus_extra.py` si cambiaron
  los registros de mejora, después `ingest.py`) y recargar la
  app. El índice es estático: la app no re-ingiere sola.
- **Si cambia el código**, desplegar la versión nueva y
  recargar; la suite de regresión
  (`.venv/bin/python tests_regresion_api.py`, 76
  comprobaciones) se corre antes de desplegar, en local.
- **Respaldo:** el repo en GitHub es la copia del código y del
  corpus versionado (`corpus-extra/`, `data/chunks.json`,
  `data/meta.json`); el índice se regenera, no se respalda.
