#!/usr/bin/env python3
"""Reconstruye data/index.faiss desde data/chunks.json versionado.

El índice FAISS no está en el repo (está en .gitignore: es un
artefacto que genera la ingesta). Pero sus entradas SÍ están
versionadas: data/chunks.json (los 572 fragmentos con su archivo y
su sección) y data/meta.json (conteos y modelo). Este script
reproduce el índice a partir de ellas: vectoriza los fragmentos con
el mismo modelo y en el mismo orden que la ingesta, y escribe el
mismo índice que produciría `python ingest.py` sobre el corpus
intacto — sin necesitar las carpetas del corpus, que viven fuera
del repo (centeia-materiales, mundo-dirsi/aprendido) y no existen
en un clon fresco ni en la CI.

Lo usa la CI (.github/workflows/ci.yml) para levantar la demo
contra el corpus completo versionado antes de correr la suite y el
canario. También sirve en local para regenerar un índice borrado
sin re-ingerir el corpus.

NO toca chunks.json ni meta.json (entradas de solo lectura: se
verifica su MD5 antes y después) y NO re-trocea nada: si el corpus
cambió, la herramienta correcta sigue siendo `python ingest.py`,
que vuelve a trocear y a escribir chunks.json y meta.json.

Seguridad: si meta.json declara otro modelo que el de rag_core, o
sus conteos no cuadran con chunks.json, el script se niega: un
índice reconstruido sobre datos incoherentes mentiría.
"""
import hashlib
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from rag_core import (  # noqa: E402
    CHUNKS_PATH,
    DATA_DIR,
    INDEX_PATH,
    META_PATH,
    MODEL_NAME,
    load_model,
)


def md5_de(ruta):
    h = hashlib.md5()
    with open(ruta, "rb") as fh:
        for bloque in iter(lambda: fh.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def main():
    if not os.path.exists(CHUNKS_PATH):
        print(f"ERROR: no existe {CHUNKS_PATH}; sin fragmentos "
              f"versionados no hay índice que reconstruir.")
        return 1
    if not os.path.exists(META_PATH):
        print(f"ERROR: no existe {META_PATH}.")
        return 1

    md5_chunks_antes = md5_de(CHUNKS_PATH)
    md5_meta_antes = md5_de(META_PATH)

    with open(META_PATH, encoding="utf-8") as fh:
        meta = json.load(fh)
    with open(CHUNKS_PATH, encoding="utf-8") as fh:
        chunks = json.load(fh)

    if meta.get("modelo") != MODEL_NAME:
        print(f"ERROR: meta.json declara el modelo "
              f"{meta.get('modelo')!r} y rag_core usa {MODEL_NAME!r}. "
              f"Reconstruir con otro modelo cambiaría todas las "
              f"similitudes: re-ingiere con `python ingest.py`.")
        return 1
    if len(chunks) != meta.get("fragmentos"):
        print(f"ERROR: chunks.json trae {len(chunks)} fragmentos y "
              f"meta.json declara {meta.get('fragmentos')}. Datos "
              f"incoherentes: re-ingiere con `python ingest.py`.")
        return 1
    if len({c.get("archivo") for c in chunks}) != meta.get("documentos"):
        print(f"ERROR: chunks.json cubre "
              f"{len({c.get('archivo') for c in chunks})} archivos "
              f"distintos y meta.json declara "
              f"{meta.get('documentos')} documentos. Datos incoherentes.")
        return 1

    import faiss
    import numpy as np

    print(f"Reconstruyendo el índice desde {CHUNKS_PATH}: "
          f"{meta['documentos']} documentos, {len(chunks)} fragmentos, "
          f"modelo {MODEL_NAME}.")
    model = load_model()
    texts = [c["texto"] for c in chunks]
    embeddings = model.encode(
        texts, batch_size=32, show_progress_bar=False,
        normalize_embeddings=True,
    )
    embeddings = np.asarray(embeddings, dtype="float32")

    if embeddings.shape[1] != meta.get("dimension"):
        print(f"ERROR: el modelo produce dimensión "
              f"{embeddings.shape[1]} y meta.json declara "
              f"{meta.get('dimension')}.")
        return 1

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    # Publicación atómica, como la ingesta: se escribe a un temporal
    # del mismo directorio y se renombra, para no dejar un índice a
    # medias si algo se corta.
    tmp_path = os.path.join(DATA_DIR, ".index.faiss.tmp")
    faiss.write_index(index, tmp_path)
    os.replace(tmp_path, INDEX_PATH)

    # Verificación: se relee el índice escrito y se comprueba que
    # las entradas no se tocaron.
    comprobado = faiss.read_index(INDEX_PATH)
    if comprobado.ntotal != len(chunks):
        print(f"ERROR: el índice escrito tiene {comprobado.ntotal} "
              f"vectores, esperados {len(chunks)}.")
        return 1
    if (md5_de(CHUNKS_PATH) != md5_chunks_antes
            or md5_de(META_PATH) != md5_meta_antes):
        print("ERROR: chunks.json o meta.json cambiaron durante la "
              "reconstrucción (no debería pasar: son de solo lectura).")
        return 1

    print(f"Índice guardado en {INDEX_PATH}: {comprobado.ntotal} "
          f"vectores, dimensión {embeddings.shape[1]}.")
    print("chunks.json y meta.json intactos (MD5 sin cambios).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
