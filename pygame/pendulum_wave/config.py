"""
Parámetros de la sim Pendulum Wave.
Los 5 más importantes para tunear el feel están marcados con ★.
"""
import os
import math

# ── Física ★ ──────────────────────────────────────────────────────────────
N          = 16          # ★ número de péndulos (8–20 funcionan bien)
BASE_OSC   = 20          # ★ oscilaciones del péndulo más largo en T_LOOP
T_LOOP     = 22.0        # ★ duración del loop en segundos (= largo del Short)
AMPLITUDE_RAD = math.radians(12)  # ★ amplitud; más → más drama, pero a >15° se ve extraño

# ── Estructura del video ──────────────────────────────────────────────────
WAIT_SECS  = 1.0    # segundos iniciales con todo quieto
RAMP_IN    = 0.8    # segundos de fade-in suave de la amplitud (0 → 1)
SYNC_SECS  = 3.0    # segundos extra después del re-sync final antes de cortar

# ── Layout 1080×1920 ───────────────────────────────────────────────────────
PIVOT_SPAN  = 540        # ancho total del array de pivotes en px (centrado en x=540)
L_MAX_PX    = 1100       # ★ largo del péndulo k=0 (el más lento); más = más majestuoso
BASELINE_Y  = 1500       # y donde reposan todas las bolas en equilibrio

# ── Audio — escala pentatónica C mayor (16 notas, grave→aguda) ────────────
NOTES_HZ = [
    261.63, 293.66, 329.63, 392.00, 440.00,      # C4 D4 E4 G4 A4
    523.25, 587.33, 659.25, 783.99, 880.00,       # C5 D5 E5 G5 A5
    1046.50, 1174.66, 1318.51, 1567.98, 1760.00,  # C6 D6 E6 G6 A6
    2093.00,                                       # C7
]

# ── Visual — trails ────────────────────────────────────────────────────────
TRAIL_LENGTH    = 40     # puntos de historia por péndulo
TRAIL_MAX_ALPHA = 55     # brillo máximo del trail (0–255 como escala aditiva)

# ── Visual — bolas ─────────────────────────────────────────────────────────
BOB_RADIUS        = 18   # radio del núcleo
GLOW_RADIUS_SCALE = 1.4  # tamaño del halo relativo al núcleo (más bajo = más pequeño)
GLOW_LAYERS       = 9
GLOW_MAX_ALPHA    = 72   # brillo del halo en reposo; se boosted en cruce

# ── Visual — cuerdas ───────────────────────────────────────────────────────
STRINGS_VISIBLE = True
STRING_ALPHA    = 55     # translucidez (0=invisible, 255=opaco)
STRING_WIDTH    = 2

# ── Visual — pulso al cruzar el centro ────────────────────────────────────
PULSE_RADIUS_MAX    = 62
PULSE_DURATION_FRAMES = 28
PULSE_MAX_ALPHA     = 190   # escala del brillo del anillo (0–255)

# ── Visual — flash de bola al cruzar ──────────────────────────────────────
BOB_FLASH_DECAY      = 0.72   # multiplicador por frame (rápido = 0.6, lento = 0.85)
BOB_FLASH_GLOW_BOOST = 2.0    # factor extra de glow_max_alpha en el momento del cruce

# ── Visual — pivotes ───────────────────────────────────────────────────────
PIVOT_DOT_RADIUS = 3
PIVOT_DOT_COLOR  = (50, 50, 65)

# ── Colores ────────────────────────────────────────────────────────────────
BG_COLOR         = (0, 0, 0)      # negro puro
SPECTRUM_SAT     = 0.90           # saturación del espectro HSV (0.7–1.0)
SPECTRUM_HUE_MAX = 0.85           # rango de hue (0.85 = rojo→violeta sin cerrar el ciclo)

# ── HUD ────────────────────────────────────────────────────────────────────
HOOK_TEXT = "wait for them to sync back up"

# ── Salida ─────────────────────────────────────────────────────────────────
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "pendulum_wave.mp4")
