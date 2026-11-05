# CaoLg

"Orca en terminal": configuración de [CAO (CLI Agent Orchestrator)](https://github.com/awslabs/cli-agent-orchestrator) para orquestar Claude Code, Copilot, Codex, Antigravity (`agy`) y OpenCode, cada uno con su login nativo, en tmux y con un worktree por sesión.

Sin secretos en este repo: los logins viven en `~/.claude`, `~/.copilot`, `~/.codex`, `~/.gemini` y nunca se copian.

## Stack

CAO 2.5 (Python, `uv tool`), tmux ≥ 3.3, `ccusage` para el uso, bash/python3 para los scripts.

## Instalación

```bash
uv tool install cli-agent-orchestrator
./install.sh          # perfiles + enlaces de bin/* en ~/.local/bin + perfil seguro de Codex
```

## Uso

Comando único: `caolg open|here|rm|ls|usage|server` (envuelve los scripts de abajo).

```bash
cao-server                              # terminal aparte, queda corriendo (web UI: http://localhost:9889)
cao-wt ~/projects/roadmap mi-tarea      # worktree + rama agent/mi-tarea + supervisor (Opus)
cao-ls                                  # sesiones activas
cao-usage                               # uso por suscripción (tokens / costo)
cao-wt --rm ~/projects/roadmap mi-tarea # cierra la sesión y borra el worktree
```

Una terminal por proyecto: `cao-open ~/projects/<repo> <slug>` abre una ventana nueva con su sesión `cao-<slug>` (si ya existe, se adjunta). La barra de tmux muestra la carpeta, la rama y los atajos; el líder (Opus) se presenta al arrancar (`CAO_WT_GREET=0` lo desactiva).

Atajos (de `~/.config/tmux/tmux.conf`): `Alt+1..9` ventana, `Alt+←/→` anterior/siguiente, `Alt+↑/↓` otro proyecto (sesión), `Ctrl+b w` lista. El supervisor reparte con `assign` (asíncrono) y `handoff` (bloqueante) entre `claude-dev`, `codex-dev`, `gemini-dev`, `opencode-dev` y `copilot-reviewer`, rotando según `cao-usage --json`.

## Permisos por provider

| Worker | Provider | Cómo se contiene |
|---|---|---|
| supervisor | `claude_code` | sin confirmaciones (`--dangerously-skip-permissions`), límites en su prompt, aislado en el worktree |
| claude-dev | `claude_code` | `permissionMode: acceptEdits` (sigue preguntando por comandos) |
| codex-dev | `codex` | `codexProfile: cao-safe` (sin `--yolo`; `approval_policy=never` + `workspace-write`) |
| copilot-reviewer | `copilot_cli` | CAO fuerza `--allow-all --autopilot`: solo en worktree descartable |
| gemini-dev | `antigravity_cli` | CAO fuerza bypass de permisos: solo en worktree descartable |
| opencode-dev | `opencode_cli` | permisos allow/deny fijados al instalar (experimental) |

Nunca usar `cao launch --yolo` ni `allowedTools: ["*"]`. Ningún agente corre en el checkout principal.

## Limitaciones conocidas

- `cao-usage` mide tokens y costo (vía `ccusage`); el % de cupo no lo expone ninguna CLI de forma fiable, por eso figura `n/d` (se puede forzar con `CAO_USAGE_OVERRIDE` para probar la rotación).
- Si `ccusage` no detecta datos de un provider (hoy Copilot muestra 0), el número no es confiable aunque el estado sea `ok`.
- CAO no crea worktrees: lo hace `cao-wt`.

## Próximos pasos

Limpieza automática de worktrees, keybind de Hyprland para `cao-ls`, `cao-server` como servicio `systemd --user`, una TUI propia sobre la API HTTP de CAO (puerto 9889).
