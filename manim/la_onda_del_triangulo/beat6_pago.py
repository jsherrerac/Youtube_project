"""
Beat 6 — El pago y el puente
Duración objetivo: ~65s
Parte A: Recap visual — triángulo, círculo y onda pequeños, lado a lado.
Parte B: LiveSineFormula — sube A (onda se estira), luego sube k (se comprime).
Parte C: Placeholder de ~5s para el clip de Pygame (insertar en edición).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background,
    HYPOTENUSE, OPPOSITE, ADJACENT, CIRCUMFERENCE, HIGHLIGHT, WAVE,
    STROKE_DEFAULT, STROKE_THICK, FONT_LABEL, FONT_FORMULA, FONT_TITLE,
    ColorCodedRightTriangle, LiveSineFormula,
)


class Beat6Pago(Scene):
    def construct(self):
        set_background(self)
        self.wait(0.5)

        # ══════════════════════════════════════════════════════════════════════
        # PARTE A — Recap rápido: triángulo → círculo → onda (miniaturas)
        # ══════════════════════════════════════════════════════════════════════

        # Mini triángulo (izquierda)
        mini_tri = ColorCodedRightTriangle(
            alpha=PI / 4, hyp_length=1.6, show_labels=False
        ).shift(LEFT * 4.5)

        # Mini círculo con radio (centro)
        mini_circle = Circle(radius=1.0, color=CIRCUMFERENCE, stroke_width=STROKE_DEFAULT)
        mini_radius = Line(
            ORIGIN, RIGHT * 1.0,
            color=HYPOTENUSE, stroke_width=STROKE_DEFAULT,
        )
        mini_dot = Dot(RIGHT * 1.0, color=HIGHLIGHT, radius=0.07)
        mini_circle_group = VGroup(mini_circle, mini_radius, mini_dot)

        # Mini onda (derecha) — estática
        mini_wave = ParametricFunction(
            lambda t: np.array([t * 0.8, 0.6 * np.sin(t), 0.0]),
            t_range=[0, TAU, 0.05],
            color=WAVE,
            stroke_width=STROKE_DEFAULT,
        ).shift(RIGHT * 4.0 + LEFT * TAU * 0.4)

        # Etiquetas debajo de cada miniatura
        lbl_tri  = Text("triángulo",  color=WHITE, font_size=FONT_LABEL).next_to(mini_tri,          DOWN, buff=0.3)
        lbl_circ = Text("círculo",    color=WHITE, font_size=FONT_LABEL).next_to(mini_circle_group, DOWN, buff=0.3)
        lbl_wave = Text("onda seno",  color=WHITE, font_size=FONT_LABEL).next_to(mini_wave,         DOWN, buff=0.3)

        # Flechas conectoras
        arrow_1 = Arrow(mini_tri.get_right(), mini_circle.get_left(), color=WHITE, buff=0.15)
        arrow_2 = Arrow(mini_circle.get_right(), mini_wave.get_left(), color=WHITE, buff=0.15)

        self.play(
            GrowFromCenter(mini_tri), GrowFromCenter(mini_circle_group),
            run_time=1.2,
        )
        self.play(FadeIn(lbl_tri), FadeIn(lbl_circ), run_time=0.6)
        self.play(GrowArrow(arrow_1), run_time=0.6)

        self.play(Create(mini_wave), run_time=1.2)
        self.play(FadeIn(lbl_wave), run_time=0.5)
        self.play(GrowArrow(arrow_2), run_time=0.6)
        self.wait(2.0)

        # Limpiar recap
        recap_group = VGroup(
            mini_tri, mini_circle_group, mini_wave,
            lbl_tri, lbl_circ, lbl_wave,
            arrow_1, arrow_2,
        )
        self.play(FadeOut(recap_group), run_time=0.8)

        # ══════════════════════════════════════════════════════════════════════
        # PARTE B — LiveSineFormula: variar A y k
        # ══════════════════════════════════════════════════════════════════════
        lf = LiveSineFormula(A_init=1.0, k_init=1.0)
        # No scale: always_redraw usa coordenadas absolutas del Axes,
        # escalar el VGroup padre rompería la sincronía de la curva.

        self.play(FadeIn(lf.formula), run_time=0.8)
        self.wait(0.5)
        self.play(Create(lf.axes), run_time=1.2)
        self.add(lf.curve)
        self.wait(1.0)

        # Subir amplitud A: 1 → 2  (onda se estira verticalmente)
        amp_label = Text("A ↑  onda más alta", color=HIGHLIGHT, font_size=FONT_LABEL)
        amp_label.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(amp_label), run_time=0.4)
        self.play(lf.set_amplitude(2.0), run_time=2.5)
        self.wait(1.5)
        self.play(FadeOut(amp_label), run_time=0.4)

        # Subir frecuencia k: 1 → 3  (onda se comprime horizontalmente)
        freq_label = Text("k ↑  onda más comprimida", color=ADJACENT, font_size=FONT_LABEL)
        freq_label.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(freq_label), run_time=0.4)
        self.play(lf.set_frequency(3.0), run_time=2.5)
        self.wait(1.5)
        self.play(FadeOut(freq_label), run_time=0.4)

        # Volver a valores base
        self.play(
            lf.set_amplitude(1.0),
            lf.set_frequency(1.0),
            run_time=1.5,
        )
        self.wait(1.0)

        self.play(FadeOut(lf), run_time=0.8)

        # ══════════════════════════════════════════════════════════════════════
        # PARTE C — Placeholder para clip de Pygame (~5 s)
        # ══════════════════════════════════════════════════════════════════════
        # NOTA DE EDICIÓN: reemplazar estos ~5 s por el clip de la simulación
        # de Pygame en CapCut/DaVinci. El fondo negro aquí funciona de slate.

        placeholder_rect = Rectangle(
            width=10, height=5.5,
            color=GRAY, fill_color=BLACK, fill_opacity=1,
            stroke_width=1.5,
        )
        placeholder_text = Text(
            "[ CLIP PYGAME AQUÍ ]",
            color=GRAY, font_size=FONT_FORMULA,
        )
        placeholder_group = VGroup(placeholder_rect, placeholder_text).center()

        self.play(FadeIn(placeholder_group), run_time=0.5)
        self.wait(5.0)   # ← 5 s de slate para insertar el clip en edición
        self.play(FadeOut(placeholder_group), run_time=0.5)
        self.wait(0.5)
