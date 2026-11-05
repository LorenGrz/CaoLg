# Estado actual (2026-11-05)

- CAO 2.5.4 instalado con `uv tool`. Repo local, sin remoto todavía.
- Hecho: perfiles (supervisor, claude-dev, codex-dev, gemini-dev, opencode-dev, copilot-reviewer) instalados, `cao-wt`, `cao-ls`, `cao-usage`, `install.sh`.
- Verificado: `cao-server` responde en :9889 (health + web UI 200); `claude-dev` headless en un worktree descartable usó el login nativo (sin pedir login) y corrió con `--permission-mode acceptEdits --model sonnet`, sin `--dangerously-skip-permissions`; `cao-usage` (tabla y `--json`, override de cupo).
- Sin verificar todavía: sesión real de `codex-dev`, `gemini-dev`, `opencode-dev`, `copilot-reviewer`; `assign`/`handoff` entre providers; que el supervisor rote de verdad según `cao-usage --json`; `cao-wt` de punta a punta (necesita terminal interactiva: `cao launch` se adjunta a tmux).
- Gotchas: `cao launch` sin `--headless` pide confirmación (`--auto-approve` solo salta ese prompt; nunca `--yolo`); el flag es `--session-name`; descripciones de perfil con `:` van entre comillas; `cao-usage` muestra 0 para Copilot/Antigravity si `ccusage` no detecta datos.
- Pendiente: crear `LorenGrz/cao-config` en GitHub (requiere confirmación).
