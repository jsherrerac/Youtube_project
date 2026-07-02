"""
Beat 4.5 — "No fue suerte"
Tres semillas distintas (1, 2, 3) sobre UNA sola ConvergencePlot. Las tres
arrancan caóticas y separadas con N pequeño (izquierda) y se aprietan hacia la
MISMA línea punteada dorada de π (derecha). Mismo "dorado familia π", solo varía
el tono/alpha para distinguirlas. Destello suave en el encuentro. ~28s.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background, ConvergencePlot, MC_PI, MC_BORDER, FONT_TITLE,
)

np.random.seed(123)

SEEDS = [1, 2, 3]          # semillas fijas → reproducible
N_MAX = 1500               # N donde las tres ya tocan π
STRIDE = max(1, N_MAX // 400)  # submuestreo para polilíneas livianas


class Beat45Robustez(Scene):
    def construct(self):
        set_background(self)

        # ── Tres series de convergencia, una por semilla ──────────────────────
        ns = np.arange(1, N_MAX + 1)
        series = []
        for s in SEEDS:
            rng = np.random.default_rng(s)
            pts = rng.uniform(0.0, 1.0, size=(N_MAX, 2))
            inside = (pts[:, 0] ** 2 + pts[:, 1] ** 2) <= 1.0
            est = 4.0 * np.cumsum(inside) / ns
            series.append(est[::STRIDE])
        ns_s = ns[::STRIDE]

        # Tonos "familia π": dorado puro + dos mezclas suaves, todos legibles.
        colors = [
            MC_PI,
            interpolate_color(MC_PI, WHITE, 0.45),
            interpolate_color(MC_PI, ORANGE, 0.45),
        ]

        # ── Título ────────────────────────────────────────────────────────────
        title = Text("No fue suerte", color=MC_BORDER, font_size=FONT_TITLE).to_edge(UP, buff=0.6)
        self.play(Write(title), run_time=1.2)

        # ── Una sola gráfica, ejes amplios ────────────────────────────────────
        plot = ConvergencePlot(x_max=N_MAX, y_range=(2.4, 3.8, 0.2),
                               width=9.5, height=4.6).shift(DOWN * 0.4)
        self.play(Create(plot.axes), Create(plot.pi_line), FadeIn(plot.pi_label), run_time=1.4)

        # ── Las tres curvas se dibujan a la vez (Create = izq→der: caos→π) ─────
        curves = plot.multi_curve_from(ns_s, series, colors, stroke_width=3.5)
        for c, a in zip(curves, (1.0, 0.85, 0.85)):
            c.set_stroke(opacity=a)
        self.play(Create(curves), run_time=18.0, rate_func=linear)

        # ── Encuentro en π: destello suave + leyenda ──────────────────────────
        meet = plot.pi_line.get_end()
        legend = Text("3 semillas distintas → mismo π", color=MC_PI, font_size=28).next_to(
            plot.axes, DOWN, buff=0.3)
        self.play(Flash(meet, color=MC_PI, line_length=0.35, num_lines=16),
                  FadeIn(legend), run_time=1.5)
        self.wait(2.0)
