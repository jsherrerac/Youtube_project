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
    set_background, MonteCarloBoard, MC_INSIDE, MC_OUTSIDE, MC_BORDER, MC_PI,
    FONT_TITLE, FONT_FORMULA,
)

np.random.seed(99)


def _point_in_polygon(pts, poly):
    """Ray casting vectorizado: bool por punto (pts: (n,2), poly: (m,2))."""
    x, y = pts[:, 0], pts[:, 1]
    inside = np.zeros(len(pts), dtype=bool)
    m = len(poly)
    j = m - 1
    for i in range(m):
        xi, yi = poly[i]
        xj, yj = poly[j]
        cond = ((yi > y) != (yj > y)) & (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        inside ^= cond
        j = i
    return inside


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

        # ── Otras aplicaciones: forma irregular medida con puntos ─────────────
        caption = Text("la misma idea mide cualquier forma", color=MC_BORDER,
                       font_size=28).to_edge(UP, buff=0.7)
        # Blob irregular.
        theta = np.linspace(0, TAU, 11, endpoint=False)
        radii = 1.6 + 0.7 * rng.uniform(0.4, 1.0, size=len(theta))
        verts = np.c_[radii * np.cos(theta), radii * np.sin(theta)]
        blob = Polygon(*[[vx, vy, 0] for vx, vy in verts],
                       color=MC_BORDER, stroke_width=2.5)
        self.play(FadeIn(caption), Create(blob), run_time=1.5)

        # Nube de puntos clasificados dentro/fuera del blob.
        sample = rng.uniform(-2.4, 2.4, size=(400, 2))
        ins = _point_in_polygon(sample, verts)
        cloud = VGroup(*[
            Dot([x, y, 0], radius=0.03, color=MC_INSIDE if i else MC_OUTSIDE)
            for (x, y), i in zip(sample, ins)
        ])
        self.play(FadeIn(cloud, lag_ratio=0.0), run_time=1.2)
        self.wait(1.5)
        self.play(FadeOut(blob), FadeOut(cloud), FadeOut(caption), run_time=0.8)

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
