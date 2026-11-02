"""API Flask del RAG demo.

Endpoints:
    GET  /api/health   -> estado y conteos (documentos, fragmentos)
    POST /preguntar    -> {"pregunta": "..."} devuelve respuesta extractiva
                          compuesta desde los fragmentos + fuentes citadas.

Arranque:
    python ingest.py   # primero, una vez (o cuando cambie el corpus)
    python app.py      # sirve en http://127.0.0.1:5057
"""
from flask import Flask, jsonify, request

from rag_core import MODEL_NAME, RagStore, compose_answer

app = Flask(__name__)
store = RagStore()


@app.get("/api/health")
def health():
    return jsonify({
        "estado": "ok" if store.ready else "sin_indice",
        "documentos": store.meta.get("documentos", 0),
        "fragmentos": store.meta.get("fragmentos", len(store.chunks)),
        "modelo_embeddings": store.meta.get("modelo", MODEL_NAME),
        "tipo_respuesta": "extractiva (sin LLM, sin claves de API)",
    })


@app.post("/preguntar")
def preguntar():
    data = request.get_json(silent=True) or {}
    pregunta = (data.get("pregunta") or "").strip()
    if not pregunta:
        return jsonify({"error": "Falta el campo 'pregunta'."}), 400
    if not store.ready:
        return jsonify({
            "error": "El índice no existe todavía. Ejecuta primero: python ingest.py"
        }), 503
    try:
        k = int(data.get("k", 4))
    except (TypeError, ValueError):
        k = 4
    k = max(1, min(k, 8))

    results = store.search(pregunta, k=k)
    fuentes = [
        {
            "n": n,
            "archivo": r["archivo"],
            "seccion": r["seccion"],
            "similitud": r["similitud"],
            "fragmento": r["fragmento"],
        }
        for n, r in enumerate(results, start=1)
    ]
    return jsonify({
        "pregunta": pregunta,
        "tipo_respuesta": (
            "extractiva — compuesta desde los fragmentos recuperados; "
            "ningún LLM redactó esta respuesta"
        ),
        "respuesta": compose_answer(pregunta, results),
        "fuentes": fuentes,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5057)
