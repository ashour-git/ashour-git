"""Build every image the profile README uses.

  python assets/src/build.py            # reuse cached rasters (fast)
  REBUILD=1 python assets/src/build.py  # re-run the ray tracer and dithering (~4 min)

Outputs land in assets/. Icons come from assets/src/icons.json (see icons.py);
type is JetBrains Mono, subset and embedded per SVG (see kit.py).
"""

import hud
import space

if __name__ == "__main__":
    space.banner()
    space.astronaut()
    space.horizon()
    hud.build()
    print("built banner, astronaut, horizon, buttons, stack, tiles, trajectory")
