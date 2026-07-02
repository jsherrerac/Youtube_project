"""
Beat 5.5 — "El nombre" (origen de Monte Carlo)
Escena tipográfica/geométrica, 100% sin imágenes externas ni logos (todo en
paleta). Secuencia tipo historia:
  1. "1946" + "LOS ÁLAMOS" + barra CLASIFICADO que se tacha.
  2. Cartas de solitario (rectángulos redondeados, pips cian/coral) en abanico;
     una se voltea.
  3. Las cartas se disuelven en una nube de puntos al azar (callback al Beat 1)
     → un conteo rápido.
  4. Cierre: "MONTE CARLO" en dorado + ficha de casino dibujada con Manim.
~38s.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background, MC_INSIDE, MC_OUTSIDE, MC_BORDER, MC_PI, FONT_TITLE,
)

np.random.seed(1946)


def make_card(pip_color, n_pips=3):
    """Carta de solitario: rectángulo blanco redondeado con pips de un color."""
    card = RoundedRectangle(width=0.95, height=1.35, corner_radius=0.12,
                            color=MC_BORDER, stroke_width=2.5).set_fill(BLACK, 1.0)
    pips = VGroup(*[Dot(radius=0.07, color=pip_color) for _ in range(n_pips)])
    pips.arrange(DOWN, buff=0.18).move_to(card.get_center())
    return VGroup(card, pips)


def make_chip():
    """Ficha de casino: cuerpo dorado + anillo + segmentos alternados en el borde."""
    body = Circle(radius=0.8, color=MC_PI, stroke_width=5).set_fill(BLACK, 1.0)
    ring = Circle(radius=0.52, color=MC_PI, stroke_width=3)
    edge = VGroup()
    for k in range(8):  # 8 muescas alternadas blanco/coral en el borde
        col = MC_BORDER if k % 2 == 0 else MC_OUTSIDE
        seg = AnnularSector(inner_radius=0.62, outer_radius=0.8,
                            angle=TAU / 16, start_angle=k * TAU / 8,
                            color=col).set_fill(col, 1.0).set_stroke(width=0)
        edge.add(seg)
    return VGroup(body, edge, ring)


class Beat55Origen(Scene):
    def construct(self):
        set_background(self)
        rng = np.random.default_rng(1946)

        # ── 1) 1946 · LOS ÁLAMOS · CLASIFICADO ────────────────────────────────
        year = Text("1946", color=MC_BORDER, font_size=96, weight=BOLD)
        place = Text("LOS ÁLAMOS", color=MC_BORDER, font_size=40).next_to(year, DOWN, buff=0.4)
        self.play(FadeIn(year, shift=DOWN * 0.3), run_time=1.0)
        self.play(Write(place), run_time=1.0)
        self.wait(0.4)

        stamp_box = Rectangle(width=4.2, height=0.9, color=MC_OUTSIDE, stroke_width=3)
        stamp_txt = Text("CLASIFICADO", color=MC_OUTSIDE, font_size=34, weight=BOLD)
        stamp = VGroup(stamp_box, stamp_txt).next_to(place, DOWN, buff=0.7).rotate(-8 * DEGREES)
        self.play(FadeIn(stamp, scale=1.2), run_time=0.6)
        # Se tacha (línea diagonal sobre el sello).
        strike = Line(stamp.get_corner(DL), stamp.get_corner(UR),
                      color=MC_BORDER, stroke_width=5)
        self.play(Create(strike), run_time=0.6)
        self.wait(0.6)
        self.play(FadeOut(VGroup(year, place, stamp, strike)), run_time=0.8)

        # ── 2) Cartas de solitario en abanico; una se voltea ──────────────────
        n_cards = 5
        cards = VGroup(*[make_card(MC_INSIDE if i % 2 == 0 else MC_OUTSIDE,
                                   n_pips=2 + i % 3) for i in range(n_cards)])
        # Abanico: cada carta rota alrededor de un pivote inferior común.
        pivot = DOWN * 2.2
        spread = 22 * DEGREES
        for i, c in enumerate(cards):
            ang = (i - (n_cards - 1) / 2) * spread
            c.move_to(UP * 1.4).rotate(ang, about_point=pivot)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards],
                              lag_ratio=0.18), run_time=2.0)
        self.wait(0.4)
        # Voltear la carta central (ángulo de abanico 0 → vertical): aplastar en
        # x, cambiar cara, expandir.
        mid = cards[n_cards // 2]
        flipped = make_card(MC_PI, n_pips=1).move_to(mid.get_center())
        self.play(mid.animate.stretch(0.02, dim=0), run_time=0.4)
        self.remove(mid)
        flipped.stretch(0.02, dim=0)
        self.add(flipped)
        self.play(flipped.animate.stretch(50, dim=0), run_time=0.4)
        self.wait(0.6)

        # ── 3) Las cartas se disuelven en una nube de puntos (callback Beat 1) ─
        n = 140
        xs = rng.uniform(-6.2, 6.2, n)
        ys = rng.uniform(-3.4, 3.4, n)
        cols = rng.choice([MC_INSIDE, MC_OUTSIDE], size=n)
        cloud = VGroup(*[Dot([x, y, 0.0], radius=0.05, color=c)
                         for x, y, c in zip(xs, ys, cols)])
        self.play(FadeOut(cards), FadeOut(flipped),
                  LaggedStart(*[FadeIn(d, scale=0.3) for d in cloud],
                              lag_ratio=0.01), run_time=1.6)
        # Conteo rápido.
        count = Text("142", color=MC_BORDER, font_size=64)
        self.play(FadeIn(count), run_time=0.4)
        for v in (387, 921, 1503):
            self.play(Transform(count, Text(str(v), color=MC_BORDER, font_size=64)),
                      run_time=0.3)
        self.wait(0.4)
        self.play(FadeOut(cloud), FadeOut(count), run_time=0.8)

        # ── 4) Cierre: MONTE CARLO + ficha de casino ──────────────────────────
        chip = make_chip()
        name = Text("MONTE CARLO", color=MC_PI, font_size=FONT_TITLE, weight=BOLD)
        group = VGroup(chip, name).arrange(RIGHT, buff=0.6)
        self.play(DrawBorderThenFill(chip), run_time=1.2)
        self.play(Write(name), run_time=1.2)
        self.play(Rotate(chip, angle=TAU, run_time=2.0, rate_func=smooth))
        self.wait(2.0)
