# cao-config

Configuración personal de CAO (orquestador multi-CLI). Ver `README.md` para uso.

## Mapa

- `profiles/*.md`: perfiles de agentes de CAO (frontmatter YAML + prompt). Se instalan con `install.sh`.
- `codex/cao-safe.config.toml`: perfil de Codex sin `--yolo`.
- `bin/cao-wt`, `bin/cao-ls`, `bin/cao-usage`: scripts que se enlazan en `~/.local/bin`.
- `docs/decisions/`: ADRs. `docs/superpowers/plans/`: planes aprobados.

## Reglas

- Repo público: nunca secretos ni copias de `~/.claude`, `~/.codex`, `~/.copilot`, `~/.gemini`.
- Nunca `cao launch --yolo` ni `allowedTools: ["*"]`.
- Verificar con: `bin/cao-usage --json | python3 -m json.tool` y `bash -n bin/cao-wt bin/cao-ls install.sh`.
