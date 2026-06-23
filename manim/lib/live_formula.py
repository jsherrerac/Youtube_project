"""
LiveSineFormula — fórmula A·sin(k·α+φ)+d con parámetros animables en vivo.

Los números del display se actualizan en tiempo real al animar los ValueTrackers.
La curva se redibuja con always_redraw respondiendo a todos los parámetros.

Uso:
    lf = LiveSineFormula()
    scene.add(lf)
    scene.play(lf.set_amplitude(2.0), run_time=2)   # anima A de 1 → 2
    scene.play(lf.set_frequency(2.0), run_time=2)   # anima k de 1 → 2
"""
import numpy as np
from manim import (
    VGroup, Axes, DecimalNumber, Text,
    ValueTracker, always_redraw,
    WHITE, TAU, PI, RIGHT, DOWN,
)
from .theme import (
    OPPOSITE, ADJACENT, CIRCUMFERENCE, HIGHLIGHT, WAVE,
    STROKE_DEFAULT, STROKE_THICK, FONT_FORMULA, FONT_LABEL,
)


class LiveSineFormula(VGroup):
    """
    Fórmula A·sin(k·α+φ)+d con números vivos + curva reactiva.

    Parámetros
    ----------
    A_init   : amplitud inicial. Default: 1.0
    k_init   : frecuencia inicial. Default: 1.0
    phi_init : fase inicial (radianes). Default: 0.0
    d_init   : desplazamiento vertical inicial. Default: 0.0

    Atributos públicos
    ------------------
    A, k, phi, d : ValueTrackers de cada parámetro
    formula      : VGroup con DecimalNumbers + MathTex estáticos
    axes         : Axes del gráfico
    curve        : always_redraw — curva que reacciona a todos los trackers

    Métodos de animación (pasar a scene.play)
    ----------------------------------------
    set_amplitude(v), set_frequency(v), set_phase(v), set_offset(v)
    """

    def __init__(
        self,
        A_init:   float = 1.0,
        k_init:   float = 1.0,
        phi_init: float = 0.0,
        d_init:   float = 0.0,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # ── ValueTrackers ────────────────────────────────────────────────────
        self.A   = ValueTracker(A_init)
        self.k   = ValueTracker(k_init)
        self.phi = ValueTracker(phi_init)
        self.d   = ValueTracker(d_init)

        # ── Números vivos ────────────────────────────────────────────────────
        # Cada parámetro usa el color del objeto matemático que representa.
        dec_cfg = dict(num_decimal_places=2, mob_class=Text, font_size=FONT_FORMULA)
        self._A_num   = DecimalNumber(A_init,   color=HIGHLIGHT,     **dec_cfg)
        self._k_num   = DecimalNumber(k_init,   color=ADJACENT,      **dec_cfg)
        self._phi_num = DecimalNumber(phi_init,  color=CIRCUMFERENCE, **dec_cfg)
        self._d_num   = DecimalNumber(d_init,   color=HIGHLIGHT,     **dec_cfg)

        # Updaters: cada número sigue a su tracker
        self._A_num  .add_updater(lambda m: m.set_value(self.A.get_value()))
        self._k_num  .add_updater(lambda m: m.set_value(self.k.get_value()))
        self._phi_num.add_updater(lambda m: m.set_value(self.phi.get_value()))
        self._d_num  .add_updater(lambda m: m.set_value(self.d.get_value()))

        # ── Partes estáticas de la fórmula (Text con unicode — sin LaTeX) ────
        _t = lambda s: Text(s, color=WHITE, font_size=FONT_FORMULA)
        self.formula = VGroup(
            self._A_num,
            _t("·sin("),
            self._k_num,
            _t("·α +"),
            self._phi_num,
            _t(")+"),
            self._d_num,
        ).arrange(RIGHT, buff=0.06, aligned_edge=DOWN)

        # ── Ejes ─────────────────────────────────────────────────────────────
        self.axes = Axes(
            x_range=[-TAU, TAU, PI / 2],
            y_range=[-3.0, 3.0, 1.0],
            x_length=11,
            y_length=5.5,
            tips=False,
            axis_config={"color": WHITE, "stroke_width": STROKE_DEFAULT},
        )
        self.axes.x_axis.add_labels({
            -PI: Text("-π", color=WHITE, font_size=FONT_LABEL),
             PI: Text("π",  color=WHITE, font_size=FONT_LABEL),
            TAU: Text("2π", color=WHITE, font_size=FONT_LABEL),
        })

        # ── Curva reactiva ───────────────────────────────────────────────────
        def _build_curve():
            A   = self.A.get_value()
            k   = self.k.get_value()
            phi = self.phi.get_value()
            d   = self.d.get_value()
            return self.axes.plot(
                lambda x: A * np.sin(k * x + phi) + d,
                color=WAVE,
                stroke_width=STROKE_THICK,
            )

        self.curve = always_redraw(_build_curve)

        # Fórmula encima, axes debajo
        group = VGroup(self.formula, self.axes).arrange(DOWN, buff=0.6)
        self.add(group, self.curve)

    # ── Métodos de animación ──────────────────────────────────────────────────

    def set_amplitude(self, val: float):
        """Anima A → val. Pasar a scene.play()."""
        return self.A.animate.set_value(val)

    def set_frequency(self, val: float):
        """Anima k → val. Pasar a scene.play()."""
        return self.k.animate.set_value(val)

    def set_phase(self, val: float):
        """Anima φ → val (radianes). Pasar a scene.play()."""
        return self.phi.animate.set_value(val)

    def set_offset(self, val: float):
        """Anima d → val. Pasar a scene.play()."""
        return self.d.animate.set_value(val)
