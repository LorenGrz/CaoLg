# 0003 — La mitad derecha como tabs (un agente visible por vez)

- Estado: aceptada (2026-11-06)

## Contexto

Con los workers apilados a la derecha (ADR 0002), a partir del tercero los panes quedan demasiado bajos para usar una TUI. Loren quiere Opus fijo en la mitad izquierda y, en la mitad derecha, literalmente la mitad, un solo agente visible, cada uno de un color distinto, elegible con `Alt+2..9` y `Alt+0`.

## Decisión

`bin/caolg-tabs` deja en la ventana `caolg` solo dos panes: Opus (`@caolg_leader`) y la tab visible. El resto se estaciona con `break-pane` en ventanas ocultas `caolg-park` y se trae con `swap-pane`. CAO los sigue encontrando porque resuelve cada terminal por la marca del pane en toda la sesión. Los hooks `after-split-window`, `pane-exited` y `after-kill-pane` corren `sync`, y la tab más nueva es la que se ve.

- Número de tab (`@caolg_tab`) y color (`@caolg_color`, una clave de `TAB_PALETTE`, no un hex, para seguir al tema) se fijan al crear la tab. Mover una tab cambia su número, no su color.
- La marca de CAO del supervisor (`@cao_terminal`, `@cao_terminal_id`) es una opción de **ventana**, y los formatos de tmux la heredan a todos los panes. Por eso las marcas se resuelven con `owner_marks` (valor propio del pane, o el de ventana solo para el líder). Antes, una terminal suelta en la ventana de Opus "era" Opus: `Alt+Esc` sobre ella borraba al supervisor vía CAO y la sesión se rompía.
- En tmux 3.8, `show`/`set -t` esperan un pane: para opciones de sesión se usa `=<s>:` (con `=<s>` falla y la opción no se lee ni se guarda).

## Alternativas descartadas

- Workers apilados (ADR 0002): ilegibles con 3 o más.
- Una ventana de tmux por worker: Opus deja de estar visible al cambiar de worker.
