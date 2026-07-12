"""tiles.graybox — M1 gray-box tileset (floor, wall, floor_var, marker).

4 tiles of 16x16 art px on one row, baked at 2x -> 32x32 cells.
Palette contract: ONLY the ``stone`` and ``void`` ramps (plan section 2).
Sidecar: ``{grid:{cell,cols,rows}, tiles:[...]}`` — atlas order is append-only.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from ..canvas import PixelCanvas
from ..palette import Palette, Ramp

ART_CELL = 16
TILE_ORDER = ("floor", "wall", "floor_var", "marker")
FLOOR_SPECKLES = 9
VAR_PEBBLES = 3


def generate(manifest: dict, palette: Palette, out_root: Path) -> None:
    art_cell = int(manifest.get("art_cell", ART_CELL))
    if art_cell != ART_CELL:
        raise ValueError(f"tiles.graybox only draws {ART_CELL}px cells, got {art_cell}")
    scale = int(manifest.get("scale", 2))
    tiles = tuple(manifest.get("tiles", TILE_ORDER))
    rng = random.Random(manifest["seed"])
    stone = palette.ramp("stone")
    void = palette.ramp("void")

    drawers = {
        "floor": _draw_floor,
        "wall": _draw_wall,
        "floor_var": _draw_floor_var,
        "marker": _draw_marker,
    }
    sheet = PixelCanvas(ART_CELL * len(tiles), ART_CELL, palette)
    for col, tile_name in enumerate(tiles):
        tile = PixelCanvas(ART_CELL, ART_CELL, palette)
        drawers[tile_name](tile, stone, void, rng)
        sheet.paste(tile, col * ART_CELL, 0)

    out_png = Path(out_root) / manifest.get("out", "tiles/graybox_sheet.png")
    sheet.save(out_png, scale=scale)
    sidecar = {
        "grid": {"cell": ART_CELL * scale, "cols": len(tiles), "rows": 1},
        "tiles": list(tiles),
    }
    out_png.with_suffix(".json").write_text(
        json.dumps(sidecar, indent=2) + "\n", encoding="utf-8"
    )


def _draw_floor(c: PixelCanvas, stone: Ramp, _void: Ramp, rng: random.Random) -> None:
    c.rect(0, 0, ART_CELL, ART_CELL, stone[1])
    # Sparse darker speckles so large floors do not read as a flat sheet.
    for _ in range(FLOOR_SPECKLES):
        x = rng.randrange(ART_CELL)
        y = rng.randrange(ART_CELL)
        c.put(x, y, stone[0])
    # Faint mortar seam along the top/left keeps the 32px grid readable.
    c.hline(0, ART_CELL - 1, 0, stone[0])
    c.vline(0, 0, ART_CELL - 1, stone[0])


def _draw_wall(c: PixelCanvas, stone: Ramp, void: Ramp, _rng: random.Random) -> None:
    c.rect(0, 0, ART_CELL, ART_CELL, stone[2])
    c.rect(1, 1, ART_CELL - 2, 3, stone[3])  # top-lit cap (global light: above)
    c.rect(1, ART_CELL - 3, ART_CELL - 2, 2, stone[1])  # base shadow
    # Darkest frame so wall blocks read as solid mass against the floor.
    c.hline(0, ART_CELL - 1, 0, void[0])
    c.hline(0, ART_CELL - 1, ART_CELL - 1, void[0])
    c.vline(0, 0, ART_CELL - 1, void[0])
    c.vline(ART_CELL - 1, 0, ART_CELL - 1, void[0])


def _draw_floor_var(c: PixelCanvas, stone: Ramp, void: Ramp, rng: random.Random) -> None:
    _draw_floor(c, stone, void, rng)
    # A short crack plus a few lighter pebbles — enough to break repetition.
    x = rng.randrange(3, 9)
    y = rng.randrange(3, 9)
    for i in range(5):
        c.put(x + i, y + (i // 2), stone[0])
    for _ in range(VAR_PEBBLES):
        c.put(rng.randrange(2, ART_CELL - 2), rng.randrange(2, ART_CELL - 2), stone[2])


def _draw_marker(c: PixelCanvas, stone: Ramp, void: Ramp, rng: random.Random) -> None:
    _draw_floor(c, stone, void, rng)
    # Light diamond with a dark core: a legible spawn/orientation glyph.
    cx = ART_CELL // 2
    radius = 5
    for i in range(radius + 1):
        c.put(cx - radius + i, cx - i, stone[3])
        c.put(cx - radius + i, cx + i, stone[3])
        c.put(cx + radius - i, cx - i, stone[3])
        c.put(cx + radius - i, cx + i, stone[3])
    c.rect(cx - 1, cx - 1, 2, 2, void[0])
