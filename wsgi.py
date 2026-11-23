"""Entrada WSGI del RAG demo.

Para servir la app con un servidor WSGI (gunicorn o PythonAnywhere)
en vez de con `python app.py`:

    gunicorn -w 1 -b 127.0.0.1:5057 wsgi:application

Un solo worker: el modelo de embeddings se carga por proceso y cada
worker pagaría su propia carga (~25 s) y su propia memoria.

Calentamiento del modelo: por defecto NO se calienta al importar
(la primera pregunta paga la carga, como cuando se sirve por WSGI
sin pasar por app.py; /api/health dice «calentando» hasta entonces).
Con RAG_DEMO_WARMUP=1 el modelo se carga al arrancar el worker, y
la primera pregunta ya responde rápido — a cambio de un arranque
más lento. Ver DESPLIEGUE.md.
"""
import os

from app import app as application
from app import store

if os.environ.get("RAG_DEMO_WARMUP") == "1" and store.ready:
    store.warmup()
