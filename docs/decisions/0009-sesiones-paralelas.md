# 0009 — Varias sesiones caolg en la misma carpeta

Fecha: 2026-11-10 · Estado: aceptada · Modifica: 0005

## Contexto

El nombre de la sesión salía de la carpeta (`cao-cx`): abrir `claudes` otra vez se sumaba a la sesión abierta.
Loren quiere que funcione como `claude`: dos sesiones independientes en el mismo proyecto, un módulo en cada una.
Con ADR 0005 los workers trabajan en el checkout de su repo y cambian la rama: dos sesiones en el mismo repo se
pisarían la rama.

## Decisión

- `claudes` siempre abre una sesión nueva: si `cao-<slug>` tiene terminales conectadas, usa `<slug>-2`, `-3`…
  Una sesión sin terminales se sigue cerrando y se reusa su nombre. Para volver a una abierta: Alt+↑/↓.
- El líder lanza cada worker en `caolg-workdir <Carpeta> <Rama base>`: la carpeta del rol, o un worktree propio
  `<carpeta>-wt/<sesión>` (desacoplado en la base) si un pane de otra sesión `cao-*` está dentro de esa carpeta.
  En este caso no pregunta (0005 pedía preguntar).
- Tareas en `.caolg-tasks/<sesión>/` para que dos líderes en una carpeta sin git no choquen.

## Consecuencias

- La segunda sesión no le cambia la rama a la primera. La primera sigue en el checkout de Loren.
- La detección mira el cwd actual de los panes: si el worker de la otra sesión ya terminó y se cerró, la carpeta
  cuenta como libre.
- Los worktrees de workers no se borran solos (se reusan por nombre de sesión); se borran a mano.
