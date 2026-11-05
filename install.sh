#!/usr/bin/env bash
# Instala perfiles de CAO, el perfil seguro de Codex y enlaza bin/* en ~/.local/bin.
# No copia ni toca credenciales: los logins quedan en ~/.claude, ~/.codex, ~/.copilot, ~/.gemini.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)

command -v cao >/dev/null || { echo "Falta cao: uv tool install cli-agent-orchestrator" >&2; exit 1; }

mkdir -p "$HOME/.local/bin"
for f in "$here"/bin/*; do ln -sfn "$f" "$HOME/.local/bin/$(basename "$f")"; done

ln -sfn "$here/codex/cao-safe.config.toml" "$HOME/.codex/cao-safe.config.toml"

for p in supervisor claude-dev codex-dev gemini-dev; do
  cao install "$here/profiles/$p.md"
done
cao install "$here/profiles/copilot-reviewer.md" --provider copilot_cli
cao install "$here/profiles/opencode-dev.md" --provider opencode_cli

echo "Listo. Levantá el servidor (cao-server) y lanzá: cao-wt <repo> <slug>"
