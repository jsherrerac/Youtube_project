# Configuración global del engine — override por sim en su propio config.py.

WIDTH  = 1080
HEIGHT = 1920
FPS    = 60
PHYSICS_DT   = 1 / 60.0  # timestep fijo desacoplado del render
PREVIEW_SCALE = 0.4       # escala de la ventana de preview en vivo

# Paleta base (RGB)
PALETTE = {
    "background": (10, 10, 10),
    "ball":       (80, 140, 255),   # azul protagonista
    "particle":   (210, 210, 210),  # gris claro partículas
    "container":  (255, 255, 255),  # borde blanco
    "text_hook":  (255, 255, 255),
    "text_hud":   (160, 160, 160),
}

# Tipos de colisión pymunk — únicos en todo el engine
CTYPE_BALL     = 1
CTYPE_PARTICLE = 2
CTYPE_WALL     = 3

# Rutas de sonidos — stubs, reemplazar con .wav reales cuando existan
SOUND_PATHS = {
    "eat":  "pygame/engine/assets/eat.wav",
    "wall": "pygame/engine/assets/wall.wav",
    "done": "pygame/engine/assets/done.wav",
}
