"""
Partículas pequeñas dentro del contenedor.
No colisionan entre sí (mismo grupo de ShapeFilter que la bola).
La detección de comida es manual por distancia en la sim.
Cada partícula elige un color aleatorio de la paleta del config.
"""

import math
import random
import pygame
import pygame.gfxdraw
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
        x = int(self.body.position.x)
        y = int(self.body.position.y)
        r = max(2, int(self.radius))
        try:
            pygame.gfxdraw.filled_circle(surface, x, y, r, self.color)
            pygame.gfxdraw.aacircle(surface, x, y, r, self.color)
        except Exception:
            pygame.draw.circle(surface, self.color, (x, y), r)


class ParticleField:
    def __init__(self, space: pymunk.Space, center: tuple,
                 container_radius: float, n: int,
                 radius: float, colors: list, ball,
                 regen_rate: float = 3.0, max_regen: int = 250,
                 soft_glow: bool = False):
        self.space            = space
        self.center           = center
        self.container_radius = container_radius
        self.radius           = radius
        self.colors           = colors if isinstance(colors, list) else [colors]
        self.regen_rate       = regen_rate
        self.max_regen        = max_regen
        self._total_regens    = 0
        self._regen_accum     = 0.0
        self.particles: list[Particle] = []

        # Glow suave: pre-renderiza UN sprite por color, bliteado aditivo bajo la partícula.
        # Con 760 partículas son solo 760 blits de sprite pequeño — sin crear surfaces por frame.
        self._soft_glow = soft_glow
        self._glow_sprites: dict = {}   # color -> Surface; creado en primer draw()
        self._glow_r = int(radius * 2)  # extensión del glow = 2× radio partícula

        for _ in range(n):
            pos = self._random_pos(ball)
            if pos:
                self.particles.append(
                    Particle(space, pos, radius, self._pick_color())
                )

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
                    Particle(self.space, pos, self.radius, self._pick_color())
                )
                self._total_regens += 1
            self._regen_accum -= 1.0

    def regen_done(self) -> bool:
        return self._total_regens >= self.max_regen

    def draw(self, surface: pygame.Surface) -> None:
        # Pre-renderizar sprites de glow la primera vez (pygame ya está init)
        if self._soft_glow and not self._glow_sprites:
            self._make_glow_sprites()

        gr = self._glow_r
        for p in self.particles:
            if self._soft_glow:
                spr = self._glow_sprites.get(p.color)
                if spr:
                    surface.blit(spr,
                                 (int(p.body.position.x) - gr,
                                  int(p.body.position.y) - gr),
                                 special_flags=pygame.BLEND_RGB_ADD)
            p.draw(surface)

    def _make_glow_sprites(self) -> None:
        """Un sprite de glow por color único — creado una sola vez al inicio."""
        gr   = self._glow_r
        size = gr * 2
        for color in self.colors:
            surf = pygame.Surface((size, size))   # fondo negro
            r, g, b = color[0], color[1], color[2]
            inner = max(1, int(self.radius))
            for i in range(6):
                t      = i / 5.0
                ring_r = max(1, int(gr - (gr - inner) * t))
                bright = (t ** 2) * 0.35           # máximo 35 % de brillo
                c = (int(r * bright), int(g * bright), int(b * bright))
                pygame.draw.circle(surf, c, (gr, gr), ring_r)
            self._glow_sprites[color] = surf

    def _pick_color(self) -> tuple:
        return random.choice(self.colors)

    def _random_pos(self, ball, max_tries: int = 80) -> tuple | None:
        cx, cy = self.center
        bx, by = ball.body.position
        br = ball.radius
        gap   = self.radius + 4
        r_min = br + gap
        r_max = self.container_radius - gap
        if r_min >= r_max:
            return None
        for _ in range(max_tries):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(r_min, r_max)
            x = bx + r * math.cos(angle)
            y = by + r * math.sin(angle)
            if math.sqrt((x - cx)**2 + (y - cy)**2) <= self.container_radius - gap:
                return (x, y)
        return None
