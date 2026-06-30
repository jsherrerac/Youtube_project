"""
Beat 1 — Hook
Puntos cayendo al azar sobre negro, sin estructura. Al final aparece tenue
el cuadrado + cuarto de círculo (preview de lo que viene). ~20-25s.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import set_background, MonteCarloBoard, MC_INSIDE, MC_OUTSIDE

np.random.seed(7)


class Beat1Hook(Scene):
    def construct(self):
        set_background(self)
        rng = np.random.default_rng(7)

        # ── Lluvia de puntos al azar, sin estructura ──────────────────────────
        # Puntos dispersos por toda la pantalla, colores alternando sin sentido aún.
        n = 120
        xs = rng.uniform(-6.5, 6.5, n)
        ys = rng.uniform(-3.6, 3.6, n)
        cols = rng.choice([MC_INSIDE, MC_OUTSIDE], size=n)
        dots = VGroup(*[
            Dot([x, y, 0.0], radius=0.04, color=c)
            for x, y, c in zip(xs, ys, cols)
        ])

        # Caen en tandas rápidas, como ruido.
        self.wait(0.4)
        order = rng.permutation(n)
        batch = 12
        for i in range(0, n, batch):
            idx = order[i:i + batch]
            self.play(
                *[FadeIn(dots[j], scale=0.3) for j in idx],
                run_time=0.35, rate_func=rush_into,
            )
        self.wait(0.8)

        # ── Preview tenue del tablero naciendo entre el ruido ─────────────────
        board = MonteCarloBoard(side=5.0).set_opacity(0.0)
        self.add(board)
        self.play(board.animate.set_opacity(0.35), run_time=2.0)
        self.wait(2.0)
