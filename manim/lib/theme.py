"""
Paleta y estilos del canal DotCorzo.
PRINCIPIO RECTOR: cada objeto matemático tiene un color único → su etiqueta usa ESE MISMO color.
Importar de aquí en TODOS los archivos de lib/ y escenas.
"""
from manim import WHITE, BLUE, GREEN, RED, PURPLE, YELLOW, BLACK, Scene

# ── Colores canónicos del canal ──────────────────────────────────────────────
HYPOTENUSE    = WHITE     # hipotenusa / radio del círculo unitario
OPPOSITE      = BLUE      # cateto opuesto  / componente seno
ADJACENT      = GREEN     # cateto adyacente / componente coseno
CIRCUMFERENCE = RED       # circunferencia / círculo
DIAMETER      = PURPLE    # diámetro
HIGHLIGHT     = YELLOW    # ángulo focal · énfasis · resultado
WAVE          = BLUE      # onda senoidal — mismo color que OPPOSITE (misma cantidad física)

# ── Familia Monte Carlo / probabilidad (aditivo, no toca lo de arriba) ────────
MC_INSIDE   = "#22D3EE"   # punto DENTRO del cuarto de círculo — cian
MC_OUTSIDE  = "#FF6B5C"   # punto FUERA — coral
MC_BORDER   = WHITE       # borde del cuadrado y del cuarto de círculo
MC_PI       = HIGHLIGHT   # valor de π y línea de referencia — amarillo/dorado del canal

PALETTE: dict = {
    "hypotenuse":    HYPOTENUSE,
    "opposite":      OPPOSITE,
    "adjacent":      ADJACENT,
    "circumference": CIRCUMFERENCE,
    "diameter":      DIAMETER,
    "highlight":     HIGHLIGHT,
    "wave":          WAVE,
    "mc_inside":     MC_INSIDE,
    "mc_outside":    MC_OUTSIDE,
    "mc_pi":         MC_PI,
}

# ── Stroke widths (unidades Manim) ───────────────────────────────────────────
STROKE_DEFAULT = 2.5
STROKE_THICK   = 4.0
STROKE_THIN    = 1.5

# ── Tamaños de fuente ────────────────────────────────────────────────────────
FONT_LABEL   = 28
FONT_FORMULA = 36
FONT_TITLE   = 48


def set_background(scene: Scene) -> None:
    """Fondo negro canónico del canal."""
    scene.camera.background_color = BLACK


def color_tex(tex, mapping: dict):
    """
    Colorea substrings de un MathTex según {substr: color}.
    Ejemplo: color_tex(tex, {"C": RED, "d": PURPLE, "\\pi": HIGHLIGHT})
    Devuelve el mismo tex para encadenamiento.
    """
    for substr, color in mapping.items():
        tex.set_color_by_tex(substr, color)
    return tex
