"""
World Cup R32 2026 — Battle Royale
32 bolas-bandera simultáneas; última en pie gana.
NO sobreescribe world_cup_winner.py.

Uso:
    python shorts/world_cup_winner_r32.py            # preview
    python shorts/world_cup_winner_r32.py --record   # graba MP4
    Poner SEED_SEARCH = True para buscar seeds sin render.
"""

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN — editar solo este bloque
# ══════════════════════════════════════════════════════════════════════════════

SEED_SEARCH = False

WINNER_TAGLINE: str | None = "NEVER LOST A MATCH"

TEAMS_R32 = [
    # 28 clasificados confirmados al 27 jun 2026
    "USA", "MEX", "CAN", "ARG", "BRA", "COL", "URU", "ECU",
    "PAR", "ESP", "POR", "FRA", "GER", "NED", "BEL", "CRO",
    "ENG", "NOR", "SUI", "AUT", "ALG", "MAR", "EGY", "GHA",
    "SEN", "CPV", "JPN", "KOR",
    # 4 cupos pendientes — COMPLETAR antes de correr
    "TBD_01", "TBD_02", "TBD_03", "TBD_04",   # ← REEMPLAZAR
]

RANDOM_SEED   = 42      # int → fijo | None → distinto cada vez
DURATION_S    = 18      # objetivo 12-20 s
RENDER_FPS    = 60
BG_COLOR      = (0,   0,   0)
ARENA_COLOR   = (210, 210, 210)
OVERLAY_COLOR = (255, 255, 255)

# ══════════════════════════════════════════════════════════════════════════════

import os, sys, math, wave, random, argparse, subprocess, importlib.util
from collections import defaultdict

import pygame
import numpy as np
import imageio_ffmpeg

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine.effects import draw_glow

# ── Reutilizar world_cup_winner.py ────────────────────────────────────────────
_WCW_PATH = os.path.join(os.path.dirname(__file__), "world_cup_winner.py")
_spec = importlib.util.spec_from_file_location("_wcw", _WCW_PATH)
_wcw  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wcw)

ensure_flag              = _wcw.ensure_flag
get_flag_ball            = _wcw.get_flag_ball
get_flag_sub             = _wcw.get_flag_sub
Particle                 = _wcw.Particle
spawn_explosion          = _wcw.spawn_explosion   # usado solo en winner screen
collide_particles        = _wcw.collide_particles
push_particles_from_ball = _wcw.push_particles_from_ball
gen_bong                 = _wcw.gen_bong
gen_sad_whoosh           = _wcw.gen_sad_whoosh
gen_fanfare              = _wcw.gen_fanfare
gen_explosion            = _wcw.gen_explosion
pt_seg_dist              = _wcw.pt_seg_dist
FLAGS_DIR                = _wcw.FLAGS_DIR

# ── Datos de equipos ──────────────────────────────────────────────────────────
COUNTRIES_COLORS = dict(_wcw.COUNTRIES_COLORS)
FLAG_CODES       = dict(_wcw.FLAG_CODES)

_EXTRA = {
    "Mexico":       ("mx", (0,  130,  80)),
    "Canada":       ("ca", (220,   0,   0)),
    "Switzerland":  ("ch", (220,  20,  20)),
    "Ecuador":      ("ec", (0,  160,  50)),
    "Paraguay":     ("py", (0,   85, 175)),
    "South Korea":  ("kr", (205,   0,  50)),
    "Australia":    ("au", (0,   50, 160)),
    "Ivory Coast":  ("ci", (255, 130,   0)),
    "South Africa": ("za", (0,  120,  80)),
}
for _n, (_c, _col) in _EXTRA.items():
    FLAG_CODES[_n]       = _c
    COUNTRIES_COLORS[_n] = _col

_wcw.FLAG_CODES       = FLAG_CODES
_wcw.COUNTRIES_COLORS = COUNTRIES_COLORS

TEAM_TO_COUNTRY = {
    "USA": "USA",          "MEX": "Mexico",       "CAN": "Canada",
    "ARG": "Argentina",    "BRA": "Brazil",        "COL": "Colombia",
    "URU": "Uruguay",      "ECU": "Ecuador",       "PAR": "Paraguay",
    "ESP": "Spain",        "POR": "Portugal",      "FRA": "France",
    "GER": "Germany",      "NED": "Netherlands",   "BEL": "Belgium",
    "CRO": "Croatia",      "ENG": "England",       "NOR": "Norway",
    "SUI": "Switzerland",  "AUT": "Austria",       "ALG": "Algeria",
    "MAR": "Morocco",      "EGY": "Egypt",         "GHA": "Ghana",
    "SEN": "Senegal",      "CPV": "Cape Verde",    "JPN": "Japan",
    "KOR": "South Korea",  "AUS": "Australia",     "CIV": "Ivory Coast",
    "RSA": "South Africa",
}

COUNTRY_TO_ISO = {v: k for k, v in TEAM_TO_COUNTRY.items()}

BET365_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "assets", "bet-365-goal-sound.mp3")
BUBBLE_POP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "assets", "bubble-pop.mp3")

# ── Constantes físicas ────────────────────────────────────────────────────────
WIDTH, HEIGHT    = 1080, 1920
FPS              = RENDER_FPS
SAMPLE_RATE      = 44100
ARENA_CENTER     = np.array([WIDTH / 2.0, 1100.0])
ARENA_RADIUS     = 430
BALL_R0          = 13
BALL_GROWTH      = 0.22
MAX_BALL_R       = 120
BALL_SPEED0      = 450.0
ACCEL_RATE       = 0.07
MAX_SPEED        = 1800.0
SPIKE_ANGLES_DEG = [0, 120, 240]
SPIKE_ANGLES     = [math.radians(a) for a in SPIKE_ANGLES_DEG]
SPIKE_OMEGA      = 2 * math.pi / (FPS * 8)   # rad/frame (original)
SPIKE_LENGTH     = 95
SPIKE_WIDTH      = 120
GRAVITY          = 260.0
PART_DAMP        = 0.993
N_PARTICLES      = 16
INTRO_FRAMES     = int(FPS * 1.5)
WINNER_FRAMES    = int(FPS * 2.0)
MAX_FRAMES       = int(FPS * (DURATION_S + 10))

# Propagar a _wcw (Particle.step, spawn_explosion usan sus module globals)
_wcw.GRAVITY             = GRAVITY
_wcw.PART_DAMP           = PART_DAMP
_wcw.ARENA_CENTER        = ARENA_CENTER
_wcw.ARENA_RADIUS        = ARENA_RADIUS
_wcw.N_PARTICLES         = N_PARTICLES
_wcw.BALL_INITIAL_RADIUS = BALL_R0
_wcw.MAX_BALL_R          = MAX_BALL_R
_wcw.SPIKE_LENGTH        = SPIKE_LENGTH
_wcw.SPIKE_WIDTH         = SPIKE_WIDTH

# ══════════════════════════════════════════════════════════════════════════════
# GEOMETRÍA Y FÍSICA  (idéntico al original pre-chat)
# ══════════════════════════════════════════════════════════════════════════════

def spike_pts(angle):
    half_arc = math.asin(min(0.999, (SPIKE_WIDTH / 2) / ARENA_RADIUS))
    tip = ARENA_CENTER + np.array([math.cos(angle), math.sin(angle)]) * (ARENA_RADIUS - SPIKE_LENGTH)
    bl  = ARENA_CENTER + np.array([math.cos(angle - half_arc), math.sin(angle - half_arc)]) * ARENA_RADIUS
    br  = ARENA_CENTER + np.array([math.cos(angle + half_arc), math.sin(angle + half_arc)]) * ARENA_RADIUS
    return tip, bl, br


def spike_hit_and_dist(pos, r, angle):
    tip, bl, br = spike_pts(angle)
    d = min(pt_seg_dist(pos, tip, bl),
            pt_seg_dist(pos, tip, br),
            pt_seg_dist(pos, bl, br))
    return d < r + 4, d


def wall_bounce(pos, vel, r):
    delta = pos - ARENA_CENTER
    d = np.linalg.norm(delta)
    if d + r >= ARENA_RADIUS:
        n = delta / d if d > 1e-6 else np.array([0., -1.])
        if np.dot(vel, n) > 0:
            vel = vel - 2 * np.dot(vel, n) * n
        buf = r * BALL_GROWTH + 4.0
        pos = ARENA_CENTER + n * (ARENA_RADIUS - r - buf)
        return pos, vel, True
    return pos, vel, False


def bounce_particles_on_spike(particles, spike_angle):
    tip, bl, br = spike_pts(spike_angle)
    gcx = (float(tip[0]) + float(bl[0]) + float(br[0])) / 3.0
    gcy = (float(tip[1]) + float(bl[1]) + float(br[1])) / 3.0
    edges = [(tip, bl), (tip, br), (bl, br)]
    for p in particles:
        pr = float(p.r)
        for a, b in edges:
            abx = float(b[0]-a[0]); aby = float(b[1]-a[1])
            d2 = abx*abx + aby*aby
            if d2 < 1e-9: continue
            apx = float(p.pos[0]-a[0]); apy = float(p.pos[1]-a[1])
            t = max(0.0, min(1.0, (apx*abx+apy*aby)/d2))
            qx = float(a[0])+t*abx; qy = float(a[1])+t*aby
            dx = float(p.pos[0])-qx; dy = float(p.pos[1])-qy
            dist2 = dx*dx+dy*dy
            if dist2 < pr*pr and dist2 > 0.0001:
                dist = dist2**0.5
                nx = dx/dist; ny = dy/dist
                if nx*(gcx-qx)+ny*(gcy-qy) > 0:
                    nx=-nx; ny=-ny
                p.pos[0] += nx*(pr-dist+1.0)
                p.pos[1] += ny*(pr-dist+1.0)
                vn = float(p.vel[0])*nx+float(p.vel[1])*ny
                if vn < 0:
                    p.vel[0] -= 1.6*vn*nx
                    p.vel[1] -= 1.6*vn*ny


# ══════════════════════════════════════════════════════════════════════════════
# PARTÍCULA-BANDERA CIRCULAR  (círculo con flag image, física = Particle original)
# ══════════════════════════════════════════════════════════════════════════════

_PART_FADE_DUR = 0.8   # segundos de fade al final de vida

class FlagBallParticle:
    """Partícula circular con imagen de bandera. Física idéntica a Particle original."""
    __slots__ = ('pos', 'vel', 'r', 'age', 'lifetime', 'country', '_img')

    def __init__(self, pos, vel, r: float, country: str, lifetime: float):
        self.pos      = pos.astype(float)
        self.vel      = vel.astype(float)
        self.r        = float(r)
        self.age      = 0.0
        self.lifetime = lifetime
        self.country  = country
        diam          = max(2, int(r) * 2)
        self._img     = get_flag_ball(country, diam)   # círculo precacheado

    def step(self, dt: float):
        self.age     += dt
        self.vel[1]  += GRAVITY * dt
        self.vel     *= PART_DAMP
        self.pos     += self.vel * dt
        delta = self.pos - ARENA_CENTER
        d = np.linalg.norm(delta)
        if d + self.r >= ARENA_RADIUS:
            n = delta / d
            if np.dot(self.vel, n) > 0:
                self.vel -= 2 * np.dot(self.vel, n) * n
            self.pos = ARENA_CENTER + n * (ARENA_RADIUS - self.r - 1)

    def draw(self, surf: pygame.Surface):
        time_left = self.lifetime - self.age
        if time_left <= 0:
            return
        a = int(min(255.0, time_left / _PART_FADE_DUR * 255.0)) if time_left < _PART_FADE_DUR else 255
        ix, iy = int(self.pos[0]), int(self.pos[1])
        img = self._img
        if img is None:
            col = COUNTRIES_COLORS.get(self.country, (180, 180, 180))
            draw_glow(surf, (ix, iy), int(self.r), col, layers=6, max_alpha=a)
            return
        if a >= 255:
            surf.blit(img, img.get_rect(center=(ix, iy)))
        else:
            tmp = img.copy()
            tmp.fill((255, 255, 255, a), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(tmp, tmp.get_rect(center=(ix, iy)))


def _elim_lifetime(elim_count: int) -> float:
    """Duración de partículas según orden de eliminación (0-indexado)."""
    if elim_count < 10:
        return 2.5
    if elim_count < 25:
        return 3.5
    return 5.0


def spawn_flag_explosion(pos: np.ndarray, country: str, ball_r: int,
                         lifetime: float = 2.5) -> list:
    """Misma lógica de spawn que el original spawn_explosion, pero usa FlagBallParticle."""
    t      = (ball_r - BALL_R0) / max(1, MAX_BALL_R - BALL_R0)
    part_r = max(7, min(24, int(7 + 17 * t)))
    parts  = []
    for _ in range(N_PARTICLES):
        ang = random.uniform(0, 2 * math.pi)
        spd = random.uniform(120, 620)
        vel = np.array([math.cos(ang), math.sin(ang)]) * spd
        parts.append(FlagBallParticle(pos.copy(), vel, part_r, country, lifetime))
    return parts


# ══════════════════════════════════════════════════════════════════════════════
# AUDIO
# ══════════════════════════════════════════════════════════════════════════════

def gen_bubble_pop(dur: float = 0.10) -> np.ndarray:
    """Fallback sintético — solo si bubble-pop.mp3 no existe."""
    n    = int(SAMPLE_RATE * dur)
    t    = np.linspace(0, dur, n, endpoint=False)
    freq = 900 * np.exp(-t * 25) + 150
    phase = np.cumsum(freq / SAMPLE_RATE) * 2 * math.pi
    env  = np.exp(-t * 30) * np.minimum(t * 500, 1.0)
    s    = np.sin(phase) * env
    rng  = np.random.default_rng(99)
    s   += rng.standard_normal(n) * np.exp(-t * 100) * 0.08
    peak = np.max(np.abs(s))
    return (s / (peak + 1e-9) * 0.75 * 32767).astype(np.int16)


def gen_metal_hit(freq=440.0, dur=0.22) -> np.ndarray:
    """Golpe metálico con parciales inarmónicas para colisiones de pared."""
    n  = int(SAMPLE_RATE * dur)
    t  = np.linspace(0, dur, n, endpoint=False)
    s  = (np.sin(2*math.pi * freq       * t) * np.exp(-t * 18)
        + np.sin(2*math.pi * freq * 2.76 * t) * np.exp(-t * 26) * 0.55
        + np.sin(2*math.pi * freq * 5.40 * t) * np.exp(-t * 44) * 0.25
        + np.sin(2*math.pi * freq * 0.52 * t) * np.exp(-t * 12) * 0.38)
    click = np.random.default_rng(int(freq) & 0xFFFF).standard_normal(n) * np.exp(-t * 700) * 0.14
    s += click
    return (s / (np.max(np.abs(s)) + 1e-9) * 0.88 * 32767).astype(np.int16)


def gen_crunch(dur=0.18):
    n   = int(SAMPLE_RATE * dur)
    t   = np.linspace(0, dur, n, endpoint=False)
    env = np.exp(-t * 22)
    rng = np.random.default_rng(13)
    s   = (0.6 * rng.standard_normal(n) * env
         + 0.4 * np.sin(2 * math.pi * 80 * t) * env)
    return (s / (np.max(np.abs(s)) + 1e-9) * 0.85 * 32767).astype(np.int16)


def process_audio(raw_events, total_frames, bubble_pcm=None):
    CRUNCH_WIN = 18
    DUCK_WIN   = 12

    explosion_buckets = defaultdict(list)
    other_events      = []
    for fn, stype, param in raw_events:
        if stype == 'explosion':
            explosion_buckets[fn // CRUNCH_WIN].append(fn)
        else:
            other_events.append((fn, stype, param))

    processed = list(other_events)
    for bucket_fns in explosion_buckets.values():
        if len(bucket_fns) >= 3:
            mid = bucket_fns[len(bucket_fns) // 2]
            processed.append((mid, 'crunch', None))
        else:
            for fn in bucket_fns:
                processed.append((fn, 'explosion', None))

    processed.sort(key=lambda x: x[0])
    total_samples = int(total_frames / FPS * SAMPLE_RATE) + SAMPLE_RATE
    buf = np.zeros(total_samples, dtype=np.float64)
    last_fn = -9999

    for fn, stype, param in processed:
        pos  = int(fn * SAMPLE_RATE / FPS)
        duck = 0.5 if (fn - last_fn) < DUCK_WIN and stype != 'fanfare' else 1.0
        last_fn = fn
        if   stype == 'metal':     snd = gen_metal_hit(param or 440.0).astype(np.float64) * duck
        elif stype == 'bong':      snd = gen_bong(param or 300.0).astype(np.float64) * duck
        elif stype == 'explosion': snd = gen_explosion().astype(np.float64) * duck
        elif stype == 'crunch':    snd = gen_crunch().astype(np.float64) * duck
        elif stype == 'sad':       snd = gen_sad_whoosh().astype(np.float64) * duck
        elif stype == 'fanfare':   snd = gen_fanfare().astype(np.float64)
        elif stype == 'bubble':
            if bubble_pcm is not None:
                snd = bubble_pcm * duck
            else:
                snd = gen_bubble_pop().astype(np.float64) * duck
        else:
            continue
        end = min(pos + len(snd), total_samples)
        buf[pos:end] += snd[:end - pos]

    peak = np.max(np.abs(buf))
    if peak > 0:
        buf = buf / peak * 0.90 * 32767
    return buf.astype(np.int16)


def _load_mp3_pcm(path: str) -> np.ndarray:
    """Decodifica MP3 a PCM mono float64 normalizado via ffmpeg."""
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [ffmpeg_exe, '-i', path, '-f', 's16le', '-ar', str(SAMPLE_RATE), '-ac', '1', '-'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode != 0 or not result.stdout:
        return np.zeros(0, dtype=np.float64)
    pcm  = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float64)
    peak = np.max(np.abs(pcm))
    if peak > 0:
        pcm = pcm / peak * 0.85 * 32767
    return pcm


# ══════════════════════════════════════════════════════════════════════════════
# DIBUJO
# ══════════════════════════════════════════════════════════════════════════════

def make_arena_glow():
    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy = int(ARENA_CENTER[0]), int(ARENA_CENTER[1])
    r, g, b = ARENA_COLOR
    for i in range(4, 0, -1):
        pygame.draw.circle(layer, (r, g, b, 7), (cx, cy), ARENA_RADIUS + i * 3, 6)
    return layer


def draw_arena(surf, arena_glow, rotation):
    surf.blit(arena_glow, (0, 0))
    pygame.draw.circle(surf, ARENA_COLOR,
                       (int(ARENA_CENTER[0]), int(ARENA_CENTER[1])),
                       ARENA_RADIUS, 4)
    COLOR_SPIKE = (155, 155, 160)
    for angle in SPIKE_ANGLES:
        tip, bl, br = spike_pts(angle + rotation)
        pts = [(int(p[0]), int(p[1])) for p in (tip, bl, br)]
        pygame.draw.polygon(surf, COLOR_SPIKE, pts)
        pygame.draw.polygon(surf, (205, 205, 210), pts, 2)


def draw_ball_br(surf, country, pos, r, near_miss_t):
    """near_miss_t: segundos restantes del glow blanco [0, 0.4]."""
    col = COUNTRIES_COLORS.get(country, (180, 180, 180))
    if near_miss_t > 0:
        intensity = near_miss_t / 0.4
        draw_glow(surf, (int(pos[0]), int(pos[1])), int(r) + 12,
                  (255, 255, 255), layers=12, max_alpha=int(intensity * 220))
    draw_glow(surf, (int(pos[0]), int(pos[1])), int(r), col, layers=10, max_alpha=90)
    flag = get_flag_ball(country, int(r) * 2)
    if flag:
        surf.blit(flag, flag.get_rect(center=(int(pos[0]), int(pos[1]))))
    else:
        pygame.draw.circle(surf, col, (int(pos[0]), int(pos[1])), max(1, int(r)))


def draw_iso_label(surf, font_iso, country, pos, r, alpha=229):
    if alpha <= 0:
        return
    iso = COUNTRY_TO_ISO.get(country, country[:3].upper())
    txt = font_iso.render(iso, True, (255, 255, 255))
    txt.set_alpha(max(0, min(255, int(alpha))))
    surf.blit(txt, txt.get_rect(centerx=int(pos[0]),
                                centery=int(pos[1]) - int(r * 1.2) - 14))


def draw_intro_grid(surf, teams_countries, font_xs, alpha):
    COLS, ROWS = 4, 8
    CELL_W = WIDTH // COLS
    CELL_H = 158
    GRID_TOP = (HEIGHT - ROWS * CELL_H) // 2
    FLAG_H = 82

    overlay = pygame.Surface((WIDTH, ROWS * CELL_H), pygame.SRCALPHA)
    for idx, (code, country) in enumerate(teams_countries):
        col_i = idx % COLS
        row_i = idx // COLS
        cx = col_i * CELL_W + CELL_W // 2
        cy = row_i * CELL_H + CELL_H // 2

        flag = get_flag_sub(country, height=FLAG_H)
        if flag:
            overlay.blit(flag, flag.get_rect(centerx=cx, centery=cy - 12))
        else:
            pygame.draw.rect(overlay, (60, 60, 60),
                             (cx - 55, cy - 12 - FLAG_H//2, 110, FLAG_H), 2)

        label = font_xs.render(code[:6], True, (220, 220, 220))
        overlay.blit(label, label.get_rect(centerx=cx, centery=cy + FLAG_H // 2 + 4))

    overlay.set_alpha(alpha)
    surf.blit(overlay, (0, GRID_TOP))


def draw_header(surf, font_big, font_sub, font_sm, font_cmid, font_cbig,
                alive_count, total, frame):
    t1 = font_sub.render("Who will win the", True, (200, 200, 200))
    t2 = font_big.render("World Cup 2026?", True, (255, 215, 0))
    surf.blit(t1, t1.get_rect(centerx=WIDTH // 2, centery=85))
    surf.blit(t2, t2.get_rect(centerx=WIDTH // 2, centery=175))

    if alive_count <= 1:
        return

    text = f"  {alive_count} / {total} remaining  "

    if alive_count <= 4:
        pulse = 1.0 + 0.05 * math.sin(2 * math.pi * frame / (0.5 * FPS))
        t3 = font_cbig.render(text, True, (255, 200, 0))
        w, h = t3.get_size()
        t3 = pygame.transform.scale(t3, (max(1, int(w * pulse)), max(1, int(h * pulse))))
    elif alive_count <= 9:
        t3 = font_cmid.render(text, True, (220, 220, 100))
    else:
        t3 = font_sm.render(text, True, (160, 160, 160))

    surf.blit(t3, t3.get_rect(centerx=WIDTH // 2, centery=268))


def draw_winner_screen(surf, winner, timer, particles, font_big, font_med, font_sm):
    progress = 1.0 - timer / WINNER_FRAMES
    col      = COUNTRIES_COLORS.get(winner, (255, 215, 0))
    alpha    = min(255, int(progress * 3.5 * 255))

    draw_glow(surf, (WIDTH // 2, HEIGHT // 2), 350, col,
              layers=20, max_alpha=min(200, int(progress * 240)))
    for p in particles:
        p.draw(surf)

    win_r = 160
    bc = (int(WIDTH / 2), int(HEIGHT / 2) + 60)
    draw_glow(surf, bc, win_r, col, layers=18, max_alpha=160)
    flag = get_flag_ball(winner, win_r * 2)
    if flag:
        surf.blit(flag, flag.get_rect(center=bc))
    else:
        pygame.draw.circle(surf, col, bc, win_r)

    w_surf = font_big.render("WINNER", True, (255, 215, 0))
    w_surf.set_alpha(alpha)
    surf.blit(w_surf, w_surf.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 - 280))

    n_surf = font_med.render(winner, True, (255, 255, 255))
    n_surf.set_alpha(alpha)
    surf.blit(n_surf, n_surf.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 + 340))

    # Tagline en los últimos 1.5s, fade in 0.4s
    if WINNER_TAGLINE and timer < int(FPS * 1.5):
        elapsed = int(FPS * 1.5) - timer
        tag_alpha = min(255, int(255 * elapsed / (FPS * 0.4)))
        t_surf = font_sm.render(WINNER_TAGLINE, True, (255, 255, 255))
        t_surf.set_alpha(tag_alpha)
        surf.blit(t_surf, t_surf.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 + 410))


# ══════════════════════════════════════════════════════════════════════════════
# SEED SEARCH (headless, pura Python — física idéntica al original)
# ══════════════════════════════════════════════════════════════════════════════

def _sim_headless(seed, country_list):
    ACX, ACY = float(ARENA_CENTER[0]), float(ARENA_CENTER[1])
    AR   = ARENA_RADIUS
    dt   = 1.0 / FPS
    SHALF = math.asin(min(0.999, (SPIKE_WIDTH / 2) / AR))
    SA   = [math.radians(a) for a in SPIKE_ANGLES_DEG]
    OM   = SPIKE_OMEGA

    def _spts(angle):
        tx  = ACX + math.cos(angle) * (AR - SPIKE_LENGTH)
        ty  = ACY + math.sin(angle) * (AR - SPIKE_LENGTH)
        blx = ACX + math.cos(angle - SHALF) * AR
        bly = ACY + math.sin(angle - SHALF) * AR
        brx = ACX + math.cos(angle + SHALF) * AR
        bry = ACY + math.sin(angle + SHALF) * AR
        return (tx,ty),(blx,bly),(brx,bry)

    def _sd(px,py,ax,ay,bx,by):
        abx=bx-ax; aby=by-ay; apx=px-ax; apy=py-ay
        d2 = abx*abx+aby*aby
        t  = max(0.0,min(1.0,(apx*abx+apy*aby)/d2)) if d2>1e-9 else 0.0
        dx = px-(ax+t*abx); dy = py-(ay+t*aby)
        return (dx*dx+dy*dy)**0.5

    def _shit(px,py,r,angle):
        (tx,ty),(blx,bly),(brx,bry) = _spts(angle)
        return min(_sd(px,py,tx,ty,blx,bly),
                   _sd(px,py,tx,ty,brx,bry),
                   _sd(px,py,blx,bly,brx,bry)) < r+4

    rng   = random.Random(seed)
    n     = len(country_list)
    ring  = AR * 0.55
    balls = []
    for i, country in enumerate(country_list):
        a  = 2*math.pi*i/n + rng.uniform(-0.1, 0.1)
        bx = ACX + math.cos(a)*ring
        by = ACY + math.sin(a)*ring
        spd = rng.uniform(380, BALL_SPEED0)
        va  = a + math.pi + rng.uniform(-0.4, 0.4)
        balls.append([bx, by, math.cos(va)*spd, math.sin(va)*spd,
                      float(BALL_R0), True, country])

    rot  = 0.0
    elim = []

    for frame in range(MAX_FRAMES):
        rot += OM                                     # rad/frame, idéntico al main loop
        alive = [b for b in balls if b[5]]
        if len(alive) <= 1:
            break
        for b in alive:
            bx,by,vx,vy,r = b[0],b[1],b[2],b[3],b[4]
            bx+=vx*dt; by+=vy*dt
            dead = False
            for sa in SA:
                if _shit(bx,by,r,sa+rot):
                    dead=True; break
            if dead:
                b[5]=False; elim.append((frame,b[6]))
            else:
                dx=bx-ACX; dy=by-ACY; d=(dx*dx+dy*dy)**0.5
                if d+r>=AR:
                    nx=dx/d; ny=dy/d
                    dot=vx*nx+vy*ny
                    if dot>0: vx-=2*dot*nx; vy-=2*dot*ny
                    buf=r*BALL_GROWTH+4.0
                    bx=ACX+nx*(AR-r-buf); by=ACY+ny*(AR-r-buf)
                    r=min(r*(1+BALL_GROWTH),MAX_BALL_R)
                    spd=(vx*vx+vy*vy)**0.5
                    if spd>0:
                        s2=min(spd*(1+ACCEL_RATE),MAX_SPEED)/spd
                        vx*=s2; vy*=s2
                b[0]=bx;b[1]=by;b[2]=vx;b[3]=vy;b[4]=r

    still  = [b[6] for b in balls if b[5]]
    winner = still[0] if still else (elim[-1][1] if elim else "?")
    top5   = list(dict.fromkeys([winner]+[c for _,c in reversed(elim[-4:])]))[:5]
    return winner, top5, frame


def run_seed_search(country_list):
    print(f"{'seed':>6}  {'secs':>5}  {'winner':<16}  top_5_survivors")
    print("-" * 72)
    good = []
    for seed in range(200):
        winner, top5, frames = _sim_headless(seed, country_list)
        secs = frames / FPS
        t5   = " > ".join(top5[:5])
        print(f"{seed:>6}  {secs:>5.1f}  {winner:<16}  {t5}")
        if 12 <= secs <= 22:
            good.append((seed, secs, winner))
    if good:
        best = max(good, key=lambda x: x[1])
        print(f"\n→ Seed recomendado: {best[0]}  ({best[2]}, {best[1]:.1f}s)")
    else:
        print("\nNingún seed en 12-22s. Reducir BALL_GROWTH o aumentar SPIKE_OMEGA.")
    sys.exit(0)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    countries = []
    for code in TEAMS_R32:
        if code.startswith("TBD"):
            countries.append(code)
        else:
            countries.append(TEAM_TO_COUNTRY.get(code, code))

    if SEED_SEARCH:
        run_seed_search(countries)

    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()

    print("Verificando banderas...")
    for country in countries:
        if not country.startswith("TBD") and country in FLAG_CODES:
            ensure_flag(country)

    pygame.mixer.pre_init(44100, -16, 1, 1024)
    pygame.init()
    pygame.font.init()
    font_big  = pygame.font.SysFont("Arial", 72, bold=True)
    font_med  = pygame.font.SysFont("Arial", 54, bold=True)
    font_sub  = pygame.font.SysFont("Arial", 48)
    font_sm   = pygame.font.SysFont("Arial", 36)
    font_xs   = pygame.font.SysFont("Arial", 26, bold=True)
    font_cmid = pygame.font.SysFont("Arial", 47, bold=True)
    font_cbig = pygame.font.SysFont("Arial", 58, bold=True)
    font_iso  = pygame.font.SysFont("Arial", 24, bold=True)

    scale  = 0.22 if args.record else 0.36
    screen = pygame.display.set_mode((int(WIDTH * scale), int(HEIGHT * scale)))
    pygame.display.set_caption("World Cup R32 — Battle Royale" +
                                (" (grabando...)" if args.record else ""))
    surface = pygame.Surface((WIDTH, HEIGHT))

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir  = os.path.join(base_dir, "output")
    os.makedirs(out_dir, exist_ok=True)
    out_mp4  = os.path.join(out_dir, "world_cup_winner_r32.mp4")
    temp_vid = os.path.join(out_dir, "_r32_tmp.mp4")
    temp_wav = os.path.join(out_dir, "_r32_tmp.wav")

    vid_gen = None
    if args.record:
        vid_gen = imageio_ffmpeg.write_frames(
            temp_vid, (WIDTH, HEIGHT), fps=FPS,
            pix_fmt_in='rgb24', pix_fmt_out='yuv420p',
            codec='libx264', quality=None, macro_block_size=1,
            output_params=['-crf', '18', '-preset', 'fast'],
            ffmpeg_log_level='quiet',
        )
        vid_gen.send(None)

    def push(s):
        if vid_gen is None:
            return
        arr = pygame.surfarray.array3d(s)
        vid_gen.send(np.ascontiguousarray(arr.transpose(1, 0, 2)).tobytes())

    arena_glow = make_arena_glow()

    # Sonido burbuja en preview
    bubble_sfx = None
    if not args.record and os.path.exists(BUBBLE_POP_PATH):
        try:
            bubble_sfx = pygame.mixer.Sound(BUBBLE_POP_PATH)
            bubble_sfx.set_volume(0.7)
        except Exception:
            bubble_sfx = None

    # Sonidos metálicos de colisión con pared (5 notas pentatónicas)
    _PENTA_INIT = [130.81, 146.83, 164.81, 196.00, 220.00]
    metal_sfx_map: dict = {}
    if not args.record:
        for _f in _PENTA_INIT:
            try:
                _arr = gen_metal_hit(_f)
                _snd = pygame.mixer.Sound(buffer=_arr)
                _snd.set_volume(0.6)
                metal_sfx_map[_f] = _snd
            except Exception:
                pass

    # ── Inicializar 32 bolas en anillo ───────────────────────────────────────
    n_teams = len(countries)
    ring_r  = ARENA_RADIUS * 0.55
    balls   = []
    for i, country in enumerate(countries):
        a   = 2 * math.pi * i / n_teams
        pos = ARENA_CENTER + np.array([math.cos(a), math.sin(a)]) * ring_r
        spd = random.uniform(380, BALL_SPEED0)
        va  = a + math.pi + random.uniform(-0.4, 0.4)
        vel = np.array([math.cos(va), math.sin(va)]) * spd
        balls.append({
            'country':        country,
            'pos':            pos.copy(),
            'vel':            vel.copy(),
            'r':              float(BALL_R0),
            'alive':          True,
            'near_miss_t':    0.0,   # glow blanco: segundos restantes [0, 0.4]
            'near_miss_name': 0.0,   # flash ISO:   segundos restantes [0, 0.6]
        })

    # ── Estado ──────────────────────────────────────────────────────────────
    sound_events:  list = []
    all_particles: list = []
    frame          = 0
    running        = True
    rotation       = 0.0             # rad/frame acumulados
    winner:        str | None = None
    winner_timer   = 0
    winner_frame:  int | None = None
    state          = 'intro'
    intro_alpha    = 0
    fanfare3_done  = False
    note_idx       = 0
    elim_count     = 0    # cuántas bolas han muerto (para calcular lifetime)
    _PENTA         = [130.81, 146.83, 164.81, 196.00, 220.00]
    teams_codes    = list(zip(TEAMS_R32, countries))
    dt             = 1.0 / FPS

    # Escalado visual de bolas (SOLO render, nunca física)
    vis_scale        = 1.0
    vis_scale_target = 1.0
    VIS_SCALE_SPEED  = 1.0 / (0.5 * FPS)

    clock = pygame.time.Clock()

    while running and frame < MAX_FRAMES:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                running = False

        # ── Rotación de spikes: idéntica al original (rad/frame)  ───────────
        rotation += SPIKE_OMEGA

        # ── Lerp vis_scale (solo para render) ───────────────────────────────
        alive_balls = [b for b in balls if b['alive']]
        alive_count = len(alive_balls)
        if state == 'playing':
            if alive_count <= 5:
                vis_scale_target = 1.7
            elif alive_count <= 10:
                vis_scale_target = 1.4
            else:
                vis_scale_target = 1.0
            if vis_scale < vis_scale_target:
                vis_scale = min(vis_scale_target, vis_scale + VIS_SCALE_SPEED)
            elif vis_scale > vis_scale_target:
                vis_scale = max(vis_scale_target, vis_scale - VIS_SCALE_SPEED)

        # ── Estados ──────────────────────────────────────────────────────────
        if state == 'intro':
            intro_alpha = min(255, intro_alpha + 6)
            if frame >= INTRO_FRAMES:
                state = 'playing'

        elif state == 'playing':
            if alive_count == 3 and not fanfare3_done:
                sound_events.append((frame, 'fanfare', None))
                fanfare3_done = True

            if alive_count <= 1:
                if alive_count == 1:
                    winner       = alive_balls[0]['country']
                    winner_frame = frame
                    all_particles.clear()
                    col_w = COUNTRIES_COLORS.get(winner, (255, 215, 0))
                    for _ in range(4):
                        off = np.array([random.uniform(-80, 80), random.uniform(-80, 80)])
                        all_particles.extend(
                            spawn_explosion(ARENA_CENTER + off, col_w, int(MAX_BALL_R * 0.6)))
                    sound_events.append((frame, 'fanfare', None))
                    state        = 'winner'
                    winner_timer = WINNER_FRAMES
                    if not args.record:
                        try:
                            pygame.mixer.music.load(BET365_PATH)
                            pygame.mixer.music.play()
                        except Exception:
                            pass
                else:
                    running = False
            else:
                for b in alive_balls:
                    # ── Física: SOLO usa b['r'], nunca vis_scale ─────────────
                    b['pos'] += b['vel'] * dt
                    r     = b['r']
                    near  = False
                    killed = False

                    for sa in SPIKE_ANGLES:
                        hit, dist = spike_hit_and_dist(b['pos'], r, sa + rotation)
                        if hit:
                            lt = _elim_lifetime(elim_count)
                            all_particles.extend(
                                spawn_flag_explosion(b['pos'], b['country'], int(r), lt))
                            elim_count += 1
                            sound_events.append((frame, 'bubble', None))
                            b['alive'] = False
                            killed = True
                            if bubble_sfx is not None:
                                bubble_sfx.play()
                            break
                        elif dist < r * 1.5 + 4:
                            near = True

                    if killed:
                        continue

                    # Near-miss timers
                    if near:
                        if b['near_miss_t'] <= 0:
                            b['near_miss_name'] = 0.6
                        b['near_miss_t'] = 0.4
                    else:
                        b['near_miss_t'] = max(0.0, b['near_miss_t'] - dt)
                    b['near_miss_name'] = max(0.0, b['near_miss_name'] - dt)

                    b['pos'], b['vel'], bounced = wall_bounce(b['pos'], b['vel'], r)
                    if bounced:
                        b['r'] = min(b['r'] * (1 + BALL_GROWTH), MAX_BALL_R)
                        spd = np.linalg.norm(b['vel'])
                        if spd > 0:
                            b['vel'] = b['vel'] / spd * min(spd * (1 + ACCEL_RATE), MAX_SPEED)
                        freq = _PENTA[note_idx % len(_PENTA)]
                        sound_events.append((frame, 'metal', freq))
                        if metal_sfx_map:
                            s = metal_sfx_map.get(freq)
                            if s: s.play()
                        note_idx += 1

        elif state == 'winner':
            winner_timer -= 1
            if winner_timer <= 0:
                running = False

        # ── Partículas ───────────────────────────────────────────────────────
        if state in ('playing', 'winner'):
            for p in all_particles:
                p.step(dt)
            all_particles = [p for p in all_particles
                             if not isinstance(p, FlagBallParticle) or p.age < p.lifetime]
            if all_particles:
                for _ in range(2):
                    for sa in SPIKE_ANGLES:
                        bounce_particles_on_spike(all_particles, sa + rotation)
                    collide_particles(all_particles)

        # ── Dibujo ───────────────────────────────────────────────────────────
        surface.fill(BG_COLOR)

        if state == 'intro':
            draw_arena(surface, arena_glow, rotation)
            draw_header(surface, font_big, font_sub, font_sm, font_cmid, font_cbig,
                        n_teams, n_teams, frame)
            draw_intro_grid(surface, teams_codes, font_xs, intro_alpha)

        elif state == 'playing':
            draw_arena(surface, arena_glow, rotation)
            for p in all_particles:
                p.draw(surface)
            alive_now = sum(1 for b in balls if b['alive'])
            for b in balls:
                if not b['alive']:
                    continue
                draw_r = b['r'] * vis_scale   # radio visual; física usa b['r']
                draw_ball_br(surface, b['country'], b['pos'], draw_r, b['near_miss_t'])

                # ISO label: siempre si ≤3, o durante near-miss flash
                if alive_now <= 3:
                    draw_iso_label(surface, font_iso, b['country'], b['pos'], draw_r, 229)
                elif b['near_miss_name'] > 0:
                    elapsed = 0.6 - b['near_miss_name']
                    if elapsed < 0.2:
                        a = int(elapsed / 0.2 * 229)
                    elif elapsed < 0.4:
                        a = 229
                    else:
                        a = int((0.6 - elapsed) / 0.2 * 229)
                    draw_iso_label(surface, font_iso, b['country'], b['pos'], draw_r, a)

            draw_header(surface, font_big, font_sub, font_sm, font_cmid, font_cbig,
                        alive_now, n_teams, frame)

        elif state == 'winner' and winner:
            draw_winner_screen(surface, winner, winner_timer, all_particles,
                               font_big, font_med, font_sm)

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

    bubble_pcm_data = None
    if os.path.exists(BUBBLE_POP_PATH):
        print("Cargando bubble-pop.mp3...")
        bubble_pcm_data = _load_mp3_pcm(BUBBLE_POP_PATH)

    pcm = process_audio(sound_events, frame, bubble_pcm=bubble_pcm_data)

    # Mezclar bet-365 en el frame del ganador
    if os.path.exists(BET365_PATH) and winner_frame is not None:
        print("Mezclando bet-365-goal-sound...")
        mp3_f = _load_mp3_pcm(BET365_PATH)
        if len(mp3_f) > 0:
            buf_f   = pcm.astype(np.float64)
            win_pos = int(winner_frame * SAMPLE_RATE / FPS)
            end     = min(win_pos + len(mp3_f), len(buf_f))
            buf_f[win_pos:end] += mp3_f[:end - win_pos]
            peak = np.max(np.abs(buf_f))
            if peak > 0:
                buf_f = buf_f / peak * 0.90 * 32767
            pcm = buf_f.astype(np.int16)

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
