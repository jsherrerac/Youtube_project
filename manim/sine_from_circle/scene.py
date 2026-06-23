"""
sine_from_circle/scene.py
Tema: El seno nace del círculo unitario
Objetivo: validar que lib/ funciona — renderiza solo el clímax.

Paso a paso:
  1. Aparece el círculo unitario con el radio y el punto.
  2. Se muestran los catetos (opuesto=azul, adyacente=verde).
  3. Aparecen los ejes a la derecha.
  4. Clímax: el ángulo barre 0→2π y la onda seno se traza sola.
  5. Congelar para que el espectador procese la conexión.

Duración objetivo: ~12 s
"""
import sys
import os

# Asegura que lib/ sea importable sin importar desde dónde se llame manim
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from manim import *
from lib import UnitCircleWave, set_background, WAVE, OPPOSITE, ADJACENT, HIGHLIGHT


class SineClimaxScene(Scene):
    def construct(self):
        set_background(self)

        ucw = UnitCircleWave()

        # ── 1. Círculo unitario ───────────────────────────────────────────────
        self.play(Create(ucw.circle), run_time=1.4)

        # ── 2. Radio y punto en alpha = 0 ────────────────────────────────────
        # always_redraw → se añaden directamente (ya tienen el estado correcto)
        self.add(ucw.radius_line, ucw.dot)
        self.wait(0.4)

        # ── 3. Catetos: intuición de "coordenadas" antes de los ejes ─────────
        self.add(ucw.opposite, ucw.adjacent)
        self.wait(0.6)

        # ── 4. Ejes a la derecha ─────────────────────────────────────────────
        self.play(Create(ucw.axes), run_time=1.5)
        self.wait(0.3)

        # ── 5. Conector punteado (silenciosamente) ────────────────────────────
        self.add(ucw.wave_sin, ucw.wave_dot, ucw.dashed_connector)
        self.wait(0.3)

        # ── 6. CLÍMAX: barrer de 0 a 2π trazando la onda ────────────────────
        self.play(
            ucw.sweep(),
            run_time=6,
            rate_func=linear,
        )

        # ── 7. Pausa final para que el espectador vea la onda completa ────────
        self.wait(2.0)
