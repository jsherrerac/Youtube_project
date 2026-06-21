# Canal de YouTube: matemáticas y física a través de código

## Sobre el creador
Estudiante de Ingeniería de Sistemas y Computación en Uniandes (4to semestre).
Fuerte en matemáticas, física y Python. Inglés B2.
Habla en español de Colombia, tono informal y directo (parcero, de una, bro).

## Objetivo del proyecto
Canal de YouTube que combina dos tipos de contenido:
1. Shorts de simulaciones de física satisfactorias (Pygame + Pymunk).
2. Videos largos explicativos estilo 3Blue1Brown (Manim Community).
Idioma: español primero, con titulares/overlays en inglés cuando sume alcance.

## Stack técnico
- Python 3.12+
- Manim Community Edition (NO ManimGL). Import: `from manim import *`
- Pygame + Pymunk para simulaciones de física 2D
- ffmpeg para procesar/exportar video
- Render objetivo: vertical 1080x1920 para shorts, 1920x1080 para videos largos

## Convenciones de código
- Comentarios en español
- Nombres de variables en inglés (snake_case)
- Cada simulación/escena en su propio archivo dentro de manim/ o pygame/
- Para Manim: una clase Scene por archivo, nombre descriptivo
- Para Pygame: incluir loop de captura de frames para exportar MP4

## Estilo pedagógico (importante para Manim)
- Explicar desde primeros principios, no fórmulas memorizadas
- Código de colores consistente: blanco=estructura, azul=variable principal,
  verde=secundaria, amarillo=resultado o foco
- Fondo negro siempre
- Animar la intuición antes que la formalidad

## Workflow
1. Antes de codear un video nuevo, escribir comentario al inicio del archivo
   con: tema, duración objetivo, qué se anima paso a paso.
2. Renderizar primero en calidad media (-qm en Manim) para iterar rápido.
3. Render final solo cuando el contenido está aprobado.

## Cosas que NO hacer
- No usar ManimGL ni mezclar sintaxis vieja
- No instalar paquetes globalmente sin avisar
- No tocar archivos fuera de las carpetas manim/ y pygame/
