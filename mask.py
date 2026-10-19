"""Tunon's Face of Judgment, drawn in braille for the Hermes banner.

The canvas is 56x60 dots, which braille packs into 28 columns by 15 rows: the
size of the caduceus in Hermes' default skin. Each dot is about square in a
terminal cell, so the coordinates below read as a picture. The drawing is
mirrored about the centre line unless a stroke says otherwise.
"""

from __future__ import annotations

import math
from itertools import pairwise

W, H = 56, 60
CX = (W - 1) / 2

# Braille dot bits by (column, row) inside a 2x4 cell.
DOTS = {(0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (1, 0): 0x08,
        (1, 1): 0x10, (1, 2): 0x20, (0, 3): 0x40, (1, 3): 0x80}


class Dots:
    def __init__(self) -> None:
        self.grid = [[False] * W for _ in range(H)]

    def plot(self, x: float, y: float, mirror: bool = True) -> None:
        for px in (x, W - 1 - x) if mirror else (x,):
            xi, yi = round(px), round(y)
            if 0 <= xi < W and 0 <= yi < H:
                self.grid[yi][xi] = True

    def line(self, a, b, mirror: bool = True) -> None:
        (x0, y0), (x1, y1) = a, b
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(n + 1):
            t = i / n
            self.plot(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, mirror)

    def poly(self, pts, mirror: bool = True) -> None:
        for a, b in pairwise(pts):
            self.line(a, b, mirror)

    def arch(self, apex_y: float, side_x: float, base_y: float, k: float) -> None:
        """Half an arch from the apex on the centre line down to (side_x, base_y)."""
        self.poly([(CX + (side_x - CX) * t, apex_y + (base_y - apex_y) * t ** k)
                   for t in (i / 40 for i in range(41))])

    def circle(self, cx: float, cy: float, r: float) -> None:
        for i in range(60):
            a = 2 * math.pi * i / 60
            self.plot(cx + r * math.cos(a), cy + r * math.sin(a), mirror=False)

    def braille(self) -> list[str]:
        return ["".join(
            chr(0x2800 + sum(bit for (dx, dy), bit in DOTS.items() if self.grid[r * 4 + dy][c * 2 + dx]))
            for c in range(W // 2)) for r in range(H // 4)]


def face_of_judgment() -> list[str]:
    """The flat metal mask framed by the red hood band, over Kyros' sigil."""
    d = Dots()
    # Hood: the outer edge and the inner edge of the red band, falling as drapes.
    d.arch(0, 5, 30, k=1.6)
    d.line((5, 30), (1, 59))
    d.arch(4, 10, 28, k=1.6)
    d.line((10, 28), (8, 59))
    # Mask plate: domed brow, flat sides, jaw cut in to a square chin.
    d.arch(8, 14, 17, k=1.7)
    d.line((14, 17), (14, 35))
    d.line((14, 35), (20, 44))
    d.line((20, 44), (CX, 44))
    # A level brow ridge that turns down into the bridge of the nose.
    d.line((16, 20), (25, 20))
    d.line((25, 20), (26, 21))
    # Half-lidded slits: a heavy straight lid, a shallow lower lid, the pupil
    # under the lid. Wide or round eyes read as startled, not impartial.
    d.line((17, 23), (24, 23))
    d.poly([(18, 24), (20, 25), (22, 25), (24, 24)])
    d.plot(21, 24)
    # A narrow nose ridge on a small flat base.
    d.line((26, 21), (26, 30))
    d.poly([(26, 30), (25, 31), (26, 32), (CX, 32)])
    # One firm line for the closed mouth, and the crease above the chin.
    d.line((22, 36), (CX, 36))
    d.line((25, 40), (CX, 40))
    # Kyros' sigil on the chest: a ring round a four-armed star.
    d.circle(CX, 53, 5.2)
    d.line((27, 50), (27, 56))
    d.line((24, 52), (27, 52))
    d.line((24, 53), (27, 53))
    return d.braille()
