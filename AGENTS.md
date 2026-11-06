# CaoLg

Configuración personal de CAO (orquestador multi-CLI) con layout tipo IDE en tmux. Ver `README.md` para uso.

## Mapa

- `profiles/*.md`: perfiles de CAO (frontmatter YAML + prompt). `supervisor` = líder Opus; workers genéricos por provider (`claude-dev`, `codex-dev`, `gemini-dev`, `opencode-dev`, `copilot-dev`), el rol viene en la tarea.
- `bin/caolg` (alias `codes`): entrada única. Sin args usa la carpeta actual: repo git → worktree; sin git → `cao-wt --dir` en la carpeta misma.
- `bin/cao-wt`, `bin/cao-open`, `bin/cao-ls`, `bin/cao-usage`: worktree + lanzamiento, terminal por proyecto, sesiones, usage.
- `bin/caolg-close`: hook `client-detached`; al cerrar la última terminal guarda estado, cierra sesión/watcher y apaga el cao-server propio (pidfile).
- `bin/caolg-mcp`: `cao-mcp-server` de los agentes de Claude (scope de usuario, `--ensure`): completo para el líder, solo `send_message` al líder para los workers, vacío fuera de CAO. Los perfiles de Claude no definen `mcpServers` para que CAO no use `--strict-mcp-config`. ADR 0004.
- `bin/caolg-session`: post-lanzamiento (truco de la marca, hooks, tema, atajos, saludo) y luego `caolg-watch`.
- `bin/caolg-watch`: bordes/tabs por provider, línea 2 de la barra (`~/.cache/caolg/<s>.bar`), `/clear` automático.
- `bin/caolg-tabs`: mitad derecha como tabs (Opus 50% fijo + un agente visible; el resto en ventanas ocultas `caolg-park`), color fijo por tab, Alt+N. ADR 0003.
- `bin/caolg-layout`, `bin/caolg-theme`, `bin/caolg-clear`: hook de layout (llama a `caolg-tabs sync`), colores del tema de Omarchy, `/clear` con resumen.
- tmux 3.8: opciones de sesión con `-t "=<s>:"` (no `=<s>`). La marca de CAO del supervisor es de ventana y se hereda: resolver con `owner_marks`.
- `lib/caolg_lib.py`: funciones puras (tema, transcripts, barra). `tests/test_caolg.py`.
- `tmux/caolg-keys.conf`: atajos que solo actúan en sesiones `cao-*`.
- `omarchy/50-caolg-theme`: hook `theme-set`.
- `codex/cao-safe.config.toml`: perfil de Codex sin `--yolo`.
- `docs/decisions/`: ADRs. `docs/superpowers/plans/`: planes aprobados.

## Datos fuera del repo

- Roles por carpeta: `~/.local/share/caolg/<repo>/agents/*.md`. Estado de Opus: `~/.local/share/caolg/<repo>/<slug>/state.md`.
- Cache: `~/.cache/caolg/` (barra por sesión, `usage.json`).

## Reglas

- Después de cada cambio: tests + `bash -n`, commit (Conventional Commits) y push a `main` sin preguntar (pedido de Loren).
- Repo público: nunca secretos ni copias de `~/.claude`, `~/.codex`, `~/.copilot`, `~/.gemini`.
- Nunca `cao launch --yolo` ni `allowedTools: ["*"]`.
- CAO pineado en 2.5.4 (ADR 0002). Subir de versión exige repetir la verificación del plan visual.
- Verificar con: `python3 -m unittest discover tests` y `bash -n` sobre los scripts bash de `bin/`.
