"""
Sonidos procedurales generados con numpy — no requieren archivos .wav.
Retorna pygame.mixer.Sound listos para play().
"""

import numpy as np
import pygame

SR = 44100  # sample rate


def make_eat_sound() -> pygame.mixer.Sound:
    """Bloop ascendente satisfactorio — pitch sube de 500 a 1400 Hz."""
    dur = 0.11
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Frecuencia que escala con t^0.6 para subir rápido al inicio
    freq = 500 + 900 * (t / dur) ** 0.6
    phase = np.cumsum(freq / SR) * 2 * np.pi
    tone = 0.48 * np.sin(phase) * np.exp(-t * 22)
    # Segunda armónica sutil para cuerpo
    tone += 0.12 * np.sin(phase * 2) * np.exp(-t * 35)
    return _to_sound(tone)


def make_wall_sound() -> pygame.mixer.Sound:
    """
    'Bong' resonante satisfactorio: tono que baja de ~300 a 80 Hz + un cuerpo
    bajo que da punch. Como golpear una campana o un balón inflado fuerte.
    """
    dur = 0.22
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Tono principal: frecuencia que cae exponencialmente (efecto 'pow')
    freq = 280 * np.exp(-t * 8) + 80   # va de 360 Hz a ~80 Hz
    phase = np.cumsum(freq / SR) * 2 * np.pi
    body = np.sin(phase) * np.exp(-t * 14)
    # Segunda parcial inarmónica para textura metálica/satisfactoria
    freq2 = freq * 2.3
    phase2 = np.cumsum(freq2 / SR) * 2 * np.pi
    ring = 0.35 * np.sin(phase2) * np.exp(-t * 22)
    # Transiente de ataque muy corto (da snap)
    snap_len = int(SR * 0.008)
    snap = np.zeros(len(t))
    snap[:snap_len] = np.random.default_rng(11).standard_normal(snap_len) * np.exp(
        -np.arange(snap_len) / snap_len * 8
    )
    tone = 0.55 * (body + ring) + 0.25 * snap
    return _to_sound(tone.astype(np.float32))


def make_melody_note(freq: float, duration: float = 0.18) -> pygame.mixer.Sound:
    """Nota de melodía: sinusoide con ataque/decay suaves, idéntica a audio.py."""
    t = np.linspace(0, duration, int(SR * duration), endpoint=False)
    tone = 0.50 * np.sin(2 * np.pi * freq * t)
    tone += 0.15 * np.sin(2 * np.pi * freq * 2 * t)  # 2a armónica
    n_att = int(SR * 0.012)
    n_rel = int(SR * 0.05)
    env = np.ones(len(t))
    env[:n_att] = np.linspace(0, 1, n_att)
    env[-n_rel:] = np.linspace(1, 0, n_rel)
    return _to_sound((tone * env).astype(np.float32))


def _to_sound(arr: np.ndarray) -> pygame.mixer.Sound:
    """Convierte array float32 mono a pygame.mixer.Sound estéreo."""
    pcm = (arr * 32767).astype(np.int16)
    stereo = np.column_stack([pcm, pcm])  # pygame mixer espera 2 canales
    return pygame.mixer.Sound(buffer=stereo.tobytes())
