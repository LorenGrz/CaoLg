"""Parches locales a CAO 2.5.4 (pineado, ADR 0002). Funciones puras: texto del módulo -> texto parcheado.
Las aplica bin/caolg-patch-cao (lo llama install.sh). Ver ADR 0006."""
import re

MARK = "# caolg: barra recortada (ADR 0006)"

# Copilot recorta su barra inferior cuando el pane es angosto (la mitad derecha de caolg):
#   ancho:     "← open sidebar · Autopilot · Allow All · / commands · ? help   copilot-dev · …"
#   angosto:   "Autopilot · Allow All · / … copilot-dev · Copilot Fus…"           (1.0.106)
#   más aún:   "Autopilot · Allow All    copilot-dev · Copilot …"                  (1.0.110, sin el "/")
# CAO solo reconoce la ancha y nunca ve a Copilot "listo" (timeout de 60 s al iniciar). Basta con que la
# línea empiece por el modo: este patrón solo se mira en la fila de abajo de la caja del composer.
HINT_BAR_ORIGINAL = re.compile(r'(    r"←\.\*\[·•\]\\s\*/ commands\\b"\n)(\))')
HINT_BAR_LINE = '    r"|^(?:autopilot|interactive|plan)\\s*[·•]"\n'
HINT_BAR_EXTRA = f"    {MARK}\n" + HINT_BAR_LINE
# Lo que escribía la versión anterior del parche (exigía "· /"): se reemplaza al volver a parchear.
HINT_BAR_OLD_LINE = '    r"|^(?:autopilot|interactive|plan)\\s*[·•].*[·•]\\s*/"\n'


def patch_copilot_hint_bar(src):
    """Suma a COPILOT_HINT_BAR_PATTERN la barra recortada. Ya parcheado: igual (o actualiza el parche viejo).
    Formato desconocido: None."""
    if MARK in src:
        return src.replace(HINT_BAR_OLD_LINE, HINT_BAR_LINE, 1)
    new, n = HINT_BAR_ORIGINAL.subn(lambda m: m.group(1) + HINT_BAR_EXTRA + m.group(2), src, count=1)
    return new if n == 1 else None
