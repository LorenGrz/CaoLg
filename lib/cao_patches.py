"""Parches locales a CAO 2.5.4 (pineado, ADR 0002). Funciones puras: texto del módulo -> texto parcheado.
Las aplica bin/caolg-patch-cao (lo llama install.sh). Ver ADR 0006."""
import re

MARK = "# caolg: barra recortada (ADR 0006)"

# Copilot recorta su barra inferior cuando el pane es angosto (la mitad derecha de caolg):
#   ancho:    "← open sidebar · Autopilot · Allow All · / commands · ? help   copilot-dev · …"
#   angosto:  "Autopilot · Allow All · / … copilot-dev · Copilot Fus…"
# CAO solo reconoce la ancha y nunca ve a Copilot "listo" (timeout de 60 s al iniciar).
HINT_BAR_ORIGINAL = re.compile(r'(    r"←\.\*\[·•\]\\s\*/ commands\\b"\n)(\))')
HINT_BAR_EXTRA = (
    f"    {MARK}\n"
    '    r"|^(?:autopilot|interactive|plan)\\s*[·•].*[·•]\\s*/"\n'
)


def patch_copilot_hint_bar(src):
    """Suma a COPILOT_HINT_BAR_PATTERN la barra recortada. Ya parcheado: igual. Formato desconocido: None."""
    if MARK in src:
        return src
    new, n = HINT_BAR_ORIGINAL.subn(lambda m: m.group(1) + HINT_BAR_EXTRA + m.group(2), src, count=1)
    return new if n == 1 else None
