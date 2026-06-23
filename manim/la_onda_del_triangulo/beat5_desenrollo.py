"""
Beat 5 — El desenrollo (CLÍMAX)
Duración objetivo: ~80s
UnitCircleWave: círculo a la izquierda + ejes a la derecha.
La onda seno azul se traza sola conforme alpha va de 0 a 2π.
Después se superpone el coseno verde con una marca del desfase π/2.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background,
    HYPOTENUSE, OPPOSITE, ADJACENT, CIRCUMFERENCE, HIGHLIGHT, WAVE,
    STROKE_DEFAULT, STROKE_THICK, STROKE_THIN, FONT_LABEL,
    UnitCircleWave,
)


class Beat5Desenrollo(Scene):
    def construct(self):
        set_background(self)
        self.wait(0.5)

        ucw = UnitCircleWave(circle_radius=2.0)

        # ══════════════════════════════════════════════════════════════════════
        # Presentación del escenario
        # ══════════════════════════════════════════════════════════════════════
        self.play(Create(ucw.circle), run_time=1.5)
        self.add(ucw.radius_line, ucw.dot)
        self.wait(0.4)
        self.add(ucw.opposite, ucw.adjacent)
        self.wait(0.4)
        self.play(Create(ucw.axes), run_time=1.5)
        self.wait(0.5)

        # Conector punteado y punto en la onda (aparecen silenciosamente)
        self.add(ucw.dashed_connector, ucw.wave_dot)
        self.wait(0.3)

        # ══════════════════════════════════════════════════════════════════════
        # CLÍMAX — La onda seno se traza sola (el momento del video)
        # ══════════════════════════════════════════════════════════════════════
        self.add(ucw.wave_sin)   # empieza en alpha=0, vacío

        # 10 segundos de barrido — el alpha avanza de 0 a 2π
        self.play(
            ucw.sweep(),
            run_time=10,
            rate_func=linear,
        )

        # Dejar respirar: la onda completa visible, el punto quieto al final
        self.wait(3.0)

        # ══════════════════════════════════════════════════════════════════════
        # Coseno — aparece en verde, desfasado π/2 respecto al seno
        # ══════════════════════════════════════════════════════════════════════
        cos_curve = ucw.axes.plot(
            np.cos,
            x_range=[0, TAU],
            color=ADJACENT,
            stroke_width=STROKE_THICK,
        )
        self.play(Create(cos_curve), run_time=3, rate_func=linear)
        self.wait(1.0)

        # Marcar el desfase π/2:
        # El coseno alcanza su pico en x=0; el seno en x=π/2.
        # Una doble flecha entre esos dos puntos muestra el desfase.
        p_cos_peak = ucw.axes.c2p(0,    1.0)   # pico del coseno
        p_sin_peak = ucw.axes.c2p(PI/2, 1.0)   # pico del seno

        # Puntos de referencia en y=1.25 para la flecha horizontal
        arr_y = ucw.axes.c2p(0, 1.28)[1]
        arr_start = np.array([p_cos_peak[0], arr_y, 0])
        arr_end   = np.array([p_sin_peak[0], arr_y, 0])

        phase_arrow = DoubleArrow(
            arr_start, arr_end,
            color=HIGHLIGHT,
            buff=0,
            stroke_width=3,
            tip_length=0.18,
        )
        phase_label = Text("π/2", color=HIGHLIGHT, font_size=FONT_LABEL)
        phase_label.next_to(phase_arrow, UP, buff=0.12)

        self.play(GrowArrow(phase_arrow), run_time=0.8)
        self.play(Write(phase_label), run_time=0.6)
        self.wait(3.0)

        # Fade final
        self.play(
            FadeOut(VGroup(
                ucw.circle, ucw.radius_line, ucw.dot,
                ucw.opposite, ucw.adjacent,
                ucw.axes, ucw.wave_sin, ucw.wave_dot,
                ucw.dashed_connector, cos_curve,
                phase_arrow, phase_label,
            )),
            run_time=1.5,
        )
        self.wait(0.5)
