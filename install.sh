#!/usr/bin/env bash
# Instala CaoLg: CAO pineado + modo pane, perfiles, perfil seguro de Codex, bin/* en ~/.local/bin
# y hook de tema de Omarchy. No copia ni toca credenciales (~/.claude, ~/.codex, ~/.copilot, ~/.gemini).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
CAO_VERSION=2.5.4   # el truco de la marca (ADR 0002) depende de internals de esta versión

if ! cao -V 2>/dev/null | grep -q "$CAO_VERSION"; then
  uv tool install "cli-agent-orchestrator==$CAO_VERSION"
fi
# Parches locales a CAO (idempotente; ADR 0006). Si CAO cambió de formato, avisa y no toca nada.
"$here/bin/caolg-patch-cao" || echo "caolg-patch-cao: sin aplicar, ver ADR 0006" >&2

# Modo pane: los workers se suman como panes a la ventana "caolg" (donde caolg-session deja a Opus).
cao config set terminal.spawn_mode pane >/dev/null
cao config set terminal.pane_window caolg >/dev/null
cao config set terminal.pane_layout none >/dev/null   # el layout lo maneja caolg-layout

mkdir -p "$HOME/.local/bin"
for f in "$here"/bin/*; do [[ -f "$f" ]] && ln -sfn "$f" "$HOME/.local/bin/$(basename "$f")"; done
ln -sfn "$here/bin/caolg" "$HOME/.local/bin/claudes"   # alias corto

# Copia (no symlink): Codex escribe su propio estado en este archivo y ensuciaría el repo.
rm -f "$HOME/.codex/cao-safe.config.toml"
cp "$here/codex/cao-safe.config.toml" "$HOME/.codex/cao-safe.config.toml"

for p in supervisor claude-dev codex-dev gemini-dev; do
  cao install "$here/profiles/$p.md"
done
cao install "$here/profiles/copilot-dev.md" --provider copilot_cli
cao install "$here/profiles/opencode-dev.md" --provider opencode_cli
# cao-mcp-server de los agentes de Claude, con scope de usuario (ver bin/caolg-mcp y ADR 0004).
"$here/bin/caolg-mcp" --ensure || echo "no pude registrar cao-mcp-server en Claude" >&2

# Perfil viejo renombrado a copilot-dev.
rm -f "$HOME/.copilot/agents/copilot-reviewer.agent.md" \
      "$HOME/.aws/cli-agent-orchestrator/agent-context/copilot-reviewer.md"

if command -v omarchy >/dev/null; then
  omarchy hook install theme-set "$here/omarchy/50-caolg-theme"
fi

echo "Listo. Reiniciá cao-server si estaba corriendo (toma la config de modo pane) y abrí: caolg open <repo> <slug>"
