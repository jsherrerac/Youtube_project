"""
Beat 2 — La razón que no cambia
Duración objetivo: 13s exactos
Parte A (6s): triángulo coloreado crece y encoge, α = π/4 fijo → sin(α) = 0.707.
Parte B (7s): α varía → sin(α) sube, baja, llega a ~1 (línea), vuelve a 0.707.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import set_background, HYPOTENUSE, OPPOSITE, ADJACENT, HIGHLIGHT, FONT_FORMULA


class Beat2Ratio(Scene):
    def construct(self):
        set_background(self)

        alpha_t = ValueTracker(PI / 4)
        hyp_t   = ValueTracker(2.5)

        def make_tri():
            a        = alpha_t.get_value()
            H        = hyp_t.get_value()
            ca, sa   = np.cos(a), np.sin(a)
            opp_len  = H * sa
            adj_len  = H * ca

            # Vértices centrados en ORIGIN
            A = np.array([-2*adj_len/3, -opp_len/3, 0])   # inferior-izq  (α)
            B = np.array([ adj_len/3,   -opp_len/3, 0])   # inferior-der  (90°)
            C = np.array([ adj_len/3,  2*opp_len/3, 0])   # superior-der

            parts = [
                Line(A, C, color=HYPOTENUSE, stroke_width=3),   # hipotenusa
                Line(A, B, color=ADJACENT,   stroke_width=3),   # adyacente
                Line(B, C, color=OPPOSITE,   stroke_width=3),   # opuesto
            ]

            # Cuadrado ángulo recto (desaparece cuando el triángulo es casi una línea)
            if adj_len > 0.25:
                sq = min(0.13, adj_len * 0.5, opp_len * 0.22)
                parts.append(Polygon(
                    B, B+UP*sq, B+UP*sq+LEFT*sq, B+LEFT*sq,
                    color=HYPOTENUSE, stroke_width=2, fill_opacity=0,
                ))

            # Arco y label α
            if adj_len > 0.4:
                arc_r = min(0.30, adj_len * 0.38)
                arc = Arc(radius=arc_r, start_angle=0, angle=a,
                          color=HIGHLIGHT, stroke_width=2).shift(A)
                mid   = a / 2
                pos   = A + np.array([np.cos(mid), np.sin(mid), 0]) * (arc_r + 0.24)
                lbl   = Text("α", color=HIGHLIGHT, font_size=26).move_to(pos)
                parts.extend([arc, lbl])

            return VGroup(*parts)

        tri     = always_redraw(make_tri)
        sin_lbl = Text("sin(α)  =", color=OPPOSITE, font_size=FONT_FORMULA)
        sin_lbl.move_to(DOWN * 3.0 + LEFT * 1.05)
        sin_num = always_redraw(
            lambda: Text(
                f"{np.sin(alpha_t.get_value()):.3f}",
                color=HIGHLIGHT, font_size=FONT_FORMULA,
            ).next_to(sin_lbl, RIGHT, buff=0.15)
        )

        self.add(tri, sin_lbl, sin_num)

        # ── Fase 1: tamaño sube y baja, α fijo = π/4  (6s) ──────────────────
        self.play(hyp_t.animate.set_value(4.5), run_time=2.0, rate_func=smooth)
        self.play(hyp_t.animate.set_value(1.0), run_time=2.0, rate_func=smooth)
        self.play(hyp_t.animate.set_value(2.5), run_time=2.0, rate_func=smooth)

        # ── Fase 2: α varía  (7s) ────────────────────────────────────────────
        self.play(alpha_t.animate.set_value(5*PI/12),    run_time=1.5, rate_func=smooth)  # 75° → sin ≈ 0.966
        self.play(alpha_t.animate.set_value(PI/12),      run_time=1.5, rate_func=smooth)  # 15° → sin ≈ 0.259
        self.play(alpha_t.animate.set_value(PI/2 - 0.04),run_time=1.5, rate_func=smooth)  # ~90° → línea, sin ≈ 0.999
        self.play(alpha_t.animate.set_value(PI/4),       run_time=2.5, rate_func=smooth)  # vuelve 45° → 0.707
        # Total: 6 + 7 = 13s ✓
