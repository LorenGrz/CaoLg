# 0005 — Cada worker trabaja en la carpeta de su rol

Fecha: 2026-11-06 · Estado: aceptada

## Contexto

El líder arrancaba a todos los workers en su propia carpeta (la raíz del proyecto) y, para no pisar el checkout
de Loren, les armaba worktrees aparte (`cx-reino/wt-front-monitor`). Eso dejaba carpetas sueltas que no son
ninguno de los repos, y desde el borde no se entendía dónde trabajaba cada uno.

## Decisión

- Cada rol declara `Carpeta:` (y `Rama base:` si implementa). Front y back trabajan en la carpeta de su repo y
  crean ahí la rama de la tarea desde la base (`origin/dev`); reviewer y roles transversales, en la raíz.
- El líder lanza al worker con `working_directory` = esa carpeta. `assign`/`handoff` solo aceptan ese parámetro
  si el MCP corre con `CAO_ENABLE_WORKING_DIRECTORY=true`: lo pone `bin/caolg-mcp` solo para el líder.
- Antes de asignar, el líder mira la carpeta: con cambios sin commitear frena y pregunta; limpia en otra rama,
  cambia de rama y avisa. Worktree aparte solo para trabajo en paralelo en el mismo repo, y preguntando.

## Consecuencias

- El borde muestra el repo real y su rama. Menos carpetas sueltas.
- El worker cambia la rama del checkout de Loren: si Loren estaba en otra rama, queda movido (sin perder nada:
  solo se cambia con el árbol limpio).
- Dos tareas en paralelo sobre el mismo repo vuelven a necesitar un worktree.
