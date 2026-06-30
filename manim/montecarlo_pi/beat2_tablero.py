"""
Beat 2 — El tablero
Create del cuadrado (lado 1) y del cuarto de círculo (radio 1). Soltá un punto,
dibujá el segmento de su distancia a la esquina y compáralo con el radio
(dentro→cian, fuera→coral). Repetí con ~10 puntos uno a uno. ~60s.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background, MonteCarloBoard, MC_INSIDE, MC_OUTSIDE, MC_BORDER,
    STROKE_DEFAULT, STROKE_THIN, FONT_LABEL,
)

np.random.seed(11)


class Beat2Tablero(Scene):
    def construct(self):
        set_background(self)
        rng = np.random.default_rng(11)

        board = MonteCarloBoard(side=5.0).shift(LEFT * 1.2)
        corner = board.point(0, 0)  # esquina-origen (centro del cuarto de círculo)

        # ── Construir el tablero ──────────────────────────────────────────────
        self.play(Create(board.square), run_time=1.5)
        lbl_side = Text("1", color=MC_BORDER, font_size=FONT_LABEL).next_to(
            board.square, DOWN, buff=0.2)
        self.play(FadeIn(lbl_side), run_time=0.4)
        self.play(Create(board.quarter), run_time=1.8)

        # Radio de referencia (= 1) dibujado desde la esquina.
        radius_ref = Line(corner, board.point(1, 0), color=MC_BORDER,
                          stroke_width=STROKE_THIN)
        lbl_r = Text("r = 1", color=MC_BORDER, font_size=FONT_LABEL).next_to(
            radius_ref, UP, buff=0.15)
        self.play(Create(radius_ref), FadeIn(lbl_r), run_time=0.8)
        self.wait(0.5)
        self.play(FadeOut(radius_ref), FadeOut(lbl_r), run_time=0.5)

        # ── Puntos uno a uno: distancia a la esquina vs radio ─────────────────
        pts = rng.uniform(0.0, 1.0, size=(11, 2))
        inside = (pts[:, 0] ** 2 + pts[:, 1] ** 2) <= 1.0

        for k, ((x, y), ins) in enumerate(zip(pts, inside)):
            p = board.point(x, y)
            dot = Dot(p, radius=0.06, color=MC_BORDER)
            seg = Line(corner, p, color=MC_BORDER, stroke_width=STROKE_THIN)
            col = MC_INSIDE if ins else MC_OUTSIDE

            if k < 3:
                # Tratamiento completo en los primeros: aparece, mide, decide.
                self.play(FadeIn(dot, scale=0.4), run_time=0.4)
                self.play(Create(seg), run_time=0.6)
                self.wait(0.3)
                self.play(dot.animate.set_color(col),
                          seg.animate.set_color(col), run_time=0.4)
                self.play(FadeOut(seg), run_time=0.4)
            else:
                # Más ágil: flash del segmento y se colorea.
                self.play(FadeIn(dot, scale=0.4),
                          Create(seg), run_time=0.35)
                self.play(dot.animate.set_color(col),
                          FadeOut(seg), run_time=0.3)

        self.wait(1.5)
