"""Extract icon outlines into assets/src/icons.json.

Sources (both already on this machine, both permissively licensed):
  - Phosphor Icons (MIT) from site/node_modules/@phosphor-icons/react, 256x256 grid
  - Devicons (MIT) as patched into JetBrains Mono Nerd Font, read with fontTools

Run once when the icon list changes:  python assets/src/icons.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
PHOSPHOR = ROOT / "site/node_modules/@phosphor-icons/react/dist/defs"
NERD_FONT = Path("C:/Windows/Fonts/JetBrainsMonoNerdFont-Regular.ttf")

PHOSPHOR_ICONS = ["Planet", "LinkedinLogo", "FileText", "EnvelopeSimple", "ChefHat", "Graph",
                  "Storefront", "Sparkle", "Eye", "Database", "Cloud", "RocketLaunch", "Translate"]
DEVICONS = ["python", "typescript", "fastapi", "nextjs", "postgresql", "redis", "sqlite",
            "tensorflow", "opencv", "pandas",
            "docker", "azure", "aws", "githubactions", "vercel"]


def phosphor(name: str, weight: str) -> list[str]:
    src = (PHOSPHOR / f"{name}.mjs").read_text(encoding="utf-8")
    block = re.search(rf'\[\s*"{weight}",(.*?)\n  \]', src, re.S).group(1)
    return re.findall(r'd: "([^"]+)"', block)


def devicon(font: TTFont, name: str) -> dict:
    gs = font.getGlyphSet()
    g = gs[f"dev-{name}"]
    pen = SVGPathPen(gs)
    g.draw(pen)
    bp = BoundsPen(gs)
    g.draw(bp)
    return {"d": pen.getCommands(), "bounds": bp.bounds}  # font units, y up


def main():
    font = TTFont(NERD_FONT)
    out = {"phosphor": {}, "devicon": {}}
    for n in PHOSPHOR_ICONS:
        out["phosphor"][n] = {w: phosphor(n, w) for w in ("regular", "light")}
    for n in DEVICONS:
        out["devicon"][n] = devicon(font, n)
    dest = Path(__file__).with_name("icons.json")
    dest.write_text(json.dumps(out), encoding="utf-8")
    print(f"wrote {dest.name}: {len(PHOSPHOR_ICONS)} phosphor, {len(DEVICONS)} devicons")


if __name__ == "__main__":
    main()
