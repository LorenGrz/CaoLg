# 0001 — CAO como orquestador multi-CLI

- Estado: aceptada (2026-11-05)

## Contexto

Se quiere el flujo de Orca en terminal, liviano, reutilizando el login nativo de cada suscripción (Claude Pro, Copilot, Codex, Google/Antigravity, OpenCode). Anthropic indica que apps de terceros deben usar API keys; lanzar el binario oficial `claude` como proceso externo mantiene su sesión propia.

## Decisión

Usar CAO (awslabs/cli-agent-orchestrator): lanza cada CLI real en tmux con su autenticación nativa. Descartados: Crush/Hermes (usan providers por API, no el login de suscripción), TUI propia (más costo ahora; se puede construir luego sobre la API HTTP de CAO).

Se agrega encima: `cao-wt` (CAO no crea worktrees), `cao-usage` (uso global vía `ccusage`) y perfiles con supervisor Opus que rota workers por dificultad y cupo.

## Permisos (trade-off)

CAO lanza por defecto sus agentes sin pedir permisos. Se contiene así: el líder (supervisor, Opus) corre sin confirmaciones por pedido explícito de Loren (2026-11-05), con límites en su prompt y aislado en el worktree; `claude-dev` con `permissionMode: acceptEdits`; Codex con `codexProfile: cao-safe`; Copilot y Antigravity no permiten apagar el bypass, por lo que solo corren en worktrees aislados; OpenCode con `allowedTools` acotado. Esto reemplaza la práctica base de "aprobar acciones" con aislamiento por worktree + revisión de `git diff` antes de mergear.

Actualización 2026-11-05: el layout tipo IDE (Opus + workers en la misma ventana) se decidió en el ADR 0002; el líder pasó a `role: developer` para poder escribir roles, tareas y su estado.

## Consecuencias

- Los workers de Copilot y Antigravity pueden ejecutar comandos sin confirmación dentro de su worktree.
- El cupo (%) no es legible de forma fiable; la rotación usa tokens/costo y override manual.
