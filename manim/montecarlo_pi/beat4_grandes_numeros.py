"""
Beat 4 — Ley de los grandes números
Puntos en tandas (10 → salta lejos de π; 100 → se acerca; 1000 → casi le apunta),
con el contador de π actualizándose. ConvergencePlot al lado mostrando la
estimación vs N temblando y apretándose hacia la línea punteada de π. ~70s.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background, MonteCarloBoard, sample_points, pi_counter, ConvergencePlot,
    MC_PI, MC_BORDER,
)

np.random.seed(23)

N_MAX = 1000
STAGES = [10, 100, 1000]


class Beat4GrandesNumeros(Scene):
    def construct(self):
        set_background(self)
        rng = np.random.default_rng(23)

        # ── Tablero a la izquierda ────────────────────────────────────────────
        board = MonteCarloBoard(side=4.2).to_edge(LEFT, buff=0.8).shift(DOWN * 0.3)
        self.play(FadeIn(board), run_time=0.6)

        # Todos los puntos de una, revelados por tandas (orden fijo).
        all_dots, pts, inside_mask = sample_points(board, N_MAX, rng, dot_radius=0.028)

        # Estimación acumulada (para la curva y el contador).
        cum_inside = np.cumsum(inside_mask)
        ns = np.arange(1, N_MAX + 1)
        estimates = 4.0 * cum_inside / ns

        # ── Contador de π en vivo (arriba) ────────────────────────────────────
        inside_tr = ValueTracker(0)
        total_tr = ValueTracker(0)
        counter = pi_counter(inside_tr, total_tr)
        lbl = Text("π ≈", color=MC_PI, font_size=44)
        head = VGroup(lbl, counter).arrange(RIGHT, buff=0.2).to_edge(UP, buff=0.6).shift(LEFT * 3.5)
        n_label = always_redraw(lambda: Text(
            f"N = {int(total_tr.get_value())}", color=MC_BORDER, font_size=24
        ).next_to(head, DOWN, buff=0.3).align_to(head, LEFT))
        self.add(counter, n_label)
        self.play(FadeIn(lbl), run_time=0.4)

        # ── Gráfica de convergencia a la derecha ──────────────────────────────
        plot = ConvergencePlot(x_max=N_MAX, width=5.2, height=3.4).to_edge(RIGHT, buff=0.7).shift(DOWN * 0.3)
        self.play(Create(plot.axes), Create(plot.pi_line), FadeIn(plot.pi_label), run_time=1.2)

        curve = VMobject(color=MC_PI, stroke_width=3)
        self.add(curve)

        # ── Tandas ────────────────────────────────────────────────────────────
        prev = 0
        for stage in STAGES:
            batch = all_dots[prev:stage]
            # Revela la tanda de golpe (no Create individual → barato).
            self.play(FadeIn(batch, lag_ratio=0.0, scale=0.5), run_time=0.8)
            # Actualiza contador.
            self.play(
                inside_tr.animate.set_value(int(cum_inside[stage - 1])),
                total_tr.animate.set_value(stage),
                run_time=0.6,
            )
            # Extiende la curva de convergencia hasta este N (temblando→apretando).
            new_curve = plot.curve_from(ns[:stage], estimates[:stage])
            self.play(Transform(curve, new_curve), run_time=1.6)
            self.wait(0.8)
            prev = stage

        self.wait(1.5)
