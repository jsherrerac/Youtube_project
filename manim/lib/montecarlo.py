"""
montecarlo.py — banco reutilizable de componentes Monte Carlo / probabilidad.

PRINCIPIO RECTOR (consistencia de color del canal):
  DENTRO  → MC_INSIDE  (cian)
  FUERA   → MC_OUTSIDE (coral)
  borde   → MC_BORDER  (blanco)
  π       → MC_PI      (amarillo/dorado)

Componentes:
  - MonteCarloBoard : cuadrado unidad + cuarto de círculo radio 1.
  - sample_points   : N puntos uniformes clasificados dentro/fuera → Dots coloreados.
  - pi_counter      : DecimalNumber always_redraw con π = 4·dentro/total.
  - ConvergencePlot : ejes (N vs estimación) + línea actualizable + línea π real.
"""
import numpy as np
from manim import (
    VGroup, Square, Arc, Dot, Text, Axes, DashedLine,
    VMobject, always_redraw, PI, ORIGIN,
)
from .theme import (
    MC_INSIDE, MC_OUTSIDE, MC_BORDER, MC_PI,
    STROKE_DEFAULT, STROKE_THICK, STROKE_THIN, FONT_FORMULA,
)


# ──────────────────────────────────────────────────────────────────────────────
# Tablero: cuadrado unidad + cuarto de círculo
# ──────────────────────────────────────────────────────────────────────────────
class MonteCarloBoard(VGroup):
    """
    Cuadrado de lado 1 (blanco) con un cuarto de círculo de radio 1 (blanco)
    anclado en una esquina. El cuadrado vive en coordenadas-unidad [0,1]×[0,1];
    la esquina del cuarto de círculo es el origen unidad (0,0).

    Parámetros
    ----------
    side      : longitud del lado en unidades Manim (default 5.0).
    center    : centro del cuadrado en la escena (default ORIGIN).
    corner    : esquina donde se centra el cuarto de círculo. Una de
                "DL", "DR", "UL", "UR" (default "DL" = abajo-izquierda).

    Métodos
    -------
    point(x, y) : mapea coords-unidad (x,y ∈ [0,1]) a un punto de escena.
    """

    def __init__(self, side: float = 5.0, center=ORIGIN, corner: str = "DL", **kwargs):
        super().__init__(**kwargs)
        self.side = float(side)
        self._center = np.array(center, dtype=float)
        self.corner = corner

        # Esquina-origen (unidad 0,0) y direcciones de los ejes unidad en escena.
        half = self.side / 2.0
        sx, sy = {
            "DL": (-1, -1), "DR": (1, -1), "UL": (-1, 1), "UR": (1, 1),
        }[corner]
        # Esquina física donde se centra el cuarto de círculo:
        self._origin_pt = self._center + np.array([sx * half, sy * half, 0.0])
        # El eje x-unidad y y-unidad apuntan hacia el interior del cuadrado:
        self._ux = np.array([-sx, 0.0, 0.0])
        self._uy = np.array([0.0, -sy, 0.0])

        # Cuadrado blanco.
        self.square = Square(side_length=self.side, color=MC_BORDER,
                             stroke_width=STROKE_DEFAULT).move_to(self._center)

        # Cuarto de círculo: arco radio = side, centrado en la esquina-origen,
        # barriendo 90° hacia el interior del cuadrado.
        start_angle = {"DL": 0.0, "DR": PI / 2, "UR": PI, "UL": 3 * PI / 2}[corner]
        self.quarter = Arc(
            radius=self.side, start_angle=start_angle, angle=PI / 2,
            arc_center=self._origin_pt, color=MC_BORDER, stroke_width=STROKE_THICK,
        )

        self.add(self.square, self.quarter)

    def point(self, x: float, y: float) -> np.ndarray:
        """Coords-unidad (x,y ∈ [0,1]) → punto de escena."""
        return self._origin_pt + self.side * (x * self._ux + y * self._uy)


# ──────────────────────────────────────────────────────────────────────────────
# Muestreo
# ──────────────────────────────────────────────────────────────────────────────
def sample_points(board: MonteCarloBoard, n: int, rng: np.random.Generator,
                  dot_radius: float = 0.035):
    """
    Genera n puntos uniformes en el cuadrado unidad, los clasifica con
    x²+y² ≤ 1 y devuelve (dots, pts, inside_mask).

      dots        : VGroup de Dot coloreados (DENTRO=cian, FUERA=coral).
      pts         : ndarray (n,2) en coords-unidad.
      inside_mask : ndarray bool (n,).
    """
    pts = rng.uniform(0.0, 1.0, size=(n, 2))
    inside_mask = (pts[:, 0] ** 2 + pts[:, 1] ** 2) <= 1.0
    dots = VGroup(*[
        Dot(board.point(x, y), radius=dot_radius,
            color=MC_INSIDE if ins else MC_OUTSIDE)
        for (x, y), ins in zip(pts, inside_mask)
    ])
    return dots, pts, inside_mask


# ──────────────────────────────────────────────────────────────────────────────
# Contador en vivo de π
# ──────────────────────────────────────────────────────────────────────────────
def pi_counter(inside_tracker, total_tracker, num_decimal_places: int = 4,
              font_size: int = FONT_FORMULA):
    """
    Número en vivo (Text, sin LaTeX) con π ≈ 4·dentro/total, en amarillo.
    Recibe dos ValueTracker (dentro, total). Si total=0 muestra 0.
    """
    def _build():
        total = total_tracker.get_value()
        inside = inside_tracker.get_value()
        val = 4.0 * inside / total if total > 0 else 0.0
        return Text(f"{val:.{num_decimal_places}f}", color=MC_PI, font_size=font_size)
    return always_redraw(_build)


# ──────────────────────────────────────────────────────────────────────────────
# Gráfica de convergencia
# ──────────────────────────────────────────────────────────────────────────────
class ConvergencePlot(VGroup):
    """
    Ejes (x=N puntos, y=estimación) con línea punteada de referencia en π.
    Reutilizable: alimentá la curva con curve_from(ns, estimates).

    Parámetros
    ----------
    x_max   : N máximo del eje (default 1000).
    y_range : (min, max, step) del eje vertical (default (2.4, 3.8, 0.2)).
    width   : ancho en unidades Manim (default 5.5).
    height  : alto en unidades Manim (default 3.5).
    """

    def __init__(self, x_max: float = 1000, y_range=(2.4, 3.8, 0.2),
                 width: float = 5.5, height: float = 3.5, **kwargs):
        super().__init__(**kwargs)
        self.axes = Axes(
            x_range=[0, x_max, x_max / 5],
            y_range=list(y_range),
            x_length=width, y_length=height,
            axis_config={"include_tip": False, "stroke_width": STROKE_THIN,
                         "color": MC_BORDER},
            tips=False,
        )
        # Línea punteada en π real.
        self.pi_line = DashedLine(
            self.axes.c2p(0, PI), self.axes.c2p(x_max, PI),
            color=MC_PI, stroke_width=STROKE_DEFAULT, dash_length=0.12,
        )
        self.pi_label = Text("π", color=MC_PI, font_size=FONT_FORMULA)
        self.pi_label.next_to(self.pi_line.get_end(), direction=np.array([0.4, 0.3, 0]))

        self.add(self.axes, self.pi_line, self.pi_label)

    def curve_from(self, ns, estimates, color=MC_PI, stroke_width=STROKE_DEFAULT) -> VMobject:
        """Construye la polilínea de la estimación vs N (no se añade sola)."""
        pts = [self.axes.c2p(n, e) for n, e in zip(ns, estimates)]
        curve = VMobject(color=color, stroke_width=stroke_width)
        if pts:
            curve.set_points_as_corners(pts)
        return curve
