"""
Beat 5 — Convergencia · CLÍMAX
Lluvia rápida de miles de puntos; el cuadrado se llena de cian/coral dibujando
nítido el cuarto de círculo; el número de π (grande, dorado) hace tic hacia
3.14159; la línea de convergencia besa la línea punteada. Respira 2-3s al final.

RENDIMIENTO: no se anima un Create por punto. Se generan con numpy y se agregan
en lotes (FadeIn de VGroup). Los puntos VISIBLES se capan a ~3000; el contador y
la curva usan un N grande (cálculo numérico, sin dibujar) para converger nítido.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background, MonteCarloBoard, ConvergencePlot,
    MC_INSIDE, MC_OUTSIDE, MC_PI, MC_BORDER,
)

np.random.seed(42)

N_HIDDEN  = 60000   # para contador y curva (solo cálculo, no se dibuja)
N_VISIBLE = 3000    # puntos efectivamente renderizados (cap de rendimiento)
N_BATCHES = 15      # tandas de la lluvia


class Beat5Convergencia(Scene):
    def construct(self):
        set_background(self)
        rng = np.random.default_rng(42)

        # ── Muestra grande (numérica) para convergencia precisa ───────────────
        pts = rng.uniform(0.0, 1.0, size=(N_HIDDEN, 2))
        inside_mask = (pts[:, 0] ** 2 + pts[:, 1] ** 2) <= 1.0
        cum = np.cumsum(inside_mask)
        ns = np.arange(1, N_HIDDEN + 1)
        estimates = 4.0 * cum / ns
        final_est = estimates[-1]

        # ── Tablero a la izquierda ────────────────────────────────────────────
        board = MonteCarloBoard(side=5.0).to_edge(LEFT, buff=0.7)
        self.add(board)

        # Dots visibles (primeros N_VISIBLE), pre-agrupados por tanda.
        vis_pts, vis_in = pts[:N_VISIBLE], inside_mask[:N_VISIBLE]
        dots = VGroup(*[
            Dot(board.point(x, y), radius=0.022,
                color=MC_INSIDE if ins else MC_OUTSIDE)
            for (x, y), ins in zip(vis_pts, vis_in)
        ])

        # ── Número de π grande y dorado (arriba-derecha) ──────────────────────
        est_tr = ValueTracker(0.0)
        pi_num = always_redraw(lambda: Text(
            f"{est_tr.get_value():.5f}", color=MC_PI, font_size=72))
        pi_lbl = Text("π ≈", color=MC_PI, font_size=72)
        head = VGroup(pi_lbl, pi_num).arrange(RIGHT, buff=0.25).to_edge(UP, buff=0.7).shift(RIGHT * 1.5)
        self.add(pi_num)
        self.play(FadeIn(pi_lbl), run_time=0.4)

        # ── Curva de convergencia (abajo-derecha) ─────────────────────────────
        plot = ConvergencePlot(x_max=N_HIDDEN, y_range=(2.8, 3.5, 0.1),
                               width=5.0, height=2.6).to_edge(RIGHT, buff=0.7).to_edge(DOWN, buff=0.6)
        self.play(Create(plot.axes), Create(plot.pi_line), FadeIn(plot.pi_label), run_time=1.0)
        curve = VMobject(color=MC_PI, stroke_width=3)
        self.add(curve)

        # Checkpoints de N para sincronizar lluvia + contador + curva.
        checkpoints = np.linspace(0, N_HIDDEN, N_BATCHES + 1).astype(int)
        batch_size = N_VISIBLE // N_BATCHES

        # ── Lluvia rápida ─────────────────────────────────────────────────────
        for b in range(N_BATCHES):
            lo, hi = b * batch_size, (b + 1) * batch_size
            n_now = int(checkpoints[b + 1])
            new_curve = plot.curve_from(ns[:n_now:max(1, n_now // 400)],
                                        estimates[:n_now:max(1, n_now // 400)])
            self.play(
                FadeIn(dots[lo:hi], lag_ratio=0.0),
                est_tr.animate.set_value(estimates[n_now - 1]),
                Transform(curve, new_curve),
                run_time=0.45, rate_func=linear,
            )

        # ── Cierre: el número se asienta, la curva besa la línea de π ─────────
        self.play(est_tr.animate.set_value(final_est), run_time=0.8)
        target = Text("3.14159…", color=MC_PI, font_size=32).next_to(head, DOWN, buff=0.4)
        self.play(FadeIn(target), Flash(plot.pi_line.get_end(), color=MC_PI), run_time=1.0)

        # Respira sin texto nuevo.
        self.wait(3.0)
