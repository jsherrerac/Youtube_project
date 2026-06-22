"""
Parámetros de feel de eat_the_map.
Todos los valores tuneable están aquí — la lógica de sim.py no contiene números mágicos.
"""

import os

# --- Resolución de output ---
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "eat_the_map.mp4")

# --- Contenedor ---
CONTAINER_RADIUS = 470   # px desde el centro de la pantalla

# --- Bola protagonista ---
BALL_RADIUS_INIT = 28    # radio inicial en px
BALL_RADIUS_MAX  = 448   # radio de victoria: llena casi todo el contenedor (470)
BALL_MASS        = 5.0
BALL_SPEED_INIT  = 250   # píxeles/segundo al arrancar
BALL_SPEED_MIN   = 230   # piso de velocidad (debe ser <= BALL_SPEED_INIT)
BALL_SPEED_MAX   = 2400  # cap de velocidad (más alto para la mayor aceleración)

# --- Crecimiento y aceleración ---
GROW_ON_EAT  = 0.11    # px de radio por partícula comida
GROW_ON_WALL = 0          # sin crecimiento al rebotar — solo crece al comer

# Fase final: cuando ya no quedan partículas ni caben nuevas, la bola crece
# suavemente hasta llenar el mapa y terminar (~3 segundos satisfactorios).
FINALE_GROW_PX_PER_SEC = 4.0
ACCEL_ON_EAT  = 1.005   # factor multiplicativo de velocidad al comer (aumentado)
ACCEL_ON_WALL = 1.016   # factor multiplicativo de velocidad al rebotar (aumentado)

# --- Partículas ---
N_PARTICLES    = 760   # cantidad inicial (doble)
PARTICLE_RADIUS = 8    # radio en px (más grande para que se vean bien)

# Paleta de colores para las partículas (vibrant sobre fondo negro)
PARTICLE_COLORS = [
    (255,  90,  90),   # rojo
    (100, 230, 120),   # verde
    (255, 210,  50),   # amarillo
    (200,  90, 255),   # morado
    (255, 135,  40),   # naranja
    ( 60, 210, 230),   # cian
    (255,  90, 180),   # rosa
    (140, 200, 255),   # azul claro
]

# --- Regeneración (genera tensión pero no impide el final) ---
REGEN_RATE  = 64      # partículas nuevas por segundo
MAX_REGEN   = 999999  # efectivamente ilimitado — la regen para cuando la bola gana

# --- Física ---
GRAVITY = 0     # sin gravedad; la bola rebota indefinidamente
DAMPING = 1.0   # sin amortiguación de aire

# Rotación aleatoria máxima aplicada en cada rebote de pared (grados).
# Rompe órbitas periódicas (línea recta) sin que el movimiento se vea forzado.
DRIFT_ON_WALL_DEG = 4.0

# --- Melodía (In the Hall of the Mountain King - Grieg, dominio público) ---
# Cada colisión con la pared toca la siguiente nota de la secuencia.
MELODY = [
    "E4", "F#4", "G4", "A4", "B4", "G4", "B4",
    "Bb4", "F#4", "Bb4", "A4", "F4", "A4",
    "E4", "F#4", "G4", "A4", "B4", "G4", "B4", "E5",
    "D5", "B4", "G4", "B4", "D5",
]

# --- Visual: cometa (bola protagonista) ---
# COMET_VISUAL_MAX_R: cap del radio dibujado. Igualarlo a BALL_RADIUS_MAX (448)
# desactiva el cap → el cometa crece visualmente igual que la física.
# Bájalo (ej. 100) si quieres un cometa pequeño que no crezca visualmente.
COMET_VISUAL_MAX_R = 448      # sin cap (= BALL_RADIUS_MAX)

TRAIL_LENGTH       = 45       # puntos de historia de la cola
TRAIL_MAX_ALPHA    = 55       # 0–255; bajo → partículas visibles a través
HUE_SPEED          = 0.003    # avance de tono por frame (~5.5s ciclo completo a 60fps)
HUE_TRAIL_STEP     = 0.04     # diferencia de tono entre puntos consecutivos

GLOW_LAYERS        = 12       # capas del halo (más = gradiente más suave)
GLOW_MAX_ALPHA     = 95       # intensidad del halo (0–255)
CORE_COLOR         = (235, 245, 255)   # blanco cálido del núcleo
CORE_RADIUS_SCALE  = 0.82     # núcleo visible = visual_radius × este valor

# Glow suave en partículas: pre-renderiza 1 sprite por color, bliteado aditivo.
# Con 760 partículas en software puede costar 3–5ms extra → False por defecto.
PARTICLE_SOFT_GLOW = False

# --- Overlay ---
HOOK_TEXT = "how long will it take to clean the map?"
