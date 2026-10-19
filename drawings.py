"""Notebook plates after Leonardo, drawn as wireframes on the solforged.io sheet.

Each plate is a page of studies: one main figure, smaller figures in the
margins, labels, and mirrored notes. Coordinates are pixels on a 3840x2160
sheet; 3D figures use a small orthographic camera.
"""

from __future__ import annotations

import math
from xml.sax.saxutils import escape

W, H = 3840, 2160
FONT = "Berkeley Mono Variable, Berkeley Mono, monospace"
PHI = (1 + math.sqrt(5)) / 2

QUOTES = {
    "sol": ["il sole", "no si move"],
    "sapientia": ["la sapientia è", "figliola della", "sperientia"],
    "tempo": ["o tempo, consumatore", "delle cose, e o invidiosa", "antichità"],
    "vacuus": [
        "nessuna humana investigatione",
        "si pò dimandare vera scientia",
        "s'essa non passa per le",
        "matematiche dimostrationi",
    ],
    "occhio": [
        "l'occhio, che si dice",
        "finestra dell'anima, è la",
        "principale via donde il",
        "comune senso può più copiosa-",
        "mente considerare le infinite",
        "opere di natura",
    ],
    "sentimenti": ["ogni nostra cognitione", "prencipia da' sentimenti"],
}


# ---------------------------------------------------------------- vectors

def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    n = math.sqrt(dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


class Cam:
    """Orthographic camera: yaw about y, then pitch about x; y is up."""

    def __init__(self, cx, cy, scale=1.0, yaw=0.0, pitch=0.0):
        self.cx, self.cy, self.scale = cx, cy, scale
        self.cy_, self.sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        self.cp_, self.sp_ = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def rot(self, v):
        x, y, z = v
        x, z = self.cy_ * x + self.sy_ * z, -self.sy_ * x + self.cy_ * z
        y, z = self.cp_ * y - self.sp_ * z, self.sp_ * y + self.cp_ * z
        return x, y, z

    def __call__(self, v):
        x, y, _ = self.rot(v)
        return self.cx + x * self.scale, self.cy - y * self.scale

    def facing(self, normal) -> bool:
        return self.rot(normal)[2] > 1e-6


def basis(n):
    n = norm(n)
    helper = (0, 1, 0) if abs(n[1]) < 0.9 else (1, 0, 0)
    u = norm(cross(n, helper))
    return u, cross(n, u)


def circle3d(c, n, r, steps=72, a0=0.0, a1=2 * math.pi):
    u, w = basis(n)
    return [add(c, add(mul(u, r * math.cos(a0 + (a1 - a0) * k / steps)), mul(w, r * math.sin(a0 + (a1 - a0) * k / steps))))
            for k in range(steps + 1)]


# ---------------------------------------------------------------- sheet

def f(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def pt(x: float, y: float) -> str:
    return f"{f(x)},{f(y)}"


class Sheet:
    """One plate: desk, sheet, grid and the SVG fragments drawn on it."""

    def __init__(self, palette: dict, plate: str, title: str):
        self.p = palette
        self.parts: list[str] = []
        self.defs: list[str] = []
        self.plate = plate
        self.title = title
        self.inset = 44

    def add(self, s: str) -> None:
        self.parts.append(s)

    def stroke(self, role, width, dash=None, opacity=1.0) -> str:
        s = f'fill="none" stroke="{self.p[role]}" stroke-width="{f(width)}"'
        if dash:
            s += f' stroke-dasharray="{dash}"'
        if opacity < 1:
            s += f' stroke-opacity="{f(opacity)}"'
        return s + ' stroke-linecap="round" stroke-linejoin="round"'

    def line(self, x1, y1, x2, y2, role="line", width=1.2, dash=None, opacity=1.0):
        self.add(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" {self.stroke(role, width, dash, opacity)}/>')

    def circle(self, cx, cy, r, role="gilt", width=2.0, dash=None, opacity=1.0, fill=None):
        attrs = self.stroke(role, width, dash, opacity)
        if fill:
            attrs = attrs.replace('fill="none"', f'fill="{fill}"')
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" {attrs}/>')

    def path(self, d, role="gilt", width=2.0, dash=None, opacity=1.0, fill=None):
        attrs = self.stroke(role, width, dash, opacity)
        if fill:
            attrs = attrs.replace('fill="none"', f'fill="{fill}"')
        self.add(f'<path d="{d}" {attrs}/>')

    def poly(self, pts, role="gilt", width=2.0, dash=None, opacity=1.0, closed=False, fill=None):
        d = "M" + " L".join(pt(*q) for q in pts) + (" Z" if closed else "")
        self.path(d, role, width, dash, opacity, fill)

    def poly3(self, cam, pts, role="gilt", width=2.0, dash=None, opacity=1.0, closed=False):
        self.poly([cam(p) for p in pts], role, width, dash, opacity, closed)

    def line3(self, cam, a, b, role="gilt", width=1.4, dash=None, opacity=1.0):
        self.line(*cam(a), *cam(b), role, width, dash, opacity)

    def text(self, x, y, s, role="muted", size=22, anchor="start", opacity=1.0, spacing=0.0, mirror=False, rotate=0.0):
        op = f' fill-opacity="{f(opacity)}"' if opacity < 1 else ""
        sp = f' letter-spacing="{f(spacing)}"' if spacing else ""
        tf = f"translate({f(x)},{f(y)})"
        if rotate:
            tf += f" rotate({f(rotate)})"
        if mirror:
            # Leonardo wrote right to left; the glyphs are reflected in place.
            tf += " scale(-1,1)"
        self.add(f'<text transform="{tf}" font-family="{FONT}" font-size="{f(size)}" fill="{self.p[role]}" '
                 f'text-anchor="{anchor}"{op}{sp}>{escape(s)}</text>')

    def clip(self, shape: str) -> str:
        cid = f"c{len(self.defs)}"
        self.defs.append(f'<clipPath id="{cid}">{shape}</clipPath>')
        return cid

    def hatch(self, pts, angle=45.0, spacing=10.0, role="gilt", width=0.8, opacity=0.4):
        """Parallel pen hatching clipped to a polygon."""
        cid = self.clip(f'<polygon points="{" ".join(pt(*q) for q in pts)}"/>')
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        r = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 2
        a = math.radians(angle)
        dx, dy = math.cos(a), math.sin(a)
        lines = []
        t = -r
        while t <= r:
            ox, oy = cx - dy * t, cy + dx * t
            lines.append(f'<line x1="{f(ox - dx * r)}" y1="{f(oy - dy * r)}" x2="{f(ox + dx * r)}" y2="{f(oy + dy * r)}"/>')
            t += spacing
        self.add(f'<g clip-path="url(#{cid})" {self.stroke(role, width, None, opacity)}>{"".join(lines)}</g>')

    def crosshair(self, cx, cy, r, role="line", width=1.0, opacity=1.0):
        self.line(cx - r, cy, cx + r, cy, role, width, "3 9", opacity)
        self.line(cx, cy - r, cx, cy + r, role, width, "3 9", opacity)

    def arrow(self, x, y, ux, uy, role="rubric", size=14):
        nx, ny = -uy, ux
        self.poly([(x - ux * size + nx * size * 0.35, y - uy * size + ny * size * 0.35), (x, y),
                   (x - ux * size - nx * size * 0.35, y - uy * size - ny * size * 0.35)], role, 1.2)

    def dimension(self, x1, y1, x2, y2, label, offset=40, role="rubric", size=20):
        """Dimension line parallel to (x1,y1)-(x2,y2), offset to its left."""
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy)
        ux, uy = dx / n, dy / n
        nx, ny = -uy, ux
        ax, ay = x1 + nx * offset, y1 + ny * offset
        bx, by = x2 + nx * offset, y2 + ny * offset
        sgn = 1 if offset >= 0 else -1
        self.line(x1 + nx * 6 * sgn, y1 + ny * 6 * sgn, ax + nx * 10 * sgn, ay + ny * 10 * sgn, "line", 0.9)
        self.line(x2 + nx * 6 * sgn, y2 + ny * 6 * sgn, bx + nx * 10 * sgn, by + ny * 10 * sgn, "line", 0.9)
        self.line(ax, ay, bx, by, role, 1.1)
        self.arrow(ax, ay, -ux, -uy, role)
        self.arrow(bx, by, ux, uy, role)
        angle = math.degrees(math.atan2(uy, ux))
        if angle > 90 or angle < -90:
            angle += 180
        mx, my = (ax + bx) / 2 + nx * 14 * sgn, (ay + by) / 2 + ny * 14 * sgn
        self.text(mx, my + 6, label, role, size, "middle", rotate=angle)

    def leader(self, x, y, tx, ty, label, role="muted", size=20):
        """A labelled leader from a point on the drawing to a note in the margin."""
        self.circle(x, y, 3.5, "rubric", 1.1)
        self.line(x, y, tx, ty, "line", 0.9)
        anchor = "start" if tx >= x else "end"
        self.line(tx, ty, tx + (14 if anchor == "start" else -14), ty, "line", 0.9)
        self.text(tx + (22 if anchor == "start" else -22), ty + 7, label, role, size, anchor)

    def fig(self, x, y, num, title):
        self.text(x, y, f"FIG. {num}", "rubric", 19, spacing=3)
        self.text(x, y + 30, title, "ink", 22)

    def title_block(self, num, title, sub):
        self.text(300, 330, f"FIG. {num}", "rubric", 24, spacing=4)
        self.text(300, 376, title, "ink", 30)
        self.text(300, 414, sub, "muted", 21, spacing=1)
        self.line(300, 446, 860, 446, "line", 1.0)

    def notes(self, x, y, lines, size=24, leading=36):
        for i, s in enumerate(lines):
            self.text(x, y + i * leading, s, "muted", size, "start", 0.5, mirror=True)

    def scale_bar(self, x, y, units=4, unit=90):
        self.line(x, y, x + units * unit, y, "muted", 1.3)
        for k in range(units + 1):
            self.line(x + k * unit, y - (12 if k % 2 == 0 else 7), x + k * unit, y, "muted", 1.3)
            if k % 2 == 0:
                self.text(x + k * unit, y + 32, str(k), "muted", 18, "middle")
        for k in range(0, units, 2):
            self.path(f"M{pt(x + k * unit, y)} h{unit} v5 h{-unit} Z", "muted", 1.0, fill=self.p["muted"], opacity=0.8)
        self.text(x + units * unit + 24, y + 6, "braccia", "muted", 18)

    def svg(self) -> str:
        p, i = self.p, self.inset
        sw, sh = W - 2 * i, H - 2 * i
        head = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <pattern id="minor" width="40" height="40" patternUnits="userSpaceOnUse" x="{i}" y="{i}">
    <path d="M40 0H0V40" fill="none" stroke="{p['grid']}" stroke-width="1" stroke-opacity="0.4"/>
  </pattern>
  <pattern id="major" width="200" height="200" patternUnits="userSpaceOnUse" x="{i}" y="{i}">
    <path d="M200 0H0V200" fill="none" stroke="{p['grid']}" stroke-width="1.2"/>
  </pattern>
  <radialGradient id="wash" cx="0.6" cy="0.5" r="0.75">
    <stop offset="0" stop-color="{p['slip']}" stop-opacity="0.55"/>
    <stop offset="1" stop-color="{p['sheet']}" stop-opacity="0"/>
  </radialGradient>
  {"".join(self.defs)}
</defs>
<rect width="{W}" height="{H}" fill="{p['desk']}"/>
<rect x="{i}" y="{i}" width="{sw}" height="{sh}" fill="{p['sheet']}"/>
<rect x="{i}" y="{i}" width="{sw}" height="{sh}" fill="url(#wash)"/>
<rect x="{i}" y="{i}" width="{sw}" height="{sh}" fill="url(#minor)"/>
<rect x="{i}" y="{i}" width="{sw}" height="{sh}" fill="url(#major)"/>
<rect x="{i + 0.7}" y="{i + 0.7}" width="{sw - 1.4}" height="{sh - 1.4}" fill="none" stroke="{p['line']}" stroke-width="1.4"/>
"""
        ticks = []
        for (cx, cy, sx, sy) in ((i + 36, i + 36, 1, 1), (W - i - 36, i + 36, -1, 1),
                                 (i + 36, H - i - 36, 1, -1), (W - i - 36, H - i - 36, -1, -1)):
            ticks.append(f'<path d="M{pt(cx, cy + sy * 22)} V{f(cy)} H{f(cx + sx * 22)}" fill="none" '
                         f'stroke="{p["muted"]}" stroke-width="2" stroke-opacity="0.7"/>')
        foot = (f'<text x="{W - i - 72}" y="{H - i - 64}" font-family="{FONT}" font-size="21" '
                f'fill="{p["muted"]}" fill-opacity="0.75" text-anchor="end" letter-spacing="3">'
                f'{escape(self.plate)}  ·  {escape(self.title)}</text>')
        return head + "\n".join(ticks) + "\n" + "\n".join(self.parts) + "\n" + foot + "\n</svg>\n"


# ---------------------------------------------------------------- shared figures

def wired_sun(s: Sheet, cx, cy, r, role="gilt", width=2.4):
    """The Solforge mark: ringed sun, compass ticks, one filled quadrant."""
    s.circle(cx, cy, r, role, width)
    k = r / 14
    for (a, b) in ((-21, -17), (17, 21)):
        s.line(cx, cy + a * k, cx, cy + b * k, role, width)
        s.line(cx + a * k, cy, cx + b * k, cy, role, width)
    s.line(cx - 9.9 * k, cy + 9.9 * k, cx + 9.9 * k, cy - 9.9 * k, role, width)
    s.path(f"M{pt(cx, cy)} V{f(cy - r)} A{f(r)},{f(r)} 0 0 1 {pt(cx + r, cy)} Z", role, 0.1, fill=s.p[role])


def gear_path(cx, cy, teeth, module, rot):
    """Spur gear outline with arced tips and roots."""
    rp = module * teeth / 2
    ra, rr = rp + module, rp - 1.25 * module
    step = 2 * math.pi / teeth
    wr, wt = 0.6 * step, 0.3 * step
    d = []
    for k in range(teeth):
        c = rot + k * step
        a0, a1, a2, a3 = c - wr / 2, c - wt / 2, c + wt / 2, c + wr / 2
        p0 = (cx + rr * math.cos(a0), cy + rr * math.sin(a0))
        p1 = (cx + ra * math.cos(a1), cy + ra * math.sin(a1))
        p2 = (cx + ra * math.cos(a2), cy + ra * math.sin(a2))
        p3 = (cx + rr * math.cos(a3), cy + rr * math.sin(a3))
        nxt = c + step - wr / 2
        p4 = (cx + rr * math.cos(nxt), cy + rr * math.sin(nxt))
        d += [("M" if k == 0 else "L") + pt(*p0), "L" + pt(*p1), f"A{f(ra)},{f(ra)} 0 0 1 {pt(*p2)}",
              "L" + pt(*p3), f"A{f(rr)},{f(rr)} 0 0 1 {pt(*p4)}"]
    return " ".join(d) + " Z", rp, ra, rr


def draw_gear(s: Sheet, cx, cy, teeth, module, rot, spokes=5, width=1.8, pitch=True, cross=True):
    d, rp, ra, rr = gear_path(cx, cy, teeth, module, rot)
    if pitch:
        s.circle(cx, cy, rp, "line", 0.9, "6 8")
    s.path(d, "gilt", width)
    hub = max(module * 2.2, rp * 0.16)
    if spokes:
        rim = rr - module * 1.4
        s.circle(cx, cy, rim, "gilt", width * 0.7)
        for k in range(spokes):
            a = rot * 0.5 + k * 2 * math.pi / spokes
            ox, oy = -math.sin(a), math.cos(a)
            half = max(module * 0.7, 4)
            for sgn in (1, -1):
                s.line(cx + hub * math.cos(a) + sgn * ox * half, cy + hub * math.sin(a) + sgn * oy * half,
                       cx + rim * math.cos(a) + sgn * ox * half, cy + rim * math.sin(a) + sgn * oy * half,
                       "gilt", width * 0.65)
    else:
        hub = rr * 0.45
    s.circle(cx, cy, hub, "gilt", width * 0.7)
    s.circle(cx, cy, hub * 0.4, "gilt", width * 0.6)
    if cross:
        s.crosshair(cx, cy, ra + 30)
    return rp, ra


def mesh_rotation(rot1, teeth1, teeth2, phi):
    """Rotation for gear 2 at direction phi from gear 1 so the teeth interleave."""
    step1, step2 = 2 * math.pi / teeth1, 2 * math.pi / teeth2
    t1 = ((phi - rot1) / step1) % 1.0
    return phi + math.pi - (0.5 - t1) * step2


def gear_points(cx, cy, teeth, module, rot, steps=3):
    """The gear_path outline as points, for drawing a wheel in a 3D plane."""
    rp = module * teeth / 2
    ra, rr = rp + module, rp - 1.25 * module
    step = 2 * math.pi / teeth
    wr, wt = 0.6 * step, 0.3 * step

    def polar(r, a):
        return cx + r * math.cos(a), cy + r * math.sin(a)

    pts = []
    for k in range(teeth):
        c = rot + k * step
        a0, a1, a2, a3 = c - wr / 2, c - wt / 2, c + wt / 2, c + wr / 2
        nxt = c + step - wr / 2
        pts.append(polar(rr, a0))
        pts += [polar(ra, a1 + (a2 - a1) * j / steps) for j in range(steps + 1)]
        pts += [polar(rr, a3 + (nxt - a3) * j / steps) for j in range(steps)]
    return pts


def escape_points(cx, cy, r, teeth=30, h=None, rot=0.0):
    """Saw-toothed escape wheel outline as points."""
    h = h or r * 0.16
    pts = []
    for k in range(teeth):
        a0 = rot + k * 2 * math.pi / teeth
        a1 = a0 + 2 * math.pi / teeth
        pts.append((cx + r * math.cos(a0), cy + r * math.sin(a0)))
        pts.append((cx + (r + h) * math.cos(a0 + 0.05), cy + (r + h) * math.sin(a0 + 0.05)))
        pts += [(cx + r * math.cos(a0 + 0.05 + (a1 - a0 - 0.05) * j / 4), cy + r * math.sin(a0 + 0.05 + (a1 - a0 - 0.05) * j / 4))
                for j in range(1, 4)]
    return pts


def escape_wheel(s: Sheet, cx, cy, r, teeth=30, h=None, rot=0.0, width=1.8):
    s.poly(escape_points(cx, cy, r, teeth, h, rot), "gilt", width, closed=True)


def box_edges(s: Sheet, cam, x0, x1, y0, y1, z0, z1, width=1.8):
    """Wire box; edges between two hidden faces are dashed. Returns the visible faces."""
    v = {(i, j, k): (x, y, z) for i, x in enumerate((x0, x1)) for j, y in enumerate((y0, y1)) for k, z in enumerate((z0, z1))}
    faces = {("x", 0): (-1, 0, 0), ("x", 1): (1, 0, 0), ("y", 0): (0, -1, 0), ("y", 1): (0, 1, 0),
             ("z", 0): (0, 0, -1), ("z", 1): (0, 0, 1)}
    visible = {key for key, n in faces.items() if cam.facing(n)}
    axes = "xyz"
    for a in v:
        for axis in range(3):
            if a[axis] == 0:
                b = list(a)
                b[axis] = 1
                b = tuple(b)
                touching = [(axes[o], a[o]) for o in range(3) if o != axis]
                shown = any(t in visible for t in touching)
                s.line3(cam, v[a], v[b], "gilt", width if shown else 1.0, None if shown else "6 7", 1.0 if shown else 0.8)
    return visible


# ---------------------------------------------------------------- solids

def _signs(p):
    out = {()}
    for c in p:
        out = {o + (c,) for o in out} | ({o + (-c,) for o in out} if c else set())
    return out


def _cyclic(p):
    x, y, z = p
    return set().union(*(_signs(q) for q in ((x, y, z), (z, x, y), (y, z, x))))


def solid(name):
    verts = {
        "tetra": {(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)},
        "cube": _signs((1, 1, 1)),
        "octa": _cyclic((1, 0, 0)),
        "icosa": _cyclic((0, 1, PHI)),
        "dodeca": _signs((1, 1, 1)) | _cyclic((0, 1 / PHI, PHI)),
        "cubocta": _cyclic((1, 1, 0)),
        "rhombicubocta": _cyclic((1, 1, 1 + math.sqrt(2))),
    }[name]
    verts = sorted(verts)
    r = math.sqrt(dot(verts[0], verts[0]))
    return [mul(v, 1 / r) for v in verts]


def hull_faces(verts):
    """Faces of a convex solid as (outward normal, ordered vertex indices, centroid)."""
    found = {}
    n = len(verts)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                nrm = cross(sub(verts[j], verts[i]), sub(verts[k], verts[i]))
                length = math.sqrt(dot(nrm, nrm))
                if length < 1e-9:
                    continue
                nrm = mul(nrm, 1 / length)
                d = dot(nrm, verts[i])
                side = [dot(nrm, v) - d for v in verts]
                if all(x <= 1e-6 for x in side):
                    pass
                elif all(x >= -1e-6 for x in side):
                    nrm = mul(nrm, -1)
                else:
                    continue
                key = frozenset(m for m, x in enumerate(side) if abs(x) < 1e-6)
                found.setdefault(key, nrm)
    faces = []
    for key, nrm in found.items():
        idx = list(key)
        c = mul(tuple(sum(verts[m][q] for m in idx) for q in range(3)), 1 / len(idx))
        u = norm(sub(verts[idx[0]], c))
        w = cross(nrm, u)
        idx.sort(key=lambda m: math.atan2(dot(sub(verts[m], c), w), dot(sub(verts[m], c), u)))
        faces.append((nrm, idx, c))
    return faces


def draw_solid(s: Sheet, cam, verts, beam=0.66, width=2.0, hatch=True):
    """Leonardo's 'vacuus' rendering: each face a frame, the far side dashed through it."""
    faces = hull_faces(verts)
    proj = [cam(v) for v in verts]
    back = set()
    front = []
    for nrm, idx, c in faces:
        if cam.facing(nrm):
            front.append((nrm, idx, c))
        else:
            for a, b in zip(idx, idx[1:] + idx[:1]):
                back.add(tuple(sorted((a, b))))
    for a, b in back:
        s.line(*proj[a], *proj[b], "line", 1.0, "6 7")
    light = norm((-0.5, 0.6, 0.62))
    for nrm, idx, c in front:
        outer = [proj[m] for m in idx]
        inner = [cam(add(c, mul(sub(verts[m], c), beam))) for m in idx]
        s.poly(outer, "gilt", width, closed=True)
        s.poly(inner, "gilt", width * 0.6, closed=True)
        if hatch and dot(cam.rot(nrm), light) < 0.12:
            for k in range(len(outer)):
                o0, o1 = outer[k], outer[(k + 1) % len(outer)]
                i0, i1 = inner[k], inner[(k + 1) % len(inner)]
                for t in (0.25, 0.5, 0.75):
                    s.line(*lerp(o0, o1, t), *lerp(i0, i1, t), "gilt", 0.8, opacity=0.5)
    return proj


def hang(s: Sheet, proj, top_y):
    """Hang a solid from a cord by its highest projected vertex, as in Pacioli's plates."""
    x, y = min(proj, key=lambda q: q[1])
    s.line(x, y, x, top_y, "muted", 1.1)
    s.circle(x, y - 14, 9, "muted", 1.2)


# ---------------------------------------------------------------- plate I: specchio ustorio

def plate_specchio(s: Sheet):
    """Sunlight gathered by a burning mirror into the crucible of a forge."""
    cam = Cam(2620, 1130, 1.0, yaw=10, pitch=9)
    a = norm((-0.7, 0.45, 0.62))
    u = norm(cross((0, 1, 0), a))
    w = cross(a, u)
    R, foc, ground, sun_d = 270, 380, -330, 2000

    def dish(rho, th, back=0.0):
        return add(mul(a, rho * rho / (4 * foc) - back), add(mul(u, rho * math.cos(th)), mul(w, rho * math.sin(th))))

    F = mul(a, foc)
    S = cam(mul(a, sun_d))

    # Floor of the workshop.
    s.poly3(cam, [(-1000, ground, -430), (720, ground, -430), (720, ground, 430), (-1000, ground, 430)],
            "line", 1.0, "3 9", closed=True)

    # Sun, its rings, and the parallel light it sends along the mirror's axis.
    wired_sun(s, *S, 56, "gilt", 2.2)
    s.circle(*S, 84, "gilt", 1.1)
    s.circle(*S, 108, "line", 1.0, "4 7")
    for k in range(48):
        t = k * 2 * math.pi / 48
        r1 = 122 if k % 2 else 124
        r2 = 136 if k % 4 else (196 if k % 12 == 0 else 158)
        s.line(S[0] + r1 * math.cos(t), S[1] + r1 * math.sin(t), S[0] + r2 * math.cos(t), S[1] + r2 * math.sin(t),
               "gilt", 1.0, opacity=0.8)
    s.text(S[0] - 150, S[1] - 150, "SOL", "rubric", 22, "end", spacing=6)

    rays = [dish(R, math.radians(d)) for d in range(0, 360, 30)]
    rays += [dish(R * 0.55, math.radians(d)) for d in range(15, 360, 60)]
    for P in rays:
        s.line3(cam, add(P, mul(a, sun_d - 150)), P, "gilt", 0.9, "12 9", 0.7)
    for P in rays:
        s.line3(cam, P, F, "rubric", 1.1, None, 0.9)

    # Mount: turntable, column, fork and a toothed elevation sector worked by a worm.
    base = (0, ground, 0)
    top = add(base, (0, 22, 0))
    for c, r in ((base, 140), (top, 140), (top, 112)):
        s.poly3(cam, circle3d(c, (0, 1, 0), r), "gilt", 1.4 if r == 140 else 1.0)
    for k in range(72):
        t = k * 2 * math.pi / 72
        s.line3(cam, add(top, (140 * math.cos(t), 0, 140 * math.sin(t))), add(top, (152 * math.cos(t), 0, 152 * math.sin(t))),
                "gilt", 0.9, None, 0.8)
    worm_c = add(top, (0, -8, 172))
    for dz in (-60, 60):
        s.poly3(cam, circle3d(add(worm_c, (dz, 0, 0)), (1, 0, 0), 13), "gilt", 1.1)
    for dy in (-13, 13):
        s.line3(cam, add(worm_c, (-60, dy, 0)), add(worm_c, (60, dy, 0)), "gilt", 1.1)
    s.poly3(cam, [add(worm_c, (x, 13 * math.cos(x / 6), 13 * math.sin(x / 6))) for x in range(-60, 61, 3)], "gilt", 0.8)

    yoke = (0, -215, 0)
    for dx in (-11, 11):
        s.line3(cam, add(top, (dx, 0, 0)), add(yoke, (dx, 0, 0)), "gilt", 1.6)
    pivots = [dish(R, 0), dish(R, math.pi)]
    for side, P in zip((1, -1), pivots):
        foot = add(yoke, mul(u, side * 46))
        for off in (-7, 7):
            s.line3(cam, add(foot, mul(a, off)), add(add(P, mul(u, side * 18)), mul(a, off)), "gilt", 1.4)
        s.poly3(cam, circle3d(add(P, mul(u, side * 18)), u, 15), "gilt", 1.2)
    s.line3(cam, add(yoke, mul(u, -46)), add(yoke, mul(u, 46)), "gilt", 1.6)

    piv = add(pivots[0], mul(u, 26))
    up_w = w
    arc = [add(piv, add(mul(a, 118 * math.cos(t)), mul(up_w, 118 * math.sin(t))))
           for t in [math.radians(d) for d in range(150, 291, 3)]]
    s.poly3(cam, arc, "gilt", 1.4)
    for d in range(150, 291, 5):
        t = math.radians(d)
        dirv = add(mul(a, math.cos(t)), mul(up_w, math.sin(t)))
        s.line3(cam, add(piv, mul(dirv, 118)), add(piv, mul(dirv, 130)), "gilt", 0.9)
    for d in (150, 220, 290):
        t = math.radians(d)
        s.line3(cam, piv, add(piv, mul(add(mul(a, math.cos(t)), mul(up_w, math.sin(t))), 118)), "gilt", 1.0)

    # The mirror: a paraboloid in meridians and parallels, ribbed behind.
    hub = mul(a, -46)
    for k in range(6):
        s.line3(cam, dish(R, k * math.pi / 3, 4), hub, "line", 1.0, "5 6")
    for deg in range(0, 360, 15):
        th = math.radians(deg)
        s.poly3(cam, [dish(R * k / 16, th) for k in range(17)], "gilt", 0.8, None, 0.6)
    for frac in (0.25, 0.5, 0.75):
        s.poly3(cam, [dish(R * frac, math.radians(d)) for d in range(0, 361, 5)], "gilt", 0.9, None, 0.7)
    s.poly3(cam, [dish(R, math.radians(d)) for d in range(0, 361, 4)], "gilt", 2.2)
    s.poly3(cam, [dish(R, math.radians(d), 9) for d in range(0, 361, 4)], "gilt", 1.0)

    # Forge: a low brick hearth of coals, and a crucible on a tripod at the focus.
    hx0, hx1 = F[0] - 230, F[0] + 150
    hz0, hz1 = F[2] - 140, F[2] + 140
    htop = ground + 170
    visible = box_edges(s, cam, hx0, hx1, ground, htop, hz0, hz1, 1.8)
    side_x = hx1 if ("x", 1) in visible else hx0
    course = 34
    for y in range(int(ground) + course, int(htop), course):
        s.line3(cam, (hx0, y, hz1), (hx1, y, hz1), "gilt", 0.8, None, 0.7)
        s.line3(cam, (side_x, y, hz0), (side_x, y, hz1), "gilt", 0.8, None, 0.7)
    for row in range(int((htop - ground) // course) + 1):
        y0 = ground + row * course
        y1 = min(y0 + course, htop)
        off = 0 if row % 2 else 34
        x = hx0 + off + 34
        while x < hx1:
            s.line3(cam, (x, y0, hz1), (x, y1, hz1), "gilt", 0.7, None, 0.6)
            x += 68
        z = hz0 + off + 34
        while z < hz1:
            s.line3(cam, (side_x, y0, z), (side_x, y1, z), "gilt", 0.7, None, 0.6)
            z += 68
    s.hatch([cam((side_x, ground, hz0)), cam((side_x, htop, hz0)), cam((side_x, htop, hz1)), cam((side_x, ground, hz1))],
            60, 9, "gilt", 0.7, 0.3)
    s.poly3(cam, [(hx0 + 30, htop, hz0 + 30), (hx1 - 30, htop, hz0 + 30), (hx1 - 30, htop, hz1 - 30), (hx0 + 30, htop, hz1 - 30)],
            "gilt", 1.0, None, 0.8, closed=True)
    coals = [(-150, -80, 16), (-110, 40, 13), (-60, -20, 15), (-20, 85, 12), (30, -90, 14), (60, 20, 16), (100, -40, 12),
             (-170, 70, 11), (110, 80, 13), (-80, 100, 10), (0, -45, 11), (-130, -20, 12)]
    for (dx, dz, r) in coals:
        s.poly3(cam, circle3d((F[0] + dx, htop + 6, F[2] + dz), (0, 1, 0), r, 24), "rubric", 0.9, None, 0.8)
    cb, ct = (F[0], F[1] - 70, F[2]), (F[0], F[1] - 4, F[2])
    for k in range(3):
        t = k * 2 * math.pi / 3 + 0.4
        s.line3(cam, add(cb, (30 * math.cos(t), 0, 30 * math.sin(t))), (F[0] + 95 * math.cos(t), htop, F[2] + 95 * math.sin(t)),
                "gilt", 1.4)
    s.poly3(cam, circle3d(add(cb, (0, -40, 0)), (0, 1, 0), 52, 48), "gilt", 1.0)
    s.poly3(cam, circle3d(cb, (0, 1, 0), 34, 48), "gilt", 1.3)
    s.poly3(cam, circle3d(ct, (0, 1, 0), 50, 48), "gilt", 1.6)
    s.poly3(cam, circle3d(ct, (0, 1, 0), 43, 48), "gilt", 0.9)
    for k in range(10):
        t = k * 2 * math.pi / 10
        s.line3(cam, add(cb, (34 * math.cos(t), 0, 34 * math.sin(t))), add(ct, (50 * math.cos(t), 0, 50 * math.sin(t))),
                "gilt", 0.8, None, 0.6)
    fx, fy = cam(F)
    for dx, hgt in ((-18, 54), (0, 78), (18, 48)):
        s.path(f"M{pt(fx + dx, fy + 6)} C{pt(fx + dx - 14, fy - hgt * 0.35)} {pt(fx + dx + 14, fy - hgt * 0.65)} {pt(fx + dx, fy - hgt)}",
               "rubric", 1.2)
    s.circle(fx, fy, 7, "rubric", 1.3)
    s.line(fx - 14, fy, fx + 14, fy, "rubric", 1.0)
    s.line(fx, fy - 14, fx, fy + 14, "rubric", 1.0)

    hinge = (hx0 - 6, htop - 40, F[2])
    s.line3(cam, hinge, add(hinge, (50, 0, 0)), "gilt", 2.0)
    length = 210

    def board(lift, t, side):
        x = hinge[0] - length * t
        half = 16 + 52 * math.sin(math.pi * min(1.0, t * 0.85 + 0.1))
        return (x, hinge[1] + lift * t, hinge[2] + side * half)

    ts = [k / 20 for k in range(21)]
    for lift in (80, -20):
        s.poly3(cam, [board(lift, t, 1) for t in ts] + [board(lift, t, -1) for t in reversed(ts)], "gilt", 1.5, closed=True)
    for k, t in enumerate([0.3 + k * 0.1 for k in range(8)]):
        top_p, bot_p = board(80, t, 1), board(-20, t, 1)
        mid = lerp(top_p, bot_p, 0.5)
        mid = (mid[0] + (8 if k % 2 else -8), mid[1], mid[2] + 10)
        s.poly3(cam, [top_p, mid, bot_p], "gilt", 0.9, None, 0.8)
    for lift in (80, -20):
        end = board(lift, 1.0, 0)
        s.line3(cam, end, add(end, (-56, lift * 0.25, 0)), "gilt", 1.4)
        s.poly3(cam, circle3d(add(end, (-63, lift * 0.25, 0)), (0, 0, 1), 7, 24), "gilt", 1.1)

    # Measures and names.
    V = cam((0, 0, 0))
    s.dimension(*V, fx, fy, "f = r² / 4p", offset=-46)
    s.leader(*S, S[0] + 260, S[1] - 120, "sole", "muted")
    rp = cam(dish(R, math.radians(300)))
    s.leader(*rp, rp[0] + 230, rp[1] + 130, "specchio ustorio", "muted")
    s.leader(fx, fy, fx - 260, fy - 150, "fuoco", "muted")
    hp = cam((hx0, (ground + htop) / 2, hz1))
    s.leader(*hp, hp[0] - 300, hp[1] + 120, "fucina", "muted")
    bp = cam(board(80, 0.7, 1))
    s.leader(*bp, bp[0] - 120, bp[1] - 150, "mantice", "muted")
    wp = cam(worm_c)
    s.leader(*wp, wp[0] + 260, wp[1] + 90, "vite perpetua", "muted")
    sp = cam(arc[len(arc) // 2])
    s.leader(*sp, sp[0] + 280, sp[1] - 40, "settore dentato", "muted")

    # FIG. 2: the parabola's construction.
    px, py, p = 3260, 700, 52
    s.fig(3060, 300, 2, "della parabola")
    para = [(px + x, py - x * x / (4 * p)) for x in range(-190, 191, 5)]
    s.poly(para, "gilt", 1.6)
    s.line(px - 230, py + p, px + 230, py + p, "line", 1.0, "8 6")
    s.text(px + 236, py + p + 6, "direttrice", "muted", 18)
    s.line(px, py + p + 20, px, py - 210, "line", 0.9, "3 7")
    s.circle(px, py - p, 5, "rubric", 1.2)
    s.text(px + 12, py - p - 10, "F", "rubric", 20)
    for x in (-160, -95, 60, 140):
        yv = py - x * x / (4 * p)
        s.line(px + x, py - 230, px + x, yv, "gilt", 0.9, "10 7", 0.8)
        s.line(px + x, yv, px, py - p, "rubric", 1.0)
    x = 140
    yv = py - x * x / (4 * p)
    s.line(px + x, yv, px + x, py + p, "line", 0.9, "2 6")
    slope = x / (2 * p)
    s.line(px + x - 110, yv + slope * 110, px + x + 80, yv - slope * 80, "line", 1.0)
    s.path(f"M{pt(px + x, yv - 34)} A34,34 0 0 1 {pt(px + x + 34 / math.hypot(1, slope), yv - 34 * slope / math.hypot(1, slope))}",
           "rubric", 1.0)
    s.text(px - 210, py + p + 52, "ogni raggio equidistante", "muted", 18)
    s.text(px - 210, py + p + 78, "al fuoco e alla direttrice", "muted", 18)

    # FIG. 3: anvil and hammer, extruded in oblique.
    ax_, ay_ = 760, 1520
    s.fig(470, 1210, 3, "incudine e martello")
    prof = [(-140, 0), (140, 0), (140, -28), (92, -46), (78, -104), (140, -112), (160, -140), (-56, -140), (-100, -138),
            (-150, -131), (-196, -118), (-232, -106), (-196, -98), (-140, -94), (-96, -90), (-82, -46), (-140, -28)]
    dx_, dy_ = 46, -26
    front = [(ax_ + x, ay_ + y) for x, y in prof]
    back = [(ax_ + x + dx_, ay_ + y + dy_) for x, y in prof]
    s.poly(back, "line", 1.0, "5 6", closed=True)
    s.poly(front, "gilt", 1.8, closed=True)
    for k in (0, 1, 2, 4, 5, 6, 7, 11):
        s.line(*front[k], *back[k], "gilt", 1.0)
    s.hatch(front[:7] + [front[7]], 135, 9, "gilt", 0.7, 0.3)
    y0, y1 = ay_, ay_ + 190
    s.path(f"M{pt(ax_ - 120, y0 + 6)} A120,26 0 0 0 {pt(ax_ + 140, y0 + 6)}", "gilt", 1.4)
    s.line(ax_ - 120, y0 + 6, ax_ - 112, y1, "gilt", 1.4)
    s.line(ax_ + 140, y0 + 6, ax_ + 132, y1, "gilt", 1.4)
    s.path(f"M{pt(ax_ - 112, y1)} A122,26 0 0 0 {pt(ax_ + 132, y1)}", "gilt", 1.4)
    for k in range(5):
        xx = ax_ - 80 + k * 44
        s.path(f"M{pt(xx, y0 + 34)} q6,70 -2,140", "gilt", 0.7, None, 0.5)
    hpiv, L = (ax_ + 330, ay_ - 330), 345
    for ang, dash, op in ((154, None, 1.0), (172, "6 7", 0.6), (190, "6 7", 0.35)):
        t = math.radians(ang)
        s.circle(*hpiv, 8, "gilt", 1.0, None, op)
        hx, hy = hpiv[0] + L * math.cos(t), hpiv[1] + L * math.sin(t)
        s.line(*hpiv, hx, hy, "gilt", 1.4, dash, op)
        nx, ny = -math.sin(t), math.cos(t)
        head = [(hx + nx * 48 - math.cos(t) * 14, hy + ny * 48 - math.sin(t) * 14),
                (hx + nx * 48 + math.cos(t) * 30, hy + ny * 48 + math.sin(t) * 30),
                (hx - nx * 40 + math.cos(t) * 30, hy - ny * 40 + math.sin(t) * 30),
                (hx - nx * 40 - math.cos(t) * 14, hy - ny * 40 - math.sin(t) * 14)]
        s.poly(head, "gilt", 1.6 if op == 1 else 1.0, dash, op, closed=True)
    t0, t1 = math.radians(196), math.radians(150)
    s.path(f"M{pt(hpiv[0] + (L + 60) * math.cos(t0), hpiv[1] + (L + 60) * math.sin(t0))} A{L + 60},{L + 60} 0 0 0 "
           f"{pt(hpiv[0] + (L + 60) * math.cos(t1), hpiv[1] + (L + 60) * math.sin(t1))}", "rubric", 1.0, "3 8")
    s.arrow(hpiv[0] + (L + 60) * math.cos(t1), hpiv[1] + (L + 60) * math.sin(t1), math.sin(t1), -math.cos(t1))
    for k in range(9):
        t = math.radians(-170 + k * 20)
        s.line(ax_ + 10 + 26 * math.cos(t), ay_ - 150 + 26 * math.sin(t),
               ax_ + 10 + (48 + 10 * (k % 3)) * math.cos(t), ay_ - 150 + (48 + 10 * (k % 3)) * math.sin(t), "rubric", 1.0)

    # FIG. 4: gnomon and the hours.
    gx, gy, gr = 640, 1010, 150
    s.fig(470, 650, 4, "gnomone")
    s.path(f"M{pt(gx - gr, gy)} A{gr},{gr} 0 0 1 {pt(gx + gr, gy)}", "gilt", 1.5)
    s.line(gx - gr - 20, gy, gx + gr + 20, gy, "gilt", 1.5)
    for k in range(13):
        t = math.pi + k * math.pi / 12
        s.line(gx, gy, gx + gr * math.cos(t), gy + gr * math.sin(t), "gilt", 0.7, None, 0.6)
        if k % 3 == 0:
            s.text(gx + (gr + 24) * math.cos(t), gy + (gr + 24) * math.sin(t) + 6, ["VI", "IX", "XII", "III", "VI"][k // 3], "muted", 16, "middle")
    s.poly([(gx, gy), (gx, gy - 70), (gx + 40, gy)], "gilt", 1.4, closed=True)
    t = math.pi + 4.2 * math.pi / 12
    s.line(gx, gy, gx + gr * 0.92 * math.cos(t), gy + gr * 0.92 * math.sin(t), "rubric", 1.6)
    for ang in (200, 250, 300):
        sx, sy = gx + 230 * math.cos(math.radians(ang)), gy - 70 + 140 * math.sin(math.radians(ang))
        s.circle(sx, sy, 12, "gilt", 1.0)
        s.circle(sx, sy, 4, "gilt", 1.0, fill=s.p["gilt"])
    s.path(f"M{pt(gx - 230, gy - 70)} A230,140 0 0 1 {pt(gx + 230, gy - 70)}", "line", 0.9, "3 7")

    # FIG. 5: the sun's daily course over Florence, on a wire hemisphere.
    s.fig(1180, 1400, 5, "corso del sole")
    hc = Cam(1460, 1720, 1.0, yaw=24, pitch=24)
    Rh, lat = 170, math.radians(43.77)
    s.poly3(hc, circle3d((0, 0, 0), (0, 1, 0), Rh), "gilt", 1.4)
    s.poly3(hc, circle3d((0, 0, 0), (0, 1, 0), Rh + 16), "line", 0.9)
    for k in range(72):
        t = k * 2 * math.pi / 72
        r2 = Rh + (16 if k % 6 == 0 else 8)
        s.line3(hc, (Rh * math.cos(t), 0, Rh * math.sin(t)), (r2 * math.cos(t), 0, r2 * math.sin(t)), "gilt", 0.7, None, 0.7)
    for az in range(0, 180, 30):
        d = (math.cos(math.radians(az)), 0, math.sin(math.radians(az)))
        s.poly3(hc, [add(mul(d, Rh * math.cos(t)), (0, Rh * math.sin(t), 0)) for t in [k * math.pi / 48 for k in range(49)]],
                "gilt", 0.7, None, 0.5)
    pole = (0, math.sin(lat), -math.cos(lat))
    s.line3(hc, mul(pole, -Rh * 1.3), mul(pole, Rh * 1.3), "rubric", 1.0, "8 5")
    for dec in (-23.44, 0.0, 23.44):
        dr = math.radians(dec)
        ring = circle3d(mul(pole, Rh * math.sin(dr)), pole, Rh * math.cos(dr), 120)
        for k in range(len(ring) - 1):
            up_ = ring[k][1] >= 0 and ring[k + 1][1] >= 0
            s.line3(hc, ring[k], ring[k + 1], "gilt" if up_ else "line", 1.3 if up_ else 0.8, None if up_ else "3 5")
        if dec > 0:
            sun_p = hc(max(ring, key=lambda q: q[1] - 0.3 * q[0]))
            s.circle(*sun_p, 11, "gilt", 1.2)
            s.circle(*sun_p, 4, "gilt", 1.0, fill=s.p["gilt"])
    s.text(1460, 1950, "lat. 43° 46′ · Firenze", "muted", 18, "middle")

    s.title_block("I", "specchio ustorio, con fucina", "sole · fuoco · fucina")
    s.notes(860, 560, QUOTES["sol"], 28, 42)
    s.notes(3560, 1620, QUOTES["sapientia"])
    s.scale_bar(300, 1900)


# ---------------------------------------------------------------- plate II: orologio

def plate_orologio(s: Sheet):
    """A weight-driven going train with an anchor escapement and pendulum."""
    m, re = 5, 112
    A, rotA = (-180.0, 160.0), 0.03
    phiAB, phiBC, phiCD = math.radians(-28), math.radians(-78), math.radians(14)
    zA, zb, zB, zc, zC, zd = 80, 10, 60, 8, 48, 8
    B = (A[0] + (zA + zb) * m / 2 * math.cos(phiAB), A[1] + (zA + zb) * m / 2 * math.sin(phiAB))
    C = (B[0] + (zB + zc) * m / 2 * math.cos(phiBC), B[1] + (zB + zc) * m / 2 * math.sin(phiBC))
    D = (C[0] + (zC + zd) * m / 2 * math.cos(phiCD), C[1] + (zC + zd) * m / 2 * math.sin(phiCD))
    E = (D[0], D[1] - re - 110)
    rotb = mesh_rotation(rotA, zA, zb, phiAB)
    rotB = 0.12
    rotc = mesh_rotation(rotB, zB, zc, phiBC)
    rotC = 0.2
    rotd = mesh_rotation(rotC, zC, zd, phiCD)

    # The train stands between two plates; each wheel sits at its own depth.
    cam = Cam(2140, 960, 1.0, yaw=-40, pitch=12)
    zplate, zA_, zB_, zC_, zE_, zpend = 110, 66, 6, -54, 36, -170

    def P3(x, y, z):
        return (x, -y, z)

    def at(x, y, z):
        return cam(P3(x, y, z))

    def flat(pts, z, role="gilt", width=1.6, dash=None, opacity=1.0, closed=True):
        s.poly3(cam, [P3(x, y, z) for x, y in pts], role, width, dash, opacity, closed)

    def ring(c, r, z, role="gilt", width=1.0, dash=None, opacity=1.0, steps=64):
        flat([(c[0] + r * math.cos(t), c[1] + r * math.sin(t)) for t in [k * 2 * math.pi / steps for k in range(steps)]],
             z, role, width, dash, opacity)

    def wheel(c, z, teeth, rot, spokes):
        flat(gear_points(*c, teeth, m, rot), z, "gilt", 1.6)
        rp = m * teeth / 2
        rr = rp - 1.25 * m
        ring(c, rp, z, "line", 0.8, "5 7")
        if spokes:
            rim, hub = rr - m * 1.4, rp * 0.16
            ring(c, rim, z, "gilt", 1.1)
            ring(c, hub, z, "gilt", 1.0, steps=32)
            for k in range(spokes):
                t = rot * 0.5 + k * 2 * math.pi / spokes
                for sg in (1, -1):
                    ox, oy = -math.sin(t) * 4 * sg, math.cos(t) * 4 * sg
                    s.line3(cam, P3(c[0] + hub * math.cos(t) + ox, c[1] + hub * math.sin(t) + oy, z),
                            P3(c[0] + rim * math.cos(t) + ox, c[1] + rim * math.sin(t) + oy, z), "gilt", 1.0)
        else:
            for dz in (-12, 12):
                flat(gear_points(*c, teeth, m, rot), z + dz, "gilt", 0.9, None, 0.7)

    def rounded(x0, y0, x1, y1, r):
        pts = []
        for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            pts += [(cx + r * math.cos(math.radians(a0 + d)), cy + r * math.sin(math.radians(a0 + d))) for d in range(0, 91, 10)]
        return pts

    plate = rounded(-440, -420, 390, 420, 70)
    flat(plate, -zplate, "line", 1.1, "8 7")
    pillars = [(-380, -360), (330, -360), (-380, 360), (330, 360)]
    for (px, py) in pillars:
        s.line3(cam, P3(px, py, -zplate), P3(px, py, zplate), "gilt", 1.2)
        for z in (-zplate, zplate):
            ring((px, py), 13, z, "gilt", 1.0, steps=24)

    # Pendulum, hung behind the back plate from the anchor's arbor.
    L = 860
    bob = (E[0], E[1] + L)
    s.line3(cam, P3(*E, zE_), P3(*E, zpend), "gilt", 1.2)
    for k in range(5):
        s.line3(cam, P3(E[0] - 16, E[1] - 30 - k * 7, zpend), P3(E[0] + 16, E[1] - 33 - k * 7, zpend), "gilt", 0.8)
    s.line3(cam, P3(E[0], E[1] - 30, zpend), P3(E[0], E[1] - 90, zpend), "muted", 1.0)
    for dx in (-3, 3):
        s.line3(cam, P3(E[0] + dx, E[1], zpend), P3(bob[0] + dx, bob[1] - 50, zpend), "gilt", 1.1)
    bc = P3(*bob, zpend)
    for n_ in ((0, 0, 1), (1, 0, 0), (0, 1, 0)):
        s.poly3(cam, circle3d(bc, n_, 50, 64), "gilt", 1.5 if n_ == (0, 0, 1) else 0.9)
    crutch_y = E[1] + 150
    s.line3(cam, P3(*E, zpend + 20), P3(E[0], crutch_y, zpend), "gilt", 1.0)
    s.poly3(cam, [P3(E[0] - 10, crutch_y - 6, zpend), P3(E[0] - 10, crutch_y + 6, zpend), P3(E[0] + 10, crutch_y + 6, zpend),
                  P3(E[0] + 10, crutch_y - 6, zpend)], "gilt", 1.0, closed=True)
    swing = 6
    for sg in (-1, 1):
        t = math.radians(90 + sg * swing)
        end = (E[0] + L * math.cos(t), E[1] + L * math.sin(t))
        s.line3(cam, P3(*E, zpend), P3(*end, zpend), "line", 0.9, "6 8")
        s.poly3(cam, circle3d(P3(*end, zpend), (0, 0, 1), 50, 48), "line", 0.8, "4 6", 0.7)
    arc = [(E[0] + (L + 80) * math.cos(math.radians(90 + d / 2)), E[1] + (L + 80) * math.sin(math.radians(90 + d / 2)))
           for d in range(-2 * swing - 4, 2 * swing + 5)]
    flat(arc, zpend, "rubric", 1.0, closed=False)
    for d in range(-swing - 2, swing + 3):
        t = math.radians(90 + d)
        r2 = L + 80 + (14 if d % 5 == 0 else 7)
        s.line3(cam, P3(E[0] + (L + 80) * math.cos(t), E[1] + (L + 80) * math.sin(t), zpend),
                P3(E[0] + r2 * math.cos(t), E[1] + r2 * math.sin(t), zpend), "rubric", 0.9)

    # Arbors, wheels and pinions.
    for c, z0, z1 in ((A, -zplate, zplate + 26), (B, -zplate, zplate), (C, -zplate, zplate), (D, -zplate, zplate),
                      (E, zpend, zplate)):
        s.line3(cam, P3(*c, z0), P3(*c, z1), "gilt", 1.1)
        for z in (-zplate, zplate):
            if z0 <= z <= z1:
                ring(c, 9, z, "gilt", 1.0, steps=20)
    sq = [(A[0] - 9, A[1] - 9), (A[0] + 9, A[1] - 9), (A[0] + 9, A[1] + 9), (A[0] - 9, A[1] + 9)]
    flat(sq, zplate + 26, "gilt", 1.2)
    for z in (-90, -20):
        ring(A, 70, z, "gilt", 1.3)
    for k in range(12):
        t = k * 2 * math.pi / 12
        s.line3(cam, P3(A[0] + 70 * math.cos(t), A[1] + 70 * math.sin(t), -90), P3(A[0] + 70 * math.cos(t), A[1] + 70 * math.sin(t), -20),
                "gilt", 0.8, None, 0.7)
    flat(escape_points(*A, 46, 16, 8, 0.2), zA_ + 14, "gilt", 1.1)
    wheel(C, zC_, zC, rotC, 4)
    wheel(D, zC_, zd, rotd, 0)
    wheel(B, zB_, zB, rotB, 5)
    wheel(C, zB_, zc, rotc, 0)
    wheel(A, zA_, zA, rotA, 6)
    wheel(B, zA_, zb, rotb, 0)
    flat(escape_points(*D, re, 30, 20, 0.04), zE_, "gilt", 1.7)
    ring(D, re - 26, zE_, "gilt", 1.0)
    for k in range(5):
        t = k * 2 * math.pi / 5
        s.line3(cam, P3(D[0] + 20 * math.cos(t), D[1] + 20 * math.sin(t), zE_),
                P3(D[0] + (re - 26) * math.cos(t), D[1] + (re - 26) * math.sin(t), zE_), "gilt", 0.9)

    # Anchor in the escape wheel's plane.
    for sg in (-1, 1):
        t = math.radians(-90 + sg * 38)
        tip = (D[0] + (re + 6) * math.cos(t), D[1] + (re + 6) * math.sin(t))
        dx, dy = tip[0] - E[0], tip[1] - E[1]
        n = math.hypot(dx, dy)
        ox, oy = -dy / n * 8, dx / n * 8
        flat([(E[0] + ox, E[1] + oy), (tip[0] + ox, tip[1] + oy), (tip[0] - ox, tip[1] - oy), (E[0] - ox, E[1] - oy)], zE_, "gilt", 1.4)
        flat([(tip[0] - ox * 1.6, tip[1] - oy * 1.6 + 6), (tip[0] + sg * 10, tip[1] + 24), (tip[0] + ox * 1.6, tip[1] + oy * 1.6 + 6)],
             zE_, "gilt", 1.4, closed=False)
    ring(E, 15, zE_, "gilt", 1.4, steps=24)

    # Weight on its cord from the barrel.
    wx, wz, wt, wb = A[0] - 70, -55, A[1] + 520, A[1] + 700
    s.line3(cam, P3(wx, A[1], wz), P3(wx, wt - 26, wz), "muted", 1.1)
    s.poly3(cam, circle3d(P3(wx, wt - 26, wz), (0, 0, 1), 9, 24), "muted", 1.0)
    for yy in (wt, wb):
        s.poly3(cam, circle3d(P3(wx, yy, wz), (0, 1, 0), 42, 48), "gilt", 1.4)
    for k in range(8):
        t = k * 2 * math.pi / 8
        s.line3(cam, P3(wx + 42 * math.cos(t), wt, wz + 42 * math.sin(t)), P3(wx + 42 * math.cos(t), wb, wz + 42 * math.sin(t)),
                "gilt", 1.2 if math.sin(t) > -0.3 else 0.7, None if math.sin(t) > -0.3 else "4 6")

    flat(plate, zplate, "gilt", 1.3)
    s.dimension(*at(*E, zpend), *at(*bob, zpend), "L", offset=-150)

    # Names.
    s.leader(*at(A[0] - 120, A[1] + 150, zA_), *at(A[0] - 440, A[1] + 250, zA_), "ruota maestra")
    s.leader(*at(wx, wt + 90, wz), *at(wx - 260, wt + 150, wz), "peso")
    s.leader(*at(A[0], A[1] + 70, -25), *at(A[0] + 250, A[1] + 520, -25), "tamburo")
    s.leader(*at(B[0] + 20, B[1] - 20, zA_), *at(B[0] + 600, B[1] + 200, zA_), "rocchetto")
    s.leader(*at(D[0] + re, D[1] + 30, zE_), *at(D[0] + 500, D[1] + 130, zE_), "ruota di scappamento")
    s.leader(*at(E[0] + 30, E[1] + 20, zE_), *at(E[0] + 480, E[1] - 100, zE_), "àncora")
    s.leader(*at(E[0], E[1] + 420, zpend), *at(E[0] + 420, E[1] + 440, zpend), "pendolo")
    s.leader(*at(330, -360, zplate), *at(520, -520, zplate), "cartella")

    # FIG. 2: the depthing of two teeth, enlarged in a circular field.
    gx, gy, gr = 3240, 620, 190
    s.fig(3040, 300, 2, "ingranaggio")
    cid = s.clip(f'<circle cx="{f(gx)}" cy="{f(gy)}" r="{f(gr)}"/>')
    sub_ = Sheet(s.p, "", "")
    m2 = 34
    g1 = (gx, gy + 18 * m2 / 2)
    g2 = (gx, g1[1] - (18 + 12) * m2 / 2)
    r1rot = 0.1
    draw_gear(sub_, *g1, 18, m2, r1rot, spokes=0, cross=False)
    draw_gear(sub_, *g2, 12, m2, mesh_rotation(r1rot, 18, 12, -math.pi / 2), spokes=0, cross=False)
    sub_.line(gx, gy - gr, gx, gy + gr, "line", 0.9, "3 7")
    pa = math.radians(20)
    sub_.line(gx - gr * math.cos(pa), gy - gr * math.sin(pa), gx + gr * math.cos(pa), gy + gr * math.sin(pa), "rubric", 1.2)
    s.add(f'<g clip-path="url(#{cid})">' + "".join(sub_.parts) + "</g>")
    s.circle(gx, gy, gr, "gilt", 1.6)
    s.circle(gx, gy, gr + 10, "line", 1.0)
    pp = (gx, g1[1] - 18 * m2 / 2)
    s.circle(*pp, 5, "rubric", 1.2)
    s.text(pp[0] + 14, pp[1] - 10, "P", "rubric", 20)
    s.text(gx + gr + 30, gy + 80, "angolo 20°", "muted", 18)

    # FIG. 3: a lantern pinion.
    s.fig(3040, 1050, 3, "rocchetto a lanterna")
    cam = Cam(3250, 1380, 1.0, yaw=34, pitch=24)
    for y in (-74, 74):
        s.poly3(cam, circle3d((0, y, 0), (0, 1, 0), 96), "gilt", 1.6)
        s.poly3(cam, circle3d((0, y, 0), (0, 1, 0), 22), "gilt", 1.0)
    for k in range(8):
        t = k * 2 * math.pi / 8
        p0, p1 = (74 * math.cos(t), -74, 74 * math.sin(t)), (74 * math.cos(t), 74, 74 * math.sin(t))
        s.line3(cam, p0, p1, "gilt", 1.4 if math.sin(t) > -0.2 else 0.9, None if math.sin(t) > -0.2 else "5 6")
    s.line3(cam, (0, -190, 0), (0, 190, 0), "line", 1.0, "8 6")

    # FIG. 4: verge and foliot, the older escapement.
    s.fig(470, 1180, 4, "verga e bilanciere")
    vc = Cam(780, 1660, 1.0, yaw=38, pitch=16)
    rc = 110
    s.poly3(vc, circle3d((0, 0, 0), (1, 0, 0), rc), "gilt", 1.6)
    s.poly3(vc, circle3d((-14, 0, 0), (1, 0, 0), rc), "gilt", 0.9)
    s.poly3(vc, circle3d((0, 0, 0), (1, 0, 0), rc - 30), "gilt", 0.9)
    for k in range(15):
        t0, t1 = k * 2 * math.pi / 15, (k + 0.6) * 2 * math.pi / 15
        base0 = (0, rc * math.cos(t0), rc * math.sin(t0))
        base1 = (0, rc * math.cos(t1), rc * math.sin(t1))
        tip = (34, rc * math.cos(t0), rc * math.sin(t0))
        s.poly3(vc, [base0, tip, base1], "gilt", 1.2)
    s.line3(vc, (-150, 0, 0), (60, 0, 0), "line", 1.0, "6 6")
    vx = 52
    s.line3(vc, (vx, -150, 0), (vx, 250, 0), "gilt", 1.6)
    for yy, flag in ((rc - 8, "z"), (-rc + 8, "x")):
        if flag == "z":
            s.poly3(vc, [(vx, yy - 14, 0), (vx, yy - 14, 36), (vx, yy + 14, 36), (vx, yy + 14, 0)], "rubric", 1.3, closed=True)
        else:
            s.poly3(vc, [(vx, yy - 14, 0), (vx + 36, yy - 14, 0), (vx + 36, yy + 14, 0), (vx, yy + 14, 0)], "rubric", 1.3, closed=True)
    s.line3(vc, (vx, 250, -200), (vx, 250, 200), "gilt", 1.8)
    for z in range(-180, 181, 20):
        s.line3(vc, (vx, 250, z), (vx, 258, z), "gilt", 0.8)
    for z in (-150, 150):
        s.poly3(vc, circle3d((vx, 250, z), (0, 0, 1), 16, 32), "gilt", 1.3)
        s.poly3(vc, circle3d((vx, 250, z), (0, 1, 0), 16, 32), "gilt", 0.8)
    s.line3(vc, (vx, 250, 0), (vx, 340, 0), "muted", 1.0)
    fp = vc((vx, 250, -150))
    s.leader(*fp, fp[0] + 330, fp[1] - 40, "regoli")

    s.title_block("II", "orologio a peso, con pendolo", "ruote · rocchetti · scappamento")
    s.text(300, 540, "80/10 · 60/8 · 48/8", "ink", 22)
    s.text(300, 574, "= 8 · 7½ · 6 = 360 : 1", "muted", 20)
    s.text(300, 608, "scappamento di 30 denti", "muted", 20)
    s.notes(860, 760, QUOTES["tempo"])
    s.scale_bar(300, 1900)


# ---------------------------------------------------------------- plate III: corpi vacui

def plate_vacui(s: Sheet):
    """Pacioli's hollow solids, as Leonardo drew them: one large, six hung in a row."""
    main = solid("rhombicubocta")
    cam = Cam(1560, 1080, 360, yaw=27, pitch=-19)
    R = 360
    s.circle(1560, 1080, R * 1.04, "line", 1.0, "8 10")
    s.circle(1560, 1080, R * 1.24, "line", 0.9, "2 10", 0.8)
    s.crosshair(1560, 1080, R * 1.32)
    s.path(f"M{pt(1560 - R * 1.04, 1080)} A{f(R * 1.04)},{f(R * 0.32)} 0 0 0 {pt(1560 + R * 1.04, 1080)}", "line", 0.9, "5 8")
    proj = draw_solid(s, cam, main, 0.66, 2.0)
    hang(s, proj, s.inset + 2)
    s.text(1560, 1080 + R * 1.32 + 52, "XXVI · vigintisex basium planus vacuus", "rubric", 20, "middle", spacing=2)

    small = [
        ("tetra", "II", "tetracedron", (22, 18)),
        ("octa", "VI", "octocedron", (35, 24)),
        ("cube", "IIII", "exacedron", (28, 22)),
        ("icosa", "XXII", "icocedron", (18, 16)),
        ("dodeca", "XXVIII", "duodecedron", (24, -18)),
        ("cubocta", "XIIII", "exacedron abscisus", (32, 20)),
    ]
    xs, ys, r = (2460, 2930, 3400), (760, 1460), 125
    for row, y in enumerate(ys):
        rail = y - r - 150
        s.line(xs[0] - 170, rail, xs[-1] + 170, rail, "gilt", 1.4)
        for xx in (xs[0] - 170, xs[-1] + 170):
            s.circle(xx, rail, 8, "gilt", 1.2)
        for col, x in enumerate(xs):
            name, num, label, (yaw, pitch) = small[row * 3 + col]
            cam = Cam(x, y, r, yaw=yaw, pitch=pitch)
            proj = draw_solid(s, cam, solid(name), 0.62, 1.6)
            hang(s, proj, rail)
            s.text(x, y + r + 60, num, "rubric", 19, "middle", spacing=3)
            s.text(x, y + r + 90, f"{label} vacuum", "muted", 18, "middle")

    # FIG. 2: the divine proportion.
    s.fig(300, 1190, 2, "divina proportione")
    x, y, w, h = 300, 1270, 560, 560 / PHI
    s.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], "gilt", 1.6, closed=True)
    for i in range(10):
        d = i % 4
        if d == 0:
            q = h
            s.line(x + q, y, x + q, y + h, "gilt", 1.0)
            s.path(f"M{pt(x, y + q)} A{f(q)},{f(q)} 0 0 1 {pt(x + q, y)}", "rubric", 1.2)
            x, w = x + q, w - q
        elif d == 1:
            q = w
            s.line(x, y + q, x + w, y + q, "gilt", 1.0)
            s.path(f"M{pt(x, y)} A{f(q)},{f(q)} 0 0 1 {pt(x + q, y + q)}", "rubric", 1.2)
            y, h = y + q, h - q
        elif d == 2:
            q = h
            s.line(x + w - q, y, x + w - q, y + h, "gilt", 1.0)
            s.path(f"M{pt(x + w, y)} A{f(q)},{f(q)} 0 0 1 {pt(x + w - q, y + q)}", "rubric", 1.2)
            w = w - q
        else:
            q = w
            s.line(x, y + h - q, x + w, y + h - q, "gilt", 1.0)
            s.path(f"M{pt(x + q, y + h)} A{f(q)},{f(q)} 0 0 1 {pt(x, y + h - q)}", "rubric", 1.2)
            h = h - q
    s.text(300, 1270 + 560 / PHI + 44, "a : b = (a + b) : a", "muted", 18)

    # FIG. 3: the cube unfolded.
    s.fig(300, 560, 3, "explicatio exacedri")
    q, nx, ny = 64, 360, 640
    for (cx, cy) in ((1, 0), (0, 1), (1, 1), (2, 1), (3, 1), (1, 2)):
        s.poly([(nx + cx * q, ny + cy * q), (nx + (cx + 1) * q, ny + cy * q), (nx + (cx + 1) * q, ny + (cy + 1) * q),
                (nx + cx * q, ny + (cy + 1) * q)], "gilt", 1.3, closed=True)
        s.poly([(nx + cx * q + 12, ny + cy * q + 12), (nx + (cx + 1) * q - 12, ny + cy * q + 12),
                (nx + (cx + 1) * q - 12, ny + (cy + 1) * q - 12), (nx + cx * q + 12, ny + (cy + 1) * q - 12)],
               "gilt", 0.8, None, 0.7, closed=True)
    s.title_block("XXVI", "corpi vacui, dopo Pacioli", "De divina proportione · 1509")
    s.notes(860, 900, QUOTES["vacuus"])
    s.scale_bar(300, 1900)


# ---------------------------------------------------------------- plate IV: oculus

def plate_oculus(s: Sheet):
    """The eye in section, the camera obscura, the visual pyramid, and the iris as a wheel."""
    k = 0.58
    ex, ey, R = 1420, 1080, 430 * k
    s.circle(ex, ey, R, "gilt", 2.0)
    s.circle(ex, ey, R - 15, "gilt", 1.0)
    s.circle(ex, ey, R - 34, "line", 1.0, "6 8")
    cr = 210 * k
    ccx = ex - R + 130 * k
    ang = math.degrees(math.acos((R ** 2 + (ex - ccx) ** 2 - cr ** 2) / (2 * R * (ex - ccx))))
    p_top = (ex - R * math.cos(math.radians(ang)), ey - R * math.sin(math.radians(ang)))
    p_bot = (p_top[0], 2 * ey - p_top[1])
    s.path(f"M{pt(*p_top)} A{f(cr)},{f(cr)} 0 0 0 {pt(*p_bot)}", "gilt", 2.0)
    ix = ex - R + 150 * k
    s.line(ix, ey - 100, ix, ey - 28, "gilt", 2.4)
    s.line(ix, ey + 28, ix, ey + 100, "gilt", 2.4)
    lx = ix + 40
    s.add(f'<ellipse cx="{f(lx)}" cy="{f(ey)}" rx="36" ry="74" {s.stroke("gilt", 1.6)}/>')
    s.add(f'<ellipse cx="{f(lx)}" cy="{f(ey)}" rx="20" ry="56" {s.stroke("line", 1.0, "4 6")}/>')
    nx = ex + R * math.cos(math.radians(14))
    for sgn in (1, -1):
        y0 = ey + sgn * R * math.sin(math.radians(14))
        s.path(f"M{pt(nx, y0)} C{pt(nx + 90, y0)} {pt(nx + 150, y0 + sgn * 18)} {pt(nx + 240, y0 + sgn * 40)}", "gilt", 1.6)
    s.hatch([(ex + 40, ey - R + 20), (ex + R - 10, ey - 60), (ex + R - 10, ey + 60), (ex + 40, ey + R - 20)], 70, 9, "gilt", 0.6, 0.25)
    ox, top, bot = 660, ey - 180, ey + 180
    s.line(ox, top + 44, ox, bot, "gilt", 1.8)
    s.line(ox - 18, bot, ox + 18, bot, "gilt", 1.8)
    s.path(f"M{pt(ox, top + 44)} C{pt(ox - 14, top + 24)} {pt(ox - 6, top + 6)} {pt(ox, top - 14)} "
           f"C{pt(ox + 6, top + 6)} {pt(ox + 14, top + 24)} {pt(ox, top + 44)}", "rubric", 1.6)
    retina = ex + R - 15
    for src in (top + 12, top + 90, ey, bot - 90, bot - 6):
        t = (retina - lx) / (lx - ox)
        dst = ey - (src - ey) * t
        role = "rubric" if src in (top + 12, bot - 6) else "gilt"
        s.line(ox, src, lx, ey, role, 1.0, None, 0.9)
        s.line(lx, ey, retina, dst, role, 1.0, "8 6", 0.9)
    s.dimension(ox, bot + 60, ex - R, bot + 60, "distantia", offset=0)
    s.leader(ix, ey - 100, ix - 120, ey - 300, "pupilla")
    s.leader(lx + 30, ey + 50, lx + 160, ey + 330, "cristallino")
    s.leader(nx + 200, ey + R * 0.24 + 30, nx + 260, ey + 300, "nervo")

    # FIG. 2: camera obscura, with a tower imaged upside down on the far wall.
    s.fig(2240, 300, 2, "camera oscura")
    cam = Cam(2800, 780, 1.0, yaw=-42, pitch=14)
    box_edges(s, cam, -260, 260, -150, 150, -180, 180, 1.6)
    hole = (-260, 0, 0)
    s.poly3(cam, circle3d(hole, (1, 0, 0), 9, 24), "rubric", 1.4)
    apex = (-900, 132, 0)
    for zz in (-36, 36):
        s.line3(cam, (-936, -110, zz), (-936, 80, zz), "gilt", 1.2)
        s.line3(cam, (-864, -110, zz), (-864, 80, zz), "gilt", 1.2)
    for yy in (-110, 80):
        s.poly3(cam, [(-936, yy, -36), (-864, yy, -36), (-864, yy, 36), (-936, yy, 36)], "gilt", 1.2, closed=True)
    for corner in ((-936, 80, -36), (-864, 80, -36), (-864, 80, 36), (-936, 80, 36)):
        s.line3(cam, corner, apex, "gilt", 1.2)
    for yy in range(-80, 80, 32):
        s.line3(cam, (-864, yy, 36), (-936, yy, 36), "gilt", 0.6, None, 0.5)
    s.line3(cam, (-1040, -110, 0), (-760, -110, 0), "line", 1.0, "3 7")

    def image(q):
        kk = (260 - hole[0]) / (hole[0] - q[0])
        return add(hole, mul(sub(hole, q), kk))

    outline = [(-900, -110, -36), (-900, 80, -36), (-900, 132, 0), (-900, 80, 36), (-900, -110, 36)]
    s.poly3(cam, [image(q) for q in outline], "gilt", 1.4)
    for q in ((-900, 132, 0), (-900, -110, 0)):
        s.line3(cam, q, hole, "rubric", 1.0, None, 0.9)
        s.line3(cam, hole, image(q), "rubric", 1.0, "8 6", 0.9)
    hp = cam(hole)
    s.leader(*hp, hp[0] - 120, hp[1] + 230, "foro")
    ip = cam(image((-900, 20, 0)))
    s.leader(*ip, ip[0] + 160, ip[1] + 200, "imagine rovescia")

    # FIG. 3: the visual pyramid cut by the picture plane.
    s.fig(2240, 1240, 3, "piramide visiva")
    cam = Cam(2700, 1640, 1.0, yaw=34, pitch=16)
    eye = (-330, 0, 0)
    plane_x = -70
    s.poly3(cam, [(plane_x, -120, -140), (plane_x, 120, -140), (plane_x, 120, 140), (plane_x, -120, 140)], "gilt", 1.5, closed=True)
    for zz in (-70, 0, 70):
        s.line3(cam, (plane_x, -120, zz), (plane_x, 120, zz), "line", 0.8, "3 6")
    for yy in (-60, 0, 60):
        s.line3(cam, (plane_x, yy, -140), (plane_x, yy, 140), "line", 0.8, "3 6")
    cube = [(x, y, z) for x in (180, 300) for y in (-100, 20) for z in (-60, 60)]
    edges = [(i, j) for i in range(8) for j in range(i + 1, 8) if sum(cube[i][q] != cube[j][q] for q in range(3)) == 1]
    for i, j in edges:
        s.line3(cam, cube[i], cube[j], "gilt", 1.6)

    def cut(q):
        t = (plane_x - eye[0]) / (q[0] - eye[0])
        return add(eye, mul(sub(q, eye), t))

    for q in cube:
        s.line3(cam, eye, q, "gilt", 0.7, "6 7", 0.6)
        s.circle(*cam(cut(q)), 3, "rubric", 1.0)
    for i, j in edges:
        s.line3(cam, cut(cube[i]), cut(cube[j]), "rubric", 1.2)
    ep = cam(eye)
    s.add(f'<ellipse cx="{f(ep[0])}" cy="{f(ep[1])}" rx="18" ry="10" {s.stroke("gilt", 1.4)}/>')
    s.circle(*ep, 5, "gilt", 1.0, fill=s.p["gilt"])
    s.leader(*ep, ep[0] - 160, ep[1] + 120, "occhio")

    # FIG. 4: the iris in plan as an escape wheel.
    wx, wy, wr = 3420, 1520, 150
    s.fig(3220, 1240, 4, "pupilla · rota")
    escape_wheel(s, wx, wy, wr, 30, 24, 0.0, 1.8)
    s.circle(wx, wy, wr - 22, "gilt", 1.2)
    s.circle(wx, wy, 66, "gilt", 1.6)
    s.circle(wx, wy, 36, "gilt", 1.0, fill=s.p["sheet"])
    for kk in range(72):
        t = kk * 2 * math.pi / 72
        r0, r1 = 72, wr - 28 - (10 if kk % 3 else 0)
        s.line(wx + r0 * math.cos(t), wy + r0 * math.sin(t), wx + r1 * math.cos(t), wy + r1 * math.sin(t), "gilt", 0.7, None, 0.6)
    wired_sun(s, wx, wy, 24, "gilt", 1.8)
    s.crosshair(wx, wy, wr + 60)

    s.title_block("III", "dell'occhio, in sezione", "lume · cristallino · nervo")
    s.notes(860, 560, QUOTES["occhio"])
    s.notes(3600, 300, QUOTES["sentimenti"])
    s.scale_bar(300, 1900)


# ---------------------------------------------------------------- plate 0: fucina stellare

def split_runs(pts, front):
    """Split a 3D polyline into the runs where `front(p)` holds and the runs where it does not."""
    near, far, cur, side = [], [], [], None
    for p in pts:
        here = front(p)
        if side is not None and here != side:
            (near if side else far).append(cur + [p])
            cur = []
        cur.append(p)
        side = here
    if len(cur) > 1:
        (near if side else far).append(cur)
    return near, far


def draw_runs(s: Sheet, cam, pts, front, role="gilt", width=1.2, far=("5 7", 0.4), opacity=1.0):
    """A 3D polyline, solid where visible and dashed (or dropped, with far=None) where hidden."""
    near, back = split_runs(pts, front)
    for run in near:
        s.poly3(cam, run, role, width, None, opacity)
    if far:
        for run in back:
            s.poly3(cam, run, role, width * 0.7, far[0], far[1] * opacity)


def facing_from(cam, c):
    """Visibility test for points on a sphere centred at c: the hemisphere toward the viewer."""
    return lambda p: cam.rot(sub(p, c))[2] >= 0


def wire_sphere(s: Sheet, cam, c, r, lats, lons, role="gilt", width=1.0, far=None, lat_max=90):
    """Latitude and longitude lines on a sphere; the far side is dropped unless `far` is given."""
    front = facing_from(cam, c)
    for a in lats:
        t = math.radians(a)
        draw_runs(s, cam, circle3d(add(c, (0, r * math.sin(t), 0)), (0, 1, 0), r * math.cos(t), 180), front, role, width, far)
    for lon in lons:
        g = math.radians(lon)
        pts = [add(c, (r * math.cos(math.radians(a)) * math.cos(g), r * math.sin(math.radians(a)),
                       r * math.cos(math.radians(a)) * math.sin(g))) for a in range(-90, lat_max + 1, 2)]
        draw_runs(s, cam, pts, front, role, width, far)


def plate_fucina(s: Sheet):
    """A star forge of vanes and wheels, driving a solar lance into the sun it is building."""
    # World units are the forge's; K zooms the whole scene, and the sun's cap fills the bottom third.
    R, K = 1700, 0.88
    Rs = R * K
    cam = Cam(1920, 1400 + Rs, K, yaw=0, pitch=16)
    sx, sy = cam((0, 0, 0))

    def outside(p):
        """Points off the sun's surface: hidden only when the sun stands between them and the eye."""
        q = cam.rot(p)
        return q[0] ** 2 + q[1] ** 2 >= R * R or q[2] >= 0

    def flat(pts2, y):
        return [(x, y, z) for x, z in pts2]

    def axis_front(y):
        return lambda p: cam.rot((p[0], 0, p[2]))[2] >= 0

    # The sun, clipped to the sheet: growth shells, a toothed ring at its limb, corona ticks.
    # Rings above the pole leave a gap so the lance reads clearly.
    def ring_gap(r, role, width, dash, op):
        g = math.degrees(80 / r)
        a0, a1 = math.radians(270 + g), math.radians(270 - g)
        s.path(f"M{pt(sx + r * math.cos(a0), sy + r * math.sin(a0))} A{f(r)},{f(r)} 0 1 1 "
               f"{pt(sx + r * math.cos(a1), sy + r * math.sin(a1))}", role, width, dash, op)

    i = s.inset
    cid = s.clip(f'<rect x="{i}" y="{i}" width="{W - 2 * i}" height="{H - 2 * i}"/>')
    s.add(f'<g clip-path="url(#{cid})">')
    for dr, op in ((360, 0.3), (260, 0.45)):
        ring_gap(Rs + dr, "line", 1.0, "4 12", op)
    s.path(gear_path(sx, sy, 480, 2 * (Rs + 100) / 480, 0.0)[0], "gilt", 1.0, None, 0.75)
    ring_gap(Rs + 52, "line", 0.9, "6 8", 1.0)
    for k in range(360):
        if abs(k - 270) < 4:
            continue
        a = math.radians(k)
        r1 = Rs + (190 if k % 10 == 0 else 170 if k % 5 == 0 else 158)
        s.line(sx + (Rs + 140) * math.cos(a), sy + (Rs + 140) * math.sin(a), sx + r1 * math.cos(a),
               sy + r1 * math.sin(a), "gilt", 0.9, None, 0.7)
    for ang in (240, 300):
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        s.line(sx + (Rs + 200) * ux, sy + (Rs + 200) * uy, sx + (Rs + 356) * ux, sy + (Rs + 356) * uy, "rubric", 1.1)
        s.arrow(sx + (Rs + 356) * ux, sy + (Rs + 356) * uy, ux, uy)

    # Limb shading, hatched as Leonardo shaded a sphere's turning edge.
    for a0, a1, hang in ((196, 248, 62), (292, 344, 118)):
        outer = [(sx + Rs * math.cos(math.radians(a)), sy + Rs * math.sin(math.radians(a))) for a in range(a0, a1 + 1, 2)]
        inner = [(sx + Rs * 0.955 * math.cos(math.radians(a)), sy + Rs * 0.955 * math.sin(math.radians(a)))
                 for a in range(a1, a0 - 1, -2)]
        s.hatch(outer + inner, hang, 13, "gilt", 0.8, 0.28)

    # Inner shells seen through the surface, the graticule, and ripples where the lance strikes.
    s.circle(sx, sy, Rs * 0.72, "line", 1.0, "10 10")
    s.circle(sx, sy, Rs * 0.88, "line", 0.9, "3 9")
    wire_sphere(s, cam, (0, 0, 0), R, range(30, 81, 10), range(0, 360, 15), "gilt", 0.9, lat_max=84)
    for a, dash in ((81.5, None), (84, "6 6"), (86.2, None), (88, "4 5")):
        t = math.radians(a)
        s.poly3(cam, circle3d((0, R * math.sin(t), 0), (0, 1, 0), R * math.cos(t), 120), "rubric", 1.2, dash, 0.9)
    s.circle(sx, sy, Rs, "gilt", 2.6)
    s.add("</g>")

    # The forge stands on the sun's axis: four vanes, a core sphere, two wheels, a coiled nozzle.
    Ye, Yc, Yw, rc = 2080, 2520, 2340, 130
    RW, RX = 472, 340
    C = (0.0, float(Yc), 0.0)
    OUT = [(70, 2160), (250, 2330), (370, 2520), (350, 2720), (260, 2920), (215, 3000)]
    INN = [(70, 2160), (140, 2260), (190, 2400), (200, 2640), (185, 2860), (215, 3000)]
    Y0, Y1, TIP = OUT[0][1], OUT[-1][1], OUT[-1][0]
    STRIP, PANELS = list(range(2360, 2901, 20)), range(Y0 + 50, Y1 - 9, 50)
    profile = OUT + INN[::-1][1:-1]

    def along(prof, y):
        for (r0, y0), (r1, y1) in zip(prof, prof[1:]):
            if y0 <= y <= y1:
                return r0 + (r1 - r0) * (y - y0) / (y1 - y0)
        raise ValueError(y)

    thetas = [math.radians(a) for a in (45, 135, 225, 315)]

    def radial(theta):
        return (math.cos(theta), 0.0, math.sin(theta)), (-math.sin(theta), 0.0, math.cos(theta))

    def vane(theta, front):
        d, t = radial(theta)
        side = 1 if cam.facing(t) else -1

        def P(r, y, k=side):
            return add(add(mul(d, r), mul(t, 24 * k)), (0.0, y, 0.0))

        face = [P(r, y) for r, y in profile]
        if not front:
            s.poly3(cam, face, "gilt", 1.0, "6 7", 0.5, closed=True)
            return
        s.poly3(cam, [P(r, y, -side) for r, y in profile], "gilt", 0.8, None, 0.45, closed=True)
        for r, y in OUT:
            s.line3(cam, P(r, y), P(r, y, -side), "gilt", 0.8, None, 0.6)
        s.poly3(cam, face, "gilt", 1.8, closed=True)
        strip = [P(along(INN, y), y) for y in STRIP] + [P(along(INN, y) + 45, y) for y in reversed(STRIP)]
        s.hatch([cam(q) for q in strip], 78, 8, "gilt", 0.7, 0.45)
        s.poly3(cam, strip, "gilt", 0.9, None, 0.8, closed=True)
        for y in PANELS:
            s.line3(cam, P(along(INN, y), y), P(along(OUT, y), y), "gilt", 0.8, None, 0.65)
        s.poly3(cam, [P((along(INN, y) + 45 + along(OUT, y)) / 2, y) for y in STRIP], "gilt", 0.7, "2 6", 0.7)
        for dr, h in ((-12, 60), (0, 92), (10, 40)):
            s.line3(cam, P(TIP + dr, Y1 - 6), P(TIP + dr, Y1 + h), "gilt", 0.9)
        for h in (26, 54):
            s.line3(cam, P(TIP - 18, Y1 + h), P(TIP + 18, Y1 + h), "gilt", 0.8)

    for th in thetas:
        if not cam.facing(radial(th)[0]):
            vane(th, False)

    # Mast and finial.
    s.line3(cam, (0, Ye + 30, 0), (0, Y1 + 80, 0), "rubric", 1.0, "14 6 3 6", 0.8)
    s.poly3(cam, circle3d((0, Y1 - 20, 0), (0, 1, 0), 22, 36), "gilt", 1.1)
    s.circle(*cam((0, Y1 + 14, 0)), 10, "gilt", 1.2)

    # Core sphere with its seam and two armillary rings.
    wire_sphere(s, cam, C, rc, range(-60, 61, 30), range(0, 360, 30), "gilt", 1.0, far=("3 6", 0.35))
    core_front = facing_from(cam, C)
    for a in (-7, 7):
        t = math.radians(a)
        draw_runs(s, cam, circle3d(add(C, (0, rc * math.sin(t), 0)), (0, 1, 0), rc * math.cos(t), 120), core_front,
                  "gilt", 1.3, None)
    s.circle(*cam(C), rc * K, "gilt", 1.8)
    for n in ((0.5, 0.866, 0.0), (-0.5, 0.866, 0.0)):
        draw_runs(s, cam, circle3d(C, n, 184, 120), core_front, "gilt", 1.2)

    # Struts from core to vanes, and from vanes out to the two wheels.
    for th in thetas:
        d, _ = radial(th)
        front = cam.facing(d)
        style = ("gilt", 1.2, None, 0.9) if front else ("gilt", 0.8, "4 6", 0.45)
        for y in (Yc - 60, Yc + 60):
            r0 = math.sqrt(rc * rc - (y - Yc) ** 2)
            s.line3(cam, add(mul(d, r0), (0, y, 0)), add(mul(d, along(INN, y)), (0, y, 0)), *style)
        s.line3(cam, add(mul(d, along(OUT, Yc)), C), add(mul(d, RW - 10), C), *style)
        s.line3(cam, add(mul(d, along(OUT, Yw)), (0, Yw, 0)), add(mul(d, RX + 2), (0, Yw, 0)), *style)

    # Crown wheel at the core, with a graduated rim; an escape wheel below it.
    draw_runs(s, cam, flat(gear_points(0, 0, RW // 4, 8, 0.0), Yc), axis_front(Yc), "gilt", 1.4)
    rim = RW - 30
    draw_runs(s, cam, flat([(rim * math.cos(a), rim * math.sin(a)) for a in [k * math.pi / 90 for k in range(181)]], Yc),
              axis_front(Yc), "gilt", 0.9)
    for k in range(72):
        a = k * math.pi / 36
        c, sn = math.cos(a), math.sin(a)
        r0 = rim - (38 if k % 6 == 0 else 20)
        if cam.facing((c, 0, sn)):
            s.line3(cam, (r0 * c, Yc, r0 * sn), (rim * c, Yc, rim * sn), "gilt", 0.8, None, 0.8)
    draw_runs(s, cam, flat(escape_points(0, 0, RX, 48, 24, 0.1), Yw), axis_front(Yw), "gilt", 1.2)

    # Nozzle: five toothed coils narrowing to the emitter, caged by eight rods.
    coils = [(2125 + k * 30, 40 + k * 16) for k in range(5)]
    for k, (y, r) in enumerate(coils):
        teeth = max(12, int(r / 3))
        draw_runs(s, cam, flat(gear_points(0, 0, teeth, 2 * r / teeth, k * 0.1), y), axis_front(y), "gilt", 1.1)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        c, sn = math.cos(a), math.sin(a)
        rod = [(r * c, y, r * sn) for y, r in coils]
        if cam.facing((c, 0, sn)):
            s.poly3(cam, rod, "gilt", 1.0)
        else:
            s.poly3(cam, rod, "gilt", 0.7, "4 6", 0.45)

    for th in thetas:
        if cam.facing(radial(th)[0]):
            vane(th, True)

    # Emitter and the solar lance: a coiled shaft with a leaf blade, striking the pole.
    ex, ey = cam((0, Ye, 0))
    s.circle(ex, ey, 30, "rubric", 1.6)
    s.circle(ex, ey, 9, "rubric", 1.0, fill=s.p["rubric"])
    for r, dash in ((72, "2 6"), (104, "2 9")):
        s.circle(ex, ey, r, "rubric", 1.0, dash, 0.6)
    for k in range(24):
        a = k * math.pi / 12
        s.line(ex + 40 * math.cos(a), ey + 40 * math.sin(a), ex + (58 if k % 2 else 50) * math.cos(a),
               ey + (58 if k % 2 else 50) * math.sin(a), "rubric", 1.0)
    head = [(0, R), (30, R + 56), (46, R + 110), (26, R + 170), (12, R + 190)]
    leaf = head + [(-x, y) for x, y in reversed(head[1:-1])] + [(-12, R + 190)]
    s.poly3(cam, [(x, y, 0) for x, y in leaf], "rubric", 1.6, closed=True)
    s.line3(cam, (0, R + 6, 0), (0, R + 188, 0), "rubric", 0.9)
    s.hatch([cam((x, y, 0)) for x, y in head + [(0, R + 190)]], 30, 7, "rubric", 0.8, 0.5)
    for y in (R + 192, R + 206):
        s.poly3(cam, circle3d((0, y, 0), (0, 1, 0), 16, 24), "rubric", 1.1)
    for x in (-9, 9):
        s.line3(cam, (x, R + 206, 0), (x, Ye - 34, 0), "rubric", 1.4)
    y0, y1, turns = R + 225, Ye - 44, 6
    helix = [(24 * math.cos(turns * 2 * math.pi * k / 360), y1 - (y1 - y0) * k / 360,
              24 * math.sin(turns * 2 * math.pi * k / 360)) for k in range(361)]
    draw_runs(s, cam, helix, lambda p: p[2] >= 0, "rubric", 1.0, ("3 5", 0.5))

    # Plasma drawn down from the nozzle and laid along the surface.
    for k in range(9):
        lon = math.radians(20 + k * 40)
        lat = math.radians(72 if k % 2 else 60)
        p2 = (R * math.cos(lat) * math.cos(lon), R * math.sin(lat), R * math.cos(lat) * math.sin(lon))
        p0, p1 = (0.0, Ye - 40.0, 0.0), (p2[0] * 0.12, R + 70.0, p2[2] * 0.12)
        curve = [add(add(mul(p0, (1 - t) ** 2), mul(p1, 2 * t * (1 - t))), mul(p2, t * t))
                 for t in [j / 48 for j in range(49)]]
        draw_runs(s, cam, curve, outside, "rubric", 1.1, ("5 7", 0.45), 0.8)

    # Names.
    def lead(p3, dx, dy, label):
        x, y = cam(p3)
        s.leader(x, y, x + dx, y + dy, label)

    lead(add(C, (-92, 92, 0)), -480, -230, "nucleo")
    d45 = radial(math.radians(45))[0]
    lead(add(mul(d45, along(OUT, 2800) - 20), (0, 2800, 0)), 620, -130, "pala")
    lead((RW * math.cos(0.35), Yc, RW * math.sin(0.35)), 460, -20, "ruota maestra")
    lead((RX * math.cos(0.3), Yw, RX * math.sin(0.3)), 560, 40, "ruota di scappamento")
    lead((-coils[3][1], coils[3][0], 0), -420, -10, "bobine")
    lead((-9, 1960, 0), -420, -40, "lancia solare")
    lead((0, R, 0), 460, -150, "polo")
    lx, ly = sx + Rs * math.cos(math.radians(250)), sy + Rs * math.sin(math.radians(250))
    s.leader(lx, ly, lx - 200, ly - 60, "fotosfera")
    ax_, ay_ = sx + (Rs + 300) * math.cos(math.radians(300)), sy + (Rs + 300) * math.sin(math.radians(300))
    s.leader(ax_, ay_, ax_ + 200, ay_ + 30, "accrescimento")

    # FIG. 2: the forge in plan.
    k, px, py = 0.36, 620, 1010
    s.fig(420, 760, 2, "pianta")
    s.path(gear_path(px, py, RW // 4, 8 * k, 0.0)[0], "gilt", 1.2)
    s.circle(px, py, rim * k, "gilt", 0.8)
    s.poly(escape_points(px, py, RX * k, 48, 24 * k, 0.1), "gilt", 0.8, "4 5", 0.6, closed=True)
    s.circle(px, py, rc * k, "gilt", 1.4)
    for th in thetas:
        (dx, _, dz), (tx, _, tz) = radial(th)
        rmax = max(r for r, _ in OUT)
        rect = [(px + dx * r + tx * h, py + dz * r + tz * h) for r, h in ((70 * k, -24 * k), (rmax * k, -24 * k),
                                                                          (rmax * k, 24 * k), (70 * k, 24 * k))]
        s.poly(rect, "gilt", 1.3, closed=True)
        s.hatch(rect, math.degrees(th) + 90, 6, "gilt", 0.6, 0.4)
    s.crosshair(px, py, 230)
    s.dimension(px - (RW + 8) * k, py + 230, px + (RW + 8) * k, py + 230, str(2 * (RW + 8)), offset=-20)

    # FIG. 3: one vane in elevation.
    s.fig(3060, 330, 3, "pala, in alzato")

    def el(r, y):
        return 3140 + r * 0.8, 1180 - (y - Y0) * 0.75

    s.line(*el(0, Y0 - 40), *el(0, Y1 + 60), "rubric", 1.0, "14 6 3 6", 0.8)
    s.poly([el(r, y) for r, y in profile], "gilt", 1.6, closed=True)
    strip = [el(along(INN, y), y) for y in STRIP] + [el(along(INN, y) + 45, y) for y in reversed(STRIP)]
    s.hatch(strip, 78, 7, "gilt", 0.7, 0.45)
    s.poly(strip, "gilt", 0.9, closed=True)
    for y in PANELS:
        s.line(*el(along(INN, y), y), *el(along(OUT, y), y), "gilt", 0.8, None, 0.65)
    s.dimension(*el(400, Y0), *el(400, Y1), str(Y1 - Y0), offset=-30)
    sp_ = el(along(INN, 2700) + 30, 2700)
    s.leader(*sp_, sp_[0] - 220, sp_[1] - 120, "collettore")

    s.title_block("0", "fucina stellare, con lancia solare", "sole · lancia · fucina")
    s.text(300, 540, f"{len(thetas)} pale · {RW // 4} denti · {len(coils)} bobine", "ink", 22)
    s.text(300, 574, "sol nascens", "muted", 20)
    s.notes(3560, 1500, QUOTES["sol"], 28, 42)
    s.scale_bar(300, 1480)
    # The plate's footer sits over the sun's corona; give it a clear patch of sheet.
    s.add(f'<rect x="{W - s.inset - 700}" y="{H - s.inset - 100}" width="660" height="56" fill="{s.p["sheet"]}" '
          'fill-opacity="0.9"/>')


PLATES = [
    ("00-fucina", "TAV. 0", "fucina stellare", plate_fucina),
    ("01-specchio", "TAV. I", "specchio ustorio", plate_specchio),
    ("02-orologio", "TAV. II", "orologio", plate_orologio),
    ("03-vacui", "TAV. XXVI", "corpi vacui", plate_vacui),
    ("04-oculus", "TAV. III", "oculus", plate_oculus),
]
