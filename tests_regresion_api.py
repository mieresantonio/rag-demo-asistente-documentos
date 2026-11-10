#!/usr/bin/env python3
"""Suite de regresión automática del contrato de la API del RAG demo.

Convierte en comprobaciones programáticas la batería manual de las
rondas 2-3 de la operación de mejora (2026-11-09): fases sin índice y
con índice, errores en JSON, techo de cuerpo de 32 KB, valores
patológicos de `k` (incluido Infinity) y la puerta de honestidad por
umbral. Si alguna respuesta se desvía del contrato medido, la suite
falla en voz alta con la respuesta real: no maquilla.

Uso (con el entorno del proyecto; en el workspace del autor la semilla
vive en ~/workspace/rag-demo y su .venv es el entorno de referencia):

    ~/workspace/rag-demo/.venv/bin/python tests_regresion_api.py
    ~/workspace/rag-demo/.venv/bin/python tests_regresion_api.py --modo sin
    ~/workspace/rag-demo/.venv/bin/python tests_regresion_api.py --modo con

Modos:
    sin   Mueve data/index.faiss a un respaldo temporal, levanta la app
          y comprueba el estado honesto sin índice (health 0/0 y
          «sin_indice», /preguntar 503). Restaura el índice al terminar.
    con   Levanta la app con el índice presente (27 documentos /
          527 fragmentos) y comprueba la ruta feliz y los errores.
    ambos (por defecto) Ejecuta «sin» y después «con».

La suite levanta la app en un puerto libre con RAG_DEMO_PORT, la
detiene al final de cada modo y deja data/ exactamente como estaba
(verifica los MD5 de data/ antes y después). Código de salida 0 si
todas las comprobaciones pasan, 1 si alguna falla.

Solo usa la biblioteca estándar para hablar con la API; el servidor se
lanza con el intérprete indicado por --python o la variable
RAG_TEST_PYTHON (por defecto, el .venv de la semilla del workspace).
"""
import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(BASE_DIR) == "tests":
    BASE_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_PATH = os.path.join(DATA_DIR, "index.faiss")

PYTHON_POR_DEFECTO = os.environ.get(
    "RAG_TEST_PYTHON",
    os.path.expanduser("~/workspace/rag-demo/.venv/bin/python"),
)

PREGUNTA_VALIDA = "¿Qué es blockchain y la web3?"
# Medida repetida en las rondas 2-3 y en la verificación de la semilla:
# confianza alta, similitud máxima 0,799 y 4 fuentes de blockchain-web3.md.
SIMILITUD_VALIDA_ESPERADA = 0.799
PREGUNTA_BAJO_UMBRAL = "¿Qué es el segundo yo 24/7 de CenteIA?"
UMBRAL_CLARO = 0.50  # rag_core.UMBRAL_CLARO

resultados = []  # (modo, nombre, ok, detalle)


def registrar(modo, nombre, ok, detalle=""):
    resultados.append((modo, nombre, bool(ok), detalle))
    marca = "OK  " if ok else "FALLO"
    linea = f"[{marca}] ({modo}) {nombre}"
    if detalle:
        linea += f" — {detalle}"
    print(linea, flush=True)
    return ok


def comprobar(modo, nombre, condicion, detalle=""):
    return registrar(modo, nombre, condicion, detalle)


# ---------------------------------------------------------------- HTTP
def peticion(base, metodo, ruta, cuerpo_crudo=None, content_type=None):
    """Devuelve (estado, es_json, cuerpo_parseado_o_None, texto_crudo)."""
    req = urllib.request.Request(base + ruta, method=metodo)
    datos = None
    if cuerpo_crudo is not None:
        datos = cuerpo_crudo.encode("utf-8") if isinstance(
            cuerpo_crudo, str) else cuerpo_crudo
        if content_type:
            req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, data=datos, timeout=60) as resp:
            texto = resp.read().decode("utf-8", errors="replace")
            estado = resp.status
            ctype = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        texto = e.read().decode("utf-8", errors="replace")
        estado = e.code
        ctype = e.headers.get("Content-Type", "") if e.headers else ""
    try:
        parsed = json.loads(texto)
    except (ValueError, TypeError):
        parsed = None
    return estado, "application/json" in (ctype or ""), parsed, texto


def post_json(base, obj):
    return peticion(base, "POST", "/preguntar",
                    json.dumps(obj, ensure_ascii=False), "application/json")


def post_crudo(base, texto, content_type="application/json"):
    return peticion(base, "POST", "/preguntar", texto, content_type)


# ---------------------------------------------------------------- servidor
def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def levantar(python, modo, timeout_s=180):
    """Levanta app.py en un puerto libre; espera a que health responda."""
    puerto = puerto_libre()
    base = f"http://127.0.0.1:{puerto}"
    env = dict(os.environ)
    env["RAG_DEMO_HOST"] = "127.0.0.1"
    env["RAG_DEMO_PORT"] = str(puerto)
    log = tempfile.NamedTemporaryFile(
        mode="w", prefix=f"rag-regresion-{modo}-", suffix=".log",
        delete=False)
    proc = subprocess.Popen(
        [python, "app.py"], cwd=BASE_DIR, env=env,
        stdout=log, stderr=subprocess.STDOUT)
    inicio = time.time()
    try:
        while time.time() - inicio < timeout_s:
            if proc.poll() is not None:
                raise RuntimeError(
                    f"app.py terminó antes de escuchar (código "
                    f"{proc.returncode}); log: {log.name}")
            try:
                estado, _j, cuerpo, _t = peticion(base, "GET", "/api/health")
                if estado == 200 and isinstance(cuerpo, dict):
                    # Con índice, «ok» exige el warmup ya hecho: app.py
                    # carga el modelo ANTES de app.run, así que el
                    # primer health 200 ya es el estado definitivo.
                    return proc, base, time.time() - inicio, log.name
            except Exception:
                pass
            time.sleep(0.5)
        raise RuntimeError(
            f"la app no respondió en {timeout_s} s; log: {log.name}")
    except Exception:
        detener(proc)
        raise


def detener(proc):
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


def md5_de(ruta):
    h = hashlib.md5()
    with open(ruta, "rb") as fh:
        for bloque in iter(lambda: fh.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def foto_data():
    foto = {}
    for nombre in sorted(os.listdir(DATA_DIR)):
        ruta = os.path.join(DATA_DIR, nombre)
        if os.path.isfile(ruta):
            foto[nombre] = md5_de(ruta)
    return foto


# ---------------------------------------------------------------- modo SIN
def bateria_sin_indice(base):
    modo = "sin"
    estado, es_json, h, crudo = peticion(base, "GET", "/api/health")
    comprobar(modo, "health responde 200 en JSON",
              estado == 200 and es_json and isinstance(h, dict),
              f"HTTP {estado}, cuerpo: {crudo[:200]}")
    if not isinstance(h, dict):
        h = {}
    comprobar(modo, "health estado «sin_indice»",
              h.get("estado") == "sin_indice", f"estado={h.get('estado')!r}")
    # Rareza conocida y NO corregida: meta.json en disco dice 27/527,
    # pero RagStore solo lo carga si existe index.faiss → 0/0 honesto.
    comprobar(modo, "health 0/0 sin índice (documentos y fragmentos)",
              h.get("documentos") == 0 and h.get("fragmentos") == 0,
              f"documentos={h.get('documentos')!r}, "
              f"fragmentos={h.get('fragmentos')!r}")
    comprobar(modo, "health modelo_cargado false sin índice",
              h.get("modelo_cargado") is False,
              f"modelo_cargado={h.get('modelo_cargado')!r}")

    estado, es_json, cuerpo, crudo = post_json(
        base, {"pregunta": PREGUNTA_VALIDA})
    comprobar(modo, "/preguntar válido sin índice → 503 en JSON",
              estado == 503 and es_json and isinstance(cuerpo, dict)
              and "ingest.py" in str(cuerpo.get("error", "")),
              f"HTTP {estado}, cuerpo: {crudo[:200]}")

    estado, es_json, cuerpo, crudo = post_json(base, {"pregunta": ""})
    comprobar(modo, "/preguntar vacía sin índice → 400 en JSON",
              estado == 400 and es_json and isinstance(cuerpo, dict)
              and "error" in cuerpo,
              f"HTTP {estado}, cuerpo: {crudo[:200]}")

    estado, es_json, cuerpo, crudo = peticion(base, "GET", "/no-existe")
    comprobar(modo, "404 en JSON sin índice",
              estado == 404 and es_json and isinstance(cuerpo, dict)
              and "error" in cuerpo,
              f"HTTP {estado}, cuerpo: {crudo[:200]}")

    estado, es_json, cuerpo, crudo = peticion(base, "GET", "/preguntar")
    comprobar(modo, "405 en JSON sin índice (GET /preguntar)",
              estado == 405 and es_json and isinstance(cuerpo, dict)
              and "error" in cuerpo,
              f"HTTP {estado}, cuerpo: {crudo[:200]}")

    grande = json.dumps({"pregunta": "x" * 40000})
    estado, es_json, cuerpo, crudo = post_crudo(base, grande)
    comprobar(modo, "413 en JSON sin índice (cuerpo ~40 KB > techo 32 KB)",
              estado == 413 and es_json and isinstance(cuerpo, dict)
              and "error" in cuerpo,
              f"HTTP {estado}, cuerpo: {crudo[:200]}")


# ---------------------------------------------------------------- modo CON
def bateria_con_indice(base):
    modo = "con"
    estado, es_json, h, crudo = peticion(base, "GET", "/api/health")
    comprobar(modo, "health responde 200 en JSON",
              estado == 200 and es_json and isinstance(h, dict),
              f"HTTP {estado}, cuerpo: {crudo[:200]}")
    if not isinstance(h, dict):
        h = {}
    comprobar(modo, "health estado «ok» con índice",
              h.get("estado") == "ok", f"estado={h.get('estado')!r}")
    comprobar(modo, "health 27 documentos / 527 fragmentos",
              h.get("documentos") == 27 and h.get("fragmentos") == 527,
              f"documentos={h.get('documentos')!r}, "
              f"fragmentos={h.get('fragmentos')!r}")
    comprobar(modo, "health modelo_cargado true con índice",
              h.get("modelo_cargado") is True,
              f"modelo_cargado={h.get('modelo_cargado')!r}")

    # --- ruta feliz
    estado, es_json, r, crudo = post_json(base, {"pregunta": PREGUNTA_VALIDA})
    if not isinstance(r, dict):
        r = {}
    fuentes = r.get("fuentes") or []
    comprobar(modo, "/preguntar válido → 200 en JSON",
              estado == 200 and es_json,
              f"HTTP {estado}, cuerpo: {crudo[:200]}")
    comprobar(modo, "/preguntar válido → confianza alta",
              r.get("confianza") == "alta",
              f"confianza={r.get('confianza')!r}")
    comprobar(modo, "/preguntar válido → ≥1 fuente (esperadas 4)",
              len(fuentes) >= 1,
              f"fuentes={len(fuentes)}")
    sims_ok = all(
        isinstance(f.get("similitud"), (int, float)) for f in fuentes)
    comprobar(
        modo, "/preguntar válido → similitud registrada "
              f"(máxima {SIMILITUD_VALIDA_ESPERADA}, por fuente)",
        r.get("similitud_maxima") == SIMILITUD_VALIDA_ESPERADA and sims_ok
        and len(fuentes) > 0,
        f"similitud_maxima={r.get('similitud_maxima')!r}, "
        f"similitudes={[f.get('similitud') for f in fuentes]}")

    # --- puerta de honestidad (umbral)
    estado, _j, r2, crudo = post_json(
        base, {"pregunta": PREGUNTA_BAJO_UMBRAL})
    if not isinstance(r2, dict):
        r2 = {}
    sim2 = r2.get("similitud_maxima")
    comprobar(modo, "bajo umbral → 200 con confianza baja",
              estado == 200 and r2.get("confianza") == "baja",
              f"HTTP {estado}, confianza={r2.get('confianza')!r}, "
              f"cuerpo: {crudo[:160]}")
    comprobar(modo, "bajo umbral → 0 fuentes y similitud < 0,50",
              r2.get("fuentes") == [] and isinstance(sim2, (int, float))
              and sim2 < UMBRAL_CLARO,
              f"fuentes={r2.get('fuentes')!r}, similitud_maxima={sim2!r}")

    # --- 400: validación de «pregunta»
    casos_400 = [
        ("400 pregunta vacía", {"pregunta": ""}),
        ("400 pregunta solo espacios", {"pregunta": "   "}),
        ("400 pregunta no-cadena (número)", {"pregunta": 42}),
        ("400 pregunta no-cadena (lista)", {"pregunta": ["blockchain"]}),
        ("400 sin campo pregunta", {"otra": "cosa"}),
        ("400 pregunta null", {"pregunta": None}),
        ("400 pregunta de 1001 caracteres (>1000)",
         {"pregunta": "a" * 1001}),
    ]
    for nombre, obj in casos_400:
        estado, es_json, cuerpo, crudo = post_json(base, obj)
        comprobar(modo, nombre + " en JSON",
                  estado == 400 and es_json and isinstance(cuerpo, dict)
                  and "error" in cuerpo,
                  f"HTTP {estado}, cuerpo: {crudo[:160]}")

    estado, es_json, cuerpo, crudo = post_crudo(base, "{esto no es json")
    comprobar(modo, "400 JSON malformado en JSON",
              estado == 400 and es_json and isinstance(cuerpo, dict)
              and "error" in cuerpo,
              f"HTTP {estado}, cuerpo: {crudo[:160]}")

    estado, es_json, cuerpo, crudo = post_crudo(
        base, "pregunta=blockchain", "text/plain")
    comprobar(modo, "400 cuerpo no JSON en JSON",
              estado == 400 and es_json and isinstance(cuerpo, dict)
              and "error" in cuerpo,
              f"HTTP {estado}, cuerpo: {crudo[:160]}")

    # Límite inclusivo: exactamente 1000 caracteres SÍ pasa la validación.
    estado, _j, r3, crudo = post_json(base, {"pregunta": "a" * 1000})
    comprobar(modo, "pregunta de exactamente 1000 caracteres → 200",
              estado == 200 and isinstance(r3, dict),
              f"HTTP {estado}, cuerpo: {crudo[:160]}")

    # --- 404 / 405 / 413 en JSON
    for ruta in ("/no-existe", "/"):
        estado, es_json, cuerpo, crudo = peticion(base, "GET", ruta)
        comprobar(modo, f"404 en JSON (GET {ruta})",
                  estado == 404 and es_json and isinstance(cuerpo, dict)
                  and "error" in cuerpo,
                  f"HTTP {estado}, cuerpo: {crudo[:160]}")
    estado, es_json, cuerpo, crudo = peticion(base, "GET", "/preguntar")
    comprobar(modo, "405 en JSON (GET /preguntar)",
              estado == 405 and es_json and isinstance(cuerpo, dict)
              and "error" in cuerpo,
              f"HTTP {estado}, cuerpo: {crudo[:160]}")
    estado, es_json, cuerpo, crudo = peticion(
        base, "POST", "/api/health", "{}", "application/json")
    comprobar(modo, "405 en JSON (POST /api/health)",
              estado == 405 and es_json and isinstance(cuerpo, dict)
              and "error" in cuerpo,
              f"HTTP {estado}, cuerpo: {crudo[:160]}")
    grande = json.dumps({"pregunta": "x" * 40000})
    estado, es_json, cuerpo, crudo = post_crudo(base, grande)
    comprobar(modo, "413 en JSON (cuerpo ~40 KB > techo 32 KB)",
              estado == 413 and es_json and isinstance(cuerpo, dict)
              and "error" in cuerpo,
              f"HTTP {estado}, cuerpo: {crudo[:160]}")

    # --- k patológicos: nunca un 500 (regresión de la ronda 2)
    def caso_k(nombre, cuerpo_extra, n_fuentes_esperadas=None):
        if cuerpo_extra is None:
            pet = {"pregunta": PREGUNTA_VALIDA}
            estado, _j, r, crudo = post_json(base, pet)
        else:
            crudo_k = json.dumps(
                {"pregunta": PREGUNTA_VALIDA}, ensure_ascii=False)
            crudo_k = crudo_k[:-1] + ', "k": ' + cuerpo_extra + "}"
            estado, _j, r, crudo = post_crudo(base, crudo_k)
        if not isinstance(r, dict):
            r = {}
        n = len(r.get("fuentes") or [])
        ok = estado == 200 and r.get("confianza") == "alta"
        detalle = (f"HTTP {estado}, fuentes={n}, "
                   f"cuerpo: {crudo[:120]}")
        if n_fuentes_esperadas is not None:
            ok = ok and n == n_fuentes_esperadas
            detalle += f" (esperadas {n_fuentes_esperadas})"
        comprobar(modo, nombre, ok, detalle)

    caso_k("k ausente → 200 con 4 fuentes (defecto)", None, 4)
    caso_k("k=0 → 200 con 1 fuente (clamp mínimo)", "0", 1)
    caso_k("k=99 → 200 con 8 fuentes (clamp máximo)", "99", 8)
    caso_k("k=\"abc\" → 200 con 4 fuentes (defecto)", '"abc"', 4)
    caso_k("k=NaN → 200 sin 500", "NaN", 4)
    caso_k("k=Infinity → 200 sin 500 (regresión ronda 2)", "Infinity", 4)
    caso_k("k=1e999 → 200 sin 500 (infinito por exponente)", "1e999", 4)
    caso_k("k=-Infinity → 200 sin 500", "-Infinity", 4)


# ---------------------------------------------------------------- main
def ejecutar_modo(python, modo):
    respaldo = None
    proc = None
    try:
        if modo == "sin":
            if not os.path.exists(INDEX_PATH):
                registrar(modo, "preparación: index.faiss presente para "
                          "poder apartarlo", False,
                          "data/index.faiss no existe en el clon")
                return
            respaldo = INDEX_PATH + ".bak-regresion"
            if os.path.exists(respaldo):
                os.remove(respaldo)
            os.rename(INDEX_PATH, respaldo)
        elif not os.path.exists(INDEX_PATH):
            registrar(modo, "preparación: index.faiss presente", False,
                      "data/index.faiss no existe en el clon; sin él no "
                      "hay modo «con» que probar")
            return
        proc, base, arranque, log = levantar(python, modo)
        print(f"… servidor ({modo}) en {base} tras {arranque:.1f} s "
              f"(log: {log})", flush=True)
        if modo == "sin":
            bateria_sin_indice(base)
        else:
            bateria_con_indice(base)
    except Exception as exc:  # arranque fallido: un fallo, no un cuelgue
        registrar(modo, "arranque de la app", False, repr(exc))
    finally:
        detener(proc)
        if respaldo is not None and os.path.exists(respaldo):
            if os.path.exists(INDEX_PATH):
                os.remove(INDEX_PATH)
            os.rename(respaldo, INDEX_PATH)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--modo", choices=["sin", "con", "ambos"],
                    default="ambos")
    ap.add_argument("--python", default=PYTHON_POR_DEFECTO,
                    help="intérprete con las dependencias del proyecto")
    args = ap.parse_args()

    if not os.path.isfile(args.python):
        print(f"ERROR: no existe el intérprete {args.python}")
        return 2
    if not os.path.isdir(DATA_DIR):
        print(f"ERROR: no existe {DATA_DIR}")
        return 2

    foto_antes = foto_data()
    print(f"Suite de regresión de la API — clon: {BASE_DIR}")
    print(f"Intérprete del servidor: {args.python}")
    print(f"data/ antes: {foto_antes}")

    modos = ["sin", "con"] if args.modo == "ambos" else [args.modo]
    for modo in modos:
        ejecutar_modo(args.python, modo)

    foto_despues = foto_data()
    comprobar("cierre", "data/ queda como estaba (MD5 idénticos)",
              foto_antes == foto_despues,
              f"antes={foto_antes} después={foto_despues}")

    total = len(resultados)
    fallidas = [r for r in resultados if not r[2]]
    print()
    print(f"RESULTADO: {total - len(fallidas)}/{total} comprobaciones "
          f"superadas; {len(fallidas)} falladas.")
    for modo, nombre, _ok, detalle in fallidas:
        print(f"  FALLO ({modo}) {nombre} — {detalle}")
    return 1 if fallidas else 0


if __name__ == "__main__":
    sys.exit(main())
