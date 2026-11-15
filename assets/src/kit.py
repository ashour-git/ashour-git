"""Shared design tokens and SVG helpers for the profile art.

Tokens
  BG      void       #0d1117  GitHub's dark canvas, so panels melt into the page
  INK     starlight  #e6edf3  primary marks and text
  DIM     dust       #7d8590  secondary text
  LINE    hull       #30363d  panel edges and rules
  PANEL   deck       #161b22  raised surfaces (buttons, chips)
  ACCENT  accretion  #f0643c  the only accent; it marks what is live

Type: JetBrains Mono (OFL), subset per SVG and embedded as WOFF, so the art
renders the same on every OS. Fallback is the system monospace stack.
"""

from __future__ import annotations

import base64
import io
import json
from functools import lru_cache
from pathlib import Path

from fontTools import subset

BG, INK, DIM, LINE, PANEL, ACCENT = "#0d1117", "#e6edf3", "#7d8590", "#30363d", "#161b22", "#f0643c"
FONT_DIR = Path("C:/Windows/Fonts")
FONT_FILES = {400: "JetBrainsMonoNerdFont-Regular.ttf", 700: "JetBrainsMonoNerdFont-Bold.ttf",
              800: "JetBrainsMonoNerdFont-ExtraBold.ttf"}
FAMILY = "JBM"
FALLBACK = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
ICONS = json.loads(Path(__file__).with_name("icons.json").read_text(encoding="utf-8"))

REDUCED_OK = "@media (prefers-reduced-motion: no-preference)"


def font_css(text: str, weights=(400, 700)) -> str:
    """@font-face rules for a WOFF subset that covers `text` (plus ASCII digits/punctuation)."""
    chars = "".join(sorted(set(text + " 0123456789.,:-+_/()'\"$~@")))
    rules = []
    for w in weights:
        rules.append(f"@font-face{{font-family:{FAMILY};font-weight:{w};"
                     f"src:url(data:font/woff;base64,{_subset(w, chars)}) format('woff')}}")
    rules.append(f"text{{font-family:{FAMILY},{FALLBACK}}}")
    return "\n".join(rules)


@lru_cache(maxsize=None)
def _subset(weight: int, chars: str) -> str:
    opts = subset.Options()
    opts.flavor = "woff"
    opts.layout_features = ["kern"]
    opts.name_IDs = [0, 1, 2, 3, 4, 5, 6]
    opts.notdef_outline = True
    font = subset.load_font(str(FONT_DIR / FONT_FILES[weight]), opts)
    sub = subset.Subsetter(opts)
    sub.populate(text=chars)
    sub.subset(font)
    buf = io.BytesIO()
    subset.save_font(font, buf, opts)
    return base64.b64encode(buf.getvalue()).decode()


def phosphor(name: str, x: float, y: float, size: float, fill=INK, weight="regular", extra="") -> str:
    """Phosphor icon (256 grid) with its top-left at (x, y)."""
    s = size / 256
    paths = "".join(f'<path d="{d}"/>' for d in ICONS["phosphor"][name][weight])
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.4f})" fill="{fill}" {extra}>{paths}</g>'


def devicon(name: str, cx: float, cy: float, size: float, fill=INK, extra="") -> str:
    """Devicon glyph centred on (cx, cy), fitted into a size x size box."""
    ic = ICONS["devicon"][name]
    x0, y0, x1, y1 = ic["bounds"]
    s = size / max(x1 - x0, y1 - y0)
    tx = cx - (x0 + x1) / 2 * s
    ty = cy + (y0 + y1) / 2 * s
    return (f'<g transform="translate({tx:.2f},{ty:.2f}) scale({s:.5f},{-s:.5f})" fill="{fill}" {extra}>'
            f'<path d="{ic["d"]}"/></g>')


def brackets(x, y, w, h, arm=12, color=INK, sw=1.5) -> str:
    """HUD corner brackets around a box."""
    o = sw / 2
    x0, y0, x1, y1 = x + o, y + o, x + w - o, y + h - o
    d = (f"M{x0},{y0 + arm}V{y0}H{x0 + arm} M{x1 - arm},{y0}H{x1}V{y0 + arm} "
         f"M{x1},{y1 - arm}V{y1}H{x1 - arm} M{x0 + arm},{y1}H{x0}V{y1 - arm}")
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"/>'


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, title, body, css="", desc=None) -> str:
    d = f'\n  <desc id="d">{esc(desc)}</desc>' if desc else ""
    lab = "t d" if desc else "t"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="{lab}">\n  <title id="t">{esc(title)}</title>{d}\n'
            f'  <style>\n{css}\n  </style>\n{body}\n</svg>\n')
