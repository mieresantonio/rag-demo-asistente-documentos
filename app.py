"""API Flask del RAG demo.

Endpoints:
    GET  /api/health   -> estado y conteos (documentos, fragmentos)
    POST /preguntar    -> {"pregunta": "..."} devuelve respuesta extractiva
                          compuesta desde los fragmentos + fuentes citadas.
                          "pregunta" debe ser una cadena de texto no vacía
                          de como máximo MAX_PREGUNTA caracteres; cualquier
                          otro tipo o valor recibe un 400 en JSON.

Arranque:
    python ingest.py   # primero, una vez (o cuando cambie el corpus)
    python app.py      # carga el modelo de embeddings y después sirve
                       # en http://127.0.0.1:5057 (la carga forma parte
                       # del arranque; /api/health dice «calentando»
                       # mientras el modelo no esté listo)
"""
from flask import Flask, jsonify, request

from rag_core import (
    MODEL_NAME,
    UMBRAL_CLARO,
    RagStore,
    compose_answer,
    compose_sin_resultados_claros,
)

MAX_PREGUNTA = 1000  # longitud máxima aceptada para el campo "pregunta"

app = Flask(__name__)
store = RagStore()


@app.get("/api/health")
def health():
    # «ok» solo cuando se puede responder de verdad: índice presente Y
    # modelo de embeddings ya cargado. Con el índice pero sin el modelo
    # (p. ej. si la app se sirve sin pasar por el arranque de abajo), el
    # estado honesto es «calentando», no «ok».
    if not store.ready:
        estado = "sin_indice"
    elif store.model_loaded:
        estado = "ok"
    else:
        estado = "calentando"
    return jsonify({
        "estado": estado,
        "modelo_cargado": store.model_loaded,
        "documentos": store.meta.get("documentos", 0),
        "fragmentos": store.meta.get("fragmentos", len(store.chunks)),
        "modelo_embeddings": store.meta.get("modelo", MODEL_NAME),
        "tipo_respuesta": "extractiva (sin LLM, sin claves de API)",
    })


@app.post("/preguntar")
def preguntar():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "error": "El cuerpo debe ser un objeto JSON con el campo 'pregunta'."
        }), 400
    if "pregunta" not in data or data.get("pregunta") is None:
        return jsonify({"error": "Falta el campo 'pregunta'."}), 400
    pregunta_raw = data.get("pregunta")
    if not isinstance(pregunta_raw, str):
        return jsonify({
            "error": "El campo 'pregunta' debe ser una cadena de texto."
        }), 400
    pregunta = pregunta_raw.strip()
    if not pregunta:
        return jsonify({"error": "El campo 'pregunta' no puede estar vacío."}), 400
    if len(pregunta) > MAX_PREGUNTA:
        return jsonify({
            "error": (
                "La pregunta es demasiado larga: máximo %d caracteres."
                % MAX_PREGUNTA
            )
        }), 400
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
    # La puerta de claridad mira la mejor similitud SEMÁNTICA de la
    # consulta en todo el corpus (definición del Ciclo 1): los
    # resultados vienen reordenados por relevancia híbrida, así que
    # no es necesariamente la similitud del primer resultado; la
    # búsqueda la adjunta a cada resultado como «similitud_maxima».
    similitud_maxima = results[0]["similitud_maxima"] if results else None
    if similitud_maxima is None or similitud_maxima < UMBRAL_CLARO:
        # Honestidad ante la duda: sin un fragmento claramente parecido,
        # no se rellena la respuesta con fragmentos débiles.
        return jsonify({
            "pregunta": pregunta,
            "tipo_respuesta": (
                "extractiva — compuesta desde los fragmentos recuperados; "
                "ningún LLM redactó esta respuesta"
            ),
            "respuesta": compose_sin_resultados_claros(similitud_maxima),
            "fuentes": [],
            "confianza": "baja",
            "similitud_maxima": similitud_maxima,
        })
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
        "confianza": "alta",
        "similitud_maxima": similitud_maxima,
    })


if __name__ == "__main__":
    # Arranque en caliente: el modelo se carga ANTES de aceptar
    # peticiones, para que la primera pregunta no pague la carga
    # perezosa (~26 s medidos en frío). El tiempo de carga se imprime
    # y forma parte del arranque; /api/health no dirá «ok» hasta que
    # el modelo esté listo (ver arriba).
    import time

    if store.ready:
        t0 = time.time()
        store.warmup()
        print(
            "Modelo de embeddings cargado en %.1f s; "
            "la primera pregunta no pagará la carga." % (time.time() - t0),
            flush=True,
        )
    app.run(host="127.0.0.1", port=5057)
