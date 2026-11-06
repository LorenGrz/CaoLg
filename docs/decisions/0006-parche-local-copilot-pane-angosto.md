# 0006 — Parche local a CAO: Copilot en un pane angosto

Fecha: 2026-11-06 · Estado: aceptada

## Contexto

Un worker de Copilot falló al iniciar: `Copilot initialization timed out after 60 seconds`. Copilot había
arrancado bien (MCP conectado, prompt listo), pero CAO 2.5.4 detecta "listo" buscando la barra inferior completa
(`← open sidebar · … · / commands`). En la mitad derecha de caolg el pane tiene ~56 columnas y Copilot 1.0.106
la recorta a `Autopilot · Allow All · / … copilot-dev · Copilot Fus…`, que no coincide. Pasando la pantalla real
del fallo por el detector de CAO: recortada = no lista; con la barra completa = lista. La misma detección se usa
después (fin de turno, entrega de mensajes), así que lanzar el worker en una ventana ancha no alcanza.

## Decisión

Parche local mínimo: `COPILOT_HINT_BAR_PATTERN` también acepta la barra recortada
(`^(?:autopilot|interactive|plan) · … · /`). La caja del composer se sigue exigiendo igual, así que no reconoce
"listo" en otra parte de la pantalla. Vive en `lib/cao_patches.py` (puro, con test) y lo aplica `bin/caolg-patch-cao`
desde `install.sh`: idempotente, y si el archivo de CAO no tiene el formato esperado no toca nada y avisa.

## Consecuencias

- Hay que reiniciar cao-server para que lo tome (pasa solo al cerrar la última terminal de caolg y volver a abrir).
- Al subir CAO de versión, revisar si upstream ya lo resolvió y sacar el parche.
- Pendiente: reportarlo upstream (awslabs/cli-agent-orchestrator), con el OK de Loren sobre el texto.
