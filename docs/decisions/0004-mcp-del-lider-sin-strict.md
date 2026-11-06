# 0004 — Los agentes de Claude usan los MCP de Loren (sin --strict-mcp-config)

- Estado: aceptada (2026-11-06)

## Contexto

Si un perfil define `mcpServers`, CAO lanza Claude con `--mcp-config <solo esos> --strict-mcp-config`. El perfil `supervisor` definía `cao-mcp-server`, así que el líder perdía todos los conectores de claude.ai (Atlassian, GitHub, Slack, Gmail, Drive…) y los MCP de plugins. Para cargar un ticket en Jira, por ejemplo, tenía que abrir un worker. CAO 2.5.4 no deja pasar flags propios a `claude` (ADR 0002).

## Decisión

- `profiles/supervisor.md` no define `mcpServers`, y CAO deja de agregar `--strict-mcp-config`. El líder hereda los mismos MCP que un Claude abierto a mano, con los logins que ya existen.
- `install.sh` y `bin/cao-wt` registran `cao-mcp-server` con scope de usuario (`bin/caolg-mcp --ensure`). Claude le pasa el entorno al servidor, incluido `CAO_TERMINAL_ID`.
- `bin/caolg-mcp` decide según la API de CAO:
  - **Líder** (`agent_profile: supervisor`): el `cao-mcp-server` completo.
  - **Worker** (cualquier otra terminal de CAO): el mismo servidor detrás de un filtro que solo expone `send_message` sin `receiver_id`. El mensaje va siempre a quien le asignó la tarea, o sea al líder. Antes los workers de Claude no tenían `cao-mcp-server`, usaban el `SendMessage` propio de Claude y el resultado no le llegaba al líder.
  - **Fuera de CAO** (un Claude abierto a mano): un MCP vacío, sin herramientas ni errores.
- El prompt del líder trata cualquier escritura en esos conectores (crear, editar, comentar, enviar, mover) como acción hacia afuera: solo con el OK de Loren sobre el texto exacto.

## Consecuencias

- El líder corre con `--dangerously-skip-permissions` (ADR 0001), así que puede usar cualquier conector sin confirmación del sistema. El único freno es la regla de su prompt. Lo eligió Loren sobre la alternativa de una lista cerrada.
- Más contexto inicial: los nombres de las herramientas diferidas de cada conector.

## Alternativas descartadas

- Lista cerrada de servidores HTTP en el perfil, manteniendo strict: más control y menos contexto, pero cada servidor pide su propio login desde `/mcp`, y Loren prefirió tener todos.
- Scope local en la carpeta del líder (primera versión): no les llegaba a los workers que trabajan en otra carpeta. Con scope de usuario aparece en todas las sesiones de Claude, pero fuera de CAO no tiene herramientas.
- `mcpServers` en `claude-dev`: CAO le pondría strict al worker y perdería los conectores (el worker «jira» los usa).
