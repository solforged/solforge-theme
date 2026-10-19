#!/usr/bin/env python3
"""Generate the Solforge Omarchy themes: palette files, backgrounds, previews.

The palettes extend the solforged.io sheet tokens (desk, sheet, ink, gilt,
rubric, line, grid) into a full Omarchy colors.toml. Backgrounds are
construction drawings after Leonardo's notebooks, drawn as wireframes on the
site's sheet-on-desk layout. Requires rsvg-convert and ImageMagick.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from drawings import FONT, PLATES, Sheet

ROOT = Path(__file__).resolve().parent

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
        if not only:
            keep = {f"{slug}.png" for slug, *_ in PLATES}
            for old in bgdir.glob("*.png"):
                if old.name not in keep:
                    old.unlink()
        for slug, plate, title, draw in PLATES:
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
                ["magick", str(bgdir / f"{PLATES[0][0]}.png"), "-resize", "2560x1440", str(overlay),
                 "-composite", "-define", "png:exclude-chunks=date,time", str(dest / "preview.png")],
                check=True,
            )
        print("  preview.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
