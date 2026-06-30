"""
Match Score — partido 1v1 dentro de un aro con dos porterías (huecos).
Dos pelotas (COL y POR) rebotan dentro de la circunferencia y colisionan entre
sí. El aro rebota EXCEPTO en dos huecos: arriba (lo defiende COL) y abajo (lo
defiende POR). Pelota que sale por un hueco = GOL para el equipo CONTRARIO al
que lo defiende. Reloj 0'→90' acelerado a ~16 s. Pitido final al 90'.
Formato: 1080x1920 Short vertical, 60fps.

Uso:
    python shorts/match_score.py            # preview
    python shorts/match_score.py --record   # graba MP4 en shorts/output/
"""

# ═══════════════════════════════════════════════════════════════════════════
# ██  CONFIGURACIÓN DEL PARTIDO — editar solo este bloque para cada juego  ██
# ═══════════════════════════════════════════════════════════════════════════

TEAM_TOP    = "NED"   # defiende el hueco de ARRIBA   ← CAMBIAR AQUÍ
TEAM_BOTTOM = "MAR"   # defiende el hueco de ABAJO    ← CAMBIAR AQUÍ
RANDOM_SEED = 22      # int → resultado fijo | None → distinto cada vez

HOOK_TEXT   = "NO REFEREE. ONLY PHYSICS."   # gancho conceptual del inicio

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
Particle                 = _wcw.Particle
spawn_explosion          = _wcw.spawn_explosion
collide_particles        = _wcw.collide_particles
push_particles_from_ball = _wcw.push_particles_from_ball
gen_bong                 = _wcw.gen_bong

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
    "GHA": "Ghana",     "PAN": "Panama",         "COD": "DR Congo",
    "UZB": "Uzbekistan","ALG": "Algeria",        "AUT": "Austria",
    "JOR": "Jordan",    "PAR": "Paraguay",
}


# ════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ════════════════════════════════════════════════════════════════════════════

WIDTH, HEIGHT = 1080, 1920
FPS           = 60
SAMPLE_RATE   = 44100

ARENA_CENTER = np.array([WIDTH / 2.0, 1060.0])
ARENA_RADIUS = 350        # tamaño original de la circunferencia

# Reloj de partido: 0'→90' mapeado a ~16 s reales
MATCH_SECONDS = 16
MATCH_FRAMES  = MATCH_SECONDS * FPS        # 960 frames de juego
FINAL_FRAMES  = int(FPS * 2.4)             # pantalla final ~2.4 s
KICKOFF_FRAME = 0

# Hook de texto inicial: aparece ~0.3s, se mantiene ~1.5s, fade out
HOOK_IN_FRAME = int(FPS * 0.3)            # entra a ~0.3 s
HOOK_HOLD     = int(FPS * 1.5)            # se mantiene ~1.5 s
HOOK_FADE     = int(FPS * 0.5)            # fade out de ~0.5 s
HOOK_Y        = 420                       # tercio superior, bajo el marcador, sobre el aro

# Un solo hueco (portería compartida) que GIRA con la circunferencia.
GAP_BASE_DEG = -90                          # arranca arriba (y crece hacia abajo)
GAP_HALF_DEG = 15                           # arco a la mitad (antes 34)
GAP_BASE     = math.radians(GAP_BASE_DEG)
GAP_HALF     = math.radians(GAP_HALF_DEG)
ROT_OMEGA    = 2 * math.pi / (FPS * 5)      # 1 vuelta cada 7 s

BALL_RADIUS  = 40
BALL_SPEED0  = 800.0
SPEED_GAIN   = 1.012      # subida muy leve por rebote
MAX_SPEED    = 1500.0

GRAVITY   = 0.0            # sin gravedad: rebote puro dentro del aro
PART_DAMP = 0.992

COLOR_BG  = (0, 0, 0)
MAX_TOTAL_FRAMES = FPS * 30

# ── Propagar constantes a _wcw (Particle/spawn_explosion usan sus globals) ──
_wcw.ARENA_CENTER        = ARENA_CENTER
_wcw.ARENA_RADIUS        = ARENA_RADIUS
_wcw.GRAVITY             = GRAVITY
_wcw.PART_DAMP           = PART_DAMP
_wcw.BALL_INITIAL_RADIUS = BALL_RADIUS
_wcw.MAX_BALL_R          = BALL_RADIUS


# ════════════════════════════════════════════════════════════════════════════
# GEOMETRÍA / HUECOS
# ════════════════════════════════════════════════════════════════════════════

def in_gap(angle: float, rotation: float) -> bool:
    """True si `angle` cae dentro del único hueco, ya rotado."""
    center = GAP_BASE + rotation
    diff   = (angle - center + math.pi) % (2 * math.pi) - math.pi
    return abs(diff) <= GAP_HALF


# ════════════════════════════════════════════════════════════════════════════
# RED DE PORTERÍA (malla curva afuera del aro, con resorte)
# ════════════════════════════════════════════════════════════════════════════

class GoalNet:
    """Malla curva en el arco del hueco; gira con la circunferencia y se ondula al gol."""
    def __init__(self, base_ang: float, color: tuple):
        self.base   = base_ang
        # red neutra (portería compartida); el flash usa el color del que anota
        self.color  = tuple(int(c * 0.30 + 255 * 0.70) for c in color)
        self.na     = 13          # nodos angulares
        self.nr     = 4           # nodos radiales (j=0 anclado al aro)
        self.depth  = 78          # profundidad de la red hacia afuera (px)
        self.disp   = np.zeros((self.na, self.nr, 2))
        self.vel    = np.zeros((self.na, self.nr, 2))
        self._rest  = np.zeros((self.na, self.nr, 2))
        self.update(0.0)

    def update(self, rotation: float):
        """Recalcula las posiciones de reposo según la rotación actual."""
        center = self.base + rotation
        for i in range(self.na):
            a = center - GAP_HALF + (2 * GAP_HALF) * i / (self.na - 1)
            cos_a, sin_a = math.cos(a), math.sin(a)
            for j in range(self.nr):
                rr = ARENA_RADIUS + 3 + self.depth * j / (self.nr - 1)
                self._rest[i, j] = ARENA_CENTER + np.array([cos_a, sin_a]) * rr

    def step(self, dt: float):
        k, damp = 130.0, 6.5
        self.vel += (-k * self.disp - damp * self.vel) * dt
        self.disp += self.vel * dt
        self.disp[:, 0, :] = 0.0    # fila pegada al aro no se mueve
        self.vel[:, 0, :]  = 0.0

    def impact(self, point: np.ndarray, strength: float = 520.0):
        for i in range(self.na):
            for j in range(1, self.nr):
                rp   = self._rest[i, j]
                d    = float(np.linalg.norm(rp - point))
                w    = math.exp(-(d * d) / (2 * 50 * 50)) * (j / (self.nr - 1))
                rad  = rp - ARENA_CENTER
                rad /= (np.linalg.norm(rad) + 1e-6)
                self.vel[i, j] += rad * (strength * w)

    def draw(self, surf: pygame.Surface):
        pos = self._rest + self.disp
        for i in range(self.na):
            pts = [(int(pos[i, j, 0]), int(pos[i, j, 1])) for j in range(self.nr)]
            pygame.draw.lines(surf, self.color, False, pts, 2)
        for j in range(self.nr):
            pts = [(int(pos[i, j, 0]), int(pos[i, j, 1])) for i in range(self.na)]
            pygame.draw.lines(surf, self.color, False, pts, 2)


# ════════════════════════════════════════════════════════════════════════════
# AUDIO
# ════════════════════════════════════════════════════════════════════════════

def mix_audio(events: list, total_frames: int) -> np.ndarray:
    total_samples = int(total_frames / FPS * SAMPLE_RATE) + SAMPLE_RATE
    buf = np.zeros(total_samples, dtype=np.float64)
    for fn, stype, param in events:
        pos = int(fn * SAMPLE_RATE / FPS)
        if stype == 'goal':
            snd = _load_mp3('forza1903-a-football-hits-the-net-goal-313216.mp3')
        elif stype == 'whistle':
            snd = _load_mp3('freesound_community-referee-whistle-blow-gymnasium-6320.mp3')
        elif stype == 'bet365':
            snd = _load_mp3('bet-365-goal-sound.mp3')
        elif stype == 'bong':
            snd = gen_bong(param if param else 220.0).astype(np.float64) * 0.35
        else:
            continue
        end = min(pos + len(snd), total_samples)
        buf[pos:end] += snd[:end - pos]
    peak = np.max(np.abs(buf))
    if peak > 0:
        buf = buf / peak * 0.92 * 32767
    return buf.astype(np.int16)


# ════════════════════════════════════════════════════════════════════════════
# DIBUJO
# ════════════════════════════════════════════════════════════════════════════

def draw_ring(surf: pygame.Surface, rotation: float):
    """Dibuja el aro (glow aditivo + trazo) cortando el hueco en su posición rotada."""
    glow   = pygame.Surface((WIDTH, HEIGHT))                 # RGB negro → aditivo
    cx, cy = float(ARENA_CENTER[0]), float(ARENA_CENTER[1])
    N = 480
    strokes = []
    prev_pt = None
    prev_in = True
    for i in range(N + 1):
        a  = 2 * math.pi * i / N
        ig = in_gap(a, rotation)
        pt = (int(cx + math.cos(a) * ARENA_RADIUS),
              int(cy + math.sin(a) * ARENA_RADIUS))
        if prev_pt is not None and not ig and not prev_in:
            for w, c in ((15, (24, 24, 28)), (9, (40, 40, 46)), (5, (72, 72, 80))):
                pygame.draw.line(glow, c, prev_pt, pt, w)
            strokes.append((prev_pt, pt))
        prev_pt, prev_in = pt, ig
    surf.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    for a, b in strokes:
        pygame.draw.line(surf, (255, 255, 255), a, b, 5)


def make_inner_dark():
    """Disco negro semi-transparente para oscurecer DENTRO del aro."""
    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(layer, (0, 0, 0, 90),
                       (int(ARENA_CENTER[0]), int(ARENA_CENTER[1])), ARENA_RADIUS - 2)
    return layer


def draw_ball(surf: pygame.Surface, country: str, pos: np.ndarray, r: int):
    glow_col = COUNTRIES_COLORS[country]
    draw_glow(surf, (int(pos[0]), int(pos[1])), r, glow_col, layers=14, max_alpha=120)
    flag = get_flag_ball(country, r * 2)
    if flag:
        surf.blit(flag, flag.get_rect(center=(int(pos[0]), int(pos[1]))))
    else:
        pygame.draw.circle(surf, glow_col, (int(pos[0]), int(pos[1])), r)


def render_outline(font, text, color, oc=(0, 0, 0), ow=3):
    base = font.render(text, True, color)
    ol   = font.render(text, True, oc)
    w, h = base.get_size()
    surf = pygame.Surface((w + 2 * ow, h + 2 * ow), pygame.SRCALPHA)
    for dx in (-ow, 0, ow):
        for dy in (-ow, 0, ow):
            if dx or dy:
                surf.blit(ol, (ow + dx, ow + dy))
    surf.blit(base, (ow, ow))
    return surf


def draw_scoreboard(surf, fonts, ct, cb, st, sb, minute, pulse_top, pulse_bot):
    """Barra superior: banderas + 'COL x – y POR' + minuto. cb=abajo, ct=arriba."""
    f_team, f_score, f_min = fonts['team'], fonts['score'], fonts['min']

    # barra negra semi-transparente
    bar = pygame.Surface((WIDTH, 215), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 150))
    surf.blit(bar, (0, 0))

    def sc_color(pulse):
        if pulse > 0:
            t = pulse / 12.0
            return (255, int(220 * (1 - t * 0.25)), int(40 * (1 - t)))
        return (255, 255, 255)

    fh    = 60
    fl_t  = get_flag_sub(ct, height=fh)
    fl_b  = get_flag_sub(cb, height=fh)
    code_t = render_outline(f_team, TEAM_TOP,    (255, 255, 255))
    code_b = render_outline(f_team, TEAM_BOTTOM, (255, 255, 255))
    s_t    = render_outline(f_score, str(st), sc_color(pulse_top))
    dash   = render_outline(f_score, "–", (200, 200, 200))
    s_b    = render_outline(f_score, str(sb), sc_color(pulse_bot))

    G = 16
    pieces = [fl_t, code_t, s_t, dash, s_b, code_b, fl_b]
    total  = sum(p.get_width() for p in pieces) + G * (len(pieces) - 1)
    x  = WIDTH // 2 - total // 2
    cy = 80
    for p in pieces:
        surf.blit(p, (x, cy - p.get_height() // 2))
        x += p.get_width() + G

    # minuto
    mt = render_outline(f_min, f"{minute}'", (255, 230, 90))
    surf.blit(mt, mt.get_rect(centerx=WIDTH // 2, centery=170))


def render_hook_surface(font, text, ow=5):
    """Texto con sombra suave + contorno negro continuo y grueso + relleno blanco."""
    base   = font.render(text, True, (255, 255, 255))
    ol     = font.render(text, True, (0, 0, 0))
    w, h   = base.get_size()
    pad    = ow + 10
    surf   = pygame.Surface((w + 2 * pad, h + 2 * pad), pygame.SRCALPHA)
    ox, oy = pad, pad

    # sombra desplazada
    shadow = font.render(text, True, (0, 0, 0))
    shadow.set_alpha(150)
    surf.blit(shadow, (ox + 5, oy + 8))

    # contorno continuo: anillo de blits a radio ow (y un radio interior)
    offsets = set()
    for k in range(24):
        a = 2 * math.pi * k / 24
        offsets.add((round(ow * math.cos(a)),       round(ow * math.sin(a))))
        offsets.add((round(ow * 0.6 * math.cos(a)), round(ow * 0.6 * math.sin(a))))
    for dx, dy in offsets:
        surf.blit(ol, (ox + dx, oy + dy))

    surf.blit(base, (ox, oy))
    return surf


def draw_hook(surf, fonts, frame):
    """Texto-gancho del inicio: aparece ~0.3s, se mantiene ~1.5s y hace fade out."""
    fade_in = FPS * 0.15
    if frame < HOOK_IN_FRAME - fade_in or frame >= HOOK_IN_FRAME + HOOK_HOLD + HOOK_FADE:
        return
    if frame < HOOK_IN_FRAME:
        alpha = int(255 * (frame - (HOOK_IN_FRAME - fade_in)) / fade_in)
    elif frame < HOOK_IN_FRAME + HOOK_HOLD:
        alpha = 255
    else:
        t = (frame - (HOOK_IN_FRAME + HOOK_HOLD)) / HOOK_FADE
        alpha = int(255 * (1.0 - t))
    alpha = max(0, min(255, alpha))

    txt   = render_hook_surface(fonts['hook'], HOOK_TEXT)
    max_w = WIDTH - 90                                    # margen lateral
    if txt.get_width() > max_w:
        s   = max_w / txt.get_width()
        txt = pygame.transform.smoothscale(
            txt, (int(txt.get_width() * s), int(txt.get_height() * s)))
    txt.set_alpha(alpha)
    surf.blit(txt, txt.get_rect(centerx=WIDTH // 2, centery=HOOK_Y))


def draw_final(surf, fonts, ct, cb, st, sb, timer):
    progress = 1.0 - timer / FINAL_FRAMES
    alpha    = min(255, int(progress * 4 * 255))

    if st > sb:
        winner, w_col = ct, COUNTRIES_COLORS[ct]
        msg = f"{TEAM_TOP} WINS"
    elif sb > st:
        winner, w_col = cb, COUNTRIES_COLORS[cb]
        msg = f"{TEAM_BOTTOM} WINS"
    else:
        winner, w_col, msg = None, (255, 215, 0), "DRAW"

    ft = render_outline(fonts['big'], "FINAL", (255, 215, 0))
    ft.set_alpha(alpha)
    surf.blit(ft, ft.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 - 430))

    # bandera del ganador resaltada (o ambas si empate)
    cy_flag = HEIGHT // 2 - 170
    if winner:
        draw_glow(surf, (WIDTH // 2, cy_flag), 150, w_col, layers=18, max_alpha=170)
        fl = get_flag_ball(winner, 280)
        if fl:
            surf.blit(fl, fl.get_rect(center=(WIDTH // 2, cy_flag)))
    else:
        for c, dx in ((ct, -160), (cb, 160)):
            fl = get_flag_ball(c, 220)
            if fl:
                surf.blit(fl, fl.get_rect(center=(WIDTH // 2 + dx, cy_flag)))

    # marcador grande
    s_t  = render_outline(fonts['final_score'], str(st), (255, 255, 255))
    dash = render_outline(fonts['final_score'], "–", (150, 150, 150))
    s_b  = render_outline(fonts['final_score'], str(sb), (255, 255, 255))
    G = 26
    total = s_t.get_width() + dash.get_width() + s_b.get_width() + 2 * G
    x  = WIDTH // 2 - total // 2
    cy = HEIGHT // 2 + 110
    for p in (s_t, dash, s_b):
        p.set_alpha(alpha)
        surf.blit(p, (x, cy - p.get_height() // 2))
        x += p.get_width() + G

    wt = render_outline(fonts['med'], msg, w_col)
    wt.set_alpha(alpha)
    surf.blit(wt, wt.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 + 300))


# ════════════════════════════════════════════════════════════════════════════
# FÍSICA DE PELOTAS
# ════════════════════════════════════════════════════════════════════════════

def spawn_ball(side: str):
    ang = random.uniform(0, 2 * math.pi)
    vel = np.array([math.cos(ang), math.sin(ang)]) * BALL_SPEED0
    ox  = -150.0 if side == 'top' else 150.0
    oy  = random.uniform(-40, 40)
    return (ARENA_CENTER + np.array([ox, oy])).astype(float), vel.astype(float)


def ball_ball_collision(p1, v1, p2, v2, r):
    delta = p1 - p2
    d = float(np.linalg.norm(delta))
    hit = False
    if 1e-6 < d < 2 * r:
        n   = delta / d
        # separar
        overlap = 2 * r - d
        p1 += n * (overlap / 2)
        p2 -= n * (overlap / 2)
        # intercambio elástico de componente normal (masas iguales)
        rel = float(np.dot(v1 - v2, n))
        if rel < 0:
            v1 -= rel * n
            v2 += rel * n
            hit = True
    return p1, v1, p2, v2, hit


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    country_t = TEAM_TO_COUNTRY[TEAM_TOP]
    country_b = TEAM_TO_COUNTRY[TEAM_BOTTOM]

    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()

    print("Verificando banderas...")
    ensure_flag(country_t)
    ensure_flag(country_b)

    pygame.init()
    pygame.font.init()

    fonts = {
        'team':        pygame.font.SysFont("Arial", 46, bold=True),
        'score':       pygame.font.SysFont("Arial", 84, bold=True),
        'min':         pygame.font.SysFont("Arial", 50, bold=True),
        'big':         pygame.font.SysFont("Arial", 92, bold=True),
        'med':         pygame.font.SysFont("Arial", 64, bold=True),
        'final_score': pygame.font.SysFont("Arial", 150, bold=True),
        'hook':        pygame.font.SysFont("impact,anton,arialblack", 92),
    }

    scale  = 0.22 if args.record else 0.36
    screen = pygame.display.set_mode((int(WIDTH * scale), int(HEIGHT * scale)))
    pygame.display.set_caption(
        f"{TEAM_TOP} vs {TEAM_BOTTOM}" + (" — grabando..." if args.record else ""))
    surface = pygame.Surface((WIDTH, HEIGHT))

    out_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_mp4  = os.path.join(out_dir, f"match_{TEAM_TOP}_vs_{TEAM_BOTTOM}.mp4")
    temp_vid = os.path.join(out_dir, f"_ms_{TEAM_TOP}_{TEAM_BOTTOM}.mp4")
    temp_wav = os.path.join(out_dir, f"_ms_{TEAM_TOP}_{TEAM_BOTTOM}.wav")

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

    # ── Fondo (pitch) + capas ──────────────────────────────────────────────
    pitch_raw = pygame.image.load(os.path.join(_ASSETS_DIR, "pitch_1v1_muted.png")).convert()
    pitch     = pygame.transform.smoothscale(pitch_raw, (WIDTH, HEIGHT))
    inner_dark = make_inner_dark()

    # Una sola red (portería compartida) que gira con el aro
    net = GoalNet(GAP_BASE, COUNTRIES_COLORS[country_t])

    # ── Estado ─────────────────────────────────────────────────────────────
    sound_events:  list = []
    all_particles: list = []
    frame    = 0
    running  = True
    rotation = 0.0

    score_t = 0      # goles de COL (country_t)
    score_b = 0      # goles de POR (country_b)
    pulse_t = 0
    pulse_b = 0
    goal_flash = 0
    goal_cooldown = 0      # frames en que el hueco no cuenta gol (anti doble gol)
    flash_pos  = np.array([0.0, 0.0])
    flash_col  = (255, 255, 255)

    pos_t, vel_t = spawn_ball('top')
    pos_b, vel_b = spawn_ball('bottom')

    state = 'playing'
    final_timer = 0
    note_idx = 0
    _PENTA = [130.81, 146.83, 164.81, 196.00, 220.00]   # pentatónica grave (rebote pared)
    sound_events.append((KICKOFF_FRAME, 'whistle', None))

    clock = pygame.time.Clock()

    def step_ball(pos, vel, r, rot, allow_goal=True):
        """Mueve una pelota con contención en el aro (el hueco no rebota).
        Si allow_goal es False el hueco actúa como pared (evita doble gol).
        Devuelve (pos, vel, gol_bool, rebote_pared_bool)."""
        sub = 2
        bounced = False
        for _ in range(sub):
            pos += vel * (1.0 / FPS / sub)
            delta = pos - ARENA_CENTER
            d = float(np.linalg.norm(delta))
            ang = math.atan2(float(delta[1]), float(delta[0]))
            gap = in_gap(ang, rot)
            if allow_goal and gap and d > ARENA_RADIUS + r:
                return pos, vel, True, bounced             # ¡GOL!
            if d + r >= ARENA_RADIUS and (not gap or not allow_goal):
                n = delta / d if d > 1e-6 else np.array([0.0, -1.0])
                if float(np.dot(vel, n)) > 0:
                    vel -= 2 * float(np.dot(vel, n)) * n
                    bounced = True
                pos = ARENA_CENTER + n * (ARENA_RADIUS - r - 1.0)
                spd = float(np.linalg.norm(vel))
                vel = vel / spd * min(spd * SPEED_GAIN, MAX_SPEED)
        return pos, vel, False, bounced

    def register_goal(scorer_top: bool, gpos):
        nonlocal score_t, score_b, pulse_t, pulse_b, goal_flash, goal_cooldown, flash_pos, flash_col
        country = country_t if scorer_top else country_b
        col     = COUNTRIES_COLORS[country]
        if scorer_top:
            score_t += 1; pulse_t = 12
        else:
            score_b += 1; pulse_b = 12
        net.impact(gpos.copy())
        all_particles.extend(spawn_explosion(gpos, col, BALL_RADIUS))
        sound_events.append((frame, 'goal', None))
        goal_flash = 14
        goal_cooldown = int(FPS * 0.4)     # cierra el hueco un instante tras anotar
        flash_pos  = gpos.copy()
        flash_col  = col

    while running and frame < MAX_TOTAL_FRAMES:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                running = False

        dt = 1.0 / FPS
        if pulse_t > 0: pulse_t -= 1
        if pulse_b > 0: pulse_b -= 1
        if goal_flash > 0: goal_flash -= 1
        if goal_cooldown > 0: goal_cooldown -= 1

        minute = min(90, int(frame / MATCH_FRAMES * 90))

        if state == 'playing':
            rotation += ROT_OMEGA

            # Colisión entre las dos pelotas → bong grave
            pos_t, vel_t, pos_b, vel_b, balls_hit = ball_ball_collision(
                pos_t, vel_t, pos_b, vel_b, BALL_RADIUS)
            if balls_hit:
                sound_events.append((frame, 'bong', 98.0))

            # Pelota de COL: si sale por el hueco, anota COL
            pos_t, vel_t, goal_t, bounce_t = step_ball(pos_t, vel_t, BALL_RADIUS, rotation, goal_cooldown == 0)
            if goal_t:
                register_goal(scorer_top=True, gpos=pos_t.copy())
                pos_t, vel_t = spawn_ball('top')
            elif bounce_t:
                sound_events.append((frame, 'bong', _PENTA[note_idx % len(_PENTA)]))
                note_idx += 1

            # Pelota de POR: si sale por el hueco, anota POR
            pos_b, vel_b, goal_b, bounce_b = step_ball(pos_b, vel_b, BALL_RADIUS, rotation, goal_cooldown == 0)
            if goal_b:
                register_goal(scorer_top=False, gpos=pos_b.copy())
                pos_b, vel_b = spawn_ball('bottom')
            elif bounce_b:
                sound_events.append((frame, 'bong', _PENTA[note_idx % len(_PENTA)]))
                note_idx += 1

            # Fin del partido al minuto 90
            if frame >= MATCH_FRAMES:
                sound_events.append((frame, 'whistle', None))
                if score_t != score_b:        # hay ganador → celebración bet365
                    sound_events.append((frame + FPS // 2, 'bet365', None))
                state = 'final'
                final_timer = FINAL_FRAMES

        elif state == 'final':
            final_timer -= 1
            if final_timer <= 0:
                running = False

        # ── Partículas y red ────────────────────────────────────────────────
        net.update(rotation)
        net.step(dt)
        for p in all_particles:
            p.step(dt)
            p.alpha -= 360 * dt      # burst de gol breve, sin acumular
        all_particles[:] = [p for p in all_particles if p.alpha > 0]
        if all_particles:
            collide_particles(all_particles)
            if state == 'playing':
                push_particles_from_ball(all_particles, pos_t, BALL_RADIUS, vel_t)
                push_particles_from_ball(all_particles, pos_b, BALL_RADIUS, vel_b)

        # ── Dibujo ──────────────────────────────────────────────────────────
        surface.blit(pitch, (0, 0))

        if state == 'final':
            draw_final(surface, fonts, country_t, country_b, score_t, score_b, final_timer)
        else:
            surface.blit(inner_dark, (0, 0))
            net.draw(surface)
            draw_ring(surface, rotation)

            if goal_flash > 0:
                draw_glow(surface, (int(flash_pos[0]), int(flash_pos[1])),
                          90, flash_col, layers=16, max_alpha=int(150 * goal_flash / 14))

            for p in all_particles:
                p.draw(surface)

            draw_ball(surface, country_t, pos_t, BALL_RADIUS)
            draw_ball(surface, country_b, pos_b, BALL_RADIUS)

            draw_scoreboard(surface, fonts, country_t, country_b,
                            score_t, score_b, minute, pulse_t, pulse_b)

            draw_hook(surface, fonts, frame)

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

    print(f"MP4 listo -> {out_mp4}")


if __name__ == "__main__":
    main()
