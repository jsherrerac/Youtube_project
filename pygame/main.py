"""
Dispatcher CLI para las sims del engine.

Uso (desde la carpeta pygame/):
    python main.py eat_the_map           # preview en ventana
    python main.py eat_the_map --record  # graba mp4 en eat_the_map/output/
"""

import sys
import os
import argparse

# Garantizar que "from engine..." y "from eat_the_map..." funcionen
sys.path.insert(0, os.path.dirname(__file__))


def main() -> None:
    parser = argparse.ArgumentParser(description="Motor de Shorts — despacha sims")
    parser.add_argument("sim",
                        choices=["eat_the_map", "pendulum_wave"],
                        help="Nombre de la sim a ejecutar")
    parser.add_argument("--record", action="store_true",
                        help="Graba mp4 en <sim>/output/ (más rápido que realtime)")
    args = parser.parse_args()

    if args.sim == "eat_the_map":
        from eat_the_map.sim import EatTheMap
        import eat_the_map.config as sim_cfg
        sim = EatTheMap(sim_cfg)
    elif args.sim == "pendulum_wave":
        from pendulum_wave.sim import PendulumWave
        import pendulum_wave.config as sim_cfg
        sim = PendulumWave(sim_cfg)
    else:
        print(f"[main] Sim desconocida: {args.sim}")
        sys.exit(1)

    sim.run(record=args.record)


if __name__ == "__main__":
    main()
