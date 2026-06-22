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
BALL_RADIUS_MAX  = 210   # radio máximo (no crece más)
BALL_MASS        = 5.0
BALL_SPEED_INIT  = 420   # píxeles/segundo al arrancar
BALL_SPEED_MIN   = 380   # no dejar que la bola se frene más de esto
BALL_SPEED_MAX   = 2400  # cap de velocidad (más alto para la mayor aceleración)

# --- Crecimiento y aceleración ---
GROW_ON_EAT  = 0.22    # px de radio por partícula comida
GROW_ON_WALL = 0.14    # px de radio por rebote en la pared
ACCEL_ON_EAT  = 1.005   # factor multiplicativo de velocidad al comer (aumentado)
ACCEL_ON_WALL = 1.010   # factor multiplicativo de velocidad al rebotar (aumentado)

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
REGEN_RATE  = 4.0    # partículas nuevas por segundo
MAX_REGEN   = 400    # cuota total de partículas regeneradas; luego para

# --- Física ---
GRAVITY = 0     # sin gravedad; la bola rebota indefinidamente
DAMPING = 1.0   # sin amortiguación de aire

# --- Overlay ---
HOOK_TEXT = "how long will it take to clean the map?"
