"""Núcleo del RAG demo: troceado, embeddings, índice FAISS y recuperación.

Sin claves de API: los embeddings se calculan localmente con
sentence-transformers y la respuesta es EXTRACTIVA (se compone desde los
fragmentos recuperados, no la genera un LLM).
"""
import json
import os
import re
import threading
import unicodedata
from functools import lru_cache

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

# Reordenación híbrida acotada (calibrada el 2026-11-02, Ciclo 2):
# la búsqueda semántica pura dejaba «¿Cómo se despliega una
# aplicación?» sin ningún fragmento de despliegue.md ni en el top-12
# (su mejor fragmento puntuaba 0,371: el documento trata el despliegue
# como doctrina —tarjetas, costes, runbook— y el embedding de cada
# fragmento de ~900 caracteres diluye el tema). Por eso, sobre los
# candidatos que ya superan el suelo semántico, se reordena sumando
# una bonificación pequeña por coincidencia léxica de raíces entre la
# pregunta y los metadatos del fragmento (archivo + sección, peso
# 0,30) y su texto (peso 0,10). La `similitud` que se devuelve sigue
# siendo la semántica pura, y la puerta de claridad (UMBRAL_CLARO) no
# cambia: se aplica a la mejor similitud semántica de lo devuelto.
PESO_TITULO = 0.30
PESO_TEXTO = 0.10

_PALABRAS_VACIAS = {
    "como", "cual", "cuales", "que", "para", "una", "unos", "unas",
    "del", "las", "los", "por", "con", "sin", "hace", "hoy", "cuando",
    "donde", "desde", "entre", "sobre", "segun", "esto", "esta",
    "este", "es",
}


# Caché de raíces: `_raices` es una función pura del texto y `search`
# la recalculaba para los mismos fragmentos en cada petición; los
# llamantes solo leen el conjunto (intersecciones), nunca lo mutan.
@lru_cache(maxsize=4096)
def _raices(texto):
    """Raíces léxicas simples: palabras de 4+ letras sin tildes ni
    palabras vacías, recortadas a 6 caracteres («despliega»,
    «despliegue» y «desplegar» comparten la raíz «despli»)."""
    plano = unicodedata.normalize("NFKD", (texto or "").lower())
    plano = "".join(c for c in plano if not unicodedata.combining(c))
    return {
        palabra[:6]
        for palabra in re.findall(r"[a-z0-9]+", plano)
        if len(palabra) >= 4 and palabra not in _PALABRAS_VACIAS
    }


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


def _doc_title_and_body(title, body):
    """Separa la línea de encabezado del cuerpo de una sección Markdown.

    El cuerpo que devuelve `split_markdown_sections` empieza por la
    propia línea del encabezado; sin separarla, el troceado la aísla
    en un fragmento de solo título (16 de 135 fragmentos en la ingesta
    de 2026-11-02) y los demás fragmentos de la sección se quedan sin
    ningún contexto de título al calcular su embedding.
    """
    lines = body.splitlines()
    if lines and re.match(r"^#{1,4}\s+", lines[0]):
        return "\n".join(lines[1:]).strip()
    return body


def collect_chunks(corpus_dirs):
    """Lee .md/.pdf de las carpetas dadas y produce la lista de fragmentos.

    Cada fragmento Markdown lleva antepuestos el título del documento
    y el de su sección: ese contexto forma parte del texto que se
    vectoriza (y del fragmento citado), para que una pregunta sobre el
    tema de una sección pueda recuperar también sus fragmentos segundo
    y siguientes, no solo el primero.
    """
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
                    raw = fh.read()
                sections = split_markdown_sections(raw)
                m = re.search(r"^#\s+(.+)", raw, flags=re.MULTILINE)
                doc_title = m.group(1).strip() if m else None
            elif lower.endswith(".pdf"):
                sections = extract_pdf_pages(path)
                doc_title = None
            else:
                continue
            rel = os.path.relpath(path, os.path.expanduser("~/workspace"))
            documents.add(rel)
            for title, body in sections:
                if lower.endswith(".md"):
                    body = _doc_title_and_body(title, body)
                    encabezado = []
                    if doc_title and doc_title != title:
                        encabezado.append(doc_title)
                    if title and title != "(sin título)":
                        encabezado.append(title)
                    prefijo = "\n".join(encabezado)
                else:
                    prefijo = ""
                for piece in chunk_text(body):
                    texto = (prefijo + "\n\n" + piece) if prefijo else piece
                    chunks.append({
                        "archivo": rel,
                        "seccion": title,
                        "texto": texto,
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
    meta = {
        "modelo": MODEL_NAME,
        "documentos": len(documents),
        "archivos": documents,
        "fragmentos": len(chunks),
        "dimension": int(embeddings.shape[1]),
    }
    # Escritura atómica de los tres artefactos (ronda 11, bucle 3).
    # Antes se escribía directamente sobre los destinos, en secuencia:
    # un corte dentro de esa ventana (~10 ms) dejaba un conjunto
    # mezclado o truncado, y medido en sondas eso importa: un
    # chunks.json truncado o un index.faiss truncado impiden arrancar
    # (la excepción sale de RagStore en el import de app.py), y un
    # índice nuevo con los fragmentos viejos deja /api/health en «ok»
    # mientras las preguntas que tocan ids nuevos reciben un 500 por
    # IndexError en `search`. Por eso:
    #
    # Fase 1 — preparación: cada artefacto se escribe COMPLETO en un
    # temporal del mismo directorio (misma partición, renombre
    # atómico posible) y se sincroniza a disco. Los destinos no se
    # tocan en esta fase: cualquier corte aquí deja el conjunto
    # anterior íntegro y servible, y los temporales huérfanos no los
    # lee RagStore (busca los nombres exactos).
    #
    # Fase 2 — publicación: tres `os.replace` en este orden:
    #   1. chunks.json: es el fichero que `search` desreferencia por
    #      los ids que devuelve el índice; sus datos nuevos deben
    #      estar en su sitio antes de que el índice nuevo exista.
    #   2. index.faiss: RagStore lo lee primero y es la fuente de
    #      los ids; solo se publica cuando ya puede desreferenciarse
    #      contra los fragmentos publicados en el paso anterior.
    #   3. meta.json: RagStore lo lee el último y /api/health lo usa
    #      como descriptor del conjunto (documentos/fragmentos), así
    #      que solo se publica cuando la pareja índice+fragmentos que
    #      describe ya es la nueva; actúa como marca de cierre.
    # Entre un replace y el siguiente la ventana residual es la de
    # tres llamadas al sistema encadenadas (sin escrituras de datos
    # de por medio): no es eliminable con renombres simples —exigiría
    # directorios por generación—, pero la ventana de escritura, que
    # es la que dura y la que truncaba ficheros, queda cerrada.
    tmp_index = INDEX_PATH + ".tmp"
    tmp_chunks = CHUNKS_PATH + ".tmp"
    tmp_meta = META_PATH + ".tmp"
    temporales = (tmp_index, tmp_chunks, tmp_meta)
    try:
        faiss.write_index(index, tmp_index)
        with open(tmp_index, "rb") as fh:
            os.fsync(fh.fileno())
        with open(tmp_chunks, "w", encoding="utf-8") as fh:
            json.dump(chunks, fh, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        with open(tmp_meta, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_chunks, CHUNKS_PATH)
        os.replace(tmp_index, INDEX_PATH)
        os.replace(tmp_meta, META_PATH)
    finally:
        # Tras publicar, los temporales ya no existen (fueron
        # renombrados); si algo falló en la fase 1, se retiran los
        # que queden para no dejar residuos en data/.
        for tmp in temporales:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
    return meta


# ---------------------------------------------------------------- consulta
def _comprobar_coherencia(index, chunks, meta):
    """Cuadre mínimo del conjunto índice + fragmentos + metadatos.

    Lanza ValueError con el motivo si el conjunto no es servible:
    el nº de vectores del índice, el nº de fragmentos cargados y el
    que meta.json declara deben ser EL MISMO número (si meta trae un
    desglose por documento —la lista «archivos» frente a
    «documentos», o un dict de fragmentos por documento—, su suma
    también debe cuadrar, y la «dimension» declarada debe ser la del
    índice). Sin este cuadre, medido en la ronda 11, la app mentía:
    un índice de 568 vectores con 527 fragmentos dejaba /api/health
    en «ok» con conteos de otro conjunto y `search` reventaba con
    IndexError solo en las preguntas que tocaban los ids nuevos.
    """
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("chunks.json no es una lista de fragmentos "
                         "no vacía")
    n = len(chunks)
    if index.ntotal != n:
        raise ValueError(
            "el índice tiene %d vectores y chunks.json %d fragmentos"
            % (index.ntotal, n))
    if not isinstance(meta, dict):
        raise ValueError("meta.json no es un objeto JSON")
    fragmentos_meta = meta.get("fragmentos")
    if fragmentos_meta is not None and fragmentos_meta != n:
        raise ValueError(
            "meta.json declara %s fragmentos y chunks.json tiene %d"
            % (fragmentos_meta, n))
    dimension_meta = meta.get("dimension")
    if dimension_meta is not None and dimension_meta != index.d:
        raise ValueError(
            "meta.json declara dimensión %s y el índice tiene %d"
            % (dimension_meta, index.d))
    archivos = meta.get("archivos")
    documentos = meta.get("documentos")
    if archivos is not None and documentos is not None \
            and len(archivos) != documentos:
        raise ValueError(
            "meta.json declara %s documentos pero su desglose "
            "«archivos» lista %d" % (documentos, len(archivos)))
    for clave in ("fragmentos_por_documento", "fragmentos_por_archivo"):
        desglose = meta.get(clave)
        if isinstance(desglose, dict) and sum(desglose.values()) != n:
            raise ValueError(
                "el desglose «%s» de meta.json suma %s fragmentos "
                "y chunks.json tiene %d"
                % (clave, sum(desglose.values()), n))


class RagStore:
    """Carga el índice una vez y responde preguntas recuperando fragmentos."""

    def __init__(self):
        self.index = None
        self.chunks = []
        self.meta = {}
        self.model = None
        self._model_lock = threading.Lock()
        if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
            # Carga con red de seguridad (ronda 12): las escrituras
            # atómicas de build_index evitan PRODUCIR un conjunto
            # incoherente o truncado, pero el estado puede aparecer
            # por otra vía (copia manual, disco, un índice de otra
            # foto del corpus). Antes, un fichero corrupto reventaba
            # aquí y la app ni arrancaba, y un conjunto incoherente
            # cargaba «bien» y mentía en health o fallaba según la
            # pregunta. Ahora cualquier fallo de lectura o de cuadre
            # cae al MISMO estado que ya existe para «sin_indice»
            # (index None, chunks y meta vacíos: health lo reporta
            # así y /preguntar responde 503), registrando el motivo.
            try:
                import faiss
                index = faiss.read_index(INDEX_PATH)
                with open(CHUNKS_PATH, encoding="utf-8") as fh:
                    chunks = json.load(fh)
                meta = {}
                if os.path.exists(META_PATH):
                    with open(META_PATH, encoding="utf-8") as fh:
                        meta = json.load(fh)
                _comprobar_coherencia(index, chunks, meta)
            except Exception as exc:
                print(
                    "RagStore: conjunto de artefactos no servible "
                    "(%s); se arranca en estado «sin_indice»." % (exc,),
                    flush=True,
                )
                return
            self.index = index
            self.chunks = chunks
            self.meta = meta

    @property
    def ready(self):
        return self.index is not None and bool(self.chunks)

    @property
    def model_loaded(self):
        return self.model is not None

    def warmup(self):
        """Carga el modelo de embeddings y lo deja listo para buscar.

        Sin esto, el modelo se carga perezosamente en la primera
        pregunta y esa primera respuesta paga toda la carga (~26 s
        medidos en la primera búsqueda en frío, 2026-11-02) mientras
        `/api/health` ya decía «ok». Devuelve True si el modelo quedó
        cargado.
        """
        if not self.ready:
            return False
        self._embed("calentamiento del modelo")
        return self.model_loaded

    def _embed(self, text):
        # Doble comprobación con cerradura: sin ella, dos hilos que
        # llegan en frío a la vez (posible si la app se sirve por WSGI
        # sin pasar por warmup()) cargaban el modelo dos veces a la
        # vez — medido en la ronda 8: 2 cargas solapadas en 2/2
        # sondas. La comprobación exterior evita tomar la cerradura
        # en cada búsqueda una vez el modelo existe.
        if self.model is None:
            with self._model_lock:
                if self.model is None:
                    self.model = load_model()
        import numpy as np
        vec = self.model.encode([text], normalize_embeddings=True)
        return np.asarray(vec, dtype="float32")

    def search(self, question, k=4, min_score=UMBRAL_SIMILITUD):
        """Recupera los k fragmentos más relevantes para la pregunta.

        Primero manda la similitud semántica (coseno): solo los
        fragmentos que superan `min_score` son candidatos. Después se
        reordenan con la bonificación léxica acotada de PESO_TITULO /
        PESO_TEXTO (ver la nota junto a las constantes). La búsqueda
        en el índice pide todos los fragmentos: con un corpus de demo
        es barato, y un candidato con similitud modesta pero título
        exactamente del tema preguntado debe poder entrar en la
        reordenación (con un top-k semántico pequeño quedaba fuera).
        """
        if not self.ready:
            return []
        vec = self._embed(question)
        scores, ids = self.index.search(vec, self.index.ntotal)
        raices_pregunta = _raices(question)
        candidates = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0 or score < min_score:
                continue
            c = self.chunks[int(idx)]
            if raices_pregunta:
                en_titulo = len(raices_pregunta & _raices(
                    c["archivo"] + " " + c["seccion"])) / len(raices_pregunta)
                en_texto = len(raices_pregunta & _raices(
                    c["texto"])) / len(raices_pregunta)
            else:
                en_titulo = en_texto = 0.0
            relevancia = float(score) + PESO_TITULO * en_titulo \
                + PESO_TEXTO * en_texto
            candidates.append((relevancia, float(score), c))
        candidates.sort(key=lambda item: (-item[0], -item[1]))
        # Mejor similitud semántica de TODA la consulta (no solo de lo
        # devuelto): es el dato de la puerta de claridad del Ciclo 1 y
        # viaja en cada resultado para que la API lo lea sin recalcular.
        similitud_maxima = max(
            (score for _, score, _ in candidates), default=None)
        results = []
        for relevancia, score, c in candidates[:k]:
            results.append({
                "archivo": c["archivo"],
                "seccion": c["seccion"],
                "similitud": round(score, 3),
                "relevancia": round(relevancia, 3),
                "similitud_maxima": (
                    round(similitud_maxima, 3)
                    if similitud_maxima is not None else None
                ),
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
