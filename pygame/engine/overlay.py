"""Renderiza texto sobre la surface: hook arriba, HUD abajo."""

import pygame

_font_hook:  pygame.font.Font | None = None
_font_hud:   pygame.font.Font | None = None
_font_timer: pygame.font.Font | None = None


def _init_fonts() -> None:
    global _font_hook, _font_hud, _font_timer
    if _font_hook is None:
        pygame.font.init()
        _font_hook  = pygame.font.SysFont("Arial", 54, bold=True)
        _font_hud   = pygame.font.SysFont("Arial", 46)
        _font_timer = pygame.font.SysFont("Arial", 210, bold=True)


def draw_hook(surface: pygame.Surface, text: str,
              color=(255, 255, 255)) -> None:
    _init_fonts()
    lines = _wrap(text, max_chars=22)
    y = 55
    for line in lines:
        surf = _font_hook.render(line, True, color)
        x = (surface.get_width() - surf.get_width()) // 2
        surface.blit(surf, (x, y))
        y += surf.get_height() + 6


def draw_big_timer(surface: pygame.Surface, elapsed_secs: float) -> None:
    """Timer gigante centrado — elemento del escenario, la acción pasa encima."""
    _init_fonts()
    m, s = divmod(int(elapsed_secs), 60)
    text_surf = _font_timer.render(f"{m:02d}:{s:02d}", True, (52, 52, 52))
    x = (surface.get_width()  - text_surf.get_width())  // 2
    y = (surface.get_height() - text_surf.get_height()) // 2
    surface.blit(text_surf, (x, y))


def draw_hud(surface: pygame.Surface, elapsed_secs: float,
             particle_count: int, color=(160, 160, 160)) -> None:
    _init_fonts()
    count = f"particles left: {particle_count}"
    _blit_centered(surface, _font_hud.render(count, True, color), 200)


# ---------- helpers ----------

def _wrap(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines, current = [], []
    for w in words:
        if sum(len(x) for x in current) + len(current) + len(w) > max_chars and current:
            lines.append(' '.join(current))
            current = []
        current.append(w)
    if current:
        lines.append(' '.join(current))
    return lines


def _blit_centered(surface: pygame.Surface, text_surf: pygame.Surface,
                   y: int) -> None:
    x = (surface.get_width() - text_surf.get_width()) // 2
    surface.blit(text_surf, (x, y))
