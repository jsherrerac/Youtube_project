"""Bola protagonista: body+shape pymunk, render, crecimiento y aceleración."""

import pygame
import pymunk
from engine.config import CTYPE_BALL
from engine.renderer import draw_circle_filled

ELASTICITY = 0.92
FRICTION   = 0.0
# Grupo 1: bola y partículas no colisionan entre sí, pero sí con las paredes (grupo 0)
_FILTER = pymunk.ShapeFilter(group=1)


class Ball:
    def __init__(self, space: pymunk.Space, pos: tuple,
                 radius: float, color: tuple, mass: float = 5.0,
                 max_radius: float = 220.0):
        self.space      = space
        self.color      = color
        self.radius     = radius
        self.max_radius = max_radius

        moment   = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = pos
        self.shape = self._make_shape(radius)
        space.add(self.body, self.shape)

    def grow(self, amount: float) -> None:
        new_r = min(self.radius + amount, self.max_radius)
        if new_r == self.radius:
            return
        self.radius = new_r
        self.space.remove(self.shape)
        self.shape = self._make_shape(new_r)
        self.space.add(self.shape)

    def accelerate(self, factor: float) -> None:
        self.body.velocity = self.body.velocity * factor

    def draw(self, surface: pygame.Surface) -> None:
        draw_circle_filled(surface, self.color,
                           self.body.position, self.radius)

    def _make_shape(self, radius: float) -> pymunk.Circle:
        s = pymunk.Circle(self.body, radius)
        s.elasticity      = ELASTICITY
        s.friction        = FRICTION
        s.collision_type  = CTYPE_BALL
        s.filter          = _FILTER
        return s
