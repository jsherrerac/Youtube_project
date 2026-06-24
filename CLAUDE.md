# DotCorzo — sims de física (Pygame) + videos educativos (Manim)

## Stack
- Python 3.12+
- Manim Community (NO ManimGL). `from manim import *`
- Pygame + Pymunk (física 2D), ffmpeg para export
- Render: shorts 1080x1920 vertical, largos 1920x1080

## Convenciones
- Comentarios en español, variables en inglés snake_case
- Cada sim/escena en su propio archivo dentro de manim/ o pygame/
- Manim: una clase Scene por archivo, nombre descriptivo
- Pygame: incluir captura de frames para exportar MP4
- Iterar con -qm; render final -qh solo cuando esté aprobado

## Estilo Manim (solo al trabajar en manim/)
- Primeros principios, no fórmulas memorizadas
- Colores fijos: blanco=estructura, azul=variable principal,
  verde=secundaria, amarillo=resultado/foco. Fondo negro.

## NO hacer
- No ManimGL ni sintaxis vieja
- No instalar paquetes globales sin avisar
- No tocar archivos fuera de manim/ y pygame/

## Respuestas
- Terse y directas: solo código + 1-2 líneas de qué cambió
- Sin explicaciones no pedidas, sin relleno, sin resúmenes largos
- Si algo falla, indicar la causa en una línea y el fix directo