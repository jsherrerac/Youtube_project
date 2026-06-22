"""Grabación offline: cada frame se escribe directamente al mp4 vía imageio."""

import os
import numpy as np
import pygame
import imageio


class Recorder:
    def __init__(self, output_path: str, fps: int, size: tuple):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self._writer = imageio.get_writer(
            output_path, fps=fps, macro_block_size=None,
            ffmpeg_params=['-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'fast']
        )

    def capture(self, surface: pygame.Surface) -> None:
        arr = pygame.surfarray.array3d(surface)   # (W, H, 3)
        self._writer.append_data(arr.transpose(1, 0, 2))  # imageio: (H, W, 3)

    def finish(self) -> None:
        self._writer.close()
