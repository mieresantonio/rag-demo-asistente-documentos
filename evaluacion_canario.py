#!/usr/bin/env python3
"""Evaluación canario del RAG demo: 15 preguntas fijas con respuestas esperadas.

Convierte en comprobaciones programáticas las preguntas medidas de la
batería y del mapa de cobertura (registro de mejoras, 2026-11-16): tras
cada cambio de corpus o de código, el canario verifica que la demo
sigue diciendo «no lo sé» cuando no sabe (preguntas tipo no-sabe:
confianza baja, cero fuentes, similitud bajo la puerta de claridad)
y citando bien cuando sabe (tipo sabe: confianza alta, el documento
esperado en 1.ª posición, similitud dentro de su banda, y citas [n]
coherentes con las fuentes devueltas).

Las preguntas y sus valores medidos viven en canario.json, junto a
este script: añadir una pregunta es añadir una entrada al JSON, sin
tocar código. Los valores medidos corresponden al corpus del Ciclo 14
(28 documentos / 572 fragmentos); el JSON registra la huella MD5 de
data/chunks.json y data/meta.json de esa ingesta.

Si la huella del corpus cambió (un refresco legítimo), el canario NO
bendice las cifras viejas: sigue comprobando las puertas (confianza,
documento en 1.ª posición, citas), salta las bandas de similitud y
termina con código 2 pidiendo recalibrar. La recalibración es
deliberada y humana: `python evaluacion_canario.py --reporte` mide
los valores nuevos SIN afirmar nada, y quien revisa actualiza
canario.json a mano (con su huella nueva) cuando los valores tienen
sentido. Un canario que se recalibrara solo se tragaría cualquier
regresión.

Códigos de salida:
    0  todo pasa (87 comprobaciones en modo normal)
    1  REGRESIÓN: alguna puerta falla (confianza, documento, citas,
       o una pregunta no-sabe que empieza a responderse)
    2  ATENCIÓN: sin índice, el servidor no arranca, o el corpus
       cambió y hay que recalibrar (las bandas se saltaron)

Uso (con el entorno del proyecto):

    python evaluacion_canario.py                 # levanta la app y corre
    python evaluacion_canario.py --reporte       # solo mide, no afirma
    python evaluacion_canario.py --solo despliegue
    python evaluacion_canario.py --base-url http://127.0.0.1:5057

Solo usa la biblioteca estándar para hablar con la API; el servidor se
lanza con el intérprete indicado por --python (por defecto, el mismo
que corre este script).
"""
import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_PATH = os.path.join(DATA_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(DATA_DIR, "chunks.json")
META_PATH = os.path.join(DATA_DIR, "meta.json")
CANARIO_PATH = os.path.join(BASE_DIR, "canario.json")

resultados = []  # (id, nombre, ok, detalle)
avisos = []      # advertencias que no fallan la corrida


def registrar(pregunta_id, nombre, ok, detalle=""):
    resultados.append((pregunta_id, nombre, bool(ok), detalle))
    marca = "OK  " if ok else "FALLO"
    linea = f"[{marca}] ({pregunta_id}) {nombre}"
    if detalle:
        linea += f" — {detalle}"
    print(linea, flush=True)
    return ok


def comprobar(pregunta_id, nombre, condicion, detalle=""):
    return registrar(pregunta_id, nombre, condicion, detalle)


def avisar(texto):
    avisos.append(texto)
    print(f"[AVISO] {texto}", flush=True)


def md5_de(ruta):
    h = hashlib.md5()
    with open(ruta, "rb") as fh:
        for bloque in iter(lambda: fh.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


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


# ---------------------------------------------------------------- servidor
def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def levantar(python, timeout_s=180):
    """Levanta app.py en un puerto libre; espera a que health responda."""
    puerto = puerto_libre()
    base = f"http://127.0.0.1:{puerto}"
    env = dict(os.environ)
    env["RAG_DEMO_HOST"] = "127.0.0.1"
    env["RAG_DEMO_PORT"] = str(puerto)
    log = tempfile.NamedTemporaryFile(
        mode="w", prefix="rag-canario-", suffix=".log", delete=False)
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


# ---------------------------------------------------------------- comprobaciones
def comprobar_citas(pregunta_id, respuesta, fuentes):
    """Las citas [n] del texto deben ser exactamente las fuentes [1..n].

    compose_answer escribe cada fragmento como una línea «[n] ...»
    (el extracto no tiene saltos de línea: se colapsan a espacios),
    así que las líneas que empiezan por [n] son las citas y deben
    coincidir una a una con la lista de fuentes.
    """
    if not isinstance(respuesta, str):
        return comprobar(pregunta_id, "citas [n] coherentes con las fuentes",
                         False, "la respuesta no es texto")
    numeros = sorted(int(n) for n in re.findall(
        r"^\[(\d+)\] ", respuesta, flags=re.MULTILINE))
    esperado = list(range(1, len(fuentes) + 1))
    return comprobar(pregunta_id, "citas [n] coherentes con las fuentes",
                     numeros == esperado,
                     f"citas={numeros}, fuentes={len(fuentes)}")


def comprobar_campos_fuente(pregunta_id, fuentes):
    """Cada fuente trae archivo, sección, similitud y relevancia."""
    ok = True
    for f in fuentes:
        if not isinstance(f, dict):
            ok = False
            break
        if not f.get("archivo") or not f.get("seccion"):
            ok = False
            break
        if not isinstance(f.get("similitud"), (int, float)):
            ok = False
            break
        if not isinstance(f.get("relevancia"), (int, float)):
            ok = False
            break
    return comprobar(pregunta_id,
                     "fuentes con archivo, sección, similitud y relevancia",
                     ok and len(fuentes) > 0,
                     f"fuentes={len(fuentes)}")


def evaluar_sabe(base, caso, umbral_claro, tolerancia, recalibrar):
    """Una pregunta que la demo DEBE responder con confianza alta."""
    pid = caso["id"]
    estado, _j, r, crudo = post_json(base, {"pregunta": caso["pregunta"]})
    if not isinstance(r, dict):
        r = {}
    fuentes = r.get("fuentes") or []
    comprobar(pid, "→ 200 en JSON", estado == 200,
              f"HTTP {estado}, cuerpo: {crudo[:160]}")
    comprobar(pid, "→ confianza alta", r.get("confianza") == "alta",
              f"confianza={r.get('confianza')!r}")
    top = fuentes[0].get("archivo", "") if fuentes else ""
    comprobar(pid, f"→ top-1 es {caso['documento']}",
              top == caso["documento"], f"top={top!r}")
    sim = r.get("similitud_maxima")
    medida = caso["similitud_medida"]
    if recalibrar:
        # El corpus cambió: la cifra medida es historia, no un valor
        # contra el que fallar. Se registra lo medido y se sigue.
        print(f"[saltada] ({pid}) similitud en banda: medida ahora "
              f"{sim!r}, registrada {medida} (corpus cambiado)",
              flush=True)
    else:
        minimo = max(umbral_claro, medida - tolerancia)
        comprobar(pid,
                  f"→ similitud en banda (medida {medida}, "
                  f"mínimo {minimo:.3f})",
                  isinstance(sim, (int, float)) and sim >= minimo,
                  f"similitud_maxima={sim!r}")
    comprobar_citas(pid, r.get("respuesta"), fuentes)
    comprobar_campos_fuente(pid, fuentes)
    return {
        "id": pid, "pregunta": caso["pregunta"], "tipo": "sabe",
        "confianza": r.get("confianza"),
        "similitud_maxima": sim,
        "similitud_medida": medida,
        "top": top,
        "n_fuentes": len(fuentes),
    }


def evaluar_no_sabe(base, caso, umbral_claro):
    """Una pregunta que la demo NO debe responder: «no lo sé» honesto."""
    pid = caso["id"]
    estado, _j, r, crudo = post_json(base, {"pregunta": caso["pregunta"]})
    if not isinstance(r, dict):
        r = {}
    sim = r.get("similitud_maxima")
    comprobar(pid, "→ 200 en JSON", estado == 200,
              f"HTTP {estado}, cuerpo: {crudo[:160]}")
    comprobar(pid, "→ confianza baja", r.get("confianza") == "baja",
              f"confianza={r.get('confianza')!r}")
    comprobar(pid, "→ 0 fuentes", r.get("fuentes") == [],
              f"fuentes={r.get('fuentes')!r}")
    comprobar(pid, f"→ similitud bajo la puerta ({umbral_claro})",
              sim is None or (isinstance(sim, (int, float))
                              and sim < umbral_claro),
              f"similitud_maxima={sim!r}")
    # Aviso temprano (no fallo): si la similitud sube hacia la puerta,
    # la próxima vez puede colarse como respuesta. La subida de 0,05
    # es la señal, no la condena.
    medida = caso["similitud_medida"]
    if (isinstance(sim, (int, float)) and isinstance(medida, (int, float))
            and sim > medida + 0.05):
        avisar(f"({pid}) la similitud sube hacia la puerta: medida "
               f"{medida}, ahora {sim} (puerta {umbral_claro})")
    return {
        "id": pid, "pregunta": caso["pregunta"], "tipo": "no-sabe",
        "confianza": r.get("confianza"),
        "similitud_maxima": sim,
        "similitud_medida": medida,
        "top": None,
        "n_fuentes": len(r.get("fuentes") or []),
    }


def comprobar_health(base):
    """La app responde ok y sus conteos son los de meta.json."""
    estado, es_json, h, crudo = peticion(base, "GET", "/api/health")
    comprobar("health", "health responde 200 en JSON",
              estado == 200 and es_json and isinstance(h, dict),
              f"HTTP {estado}, cuerpo: {crudo[:200]}")
    if not isinstance(h, dict):
        h = {}
    comprobar("health", "health estado «ok»",
              h.get("estado") == "ok", f"estado={h.get('estado')!r}")
    with open(META_PATH, encoding="utf-8") as fh:
        meta = json.load(fh)
    comprobar("health", "health %s documentos / %s fragmentos (meta.json)"
              % (meta.get("documentos"), meta.get("fragmentos")),
              h.get("documentos") == meta.get("documentos")
              and h.get("fragmentos") == meta.get("fragmentos"),
              f"documentos={h.get('documentos')!r}, "
              f"fragmentos={h.get('fragmentos')!r}")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--python", default=sys.executable,
                    help="intérprete con las dependencias del proyecto")
    ap.add_argument("--base-url", default=None,
                    help="usar un servidor ya levantado en vez de "
                         "arrancar uno propio")
    ap.add_argument("--solo", default=None, metavar="ID",
                    help="correr solo la pregunta con este id")
    ap.add_argument("--reporte", action="store_true",
                    help="solo mide los valores actuales y los imprime, "
                         "sin comprobar nada (instrumento de recalibración)")
    args = ap.parse_args()

    if not os.path.isfile(CANARIO_PATH):
        print(f"ERROR: no existe {CANARIO_PATH}")
        return 2
    with open(CANARIO_PATH, encoding="utf-8") as fh:
        canario = json.load(fh)
    casos = canario["preguntas"]
    if args.solo:
        casos = [c for c in casos if c["id"] == args.solo]
        if not casos:
            print(f"ERROR: no hay ninguna pregunta canario con id "
                  f"{args.solo!r}")
            return 2
    umbral = canario.get("umbral_claro", 0.50)
    tolerancia = canario.get("tolerancia_bajada", 0.03)

    if not os.path.exists(INDEX_PATH):
        print("ERROR: data/index.faiss no existe; sin índice no hay "
              "canario que correr. Ejecuta primero: python ingest.py "
              "(corpus completo) o python rebuild_index.py (desde "
              "data/chunks.json versionado).")
        return 2

    # Huella del corpus: ¿siguen vigentes los valores medidos?
    huella = canario.get("corpus", {})
    md5_chunks = md5_de(CHUNKS_PATH) if os.path.exists(CHUNKS_PATH) else None
    md5_meta = md5_de(META_PATH) if os.path.exists(META_PATH) else None
    recalibrar = (md5_chunks != huella.get("md5_chunks_json")
                  or md5_meta != huella.get("md5_meta_json"))
    print(f"Evaluación canario — corpus: {huella.get('documentos')} "
          f"documentos / {huella.get('fragmentos')} fragmentos "
          f"(medido {huella.get('medido_en')})")
    print(f"Huella actual: chunks.json {md5_chunks}, "
          f"meta.json {md5_meta}")
    if recalibrar:
        print("El corpus CAMBIÓ desde la medición registrada: las bandas "
              "de similitud se saltan y esta corrida termina pidiendo "
              "recalibrar (código 2). Las puertas (confianza, documento "
              "en 1.ª, citas) se comprueban igual.", flush=True)

    proc = None
    try:
        if args.base_url:
            base = args.base_url.rstrip("/")
            print(f"… usando el servidor ya levantado en {base}",
                  flush=True)
        else:
            proc, base, arranque, log = levantar(args.python)
            print(f"… servidor en {base} tras {arranque:.1f} s "
                  f"(log: {log})", flush=True)
        if not args.reporte:
            comprobar_health(base)
        medidos = []
        for caso in casos:
            if args.reporte:
                # Modo medida: pregunta y anota, sin afirmar nada.
                estado, _j, r, _t = post_json(
                    base, {"pregunta": caso["pregunta"]})
                if not isinstance(r, dict):
                    r = {}
                fuentes = r.get("fuentes") or []
                medidos.append({
                    "id": caso["id"],
                    "pregunta": caso["pregunta"],
                    "tipo": caso["tipo"],
                    "confianza": r.get("confianza"),
                    "similitud_maxima": r.get("similitud_maxima"),
                    "top": (fuentes[0].get("archivo")
                            if fuentes else None),
                    "n_fuentes": len(fuentes),
                })
            elif caso["tipo"] == "sabe":
                medidos.append(evaluar_sabe(
                    base, caso, umbral, tolerancia, recalibrar))
            else:
                medidos.append(evaluar_no_sabe(base, caso, umbral))
    except Exception as exc:
        print(f"ERROR: no se pudo correr el canario: {exc!r}")
        return 2
    finally:
        detener(proc)

    if args.reporte:
        print()
        print("REPORTE (medido ahora, sin comprobar nada):")
        print(f"{'id':<16} {'tipo':<8} {'confianza':<9} "
              f"{'sim_max':<8} {'top':<50} {'n'}")
        for m in medidos:
            sim = m["similitud_maxima"]
            sim_txt = "null" if sim is None else f"{sim:.3f}"
            print(f"{m['id']:<16} {m['tipo']:<8} "
                  f"{str(m['confianza']):<9} {sim_txt:<8} "
                  f"{str(m['top'])[:50]:<50} {m['n_fuentes']}")
        print()
        print("Para recalibrar canario.json, revisa estos valores a mano "
              "(¿tienen sentido con el corpus nuevo?) y actualiza "
              "similitud_medida, documento (top-1) y la huella "
              "md5_chunks_json / md5_meta_json. No se recalibran solos.")
        return 0

    total = len(resultados)
    fallidas = [r for r in resultados if not r[2]]
    print()
    print(f"CANARIO: {total - len(fallidas)}/{total} comprobaciones "
          f"superadas; {len(fallidas)} falladas; {len(avisos)} avisos.")
    for pid, nombre, _ok, detalle in fallidas:
        print(f"  FALLO ({pid}) {nombre} — {detalle}")
    if recalibrar:
        print("El corpus cambió desde la medición registrada: ejecuta "
              "`python evaluacion_canario.py --reporte`, revisa los "
              "valores y actualiza canario.json (valores + huella).")
        return 1 if fallidas else 2
    return 1 if fallidas else 0


if __name__ == "__main__":
    sys.exit(main())
