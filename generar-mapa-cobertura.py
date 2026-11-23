"""Genera el fragmento HTML del mapa de cobertura para templates/index.html.

Uso (desde la raíz del repo, con el índice del ciclo en curso):

    python generar-mapa-cobertura.py > /tmp/cobertura.html

Lee data/chunks.json y emite la sección <details id="cobertura"> con
los 28 documentos agrupados (CenteIA, aprendido, corpus-extra), cada
uno con su número de fragmentos, su número de secciones, la lista de
secciones y su pregunta medida clicable (canario del 16 nov 2026 o
pregunta de la batería, con la similitud medida y la posición).

Las preguntas y sus similitudes son DATOS, no texto inventado: cada
una está medida contra la API real y documentada en improvement-log.md
(entrada «Mapa de cobertura», 16 nov 2026) o en la batería de los
ciclos 2-14. Si una pregunta cambia o un documento nuevo entra en el
corpus, se actualiza CANARIOS aquí y se regenera: nunca se edita el
fragmento a mano dentro de la plantilla.

El script comprueba que cada documento de chunks.json tiene su
pregunta y que no sobra ninguna: si el corpus cambia sin actualizar
esta tabla, falla en voz alta en vez de generar un mapa a medias.
"""

import collections
import html
import json
import sys

# pregunta, similitud medida, posición medida, origen de la medida.
# Similitudes con coma decimal, como en el registro y en el README.
CANARIOS = {
    # CenteIA (5)
    "centeia-materiales/analisis.md": (
        "¿Cuáles son las 25 tareas que la IA ya puede hacer por ti según los materiales de CenteIA?",
        "0,694", "1.ª (3 de 4 fuentes)", "canario 16 nov 2026"),
    "centeia-materiales/automatizaciones-analisis.md": (
        "¿Qué automatizaciones presenta la guía de CenteIA y cómo se venden?",
        "0,699", "las 4 fuentes", "batería, Ciclo 5"),
    "centeia-materiales/guia-diseno-web-centeia-evaluacion.md": (
        "¿Qué herramientas recomienda la guía de diseño web de CenteIA para diseñar con Claude Code?",
        "0,696", "1.ª (las 4 fuentes)", "canario 16 nov 2026"),
    "centeia-materiales/regalo-1-trabajo-delegado-evaluacion.md": (
        "¿Cuál es la regla de oro anti-invención del primer trabajo delegado a la IA?",
        "0,580", "1.ª (3 de 4 fuentes)", "canario 16 nov 2026"),
    "centeia-materiales/sintesis-videos-2026-11-04.md": (
        "¿Qué es el segundo yo 24/7 de CenteIA?",
        "0,545", "1.ª (3 de 4 fuentes)", "batería, Ciclo 13"),
    # mundo-dirsi/aprendido (8)
    "mundo-dirsi/aprendido/agentes-e-ia.md": (
        "¿Qué es un agente de código en la práctica?",
        "0,821", "1.ª (3 de 4 fuentes)", "canario 16 nov 2026"),
    "mundo-dirsi/aprendido/blockchain-web3.md": (
        "¿Qué es blockchain y la web3?",
        "0,799", "las 4 fuentes", "batería, Ciclo 14"),
    "mundo-dirsi/aprendido/comparacion-prompts-45-vs-90.md": (
        "¿Los 45 prompts son un subconjunto de los 90 prompts?",
        "0,669", "las 4 fuentes", "batería, Ciclo 5"),
    "mundo-dirsi/aprendido/desarrollo-web.md": (
        "¿Qué principio de desarrollo web dice que cada app debe tener una sola especialización?",
        "0,665", "1.ª (3 de 4 fuentes)", "canario 16 nov 2026"),
    "mundo-dirsi/aprendido/despliegue.md": (
        "¿Cómo se despliega una aplicación?",
        "0,502", "posiciones 1–3", "batería, Ciclo 2"),
    "mundo-dirsi/aprendido/herramientas-y-conexiones.md": (
        "¿Por qué el conector de GitHub no crea repositorios?",
        "0,713", "1.ª (3 de 4 fuentes)", "canario 16 nov 2026"),
    "mundo-dirsi/aprendido/ingenieria-inversa.md": (
        "¿Qué es REA y para qué sirve?",
        "0,526", "1.ª", "batería, Ciclo 14"),
    "mundo-dirsi/aprendido/portafolio-y-empleo.md": (
        "¿Dónde está publicado el portafolio de Antonio?",
        "0,513", "fuentes 1, 2 y 4", "batería, Ciclo 13"),
    # corpus-extra (15)
    "rag-demo/corpus-extra/anti-phishing-improvement-log.md": (
        "¿Cuántas comprobaciones tiene el test de anti-phishing?",
        "0,597", "las 4 fuentes", "batería, Ciclo 9"),
    "rag-demo/corpus-extra/api-segundo-yo-improvement-log.md": (
        "¿Qué validación real de payloads se añadió a la API del segundo yo?",
        "0,569", "1.ª (3 de 4 fuentes)", "canario 16 nov 2026"),
    "rag-demo/corpus-extra/barberia-improvement-log.md": (
        "¿Qué verifica el script verify-catalog de la barbería?",
        "0,581", "las 4 fuentes", "batería, Ciclo 11"),
    "rag-demo/corpus-extra/biblioteca-prompts-improvement-log.md": (
        "¿Qué pasó con los 15 roles anunciados en la biblioteca de prompts si solo 8 tenían prompt?",
        "0,637", "1.ª (las 4 fuentes)", "canario 16 nov 2026"),
    "rag-demo/corpus-extra/block-explorer-improvement-log.md": (
        "¿Qué cambió toReversed en block-explorer?",
        "0,538", "las 4 fuentes", "batería, Ciclo 12"),
    "rag-demo/corpus-extra/contract-play-improvement-log.md": (
        "¿Qué cambió en el simulador de contratos de contract-play para alinearse con los fragmentos?",
        "0,614", "1.ª (las 4 fuentes)", "canario 16 nov 2026"),
    "rag-demo/corpus-extra/dao-vote-improvement-log.md": (
        "¿Por qué los filtros Activas y Cerradas de DAO Vote devolvían siempre 0?",
        "0,693", "1.ª (las 4 fuentes)", "canario 16 nov 2026"),
    "rag-demo/corpus-extra/gas-calc-improvement-log.md": (
        "¿Qué corrigió gas-calc sobre el wei exacto y EIP-1559?",
        "0,710", "1.ª (las 4 fuentes)", "canario 16 nov 2026"),
    "rag-demo/corpus-extra/hash-lab-improvement-log.md": (
        "¿Qué es la validez transitiva en hash-lab y qué cambió en Restaurar?",
        "0,707", "1.ª (las 4 fuentes)", "canario 16 nov 2026"),
    "rag-demo/corpus-extra/mundo-vida-ia-improvement-log.md": (
        "¿Qué se arregló en mundo-vida-ia para las consolas ASCII?",
        "0,545", "las 4 fuentes", "batería, Ciclo 13"),
    "rag-demo/corpus-extra/nft-studio-improvement-log.md": (
        "¿A qué versiones se alineó nft-studio en el Ciclo 6?",
        "0,570", "las 4 fuentes", "batería, Ciclo 6"),
    "rag-demo/corpus-extra/segundo-yo-improvement-log.md": (
        "¿Qué decisión visual fuerte se tomó en la app segundo-yo con la ficha como tarjeta de identidad?",
        "0,706", "1.ª (las 4 fuentes)", "canario 16 nov 2026"),
    "rag-demo/corpus-extra/token-explorer-improvement-log.md": (
        "¿Por qué se renombró un token en token-explorer?",
        "0,538", "1.ª (las 4 fuentes)", "canario 16 nov 2026"),
    "rag-demo/corpus-extra/tx-builder-improvement-log.md": (
        "¿Qué suelo de tests se añadió a tx-builder en el Ciclo 10?",
        "0,674", "las 4 fuentes", "batería, Ciclo 10"),
    "rag-demo/corpus-extra/wallet-sim-improvement-log.md": (
        "¿Por qué la cartera nueva de wallet-sim empieza a 0 y qué hace el faucet?",
        "0,512", "1.ª (las 4 fuentes)", "canario 16 nov 2026"),
}

GRUPOS = [
    ("centeia-materiales/",
     "CenteIA — materiales del curso «Tu segundo yo 24/7»"),
    ("mundo-dirsi/aprendido/",
     "Aprendido — notas de Antonio en mundo-dirsi"),
    ("rag-demo/corpus-extra/",
     "Registros de mejora — qué se arregló en cada app (Fase 2)"),
]


def nombre_corto(archivo):
    base = archivo.rsplit("/", 1)[-1]
    if base.endswith("-improvement-log.md"):
        base = base[: -len("-improvement-log.md")]
    elif base.endswith(".md"):
        base = base[:-3]
    return base


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else "data/chunks.json"
    with open(ruta, encoding="utf-8") as f:
        chunks = json.load(f)
    por_archivo = collections.Counter(c["archivo"] for c in chunks)
    secciones = collections.defaultdict(list)
    for c in chunks:
        if c["seccion"] not in secciones[c["archivo"]]:
            secciones[c["archivo"]].append(c["seccion"])
    # El mapa no admite huecos: cada documento del índice necesita su
    # pregunta medida, y cada pregunta necesita su documento.
    sin_pregunta = sorted(set(por_archivo) - set(CANARIOS))
    sin_documento = sorted(set(CANARIOS) - set(por_archivo))
    if sin_pregunta or sin_documento:
        for a in sin_pregunta:
            print("SIN PREGUNTA MEDIDA: %s" % a, file=sys.stderr)
        for a in sin_documento:
            print("SIN DOCUMENTO EN EL ÍNDICE: %s" % a, file=sys.stderr)
        sys.exit(1)
    total_docs = len(por_archivo)
    total_frags = len(chunks)
    total_secs = sum(len(v) for v in secciones.values())
    out = []
    out.append('<details class="tarjeta" id="cobertura">')
    out.append(
        "  <summary><span id=\"cobertura-resumen\">Qué puedo responder — "
        "mapa de cobertura: %d documentos · %d fragmentos · %d secciones"
        "</span></summary>"
        % (total_docs, total_frags, total_secs))
    out.append(
        '  <p class="cobertura-intro">Cada documento tiene una pregunta '
        "medida que lo recupera con confianza alta (similitud ≥ 0,50): "
        "ningún documento está muerto. Pulsa «Probar» para lanzar la "
        "pregunta tal cual se midió. Las similitudes son las medidas en "
        "la batería (Ciclos 2–14) y en el mapa de cobertura del 16 nov "
        "2026; los controles re-medidos ese día salieron idénticos.</p>")
    out.append(
        '  <p class="cobertura-aviso" id="cobertura-aviso" hidden></p>')
    for prefijo, titulo in GRUPOS:
        docs = sorted(a for a in por_archivo if a.startswith(prefijo))
        frags = sum(por_archivo[a] for a in docs)
        out.append("  <h3>%s (%d documentos · %d fragmentos)</h3>"
                   % (html.escape(titulo), len(docs), frags))
        out.append('  <table class="cobertura-tabla">')
        out.append("    <thead><tr><th>Documento</th><th>Frag.</th>"
                   "<th>Secciones</th><th>Pregunta medida</th></tr></thead>")
        out.append("    <tbody>")
        for a in docs:
            pregunta, sim, pos, origen = CANARIOS[a]
            secs = secciones[a]
            items = "".join(
                "<li>%s</li>" % html.escape(s) for s in secs)
            out.append("      <tr>")
            out.append(
                '        <td><span class="cobertura-doc">%s</span>'
                '<br><span class="cobertura-ruta">%s</span></td>'
                % (html.escape(nombre_corto(a)), html.escape(a)))
            out.append('        <td class="num">%d</td>' % por_archivo[a])
            out.append(
                '        <td><details class="cobertura-secciones">'
                "<summary>%d secciones</summary>"
                '<ul class="cobertura-lista-secciones">%s</ul>'
                "</details></td>" % (len(secs), items))
            out.append(
                '        <td><span class="cobertura-pregunta">%s</span>'
                '<br><span class="cobertura-sim">sim. %s · %s · %s</span>'
                "<br>"
                '<button type="button" class="canario" data-pregunta="%s"'
                ">Probar</button></td>"
                % (html.escape(pregunta), html.escape(sim),
                   html.escape(pos), html.escape(origen),
                   html.escape(pregunta, quote=True)))
            out.append("      </tr>")
        out.append("    </tbody>")
        out.append("  </table>")
    out.append(
        '  <p class="cobertura-nota">Detalle por documento de la ingesta '
        "del Ciclo 14 (16 nov 2026). Si el índice cargado trae otros "
        "conteos, la página lo avisa aquí mismo y muestra los conteos "
        "vivos en el resumen.</p>")
    out.append("</details>")
    fragmento = "\n".join(out) + "\n"
    # La suite exige cero URLs absolutas en la página servida: los
    # títulos de sección vienen del corpus y no deben traer ninguna.
    assert "http://" not in fragmento and "https://" not in fragmento, (
        "el fragmento contiene una URL absoluta (¿un título de sección?)")
    sys.stdout.write(fragmento)


if __name__ == "__main__":
    main()
