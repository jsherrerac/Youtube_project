"""
double_pendulum_chaos.py — Short vertical 1080×1920, 60 fps, ~23 s
Caos de doble péndulo: dos péndulos casi idénticos que divergen.
"""

import sys
import os
import math
import collections
import pygame

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from engine.effects  import draw_glow
from engine.recorder import Recorder
from engine.audio    import AudioLog, note_to_freq

# ── Constantes ajustables ─────────────────────────────────────────────────────
INITIAL_ANGLE_1        = 2.0          # θ1 (ambos péndulos) en rad
INITIAL_ANGLE_2_LEFT   = 2.0          # θ2 péndulo izquierdo
INITIAL_ANGLE_2_RIGHT  = 2.001        # θ2 péndulo derecho (difiere 0.001 rad)

TRAIL_LENGTH_SECONDS   = 1.5          # duración del rastro en segundos
GLOW_RADIUS            = 18           # radio base del núcleo de la masa
GLOW_INTENSITY         = 230          # max_alpha del halo principal (0–255)
CORE_BRIGHTNESS        = 255          # brillo del núcleo blanco
COLOR_LEFT             = (0, 220, 255)     # cyan brillante
COLOR_RIGHT            = (255, 0, 200)     # magenta brillante
ARM_THICKNESS          = 3            # grosor de los brazos (px)
MASS_RADIUS            = 7            # radio del núcleo de la bolita (px)
DURATION_SECONDS       = 23           # duración total del video

# ── Física ────────────────────────────────────────────────────────────────────
G  = 9.81
L1 = 1.0
L2 = 1.0
M1 = 1.0
M2 = 1.0

# ── Render ────────────────────────────────────────────────────────────────────
W, H          = 1080, 1920
FPS           = 60
SCALE         = 270    # píxeles por unidad de longitud física
PREVIEW_SCALE = 0.25   # fracción para la ventana de preview (0.25 → 270×480)

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'output',
    'double_pendulum_chaos.mp4'
)


def _deriv(th1, w1, th2, w2):
    dth     = th2 - th1
    sin_dth = math.sin(dth)
    cos_dth = math.cos(dth)
    denom   = 2*M1 + M2 - M2 * math.cos(2*dth)

    dw1 = (
        -G*(2*M1 + M2)*math.sin(th1)
        - M2*G*math.sin(th1 - 2*th2)
        - 2*sin_dth*M2*(w2*w2*L2 + w1*w1*L1*cos_dth)
    ) / (L1 * denom)

    dw2 = (
        2*sin_dth*(
            w1*w1*L1*(M1 + M2)
            + G*(M1 + M2)*math.cos(th1)
            + w2*w2*L2*M2*cos_dth
        )
    ) / (L2 * denom)

    return w1, dw1, w2, dw2


def rk4(state, dt):
    th1, w1, th2, w2 = state
    k1 = _deriv(th1,             w1,             th2,             w2)
    k2 = _deriv(th1+dt/2*k1[0], w1+dt/2*k1[1], th2+dt/2*k1[2], w2+dt/2*k1[3])
    k3 = _deriv(th1+dt/2*k2[0], w1+dt/2*k2[1], th2+dt/2*k2[2], w2+dt/2*k2[3])
    k4 = _deriv(th1+dt*k3[0],   w1+dt*k3[1],   th2+dt*k3[2],   w2+dt*k3[3])
    return (
        th1 + dt/6*(k1[0]+2*k2[0]+2*k3[0]+k4[0]),
        w1  + dt/6*(k1[1]+2*k2[1]+2*k3[1]+k4[1]),
        th2 + dt/6*(k1[2]+2*k2[2]+2*k3[2]+k4[2]),
        w2  + dt/6*(k1[3]+2*k2[3]+2*k3[3]+k4[3]),
    )


def positions(state, pivot):
    th1, _, th2, _ = state
    px, py = pivot
    x1 = px + SCALE * math.sin(th1)
    y1 = py + SCALE * math.cos(th1)
    x2 = x1 + SCALE * math.sin(th2)
    y2 = y1 + SCALE * math.cos(th2)
    return (x1, y1), (x2, y2)


def text_alpha(t, t_in, t_out, fade=0.45):
    if t < t_in or t > t_out:
        return 0
    a = min(1.0, (t - t_in) / fade)
    b = min(1.0, (t_out - t) / fade)
    return int(255 * min(a, b))


def blit_text(surface, font, text, y, alpha, color=(255, 255, 255)):
    surf = font.render(text, True, color)
    surf.set_alpha(alpha)
    surface.blit(surf, ((W - surf.get_width()) // 2, y))


def main():
    pygame.init()
    pygame.font.init()

    font_main  = pygame.font.SysFont("Arial", 60, bold=True)
    font_small = pygame.font.SysFont("Arial", 46)

    PW, PH  = int(W * PREVIEW_SCALE), int(H * PREVIEW_SCALE)
    screen  = pygame.display.set_mode((PW, PH))
    surface = pygame.Surface((W, H))   # canvas off-screen a resolución real
    pygame.display.set_caption("Double Pendulum Chaos — preview")

    recorder  = Recorder(OUTPUT_PATH, FPS, (W, H))
    audio_log = AudioLog()

    TRAIL_FRAMES    = int(TRAIL_LENGTH_SECONDS * FPS)
    TOTAL_FRAMES    = DURATION_SECONDS * FPS
    STEPS_PER_FRAME = 17                              # ~0.000980 s por paso RK4
    DT              = 1.0 / (FPS * STEPS_PER_FRAME)

    PIVOT_L = (W // 4,     580)
    PIVOT_R = (3 * W // 4, 580)

    state_L = (INITIAL_ANGLE_1, 0.0, INITIAL_ANGLE_2_LEFT,  0.0)
    state_R = (INITIAL_ANGLE_1, 0.0, INITIAL_ANGLE_2_RIGHT, 0.0)

    trail_L: collections.deque = collections.deque(maxlen=TRAIL_FRAMES)
    trail_R: collections.deque = collections.deque(maxlen=TRAIL_FRAMES)

    scale_L = [note_to_freq(n) for n in ('C4', 'D4', 'E4', 'G4', 'A4')]
    scale_R = [note_to_freq(n) for n in ('G4', 'A4', 'B4', 'D5', 'E5')]
    ni_L = ni_R = 0
    prev_y2_L = prev_y2_R = None
    vy_L = vy_R = 0.0
    last_note_L = last_note_R = -FPS
    COOLDOWN = FPS // 3

    arm_surf   = pygame.Surface((W, H))
    trail_surf = pygame.Surface((W, H))

    for frame in range(TOTAL_FRAMES):
        t = frame / FPS

        # ── Física: pasos RK4 ─────────────────────────────────────────────────
        for _ in range(STEPS_PER_FRAME):
            state_L = rk4(state_L, DT)
            state_R = rk4(state_R, DT)

        (x1L, y1L), (x2L, y2L) = positions(state_L, PIVOT_L)
        (x1R, y1R), (x2R, y2R) = positions(state_R, PIVOT_R)

        # Detectar paso por punto más bajo: vy cambia de + a ≤ 0 (screen y baja = físico sube)
        new_vy_L = (y2L - prev_y2_L) if prev_y2_L is not None else 0.0
        new_vy_R = (y2R - prev_y2_R) if prev_y2_R is not None else 0.0
        if vy_L > 0 and new_vy_L <= 0 and frame - last_note_L > COOLDOWN:
            audio_log.log(frame, f"note:{scale_L[ni_L % len(scale_L)]:.2f}")
            ni_L += 1; last_note_L = frame
        if vy_R > 0 and new_vy_R <= 0 and frame - last_note_R > COOLDOWN:
            audio_log.log(frame, f"note:{scale_R[ni_R % len(scale_R)]:.2f}")
            ni_R += 1; last_note_R = frame
        prev_y2_L, vy_L = y2L, new_vy_L
        prev_y2_R, vy_R = y2R, new_vy_R

        trail_L.append((x2L, y2L))
        trail_R.append((x2R, y2R))

        # ── Render ────────────────────────────────────────────────────────────
        surface.fill((0, 0, 0))

        # --- Trails ---
        trail_surf.fill((0, 0, 0))
        for trail, col in ((trail_L, COLOR_LEFT), (trail_R, COLOR_RIGHT)):
            n = len(trail)
            if n < 2:
                continue
            r, g, b = col
            for i in range(1, n):
                frac  = i / n                # 0=más antiguo, 1=más reciente
                alpha = frac ** 1.6
                c = (int(r*alpha), int(g*alpha), int(b*alpha))
                w_line = max(1, int(4 * frac))
                p0 = (int(trail[i-1][0]), int(trail[i-1][1]))
                p1 = (int(trail[i][0]),   int(trail[i][1]))
                pygame.draw.line(trail_surf, c, p0, p1, w_line)
        surface.blit(trail_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # --- Brazos ---
        arm_surf.fill((0, 0, 0))
        for (p_piv, p_m1, p_m2), col in (
            ((PIVOT_L, (x1L, y1L), (x2L, y2L)), COLOR_LEFT),
            ((PIVOT_R, (x1R, y1R), (x2R, y2R)), COLOR_RIGHT),
        ):
            r, g, b = col
            glow_c   = (int(r*0.12), int(g*0.12), int(b*0.12))
            bright_c = (int(r*0.85), int(g*0.85), int(b*0.85))
            for pa, pb in ((p_piv, p_m1), (p_m1, p_m2)):
                pa_i = (int(pa[0]), int(pa[1]))
                pb_i = (int(pb[0]), int(pb[1]))
                pygame.draw.line(arm_surf, glow_c,   pa_i, pb_i, ARM_THICKNESS + 10)
                pygame.draw.line(arm_surf, bright_c, pa_i, pb_i, ARM_THICKNESS)
        surface.blit(arm_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # --- Pivotes ---
        for piv, col in ((PIVOT_L, COLOR_LEFT), (PIVOT_R, COLOR_RIGHT)):
            draw_glow(surface, piv, 5, col, layers=8, max_alpha=180)
            pygame.draw.circle(surface, (255, 255, 255), piv, 4)

        # --- Masa 1 ---
        for pos, col in (((x1L, y1L), COLOR_LEFT), ((x1R, y1R), COLOR_RIGHT)):
            draw_glow(surface, pos, MASS_RADIUS*2.5, col, layers=10,
                      max_alpha=int(GLOW_INTENSITY * 0.6))
            pygame.draw.circle(surface, (255, 255, 255),
                               (int(pos[0]), int(pos[1])), MASS_RADIUS - 2)

        # --- Masa 2: glow máximo (cuenta la historia) ---
        for pos, col in (((x2L, y2L), COLOR_LEFT), ((x2R, y2R), COLOR_RIGHT)):
            draw_glow(surface, pos, GLOW_RADIUS * 5.0, col, layers=16, max_alpha=GLOW_INTENSITY)
            draw_glow(surface, pos, GLOW_RADIUS * 2.8, col, layers=12,
                      max_alpha=min(255, int(GLOW_INTENSITY * 1.3)))
            draw_glow(surface, pos, GLOW_RADIUS * 1.2, col, layers=8,  max_alpha=255)
            pygame.draw.circle(surface, (255, 255, 255),
                               (int(pos[0]), int(pos[1])), MASS_RADIUS)

        # --- Texto overlay ---
        a = text_alpha(t, 0.0, 4.2, fade=0.4)
        if a:
            blit_text(surface, font_main,  "same pendulum.",       1630, a)
            blit_text(surface, font_main,  "same starting angle.", 1700, a)

        a = text_alpha(t, 3.0, 6.5, fade=0.5)
        if a:
            blit_text(surface, font_small, "(within 0.001°)", 1790, a, (180, 180, 180))

        a = text_alpha(t, 11.0, 17.0, fade=0.6)
        if a:
            blit_text(surface, font_main, "this is chaos.", 1680, a)

        a = text_alpha(t, 19.0, 23.0, fade=0.5)
        if a:
            blit_text(surface, font_main, "tiny difference.",  1630, a)
            blit_text(surface, font_main, "opposite future.",  1700, a)

        # ── Grabar y preview ──────────────────────────────────────────────────
        recorder.capture(surface)
        pygame.transform.scale(surface, (PW, PH), screen)
        pygame.display.flip()

        if frame % 60 == 0:
            print(f"  frame {frame:4d}/{TOTAL_FRAMES}  t={t:.1f}s")

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (
                ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE
            ):
                recorder.finish()
                audio_log.build_and_mux(OUTPUT_PATH, FPS, TOTAL_FRAMES)
                pygame.quit()
                return

    recorder.finish()
    audio_log.build_and_mux(OUTPUT_PATH, FPS, TOTAL_FRAMES)
    print(f"\n[OK] {OUTPUT_PATH}")
    pygame.quit()


if __name__ == '__main__':
    main()
