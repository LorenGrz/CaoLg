# 0002 — Opus y workers en la misma ventana (modo pane + marca)

- Estado: aceptada (2026-11-05)

## Contexto

Loren quiere a Opus siempre visible a la izquierda y los workers como paneles interactivos a la derecha, con desborde a tabs. CAO en modo `window` abre una ventana por agente; en modo `pane` (`terminal.spawn_mode=pane`) suma los workers como panes a `terminal.pane_window`, pero deja al primer terminal (el líder) en su propia ventana.

## Decisión

Usar el modo pane con `pane_window=caolg` y, cuando el líder terminó de inicializar, aplicarle "el truco de la marca" (`bin/caolg-session`):

1. Copiar al pane de Opus la marca `@cao_terminal=<nombre de su ventana>` y `@cao_terminal_id`.
2. Reemplazar el hook anti-renombre que CAO pone en la ventana (`window-renamed` → nombre original) por uno que fije `caolg`, y renombrar la ventana a `caolg`.

CAO busca un terminal por nombre de ventana y, si no existe, por la marca del pane en toda la sesión (`clients/tmux.py`: `_resolve_pane`, `_send_target`), así que sigue encontrando a Opus, y los workers se suman al lado. El layout (`main-vertical`, 55%) lo aplica `caolg-layout` vía hooks `after-split-window`/`pane-exited` (`terminal.pane_layout=none`). Los bordes van a nivel pane (`set -p pane-border-format`) porque CAO pisa el de la ventana en cada split.

## Alternativas descartadas

- Espejo de solo lectura del worker (`capture-pane`) en un pane al lado de Opus: no es interactivo y las TUIs se cortan al ancho del pane.
- `join-pane` de Opus a la ventana de workers: rompe la búsqueda por nombre de ventana.
- Modo pane puro (Opus en su ventana, workers en otra): fallback si el truco deja de funcionar.

## Consecuencias

- Depende de internals de CAO 2.5.4 → `install.sh` pinea esa versión. Antes de subir de versión, repetir la verificación del plan `docs/superpowers/plans/2026-11-05-caolg-visual.md`.
- El truco solo se aplica cuando el líder está listo: si se renombra durante la inicialización, CAO da el arranque por fallido y cierra la sesión (visto en la prueba).
- El líder usa `role: developer` (no `supervisor`): necesita escribir roles, tareas y `state.md`, y correr `cao-usage`/`tmux`.
