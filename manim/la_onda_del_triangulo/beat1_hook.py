"""
Beat 1 — Hook
Duración objetivo: ~20s
Una onda senoidal azul llena la pantalla y se mueve sola.
Al final colapsa hacia el centro y un triángulo rectángulo nace de ese punto.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background, WAVE, HYPOTENUSE, OPPOSITE, ADJACENT, HIGHLIGHT,
    STROKE_THICK, ColorCodedRightTriangle,
)

_W = 7.5   # mitad del ancho de escena — la onda cubre toda la pantalla


class Beat1Hook(Scene):
    def construct(self):
        set_background(self)
        self.wait(0.5)

        # ── Onda senoidal moviéndose ──────────────────────────────────────────
        phase = ValueTracker(0.0)

        wave = always_redraw(lambda: ParametricFunction(
            lambda t: np.array([t, 1.6 * np.sin(t + phase.get_value()), 0.0]),
            t_range=[-_W, _W, 0.04],
            color=WAVE,
            stroke_width=STROKE_THICK,
        ))

        self.play(FadeIn(wave), run_time=0.8)

        # ~12 s desplazándose (2 períodos completos a velocidad constante)
        self.play(phase.animate.set_value(2 * TAU), run_time=12, rate_func=linear)

        # ── Colapsar la onda hacia el centro ──────────────────────────────────
        # Congelamos la onda en su posición actual para poder animarla
        self.remove(wave)
        current_phase = phase.get_value()
        frozen = ParametricFunction(
            lambda t: np.array([t, 1.6 * np.sin(t + current_phase), 0.0]),
            t_range=[-_W, _W, 0.04],
            color=WAVE,
            stroke_width=STROKE_THICK,
        )
        self.add(frozen)

        self.play(
            FadeOut(frozen, scale=0.02, run_time=1.5, rate_func=rush_into),
        )

        # ── Triángulo nace del centro ─────────────────────────────────────────
        tri = ColorCodedRightTriangle(
            alpha=PI / 4, hyp_length=2.8, show_labels=True
        ).center()

        self.play(GrowFromCenter(tri), run_time=1.8)
        self.wait(2.5)
        self.play(FadeOut(tri), run_time=0.8)
        self.wait(0.5)
