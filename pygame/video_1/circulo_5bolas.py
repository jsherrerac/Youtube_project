"""
Tema: 5 bolas en arena circular - Primer Short del canal
Duración objetivo: 30-90 segundos (termina cuando queda 1 bola)
Animación paso a paso:
  1. 5 bolas de colores rebotan dentro de un círculo grande
  2. Cada colisión bola-bola resta una vida a ambas (número visible en la bola)
  3. Al llegar a 0 vidas, la bola explota con un pop
  4. La última bola en pie gana y se muestra con brillo pulsante
"""

import os
import glob
import wave
import subprocess

import pygame
import numpy as np


def find_ffmpeg():
    """Busca ffmpeg en PATH y en ubicaciones comunes de WinGet/Chocolatey."""
    # 1. Intentar directamente (si está en PATH)
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return 'ffmpeg'
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # 2. Buscar en WinGet
    pattern = os.path.expandvars(
        r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\**\ffmpeg.exe'
    )
    matches = glob.glob(pattern, recursive=True)
    if matches:
        return matches[0]

    # 3. Buscar en rutas comunes
    candidates = [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c

    raise FileNotFoundError(
        "No se encontró ffmpeg. Agrégalo al PATH o instálalo con: winget install Gyan.FFmpeg"
    )


FFMPEG = find_ffmpeg()


# ── Constantes ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT   = 1080, 1920
FPS             = 60
SAMPLE_RATE     = 44100
MAX_FRAMES      = FPS * 150          # tope de seguridad: 2.5 min

ARENA_CENTER    = np.array([WIDTH / 2.0, HEIGHT / 2.0])
ARENA_RADIUS    = 500
BALL_RADIUS     = 48
MIN_DIST        = BALL_RADIUS * 2
MAX_SPEED       = 1150
ACCEL           = 1.0008             # aceleración sutil por frame
TRAIL_LEN       = 10
COOLDOWN_FRAMES = int(0.2 * FPS)     # 200 ms de debounce entre vidas
WINNER_FRAMES   = FPS * 3            # 3 s de pantalla de ganadora
TITLE_FRAMES    = FPS * 2            # 2 s de título

COLOR_BG    = (0, 0, 0)
COLOR_ARENA = (200, 235, 255)

BALL_COLORS = [
    (  0, 225, 255),   # cian
    (255,   0, 200),   # magenta
    (255, 220,   0),   # amarillo
    (  0, 255, 110),   # verde
    (255, 120,   0),   # naranja
]

INITIAL_OFFSETS = [
    np.array([   0.0, -280.0]),
    np.array([ 240.0,  -90.0]),
    np.array([ 140.0,  240.0]),
    np.array([-140.0,  240.0]),
    np.array([-240.0,  -90.0]),
]

INITIAL_VELS = [
    np.array([ 430.0,  290.0]),
    np.array([-290.0,  410.0]),
    np.array([ 350.0, -245.0]),
    np.array([-410.0, -290.0]),
    np.array([ 135.0, -470.0]),
]

PENTATONIC_HZ = [261.63, 293.66, 329.63, 392.00, 440.00,
                 523.25, 587.33, 659.25, 783.99, 880.00]


# ── Síntesis de sonido ────────────────────────────────────────────────────────

def gen_bell(freq, dur=0.45):
    """Campana/marimba con armónicos y decay para rebote en pared."""
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    s = (np.sin(2 * np.pi * freq       * t) * 0.55
       + np.sin(2 * np.pi * freq * 2.0 * t) * 0.28
       + np.sin(2 * np.pi * freq * 3.0 * t) * 0.12
       + np.sin(2 * np.pi * freq * 4.1 * t) * 0.05)
    env = np.exp(-7.0 * t / dur)
    return (s * env * 0.72 * 32767).astype(np.int16)


def gen_click(dur=0.09):
    """Click seco para colisión bola-bola (fallback si no hay archivo)."""
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    s = (np.sin(2 * np.pi *  780.0 * t) * 0.7
       + np.sin(2 * np.pi * 1200.0 * t) * 0.3)
    env = np.exp(-35.0 * t)
    return (s * env * 0.85 * 32767).astype(np.int16)


def make_collision_sound(mp3_path):
    """
    Carga el MP3 y lo transforma tanto que no dispara ContentID:
      - Sube el pitch ~5 semitonos acelerando el audio (1.34x)
      - Recorta a 0.5 s para que quede punchy
      - Reverb Schroeder (3 comb filters paralelos)
      - Echo corto al 30%
    Retorna array int16 o None si el archivo no existe.
    """
    if not os.path.isfile(mp3_path):
        return None

    # Decodificar MP3 → PCM mono int16 via ffmpeg
    proc = subprocess.Popen(
        [FFMPEG, '-i', mp3_path,
         '-f', 's16le', '-ac', '1', '-ar', str(SAMPLE_RATE), 'pipe:1'],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    raw = proc.stdout.read()
    proc.wait()

    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32767.0

    # 1. Subir pitch ~5 semitonos comprimiendo en tiempo (más rápido + más agudo)
    factor  = 2 ** (5 / 12)          # ≈ 1.335
    new_len = int(len(audio) / factor)
    audio   = np.interp(np.linspace(0, len(audio) - 1, new_len),
                        np.arange(len(audio)), audio)

    # 2. Recortar a 0.5 s
    audio = audio[:int(SAMPLE_RATE * 0.5)]

    # 3. Reverb: 3 comb filters con diferentes delays/ganancias
    def comb(sig, delay, gain):
        out = sig.copy()
        for i in range(delay, len(out)):
            out[i] += out[i - delay] * gain
        return out

    reverb = (comb(audio, 1800, 0.52)
            + comb(audio, 2300, 0.48)
            + comb(audio, 2750, 0.44)) / 3.0
    audio = audio * 0.58 + reverb * 0.42

    # 4. Echo corto (55 ms al 30%)
    d = int(0.055 * SAMPLE_RATE)
    echo       = np.zeros_like(audio)
    echo[d:]   = audio[:-d] * 0.30
    audio     += echo

    # 5. Normalizar al 80 %
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.80

    return (audio * 32767).astype(np.int16)


def gen_pop(dur=0.35):
    """Barrido descendente para eliminación de bola."""
    n      = int(SAMPLE_RATE * dur)
    t      = np.linspace(0, dur, n, endpoint=False)
    f_inst = 600.0 * np.exp(-5.0 * t)
    phase  = 2 * np.pi * np.cumsum(f_inst) / SAMPLE_RATE
    env    = np.exp(-4.5 * t)
    return (np.sin(phase) * env * 0.9 * 32767).astype(np.int16)


def mix_audio(events, total_frames, collision_snd=None):
    """Mezcla todos los eventos de sonido en un buffer PCM int16 mono."""
    total_samples = int(total_frames / FPS * SAMPLE_RATE) + SAMPLE_RATE
    buf = np.zeros(total_samples, dtype=np.float64)

    for frame_num, stype, param in events:
        pos = int(frame_num * SAMPLE_RATE / FPS)
        if stype == 'wall':
            snd = gen_bell(PENTATONIC_HZ[param % len(PENTATONIC_HZ)])
        elif stype == 'collision':
            snd = collision_snd if collision_snd is not None else gen_click()
        elif stype == 'pop':
            snd = gen_pop()
        else:
            continue
        end = min(pos + len(snd), total_samples)
        buf[pos:end] += snd[:end - pos].astype(np.float64)

    peak = np.max(np.abs(buf))
    if peak > 0:
        buf = buf / peak * 0.92 * 32767
    return buf.astype(np.int16)


# ── Dibujo ────────────────────────────────────────────────────────────────────

def draw_glow(surf, color, pos, radius, layers=4, max_extra=20, base_alpha=55):
    size = (radius + max_extra) * 2 + 4
    tmp  = pygame.Surface((size, size), pygame.SRCALPHA)
    c    = size // 2
    for i in range(layers, 0, -1):
        r_extra = int(max_extra * i / layers)
        alpha   = int(base_alpha * (layers - i + 1) / layers)
        pygame.draw.circle(tmp, (*color, alpha), (c, c), radius + r_extra)
    surf.blit(tmp, (int(pos[0]) - c, int(pos[1]) - c))


def draw_ball(surf, ball, font):
    x, y = int(ball.pos[0]), int(ball.pos[1])
    r    = BALL_RADIUS
    col  = ball.color

    # Estela
    n_trail = len(ball.trail)
    for k, tpos in enumerate(ball.trail):
        alpha   = int(110 * (k + 1) / n_trail)
        trail_r = max(4, int(r * 0.5 * (k + 1) / n_trail))
        tmp = pygame.Surface((trail_r * 2 + 2, trail_r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(tmp, (*col, alpha), (trail_r + 1, trail_r + 1), trail_r)
        surf.blit(tmp, (int(tpos[0]) - trail_r - 1, int(tpos[1]) - trail_r - 1))

    # Cuerpo (sin glow ni brillo)
    pygame.draw.circle(surf, col, (x, y), r)

    # Número de vidas
    label = font.render(str(ball.lives), True, (0, 0, 0))
    surf.blit(label, label.get_rect(center=(x, y)))


# ── Clase Ball ────────────────────────────────────────────────────────────────

class Ball:
    def __init__(self, idx, offset, vel, color):
        self.idx       = idx
        self.pos       = ARENA_CENTER + offset.astype(float)
        self.vel       = vel.astype(float)
        self.color     = color
        self.lives     = 5
        self.alive     = True
        self.trail     = []
        self.cooldowns = {}   # {other_idx: frames_remaining}

    def step(self, dt):
        speed = np.linalg.norm(self.vel)
        if speed > 0:
            self.vel = self.vel / speed * min(speed * ACCEL, MAX_SPEED)
        self.pos += self.vel * dt

        self.trail.append(self.pos.copy())
        if len(self.trail) > TRAIL_LEN:
            self.trail.pop(0)

        for k in list(self.cooldowns):
            self.cooldowns[k] -= 1
            if self.cooldowns[k] <= 0:
                del self.cooldowns[k]

    def bounce_wall(self):
        """Rebota contra la pared circular. Retorna True si colisionó."""
        delta = self.pos - ARENA_CENTER
        d     = np.linalg.norm(delta)
        if d + BALL_RADIUS >= ARENA_RADIUS:
            normal = (delta / d) if d > 1e-6 else np.array([1.0, 0.0])
            if np.dot(self.vel, normal) > 0:
                self.vel -= 2 * np.dot(self.vel, normal) * normal
            self.pos = ARENA_CENTER + normal * (ARENA_RADIUS - BALL_RADIUS - 1.5)
            return True
        return False


def resolve_collision(b1, b2):
    """
    Rebote elástico 2D de igual masa + separación posicional.
    Retorna True si hubo colisión.
    """
    diff = b2.pos - b1.pos
    dist = np.linalg.norm(diff)

    if dist >= MIN_DIST:
        return False

    if dist < 1e-6:
        angle = np.random.uniform(0, 2 * np.pi)
        diff  = np.array([np.cos(angle), np.sin(angle)])
        dist  = 1.0

    normal  = diff / dist
    overlap = MIN_DIST - dist

    b1.pos -= normal * (overlap / 2 + 0.6)
    b2.pos += normal * (overlap / 2 + 0.6)

    rel = np.dot(b1.vel - b2.vel, normal)
    if rel > 0:
        b1.vel -= rel * normal
        b2.vel += rel * normal

    # Boost leve tras colisión
    for b in (b1, b2):
        speed = np.linalg.norm(b.vel)
        if speed > 0:
            b.vel = b.vel / speed * min(speed * 1.06, MAX_SPEED)

    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    font       = pygame.font.SysFont("Arial", 38, bold=True)
    font_big   = pygame.font.SysFont("Arial", 96, bold=True)
    font_title = pygame.font.SysFont("Arial", 90, bold=True)

    screen = pygame.Surface((WIDTH, HEIGHT))

    base_dir   = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    temp_vid = os.path.join(output_dir, "_temp_video.mp4")
    temp_wav = os.path.join(output_dir, "_temp_audio.wav")
    out_mp4  = os.path.join(output_dir, "circulo_5bolas.mp4")

    # Pipe de video hacia ffmpeg
    ffmpeg_vid = subprocess.Popen([
        FFMPEG, '-y',
        '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{WIDTH}x{HEIGHT}', '-pix_fmt', 'rgb24',
        '-r', str(FPS), '-i', 'pipe:0',
        '-vcodec', 'libx264', '-pix_fmt', 'yuv420p',
        '-preset', 'fast', '-crf', '18',
        temp_vid,
    ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    # Layer estático de la arena (se renderiza una vez)
    arena_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy = int(ARENA_CENTER[0]), int(ARENA_CENTER[1])
    for i in range(4, 0, -1):
        pygame.draw.circle(arena_layer, (100, 180, 255, 8 + i * 4),
                           (cx, cy), ARENA_RADIUS + i * 7, 14)
    pygame.draw.circle(arena_layer, (*COLOR_ARENA, 255), (cx, cy), ARENA_RADIUS, 6)

    balls = [Ball(i, INITIAL_OFFSETS[i], INITIAL_VELS[i], BALL_COLORS[i])
             for i in range(5)]

    sound_events     = []
    flashes          = []   # [pos, frames_total, frames_left, color]
    wall_note        = 0
    frame            = 0
    winner           = None
    winner_frame_cnt = 0
    dt               = 1.0 / FPS

    # Cargar y procesar sonido de colisión bola-bola
    mp3_path      = os.path.join(base_dir, "Voicy_Roblox Death.mp3")
    collision_snd = make_collision_sound(mp3_path)
    if collision_snd is not None:
        print("Sonido personalizado cargado y procesado.")
    else:
        print("Sonido personalizado no encontrado, usando fallback.")

    print("Renderizando... (puede tardar 1-3 minutos)")

    # ── Pantalla de título (2 segundos) ───────────────────────────────────────
    line1 = font_title.render("Which ball", True, (255, 255, 255))
    line2 = font_title.render("will win?",  True, (255, 220, 50))
    for _ in range(TITLE_FRAMES):
        screen.fill(COLOR_BG)
        screen.blit(arena_layer, (0, 0))

        # Bolas estáticas en posición inicial
        for b in balls:
            bx, by = int(b.pos[0]), int(b.pos[1])
            pygame.draw.circle(screen, b.color, (bx, by), BALL_RADIUS)
            lbl = font.render(str(b.lives), True, (0, 0, 0))
            screen.blit(lbl, lbl.get_rect(center=(bx, by)))

        # Título centrado en el espacio sobre la arena
        screen.blit(line1, line1.get_rect(center=(WIDTH // 2, 185)))
        screen.blit(line2, line2.get_rect(center=(WIDTH // 2, 295)))

        arr = pygame.surfarray.array3d(screen)
        ffmpeg_vid.stdin.write(np.ascontiguousarray(arr.transpose(1, 0, 2)).tobytes())
        frame += 1

    while frame < MAX_FRAMES:

        # ── Pantalla de ganadora ──────────────────────────────────────────────
        if winner is not None:
            winner_frame_cnt += 1
            screen.fill(COLOR_BG)
            screen.blit(arena_layer, (0, 0))

            pulse = 1.0 + 0.18 * np.sin(winner_frame_cnt * 0.18)
            wr    = int(BALL_RADIUS * pulse)
            wx, wy = int(winner.pos[0]), int(winner.pos[1])

            draw_glow(screen, winner.color, winner.pos, wr,
                      layers=6, max_extra=45, base_alpha=90)
            pygame.draw.circle(screen, winner.color, (wx, wy), wr)
            lbl = font.render(str(winner.lives), True, (0, 0, 0))
            screen.blit(lbl, lbl.get_rect(center=(wx, wy)))

            wtxt = font_big.render("WINNER!", True, winner.color)
            screen.blit(wtxt, wtxt.get_rect(
                center=(WIDTH // 2, int(ARENA_CENTER[1]) - ARENA_RADIUS - 90)))

            arr = pygame.surfarray.array3d(screen)
            ffmpeg_vid.stdin.write(
                np.ascontiguousarray(arr.transpose(1, 0, 2)).tobytes())
            frame += 1

            if winner_frame_cnt >= WINNER_FRAMES:
                break
            continue

        # ── Física ───────────────────────────────────────────────────────────
        alive = [b for b in balls if b.alive]

        for b in alive:
            b.step(dt)

        for b in alive:
            if b.bounce_wall():
                sound_events.append((frame, 'wall', wall_note))
                wall_note += 1

        for i in range(len(alive)):
            for j in range(i + 1, len(alive)):
                b1, b2 = alive[i], alive[j]
                if resolve_collision(b1, b2):
                    mid = (b1.pos + b2.pos) / 2
                    flashes.append([mid.copy(), 20, 20, (255, 255, 255)])
                    sound_events.append((frame, 'collision', None))
                    if b2.idx not in b1.cooldowns:
                        b1.lives -= 1
                        b2.lives -= 1
                        b1.cooldowns[b2.idx] = COOLDOWN_FRAMES
                        b2.cooldowns[b1.idx] = COOLDOWN_FRAMES

        for b in alive:
            if b.lives <= 0 and b.alive:
                b.alive = False
                flashes.append([b.pos.copy(), 35, 35, b.color])
                sound_events.append((frame, 'pop', None))

        alive = [b for b in balls if b.alive]

        if len(alive) == 1 and winner is None:
            winner = alive[0]
        elif len(alive) == 0:
            break

        # ── Dibujo ───────────────────────────────────────────────────────────
        screen.fill(COLOR_BG)
        screen.blit(arena_layer, (0, 0))

        for b in alive:
            draw_ball(screen, b, font)

        for f in flashes:
            pos, t_max, t_left, color = f[0], f[1], f[2], f[3]
            progress = t_left / t_max
            alpha    = int(255 * progress)
            r_flash  = int(BALL_RADIUS * 1.6 * (1 - progress) + 10)
            tmp = pygame.Surface((r_flash * 2 + 4, r_flash * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(tmp, (*color, alpha),
                               (r_flash + 2, r_flash + 2), r_flash)
            screen.blit(tmp, (int(pos[0]) - r_flash - 2, int(pos[1]) - r_flash - 2))
            f[2] -= 1
        flashes = [f for f in flashes if f[2] > 0]

        arr = pygame.surfarray.array3d(screen)
        ffmpeg_vid.stdin.write(
            np.ascontiguousarray(arr.transpose(1, 0, 2)).tobytes())

        if frame % FPS == 0:
            print(f"  t={frame // FPS:3d}s  |  bolas vivas: {len(alive)}")

        frame += 1

    # ── Cerrar video ──────────────────────────────────────────────────────────
    ffmpeg_vid.stdin.close()
    ffmpeg_vid.wait()
    total_frames = frame
    print(f"\nVideo listo ({total_frames} frames). Generando audio...")

    # ── Generar WAV ───────────────────────────────────────────────────────────
    pcm = mix_audio(sound_events, total_frames, collision_snd)
    with wave.open(temp_wav, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())

    print("Audio listo. Combinando con ffmpeg...")

    # ── Unir video + audio ────────────────────────────────────────────────────
    subprocess.run([
        FFMPEG, '-y',
        '-i', temp_vid,
        '-i', temp_wav,
        '-c:v', 'copy',
        '-c:a', 'aac', '-b:a', '192k',
        '-shortest',
        out_mp4,
    ], stderr=subprocess.DEVNULL)

    for tmp_path in (temp_vid, temp_wav):
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    winner_str = (f"bola {winner.idx}  RGB{winner.color}"
                  if winner else "ninguna (empate)")
    print(f"\nMP4 listo -> {out_mp4}")
    print(f"Ganadora  -> {winner_str}")

    pygame.quit()


if __name__ == '__main__':
    main()
