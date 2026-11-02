# Registro de mejoras — Entrenador Anti-Phishing

## 2026-11-02 · Fase 2, Ciclo 1

### [A-A1 · ALTA · Contenido] Caso 9 (typosquatting) corregido: estaba invertido

- **Hallazgo:** el caso 9 de `src/data.js` etiquetaba como «oficial» la URL con la «I» mayúscula (`lumenswap-ejempIo.com`) y como sospechosa la correcta, y enseñaba que la mayúscula crea un dominio distinto, lo cual es falso en DNS.
- **Cambio:** invertidas las etiquetas y reescrita la explicación. Contenido nuevo: el sospechoso es `https://lumenswap-ejempIo.com` y el oficial es `https://lumenswap-ejemplo.com`. La explicación nueva aclara que los dominios no distinguen mayúsculas de minúsculas — escribir el mismo dominio con mayúsculas no crea un dominio distinto — y que el truco real es la confusión de caracteres: la sustitución de la letra «l» (ele) por la letra «I» (i mayúscula), visualmente casi idéntica en muchas fuentes; al ser letras distintas, el dominio falso no es el oficial. Se mantiene la marca de ficción: el dominio oficial lleva «-ejemplo» y el falso lo imita visualmente.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 175,98 kB); `node --check` de `data.js` correcto.
- **Verificación 2 (smoke funcional):** leído el caso 9 corregido desde los datos ejecutados en Node: oficial = dominio correcto (`lumenswap-ejemplo.com`), sospechoso = el de la «I», veredicto `phishing` coherente con la explicación; el texto corregido también está en el bundle de `dist/`; grep de `<a`/ `href=` en `src/` = 0 resultados (ningún enlace clicable a sitios reales; las URL siguen como texto plano).
- **Verificación 3 (checklist):** ortografía revisada (acentos y comillas correctos); sin regresiones: siguen siendo 16 casos, 10 phishing y 6 legítimos; el README no describe el caso 9 en detalle, así que sigue siendo veraz sin cambios.

### [A-M2 · alineado con A-A1] Explicación del caso 4 reescrita para no contradecirse

- **Hallazgo:** la explicación afirmaba que «los primeros y últimos caracteres coinciden», pero el inicio era distinto, y el final solo difería en la mayúscula (`2e`/`2E`, el mismo valor hexadecimal).
- **Cambio:** contenido aclarado («tu contacto habitual es 0x7f8b…9C2E») y explicación nueva: el final sí coincide porque en hexadecimal las mayúsculas no cambian el dígito, pero el principio no coincide (solo comparten «0x7f»); por tanto es una dirección diferente y hay que verificar la dirección completa. Primera señal del caso ajustada en la misma línea.
- **Verificación 1 (build):** `npm run build` → exit 0 (misma build anterior).
- **Verificación 2 (smoke funcional):** explicación leída desde los datos ejecutados en Node y contrastada carácter a carácter con la evidencia del propio caso: coherente, sin contradicción.
- **Verificación 3 (checklist):** ortografía revisada; la conclusión pedagógica («verifica la dirección completa») se mantiene; ningún otro caso se tocó.

## 2026-11-02 · Fase 2, Ciclo 2

### [A-M1 · MEDIA · Regla dura/etiquetado] Marca de ficción en los dos dominios registrables que no la llevaban

- **Hallazgo:** caso 1: `novachain-soporte-urgente.net` sin ninguna marca de ficción en el dominio registrable. Caso 15: en `cadenanova-ejemplo.soporte-ayuda24.com` la marca «ejemplo» estaba solo en el subdominio; el dominio registrable, `soporte-ayuda24.com`, no llevaba ninguna y podría parecer un servicio real operativo.
- **Cambio:** aplicada la convención que ya usa la app (sufijo `-ejemplo` en el dominio registrable): caso 1 → `https://novachain-soporte-urgente-ejemplo.net/verificar-cartera` (se conserva intacta la lección: «soporte-urgente» + urgencia falsa); caso 15 → `https://cadenanova-ejemplo.soporte-ayuda24-ejemplo.com/iniciar-sesion`, con `context` y `explanation` actualizados al nuevo dominio literal (la lección del subdominio engañoso no cambia: la marca sigue puesta como subdominio y el dominio real sigue siendo otro). Revisión completa de dominios de los 16 casos: caso 3 (`docs.cadenanova-ejemplo.org` → registrable con marca), caso 9 (`lumenswap-ejemplo.com` y su variante visual `lumenswap-ejempIo.com`, derivada de «ejemplo») — ningún dominio de ejemplo queda sin marca ni parece un servicio real operativo. URLs siempre como texto plano, nunca clicables (sin cambios en ese punto).
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 176,01 kB); `node --check` de `data.js` correcto.
- **Verificación 2 (smoke funcional):** datos ejecutados en Node: **16 casos (10 phishing / 6 legítimos)**, coherentes; grep de los dominios antiguos sin marca en `src/` = **0** (`novachain-soporte-urgente.net` y `soporte-ayuda24.com` como registrable ya no existen); grep de `<a`/`href=` en `src/` = 0 (ningún enlace clicable).
- **Verificación 3 (checklist + contenido del bundle + comparación):** ortografía revisada; contexto y explicación del caso 15 citan el nuevo dominio de forma consistente; sin regresiones en el resto de casos. **Contenido del bundle verificado por cadenas decisivas**: `novachain-soporte-urgente-ejemplo.net` ×1, `soporte-ayuda24-ejemplo.com` ×3 (URL, contexto y explicación), URL completa del caso 15 ×1; dominios antiguos con delimitador = **0** en el bundle; vistas presentes («Señales de alerta», «Legítimo», «Phishing»). **Comparación contra el último build conocido-bueno** (Ciclo 1: 175,98 kB): 176,01 kB, **+0,02 %**, explicado por los pocos caracteres añadidos a los dominios. Sin variables de entorno: build autónomo, sin dependencia no documentada.

## 2026-11-02 · Fase 2, Ciclo 3

### [A-B4 parcial · BAJA · Accesibilidad] Progreso y feedback anunciables + [A-B3] `.gitignore`

- **Hallazgo:** la barra de progreso era un `div` con `aria-label` pero sin `role="progressbar"` ni valores, y el bloque de feedback (correcto/fallaste) no se anunciaba a lectores de pantalla; la app no tenía `.gitignore`.
- **Cambio:** la barra lleva ahora `role="progressbar"` con `aria-valuemin={0}`, `aria-valuemax={deck.length}` y `aria-valuenow` según el avance real; el bloque de feedback lleva `role="status"`. Añadido `.gitignore` estándar (el mismo de nft-studio).
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 176,11 kB).
- **Verificación 2 (smoke):** bundle con `progressbar` ×1 y `aria-valuenow` ×1; las URLs de los casos siguen como texto plano (sin cambios en ese punto: grep de `<a` en `src/` se mantiene en 0, verificado en ciclos anteriores y sin tocar el render de evidencias).
- **Verificación 3 (checklist + comparación):** sin regresiones (A-A1, A-M2 y A-M1 de Ciclos 1–2 intactos; siguen 16 casos). **Comparación contra el último build conocido-bueno** (Ciclo 2: 176,01 kB): 176,11 kB, **+0,06 %**, explicado por los atributos ARIA. Sin variables `VITE_*`: build autónomo.

## 2026-11-02 · Fase 2, Ciclo 4 — Coherencia visual (GR-1): firma de cabecera

- **Gesto:** cinta de precinto de advertencia bajo la cabecera (`.sig-tape`, `aria-hidden`): franja diagonal ámbar/oscuro repetida, el precinto de una zona de riesgo — coherente con su paleta pizarra/ámbar, la más propia del grupo. Solo presentación: 1 div JSX vacío + 1 regla CSS; lógica, datos y textos funcionales intactos.
- **Verificación 1 (build):** `npm run build` → exit 0.
- **Verificación 2 (sirve + smoke):** `dist/` servido en local → index 200 y asset JS 200; el juego (16 casos) no se tocó.
- **Verificación 3 (contenido + comparación):** bundle con `sig-tape` ×2 y cadenas decisivas de Ciclos 1–2 intactas: `novachain-soporte-urgente-ejemplo.net` ×1, `soporte-ayuda24-ejemplo.com` ×3, «Datos de ejemplo» ×2. JS 176.114 → 176.171 B (+57 B) y CSS 7.585 → 7.701 B. `VITE_*` = 0.

## 2026-11-02 · Fase 2, Ciclo 5

### [A-B1 · BAJA · Contenido] Caso 10: los errores citados ya están en la evidencia

- **Hallazgo:** el contexto citaba los errores «actulización» y «cartera bockeada», pero el correo mostrado estaba ortográficamente correcto: la señal «Errores de ortografía» no se podía observar en el material.
- **Cambio:** el `content` del caso 10 ahora contiene literalmente los dos errores citados («Nueva actulización obligatoria de tu wallet. Descarga el instalador adjunto: tu cartera bockeada perderá el acceso…»). Veredicto, explicación y señales no cambian (los errores son intencionados: son la señal).
- **Verificación 2 (smoke):** datos en Node: caso 10 `phishing`, su evidencia contiene «actulización» y «cartera bockeada» (comprobado por programa); siguen 16 casos (10 phishing / 6 legítimos). Bundle: «actulización» ×2 y «cartera bockeada» ×2 (evidencia + contexto que los cita).

### [A-B2 · BAJA · Contenido] Caso 8: el truncado se declara representación en pantalla

- **Hallazgo:** la evidencia muestra la dirección truncada (`0x4b2d…A71f`) pero el veredicto «Legítimo» se apoyaba en «verificada carácter por carácter», sin aclarar que el truncado es solo cómo se muestra.
- **Cambio:** añadida al propio caso la frase «(Aquí la dirección se muestra truncada solo como representación en pantalla; la verificación se hizo sobre la dirección completa, no sobre este resumen.)». Sin cambios de veredicto ni de explicación (que ya decía «se verificó completa»).
- **Verificación:** bundle con «representación en pantalla» ×1; caso 8 sigue `legit` en el smoke de datos.

### [A-B8 · BAJA · Contenido] Casos 6 y 11: evidencia mostrada, no narrada

- **Hallazgo:** en los casos 6 y 11 el `content` era una narración del procedimiento y no la evidencia a juzgar (en el 11 ni siquiera aparecía ninguna URL, pese a su etiqueta «Enlace / URL»).
- **Cambios:** caso 6 — su tipo pasa de `url` a `message` (es un aviso, no un enlace) y el contenido es el aviso literal («Detectamos un inicio de sesión nuevo. Revisa tu actividad en Ajustes → Seguridad.»); el dato «sin ningún enlace» se conserva en el contexto. Caso 11 — el contenido muestra la evidencia: la URL acortada de ejemplo `https://acorta-ejemplo.net/x7k2` (dominio registrable con marca «-ejemplo», en texto plano) y su destino expandido real dentro del ejemplo, `https://docs.cadenanova-ejemplo.org/guias/seguridad` (la misma documentación legítima del caso 3). Veredictos, contextos, explicaciones y señales de ambos casos quedan coherentes sin reescribirlos.
- **Verificación:** smoke de datos: caso 6 `message`/`legit` con el aviso como contenido; caso 11 `url`/`legit` y su contenido contiene una URL. Regla dura intacta: grep de `<a`/`href=` en `src/` = **0** (todo sigue en texto plano).

### [A-B7 · BAJA · UX] «Reiniciar partida» pide confirmación si hay progreso

- **Hallazgo:** el botón estaba visible durante el juego y en el feedback; un toque accidental descartaba puntos, racha y progreso sin aviso.
- **Cambio:** nueva función `restart()` solo para ese botón: si ya hay resultados en la partida, pide confirmación con `window.confirm` («¿Reiniciar la partida? Se perderán tus puntos, tu racha y tu progreso en esta partida.»); sin progreso, reinicia directo. Los botones «Empezar entrenamiento» y «Jugar otra vez» no cambian (ahí no hay partida en curso que perder).
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 176,53 kB). **Verificación 3 (bundle + comparación):** bundle con «Se perderán tus puntos» ×1 y cadenas decisivas de ciclos anteriores intactas (`novachain-soporte-urgente-ejemplo.net` ×1, `soporte-ayuda24-ejemplo.com` ×3). **Comparación contra el último build conocido-bueno** (Ciclo 4: 176.171 B): 176.530 B, **+0,20 %**, explicado por los textos de A-B1/A-B2/A-B8 y la confirmación de A-B7. Sin variables `VITE_*`.

### Pendientes de esta app (con motivo)

- **[A-B4 resto]** Rótulo duplicado en móvil (botón desplegable «Señales de alerta» y el `<h2>` idéntico dentro del panel): la parte anunciable (progressbar/feedback) se cerró en el Ciclo 3; este resto exige decidir qué rótulo se conserva o se oculta a lectores de pantalla, y no es verificable sin render/lector — queda para decisión.
- **[A-B6 · para el frente de READMEs en paralelo]** Este frente NO editó el README. Sigue pendiente de veracidad: `README.md` declara «Mobile-first» pero `src/styles.css` es desktop-first (`.layout` base a dos columnas `1fr 330px`, adaptación con `max-width: 900px/560px`). La adaptación funciona; lo falso es la etiqueta.
- **[A-B5]** Genérico de plantilla: ya tratado por la vía del Ciclo 4 (firma de cabecera); no se fuerza más.
