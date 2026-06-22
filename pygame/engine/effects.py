"""Efectos visuales reutilizables — solo depende de pygame."""

import pygame


def draw_glow(
    surface: pygame.Surface,
    pos,
    radius: float,
    color,
    layers: int = 10,
    max_alpha: int = 80,
) -> None:
    """
    Bloom aditivo por capas concéntricas.

    Crea una surface temporal del tamaño del glow (no full-screen) y la blitea
    con BLEND_RGB_ADD. El fondo negro (0,0,0) no contribuye al blend aditivo.

    Parámetros:
        radius    : radio de referencia (el del núcleo dibujado)
        color     : (R, G, B) — tono del halo
        layers    : capas concéntricas; 10–16 recomendado para gradiente suave
        max_alpha : brillo máximo (0–255); ≤ 120 para no saturar la escena
    """
    gr   = int(radius * 2.5) + 2
    size = gr * 2
    tmp  = pygame.Surface((size, size))   # fondo negro por defecto
    cx = cy = gr
    r, g, b = int(color[0]), int(color[1]), int(color[2])
    inner   = max(1, int(radius * 0.8))

    for i in range(layers):
        t      = i / max(layers - 1, 1)            # 0 = outer, 1 = inner
        ring_r = max(1, int(gr - (gr - inner) * t))
        bright = (t ** 2.2) * max_alpha / 255.0    # gamma 2.2 → caída natural
        pygame.draw.circle(
            tmp,
            (int(r * bright), int(g * bright), int(b * bright)),
            (cx, cy),
            ring_r,
        )

    surface.blit(
        tmp,
        (int(pos[0]) - gr, int(pos[1]) - gr),
        special_flags=pygame.BLEND_RGB_ADD,
    )
