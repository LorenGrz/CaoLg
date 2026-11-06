# 0004 — El líder usa los MCP de Loren (sin --strict-mcp-config)

- Estado: aceptada (2026-11-06)

## Contexto

Si un perfil define `mcpServers`, CAO lanza Claude con `--mcp-config <solo esos> --strict-mcp-config`. El perfil `supervisor` definía `cao-mcp-server`, así que el líder perdía todos los conectores de claude.ai (Atlassian, GitHub, Slack, Gmail, Drive…) y los MCP de plugins. Para cargar un ticket en Jira, por ejemplo, tenía que abrir un worker. CAO 2.5.4 no deja pasar flags propios a `claude` (ADR 0002).

## Decisión

- `profiles/supervisor.md` no define `mcpServers`, y CAO deja de agregar `--strict-mcp-config`. El líder hereda los mismos MCP que un Claude abierto a mano, con los logins que ya existen.
- `bin/cao-wt` registra `cao-mcp-server` con scope local en la carpeta del líder (`claude mcp add -s local`), apuntando a `bin/caolg-mcp`. Claude le pasa el entorno al servidor, incluido `CAO_TERMINAL_ID`.
- `bin/caolg-mcp` ejecuta el `cao-mcp-server` de CAO solo si `CAO_TERMINAL_ID` es de un líder (la API de CAO dice `agent_profile: supervisor`). En los demás casos responde como un MCP vacío: un worker de Claude en la misma carpeta o un Claude abierto a mano ahí no ganan herramientas de CAO ni muestran errores.
- El prompt del líder trata cualquier escritura en esos conectores (crear, editar, comentar, enviar, mover) como acción hacia afuera: solo con el OK de Loren sobre el texto exacto.

## Consecuencias

- El líder corre con `--dangerously-skip-permissions` (ADR 0001), así que puede usar cualquier conector sin confirmación del sistema. El único freno es la regla de su prompt. Lo eligió Loren sobre la alternativa de una lista cerrada.
- Más contexto inicial: los nombres de las herramientas diferidas de cada conector.

## Alternativas descartadas

- Lista cerrada de servidores HTTP en el perfil, manteniendo strict: más control y menos contexto, pero cada servidor pide su propio login desde `/mcp`, y Loren prefirió tener todos.
- `cao-mcp-server` con scope de usuario: aparecería en todas las sesiones de Claude, no solo en las carpetas de caolg.
