"""Helpers de dibujo para surfaces pygame. Sin estado global."""

import pygame


def clear(surface: pygame.Surface, color=(10, 10, 10)) -> None:
    surface.fill(color)


def draw_circle_filled(surface: pygame.Surface, color, center, radius: float) -> None:
    pygame.draw.circle(surface, color,
                       (int(center[0]), int(center[1])), max(1, int(radius)))


def draw_circle_outline(surface: pygame.Surface, color, center,
                        radius: float, width: int = 3) -> None:
    pygame.draw.circle(surface, color,
                       (int(center[0]), int(center[1])), max(1, int(radius)), width)
