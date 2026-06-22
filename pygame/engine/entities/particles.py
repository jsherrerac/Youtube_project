"""
Partículas pequeñas dentro del contenedor.
No colisionan entre sí (mismo grupo de ShapeFilter que la bola).
La detección de comida es manual por distancia en la sim.
"""

import math
import random
import pygame
import pymunk
from engine.config import CTYPE_PARTICLE

_FILTER    = pymunk.ShapeFilter(group=1)
ELASTICITY = 0.85
FRICTION   = 0.0
MASS       = 0.1


class Particle:
    def __init__(self, space: pymunk.Space, pos: tuple,
                 radius: float, color: tuple):
        self.radius = radius
        self.color  = color
        moment = pymunk.moment_for_circle(MASS, 0, radius)
        self.body  = pymunk.Body(MASS, moment)
        self.body.position = pos
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity     = ELASTICITY
        self.shape.friction       = FRICTION
        self.shape.collision_type = CTYPE_PARTICLE
        self.shape.filter         = _FILTER
        space.add(self.body, self.shape)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, self.color,
                           (int(self.body.position.x),
                            int(self.body.position.y)),
                           max(2, int(self.radius)))


class ParticleField:
    def __init__(self, space: pymunk.Space, center: tuple,
                 container_radius: float, n: int,
                 radius: float, color: tuple, ball,
                 regen_rate: float = 3.0, max_regen: int = 250):
        self.space            = space
        self.center           = center
        self.container_radius = container_radius
        self.radius           = radius
        self.color            = color
        self.regen_rate       = regen_rate
        self.max_regen        = max_regen
        self._total_regens    = 0
        self._regen_accum     = 0.0
        self.particles: list[Particle] = []

        for _ in range(n):
            pos = self._random_pos(ball)
            if pos:
                self.particles.append(Particle(space, pos, radius, color))

    def remove(self, particle: Particle) -> None:
        if particle in self.particles:
            self.particles.remove(particle)
            self.space.remove(particle.body, particle.shape)

    def regen_tick(self, dt: float, ball) -> None:
        if self._total_regens >= self.max_regen:
            return
        self._regen_accum += dt * self.regen_rate
        while self._regen_accum >= 1.0 and self._total_regens < self.max_regen:
            pos = self._random_pos(ball)
            if pos:
                self.particles.append(
                    Particle(self.space, pos, self.radius, self.color)
                )
                self._total_regens += 1
            self._regen_accum -= 1.0

    def regen_done(self) -> bool:
        return self._total_regens >= self.max_regen

    def draw(self, surface: pygame.Surface) -> None:
        for p in self.particles:
            p.draw(surface)

    def _random_pos(self, ball, max_tries: int = 60) -> tuple | None:
        cx, cy = self.center
        bx, by = ball.body.position
        br = ball.radius
        margin = self.radius + 5
        for _ in range(max_tries):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, self.container_radius - margin)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            dx, dy = x - bx, y - by
            if math.sqrt(dx * dx + dy * dy) > br + self.radius + 25:
                return (x, y)
        return None
