"""
Beat 1.2 — Los tres tipos de triángulo
Duración objetivo: 13s exactos
Un triángulo rectángulo blanco crece desde el centro (5s),
luego se "multiplica" y se separa en tres: equilátero, isósceles, escaleno.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import set_background, FONT_LABEL, FONT_FORMULA


POS_L = LEFT  * 4.5
POS_C = ORIGIN
POS_R = RIGHT * 4.5


def _right_tri(center=ORIGIN, s=1.5):
    """Triángulo rectángulo: ángulo recto abajo-derecha, sin colores."""
    return Polygon(
        center + np.array([-s, -s, 0]),   # inferior izquierdo (ángulo α)
        center + np.array([ s, -s, 0]),   # inferior derecho   (ángulo recto)
        center + np.array([ s,  s, 0]),   # superior derecho
        color=WHITE, stroke_width=3, fill_opacity=0,
    )


def _equilateral(center=ORIGIN, side=2.8):
    h = side * np.sqrt(3) / 2
    return Polygon(
        center + np.array([      0,  h * 2/3, 0]),
        center + np.array([ side/2, -h * 1/3, 0]),
        center + np.array([-side/2, -h * 1/3, 0]),
        color=WHITE, stroke_width=3, fill_opacity=0,
    )


def _isosceles(center=ORIGIN):
    return Polygon(
        center + np.array([  0.0,  1.8, 0]),   # vértice superior (eje de simetría)
        center + np.array([ 1.4, -1.1, 0]),
        center + np.array([-1.4, -1.1, 0]),
        color=WHITE, stroke_width=3, fill_opacity=0,
    )


def _scalene(center=ORIGIN):
    """Todos los lados distintos — claramente asimétrico."""
    return Polygon(
        center + np.array([-0.4,  1.5, 0]),
        center + np.array([ 1.5, -1.0, 0]),
        center + np.array([-1.3, -0.3, 0]),
        color=WHITE, stroke_width=3, fill_opacity=0,
    )


class Beat12(Scene):
    def construct(self):
        set_background(self)

        # ── Fase 1: negro (1s) ────────────────────────────────────────────────
        self.wait(1.0)

        # ── Fase 2: triángulo rectángulo crece desde el centro (5s) ──────────
        tri = _right_tri(ORIGIN, s=1.5)
        self.play(GrowFromCenter(tri), run_time=5.0)

        # ── Fase 3: se multiplica y transforma (3s) ───────────────────────────
        # Crear copias superpuestas para el efecto "multiplicación"
        copy_l = tri.copy()
        copy_r = tri.copy()
        self.add(copy_l, copy_r)

        # Triángulos destino
        eq  = _equilateral(POS_L, side=2.8)
        iso = _isosceles(POS_C)
        sca = _scalene(POS_R)

        self.play(
            Transform(copy_l, eq),    # izquierda → equilátero
            Transform(tri,    iso),   # centro    → isósceles
            Transform(copy_r, sca),   # derecha   → escaleno
            run_time=3.0,
            rate_func=smooth,
        )

        # ── Fase 4: etiquetas (1.5s write + 2.5s hold = 4s) ─────────────────
        lbl_l = Text("Equilátero", color=WHITE, font_size=FONT_FORMULA)
        lbl_c = Text("Isósceles",  color=WHITE, font_size=FONT_FORMULA)
        lbl_r = Text("Escaleno",   color=WHITE, font_size=FONT_FORMULA)

        lbl_l.next_to(eq,  UP, buff=0.4)
        lbl_c.next_to(iso, UP, buff=0.4)
        lbl_r.next_to(sca, UP, buff=0.4)

        self.play(
            Write(lbl_l), Write(lbl_c), Write(lbl_r),
            run_time=1.5,
        )
        self.wait(2.5)
        # Total: 1 + 5 + 3 + 1.5 + 2.5 = 13s
