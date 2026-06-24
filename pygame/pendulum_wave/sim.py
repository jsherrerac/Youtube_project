"""
Pendulum Wave — N péndulos con SHM analítico puro (sin Pymunk).

Estructura del video:
  [0, WAIT_SECS)             → todos quietos en equilibrio (angle=0)
  [WAIT_SECS, +T_LOOP)       → SHM con cos(); envolvente suave los primeros RAMP_IN s
  [+T_LOOP, +T_LOOP+SYNC_SECS] → re-sync visual (todos vuelven al máximo simultáneamente)

Física: angle_k(t_phys) = envelope(t_phys) · A · cos(2π · freq_k · t_phys)
  donde freq_k = (BASE_OSC + k) / T_LOOP → en t_phys=T_LOOP todos en cos(2π·int) = 1.
"""

import math
import colorsys
from collections import deque

import pygame

from engine import BaseSimulation, engine_config as ecfg
from engine.effects import draw_glow
from engine.overlay import draw_hook
from engine.renderer import clear, draw_circle_filled


class PendulumWave(BaseSimulation):

    def __init__(self, cfg):
        super().__init__(cfg)
        self._t: float = 0.0

        # Listas por péndulo (pobladas en spawn_entities)
        self._freqs:       list[float]       = []
        self._lengths:     list[float]       = []
        self._pivot_xs:    list[float]       = []
        self._pivot_ys:    list[float]       = []
        self._colors:      list[tuple]       = []
        self._center_pos:  list[tuple]       = []  # pos del bob cuando angle=0
        self._trails:      list[deque]       = []
        self._prev_angles: list[float]       = []
        self._bob_pos:     list[tuple]       = []  # posición actual (cache)
        self._flash:       list[float]       = []  # intensidad del flash [0,1]

        # Pulsos activos: [cx, cy, frame_start, color]
        self._pulses: list[list] = []

        # Surfaces pre-allocadas para evitar allocs por frame
        self._trail_surf: pygame.Surface | None = None
        self._pulse_surf: pygame.Surface | None = None
        self._str_surf:   pygame.Surface | None = None

    # ------------------------------------------------------------------ #
    # Ciclo de vida                                                        #
    # ------------------------------------------------------------------ #

    def setup_space(self) -> None:
        self.space.gravity = (0, 0)  # Pymunk inutilizado; sin gravedad

    def spawn_entities(self) -> None:
        cfg = self.sim_cfg
        W, H = ecfg.WIDTH, ecfg.HEIGHT
        cx = W // 2

        n = cfg.N
        spacing = cfg.PIVOT_SPAN / max(n - 1, 1)
        left_x  = cx - cfg.PIVOT_SPAN / 2.0

        for k in range(n):
            osc_k  = cfg.BASE_OSC + k
            freq_k = osc_k / cfg.T_LOOP
            # L proporcional a 1/osc² → péndulo largo = oscilación más lenta ✓
            L_px    = cfg.L_MAX_PX * (cfg.BASE_OSC / osc_k) ** 2
            pivot_x = left_x + k * spacing
            # Pivote sobre la línea base: reposo de la bola = BASELINE_Y
            pivot_y = cfg.BASELINE_Y - L_px

            # Espectro arcoíris: hue 0 (rojo) → HUE_MAX (violeta)
            hue = (k / max(n - 1, 1)) * cfg.SPECTRUM_HUE_MAX
            r, g, b = colorsys.hsv_to_rgb(hue, cfg.SPECTRUM_SAT, 1.0)
            color = (int(r * 255), int(g * 255), int(b * 255))

            self._freqs.append(freq_k)
            self._lengths.append(L_px)
            self._pivot_xs.append(pivot_x)
            self._pivot_ys.append(pivot_y)
            self._colors.append(color)
            self._center_pos.append((pivot_x, cfg.BASELINE_Y))
            self._trails.append(deque(maxlen=cfg.TRAIL_LENGTH))
            self._prev_angles.append(0.0)  # empieza en equilibrio (espera quieta)
            self._bob_pos.append((pivot_x, cfg.BASELINE_Y))
            self._flash.append(0.0)

        # Pre-alocar surfaces reutilizables
        self._trail_surf = pygame.Surface((W, H))
        self._pulse_surf = pygame.Surface((W, H))
        self._str_surf   = pygame.Surface((W, H), pygame.SRCALPHA)

    def register_collision_handlers(self) -> None:
        pass  # sin colisiones

    # ------------------------------------------------------------------ #
    # Loop                                                                 #
    # ------------------------------------------------------------------ #

    def update(self, dt: float) -> None:
        cfg = self.sim_cfg
        # Tiempo absoluto del video: exacto en grabación, acumulado en preview.
        if self.is_recording:
            self._t = self.frame_count / ecfg.FPS
        else:
            self._t += dt

        # ── Fase de espera: todo quieto ───────────────────────────────────
        if self._t < cfg.WAIT_SECS:
            for k in range(cfg.N):
                self._bob_pos[k]     = (self._pivot_xs[k], cfg.BASELINE_Y)
                self._prev_angles[k] = 0.0
                self._flash[k]      *= cfg.BOB_FLASH_DECAY
            return  # sin trails ni pulsos durante la espera

        # ── Fase de física SHM ────────────────────────────────────────────
        t_phys = self._t - cfg.WAIT_SECS

        if t_phys >= cfg.T_LOOP:
            # ── Fase de re-sync: todos a la misma frecuencia (freq_0) ─────
            # En t_phys=T_LOOP todos llegaron a cos(2π·int)=1 simultáneamente.
            # Desde aquí oscilan juntos: tau=0 → cos(0)=1 → transición sin salto.
            tau = t_phys - cfg.T_LOOP
            sync_angle = cfg.AMPLITUDE_RAD * math.cos(
                2.0 * math.pi * self._freqs[0] * tau
            )
            for k in range(cfg.N):
                L  = self._lengths[k]
                px = self._pivot_xs[k] + L * math.sin(sync_angle)
                py = self._pivot_ys[k] + L * math.cos(sync_angle)
                self._bob_pos[k] = (px, py)
                self._trails[k].append((px, py))

                prev = self._prev_angles[k]
                if prev * sync_angle < 0.0:
                    note_hz = cfg.NOTES_HZ[k % len(cfg.NOTES_HZ)]
                    self.audio_log.log(self.frame_count, f"note:{note_hz:.2f}")
                    cpx, cpy = self._center_pos[k]
                    self._pulses.append([cpx, cpy, self.frame_count, self._colors[k]])
                    self._flash[k] = 1.0

                self._prev_angles[k] = sync_angle
                self._flash[k] *= cfg.BOB_FLASH_DECAY

        else:
            # ── SHM normal con frecuencias distintas ──────────────────────
            # Envolvente cúbica: sube de 0→1 durante RAMP_IN s para arrancar suave
            if t_phys < cfg.RAMP_IN:
                u = t_phys / cfg.RAMP_IN
                envelope = u * u * (3.0 - 2.0 * u)  # ease-in-out [0, 1]
            else:
                envelope = 1.0

            for k in range(cfg.N):
                angle = (envelope * cfg.AMPLITUDE_RAD
                         * math.cos(2.0 * math.pi * self._freqs[k] * t_phys))
                L  = self._lengths[k]
                px = self._pivot_xs[k] + L * math.sin(angle)
                py = self._pivot_ys[k] + L * math.cos(angle)

                self._bob_pos[k] = (px, py)
                self._trails[k].append((px, py))

                prev = self._prev_angles[k]
                if envelope >= 0.05 and prev * angle < 0.0:
                    note_hz = cfg.NOTES_HZ[k % len(cfg.NOTES_HZ)]
                    self.audio_log.log(self.frame_count, f"note:{note_hz:.2f}")
                    cpx, cpy = self._center_pos[k]
                    self._pulses.append([cpx, cpy, self.frame_count, self._colors[k]])
                    self._flash[k] = 1.0

                self._prev_angles[k] = angle
                self._flash[k] *= cfg.BOB_FLASH_DECAY

        # Purgar pulsos expirados
        self._pulses = [
            p for p in self._pulses
            if self.frame_count - p[2] < cfg.PULSE_DURATION_FRAMES
        ]

    def draw(self, surface: pygame.Surface) -> None:
        cfg = self.sim_cfg

        # Fondo propio (azulado oscuro en vez del negro engine)
        clear(surface, cfg.BG_COLOR)

        # ── Cuerdas (líneas translúcidas pivote→bola) ──────────────────
        if cfg.STRINGS_VISIBLE:
            self._str_surf.fill((0, 0, 0, 0))  # limpiar a transparente
            for k in range(cfg.N):
                pvx = int(self._pivot_xs[k])
                pvy = int(self._pivot_ys[k])
                bx, by = self._bob_pos[k]
                col = (*self._colors[k], cfg.STRING_ALPHA)
                pygame.draw.line(
                    self._str_surf, col,
                    (pvx, pvy), (int(bx), int(by)),
                    cfg.STRING_WIDTH,
                )
            surface.blit(self._str_surf, (0, 0))

        # ── Puntos de pivote ───────────────────────────────────────────
        for k in range(cfg.N):
            pygame.draw.circle(
                surface, cfg.PIVOT_DOT_COLOR,
                (int(self._pivot_xs[k]), int(self._pivot_ys[k])),
                cfg.PIVOT_DOT_RADIUS,
            )

        # ── Trails (blend aditivo sobre fondo negro) ───────────────────
        self._trail_surf.fill((0, 0, 0))
        for k in range(cfg.N):
            trail  = list(self._trails[k])
            n_pts  = len(trail)
            if n_pts < 2:
                continue
            color = self._colors[k]
            for i, pos in enumerate(trail):
                fac = (i / (n_pts - 1)) ** 1.5   # 0=más viejo, 1=más nuevo
                if fac < 0.02:
                    continue
                # RGB escalado por brillo (sin canal alpha — blit aditivo)
                brightness = fac * cfg.TRAIL_MAX_ALPHA / 255.0
                rc = int(color[0] * brightness)
                gc = int(color[1] * brightness)
                bc = int(color[2] * brightness)
                r_dot = max(2, int(cfg.BOB_RADIUS * 0.65 * fac))
                pygame.draw.circle(
                    self._trail_surf, (rc, gc, bc),
                    (int(pos[0]), int(pos[1])), r_dot,
                )
        surface.blit(self._trail_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # ── Bolas: glow + núcleo brillante ─────────────────────────────
        for k in range(cfg.N):
            px, py = self._bob_pos[k]
            color  = self._colors[k]
            fl     = self._flash[k]

            # Glow con boost en el momento del cruce
            glow_alpha = min(255, int(cfg.GLOW_MAX_ALPHA * (1.0 + fl * cfg.BOB_FLASH_GLOW_BOOST)))
            draw_glow(
                surface, (px, py),
                cfg.BOB_RADIUS * cfg.GLOW_RADIUS_SCALE,
                color,
                cfg.GLOW_LAYERS,
                glow_alpha,
            )
            # Núcleo blanco que crece brevemente en el cruce
            core_r = max(3, int(cfg.BOB_RADIUS * (0.55 + 0.45 * fl)))
            draw_circle_filled(surface, (235, 242, 255), (int(px), int(py)), core_r)

        # ── Pulsos: anillos expansivos aditivos ────────────────────────
        if self._pulses:
            self._pulse_surf.fill((0, 0, 0))
            for pulse in self._pulses:
                pcx, pcy, frame_start, pcolor = pulse
                age      = self.frame_count - frame_start
                progress = age / cfg.PULSE_DURATION_FRAMES
                r_ring   = max(1, int(cfg.PULSE_RADIUS_MAX * progress))
                fade     = (1.0 - progress) ** 2
                scale    = fade * cfg.PULSE_MAX_ALPHA / 255.0
                rc = int(pcolor[0] * scale)
                gc = int(pcolor[1] * scale)
                bc = int(pcolor[2] * scale)
                # Anillo doble: uno grueso exterior y uno delgado interior
                pygame.draw.circle(
                    self._pulse_surf, (rc, gc, bc),
                    (int(pcx), int(pcy)), r_ring, 3,
                )
                if r_ring > 6:
                    rc2 = int(rc * 0.5)
                    gc2 = int(gc * 0.5)
                    bc2 = int(bc * 0.5)
                    pygame.draw.circle(
                        self._pulse_surf, (rc2, gc2, bc2),
                        (int(pcx), int(pcy)), r_ring - 5, 1,
                    )
            surface.blit(self._pulse_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # ── Hook text (overlay fijo arriba) ────────────────────────────
        self.draw_hook_text(surface, cfg.HOOK_TEXT)

    def is_finished(self) -> bool:
        cfg = self.sim_cfg
        total_secs = cfg.WAIT_SECS + cfg.T_LOOP + cfg.SYNC_SECS
        return self.frame_count >= round(total_secs * ecfg.FPS)
