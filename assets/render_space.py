"""Render the dithered space art for the profile README.

Everything here is procedural: a ray-marched SDF astronaut, a noise-textured
planet and a lunar horizon, each reduced to 1-bit with Atkinson dithering and
wrapped in an SVG (raster embedded as base64, motion in CSS gated by
prefers-reduced-motion). Run:  python assets/render_space.py
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).parent
BG = "#0d1117"      # GitHub dark canvas, so panels blend in dark mode
INK = "#e6edf3"     # GitHub dark foreground
DIM = "#7d8590"
LINE = "#30363d"
ACCENT = "#f0643c"  # international orange, the only accent on the page
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

rng = np.random.default_rng(7)


# ----------------------------------------------------------------- utilities
def norm(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def atkinson(gray: np.ndarray) -> np.ndarray:
    """1-bit Atkinson dither. gray in [0,1], returns bool (True = lit)."""
    g = gray.astype(np.float64).copy()
    h, w = g.shape
    out = np.zeros((h, w), bool)
    for y in range(h):
        row = g[y]
        for x in range(w):
            old = row[x]
            new = 1.0 if old >= 0.5 else 0.0
            out[y, x] = new > 0
            err = (old - new) / 8.0
            if x + 1 < w:
                row[x + 1] += err
            if x + 2 < w:
                row[x + 2] += err
            if y + 1 < h:
                if x > 0:
                    g[y + 1, x - 1] += err
                g[y + 1, x] += err
                if x + 1 < w:
                    g[y + 1, x + 1] += err
            if y + 2 < h:
                g[y + 2, x] += err
    return out


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def to_png(index: np.ndarray, palette: list[str | None]) -> bytes:
    """index: uint8 array into palette; None entry = transparent."""
    img = Image.fromarray(index.astype(np.uint8), "P")
    pal = []
    trans = None
    for i, c in enumerate(palette):
        if c is None:
            trans = i
            pal += [0, 0, 0]
        else:
            pal += list(hexrgb(c))
    img.putpalette(pal + [0] * (768 - len(pal)))
    buf = io.BytesIO()
    if trans is not None:
        img.save(buf, "PNG", optimize=True, transparency=trans)
    else:
        img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def data_uri(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode()


# --------------------------------------------------------------- value noise
_perm = rng.permutation(4096)


def _hash(ix, iy, iz):
    h = _perm[(ix * 73856093 ^ iy * 19349663 ^ iz * 83492791) & 4095]
    return _perm[(h + iz) & 4095] / 4095.0


def vnoise(p):
    i = np.floor(p).astype(np.int64)
    f = p - i
    u = f * f * (3 - 2 * f)
    acc = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (np.where(dx, u[..., 0], 1 - u[..., 0])
                     * np.where(dy, u[..., 1], 1 - u[..., 1])
                     * np.where(dz, u[..., 2], 1 - u[..., 2]))
                acc = acc + w * _hash(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz)
    return acc


def fbm(p, octaves=5):
    s, a, tot = 0.0, 0.5, 0.0
    for _ in range(octaves):
        s = s + a * vnoise(p)
        tot += a
        p = p * 2.03 + 17.1
        a *= 0.5
    return s / tot


def starfield(h, w, density, bright=0.9):
    stars = np.zeros((h, w))
    m = rng.random((h, w)) < density
    stars[m] = rng.uniform(0.55, bright + 0.1, m.sum())
    return stars


# ------------------------------------------------------------------- planet
def render_planet(w, h, cx, cy, r, light, seed_off=0.0, cities=True, craters=False):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    dx, dy = (xx - cx) / r, (cy - yy) / r
    d2 = dx * dx + dy * dy
    inside = d2 < 1.0
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    n = np.stack([dx, dy, nz], -1)
    L = norm(np.array(light, float))
    lam = np.clip((n * L).sum(-1), 0, 1)

    p = n * 2.2 + seed_off
    if craters:
        base = fbm(p * 1.6, 5)
        maria = fbm(p * 0.9 + 3.3, 4) < 0.45
        alb = 0.62 + 0.9 * (base - 0.5) - 0.16 * maria
        cr = fbm(p * 9.0 + 9.1, 3)
        alb -= 0.3 * np.clip((cr - 0.6) * 5, 0, 1)
        alb += 0.25 * np.clip((0.4 - cr) * 5, 0, 1)
        fade = np.clip(0.75 + (yy - (cy - r)) / (h * 1.2), 0.75, 1)
        surf = alb * (lam ** 0.85) * fade
        night = np.zeros_like(surf)
    else:
        land = fbm(p, 6) > 0.52
        clouds = np.clip((fbm(p * 1.7 + 41.0, 5) - 0.5) * 3.2, 0, 1)
        alb = np.where(land, 0.55, 0.16) + 0.1 * (fbm(p * 4, 3) - 0.5)
        alb = alb * (1 - clouds) + 0.95 * clouds
        surf = alb * (lam ** 0.8)
        # atmosphere: brighten the lit limb
        rim = np.clip((d2 - 0.82) / 0.18, 0, 1) ** 2
        surf = surf + 0.55 * rim * np.clip((n * L).sum(-1) + 0.35, 0, 1)
        night = (land & (lam < 0.02) & (clouds < 0.2)).astype(float)
        night *= (fbm(p * 18.0 + 5.0, 2) > 0.66)

    halo = np.zeros_like(surf)
    if not craters:
        d = np.sqrt(d2)
        halo = np.clip(1 - (d - 1) / 0.06, 0, 1) * (d >= 1) * 0.5
        halo *= np.clip((n[..., :2] * L[:2]).sum(-1) / np.maximum(d, 1e-6) + 0.3, 0, 1)

    gray = np.where(inside, surf, halo)
    city = inside & (night > 0) if cities else np.zeros_like(inside)
    return np.clip(gray, 0, 1), inside, city


# ---------------------------------------------------------------- astronaut
def sd_sphere(p, c, r):
    return np.linalg.norm(p - c, axis=-1) - r


def sd_capsule(p, a, b, r):
    pa, ba = p - a, b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - h[..., None] * ba, axis=-1) - r


def sd_rbox(p, c, b, r):
    q = np.abs(p - c) - b
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(-1), 0) - r


def sd_torus(p, c, R, r):
    q = p - c
    a = np.sqrt(q[..., 0] ** 2 + q[..., 2] ** 2) - R
    return np.sqrt(a * a + q[..., 1] ** 2) - r


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def rot(ax, ay, az):
    cx, sx, cy, sy, cz, sz = np.cos(ax), np.sin(ax), np.cos(ay), np.sin(ay), np.cos(az), np.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


V = np.array
HELMET_C, HELMET_R = V([0, 1.42, 0.02]), 0.47
R_WORLD = rot(0.12, -0.55, -0.32)   # model -> world
R_INV = R_WORLD.T


def astro_parts(p):
    """p in model space. returns dict of part distances."""
    d = {}
    d["helmet"] = sd_sphere(p, HELMET_C, HELMET_R)
    d["ring"] = sd_torus(p, V([0, 1.0, 0]), 0.29, 0.075)
    torso = sd_rbox(p, V([0, 0.56, 0]), V([0.34, 0.4, 0.22]), 0.13)
    hips = sd_rbox(p, V([0, 0.06, 0]), V([0.3, 0.14, 0.2]), 0.12)
    body = smin(torso, hips, 0.12)
    # arms: right arm reaches up and out, left arm relaxed
    ra = smin(sd_capsule(p, V([0.47, 0.86, 0]), V([0.86, 1.12, 0.18]), 0.155),
              sd_capsule(p, V([0.86, 1.12, 0.18]), V([1.12, 1.52, 0.34]), 0.135), 0.06)
    la = smin(sd_capsule(p, V([-0.47, 0.86, 0]), V([-0.74, 0.42, 0.1]), 0.155),
              sd_capsule(p, V([-0.74, 0.42, 0.1]), V([-0.64, 0.04, 0.34]), 0.135), 0.06)
    rl = smin(sd_capsule(p, V([0.18, -0.05, 0]), V([0.27, -0.58, 0.26]), 0.175),
              sd_capsule(p, V([0.27, -0.58, 0.26]), V([0.25, -1.06, 0.06]), 0.155), 0.06)
    ll = smin(sd_capsule(p, V([-0.18, -0.05, 0]), V([-0.3, -0.54, -0.06]), 0.175),
              sd_capsule(p, V([-0.3, -0.54, -0.06]), V([-0.33, -1.02, -0.24]), 0.155), 0.06)
    suit = smin(smin(smin(smin(body, ra, 0.08), la, 0.08), rl, 0.08), ll, 0.08)
    d["suit"] = suit
    d["pack"] = sd_rbox(p, V([0, 0.64, -0.37]), V([0.33, 0.44, 0.12]), 0.07)
    d["chest"] = sd_rbox(p, V([0, 0.56, 0.33]), V([0.17, 0.1, 0.05]), 0.03)
    d["glove"] = np.minimum(sd_sphere(p, V([1.17, 1.6, 0.37]), 0.135),
                            sd_sphere(p, V([-0.62, -0.03, 0.38]), 0.135))
    d["cuff"] = np.minimum(sd_capsule(p, V([1.06, 1.42, 0.3]), V([1.1, 1.48, 0.32]), 0.15),
                           sd_capsule(p, V([-0.65, 0.12, 0.3]), V([-0.64, 0.07, 0.33]), 0.15))
    d["boot"] = np.minimum(sd_rbox(p, V([0.25, -1.13, 0.12]), V([0.11, 0.08, 0.17]), 0.06),
                           sd_rbox(p, V([-0.33, -1.09, -0.16]), V([0.11, 0.08, 0.17]), 0.06))
    return d


def astro_sdf(pw):
    p = pw @ R_WORLD  # world -> model (row vectors: p_m = R^T p_w)
    parts = astro_parts(p)
    return np.min(np.stack(list(parts.values())), 0), parts, p


def render_astronaut(w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    aspect = w / h
    u = (xx + 0.5) / w * 2 - 1
    v = 1 - (yy + 0.5) / h * 2
    fov = np.tan(np.radians(19))
    ro = V([0.0, 0.3, 5.5])
    rd = norm(np.stack([u * fov * aspect, v * fov, -np.ones_like(u)], -1))
    rd = rd.reshape(-1, 3)
    t = np.zeros(len(rd))
    hit = np.zeros(len(rd), bool)
    alive = np.ones(len(rd), bool)
    for _ in range(140):
        idx = np.where(alive)[0]
        if not len(idx):
            break
        pts = ro + rd[idx] * t[idx, None]
        dist, _, _ = astro_sdf(pts)
        t[idx] += dist * 0.9
        done = dist < 1e-3
        hit[idx[done]] = True
        alive[idx[done]] = False
        alive[idx[t[idx] > 12]] = False

    gray = np.zeros(len(rd))
    accent = np.zeros(len(rd), bool)
    hi = np.where(hit)[0]
    P = ro + rd[hi] * t[hi, None]
    e = 1e-3
    grad = np.stack([
        astro_sdf(P + V([e, 0, 0]))[0] - astro_sdf(P - V([e, 0, 0]))[0],
        astro_sdf(P + V([0, e, 0]))[0] - astro_sdf(P - V([0, e, 0]))[0],
        astro_sdf(P + V([0, 0, e]))[0] - astro_sdf(P - V([0, 0, e]))[0]], -1)
    N = norm(grad)
    _, parts, Pm = astro_sdf(P)
    names = list(parts.keys())
    mat = np.argmin(np.stack([parts[k] for k in names]), 0)
    mat_name = np.array(names)[mat]

    key = norm(V([0.65, 0.75, 0.55]))
    rim = norm(V([-0.8, 0.1, -0.55]))
    # soft shadow toward key light
    sh = np.ones(len(P))
    st = np.full(len(P), 0.03)
    for _ in range(40):
        dd, _, _ = astro_sdf(P + N * 0.004 + key * st[:, None])
        sh = np.minimum(sh, np.clip(10 * dd / st, 0, 1))
        st += np.clip(dd, 0.02, 0.2)
    ao = np.ones(len(P))
    for k in range(1, 6):
        dd, _, _ = astro_sdf(P + N * (0.06 * k))
        ao -= (0.06 * k - dd) * (0.5 ** k) * 3.5
    ao = np.clip(ao, 0.15, 1)

    diff = np.clip(N @ key, 0, 1) * (0.45 + 0.55 * sh)
    fill = np.clip(N @ norm(V([-0.2, 0.15, 1.0])), 0, 1) * 0.42
    back = np.clip(N @ rim, 0, 1) ** 1.5
    albedo = {"suit": 0.92, "helmet": 0.95, "ring": 0.55, "pack": 0.8, "chest": 0.4,
              "glove": 0.78, "cuff": 0.35, "boot": 0.6}
    alb = np.array([albedo[m] for m in mat_name])
    # fabric folds on the suit
    fold = 1 + 0.12 * np.sin(Pm[:, 1] * 38) * (mat_name == "suit")
    col = alb * fold * (0.08 + 0.9 * diff + fill) * ao + 0.5 * back * ao

    # visor: front of the helmet in model space
    nl = norm(Pm - HELMET_C)
    visor = (mat_name == "helmet") & (nl[:, 2] > 0.22) & (nl[:, 1] > -0.5) & (nl[:, 1] < 0.55) & (np.abs(nl[:, 0]) < 0.86)
    viewd = rd[hi]
    refl = viewd - 2 * (viewd * N).sum(-1, keepdims=True) * N
    spec = np.clip(refl @ key, 0, 1) ** 40
    fres = (1 - np.clip(-(viewd * N).sum(-1), 0, 1)) ** 3
    earth = np.clip(-refl[:, 1] - 0.2, 0, 1) * 0.35
    vcol = 0.03 + 0.6 * fres + 1.4 * spec + earth
    col = np.where(visor, vcol, col)
    # visor rim band
    band = (mat_name == "helmet") & ~visor & (nl[:, 2] > 0.12) & (nl[:, 1] > -0.6) & (nl[:, 1] < 0.66) & (np.abs(nl[:, 0]) < 0.93)
    col = np.where(band, col * 0.55, col)
    # chest status light in accent
    chestlight = (mat_name == "chest") & (np.abs(Pm[:, 0] - 0.09) < 0.035) & (np.abs(Pm[:, 1] - 0.58) < 0.035)
    accent[hi] = chestlight

    gray[hi] = np.clip(col, 0, 1) ** 0.75
    return gray.reshape(h, w), hit.reshape(h, w), accent.reshape(h, w)


# --------------------------------------------------------------- black hole
def atkinson_levels(gray: np.ndarray, levels) -> np.ndarray:
    """Multi-level Atkinson dither. Returns index into `levels`."""
    g = gray.astype(np.float64).copy()
    lv = np.asarray(levels, float)
    h, w = g.shape
    out = np.zeros((h, w), np.uint8)
    for y in range(h):
        row = g[y]
        for x in range(w):
            old = row[x]
            k = int(np.abs(lv - old).argmin())
            out[y, x] = k
            err = (old - lv[k]) / 8.0
            if x + 1 < w:
                row[x + 1] += err
            if x + 2 < w:
                row[x + 2] += err
            if y + 1 < h:
                if x > 0:
                    g[y + 1, x - 1] += err
                g[y + 1, x] += err
                if x + 1 < w:
                    g[y + 1, x + 1] += err
            if y + 2 < h:
                g[y + 2, x] += err
    return out


def render_blackhole(w, h, cx, cy, f, dist=18.0, tilt=7.0, roll=-5.0, r_in=3.0, r_out=11.5):
    """Schwarzschild ray tracer (r_s = 1). Null geodesics are integrated with the
    Binet-equivalent force x'' = -1.5 h^2 x / r^5, against a thin accretion disk
    in the y=0 plane with Doppler beaming. Returns intensity, roughly [0, 1]."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    sx, sy = (xx + 0.5 - cx) / f, (cy - (yy + 0.5)) / f
    cr, sr = np.cos(np.radians(roll)), np.sin(np.radians(roll))
    sx, sy = sx * cr - sy * sr, sx * sr + sy * cr
    t = np.radians(tilt)
    cam = V([0.0, dist * np.sin(t), -dist * np.cos(t)])
    fwd = norm(-cam)
    right = norm(np.cross(V([0, 1.0, 0]), fwd))
    up = np.cross(fwd, right)
    d = norm(fwd + sx[..., None] * right + sy[..., None] * up).reshape(-1, 3)
    n = len(d)
    x = np.tile(cam, (n, 1))
    v = d.copy()
    h2 = (np.cross(x, v) ** 2).sum(-1)
    col = np.zeros(n)
    alpha = np.zeros(n)
    alive = np.ones(n, bool)
    escaped = np.zeros(n, bool)

    def acc(p, hh):
        r2 = (p * p).sum(-1)
        return -1.5 * hh[:, None] * p / (r2 ** 2.5)[:, None]

    for _ in range(900):
        i = np.where(alive)[0]
        if not len(i):
            break
        p, q, hh = x[i], v[i], h2[i]
        r = np.linalg.norm(p, axis=-1)
        dt = np.clip(0.035 * r * r / (1 + r), 0.01, 0.6)[:, None]
        a0 = acc(p, hh)
        p1 = p + q * dt + 0.5 * a0 * dt * dt
        q1 = q + 0.5 * (a0 + acc(p1, hh)) * dt
        cross = (p[:, 1] * p1[:, 1]) < 0
        if cross.any():
            c = np.where(cross)[0]
            fr = p[c, 1] / (p[c, 1] - p1[c, 1])
            pc = p[c] + (p1[c] - p[c]) * fr[:, None]
            rc = np.linalg.norm(pc, axis=-1)
            ok = (rc > r_in) & (rc < r_out)
            if ok.any():
                c, pc, rc = c[ok], pc[ok], rc[ok]
                prof = rc ** -3 * (1 - np.sqrt(r_in / rc))
                prof /= (4.08 ** -3 * (1 - np.sqrt(3 / 4.08)))
                phi = np.arctan2(pc[:, 2], pc[:, 0])
                tex = fbm(np.stack([rc * 3.2, np.cos(phi) * 0.9, np.sin(phi) * 0.9], -1), 4)
                streak = fbm(np.stack([rc * 9.0, np.cos(phi) * 2.6, np.sin(phi) * 2.6], -1) + 11.0, 3)
                tex = 0.45 + 1.1 * (tex - 0.5) + 0.5 * (streak - 0.5)
                beta = np.clip(np.sqrt(0.5 / rc), 0, 0.6)
                vel = np.stack([-pc[:, 2], np.zeros_like(rc), pc[:, 0]], -1) / rc[:, None] * beta[:, None]
                ncam = -norm(q[c])
                gam = 1 / np.sqrt(1 - beta ** 2)
                dop = 1 / (gam * (1 - (vel * ncam).sum(-1)))
                edge = np.clip((r_out - rc) / 3.0, 0, 1) * np.clip((rc - r_in) / 0.25, 0, 1)
                I = np.clip(prof * tex, 0, None) * dop ** 3 * edge
                k = i[c]
                col[k] += (1 - alpha[k]) * I
                alpha[k] += (1 - alpha[k]) * 0.92 * edge
        x[i], v[i] = p1, q1
        r1 = np.linalg.norm(p1, axis=-1)
        fell = r1 < 1.0
        out = (r1 > dist * 1.6) & ((p1 * q1).sum(-1) > 0)
        opaque = alpha[i] > 0.985
        alive[i[fell | out | opaque]] = False
        escaped[i[out]] = True

    # lensed background stars, sampled by the escaped direction
    fd = norm(v)
    star = vnoise(fd * 150.0)
    axis = (fd @ fwd) > np.cos(np.radians(6))      # hide the Einstein-ring pile-up
    sky = (star > 0.9) & escaped & (alpha < 0.5) & ~axis
    return col.reshape(h, w), sky.reshape(h, w)


# ------------------------------------------------------------------ outputs
CSS_MOTION = """
@media (prefers-reduced-motion: no-preference) {
  .tw{animation:tw 4.2s ease-in-out infinite}
  .tw2{animation:tw 6.4s ease-in-out infinite 1.3s}
  .tw3{animation:tw 5.1s ease-in-out infinite 2.6s}
  .cur{animation:blink 1.1s steps(1) infinite}
  .float{animation:float 9s ease-in-out infinite}
  .sig{animation:sig 3.6s linear infinite}
  .out{animation:pulse 3.6s ease-out infinite}
}
@keyframes tw{0%,100%{opacity:.15}50%{opacity:1}}
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
@keyframes float{0%,100%{transform:translate(0,0) rotate(0deg)}50%{transform:translate(0,-9px) rotate(-1.6deg)}}
@keyframes sig{0%{stroke-dashoffset:112}38%,100%{stroke-dashoffset:-12}}
@keyframes pulse{0%,72%{opacity:.35}82%{opacity:1}100%{opacity:.35}}
"""


def twinkles(w, h, n, avoid=None, size=2, accent_last=True):
    out = []
    for i in range(n):
        for _ in range(80):
            x, y = rng.uniform(8, w - 8), rng.uniform(8, h - 8)
            if avoid is None or not avoid(x, y):
                break
        cls = ("tw", "tw2", "tw3")[i % 3]
        s = size if rng.random() < 0.7 else size * 2
        fill = ACCENT if (accent_last and i == n - 1) else INK
        out.append(f'<rect class="{cls}" x="{x:.0f}" y="{y:.0f}" width="{s}" height="{s}" fill="{fill}"/>')
    return "\n  ".join(out)


def banner():
    W, H, S = 1200, 400, 2
    w, h = W // S, H // S
    bx, by = 452, 104                       # black hole centre, logical px
    I, stars = render_blackhole(w, h, cx=bx, cy=by, f=214)
    gray = 1 - np.exp(-2.6 * I)
    idx = atkinson_levels(gray, [0.0, 0.38, 1.0])   # 0 bg, 1 accent, 2 ink
    pal_idx = np.choose(idx, [0, 3, 2]).astype(np.uint8)
    pal_idx[stars & (idx == 0)] = 2
    png = to_png(np.kron(pal_idx, np.ones((S, S), np.uint8)), [None, BG, INK, ACCENT])

    tx, ty = 72, 112
    prompt = f'<tspan fill="{ACCENT}">$</tspan>'
    X1 = 560
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
  <title id="t">Mohamed Ashour, AI Engineer</title>
  <desc id="d">A terminal window reading: whoami, Mohamed Ashour, AI Engineer, LLMs, NLP and computer vision. Beside it, a ray-traced black hole whose accretion disk bends over the event horizon.</desc>
  <style>{CSS_MOTION}
  text{{font-family:{MONO}}}
  </style>
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <image href="{data_uri(png)}" width="{W}" height="{H}" style="image-rendering:pixelated"/>
  {twinkles(W, H, 8, avoid=lambda x, y: x < X1 + 40 or (x - bx * S) ** 2 / 360 ** 2 + (y - by * S) ** 2 / 150 ** 2 < 1, accent_last=False)}
  <g>
    <rect x="40" y="52" width="{X1 - 40}" height="276" fill="{BG}" stroke="{INK}" stroke-width="1.5"/>
    <line x1="40" y1="84" x2="{X1}" y2="84" stroke="{INK}" stroke-width="1.5"/>
    <text x="56" y="74" font-size="14" fill="{DIM}">ashour@event-horizon: ~</text>
    <rect x="{X1 - 66}" y="62" width="12" height="12" fill="none" stroke="{INK}"/>
    <rect x="{X1 - 46}" y="62" width="12" height="12" fill="none" stroke="{INK}"/>
    <rect x="{X1 - 26}" y="62" width="12" height="12" fill="{INK}"/>
    <text x="{tx}" y="{ty + 14}" font-size="21" fill="{DIM}">{prompt} whoami</text>
    <text x="{tx}" y="{ty + 76}" font-size="52" font-weight="700" fill="{INK}" letter-spacing="-1">Mohamed Ashour</text>
    <text x="{tx}" y="{ty + 120}" font-size="24" fill="{INK}">AI Engineer</text>
    <text x="{tx}" y="{ty + 152}" font-size="19" fill="{DIM}">LLMs, NLP and computer vision</text>
    <text x="{tx}" y="{ty + 198}" font-size="21" fill="{DIM}">{prompt}</text>
    <rect class="cur" x="{tx + 22}" y="{ty + 181}" width="12" height="22" fill="{INK}"/>
  </g>
</svg>
'''
    (OUT / "banner.svg").write_text(svg, encoding="utf-8")


def network_constellation():
    """A small feed-forward net drawn as a constellation; pulses run layer by layer."""
    layers = [(96, [22, 48, 74, 100]), (166, [14, 38, 62, 86, 110]), (236, [30, 60, 90]), (306, [136])]
    edges, nodes = [], []
    for li in range(len(layers) - 1):
        (xa, ya), (xb, yb) = layers[li], layers[li + 1]
        for a in ya:
            for b in yb:
                edges.append(f'<line x1="{xa}" y1="{a}" x2="{xb}" y2="{b}" stroke="{INK}" stroke-opacity=".16" stroke-width="1"/>')
        for j in range(3):
            a, b = ya[j % len(ya)], yb[(j * 2 + 1) % len(yb)]
            delay = li * 1.1 + j * 0.15
            edges.append(f'<line class="sig" pathLength="100" x1="{xa}" y1="{a}" x2="{xb}" y2="{b}" stroke="{INK}" '
                         f'stroke-width="2" stroke-dasharray="12 100" stroke-dashoffset="112" style="animation-delay:{delay:.2f}s"/>')
    for li, (x, ys) in enumerate(layers):
        for y in ys:
            if li == len(layers) - 1:
                nodes.append(f'<rect class="out" x="{x - 4}" y="{y - 4}" width="8" height="8" fill="{ACCENT}"/>')
            else:
                nodes.append(f'<rect x="{x - 2}" y="{y - 2}" width="4" height="4" fill="{INK}"/>')
    return "\n  ".join(edges + nodes)


def astronaut():
    W, H, S = 360, 520, 2
    DY = 100
    w, h = W // S, 420 // S
    gray, hit, acc = render_astronaut(w, h)
    bits = atkinson(gray)
    idx = np.where(bits, 2, 0).astype(np.uint8)
    idx[hit & ~bits] = 1
    idx[acc] = 3
    png = to_png(np.kron(idx, np.ones((S, S), np.uint8)), [None, BG, INK, ACCENT])
    sky = atkinson(starfield(H // S, w, 0.010) * 0.95)
    sky[: 150 // S, 80 // S:] = False            # keep the constellation legible
    sky_png = to_png(np.kron(np.where(sky, 1, 0).astype(np.uint8), np.ones((S, S), np.uint8)), [None, INK])
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
  <title id="t">A dithered astronaut reaching toward a neural network drawn as a constellation</title>
  <style>{CSS_MOTION}
  .float{{transform-origin:180px 310px;transform-box:view-box}}
  </style>
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <image href="{data_uri(sky_png)}" width="{W}" height="{H}" style="image-rendering:pixelated"/>
  {twinkles(W, H, 5, avoid=lambda x, y: y < 150 and x > 80)}
  {network_constellation()}
  <g class="float"><image href="{data_uri(png)}" y="{DY}" width="{W}" height="420" style="image-rendering:pixelated"/></g>
  <rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" fill="none" stroke="{LINE}" stroke-width="1.5"/>
</svg>
'''
    (OUT / "astronaut.svg").write_text(svg, encoding="utf-8")


def horizon():
    W, H, S = 1200, 260, 2
    w, h = W // S, H // S
    moon, minside, _ = render_planet(w, h, cx=w * 0.5, cy=h + 1505, r=1560, light=(0.35, 0.9, 0.25),
                                     craters=True, cities=False)
    ex, ey, er = w * 0.73, 47, 19
    earth, einside, _ = render_planet(w, h, cx=ex, cy=ey, r=er, light=(-0.9, 0.25, 0.4), seed_off=4.2, cities=False)
    gray = np.where(minside, moon, np.maximum(earth, starfield(h, w, 0.005) * ~einside))
    bits = atkinson(gray)
    idx = np.where(bits, 2, 0).astype(np.uint8)
    idx[(minside | einside) & ~bits] = 1
    png = to_png(np.kron(idx, np.ones((S, S), np.uint8)), [None, BG, INK, ACCENT])
    bx, by, bs = int(ex * S - 46), int(ey * S - 46), 92
    label = "earth 0.97"
    cap = 'caption: "earth rising over a lunar horizon"'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
  <title id="t">Earth rising over a dithered lunar horizon, marked by a detection box labelled earth 0.97 and an image caption</title>
  <style>{CSS_MOTION}
  text{{font-family:{MONO}}}
  </style>
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <image href="{data_uri(png)}" width="{W}" height="{H}" style="image-rendering:pixelated"/>
  {twinkles(W, 140, 6, avoid=lambda x, y: bx - 30 < x < bx + bs + 30 and y < by + bs + 20)}
  <rect x="{bx}" y="{by}" width="{bs}" height="{bs}" fill="none" stroke="{ACCENT}" stroke-width="2"/>
  <rect x="{bx - 1}" y="{by - 22}" width="{len(label) * 8.4 + 14:.0f}" height="22" fill="{ACCENT}"/>
  <text x="{bx + 6}" y="{by - 6}" font-size="14" font-weight="700" fill="{BG}">{label}</text>
  <rect x="24" y="{H - 44}" width="{len(cap) * 8.4 + 24:.0f}" height="28" fill="{BG}" stroke="{LINE}"/>
  <text x="36" y="{H - 25}" font-size="14" fill="{INK}">{cap}</text>
</svg>
'''
    (OUT / "horizon.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    import sys
    jobs = {"banner": banner, "astronaut": astronaut, "horizon": horizon}
    for name in (sys.argv[1:] or jobs):
        jobs[name]()
        print("wrote", name + ".svg")
