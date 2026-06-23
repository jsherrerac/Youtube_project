"""
UnitCircleWave — el componente estrella del canal.

Muestra cómo la altura del punto en el círculo unitario genera la onda seno
conforme el ángulo alpha avanza de 0 a 2π.

Layout por defecto (escena 16:9):
  Círculo a la izquierda (centro ~-4.5, 0)  |  Ejes a la derecha
  Radio giratorio, catetos azul/verde        |  Onda trazándose en tiempo real
  Línea punteada conectando altura ↔ onda    |

Uso típico:
    ucw = UnitCircleWave()
    self.add(ucw.circle)
    self.add(ucw.radius_line, ucw.dot, ucw.opposite, ucw.adjacent)
    self.play(Create(ucw.axes), run_time=1.5)
    self.add(ucw.wave_sin, ucw.wave_dot, ucw.dashed_connector)
    self.play(ucw.sweep(), run_time=6, rate_func=linear)
"""
import numpy as np
from manim import (
    VGroup, Circle, Dot, Line, DashedLine, Axes,
    Text, ValueTracker,
    always_redraw,
    WHITE, TAU, PI,
)
from .theme import (
    HYPOTENUSE, OPPOSITE, ADJACENT, CIRCUMFERENCE, HIGHLIGHT, WAVE,
    STROKE_DEFAULT, STROKE_THICK, STROKE_THIN, FONT_LABEL,
)


class UnitCircleWave(VGroup):
    """
    Círculo unitario + ejes + onda seno trazándose en tiempo real.

    Parámetros
    ----------
    circle_center : centro del círculo en coords Manim. Default: (-4.5, 0, 0).
    circle_radius : radio visual (unidades Manim). Default: 2.0.
    trace_cos     : traza también el coseno en color ADJACENT. Default: False.

    Atributos públicos (para animar por separado)
    -------------------
    alpha          : ValueTracker — avanza de 0 a TAU durante sweep()
    circle         : Circle (estático, Color CIRCUMFERENCE)
    radius_line    : always_redraw — radio del centro al punto
    dot            : always_redraw — punto sobre el círculo (HIGHLIGHT)
    opposite       : always_redraw — cateto vertical (OPPOSITE/azul)
    adjacent       : always_redraw — cateto horizontal (ADJACENT/verde)
    axes           : Axes (estático)
    wave_sin       : always_redraw — curva seno trazándose
    wave_dot       : always_redraw — punto actual sobre la onda
    dashed_connector: always_redraw — línea punteada círculo ↔ onda
    wave_cos       : always_redraw — curva coseno (solo si trace_cos=True)
    """

    def __init__(
        self,
        circle_center: np.ndarray = None,
        circle_radius: float = 2.0,
        trace_cos: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        cc = np.array(circle_center if circle_center is not None else [-4.5, 0.0, 0.0])
        cr = circle_radius

        # ── ValueTracker central ─────────────────────────────────────────────
        self.alpha = ValueTracker(0.0)

        # ── Círculo unitario ─────────────────────────────────────────────────
        self.circle = Circle(radius=cr, color=CIRCUMFERENCE, stroke_width=STROKE_THICK)
        self.circle.move_to(cc)

        # ── Radio giratorio ──────────────────────────────────────────────────
        self.radius_line = always_redraw(lambda: Line(
            cc,
            cc + cr * np.array([np.cos(self.alpha.get_value()),
                                  np.sin(self.alpha.get_value()), 0.0]),
            color=HYPOTENUSE,
            stroke_width=STROKE_THICK,
        ))

        # ── Punto sobre el círculo ───────────────────────────────────────────
        self.dot = always_redraw(lambda: Dot(
            cc + cr * np.array([np.cos(self.alpha.get_value()),
                                  np.sin(self.alpha.get_value()), 0.0]),
            color=HIGHLIGHT,
            radius=0.10,
        ))

        # ── Cateto opuesto (vertical, azul) ─────────────────────────────────
        self.opposite = always_redraw(lambda: Line(
            cc + cr * np.array([np.cos(self.alpha.get_value()), 0.0, 0.0]),
            cc + cr * np.array([np.cos(self.alpha.get_value()),
                                  np.sin(self.alpha.get_value()), 0.0]),
            color=OPPOSITE,
            stroke_width=STROKE_DEFAULT,
        ))

        # ── Cateto adyacente (horizontal, verde) ─────────────────────────────
        self.adjacent = always_redraw(lambda: Line(
            cc,
            cc + cr * np.array([np.cos(self.alpha.get_value()), 0.0, 0.0]),
            color=ADJACENT,
            stroke_width=STROKE_DEFAULT,
        ))

        # ── Ejes ─────────────────────────────────────────────────────────────
        self.axes = Axes(
            x_range=[0, TAU, PI / 2],
            y_range=[-1.35, 1.35, 0.5],
            x_length=6.5,
            y_length=4.0,
            tips=False,
            axis_config={"color": WHITE, "stroke_width": STROKE_DEFAULT},
        ).move_to(np.array([1.8, 0.0, 0.0]))

        # Labels en eje x: π y 2π  (Text con unicode — no requiere LaTeX)
        self.axes.x_axis.add_labels({
            PI:  Text("π",   color=WHITE, font_size=FONT_LABEL),
            TAU: Text("2π",  color=WHITE, font_size=FONT_LABEL),
        })
        # Labels en eje y: 1 y -1
        self.axes.y_axis.add_labels({
             1: Text("1",  color=WHITE, font_size=FONT_LABEL),
            -1: Text("-1", color=WHITE, font_size=FONT_LABEL),
        })

        # ── Onda seno trazándose ─────────────────────────────────────────────
        # Clampeado a [ε, TAU] para evitar x_range vacío o fuera de ejes.
        def _sin_curve():
            a = min(max(self.alpha.get_value(), 1e-4), TAU)
            return self.axes.plot(
                np.sin, x_range=[0.0, a],
                color=WAVE, stroke_width=STROKE_THICK,
            )

        self.wave_sin = always_redraw(_sin_curve)

        # ── Punto actual sobre la onda ───────────────────────────────────────
        self.wave_dot = always_redraw(lambda: Dot(
            self.axes.c2p(
                min(self.alpha.get_value(), TAU),
                np.sin(self.alpha.get_value()),
            ),
            color=WAVE,
            radius=0.09,
        ))

        # ── Línea punteada: punto del círculo ↔ punto de la onda ─────────────
        # Comunica visualmente que la altura del círculo ES el valor del seno.
        self.dashed_connector = always_redraw(lambda: DashedLine(
            cc + cr * np.array([np.cos(self.alpha.get_value()),
                                  np.sin(self.alpha.get_value()), 0.0]),
            self.axes.c2p(
                min(self.alpha.get_value(), TAU),
                np.sin(self.alpha.get_value()),
            ),
            color=OPPOSITE,
            stroke_width=STROKE_THIN,
            dash_length=0.14,
        ))

        # ── Coseno opcional ───────────────────────────────────────────────────
        if trace_cos:
            def _cos_curve():
                a = min(max(self.alpha.get_value(), 1e-4), TAU)
                return self.axes.plot(
                    np.cos, x_range=[0.0, a],
                    color=ADJACENT, stroke_width=STROKE_THICK,
                )
            self.wave_cos = always_redraw(_cos_curve)
        else:
            self.wave_cos = None

        # El VGroup agrupa todo para moverse/escalar como unidad.
        # En escenas, añadir los submobjects individualmente da control granular.
        self.add(
            self.circle, self.axes,
            self.radius_line, self.dot,
            self.opposite, self.adjacent,
            self.wave_sin, self.wave_dot,
            self.dashed_connector,
            *([self.wave_cos] if self.wave_cos else []),
        )

    # ── API de animación ──────────────────────────────────────────────────────

    def sweep(self):
        """
        Animación de alpha 0 → 2π que traza la onda completa.

        Usar así:
            self.play(ucw.sweep(), run_time=6, rate_func=linear)
        """
        return self.alpha.animate.set_value(TAU)

    def reset(self):
        """Devuelve alpha a 0 (para repetir el sweep)."""
        return self.alpha.animate.set_value(0.0)
