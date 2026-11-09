# Estado actual (2026-11-09)

- Repo en ~/projects/caolg, remoto https://github.com/LorenGrz/CaoLg (público, main). CAO 2.5.4 pineado en modo pane (`terminal.spawn_mode=pane`, `pane_window=caolg`, `pane_layout=none`).
- Hecho: líder Opus + workers por provider, layout Opus izquierda / workers derecha (truco de la marca, ADR 0002), bordes y tabs por provider, barra de 2 líneas (agentes, ctx de Opus, usage), colores de Omarchy + hook theme-set, atajos solo en `cao-*`, `/clear` con resumen solo a mano (Alt+c; nunca automático), roles por carpeta en `~/.local/share/caolg/<repo>/agents`.
- Verificado end-to-end (headless, repo descartable): rename + marca tras inicializar; Opus creó roles; assign a agy y codex quedó como 2 panes a la derecha con etiquetas `front · agy` / `back · codex`; Codex con `--profile cao-safe`; barra con estados y usage; `/clear` con Alt+c (nuevo transcript; Opus guardó su estado en state.md y, tras el clear, no retoma solo: espera la indicación de Loren, supervisor.md); `/context` confirma ventana de 1M y el cálculo de tokens.
- Sin verificar: desborde a tabs con muchos workers; `omarchy theme set` real; uso interactivo adjuntado (Loren).
- Gotchas: renombrar la ventana del líder antes de que CAO lo inicialice hace fallar el arranque; `tmux has-session -t x` matchea por prefijo (usar `=x`); CAO pisa `pane-border-format` de la ventana en cada split (usar nivel pane); `role: supervisor` no puede escribir archivos.
- Login: `cao-usage` reporta `logged_in`/`login_hint` por provider (cache 5 min en `~/.cache/caolg/auth.json`, override en `~/.config/caolg/auth.toml`); el líder solo usa los que tienen login. Hoy: claude, agy, opencode, copilot sí; codex no.
- Codex CLI de Loren sin login (`codex login status` → Not logged in): los workers `codex-dev` quedan en la pantalla de login hasta que haga `codex login`.
- `cao-server` corre como proceso en segundo plano de una sesión de Claude Code; pendiente pasarlo a `systemd --user`.
