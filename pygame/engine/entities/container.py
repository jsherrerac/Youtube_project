"""Contenedor circular estático: N segmentos pymunk que forman el borde interior."""

import math
import pygame
import pymunk
from engine.config import CTYPE_WALL

N_SEGMENTS = 80   # cuántos lados tiene el polígono que aproxima el círculo
ELASTICITY  = 0.90
FRICTION    = 0.0


class Container:
    def __init__(self, space: pymunk.Space, center: tuple,
                 radius: float, draw_width: int = 5,
                 color: tuple = (255, 255, 255)):
        self.center      = center
        self.radius      = radius
        self.color       = color
        self.draw_width  = draw_width

        cx, cy = center
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        space.add(body)  # el body debe entrar antes que sus shapes
        for i in range(N_SEGMENTS):
            a1 = 2 * math.pi * i       / N_SEGMENTS
            a2 = 2 * math.pi * (i + 1) / N_SEGMENTS
            p1 = (cx + radius * math.cos(a1), cy + radius * math.sin(a1))
            p2 = (cx + radius * math.cos(a2), cy + radius * math.sin(a2))
            seg = pymunk.Segment(body, p1, p2, 1)
            seg.elasticity     = ELASTICITY
            seg.friction       = FRICTION
            seg.collision_type = CTYPE_WALL
            space.add(seg)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, self.color,
                           (int(self.center[0]), int(self.center[1])),
                           int(self.radius), self.draw_width)
