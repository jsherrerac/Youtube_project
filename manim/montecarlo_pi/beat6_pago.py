"""
Beat 6 — Pago y puente
Recap en 3 imágenes (puntos al azar → razón de áreas → el número π); imagen de
"otras aplicaciones" (forma irregular medida con puntos al azar); placeholder de
~5s para un clip de Pygame; cierre con handle DotCorzo. ~60s.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background, MonteCarloBoard, ArbitraryShape,
    MC_INSIDE, MC_OUTSIDE, MC_BORDER, MC_PI, FONT_TITLE, FONT_FORMULA,
)

np.random.seed(99)


class Beat6Pago(Scene):
    def construct(self):
        set_background(self)
        rng = np.random.default_rng(99)

        # ── Recap en 3 imágenes ───────────────────────────────────────────────
        # 1) Puntos al azar.
        p1 = VGroup(*[
            Dot([x, y, 0], radius=0.03,
                color=rng.choice([MC_INSIDE, MC_OUTSIDE]))
            for x, y in rng.uniform(-0.7, 0.7, size=(40, 2))
        ])
        # 2) Razón de áreas (mini tablero + sector).
        mini = MonteCarloBoard(side=1.5)
        sector = Sector(radius=1.5, start_angle=0, angle=PI / 2,
                        arc_center=mini.point(0, 0)).set_fill(MC_INSIDE, opacity=0.35).set_stroke(width=0)
        p2 = VGroup(mini, sector)
        # 3) El número π.
        p3 = Text("π", color=MC_PI, font_size=120)

        panels = VGroup(p1, p2, p3).arrange(RIGHT, buff=1.4).scale(0.9)
        arrows = VGroup(
            Text("→", color=MC_BORDER, font_size=60).move_to(
                (p1.get_right() + p2.get_left()) / 2),
            Text("→", color=MC_BORDER, font_size=60).move_to(
                (p2.get_right() + p3.get_left()) / 2),
        )
        self.play(FadeIn(p1), run_time=0.8)
        self.play(FadeIn(arrows[0]), FadeIn(p2), run_time=0.8)
        self.play(FadeIn(arrows[1]), FadeIn(p3), run_time=0.8)
        self.wait(1.5)
        self.play(FadeOut(panels), FadeOut(arrows), run_time=0.8)

        # ── Otras aplicaciones: ESTIMACIÓN EN VIVO del área de un blob ─────────
        caption = Text("la misma idea mide cualquier forma", color=MC_BORDER,
                       font_size=28).to_edge(UP, buff=0.7)
        # Blob sin fórmula de área conocida (semilla fija → reproducible).
        blob = ArbitraryShape(n_lobes=9, base_r=1.9, jitter=0.7,
                              rng=np.random.default_rng(99)).shift(LEFT * 2.6)
        # Bounding box de muestreo (rectángulo punteado tenue alrededor del blob).
        x0, x1, y0, y1 = blob.bbox()
        box = DashedVMobject(Rectangle(width=x1 - x0, height=y1 - y0,
                             color=MC_BORDER, stroke_width=1.5).move_to(
                             [(x0 + x1) / 2, (y0 + y1) / 2, 0]), num_dashes=48)
        self.play(FadeIn(caption), Create(blob), FadeIn(box), run_time=1.5)

        # Muestreo uniforme dentro del bbox; dentro del blob → cian, fuera → coral.
        N = 2000
        sample = np.c_[rng.uniform(x0, x1, N), rng.uniform(y0, y1, N)]
        ins = blob.contains(sample)
        box_area = (x1 - x0) * (y1 - y0)

        # Número de área en vivo (dorado), ligado a un ValueTracker de conteo.
        seen_tr = ValueTracker(0)
        def _area_label():
            k = int(seen_tr.get_value())
            frac = ins[:k].mean() if k > 0 else 0.0
            return Text(f"área ≈ {box_area * frac:.2f}", color=MC_PI,
                        font_size=FONT_FORMULA).to_edge(RIGHT, buff=1.2).shift(UP * 0.5)
        area_label = always_redraw(_area_label)
        real_lbl = Text(f"(real {blob.area():.2f})", color=MC_BORDER,
                        font_size=24).to_edge(RIGHT, buff=1.2).shift(DOWN * 0.3)
        self.add(area_label)

        # Lluvia en tandas: la nube llena el bbox y el número se estabiliza.
        dots = VGroup(*[
            Dot([x, y, 0], radius=0.025, color=MC_INSIDE if i else MC_OUTSIDE)
            for (x, y), i in zip(sample, ins)
        ])
        n_batches = 10
        step = N // n_batches
        for b in range(n_batches):
            lo, hi = b * step, (b + 1) * step
            self.play(FadeIn(dots[lo:hi], lag_ratio=0.0),
                      seen_tr.animate.set_value(hi),
                      run_time=0.35, rate_func=linear)
        self.play(FadeIn(real_lbl), run_time=0.6)
        self.wait(1.5)
        self.play(FadeOut(VGroup(blob, box, dots, caption, area_label, real_lbl)),
                  run_time=0.8)

        # ── Placeholder para clip de Pygame (~5s) ─────────────────────────────
        # TODO(edición): reemplazar este rectángulo por un clip MP4 de la
        # simulación de Pygame en CapCut. Dura ~5s a propósito.
        holder = Rectangle(width=8.0, height=4.5, color=MC_BORDER,
                           stroke_width=2).set_fill(BLACK, opacity=1.0)
        holder_border = DashedVMobject(holder.copy(), num_dashes=60).set_color(MC_BORDER)
        ph_text = Text("[ clip Pygame aquí ]", color=MC_BORDER, font_size=30)
        self.play(Create(holder_border), FadeIn(ph_text), run_time=1.0)
        self.wait(5.0)
        self.play(FadeOut(holder_border), FadeOut(ph_text), run_time=0.6)

        # ── Cierre ────────────────────────────────────────────────────────────
        handle = Text("DotCorzo", color=MC_PI, font_size=FONT_TITLE, weight=BOLD)
        tag = Text("donde la física se vuelve visible", color=MC_BORDER, font_size=28)
        closing = VGroup(handle, tag).arrange(DOWN, buff=0.4)
        self.play(Write(handle), run_time=1.0)
        self.play(FadeIn(tag, shift=UP * 0.2), run_time=0.8)
        self.wait(2.5)
