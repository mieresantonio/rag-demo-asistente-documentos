"""Núcleo del RAG demo: troceado, embeddings, índice FAISS y recuperación.

Sin claves de API: los embeddings se calculan localmente con
sentence-transformers y la respuesta es EXTRACTIVA (se compone desde los
fragmentos recuperados, no la genera un LLM).
"""
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_PATH = os.path.join(DATA_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(DATA_DIR, "chunks.json")
META_PATH = os.path.join(DATA_DIR, "meta.json")

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Carpetas del corpus por defecto (materiales propios de Antonio).
DEFAULT_CORPUS_DIRS = [
    os.path.expanduser("~/workspace/centeia-materiales"),
    os.path.expanduser("~/workspace/mundo-dirsi/aprendido"),
]

CHUNK_CHARS = 900      # tamaño objetivo de cada fragmento
OVERLAP_CHARS = 180    # solape entre fragmentos consecutivos de una sección

# Política de similitud (calibrada con pruebas reales el 2026-11-02):
# - UMBRAL_SIMILITUD es el suelo duro: ningún fragmento por debajo entra.
# - UMBRAL_CLARO se aplica a la MEJOR similitud de la consulta: si ni el
#   mejor fragmento lo alcanza, la API responde «sin resultados claros»
#   y no devuelve fuentes, en vez de rellenar con fragmentos débiles.
# Medido sobre el corpus actual (similitud máxima por consulta):
# preguntas dentro de tema 0,44–0,74; fuera de tema y texto basura
# 0,41–0,46. La zona 0,44–0,50 se solapa, por eso se trata como «no
# clara»: es preferible pedir una reformulación que presentar como
# respuesta algo que puede no tener relación con la pregunta.
UMBRAL_SIMILITUD = 0.30
UMBRAL_CLARO = 0.50


# ---------------------------------------------------------------- troceado
def split_markdown_sections(text):
    """Devuelve [(encabezado, cuerpo)] respetando la estructura # del Markdown."""
    sections = []
    current_title = "(sin título)"
    current_lines = []
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        m = re.match(r"^(#{1,4})\s+(.*)", line) if not in_code else None
        if m:
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = m.group(2).strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))
    return [(t, b) for t, b in sections if len(b) >= 40]


def chunk_text(text, size=CHUNK_CHARS, overlap=OVERLAP_CHARS):
    """Trocea por párrafos acumulando hasta `size` caracteres, con solape."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(para) > size:  # párrafo gigante: ventana deslizante dura
            if current:
                chunks.append(current)
                current = ""
            step = size - overlap
            for i in range(0, len(para), step):
                chunks.append(para[i:i + size])
            continue
        candidate = (current + "\n\n" + para) if current else para
        if len(candidate) <= size:
            current = candidate
        else:
            chunks.append(current)
            # solape: arrastra el último párrafo al siguiente fragmento
            tail = para if len(para) <= overlap else current[-overlap:]
            current = (tail + "\n\n" + para) if tail != para else para
    if current:
        chunks.append(current)
    return [c for c in chunks if len(c) >= 40]


def extract_pdf_pages(path):
    """Devuelve [(sección, texto)] con una sección por página."""
    from pypdf import PdfReader
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        txt = (page.extract_text() or "").strip()
        if len(txt) >= 40:
            pages.append((f"Página {i}", txt))
    return pages


def collect_chunks(corpus_dirs):
    """Lee .md/.pdf de las carpetas dadas y produce la lista de fragmentos."""
    chunks = []
    documents = set()
    for folder in corpus_dirs:
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            if not os.path.isfile(path):
                continue
            lower = name.lower()
            if lower.endswith(".md"):
                with open(path, encoding="utf-8") as fh:
                    sections = split_markdown_sections(fh.read())
            elif lower.endswith(".pdf"):
                sections = extract_pdf_pages(path)
            else:
                continue
            rel = os.path.relpath(path, os.path.expanduser("~/workspace"))
            documents.add(rel)
            for title, body in sections:
                for piece in chunk_text(body):
                    chunks.append({
                        "archivo": rel,
                        "seccion": title,
                        "texto": piece,
                    })
    return chunks, sorted(documents)


# ---------------------------------------------------------------- embeddings
def load_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def build_index(corpus_dirs=None):
    """Ingesta completa: trocea, vectoriza y guarda índice FAISS + metadatos."""
    import faiss
    import numpy as np

    corpus_dirs = corpus_dirs or DEFAULT_CORPUS_DIRS
    chunks, documents = collect_chunks(corpus_dirs)
    if not chunks:
        raise RuntimeError("No se encontraron documentos en el corpus.")

    model = load_model()
    texts = [c["texto"] for c in chunks]
    embeddings = model.encode(
        texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True
    )
    embeddings = np.asarray(embeddings, dtype="float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])  # coseno (vectores normalizados)
    index.add(embeddings)

    os.makedirs(DATA_DIR, exist_ok=True)
    faiss.write_index(index, INDEX_PATH)
    with open(CHUNKS_PATH, "w", encoding="utf-8") as fh:
        json.dump(chunks, fh, ensure_ascii=False)
    meta = {
        "modelo": MODEL_NAME,
        "documentos": len(documents),
        "archivos": documents,
        "fragmentos": len(chunks),
        "dimension": int(embeddings.shape[1]),
    }
    with open(META_PATH, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    return meta


# ---------------------------------------------------------------- consulta
class RagStore:
    """Carga el índice una vez y responde preguntas recuperando fragmentos."""

    def __init__(self):
        self.index = None
        self.chunks = []
        self.meta = {}
        self.model = None
        if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
            import faiss
            self.index = faiss.read_index(INDEX_PATH)
            with open(CHUNKS_PATH, encoding="utf-8") as fh:
                self.chunks = json.load(fh)
            if os.path.exists(META_PATH):
                with open(META_PATH, encoding="utf-8") as fh:
                    self.meta = json.load(fh)

    @property
    def ready(self):
        return self.index is not None and bool(self.chunks)

    def _embed(self, text):
        if self.model is None:
            self.model = load_model()
        import numpy as np
        vec = self.model.encode([text], normalize_embeddings=True)
        return np.asarray(vec, dtype="float32")

    def search(self, question, k=4, min_score=UMBRAL_SIMILITUD):
        """Recupera los k fragmentos más parecidos (similitud coseno)."""
        if not self.ready:
            return []
        vec = self._embed(question)
        scores, ids = self.index.search(vec, k)
        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0 or score < min_score:
                continue
            c = self.chunks[int(idx)]
            results.append({
                "archivo": c["archivo"],
                "seccion": c["seccion"],
                "similitud": round(float(score), 3),
                "fragmento": c["texto"],
            })
        return results


def compose_sin_resultados_claros(similitud_maxima):
    """Texto honesto cuando ningún fragmento supera el umbral claro.

    Se usa cuando la mejor similitud queda por debajo de UMBRAL_CLARO:
    la API lo dice explícitamente y no presenta fragmentos como si
    fueran una respuesta.
    """
    def _num(valor, decimales=2):
        return ("%.*f" % (decimales, valor)).replace(".", ",")

    if similitud_maxima is None:
        detalle = (
            "Ningún fragmento alcanzó siquiera el umbral mínimo de %s."
            % _num(UMBRAL_SIMILITUD)
        )
    else:
        detalle = (
            "La similitud máxima encontrada fue %s y el umbral de "
            "claridad es %s." % (_num(similitud_maxima, 3), _num(UMBRAL_CLARO))
        )
    return (
        "Sin resultados claros en tus documentos para esa pregunta. "
        + detalle
        + " Prueba reformularla con términos más cercanos al contenido "
          "del corpus o amplía el corpus y vuelve a ejecutar la ingesta."
    )


def compose_answer(question, results):
    """Respuesta EXTRACTIVA: se construye solo con los fragmentos recuperados.

    No hay generación de un LLM: se ordenan los fragmentos por relevancia y
    se presentan con su cita [n], para que la respuesta sea verificable.
    """
    if not results:
        return (
            "No encontré fragmentos relevantes en el corpus para esa pregunta. "
            "Prueba reformularla o amplía el corpus y vuelve a ejecutar la ingesta."
        )
    lines = [
        "Respuesta extractiva (compuesta desde los fragmentos recuperados, "
        "sin generación de un modelo de lenguaje):",
        "",
    ]
    for n, r in enumerate(results, start=1):
        excerpt = " ".join(r["fragmento"].split())
        if len(excerpt) > 700:
            excerpt = excerpt[:700].rsplit(" ", 1)[0] + "…"
        lines.append(f"[{n}] {excerpt}")
        lines.append("")
    return "\n".join(lines).strip()
