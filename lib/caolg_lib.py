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


def ctx_from_statusline(data):
    """% de contexto que guarda la statusline de Claude Code por terminal de CAO (o None)."""
    try:
        return round(float((data or {})["used_percentage"]))
    except (KeyError, TypeError, ValueError):
        return None


def cwd_from_statusline(data):
    """Carpeta actual de la sesión de Claude (sigue los `cd` del agente, CAO no) según la statusline, o None."""
    cwd = (data or {}).get("cwd")
    return cwd if isinstance(cwd, str) and cwd else None


def where_label(path, branch=None, max_branch=28):
    """'wt-front-monitor (fix/monitor-ver…)': carpeta (raíz del repo si es git) y rama recortada. '' sin carpeta."""
    name = os.path.basename((path or "").rstrip("/"))
    if not name:
        return ""
    if not branch:
        return name
    if len(branch) > max_branch:
        branch = branch[: max_branch - 1] + "…"
    return f"{name} ({branch})"


def ctx_warning(pct, warn_at):
    """Aviso para el borde de Opus cuando su contexto pasó el límite; None si no hay que avisar."""
    if not warn_at or pct is None or pct < warn_at:
        return None
    return f"⚠ ctx {pct}% · Alt+c"


def should_close(own_client_alive, seen_client, misses, limit=2):
    """(cerrar, misses): tmux no dispara client-detached cuando la terminal se cierra (SIGHUP), así que el
    watcher cuenta los chequeos en que no queda viva ninguna terminal que haya mirado esta sesión. Antes de la
    primera terminal no cuenta (la sesión arranca sin cliente); una terminal que pasó a otra sesión con Alt+↑/↓
    sigue contando como viva."""
    if own_client_alive or not seen_client:
        return False, 0
    misses += 1
    return misses >= limit, misses


def human(n):
    if n is None:
        return "n/d"
    for div, suf in ((1_000_000, "M"), (1_000, "k")):
        if n >= div:
            return f"{n / div:.1f}{suf}"
    return str(n)


# Alias de CAO (model: opus en el perfil) -> nombre a mostrar.
CLAUDE_MODELS = {"opus": "Opus 5.5", "sonnet": "Sonnet 5.5", "haiku": "Haiku 5.5", "fable": "Fable 5.1"}


def display_model(term):
    """'Opus 5.5', 'Sonnet 5.5'…; un id completo ('claude-opus-5-5') también. Sin modelo: el provider."""
    model = (term.get("model") or "").strip()
    m = re.fullmatch(r"claude-([a-z]+)-(\d+)-(\d+)(?:-\d+)?", model)
    if m:
        return f"{m.group(1).capitalize()} {m.group(2)}.{m.group(3)}"
    if model:
        return CLAUDE_MODELS.get(model, model)
    return provider_short(term.get("provider"))


def pane_label(term, conductor_id, role=None):
    """Texto del borde: 'líder (<modelo>)' para Opus, '<rol> (<modelo>)' para el resto (el número de tab lo
    antepone quien lo dibuja). `role` pisa el de CAO (Alt+i). Nada de precio ni contexto: eso lo muestra cada
    CLI abajo (statusline)."""
    if term["id"] == conductor_id:
        return f"líder ({display_model(term)})"
    role = role or term.get("description") or term.get("agent_profile") or "?"
    return f"{role} ({display_model(term)})"


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
    """Formato tmux del borde superior de la mitad derecha: ' 2 front (agy)  3 zsh '.
    tabs: [{'id', 'label', 'color', 'where'?}] ya ordenadas. La visible va resaltada con el color de su provider
    y además muestra 'where' (carpeta y rama); las otras no, para que la tira no desborde."""
    parts = []
    for pos, t in enumerate(tabs):
        key = tab_key(pos)
        label = t["label"]
        if t["id"] == visible_id and t.get("where"):
            label = f"{label} · {t['where']}"
        txt = f" {key} {label} " if key else f" {label} "
        c = t.get("color") or colors["muted"]
        if t["id"] == visible_id:
            parts.append(f"#[fg={colors['background']},bg={c},bold]{txt}#[default]")
        else:
            parts.append(f"#[fg={c}]{txt}#[default]")
    return "".join(parts)


# ── Cupos de cada suscripción (línea 2 de la barra) ─────────────────────────
# Cada CLI expone su cupo distinto; todo se normaliza a [{label, pct (usado), resets_at (epoch)}].

def to_epoch(v):
    """resets_at en segundos, milisegundos o ISO ('2026-11-11T05:00:00Z', '2026-12-01') -> epoch o None."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace(".", "", 1).isdigit()):
        e = float(v)
        return e / 1000 if e > 1e12 else e
    import datetime
    try:
        d = datetime.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=datetime.timezone.utc)
    return d.timestamp()


def window_label(minutes):
    """300 -> '5h', 10080 -> '7d', 43200 -> 'mes'."""
    if not minutes:
        return "?"
    if minutes >= 28 * 1440:
        return "mes"
    if minutes >= 1440:
        return f"{round(minutes / 1440)}d"
    return f"{round(minutes / 60)}h"


def claude_limits(cache):
    """Copia que escribe la statusline de Claude Code (~/.cache/claude/rate-limits.json)."""
    rl = (cache or {}).get("rate_limits") or {}
    out = []
    for key, label in (("five_hour", "5h"), ("seven_day", "7d")):
        w = rl.get(key) or {}
        if w.get("used_percentage") is not None:
            out.append({"label": label, "pct": float(w["used_percentage"]), "resets_at": to_epoch(w.get("resets_at"))})
    return out


def codex_limits(event):
    """Evento token_count de un rollout de Codex (~/.codex/sessions/**/rollout-*.jsonl)."""
    payload = (event or {}).get("payload") or event or {}
    rl = payload.get("rate_limits") or (payload.get("info") or {}).get("rate_limits") or {}
    base = to_epoch((event or {}).get("timestamp"))
    out = []
    for key in ("primary", "secondary"):
        w = rl.get(key) or {}
        if w.get("used_percent") is None:
            continue
        reset = to_epoch(w.get("resets_at"))
        if reset is None and w.get("resets_in_seconds") is not None and base:
            reset = base + float(w["resets_in_seconds"])
        out.append({"label": window_label(w.get("window_minutes")), "pct": float(w["used_percent"]),
                    "resets_at": reset})
    return out


def copilot_limits(user):
    """Respuesta de `gh api /copilot_internal/user`: pedidos premium del mes (chat y completions son ilimitados)."""
    q = ((user or {}).get("quota_snapshots") or {}).get("premium_interactions") or {}
    if q.get("unlimited") or q.get("percent_remaining") is None:
        return []
    return [{"label": "mes", "pct": max(0.0, 100 - float(q["percent_remaining"])),
             "resets_at": to_epoch(user.get("quota_reset_date_utc") or user.get("quota_reset_date"))}]


# Agentes cuyo cupo en Omarchy no es el del plan. agy: Google no informa ventana para los modelos Gemini y
# Omarchy muestra en su lugar el bucket de Claude/GPT dentro de Antigravity (siempre ~0%). Ver ADR 0007.
QUOTA_NOT_REPORTED = {"antigravity"}


def omarchy_limits(record, agent=None):
    """Registro de Omarchy (~/.local/state/omarchy/agents/usage/<agente>.json, lo mantiene su panel de
    agentes) -> ventanas normalizadas. `percent` viene como fracción (0.18 = 18%). Solo 5h, 7d y mes:
    los cupos por modelo (p. ej. 'Fable Weekly') no entran en la barra. Agentes de QUOTA_NOT_REPORTED: []."""
    if agent in QUOTA_NOT_REPORTED:
        return []
    out = []
    for lim in (record or {}).get("limits") or []:
        label = lim.get("label") or ""
        if "5-hour" in label:
            short = "5h"
        elif label.startswith("Weekly"):
            short = "7d"
        elif label.startswith("Monthly"):
            short = "mes"
        else:
            continue
        if lim.get("percent") is None:
            continue
        out.append({"label": short, "pct": float(lim["percent"]) * 100, "resets_at": to_epoch(lim.get("resetsAt"))})
    return out


def time_left(resets_at, now):
    """Lo que falta para el reset, como la statusline de Claude: '45m', '4h07m', '4d18h'; '--' si ya pasó."""
    if resets_at is None:
        return "--"
    d = int(resets_at - now)
    if d <= 0:
        return "--"
    if d < 3600:
        return f"{d // 60}m"
    if d < 86400:
        return f"{d // 3600}h{d % 3600 // 60:02d}m"
    return f"{d // 86400}d{d % 86400 // 3600}h"


def pct_color(pct, colors):
    """Mismos umbrales que la statusline de Claude: amarillo desde 50%, rojo desde 80%."""
    return colors["red"] if pct >= 80 else colors["yellow"] if pct >= 50 else colors["green"]


# claude, codex y copilot primero: los que tienen cupo real; agy y opencode (n/d) al final.
BAR_ORDER = ("claude", "codex", "copilot", "antigravity", "opencode")


def build_bar(usage, colors, now=None):
    """Línea 2 de la barra: el cupo de cada suscripción, p. ej.
    'claude 5h 8% 4h07m · 7d 1% 4d18h | agy n/d | copilot mes 3% 24d'. Sin tokens ni precios."""
    import time
    now = time.time() if now is None else now
    fg, muted = colors["foreground"], colors["muted"]
    parts = []
    # Solo las suscripciones con login, en el orden de BAR_ORDER (las que no figuran, al final).
    provs = [p for p in (usage or {}).get("providers", []) if p.get("logged_in") is True]
    provs.sort(key=lambda p: BAR_ORDER.index(p["agent"]) if p["agent"] in BAR_ORDER else len(BAR_ORDER))
    for p in provs:
        name = USAGE_SHORT.get(p["agent"], p["agent"])
        wins = []
        for w in p.get("limits") or []:
            reset = w.get("resets_at")
            pct = 0 if reset and reset <= now else round(w["pct"])  # ventana ya reseteada: arranca de cero
            wins.append(f"{w['label']} #[fg={pct_color(pct, colors)}]{pct}%#[fg={muted}] {time_left(reset, now)}")
        body = f"#[fg={muted}] · ".join(f"#[fg={fg}]{w}" for w in wins) if wins else f"#[fg={muted}]n/d"
        parts.append(f"#[fg={fg},bold]{name}#[nobold] {body}")
    if not parts:
        return f"#[fg={muted}] cupos n/d "
    return " " + f" #[fg={muted}]| ".join(parts) + " "
