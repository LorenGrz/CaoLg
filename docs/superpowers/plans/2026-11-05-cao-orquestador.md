# Plan: "Orca en terminal" con CAO (Claude Code + Copilot CLI)

## Context
Querés el flujo de Orca (varios agentes, cada uno con su worktree, viendo sus sesiones y pasándose trabajo) pero en terminal y liviano, usando el login nativo de Claude Pro (`~/.claude`) y de Copilot (`~/.copilot`). Elegiste CAO (awslabs/cli-agent-orchestrator): lanza `claude` y `copilot` como procesos reales dentro de tmux, así que cada CLI usa su propia autenticación. La idea es arrancar con lo mínimo y sumar cosas a medida que las uses.

Ya está todo lo necesario: tmux 3.8 (CAO pide ≥3.3), uv 0.11, Python 3.14, Claude Code 2.1.318, Copilot CLI 1.0.105 (con `~/.copilot` ya configurado).

## Qué ofrece CAO y qué falta
| Necesidad del MVP | CAO | Solución |
|---|---|---|
| Paneles simultáneos | Sí: una sesión tmux `cao-*` con una ventana por agente (`Ctrl+b w`) | Usarlo tal cual |
| Lista de sesiones | Web UI en `http://localhost:9889` + `tmux ls` | Usar ambos; alias `cao-ls` |
| Handoff entre agentes | Sí: herramientas MCP `handoff` / `assign` / `send_message` | Perfiles supervisor + workers |
| Worktree por agente | **No lo hace nativamente** | Script chico `cao-wt` que crea el worktree y lanza CAO adentro |

## Providers (todos ya instalados y con login nativo)
| CLI | Provider CAO | Login | Permisos por defecto en CAO | Cómo lo contenemos |
|---|---|---|---|---|
| Claude Code | `claude_code` | `~/.claude` (Pro) | `--dangerously-skip-permissions` | perfil con `permissionMode: acceptEdits` → sigue preguntando por comandos |
| Copilot CLI | `copilot_cli` | `~/.copilot` | `--allow-all --autopilot` (no se puede apagar) | solo en worktree descartable, rol revisor |
| Codex | `codex` | `~/.codex` | `--yolo` | `codexProfile: cao-safe` → `~/.codex/cao-safe.config.toml` con `approval_policy="never"` + `sandbox_mode="workspace-write"` |
| Antigravity (Google) | `antigravity_cli` | `~/.gemini` (`agy`) | `--dangerously-skip-permissions` (no se puede apagar) | solo en worktree descartable |
| OpenCode (experimental) | `opencode_cli` | su config propia en `~/.aws/opencode/` | permisos allow/deny fijados al instalar | `allowedTools` acotado en el perfil |

Regla: ningún agente corre en el checkout principal. Siempre en un worktree de `cao-wt`, así lo que haga un agente sin confirmaciones queda aislado y se revisa con `git diff` antes de mergear. Nunca usar `cao launch --yolo` ni `allowedTools: ["*"]` (reactivan el bypass en Codex). Notas: Antigravity comparte un único `~/.gemini/config/mcp_config.json` entre workers; OpenCode está marcado experimental en CAO.

## Modelo principal y ruteo de workers entre suscripciones
- **Supervisor = Opus** (`claude_code`, `model: opus`): es con quien hablás siempre. Conversa, detecta cuándo hace falta un plan o lo recibe de vos, y reparte el trabajo.
- **Workers rotan por dificultad y por cupo disponible**, no siempre Sonnet. La tabla vive en el prompt del supervisor (`profiles/supervisor.md`) y se ajusta con el uso:

| Tipo de tarea | Primera opción | Alternativas (rotación) |
|---|---|---|
| Decisión, plan o bug sin causa conocida | el supervisor mismo (Opus) | `codex-dev` con razonamiento alto |
| Implementar un plan ya aprobado | `claude-dev` (Sonnet) | `codex-dev`, `gemini-dev` |
| Trabajo mecánico o masivo (boilerplate, tests en lote) | `gemini-dev` | `opencode-dev`, `codex-dev` |
| Revisión de código | `copilot-reviewer` | `codex-dev` |

- **Rotación**: antes de cada `assign` o `handoff`, el supervisor corre `cao-usage --json` y, entre las opciones válidas para esa tarea, elige el provider con más cupo libre. Si un provider está cerca del límite, se saltea.
- **Automático vs. con vos**: las tareas automáticas van directo a los workers. Lo que requiere un plan se te propone primero, igual que hoy con plan mode, y recién cuando lo aprobás se reparte entre suscripciones.

## Usage: por sesión y global
- **Por sesión**: cada ventana tmux corre la CLI real, así que su propio indicador de uso y contexto se ve tal cual (statusline de Claude Code, `/usage` de Copilot, estado de Codex, etc.). No hay que construir nada.
- **Global**: script `bin/cao-usage` que junta lo que cada CLI guarda en disco y muestra una tabla con una fila por suscripción: tokens/costo del día y de la ventana de límite, y % del cupo cuando la CLI lo expone.
  - Claude: `ccusage` (lee `~/.claude/projects/*.jsonl`).
  - Codex: `@ccusage/codex` (lee `~/.codex/sessions`).
  - Copilot, Antigravity y OpenCode: se lee lo que guarde cada uno en disco (`~/.copilot/session-state`, `~/.gemini`, `~/.local/share/opencode`). Primer paso de la implementación: inspeccionar esos formatos. Lo que no se pueda leer aparece como "n/d" en vez de un número inventado.
  - Se ve en la línea de estado de tmux (`status-right` refrescando cada 60 s) y en una ventana fija `usage` dentro de cada sesión `cao-*` (`watch -n 60 cao-usage`). Con `--json` lo consume el supervisor para la rotación.

## Pasos
1. **Instalar CAO** con la versión publicada en PyPI (más estable que `main`): `uv tool install cli-agent-orchestrator`, después `cao --help`.
2. **Repo de configuración** en `~/projects/cao-config`, público, sin secretos (los logins quedan en `~/.claude` y `~/.copilot` y nunca se copian):
   - `profiles/supervisor.md`: `provider: claude_code`, `permissionMode: acceptEdits`; reparte el trabajo con `assign` y `handoff`.
   - `profiles/claude-dev.md`: worker de Claude que implementa.
   - `profiles/copilot-reviewer.md`: worker de Copilot que revisa, con `provider: copilot_cli`.
   - `profiles/codex-dev.md` (`provider: codex`, `codexProfile: cao-safe`) + `codex/cao-safe.config.toml` enlazado a `~/.codex/`.
   - `profiles/gemini-dev.md` (`provider: antigravity_cli`).
   - `profiles/opencode-dev.md` (`provider: opencode_cli`, `allowedTools` acotado; se instala con `--provider opencode_cli`).
   - `bin/cao-wt <repo> <slug> [perfil]`: hace `git worktree add ../<repo>-wt/<slug> -b agent/<slug>`, entra con `cd` y corre `cao launch --agents <perfil> --session <slug>`. Con `--rm` hace `cao shutdown` y `git worktree remove`.
   - `bin/cao-ls`: `tmux ls | grep cao-` más la URL de la web UI.
   - `install.sh`: instala los perfiles con `cao install profiles/*.md`, y `cao install ... --provider copilot_cli` para el de Copilot. También enlaza `bin/*` en `~/.local/bin`.
   - `README.md`: el flujo de uso y las decisiones; `AGENTS.md` y `.agents/CONTEXT.md` mínimos, como piden tus convenciones.
   - `docs/decisions/0001-cao-como-orquestador.md`: por qué CAO y no Crush/Hermes/TUI propia, y cómo se resolvió el tema de permisos.
3. **Servidor**: `cao-server` corre en una terminal aparte. Más adelante, si lo usás seguido, se puede pasar a un servicio `systemd --user`.
4. **Más adelante, solo cuando lo necesites** (no entra en este plan): limpieza automática de worktrees, sincronizar perfiles con tus skills, keybind de Hyprland para abrir `cao-ls`, una TUI propia sobre la API HTTP de CAO (puerto 9889).

## Verificación
- `cao --help` y `cao-server` levantan, y `http://localhost:9889` responde.
- `cao-wt ~/projects/roadmap test-cao claude-dev` crea el worktree y una sesión `cao-test-cao`; dentro, `claude` **no** pide login (usa Claude Pro) y pide permiso antes de correr comandos.
- Desde el supervisor, `assign` a `copilot-reviewer` abre una ventana de Copilot que **no** pide login, y la respuesta vuelve por `send_message`.
- Lo mismo con `codex-dev`, `gemini-dev` y `opencode-dev`: cada uno abre su ventana sin pedir login; Codex corre con `--profile cao-safe` (sin `--yolo`, verificable con `ps aux | grep codex`).
- `cao-usage` muestra una fila por suscripción con números reales para Claude y Codex, y "n/d" donde no haya datos; `cao-usage --json` es JSON válido (`| jq .`).
- Con una tarea mecánica, el supervisor (Opus) delega en `gemini-dev`/`opencode-dev` y no en Sonnet. Si se simula que un provider está al límite (por ejemplo con un override `CAO_USAGE_OVERRIDE`), elige otro.
- `cao-ls` muestra la sesión y la web UI la lista.
- `cao-wt --rm roadmap test-cao` cierra la sesión y borra el worktree; `git worktree list` queda limpio.

## Acciones hacia afuera (piden confirmación al ejecutar)
- Crear el repo remoto `LorenGrz/cao-config` en GitHub y hacer el primer push.
