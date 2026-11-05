# Plan: CaoLg visual — Opus fijo + workers al lado, barra con agentes/usage, tema Omarchy, /clear, roles por carpeta

## Context
CaoLg (`~/projects/caolg`, `LorenGrz/CaoLg`) ya lanza una sesión CAO por worktree, con un líder Opus y workers multi-provider, cada uno en una ventana tmux. Loren quiere que se parezca a un IDE:
- Opus siempre visible a la izquierda y los workers al lado, como paneles reales e interactivos.
- Cuando no entran más workers, que pasen a ventanas, visibles como tabs horizontales.
- Una barra con los agentes abiertos y su estado, más el usage de todas las suscripciones.
- Un color por provider y colores que sigan el tema de Omarchy.
- `/clear` de Opus con resumen previo, por atajo y también automático.
- Roles por carpeta (front, back, reviewer…) que escribe Opus. Opus también redacta cada tarea y elige la CLI que la ejecuta.

## Hallazgos que definen el diseño (CAO 2.5.4, leído del código)
- **Modo paneles nativo.** CAO tiene `terminal.spawn_mode=pane`. Los workers se suman como panes a la ventana `terminal.pane_window`. Si no entran, CAO crea una ventana aparte: esas son las tabs (`clients/tmux.py`, `create_pane`).
- **Cómo encuentra cada terminal.** Primero busca una ventana con su nombre y, si no existe, el pane que tiene la marca `@cao_terminal=<nombre>` en toda la sesión (`_resolve_pane`, `_send_target`). Por eso a Opus se le puede poner la marca en su pane y renombrar su ventana al nombre de la ventana anfitriona: los workers se suman al lado de Opus y CAO lo sigue encontrando.
- **Tema de Omarchy.** Los colores están en `~/.local/state/omarchy/current/theme/colors.toml` (`accent`, `background`, `foreground`, `red`, `green`, `blue`, `orange`, `magenta`, `cyan`, `muted`…). Hay un hook `omarchy hook install theme-set <script>` que corre cuando cambia el tema.
- **Contexto de Opus.** Se puede leer del transcript `~/.claude/projects/<cwd codificado>/*.jsonl`: el último `usage` da `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`. Lo verifiqué con la sesión de prueba (~61k tokens).
- **Atajos con Alt.** Ya están en `~/.config/tmux/tmux.conf`: `Alt+1..9` ventana, `Alt+←/→` ventana anterior o siguiente, `Alt+↑/↓` sesión.

## Layout objetivo
```
 1:caolg●  2:extra(codex)          ~/projects/roadmap-wt/demo (agent/demo)
┌─ Opus · líder ─────────┬─ front · agy ─────────┐
│ > ...                  │ trabajando…           │
│                        ├─ back · codex ────────┤
│                        │                       │
├────────────────────────┴───────────────────────┤
 agentes: front(agy)● back(codex)○ │ Opus ctx 42% │ claude 25.8M $13.6 · codex 0 · agy n/d
```

## Cambios

1. **Fijar CAO y configurar el modo paneles.** Pinear con `uv tool install cli-agent-orchestrator==2.5.4`, porque el truco de la marca depende de su código. Configurar con `cao config set`: `terminal.spawn_mode pane`, `terminal.pane_window caolg` y `terminal.pane_layout none` (el layout lo maneja CaoLg). Después reiniciar `cao-server`. Todo queda en `install.sh`.

2. **`bin/caolg-session <session>`.** Lo lanza `cao-wt` en segundo plano en lugar del bloque actual de barra y saludo. Pasos:
   - Espera a que exista la sesión y toma el pane de Opus, que es el único.
   - Copia `@cao_terminal` (el nombre de su ventana) y `@cao_terminal_id` (que está en la ventana) al pane, y renombra la ventana a `caolg`.
   - Instala el hook de sesión `after-split-window` → `caolg-layout`.
   - Aplica `caolg-theme <session>` y manda el saludo (`CAO_WT_GREET`).
   - Arranca el watcher (`caolg-watch`), que termina solo cuando la sesión deja de existir.

3. **`bin/caolg-layout <session>`.** Aplica `select-layout main-vertical` con `main-pane-width 55%` y Opus como pane principal. Pone `pane-border-status top` con un borde que muestra rol y provider, coloreado según la marca:
   - Opus: color `accent`.
   - `claude-*`: `orange`.
   - `codex-*`: `green`.
   - `gemini-*`: `blue`.
   - `opencode-*`: `magenta`.
   - `copilot-*`: `cyan`.

   El rol sale de la `description` del `assign`.

4. **`bin/caolg-theme [<session>|--all]`** (python3, `tomllib`). Lee `colors.toml` y fija opciones de sesión en tmux: `@caolg_c_<provider>`, `status-style`, el formato de las tabs con color por provider y los bordes. Los formatos de 2 y 3 referencian esas variables, así que un cambio de tema solo actualiza variables. `bin/caolg-theme-hook` corre `caolg-theme --all`, y `install.sh` lo registra con `omarchy hook install theme-set`. Si `colors.toml` no existe, usa colores por defecto.

5. **Barra de 2 líneas (solo sesiones `cao-*`).**
   - **Línea 1:** tabs de ventanas, más carpeta y rama a la derecha.
   - **Línea 2:** `status-format[1]` = `#(cat ~/.cache/caolg/<session>.bar)`. Contiene los agentes abiertos con su rol, provider y estado (● trabajando, ○ idle), el `Opus ctx %` y el usage resumido.
   - **`bin/caolg-watch <session>`** escribe ese archivo:
     - Cada 10 s lee `cao session status <s> --workers`. Su formato exacto lo verifico al implementar.
     - Cada 60 s corre `cao-usage --json`.
     - Calcula el % de contexto con el transcript. El tamaño de la ventana de contexto se configura con `CAOLG_CTX_WINDOW` (default 200000); lo verifico con `/context`.

6. **Atajos (solo en sesiones `cao-*`).** Se aplican en tiempo de ejecución con `tmux bind` y `if -F "#{m:cao-*,#{session_name}}"`, así que fuera de CaoLg los atajos siguen como están y no hace falta editar `tmux.conf`:
   - `Alt+1..9`: ir al pane N (Opus es el 1).
   - `Alt+z`: zoom del pane.
   - `Alt+c`: `/clear` con resumen.
   - `Alt+←/→`: tabs, sin cambios.

7. **`/clear` con resumen: `bin/caolg-clear <session>`.**
   - Primero manda a Opus, de forma bloqueante con `cao session send`: "Escribí el estado (objetivo, decisiones, workers abiertos y su tarea, próximos pasos) en `$CAOLG_STATE`".
   - Después manda `/clear` + Enter al pane de Opus con `tmux send-keys`.
   - Por último manda "Leé `$CAOLG_STATE` y retomá".
   - **Disparadores:**
     - **Manual:** `Alt+c`.
     - **Automático:** `caolg-watch` lo dispara cuando `ctx ≥ CAOLG_CLEAR_AT` (60%) y Opus está idle, con un enfriamiento de 10 minutos.

8. **Roles por carpeta, fuera del repo** (no ensucian el proyecto y sobreviven a los worktrees).
   - Viven en `~/.local/share/caolg/<repo>/agents/*.md` y el estado en `~/.local/share/caolg/<repo>/<slug>/state.md`.
   - `cao-wt` pasa `--env CAOLG_ROLES_DIR=… --env CAOLG_STATE=…`.
   - **`profiles/supervisor.md`:**
     - Al presentarse, si no hay roles en la carpeta, lee el repo y crea los que tengan sentido (front, back, reviewer…).
     - En cada tarea elige rol + worker de provider, manda el contenido del rol más la tarea, y pone `description: "<rol>"` en el `assign`.
     - Anuncia el pane (`Alt+N`).
   - **Workers genéricos por provider:** `claude-dev`, `codex-dev`, `gemini-dev`, `opencode-dev` y `copilot-dev`. `copilot-reviewer` pasa a `copilot-dev` con `role: developer`, y en todos los prompts el rol viene en la tarea.

9. **Docs y tests.**
   - Actualizar `README` (layout y atajos), `AGENTS.md`, `.agents/CONTEXT.md` y copiar este plan a `docs/superpowers/plans/2026-11-05-caolg-visual.md`.
   - ADR `0002-modo-paneles-con-marca.md`: depende de internals de CAO, versión pineada, y el fallback es el modo paneles puro (Opus en su ventana y los workers en otra).
   - `tests/test_caolg.py` (`python3 -m unittest`): cálculo del % de contexto con un `.jsonl` de muestra, armado de la línea de la barra y lectura de `colors.toml`.

## Ejecución
Inline en la sesión principal, por pasos, probando cada uno en una sesión `cao-*` real. Es trabajo iterativo contra tmux y CAO en vivo, y un `worker` no puede ver la pantalla. Commit por paso y push a `main` al final.

## Verificación
- `python3 -m unittest discover tests` y `bash -n bin/*` pasan.
- `caolg open ~/projects/roadmap demo2` abre la terminal. Opus queda a la izquierda, con su borde en color accent, y la barra muestra 2 líneas con carpeta y rama.
- Al pedirle "abrí un worker front con agy y uno back con codex", aparecen 2 panes a la derecha con borde y color por provider. Opus sigue respondiendo; esto prueba que el truco de la marca funciona y que CAO le entrega mensajes. `Alt+2` y `Alt+3` llevan a esos panes y se puede escribir en ellos.
- Con más workers que lugar, el que no entra aparece como tab nueva arriba.
- La línea 2 muestra los agentes con ●/○, `Opus ctx %` y el usage. Se actualiza en ≤10 s.
- `omarchy theme set <otro>` cambia los colores de la sesión abierta sin reiniciarla.
- `Alt+c` escribe `state.md`, limpia Opus (el % de contexto baja) y Opus retoma leyendo el estado. Con `CAOLG_CLEAR_AT=1` se dispara solo.
- En un repo sin roles, Opus crea `~/.local/share/caolg/<repo>/agents/*.md` al presentarse.
- Fuera de CaoLg, en una sesión tmux normal, `Alt+1` sigue cambiando de ventana.
