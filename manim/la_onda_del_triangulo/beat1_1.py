"""
Beat 1.1 — El triángulo equilátero
Duración objetivo: ~8s
Un triángulo equilátero blanco crece desde el centro.
Sin etiquetas, sin colores extra — solo la figura.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from manim import *
from lib import set_background


def _equilateral(side: float) -> Polygon:
    """Triángulo equilátero centrado en el origen, vértice superior."""
    h = side * np.sqrt(3) / 2
    return Polygon(
        np.array([0,       h * 2/3, 0]),   # vértice superior
        np.array([ side/2, -h/3,    0]),   # inferior derecho
        np.array([-side/2, -h/3,    0]),   # inferior izquierdo
        color=WHITE,
        stroke_width=4,
        fill_opacity=0,
    )


class Beat11(Scene):
    def construct(self):
        set_background(self)

        tri = _equilateral(6.0)

        self.wait(1.0)
        self.play(GrowFromCenter(tri), run_time=2.0, rate_func=rush_from)
        self.wait(3.0)
