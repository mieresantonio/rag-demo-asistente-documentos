# Registro de mejoras — DAO Vote

## 2026-11-02 · Fase 2, Ciclo 1

### [D-A1 · ALTA · Lógica] Filtros «Activas»/«Cerradas» corregidos: devolvían siempre 0

- **Hallazgo:** las claves de filtro en `src/App.jsx` eran plurales (`'activas'`, `'cerradas'`) y `filtered` las comparaba contra `p.status`, cuyos valores en `src/data.js` son singulares (`'activa'`, `'cerrada'`). Al pulsar «Activas» o «Cerradas» siempre se mostraba el estado vacío, aunque el README anuncia los filtros como función entregada.
- **Cambio:** claves de filtro igualadas a los valores reales de `status`: `['activa', 'Activas']` y `['cerrada', 'Cerradas']`. Las etiquetas visibles («Todas», «Activas», «Cerradas») no cambian; tampoco se tocaron los datos ni el resto de la lógica.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 166,61 kB); `node --check` de `data.js` correcto.
- **Verificación 2 (smoke funcional):** lógica ejecutada en Node contra los datos reales de la app: filtro `todas` → 6 propuestas; `activa` → 3 (p1, p2, p3); `cerrada` → 3 (p4, p5, p6). Con las claves antiguas, la misma expresión devolvía 0 y 0, lo que reproduce el fallo original. El bundle de `dist/` contiene las claves corregidas (`"activa","Activas"` / `"cerrada","Cerradas"`).
- **Verificación 3 (checklist):** sin regresiones (resumen, votación y creación de propuestas intactos; la creación sigue fijando el filtro en `todas`); ortografía sin cambios, ya correcta; el README vuelve a ser veraz en lo que anuncia de los filtros sin necesidad de editarlo.

## 2026-11-02 · Fase 2, Ciclo 3

### [D-M1 · MEDIA · Diseño] Paleta diferenciada de tx-builder (acotada) + [D-B4] contraste ≥4,5:1

- **Hallazgo:** paleta clónica con tx-builder (`--violet #8b5cf6` idéntico, dorados y fondos casi iguales) y, a la vez, texto `#f2f0fa` sobre ese violeta a 3,75:1 en chip de filtro activo y botón primario (por debajo de AA).
- **Cambio:** un solo gesto resuelve ambas cosas: el acento pasa a un rosa oscuro propio `#be185d` (token `--violet` conservado de nombre para no tocar el resto de reglas), con su fondo suave `#3d1226`, el degradado del hero en la misma familia (`#3a0f24`) y el texto claro de categoría/eyebrow a `#fbcfe8`. tx-builder conserva su violeta: las dos apps ya no comparten acento.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 166,89 kB).
- **Verificación 2 (smoke):** contraste calculado con la fórmula WCAG sobre los hex finales: texto `#f2f0fa` sobre `#be185d` = **5,35:1** (≥4,5 ✅; antes 3,75:1); categoría `#fbcfe8` sobre panel = 13,19:1; eyebrow sobre fondo suave = 11,57:1.
- **Verificación 3 (checklist + bundle + comparación):** bundle CSS con `#be185d` ×1 y `#8b5cf6` ×0; sin cambios de layout ni de textos. **Comparación contra el último build conocido-bueno** (Ciclo 1: 166,61 kB): 166,89 kB, **+0,17 %**, explicado por los textos de empate/Subvenciones de este ciclo. Sin variables `VITE_*`: build autónomo.

### [D-B1 · BAJA · Contenido] El texto de «rechazada» ya no miente en caso de empate

- **Hallazgo:** con quórum y `favor === contra`, `outcome()` devuelve 'rechazada' y la tarjeta afirmaba «rechazada (más votos en contra)», falso en el empate.
- **Cambio:** el veredicto distingue según los datos reales de la propuesta: si hay empate muestra «Resultado: no aprobada por empate (X VP a favor y X VP en contra; sin mayoría a favor no se aprueba)»; el texto «más votos en contra» solo aparece cuando en efecto `contra > favor`. Comentario en `data.js` que deja constancia de la regla. `outcome()` y los conteos del resumen no cambian (el empate sigue sin aprobarse).
- **Verificación 2 (smoke con lógica ejecutada):** cerradas reales contrastadas — p4 aprobada (2100/150), p5 rechazada con más en contra (400/980, su texto sigue siendo el de «más votos en contra»), p6 sin quórum (700/690, 1.430 < 1.500) — y caso sintético de empate con quórum (800/800, total 1.700 ≥ 1.500): `outcome` = no aprobada y la rama visible seleccionada es la de empate, no la de «más votos en contra». Filtros sin regresión: **todas 6 / activas 3 / cerradas 3** (D-A1 de Ciclo 1 intacto).
- **Verificación 3:** bundle con «no aprobada por empate» ×1, «sin mayoría a favor no se aprueba» ×1 y «rechazada (más votos en contra)» ×1 (solo para el caso real); ortografía revisada.

### [D-B3 · BAJA · Localización] «Grants» → «Subvenciones»

- **Cambio:** categoría renombrada en `CATEGORIES`, en la propuesta p6, en la clave de icono de `App.jsx`, en el título de p1 («fondo comunitario para subvenciones») y en el README. Las cinco categorías quedan en español.
- **Verificaciones:** build ✅; bundle JS con «Subvenciones» ×3 y «Grants» ×0; grep en `src/` y README sin restos en inglés para esta categoría.

## 2026-11-02 · Fase 2, Ciclo 4 — Coherencia visual (GR-1): sin cambio, identidad suficiente

- **Decisión:** no se toca. La diferenciación pedida por este frente ya existe y fue cerrada en el Ciclo 3: acento rosa oscuro `#be185d` (bundle CSS ×1, `#8b5cf6` ×0, verificado hoy sin rebuild), hero asimétrico con tarjeta de poder de voto a la derecha — composición distinta de la columna centrada del resto — y barras de resultados/quórum como recurso visual propio por tarjeta. Añadir otro gesto forzaría la cabecera y arriesgaría lo cerrado; se anota y no se fuerza, según el criterio del ciclo.
- **Verificación:** `dist/` vigente servido en local → index 200 y asset JS 200. Smoke de datos en Node: 6 propuestas, 3 activas y 3 cerradas (filtros de D-A1 operativos sobre los datos). Sin build nuevo: ningún archivo de la app se modificó en este frente.

## 2026-11-02 · Fase 2, Ciclo 5

### [D-B2 · BAJA · Etiquetado] Cantidades en USDC marcadas como de ejemplo donde se vota

- **Hallazgo:** las propuestas p1 («Destinar 120.000 USDC…») y p6 («Asignar 50.000 USDC…») citaban un token real y cifras de tesorería sin marca local: el texto de la propuesta, citado fuera de contexto, se leía como fondos reales (la cabecera y el pie sí declaran la simulación, por eso era baja).
- **Cambio:** marca local en los dos únicos sitios con USDC de `src/` (grep previo: solo p1 y p6; el README no menciona USDC): p1 → «120.000 USDC de ejemplo (simulados, sin valor real)»; p6 → «50.000 USDC de ejemplo (simulados)». Ningún otro texto se tocó.
- **Verificación 1 (build):** `npm run build` → exit 0 (Vite 6.4.5, JS 167,05 kB).
- **Verificación 2 (smoke):** filtros intactos sobre los datos reales — todas 6 / activas 3 / cerradas 3 — y empate veraz intacto: caso sintético con quórum y 800/800 → `outcome` no aprobada y texto «no aprobada por empate» presente en el bundle ×1.
- **Verificación 3 (contenido + comparación):** bundle con «USDC de ejemplo» ×2 (ambas ocurrencias marcadas) y patrón sin marca «120.000 USDC de la» ×0; «Subvenciones» ×3 (Ciclo 3 intacto). **Comparación contra el último build conocido-bueno** (Ciclo 3: 166.885 B): 167.054 B, **+0,10 %**, explicado por las marcas USDC y la defensa de `vote()` de D-B6. Sin variables `VITE_*`.

### [D-B6 parcial · BAJA · Código] Memo real y voto con defensa

- **Cambios seguros aplicados:** (a) `closed` se calcula ahora dentro del `useMemo` de `summary` (fuera se recreaba en cada render y entraba como dependencia: la memoización nunca reutilizaba nada); la dependencia queda solo en `proposals` y el resumen calculado es idéntico. (b) `vote()` ya no confía solo en la UI: busca la propuesta y devuelve sin votar si no existe, si no está `'activa'` o si la opción no es una de `favor`/`contra`/`abstencion`.
- **Subparte no aplicada, con motivo:** el retorno silencioso de `createProposal` con título/descripción vacíos queda como está: es inalcanzable desde la UI (botón `disabled` + campos `required`), y mostrar un mensaje nuevo exigiría estado y texto nuevos — cambio de UX, no corrección segura.
- **Verificación:** misma build y mismo smoke de D-B2 (resumen y filtros sin cambios: 6/3/3); bundle con el resumen y los textos de siempre.

### [D-B7 · BAJA · Lógica] PENDIENTE — exige decisión, no corrección segura

- **Motivo:** derivar el estado de `deadline` (o cerrar propuestas con un temporizador) es una decisión de modelo de gobernanza — cuándo y cómo se cierra una propuesta activa en mitad de una sesión, qué pasa con la creada por el usuario y cómo se anuncia el cierre —, no un arreglo mecánico verificable. Aplicarlo sin esa decisión arriesga los smokes cerrados (filtros 6/3/3 y conteos del resumen). Queda anotado para decisión de Antonio/coordinador.
- **También queda sin tocar:** D-B5 (sin `.gitignore`), fuera del alcance enumerado de este ciclo.
- **Nota para el frente de READMEs (paralelo):** el README de esta app no se editó en este ciclo y no lo necesita por D-B2 (no cita cantidades en USDC).
