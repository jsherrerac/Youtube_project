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
    """Click mecánico — transiente de ruido + pequeño thump, como switch de teclado."""
    dur = 0.055
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    rng = np.random.default_rng(7)
    # Click: ruido blanco con decay muy rápido
    click = rng.standard_normal(len(t)) * np.exp(-t * 150)
    # Thump: onda baja que da cuerpo al golpe
    thump = 0.5 * np.sin(2 * np.pi * 120 * t) * np.exp(-t * 90)
    tone = 0.38 * (click + thump)
    return _to_sound(tone)


def _to_sound(arr: np.ndarray) -> pygame.mixer.Sound:
    """Convierte array float32 mono a pygame.mixer.Sound estéreo."""
    pcm = (arr * 32767).astype(np.int16)
    stereo = np.column_stack([pcm, pcm])  # pygame mixer espera 2 canales
    return pygame.mixer.Sound(buffer=stereo.tobytes())
