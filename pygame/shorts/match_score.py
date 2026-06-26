"""
Match Score — partido entre dos países del Mundial 2026.
Rebote contra circunferencia = gol. Spike = muerte. Termina cuando ambas bolas mueren.
Formato: 1080x1920 Short vertical, 60fps.

Uso:
    python shorts/match_score.py            # preview
    python shorts/match_score.py --record   # graba MP4 en shorts/output/
"""

# ═══════════════════════════════════════════════════════════════════════════
# ██  CONFIGURACIÓN DEL PARTIDO — editar solo este bloque para cada juego  ██
# ═══════════════════════════════════════════════════════════════════════════

TEAM_LEFT   = "COD"   # código equipo izquierdo  ← línea 14, CAMBIAR AQUÍ
TEAM_RIGHT  = "UZB"   # código equipo derecho    ← línea 15, CAMBIAR AQUÍ
RANDOM_SEED = 23  # int → resultado fijo | None → diferente cada vez ← línea 16

CIRCLE_RGB       = (255, 255, 255)  # color de la circunferencia           ← línea 18
CIRCLE_THICKNESS = 4                # grosor de la línea en px             ← línea 19

# ═══════════════════════════════════════════════════════════════════════════

import os
import sys
import math
import wave
import random
import argparse
import subprocess
import importlib.util

import pygame
import numpy as np
import imageio_ffmpeg

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine.effects import draw_glow

# ── Cargar world_cup_winner como módulo para reutilizar utilidades ─────────
_WCW_PATH = os.path.join(os.path.dirname(__file__), "world_cup_winner.py")
_wcw_spec = importlib.util.spec_from_file_location("_wcw", _WCW_PATH)
_wcw      = importlib.util.module_from_spec(_wcw_spec)
_wcw_spec.loader.exec_module(_wcw)

# Utilidades reutilizadas directamente de world_cup_winner
ensure_flag              = _wcw.ensure_flag
get_flag_ball            = _wcw.get_flag_ball
get_flag_sub             = _wcw.get_flag_sub
COUNTRIES_COLORS         = _wcw.COUNTRIES_COLORS
FLAGS_DIR                = _wcw.FLAGS_DIR
Particle                 = _wcw.Particle
spawn_explosion          = _wcw.spawn_explosion
collide_particles        = _wcw.collide_particles
push_particles_from_ball = _wcw.push_particles_from_ball
gen_bong                 = _wcw.gen_bong
gen_sad_whoosh           = _wcw.gen_sad_whoosh
gen_fanfare              = _wcw.gen_fanfare
gen_explosion            = _wcw.gen_explosion
pt_seg_dist              = _wcw.pt_seg_dist

_ASSETS_DIR  = os.path.join(os.path.dirname(__file__), "assets")
_mp3_cache: dict[str, np.ndarray] = {}

def _load_mp3(filename: str) -> np.ndarray:
    """Decodifica un MP3 a PCM int16 mono 44100 Hz usando ffmpeg."""
    if filename in _mp3_cache:
        return _mp3_cache[filename]
    path = os.path.join(_ASSETS_DIR, filename)
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [ffmpeg_exe, '-i', path, '-f', 's16le', '-ac', '1', '-ar', str(SAMPLE_RATE), '-'],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    arr = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float64)
    _mp3_cache[filename] = arr
    return arr


# ════════════════════════════════════════════════════════════════════════════
# MAPEO DE CÓDIGOS DE EQUIPO
# ════════════════════════════════════════════════════════════════════════════

TEAM_TO_COUNTRY = {
    "ARG": "Argentina", "FRA": "France",        "ESP": "Spain",
    "BRA": "Brazil",    "ENG": "England",        "GER": "Germany",
    "POR": "Portugal",  "NED": "Netherlands",    "CRO": "Croatia",
    "BEL": "Belgium",   "ITA": "Italy",          "URU": "Uruguay",
    "COL": "Colombia",  "MAR": "Morocco",        "JPN": "Japan",
    "USA": "USA",
    "NOR": "Norway",    "SEN": "Senegal",        "IRQ": "Iraq",
    "CPV": "Cape Verde","SAU": "Saudi Arabia",   "EGY": "Egypt",
    "IRN": "Iran",      "NZL": "New Zealand",
    # Mundial 2026 — nuevos
    "GHA": "Ghana",     "PAN": "Panama",         "COD": "DR Congo",
    "UZB": "Uzbekistan","ALG": "Algeria",         "AUT": "Austria",
    "JOR": "Jordan",
}


# ════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ════════════════════════════════════════════════════════════════════════════

WIDTH, HEIGHT = 1080, 1920
FPS           = 60
SAMPLE_RATE   = 44100

TITLE_Y  = 100   # centro del bloque de título
SCORE_Y  = 280   # centro del marcador

ARENA_CENTER = np.array([WIDTH / 2.0, 1100.0])
ARENA_RADIUS = 430

BALL_INITIAL_RADIUS    = 18
BALL_GROWTH_PER_BOUNCE = 0.40
MAX_BALL_R    = 150
BALL_SPEED0   = 500.0
ACCEL_RATE    = 0.08
MAX_SPEED     = 1900.0

# 4 spikes en cruz — más cobertura para muertes rápidas y scores realistas
SPIKE_ANGLES_DEG = [0, 90, 180, 270]
SPIKE_ANGLES     = [math.radians(a) for a in SPIKE_ANGLES_DEG]
SPIKE_OMEGA      = 2 * math.pi / (FPS * 10)
SPIKE_LENGTH     = 100
SPIKE_WIDTH      = 130

GRAVITY   = 260.0
PART_DAMP = 0.993

PULSE_FRAMES = 12     # duración del flash de gol (0.2 s)
FINAL_FRAMES = int(FPS * 3.5)

COLOR_BG         = (0, 0, 0)
MAX_TOTAL_FRAMES = FPS * 90   # tope: 1.5 min

# ── Propagar constantes a _wcw para que spike_pts, spike_hit y
#    bounce_particles_on_spike de _wcw usen los valores de este partido ─────
_wcw.SPIKE_LENGTH        = SPIKE_LENGTH
_wcw.SPIKE_WIDTH         = SPIKE_WIDTH
_wcw.ARENA_CENTER        = ARENA_CENTER
_wcw.ARENA_RADIUS        = ARENA_RADIUS
_wcw.GRAVITY             = GRAVITY
_wcw.PART_DAMP           = PART_DAMP
_wcw.BALL_INITIAL_RADIUS = BALL_INITIAL_RADIUS
_wcw.MAX_BALL_R          = MAX_BALL_R


# ════════════════════════════════════════════════════════════════════════════
# FÍSICA LOCAL
# ════════════════════════════════════════════════════════════════════════════

def spike_pts(angle: float):
    half_arc = math.asin(min(0.999, (SPIKE_WIDTH / 2) / ARENA_RADIUS))
    tip = ARENA_CENTER + np.array([math.cos(angle), math.sin(angle)]) * (ARENA_RADIUS - SPIKE_LENGTH)
    bl  = ARENA_CENTER + np.array([math.cos(angle - half_arc), math.sin(angle - half_arc)]) * ARENA_RADIUS
    br  = ARENA_CENTER + np.array([math.cos(angle + half_arc), math.sin(angle + half_arc)]) * ARENA_RADIUS
    return tip, bl, br


def spike_hit(pos: np.ndarray, r: float, angle: float) -> bool:
    tip, bl, br = spike_pts(angle)
    return min(pt_seg_dist(pos, tip, bl),
               pt_seg_dist(pos, tip, br),
               pt_seg_dist(pos, bl, br)) < r + 4


def wall_bounce(pos: np.ndarray, vel: np.ndarray, r: float):
    delta = pos - ARENA_CENTER
    d     = np.linalg.norm(delta)
    if d + r >= ARENA_RADIUS:
        n = delta / d if d > 1e-6 else np.array([0., -1.])
        if np.dot(vel, n) > 0:
            vel = vel - 2 * np.dot(vel, n) * n
        # buffer ≥ crecimiento del radio para evitar doble rebote el frame siguiente
        buffer = r * BALL_GROWTH_PER_BOUNCE + 4.0
        pos = ARENA_CENTER + n * (ARENA_RADIUS - r - buffer)
        return pos, vel, True
    return pos, vel, False


def bounce_particles_on_spike(particles: list, spike_angle: float):
    tip, bl, br = spike_pts(spike_angle)
    gcx = (float(tip[0]) + float(bl[0]) + float(br[0])) / 3.0
    gcy = (float(tip[1]) + float(bl[1]) + float(br[1])) / 3.0
    edges = [(tip, bl), (tip, br), (bl, br)]
    for p in particles:
        pr = float(p.r)
        for a, b in edges:
            abx = float(b[0] - a[0]); aby = float(b[1] - a[1])
            d2  = abx * abx + aby * aby
            if d2 < 1e-9:
                continue
            apx = float(p.pos[0] - a[0]); apy = float(p.pos[1] - a[1])
            t   = max(0.0, min(1.0, (apx * abx + apy * aby) / d2))
            qx  = float(a[0]) + t * abx; qy = float(a[1]) + t * aby
            dx  = float(p.pos[0]) - qx;  dy = float(p.pos[1]) - qy
            dist2 = dx * dx + dy * dy
            if dist2 < pr * pr and dist2 > 0.0001:
                dist = dist2 ** 0.5
                nx = dx / dist; ny = dy / dist
                if nx * (gcx - qx) + ny * (gcy - qy) > 0:
                    nx = -nx; ny = -ny
                p.pos[0] += nx * (pr - dist + 1.0)
                p.pos[1] += ny * (pr - dist + 1.0)
                vn = float(p.vel[0]) * nx + float(p.vel[1]) * ny
                if vn < 0:
                    p.vel[0] -= 1.6 * vn * nx
                    p.vel[1] -= 1.6 * vn * ny


# ════════════════════════════════════════════════════════════════════════════
# AUDIO
# ════════════════════════════════════════════════════════════════════════════

def gen_cheer(dur: float = 0.28) -> np.ndarray:
    """Arpeggio ascendente corto — celebración de gol."""
    n   = int(SAMPLE_RATE * dur)
    t   = np.linspace(0, dur, n, endpoint=False)
    buf = np.zeros(n)
    for freq, delay in [(523.25, 0.00), (659.25, 0.07), (783.99, 0.14)]:
        d0 = int(delay * SAMPLE_RATE)
        tt = t[d0:]
        atk = np.minimum(tt / 0.007, 1.0)
        dec = np.exp(-9.0 * tt)
        s   = (0.55 * np.sin(2 * math.pi * freq * tt)
             + 0.20 * np.sin(2 * math.pi * freq * 2 * tt))
        buf[d0:d0 + len(tt)] += s * atk * dec
    peak = np.max(np.abs(buf))
    if peak > 0:
        buf /= peak * 1.05
    return (buf * 0.72 * 32767).astype(np.int16)


def mix_audio(events: list, total_frames: int) -> np.ndarray:
    total_samples = int(total_frames / FPS * SAMPLE_RATE) + SAMPLE_RATE
    buf = np.zeros(total_samples, dtype=np.float64)
    for fn, stype, param in events:
        pos = int(fn * SAMPLE_RATE / FPS)
        if stype == 'bong':
            snd = gen_bong(param if param else 220.0).astype(np.float64)
        elif stype == 'cheer':
            snd = gen_cheer().astype(np.float64)
        elif stype == 'explosion':
            snd = gen_explosion().astype(np.float64)
        elif stype == 'pessi':
            snd = _load_mp3('pessi.mp3')
        elif stype == 'bet365':
            snd = _load_mp3('bet-365-goal-sound.mp3')
        else:
            continue
        end = min(pos + len(snd), total_samples)
        buf[pos:end] += snd[:end - pos]
    peak = np.max(np.abs(buf))
    if peak > 0:
        buf = buf / peak * 0.90 * 32767
    return buf.astype(np.int16)


# ════════════════════════════════════════════════════════════════════════════
# DIBUJO
# ════════════════════════════════════════════════════════════════════════════

def make_arena_glow() -> pygame.Surface:
    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy = int(ARENA_CENTER[0]), int(ARENA_CENTER[1])
    r, g, b = CIRCLE_RGB
    for i in range(4, 0, -1):
        pygame.draw.circle(layer, (r, g, b, 7), (cx, cy), ARENA_RADIUS + i * 3, 6)
    return layer


def draw_arena(surf: pygame.Surface, arena_glow: pygame.Surface):
    surf.blit(arena_glow, (0, 0))
    pygame.draw.circle(surf, CIRCLE_RGB,
                       (int(ARENA_CENTER[0]), int(ARENA_CENTER[1])),
                       ARENA_RADIUS, CIRCLE_THICKNESS)


def draw_spikes(surf: pygame.Surface, rotation: float):
    COLOR_SPIKE = (155, 155, 160)
    for angle in SPIKE_ANGLES:
        tip, bl, br = spike_pts(angle + rotation)
        pts = [(int(p[0]), int(p[1])) for p in (tip, bl, br)]
        pygame.draw.polygon(surf, COLOR_SPIKE, pts)
        pygame.draw.polygon(surf, (205, 205, 210), pts, 2)


def draw_ball(surf: pygame.Surface, country: str, pos: np.ndarray, r: int):
    glow_col = COUNTRIES_COLORS[country]
    draw_glow(surf, (int(pos[0]), int(pos[1])), r, glow_col, layers=14, max_alpha=110)
    flag = get_flag_ball(country, r * 2)
    if flag:
        surf.blit(flag, flag.get_rect(center=(int(pos[0]), int(pos[1]))))
    else:
        pygame.draw.circle(surf, glow_col, (int(pos[0]), int(pos[1])), r)


def draw_title(surf: pygame.Surface, font_big: pygame.font.Font,
               font_sub: pygame.font.Font, name_l: str, name_r: str):
    t1 = font_big.render(f"{name_l} vs {name_r}", True, (255, 255, 255))
    t2 = font_sub.render("but physics plays it", True, (160, 160, 160))
    surf.blit(t1, t1.get_rect(centerx=WIDTH // 2, centery=TITLE_Y - 18))
    surf.blit(t2, t2.get_rect(centerx=WIDTH // 2, centery=TITLE_Y + 58))


def draw_scoreboard(surf: pygame.Surface, font_score: pygame.font.Font,
                    cl: str, cr: str,
                    sl: int, sr: int,
                    dead_l: bool, dead_r: bool,
                    pulse_l: int, pulse_r: int):
    FLAG_H = 62

    def score_color(pulse, dead):
        if dead:
            return (90, 90, 90)
        if pulse > 0:
            t = pulse / PULSE_FRAMES
            return (255, int(215 * (1 - t * 0.3)), int(30 * (1 - t)))
        return (255, 255, 255)

    fl  = get_flag_sub(cl, height=FLAG_H)
    fr  = get_flag_sub(cr, height=FLAG_H)
    tl  = font_score.render(str(sl), True, score_color(pulse_l, dead_l))
    td  = font_score.render("–",     True, (120, 120, 120))
    tr  = font_score.render(str(sr), True, score_color(pulse_r, dead_r))

    GAP = 18
    fw_l = fl.get_width() + GAP if fl else 0
    fw_r = fr.get_width() + GAP if fr else 0
    total = fw_l + tl.get_width() + GAP + td.get_width() + GAP + tr.get_width() + fw_r
    x    = WIDTH // 2 - total // 2
    cy   = SCORE_Y

    def blit_c(img, x):
        surf.blit(img, (x, cy - img.get_height() // 2))
        return x + img.get_width() + GAP

    if fl:  x = blit_c(fl, x)
    x = blit_c(tl, x)
    x = blit_c(td, x)
    x = blit_c(tr, x)
    if fr:  blit_c(fr, x)


def draw_final(surf: pygame.Surface, font_big: pygame.font.Font,
               font_med: pygame.font.Font, font_score: pygame.font.Font,
               cl: str, cr: str, sl: int, sr: int,
               timer: int, particles: list):
    progress = 1.0 - timer / FINAL_FRAMES
    alpha    = min(255, int(progress * 4 * 255))

    # Partículas acumuladas del partido
    for p in particles:
        p.draw(surf)

    # Título FINAL
    ft = font_big.render("FINAL", True, (255, 215, 0))
    ft.set_alpha(alpha)
    surf.blit(ft, ft.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 - 420))

    # Banderas grandes
    fl = get_flag_sub(cl, height=160)
    fr = get_flag_sub(cr, height=160)
    cy_flags = HEIGHT // 2 - 200
    if fl:
        surf.blit(fl, fl.get_rect(right=WIDTH // 2 - 70, centery=cy_flags))
    if fr:
        surf.blit(fr, fr.get_rect(left=WIDTH // 2 + 70,  centery=cy_flags))

    # Marcador grande
    tl = font_score.render(str(sl), True, (255, 255, 255))
    td = font_score.render("–",     True, (140, 140, 140))
    tr = font_score.render(str(sr), True, (255, 255, 255))
    for t in (tl, td, tr):
        t.set_alpha(alpha)
    total = tl.get_width() + 24 + td.get_width() + 24 + tr.get_width()
    x  = WIDTH // 2 - total // 2
    cy = HEIGHT // 2 + 60
    surf.blit(tl, (x, cy - tl.get_height() // 2)); x += tl.get_width() + 24
    surf.blit(td, (x, cy - td.get_height() // 2)); x += td.get_width() + 24
    surf.blit(tr, (x, cy - tr.get_height() // 2))

    # Resultado
    if sl > sr:
        msg = f"{cl} wins!"
    elif sr > sl:
        msg = f"{cr} wins!"
    else:
        msg = "Draw!"
    wt = font_med.render(msg, True, (255, 215, 0))
    wt.set_alpha(alpha)
    surf.blit(wt, wt.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 + 240))


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    country_l = TEAM_TO_COUNTRY[TEAM_LEFT]
    country_r = TEAM_TO_COUNTRY[TEAM_RIGHT]

    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()

    print("Verificando banderas...")
    ensure_flag(country_l)
    ensure_flag(country_r)

    pygame.init()
    pygame.font.init()

    font_big   = pygame.font.SysFont("Arial", 68, bold=True)
    font_med   = pygame.font.SysFont("Arial", 56, bold=True)
    font_sub   = pygame.font.SysFont("Arial", 44)
    font_score = pygame.font.SysFont("Arial", 120, bold=True)

    scale  = 0.22 if args.record else 0.36
    screen = pygame.display.set_mode((int(WIDTH * scale), int(HEIGHT * scale)))
    pygame.display.set_caption(
        f"{TEAM_LEFT} vs {TEAM_RIGHT}" + (" — grabando..." if args.record else ""))
    surface = pygame.Surface((WIDTH, HEIGHT))

    out_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_mp4  = os.path.join(out_dir, f"match_{TEAM_LEFT}_vs_{TEAM_RIGHT}.mp4")
    temp_vid = os.path.join(out_dir, f"_ms_{TEAM_LEFT}_{TEAM_RIGHT}.mp4")
    temp_wav = os.path.join(out_dir, f"_ms_{TEAM_LEFT}_{TEAM_RIGHT}.wav")

    vid_gen = None
    if args.record:
        vid_gen = imageio_ffmpeg.write_frames(
            temp_vid, (WIDTH, HEIGHT),
            fps=FPS, pix_fmt_in='rgb24', pix_fmt_out='yuv420p',
            codec='libx264', quality=None, macro_block_size=1,
            output_params=['-crf', '18', '-preset', 'fast'],
            ffmpeg_log_level='quiet',
        )
        vid_gen.send(None)

    def push(s: pygame.Surface):
        if vid_gen is None:
            return
        arr = pygame.surfarray.array3d(s)
        vid_gen.send(np.ascontiguousarray(arr.transpose(1, 0, 2)).tobytes())

    arena_glow = make_arena_glow()

    # ── Estado ────────────────────────────────────────────────────────────
    sound_events:  list = []
    all_particles: list = []
    frame          = 0
    running        = True
    rotation       = 0.0
    note_idx       = 0

    score_l = 0;  score_r = 0
    dead_l  = False; dead_r = False
    pulse_l = 0;  pulse_r = 0

    state       = 'playing'
    final_timer = 0

    _PENTA = [130.81, 146.83, 164.81, 196.00, 220.00]

    def init_ball(side: str):
        ang = random.uniform(0, 2 * math.pi)
        spd = random.uniform(380, BALL_SPEED0)
        vel = np.array([math.cos(ang), math.sin(ang)]) * spd
        ox  = -100.0 if side == 'left' else 100.0
        oy  = random.uniform(-60, 60)
        return (ARENA_CENTER + np.array([ox, oy])).copy(), vel.copy(), BALL_INITIAL_RADIUS

    pos_l, vel_l, r_l = init_ball('left')
    pos_r, vel_r, r_r = init_ball('right')

    clock = pygame.time.Clock()

    while running and frame < MAX_TOTAL_FRAMES:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                running = False

        dt = 1.0 / FPS
        rotation += SPIKE_OMEGA
        if pulse_l > 0: pulse_l -= 1
        if pulse_r > 0: pulse_r -= 1

        # ── Lógica ────────────────────────────────────────────────────────
        if state == 'playing':

            # Bola izquierda
            if not dead_l:
                pos_l += vel_l * dt
                if any(spike_hit(pos_l, r_l, sa + rotation) for sa in SPIKE_ANGLES):
                    all_particles.extend(spawn_explosion(pos_l, COUNTRIES_COLORS[country_l], r_l))
                    sound_events.append((frame, 'explosion', None))
                    sound_events.append((frame + FPS // 4, 'pessi', None))
                    dead_l = True
                else:
                    pos_l, vel_l, hit = wall_bounce(pos_l, vel_l, r_l)
                    if hit:
                        score_l += 1
                        pulse_l  = PULSE_FRAMES
                        r_l      = min(int(r_l * (1 + BALL_GROWTH_PER_BOUNCE)), MAX_BALL_R)
                        spd      = np.linalg.norm(vel_l)
                        vel_l    = vel_l / spd * min(spd * (1 + ACCEL_RATE), MAX_SPEED)
                        sound_events.append((frame, 'bong',  _PENTA[note_idx % len(_PENTA)]))
                        sound_events.append((frame + 4, 'cheer', None))
                        note_idx += 1

            # Bola derecha
            if not dead_r:
                pos_r += vel_r * dt
                if any(spike_hit(pos_r, r_r, sa + rotation) for sa in SPIKE_ANGLES):
                    all_particles.extend(spawn_explosion(pos_r, COUNTRIES_COLORS[country_r], r_r))
                    sound_events.append((frame, 'explosion', None))
                    sound_events.append((frame + FPS // 4, 'pessi', None))
                    dead_r = True
                else:
                    pos_r, vel_r, hit = wall_bounce(pos_r, vel_r, r_r)
                    if hit:
                        score_r += 1
                        pulse_r  = PULSE_FRAMES
                        r_r      = min(int(r_r * (1 + BALL_GROWTH_PER_BOUNCE)), MAX_BALL_R)
                        spd      = np.linalg.norm(vel_r)
                        vel_r    = vel_r / spd * min(spd * (1 + ACCEL_RATE), MAX_SPEED)
                        sound_events.append((frame, 'bong',  _PENTA[note_idx % len(_PENTA)]))
                        sound_events.append((frame + 4, 'cheer', None))
                        note_idx += 1

            if dead_l and dead_r:
                sound_events.append((frame + FPS // 3, 'bet365', None))
                state       = 'final'
                final_timer = FINAL_FRAMES

        elif state == 'final':
            final_timer -= 1
            if final_timer <= 0:
                running = False

        # ── Partículas ────────────────────────────────────────────────────
        for p in all_particles:
            p.step(dt)
        if all_particles:
            for _ in range(3):
                for sa in SPIKE_ANGLES:
                    bounce_particles_on_spike(all_particles, sa + rotation)
                collide_particles(all_particles)
            for bpos, br, bvel in (
                [] if dead_l else [(pos_l, r_l, vel_l)]
            ) + (
                [] if dead_r else [(pos_r, r_r, vel_r)]
            ):
                push_particles_from_ball(all_particles, bpos, br, bvel)

        # ── Dibujo ────────────────────────────────────────────────────────
        surface.fill(COLOR_BG)

        if state == 'final':
            draw_final(surface, font_big, font_med, font_score,
                       country_l, country_r, score_l, score_r,
                       final_timer, all_particles)
        else:
            draw_arena(surface, arena_glow)
            draw_spikes(surface, rotation)

            for p in all_particles:
                p.draw(surface)

            if not dead_l:
                draw_ball(surface, country_l, pos_l, r_l)
            if not dead_r:
                draw_ball(surface, country_r, pos_r, r_r)

            draw_title(surface, font_big, font_sub, country_l, country_r)
            draw_scoreboard(surface, font_score,
                            country_l, country_r,
                            score_l, score_r,
                            dead_l, dead_r,
                            pulse_l, pulse_r)

        push(surface)
        scaled = pygame.transform.scale(surface, screen.get_size())
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        if not args.record:
            clock.tick(FPS)
        frame += 1

    pygame.quit()

    if not args.record:
        return

    vid_gen.close()
    print(f"\nVideo: {frame} frames ({frame / FPS:.1f}s). Generando audio...")

    pcm = mix_audio(sound_events, frame)
    with wave.open(temp_wav, 'w') as wf:
        wf.setnchannels(1); wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE); wf.writeframes(pcm.tobytes())

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([
        ffmpeg_exe, '-y', '-i', temp_vid, '-i', temp_wav,
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', out_mp4,
    ], check=True, stderr=subprocess.DEVNULL)

    for f in (temp_vid, temp_wav):
        if os.path.exists(f):
            os.remove(f)

    print(f"MP4 listo → {out_mp4}")


if __name__ == "__main__":
    main()
