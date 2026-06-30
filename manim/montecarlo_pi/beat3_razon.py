"""
Beat 3 — La razón escondida
Sombreá el cuarto de círculo (cian translúcido) vs el cuadrado; mostrá la razón
(área círculo)/(área cuadrado) = (π/4)/1; construí π ≈ 4·(dentro/total) y
evalualo con los conteos del beat 2 (valor todavía impreciso). ~60s.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background, MonteCarloBoard, MC_INSIDE, MC_OUTSIDE, MC_BORDER, MC_PI,
    FONT_FORMULA,
)

np.random.seed(11)


class Beat3Razon(Scene):
    def construct(self):
        set_background(self)

        # Mismos puntos/seed que el beat 2 → conteo consistente (impreciso).
        rng = np.random.default_rng(11)
        pts = rng.uniform(0.0, 1.0, size=(11, 2))
        inside_mask = (pts[:, 0] ** 2 + pts[:, 1] ** 2) <= 1.0
        n_in, n_tot = int(inside_mask.sum()), len(pts)

        board = MonteCarloBoard(side=4.2).to_edge(LEFT, buff=1.0)
        corner = board.point(0, 0)
        self.play(FadeIn(board), run_time=0.8)

        # ── Sombreado de áreas ────────────────────────────────────────────────
        sq_fill = board.square.copy().set_fill(MC_BORDER, opacity=0.10).set_stroke(width=0)
        sector = Sector(radius=board.side, start_angle=0, angle=PI / 2,
                        arc_center=corner).set_fill(MC_INSIDE, opacity=0.35).set_stroke(width=0)
        self.play(FadeIn(sq_fill), run_time=0.6)
        self.play(FadeIn(sector), run_time=1.0)
        self.wait(0.4)

        # ── Razón de áreas ────────────────────────────────────────────────────
        ratio = VGroup(
            Text("área círculo", color=MC_INSIDE, font_size=26),
            Line(LEFT * 1.3, RIGHT * 1.3, color=MC_BORDER, stroke_width=2),
            Text("área cuadrado", color=MC_BORDER, font_size=26),
            Text("=   (π/4) / 1   =   π/4", t2c={"π": MC_PI}, font_size=30),
        )
        ratio[:3].arrange(DOWN, buff=0.15)
        ratio[3].next_to(ratio[:3], RIGHT, buff=0.4)
        ratio.to_edge(RIGHT, buff=0.8).shift(UP * 1.5)
        self.play(Write(ratio), run_time=2.0)
        self.wait(0.6)

        # ── De la razón a la estimación: π ≈ 4·(dentro/total) ─────────────────
        formula = Text("π  ≈  4 · ( dentro / total )",
                       t2c={"π": MC_PI, "dentro": MC_INSIDE},
                       font_size=FONT_FORMULA).next_to(ratio, DOWN, buff=1.0)
        self.play(Write(formula), run_time=1.6)
        self.wait(0.4)

        # ── Evaluación con los conteos del beat 2 ─────────────────────────────
        est = 4.0 * n_in / n_tot
        evaluated = Text(f"π  ≈  4 · ( {n_in} / {n_tot} )  =  {est:.2f}",
                         t2c={"π": MC_PI, f"{est:.2f}": MC_PI, f" {n_in} ": MC_INSIDE},
                         font_size=FONT_FORMULA).next_to(formula, DOWN, buff=0.9)
        self.play(TransformFromCopy(formula, evaluated), run_time=1.6)

        # Nota: todavía impreciso (pocos puntos).
        note = Text("(pocos puntos → impreciso)", color=MC_OUTSIDE, font_size=22).next_to(
            evaluated, DOWN, buff=0.4).align_to(evaluated, LEFT)
        self.play(FadeIn(note), run_time=0.8)
        self.wait(2.0)
