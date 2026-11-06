# 0007 — agy sin cupo en la barra (n/d)

Fecha: 2026-11-06 · Estado: aceptada

## Contexto

La barra mostraba `agy 7d 0%` aunque ese día se habían usado ~5,9 M de tokens de `gemini-3.8-flash-high`. La
respuesta cruda de Google (`retrieveUserQuotaSummary`, la que pide el panel de agentes de Omarchy) trae un solo
grupo, "Claude and GPT models" (bucket `3p-weekly`, `remainingFraction: 1`): para los modelos Gemini del plan
Free no hay ventana de cupo. El colector de Omarchy, al no encontrar el grupo Gemini, toma `groups[0]` y lo
publica como el cupo semanal de agy. Ese 0% es el cupo de Claude/GPT dentro de Antigravity, no el de Gemini.

## Decisión

- `cao-usage` ignora los límites de Omarchy para agy (`QUOTA_NOT_REPORTED` en `lib/caolg_lib.py`): la barra
  muestra `agy n/d`. Desde el JSON de Omarchy no se puede saber de qué grupo vino el número.
- Orden de la barra: claude, codex, copilot (cupo real) y después agy, opencode (n/d).

## Consecuencias

- Si Google empieza a informar el cupo de Gemini (u Omarchy deja de caer en `groups[0]`), hay que sacar agy de
  `QUOTA_NOT_REPORTED` a mano.
- La rotación por cupo del líder no tiene número para agy: lo trata como "sin datos".
- Pendiente: reportarlo a Omarchy, con el OK de Loren sobre el texto.
