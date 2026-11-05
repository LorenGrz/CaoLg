# CaoLg

"Orca en terminal": configuración de [CAO (CLI Agent Orchestrator)](https://github.com/awslabs/cli-agent-orchestrator) para trabajar con un líder **Opus** que planifica y abre workers de **Claude Code, Copilot, Codex, Antigravity (`agy`) y OpenCode**, cada uno con su login nativo, en tmux, con un worktree y una terminal por proyecto.

Sin secretos en este repo: los logins viven en `~/.claude`, `~/.copilot`, `~/.codex`, `~/.gemini` y nunca se copian.

## Stack

CAO 2.5.4 (pineado, Python, `uv tool`), tmux ≥ 3.3, `ccusage` para el uso, bash + python3 (stdlib) para los scripts, tema de Omarchy para los colores.

## Instalación

```bash
./install.sh   # CAO 2.5.4 + modo pane, perfiles, bin/* en ~/.local/bin, perfil seguro de Codex, hook de tema
caolg server   # en una terminal aparte (reiniciarlo después de install.sh)
```

Cada CLI tiene que tener su sesión iniciada antes (`claude`, `copilot login`, `codex login`, `agy`, `opencode`).

## Uso

```bash
caolg open ~/projects/<repo> <slug>   # terminal nueva: worktree + rama agent/<slug> + líder Opus
caolg here ~/projects/<repo> <slug>   # lo mismo en esta terminal
caolg ls                              # sesiones activas (web UI: http://localhost:9889)
caolg usage                           # uso por suscripción
caolg rm ~/projects/<repo> <slug>     # cierra la sesión y borra el worktree
```

### Layout

```
 caolg  1:caolg                         ~/projects/web-wt/demo (agent/demo)  Alt+1..9 pane · Alt+z · Alt+c
┌─ Opus · líder ─────────┬─ front · agy ─────────┐
│ > ...                  │                       │
│                        ├─ back · codex ────────┤
│                        │                       │
└────────────────────────┴───────────────────────┘
 agentes: front · agy● back · codex⚠ │ Opus ctx 6% │ claude 49.1M $23.59 · codex 0 · agy 76.7k · …
```

- Opus a la izquierda (55%); los workers apilados a la derecha, con borde del color de su provider (claude naranja, codex verde, agy azul, opencode magenta, copilot cyan). Si no entran, CAO abre el siguiente como tab arriba.
- Línea 2: agentes con estado (● trabajando, ○ libre, ⚠ te necesita, ✗ error, ◌ desconocido), contexto de Opus y usage del día. Se actualiza cada 10 s.
- Colores del tema actual de Omarchy; al cambiar de tema se recolorean las sesiones abiertas.

### Atajos (solo dentro de sesiones `cao-*`; afuera siguen como en tu tmux.conf)

| Atajo | Acción |
|---|---|
| `Alt+1..9` | ir al pane N (Opus es el 1) |
| `Alt+z` | zoom del pane |
| `Alt+c` | `/clear` de Opus con resumen (guarda estado, limpia, lo relee) |
| `Alt+←/→` | tabs (ventanas) |
| `Alt+↑/↓` | otro proyecto (sesión) |

### Cómo trabaja el líder

- Al abrir un proyecto se presenta (carpeta, rama, workers) y, si no hay, crea los **roles de la carpeta** en `~/.local/share/caolg/<repo>/agents/*.md` (front, back, reviewer…).
- En cada tarea elige rol + CLI (por dificultad y cupo, o la que le pidas: "abrilo con agy"), escribe la tarea en `.caolg-tasks/` (excluido de git) y te dice en qué `Alt+N` quedó.
- **/clear automático** cuando su contexto pasa `CAOLG_CLEAR_AT` (default 30% de 1M); antes escribe su estado en `~/.local/share/caolg/<repo>/<slug>/state.md` y después lo relee.

Variables: `CAO_WT_GREET=0` (sin saludo), `CAOLG_CLEAR_AT` (0 desactiva), `CAOLG_CTX_WINDOW`, `CAOLG_TICK`.

## Permisos por provider

| Worker | Provider | Cómo se contiene |
|---|---|---|
| supervisor (líder) | `claude_code` | sin confirmaciones (`--dangerously-skip-permissions`), límites en su prompt, aislado en el worktree |
| claude-dev | `claude_code` | `permissionMode: acceptEdits` |
| codex-dev | `codex` | `codexProfile: cao-safe` (sin `--yolo`; `approval_policy=never` + `workspace-write`) |
| copilot-dev | `copilot_cli` | CAO fuerza `--allow-all --autopilot`: solo en el worktree |
| gemini-dev | `antigravity_cli` | CAO fuerza bypass de permisos: solo en el worktree |
| opencode-dev | `opencode_cli` | permisos allow/deny fijados al instalar (experimental) |

Nunca usar `cao launch --yolo` ni `allowedTools: ["*"]`. Ningún agente corre en el checkout principal.

## Decisiones

- [0001](docs/decisions/0001-cao-como-orquestador.md): CAO como orquestador y manejo de permisos.
- [0002](docs/decisions/0002-modo-paneles-con-marca.md): Opus y workers en la misma ventana (modo pane + marca). Depende de internals de CAO 2.5.4.

## Limitaciones conocidas

- El % de cupo de cada suscripción no lo expone ninguna CLI; la barra muestra tokens/costo (vía `ccusage`).
- El estado de agy y copilot a veces figura ◌ (CAO no lo detecta).
- Probado: layout con 2 workers, bordes, barra, `/clear` manual y automático, roles por carpeta. **Sin probar**: desborde a tabs con muchos workers y el cambio real de tema de Omarchy.

## Tests

```bash
python3 -m unittest discover tests
```

## Próximos pasos

`cao-server` como servicio `systemd --user`, limpieza automática de worktrees, keybind de Hyprland para `caolg open`.
