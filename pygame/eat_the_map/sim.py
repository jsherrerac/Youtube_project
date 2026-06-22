"""
eat_the_map — sim de ejemplo del engine.

Mecánica:
- Una bola rebota dentro de un contenedor circular lleno de N partículas.
- Tocar una partícula la "come": desaparece, la bola crece y acelera un poco.
- Rebotar en la pared también la hace crecer y acelerar (menos).
- Las partículas regeneran lentamente hasta una cuota máxima, luego paran.
- is_finished(): mapa limpio (sin partículas y regen agotado).
"""

import math
import random
import pygame
import pymunk

from engine import BaseSimulation
from engine import engine_config as ecfg
from engine.entities.ball import Ball
from engine.entities.container import Container
from engine.entities.particles import ParticleField


class EatTheMap(BaseSimulation):
    def __init__(self, cfg):
        super().__init__(cfg)
        self._wall_hits = 0   # contador de impactos bola-pared desde el último step

    # ------------------------------------------------------------------ #
    # Ciclo de vida                                                        #
    # ------------------------------------------------------------------ #

    def setup_space(self) -> None:
        self.space.gravity  = (0, self.sim_cfg.GRAVITY)
        self.space.damping  = self.sim_cfg.DAMPING

    def spawn_entities(self) -> None:
        cx, cy = ecfg.WIDTH // 2, ecfg.HEIGHT // 2

        self.container = Container(
            self.space, (cx, cy),
            self.sim_cfg.CONTAINER_RADIUS,
            color=ecfg.PALETTE["container"],
        )
        self.ball = Ball(
            self.space, (cx, cy),
            self.sim_cfg.BALL_RADIUS_INIT,
            ecfg.PALETTE["ball"],
            mass=self.sim_cfg.BALL_MASS,
            max_radius=self.sim_cfg.BALL_RADIUS_MAX,
        )
        # Velocidad inicial aleatoria
        angle = random.uniform(0, 2 * math.pi)
        spd   = self.sim_cfg.BALL_SPEED_INIT
        self.ball.body.velocity = (spd * math.cos(angle), spd * math.sin(angle))

        self.field = ParticleField(
            self.space, (cx, cy),
            self.sim_cfg.CONTAINER_RADIUS,
            self.sim_cfg.N_PARTICLES,
            self.sim_cfg.PARTICLE_RADIUS,
            ecfg.PALETTE["particle"],
            self.ball,
            regen_rate=self.sim_cfg.REGEN_RATE,
            max_regen=self.sim_cfg.MAX_REGEN,
        )
        self._elapsed = 0.0

    def register_collision_handlers(self) -> None:
        # pymunk 7+: on_collision en vez de add_collision_handler
        # post_solve: se ejecuta tras resolver el impulso; solo contamos, no modificamos
        self.space.on_collision(
            ecfg.CTYPE_BALL, ecfg.CTYPE_WALL,
            post_solve=self._on_ball_wall,
        )

    # ------------------------------------------------------------------ #
    # Loop                                                                 #
    # ------------------------------------------------------------------ #

    def update(self, dt: float) -> None:
        self._elapsed += dt

        # 1. Aplicar efectos de impactos de pared del step anterior
        for _ in range(self._wall_hits):
            self.ball.grow(self.sim_cfg.GROW_ON_WALL)
            self.ball.accelerate(self.sim_cfg.ACCEL_ON_WALL)
            self.audio_log.log(self.frame_count, "wall")
        self._wall_hits = 0

        # 2. Detectar y comer partículas (chequeo por distancia, fuera del step)
        bx, by = self.ball.body.position
        br = self.ball.radius
        eaten = [
            p for p in self.field.particles
            if _dist(p.body.position, (bx, by)) < br + p.radius + 1
        ]
        for p in eaten:
            self.field.remove(p)
            self.ball.grow(self.sim_cfg.GROW_ON_EAT)
            self.ball.accelerate(self.sim_cfg.ACCEL_ON_EAT)
            self.audio_log.log(self.frame_count, "eat")

        # 3. Regenerar partículas
        self.field.regen_tick(dt, self.ball)

        # 4. Clampar velocidad en [min, max] — mantiene el Short visualmente activo
        v = self.ball.body.velocity
        spd = math.sqrt(v.x * v.x + v.y * v.y)
        if spd < 1e-6:
            spd = 1e-6
        min_spd = self.sim_cfg.BALL_SPEED_MIN
        max_spd = self.sim_cfg.BALL_SPEED_MAX
        if spd < min_spd:
            self.ball.body.velocity = v * (min_spd / spd)
        elif spd > max_spd:
            self.ball.body.velocity = v * (max_spd / spd)

    def draw(self, surface: pygame.Surface) -> None:
        self.container.draw(surface)
        self.field.draw(surface)
        self.ball.draw(surface)
        self.draw_hook_text(surface, self.sim_cfg.HOOK_TEXT)
        self.draw_hud_text(surface, self._elapsed, len(self.field.particles))

    def is_finished(self) -> bool:
        return len(self.field.particles) == 0 and self.field.regen_done()

    # ------------------------------------------------------------------ #
    # Callbacks pymunk (se llaman dentro de space.step)                   #
    # ------------------------------------------------------------------ #

    def _on_ball_wall(self, arbiter, space, data) -> None:
        # Solo contar; las modificaciones reales ocurren en update()
        self._wall_hits += 1


# ---------- helper ----------

def _dist(a, b) -> float:
    dx = a.x - b[0]
    dy = a.y - b[1]
    return math.sqrt(dx * dx + dy * dy)
