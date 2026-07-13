"""tiles.town_exterior — Taşlıca town-square exterior set (M4).

One manifest emits two sheets:
  * tiles/town_sheet.png  — 6 ground tiles (cobble/dirt/scrub + variants),
    16x16 art px baked 2x -> 32x32 cells. Atlas order is append-only.
  * props/town_props.png  — 12 front-facing props (shop facades, houses,
    dolmuş, stop sign, gold poplars, teahouse furniture, çeşme), packed
    tight; sidecar regions/solids in FINAL (2x) pixels.

Golden-hour autumn at altitude: stone, dust, gold poplars, warm windows.
Global light from above, slightly right — top faces lightest, right edges
lit, left edges and undersides shaded (shadows step DOWN the ramp toward
blue-violet, highlights step UP toward warm light).

Palette contract: stone/earth/amber/rose/ship/paper/void ramps only.
The forbidden signal ramp is never touched here.
Determinism: every RNG is random.Random seeded from manifest["seed"] plus a
fixed per-asset tag string — no other entropy source.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from ..canvas import PixelCanvas
from ..palette import Palette, Ramp

ART_CELL = 16

TILE_ORDER = ("cobble", "cobble_var", "dirt", "dirt_var", "scrub", "scrub_var")

# name -> (art_x, art_y, art_w, art_h, solid-in-art-px-or-None) — solid is
# relative to the region's top-left, hugging the floor footprint.
PROP_ORDER = (
    "bakery_facade",
    "bakkal_facade",
    "teahouse_facade",
    "house_a",
    "house_b",
    "minibus",
    "stop_sign",
    "poplar",
    "poplar_small",
    "tea_table",
    "extra_chair",
    "cesme",
)
PROP_LAYOUT = {
    "bakery_facade": (0, 0, 64, 48, (0, 36, 64, 12)),
    "bakkal_facade": (64, 0, 56, 48, (0, 36, 56, 12)),
    "teahouse_facade": (120, 0, 72, 48, (0, 36, 72, 12)),
    "poplar": (192, 0, 16, 48, (4, 42, 8, 6)),
    "house_a": (0, 48, 48, 40, (0, 28, 48, 12)),
    "house_b": (48, 48, 48, 40, (0, 28, 48, 12)),
    "minibus": (96, 48, 48, 26, (0, 18, 48, 8)),
    "poplar_small": (144, 48, 12, 32, (3, 27, 6, 5)),
    "cesme": (156, 48, 20, 24, (0, 16, 20, 8)),
    "stop_sign": (176, 48, 10, 24, (2, 20, 6, 4)),
    "tea_table": (186, 48, 24, 18, (0, 11, 24, 7)),
    "extra_chair": (210, 48, 10, 14, None),
}
PROP_SHEET_W = 220
PROP_SHEET_H = 88


def generate(manifest: dict, palette: Palette, out_root: Path) -> None:
    art_cell = int(manifest.get("art_cell", ART_CELL))
    if art_cell != ART_CELL:
        raise ValueError(f"tiles.town_exterior draws {ART_CELL}px cells, got {art_cell}")
    scale = int(manifest.get("scale", 2))
    seed = manifest["seed"]
    _emit_tiles(manifest, palette, Path(out_root), scale, seed)
    _emit_props(manifest, palette, Path(out_root), scale, seed)


# =========================================================================
# GROUND TILES
# =========================================================================


def _emit_tiles(manifest: dict, palette: Palette, out_root: Path, scale: int, seed) -> None:
    drawers = {
        "cobble": _draw_cobble,
        "cobble_var": _draw_cobble_var,
        "dirt": _draw_dirt,
        "dirt_var": _draw_dirt_var,
        "scrub": _draw_scrub,
        "scrub_var": _draw_scrub_var,
    }
    sheet = PixelCanvas(ART_CELL * len(TILE_ORDER), ART_CELL, palette)
    for col, name in enumerate(TILE_ORDER):
        tile = PixelCanvas(ART_CELL, ART_CELL, palette)
        drawers[name](tile, palette, random.Random(f"{seed}:tile:{name}"))
        sheet.paste(tile, col * ART_CELL, 0)
    out_png = out_root / manifest.get("tiles_out", "tiles/town_sheet.png")
    sheet.save(out_png, scale=scale)
    sidecar = {
        "grid": {"cell": ART_CELL * scale, "cols": len(TILE_ORDER), "rows": 1},
        "tiles": list(TILE_ORDER),
        "solid": [],
    }
    out_png.with_suffix(".json").write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")


# --- cobble --------------------------------------------------------------

# Hand-laid course layout with a 16px wrap period so the square tiles
# seamlessly: (y0, height, stones as (x0, width) spans; x may wrap).
_COBBLE_ROWS = (
    (0, 5, ((0, 7), (8, 7))),   # mortar cols 7, 15 / row y=5
    (6, 5, ((4, 7), (12, 7))),  # second stone wraps 12..15,0..2 / row y=11
    (12, 3, ((1, 7), (9, 6))),  # short course; mortar cols 0, 8, 15 / row y=15
)


def _cobblestone(c: PixelCanvas, x0: int, y0: int, w: int, h: int, stone: Ramp,
                 tone: int, glint: bool) -> None:
    """One rounded cobble; x wraps modulo the 16px tile period."""
    for yy in range(y0, y0 + h):
        for xx in range(x0, x0 + w):
            if (xx in (x0, x0 + w - 1)) and (yy in (y0, y0 + h - 1)):
                continue  # knocked corners -> reads rounded, mortar shows
            idx = tone + 1 if yy == y0 else tone  # top edge catches the light
            c.put_ramp(xx % ART_CELL, yy, stone, idx)
    if glint:  # sun glint on the top-right shoulder
        c.put_ramp((x0 + w - 2) % ART_CELL, y0, stone, tone + 2)
        c.put_ramp((x0 + w - 3) % ART_CELL, y0 + 1, stone, tone + 1)


def _cobble_base(c: PixelCanvas, stone: Ramp, paper: Ramp, rng: random.Random,
                 tones: dict) -> None:
    c.rect(0, 0, ART_CELL, ART_CELL, stone[0])  # mortar bed everywhere
    for ri, (y0, h, stones) in enumerate(_COBBLE_ROWS):
        for si, (x0, w) in enumerate(stones):
            tone, glint = tones.get((ri, si), (1, False))
            _cobblestone(c, x0, y0, w, h, stone, tone, glint)
    # sun catching the mortar: a few warm flecks in the joints
    placed = 0
    for _ in range(20):
        x, y = rng.randrange(ART_CELL), rng.randrange(ART_CELL)
        if c.get(x, y) == stone[0]:
            c.put(x, y, paper[0])
            placed += 1
            if placed >= 4:
                break
    # wear pits inside a couple of stones
    for _ in range(3):
        x, y = rng.randrange(1, 15), rng.randrange(1, 14)
        if c.get(x, y) == stone[1]:
            c.put(x, y, stone[0])


def _draw_cobble(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    stone, paper = palette.ramp("stone"), palette.ramp("paper")
    tones = {(0, 0): (1, True), (1, 0): (2, False), (1, 1): (1, True), (2, 1): (1, True)}
    _cobble_base(c, stone, paper, rng, tones)


def _draw_cobble_var(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    stone, paper = palette.ramp("stone"), palette.ramp("paper")
    tones = {(0, 1): (1, True), (2, 0): (2, True)}
    _cobble_base(c, stone, paper, rng, tones)
    # one cobble gone missing: a ragged sunken gap with a pebble left behind
    c.hline(5, 9, 7, stone[0])
    c.hline(4, 9, 8, stone[0])
    c.hline(5, 8, 9, stone[0])
    c.put(6, 8, stone[1])
    c.put(8, 9, paper[0])
    # a cracked stone in the top course
    c.put(10, 1, stone[0])
    c.put(11, 2, stone[0])
    c.put(11, 3, stone[0])
    c.put(12, 4, stone[0])


# --- dirt ----------------------------------------------------------------


def _draw_dirt(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    earth = palette.ramp("earth")
    c.rect(0, 0, ART_CELL, ART_CELL, earth[1])
    # packed strata: short broken horizontal dashes
    for _ in range(4):
        x, y = rng.randrange(0, 13), rng.randrange(1, 15)
        c.hline(x, x + rng.randrange(2, 4), y, earth[0])
    # speckle — adjacent ramp steps only, sparse
    for _ in range(7):
        c.put(rng.randrange(ART_CELL), rng.randrange(ART_CELL), earth[0])
    for _ in range(5):
        c.put(rng.randrange(ART_CELL), rng.randrange(ART_CELL), earth[2])
    # two half-buried pebbles with a lit top
    for _ in range(2):
        x, y = rng.randrange(1, 14), rng.randrange(2, 14)
        c.put(x, y, earth[2])
        c.put(x + 1, y, earth[2])
        c.put(x + 1, y - 1, earth[3])


def _draw_dirt_var(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    _draw_dirt(c, palette, rng)
    earth = palette.ramp("earth")
    # wheel-rut hint: two broken parallel ruts running N-S, right lips lit
    for rut_x in (4, 11):
        y = 0
        while y < ART_CELL:
            run = rng.randrange(2, 5)
            for i in range(run):
                if y + i < ART_CELL:
                    c.put(rut_x, y + i, earth[0])
            if rng.random() < 0.5 and y + 1 < ART_CELL:
                c.put(rut_x + 1, y + 1, earth[2])  # light catches the rut lip
            y += run + rng.randrange(1, 3)


# --- scrub ---------------------------------------------------------------


def _tuft(c: PixelCanvas, x: int, y: int, earth: Ramp, amber: Ramp,
          rng: random.Random, tall: bool = False) -> None:
    """A clump of dry grass: separate upright blades with ground showing
    between them, splayed outward. y is the ground line."""
    # left blade, leaning out, in shadow
    c.put(x - 2, y, earth[3])
    c.put(x - 2, y - 1, earth[3])
    if tall:
        c.put(x - 3, y - 2, earth[3])
    # center blade, tallest, sunlit tip
    h = 3 if tall else 2
    for i in range(h):
        c.put(x, y - i, amber[0])
    c.put(x, y - h, amber[1])
    # right blade
    c.put(x + 2, y, amber[0])
    c.put(x + 2, y - 1, amber[0])
    if rng.random() < 0.5:
        c.put(x + 3, y - 2, amber[0])
    # a low filler blade and the root shadow
    c.put(x + 1, y, earth[3])
    c.put(x - 1, y + 1, earth[0])
    c.put(x, y + 1, earth[0])


def _draw_scrub(c: PixelCanvas, palette: Palette, rng: random.Random,
                dense: bool = False) -> None:
    earth, amber = palette.ramp("earth"), palette.ramp("amber")
    c.rect(0, 0, ART_CELL, ART_CELL, earth[1])
    for _ in range(6):
        c.put(rng.randrange(ART_CELL), rng.randrange(ART_CELL), earth[0])
    for _ in range(3):
        c.put(rng.randrange(ART_CELL), rng.randrange(ART_CELL), earth[2])
    n = 4 if dense else 2
    spots = [(4, 5), (11, 11), (12, 4), (5, 12)]
    for i in range(n):
        bx, by = spots[i]
        bx += rng.randrange(-1, 2)
        by += rng.randrange(-1, 2)
        bx = max(3, min(12, bx))
        by = max(4, min(12, by))
        _tuft(c, bx, by, earth, amber, rng, tall=dense and i == 0)
    # one stray dry blade, fallen flat
    x, y = rng.randrange(1, 14), rng.randrange(1, 15)
    c.put(x, y, earth[3])
    c.put(x + 1, y, earth[3])


def _draw_scrub_var(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    _draw_scrub(c, palette, rng, dense=True)


# =========================================================================
# PROPS
# =========================================================================


def _emit_props(manifest: dict, palette: Palette, out_root: Path, scale: int, seed) -> None:
    drawers = {
        "bakery_facade": _draw_bakery,
        "bakkal_facade": _draw_bakkal,
        "teahouse_facade": _draw_teahouse,
        "house_a": _draw_house_a,
        "house_b": _draw_house_b,
        "minibus": _draw_minibus,
        "stop_sign": _draw_stop_sign,
        "poplar": _draw_poplar_big,
        "poplar_small": _draw_poplar_small,
        "tea_table": _draw_tea_table,
        "extra_chair": _draw_extra_chair,
        "cesme": _draw_cesme,
    }
    sheet = PixelCanvas(PROP_SHEET_W, PROP_SHEET_H, palette)
    props_meta: dict[str, dict] = {}
    for name in PROP_ORDER:
        x, y, w, h, solid = PROP_LAYOUT[name]
        canvas = drawers[name](palette, random.Random(f"{seed}:prop:{name}"))
        if (canvas.width, canvas.height) != (w, h):
            raise ValueError(f"{name}: drew {canvas.width}x{canvas.height}, layout says {w}x{h}")
        sheet.paste(canvas, x, y)
        props_meta[name] = {
            "region": [x * scale, y * scale, w * scale, h * scale],
            "solid": [v * scale for v in solid] if solid else None,
        }
    out_png = out_root / manifest.get("props_out", "props/town_props.png")
    sheet.save(out_png, scale=scale)
    sidecar = {"scale": scale, "props": props_meta}
    out_png.with_suffix(".json").write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")


# --- shared facade vocabulary --------------------------------------------


def _block_hints(c: PixelCanvas, x0: int, y0: int, w: int, h: int, stone: Ramp,
                 rng: random.Random, n: int) -> None:
    """Suggest a few individual masonry blocks on an otherwise calm wall."""
    for _ in range(n):
        bw = rng.randrange(5, 9)
        bh = rng.randrange(3, 5)
        bx = rng.randrange(x0, max(x0 + 1, x0 + w - bw))
        by = rng.randrange(y0, max(y0 + 1, y0 + h - bh))
        c.hline(bx, bx + bw - 1, by + bh - 1, stone[0])  # bottom joint
        c.vline(bx + bw - 1, by, by + bh - 1, stone[0])  # right joint
        c.hline(bx, bx + bw - 2, by, stone[2])           # lit top edge


def _plaster_patch(c: PixelCanvas, x0: int, y0: int, w: int, h: int, paper: Ramp,
                   rng: random.Random) -> None:
    """Ragged patch of surviving whitewash render over stone."""
    for y in range(y0, y0 + h):
        il = rng.choice((0, 0, 1, 2))
        ir = rng.choice((0, 0, 1, 2))
        if y in (y0, y0 + h - 1):
            il += 1
            ir += 1
        c.hline(x0 + il, x0 + w - 1 - ir, y, paper[1])
    for _ in range(3):  # grime creeping up the lower edge
        c.put(rng.randrange(x0 + 1, x0 + w - 1), y0 + h - 1 - rng.randrange(2), paper[0])


def _foundation(c: PixelCanvas, y0: int, w: int, h: int, stone: Ramp,
                rng: random.Random) -> None:
    """Coursed stone footing along a facade base; bottom row is ground shadow."""
    c.rect(0, y0, w, h, stone[1])
    c.hline(0, w - 1, y0, stone[2])  # light catches the footing ledge
    x = rng.randrange(3, 7)
    while x < w:
        c.vline(x, y0 + 1, y0 + h - 2, stone[0])
        x += rng.randrange(8, 13)
    c.hline(0, w - 1, y0 + h - 1, stone[0])


def _glyph(c: PixelCanvas, x: int, y: int, mask: tuple, color) -> None:
    for dx, dy in mask:
        c.put(x + dx, y + dy, color)


# abstract signage marks — bar-and-notch shapes that read as painted
# lettering without spelling anything (localization/readability rule)
_MARK_BAR_STUB = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (2, 0))
_MARK_SHORT = ((0, 1), (0, 2), (0, 3), (0, 4))
_MARK_DOT_BAR = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (2, 2))
_MARK_ARCH = ((0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2), (0, 3), (2, 3), (0, 4), (2, 4))
_MARK_FOOT = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4), (2, 4), (2, 3))
_MARK_OPEN_BOX = ((1, 0), (2, 0), (0, 1), (0, 2), (0, 3), (1, 4), (2, 4))
_MARK_CHEVRON = ((1, 0), (0, 1), (2, 1), (0, 2), (2, 2), (0, 3), (2, 3), (0, 4), (2, 4))
_MARK_FORK = ((0, 0), (2, 0), (1, 1), (1, 2), (1, 3), (1, 4))


# --- bakery ---------------------------------------------------------------


def _draw_bakery(palette: Palette, rng: random.Random) -> PixelCanvas:
    c = PixelCanvas(64, 48, palette)
    stone = palette.ramp("stone")
    earth = palette.ramp("earth")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    paper = palette.ramp("paper")
    void = palette.ramp("void")

    # parapet cap, top-lit
    c.rect(0, 0, 64, 2, stone[2])
    c.hline(0, 63, 0, stone[3])
    c.rect(0, 2, 64, 3, stone[1])  # fascia in the cap's shadow
    # wall body
    c.rect(0, 5, 64, 37, stone[1])
    _block_hints(c, 1, 14, 62, 26, stone, rng, n=7)
    c.vline(0, 5, 41, stone[0])   # shaded left edge
    c.vline(63, 5, 41, stone[2])  # lit right edge

    # sign board: dark timber, warm painted marks (FIRIN cadence, unreadable)
    c.rect(4, 6, 56, 8, earth[1])
    c.hline(4, 59, 6, earth[2])
    c.hline(4, 59, 13, earth[0])
    c.vline(4, 6, 13, earth[0])
    c.vline(59, 6, 13, earth[0])
    for i, mark in enumerate((_MARK_BAR_STUB, _MARK_SHORT, _MARK_DOT_BAR, _MARK_SHORT, _MARK_ARCH)):
        _glyph(c, 18 + i * 6, 8, mark, amber[2])

    # rose awning over the bread window, scalloped, casting shadow
    for sx in range(2, 32, 4):
        col = rose[2] if (sx // 4) % 2 == 0 else rose[1]
        c.rect(sx, 16, 4, 5, col)
        c.put(sx + 1, 21, col)  # scallop tab
        c.put(sx + 2, 21, col)
        c.put(sx + 1, 22, rose[0])
        c.put(sx + 2, 22, rose[0])
    c.hline(2, 33, 16, rose[2])       # sunlit awning top
    c.hline(2, 33, 15, earth[0])      # mounting bar
    c.hline(3, 32, 23, stone[0])      # cast shadow on the wall

    # bread window: warm glow, two loaf shelves
    c.rect(4, 24, 26, 14, earth[0])       # dark outer frame
    c.rect(5, 25, 24, 12, earth[2])       # inner frame
    c.rect(6, 26, 22, 10, amber[0])       # glass / interior glow
    c.rect(8, 26, 18, 4, amber[1])        # brighter near the oven light
    c.hline(6, 27, 30, earth[0])          # upper shelf
    c.hline(6, 27, 35, earth[0])          # lower shelf edge (sill line)
    for lx in (8, 14, 20):                # loaves on the upper shelf
        c.rect(lx, 28, 4, 2, amber[2])
        c.put(lx + 2, 28, amber[3])
        c.put(lx + 3, 28, amber[3])
        c.put(lx, 29, amber[1])
    for lx in (7, 12, 17, 22):            # round loaves below
        c.rect(lx, 32, 3, 2, amber[2])
        c.put(lx + 1, 32, amber[3])
        c.put(lx, 33, amber[1])

    # vent window high right
    c.rect(47, 15, 6, 5, stone[0])
    c.rect(48, 16, 4, 3, void[1])

    # door: stone lintel, plank door, brass handle, glass top
    c.rect(42, 24, 16, 2, stone[2])
    c.hline(42, 57, 24, stone[3])
    c.vline(43, 26, 41, stone[0])
    c.vline(56, 26, 41, stone[0])
    c.rect(44, 26, 12, 16, earth[1])
    c.vline(47, 27, 41, earth[0])
    c.vline(51, 27, 41, earth[0])
    c.vline(55, 26, 41, earth[2])         # lit door edge
    c.rect(45, 27, 10, 4, amber[1])       # glass pane, someone's inside
    c.vline(49, 27, 30, earth[0])
    c.hline(45, 54, 31, earth[0])
    c.put(46, 34, amber[2])               # brass handle
    c.put(46, 35, amber[0])

    # bread crate waiting by the door
    c.rect(32, 35, 9, 7, earth[1])
    c.hline(32, 40, 35, earth[2])
    c.vline(34, 36, 41, earth[0])
    c.vline(37, 36, 41, earth[0])
    for lx in (33, 36, 39):
        c.put(lx, 34, amber[2])
        c.put(lx + 1, 34, amber[2])
        c.put(lx + 1, 33, amber[3])

    # threshold + foundation
    _foundation(c, 42, 64, 6, stone, rng)
    c.rect(45, 42, 10, 2, paper[1])       # worn doorstep
    c.hline(45, 54, 42, paper[2])
    return c


# --- bakkal ---------------------------------------------------------------


def _draw_bakkal(palette: Palette, rng: random.Random) -> PixelCanvas:
    c = PixelCanvas(56, 48, palette)
    stone = palette.ramp("stone")
    earth = palette.ramp("earth")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    ship = palette.ramp("ship")
    paper = palette.ramp("paper")
    void = palette.ramp("void")

    # timber fascia
    c.hline(0, 55, 0, earth[3])
    c.rect(0, 1, 56, 2, earth[2])
    c.hline(0, 55, 3, earth[0])
    # whitewashed upper wall
    c.rect(0, 4, 56, 12, paper[1])
    c.hline(0, 55, 4, paper[0])            # thin shadow under the fascia
    c.vline(0, 4, 15, paper[0])
    c.vline(55, 4, 15, paper[2])
    c.put(2, 14, paper[0])                 # weather stains
    c.put(3, 15, paper[0])
    c.put(50, 15, paper[0])
    # hand-painted teal sign
    c.rect(14, 6, 28, 7, ship[1])
    c.hline(14, 41, 6, ship[2])
    c.hline(14, 41, 12, ship[0])
    c.vline(14, 6, 12, ship[0])
    c.vline(41, 6, 12, ship[0])
    for i, mark in enumerate((_MARK_ARCH, _MARK_SHORT, _MARK_FOOT, _MARK_DOT_BAR)):
        _glyph(c, 19 + i * 5, 7, mark, paper[2])

    # stone shopfront below a paper ledge
    c.hline(0, 55, 16, paper[2])
    c.rect(0, 17, 56, 25, stone[1])
    _block_hints(c, 1, 18, 54, 22, stone, rng, n=5)
    c.vline(0, 17, 41, stone[0])
    c.vline(55, 17, 41, stone[2])

    # display window: teal-painted frame, dim warm interior, jar shelves
    c.rect(3, 18, 22, 19, ship[1])
    c.hline(3, 24, 18, ship[2])
    c.rect(5, 20, 18, 15, amber[0])
    c.hline(5, 22, 25, earth[0])           # upper shelf
    c.hline(5, 22, 31, earth[0])           # lower shelf
    for i, jx in enumerate((6, 10, 14, 18)):   # preserve jars, alternating
        col_body = rose[1] if i % 2 == 0 else amber[1]
        col_lid = rose[2] if i % 2 == 0 else amber[2]
        c.rect(jx, 22, 2, 3, col_body)
        c.put(jx, 22, col_lid)
        c.put(jx + 1, 22, col_lid)
    for i, jx in enumerate((7, 12, 17)):        # bigger jars below
        col_body = amber[1] if i % 2 == 0 else rose[1]
        c.rect(jx, 27, 3, 4, col_body)
        c.hline(jx, jx + 2, 27, earth[0])       # lids
    c.put(21, 21, paper[2])                # glass glint, top right
    c.put(20, 22, paper[2])

    # doorway with a fly-strip curtain
    c.rect(36, 19, 15, 23, earth[1])
    c.hline(36, 50, 19, earth[3])
    c.hline(37, 49, 20, earth[2])
    c.rect(38, 21, 11, 21, void[1])
    curtain = (rose[1], paper[1], ship[2], rose[1], paper[1], ship[2], rose[1], paper[1], ship[2], rose[1], paper[1])
    for i, cx in enumerate(range(38, 49)):
        length = 12 + (i * 7) % 3          # uneven strip ends
        c.vline(cx, 21, 21 + length, curtain[i])

    # hanging goods between window and door: peppers and corn
    c.vline(28, 17, 20, earth[0])
    for px, py in ((27, 21), (28, 21), (29, 21), (27, 22), (28, 22), (29, 22), (28, 23), (28, 24)):
        c.put(px, py, rose[1])
    c.put(29, 21, rose[2])
    c.put(27, 22, rose[0])
    c.put(28, 25, rose[0])
    c.vline(32, 17, 19, earth[0])
    for px, py in ((31, 20), (32, 20), (33, 20), (31, 21), (32, 21), (33, 21), (32, 22), (32, 23)):
        c.put(px, py, amber[0])
    c.put(33, 20, amber[1])
    c.put(32, 24, earth[2])

    _foundation(c, 42, 56, 6, stone, rng)

    # produce crates out front (drawn last: they stand in front of everything)
    c.rect(2, 33, 12, 11, earth[1])
    c.hline(2, 13, 33, earth[3])
    c.vline(5, 34, 43, earth[0])
    c.vline(9, 34, 43, earth[0])
    c.hline(2, 13, 43, earth[0])
    for tx in (3, 6, 9, 12):               # tomatoes heaped over the rim
        c.rect(tx, 31, 2, 2, rose[1])
        c.put(tx + 1, 31, rose[2])
    c.put(5, 30, rose[1])
    c.put(10, 30, rose[2])
    c.rect(15, 36, 11, 8, earth[1])
    c.hline(15, 25, 36, earth[3])
    c.vline(18, 37, 43, earth[0])
    c.vline(22, 37, 43, earth[0])
    c.hline(15, 25, 43, earth[0])
    for tx in (16, 19, 22):                # quinces
        c.rect(tx, 34, 2, 2, amber[1])
        c.put(tx + 1, 34, amber[2])
    c.put(18, 33, amber[1])
    return c


# --- teahouse -------------------------------------------------------------


def _draw_teahouse(palette: Palette, rng: random.Random) -> PixelCanvas:
    c = PixelCanvas(72, 48, palette)
    stone = palette.ramp("stone")
    earth = palette.ramp("earth")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    paper = palette.ramp("paper")

    # shallow kiremit roof: ridge, ribbed pan tiles, eave shadow
    c.hline(0, 71, 0, rose[2])
    c.rect(0, 1, 72, 5, rose[1])
    for x in range(1, 72, 3):
        c.vline(x, 1, 5, rose[0])
        if x + 1 < 72:
            c.put(x + 1, 1, rose[2])        # sun on each tile crown
    c.hline(0, 71, 6, rose[0])              # eave shadow

    # upper wall + sign (ÇAY cadence, abstract marks)
    c.rect(1, 7, 70, 6, paper[1])
    c.hline(1, 70, 7, paper[0])
    c.rect(27, 7, 19, 6, earth[1])
    c.hline(27, 45, 7, earth[2])
    c.vline(27, 7, 12, earth[0])
    c.vline(45, 7, 12, earth[0])
    _glyph(c, 30, 8, _MARK_OPEN_BOX, amber[2])
    c.put(31, 12, amber[2])                 # cedilla-ish drip
    _glyph(c, 36, 8, _MARK_CHEVRON, amber[2])
    _glyph(c, 41, 8, _MARK_FORK, amber[2])

    # porch roof band
    c.hline(0, 71, 13, earth[3])
    c.rect(0, 14, 72, 2, earth[2])
    c.hline(0, 71, 16, earth[0])

    # recessed wall in porch shade
    c.rect(2, 17, 68, 23, paper[0])

    # window with the tea-glass pyramid, dim interior so the glasses glow
    c.rect(8, 19, 23, 17, earth[1])
    c.hline(8, 30, 19, earth[2])
    c.rect(10, 21, 19, 14, earth[0])
    c.hline(10, 28, 24, earth[2])           # lit shelf edges
    c.hline(10, 28, 29, earth[2])

    def glass(gx: int, gy: int) -> None:    # 2x3 tulip glass, lit rim
        c.put(gx, gy, amber[2])
        c.put(gx + 1, gy, amber[2])
        c.put(gx, gy + 1, amber[1])
        c.put(gx + 1, gy + 1, amber[1])
        c.put(gx, gy + 2, amber[1])
        c.put(gx + 1, gy + 2, amber[1])

    for gx in (15, 21):                     # 2 on top …
        glass(gx, 21)
    for gx in (13, 18, 23):                 # … 3 in the middle …
        glass(gx, 26)
    for gx in (11, 16, 21, 26):             # … 4 on the sill
        glass(gx, 31)
    c.hline(10, 28, 34, earth[2])           # sill

    # double doors with warm glass tops
    c.rect(40, 21, 17, 19, earth[1])
    c.hline(40, 56, 21, earth[2])
    c.vline(48, 22, 39, earth[0])
    c.rect(42, 23, 5, 5, amber[1])
    c.rect(50, 23, 5, 5, amber[1])
    c.hline(42, 46, 25, earth[0])
    c.hline(50, 54, 25, earth[0])
    c.hline(41, 47, 33, earth[0])           # panel lines
    c.hline(49, 55, 33, earth[0])
    c.put(46, 31, amber[2])                 # handles
    c.put(50, 31, amber[2])
    c.vline(40, 22, 39, earth[0])
    c.vline(56, 22, 39, earth[2])

    # hanging lamp between the doors and the right post
    c.vline(61, 17, 20, earth[0])
    c.rect(60, 21, 3, 3, amber[2])
    c.put(61, 22, amber[3])
    c.put(61, 24, amber[0])

    # porch posts, square timber with a lit face
    for px in (3, 33, 65):
        c.vline(px, 17, 39, earth[0])
        c.vline(px + 1, 17, 39, earth[1])
        c.vline(px + 2, 17, 39, earth[2])

    # porch floor planks
    c.hline(0, 71, 40, earth[3])
    c.rect(0, 41, 72, 2, earth[2])
    for sx in range(7, 72, 9):
        c.vline(sx, 41, 42, earth[1])
    c.hline(0, 71, 43, earth[0])

    _foundation(c, 44, 72, 4, stone, rng)
    return c


# --- house A: hip roof, shutters, autumn vine ------------------------------


def _draw_house_a(palette: Palette, rng: random.Random) -> PixelCanvas:
    c = PixelCanvas(48, 40, palette)
    stone = palette.ramp("stone")
    earth = palette.ramp("earth")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    ship = palette.ramp("ship")
    paper = palette.ramp("paper")

    # roof: full-width ribbed kiremit tiles
    c.hline(0, 47, 0, rose[2])
    c.rect(0, 1, 48, 6, rose[1])
    for x in range(1, 48, 3):
        c.vline(x, 1, 6, rose[0])
        if x + 1 < 48:
            c.put(x + 1, 1, rose[2])
    c.hline(0, 47, 7, rose[0])
    # wall, inset under the eaves
    c.rect(2, 8, 44, 26, stone[1])
    c.hline(2, 45, 8, stone[0])             # eave shadow on the wall
    _block_hints(c, 3, 10, 42, 22, stone, rng, n=6)
    _plaster_patch(c, 5, 9, 12, 6, paper, rng)
    c.vline(2, 8, 33, stone[0])
    c.vline(45, 8, 33, stone[2])

    def window(wx: int, lit: bool) -> None:
        c.rect(wx - 1, 12, 12, 2, paper[1])      # lintel
        c.hline(wx - 1, wx + 10, 12, paper[2])
        c.rect(wx, 14, 10, 10, earth[0])         # frame
        if lit:
            c.rect(wx + 1, 15, 8, 8, amber[1])
            c.rect(wx + 4, 17, 3, 3, amber[2])   # someone is home
        else:
            c.rect(wx + 1, 15, 8, 8, ship[0])
            c.put(wx + 7, 16, paper[2])          # sky reflection
            c.put(wx + 6, 17, paper[2])
        c.vline(wx + 4, 15, 22, earth[0])
        c.hline(wx + 1, wx + 8, 18, earth[0])
        c.rect(wx - 1, 24, 12, 1, paper[1])      # sill
        c.hline(wx - 1, wx + 10, 25, stone[0])   # sill shadow
        # open shutters
        for sx, lit_edge in ((wx - 4, False), (wx + 10, True)):
            c.rect(sx, 14, 3, 10, earth[2])
            c.hline(sx, sx + 2, 17, earth[1])
            c.hline(sx, sx + 2, 20, earth[1])
            c.vline(sx + (2 if lit_edge else 0), 14, 23, earth[3] if lit_edge else earth[0])

    window(7, lit=True)
    window(31, lit=False)

    # door
    c.rect(19, 21, 10, 1, stone[2])
    c.hline(19, 28, 21, stone[3])
    c.rect(20, 22, 8, 12, earth[1])
    c.vline(20, 22, 33, earth[0])
    c.vline(23, 23, 33, earth[0])
    c.vline(27, 22, 33, earth[2])
    c.put(26, 28, amber[2])
    c.rect(19, 34, 10, 1, paper[1])

    # autumn vine climbing the lit corner
    stem = ((44, 33), (44, 32), (43, 31), (43, 30), (44, 29), (44, 28), (43, 27),
            (43, 26), (42, 25), (43, 24), (43, 23), (44, 22), (44, 21), (43, 20),
            (43, 19), (42, 18), (43, 17), (43, 16), (43, 15), (42, 14), (43, 13),
            (43, 12), (43, 11), (44, 10))
    for sx, sy in stem:
        c.put(sx, sy, earth[0])
    for lx, ly in ((42, 30), (45, 27), (41, 24), (44, 20), (41, 17), (44, 13), (42, 10), (45, 9)):
        c.rect(lx, ly, 2, 2, amber[0])
        c.put(lx + 1, ly, amber[1])
    for lx, ly in ((45, 31), (42, 22), (45, 16), (40, 12)):
        c.put(lx, ly, amber[0])

    _foundation(c, 34, 48, 6, stone, rng)
    c.outline(palette.ramp("void"))
    return c


# --- house B: gable + chimney, plaster, laundry line -----------------------


def _draw_house_b(palette: Palette, rng: random.Random) -> PixelCanvas:
    c = PixelCanvas(48, 40, palette)
    stone = palette.ramp("stone")
    earth = palette.ramp("earth")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    ship = palette.ramp("ship")
    paper = palette.ramp("paper")
    void = palette.ramp("void")

    # asymmetric gable roofline: peak at x=30
    def roof_top(x: int) -> int:
        if x <= 30:
            return (30 - x + 2) // 3
        return ((x - 30) * 2) // 5

    for x in range(48):
        rt = roof_top(x)
        c.put(x, rt, rose[2])
        c.put(x, rt + 1, rose[1])
        c.put(x, rt + 2, rose[1])
        c.put(x, rt + 3, rose[0])
        # plaster wall fills from under the roof down
        for y in range(rt + 4, 34):
            c.put(x, y, paper[1])
    # chimney on the left slope
    c.hline(9, 14, 2, stone[2])
    c.hline(9, 14, 1, stone[3])
    c.rect(10, 3, 4, 4, stone[1])
    c.vline(13, 3, 6, stone[2])

    # attic vent under the peak
    c.rect(28, 6, 4, 4, stone[0])
    c.rect(29, 7, 2, 3, void[1])
    # stone quoins at the corners
    for qy in range(12, 34, 3):
        c.rect(0, qy, 3, 2, stone[2] if (qy // 3) % 2 == 0 else stone[1])
    for qy in range(10, 34, 3):
        c.rect(45, qy, 3, 2, stone[2] if (qy // 3) % 2 == 1 else stone[1])
    # plaster weathering
    for _ in range(6):
        c.put(rng.randrange(5, 43), rng.randrange(28, 33), paper[0])

    # window with shutters
    c.rect(7, 20, 10, 9, earth[0])
    c.rect(8, 21, 8, 7, ship[0])
    c.put(14, 22, paper[2])
    c.vline(11, 21, 27, earth[0])
    c.hline(8, 15, 24, earth[0])
    for sx, lit_edge in ((4, False), (17, True)):
        c.rect(sx, 20, 3, 9, earth[2])
        c.hline(sx, sx + 2, 23, earth[1])
        c.hline(sx, sx + 2, 26, earth[1])
        c.vline(sx + (2 if lit_edge else 0), 20, 28, earth[3] if lit_edge else earth[0])
    c.rect(6, 29, 12, 1, paper[1])

    # door
    c.rect(29, 21, 10, 1, stone[2])
    c.hline(29, 38, 21, stone[3])
    c.rect(30, 22, 8, 12, earth[1])
    c.vline(30, 22, 33, earth[0])
    c.vline(33, 23, 33, earth[0])
    c.vline(37, 22, 33, earth[2])
    c.put(36, 28, amber[2])

    # laundry line: rope sagging between the corners, four garments
    def rope_y(x: int) -> int:
        t = (x - 3) / 41.0
        return 12 + round(10 * t * (1 - t))

    for x in range(3, 45):
        c.put(x, rope_y(x), paper[0] if x % 2 == 0 else earth[0])
    # shirt (rose)
    ry = rope_y(9)
    c.put(8, ry, earth[0])
    c.rect(7, ry + 1, 4, 5, rose[1])
    c.hline(7, 10, ry + 1, rose[2])
    c.put(6, ry + 2, rose[1])
    c.put(11, ry + 2, rose[1])
    c.put(7, ry + 5, rose[0])
    # sheet (paper)
    ry = rope_y(19)
    c.put(18, ry, earth[0])
    c.put(22, ry, earth[0])
    c.rect(17, ry + 1, 7, 7, paper[2])
    c.vline(20, ry + 2, ry + 7, paper[1])
    c.hline(17, 23, ry + 7, paper[1])
    c.put(17, ry + 7, paper[0])
    # trousers (ship)
    ry = rope_y(29)
    c.put(29, ry, earth[0])
    c.rect(28, ry + 1, 4, 2, ship[2])
    c.vline(28, ry + 3, ry + 6, ship[2])
    c.vline(31, ry + 3, ry + 6, ship[2])
    c.put(28, ry + 6, ship[1])
    # small towel (amber)
    ry = rope_y(37)
    c.put(37, ry, earth[0])
    c.rect(36, ry + 1, 3, 4, amber[1])
    c.hline(36, 38, ry + 1, amber[2])
    c.put(36, ry + 4, amber[0])

    _foundation(c, 34, 48, 6, stone, rng)
    c.outline(void)
    return c


# --- minibus (dolmuş) ------------------------------------------------------


def _draw_minibus(palette: Palette, rng: random.Random) -> PixelCanvas:
    c = PixelCanvas(48, 26, palette)
    stone = palette.ramp("stone")
    earth = palette.ramp("earth")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    ship = palette.ramp("ship")
    paper = palette.ramp("paper")
    void = palette.ramp("void")

    # roof rack
    c.hline(8, 38, 0, earth[1])
    for rx in (8, 23, 38):
        c.put(rx, 1, earth[1])
    # roof, rounded ends, sunlit
    c.hline(4, 43, 2, paper[2])
    c.hline(3, 44, 3, paper[2])
    # cab/window band
    c.rect(2, 4, 44, 6, paper[1])
    c.put(2, 4, paper[0])                    # rounded rear shoulder
    for wx in (5, 12, 19, 26):               # side windows
        c.rect(wx, 5, 6, 5, ship[0])
        c.put(wx + 4, 5, ship[1])
        c.put(wx + 5, 5, ship[1])
    c.rect(33, 5, 6, 5, ship[0])             # door window
    c.put(37, 5, ship[1])
    # windshield, raked
    c.rect(41, 5, 5, 5, ship[0])
    c.put(41, 5, paper[1])
    c.put(45, 5, ship[1])
    c.put(44, 5, ship[1])
    c.rect(43, 8, 3, 2, paper[2])            # destination card on the dash
    # body
    c.rect(1, 10, 47, 7, paper[1])
    c.put(1, 10, paper[0])
    c.put(1, 16, paper[0])
    c.put(1, 11, rose[2])                    # tail light
    c.hline(44, 47, 10, paper[2])            # hood top catches the sun
    c.put(46, 11, amber[2])                  # headlight
    c.put(47, 11, amber[1])
    c.hline(45, 47, 13, paper[0])            # grille slit
    # rose beltline stripe
    c.hline(2, 43, 12, rose[1])
    c.hline(2, 43, 13, rose[1])
    c.put(43, 12, rose[2])
    c.put(42, 12, rose[2])
    # sliding door seams + handle
    c.vline(32, 10, 16, paper[0])
    c.vline(39, 10, 16, paper[0])
    c.put(33, 11, earth[0])
    # skirt, shaded, with round wheel arches
    c.rect(2, 17, 44, 2, paper[0])
    for ax in (5, 35):
        c.hline(ax + 1, ax + 7, 16, void[1])
        c.rect(ax, 17, 9, 2, void[1])
    # bumpers
    c.rect(43, 15, 5, 2, stone[2])
    c.hline(43, 47, 15, stone[3])
    c.rect(0, 15, 2, 2, stone[2])
    # wheels — rounded tires, small lit hub
    for wx in (5, 35):
        c.hline(wx + 2, wx + 6, 17, void[1])
        c.rect(wx + 1, 18, 7, 3, void[1])
        c.hline(wx + 2, wx + 6, 21, void[1])
        c.hline(wx + 3, wx + 5, 22, void[1])
        c.rect(wx + 3, 19, 2, 2, stone[2])
        c.put(wx + 4, 19, stone[3])
    # mirror
    c.put(46, 6, paper[0])
    c.put(47, 5, paper[2])

    c.outline(void)
    # ground shadow, painted after the outline so it stays soft
    c.hline(3, 44, 23, void[1])
    c.hline(5, 42, 24, void[1])
    return c


# --- dolmuş stop sign -------------------------------------------------------


def _draw_stop_sign(palette: Palette, rng: random.Random) -> PixelCanvas:
    c = PixelCanvas(10, 24, palette)
    stone = palette.ramp("stone")
    ship = palette.ramp("ship")
    paper = palette.ramp("paper")
    void = palette.ramp("void")

    # board
    c.rect(1, 1, 8, 8, ship[1])
    c.hline(1, 8, 1, ship[2])
    c.hline(1, 8, 8, ship[0])
    c.vline(1, 1, 8, ship[0])
    c.vline(8, 2, 7, ship[2])
    # the D
    for px, py in ((3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 2), (5, 3), (5, 4), (5, 5), (4, 6)):
        c.put(px, py, paper[2])
    # pole
    c.vline(4, 9, 20, stone[1])
    c.vline(5, 9, 20, stone[2])
    c.put(5, 9, stone[3])
    # concrete foot
    c.rect(2, 21, 6, 3, stone[1])
    c.hline(2, 7, 21, stone[2])
    c.hline(2, 7, 23, stone[0])
    c.outline(void)
    return c


# --- poplars ----------------------------------------------------------------

# hand-shaped columnar envelopes: y -> (x0, x1)
_POPLAR_BIG = {
    1: (7, 8), 2: (7, 8), 3: (6, 9), 4: (6, 9), 5: (5, 10), 6: (5, 10),
    7: (5, 10), 8: (4, 11), 9: (4, 11), 10: (4, 11), 11: (3, 12), 12: (3, 12),
    13: (3, 12), 14: (3, 12), 15: (2, 13), 16: (3, 12), 17: (2, 13), 18: (2, 13),
    19: (2, 13), 20: (2, 13), 21: (3, 13), 22: (2, 13), 23: (2, 12), 24: (2, 13),
    25: (3, 13), 26: (3, 12), 27: (3, 12), 28: (4, 12), 29: (4, 11), 30: (4, 11),
    31: (5, 11), 32: (5, 10), 33: (5, 10), 34: (6, 10), 35: (6, 9), 36: (6, 9),
    37: (7, 9), 38: (7, 8),
}
_POPLAR_SMALL = {
    1: (5, 6), 2: (5, 6), 3: (4, 7), 4: (4, 7), 5: (3, 8), 6: (3, 8),
    7: (3, 8), 8: (2, 9), 9: (2, 9), 10: (2, 9), 11: (1, 10), 12: (2, 10),
    13: (1, 10), 14: (1, 10), 15: (2, 9), 16: (1, 10), 17: (2, 9), 18: (2, 9),
    19: (3, 9), 20: (3, 8), 21: (3, 8), 22: (4, 7), 23: (4, 7), 24: (5, 6),
    25: (5, 6),
}


def _draw_poplar(palette: Palette, rng: random.Random, w: int, h: int,
                 envelope: dict, trunk_x: int, trunk_top: int) -> PixelCanvas:
    c = PixelCanvas(w, h, palette)
    earth = palette.ramp("earth")
    amber = palette.ramp("amber")

    rows = sorted(envelope.items())
    lo_y, hi_y = rows[0][0], rows[-1][0]
    span = hi_y - lo_y
    # base canopy mass with a jittered, ragged edge
    for y, (x0, x1) in rows:
        jl = rng.choice((0, 0, 0, -1, 1)) if x1 - x0 > 3 else 0
        jr = rng.choice((0, 0, 0, -1, 1)) if x1 - x0 > 3 else 0
        c.hline(max(0, x0 + jl), min(w - 1, x1 + jr), y, amber[0])
    # shade the left flank (light comes from upper right)
    for y, (x0, x1) in rows:
        width = x1 - x0
        if width >= 3:
            c.put(x0, y, earth[3])
        if width >= 6:
            c.put(x0 + 1, y, earth[3])
        if width >= 8 and y > lo_y + span // 3:
            c.put(x0, y, earth[2])
    # leaf strokes follow the tree's upward flow: short vertical dashes.
    # shadow strokes biased low/left …
    for _ in range(9 + span // 4):
        y = rng.randrange(lo_y + span // 4, hi_y - 1)
        x0, x1 = envelope[y]
        if x1 - x0 < 4:
            continue
        cx = rng.randrange(x0 + 1, x0 + max(2, (x1 - x0) * 2 // 3))
        c.put(cx, y, earth[3])
        c.put(cx, y + 1, earth[3])
        if rng.random() < 0.4:
            c.put(cx, y + 2, earth[2])
    # … sunlit strokes biased high/right
    for _ in range(8 + span // 4):
        y = rng.randrange(lo_y + 1, lo_y + span * 2 // 3)
        x0, x1 = envelope[y]
        if x1 - x0 < 3:
            continue
        cx = rng.randrange(x0 + max(1, (x1 - x0) // 3), x1)
        c.put(cx, y, amber[1])
        if rng.random() < 0.6:
            c.put(cx, y - 1, amber[1])
    # rim glints on the top-right edge
    for _ in range(4):
        y = rng.randrange(lo_y + 1, lo_y + span // 2)
        c.put(envelope[y][1], y, amber[2])
    # under-tuft shadows where the canopy narrows toward the bottom
    for y, (x0, x1) in rows:
        if y > lo_y + span * 2 // 3 and y + 1 in envelope and envelope[y + 1][1] < x1:
            c.put(x1, y, earth[2])
    # trunk with flared roots
    for ty in range(trunk_top, h):
        c.put(trunk_x, ty, earth[0])
        c.put(trunk_x + 1, ty, earth[1])
    c.put(trunk_x + 1, trunk_top + 1, earth[2])   # bark catching light
    c.put(trunk_x - 1, h - 1, earth[0])
    c.put(trunk_x + 2, h - 1, earth[1])
    c.put(trunk_x + 2, h - 2, earth[1])
    c.outline(earth)
    return c


def _draw_poplar_big(palette: Palette, rng: random.Random) -> PixelCanvas:
    return _draw_poplar(palette, rng, 16, 48, _POPLAR_BIG, 7, 38)


def _draw_poplar_small(palette: Palette, rng: random.Random) -> PixelCanvas:
    return _draw_poplar(palette, rng, 12, 32, _POPLAR_SMALL, 5, 25)


# --- teahouse furniture ------------------------------------------------------


def _profile_chair(c: PixelCanvas, x: int, earth: Ramp, paper: Ramp, *, facing_right: bool) -> None:
    """Side-view coffeehouse chair anchored at ground y=16, 6px wide."""
    if facing_right:
        post, seat0, leg = x, x + 2, x + 4
    else:
        post, seat0, leg = x + 4, x, x
    c.vline(post, 3, 16, earth[1])
    c.vline(post + 1, 3, 16, earth[2])
    c.put(post, 3, earth[3])
    c.put(post + 1, 3, earth[3])
    c.hline(seat0, seat0 + 3, 10, paper[1])
    c.hline(seat0, seat0 + 3, 11, earth[1])
    c.vline(leg, 12, 16, earth[1])
    c.vline(leg + 1, 12, 16, earth[2])


def _draw_tea_table(palette: Palette, rng: random.Random) -> PixelCanvas:
    c = PixelCanvas(24, 18, palette)
    earth = palette.ramp("earth")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    paper = palette.ramp("paper")

    _profile_chair(c, 0, earth, paper, facing_right=True)
    _profile_chair(c, 18, earth, paper, facing_right=False)

    # table
    c.hline(6, 17, 7, earth[3])
    c.rect(6, 8, 12, 2, earth[2])
    c.hline(6, 17, 9, earth[0])
    for lx in (7, 15):
        c.vline(lx, 10, 16, earth[1])
        c.vline(lx + 1, 10, 16, earth[2])

    # backgammon board lying flat, set off-center; pale field, dark hinge,
    # two checkers mid-game placed asymmetrically (no face-symmetry)
    c.rect(8, 5, 6, 2, paper[1])
    c.vline(10, 5, 6, earth[0])
    c.put(9, 6, rose[1])
    c.put(12, 5, rose[1])
    # both teas served on the window side of the board
    c.put(15, 5, amber[2])
    c.put(15, 6, amber[1])
    c.put(17, 6, amber[1])

    c.outline(earth)
    return c


def _draw_extra_chair(palette: Palette, rng: random.Random) -> PixelCanvas:
    """The anomaly. Drawn perfectly, unremarkably ordinary — that's the point."""
    c = PixelCanvas(10, 14, palette)
    earth = palette.ramp("earth")
    paper = palette.ramp("paper")

    # crest rail + back posts
    c.hline(1, 8, 0, earth[2])
    c.put(7, 0, earth[3])
    c.put(8, 0, earth[3])
    c.hline(1, 8, 1, earth[1])
    c.vline(1, 2, 4, earth[1])
    c.vline(2, 2, 4, earth[1])
    c.vline(7, 2, 4, earth[1])
    c.vline(8, 2, 4, earth[2])
    c.hline(2, 7, 3, earth[1])                # mid slat
    # woven rush seat
    c.hline(0, 9, 5, paper[1])
    c.put(8, 5, paper[2])
    c.put(9, 5, paper[2])
    for sx in range(0, 10):
        c.put(sx, 6, paper[1] if sx % 4 < 2 else paper[0])
    c.hline(0, 9, 7, earth[1])
    # legs + stretcher
    c.vline(1, 8, 12, earth[1])
    c.vline(2, 8, 12, earth[1])
    c.vline(7, 8, 12, earth[1])
    c.vline(8, 8, 12, earth[2])
    c.hline(3, 6, 10, earth[1])
    c.put(1, 12, earth[0])
    c.put(8, 12, earth[0])
    c.outline(earth)
    return c


# --- çeşme -------------------------------------------------------------------


def _draw_cesme(palette: Palette, rng: random.Random) -> PixelCanvas:
    c = PixelCanvas(20, 24, palette)
    stone = palette.ramp("stone")
    amber = palette.ramp("amber")
    ship = palette.ramp("ship")
    paper = palette.ramp("paper")
    void = palette.ramp("void")

    # back slab with a lit cap
    c.hline(1, 18, 0, stone[3])
    c.hline(1, 18, 1, stone[2])
    c.rect(2, 2, 16, 12, stone[1])
    c.vline(2, 2, 13, stone[0])
    c.vline(17, 2, 13, stone[2])
    c.hline(4, 9, 12, stone[0])               # a masonry joint
    c.vline(14, 3, 5, stone[0])
    # pointed niche
    c.hline(9, 10, 3, stone[0])
    c.hline(8, 11, 4, stone[0])
    c.hline(7, 12, 5, stone[0])
    c.rect(6, 6, 8, 6, stone[0])
    c.rect(8, 8, 4, 4, void[1])               # deepest shade
    c.put(12, 4, stone[2])                    # rim catching light
    c.vline(14, 6, 10, stone[2])
    # brass tap: stub from the niche wall, spout turned down
    c.put(8, 8, amber[0])
    c.put(9, 8, amber[1])
    c.put(10, 8, amber[0])
    c.put(10, 9, amber[0])
    # falling water, pale teal, splash where it meets the basin
    c.vline(10, 10, 14, ship[3])
    # basin: rim, water, carved front
    c.hline(0, 19, 14, stone[2])
    c.put(18, 14, stone[3])
    c.hline(1, 18, 15, ship[2])               # water surface
    c.put(9, 15, ship[3])
    c.put(10, 15, paper[2])                   # splash glint
    c.put(11, 15, ship[3])
    c.put(15, 15, ship[3])
    c.hline(0, 19, 16, stone[3])              # lit front lip
    c.rect(0, 17, 20, 6, stone[1])
    c.rect(3, 18, 14, 1, stone[0])            # carved recess panel
    c.hline(4, 15, 20, stone[2])              # panel's lit lower edge
    c.vline(0, 17, 22, stone[0])
    c.vline(19, 17, 22, stone[2])
    c.hline(0, 19, 23, stone[0])
    c.outline(stone)
    return c
