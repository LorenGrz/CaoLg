# Plan S: varias sesiones caolg en la misma carpeta

## Contexto
`caolg` arma el nombre de la sesión con el nombre de la carpeta (`cao-cx`). Si esa sesión ya está abierta, la segunda vez se suma a ella. Loren quiere que funcione como `claude`: **cada `caolg` abre una sesión nueva e independiente**, para trabajar en dos módulos del mismo proyecto a la vez. Si dos sesiones tocan el mismo repo, los workers de la que llega segunda usan un **worktree propio, automático**.

## Cambios (repo `~/projects/caolg`)

1. **`bin/caolg`**: nueva función `free_slug`, que se llama solo en `launch`. Si `cao-<slug>` existe y tiene terminales conectadas (`#{session_attached}` > 0), prueba `<slug>-2`, `-3`… hasta encontrar uno libre. Una sesión vieja sin terminales sigue cerrándose y se reusa su nombre, como hoy.
   - Modo repo: `<repo>-2` usa su propio worktree `<repo>-wt/<repo>-2` (rama `agent/<repo>-2`). Eso ya lo hace `cao-wt`.
   - Modo carpeta (`cx`): el líder trabaja en la misma carpeta, igual que dos `claude`.
   - `caolg rm` sin argumentos sigue usando el nombre base (no llama a `free_slug`).
   - Actualizar el comentario de ayuda: "cada `caolg` abre una sesión nueva; para volver a una existente: `caolg ls` + Alt+↑/↓".
   - `cao-open` no cambia: recibe un nombre que ya está libre.
2. **`bin/caolg-workdir`** (nuevo, ~20 líneas): `caolg-workdir <carpeta>` devuelve la carpeta donde lanzar al worker.
   - Toma la sesión propia con `tmux display -p '#S'`.
   - Si algún pane de **otra** sesión `cao-*` tiene su cwd dentro de `<carpeta>` (`tmux list-panes -a -F '#S #{pane_current_path}'`), crea o reusa `<carpeta>-wt/<slug>` con `git fetch origin && git worktree add --detach <wt> origin/dev`, agrega `.caolg-tasks/` al exclude y devuelve esa ruta.
   - Si no, devuelve `<carpeta>`.
   - Si la carpeta no es un repo git, devuelve la carpeta tal cual.
3. **`profiles/supervisor.md`**:
   - Tareas en `.caolg-tasks/<sesión>/<rol>-<n>.md`, para que dos líderes en `cx` no choquen.
   - `working_directory` = salida de `caolg-workdir <Carpeta del rol>`, en vez de la `Carpeta:` directa. Si devuelve un worktree, avisarle a Loren en una línea.
   - La regla "worktree aparte, preguntando" pasa a ser automática solo en este caso.
4. **ADR `docs/decisions/0006-sesiones-paralelas.md`**: modifica el ADR 0005 (el worktree automático cuando otra sesión ya ocupa el repo). Actualizar también `README.md` y `AGENTS.md` (comandos y nuevo script).
5. **`install.sh`**: si enlaza los scripts de `bin/` uno por uno, agregar `caolg-workdir`.

Limpieza: los worktrees `<repo>-wt/<slug>` de los workers no se borran solos. Se reusan la próxima vez con el mismo nombre de sesión y se borran a mano con `git worktree remove`, como pasa hoy con los del líder. Queda documentado.

## Verificación
- `python3 -m unittest discover tests` y `bash -n bin/caolg bin/caolg-workdir`.
- Manual en `~/work/reino/cx`:
  - abrir `caolg` dos veces y comprobar que aparecen `cao-cx` y `cao-cx-2` en `caolg ls`;
  - en `cx-2`, `caolg-workdir /home/loren/work/reino/cx/cx-reino-backend` con un worker de `cx` parado ahí → devuelve `cx-reino-backend-wt/cx-2`;
  - sin worker de otra sesión ahí → devuelve la carpeta original.
- Commit y push a `main`, según el `AGENTS.md` del repo.

Plan S porque son pocos archivos y el diseño ya quedó decidido (nombre automático, worktree automático); falta acordar solo los detalles de ejecución.
