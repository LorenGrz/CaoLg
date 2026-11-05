# CaoLg

Configuración personal de CAO (orquestador multi-CLI) con layout tipo IDE en tmux. Ver `README.md` para uso.

## Mapa

- `profiles/*.md`: perfiles de CAO (frontmatter YAML + prompt). `supervisor` = líder Opus; workers genéricos por provider (`claude-dev`, `codex-dev`, `gemini-dev`, `opencode-dev`, `copilot-dev`), el rol viene en la tarea.
- `bin/caolg`: entrada única (`open|here|rm|ls|usage|server`).
- `bin/cao-wt`, `bin/cao-open`, `bin/cao-ls`, `bin/cao-usage`: worktree + lanzamiento, terminal por proyecto, sesiones, usage.
- `bin/caolg-session`: post-lanzamiento (truco de la marca, hooks, tema, atajos, saludo) y luego `caolg-watch`.
- `bin/caolg-watch`: bordes/tabs por provider, línea 2 de la barra (`~/.cache/caolg/<s>.bar`), `/clear` automático.
- `bin/caolg-layout`, `bin/caolg-theme`, `bin/caolg-clear`: layout main-vertical, colores del tema de Omarchy, `/clear` con resumen.
- `lib/caolg_lib.py`: funciones puras (tema, transcripts, barra). `tests/test_caolg.py`.
- `tmux/caolg-keys.conf`: atajos que solo actúan en sesiones `cao-*`.
- `omarchy/50-caolg-theme`: hook `theme-set`.
- `codex/cao-safe.config.toml`: perfil de Codex sin `--yolo`.
- `docs/decisions/`: ADRs. `docs/superpowers/plans/`: planes aprobados.

## Datos fuera del repo

- Roles por carpeta: `~/.local/share/caolg/<repo>/agents/*.md`. Estado de Opus: `~/.local/share/caolg/<repo>/<slug>/state.md`.
- Cache: `~/.cache/caolg/` (barra por sesión, `usage.json`).

## Reglas

- Repo público: nunca secretos ni copias de `~/.claude`, `~/.codex`, `~/.copilot`, `~/.gemini`.
- Nunca `cao launch --yolo` ni `allowedTools: ["*"]`.
- CAO pineado en 2.5.4 (ADR 0002). Subir de versión exige repetir la verificación del plan visual.
- Verificar con: `python3 -m unittest discover tests` y `bash -n` sobre los scripts bash de `bin/`.
