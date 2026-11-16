"""Vector HUD components: link buttons, stack console, project tiles, trajectory."""

from __future__ import annotations

from pathlib import Path

from kit import (ACCENT, BG, DIM, INK, LINE, PANEL, REDUCED_OK, brackets, devicon, esc, font_css,
                 phosphor, svg)

OUT = Path(__file__).resolve().parents[1]
CH = 0.6  # JetBrains Mono advance width, in em


def tw(text: str, size: float) -> float:
    return len(text) * CH * size


# ------------------------------------------------------------------ buttons
BUTTONS = [
    ("portfolio", "portfolio", "Planet"),
    ("linkedin", "linkedin", "LinkedinLogo"),
    ("resume", "resume.pdf", "FileText"),
    ("email", "email", "EnvelopeSimple"),
]


def button(slug: str, label: str, icon: str):
    h, pad, isz, fs = 44, 14, 20, 15
    w = round(pad + isz + 10 + tw(label, fs) + pad + 2)
    body = f'''  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" fill="{PANEL}" stroke="{LINE}"/>
  {brackets(0, 0, w, h, arm=7)}
  {phosphor(icon, pad, (h - isz) / 2, isz)}
  <text x="{pad + isz + 10}" y="{h / 2 + 5.2:.1f}" font-size="{fs}" fill="{INK}">{esc(label)}</text>'''
    (OUT / f"btn-{slug}.svg").write_text(svg(w, h, label, body, font_css(label, (400,))), encoding="utf-8")


# ------------------------------------------------------------ stack console
STACK = [
    ("Sparkle", "LLMs and agents", {"chips": [["Claude Haiku 4.5", "GPT-4o", "Gemini 2.5 Flash", "Llama 3.3 70B"],
                                              ["LangGraph", "LangChain", "DSPy", "Hugging Face", "pgvector", "Ollama"]]}),
    ("Eye", "ML and vision", {"icons": [("tensorflow", "TensorFlow"), ("opencv", "OpenCV"), ("pandas", "pandas")],
                              "extra": ["PyTorch", "scikit-learn", "LightGBM", "MLflow", "YOLOv5", "MediaPipe"]}),
    ("Database", "Backend and data", {"icons": [("python", "Python"), ("typescript", "TypeScript"),
                                                ("fastapi", "FastAPI"), ("nextjs", "Next.js"),
                                                ("postgresql", "PostgreSQL"), ("redis", "Redis"),
                                                ("sqlite", "SQLite")]}),
    ("Cloud", "Cloud and ops", {"icons": [("docker", "Docker"), ("azure", "Azure"), ("aws", "AWS"),
                                          ("githubactions", "GH Actions"), ("vercel", "Vercel")],
                                "extra": ["Neon", "Inngest"]}),
]


def stack():
    W, M, X0, CELL = 900, 24, 236, 92
    SCAN = 1.8
    rows_h = [92, 84, 84, 84]
    H = M + sum(rows_h) + 12
    parts, texts = [], []

    def lit(x):  # scan reveal delay for an element at x
        return f'class="lit" style="animation-delay:{0.15 + SCAN * x / W:.2f}s"'

    def chip(x, y, label, fs=14, filled=True):
        w = tw(label, fs) + 20
        texts.append(label)
        fill = PANEL if filled else "none"
        parts.append(f'<g {lit(x)}><rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="28" fill="{fill}" '
                     f'stroke="{LINE}"/><text x="{x + 10:.1f}" y="{y + 19}" font-size="{fs}" fill="{INK}">'
                     f'{esc(label)}</text></g>')
        return w

    y = M
    for (icon, label, spec), rh in zip(STACK, rows_h):
        texts.append(label)
        parts.append(phosphor(icon, M, y + 10, 22, fill=INK))
        parts.append(f'<text x="{M + 32}" y="{y + 27}" font-size="15" font-weight="700" fill="{INK}">{esc(label)}</text>')
        if "chips" in spec:
            for li, line in enumerate(spec["chips"]):
                x = X0
                for c in line:
                    x += chip(x, y + 8 + li * 38, c, filled=(li == 0)) + 10
        else:
            for i, (slug, name) in enumerate(spec["icons"]):
                cx = X0 + CELL / 2 + i * CELL
                texts.append(name)
                parts.append(f'<g {lit(cx)}>{devicon(slug, cx, y + 26, 32)}'
                             f'<text x="{cx}" y="{y + 68}" font-size="12" fill="{DIM}" text-anchor="middle">{esc(name)}</text></g>')
            extra = spec.get("extra", [])
            ex0 = X0 + len(spec["icons"]) * CELL + 12
            lines, cur, x = [], [], ex0
            for c in extra:                       # flow chips, wrap at the panel edge
                cw = tw(c, 13) + 20
                if cur and x + cw > W - M:
                    lines.append(cur)
                    cur, x = [], ex0
                cur.append(c)
                x += cw + 10
            if cur:
                lines.append(cur)
            top = y + 18 - (len(lines) - 1) * 17
            for li, line in enumerate(lines):
                x = ex0
                for c in line:
                    x += chip(x, top + li * 34, c, fs=13, filled=False) + 10
        y += rh

    grid = (f'<defs><pattern id="g" width="18" height="18" patternUnits="userSpaceOnUse">'
            f'<circle cx="1" cy="1" r="0.9" fill="{LINE}"/></pattern></defs>'
            f'<rect width="{W}" height="{H}" fill="{BG}"/><rect width="{W}" height="{H}" fill="url(#g)" opacity=".55"/>')
    scan = f'<rect class="scan" x="0" y="6" width="2" height="{H - 12}" fill="{ACCENT}" opacity="0"/>'
    css = font_css(" ".join(texts), (400, 700)) + f"""
{REDUCED_OK} {{
  .lit{{animation:lit .5s ease-out both}}
  .scan{{animation:scan {SCAN}s cubic-bezier(.4,0,.2,1) .15s both}}
}}
@keyframes lit{{from{{opacity:.18}}to{{opacity:1}}}}
@keyframes scan{{0%{{opacity:1;transform:translateX(0)}}92%{{opacity:1}}100%{{opacity:0;transform:translateX({W}px)}}}}"""
    body = "\n  ".join([grid, brackets(0, 0, W, H, arm=16)] + parts + [scan])
    names = []
    for _, label, spec in STACK:
        items = [c for line in spec.get("chips", []) for c in line] + [n for _, n in spec.get("icons", [])] + spec.get("extra", [])
        names.append(f"{label}: {', '.join(items)}")
    (OUT / "stack.svg").write_text(svg(W, H, "Tech stack", "  " + body, css, desc=". ".join(names) + "."),
                                   encoding="utf-8")


# ------------------------------------------------------------ project tiles
TILES = [
    ("bilingual", "Bilingual RAG Copilot", "Translate", ["nextjs", "typescript", "vercel"]),
    ("restai", "RestAI", "ChefHat", ["fastapi", "nextjs", "postgresql"]),
    ("copilot", "Retail Analytics Copilot", "Graph", ["python", "sqlite"]),
    ("storefy", "Storefy", "Storefront", ["nextjs", "typescript", "postgresql"]),
]


def tile(slug, name, icon, stack_icons):
    S = 128
    n = len(stack_icons)
    icons = "".join(devicon(s, S / 2 + (i - (n - 1) / 2) * 26, 106, 16, fill=DIM) for i, s in enumerate(stack_icons))
    body = f'''  <rect width="{S}" height="{S}" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{S - 1}" height="{S - 1}" fill="none" stroke="{LINE}"/>
  {brackets(0, 0, S, S, arm=12)}
  {phosphor(icon, (S - 56) / 2, 20, 56, weight="light")}
  <line x1="24" y1="88" x2="{S - 24}" y2="88" stroke="{LINE}"/>
  {icons}'''
    (OUT / f"tile-{slug}.svg").write_text(svg(S, S, f"{name} project", body), encoding="utf-8")


# --------------------------------------------------------------- trajectory
STOPS = [
    (0.05, "2023", "B.Sc. Computer Science", "Zagazig University", ""),
    (0.31, "May-Dec 2024", "ML Intern", "CodeAlpha", "ResNet-50, recommender"),
    (0.56, "May 2025", "Data Engineer Intern", "SustainGRC", "Text-to-SQL, backup and DR"),
    (0.82, "Jul 2025, now", "AI Engineer", "SustainGRC", "LLM service, classifier"),
]


def trajectory():
    W, H = 900, 214
    P0, C, P2 = (24, 92), (450, 22), (876, 92)

    def B(t):
        return ((1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * C[0] + t * t * P2[0],
                (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * C[1] + t * t * P2[1])

    def seg(t0, t1, n=40):
        pts = [B(t0 + (t1 - t0) * k / n) for k in range(n + 1)]
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    tnow = STOPS[-1][0]
    parts = [f'<rect width="{W}" height="{H}" fill="{BG}"/>',
             f'<defs><linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="{INK}" stop-opacity=".55"/>'
             f'<stop offset="1" stop-color="{INK}" stop-opacity="0"/></linearGradient></defs>',
             f'<path d="{seg(0, tnow)}" fill="none" stroke="{INK}" stroke-opacity=".45" stroke-width="1.5"/>',
             f'<path d="{seg(tnow, 1)}" fill="none" stroke="url(#fade)" stroke-width="1.5" stroke-dasharray="2 6"/>']
    texts = []
    for i, (t, date, role, org, note) in enumerate(STOPS):
        x, y = B(t)
        now = i == len(STOPS) - 1
        texts += [date, role, org, note]
        if now:
            parts.append(f'<rect class="ring" x="{x - 12:.1f}" y="{y - 12:.1f}" width="24" height="24" fill="none" '
                         f'stroke="{ACCENT}" style="transform-origin:{x:.1f}px {y:.1f}px"/>')
            parts.append(f'<rect x="{x - 6:.1f}" y="{y - 6:.1f}" width="12" height="12" fill="{ACCENT}"/>')
        else:
            parts.append(f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{BG}" stroke="{INK}" stroke-width="1.5"/>')
        tx = x - 5
        parts.append(f'<line x1="{x:.1f}" y1="{y + 10:.1f}" x2="{x:.1f}" y2="{y + 26:.1f}" stroke="{LINE}"/>')
        parts.append(f'<text x="{tx:.1f}" y="{y + 44:.1f}" font-size="13" fill="{ACCENT if now else DIM}">{esc(date)}</text>')
        parts.append(f'<text x="{tx:.1f}" y="{y + 66:.1f}" font-size="15" font-weight="700" fill="{INK}">{esc(role)}</text>')
        parts.append(f'<text x="{tx:.1f}" y="{y + 86:.1f}" font-size="13" fill="{DIM}">{esc(org)}</text>')
        if note:
            parts.append(f'<text x="{tx:.1f}" y="{y + 106:.1f}" font-size="12" fill="{DIM}" opacity=".8">{esc(note)}</text>')
    parts.append(brackets(0, 0, W, H, arm=16))
    css = font_css(" ".join(texts), (400, 700)) + f"""
{REDUCED_OK} {{ .ring{{animation:ring 2.8s ease-out infinite}} }}
@keyframes ring{{0%{{opacity:.9;transform:scale(.6)}}100%{{opacity:0;transform:scale(1.7)}}}}"""
    desc = "Experience: " + "; ".join(", ".join(x for x in (d, r, o, n) if x) for _, d, r, o, n in STOPS) + "."
    (OUT / "trajectory.svg").write_text(svg(W, H, "Career trajectory", "  " + "\n  ".join(parts), css, desc=desc),
                                        encoding="utf-8")


def build():
    for b in BUTTONS:
        button(*b)
    stack()
    for t in TILES:
        tile(*t)
    trajectory()


if __name__ == "__main__":
    build()
    print("wrote buttons, stack, tiles, trajectory")
