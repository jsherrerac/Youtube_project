"""
ColorCodedRightTriangle — triángulo rectángulo con lados coloreados por rol matemático.

  Hipotenusa  → HYPOTENUSE (blanco)
  Cateto adj. → ADJACENT   (verde, horizontal)
  Cateto op.  → OPPOSITE   (azul, vertical)
  Ángulo α    → HIGHLIGHT  (amarillo)
"""
import numpy as np
from manim import (
    VGroup, VMobject, Line, RightAngle, Angle, Text,
    WHITE, PI, RIGHT, DOWN,
)
from .theme import (
    HYPOTENUSE, OPPOSITE, ADJACENT, HIGHLIGHT,
    STROKE_DEFAULT, STROKE_THICK, FONT_LABEL,
)


class ColorCodedRightTriangle(VGroup):
    """
    Triángulo rectángulo color-coded.

    Parámetros
    ----------
    alpha          : ángulo en el vértice A (radianes). Default: PI/4.
    hyp_length     : longitud de la hipotenusa en unidades Manim. Default: 2.0.
    vertex         : posición del vértice A (donde está alpha). Default: ORIGIN.
    show_labels    : muestra etiquetas H/A/O sobre cada lado.
    show_right_angle: muestra el cuadradito en el ángulo recto.

    Accesores
    ---------
    get_hypotenuse(), get_adjacent(), get_opposite(), get_angle_arc()
    """

    def __init__(
        self,
        alpha: float = PI / 4,
        hyp_length: float = 2.0,
        vertex: np.ndarray = None,
        show_labels: bool = True,
        show_right_angle: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)

        A = np.array(vertex if vertex is not None else [0.0, 0.0, 0.0], dtype=float)
        adj = hyp_length * np.cos(alpha)
        opp = hyp_length * np.sin(alpha)
        B = A + np.array([adj, 0.0, 0.0])           # vértice ángulo recto
        C = A + np.array([adj, opp, 0.0])            # vértice opuesto

        # ── Lados ────────────────────────────────────────────────────────────
        self.hyp_line = Line(A, C, color=HYPOTENUSE, stroke_width=STROKE_THICK)
        self.adj_line = Line(A, B, color=ADJACENT,   stroke_width=STROKE_DEFAULT)
        self.opp_line = Line(B, C, color=OPPOSITE,   stroke_width=STROKE_DEFAULT)

        # ── Cuadradito ángulo recto en B ─────────────────────────────────────
        self._right_sq = (
            RightAngle(self.adj_line, self.opp_line, length=0.18, color=WHITE)
            if show_right_angle else VMobject()
        )

        # ── Arco del ángulo alpha ─────────────────────────────────────────────
        _h_ref   = Line(A, B)
        _hyp_ref = Line(A, C)
        self.angle_arc = Angle(_h_ref, _hyp_ref, radius=0.42, color=HIGHLIGHT)
        mid = alpha / 2
        self.angle_label = Text("α", color=HIGHLIGHT, font_size=FONT_LABEL).move_to(
            A + 0.72 * np.array([np.cos(mid), np.sin(mid), 0.0])
        )

        # ── Etiquetas de lado ────────────────────────────────────────────────
        self.side_labels = VGroup()
        if show_labels:
            perp = np.array([-np.sin(alpha), np.cos(alpha), 0.0])
            self.side_labels.add(
                Text("H", color=HYPOTENUSE, font_size=FONT_LABEL).move_to(
                    (A + C) / 2 + 0.32 * perp
                ),
                Text("A", color=ADJACENT, font_size=FONT_LABEL).move_to(
                    (A + B) / 2 + DOWN * 0.30
                ),
                Text("O", color=OPPOSITE, font_size=FONT_LABEL).move_to(
                    (B + C) / 2 + RIGHT * 0.32
                ),
            )

        self.add(
            self.adj_line, self.opp_line, self.hyp_line,
            self._right_sq,
            self.angle_arc, self.angle_label,
            self.side_labels,
        )

    # ── Accesores ─────────────────────────────────────────────────────────────
    def get_hypotenuse(self) -> Line:  return self.hyp_line
    def get_adjacent(self)  -> Line:   return self.adj_line
    def get_opposite(self)  -> Line:   return self.opp_line
    def get_angle_arc(self) -> Angle:  return self.angle_arc
