"""tiles.dolmus_interior — İsmet's dolmuş interior (M4, Act 1).

One manifest, two sheets:
  tiles/dolmus_sheet.png — 2 tiles, 16x16 art baked 2x -> 32x32 cells, atlas
      order (append-only): bus_floor, bus_wall.
  props/dolmus_props.png — 5 props, tightly packed; the sidecar's props dict
      is emitted in the append-only contract order: window_valley, dashboard,
      seat_row, seat_single, bus_door.

Mood: cramped, warm, rattling, holy — golden hour on the switchbacks, the
town shrinking in the windows. Global light from above, slightly right:
top faces lightest, right edges lit, left edges and undersides shaded.
Ramps: stone (ribbed rubber floor, chrome, far ridges), paper (cream body
panels), rose (worn upholstery, tesbih, roof tiles), ship (glass, the nazar
boncuğu), earth (dash vinyl, valley slopes), amber (the golden valley, dial
lamps), void (gaskets, deep shadow, mass separation). No signal ramp here.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from ..canvas import PixelCanvas
from ..palette import Palette, Ramp

ART = 16

TILE_ORDER = ("bus_floor", "bus_wall")
SOLID_TILES = ("bus_wall",)

# Sidecar key order — the append-only atlas contract for props.
PROP_ORDER = ("window_valley", "dashboard", "seat_row", "seat_single", "bus_door")
# name -> (sheet x, sheet y, w, h, solid rect rel. to region) — all in ART px.
PROP_LAYOUT = {
    "window_valley": (0, 0, 64, 16, None),
    "dashboard": (0, 16, 32, 18, (0, 0, 32, 18)),
    "seat_row": (32, 16, 20, 14, (0, 6, 20, 8)),
    "seat_single": (52, 16, 12, 14, (0, 6, 12, 8)),
    "bus_door": (64, 0, 16, 24, None),
}
PROP_SHEET_W = 80
PROP_SHEET_H = 34


def generate(manifest: dict, palette: Palette, out_root: Path) -> None:
    art_cell = int(manifest.get("art_cell", ART))
    if art_cell != ART:
        raise ValueError(f"tiles.dolmus_interior draws {ART}px art cells, got {art_cell}")
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
    stone = palette.ramp("stone")
    paper = palette.ramp("paper")
    void = palette.ramp("void")

    drawers = {
        "bus_floor": lambda c: _draw_bus_floor(c, stone, rng),
        "bus_wall": lambda c: _draw_bus_wall(c, paper, stone, void, rng),
    }
    sheet = PixelCanvas(ART * len(TILE_ORDER), ART, palette)
    for col, name in enumerate(TILE_ORDER):
        tile = PixelCanvas(ART, ART, palette)
        drawers[name](tile)
        sheet.paste(tile, col * ART, 0)

    out_png = out_root / manifest.get("out_tiles", "tiles/dolmus_sheet.png")
    sheet.save(out_png, scale=scale)
    sidecar = {
        "grid": {"cell": ART * scale, "cols": len(TILE_ORDER), "rows": 1},
        "tiles": list(TILE_ORDER),
        "solid": list(SOLID_TILES),
    }
    out_png.with_suffix(".json").write_text(
        json.dumps(sidecar, indent=2) + "\n", encoding="utf-8"
    )


def _draw_bus_floor(c: PixelCanvas, stone: Ramp, rng: random.Random) -> None:
    """Ribbed rubber runner laid along the aisle, worn pale down the middle.

    Vertical ribs on a 4px period (tiles seamlessly); ridges catch the light
    on their right flank. The center band is where every passenger shuffles
    to the back — grooves silted shallow, rib tops polished a step lighter."""
    for x in range(ART):
        idx = (0, 1, 2, 1)[x % 4]  # groove / flank / lit ridge / flank
        c.vline(x, 0, ART - 1, stone[idx])
    # worn walking path: brighten toward the middle, fade at the edges
    c.dither_rect(5, 0, 1, ART, stone, 1, 2, 0.4)
    c.dither_rect(6, 0, 1, ART, stone, 2, 3, 0.4)
    c.dither_rect(7, 0, 1, ART, stone, 1, 2, 0.6)
    c.dither_rect(8, 0, 1, ART, stone, 0, 1, 0.7)
    c.dither_rect(9, 0, 1, ART, stone, 1, 2, 0.6)
    c.dither_rect(10, 0, 1, ART, stone, 2, 3, 0.4)
    c.dither_rect(11, 0, 1, ART, stone, 1, 2, 0.3)
    # heel scuffs in the worn band — brightest only on the ridge columns
    for _ in range(4):
        sx = rng.randrange(5, 11)
        sy = rng.randrange(ART)
        c.put(sx, sy, stone[3] if sx in (6, 10) else stone[2])
    # grit swept against the seat rails at the edges
    for _ in range(3):
        c.put(rng.choice((1, 2, 13, 14)), rng.randrange(ART), stone[0])


def _draw_bus_wall(
    c: PixelCanvas, paper: Ramp, stone: Ramp, void: Ramp, rng: random.Random
) -> None:
    """Cream panel below the window band: gasket shadow, lit sill cap,
    riveted panel joint, chrome rub-rail, kick shadow at the floor."""
    c.rect(0, 0, ART, ART, paper[1])
    c.hline(0, ART - 1, 0, void[0])                        # gasket under the glass
    c.rect(0, 1, ART, 2, paper[2])                         # lit sill cap
    for nx in (2, 7, 12):
        c.put(nx, 2, paper[1])                             # cap wears through, ragged
    # panel joint (repeats every tile-width, like the real pressed panels)
    c.vline(8, 3, 11, paper[0])
    c.put(8, 4, stone[1])                                  # rivets on the joint
    c.put(8, 9, stone[1])
    # scuffs from bags and knees — single-pixel marks only
    c.put(3, 5, paper[0])
    c.put(12, 7, paper[0])
    c.put(5, 9, paper[0])
    c.put(11, 4, paper[2])                                 # one bright fleck
    # chrome rub-rail
    c.hline(0, ART - 1, 10, stone[2])
    c.put(5, 10, stone[3])                                 # glints, light from the right
    c.put(13, 10, stone[3])
    c.hline(0, ART - 1, 11, stone[1])
    # kick shadow pooling at the floor — ragged, not banded
    c.hline(0, 3, 12, paper[0])
    c.hline(7, 10, 12, paper[0])
    c.hline(13, 15, 12, paper[0])
    c.hline(0, ART - 1, 13, paper[0])
    c.hline(0, ART - 1, 14, stone[1])
    c.hline(0, ART - 1, 15, stone[0])


# ---------------------------------------------------------------------------
# prop sheet
# ---------------------------------------------------------------------------

def _emit_prop_sheet(
    manifest: dict, palette: Palette, out_root: Path, rng: random.Random, scale: int
) -> None:
    drawers = {
        "window_valley": _draw_window_valley,
        "dashboard": _draw_dashboard,
        "seat_row": _draw_seat_row,
        "seat_single": _draw_seat_single,
        "bus_door": _draw_bus_door,
    }
    sheet = PixelCanvas(PROP_SHEET_W, PROP_SHEET_H, palette)
    for name in PROP_ORDER:
        x, y, w, h, _solid = PROP_LAYOUT[name]
        prop = PixelCanvas(w, h, palette)
        drawers[name](prop, palette, rng)
        sheet.paste(prop, x, y)

    out_png = out_root / manifest.get("out_props", "props/dolmus_props.png")
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


# --- window strip: the town shrinking below ---------------------------------

def _draw_window_valley(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """64x16. Four panes of golden valley: Taşlıca small below, ridgelines,
    amber haze, the one switchback road we are climbing. Continuous vista
    painted first, window pillars and gaskets over it."""
    amber = palette.ramp("amber")
    stone = palette.ramp("stone")
    earth = palette.ramp("earth")
    rose = palette.ramp("rose")
    paper = palette.ramp("paper")
    void = palette.ramp("void")

    # -- sky, brightening toward the low sun right of center
    c.hline(0, 63, 1, amber[1])
    c.hline(0, 63, 2, amber[2])
    c.dither_rect(0, 2, 16, 1, amber, 1, 2, 0.5)           # deeper away from the sun
    c.hline(0, 63, 3, amber[2])
    c.dither_rect(30, 3, 26, 1, amber, 2, 3, 0.55)         # glow gathering
    c.hline(0, 63, 4, amber[3])                            # horizon blaze
    c.dither_rect(0, 4, 12, 1, amber, 2, 3, 0.5)
    # the low sun, squashed by the haze, sitting over the saddle
    c.rect(39, 2, 3, 2, amber[3])
    c.put(38, 3, amber[3])
    c.put(42, 3, amber[3])
    # two birds crossing the glow
    c.put(32, 2, earth[0])
    c.put(33, 2, earth[0])
    c.put(36, 3, earth[0])

    # -- far ridge: violet-gray haze wall, dipping to a saddle under the sun
    far_top = []
    for x in range(64):
        if x < 10:
            t = 5
        elif x < 18:
            t = 4
        elif x < 28:
            t = 5
        elif x < 36:
            t = 4
        elif x < 47:
            t = 6                                          # saddle under the sun
        elif x < 56:
            t = 5
        else:
            t = 4
        far_top.append(t)
        for y in range(t, 7):
            c.put(x, y, stone[2])
    for x in list(range(30, 36)) + list(range(47, 53)):
        c.put(x, far_top[x], stone[3])                     # rim light beside the sun

    # -- valley haze band between the far wall and the fields
    c.hline(10, 49, 7, amber[2])

    # -- valley floor: fields, then the town, river, poplars
    c.rect(0, 8, 50, 4, earth[2])
    c.rect(30, 8, 5, 2, earth[3])                          # pale stubble field
    c.rect(41, 8, 5, 2, amber[0])                          # cut hay, gone gold
    c.rect(42, 10, 5, 1, earth[1])                         # fresh-plowed strip
    # poplar line between fields, autumn-yellow crowns
    for px in (35, 37):
        c.put(px, 8, amber[0])
        c.put(px, 9, earth[0])
    # the river, slipping out of town westward, catching the sky
    for rx, ry, glint in (
        (10, 11, False), (11, 10, False), (12, 10, True), (13, 9, False),
        (14, 9, True), (15, 9, False), (16, 9, False), (17, 9, True),
    ):
        c.put(rx, ry, amber[3] if glint else amber[2])
    # Taşlıca: small kiremit roofs, sunlit on the right, two window glints,
    # the mosque dome and one white minaret rising into the haze
    _town_roof(c, rose, 18, 9, 2)
    _town_roof(c, rose, 21, 8, 2)
    _town_roof(c, rose, 24, 9, 3)
    _town_roof(c, rose, 19, 11, 2)
    _town_roof(c, rose, 22, 10, 2)
    _town_roof(c, rose, 25, 11, 2)
    c.put(20, 10, paper[2])                                # whitewashed gable ends
    c.put(23, 9, paper[2])
    c.put(26, 10, amber[3])                                # a window catches the sun
    c.put(18, 10, amber[3])
    c.put(23, 8, stone[2])                                 # lead mosque dome
    c.put(24, 8, stone[2])
    c.put(27, 6, stone[1])                                 # minaret cone tip
    c.vline(27, 7, 9, paper[2])                            # the minaret itself

    # -- near slope rising toward us (we are high on it)
    for x in range(64):
        top = 13 if x < 26 else (12 if x < 48 else 11)
        for y in range(top, 14):
            c.put(x, y, earth[1])
    for sx, sy in ((28, 12), (50, 11), (55, 11), (60, 11)):
        c.put(sx, sy, earth[2])                            # dry grass catching light
    for sx, sy in ((5, 13), (12, 13), (31, 13), (34, 13), (49, 12), (58, 12)):
        c.put(sx, sy, earth[0])                            # scrub clumps
    c.put(53, 12, amber[0])                                # one gold bush
    c.put(61, 13, amber[0])

    # -- the switchback: one thin road folding up the slope toward us
    c.hline(27, 39, 10, paper[1])
    c.put(40, 10, paper[2])                                # lit outer curve, east hairpin
    c.put(40, 11, paper[1])
    c.hline(28, 39, 11, paper[1])
    c.put(27, 11, paper[2])                                # west hairpin
    c.put(27, 12, paper[1])
    c.hline(28, 44, 12, paper[1])
    c.put(45, 12, paper[2])
    c.put(45, 13, paper[1])
    c.hline(46, 57, 13, paper[1])                          # the stretch we are on

    # -- left spur, closer and cooler, carrying the observatory dome
    for x in range(17):
        if x < 4:
            t = 4
        elif x < 9:
            t = 5
        elif x < 13:
            t = 6
        else:
            t = 7
        for y in range(t, 9):
            c.put(x, y, stone[1])
    c.put(6, 3, paper[2])                                  # the observatory, tiny, above
    c.hline(5, 7, 4, paper[2])
    c.hline(5, 7, 5, stone[0])                             # its shadowed base

    # -- right spur, nearest ridge, shouldering into frame
    for x in range(50, 64):
        t = 7 if x < 54 else (6 if x < 59 else 5)
        for y in range(t, 11):
            c.put(x, y, stone[1])
    for x in range(54, 60):
        c.put(x, 6 if x < 59 else 5, stone[2])             # its lit brow

    # -- window pillars with rubber gaskets, then frame and sill
    for px0 in (14, 30, 46):
        c.vline(px0, 1, 13, void[0])
        c.vline(px0 + 1, 1, 13, paper[1])
        c.vline(px0 + 2, 1, 13, paper[2])                  # right face lit
        c.vline(px0 + 3, 1, 13, void[0])
    c.hline(0, 63, 0, void[0])                             # top gasket
    c.hline(0, 63, 14, void[0])                            # bottom gasket
    c.hline(0, 63, 15, paper[2])                           # continuous lit sill rail
    c.vline(0, 0, 15, void[0])
    c.vline(63, 0, 15, void[0])


def _town_roof(c: PixelCanvas, rose: Ramp, x: int, y: int, w: int) -> None:
    """A distant kiremit roof: shaded left, lit right (sun sits to the right)."""
    c.put(x, y, rose[1])
    for dx in range(1, w):
        c.put(x + dx, y, rose[2])


# --- dashboard ---------------------------------------------------------------

def _draw_dashboard(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """32x18. İsmet's dash: dark vinyl pad over a cream fascia, the big thin
    wheel, gauges glowing amber, radio slot, glovebox, destination card —
    and off the mirror, the nazar boncuğu and his tesbih."""
    earth = palette.ramp("earth")
    paper = palette.ramp("paper")
    stone = palette.ramp("stone")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    ship = palette.ramp("ship")
    void = palette.ramp("void")

    # vinyl pad, sun-warmed top edge, vent slits
    c.hline(0, 31, 8, earth[2])
    c.rect(0, 9, 32, 2, earth[1])
    c.hline(21, 23, 9, earth[0])
    c.hline(26, 28, 9, earth[0])
    c.vline(0, 9, 10, earth[0])                            # shaded left shoulder
    c.vline(31, 9, 10, earth[2])                           # lit right shoulder
    # cream fascia below
    c.hline(0, 31, 11, paper[0])                           # shadow under the pad lip
    c.rect(0, 12, 32, 4, paper[1])
    c.vline(0, 12, 15, paper[0])
    c.vline(31, 12, 15, paper[2])
    # instrument binnacle behind the wheel, dials lit for the evening run
    c.rect(5, 11, 7, 2, void[1])
    c.put(6, 12, amber[2])                                 # speedo needle glow
    c.put(9, 12, amber[1])                                 # fuel, always half
    # radio slot: dial lamp on, tuned to the one station that reaches up here
    c.rect(17, 12, 7, 4, void[1])
    c.hline(18, 22, 13, amber[1])
    c.put(20, 13, amber[3])                                # the needle
    c.put(18, 15, stone[2])                                # knobs
    c.put(22, 15, stone[2])
    # glovebox, lid edge catching light, one button
    c.hline(26, 30, 12, paper[0])
    c.vline(26, 13, 15, paper[0])
    c.vline(30, 13, 15, paper[0])
    c.hline(27, 29, 13, paper[2])
    c.put(28, 14, stone[1])
    # destination card propped against the glass: TAŞLICA
    c.rect(25, 7, 6, 2, paper[2])
    c.put(26, 8, paper[0])
    c.put(28, 8, paper[0])
    c.put(29, 8, paper[0])
    # under-dash shadow
    c.hline(0, 31, 16, paper[0])
    c.hline(1, 30, 17, void[1])

    # the big thin wheel — bakelite ring, worn chrome hub, three spokes
    c.hline(3, 6, 10, void[1])                             # spokes first
    c.hline(10, 13, 10, void[1])
    c.vline(8, 11, 14, void[1])                            # down-spoke into the column
    c.rect(7, 9, 3, 2, stone[1])                           # hub
    c.put(9, 9, stone[2])                                  # horn button, lit side
    c.hline(6, 10, 6, void[1])                             # ring
    for x, y in ((4, 7), (5, 7), (11, 7), (12, 7), (3, 8), (13, 8),
                 (2, 9), (14, 9), (2, 10), (14, 10), (3, 11), (13, 11),
                 (4, 12), (5, 12), (11, 12), (12, 12)):
        c.put(x, y, void[1])
    c.hline(6, 10, 13, void[1])
    c.put(9, 6, stone[1])                                  # rim sheen, upper right
    c.put(10, 6, stone[1])
    c.put(12, 7, stone[1])

    # rearview mirror holding the sunset, hung with what keeps a bus safe
    c.put(17, 0, stone[1])                                 # stalk
    c.hline(13, 20, 1, stone[2])                           # lit frame top
    c.hline(14, 19, 2, amber[1])                           # the road behind, golden
    c.put(18, 2, amber[2])
    c.hline(13, 20, 3, stone[0])
    # nazar boncuğu on its string
    c.vline(16, 4, 5, earth[0])
    c.put(16, 6, ship[3])
    c.put(15, 7, ship[3])
    c.put(17, 7, ship[3])
    c.put(16, 8, ship[3])
    c.put(16, 7, paper[2])                                 # the eye
    # tesbih looped over the mirror's right arm, tassel resting on the pad
    for bx, by in ((20, 4), (21, 5), (21, 6), (20, 7), (19, 6), (19, 5)):
        c.put(bx, by, rose[0])
    c.put(21, 5, rose[1])                                  # one bead catches light
    c.put(20, 8, rose[0])                                  # tassel
    c.put(20, 9, rose[1])


# --- seats --------------------------------------------------------------------

def _draw_seat_row(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """20x14. Two-passenger bench: chrome grab rail, worn rose upholstery
    split into two cushions, one torn seam, tube-steel legs."""
    rose = palette.ramp("rose")
    stone = palette.ramp("stone")
    paper = palette.ramp("paper")
    void = palette.ramp("void")

    # grab rail across the top, lit chrome with cooler ends
    c.hline(2, 17, 0, stone[3])
    c.put(1, 0, stone[2])
    c.put(18, 0, stone[2])
    c.put(3, 1, stone[1])                                  # rail posts
    c.put(16, 1, stone[1])
    # seatback, two cushions
    c.rect(1, 1, 18, 8, rose[1])
    c.hline(1, 18, 1, rose[2])                             # lit top roll
    c.vline(1, 2, 8, rose[0])                              # shaded left edge
    c.vline(18, 2, 8, rose[2])                             # lit right edge
    c.vline(9, 2, 8, rose[0])                              # center seam
    # sit-shine where shoulders rub, one polished patch per cushion
    c.dither_rect(3, 3, 5, 4, rose, 1, 2, 0.35)
    c.dither_rect(12, 3, 5, 4, rose, 1, 2, 0.35)
    # the tear on the right cushion, foam poking through
    c.put(14, 3, rose[0])
    c.put(15, 3, paper[1])
    c.put(16, 4, rose[0])
    c.hline(1, 18, 8, rose[0])                             # crease above the cushion
    # seat cushion, a shade wider, front face rolling under
    c.hline(0, 19, 9, rose[2])
    c.rect(0, 10, 20, 2, rose[1])
    c.put(5, 10, rose[0])                                  # butt creases
    c.put(14, 10, rose[0])
    c.hline(0, 19, 11, rose[0])
    # under-seat dark, tube legs, floor shadow
    c.hline(1, 18, 12, void[1])
    c.vline(2, 12, 13, stone[1])
    c.vline(17, 12, 13, stone[1])
    c.put(2, 13, stone[0])
    c.put(17, 13, stone[0])
    c.hline(3, 16, 13, void[1])


def _draw_seat_single(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """12x14. The single seat by the door, same worn bench cut down —
    someone stitched a darker patch over the worst of it."""
    rose = palette.ramp("rose")
    stone = palette.ramp("stone")
    void = palette.ramp("void")

    c.hline(2, 9, 0, stone[3])
    c.put(1, 0, stone[2])
    c.put(10, 0, stone[2])
    c.put(3, 1, stone[1])
    c.put(8, 1, stone[1])
    c.rect(1, 1, 10, 8, rose[1])
    c.hline(1, 10, 1, rose[2])
    c.vline(1, 2, 8, rose[0])
    c.vline(10, 2, 8, rose[2])
    c.dither_rect(3, 3, 5, 4, rose, 1, 2, 0.35)
    # the hand-sewn patch
    c.rect(6, 5, 2, 2, rose[0])
    c.put(7, 5, rose[2])                                   # one proud stitch
    c.hline(1, 10, 8, rose[0])
    c.hline(0, 11, 9, rose[2])
    c.rect(0, 10, 12, 2, rose[1])
    c.put(4, 10, rose[0])
    c.hline(0, 11, 11, rose[0])
    c.hline(1, 10, 12, void[1])
    c.vline(2, 12, 13, stone[1])
    c.vline(9, 12, 13, stone[1])
    c.put(2, 13, stone[0])
    c.put(9, 13, stone[0])
    c.hline(3, 8, 13, void[1])


# --- folding door --------------------------------------------------------------

def _draw_bus_door(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """16x24. Bi-fold dolmuş door: mechanism rail up top, two glass panes in
    rubber, cream lower panels, chrome grab bar, dark step well below."""
    paper = palette.ramp("paper")
    ship = palette.ramp("ship")
    stone = palette.ramp("stone")
    void = palette.ramp("void")

    # header + fold mechanism
    c.hline(0, 15, 0, stone[2])
    c.hline(1, 14, 1, void[1])
    c.put(7, 1, stone[2])                                  # pivot arm
    c.put(8, 1, stone[2])
    # frame posts
    c.vline(0, 1, 22, stone[1])
    c.vline(15, 1, 22, stone[2])                           # lit right post
    # leaves
    c.rect(1, 2, 14, 20, paper[1])
    c.vline(7, 2, 21, void[1])                             # fold seam
    c.vline(8, 2, 21, paper[0])
    c.vline(1, 2, 21, paper[0])                            # leaf A shaded edge
    c.vline(14, 2, 21, paper[2])                           # leaf B lit edge
    # glass panes in rubber gaskets, evening reflections sliding across
    c.rect(2, 3, 5, 9, ship[0])
    c.put(3, 4, ship[1])
    c.put(4, 5, ship[1])
    c.put(5, 6, ship[1])
    c.put(6, 3, ship[2])
    c.rect(9, 3, 5, 9, ship[0])
    c.put(10, 5, ship[1])
    c.put(11, 6, ship[1])
    c.put(12, 7, ship[1])
    c.put(13, 3, ship[2])                                  # brighter on the lit leaf
    c.put(13, 4, ship[2])
    # mid rail
    c.hline(1, 14, 12, paper[2])
    c.hline(1, 14, 13, paper[0])
    # chrome grab bar on the lit leaf
    c.vline(12, 14, 18, stone[2])
    c.put(12, 14, stone[3])
    # kick scuffs on the lower panels
    c.put(3, 19, paper[0])
    c.put(5, 20, paper[0])
    c.put(10, 19, paper[0])
    # bottom rail + step well falling into dark
    c.hline(1, 14, 21, paper[0])
    c.rect(1, 22, 14, 2, void[1])
    c.hline(2, 13, 23, void[0])
