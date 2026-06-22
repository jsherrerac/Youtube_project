"""Bola protagonista: body+shape pymunk, render de cometa, crecimiento."""

import collections
import colorsys

import pygame
import pygame.gfxdraw
import pymunk

from engine.config  import CTYPE_BALL
from engine.effects import draw_glow

ELASTICITY = 0.92
FRICTION   = 0.0
_FILTER    = pymunk.ShapeFilter(group=1)


def _hsv_rgb(h: float, s: float = 1.0, v: float = 1.0) -> tuple:
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


class Ball:
    def __init__(
        self,
        space: pymunk.Space,
        pos: tuple,
        radius: float,
        color: tuple,
        mass: float = 5.0,
        max_radius: float = 448.0,
        visual_cfg: dict | None = None,
    ):
        self.space      = space
        self.color      = color
        self.radius     = radius
        self.max_radius = max_radius

        vcfg = visual_cfg or {}
        # visual_max_radius: cap de dibujo — física sigue creciendo hasta max_radius
        self._visual_max_r    = float(vcfg.get('visual_max_radius', max_radius))
        self._trail_maxlen    = int(vcfg.get('trail_length',      45))
        self._trail_max_alpha = int(vcfg.get('trail_max_alpha',   60))
        self._hue_speed       = float(vcfg.get('hue_speed',       0.003))
        self._hue_trail_step  = float(vcfg.get('hue_trail_step',  0.04))
        self._glow_layers     = int(vcfg.get('glow_layers',       10))
        self._glow_max_alpha  = int(vcfg.get('glow_max_alpha',    90))
        self._core_color      = vcfg.get('core_color',    (235, 245, 255))
        self._core_scale      = float(vcfg.get('core_scale',      0.82))

        self._trail     : collections.deque = collections.deque(maxlen=self._trail_maxlen)
        self._hue       : float = 0.0
        self._trail_surf: pygame.Surface | None = None   # creada en primer draw()

        moment    = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = pos
        self.shape = self._make_shape(radius)
        space.add(self.body, self.shape)

    # ------------------------------------------------------------------ #
    # Propiedades                                                          #
    # ------------------------------------------------------------------ #

    @property
    def visual_radius(self) -> float:
        """Radio de dibujo — nunca supera _visual_max_r; física usa self.radius."""
        return min(self.radius, self._visual_max_r)

    # ------------------------------------------------------------------ #
    # Física                                                               #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    # Render                                                               #
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface) -> None:
        # Crear trail surface la primera vez (tamaño del canvas real)
        if self._trail_surf is None:
            self._trail_surf = pygame.Surface(surface.get_size())

        # Avanzar hue y registrar posición
        self._hue = (self._hue + self._hue_speed) % 1.0
        pos = self.body.position
        self._trail.append((float(pos.x), float(pos.y)))

        vr = self.visual_radius

        # 1. Cola (BLEND_RGB_ADD — no tapa partículas)
        self._draw_trail(surface, vr)

        # 2. Halo / glow concéntrico (BLEND_RGB_ADD)
        draw_glow(surface, pos, vr, _hsv_rgb(self._hue),
                  self._glow_layers, self._glow_max_alpha)

        # 3. Núcleo blanco-cálido opaco encima del glow
        nx, ny = int(pos.x), int(pos.y)
        nr = max(2, int(vr * self._core_scale))
        try:
            pygame.gfxdraw.filled_circle(surface, nx, ny, nr, self._core_color)
            pygame.gfxdraw.aacircle(surface, nx, ny, nr, self._core_color)
        except Exception:
            pygame.draw.circle(surface, self._core_color, (nx, ny), nr)

    def _draw_trail(self, surface: pygame.Surface, vr: float) -> None:
        trail = list(self._trail)
        n = len(trail)
        if n < 2:
            return

        # Bounding box del trail para limpiar/blit solo esa región (rendimiento)
        margin = int(vr) + 4
        W, H   = self._trail_surf.get_size()
        x0 = max(0,  int(min(p[0] for p in trail)) - margin)
        y0 = max(0,  int(min(p[1] for p in trail)) - margin)
        x1 = min(W,  int(max(p[0] for p in trail)) + margin)
        y1 = min(H,  int(max(p[1] for p in trail)) + margin)
        if x1 <= x0 or y1 <= y0:
            return

        clip = pygame.Rect(x0, y0, x1 - x0, y1 - y0)
        self._trail_surf.fill((0, 0, 0), clip)

        for i, (px, py) in enumerate(trail):
            t     = i / (n - 1)         # 0 = más viejo, 1 = más nuevo
            hue   = (self._hue + i * self._hue_trail_step) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            alpha = int(self._trail_max_alpha * (t ** 2))   # cuadrático: fade suave
            # Radio: escala de 10 % (viejo) a 80 % del visual_radius (nuevo)
            tr    = max(2, int(vr * (0.10 + 0.70 * t)))
            bright = alpha / 255.0
            pygame.draw.circle(
                self._trail_surf,
                (int(r * 255 * bright), int(g * 255 * bright), int(b * 255 * bright)),
                (int(px), int(py)),
                tr,
            )

        # Blit solo la región del trail — mucho más rápido que blit pantalla completa
        surface.blit(self._trail_surf, (x0, y0), clip,
                     special_flags=pygame.BLEND_RGB_ADD)

    # ------------------------------------------------------------------ #
    # Pymunk                                                               #
    # ------------------------------------------------------------------ #

    def _make_shape(self, radius: float) -> pymunk.Circle:
        s = pymunk.Circle(self.body, radius)
        s.elasticity     = ELASTICITY
        s.friction       = FRICTION
        s.collision_type = CTYPE_BALL
        s.filter         = _FILTER
        return s
