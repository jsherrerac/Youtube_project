"""
Beat 3 — De razón a función
Duración objetivo: ~60s
Parte A: Muestra O/H como fracción, idea "ángulo → número".
Parte B: Define sin(α) en azul y cos(α) en verde.
Parte C: Fija H=1 → sin(α) es literalmente la longitud del cateto opuesto.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background,
    HYPOTENUSE, OPPOSITE, ADJACENT, HIGHLIGHT,
    STROKE_DEFAULT, STROKE_THICK, FONT_LABEL, FONT_FORMULA, FONT_TITLE,
    ColorCodedRightTriangle,
)


def _frac(n_str, n_col, d_str, d_col, fs=FONT_FORMULA):
    n = Text(n_str, color=n_col, font_size=fs)
    d = Text(d_str, color=d_col, font_size=fs)
    w = max(n.width, d.width) + 0.3
    line = Line(LEFT * w / 2, RIGHT * w / 2, color=WHITE, stroke_width=2)
    n.next_to(line, UP, buff=0.12)
    d.next_to(line, DOWN, buff=0.12)
    return VGroup(n, line, d)


class Beat3Funcion(Scene):
    def construct(self):
        set_background(self)
        self.wait(0.5)

        ALPHA = PI / 4    # ángulo fijo para toda la escena (salvo Parte C)

        # ══════════════════════════════════════════════════════════════════════
        # PARTE A — La razón O/H da un número; ese número depende de alfa
        # ══════════════════════════════════════════════════════════════════════
        tri = ColorCodedRightTriangle(alpha=ALPHA, hyp_length=2.6, show_labels=True).center()
        self.play(GrowFromCenter(tri), run_time=1.2)
        self.wait(0.8)

        # Fracción O/H a la derecha
        frac = _frac("Opuesto", OPPOSITE, "Hipotenusa", HYPOTENUSE, fs=32)
        frac.shift(RIGHT * 3.8)
        self.play(FadeIn(frac), run_time=0.8)
        self.wait(0.8)

        # Resultado numérico
        result = VGroup(
            Text("=", color=WHITE, font_size=FONT_FORMULA),
            DecimalNumber(np.sin(ALPHA), num_decimal_places=3,
                          mob_class=Text, color=OPPOSITE, font_size=FONT_FORMULA),
        ).arrange(RIGHT, buff=0.15)
        result.next_to(frac, DOWN, buff=0.45)
        self.play(FadeIn(result), run_time=0.8)
        self.wait(1.2)

        # Flecha: "ángulo" → "número"
        box_angle = SurroundingRectangle(tri.angle_label, color=HIGHLIGHT, buff=0.15)
        box_num   = SurroundingRectangle(result, color=OPPOSITE, buff=0.12)
        arrow_fn  = CurvedArrow(
            box_angle.get_right() + RIGHT * 0.1,
            box_num.get_left()   + LEFT  * 0.1,
            color=WHITE, angle=-TAU / 6,
        )
        self.play(Create(box_angle), run_time=0.5)
        self.play(Create(arrow_fn), run_time=0.8)
        self.play(Create(box_num), run_time=0.5)
        self.wait(2.0)

        self.play(
            FadeOut(VGroup(tri, frac, result, box_angle, box_num, arrow_fn)),
            run_time=0.8,
        )

        # ══════════════════════════════════════════════════════════════════════
        # PARTE B — Definición de sin(α) y cos(α)
        # ══════════════════════════════════════════════════════════════════════
        tri2 = ColorCodedRightTriangle(alpha=ALPHA, hyp_length=2.6, show_labels=False).center()
        self.play(GrowFromCenter(tri2), run_time=1.0)
        self.wait(0.5)

        # sin(α) = O/H  en azul
        sin_lhs = Text("sin(α)  =", color=OPPOSITE, font_size=FONT_FORMULA)
        sin_frac = _frac("O", OPPOSITE, "H", HYPOTENUSE)
        sin_def  = VGroup(sin_lhs, sin_frac).arrange(RIGHT, buff=0.25)
        sin_def.shift(RIGHT * 3.5 + UP * 0.8)

        self.play(Write(sin_def), run_time=1.2)
        # Resaltar cateto opuesto en el triángulo
        self.play(tri2.opp_line.animate.set_stroke(width=7), run_time=0.6)
        self.wait(1.2)
        self.play(tri2.opp_line.animate.set_stroke(width=STROKE_DEFAULT), run_time=0.3)

        # cos(α) = A/H  en verde
        cos_lhs  = Text("cos(α)  =", color=ADJACENT, font_size=FONT_FORMULA)
        cos_frac = _frac("A", ADJACENT, "H", HYPOTENUSE)
        cos_def  = VGroup(cos_lhs, cos_frac).arrange(RIGHT, buff=0.25)
        cos_def.shift(RIGHT * 3.5 + DOWN * 0.8)

        self.play(Write(cos_def), run_time=1.2)
        self.play(tri2.adj_line.animate.set_stroke(width=7), run_time=0.6)
        self.wait(1.2)
        self.play(tri2.adj_line.animate.set_stroke(width=STROKE_DEFAULT), run_time=0.3)
        self.wait(1.5)

        self.play(FadeOut(VGroup(tri2, sin_def, cos_def)), run_time=0.8)

        # ══════════════════════════════════════════════════════════════════════
        # PARTE C — Fijar H=1 → sin(α) ES la longitud del opuesto
        # ══════════════════════════════════════════════════════════════════════
        # Triángulo con H=1 (hipotenusa corta, la escalamos visualmente a 2.5)
        # La lógica: si H = 1 entonces O = sin(α).
        # Mostramos el triángulo normal y luego la igualdad.

        tri3 = ColorCodedRightTriangle(alpha=ALPHA, hyp_length=2.5, show_labels=False).center()
        # Etiqueta H=1 sobre la hipotenusa
        h_label = Text("H = 1", color=HYPOTENUSE, font_size=FONT_LABEL)
        h_label.next_to(tri3.hyp_line.get_center(), UL, buff=0.2)

        self.play(GrowFromCenter(tri3), run_time=1.0)
        self.play(FadeIn(h_label), run_time=0.6)
        self.wait(0.8)

        # Ecuación: sin(α) = O/1 = O
        eq_collapse = VGroup(
            Text("sin(α)  =", color=OPPOSITE, font_size=FONT_FORMULA),
            _frac("O", OPPOSITE, "1", HYPOTENUSE),
            Text("=  O", color=OPPOSITE, font_size=FONT_FORMULA),
        ).arrange(RIGHT, buff=0.25)
        eq_collapse.to_edge(DOWN, buff=0.8)

        self.play(Write(eq_collapse), run_time=1.5)
        self.wait(1.0)

        # Pulso en el cateto opuesto — "esto es literalmente la longitud"
        for _ in range(2):
            self.play(tri3.opp_line.animate.set_stroke(width=8, color=HIGHLIGHT), run_time=0.35)
            self.play(tri3.opp_line.animate.set_stroke(width=STROKE_DEFAULT, color=OPPOSITE), run_time=0.35)

        # Etiqueta "sin(α)" directamente sobre el cateto opuesto
        opp_tag = Text("sin(α)", color=OPPOSITE, font_size=FONT_LABEL)
        opp_tag.next_to(tri3.opp_line.get_center(), RIGHT, buff=0.25)
        self.play(FadeIn(opp_tag), run_time=0.6)
        self.wait(1.5)

        # Vary alpha para mostrar que la longitud de la barra azul cambia con alfa
        for new_alpha in [PI / 6, PI / 3, PI / 5]:
            new_tri = ColorCodedRightTriangle(
                alpha=new_alpha, hyp_length=2.5, show_labels=False
            ).center()
            new_h  = Text("H = 1", color=HYPOTENUSE, font_size=FONT_LABEL)
            new_h.next_to(new_tri.hyp_line.get_center(), UL, buff=0.2)
            new_tag = Text("sin(α)", color=OPPOSITE, font_size=FONT_LABEL)
            new_tag.next_to(new_tri.opp_line.get_center(), RIGHT, buff=0.25)

            self.play(
                Transform(tri3, new_tri),
                Transform(h_label, new_h),
                Transform(opp_tag, new_tag),
                run_time=1.8,
            )
            self.wait(0.8)

        self.wait(1.5)
        self.play(FadeOut(VGroup(tri3, h_label, opp_tag, eq_collapse)), run_time=0.8)
        self.wait(0.5)
