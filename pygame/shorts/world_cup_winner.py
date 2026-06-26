"""
World Cup Winner 2026 — mundialito temático de spike_melodia.
Arena circular con 3 spikes fijos y un gap en la parte inferior.
La primera bandera que escapa por el gap GANA.
Formato: 1080x1920 Short vertical, 60fps.

Uso:
    python shorts/world_cup_winner.py           # preview
    python shorts/world_cup_winner.py --record  # graba MP4 en shorts/output/
"""

import os
import sys
import math
import wave
import random
import argparse
import subprocess
import importlib.util
import urllib.request

import colorsys

import pygame
import numpy as np
import imageio_ffmpeg

# ── Imports del engine ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine.effects import draw_glow

# ── Funciones puras reutilizadas de spike_melodia via importlib ───────────────
_SM_PATH = os.path.join(os.path.dirname(__file__), "..", "spike_melodia", "spike_melodia.py")
_sm_spec = importlib.util.spec_from_file_location("_sm", _SM_PATH)
_sm      = importlib.util.module_from_spec(_sm_spec)
_sm_spec.loader.exec_module(_sm)
pt_seg_dist            = _sm.pt_seg_dist             # distancia punto→segmento
part_surf              = _sm.part_surf               # surface partícula con glow
gen_note               = _sm.gen_note                # sintetizador piano → int16
gen_explosion          = _sm.gen_explosion           # sintetizador explosión → int16
push_particles_from_ball = _sm.push_particles_from_ball  # empuje bola→partículas (pura)


# ════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ════════════════════════════════════════════════════════════════════════════

WIDTH, HEIGHT = 1080, 1920
FPS           = 60
SAMPLE_RATE   = 44100

# Layout: ~15% texto (0-290px), ~74% arena (670-1530), ~10% libre
HEADER_Y1     = 85    # "Who will win the"
HEADER_Y2     = 175   # "World Cup?"
SUBTITLE_Y    = 290   # país actual

ARENA_CENTER  = np.array([WIDTH / 2.0, 1100.0])
ARENA_RADIUS  = 430

BALL_INITIAL_RADIUS    = 22
BALL_GROWTH_PER_BOUNCE = 0.16   # +16% radio por rebote de pared
MAX_BALL_R    = 150
BALL_SPEED0   = 520.0
ACCEL_RATE    = 0.08
MAX_SPEED     = 2000.0

# 3 spikes equiespaciados; gap entre spike[1] y spike[2], centrado en 90° (abajo)
# Ángulos en grados desde eje +X (y hacia abajo en pantalla)
SPIKE_ANGLES_DEG = [-90, 30, 150]
SPIKE_ANGLES     = [math.radians(a) for a in SPIKE_ANGLES_DEG]

GAP_ANGLE_DEGREES = 15
GAP_CENTER_DEG    = 90                              # 6 en punto (abajo)
GAP_CENTER_RAD    = math.radians(GAP_CENTER_DEG)
GAP_HALF          = math.radians(GAP_ANGLE_DEGREES / 2)

SPIKE_LENGTH = 90    # px desde la pared hacia el centro
SPIKE_WIDTH  = 100   # px de arco de base
SPIKE_OMEGA  = 2 * math.pi / (FPS * 10)  # 1 vuelta cada 10 s

GRAVITY   = 260.0
PART_DAMP = 0.993
N_PARTICLES = 28

GLOW_LAYERS    = 14
GLOW_MAX_ALPHA = 110
FADE_DURATION  = 0.4   # segundos para fade del subtítulo

COLOR_BG    = (0, 0, 0)
COLOR_ARENA = (210, 210, 210)

MAX_TOTAL_FRAMES = FPS * 150   # tope de seguridad: 2.5 min


# ════════════════════════════════════════════════════════════════════════════
# PAÍSES
# ════════════════════════════════════════════════════════════════════════════

COUNTRIES_ORDER = [
    "Argentina", "France", "Spain", "Brazil", "England",
    "Germany", "Portugal", "Netherlands",
    "Croatia", "Belgium", "Italy", "Uruguay",
    "Colombia", "Morocco", "Japan", "USA",
]

COUNTRIES_COLORS = {
    "Argentina":   (108, 174, 222),
    "France":      (0,   85,  164),
    "Spain":       (198,  11,   30),
    "Brazil":      (0,  156,   59),
    "England":     (200,  16,   46),
    "Germany":     (255, 206,    0),
    "Portugal":    (220,  30,   30),
    "Netherlands": (255,  79,    0),
    "Croatia":     (220,  20,   20),
    "Belgium":     (230, 210,    0),
    "Italy":       (0,  146,   70),
    "Uruguay":     (114, 173,  217),
    "Colombia":    (252, 209,   22),
    "Morocco":     (193,  39,   45),
    "Japan":       (188,   0,   45),
    "USA":         (60,   59,  110),
}

FLAG_CODES = {
    "Argentina": "ar", "France":      "fr", "Spain":       "es",
    "Brazil":    "br", "England":     "gb", "Germany":     "de",
    "Portugal":  "pt", "Netherlands": "nl", "Croatia":     "hr",
    "Belgium":   "be", "Italy":       "it", "Uruguay":     "uy",
    "Colombia":  "co", "Morocco":     "ma", "Japan":       "jp",
    "USA":       "us",
}


FLAGS_DIR = os.path.join(os.path.dirname(__file__), "assets", "flags")


# ════════════════════════════════════════════════════════════════════════════
# BANDERAS
# ════════════════════════════════════════════════════════════════════════════

def ensure_flag(country: str) -> None:
    os.makedirs(FLAGS_DIR, exist_ok=True)
    path = os.path.join(FLAGS_DIR, f"{country}.png")
    if not os.path.exists(path):
        code = FLAG_CODES[country]
        url  = f"https://flagcdn.com/256x192/{code}.png"
        print(f"  Descargando: {country}  ({url})")
        try:
            urllib.request.urlretrieve(url, path)
        except Exception as e:
            print(f"  Error: {e}")


_flag_ball_cache: dict[tuple, pygame.Surface | None] = {}
_flag_sub_cache:  dict[str, pygame.Surface | None]   = {}


def get_flag_ball(country: str, diameter: int) -> pygame.Surface | None:
    """Bandera recortada en círculo, escalada a `diameter`×`diameter`."""
    key = (country, diameter)
    if key in _flag_ball_cache:
        return _flag_ball_cache[key]

    path = os.path.join(FLAGS_DIR, f"{country}.png")
    if not os.path.exists(path):
        _flag_ball_cache[key] = None
        return None
    try:
        raw    = pygame.image.load(path).convert_alpha()
        scaled = pygame.transform.smoothscale(raw, (diameter, diameter))
        mask   = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))
        pygame.draw.circle(mask, (255, 255, 255, 255),
                           (diameter // 2, diameter // 2), diameter // 2)
        result = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        result.blit(scaled, (0, 0))
        result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        _flag_ball_cache[key] = result
        return result
    except Exception:
        _flag_ball_cache[key] = None
        return None


def get_flag_sub(country: str, height: int = 36) -> pygame.Surface | None:
    """Bandera sin recortar, escalada a `height`px de alto, para el subtítulo."""
    key = country
    if key in _flag_sub_cache:
        return _flag_sub_cache[key]

    path = os.path.join(FLAGS_DIR, f"{country}.png")
    if not os.path.exists(path):
        _flag_sub_cache[key] = None
        return None
    try:
        raw  = pygame.image.load(path).convert_alpha()
        w    = int(raw.get_width() * height / raw.get_height())
        surf = pygame.transform.smoothscale(raw, (w, height))
        _flag_sub_cache[key] = surf
        return surf
    except Exception:
        _flag_sub_cache[key] = None
        return None


# ════════════════════════════════════════════════════════════════════════════
# GEOMETRÍA Y FÍSICA
# ════════════════════════════════════════════════════════════════════════════

def spike_pts(angle: float):
    half_arc = math.asin(min(0.999, (SPIKE_WIDTH / 2) / ARENA_RADIUS))
    tip = ARENA_CENTER + np.array([math.cos(angle), math.sin(angle)]) * (ARENA_RADIUS - SPIKE_LENGTH)
    bl  = ARENA_CENTER + np.array([math.cos(angle - half_arc), math.sin(angle - half_arc)]) * ARENA_RADIUS
    br  = ARENA_CENTER + np.array([math.cos(angle + half_arc), math.sin(angle + half_arc)]) * ARENA_RADIUS
    return tip, bl, br


def spike_hit(pos: np.ndarray, r: float, angle: float) -> bool:
    tip, bl, br = spike_pts(angle)
    return min(
        pt_seg_dist(pos, tip, bl),
        pt_seg_dist(pos, tip, br),
        pt_seg_dist(pos, bl, br),
    ) < r + 4


def gap_angle_norm(angle: float, gap_half: float) -> float:
    """Diferencia angular normalizada respecto al centro del gap [-π, π]."""
    return (angle - GAP_CENTER_RAD + math.pi) % (2 * math.pi) - math.pi


# ════════════════════════════════════════════════════════════════════════════
# PARTÍCULAS
# ════════════════════════════════════════════════════════════════════════════

class Particle:
    __slots__ = ('pos', 'vel', 'color', 'alpha', 'r')

    def __init__(self, pos, vel, color, r):
        self.pos   = pos.astype(float)
        self.vel   = vel.astype(float)
        self.color = color
        self.alpha = 255.0
        self.r     = r

    def step(self, dt: float):
        self.vel[1] += GRAVITY * dt
        self.vel    *= PART_DAMP
        self.pos    += self.vel * dt
        delta = self.pos - ARENA_CENTER
        d = np.linalg.norm(delta)
        if d + self.r >= ARENA_RADIUS:
            n = delta / d
            if np.dot(self.vel, n) > 0:
                self.vel -= 2 * np.dot(self.vel, n) * n
            self.pos = ARENA_CENTER + n * (ARENA_RADIUS - self.r - 1)

    def draw(self, surf: pygame.Surface):
        a = int(max(0.0, self.alpha))
        if a <= 0:
            return
        ix, iy = int(self.pos[0]), int(self.pos[1])
        ps = part_surf(self.r, self.color)
        if a >= 255:
            surf.blit(ps, ps.get_rect(center=(ix, iy)))
        else:
            tmp = ps.copy()
            tmp.set_alpha(a)
            surf.blit(tmp, ps.get_rect(center=(ix, iy)))


def spawn_explosion(pos: np.ndarray, color: tuple, ball_r: int) -> list:
    t      = (ball_r - BALL_INITIAL_RADIUS) / max(1, MAX_BALL_R - BALL_INITIAL_RADIUS)
    part_r = max(7, min(24, int(7 + 17 * t)))
    parts  = []
    for _ in range(N_PARTICLES):
        ang = random.uniform(0, 2 * math.pi)
        spd = random.uniform(120, 620)
        vel = np.array([math.cos(ang), math.sin(ang)]) * spd
        col = tuple(min(255, max(0, color[i] + random.randint(-30, 30))) for i in range(3))
        parts.append(Particle(pos.copy(), vel, col, part_r))
    return parts


def collide_particles(particles: list):
    n = len(particles)
    for i in range(n):
        pi  = particles[i]
        pxi = float(pi.pos[0]); pyi = float(pi.pos[1])
        ri  = float(pi.r)
        for j in range(i + 1, n):
            pj    = particles[j]
            dx    = float(pj.pos[0]) - pxi
            dy    = float(pj.pos[1]) - pyi
            min_d = ri + float(pj.r)
            d2    = dx * dx + dy * dy
            if d2 < min_d * min_d and d2 > 0.01:
                d   = d2 ** 0.5
                nx  = dx / d; ny = dy / d
                sep = (min_d - d) * 0.5 + 0.5
                pi.pos[0] -= nx * sep; pi.pos[1] -= ny * sep
                pj.pos[0] += nx * sep; pj.pos[1] += ny * sep
                pxi = float(pi.pos[0]); pyi = float(pi.pos[1])
                rel = ((float(pi.vel[0]) - float(pj.vel[0])) * nx
                     + (float(pi.vel[1]) - float(pj.vel[1])) * ny)
                if rel > 0:
                    imp = rel * 0.20
                    pi.vel[0] -= imp * nx; pi.vel[1] -= imp * ny
                    pj.vel[0] += imp * nx; pj.vel[1] += imp * ny


def bounce_particles_on_spike(particles: list, spike_angle: float):
    """Partículas rebotan en el pico. Usa spike_pts local (ARENA_CENTER/RADIUS correctos)."""
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

def gen_bong(freq: float = 300.0, dur: float = 0.50) -> np.ndarray:
    """Bong metálico: parciales inarmónicas tipo campana, ataque punch, decay largo."""
    n   = int(SAMPLE_RATE * dur)
    t   = np.linspace(0, dur, n, endpoint=False)
    atk = np.minimum(t / 0.004, 1.0)   # 4 ms — muy punch
    dec = np.exp(-4.5 * t)
    # Parciales inarmónicas (timbre de metal percutido)
    s = (np.sin(2*np.pi * freq * 1.000 * t) * 0.50
       + np.sin(2*np.pi * freq * 2.756 * t) * 0.28
       + np.sin(2*np.pi * freq * 5.404 * t) * 0.14
       + np.sin(2*np.pi * freq * 3.500 * t) * 0.12
       + np.sin(2*np.pi * freq * 8.933 * t) * 0.06)
    # Transiente de golpe (snap): ruido brevísimo al inicio
    snap_n = int(SAMPLE_RATE * 0.005)
    snap   = np.random.default_rng(7).standard_normal(snap_n)
    snap  *= np.exp(-np.arange(snap_n) / snap_n * 12) * 0.35
    s[:snap_n] += snap
    return (s * atk * dec * 0.72 * 32767).astype(np.int16)


def gen_sad_whoosh(dur: float = 0.55) -> np.ndarray:
    n     = int(SAMPLE_RATE * dur)
    t     = np.linspace(0, dur, n, endpoint=False)
    freq  = 620 * np.exp(-t * 6) + 110
    phase = np.cumsum(freq / SAMPLE_RATE) * 2 * math.pi
    env   = np.exp(-t * 4.5)
    s     = 0.50 * np.sin(phase) * env + 0.15 * np.sin(phase * 2) * env
    n_wh  = int(n * 0.30)
    s[:n_wh] += (np.random.randn(n_wh)
                 * 0.07
                 * np.exp(-np.linspace(0, 1, n_wh) * 7))
    return (s * 0.70 * 32767).astype(np.int16)


def gen_fanfare(dur: float = 2.2) -> np.ndarray:
    n   = int(SAMPLE_RATE * dur)
    t   = np.linspace(0, dur, n, endpoint=False)
    buf = np.zeros(n)
    # Acorde mayor ascendente C5-E5-G5-C6 con retardos
    for freq, delay in [(523.25, 0.00), (659.25, 0.13),
                        (783.99, 0.26), (1046.50, 0.42)]:
        d0 = int(delay * SAMPLE_RATE)
        tt = t[d0:]
        nd = len(tt)
        atk = np.minimum(tt / 0.015, 1.0)
        dec = np.exp(-2.2 * tt)
        s   = (0.50 * np.sin(2 * math.pi * freq * tt)
             + 0.20 * np.sin(2 * math.pi * freq * 2.001 * tt)
             + 0.10 * np.sin(2 * math.pi * freq * 3.002 * tt))
        buf[d0:d0 + nd] += s * atk * dec * 0.65
    peak = np.max(np.abs(buf))
    if peak > 0:
        buf /= peak * 1.05
    return (buf * 0.85 * 32767).astype(np.int16)


def mix_audio(events: list, total_frames: int) -> np.ndarray:
    total_samples = int(total_frames / FPS * SAMPLE_RATE) + SAMPLE_RATE
    buf = np.zeros(total_samples, dtype=np.float64)
    for fn, stype, param in events:
        pos = int(fn * SAMPLE_RATE / FPS)
        if stype == 'bong':
            snd = gen_bong(param if param else 300.0).astype(np.float64)
        elif stype == 'explosion':
            snd = gen_explosion().astype(np.float64)
        elif stype == 'sad':
            snd = gen_sad_whoosh().astype(np.float64)
        elif stype == 'fanfare':
            snd = gen_fanfare().astype(np.float64)
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

def make_arena_layer() -> pygame.Surface:
    """Layer estático: solo el glow difuso de la circunferencia."""
    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy = int(ARENA_CENTER[0]), int(ARENA_CENTER[1])
    for i in range(4, 0, -1):
        pygame.draw.circle(layer, (*COLOR_ARENA, 7),
                           (cx, cy), ARENA_RADIUS + i * 3, 6)
    return layer


def draw_rotating_arena(surf: pygame.Surface, rotation: float):
    """Arco RGB girado `rotation` radianes, sin gap markers."""
    cx, cy     = int(ARENA_CENTER[0]), int(ARENA_CENTER[1])
    gap_center = GAP_CENTER_RAD + rotation
    gap_end_a  = gap_center + GAP_HALF
    arc_span   = 2 * math.pi - 2 * GAP_HALF
    n_pts      = 300

    # Color RGB que avanza con la rotación (hue = posición angular)
    hue_base = (rotation / (2 * math.pi)) % 1.0

    pts = []
    for i in range(n_pts + 1):
        a   = gap_end_a + arc_span * i / n_pts
        hue = (hue_base + i / n_pts * 0.6) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        color = (int(r * 255), int(g * 255), int(b * 255))
        x = int(cx + math.cos(a) * ARENA_RADIUS)
        y = int(cy + math.sin(a) * ARENA_RADIUS)
        pts.append(((x, y), color))

    # Dibujar segmento a segmento para gradiente RGB
    for i in range(len(pts) - 1):
        pygame.draw.line(surf, pts[i][1], pts[i][0], pts[i + 1][0], 5)


def draw_spikes(surf: pygame.Surface, rotation: float):
    COLOR_SPIKE = (155, 155, 160)
    for angle in SPIKE_ANGLES:
        tip, bl, br = spike_pts(angle + rotation)
        pts = [(int(p[0]), int(p[1])) for p in (tip, bl, br)]
        pygame.draw.polygon(surf, COLOR_SPIKE, pts)
        pygame.draw.polygon(surf, (205, 205, 210), pts, 2)


def draw_ball(surf: pygame.Surface, country: str,
              pos: np.ndarray, r: int):
    glow_col = COUNTRIES_COLORS[country]
    # Glow exterior aditivo (fuera de la bandera)
    draw_glow(surf, (int(pos[0]), int(pos[1])), r, glow_col,
              layers=GLOW_LAYERS, max_alpha=GLOW_MAX_ALPHA)
    # Bandera circular centrada
    flag = get_flag_ball(country, r * 2)
    if flag:
        surf.blit(flag, flag.get_rect(center=(int(pos[0]), int(pos[1]))))
    else:
        pygame.draw.circle(surf, glow_col, (int(pos[0]), int(pos[1])), r)


def draw_header(surf: pygame.Surface,
                font_big: pygame.font.Font,
                font_sub: pygame.font.Font):
    t1 = font_sub.render("Who will win the", True, (200, 200, 200))
    t2 = font_big.render("World Cup?", True, (255, 215, 0))
    surf.blit(t1, t1.get_rect(centerx=WIDTH // 2, centery=HEADER_Y1))
    surf.blit(t2, t2.get_rect(centerx=WIDTH // 2, centery=HEADER_Y2))


def draw_subtitle(surf: pygame.Surface, font_med: pygame.font.Font,
                  country: str, alpha: int):
    if alpha <= 0 or not country:
        return
    flag_s = get_flag_sub(country, height=38)
    txt    = font_med.render(country, True, (230, 230, 230))

    gap    = 14
    flag_w = flag_s.get_width() + gap if flag_s else 0
    total_w = flag_w + txt.get_width()
    h      = max(txt.get_height(), 38) + 4
    tmp    = pygame.Surface((total_w, h), pygame.SRCALPHA)

    if flag_s:
        tmp.blit(flag_s, (0, (h - flag_s.get_height()) // 2))
    tmp.blit(txt, (flag_w, (h - txt.get_height()) // 2))
    tmp.set_alpha(alpha)
    surf.blit(tmp, tmp.get_rect(centerx=WIDTH // 2, centery=SUBTITLE_Y))


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true",
                        help="Graba MP4 offline en shorts/output/")
    args = parser.parse_args()

    print("Verificando banderas...")
    for c in COUNTRIES_ORDER:
        ensure_flag(c)

    pygame.init()
    pygame.font.init()

    font_big = pygame.font.SysFont("Arial", 78, bold=True)
    font_med = pygame.font.SysFont("Arial", 54, bold=True)
    font_sub = pygame.font.SysFont("Arial", 52)

    scale  = 0.22 if args.record else 0.36
    screen = pygame.display.set_mode((int(WIDTH * scale), int(HEIGHT * scale)))
    pygame.display.set_caption(
        "World Cup Winner — grabando..." if args.record else "World Cup Winner")
    surface = pygame.Surface((WIDTH, HEIGHT))

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir  = os.path.join(base_dir, "output")
    os.makedirs(out_dir, exist_ok=True)

    # Configurar recorder de video
    temp_vid = os.path.join(out_dir, "_wc_tmp.mp4")
    temp_wav = os.path.join(out_dir, "_wc_tmp.wav")
    out_mp4  = os.path.join(out_dir, "world_cup_winner.mp4")

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

    # Capa estática
    arena_layer = make_arena_layer()

    # Estado de la simulación
    sound_events:  list = []
    all_particles: list = []
    frame          = 0
    running        = True
    winner:        str | None = None
    rotation_angle = 0.0

    country_queue = list(COUNTRIES_ORDER)
    country_idx   = 0

    def pop_country() -> str | None:
        nonlocal country_idx
        if country_idx >= len(country_queue):
            return None
        c = country_queue[country_idx]
        country_idx += 1
        return c

    # Estado del subtítulo
    current_country  = pop_country()
    subtitle_alpha   = 0
    subtitle_target  = 255   # fade in al inicio

    FADE_FRAMES    = max(1, int(FADE_DURATION * FPS))
    DYING_FRAMES   = FPS // 2
    WINNER_FRAMES  = int(FPS * 3.5)

    state    = 'playing'   # 'playing' | 'dying' | 'winner'
    timer    = 0
    note_idx = 0           # sube el pitch del silbato con cada rebote

    def init_ball():
        ang   = random.uniform(0, 2 * math.pi)
        spd   = random.uniform(380, BALL_SPEED0)
        vel   = np.array([math.cos(ang), math.sin(ang)]) * spd
        ox    = random.uniform(-50, 50)
        oy    = random.uniform(-60, 60)
        pos   = ARENA_CENTER + np.array([ox, oy])
        return pos.copy(), vel.copy(), BALL_INITIAL_RADIUS

    ball_pos, ball_vel, ball_r = init_ball()
    alive = True

    clock = pygame.time.Clock()

    while running and frame < MAX_TOTAL_FRAMES:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        dt = 1.0 / FPS
        rotation_angle += SPIKE_OMEGA

        # ── Fade subtítulo ────────────────────────────────────────────────
        step = 255 // FADE_FRAMES + 1
        if subtitle_alpha < subtitle_target:
            subtitle_alpha = min(subtitle_target, subtitle_alpha + step)
        elif subtitle_alpha > subtitle_target:
            subtitle_alpha = max(subtitle_target, subtitle_alpha - step)

        # ── Gap dinámico: aumentar levemente si el video pasa de 50s ─────
        elapsed = frame / FPS
        if elapsed > 50:
            extra = min(1.0, (elapsed - 50) / 40)   # 0→1 en los 40s siguientes
            cur_gap_half = GAP_HALF * (1 + 0.8 * extra)
        else:
            cur_gap_half = GAP_HALF

        # ── Lógica ────────────────────────────────────────────────────────
        if state == 'playing':
            ball_pos += ball_vel * dt

            # Verificar spikes (con rotación)
            hit_spike = any(spike_hit(ball_pos, ball_r, sa + rotation_angle) for sa in SPIKE_ANGLES)

            if hit_spike:
                all_particles.extend(
                    spawn_explosion(ball_pos, COUNTRIES_COLORS[current_country], ball_r))
                sound_events.append((frame, 'explosion', None))
                sound_events.append((frame + FPS // 4, 'sad', None))
                alive  = False
                state  = 'dying'
                timer  = DYING_FRAMES
                subtitle_target = 0

            else:
                delta = ball_pos - ARENA_CENTER
                d     = np.linalg.norm(delta)
                if d + ball_r >= ARENA_RADIUS:
                    n_vec = delta / d if d > 1e-6 else np.array([0., 1.])
                    angle            = math.atan2(float(delta[1]), float(delta[0]))
                    rotated_gap_ctr  = GAP_CENTER_RAD + rotation_angle
                    diff             = (angle - rotated_gap_ctr + math.pi) % (2 * math.pi) - math.pi

                    if abs(diff) <= cur_gap_half:
                        # ¡Escapó por el gap!
                        winner = current_country
                        state  = 'winner'
                        timer  = WINNER_FRAMES
                        sound_events.append((frame, 'fanfare', None))
                        # Limpiar partículas acumuladas, solo confetti del ganador
                        all_particles.clear()
                        all_particles.extend(
                            spawn_explosion(ball_pos,
                                            COUNTRIES_COLORS[winner],
                                            ball_r))
                        for _ in range(3):
                            all_particles.extend(
                                spawn_explosion(
                                    ARENA_CENTER + np.array([
                                        random.uniform(-80, 80),
                                        random.uniform(-80, 80),
                                    ]),
                                    COUNTRIES_COLORS[winner],
                                    ball_r,
                                ))
                    else:
                        # Pared sólida — rebote + crecimiento
                        if np.dot(ball_vel, n_vec) > 0:
                            ball_vel = ball_vel - 2 * np.dot(ball_vel, n_vec) * n_vec
                        ball_pos = ARENA_CENTER + n_vec * (ARENA_RADIUS - ball_r - 1.5)
                        ball_r   = min(int(ball_r * (1 + BALL_GROWTH_PER_BOUNCE)), MAX_BALL_R)
                        spd      = np.linalg.norm(ball_vel)
                        ball_vel = ball_vel / spd * min(spd * (1 + ACCEL_RATE), MAX_SPEED)
                        # Cicla por pentatónica grave: C D E G A
                        _PENTA = [130.81, 146.83, 164.81, 196.00, 220.00]
                        pitch  = _PENTA[note_idx % len(_PENTA)]
                        sound_events.append((frame, 'bong', pitch))
                        note_idx += 1

        elif state == 'dying':
            timer -= 1
            if timer <= 0:
                current_country = pop_country()
                if current_country is None:
                    running = False
                else:
                    ball_pos, ball_vel, ball_r = init_ball()
                    alive   = True
                    state   = 'playing'
                    subtitle_alpha  = 0
                    subtitle_target = 255

        elif state == 'winner':
            timer -= 1
            if timer <= 0:
                running = False

        # ── Partículas ────────────────────────────────────────────────────
        for p in all_particles:
            p.step(dt)
        if all_particles:
            for _ in range(3):
                for sa in SPIKE_ANGLES:
                    bounce_particles_on_spike(all_particles, sa + rotation_angle)
                collide_particles(all_particles)
            if alive:
                push_particles_from_ball(all_particles, ball_pos, ball_r, ball_vel)

        # ── Dibujo ────────────────────────────────────────────────────────
        surface.fill(COLOR_BG)

        if state == 'winner' and winner:
            _draw_winner_screen(surface, winner, timer, WINNER_FRAMES,
                                all_particles, font_big, font_med)
        else:
            # Escena normal
            surface.blit(arena_layer, (0, 0))
            draw_rotating_arena(surface, rotation_angle)
            draw_spikes(surface, rotation_angle)

            for p in all_particles:
                p.draw(surface)

            if alive and current_country:
                draw_ball(surface, current_country, ball_pos, ball_r)

            draw_header(surface, font_big, font_sub)
            if current_country:
                draw_subtitle(surface, font_med, current_country, subtitle_alpha)

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
    total_frames = frame
    print(f"\nVideo: {total_frames} frames ({total_frames / FPS:.1f}s)")
    print("Sintetizando audio...")

    pcm = mix_audio(sound_events, total_frames)
    with wave.open(temp_wav, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([
        ffmpeg_exe, '-y',
        '-i', temp_vid,
        '-i', temp_wav,
        '-c:v', 'copy',
        '-c:a', 'aac', '-b:a', '192k',
        '-shortest',
        out_mp4,
    ], check=True, stderr=subprocess.DEVNULL)

    for f in (temp_vid, temp_wav):
        if os.path.exists(f):
            os.remove(f)

    print(f"MP4 listo → {out_mp4}")


def _draw_winner_screen(surf: pygame.Surface, winner: str,
                        timer: int, total_timer: int,
                        particles: list,
                        font_big: pygame.font.Font,
                        font_med: pygame.font.Font):
    progress = 1.0 - timer / total_timer
    glow_col = COUNTRIES_COLORS[winner]

    # Glow explosivo de fondo
    draw_glow(surf, (WIDTH // 2, HEIGHT // 2), 350, glow_col,
              layers=20, max_alpha=min(200, int(progress * 240)))

    # Partículas de confetti
    for p in particles:
        p.draw(surf)

    # Bola ganadora grande en el centro
    win_r = min(MAX_BALL_R + 20, 170)
    ball_center = np.array([WIDTH / 2.0, HEIGHT / 2.0 + 80.0])
    draw_glow(surf, (int(ball_center[0]), int(ball_center[1])),
              win_r, glow_col, layers=18, max_alpha=160)
    flag = get_flag_ball(winner, win_r * 2)
    if flag:
        surf.blit(flag, flag.get_rect(
            center=(int(ball_center[0]), int(ball_center[1]))))
    else:
        pygame.draw.circle(surf, glow_col,
                           (int(ball_center[0]), int(ball_center[1])), win_r)

    alpha_txt = min(255, int(progress * 3.5 * 255))

    # "WINNER"
    w_surf = font_big.render("WINNER", True, (255, 215, 0))
    w_surf.set_alpha(alpha_txt)
    surf.blit(w_surf, w_surf.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 - 260))

    # Nombre del país
    n_surf = font_med.render(winner, True, (255, 255, 255))
    n_surf.set_alpha(alpha_txt)
    surf.blit(n_surf, n_surf.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 + 360))


if __name__ == "__main__":
    main()
