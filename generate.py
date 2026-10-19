#!/usr/bin/env python3
"""Generate the Solforge Omarchy themes: palette files, backgrounds, previews.

The palettes extend the solforged.io sheet tokens (desk, sheet, ink, gilt,
rubric, line, grid) into a full Omarchy colors.toml. Backgrounds are
construction drawings after Leonardo's notebooks, drawn as wireframes on the
site's sheet-on-desk layout. Requires rsvg-convert and ImageMagick.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
W, H = 3840, 2160
FONT = "Berkeley Mono Variable, Berkeley Mono, monospace"

# Site tokens come first in each palette; the rest extend them for terminals.
THEMES = {
    "dark": {
        "name": "Solforge Dark",
        "icons": "Yaru-red",
        "site": {
            "desk": "#290401",
            "sheet": "#130807",
            "slip": "#211411",
            "ink": "#ece1ce",
            "muted": "#c2ab98",
            "gilt": "#dfb15a",
            "rubric": "#de8a70",
            "line": "#694135",
            "grid": "#36231c",
        },
        "colors": {
            "mode": "dark",
            "accent": "#dfb15a",
            "selection": "#4d1c15",
            "selection_foreground": "#faf3e4",
            "muted": "#8f7262",
            "background": "#130807",
            "dark_background": "#0e0605",
            "darker_background": "#090303",
            "lighter_background": "#211411",
            "foreground": "#ece1ce",
            "dark_foreground": "#8f7262",
            "light_foreground": "#c2ab98",
            "bright_foreground": "#faf3e4",
            "hyprland_active_border": "rgba(dfb15aee) rgba(8f2c1cee) 45deg",
            "hyprland_inactive_border": "rgba(4a2e25aa)",
            "red": "#d9654f",
            "yellow": "#dfb15a",
            "orange": "#d98c4a",
            "green": "#94ad7f",
            "cyan": "#6fa9a3",
            "blue": "#8798c7",
            "magenta": "#c98597",
            "brown": "#a87a55",
            "bright_red": "#de8a70",
            "bright_yellow": "#efcd85",
            "bright_green": "#b5cba0",
            "bright_cyan": "#96c7c0",
            "bright_blue": "#aab8de",
            "bright_magenta": "#dfa7b6",
        },
        # omp and Tern surfaces; Tern draws its tab bar in `chrome`, the oxblood desk.
        "ui": {
            "bg": "#130807", "bg_alt": "#190d0a", "bg_hl": "#211411",
            "border": "#694135", "border_muted": "#36231c",
            "comment": "#a58876", "gray": "#c2ab98", "fg": "#ece1ce", "fg_bright": "#faf3e4",
            "gilt": "#dfb15a", "rubric": "#de8a70", "red": "#d9654f", "orange": "#d98c4a",
            "green": "#94ad7f", "cyan": "#6fa9a3", "blue": "#8798c7", "madder": "#c98597",
            "sel": "#4d1c15", "diff_add": "#1b2414", "diff_delete": "#33100b",
            "chrome": "#290401", "widget": "#211411",
            "ansi0": "#4a2e25", "ansi7": "#c2ab98", "ansi15": "#faf3e4",
        },
    },
    "light": {
        "name": "Solforge Light",
        "icons": "Yaru-red",
        "site": {
            "desk": "#290401",
            "sheet": "#f6f1e6",
            "slip": "#e8dfd0",
            "ink": "#2a2120",
            "muted": "#65534a",
            "gilt": "#765411",
            "rubric": "#863f3d",
            "line": "#a39380",
            "grid": "#ddd3c1",
        },
        "colors": {
            "mode": "light",
            "accent": "#765411",
            "selection": "#ebd3c8",
            "selection_foreground": "#1a1312",
            "muted": "#857265",
            "background": "#f6f1e6",
            "dark_background": "#eee7da",
            "darker_background": "#e4d9c5",
            "lighter_background": "#e8dfd0",
            "foreground": "#2a2120",
            "dark_foreground": "#857265",
            "light_foreground": "#4f403a",
            "bright_foreground": "#1a1312",
            "hyprland_active_border": "rgba(765411ee) rgba(863f3dee) 45deg",
            "hyprland_inactive_border": "rgba(c9bba6aa)",
            "red": "#a3302a",
            "yellow": "#8a6212",
            "orange": "#a5531c",
            "green": "#4f6b3a",
            "cyan": "#2f6e6a",
            "blue": "#334f8a",
            "magenta": "#8a3a63",
            "brown": "#6b4423",
            "bright_red": "#b8402f",
            "bright_yellow": "#946a0c",
            "bright_green": "#5a7642",
            "bright_cyan": "#347a74",
            "bright_blue": "#4a66a3",
            "bright_magenta": "#a3507a",
        },
        "ui": {
            "bg": "#f6f1e6", "bg_alt": "#eee7da", "bg_hl": "#e8dfd0",
            "border": "#a39380", "border_muted": "#d9cebb",
            "comment": "#70605a", "gray": "#65534a", "fg": "#2a2120", "fg_bright": "#1a1312",
            "gilt": "#765411", "rubric": "#863f3d", "red": "#a3302a", "orange": "#a5531c",
            "green": "#4f6b3a", "cyan": "#2f6e6a", "blue": "#334f8a", "madder": "#8a3a63",
            "sel": "#ebd3c8", "diff_add": "#e2e8d3", "diff_delete": "#f3dbd3",
            "chrome": "#e8dfd0", "widget": "#fcfaf4",
            "ansi0": "#2a2120", "ansi7": "#8a7a6d", "ansi15": "#c9bba6",
        },
    },
}

# omp color roles, as names of `ui` vars. Tern reads the same file.
OMP_ROLES = {
    "accent": "gilt", "border": "border", "borderAccent": "gilt", "borderMuted": "border_muted",
    "success": "green", "error": "red", "warning": "orange", "muted": "gray", "dim": "comment",
    "text": "fg", "thinkingText": "gray",
    "selectedBg": "sel", "userMessageBg": "bg_hl", "userMessageText": "fg_bright",
    "customMessageBg": "bg_alt", "customMessageText": "gray", "customMessageLabel": "rubric",
    "toolPendingBg": "bg_alt", "toolSuccessBg": "diff_add", "toolErrorBg": "diff_delete",
    "statusLineBg": "bg", "toolTitle": "fg_bright", "toolOutput": "gray",
    "mdHeading": "gilt", "mdLink": "gilt", "mdLinkUrl": "comment", "mdCode": "rubric",
    "mdCodeBlock": "fg", "mdCodeBlockBorder": "border", "mdQuote": "gray", "mdQuoteBorder": "rubric",
    "mdHr": "border", "mdListBullet": "rubric",
    "toolDiffAdded": "green", "toolDiffRemoved": "red", "toolDiffContext": "gray",
    "syntaxComment": "comment", "syntaxKeyword": "madder", "syntaxFunction": "blue",
    "syntaxVariable": "fg", "syntaxString": "green", "syntaxNumber": "orange", "syntaxType": "gilt",
    "syntaxOperator": "gray", "syntaxPunctuation": "gray",
    "thinkingOff": "border", "thinkingMinimal": "comment", "thinkingLow": "cyan",
    "thinkingMedium": "blue", "thinkingHigh": "gilt", "thinkingXhigh": "rubric", "thinkingMax": "red",
    "bashMode": "cyan", "pythonMode": "madder",
    "statusLineSep": "border", "statusLineModel": "gilt", "statusLinePath": "blue",
    "statusLineGitClean": "green", "statusLineGitDirty": "orange", "statusLineContext": "cyan",
    "statusLineSpend": "blue", "statusLineStaged": "green", "statusLineDirty": "orange",
    "statusLineUntracked": "rubric", "statusLineOutput": "fg_bright", "statusLineCost": "gilt",
    "statusLineSubagents": "madder",
}


COLOR_ORDER = [
    "mode",
    None,
    "accent", "selection", "selection_foreground", "muted",
    None,
    "background", "dark_background", "darker_background", "lighter_background",
    None,
    "foreground", "dark_foreground", "light_foreground", "bright_foreground",
    None,
    "hyprland_active_border", "hyprland_inactive_border",
    None,
    "red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown",
    None,
    "bright_red", "bright_yellow", "bright_green", "bright_cyan", "bright_blue", "bright_magenta",
]

QUOTES = {
    "orrery": ["il sole", "no si move"],
    "vacuus": [
        "nessuna humana investigatione",
        "si pò dimandare vera scientia",
        "s'essa non passa per le",
        "matematiche dimostrationi",
    ],
    "oculus": [
        "l'occhio, che si dice",
        "finestra dell'anima, è la",
        "principale via donde il",
        "comune senso può più copiosa-",
        "mente considerare le infinite",
        "opere di natura",
    ],
}


# ---------------------------------------------------------------- color math

def rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def luminance(hex_color: str) -> float:
    def lin(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb(hex_color)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ---------------------------------------------------------------- svg helpers

def f(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def pt(x: float, y: float) -> str:
    return f"{f(x)},{f(y)}"


class Sheet:
    """One drawing: desk, sheet, grid and a list of SVG fragments."""

    def __init__(self, palette: dict, plate: str, title: str):
        self.p = palette
        self.parts: list[str] = []
        self.plate = plate
        self.title = title
        self.inset = 44

    def add(self, s: str) -> None:
        self.parts.append(s)

    def stroke(self, role: str, width: float, dash: str | None = None, opacity: float = 1.0) -> str:
        s = f'fill="none" stroke="{self.p[role]}" stroke-width="{f(width)}"'
        if dash:
            s += f' stroke-dasharray="{dash}"'
        if opacity < 1:
            s += f' stroke-opacity="{f(opacity)}"'
        return s + ' stroke-linecap="round" stroke-linejoin="round"'

    def line(self, x1, y1, x2, y2, role="line", width=1.4, dash=None, opacity=1.0):
        self.add(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" {self.stroke(role, width, dash, opacity)}/>')

    def circle(self, cx, cy, r, role="gilt", width=2.6, dash=None, opacity=1.0, fill=None):
        attrs = self.stroke(role, width, dash, opacity)
        if fill:
            attrs = attrs.replace('fill="none"', f'fill="{fill}"')
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" {attrs}/>')

    def path(self, d, role="gilt", width=2.6, dash=None, opacity=1.0, fill=None):
        attrs = self.stroke(role, width, dash, opacity)
        if fill:
            attrs = attrs.replace('fill="none"', f'fill="{fill}"')
        self.add(f'<path d="{d}" {attrs}/>')

    def text(self, x, y, s, role="muted", size=26, anchor="start", opacity=1.0, spacing=0.0, mirror=False):
        op = f' fill-opacity="{f(opacity)}"' if opacity < 1 else ""
        sp = f' letter-spacing="{f(spacing)}"' if spacing else ""
        if mirror:
            # Leonardo wrote right to left; the glyphs are reflected in place.
            self.add(
                f'<text transform="translate({f(x)},{f(y)}) scale(-1,1)" font-family="{FONT}" '
                f'font-size="{f(size)}" fill="{self.p[role]}" text-anchor="{anchor}"{op}{sp}>{escape(s)}</text>'
            )
        else:
            self.add(
                f'<text x="{f(x)}" y="{f(y)}" font-family="{FONT}" font-size="{f(size)}" '
                f'fill="{self.p[role]}" text-anchor="{anchor}"{op}{sp}>{escape(s)}</text>'
            )

    def crosshair(self, cx, cy, r, role="line", width=1.2, opacity=1.0):
        self.line(cx - r, cy, cx + r, cy, role, width, "4 10", opacity)
        self.line(cx, cy - r, cx, cy + r, role, width, "4 10", opacity)

    def dimension(self, x1, y1, x2, y2, label, offset=40, role="rubric"):
        """Dimension line parallel to (x1,y1)-(x2,y2), offset to its left."""
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy)
        ux, uy = dx / n, dy / n
        nx, ny = -uy, ux
        ax, ay = x1 + nx * offset, y1 + ny * offset
        bx, by = x2 + nx * offset, y2 + ny * offset
        self.line(x1 + nx * 8, y1 + ny * 8, ax + nx * 14, ay + ny * 14, "line", 1.1)
        self.line(x2 + nx * 8, y2 + ny * 8, bx + nx * 14, by + ny * 14, "line", 1.1)
        self.line(ax, ay, bx, by, role, 1.4)
        for (px, py, sgn) in ((ax, ay, 1), (bx, by, -1)):
            tip = (px, py)
            l = (px + sgn * ux * 18 + nx * 6, py + sgn * uy * 18 + ny * 6)
            r = (px + sgn * ux * 18 - nx * 6, py + sgn * uy * 18 - ny * 6)
            self.path(f"M{pt(*l)} L{pt(*tip)} L{pt(*r)}", role, 1.4)
        mx, my = (ax + bx) / 2 + nx * 18, (ay + by) / 2 + ny * 18
        angle = math.degrees(math.atan2(uy, ux))
        if angle > 90 or angle < -90:
            angle += 180
        self.add(
            f'<text transform="translate({f(mx)},{f(my)}) rotate({f(angle)})" font-family="{FONT}" '
            f'font-size="24" fill="{self.p[role]}" text-anchor="middle">{escape(label)}</text>'
        )

    def notes(self, x, y, lines, size=30, leading=46):
        for i, s in enumerate(lines):
            self.text(x, y + i * leading, s, "muted", size, "start", 0.5, mirror=True)

    def svg(self) -> str:
        p, i = self.p, self.inset
        sw, sh = W - 2 * i, H - 2 * i
        head = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <pattern id="minor" width="48" height="48" patternUnits="userSpaceOnUse" x="{i}" y="{i}">
    <path d="M48 0H0V48" fill="none" stroke="{p['grid']}" stroke-width="1" stroke-opacity="0.45"/>
  </pattern>
  <pattern id="major" width="240" height="240" patternUnits="userSpaceOnUse" x="{i}" y="{i}">
    <path d="M240 0H0V240" fill="none" stroke="{p['grid']}" stroke-width="1.4"/>
  </pattern>
  <radialGradient id="wash" cx="0.62" cy="0.52" r="0.75">
    <stop offset="0" stop-color="{p['slip']}" stop-opacity="0.55"/>
    <stop offset="1" stop-color="{p['sheet']}" stop-opacity="0"/>
  </radialGradient>
</defs>
<rect width="{W}" height="{H}" fill="{p['desk']}"/>
<rect x="{i}" y="{i}" width="{sw}" height="{sh}" fill="{p['sheet']}"/>
<rect x="{i}" y="{i}" width="{sw}" height="{sh}" fill="url(#wash)"/>
<rect x="{i}" y="{i}" width="{sw}" height="{sh}" fill="url(#minor)"/>
<rect x="{i}" y="{i}" width="{sw}" height="{sh}" fill="url(#major)"/>
<rect x="{i + 0.7}" y="{i + 0.7}" width="{sw - 1.4}" height="{sh - 1.4}" fill="none" stroke="{p['line']}" stroke-width="1.4"/>
"""
        # Corner ticks, as on the site's sheet.
        ticks = []
        for (cx, cy, sx, sy) in ((i + 36, i + 36, 1, 1), (W - i - 36, i + 36, -1, 1),
                                 (i + 36, H - i - 36, 1, -1), (W - i - 36, H - i - 36, -1, -1)):
            ticks.append(
                f'<path d="M{pt(cx, cy + sy * 22)} V{f(cy)} H{f(cx + sx * 22)}" fill="none" '
                f'stroke="{p["muted"]}" stroke-width="2" stroke-opacity="0.7"/>'
            )
        foot = (
            f'<text x="{W - i - 72}" y="{H - i - 64}" font-family="{FONT}" font-size="24" '
            f'fill="{p["muted"]}" fill-opacity="0.75" text-anchor="end" letter-spacing="3">'
            f'{escape(self.plate)}  ·  {escape(self.title)}</text>'
        )
        return head + "\n".join(ticks) + "\n" + "\n".join(self.parts) + "\n" + foot + "\n</svg>\n"


# ---------------------------------------------------------------- drawings

def wired_sun(s: Sheet, cx, cy, r, role="gilt", width=3.0):
    """The Solforge mark: ringed sun, compass ticks, one filled quadrant."""
    s.circle(cx, cy, r, role, width)
    k = r / 14
    for (a, b) in ((-21, -17), (17, 21)):
        s.line(cx, cy + a * k, cx, cy + b * k, role, width)
        s.line(cx + a * k, cy, cx + b * k, cy, role, width)
    s.line(cx - 9.9 * k, cy + 9.9 * k, cx + 9.9 * k, cy - 9.9 * k, role, width)
    s.path(f"M{pt(cx, cy)} V{f(cy - r)} A{f(r)},{f(r)} 0 0 1 {pt(cx + r, cy)} Z", role, 0.1, fill=s.p[role])


def gear_path(cx, cy, teeth, module, rot):
    """Wireframe spur gear outline with arced tips and roots."""
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
        d.append(("M" if k == 0 else "L") + pt(*p0))
        d.append("L" + pt(*p1))
        d.append(f"A{f(ra)},{f(ra)} 0 0 1 {pt(*p2)}")
        d.append("L" + pt(*p3))
        d.append(f"A{f(rr)},{f(rr)} 0 0 1 {pt(*p4)}")
    return " ".join(d) + " Z", rp, ra, rr


def draw_gear(s: Sheet, cx, cy, teeth, module, rot, spokes=5, hub_sun=False):
    d, rp, ra, rr = gear_path(cx, cy, teeth, module, rot)
    s.circle(cx, cy, rp, "line", 1.2, "10 12")
    s.path(d, "gilt", 2.6)
    rim = rr - module * 1.6
    hub = max(module * 3.2, rp * 0.2)
    s.circle(cx, cy, rim, "gilt", 1.8)
    s.circle(cx, cy, hub, "gilt", 1.8)
    # Spokes as double rails, like a cut-out wheel seen in plan.
    for k in range(spokes):
        a = rot * 0.5 + k * 2 * math.pi / spokes
        ox, oy = -math.sin(a), math.cos(a)
        half = max(module * 0.9, 6)
        for sgn in (1, -1):
            x1 = cx + hub * math.cos(a) + sgn * ox * half
            y1 = cy + hub * math.sin(a) + sgn * oy * half
            x2 = cx + rim * math.cos(a) + sgn * ox * half
            y2 = cy + rim * math.sin(a) + sgn * oy * half
            s.line(x1, y1, x2, y2, "gilt", 1.6)
    s.crosshair(cx, cy, ra + 60)
    if hub_sun:
        wired_sun(s, cx, cy, hub * 0.62, "gilt", 3)
    else:
        s.circle(cx, cy, hub * 0.38, "gilt", 1.8)
    return rp, ra


def mesh_rotation(rot1, teeth1, teeth2, phi):
    """Rotation for gear 2 at direction phi from gear 1 so the teeth interleave."""
    step1, step2 = 2 * math.pi / teeth1, 2 * math.pi / teeth2
    t1 = ((phi - rot1) / step1) % 1.0
    return phi + math.pi - (0.5 - t1) * step2


def draw_orrery(s: Sheet):
    m = 13
    g1 = (2360, 1130, 76)
    rot1 = 0.04
    draw_gear(s, *g1, m, rot1, spokes=6, hub_sun=True)
    rp1 = m * g1[2] / 2

    phi2 = math.radians(-38)
    n2 = 28
    rp2 = m * n2 / 2
    c2 = (g1[0] + (rp1 + rp2) * math.cos(phi2), g1[1] + (rp1 + rp2) * math.sin(phi2))
    rot2 = mesh_rotation(rot1, g1[2], n2, phi2)
    draw_gear(s, *c2, n2, m, rot2, spokes=4)

    phi3 = math.radians(30)
    n3 = 18
    rp3 = m * n3 / 2
    c3 = (c2[0] + (rp2 + rp3) * math.cos(phi3), c2[1] + (rp2 + rp3) * math.sin(phi3))
    rot3 = mesh_rotation(rot2, n2, n3, phi3)
    draw_gear(s, *c3, n3, m, rot3, spokes=3)

    # Orbits struck from the great wheel's arbor, compass-style.
    for r, dash, op in ((rp1 + 260, "2 14", 0.9), (rp1 + 420, None, 0.55), (rp1 + 620, "28 18", 0.5)):
        s.circle(g1[0], g1[1], r, "line", 1.2, dash, op)
    for r, a, size in ((rp1 + 260, 200, 16), (rp1 + 420, 158, 11), (rp1 + 620, 214, 22)):
        x = g1[0] + r * math.cos(math.radians(a))
        y = g1[1] + r * math.sin(math.radians(a))
        s.circle(x, y, size, "gilt", 2.2)
        s.circle(x, y, size + 12, "line", 1.0, "3 6")

    s.dimension(g1[0], g1[1], g1[0] + rp1 * math.cos(math.radians(150)), g1[1] + rp1 * math.sin(math.radians(150)),
                f"z = {g1[2]}", offset=-36)
    s.dimension(c2[0] - rp2, c2[1] - rp2 - 70, c2[0] + rp2, c2[1] - rp2 - 70, f"{n2} : {g1[2]}", offset=-20)

    s.text(300, 360, "FIG. I", "rubric", 28, spacing=4)
    s.text(300, 410, "rota dentata, con rocchetto", "ink", 34)
    s.text(300, 452, "76 · 28 · 18", "muted", 26, spacing=2)
    s.line(300, 488, 820, 488, "line", 1.2)
    s.notes(760, 620, QUOTES["orrery"], size=40, leading=60)
    scale_bar(s, 300, 1880)


def scale_bar(s: Sheet, x, y, units=4, unit=120):
    s.line(x, y, x + units * unit, y, "muted", 1.6)
    for k in range(units + 1):
        s.line(x + k * unit, y - (14 if k % 2 == 0 else 8), x + k * unit, y, "muted", 1.6)
        if k % 2 == 0:
            s.text(x + k * unit, y + 38, str(k), "muted", 22, "middle")
    for k in range(units):
        if k % 2 == 0:
            s.path(f"M{pt(x + k * unit, y)} h{unit} v6 h{-unit} Z", "muted", 1.2, fill=s.p["muted"], opacity=0.8)
    s.text(x + units * unit + 28, y + 6, "braccia", "muted", 22)


def rhombicuboctahedron():
    a = 1 + math.sqrt(2)
    verts = set()
    for base in ((1, 1, a), (1, a, 1), (a, 1, 1)):
        for sx in (1, -1):
            for sy in (1, -1):
                for sz in (1, -1):
                    verts.add((base[0] * sx, base[1] * sy, base[2] * sz))
    verts = sorted(verts)
    normals = []
    for axis in range(3):
        for sgn in (1, -1):
            n = [0, 0, 0]
            n[axis] = sgn
            normals.append(tuple(n))
    for i, j in ((0, 1), (0, 2), (1, 2)):
        for si in (1, -1):
            for sj in (1, -1):
                n = [0, 0, 0]
                n[i], n[j] = si, sj
                normals.append(tuple(n))
    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                normals.append((sx, sy, sz))
    faces = []
    for n in normals:
        dots = [sum(v[k] * n[k] for k in range(3)) for v in verts]
        top = max(dots)
        idx = [i for i, d in enumerate(dots) if abs(d - top) < 1e-6]
        faces.append((n, idx))
    return verts, faces


def rotate(v, yaw, pitch, roll=0.0):
    x, y, z = v
    c, s_ = math.cos(yaw), math.sin(yaw)
    x, z = c * x + s_ * z, -s_ * x + c * z
    c, s_ = math.cos(pitch), math.sin(pitch)
    y, z = c * y - s_ * z, s_ * y + c * z
    c, s_ = math.cos(roll), math.sin(roll)
    x, y = c * x - s_ * y, s_ * x + c * y
    return x, y, z


def draw_vacuus(s: Sheet):
    verts, faces = rhombicuboctahedron()
    yaw, pitch, roll = math.radians(27), math.radians(-19), math.radians(4)
    cx, cy, scale, dist = 2420, 1150, 238, 14.0
    rv = [rotate(v, yaw, pitch, roll) for v in verts]

    def project(v):
        k = dist / (dist - v[2])
        return cx + v[0] * scale * k, cy - v[1] * scale * k

    pv = [project(v) for v in rv]

    def ordered(idx, n):
        # Order a face's vertices around its centroid in the face plane.
        c3 = [sum(rv[i][k] for i in idx) / len(idx) for k in range(3)]
        nn = rotate(n, yaw, pitch, roll)
        ref = [rv[idx[0]][k] - c3[k] for k in range(3)]
        cross = (nn[1] * ref[2] - nn[2] * ref[1], nn[2] * ref[0] - nn[0] * ref[2], nn[0] * ref[1] - nn[1] * ref[0])

        def ang(i):
            d = [rv[i][k] - c3[k] for k in range(3)]
            return math.atan2(sum(d[k] * cross[k] for k in range(3)), sum(d[k] * ref[k] for k in range(3)))

        return sorted(idx, key=ang), c3, nn

    back, front = [], []
    for n, idx in faces:
        order, c3, nn = ordered(idx, n)
        (front if nn[2] > 0 else back).append((order, c3, nn))

    # Circumscribed sphere and axes: the compass work under the solid.
    R = math.sqrt(1 + 1 + (1 + math.sqrt(2)) ** 2) * scale
    s.circle(cx, cy, R * 1.02, "line", 1.2, "10 12")
    s.circle(cx, cy, R * 1.24, "line", 1.0, "2 12", 0.8)
    s.crosshair(cx, cy, R * 1.3)
    s.path(f"M{pt(cx - R * 1.02, cy)} A{f(R * 1.02)},{f(R * 0.34)} 0 0 0 {pt(cx + R * 1.02, cy)}", "line", 1.1, "6 10")

    edges = set()
    for order, _, _ in back:
        for a, b in zip(order, order[1:] + order[:1]):
            edges.add(tuple(sorted((a, b))))
    for a, b in edges:
        s.line(*pv[a], *pv[b], "line", 1.4, "8 9")

    for order, c3, nn in front:
        outer = [pv[i] for i in order]
        inner_3d = [[c3[k] + (rv[i][k] - c3[k]) * 0.66 for k in range(3)] for i in order]
        inner = [project(v) for v in inner_3d]
        s.path("M" + " L".join(pt(*q) for q in outer) + " Z", "gilt", 2.6)
        s.path("M" + " L".join(pt(*q) for q in inner) + " Z", "gilt", 1.6)
        # Light from the upper left: shade the beams on faces turned away.
        light = (-0.5, 0.6, 0.62)
        lam = sum(nn[k] * light[k] for k in range(3)) / math.sqrt(sum(c * c for c in nn))
        if lam < 0.15:
            hatch_beam(s, outer, inner)

    top = min(range(len(pv)), key=lambda i: pv[i][1] if rv[i][2] > -0.5 else 1e9)
    tx, ty = pv[top]
    s.line(tx, ty, tx, s.inset + 2, "muted", 1.4)
    s.circle(tx, ty - 22, 14, "muted", 1.6)

    s.text(300, 360, "FIG. XII", "rubric", 28, spacing=4)
    s.text(300, 410, "vigintisex basium planus vacuus", "ink", 34)
    s.text(300, 452, "26 basi · 48 lati · 24 angoli", "muted", 26, spacing=1)
    s.line(300, 488, 900, 488, "line", 1.2)
    s.notes(900, 620, QUOTES["vacuus"], size=34, leading=52)
    s.text(cx, cy + R * 1.24 + 64, "XII", "rubric", 30, "middle", spacing=6)
    scale_bar(s, 300, 1880)


def hatch_beam(s: Sheet, outer, inner):
    """Parallel hatching across each beam of a shaded face, as in pen studies."""
    n = len(outer)
    for k in range(n):
        o0, o1 = outer[k], outer[(k + 1) % n]
        i0, i1 = inner[k], inner[(k + 1) % n]
        for t in (0.2, 0.4, 0.6, 0.8):
            a = (o0[0] + (o1[0] - o0[0]) * t, o0[1] + (o1[1] - o0[1]) * t)
            b = (i0[0] + (i1[0] - i0[0]) * t, i0[1] + (i1[1] - i0[1]) * t)
            s.line(*a, *b, "gilt", 1.0, opacity=0.55)


def draw_oculus(s: Sheet):
    # Section of the eye, front to the left, after the Paris Ms D studies.
    ex, ey, R = 1900, 1120, 430
    s.circle(ex, ey, R, "gilt", 2.6)
    s.circle(ex, ey, R - 26, "gilt", 1.4)
    s.circle(ex, ey, R - 58, "line", 1.2, "8 10")
    # Cornea: a smaller sphere bulging forward.
    cr = 210
    ccx = ex - R + 130
    ang = math.degrees(math.acos((R ** 2 + (ex - ccx) ** 2 - cr ** 2) / (2 * R * (ex - ccx))))
    p_top = (ex - R * math.cos(math.radians(ang)), ey - R * math.sin(math.radians(ang)))
    p_bot = (p_top[0], 2 * ey - p_top[1])
    s.path(f"M{pt(*p_top)} A{f(cr)},{f(cr)} 0 0 0 {pt(*p_bot)}", "gilt", 2.6)
    # Iris and pupil in section.
    ix = ex - R + 150
    s.line(ix, ey - 170, ix, ey - 46, "gilt", 3.2)
    s.line(ix, ey + 46, ix, ey + 170, "gilt", 3.2)
    # Crystalline lens.
    lx = ix + 70
    s.add(f'<ellipse cx="{f(lx)}" cy="{f(ey)}" rx="62" ry="128" {s.stroke("gilt", 2.2)}/>')
    s.add(f'<ellipse cx="{f(lx)}" cy="{f(ey)}" rx="34" ry="96" {s.stroke("line", 1.2, "5 7")}/>')
    # Optic nerve leaving the back of the globe.
    nx = ex + R * math.cos(math.radians(14))
    for sgn in (1, -1):
        y0 = ey + sgn * R * math.sin(math.radians(14))
        s.path(f"M{pt(nx, y0)} C{pt(nx + 160, y0)} {pt(nx + 260, y0 + sgn * 30)} {pt(nx + 420, y0 + sgn * 70)}", "gilt", 2.2)

    # Object: a lit candle, far left; rays cross at the lens and invert on the retina.
    ox, oy_top, oy_bot = 520, ey - 300, ey + 300
    s.line(ox, oy_top + 70, ox, oy_bot, "gilt", 2.6)
    s.path(f"M{pt(ox - 26, oy_bot)} H{f(ox + 26)}", "gilt", 2.6)
    s.path(f"M{pt(ox, oy_top + 70)} C{pt(ox - 22, oy_top + 40)} {pt(ox - 10, oy_top + 10)} {pt(ox, oy_top - 20)} "
           f"C{pt(ox + 10, oy_top + 10)} {pt(ox + 22, oy_top + 40)} {pt(ox, oy_top + 70)}", "rubric", 2.2)
    retina_x = ex + R - 26
    focus = (lx, ey)
    for src_y in (oy_top + 20, oy_top + 120, ey, oy_bot - 120, oy_bot - 10):
        t = (retina_x - focus[0]) / (focus[0] - ox)
        dst_y = ey - (src_y - ey) * t
        role = "rubric" if src_y in (oy_top + 20, oy_bot - 10) else "gilt"
        width = 1.6 if role == "rubric" else 1.1
        s.line(ox, src_y, focus[0], focus[1], role, width, None, 0.9)
        s.line(focus[0], focus[1], retina_x, dst_y, role, width, "10 8", 0.9)
    s.dimension(ox, oy_bot + 90, ex - R, oy_bot + 90, "distantia", offset=0)

    # The iris in plan as an escapement wheel: clockwork and eye at once.
    wx, wy, wr = 3020, 1000, 300
    teeth = 30
    d = []
    for k in range(teeth):
        a0 = k * 2 * math.pi / teeth
        a1 = a0 + 2 * math.pi / teeth
        p0 = (wx + wr * math.cos(a0), wy + wr * math.sin(a0))
        tip = (wx + (wr + 46) * math.cos(a0 + 0.06), wy + (wr + 46) * math.sin(a0 + 0.06))
        p1 = (wx + wr * math.cos(a1), wy + wr * math.sin(a1))
        d.append(("M" if k == 0 else "L") + pt(*p0) + " L" + pt(*tip) + f" A{wr},{wr} 0 0 1 " + pt(*p1))
    s.path(" ".join(d) + " Z", "gilt", 2.4)
    s.circle(wx, wy, wr - 40, "gilt", 1.6)
    s.circle(wx, wy, 132, "gilt", 2.2)
    s.circle(wx, wy, 70, "gilt", 1.4, fill=s.p["sheet"])
    for k in range(72):
        a = k * 2 * math.pi / 72
        r0, r1 = 140, wr - 52 - (18 if k % 3 else 0)
        s.line(wx + r0 * math.cos(a), wy + r0 * math.sin(a), wx + r1 * math.cos(a), wy + r1 * math.sin(a),
               "gilt", 1.0, opacity=0.6)
    wired_sun(s, wx, wy, 44, "gilt", 2.4)
    s.crosshair(wx, wy, wr + 110)
    # Leader from the section's iris to the plan view.
    s.path(f"M{pt(ix + 6, ey - 150)} C{pt(ix + 300, ey - 620)} {pt(wx - 600, wy - 540)} {pt(wx - wr - 60, wy - 40)}",
           "rubric", 1.4, "2 10")
    s.text(wx, wy + wr + 140, "pupilla · rota", "rubric", 26, "middle", spacing=3)

    s.text(300, 360, "FIG. III", "rubric", 28, spacing=4)
    s.text(300, 410, "dell'occhio, in sezione", "ink", 34)
    s.text(300, 452, "lume · cristallino · nervo", "muted", 26, spacing=1)
    s.line(300, 488, 900, 488, "line", 1.2)
    s.notes(3600, 1640, QUOTES["oculus"], size=30, leading=46)
    scale_bar(s, 300, 1880)


DRAWINGS = [
    ("01-orrery", "TAV. I", "rota dentata", draw_orrery),
    ("02-vacuus", "TAV. XII", "vigintisex basium vacuus", draw_vacuus),
    ("03-oculus", "TAV. III", "oculus", draw_oculus),
]


# ---------------------------------------------------------------- preview

def preview_overlay(theme: dict) -> str:
    c, p = theme["colors"], theme["site"]
    PW, PH = 2560, 1440
    gap, bar = 14, 40
    grad_stops = [part for part in c["hyprland_active_border"].split() if part.startswith("rgba")]
    stops = []
    for k, g in enumerate(grad_stops):
        hexpart = g[5:-1]
        stops.append(f'<stop offset="{k / max(1, len(grad_stops) - 1)}" stop-color="#{hexpart[:6]}"/>')
    inactive = "#" + c["hyprland_inactive_border"][5:11]
    mono = FONT
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}">',
           f'<defs><linearGradient id="ab" x1="0" y1="0" x2="1" y2="1">{"".join(stops)}</linearGradient></defs>']
    # Bar.
    out.append(f'<rect width="{PW}" height="{bar}" fill="{c["background"]}"/>')
    for k in range(5):
        col = c["accent"] if k == 0 else c["foreground"]
        op = "1" if k < 3 else "0.45"
        out.append(f'<text x="{28 + k * 34}" y="27" font-family="{mono}" font-size="18" fill="{col}" fill-opacity="{op}">{k + 1}</text>')
    out.append(f'<text x="{PW / 2}" y="27" font-family="{mono}" font-size="18" fill="{c["foreground"]}" text-anchor="middle">Monday 14:32</text>')
    out.append(f'<text x="{PW - 28}" y="27" font-family="{mono}" font-size="18" fill="{c["foreground"]}" text-anchor="end">⏻  ◐  ▲  ≡</text>')

    def window(x, y, w, h, active):
        border = "url(#ab)" if active else inactive
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c["background"]}" fill-opacity="0.97" '
                   f'stroke="{border}" stroke-width="3"/>')

    # Left column: editor above an active terminal. The drawing stays visible on the right.
    lw = 1120
    ex, ey, eh = gap * 2, bar + gap, 420
    window(ex, ey, lw, eh, False)
    lx, ly = gap * 2, ey + eh + gap * 2
    lh = PH - ly - gap * 2
    window(lx, ly, lw, lh, True)
    nw, nh = 640, 150
    nx, ny = PW - gap * 2 - nw, bar + gap * 2
    window(nx, ny, nw, nh, True)

    def spans(x, y, parts, size=22):
        s = f'<text x="{x}" y="{y}" font-family="{mono}" font-size="{size}" xml:space="preserve">'
        for text, key in parts:
            s += f'<tspan fill="{c[key]}">{escape(text)}</tspan>'
        out.append(s + "</text>")

    ty = ly + 50
    lines = [
        [("~/src/tessera", "blue"), (" on ", "foreground"), (" main", "magenta"), (" ⇡1", "cyan")],
        [("❯ ", "green"), ("git log --oneline -4", "foreground")],
        [("3f9c2e1 ", "yellow"), ("feat(notes): added perspective compare", "foreground")],
        [("a17d0b4 ", "yellow"), ("fix(sync): kept highlights on rename", "foreground")],
        [("9be4410 ", "yellow"), ("docs: described the reading sheet", "foreground")],
        [("27c81fa ", "yellow"), ("chore: bumped astro to 6", "muted")],
        [("", "foreground")],
        [("❯ ", "green"), ("ls", "foreground")],
        [("anacyclosis.md  ", "foreground"), ("assets/  ", "blue"), ("build.sh  ", "green"), ("notes/  ", "blue"), ("README.md", "foreground")],
        [("", "foreground")],
        [("❯ ", "green"), ("cargo test", "foreground")],
        [("   Compiling ", "green"), ("tessera-core v0.9.2", "foreground")],
        [("warning", "yellow"), (": unused import `Highlight`", "foreground")],
        [("error[E0502]", "red"), (": cannot borrow `sheet` as mutable", "foreground")],
        [("test result: ", "foreground"), ("ok", "green"), (". 214 passed; 0 failed", "foreground")],
        [("", "foreground")],
        [("❯ ", "green"), ("█", "foreground")],
    ]
    for k, parts in enumerate(lines):
        spans(lx + 34, ty + k * 38, parts)
    # Palette strip.
    sy = ly + lh - 128
    names = ["background", "red", "green", "yellow", "blue", "magenta", "cyan", "foreground"]
    brights = ["muted", "bright_red", "bright_green", "bright_yellow", "bright_blue", "bright_magenta", "bright_cyan", "bright_foreground"]
    for row, keys in enumerate((names, brights)):
        for k, key in enumerate(keys):
            out.append(f'<rect x="{lx + 34 + k * 136}" y="{sy + row * 52}" width="124" height="40" fill="{c[key]}" '
                       f'stroke="{p["line"]}" stroke-width="1"/>')

    code = [
        [("// The reading sheet keeps each perspective distinct.", "muted")],
        [("pub fn ", "magenta"), ("compare", "blue"), ("(", "foreground"), ("notes", "foreground"), (": &[", "foreground"), ("Note", "yellow"), ("]) -> ", "foreground"), ("Sheet", "yellow"), (" {", "foreground")],
        [("    let ", "magenta"), ("mut ", "magenta"), ("sheet = ", "foreground"), ("Sheet", "yellow"), ("::", "foreground"), ("new", "blue"), ("(", "foreground"), ('"anacyclosis"', "green"), (");", "foreground")],
        [("    for ", "magenta"), ("note ", "foreground"), ("in ", "magenta"), ("notes.", "foreground"), ("iter", "blue"), ("().", "foreground"), ("take", "blue"), ("(", "foreground"), ("6", "orange"), (") {", "foreground")],
        [("        sheet.", "foreground"), ("holder", "blue"), ("(note.", "foreground"), ("author", "cyan"), (", note.", "foreground"), ("shape", "cyan"), (");", "foreground")],
        [("    }", "foreground")],
        [("    sheet", "foreground")],
        [("}", "foreground")],
    ]
    for k, parts in enumerate(code):
        spans(ex + 34, ey + 56 + k * 38, parts)
    # Selection sample in the editor.
    out.append(f'<rect x="{ex + 30}" y="{ey + 56 + 2 * 38 - 27}" width="560" height="36" fill="{c["selection"]}" fill-opacity="0.85"/>')
    spans(ex + 34, ey + 56 + 2 * 38, code[2])
    status_y = ey + eh - 24
    out.append(f'<rect x="{ex + 3}" y="{status_y - 26}" width="{lw - 6}" height="40" fill="{c["lighter_background"]}"/>')
    spans(ex + 30, status_y, [(" NORMAL ", "accent"), ("  sheet.rs", "foreground"), ("   rust · utf-8", "muted")], 20)

    # Notification card.
    spans(nx + 30, ny + 46, [("Solforge", "accent")], 22)
    spans(nx + 30, ny + 86, [("Tessera synced 214 notes and 11 questions.", "foreground")], 22)
    spans(nx + 30, ny + 122, [("Anacyclosis · six perspectives compared", "light_foreground")], 22)
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------- output

def write_colors(theme: dict, dest: Path) -> None:
    c = theme["colors"]
    lines = [f"# {theme['name']}: oxblood desk, vellum sheet, clockwork gilt. After solforged.io."]
    for key in COLOR_ORDER:
        if key is None:
            lines.append("")
        else:
            lines.append(f'{key} = "{c[key]}"')
    (dest / "colors.toml").write_text("\n".join(lines) + "\n")
    (dest / "icons.theme").write_text(theme["icons"] + "\n")
    (dest / "chromium.theme").write_text(",".join(str(v) for v in rgb(c["background"])) + "\n")


def omp_theme(variant: str, theme: dict) -> str:
    """omp theme with a `terminal` section, which Tern uses for its panes and chrome."""
    u, c = theme["ui"], theme["colors"]
    ansi = [u["ansi0"], c["red"], c["green"], c["yellow"], c["blue"], c["magenta"], c["cyan"], u["ansi7"],
            c["muted"], c["bright_red"], c["bright_green"], c["bright_yellow"], c["bright_blue"],
            c["bright_magenta"], c["bright_cyan"], u["ansi15"]]
    doc = {
        "$schema": "https://raw.githubusercontent.com/can1357/oh-my-pi/main/packages/coding-agent/src/modes/theme/theme-schema.json",
        "name": f"solforge-{variant}",
        "vars": u,
        "colors": OMP_ROLES,
        "export": {"pageBg": "bg", "cardBg": "bg_alt", "infoBg": "bg_hl"},
        "terminal": {"background": "bg", "foreground": "fg", "chrome": "chrome", "widget": "widget", "ansi": ansi},
    }
    return json.dumps(doc, indent=2) + "\n"


def omp_report(theme: dict) -> None:
    """Lowest contrast of each text role over the surfaces omp draws it on."""
    u = theme["ui"]
    surfaces = ["bg", "bg_alt", "bg_hl", "sel", "diff_add", "diff_delete"]
    texts = ["fg", "fg_bright", "gray", "comment", "gilt", "rubric", "red", "orange", "green", "cyan", "blue", "madder"]
    low = sorted((contrast(u[t], u[s]), t, s) for t in texts for s in surfaces)[:3]
    print("  omp lowest: " + ", ".join(f"{t} on {s} {r:.1f}" for r, t, s in low))


def render(svg: str, png: Path, width: int | None = None) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as tmp:
        tmp.write(svg)
    cmd = ["rsvg-convert", tmp.name, "-o", str(png)]
    if width:
        cmd[1:1] = ["-w", str(width)]
    subprocess.run(cmd, check=True)
    Path(tmp.name).unlink()


def report(theme: dict) -> None:
    c = theme["colors"]
    bg = c["background"]
    keys = ["foreground", "light_foreground", "muted", "accent", "red", "yellow", "orange", "green", "cyan",
            "blue", "magenta", "brown", "bright_red", "bright_yellow", "bright_green", "bright_cyan",
            "bright_blue", "bright_magenta"]
    worst = min(keys, key=lambda k: contrast(c[k], bg))
    print(f"  contrast on {bg}: " + " ".join(f"{k}={contrast(c[k], bg):.1f}" for k in keys))
    print(f"  selection text {contrast(c['selection_foreground'], c['selection']):.1f}; lowest {worst}")


def main() -> int:
    for tool in ("rsvg-convert", "magick"):
        if not shutil.which(tool):
            print(f"missing {tool}", file=sys.stderr)
            return 1
    only = set(sys.argv[1:])
    for variant, theme in THEMES.items():
        dest = ROOT / f"omarchy-solforge-{variant}-theme"
        bgdir = dest / "backgrounds"
        bgdir.mkdir(parents=True, exist_ok=True)
        print(f"{theme['name']} -> {dest}")
        write_colors(theme, dest)
        report(theme)
        (ROOT / "omp").mkdir(exist_ok=True)
        (ROOT / "omp" / f"solforge-{variant}.json").write_text(omp_theme(variant, theme))
        omp_report(theme)
        for slug, plate, title, draw in DRAWINGS:
            if only and slug not in only:
                continue
            sheet = Sheet(theme["site"], plate, title)
            draw(sheet)
            render(sheet.svg(), bgdir / f"{slug}.png")
            print(f"  {slug}.png")
        # Preview: first background under a mock desktop.
        with tempfile.TemporaryDirectory() as tmp:
            overlay = Path(tmp) / "overlay.png"
            render(preview_overlay(theme), overlay)
            subprocess.run(
                ["magick", str(bgdir / "01-orrery.png"), "-resize", "2560x1440", str(overlay),
                 "-composite", "-define", "png:exclude-chunks=date,time", str(dest / "preview.png")],
                check=True,
            )
        print("  preview.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
