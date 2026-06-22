"""
BaseSimulation: ciclo de vida + loop principal.
Subclases implementan: setup_space, spawn_entities, register_collision_handlers,
update, draw, is_finished.
"""

import pygame
import pymunk
from . import config as ecfg
from .renderer import clear
from .recorder import Recorder
from .audio import AudioLog
from .overlay import draw_hook, draw_hud


class BaseSimulation:
    def __init__(self, sim_cfg):
        self.sim_cfg      = sim_cfg
        self.space        = pymunk.Space()
        self.audio_log    = AudioLog()
        self.frame_count  = 0
        self._accum       = 0.0
        self._running     = True
        self.is_recording = False   # True solo en modo --record; la sim puede consultarlo

    # ------------------------------------------------------------------ #
    # Ciclo de vida — subclases deben implementar todos estos             #
    # ------------------------------------------------------------------ #

    def setup_space(self):
        raise NotImplementedError

    def spawn_entities(self):
        raise NotImplementedError

    def register_collision_handlers(self):
        raise NotImplementedError

    def update(self, dt: float):
        """Lógica pre-step: aplica fuerzas, procesa eventos de colisión pendientes."""
        raise NotImplementedError

    def draw(self, surface: pygame.Surface):
        raise NotImplementedError

    def is_finished(self) -> bool:
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Helpers para el overlay (la sim los llama desde draw)               #
    # ------------------------------------------------------------------ #

    def draw_hook_text(self, surface: pygame.Surface, text: str) -> None:
        draw_hook(surface, text, ecfg.PALETTE["text_hook"])

    def draw_hud_text(self, surface: pygame.Surface,
                      elapsed: float, count: int) -> None:
        draw_hud(surface, elapsed, count, ecfg.PALETTE["text_hud"])

    # ------------------------------------------------------------------ #
    # Loop principal                                                       #
    # ------------------------------------------------------------------ #

    def run(self, record: bool = False) -> None:
        pygame.init()
        self._init_entities()

        W, H  = ecfg.WIDTH, ecfg.HEIGHT
        fps   = ecfg.FPS
        dt    = ecfg.PHYSICS_DT

        # Ventana de preview (pequeña durante grabación para no bloquear)
        scale = ecfg.PREVIEW_SCALE if not record else 0.25
        pw, ph = int(W * scale), int(H * scale)
        screen = pygame.display.set_mode((pw, ph))
        title = "Grabando..." if record else "Preview — ESC para salir"
        pygame.display.set_caption(title)
        surface = pygame.Surface((W, H))

        self.is_recording = record  # expuesto para que la sim omita sonidos en modo record
        recorder = None
        out_path = getattr(self.sim_cfg, 'OUTPUT_PATH', None)
        if record and out_path:
            recorder = Recorder(out_path, fps, (W, H))

        clock = pygame.time.Clock()

        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._running = False

            if record:
                # Offline: exactamente un dt por iteración, sin esperar vsync
                self._step(dt)
            else:
                real_dt = clock.tick(fps) / 1000.0
                self._accum += min(real_dt, 0.1)
                while self._accum >= dt:
                    self._step(dt)
                    self._accum -= dt

            clear(surface, ecfg.PALETTE["background"])
            self.draw(surface)

            if recorder:
                recorder.capture(surface)

            scaled = pygame.transform.scale(surface, (pw, ph))
            screen.blit(scaled, (0, 0))
            pygame.display.flip()

            self.frame_count += 1

            if self.is_finished():
                self._running = False

        if recorder:
            recorder.finish()
            print(f"[engine] Video sin audio: {out_path}")
            self.audio_log.build_and_mux(out_path, fps, self.frame_count)
            print(f"[engine] Listo: {out_path}")

        pygame.quit()

    def _init_entities(self) -> None:
        self.setup_space()
        self.spawn_entities()
        self.register_collision_handlers()

    def _step(self, dt: float) -> None:
        """Un paso de simulación: lógica primero, luego física."""
        self.update(dt)
        self.space.step(dt)
