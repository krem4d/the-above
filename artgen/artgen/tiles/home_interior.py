"""tiles.home_interior — Deniz's stone-house interior (M4, Act 1 Day 1).

One manifest, two sheets:
  tiles/home_sheet.png — 5 tiles, 16x16 art baked 2x -> 32x32 cells, atlas
      order (append-only): floor_wood, floor_wood_var, rug, wall, window_day.
  props/home_props.png — 10 furniture/dressing props, tightly packed; the
      sidecar's props dict is emitted in the append-only contract order.

Mood: modest, warm, decades lived-in; golden autumn morning. Global light
from above, slightly right — top faces lightest, right edges lit, left edges
and undersides shaded. Ramps: earth (wood), paper (whitewash/linen/lace),
rose (kilim + quilt), stone (tin/iron/B&W photograph), amber (sky, tea,
bread, the radio's dial lamp), ship (gas flame under the kettle), void
(deep recesses and mass-separation lines only). No signal ramp here.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from ..canvas import PixelCanvas
from ..palette import Palette, Ramp

ART = 16

TILE_ORDER = ("floor_wood", "floor_wood_var", "rug", "wall", "window_day")
SOLID_TILES = ("wall", "window_day")

# Sidecar key order — the append-only atlas contract for props.
PROP_ORDER = (
    "bed", "kitchen_counter", "stove_kettle", "cat_bowl", "photo_wall",
    "radio_table", "wardrobe", "table_home", "chair_home", "door_home",
)
# name -> (sheet x, sheet y, w, h, solid rect rel. to region) — all in ART px.
PROP_LAYOUT = {
    "bed": (0, 0, 24, 32, (0, 11, 24, 21)),
    "kitchen_counter": (0, 32, 32, 16, (0, 0, 32, 16)),
    "stove_kettle": (64, 0, 16, 20, (1, 11, 14, 9)),
    "cat_bowl": (48, 24, 8, 6, None),
    "photo_wall": (32, 32, 24, 16, None),
    "radio_table": (80, 0, 16, 20, (1, 9, 14, 11)),
    "wardrobe": (24, 0, 24, 32, (0, 16, 24, 16)),
    "table_home": (56, 32, 24, 16, (1, 0, 22, 14)),
    "chair_home": (80, 32, 10, 14, (1, 7, 8, 7)),
    "door_home": (48, 0, 16, 24, None),
}
PROP_SHEET_W = 96
PROP_SHEET_H = 48


def generate(manifest: dict, palette: Palette, out_root: Path) -> None:
    art_cell = int(manifest.get("art_cell", ART))
    if art_cell != ART:
        raise ValueError(f"tiles.home_interior draws {ART}px art cells, got {art_cell}")
    scale = int(manifest.get("scale", 2))
    rng = random.Random(manifest["seed"])
    _emit_tile_sheet(manifest, palette, Path(out_root), rng, scale)
    _emit_prop_sheet(manifest, palette, Path(out_root), rng, scale)


# ---------------------------------------------------------------------------
# tile sheet
# ---------------------------------------------------------------------------

def _emit_tile_sheet(
    manifest: dict, palette: Palette, out_root: Path, rng: random.Random, scale: int
) -> None:
    earth = palette.ramp("earth")
    paper = palette.ramp("paper")
    rose = palette.ramp("rose")
    stone = palette.ramp("stone")
    amber = palette.ramp("amber")
    void = palette.ramp("void")

    drawers = {
        "floor_wood": lambda c: _draw_floor_wood(c, earth, rng),
        "floor_wood_var": lambda c: _draw_floor_wood_var(c, earth, rng),
        "rug": lambda c: _draw_rug(c, rose, earth, paper, rng),
        "wall": lambda c: _draw_wall(c, paper, stone, void, rng),
        "window_day": lambda c: _draw_window_day(c, paper, stone, void, earth, amber, rng),
    }
    sheet = PixelCanvas(ART * len(TILE_ORDER), ART, palette)
    for col, name in enumerate(TILE_ORDER):
        tile = PixelCanvas(ART, ART, palette)
        drawers[name](tile)
        sheet.paste(tile, col * ART, 0)

    out_png = out_root / manifest.get("out_tiles", "tiles/home_sheet.png")
    sheet.save(out_png, scale=scale)
    sidecar = {
        "grid": {"cell": ART * scale, "cols": len(TILE_ORDER), "rows": 1},
        "tiles": list(TILE_ORDER),
        "solid": list(SOLID_TILES),
    }
    out_png.with_suffix(".json").write_text(
        json.dumps(sidecar, indent=2) + "\n", encoding="utf-8"
    )


def _draw_floor_wood(
    c: PixelCanvas,
    earth: Ramp,
    rng: random.Random,
    joints: tuple[int, int] = (5, 11),
    knot: tuple[int, int] = (9, 3),
    grain: tuple = None,
) -> None:
    """Wide old boards, two per tile — a mountain house, not parquet.

    Wood, not brick: long horizontal grain streaks inside each board carry
    the read; seams stay thin and the butt joints stay unlit."""
    if grain is None:
        grain = _FLOOR_GRAIN_A
    c.rect(0, 0, ART, ART, earth[2])
    c.hline(0, ART - 1, 7, earth[1])                       # seams between boards
    c.hline(0, ART - 1, 15, earth[1])
    c.vline(joints[0], 0, 6, earth[1])                     # staggered butt joints
    c.vline(joints[1], 8, 14, earth[1])
    for x0, x1, y, warm in grain:
        c.hline(x0, x1, y, earth[3] if warm else earth[1])
    # one honest knot with its shadowed tail
    kx, ky = knot
    c.put(kx, ky, earth[0])
    c.put(kx + 1, ky, earth[1])
    # a single stray rng tick so no two floors feel machine-copied
    c.put(rng.randrange(1, ART - 1), rng.choice((2, 5, 9, 13)), earth[1])


_FLOOR_GRAIN_A = (
    # (x0, x1, y, warm) — hand-laid grain, three streaks per board, no more:
    # the floor must stay calm so the furniture reads over it
    (7, 10, 2, False), (0, 2, 5, False), (12, 13, 4, True),
    (3, 6, 10, False), (11, 14, 12, False), (5, 6, 13, True),
)
_FLOOR_GRAIN_B = (
    (2, 5, 1, False), (12, 15, 4, False), (8, 9, 3, True),
    (6, 9, 11, False), (0, 2, 13, False), (13, 14, 10, True),
)


def _draw_floor_wood_var(c: PixelCanvas, earth: Ramp, rng: random.Random) -> None:
    # different stagger + grain so the two tiles interleave without repeating
    _draw_floor_wood(
        c, earth, rng, joints=(10, 3), knot=(4, 11), grain=_FLOOR_GRAIN_B
    )
    # a short worn-pale scuff where feet pass
    px = rng.randrange(2, 8)
    c.hline(px, px + 1, 6, earth[3])
    # a pair of old nail heads flanking the board-end joint
    c.put(8, 1, earth[0])
    c.put(12, 1, earth[0])


def _draw_rug(
    c: PixelCanvas, rose: Ramp, earth: Ramp, paper: Ramp, rng: random.Random
) -> None:
    """Kilim runner band pattern; period-8 motifs so the tile self-tiles."""
    c.rect(0, 0, ART, ART, rose[1])
    # guard bands (dark cords between woven bands)
    for y in (0, 4, 12):
        c.hline(0, ART - 1, y, earth[0])
    # outer rose bands with bead rows
    for y in (1, 2, 3, 13, 14, 15):
        c.hline(0, ART - 1, y, rose[0])
    for x in range(2, ART, 4):
        c.put(x, 2, paper[2])
    for x in range(0, ART, 4):
        c.put(x, 14, paper[2])
    # main field y5..11: two kilim diamonds on an 8px period
    for cx in (4, 12):
        cy = 8
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                d = abs(dx) + abs(dy)
                if d == 2:
                    c.put(cx + dx, cy + dy, paper[2])
                elif d == 1:
                    c.put(cx + dx, cy + dy, rose[2])
        c.put(cx, cy, earth[0])
    # small warm dots between the diamonds (wrap-consistent: period 8)
    c.put(0, 8, earth[3])
    c.put(8, 8, earth[3])
    # weave slubs — darker threads, kept clear of the diamonds so they never
    # cluster into accidental shapes beside the motifs
    for _ in range(4):
        x = rng.choice((1, 2, 3, 13, 14, 15))
        y = rng.choice((5, 6, 10, 11))
        c.put(x, y, rose[0])


def _draw_wall(
    c: PixelCanvas, paper: Ramp, stone: Ramp, void: Ramp, rng: random.Random
) -> None:
    """Whitewashed plaster, lit top cap, cool stone shadow pooling at the base."""
    c.rect(0, 0, ART, ART, paper[1])
    c.hline(0, ART - 1, 0, void[0])                       # ceiling line
    c.rect(0, 1, ART, 3, paper[2])                        # lit cap
    # the cap's lower edge crumbles a little — no mechanical dither row
    for nx in (3, 9, 14):
        c.put(nx, 3, paper[1])
    c.put(6, 4, paper[2])
    # plaster: only single-pixel marks — anything with a shape would repeat
    # every 16px and read as a mechanical scratch pattern across the room
    c.put(2, 6, paper[0])
    c.put(13, 9, paper[0])
    c.put(6, 10, paper[0])
    c.put(11, 7, paper[0])
    c.put(10, 5, paper[2])                                 # single bright fleck
    # base shadow where the wall meets the floor — ragged, not banded
    c.hline(0, 2, 12, paper[0])
    c.hline(6, 8, 12, paper[0])
    c.hline(12, 15, 12, paper[0])
    c.hline(0, ART - 1, 13, paper[0])
    c.hline(0, ART - 1, 14, stone[1])
    c.hline(0, ART - 1, 15, stone[0])


def _draw_window_day(
    c: PixelCanvas,
    paper: Ramp,
    stone: Ramp,
    void: Ramp,
    earth: Ramp,
    amber: Ramp,
    rng: random.Random,
) -> None:
    """Wall tile pierced by a wooden window full of golden-hour sky."""
    _draw_wall(c, paper, stone, void, rng)
    # wooden frame: lit lintel, shaded left jamb, lit right jamb
    c.hline(2, 13, 2, earth[2])
    c.vline(2, 3, 11, earth[1])
    c.vline(13, 3, 11, earth[2])
    c.hline(3, 12, 3, earth[0])                            # frame depth shadow
    # sky x4..11, y4..11 — gradient brightens toward the low sun
    c.hline(4, 11, 4, amber[0])
    c.dither_rect(4, 5, 8, 1, amber, 0, 1, 0.4)
    c.hline(4, 11, 6, amber[1])
    c.dither_rect(4, 7, 8, 1, amber, 1, 2, 0.5)
    c.hline(4, 11, 8, amber[2])
    c.dither_rect(4, 9, 8, 1, amber, 2, 3, 0.6)
    c.hline(4, 11, 10, amber[3])
    c.hline(4, 11, 11, amber[3])
    # inner frame columns flanking the sky
    c.vline(3, 4, 11, earth[0])
    c.vline(12, 4, 11, earth[1])
    # low ridge line, violet against the glow; the valley stays open to the sun
    c.hline(4, 6, 11, stone[1])
    c.put(5, 10, stone[1])
    c.hline(10, 11, 11, stone[1])
    c.put(11, 10, stone[1])
    # low sun sinking toward the valley gap
    c.rect(9, 8, 2, 2, amber[3])
    # mullions
    c.vline(8, 4, 11, earth[1])
    c.hline(4, 11, 7, earth[1])
    # sill: lit top, shadow beneath
    c.hline(1, 14, 12, earth[3])
    c.hline(1, 14, 13, earth[1])
    c.hline(2, 13, 14, earth[0])


# ---------------------------------------------------------------------------
# prop sheet
# ---------------------------------------------------------------------------

def _emit_prop_sheet(
    manifest: dict, palette: Palette, out_root: Path, rng: random.Random, scale: int
) -> None:
    earth = palette.ramp("earth")
    paper = palette.ramp("paper")
    rose = palette.ramp("rose")
    stone = palette.ramp("stone")
    amber = palette.ramp("amber")
    ship = palette.ramp("ship")
    void = palette.ramp("void")

    drawers = {
        "bed": lambda c: _draw_bed(c, earth, rose, paper, rng),
        "kitchen_counter": lambda c: _draw_kitchen_counter(c, earth, paper, amber, void, rng),
        "stove_kettle": lambda c: _draw_stove_kettle(c, stone, paper, ship, earth, void),
        "cat_bowl": lambda c: _draw_cat_bowl(c, stone, paper, earth),
        "photo_wall": lambda c: _draw_photo_wall(c, earth, amber, stone),
        "radio_table": lambda c: _draw_radio_table(c, earth, paper, amber, stone),
        "wardrobe": lambda c: _draw_wardrobe(c, earth, rng),
        "table_home": lambda c: _draw_table_home(c, earth, paper, amber),
        "chair_home": lambda c: _draw_chair_home(c, earth),
        "door_home": lambda c: _draw_door_home(c, earth, stone, paper, void),
    }
    sheet = PixelCanvas(PROP_SHEET_W, PROP_SHEET_H, palette)
    for name in PROP_ORDER:
        x, y, w, h, _solid = PROP_LAYOUT[name]
        prop = PixelCanvas(w, h, palette)
        drawers[name](prop)
        sheet.paste(prop, x, y)

    out_png = out_root / manifest.get("out_props", "props/home_props.png")
    sheet.save(out_png, scale=scale)
    props: dict[str, dict] = {}
    for name in PROP_ORDER:
        x, y, w, h, solid = PROP_LAYOUT[name]
        props[name] = {
            "region": [x * scale, y * scale, w * scale, h * scale],
            "solid": [v * scale for v in solid] if solid else None,
        }
    sidecar = {"scale": scale, "props": props}
    out_png.with_suffix(".json").write_text(
        json.dumps(sidecar, indent=2) + "\n", encoding="utf-8"
    )


def _draw_bed(
    c: PixelCanvas, earth: Ramp, rose: Ramp, paper: Ramp, rng: random.Random
) -> None:
    """24x32. Headboard, sheet-fold, kilim-striped quilt, footboard, shadow."""
    # headboard posts with lit caps
    c.rect(0, 1, 2, 7, earth[1])
    c.rect(22, 1, 2, 7, earth[1])
    c.vline(0, 1, 7, earth[0])
    c.vline(23, 1, 7, earth[2])
    c.hline(0, 1, 0, earth[2])
    c.hline(22, 23, 0, earth[2])
    # headboard panel
    c.rect(2, 1, 20, 5, earth[1])
    c.hline(2, 21, 1, earth[2])                            # lit top rail
    c.hline(2, 21, 5, earth[0])                            # shadow under rail
    for gx in (6, 12, 17):
        c.put(gx, 3, earth[0])                              # panel grain
    # mattress sheet band behind the pillow (a step darker so the pillow pops)
    c.rect(2, 6, 20, 5, paper[1])
    c.vline(2, 6, 10, paper[0])
    c.vline(21, 6, 10, paper[2])
    # pillow: sits left-of-center, plump, clearly edged against the sheet
    c.rect(4, 6, 11, 4, paper[2])
    c.hline(4, 14, 9, paper[0])                            # undercurve shadow
    c.vline(4, 7, 9, paper[1])                             # shaded left cheek
    c.vline(14, 6, 8, paper[1])                            # right edge turns away
    c.put(9, 6, paper[1])                                  # head dent
    c.put(10, 6, paper[1])
    # fold-over sheet: lit roll, hard shadow under it
    c.hline(2, 21, 11, paper[2])
    c.hline(2, 21, 12, paper[0])
    # quilt: one wide calm field, a single kilim motif band, stripes at the foot
    c.rect(2, 13, 20, 15, rose[1])
    c.hline(2, 21, 18, rose[0])                            # motif band guards
    for dx in (5, 9, 13, 17):
        c.put(dx, 19, paper[2])                            # bead motifs
        c.put(dx, 20, rose[2])                             # each casts a warm echo
    c.hline(2, 21, 21, rose[0])
    c.hline(2, 21, 24, rose[2])                            # foot stripe pair
    c.hline(2, 21, 25, rose[0])
    c.vline(2, 13, 27, rose[0])                            # left drape shaded
    c.vline(21, 13, 27, rose[2])                           # right drape lit
    c.hline(3, 20, 27, rose[0])                            # quilt tucks at the foot
    # soft creases where the sleeper turned
    c.put(16, 14, rose[0])
    c.put(17, 15, rose[0])
    c.put(7, 16, rose[2])
    c.put(8, 16, rose[2])
    # footboard with posts
    c.rect(2, 28, 20, 2, earth[1])
    c.hline(2, 21, 28, earth[2])
    c.rect(0, 27, 2, 4, earth[1])
    c.rect(22, 27, 2, 4, earth[1])
    c.hline(0, 1, 27, earth[2])
    c.hline(22, 23, 27, earth[2])
    c.vline(0, 27, 30, earth[0])
    c.vline(23, 27, 30, earth[2])
    # shadow under the frame, spilling left (light is upper-right)
    c.hline(2, 21, 30, earth[0])
    c.hline(1, 19, 31, earth[0])


def _draw_kitchen_counter(
    c: PixelCanvas, earth: Ramp, paper: Ramp, amber: Ramp, void: Ramp, rng: random.Random
) -> None:
    """32x16. Wooden counter: worktop with breadboard + two tea glasses,
    cupboard doors, a drawer, an open shelf with a bowl."""
    # worktop
    c.hline(0, 31, 0, earth[2])                            # back rim
    c.rect(0, 1, 32, 2, earth[3])                          # lit top
    c.hline(0, 31, 3, earth[2])                            # rounded front lip
    c.hline(0, 31, 4, earth[0])                            # under-lip shadow
    c.vline(10, 1, 2, earth[2])                            # worktop board seams
    c.vline(21, 1, 2, earth[2])
    # breadboard with a loaf
    c.rect(4, 0, 8, 3, paper[1])
    c.hline(4, 11, 2, paper[0])
    c.rect(6, 0, 4, 2, amber[0])
    c.hline(6, 9, 0, amber[1])
    # two tulip tea glasses on saucers
    for gx in (23, 28):
        c.rect(gx, 0, 2, 1, amber[1])
        c.rect(gx, 1, 2, 1, amber[0])
        c.hline(gx - 1, gx + 2, 2, paper[2])
    # cupboard front
    c.rect(0, 5, 32, 9, earth[1])
    c.vline(0, 5, 13, earth[0])
    c.vline(31, 5, 13, earth[2])
    for dx0 in (2, 18):                                    # two door insets
        c.rect(dx0, 6, 12, 7, earth[1])
        c.hline(dx0, dx0 + 11, 6, earth[0])
        c.hline(dx0, dx0 + 11, 12, earth[0])
        c.vline(dx0, 6, 12, earth[0])
        c.vline(dx0 + 11, 6, 12, earth[0])
        c.hline(dx0 + 1, dx0 + 10, 11, earth[2])           # bevel catches light
    c.put(12, 9, earth[3])                                 # knobs
    c.put(19, 9, earth[3])
    # middle: small drawer over an open shelf with a bowl in shadow
    c.rect(14, 6, 4, 3, earth[1])
    c.hline(14, 17, 6, earth[0])
    c.hline(14, 17, 8, earth[0])
    c.vline(14, 6, 8, earth[0])
    c.vline(17, 6, 8, earth[0])
    c.put(15, 7, earth[3])
    c.rect(14, 9, 4, 4, void[1])
    c.hline(15, 16, 11, paper[1])                          # bowl rim in the dark
    # base rail + kick
    c.hline(0, 31, 13, earth[0])
    c.hline(0, 31, 14, earth[0])
    c.hline(1, 30, 15, earth[0])


def _draw_stove_kettle(
    c: PixelCanvas, stone: Ramp, paper: Ramp, ship: Ramp, earth: Ramp, void: Ramp
) -> None:
    """16x20. Small enamel gas stove; the çaydanlık (double kettle) sits on the
    flame — Day 1 story beat, so it reads first: bright steel on white."""
    # teapot (upper pot) with lid knob
    c.put(8, 0, stone[3])
    c.hline(6, 9, 1, stone[3])
    c.rect(5, 2, 6, 3, stone[2])
    c.vline(5, 2, 4, stone[1])
    c.hline(8, 9, 2, stone[3])
    # lower kettle: lit rim, fat body, spout up-right, ear handle left
    c.hline(4, 11, 5, stone[3])
    c.rect(4, 6, 8, 4, stone[2])
    c.vline(4, 6, 9, stone[1])
    c.vline(11, 6, 9, stone[3])
    c.hline(4, 11, 9, stone[1])
    c.put(12, 6, stone[2])
    c.put(12, 5, stone[2])
    c.put(13, 4, stone[3])
    c.vline(3, 6, 7, stone[1])
    # gas flame licking up between grate ends
    c.put(3, 10, stone[0])
    c.put(12, 10, stone[0])
    c.put(5, 10, ship[2])
    c.put(7, 10, ship[3])
    c.put(8, 10, ship[3])
    c.put(10, 10, ship[2])
    # enamel stovetop
    c.hline(1, 14, 11, paper[2])
    c.put(3, 11, stone[1])                                 # burner grate pokes out
    c.put(12, 11, stone[1])
    c.hline(1, 14, 12, paper[1])
    # front panel: two knobs on the left, small oven window on the right
    c.rect(1, 13, 14, 5, paper[1])
    c.vline(1, 13, 17, paper[0])
    c.vline(14, 13, 17, paper[2])
    c.put(3, 14, stone[1])
    c.put(5, 14, stone[1])
    c.hline(9, 12, 15, stone[1])                           # window frame top
    c.rect(9, 16, 4, 2, void[1])
    c.put(12, 16, stone[1])                                # glass glint
    # base rail, feet, shadow
    c.hline(1, 14, 18, paper[0])
    c.hline(2, 3, 19, stone[0])
    c.hline(12, 13, 19, stone[0])
    c.hline(4, 11, 19, earth[0])


def _draw_cat_bowl(c: PixelCanvas, stone: Ramp, paper: Ramp, earth: Ramp) -> None:
    """8x6. Shallow tin bowl with milk — wide and squat, not a vase."""
    c.hline(1, 6, 0, stone[3])                             # lit rim
    c.put(0, 1, stone[2])
    c.put(1, 1, stone[1])
    c.hline(2, 5, 1, paper[2])                             # milk
    c.put(6, 1, stone[1])
    c.put(7, 1, stone[3])                                  # rim glint, light side
    c.hline(0, 7, 2, stone[2])                             # body
    c.put(0, 2, stone[1])
    c.hline(1, 6, 3, stone[1])                             # curving under
    c.hline(2, 5, 4, stone[0])                             # base ring
    c.hline(1, 6, 5, earth[0])                             # floor shadow


def _draw_photo_wall(c: PixelCanvas, earth: Ramp, amber: Ramp, stone: Ramp) -> None:
    """24x16. Three hand-hung frames on plaster: a sepia couple, İbrahim before
    the dish (B&W, 1980s, center, larger), an amber landscape of the valley."""
    # nails
    c.put(4, 5, earth[0])
    c.put(12, 2, earth[0])
    c.put(20, 4, earth[0])
    # left frame: sepia wedding photo, hangs a touch low
    _frame(c, 1, 6, 7, 8, earth)
    c.rect(2, 7, 5, 6, amber[1])
    c.hline(2, 6, 7, amber[2])
    c.hline(2, 6, 12, amber[0])
    for fx in (3, 5):
        c.put(fx, 9, earth[0])
        c.vline(fx, 10, 11, earth[1])
    # center frame: İbrahim and the dish, black-and-white via the stone ramp
    _frame(c, 8, 3, 9, 12, earth)
    c.hline(9, 15, 4, earth[0])                            # inner shadow ring
    c.vline(9, 5, 13, earth[0])
    c.vline(15, 5, 13, earth[0])
    c.hline(9, 15, 13, earth[0])
    c.rect(10, 5, 5, 8, stone[2])                          # gray sky
    c.hline(11, 14, 5, stone[3])                           # dish rim, catching light
    c.put(11, 6, stone[3])
    c.hline(12, 14, 6, stone[1])                           # bowl interior shadow
    c.hline(12, 13, 7, stone[3])                           # lower rim
    c.vline(13, 8, 9, stone[1])                            # pedestal
    c.put(10, 9, stone[0])                                 # the man, small before it
    c.vline(10, 10, 11, stone[0])
    c.hline(10, 14, 12, stone[1])                          # ground
    # right frame: the valley at dusk, hangs a touch high
    _frame(c, 18, 5, 6, 7, earth)
    c.rect(19, 6, 4, 2, amber[2])
    c.put(20, 7, stone[1])                                 # far peak
    c.hline(19, 22, 8, stone[1])                           # ridge line
    c.rect(19, 9, 4, 2, earth[1])                          # dark foreground


def _frame(c: PixelCanvas, x: int, y: int, w: int, h: int, earth: Ramp) -> None:
    """Thin wooden picture frame, top edge lit."""
    c.hline(x, x + w - 1, y, earth[2])
    c.hline(x, x + w - 1, y + h - 1, earth[0])
    c.vline(x, y + 1, y + h - 2, earth[1])
    c.vline(x + w - 1, y + 1, y + h - 2, earth[1])


def _draw_radio_table(
    c: PixelCanvas, earth: Ramp, paper: Ramp, amber: Ramp, stone: Ramp
) -> None:
    """16x20. Old bakelite transistor radio on a lace doily on a side table.
    The dial lamp is lit — someone listens every morning."""
    # telescopic antenna
    c.put(13, 0, stone[3])
    c.put(12, 1, stone[2])
    # radio body, rounded shoulders
    c.hline(4, 11, 2, earth[2])
    c.rect(3, 3, 10, 6, earth[1])
    c.vline(3, 3, 8, earth[0])
    c.vline(12, 3, 8, earth[2])
    # speaker grille slits
    c.vline(5, 4, 7, earth[0])
    c.vline(7, 4, 7, earth[0])
    # warm-lit dial with needle
    c.rect(9, 4, 3, 2, amber[1])
    c.put(9, 4, paper[2])
    c.vline(10, 4, 5, earth[0])
    # knobs
    c.put(9, 7, earth[3])
    c.put(11, 7, earth[3])
    c.hline(3, 12, 8, earth[0])
    # lace doily peeking out under the radio
    c.hline(1, 14, 9, earth[3])
    c.hline(1, 14, 10, earth[3])
    for lx in range(2, 14):
        if lx not in (4, 8, 11):
            c.put(lx, 9, paper[2])
    # tabletop edge + legs
    c.hline(1, 14, 11, earth[1])
    c.rect(2, 12, 2, 7, earth[1])
    c.rect(12, 12, 2, 7, earth[1])
    c.vline(2, 12, 18, earth[0])
    c.vline(13, 12, 18, earth[2])
    c.hline(2, 3, 18, earth[0])
    c.hline(12, 13, 18, earth[0])
    c.hline(4, 11, 15, earth[1])                           # stretcher bar
    # shadow, spilling left
    c.hline(2, 12, 19, earth[0])


def _draw_wardrobe(c: PixelCanvas, earth: Ramp, rng: random.Random) -> None:
    """24x32. Tall dark-wood wardrobe: crown, two panelled doors, plinth."""
    # crown molding
    c.hline(2, 21, 0, earth[2])
    c.hline(1, 22, 1, earth[1])
    c.hline(1, 22, 2, earth[0])
    # carcass
    c.rect(2, 3, 20, 26, earth[1])
    c.vline(2, 3, 28, earth[0])
    c.vline(21, 3, 28, earth[2])
    c.vline(12, 3, 28, earth[0])                           # door split
    # four inset panels (two per door), light catching each bottom bevel
    for px0 in (4, 14):
        for py0 in (5, 17):
            c.hline(px0, px0 + 6, py0, earth[0])
            c.hline(px0, px0 + 6, py0 + 9, earth[0])
            c.vline(px0, py0 + 1, py0 + 8, earth[0])
            c.vline(px0 + 6, py0 + 1, py0 + 8, earth[0])
            c.hline(px0 + 1, px0 + 5, py0 + 8, earth[2])
    # knobs by the split
    c.put(10, 15, earth[3])
    c.put(14, 15, earth[3])
    # sparse grain
    c.vline(6, 21, 22, earth[0])
    c.vline(17, 8, 9, earth[0])
    c.put(19, 24, earth[2])
    # plinth, feet, shadow
    c.hline(2, 21, 29, earth[0])
    c.hline(2, 4, 30, earth[0])
    c.hline(19, 21, 30, earth[0])
    c.hline(1, 20, 31, earth[0])


def _draw_table_home(c: PixelCanvas, earth: Ramp, paper: Ramp, amber: Ramp) -> None:
    """24x16. Low tea table: newspaper, a glass of tea on its saucer."""
    # tabletop
    c.hline(2, 21, 0, earth[2])                            # back rim
    c.rect(1, 1, 22, 5, earth[3])
    c.hline(1, 22, 6, earth[2])                            # front rounding
    c.hline(1, 22, 7, earth[1])
    c.hline(1, 22, 8, earth[0])                            # underside shadow
    # grain ticks
    c.hline(11, 13, 5, earth[2])
    c.hline(18, 19, 2, earth[2])
    c.hline(2, 3, 3, earth[2])
    # folded newspaper
    c.rect(4, 1, 6, 4, paper[2])
    c.hline(5, 8, 2, paper[0])
    c.hline(5, 7, 3, paper[0])
    c.hline(4, 9, 4, paper[1])
    # tea: tulip glass on a saucer
    c.hline(15, 16, 1, paper[2])                           # rim glint
    c.hline(15, 16, 2, amber[1])
    c.hline(15, 16, 3, amber[0])
    c.hline(14, 17, 4, paper[2])                           # saucer
    # legs, feet
    c.rect(2, 9, 2, 5, earth[1])
    c.rect(20, 9, 2, 5, earth[1])
    c.vline(2, 9, 13, earth[0])
    c.vline(21, 9, 13, earth[2])
    c.hline(2, 3, 13, earth[0])
    c.hline(20, 21, 13, earth[0])
    # shadow
    c.hline(1, 20, 14, earth[0])


def _draw_chair_home(c: PixelCanvas, earth: Ramp) -> None:
    """10x14. Plain kitchen chair, slat back, rush seat."""
    # top rail
    c.hline(1, 8, 0, earth[2])
    c.hline(1, 8, 1, earth[1])
    # stiles + one slat, air between them
    c.vline(1, 2, 6, earth[1])
    c.vline(8, 2, 6, earth[2])
    c.hline(2, 7, 4, earth[1])
    # rush seat, lit, front edge overhanging the legs
    c.hline(1, 8, 7, earth[3])
    c.hline(0, 9, 8, earth[3])
    c.put(3, 7, earth[2])
    c.put(5, 8, earth[2])
    c.put(7, 7, earth[2])
    # apron + legs
    c.hline(1, 8, 9, earth[1])
    c.put(0, 9, earth[0])                                  # seat lip shadow ends
    c.put(9, 9, earth[0])
    c.vline(1, 10, 12, earth[0])
    c.vline(2, 10, 12, earth[1])
    c.vline(7, 10, 12, earth[1])
    c.vline(8, 10, 12, earth[2])
    c.put(1, 12, earth[0])
    c.put(8, 12, earth[0])
    # shadow
    c.hline(1, 7, 13, earth[0])


def _draw_door_home(
    c: PixelCanvas, earth: Ramp, stone: Ramp, paper: Ramp, void: Ramp
) -> None:
    """16x24. Closed plank door in its frame; iron hinges left, handle right.
    A tiny boncuk hangs on the top rail."""
    # frame
    c.vline(0, 0, 23, earth[0])
    c.vline(15, 0, 23, earth[0])
    c.hline(1, 14, 0, earth[2])                            # lit lintel
    c.hline(1, 14, 1, earth[1])
    c.vline(1, 2, 23, earth[1])
    c.vline(2, 2, 23, earth[0])
    c.vline(14, 2, 23, earth[2])
    c.vline(13, 2, 23, earth[0])
    # door slab: vertical planks
    c.rect(3, 2, 10, 22, earth[1])
    c.hline(3, 12, 2, earth[0])                            # shadow under lintel
    c.vline(6, 3, 22, earth[0])
    c.vline(9, 3, 22, earth[0])
    c.hline(4, 5, 3, earth[2])                             # plank tops catch light
    c.hline(7, 8, 3, earth[2])
    c.hline(10, 11, 3, earth[2])
    c.hline(3, 12, 23, earth[0])
    # iron handle: dark backplate, lit knob — the door's one metal accent
    c.vline(11, 11, 13, stone[0])
    c.put(10, 12, stone[3])
    c.put(11, 14, void[0])                                 # keyhole
    # wood grain
    c.put(4, 16, earth[0])
    c.vline(11, 7, 8, earth[0])
    c.put(5, 20, earth[0])
