#!/usr/bin/env python3
"""Ingesta reproducible del RAG demo.

Uso:
    python ingest.py                 # corpus por defecto
    python ingest.py carpeta1 carpeta2   # carpetas a medida
    python ingest.py --help          # solo muestra la ayuda, no ingiere

Lee documentos .md y .pdf, los trocea, calcula embeddings locales con
sentence-transformers y guarda el índice FAISS en data/.
"""
import argparse

from rag_core import DEFAULT_CORPUS_DIRS, build_index

if __name__ == "__main__":
    # Parseo con argparse (como tests_regresion_api.py): sin esto,
    # `--help` se tomaba por una carpeta más del corpus y cualquier
    # bandera desconocida arrancaba (o intentaba) la ingesta entera.
    # Sin argumentos el comportamiento es exactamente el de siempre.
    parser = argparse.ArgumentParser(
        description="Ingesta reproducible del RAG demo: trocea los "
                    "documentos .md y .pdf de las carpetas dadas, "
                    "calcula embeddings locales y guarda el índice "
                    "FAISS en data/.")
    parser.add_argument(
        "carpetas", nargs="*", metavar="CARPETA",
        help="carpetas del corpus; si no se da ninguna, se usan las "
             "carpetas por defecto")
    args = parser.parse_args()
    dirs = args.carpetas or DEFAULT_CORPUS_DIRS
    print("Corpus:", ", ".join(dirs))
    meta = build_index(dirs)
    print(f"Documentos ingeridos: {meta['documentos']}")
    for f in meta["archivos"]:
        print("  -", f)
    print(f"Fragmentos indexados: {meta['fragmentos']}")
    print(f"Modelo: {meta['modelo']} (dimensión {meta['dimension']})")
    print("Índice guardado en data/index.faiss")
