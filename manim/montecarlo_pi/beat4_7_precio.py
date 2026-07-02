"""
Beat 4.7 — "El precio de la precisión"   ·   ESCENA OPCIONAL
Tres filas que aparecen una a una: 100→3.1, 10.000→3.14, 1.000.000→3.141.
Cada ×100 en N fija SOLO un decimal más (dígito nuevo en dorado; el resto del
número en gris). Al lado, una barra de "trabajo" que crece enorme frente a un
"+1 decimal" diminuto: el contraste visual ES el mensaje. Sin board ni puntos.
~26s.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import set_background, MC_PI, MC_BORDER, FONT_TITLE, FONT_FORMULA

np.random.seed(0)  # solo por convención del canal; esta escena no muestrea

GREY = "#7A7A7A"  # número viejo "temblando" (gris neutro, no entra a la paleta MC)

ROWS = [
    ("100",       "3.1",   "1"),    # (N, estimación, dígito nuevo)
    ("10.000",    "3.14",  "4"),
    ("1.000.000", "3.141", "1"),
]
# Ancho de la barra de "trabajo": crece enorme (×100 por fila, comprimido a cuadro).
BAR_W = [0.8, 2.4, 4.0]
BAR_X0 = 0.6   # borde izquierdo común de las barras
GAIN_X = 5.9   # columna fija de la "ganancia" diminuta (cabe sin recortarse)


class Beat47Precio(Scene):
    def construct(self):
        set_background(self)

        title = Text("El precio de la precisión", color=MC_BORDER,
                     font_size=FONT_TITLE).to_edge(UP, buff=0.6)
        self.play(Write(title), run_time=1.2)

        # Encabezados de columna (trabajo vs ganancia).
        head = VGroup(
            Text("trabajo", color=MC_BORDER, font_size=24),
            Text("ganancia", color=MC_BORDER, font_size=24),
        )
        head[0].move_to([2.2, 2.1, 0])
        head[1].move_to([GAIN_X, 2.1, 0])
        self.play(FadeIn(head), run_time=0.5)

        y0, dy = 1.0, -1.4
        for i, ((n_txt, est_txt, new_dig), bw) in enumerate(zip(ROWS, BAR_W)):
            y = y0 + i * dy

            # ── N → estimación (el dígito nuevo en dorado, el resto gris) ──────
            n_label = Text(f"N = {n_txt}", color=MC_BORDER, font_size=FONT_FORMULA)
            arrow = Text("→", color=MC_BORDER, font_size=FONT_FORMULA)
            # Pintar todo gris y solo el ÚLTIMO dígito (el nuevo) en dorado.
            est = Text(est_txt, color=GREY, font_size=FONT_FORMULA)
            est[-1].set_color(MC_PI)
            row = VGroup(n_label, arrow, est).arrange(RIGHT, buff=0.35)
            row.to_edge(LEFT, buff=0.8).set_y(y)

            self.play(FadeIn(n_label, shift=RIGHT * 0.2), run_time=0.4)
            self.play(FadeIn(arrow), FadeIn(est), run_time=0.4)
            # El dígito nuevo "se asienta" (resto tiembla un instante).
            self.play(Indicate(est[-1], color=MC_PI, scale_factor=1.4), run_time=0.6)

            # ── Barra de trabajo (crece enorme) vs ganancia diminuta (+1 dec) ──
            bar = Rectangle(width=bw, height=0.45, color=MC_PI,
                            stroke_width=0).set_fill(MC_PI, opacity=0.85)
            bar.move_to([BAR_X0 + bw / 2, y, 0])  # borde izquierdo común
            work_tag = Text("×100" if i > 0 else "base", color=MC_PI,
                            font_size=20).next_to(bar, UP, buff=0.05)
            gain = Text("+1 decimal", color=MC_PI, font_size=18).move_to([GAIN_X, y, 0])

            self.play(GrowFromEdge(bar, LEFT), FadeIn(work_tag), run_time=0.7)
            self.play(FadeIn(gain, scale=0.6), run_time=0.4)
            self.wait(0.5)

        # Remate: el trabajo se dispara, la precisión apenas sube.
        punch = Text("trabajo ×100  ·  precisión +1 dígito", color=MC_BORDER,
                     font_size=28).to_edge(DOWN, buff=0.7)
        self.play(FadeIn(punch, shift=UP * 0.2), run_time=1.0)
        self.wait(2.5)
