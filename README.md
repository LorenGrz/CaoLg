# CaoLg

"Orca en terminal": configuración de [CAO (CLI Agent Orchestrator)](https://github.com/awslabs/cli-agent-orchestrator) para trabajar con un líder **Opus** que planifica y abre workers de **Claude Code, Copilot, Codex, Antigravity (`agy`) y OpenCode**, cada uno con su login nativo, en tmux, con un worktree y una terminal por proyecto.

Sin secretos en este repo: los logins viven en `~/.claude`, `~/.copilot`, `~/.codex`, `~/.gemini` y nunca se copian.

## Stack

CAO 2.5.4 (pineado, Python, `uv tool`), tmux ≥ 3.3, bash + python3 (stdlib) para los scripts, panel de agentes de Omarchy para los cupos, `ccusage` para los tokens de `caolg usage`, tema de Omarchy para los colores.

## Instalación

```bash
./install.sh   # CAO 2.5.4 + modo pane, perfiles, bin/* en ~/.local/bin (+ alias claudes), perfil seguro de Codex,
               # cao-mcp-server de los agentes de Claude, hook de tema
caolg server   # opcional: caolg lo levanta solo; reiniciarlo después de install.sh
```

El líder **solo usa los providers donde tenés sesión iniciada**. `caolg usage` muestra la columna `login` y, para los que faltan, cómo loguearte (`codex login`, `copilot login`, `opencode auth login`, abrir `agy`). Se refresca cada 5 min (o `cao-usage --refresh-auth`), así que al loguearte se suma solo. En la barra solo aparecen los que tienen login.

Detección: `claude auth status`, `codex login status`, `opencode auth list` y el panel de agentes de Omarchy; Copilot y agy no tienen comando de estado, así que cuentan como logueados si hubo uso en los últimos 7 días. Para forzarlo: `~/.config/caolg/auth.toml` con `copilot = true` o `codex = false`.

## Uso

`claudes` es el alias corto de `caolg`: son el mismo comando.

```bash
cd ~/projects/<repo> && claudes                 # repo git: worktree <repo>-wt/<repo> + sesión cao-<repo> en esta terminal
                                                # (si ya existe, se adjunta; dentro de un worktree de caolg, a esa sesión)
cd ~/cualquier/carpeta && claudes               # sin git: trabaja ahí mismo, como claude (sin worktree), sesión cao-<carpeta>
claudes open                                    # lo mismo en una terminal nueva
claudes open ~/projects/<repo> <slug>           # repo y nombre explícitos, terminal nueva
claudes here ~/projects/<repo> <slug> [perfil]  # repo y nombre explícitos, esta terminal
claudes ls                                      # sesiones activas (web UI: http://localhost:9889)
claudes usage [--json]                          # cupo y login por suscripción
claudes rm                                      # cierra la sesión de la carpeta actual (y borra su worktree si es repo)
claudes rm ~/projects/<repo> <slug>             # lo mismo, explícito
claudes server                                  # cao-server en primer plano
```

`cao-server` se levanta solo si no está corriendo (log en `~/.cache/caolg/cao-server.log`).

Si ya existe una sesión `cao-<nombre>` que no abrió caolg (sin layout, barra ni saludo), `claudes` no se adjunta en silencio: te dice cómo cerrarla (`cao shutdown --session cao-<nombre>`) o entrar igual.

**Cerrar la terminal cierra todo, como Claude Code:** Opus guarda su estado en `state.md` (si no está a mitad de una respuesta), se apagan la sesión, los workers y el watcher y, si no queda ninguna sesión `cao-*`, también el `cao-server` que levantó caolg. Quedan los archivos: worktree y rama, roles, `state.md` y transcripts. Para dejarla viva al desconectarte (tmux clásico): `CAOLG_KEEP=1 claudes`.

### Layout

```
 caolg  1:caolg                         ~/projects/web-wt/demo (agent/demo)  Alt+1..9 pane · Alt+z · Alt+c
┌─ Opus 5.5 · líder ─────┬─ 2 front · agy  3 back · codex  4 zsh ─┐
│ > ...                  │                                        │
│                        │  (tab visible: front · agy)            │
│                        │                                        │
└────────────────────────┴────────────────────────────────────────┘
 claude 5h 8% 4h07m · 7d 1% 4d18h | agy 7d 12% 3d02h | copilot mes 3% 24d | opencode n/d
```

- Opus fijo en la mitad izquierda (50%); la mitad derecha muestra **un solo** agente o terminal por vez (tabs, `bin/caolg-tabs`, ADR 0003). Los demás quedan estacionados en una ventana oculta y se traen con `Alt+2..9`/`Alt+0`. Cada tab nueva toma un color distinto (naranja, verde, azul, magenta, cyan, amarillo, rojo, en ronda) y lo conserva aunque la muevas; el borde superior lista las tabs con su tecla.
- Línea 2: el cupo de cada suscripción como lo da cada CLI: ventana, % usado y lo que falta para el reset (fuente: el panel de agentes de Omarchy, `~/.local/state/omarchy/agents/usage/`: claude `5h`/`7d`, agy `7d`, copilot `mes`; opencode no tiene cupo propio: `n/d`. Respaldo si falta o tiene más de 10 min: statusline de Claude, rollouts de Codex, `gh` para copilot). Orden: claude, agy, copilot, opencode (codex al final); solo aparecen los que tienen login, separados por `|`. Verde, amarillo desde 50%, rojo desde 80%. Sin tokens ni precios. Contexto y gasto de cada agente los muestra su propia statusline, abajo de su pane. El borde de cada agente dice `<modelo> · <nombre> · <carpeta> (<rama>)` (`Sonnet 5.5 · front · wt-front (fix/…)`): la carpeta es la raíz del repo git donde está parado (o la carpeta, sin git) y la rama se recorta a 28 caracteres. En la mitad derecha solo la tab visible muestra carpeta y rama, para que la tira no desborde. El líder muestra siempre la carpeta donde se lanzó (sin rama si no es un repo git). Los workers de Claude toman la carpeta de su statusline (sigue los `cd` del agente, por ejemplo a un worktree); los demás, la del proceso del pane. Se actualiza cada 10 s.
- Colores del tema actual de Omarchy; al cambiar de tema se recolorean las sesiones abiertas.

### Atajos (solo dentro de sesiones `cao-*`; afuera siguen como en tu tmux.conf)

| Atajo | Acción |
|---|---|
| `Alt+1` | Opus |
| `Alt+2..9`, `Alt+0` | traer la tab N a la mitad derecha |
| `Alt+Enter`, `Alt+Shift+Enter` | terminal nueva como tab |
| `Alt+Esc` | cerrar la tab visible (si es agente, vía CAO; Opus no se cierra) |
| `Alt+Shift+←/→` | mover la tab visible |
| `Alt+i` | cambiar la identidad (rol) del agente de la tab |
| `Alt+z` | zoom del pane |
| `Alt+c` | `/clear` de Opus con resumen (guarda estado, limpia, lo relee) |
| `Alt+←/→` | tab anterior / siguiente |

`Alt+↑/↓` (cambiar de proyecto, es decir de sesión) viene de tu `~/.config/tmux/tmux.conf`, no de caolg.

### Cómo trabaja el líder

- Tiene los mismos MCP que tu Claude (Atlassian/Jira, GitHub, Slack, Gmail, Drive, plugins…), así que puede leer tickets o cargarlos sin abrir un worker; escribir ahí va solo con tu OK. Para eso los perfiles de Claude no definen `mcpServers` y `cao-mcp-server` se registra con scope de usuario (`bin/caolg-mcp`, ADR 0004).
- Los workers de Claude arrancan en **auto mode** (`permissionMode: auto`) y solo ven `send_message`: le devuelven el resultado al líder que les asignó la tarea, no se hablan entre sí ni abren agentes. Un Claude que abras a mano fuera de CAO ve ese MCP vacío.
- Al abrir un proyecto responde una línea (carpeta, rama, roles) sin leer nada; solo si no hay **roles de la carpeta** lee lo justo del repo y los crea en `~/.local/share/caolg/<repo>/agents/*.md` (front, back, reviewer…).
- En cada tarea elige rol + CLI (por dificultad y cupo, o la que le pidas: "abrilo con agy"), escribe la tarea en `.caolg-tasks/` (excluido de git) y te dice en qué `Alt+N` quedó.
- **Nunca se limpia solo.** Cuando su contexto pasa `CAOLG_WARN_AT` (default 50%, medido con el % exacto de su statusline), el borde de Opus se pone rojo con `⚠ ctx N% · Alt+c` y aparece un aviso. Con `Alt+c` escribe su estado en `~/.local/share/caolg/<repo>/<slug>/state.md` y se limpia.

### Variables

| Variable | Efecto |
|---|---|
| `CAO_WT_GREET=0` | sin saludo del líder al abrir |
| `CAOLG_KEEP=1` | cerrar la terminal no cierra la sesión |
| `CAOLG_WARN_AT` | % de contexto de Opus para avisar (default 50; 0 = sin aviso; acepta el viejo `CAOLG_CLEAR_AT`) |
| `CAOLG_CTX_WINDOW` | ventana de contexto para el cálculo de respaldo (default 1000000) |
| `CAOLG_TICK` | segundos entre refrescos de bordes y barra (default 10) |
| `CAO_USAGE_OVERRIDE` | JSON para simular cupos y probar la rotación: `CAO_USAGE_OVERRIDE='{"codex": 95}' cao-usage --json` |

## Permisos por provider

| Worker | Provider | Cómo se contiene |
|---|---|---|
| supervisor (líder) | `claude_code` | sin confirmaciones (`--dangerously-skip-permissions`), límites en su prompt, aislado en el worktree |
| claude-dev | `claude_code` | `permissionMode: auto` (aprueba lo seguro, frena lo riesgoso); MCP limitado a `send_message` al líder |
| codex-dev | `codex` | `codexProfile: cao-safe` (sin `--yolo`; `approval_policy=never` + `workspace-write`) |
| copilot-dev | `copilot_cli` | CAO fuerza `--allow-all --autopilot`: solo en el worktree |
| gemini-dev | `antigravity_cli` | CAO fuerza bypass de permisos: solo en el worktree |
| opencode-dev | `opencode_cli` | permisos allow/deny fijados al instalar (experimental) |

Nunca usar `cao launch --yolo` ni `allowedTools: ["*"]`. En repos git ningún agente corre en el checkout principal (siempre worktree). En carpetas sin git trabajan en la carpeta misma, sin red de seguridad de git: `claudes` pide confirmación si la carpeta es `~` o `/`.

## Decisiones

- [0001](docs/decisions/0001-cao-como-orquestador.md): CAO como orquestador y manejo de permisos.
- [0002](docs/decisions/0002-modo-paneles-con-marca.md): Opus y workers en la misma ventana (modo pane + marca). Depende de internals de CAO 2.5.4.
- [0003](docs/decisions/0003-mitad-derecha-como-tabs.md): la mitad derecha como tabs, un agente visible por vez.
- [0004](docs/decisions/0004-mcp-del-lider-sin-strict.md): los agentes de Claude usan tus MCP (sin `--strict-mcp-config`).

## Limitaciones conocidas

- opencode no expone cupo (`n/d`); si falta el registro del panel de Omarchy, agy también queda en `n/d`.
- Copilot y agy no tienen comando de login: se infiere por uso en los últimos 7 días (o `auth.toml`).
- El estado de agy y copilot a veces figura ◌ (CAO no lo detecta).
- **Sin probar**: muchas tabs a la vez y el cambio real de tema de Omarchy.

## Tests

```bash
python3 -m unittest discover tests
for f in bin/*; do head -1 "$f" | grep -q bash && bash -n "$f"; done
```

## Próximos pasos

`cao-server` como servicio `systemd --user`, limpieza automática de worktrees, keybind de Hyprland para `claudes open`.
