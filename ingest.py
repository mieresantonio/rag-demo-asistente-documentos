#!/usr/bin/env python3
"""Ingesta reproducible del RAG demo.

Uso:
    python ingest.py                 # corpus por defecto
    python ingest.py carpeta1 carpeta2   # carpetas a medida

Lee documentos .md y .pdf, los trocea, calcula embeddings locales con
sentence-transformers y guarda el índice FAISS en data/.
"""
import sys

from rag_core import DEFAULT_CORPUS_DIRS, build_index

if __name__ == "__main__":
    dirs = sys.argv[1:] or DEFAULT_CORPUS_DIRS
    print("Corpus:", ", ".join(dirs))
    meta = build_index(dirs)
    print(f"Documentos ingeridos: {meta['documentos']}")
    for f in meta["archivos"]:
        print("  -", f)
    print(f"Fragmentos indexados: {meta['fragmentos']}")
    print(f"Modelo: {meta['modelo']} (dimensión {meta['dimension']})")
    print("Índice guardado en data/index.faiss")
