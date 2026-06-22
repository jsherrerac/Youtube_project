"""
eat_the_map — sim de ejemplo del engine.

Mecánica:
- Una bola rebota dentro de un contenedor circular lleno de N partículas.
- Tocar una partícula la "come": desaparece, la bola crece y acelera.
- Cada rebote en la pared toca la siguiente nota de MELODY (In the Hall of the Mountain King).
- Las partículas regeneran continuamente; la bola gana cuando llena el mapa.
- Fase final: cuando ya no caben partículas, la bola sigue creciendo 3 segundos más.
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
from engine.sounds import make_eat_sound, make_melody_note
from engine.audio import note_to_freq

FINALE_SECONDS = 3.0   # duración fija de la fase final


class EatTheMap(BaseSimulation):
    def __init__(self, cfg):
        super().__init__(cfg)
        self._wall_hits    = 0
        self._melody_index = 0
        self._eat_sound    = None
        self._melody_sounds: dict[float, pygame.mixer.Sound] = {}

    # ------------------------------------------------------------------ #
    # Ciclo de vida                                                        #
    # ------------------------------------------------------------------ #

    def setup_space(self) -> None:
        self.space.gravity = (0, self.sim_cfg.GRAVITY)
        self.space.damping = self.sim_cfg.DAMPING

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
            visual_cfg={
                'visual_max_radius': self.sim_cfg.COMET_VISUAL_MAX_R,
                'trail_length':      self.sim_cfg.TRAIL_LENGTH,
                'trail_max_alpha':   self.sim_cfg.TRAIL_MAX_ALPHA,
                'hue_speed':         self.sim_cfg.HUE_SPEED,
                'hue_trail_step':    self.sim_cfg.HUE_TRAIL_STEP,
                'glow_layers':       self.sim_cfg.GLOW_LAYERS,
                'glow_max_alpha':    self.sim_cfg.GLOW_MAX_ALPHA,
                'core_color':        self.sim_cfg.CORE_COLOR,
                'core_scale':        self.sim_cfg.CORE_RADIUS_SCALE,
            },
        )
        angle = random.uniform(0, 2 * math.pi)
        spd   = self.sim_cfg.BALL_SPEED_INIT
        self.ball.body.velocity = (spd * math.cos(angle), spd * math.sin(angle))

        self.field = ParticleField(
            self.space, (cx, cy),
            self.sim_cfg.CONTAINER_RADIUS,
            self.sim_cfg.N_PARTICLES,
            self.sim_cfg.PARTICLE_RADIUS,
            self.sim_cfg.PARTICLE_COLORS,
            self.ball,
            regen_rate=self.sim_cfg.REGEN_RATE,
            max_regen=self.sim_cfg.MAX_REGEN,
            soft_glow=self.sim_cfg.PARTICLE_SOFT_GLOW,
        )
        self._elapsed       = 0.0
        self._finale_active = False
        self._finale_timer  = 0.0
        self._base_speed    = float(self.sim_cfg.BALL_SPEED_INIT)
        self._sounds_ready  = False

    def register_collision_handlers(self) -> None:
        self.space.on_collision(
            ecfg.CTYPE_BALL, ecfg.CTYPE_WALL,
            post_solve=self._on_ball_wall,
        )

    # ------------------------------------------------------------------ #
    # Loop                                                                 #
    # ------------------------------------------------------------------ #

    def update(self, dt: float) -> None:
        self._elapsed += dt
        self._ensure_sounds()

        # 1. Impactos de pared: melodía + aceleración + drift
        if self._wall_hits > 0:
            factor = self.sim_cfg.ACCEL_ON_WALL ** self._wall_hits
            self._base_speed = min(self._base_speed * factor,
                                   self.sim_cfg.BALL_SPEED_MAX)
            melody = self.sim_cfg.MELODY
            for _ in range(self._wall_hits):
                self.ball.grow(self.sim_cfg.GROW_ON_WALL)
                note = melody[self._melody_index % len(melody)]
                freq = note_to_freq(note)
                self.audio_log.log(self.frame_count, f"note:{freq:.4f}")
                self._melody_index += 1

            # Sonido de la última nota en modo live
            if not self.is_recording:
                last_note = melody[(self._melody_index - 1) % len(melody)]
                freq = note_to_freq(last_note)
                snd = self._melody_sounds.get(round(freq, 2))
                if snd:
                    snd.play()

            # Rotación aleatoria para romper órbitas periódicas
            max_rad = math.radians(self.sim_cfg.DRIFT_ON_WALL_DEG)
            angle   = random.uniform(-max_rad, max_rad)
            v = self.ball.body.velocity
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            self.ball.body.velocity = pymunk.Vec2d(
                v.x * cos_a - v.y * sin_a,
                v.x * sin_a + v.y * cos_a,
            )
            self._wall_hits = 0

        # 2. Comer partículas
        bx, by = self.ball.body.position
        br = self.ball.radius
        eaten = [
            p for p in self.field.particles
            if _dist(p.body.position, (bx, by)) < br + p.radius + 1
        ]
        for p in eaten:
            self.field.remove(p)
            self.ball.grow(self.sim_cfg.GROW_ON_EAT)
            self._base_speed = min(self._base_speed * self.sim_cfg.ACCEL_ON_EAT,
                                   self.sim_cfg.BALL_SPEED_MAX)
            self.audio_log.log(self.frame_count, "eat")
        if eaten and self._eat_sound and not self.is_recording:
            self._eat_sound.play()

        # 3. Regenerar partículas
        self.field.regen_tick(dt, self.ball)

        # 3b. Fase final: sin partículas + sin espacio → crecer 3 s exactos
        no_particles = len(self.field.particles) == 0
        no_space     = (self.sim_cfg.CONTAINER_RADIUS - self.ball.radius) < 32
        if no_particles and no_space:
            self._finale_active = True
        if self._finale_active:
            self.ball.grow(self.sim_cfg.FINALE_GROW_PX_PER_SEC * dt)
            self._finale_timer += dt

        # 4. Clamp velocidad: _base_speed como piso monotónico
        v   = self.ball.body.velocity
        spd = math.sqrt(v.x * v.x + v.y * v.y)
        if spd < 1e-6:
            spd = 1e-6
        if spd < self._base_speed:
            self.ball.body.velocity = v * (self._base_speed / spd)
        elif spd > self.sim_cfg.BALL_SPEED_MAX:
            self.ball.body.velocity = v * (self.sim_cfg.BALL_SPEED_MAX / spd)

    def draw(self, surface: pygame.Surface) -> None:
        self.container.draw(surface)
        self.field.draw(surface)
        self.ball.draw(surface)
        self.draw_hook_text(surface, self.sim_cfg.HOOK_TEXT)
        self.draw_hud_text(surface, self._elapsed, len(self.field.particles))

    def is_finished(self) -> bool:
        # La bola gana al completar los 3 s de fase final O al alcanzar radio máximo
        return self._finale_timer >= FINALE_SECONDS or \
               self.ball.radius >= self.sim_cfg.BALL_RADIUS_MAX

    # ------------------------------------------------------------------ #
    # Callbacks pymunk                                                     #
    # ------------------------------------------------------------------ #

    def _on_ball_wall(self, arbiter, space, data) -> None:
        self._wall_hits += 1

    def _ensure_sounds(self) -> None:
        if self._sounds_ready:
            return
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._eat_sound = make_eat_sound()
            self._eat_sound.set_volume(0.55)
            # Pre-generar una Sound por cada nota única de la melodía
            for note in self.sim_cfg.MELODY:
                freq = note_to_freq(note)
                key  = round(freq, 2)
                if key not in self._melody_sounds:
                    snd = make_melody_note(freq)
                    snd.set_volume(0.5)
                    self._melody_sounds[key] = snd
        except Exception as e:
            print(f"[sounds] {e}")
        self._sounds_ready = True


# ---------- helper ----------

def _dist(a, b) -> float:
    dx = a.x - b[0]
    dy = a.y - b[1]
    return math.sqrt(dx * dx + dy * dy)
