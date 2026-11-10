# 0010 — Providers de workers según la organización del repo

Fecha: 2026-11-10 · Estado: aceptada

## Contexto

En los repos del trabajo Loren solo puede usar agentes Claude; en los personales quiere que el líder reparta entre
Claude, Codex, Gemini/agy, Copilot y OpenCode. caolg es público: no puede nombrar organizaciones.

## Decisión

- La org declara `agent_providers` (providers de CAO) en su `org.json` de agents-config.
- `bin/caolg-providers <carpeta>` toma el remote de la carpeta (o de los repos justo debajo), detecta la org con
  `agents-config/scripts/orgs.sh detect` y lista los perfiles `*-dev` cuyo `provider:` está permitido (intersección
  si hay varias orgs). Sin agents-config o sin el campo: todos.
- El líder lo corre antes de cada `assign`/`handoff` y no sale de esa lista, aunque el ruteo o el cupo prefieran otro.

## Consecuencias

- Una org nueva con restricción se configura en su `org.json`, sin tocar caolg.
- Es una regla del prompt del líder, no un bloqueo técnico: CAO puede abrir cualquier perfil.
- Depende de que agents-config esté en `~/projects/agents-config` (o `CAOLG_AGENTS_CONFIG`).
