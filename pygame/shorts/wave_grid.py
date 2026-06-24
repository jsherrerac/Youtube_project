"""
Wave Grid — grilla NxN de puntos oscilantes, 3 actos con transiciones suaves.

Acto 1: ondas circulares (desfase por distancia al centro)
Acto 2: ondas diagonales (desfase por x+y)
Acto 3: espiral giratoria (desfase por ángulo al centro)

Uso (desde pygame/):
    python shorts/wave_grid.py           # preview
    python shorts/wave_grid.py --record  # graba mp4 en shorts/output/
"""

import sys
import os
import math
import argparse
import colorsys

import pygame
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.effects import draw_glow
from engine.recorder import Recorder
from engine.audio import AudioLog

# ══════════════════════════════════════════════════════════════════════════
# CONSTANTES — edita aquí para iterar el feel
# ══════════════════════════════════════════════════════════════════════════
GRID_SIZE        = 30      # puntos por lado  (NxN)  — bajar a 20 para preview rápido
ACT_DURATION     = 7.0     # segundos por acto
TRANS_DURATION   = 0.5     # segundos de crossfade entre actos
POINT_SIZE       = 7       # radio base del punto en px
GLOW_RADIUS      = 3.5     # multiplicador del halo relativo a POINT_SIZE
GLOW_INTENSITY   = 1.5     # multiplicador global de brillo del glow
GLOW_MAX_ALPHA   = 210     # brillo base del halo (0-255)
GLOW_PULSE_RATIO = 0.55    # fracción de variación del halo con la onda
GLOW_MIN_FACTOR  = 0.35    # brillo mínimo del glow en el punto bajo de la onda
CORE_BRIGHTNESS  = 255     # brillo del núcleo blanco (0-255)
HUE_MODE         = "position"  # "position" = rainbow diagonal | "phase" = por fase

N_CYCLES         = 7       # ciclos de oscilación en T_TOTAL → garantiza loop perfecto
AMPLITUDE_Y      = 24      # desplazamiento vertical máx en px
SIZE_PULSE       = 0.50    # fracción de variación del radio con la onda (0=nada)

K_CIRCULAR       = 4.5     # acto 1: ciclos radiales desde el centro
K_DIAGONAL       = 4.5     # acto 2: ciclos a lo largo de la diagonal
K_SPIRAL         = 3.0     # acto 3: brazos de la espiral

GRID_MARGIN_X    = 60      # margen horizontal (cada lado) en px
GRID_MARGIN_Y    = 150     # margen vertical (cada lado) en px  (~8% de 1920)

AUDIO_STEP       = 3       # muestrear 1 de cada N columnas en la fila central
PENTATONIC_HZ    = [       # C mayor pentatónica, 10 notas (grave → aguda)
    261.63, 293.66, 329.63, 392.00, 440.00,
    523.25, 587.33, 659.25, 783.99, 880.00,
]

BG_COLOR         = (0, 0, 0)
SPECTRUM_SAT     = 0.95
SPECTRUM_HUE_MAX = 0.85

ACT_TEXTS        = ["same formula", "different phase", "infinite patterns"]
TEXT_Y           = 1800    # posición vertical del texto (bajo la grilla expandida)
TEXT_SIZE        = 52
TEXT_MAX_ALPHA   = 175

W, H, FPS = 1080, 1920, 60
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "wave_grid.mp4")
# ══════════════════════════════════════════════════════════════════════════

TAU     = 2 * math.pi
T_TOTAL = 3 * ACT_DURATION + 2 * TRANS_DURATION   # total video en segundos
OMEGA   = TAU * N_CYCLES / T_TOTAL                 # rad/s — garantiza loop


# ── Pre-cómputo de la grilla ──────────────────────────────────────────────

def build_grid() -> dict:
    n = GRID_SIZE
    grid_w = W - 2 * GRID_MARGIN_X
    grid_h = H - 2 * GRID_MARGIN_Y
    cx, cy = W / 2.0, H / 2.0

    cols = np.linspace(GRID_MARGIN_X, W - GRID_MARGIN_X, n)
    rows = np.linspace(GRID_MARGIN_Y, H - GRID_MARGIN_Y, n)
    BX, BY = np.meshgrid(cols, rows)   # shape (n, n)

    DX   = BX - cx
    DY   = BY - cy
    DIST = np.sqrt(DX**2 + DY**2)
    ANG  = np.arctan2(DY, DX)          # [-π, π]

    max_dist = max(float(DIST.max()), 1.0)

    # Fases espaciales para cada acto
    PH = [
        -K_CIRCULAR * TAU * DIST / max_dist,                          # acto 1
        -K_DIAGONAL * TAU * (DX + DY) / (grid_w + grid_h) * 2.0,     # acto 2
         K_SPIRAL   * ANG,                                             # acto 3
    ]

    # Colores: degradado diagonal arcoíris
    idx = np.arange(n)
    hue_map = (idx.reshape(n, 1) + idx.reshape(1, n)) / (2.0 * max(n - 1, 1)) * SPECTRUM_HUE_MAX
    colors = np.zeros((n, n, 3), dtype=np.uint8)
    for i in range(n):
        for j in range(n):
            r, g, b = colorsys.hsv_to_rgb(float(hue_map[i, j]), SPECTRUM_SAT, 1.0)
            colors[i, j] = (int(r * 255), int(g * 255), int(b * 255))

    # Fila central para audio
    mid     = n // 2
    acols   = list(range(0, n, AUDIO_STEP))

    return {
        "BX": BX, "BY": BY,
        "PH": PH,
        "colors": colors,
        "mid_row": mid,
        "audio_cols": acols,
        "prev_audio_waves": np.zeros(len(acols)),
    }


# ── Lógica de actos y transiciones ───────────────────────────────────────

def get_act_blend(t: float):
    """Devuelve (idx_a, idx_b, blend∈[0,1]) para interpolar fases."""
    t1  = ACT_DURATION
    t1t = t1 + TRANS_DURATION
    t2  = t1t + ACT_DURATION
    t2t = t2  + TRANS_DURATION

    def smooth(x: float) -> float:
        return x * x * (3.0 - 2.0 * x)   # smoothstep cúbico

    if t < t1:
        return 0, 1, 0.0
    elif t < t1t:
        return 0, 1, smooth((t - t1) / TRANS_DURATION)
    elif t < t2:
        return 1, 2, 0.0
    elif t < t2t:
        return 1, 2, smooth((t - t2) / TRANS_DURATION)
    else:
        return 2, 2, 0.0


def get_text_alphas(t: float) -> list[int]:
    """Alpha de cada texto de acto (fade in al 60% del acto, fade out en la transición)."""
    act_starts = [0.0,
                  ACT_DURATION + TRANS_DURATION,
                  2 * ACT_DURATION + 2 * TRANS_DURATION]
    alphas = []
    for i, ts in enumerate(act_starts):
        te  = ts + ACT_DURATION
        ttr = te + TRANS_DURATION

        t_in_s  = ts + ACT_DURATION * 0.60
        t_in_e  = ts + ACT_DURATION * 0.78
        t_out_s = te
        t_out_e = ttr if i < 2 else T_TOTAL   # acto 3: sin fade-out

        if t < t_in_s or t >= t_out_e:
            a = 0.0
        elif t < t_in_e:
            a = (t - t_in_s) / (t_in_e - t_in_s)
        elif t < t_out_s:
            a = 1.0
        elif t_out_e > t_out_s:
            a = 1.0 - (t - t_out_s) / (t_out_e - t_out_s)
        else:
            a = 1.0

        alphas.append(max(0, min(255, int(a * TEXT_MAX_ALPHA))))
    return alphas


# ── Renderizado ───────────────────────────────────────────────────────────

def _draw_points(surface: pygame.Surface, glow_surf: pygame.Surface,
                 grid: dict, waves: np.ndarray) -> None:
    """Dibuja todos los puntos: glow aditivo (un blit) + núcleo blanco."""
    n       = GRID_SIZE
    BX, BY  = grid["BX"], grid["BY"]
    colors  = grid["colors"]

    # ── Glow: todos los puntos en una surface negra, luego un blit ADD ──
    glow_surf.fill((0, 0, 0))

    for i in range(n):
        for j in range(n):
            w   = float(waves[i, j])
            px  = int(BX[i, j])
            py  = int(BY[i, j] + AMPLITUDE_Y * w)
            sz  = max(2.0, POINT_SIZE * (1.0 + SIZE_PULSE * w))
            gr  = sz * GLOW_RADIUS
            gbr = max(GLOW_MIN_FACTOR, 1.0 + GLOW_PULSE_RATIO * w) * GLOW_INTENSITY * GLOW_MAX_ALPHA / 255.0
            r   = int(colors[i, j, 0])
            g_  = int(colors[i, j, 1])
            b   = int(colors[i, j, 2])

            # 4 capas concéntricas externo→interno (el interno sobreescribe el externo)
            for rfrac, bfrac in ((1.00, 0.07), (0.65, 0.16), (0.40, 0.38), (0.20, 0.80)):
                rr     = max(1, int(gr * rfrac))
                bright = min(1.0, gbr * bfrac)
                pygame.draw.circle(
                    glow_surf,
                    (int(r * bright), int(g_ * bright), int(b * bright)),
                    (px, py), rr,
                )

    surface.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    # ── Núcleo blanco sobre la surface final ────────────────────────────
    for i in range(n):
        for j in range(n):
            w   = float(waves[i, j])
            px  = int(BX[i, j])
            py  = int(BY[i, j] + AMPLITUDE_Y * w)
            sz  = max(1.0, POINT_SIZE * (0.55 + 0.45 * (w + 1.0) * 0.5))
            cb = CORE_BRIGHTNESS
            pygame.draw.circle(surface, (cb, cb, 255), (px, py), max(1, int(sz)))


def _draw_text(surface: pygame.Surface, t: float,
               text_surfs: list[pygame.Surface]) -> None:
    alphas = get_text_alphas(t)
    for i, (surf, alpha) in enumerate(zip(text_surfs, alphas)):
        if alpha <= 0:
            continue
        surf.set_alpha(alpha)
        rect = surf.get_rect(centerx=W // 2, y=TEXT_Y)
        surface.blit(surf, rect)


# ── Loop principal ────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Wave Grid Short")
    parser.add_argument("--record", action="store_true",
                        help="Graba mp4 offline en shorts/output/")
    args = parser.parse_args()

    pygame.init()
    pygame.font.init()

    scale  = 0.25 if args.record else 0.40
    screen = pygame.display.set_mode((int(W * scale), int(H * scale)))
    pygame.display.set_caption("Wave Grid — grabando..." if args.record else "Wave Grid")
    surface   = pygame.Surface((W, H))
    glow_surf = pygame.Surface((W, H))   # surface reutilizable para el glow

    font       = pygame.font.SysFont("Arial", TEXT_SIZE)
    text_surfs = [font.render(txt, True, (255, 255, 255)) for txt in ACT_TEXTS]

    grid       = build_grid()
    audio_log  = AudioLog()

    recorder    = None
    total_frames = round(T_TOTAL * FPS)
    if args.record:
        recorder = Recorder(OUTPUT_PATH, FPS, (W, H))
        print(f"[wave_grid] Grabando {total_frames} frames ({T_TOTAL:.1f}s)…")

    clock   = pygame.time.Clock()
    frame   = 0
    running = True

    while running and frame < total_frames:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        t = frame / FPS   # tiempo determinista: garantiza loop y sync de audio

        # ── Fases blended ──────────────────────────────────────────────
        ai, bi, blend = get_act_blend(t)
        PH = grid["PH"]
        phases = PH[ai] if blend == 0.0 else (1.0 - blend) * PH[ai] + blend * PH[bi]
        waves  = np.sin(OMEGA * t + phases)   # shape (N, N)

        # ── Audio: fila central, detección de cruce de signo ───────────
        mid   = grid["mid_row"]
        acols = grid["audio_cols"]
        aw    = waves[mid, acols]
        for k, changed in enumerate(grid["prev_audio_waves"] * aw < 0):
            if changed:
                hz = PENTATONIC_HZ[k % len(PENTATONIC_HZ)]
                audio_log.log(frame, f"note:{hz:.2f}")
        grid["prev_audio_waves"] = aw.copy()

        # ── Dibujo ─────────────────────────────────────────────────────
        surface.fill(BG_COLOR)
        _draw_points(surface, glow_surf, grid, waves)
        _draw_text(surface, t, text_surfs)

        if recorder:
            recorder.capture(surface)

        scaled = pygame.transform.scale(surface, screen.get_size())
        screen.blit(scaled, (0, 0))
        pygame.display.flip()

        if not args.record:
            clock.tick(FPS)

        frame += 1

    if recorder:
        recorder.finish()
        print(f"[wave_grid] Video sin audio: {OUTPUT_PATH}")
        audio_log.build_and_mux(OUTPUT_PATH, FPS, frame)
        print(f"[wave_grid] Listo: {OUTPUT_PATH}")

    pygame.quit()


if __name__ == "__main__":
    main()
