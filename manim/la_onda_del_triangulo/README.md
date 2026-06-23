# La onda escondida en un triángulo — comandos de render

Todos los comandos se ejecutan desde la raíz del proyecto (`Youtube_project/`).
Resolución de alta calidad: **1920×1080 @ 60 fps** (`-qh`).
Para preview rápido usa `-ql` (480p15) o `-qm` (720p30).

---

## Render individual por beat

```bash
# Beat 1 — Hook (~20 s)
manim -qh manim/la_onda_del_triangulo/beat1_hook.py Beat1Hook

# Beat 2 — Triángulo rectángulo (~60 s)
manim -qh manim/la_onda_del_triangulo/beat2_triangulo.py Beat2Triangulo

# Beat 3 — De razón a función (~60 s)
manim -qh manim/la_onda_del_triangulo/beat3_funcion.py Beat3Funcion

# Beat 4 — Círculo unitario (~70 s)
manim -qh manim/la_onda_del_triangulo/beat4_circulo.py Beat4Circulo

# Beat 5 — Desenrollo / Clímax (~80 s)
manim -qh manim/la_onda_del_triangulo/beat5_desenrollo.py Beat5Desenrollo

# Beat 6 — Pago y puente (~65 s)
manim -qh manim/la_onda_del_triangulo/beat6_pago.py Beat6Pago
```

## Preview rápido (sin re-render si ya existe)

```bash
manim -ql -p manim/la_onda_del_triangulo/beat1_hook.py Beat1Hook
```

## Render todos en secuencia (PowerShell)

```powershell
$beats = @(
  "beat1_hook.py Beat1Hook",
  "beat2_triangulo.py Beat2Triangulo",
  "beat3_funcion.py Beat3Funcion",
  "beat4_circulo.py Beat4Circulo",
  "beat5_desenrollo.py Beat5Desenrollo",
  "beat6_pago.py Beat6Pago"
)
foreach ($b in $beats) {
  $file, $scene = $b -split " "
  manim -qh "manim/la_onda_del_triangulo/$file" $scene
}
```

## Output

Los MP4 quedan en:
```
manim/media/videos/beat1_hook/1080p60/Beat1Hook.mp4
manim/media/videos/beat2_triangulo/1080p60/Beat2Triangulo.mp4
...
```

## Notas de edición

- **Beat 6, Parte C**: hay un slate negro de ~5 s marcado `[ CLIP PYGAME AQUÍ ]`.
  Reemplazarlo con el clip de la simulación de Pygame en CapCut/DaVinci.
- Todos los beats usan fondo negro puro — listos para insertar directamente.
- Sin audio: las pistas de voz y música van en edición externa.
