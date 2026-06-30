"""
lib/ — banco de animaciones del canal DotCorzo.
Importar desde aquí en todas las escenas.
"""
from .theme import (
    HYPOTENUSE, OPPOSITE, ADJACENT, CIRCUMFERENCE, DIAMETER, HIGHLIGHT, WAVE,
    MC_INSIDE, MC_OUTSIDE, MC_BORDER, MC_PI,
    PALETTE,
    STROKE_DEFAULT, STROKE_THICK, STROKE_THIN,
    FONT_LABEL, FONT_FORMULA, FONT_TITLE,
    set_background, color_tex,
)
from .triangle       import ColorCodedRightTriangle
from .unit_circle_wave import UnitCircleWave
from .live_formula   import LiveSineFormula
from .montecarlo     import (
    MonteCarloBoard, sample_points, pi_counter, ConvergencePlot,
)

__all__ = [
    # Tema
    "HYPOTENUSE", "OPPOSITE", "ADJACENT", "CIRCUMFERENCE", "DIAMETER",
    "HIGHLIGHT", "WAVE", "PALETTE",
    "MC_INSIDE", "MC_OUTSIDE", "MC_BORDER", "MC_PI",
    "STROKE_DEFAULT", "STROKE_THICK", "STROKE_THIN",
    "FONT_LABEL", "FONT_FORMULA", "FONT_TITLE",
    "set_background", "color_tex",
    # Componentes
    "ColorCodedRightTriangle",
    "UnitCircleWave",
    "LiveSineFormula",
    # Monte Carlo
    "MonteCarloBoard", "sample_points", "pi_counter", "ConvergencePlot",
]
