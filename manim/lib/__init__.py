"""
lib/ — banco de animaciones del canal DotCorzo.
Importar desde aquí en todas las escenas.
"""
from .theme import (
    HYPOTENUSE, OPPOSITE, ADJACENT, CIRCUMFERENCE, DIAMETER, HIGHLIGHT, WAVE,
    PALETTE,
    STROKE_DEFAULT, STROKE_THICK, STROKE_THIN,
    FONT_LABEL, FONT_FORMULA, FONT_TITLE,
    set_background, color_tex,
)
from .triangle       import ColorCodedRightTriangle
from .unit_circle_wave import UnitCircleWave
from .live_formula   import LiveSineFormula

__all__ = [
    # Tema
    "HYPOTENUSE", "OPPOSITE", "ADJACENT", "CIRCUMFERENCE", "DIAMETER",
    "HIGHLIGHT", "WAVE", "PALETTE",
    "STROKE_DEFAULT", "STROKE_THICK", "STROKE_THIN",
    "FONT_LABEL", "FONT_FORMULA", "FONT_TITLE",
    "set_background", "color_tex",
    # Componentes
    "ColorCodedRightTriangle",
    "UnitCircleWave",
    "LiveSineFormula",
]
