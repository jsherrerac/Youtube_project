"""
Tema: Spike Melodia - bola que crece y rebota hasta morir en el pico
Duracion objetivo: 30-40 segundos (4 iteraciones + loop perfecto)
Formato: 1080x1920, fondo negro, 60 FPS
Animacion:
  1. Hook text 2s
  2. Bola rebota, crece, acelera; cada rebote toca la siguiente nota de Fur Elise
  3. Al tocar el pico: explosion de bolitas con gravedad y colisiones entre ellas
  4. 4 iteraciones (4 colores); bolitas acumuladas interactuan con pico y bola grande
  5. Fade-out final + nueva bola = loop perfecto
"""

import os
import math
import wave
import random
import subprocess

import pygame
import numpy as np
import imageio_ffmpeg


# ── Constantes ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT     = 1080, 1920
FPS               = 60
SAMPLE_RATE       = 44100
MAX_TOTAL_FRAMES  = FPS * 200   # tope de seguridad: ~3 min

ARENA_CENTER  = np.array([WIDTH / 2.0, HEIGHT / 2.0])
ARENA_RADIUS  = 490
BALL_R0       = 22       # radio inicial
BALL_SPEED0   = 580.0    # velocidad inicial px/s
GROWTH        = 0.16     # +16% radio por rebote de pared
ACCEL_RATE    = 0.10     # +10% velocidad por rebote de pared
MAX_BALL_R    = 160
MAX_SPEED     = 2400.0

SPIKE_LENGTH  = 100      # px desde la pared hacia el centro
SPIKE_WIDTH   = 110      # px de arco de base (esquinas quedan DENTRO del circulo)
SPIKE_OMEGA   = 2 * math.pi / (FPS * 9)  # 1 vuelta cada 9 segundos

GRAVITY       = 280.0    # px/s^2 hacia abajo (particulas)

N_PARTICLES   = 30
PART_R        = 13
PART_DAMP     = 0.993    # amortiguacion por frame

TITLE_FRAMES   = FPS * 2
EXPLODE_FRAMES = FPS // 2
PAUSE_FRAMES   = int(0.3 * FPS)
FADEOUT_FRAMES = FPS     # 1 s de fade-out final

# Paletas pastel neón (color_interior, color_borde_vibrante)
BALL_PALETTES = [
    ((255, 215, 235), (245,  25,  90)),  # rosa neón
    ((220, 195, 255), (155,  20, 255)),  # lila neón
    ((185, 235, 255), (  0, 165, 255)),  # celeste neón
    ((255, 252, 185), (245, 180,   0)),  # amarillo neón
    ((185, 255, 210), (  0, 210,  85)),  # verde neón
]

# Fur Elise - Beethoven (dominio publico desde 1810)
# Cada colision dispara la siguiente nota de la secuencia
_E5, _Ds5 = 659.25, 622.25
_B4, _D5  = 493.88, 587.33
_C5, _A4  = 523.25, 440.00
_C4, _E4  = 261.63, 329.63
_Gs4      = 415.30
_G4, _F5  = 392.00, 698.46
_F4       = 349.23

MELODY = [
    # A1 — primer tema
    _E5, _Ds5, _E5, _Ds5, _E5, _B4, _D5, _C5, _A4,
    _C4, _E4, _A4, _B4,
    _E4, _Gs4, _B4, _C5,
    # A2 — segundo tema (final distinto)
    _E5, _Ds5, _E5, _Ds5, _E5, _B4, _D5, _C5, _A4,
    _C4, _E4, _A4, _B4,
    _E4, _C5, _B4, _A4,
    # B — puente
    _B4, _C5, _D5, _E5,
    _G4, _F5, _E5, _D5,
    _F4, _E5, _D5, _C5,
    _E4, _D5, _C5, _B4,
]

COLOR_BG    = (0,   0,   0)
COLOR_ARENA = (0, 210, 235)
COLOR_SPIKE = (160, 160, 165)   # gris


# ── Audio ─────────────────────────────────────────────────────────────────────

def gen_note(freq, dur=0.65):
    """Campana/piano: armonicos inharmonicos, attack 10ms, decay tipo piano."""
    n   = int(SAMPLE_RATE * dur)
    t   = np.linspace(0, dur, n, endpoint=False)
    atk = np.minimum(t / 0.010, 1.0)
    dec = np.exp(-3.5 * t)
    s   = (np.sin(2*np.pi * freq * 1.000 * t) * 0.50
         + np.sin(2*np.pi * freq * 2.001 * t) * 0.24
         + np.sin(2*np.pi * freq * 3.003 * t) * 0.13
         + np.sin(2*np.pi * freq * 4.007 * t) * 0.07
         + np.sin(2*np.pi * freq * 5.012 * t) * 0.04
         + np.sin(2*np.pi * freq * 6.020 * t) * 0.02)
    return (s * atk * dec * 0.72 * 32767).astype(np.int16)


def gen_explosion(dur=0.45):
    """Poof suave: ruido blanco filtrado con decay."""
    n        = int(SAMPLE_RATE * dur)
    t        = np.linspace(0, dur, n, endpoint=False)
    noise    = np.random.randn(n)
    filtered = np.convolve(noise, np.ones(60)/60, mode='same')
    env      = np.exp(-8.0 * t)
    return (filtered * env * 0.65 * 32767).astype(np.int16)


def mix_audio(events, total_frames):
    total_samples = int(total_frames / FPS * SAMPLE_RATE) + SAMPLE_RATE
    buf = np.zeros(total_samples, dtype=np.float64)
    for fn, stype, param in events:
        pos = int(fn * SAMPLE_RATE / FPS)
        snd = gen_note(param) if stype == 'note' else gen_explosion()
        end = min(pos + len(snd), total_samples)
        buf[pos:end] += snd[:end - pos].astype(np.float64)
    peak = np.max(np.abs(buf))
    if peak > 0:
        buf = buf / peak * 0.90 * 32767
    return buf.astype(np.int16)


# ── Graficos ──────────────────────────────────────────────────────────────────

_surf_cache = {}

def ball_surf(radius, palette):
    """Bola con glow aditivo, volumen 3D descentrado, rim light y highlight.
    Cache por (radius, palette): solo se construye una vez por tamaño único."""
    key = (radius, palette)
    if key in _surf_cache:
        return _surf_cache[key]

    inn, out = palette

    # Surface grande para incluir el glow (hasta 2.2x radio)
    glow_ext = int(radius * 1.25)
    size     = (radius + glow_ext) * 2 + 4
    cx = cy  = size // 2
    surf     = pygame.Surface((size, size), pygame.SRCALPHA)

    # ── 1. GLOW EXTERIOR (capas aditivas, luz derramada sobre fondo negro) ──
    gl = pygame.Surface((size, size), pygame.SRCALPHA)
    for r_fac, alpha in [(1.08, 80), (1.22, 58), (1.40, 38),
                         (1.62, 22), (1.90, 10), (2.20,  4)]:
        gl.fill((0, 0, 0, 0))
        pygame.draw.circle(gl, (*out, alpha), (cx, cy), max(1, int(radius * r_fac)))
        surf.blit(gl, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # ── 2. DEGRADADO INTERNO descentrado (volumen tipo esfera 3D) ────────────
    shadow = tuple(max(0, int(c * 0.45)) for c in out)
    hi     = tuple(min(255, int(inn[i] * 0.20 + 255 * 0.80)) for i in range(3))
    offset = int(radius * 0.28)

    for r in range(radius, 0, -1):
        t = r / radius              # 1 = borde, 0 = centro
        if t > 0.65:
            t2  = (t - 0.65) / 0.35
            col = tuple(int(shadow[i]*t2 + out[i]*(1-t2)) for i in range(3))
        elif t > 0.28:
            t2  = (t - 0.28) / 0.37
            col = tuple(int(out[i]*t2 + inn[i]*(1-t2)) for i in range(3))
        else:
            t2  = t / 0.28
            col = tuple(int(inn[i]*t2 + hi[i]*(1-t2)) for i in range(3))
        shift = offset * (1.0 - t)  # círculos internos se desplazan arriba-izq
        pygame.draw.circle(surf, (*col, 255),
                           (int(cx - shift), int(cy - shift)), r)

    # ── 3. RIM LIGHT: anillo claro en el borde ────────────────────────────────
    rim = tuple(min(255, int(c * 1.5)) for c in inn)
    pygame.draw.circle(surf, (*rim, 55), (cx, cy), radius, 2)

    # ── 4. HIGHLIGHT ESPECULAR: brillo puntual arriba-izquierda ──────────────
    sr = max(2, int(radius * 0.18))
    sx = cx - int(radius * 0.30)
    sy = cy - int(radius * 0.30)
    for k in range(5, 0, -1):
        t = k / 5.0
        pygame.draw.circle(surf, (255, 255, 255, int(230 * t * t)),
                           (sx, sy), max(1, int(sr * t)))

    _surf_cache[key] = surf
    return surf


_part_cache = {}

def part_surf(r, color):
    """Bolita con glow (2 capas) + degradado básico 3D. Cacheada por (r, color)."""
    key = (r, color)
    if key in _part_cache:
        return _part_cache[key]

    gm   = max(r, int(r * 0.90))
    size = (r + gm) * 2 + 4
    cx = cy = size // 2
    s = pygame.Surface((size, size), pygame.SRCALPHA)

    # Glow: 2 capas aditivas
    gl = pygame.Surface((size, size), pygame.SRCALPHA)
    for r_fac, alpha in [(1.55, 50), (2.10, 18)]:
        gl.fill((0, 0, 0, 0))
        pygame.draw.circle(gl, (*color, alpha), (cx, cy), max(1, int(r * r_fac)))
        s.blit(gl, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # Cuerpo: 3 capas descentradas (sombra → color → highlight)
    shadow = tuple(max(0, int(c * 0.50)) for c in color)
    hi     = tuple(min(255, int(c * 0.25 + 255 * 0.75)) for c in color)
    off    = max(1, int(r * 0.28))
    pygame.draw.circle(s, (*shadow, 255), (cx,           cy          ), r)
    pygame.draw.circle(s, (*color,  255), (cx - off//2,  cy - off//2 ), max(1, int(r * 0.78)))
    pygame.draw.circle(s, (*hi,     255), (cx - off,     cy - off    ), max(1, int(r * 0.43)))

    # Mini highlight especular
    pygame.draw.circle(s, (255, 255, 255, 210),
                       (cx - int(r*0.30), cy - int(r*0.30)), max(1, int(r*0.16)))

    _part_cache[key] = s
    return s


def spike_pts(angle):
    """Triangulo del pico. Esquinas sobre el arco para no salirse del circulo."""
    half_arc = math.asin(min(0.999, (SPIKE_WIDTH / 2) / ARENA_RADIUS))
    tip = ARENA_CENTER + np.array([math.cos(angle),           math.sin(angle)])           * (ARENA_RADIUS - SPIKE_LENGTH)
    bl  = ARENA_CENTER + np.array([math.cos(angle - half_arc), math.sin(angle - half_arc)]) * ARENA_RADIUS
    br  = ARENA_CENTER + np.array([math.cos(angle + half_arc), math.sin(angle + half_arc)]) * ARENA_RADIUS
    return tip, bl, br


def draw_scene(surf, arena_layer, spike_angle):
    surf.fill(COLOR_BG)
    surf.blit(arena_layer, (0, 0))
    tip, bl, br = spike_pts(spike_angle)
    pts = [(int(p[0]), int(p[1])) for p in (tip, bl, br)]
    pygame.draw.polygon(surf, COLOR_SPIKE, pts)
    pygame.draw.polygon(surf, (210, 210, 215), pts, 2)


# ── Fisica ────────────────────────────────────────────────────────────────────

def pt_seg_dist(p, a, b):
    ab = b - a; ap = p - a
    d  = np.dot(ab, ab)
    if d < 1e-9:
        return np.linalg.norm(ap)
    return np.linalg.norm(ap - np.clip(np.dot(ap, ab)/d, 0.0, 1.0) * ab)


def spike_hit(pos, r, angle):
    tip, bl, br = spike_pts(angle)
    return min(pt_seg_dist(pos, tip, bl),
               pt_seg_dist(pos, tip, br),
               pt_seg_dist(pos, bl, br)) < r + 4


def wall_bounce(pos, vel, r):
    delta = pos - ARENA_CENTER
    d     = np.linalg.norm(delta)
    if d + r >= ARENA_RADIUS:
        n = (delta / d) if d > 1e-6 else np.array([0., -1.])
        if np.dot(vel, n) > 0:
            vel = vel - 2 * np.dot(vel, n) * n
        pos = ARENA_CENTER + n * (ARENA_RADIUS - r - 1.5)
        return pos, vel, True
    return pos, vel, False


# ── Particulas ────────────────────────────────────────────────────────────────

class Particle:
    __slots__ = ('pos', 'vel', 'color', 'alpha', 'r')

    def __init__(self, pos, vel, color, r):
        self.pos   = pos.astype(float)
        self.vel   = vel.astype(float)
        self.color = color
        self.alpha = 255.0
        self.r     = r

    def step(self, dt):
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

    def draw(self, surf):
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


def collide_particles(particles):
    """Colisiones entre particulas con radio variable. Separacion + rebote suave."""
    n = len(particles)
    for i in range(n):
        pi  = particles[i]
        pxi = float(pi.pos[0]);  pyi = float(pi.pos[1])
        ri  = float(pi.r)
        for j in range(i + 1, n):
            pj   = particles[j]
            dx   = float(pj.pos[0]) - pxi
            dy   = float(pj.pos[1]) - pyi
            min_d = ri + float(pj.r)
            d2   = dx*dx + dy*dy
            if d2 < min_d*min_d and d2 > 0.01:
                d   = d2 ** 0.5
                nx  = dx / d;  ny = dy / d
                sep = (min_d - d) * 0.5 + 0.5
                pi.pos[0] -= nx * sep;  pi.pos[1] -= ny * sep
                pj.pos[0] += nx * sep;  pj.pos[1] += ny * sep
                pxi = float(pi.pos[0]);  pyi = float(pi.pos[1])
                rel = (float(pi.vel[0]) - float(pj.vel[0])) * nx \
                    + (float(pi.vel[1]) - float(pj.vel[1])) * ny
                if rel > 0:
                    imp = rel * 0.20
                    pi.vel[0] -= imp * nx;  pi.vel[1] -= imp * ny
                    pj.vel[0] += imp * nx;  pj.vel[1] += imp * ny


def push_particles_from_ball(particles, ball_pos, ball_r, ball_vel):
    """La bola grande esparce las bolitas que toca."""
    bvx, bvy = float(ball_vel[0]), float(ball_vel[1])
    bpx, bpy = float(ball_pos[0]), float(ball_pos[1])
    for p in particles:
        dx    = float(p.pos[0]) - bpx
        dy    = float(p.pos[1]) - bpy
        min_d = float(ball_r + p.r + 2)
        d2    = dx*dx + dy*dy
        if d2 < min_d*min_d and d2 > 0.01:
            d  = d2 ** 0.5
            nx = dx / d;  ny = dy / d
            p.pos[0] += nx * (min_d - d + 1.0)
            p.pos[1] += ny * (min_d - d + 1.0)
            push = max(bvx*nx + bvy*ny, 0.0) * 0.7 + 160.0
            cur  = float(p.vel[0])*nx + float(p.vel[1])*ny
            if cur < push:
                diff = push - cur
                p.vel[0] += nx * diff
                p.vel[1] += ny * diff


def bounce_particles_on_spike(particles, spike_angle):
    """Particulas rebotan en el pico. Normales siempre hacia AFUERA del triangulo."""
    tip, bl, br = spike_pts(spike_angle)
    # Centroide para detectar lado interior/exterior
    cx = (float(tip[0]) + float(bl[0]) + float(br[0])) / 3.0
    cy = (float(tip[1]) + float(bl[1]) + float(br[1])) / 3.0
    edges = [(tip, bl), (tip, br), (bl, br)]
    for p in particles:
        pr = float(p.r)
        for a, b in edges:
            abx = float(b[0] - a[0]);  aby = float(b[1] - a[1])
            d2  = abx*abx + aby*aby
            if d2 < 1e-9:
                continue
            apx = float(p.pos[0] - a[0]);  apy = float(p.pos[1] - a[1])
            t   = max(0.0, min(1.0, (apx*abx + apy*aby) / d2))
            qx  = float(a[0]) + t * abx;  qy = float(a[1]) + t * aby
            dx  = float(p.pos[0]) - qx;  dy = float(p.pos[1]) - qy
            dist2 = dx*dx + dy*dy
            if dist2 < pr*pr and dist2 > 0.0001:
                dist = dist2 ** 0.5
                nx = dx/dist;  ny = dy/dist
                # Verificar que el normal apunta AFUERA (lejos del centroide)
                if nx*(cx - qx) + ny*(cy - qy) > 0:
                    nx = -nx;  ny = -ny
                push = pr - dist + 1.0
                p.pos[0] += nx * push;  p.pos[1] += ny * push
                vn = float(p.vel[0])*nx + float(p.vel[1])*ny
                if vn < 0:
                    p.vel[0] -= 1.6 * vn * nx
                    p.vel[1] -= 1.6 * vn * ny


def spawn_explosion(pos, palette, ball_r):
    """Cuanto más grande muere la bola, más grandes son sus particulas."""
    t      = (ball_r - BALL_R0) / max(1, MAX_BALL_R - BALL_R0)
    part_r = max(7, min(26, int(7 + 19 * t)))   # 7px (bola chica) → 26px (bola max)
    _, outer = palette
    parts = []
    for _ in range(N_PARTICLES):
        ang = random.uniform(0, 2*math.pi)
        spd = random.uniform(100, 680)
        vel = np.array([math.cos(ang), math.sin(ang)]) * spd
        col = tuple(min(255, max(0, outer[i] + random.randint(-28, 28)))
                    for i in range(3))
        parts.append(Particle(pos.copy(), vel, col, part_r))
    return parts


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    font_hook = pygame.font.SysFont("Arial", 48, bold=True)

    screen = pygame.Surface((WIDTH, HEIGHT))

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir  = os.path.join(base_dir, "output")
    os.makedirs(out_dir, exist_ok=True)

    temp_vid = os.path.join(out_dir, "_tmp_video.mp4")
    temp_wav = os.path.join(out_dir, "_tmp_audio.wav")
    out_mp4  = os.path.join(out_dir, "spike_melodia.mp4")

    # Writer de video (imageio_ffmpeg bundled, sin ffmpeg del sistema)
    vid_gen = imageio_ffmpeg.write_frames(
        temp_vid, (WIDTH, HEIGHT),
        fps=FPS,
        pix_fmt_in='rgb24',
        pix_fmt_out='yuv420p',
        codec='libx264',
        quality=None,
        macro_block_size=1,
        output_params=['-crf', '18', '-preset', 'fast'],
        ffmpeg_log_level='quiet',
    )
    vid_gen.send(None)  # arrancar el generador

    def push(surf):
        arr = pygame.surfarray.array3d(surf)
        vid_gen.send(np.ascontiguousarray(arr.transpose(1, 0, 2)).tobytes())

    # Layer estatico de la arena
    arena_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy = int(ARENA_CENTER[0]), int(ARENA_CENTER[1])
    for i in range(3, 0, -1):
        pygame.draw.circle(arena_layer, (*COLOR_ARENA, 10),
                           (cx, cy), ARENA_RADIUS + i*5, 10)
    pygame.draw.circle(arena_layer, (*COLOR_ARENA, 205),
                       (cx, cy), ARENA_RADIUS, 3)

    # Estado inicial de la bola (offset del centro para romper simetria)
    INIT_POS = ARENA_CENTER + np.array([40.0, 90.0])
    _v       = np.array([310.0, 370.0])
    INIT_VEL = _v / np.linalg.norm(_v) * BALL_SPEED0

    all_particles = []
    sound_events  = []
    frame         = 0
    note_idx      = 0
    spike_angle   = -math.pi / 2 + 0.4

    # ── Hook text (2 s) ───────────────────────────────────────────────────────
    hook = font_hook.render("Can you get the song?", True, (255, 235, 70))

    print("Renderizando titulo...")
    for tf in range(TITLE_FRAMES):
        spike_angle += SPIKE_OMEGA
        draw_scene(screen, arena_layer, spike_angle)
        bs = ball_surf(BALL_R0, BALL_PALETTES[0])
        screen.blit(bs, bs.get_rect(center=(int(INIT_POS[0]), int(INIT_POS[1]))))

        fade = 255 if tf < TITLE_FRAMES - 20 else int(255*(TITLE_FRAMES-tf)/20)
        tmp = pygame.Surface(hook.get_size(), pygame.SRCALPHA)
        tmp.blit(hook, (0, 0))
        tmp.set_alpha(fade)
        screen.blit(tmp, hook.get_rect(
            center=(WIDTH//2, int(ARENA_CENTER[1]) - ARENA_RADIUS - 80)))
        push(screen)
        frame += 1

    # ── 4 iteraciones ────────────────────────────────────────────────────────
    print("Renderizando simulacion...")

    for iteration in range(4):
        palette  = BALL_PALETTES[iteration]
        ball_pos = INIT_POS.copy()
        ball_vel = INIT_VEL.copy()
        ball_r   = BALL_R0
        alive    = True
        state    = 'playing'
        timer    = 0
        bounces  = 0

        while True:
            dt = 1.0 / FPS

            spike_angle += SPIKE_OMEGA   # rotar el pico cada frame

            # Logica
            if state == 'playing':
                ball_pos += ball_vel * dt

                if spike_hit(ball_pos, ball_r, spike_angle):
                    # Muerte — radio de particulas proporcional al tamaño de la bola
                    new_parts = spawn_explosion(ball_pos, palette, ball_r)
                    all_particles.extend(new_parts)
                    sound_events.append((frame, 'explosion', None))
                    alive = False
                    state = 'exploding'
                    timer = EXPLODE_FRAMES
                else:
                    ball_pos, ball_vel, hit = wall_bounce(ball_pos, ball_vel, ball_r)
                    if hit:
                        bounces += 1
                        ball_r   = min(int(ball_r * (1 + GROWTH)), MAX_BALL_R)
                        spd      = np.linalg.norm(ball_vel)
                        ball_vel = ball_vel / spd * min(spd * (1 + ACCEL_RATE), MAX_SPEED)
                        sound_events.append((frame, 'note', MELODY[note_idx % len(MELODY)]))
                        note_idx += 1

            elif state == 'exploding':
                timer -= 1
                if timer <= 0:
                    state = 'pausing'
                    timer = PAUSE_FRAMES

            elif state == 'pausing':
                timer -= 1
                if timer <= 0:
                    break

            # Actualizar particulas: step + multiple passes de colision
            for p in all_particles:
                p.step(dt)
            if all_particles:
                for _ in range(3):   # 3 passes: soluciona el apilamiento
                    bounce_particles_on_spike(all_particles, spike_angle)
                    collide_particles(all_particles)
            # La bola grande esparce las bolitas que toca
            if alive and all_particles:
                push_particles_from_ball(all_particles, ball_pos, ball_r, ball_vel)

            # Render
            draw_scene(screen, arena_layer, spike_angle)
            for p in all_particles:
                p.draw(screen)
            if alive:
                bs = ball_surf(ball_r, palette)
                screen.blit(bs, bs.get_rect(
                    center=(int(ball_pos[0]), int(ball_pos[1]))))

            push(screen)
            frame += 1

            if frame > MAX_TOTAL_FRAMES:
                break

        print(f"  Iter {iteration+1}: {bounces} rebotes | {frame/FPS:.1f}s")
        if frame > MAX_TOTAL_FRAMES:
            break

    # ── Fade-out final (1 s) ─────────────────────────────────────────────────
    print("Renderizando fade-out...")
    for tf in range(FADEOUT_FRAMES):
        spike_angle += SPIKE_OMEGA
        progress = (tf + 1) / FADEOUT_FRAMES
        fade_a   = 255.0 * (1.0 - progress)

        for p in all_particles:
            p.step(1.0 / FPS)
            p.alpha = fade_a
        if all_particles:
            for _ in range(3):
                bounce_particles_on_spike(all_particles, spike_angle)
                collide_particles(all_particles)

        draw_scene(screen, arena_layer, spike_angle)
        for p in all_particles:
            p.draw(screen)

        # La nueva bola (rosa) aparece en la segunda mitad del fade
        if progress > 0.5:
            ball_a = int(255 * (progress - 0.5) / 0.5)
            bs  = ball_surf(BALL_R0, BALL_PALETTES[0])
            tmp = pygame.Surface(bs.get_size(), pygame.SRCALPHA)
            tmp.blit(bs, (0, 0))
            tmp.set_alpha(ball_a)
            screen.blit(tmp, tmp.get_rect(
                center=(int(INIT_POS[0]), int(INIT_POS[1]))))

        push(screen)
        frame += 1

    # Frame de cierre (igual al primer frame jugable = loop perfecto)
    spike_angle += SPIKE_OMEGA
    draw_scene(screen, arena_layer, spike_angle)
    bs = ball_surf(BALL_R0, BALL_PALETTES[0])
    screen.blit(bs, bs.get_rect(center=(int(INIT_POS[0]), int(INIT_POS[1]))))
    push(screen)
    frame += 1

    vid_gen.close()
    total_frames = frame
    print(f"\nVideo: {total_frames} frames ({total_frames/FPS:.1f}s). Generando audio...")

    # WAV
    pcm = mix_audio(sound_events, total_frames)
    with wave.open(temp_wav, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())

    # Combinar video + audio con ffmpeg bundled de imageio_ffmpeg
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

    print(f"MP4 listo -> {out_mp4}")
    pygame.quit()


if __name__ == '__main__':
    main()
