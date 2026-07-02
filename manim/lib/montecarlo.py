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
    VMobject, always_redraw, PI, TAU, ORIGIN,
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
        # Dirección (constante Manim) de la esquina-origen dentro del cuadrado y
        # ejes-unidad apuntando hacia el interior. point() los reusa SIEMPRE.
        self._corner_dir = np.array([sx, sy, 0.0])
        self._ux = np.array([-sx, 0.0, 0.0])
        self._uy = np.array([0.0, -sy, 0.0])

        # Esquina física inicial (solo para construir el arco; luego point()
        # la relee del cuadrado vivo, así sobrevive a shift()/to_edge()/scale()).
        origin_pt = self._center + np.array([sx * half, sy * half, 0.0])

        # Cuadrado blanco.
        self.square = Square(side_length=self.side, color=MC_BORDER,
                             stroke_width=STROKE_DEFAULT).move_to(self._center)

        # Cuarto de círculo: arco radio = side, centrado en la esquina-origen,
        # barriendo 90° hacia el interior del cuadrado.
        start_angle = {"DL": 0.0, "DR": PI / 2, "UR": PI, "UL": 3 * PI / 2}[corner]
        self.quarter = Arc(
            radius=self.side, start_angle=start_angle, angle=PI / 2,
            arc_center=origin_pt, color=MC_BORDER, stroke_width=STROKE_THICK,
        )

        self.add(self.square, self.quarter)

    # ── ÚNICA AUTORIDAD DE COORDENADAS ───────────────────────────────────────
    # Todo (puntos, segmentos, sector sombreado) DEBE pasar por point()/radius().
    # Ambos se derivan del cuadrado VIVO, no de valores cacheados, para que
    # cualquier shift/to_edge/scale del board mantenga puntos, arco y sombreado
    # exactamente dentro del cuadrado.
    def point(self, x: float, y: float) -> np.ndarray:
        """Coords-unidad (x,y ∈ [0,1]) → punto de escena (relee el cuadrado)."""
        origin_pt = self.square.get_corner(self._corner_dir)
        return origin_pt + self.radius() * (x * self._ux + y * self._uy)

    def radius(self) -> float:
        """Lado del cuadrado = radio del cuarto de círculo (lee tamaño vivo)."""
        return self.square.get_width()


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

    def multi_curve_from(self, ns, series, colors, stroke_width=STROKE_DEFAULT) -> VGroup:
        """
        Varias series sobre los MISMOS ejes (p. ej. distintas semillas).
        `series` y `colors` son listas paralelas. No rompe curve_from (lo reusa).
        Devuelve un VGroup de polilíneas (no se añade solo).
        """
        return VGroup(*[
            self.curve_from(ns, est, color=col, stroke_width=stroke_width)
            for est, col in zip(series, colors)
        ])


# ──────────────────────────────────────────────────────────────────────────────
# Forma irregular sin fórmula de área (para Monte Carlo "de cualquier forma")
# ──────────────────────────────────────────────────────────────────────────────
def _point_in_polygon(pts, poly):
    """Ray casting vectorizado: bool por punto. pts:(n,2) en coords de escena;
    poly:(m,2) vértices del contorno en coords de escena."""
    x, y = pts[:, 0], pts[:, 1]
    inside = np.zeros(len(pts), dtype=bool)
    m = len(poly)
    j = m - 1
    for i in range(m):
        xi, yi = poly[i]
        xj, yj = poly[j]
        cond = ((yi > y) != (yj > y)) & (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        inside ^= cond
        j = i
    return inside


class ArbitraryShape(VMobject):
    """
    Blob cerrado y suave (bezier) SIN fórmula de área conocida, para demostrar
    que Monte Carlo mide cualquier forma. La frontera de clasificación es la
    MISMA curva que se ve: se muestrea el path vivo, así sobrevive a shift/scale.

    Parámetros
    ----------
    n_lobes  : nº de anclas radiales (default 9).
    base_r   : radio medio en unidades Manim (default 1.8).
    jitter   : amplitud de irregularidad (default 0.7).
    rng      : np.random.Generator (semilla fija para reproducibilidad).
    samples  : nº de muestras del contorno para área/clasificación (default 240).

    Métodos
    -------
    contains(pts) : bool por punto (pts en coords de escena).
    area()        : área real (shoelace sobre el contorno vivo).
    bbox()        : (x_min, x_max, y_min, y_max) en escena.
    """

    def __init__(self, n_lobes: int = 9, base_r: float = 1.8, jitter: float = 0.7,
                 rng=None, samples: int = 240, color=MC_BORDER,
                 stroke_width=STROKE_DEFAULT, **kwargs):
        super().__init__(color=color, stroke_width=stroke_width, **kwargs)
        if rng is None:
            rng = np.random.default_rng(0)
        self._samples = int(samples)
        theta = np.linspace(0, TAU, n_lobes, endpoint=False)
        radii = base_r + jitter * rng.uniform(-1.0, 1.0, size=n_lobes)
        anchors = [np.array([r * np.cos(t), r * np.sin(t), 0.0])
                   for r, t in zip(radii, theta)]
        # Curva cerrada y suave a través de las anclas (repetir la 1ª cierra).
        self.set_points_smoothly(anchors + [anchors[0]])

    def _current_poly(self) -> np.ndarray:
        """Muestrea el contorno VIVO → polígono fino (n,2) en coords de escena."""
        ts = np.linspace(0.0, 1.0, self._samples, endpoint=False)
        return np.array([self.point_from_proportion(t)[:2] for t in ts])

    def contains(self, pts) -> np.ndarray:
        return _point_in_polygon(np.asarray(pts)[:, :2], self._current_poly())

    def area(self) -> float:
        poly = self._current_poly()
        x, y = poly[:, 0], poly[:, 1]
        return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

    def bbox(self):
        return (self.get_left()[0], self.get_right()[0],
                self.get_bottom()[1], self.get_top()[1])
