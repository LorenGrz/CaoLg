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


def opus_context_tokens(cwd, since=0.0):
    """Tokens de contexto del transcript de Opus más reciente en ese cwd (los workers usan otro modelo).
    `since` (epoch): ignora transcripts anteriores al último /clear; si no hay ninguno posterior, el
    contexto está recién limpio -> 0 (así el /clear automático no se vuelve a disparar sobre el viejo)."""
    d = transcript_dir(cwd)
    try:
        files = sorted(d.glob("*.jsonl"), key=os.path.getmtime, reverse=True)
    except OSError:
        return None
    if since:
        files = [f for f in files if os.path.getmtime(f) > since]
        if not files:
            return 0
    for f in files[:10]:
        model, tokens = last_usage(f)
        if model and "opus" in model:
            return tokens
    return 0 if since else None


def short_model(name):
    """'claude-opus-5-5' -> 'opus', 'claude-sonnet-5-5' -> 'sonnet'; el resto tal cual."""
    for k in ("opus", "sonnet", "haiku", "fable"):
        if k in (name or ""):
            return k
    return name or "?"


def claude_costs_for_path(sessions_json, cwd):
    """Costo exacto por modelo (opus/sonnet…) de las sesiones de Claude Code cuyo cwd es `cwd`."""
    encoded = transcript_dir(cwd).name
    costs = {}
    for s in (sessions_json or {}).get("sessions", []):
        if s.get("projectPath") != encoded:
            continue
        for m in s.get("modelBreakdowns") or []:
            k = short_model(m.get("modelName"))
            costs[k] = costs.get(k, 0.0) + (m.get("cost") or 0.0)
    return costs


def cost_since(sessions_json, since_iso):
    """Costo de las sesiones con actividad desde `since_iso` (ISO UTC). Aproximado: providers sin ruta."""
    total = 0.0
    for s in (sessions_json or {}).get("sessions", []):
        last = s.get("lastActivity") or s.get("firstActivity") or ""
        if last and last >= since_iso:
            total += s.get("totalCost") or s.get("costUSD") or 0.0
    return total


def session_cost_text(costs, colors):
    """'sesión $1.69 (opus 1.23 · sonnet 0.40 · agy≈0.06)' con estilos de tmux. costs: {nombre: (usd, exacto)}."""
    if not costs:
        return f"#[fg={colors['muted']}]sesión $0.00"
    total = sum(v for v, _ in costs.values())
    parts = [f"{k}{'' if exact else '≈'}{v:.2f}" for k, (v, exact) in costs.items() if v >= 0.005]
    detail = f" #[fg={colors['muted']}]({' · '.join(parts)})" if parts else ""
    return f"#[fg={colors['yellow']},bold]sesión ${total:.2f}#[nobold]{detail}"


def human(n):
    if n is None:
        return "n/d"
    for div, suf in ((1_000_000, "M"), (1_000, "k")):
        if n >= div:
            return f"{n / div:.1f}{suf}"
    return str(n)


def pane_label(term, conductor_id, role=None):
    """Texto del borde del pane: 'Opus · líder' o '<rol> · <provider>'. `role` pisa el de CAO (Alt+i)."""
    if term["id"] == conductor_id:
        return "Opus · líder"
    role = role or term.get("description") or term.get("agent_profile") or "?"
    return f"{role} · {provider_short(term.get('provider'))}"


# ── Tabs de la mitad derecha (bin/caolg-tabs) ──────────────────────────────

def tab_key(pos):
    """Tecla Alt de la tab en la posición `pos` (0 = primera tab): Alt+2..9 y Alt+0. Más allá, sin tecla."""
    return str(pos + 2) if pos < 8 else ("0" if pos == 8 else "")


def key_to_pos(key):
    """Inversa de tab_key: '2' -> 0 … '9' -> 7, '0' -> 8. '1' (Opus) o inválida -> None."""
    if key == "0":
        return 8
    return int(key) - 2 if key.isdigit() and 2 <= int(key) <= 9 else None


def assign_tabs(tabs):
    """Numera las tabs que no tienen número (las nuevas van al final, en el orden dado).
    tabs: [{'id', 'tab': int|None}]. Devuelve {id: número} solo de las nuevas."""
    nxt = max((t["tab"] for t in tabs if t["tab"] is not None), default=0) + 1
    new = {}
    for t in tabs:
        if t["tab"] is None:
            new[t["id"]] = nxt
            nxt += 1
    return new


# Cada tab nueva toma el siguiente color (por número de tab), así dos workers del mismo provider no se confunden.
# "accent" queda reservado para Opus.
TAB_PALETTE = ("orange", "green", "blue", "magenta", "cyan", "yellow", "red")


def tab_color_key(n):
    """Clave de color (del tema) para la tab número `n` (1, 2, 3…): recorre TAB_PALETTE en ronda.
    Se guarda la clave y no el hex para que siga al tema de Omarchy."""
    return TAB_PALETTE[(max(n, 1) - 1) % len(TAB_PALETTE)]


def tab_color(key, colors):
    """Hex de una clave de TAB_PALETTE (o un hex suelto de sesiones viejas)."""
    if key and key.startswith("#"):
        return key
    return colors.get(key or "", colors["muted"])


def owner_marks(rows, leader=None):
    """A qué pane pertenece cada marca de CAO (@cao_terminal / @cao_terminal_id).

    CAO marca al supervisor con una opción de VENTANA y a los workers en panes con una de PANE. En los
    formatos de tmux la de ventana se hereda a todos los panes, así que una terminal suelta en la ventana
    de Opus "parece" Opus (y cerrarla con Alt+Esc borraba a Opus vía CAO). Esto lo desambigua:
    rows: [{'id', 'win', 'own', 'inherited'}] en orden de pane_index ('own' = valor propio del pane).
    La marca de ventana es del líder si está en esa ventana; si no, del primer pane de la ventana.
    Devuelve {pane_id: marca} solo de los panes que la tienen de verdad."""
    out, taken = {}, set()
    for r in rows:
        if r.get("own"):
            out[r["id"]] = r["own"]
    for r in rows:
        mark = r.get("inherited")
        if not mark or r.get("own") or r["win"] in taken:
            continue
        in_win = [x for x in rows if x["win"] == r["win"] and not x.get("own")]
        owner = leader if any(x["id"] == leader for x in in_win) else in_win[0]["id"]
        out[owner] = mark
        taken.add(r["win"])
    return out


def pick_visible(candidates):
    """Entre las tabs que quedaron en la ventana caolg, cuál se ve: la más nueva (número más alto).
    Así una tab recién abierta (Alt+Enter o un worker de Opus) aparece al toque."""
    return max(candidates, key=lambda c: c["tab"])["id"] if candidates else None


def tab_strip(tabs, visible_id, colors):
    """Formato tmux del borde superior de la mitad derecha: ' 2 front · agy  3 zsh '.
    tabs: [{'id', 'label', 'color'}] ya ordenadas. La visible va resaltada con el color de su provider."""
    parts = []
    for pos, t in enumerate(tabs):
        key = tab_key(pos)
        txt = f" {key} {t['label']} " if key else f" {t['label']} "
        c = t.get("color") or colors["muted"]
        if t["id"] == visible_id:
            parts.append(f"#[fg={colors['background']},bg={c},bold]{txt}#[default]")
        else:
            parts.append(f"#[fg={c}]{txt}#[default]")
    return "".join(parts)


def build_bar(session, ctx_pct, usage, colors, clear_at=30, session_costs=None, roles=None, tab_colors=None):
    """Línea 2 de la barra: agentes, contexto de Opus y usage (con estilos de tmux).
    El color del contexto es relativo al umbral del /clear automático: amarillo al 75%, rojo al llegar."""
    fg, muted = colors["foreground"], colors["muted"]
    terms = session.get("terminals", [])
    conductor = terms[0]["id"] if terms else None
    agents = []
    for t in terms[1:]:
        icon = STATUS_ICON.get(t.get("status"), "?")
        c = (colors["red"] if t.get("status") == "error" else
             (tab_colors or {}).get(t["id"]) or provider_color(t.get("provider"), colors))
        agents.append(f"#[fg={c}]{pane_label(t, conductor, (roles or {}).get(t['id']))}{icon}")
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
        if p.get("logged_in") is False:  # el líder no lo usa hasta que Loren se loguee
            use.append(f"#[fg={muted},strikethrough]{name}#[nostrikethrough] sin login#[fg={fg}]")
            continue
        cost = "" if not p.get("cost_usd") else f" ${p['cost_usd']:.2f}"
        use.append(f"{name} {human(p.get('tokens'))}{cost}")
    usage_txt = "hoy: " + " · ".join(use) if use else "hoy: usage n/d"

    sep = f"#[fg={muted}] │ "
    cost = session_cost_text(session_costs, colors) + sep if session_costs is not None else ""
    return f"#[fg={fg}] agentes: {left}{sep}{ctx}{sep}{cost}#[fg={muted}]{usage_txt} "
