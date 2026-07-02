# El número que dibuja el azar — Monte Carlo / estimar π

Video largo en **6 escenas separadas** (una por beat). Cada beat es una `Scene`
independiente y renderizable sola. Sin voz ni música — solo visual sobre fondo
negro. Componentes reutilizables en [`../lib/montecarlo.py`](../lib/montecarlo.py).

## Color (consistente en las 6 escenas)
- DENTRO = cian `#22D3EE` · FUERA = coral `#FF6B5C`
- borde (cuadrado + cuarto de círculo) = blanco
- valor de π y línea de π real = amarillo/dorado · fondo = negro

## Render — alta calidad (1920×1080, 60 fps)

Ejecutar desde la carpeta `manim/` (para que `lib/` sea importable):

```bash
manim render -qh -r 1920,1080 --fps 60 montecarlo_pi/beat1_hook.py            Beat1Hook
manim render -qh -r 1920,1080 --fps 60 montecarlo_pi/beat2_tablero.py         Beat2Tablero
manim render -qh -r 1920,1080 --fps 60 montecarlo_pi/beat3_razon.py           Beat3Razon
manim render -qh -r 1920,1080 --fps 60 montecarlo_pi/beat4_grandes_numeros.py Beat4GrandesNumeros
manim render -qh -r 1920,1080 --fps 60 montecarlo_pi/beat4_5_robustez.py      Beat45Robustez
manim render -qh -r 1920,1080 --fps 60 montecarlo_pi/beat4_7_precio.py        Beat47Precio
manim render -qh -r 1920,1080 --fps 60 montecarlo_pi/beat5_convergencia.py    Beat5Convergencia
manim render -qh -r 1920,1080 --fps 60 montecarlo_pi/beat5_5_origen.py        Beat55Origen
manim render -qh -r 1920,1080 --fps 60 montecarlo_pi/beat6_pago.py            Beat6Pago
```

Orden de montaje: 1 · 2 · 3 · 4 · **4.5** · (**4.7** opcional) · 5 · **5.5** · 6.

Iterar más rápido: cambiar `-qh` por `-qm`. Los MP4 quedan en
`media/videos/<beat>/1080p60/`.

## Notas
- Semilla fija (`np.random.seed`) por beat → convergencia reproducible entre renders.
- Beat 5 capa los puntos visibles a ~5000 (rendimiento); el contador y la curva
  usan N grande solo numéricamente.
- Beat 4.5 reusa `ConvergencePlot.multi_curve_from` (3 semillas, mismo eje).
- Beat 4.7 es OPCIONAL (escena tipográfica, sin board).
- Beat 6 estima EN VIVO el área de un `ArbitraryShape` (lib) y conserva el
  placeholder de ~5s para insertar el clip de Pygame en edición.
