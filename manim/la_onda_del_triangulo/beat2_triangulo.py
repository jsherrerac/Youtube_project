"""
Beat 2 — El triángulo rectángulo
Duración objetivo: ~60s
Parte A: Crea el triángulo, etiquetas coloreadas, ángulo alfa.
Parte B: Dos triángulos semejantes — misma razón O/H aunque tamaños distintos.
Parte C: Alpha varía → el número cambia, pero siempre es sin(alfa).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background,
    HYPOTENUSE, OPPOSITE, ADJACENT, HIGHLIGHT,
    STROKE_DEFAULT, FONT_LABEL, FONT_FORMULA, FONT_TITLE,
    ColorCodedRightTriangle,
)


def _frac(numer_text, numer_color, denom_text, denom_color, font_size=FONT_FORMULA):
    """Fracción visual con línea horizontal."""
    n = Text(numer_text, color=numer_color, font_size=font_size)
    d = Text(denom_text, color=denom_color, font_size=font_size)
    w = max(n.width, d.width) + 0.3
    line = Line(LEFT * w / 2, RIGHT * w / 2, color=WHITE, stroke_width=2)
    n.next_to(line, UP, buff=0.12)
    d.next_to(line, DOWN, buff=0.12)
    return VGroup(n, line, d)


class Beat2Triangulo(Scene):
    def construct(self):
        set_background(self)
        self.wait(0.5)

        # ══════════════════════════════════════════════════════════════════════
        # PARTE A — Presentar el triángulo
        # ══════════════════════════════════════════════════════════════════════
        tri = ColorCodedRightTriangle(alpha=PI / 4, hyp_length=2.8).center()

        self.play(Create(tri.adj_line), Create(tri.opp_line), run_time=1.2)
        self.play(Create(tri.hyp_line), run_time=0.8)
        self.play(FadeIn(tri._right_sq), run_time=0.5)
        self.play(
            FadeIn(tri.angle_arc),
            FadeIn(tri.angle_label),
            run_time=0.8,
        )
        self.play(FadeIn(tri.side_labels), run_time=0.8)
        self.wait(2.0)

        # ══════════════════════════════════════════════════════════════════════
        # PARTE B — Dos triángulos semejantes, misma razón O/H
        # ══════════════════════════════════════════════════════════════════════
        self.play(FadeOut(tri), run_time=0.6)

        tri_big = ColorCodedRightTriangle(
            alpha=PI / 4, hyp_length=3.0, show_labels=False
        ).center().shift(RIGHT * 2.8)

        tri_sml = ColorCodedRightTriangle(
            alpha=PI / 4, hyp_length=1.5, show_labels=False
        ).center().shift(LEFT * 3.2)

        self.play(GrowFromCenter(tri_big), GrowFromCenter(tri_sml), run_time=1.5)
        self.wait(1.0)

        # Etiqueta "mismo alfa" sobre ambos
        label_alfa = Text("mismo α", color=HIGHLIGHT, font_size=FONT_LABEL)
        label_alfa.to_edge(UP, buff=0.4)
        self.play(Write(label_alfa), run_time=0.8)
        self.wait(0.8)

        # Razón O/H para cada triángulo
        ratio_val = np.sin(PI / 4)   # ≈ 0.707 para ambos

        frac_big = _frac("O", OPPOSITE, "H", HYPOTENUSE).next_to(tri_big, DOWN, buff=0.4)
        frac_sml = _frac("O", OPPOSITE, "H", HYPOTENUSE).next_to(tri_sml, DOWN, buff=0.4)

        self.play(FadeIn(frac_big), FadeIn(frac_sml), run_time=0.8)
        self.wait(0.6)

        # Números resultado — IGUALES en ambos
        eq_big = Text("= 0.707", color=OPPOSITE, font_size=FONT_FORMULA).next_to(frac_big, RIGHT, buff=0.2)
        eq_sml = Text("= 0.707", color=OPPOSITE, font_size=FONT_FORMULA).next_to(frac_sml, RIGHT, buff=0.2)

        self.play(Write(eq_big), Write(eq_sml), run_time=1.0)
        self.wait(1.0)

        # Resaltar igualdad — recuadros alrededor de los 0.707
        box_big = SurroundingRectangle(eq_big, color=HIGHLIGHT, buff=0.08)
        box_sml = SurroundingRectangle(eq_sml, color=HIGHLIGHT, buff=0.08)
        self.play(Create(box_big), Create(box_sml), run_time=0.8)
        self.wait(2.0)

        # Limpiar para Parte C
        self.play(
            FadeOut(VGroup(
                tri_big, tri_sml, label_alfa,
                frac_big, frac_sml, eq_big, eq_sml, box_big, box_sml,
            )),
            run_time=0.8,
        )

        # ══════════════════════════════════════════════════════════════════════
        # PARTE C — Alpha varía → el número cambia (pero siempre es sin(alfa))
        # ══════════════════════════════════════════════════════════════════════
        tri = ColorCodedRightTriangle(alpha=PI / 4, hyp_length=2.8, show_labels=False).center()
        self.play(GrowFromCenter(tri), run_time=1.0)

        # Etiqueta "sin(α) =" fija + DecimalNumber que se actualiza
        sin_label = Text("sin(α)  =", color=OPPOSITE, font_size=FONT_FORMULA)
        sin_num   = DecimalNumber(
            np.sin(PI / 4), num_decimal_places=3,
            mob_class=Text, color=OPPOSITE, font_size=FONT_FORMULA,
        )
        ratio_row = VGroup(sin_label, sin_num).arrange(RIGHT, buff=0.18)
        ratio_row.to_edge(DOWN, buff=0.7)

        self.play(FadeIn(ratio_row), run_time=0.6)
        self.wait(0.8)

        # Discreto: transform a distintos alfa + actualizar número
        for new_alpha in [PI / 6, PI / 3, PI / 2, PI / 4]:
            new_tri = ColorCodedRightTriangle(
                alpha=new_alpha, hyp_length=2.8, show_labels=False
            ).center()
            new_num = DecimalNumber(
                np.sin(new_alpha), num_decimal_places=3,
                mob_class=Text, color=OPPOSITE, font_size=FONT_FORMULA,
            ).next_to(sin_label, RIGHT, buff=0.18).align_to(sin_num, DOWN)

            self.play(
                Transform(tri, new_tri),
                Transform(sin_num, new_num),
                run_time=1.8,
            )
            self.wait(1.0)

        self.wait(1.5)
        self.play(FadeOut(VGroup(tri, ratio_row)), run_time=0.8)
        self.wait(0.5)
