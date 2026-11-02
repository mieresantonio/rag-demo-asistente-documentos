# Registro de mejoras — rag-demo

## 2026-11-02 · Fase 2, Ciclo 1 (hallazgos ALTA de la revisión 2026-11-02)

### RAG-A1 — `/preguntar` devolvía 500 HTML con `pregunta` no-string

- **Hallazgo:** `app.py` hacía `(data.get("pregunta") or "").strip()` sin
  validar el tipo: un entero, una lista o un cuerpo que no fuera un
  objeto JSON provocaban una excepción y un 500 en HTML. La validación
  solo cubría vacío/ausente.
- **Cambio:** validación completa antes de tocar el índice, siempre con
  `400` y error en JSON: cuerpo que no es un objeto JSON → 400; campo
  ausente o `null` → 400 «Falta el campo 'pregunta'.»; tipo distinto de
  cadena → 400 «debe ser una cadena de texto»; cadena vacía o solo
  espacios → 400; longitud mayor de 1000 caracteres (`MAX_PREGUNTA`) →
  400 «demasiado larga».
- **Verificaciones:**
  1. `py_compile` limpio en `app.py`, `rag_core.py` e `ingest.py`.
  2. Smoke real con el servidor levantado: `pregunta` entera, ausente,
     vacía, como lista, cuerpo JSON como lista, cuerpo sin JSON y
     pregunta de 1001 caracteres → los 7 casos devolvieron `400` con
     `Content-Type: application/json` y mensaje claro; ningún 500.
     Servidor apagado al terminar (puerto 5057 sin respuesta).
  3. Checklist de detalle: mensajes nuevos con ortografía cuidada
     («vacío», «máximo», «cadena de texto»); el README documenta ahora
     el tipo exigido y el límite de 1000 caracteres; sin regresiones en
     `/api/health` ni en las preguntas válidas.

### RAG-A2 — El umbral 0,20 rellenaba respuestas fuera de tema

- **Hallazgo:** el README prometía que una pregunta fuera de tema no
  rellena («hay umbral de similitud, y por debajo de él la API lo dice»),
  pero con el umbral en 0,20 el texto basura puntuaba 0,35–0,41 y se
  devolvían fragmentos sin relación como si fueran la respuesta.
- **Calibración (pruebas reales sobre el corpus, similitud máxima por
  consulta):** dentro de tema 0,44–0,74 (REA 0,636; diseño CenteIA
  0,744; agentes 0,595); fuera de tema y basura 0,41–0,46 (basura
  0,414–0,437; clima 0,457; capital de Francia 0,262); un lorem ipsum
  llegó a 0,522. Conclusión: ningún umbral único separa limpiamente, así
  que se aplica una política de dos niveles y se documenta el límite.
- **Cambio:**
  - `rag_core.py`: constantes `UMBRAL_SIMILITUD = 0.30` (suelo duro de
    fragmentos, antes 0,20) y `UMBRAL_CLARO = 0.50` (puerta de claridad
    sobre la mejor similitud), con el criterio y las mediciones en un
    comentario; nueva función `compose_sin_resultados_claros()` con el
    texto «Sin resultados claros en tus documentos para esa pregunta…»
    y el detalle de la similitud alcanzada.
  - `app.py`: si no hay resultados o la similitud máxima es < 0,50, la
    respuesta es ese texto honesto, con `fuentes: []`,
    `confianza: "baja"` y `similitud_maxima`; si es ≥ 0,50, respuesta
    normal con `confianza: "alta"`.
  - `README.md`: diagrama actualizado (0,30 / 0,50) y el apartado
    «Límites honestos» reescrito con la política real, el solape medido
    0,44–0,50 y el contraejemplo del lorem ipsum (0,52).
- **Verificaciones:**
  1. `py_compile` limpio en los 3 módulos (repetido tras el ajuste
     ortográfico de decimales con coma en los textos nuevos).
  2. Smoke real con el servidor levantado: pregunta válida conocida
     («¿Qué es REA y para qué sirve?») → 200, `confianza: "alta"`,
     similitud máxima 0,636 y 4 fuentes con la fuente correcta citada;
     «¿Cuál es la capital de Francia?» → `confianza: "baja"`, sin
     fuentes y texto «sin resultados claros»; texto basura
     («asdf qwer zxcv jkl», 0,407) → lo mismo; el antiguo falso positivo
     del clima (0,457) → también «baja», sin rellenar. Servidor apagado
     al terminar (puerto 5057 sin respuesta, comprobado).
  3. Checklist de detalle: ortografía y decimales con coma («0,407»,
     «0,50») en los textos nuevos; README y comportamiento coinciden;
     la respuesta válida de REA conserva sus 4 fragmentos (el suelo
     0,30 no recorta el contexto útil) y no se detectaron regresiones.
