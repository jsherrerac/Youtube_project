"""
Beat 4 — El círculo unitario
Duración objetivo: ~70s
La hipotenusa gira y su punta traza el círculo; el triángulo inscrito se actualiza.
Se para en ángulos clave para mostrar los valores. Al final: solo la barra azul, vuelta lenta.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import (
    set_background,
    HYPOTENUSE, OPPOSITE, ADJACENT, CIRCUMFERENCE, HIGHLIGHT,
    STROKE_DEFAULT, STROKE_THICK, STROKE_THIN, FONT_LABEL, FONT_FORMULA,
    UnitCircleWave,
)


class Beat4Circulo(Scene):
    def construct(self):
        set_background(self)
        self.wait(0.5)

        # Usar UnitCircleWave centrado — cherry-pick solo los componentes del círculo.
        # Los ejes y la onda NO se añaden a la escena en este beat.
        ucw = UnitCircleWave(circle_center=ORIGIN, circle_radius=3.0)

        # ══════════════════════════════════════════════════════════════════════
        # PARTE A — Aparece el círculo
        # ══════════════════════════════════════════════════════════════════════
        self.play(Create(ucw.circle), run_time=1.5)
        self.wait(0.8)

        # ══════════════════════════════════════════════════════════════════════
        # PARTE B — Radio giratorio traza el círculo
        # ══════════════════════════════════════════════════════════════════════
        # El radio nace en alpha=0 (apunta a la derecha)
        self.add(ucw.radius_line, ucw.dot)
        self.wait(0.5)

        # Dar una vuelta completa lenta — "mira cómo el radio traza el círculo"
        self.play(ucw.alpha.animate.set_value(TAU), run_time=5, rate_func=linear)
        self.wait(0.8)

        # ══════════════════════════════════════════════════════════════════════
        # PARTE C — Triángulo inscrito en ángulos clave
        # ══════════════════════════════════════════════════════════════════════
        # Añadir catetos (altura=seno, ancho=coseno)
        self.add(ucw.opposite, ucw.adjacent)
        self.wait(0.5)

        # Etiquetas fijas en los lados
        opp_label = always_redraw(lambda: Text(
            "sin(α)", color=OPPOSITE, font_size=FONT_LABEL,
        ).next_to(ucw.opposite.get_center(), RIGHT, buff=0.18))

        adj_label = always_redraw(lambda: Text(
            "cos(α)", color=ADJACENT, font_size=FONT_LABEL,
        ).next_to(ucw.adjacent.get_center(), DOWN, buff=0.18))

        self.play(FadeIn(opp_label), FadeIn(adj_label), run_time=0.8)

        # Pausar en ángulos clave (30°, 45°, 90°, 120°)
        for target_angle in [PI / 6, PI / 4, PI / 2, 2 * PI / 3]:
            self.play(
                ucw.alpha.animate.set_value(target_angle),
                run_time=1.5,
                rate_func=smooth,
            )
            self.wait(1.2)

        # Volver a alpha = PI/4 para la parte final
        self.play(ucw.alpha.animate.set_value(PI / 4), run_time=1.2, rate_func=smooth)
        self.wait(0.8)

        # ══════════════════════════════════════════════════════════════════════
        # PARTE D — Atenuar todo menos la altura azul; vuelta lenta
        # ══════════════════════════════════════════════════════════════════════
        self.play(FadeOut(adj_label), FadeOut(opp_label), run_time=0.5)

        # Atenuar: círculo, radio, punto, cateto adyacente
        dim_group = VGroup(ucw.circle, ucw.radius_line, ucw.dot, ucw.adjacent)
        self.play(dim_group.animate.set_opacity(0.12), run_time=1.5)
        self.wait(0.5)

        # Resaltar la barra azul con pulso
        self.play(ucw.opposite.animate.set_stroke(width=8), run_time=0.5)
        self.play(ucw.opposite.animate.set_stroke(width=STROKE_DEFAULT), run_time=0.5)

        # Etiqueta "sin(α)" en la barra azul
        opp_tag = always_redraw(lambda: Text(
            "sin(α)", color=OPPOSITE, font_size=FONT_LABEL,
        ).next_to(ucw.opposite.get_center(), RIGHT, buff=0.22))
        self.play(FadeIn(opp_tag), run_time=0.6)

        # Vuelta lenta (0→2π) — solo la barra azul se mueve visiblemente
        self.play(
            ucw.alpha.animate.set_value(ucw.alpha.get_value() + TAU),
            run_time=8,
            rate_func=linear,
        )

        self.wait(2.0)
        self.play(FadeOut(VGroup(dim_group, ucw.opposite, opp_tag)), run_time=0.8)
        self.wait(0.5)
