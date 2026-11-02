#!/usr/bin/env python3
"""Refresca `corpus-extra/` con los improvement-log de las apps.

El corpus inicial del RAG demo son las carpetas por defecto de
`rag_core.DEFAULT_CORPUS_DIRS` (materiales CenteIA + aprendido de
mundo-dirsi). Desde el Ciclo 5 (2026-11-02) se suma una tercera
carpeta, `corpus-extra/` DENTRO de este proyecto, con una copia de
los `improvement-log.md` de las apps mejoradas en la Fase 2, para que
la demo también responda sobre ese trabajo de mejora.

Por qué copias y no las carpetas originales: la ingesta
(`rag_core.collect_chunks`) solo lee los archivos de primer nivel de
cada carpeta que se le pasa, y los registros están repartidos en
carpetas distintas (una por app), todos con el mismo nombre
`improvement-log.md`. Este script los copia aquí con un nombre por
app (`<app>-improvement-log.md`: el nombre forma parte de los
metadatos que se citan y de la coincidencia léxica de títulos, así
que que se sepa de qué app es cada registro importa).

Las copias son FOTOCOPIA EXACTA del original en el momento de
ejecutar el script (verificable por MD5): si un registro cambia en su
app, hay que volver a ejecutar este script y después la ingesta:

    .venv/bin/python refresh_corpus_extra.py
    .venv/bin/python ingest.py ~/workspace/centeia-materiales \
        ~/workspace/mundo-dirsi/aprendido ~/workspace/rag-demo/corpus-extra

El script es idempotente: borra de `corpus-extra/` cualquier `.md`
que ya no esté en la lista, para que la carpeta sea siempre el
resultado exacto de esta lista y no una acumulación manual.
"""
import hashlib
import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_DIR = os.path.join(BASE_DIR, "corpus-extra")
WORKSPACE = os.path.expanduser("~/workspace")

# (ruta del original respecto a ~/workspace, nombre en corpus-extra/)
SOURCES = [
    ("portfolio-apps/segundo-yo/improvement-log.md",
     "segundo-yo-improvement-log.md"),
    ("portfolio-apps/api-segundo-yo/improvement-log.md",
     "api-segundo-yo-improvement-log.md"),
    ("portfolio-apps/biblioteca-prompts/improvement-log.md",
     "biblioteca-prompts-improvement-log.md"),
    ("demo-local-barberia/improvement-log.md",
     "barberia-improvement-log.md"),
    ("web3-apps/wallet-sim/improvement-log.md",
     "wallet-sim-improvement-log.md"),
    ("web3-apps/token-explorer/improvement-log.md",
     "token-explorer-improvement-log.md"),
    ("web3-apps/nft-studio/improvement-log.md",
     "nft-studio-improvement-log.md"),
    ("web3-apps/tx-builder/improvement-log.md",
     "tx-builder-improvement-log.md"),
    ("web3-apps/block-explorer/improvement-log.md",
     "block-explorer-improvement-log.md"),
    ("web3-apps/gas-calc/improvement-log.md",
     "gas-calc-improvement-log.md"),
    ("web3-apps/hash-lab/improvement-log.md",
     "hash-lab-improvement-log.md"),
    ("web3-apps/contract-play/improvement-log.md",
     "contract-play-improvement-log.md"),
    ("web3-apps/dao-vote/improvement-log.md",
     "dao-vote-improvement-log.md"),
    ("web3-apps/anti-phishing/improvement-log.md",
     "anti-phishing-improvement-log.md"),
    ("mundo-vida-ia/improvement-log.md",
     "mundo-vida-ia-improvement-log.md"),
    # EXCLUIDO a propósito: el improvement-log del propio rag-demo.
    # Es un documento AUTORREFERENTE: su sección RAG-M2 se titula
    # literalmente con una pregunta de la batería («¿Cómo se despliega
    # una aplicación?»), y al ingerirlo en el Ciclo 5 esa sección se
    # llevó la bonificación máxima de título y DESPLAZÓ a
    # despliegue.md de las posiciones 1–3 (conocido-bueno de los
    # Ciclos 2–3) a las 3–4: el refresco empeoraba una pregunta que ya
    # funcionaba, así que este registro queda fuera del corpus y su
    # exclusión es parte del ajuste documentado de ese ciclo (ver el
    # propio improvement-log.md del proyecto, Ciclo 5). El trabajo de
    # mejora del rag-demo se sigue contando en su registro; solo no se
    # auto-indexa.
]


def _md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def main():
    os.makedirs(DEST_DIR, exist_ok=True)
    esperados = {nombre for _, nombre in SOURCES}
    for nombre in sorted(os.listdir(DEST_DIR)):
        if nombre.endswith(".md") and nombre not in esperados:
            os.remove(os.path.join(DEST_DIR, nombre))
            print("  - eliminado (ya no está en la lista):", nombre)
    fallos = 0
    for rel, nombre in SOURCES:
        origen = os.path.join(WORKSPACE, rel)
        destino = os.path.join(DEST_DIR, nombre)
        if not os.path.isfile(origen):
            print("ERROR: no existe el original:", rel)
            fallos += 1
            continue
        shutil.copyfile(origen, destino)
        if _md5(origen) != _md5(destino):
            print("ERROR: la copia no coincide (MD5) con:", rel)
            fallos += 1
            continue
        print("  -", nombre, "<-", rel)
    print(f"corpus-extra/: {len(SOURCES) - fallos} documentos copiados "
          f"de {len(SOURCES)} previstos.")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
