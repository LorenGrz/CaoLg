"""Funciones puras compartidas por los scripts de CaoLg (testeadas en tests/test_caolg.py)."""
import json
import os
import re
import tomllib
from pathlib import Path

THEME_COLORS = Path.home() / ".local/state/omarchy/current/theme/colors.toml"

# Colores por defecto (Catppuccin) si no hay tema de Omarchy.
DEFAULT_COLORS = {
    "accent": "#89b4fa", "background": "#1e1e2e", "foreground": "#cdd6f4",
    "muted": "#585b70", "red": "#f38ba8", "green": "#a6e3a1", "blue": "#89b4fa",
    "orange": "#fab387", "magenta": "#f5c2e7", "cyan": "#94e2d5", "yellow": "#f9e2af",
}

# provider de CAO -> (nombre corto, clave de color del tema)
PROVIDERS = {
    "claude_code": ("claude", "orange"),
    "codex": ("codex", "green"),
    "antigravity_cli": ("agy", "blue"),
    "opencode_cli": ("opencode", "magenta"),
    "copilot_cli": ("copilot", "cyan"),
}

# agente de ccusage -> nombre corto en la barra
USAGE_SHORT = {"claude": "claude", "codex": "codex", "antigravity": "agy",
               "opencode": "opencode", "copilot": "copilot"}

STATUS_ICON = {"processing": "●", "idle": "○", "completed": "○", "error": "✗",
               "waiting_user_answer": "⚠", "unknown": "◌"}


def load_colors(path=THEME_COLORS):
    """Paleta del tema actual; completa con los defaults lo que falte o si no hay archivo."""
    colors = dict(DEFAULT_COLORS)
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        colors.update({k: v for k, v in data.items() if isinstance(v, str) and v.startswith("#")})
    except (OSError, tomllib.TOMLDecodeError):
        pass
    return colors


def provider_short(provider):
    return PROVIDERS.get(provider, (provider or "?", "foreground"))[0]


def provider_color(provider, colors):
    return colors.get(PROVIDERS.get(provider, ("", "foreground"))[1], colors["foreground"])


def transcript_dir(cwd):
    """Carpeta de transcripts de Claude Code para un cwd (cada char no alfanumérico -> '-')."""
    return Path.home() / ".claude/projects" / re.sub(r"[^A-Za-z0-9]", "-", cwd)


def last_usage(jsonl_path):
    """(modelo, tokens de contexto) del último mensaje con usage, o (None, None)."""
    try:
        lines = Path(jsonl_path).read_text(errors="ignore").splitlines()
    except OSError:
        return None, None
    for line in reversed(lines):
        if '"usage"' not in line:
            continue
        try:
            msg = json.loads(line).get("message") or {}
        except json.JSONDecodeError:
            continue
        u = msg.get("usage") or {}
        tokens = sum(u.get(k) or 0 for k in
                     ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        return msg.get("model"), tokens
    return None, None


def opus_context_tokens(cwd):
    """Tokens de contexto del transcript de Opus más reciente en ese cwd (los workers usan otro modelo)."""
    d = transcript_dir(cwd)
    try:
        files = sorted(d.glob("*.jsonl"), key=os.path.getmtime, reverse=True)
    except OSError:
        return None
    for f in files[:10]:
        model, tokens = last_usage(f)
        if model and "opus" in model:
            return tokens
    return None


def human(n):
    if n is None:
        return "n/d"
    for div, suf in ((1_000_000, "M"), (1_000, "k")):
        if n >= div:
            return f"{n / div:.1f}{suf}"
    return str(n)


def pane_label(term, conductor_id):
    """Texto del borde del pane: 'Opus · líder' o '<rol> · <provider>'."""
    if term["id"] == conductor_id:
        return "Opus · líder"
    role = term.get("description") or term.get("agent_profile") or "?"
    return f"{role} · {provider_short(term.get('provider'))}"


def build_bar(session, ctx_pct, usage, colors, clear_at=30):
    """Línea 2 de la barra: agentes, contexto de Opus y usage (con estilos de tmux).
    El color del contexto es relativo al umbral del /clear automático: amarillo al 75%, rojo al llegar."""
    fg, muted = colors["foreground"], colors["muted"]
    terms = session.get("terminals", [])
    conductor = terms[0]["id"] if terms else None
    agents = []
    for t in terms[1:]:
        icon = STATUS_ICON.get(t.get("status"), "?")
        c = colors["red"] if t.get("status") == "error" else provider_color(t.get("provider"), colors)
        agents.append(f"#[fg={c}]{pane_label(t, conductor)}{icon}")
    left = " ".join(agents) if agents else f"#[fg={muted}](sin workers)"

    if ctx_pct is None:
        ctx = f"#[fg={muted}]Opus ctx n/d"
    else:
        limit = clear_at or 100
        c = (colors["red"] if ctx_pct >= limit else
             colors["yellow"] if ctx_pct >= limit * 0.75 else colors["green"])
        ctx = f"#[fg={c}]Opus ctx {ctx_pct}%"

    use = []
    for p in (usage or {}).get("providers", []):
        name = USAGE_SHORT.get(p["agent"], p["agent"])
        cost = "" if not p.get("cost_usd") else f" ${p['cost_usd']:.2f}"
        use.append(f"{name} {human(p.get('tokens'))}{cost}")
    usage_txt = " · ".join(use) if use else "usage n/d"

    sep = f"#[fg={muted}] │ "
    return f"#[fg={fg}] agentes: {left}{sep}{ctx}{sep}#[fg={muted}]{usage_txt} "
