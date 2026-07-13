"""tiles.obs_interior — the Sarptepe observatory control room (M4, Act 1).

One manifest, three sheets:
  tiles/obs_sheet.png — 4 tiles, 16x16 art baked 2x -> 32x32 cells, atlas
      order (append-only): floor_lino, floor_lino_var, wall_panel, window_sky.
  props/obs_props.png — 9 props, tightly packed; the sidecar's props dict is
      emitted in the append-only contract order.
  props/obs_printout.png — ONE prop (printout_overlay), the Day-1 archived
      printout, 128x96 art -> 256x192. The ONLY canvas in this module that
      opens the forbidden signal ramp; the magenta trace appears nowhere else.

Mood: fluorescent-dim, decades of state science, dusk pressing at the
windows. Global light from above, slightly right (the ceiling tubes) — top
faces lightest, right edges lit, left edges and undersides shaded.
Ramps: stone (linoleum, gray steel, CRT bezels, the dish), ship (the oily
state-green paint on every wall, cabinet and window frame), paper (upper
walls, printout boxes, meter faces, the printouts themselves), amber (pilot
lamps, the light behind the director's frosted door), rose (status lamps,
patch cords, the dish's aircraft-warning beacon), crt (phosphor screens ONLY
— never as decoration), void (screens off-glass, deep recesses, dusk sky,
mass separation). The signal ramp is touched ONLY by the printout canvas.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from ..canvas import PixelCanvas, TRANSPARENT
from ..palette import Palette, Ramp

ART = 16

TILE_ORDER = ("floor_lino", "floor_lino_var", "wall_panel", "window_sky")
SOLID_TILES = ("wall_panel", "window_sky")

# Sidecar key order — the append-only atlas contract for props.
PROP_ORDER = (
    "console_bank", "console_chair", "rack_a", "rack_b", "archive_shelf",
    "office_door", "whiteboard", "printer", "window_dish",
)
# name -> (sheet x, sheet y, w, h, solid rect rel. to region) — all in ART px.
PROP_LAYOUT = {
    "console_bank": (0, 0, 64, 32, (0, 0, 64, 32)),
    "console_chair": (112, 0, 10, 14, None),
    "rack_a": (64, 0, 16, 32, (0, 16, 16, 16)),
    "rack_b": (80, 0, 16, 32, (0, 16, 16, 16)),
    "archive_shelf": (0, 32, 48, 32, (0, 0, 48, 32)),
    "office_door": (96, 0, 16, 28, None),
    "whiteboard": (48, 32, 32, 24, None),
    "printer": (104, 32, 24, 18, (0, 6, 24, 12)),
    "window_dish": (80, 32, 24, 24, None),
}
PROP_SHEET_W = 128
PROP_SHEET_H = 64

PRINTOUT_W = 128
PRINTOUT_H = 96


def generate(manifest: dict, palette: Palette, out_root: Path) -> None:
    art_cell = int(manifest.get("art_cell", ART))
    if art_cell != ART:
        raise ValueError(f"tiles.obs_interior draws {ART}px art cells, got {art_cell}")
    scale = int(manifest.get("scale", 2))
    rng = random.Random(manifest["seed"])
    _emit_tile_sheet(manifest, palette, Path(out_root), rng, scale)
    _emit_prop_sheet(manifest, palette, Path(out_root), rng, scale)
    _emit_printout(manifest, palette, Path(out_root), rng, scale)


# ---------------------------------------------------------------------------
# tile sheet
# ---------------------------------------------------------------------------

def _emit_tile_sheet(
    manifest: dict, palette: Palette, out_root: Path, rng: random.Random, scale: int
) -> None:
    drawers = {
        "floor_lino": lambda c: _draw_floor_lino(c, palette, rng),
        "floor_lino_var": lambda c: _draw_floor_lino_var(c, palette, rng),
        "wall_panel": lambda c: _draw_wall_panel(c, palette, rng),
        "window_sky": lambda c: _draw_window_sky(c, palette, rng),
    }
    sheet = PixelCanvas(ART * len(TILE_ORDER), ART, palette)
    for col, name in enumerate(TILE_ORDER):
        tile = PixelCanvas(ART, ART, palette)
        drawers[name](tile)
        sheet.paste(tile, col * ART, 0)

    out_png = out_root / manifest.get("out_tiles", "tiles/obs_sheet.png")
    sheet.save(out_png, scale=scale)
    sidecar = {
        "grid": {"cell": ART * scale, "cols": len(TILE_ORDER), "rows": 1},
        "tiles": list(TILE_ORDER),
        "solid": list(SOLID_TILES),
    }
    out_png.with_suffix(".json").write_text(
        json.dumps(sidecar, indent=2) + "\n", encoding="utf-8"
    )


def _draw_floor_lino(
    c: PixelCanvas,
    palette: Palette,
    rng: random.Random,
    veins: tuple = None,
) -> None:
    """Institutional linoleum, cold under the tubes: one big square per tile,
    thin seams, a few marble veins drifting diagonally. The floor must stay
    calm — the consoles have to read over it."""
    stone = palette.ramp("stone")
    if veins is None:
        veins = _LINO_VEINS_A
    c.rect(0, 0, ART, ART, stone[1])
    c.hline(0, ART - 1, 15, stone[0])                      # seams — 16px squares
    c.vline(15, 0, 14, stone[0])
    for vx, vy, pale in veins:
        c.put(vx, vy, stone[2] if pale else stone[0])
    # a single stray fleck so no two floors feel machine-copied
    c.put(rng.randrange(1, 14), rng.choice((5, 9, 13)), stone[0])


_LINO_VEINS_A = (
    # (x, y, pale) — two dark diagonal drifts, one pale, a couple of flecks
    (3, 3, False), (4, 4, False), (5, 4, False),
    (11, 7, False), (12, 8, False),
    (9, 2, True), (10, 3, True),
    (6, 11, False), (7, 12, False),
    (13, 12, True), (2, 8, False),
)
_LINO_VEINS_B = (
    (10, 11, False), (11, 12, False), (12, 12, False),
    (4, 6, False), (5, 7, False),
    (2, 12, True), (3, 13, True),
    (12, 2, False), (13, 3, False),
    (6, 1, True), (8, 9, False),
)


def _draw_floor_lino_var(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """Same lino where the traffic goes: heel scuffs and a caster drag."""
    stone = palette.ramp("stone")
    _draw_floor_lino(c, palette, rng, veins=_LINO_VEINS_B)
    # black heel scuffs — short diagonal drags
    c.put(3, 4, stone[0])
    c.put(4, 5, stone[0])
    c.put(13, 8, stone[0])
    # a pale worn drag where the chair casters run
    sx = rng.choice((2, 5, 9))
    c.hline(sx, sx + 3, 10, stone[2])


def _draw_wall_panel(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """1980s state-institution wall: whitewash above, oil-paint wainscot
    below, a lit trim line between — the green every ministry corridor wears."""
    paper = palette.ramp("paper")
    ship = palette.ramp("ship")
    stone = palette.ramp("stone")
    void = palette.ramp("void")
    # upper wall
    c.rect(0, 0, ART, 7, paper[1])
    c.hline(0, ART - 1, 0, void[0])                        # ceiling line
    c.rect(0, 1, ART, 2, paper[2])                         # cap lit by the tubes
    for nx in (4, 10):
        c.put(nx, 2, paper[1])                             # cap wears ragged
    c.put(7, 3, paper[2])
    # plaster: single-pixel marks only (shapes would repeat every 16px)
    c.put(2, 5, paper[0])
    c.put(13, 4, paper[0])
    c.put(8, 6, paper[0])
    c.put(11, 3, paper[2])                                 # one bright fleck
    # trim line — the wainscot's lit cap
    c.hline(0, ART - 1, 7, ship[3])
    c.hline(0, ART - 1, 8, ship[0])                        # shadow under the lip
    # oil-paint wainscot
    c.rect(0, 9, ART, 4, ship[1])
    c.vline(8, 9, 12, ship[0])                             # pressed-panel joint
    c.put(3, 9, ship[2])                                   # paint sheen
    c.put(12, 10, ship[2])
    c.put(5, 11, ship[0])                                  # chair-back scuffs
    c.put(11, 12, ship[0])
    # base shadow where the wall meets the lino — ragged, not banded
    c.hline(0, 2, 12, ship[0])
    c.hline(6, 9, 12, ship[0])
    c.hline(13, 15, 12, ship[0])
    c.hline(0, ART - 1, 13, ship[0])
    c.hline(0, ART - 1, 14, stone[1])
    c.hline(0, ART - 1, 15, stone[0])


def _draw_window_sky(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """Wall tile pierced by a steel-framed window full of high-altitude dusk —
    a plain void->stone gradient, darkest up top, no stars yet."""
    ship = palette.ramp("ship")
    void = palette.ramp("void")
    stone = palette.ramp("stone")
    _draw_wall_panel(c, palette, rng)
    # steel frame, painted the same state green: lit lintel, shaded left jamb
    c.hline(1, 14, 1, ship[2])
    c.vline(1, 2, 11, ship[1])
    c.vline(14, 2, 11, ship[2])
    c.hline(2, 13, 2, ship[0])                             # frame depth shadow
    c.vline(2, 3, 11, ship[0])
    c.vline(13, 3, 11, ship[1])
    # the sky, x3..12 y3..11 — dusk sinking toward a pale horizon
    c.hline(3, 12, 3, void[1])
    c.dither_rect(3, 4, 10, 1, void, 1, 2, 0.5)
    c.hline(3, 12, 5, void[2])
    c.dither_rect(3, 6, 10, 1, void, 2, 3, 0.5)
    # mullion cross — sky picks up again below, warmer toward the horizon
    c.hline(3, 12, 7, ship[2])
    c.hline(3, 12, 8, void[3])
    c.dither_rect(3, 9, 10, 1, stone, 0, 1, 0.4)
    c.hline(3, 12, 10, stone[1])
    c.dither_rect(3, 11, 10, 1, stone, 1, 2, 0.4)
    c.vline(8, 3, 11, ship[1])                             # mullion over the glow
    # sill: lit top, shadow beneath
    c.hline(1, 14, 12, ship[2])
    c.hline(1, 14, 13, ship[0])


# ---------------------------------------------------------------------------
# prop sheet
# ---------------------------------------------------------------------------

def _emit_prop_sheet(
    manifest: dict, palette: Palette, out_root: Path, rng: random.Random, scale: int
) -> None:
    drawers = {
        "console_bank": _draw_console_bank,
        "console_chair": _draw_console_chair,
        "rack_a": _draw_rack_a,
        "rack_b": _draw_rack_b,
        "archive_shelf": _draw_archive_shelf,
        "office_door": _draw_office_door,
        "whiteboard": _draw_whiteboard,
        "printer": _draw_printer,
        "window_dish": _draw_window_dish,
    }
    sheet = PixelCanvas(PROP_SHEET_W, PROP_SHEET_H, palette)
    for name in PROP_ORDER:
        x, y, w, h, _solid = PROP_LAYOUT[name]
        prop = PixelCanvas(w, h, palette)
        drawers[name](prop, palette, rng)
        sheet.paste(prop, x, y)

    out_png = out_root / manifest.get("out_props", "props/obs_props.png")
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


# --- the console -------------------------------------------------------------

def _draw_console_bank(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """64x32. The main desk: state-green cabinet, two gray CRTs (a waterfall
    and a readout, both phosphor-green), meters, a patch field with red
    cords, switch banks the night shift left half-flipped, and a front lip
    worn to bare metal where Metin's forearms have rested for twenty years."""
    ship = palette.ramp("ship")
    stone = palette.ramp("stone")
    paper = palette.ramp("paper")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    crt = palette.ramp("crt")
    void = palette.ramp("void")

    # carcass
    c.hline(1, 62, 0, ship[3])                             # lit top edge
    c.rect(1, 1, 62, 29, ship[1])
    c.hline(1, 62, 1, ship[2])                             # top plane
    c.hline(1, 62, 2, ship[2])
    c.vline(0, 1, 30, ship[0])                             # shaded left flank
    c.vline(63, 1, 29, ship[2])                            # lit right flank

    # -- upright back panel, y3..12
    # CRT A — the waterfall, mid-sweep
    c.rect(4, 3, 16, 10, stone[1])
    c.hline(4, 19, 3, stone[2])                            # bezel top catches light
    c.vline(19, 4, 12, stone[2])
    c.rect(6, 5, 12, 6, void[0])                           # the glass
    for sx, sy in ((7, 9), (9, 6), (11, 8), (15, 5), (16, 9), (13, 6)):
        c.put(sx, sy, crt[0])                              # background hiss
    for tx, ty in ((14, 5), (14, 6), (13, 7), (13, 8), (12, 10)):
        c.put(tx, ty, crt[1])                              # the trace, drifting; gap = it breathes
    c.hline(5, 6, 12, stone[2])                            # maker's badge
    c.put(18, 12, amber[1])                                # pilot lamp
    # CRT B — the readout terminal
    c.rect(22, 3, 16, 10, stone[1])
    c.hline(22, 37, 3, stone[2])
    c.vline(37, 4, 12, stone[2])
    c.rect(24, 5, 12, 6, void[0])
    c.hline(25, 27, 6, crt[0])                             # lines of catalog text
    c.hline(29, 31, 6, crt[0])
    c.hline(25, 30, 8, crt[0])
    c.hline(32, 33, 8, crt[0])
    c.hline(25, 26, 10, crt[0])
    c.hline(28, 30, 10, crt[0])
    c.put(32, 10, crt[1])                                  # the cursor, waiting
    c.put(36, 12, amber[1])
    # right bay: two meters over a patch field, vents at the far end
    for mx in (42, 49):
        c.rect(mx, 4, 5, 4, paper[1])
        c.hline(mx, mx + 4, 4, paper[2])                   # glass catches the tubes
        c.put(mx + 2, 6, stone[1])                         # needle
        c.put(mx + 3, 5, stone[1])
        c.hline(mx, mx + 4, 7, stone[1])                   # bezel base
    for jy in (9, 11):
        for jx in range(42, 57, 2):
            c.put(jx, jy, void[1])                         # jack sockets
    c.put(44, 9, rose[1])                                  # a patch cord, looped
    c.hline(45, 47, 10, rose[0])
    c.put(48, 9, rose[1])
    c.put(50, 11, rose[1])                                 # a second, sagging lower
    c.hline(51, 53, 12, rose[0])
    c.put(54, 11, rose[1])
    for vy in (4, 6, 8):
        c.hline(59, 61, vy, ship[0])                       # vent slits

    # -- desk surface, y14..18
    c.hline(1, 62, 13, ship[0])                            # shadow under the shelf
    c.rect(1, 14, 62, 5, ship[2])
    c.vline(21, 14, 18, ship[1])                           # bay grooves
    c.vline(40, 14, 18, ship[1])
    # toggle bank under CRT A — the pattern the night shift left
    for tx in range(5, 19, 2):
        up = tx in (5, 9, 11, 17)
        c.put(tx, 15, stone[3] if up else stone[0])
        c.put(tx, 16, stone[0] if up else stone[3])
    c.hline(5, 6, 18, ship[1])                             # engraved labels
    c.hline(9, 10, 18, ship[1])
    c.hline(13, 14, 18, ship[1])
    # lamp field center — amber for power, rose for fault, dark for dead
    for lx, col in ((23, amber[2]), (25, ship[0]), (27, amber[1]), (29, rose[1]),
                    (31, ship[0]), (33, amber[2]), (35, ship[0]), (37, amber[1])):
        c.put(lx, 15, col)
    for lx, col in ((24, rose[2]), (28, ship[0]), (32, amber[1]), (36, ship[0])):
        c.put(lx, 17, col)
    # rotary knobs and the tuning dial, right bay
    for kx in (43, 47, 51):
        c.rect(kx, 15, 2, 2, stone[1])
        c.put(kx + 1, 15, stone[2])                        # lit shoulder
    c.rect(55, 15, 4, 2, void[1])                          # dial window
    c.hline(56, 58, 16, amber[0])                          # backlit scale
    c.put(57, 15, amber[3])                                # the needle
    # worn front lip — bare aluminum where the paint gave up
    c.hline(1, 62, 19, ship[3])
    c.hline(15, 21, 19, stone[3])                          # the operator's spot
    c.put(36, 19, ship[1])                                 # paint chips
    c.put(50, 19, ship[1])
    c.hline(1, 62, 20, ship[0])                            # under-lip shadow

    # -- kick panels, y21..28
    for sx in (16, 32, 48):
        c.vline(sx, 21, 28, ship[0])                       # bay seams
    for bx in (3, 34, 50):                                 # three cabinet doors
        c.hline(bx, bx + 11, 22, ship[0])
        c.hline(bx, bx + 11, 27, ship[0])
        c.vline(bx, 23, 26, ship[0])
        c.vline(bx + 11, 23, 26, ship[0])
        c.hline(bx + 1, bx + 10, 26, ship[2])              # bevel catches light
        c.put(bx + 9, 24, stone[3])                        # handle
    for vy in (23, 25, 27):
        c.hline(19, 29, vy, ship[0])                       # vent grille, bay 2
    # a notice taped to the third door, one corner curling
    c.rect(36, 23, 5, 3, paper[2])
    c.hline(37, 39, 24, paper[0])
    c.put(37, 25, paper[0])
    c.put(40, 25, paper[1])
    c.put(7, 28, ship[0])                                  # kick scuffs
    c.put(55, 27, ship[0])

    # base rail, plinth recess, shadow spilling left
    c.hline(1, 62, 29, ship[0])
    c.hline(2, 61, 30, void[1])
    c.hline(0, 58, 31, stone[0])


def _draw_console_chair(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """10x14. The operator's swivel chair, rose vinyl gone shiny, turned
    slightly as if someone just stood up."""
    rose = palette.ramp("rose")
    stone = palette.ramp("stone")
    # backrest
    c.hline(3, 7, 0, rose[2])
    c.rect(2, 1, 7, 5, rose[1])
    c.vline(2, 1, 5, rose[0])
    c.vline(8, 1, 5, rose[2])
    c.vline(5, 2, 4, rose[0])                              # center seam
    c.hline(2, 8, 5, rose[0])                              # bottom curl
    c.put(5, 6, stone[1])                                  # spine
    # seat pan, front edge rolling under
    c.hline(1, 8, 7, rose[2])
    c.hline(1, 8, 8, rose[1])
    c.put(3, 8, rose[0])                                   # seat crease
    c.hline(1, 8, 9, rose[0])
    # gas column and star base with casters
    c.vline(4, 10, 11, stone[2])
    c.vline(5, 10, 11, stone[1])
    c.hline(3, 6, 12, stone[1])
    c.put(2, 12, stone[1])
    c.put(7, 12, stone[1])
    c.put(1, 13, stone[0])                                 # casters
    c.put(8, 13, stone[0])
    c.put(4, 13, stone[0])


# --- equipment racks -----------------------------------------------------------

def _rack_frame(c: PixelCanvas, stone: Ramp, void: Ramp) -> None:
    """Shared 16x32 rack carcass: lit top, dark rails, plinth, floor shadow."""
    c.hline(1, 14, 0, stone[2])
    c.rect(1, 1, 14, 27, stone[1])
    c.vline(0, 0, 29, stone[0])
    c.vline(15, 0, 29, stone[1])
    c.hline(1, 14, 28, stone[0])                           # base rail
    c.hline(2, 13, 29, void[1])                            # plinth recess
    c.hline(1, 14, 30, void[1])
    c.hline(0, 12, 31, stone[0])                           # shadow spills left


def _draw_rack_a(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """16x32. Receiver rack: a meter unit, the big dark IF receiver with its
    lamp column half-lit, a newer vented unit, a blank plate, and one cable
    somebody never dressed properly."""
    stone = palette.ramp("stone")
    paper = palette.ramp("paper")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    void = palette.ramp("void")
    _rack_frame(c, stone, void)
    # unit 1: meter + knobs
    c.hline(1, 14, 1, stone[2])
    c.rect(3, 2, 4, 3, paper[1])
    c.hline(3, 6, 2, paper[2])
    c.put(4, 4, stone[0])                                  # needle
    c.put(5, 3, stone[0])
    c.put(9, 3, stone[3])                                  # knobs
    c.put(11, 3, stone[3])
    c.hline(9, 10, 5, stone[0])
    c.put(13, 3, amber[1])                                 # pilot lamp
    c.hline(1, 14, 6, stone[0])
    # unit 2: the dark receiver, y7..15
    c.rect(1, 7, 14, 9, void[1])
    c.hline(1, 14, 7, void[2])                             # its top edge, barely lit
    c.vline(2, 9, 13, stone[2])                            # rack handle
    for px, py in ((5, 9), (6, 9), (7, 9), (5, 10), (7, 10), (5, 11), (6, 11), (7, 11)):
        c.put(px, py, stone[1])                            # tuning dial ring
    c.put(6, 10, stone[3])                                 # its pointer
    c.hline(4, 6, 13, stone[1])                            # engraved label
    for ly, col in ((8, amber[2]), (9, stone[0]), (10, amber[1]), (11, rose[1]),
                    (12, stone[0]), (13, amber[2]), (14, stone[0])):
        c.put(11, ly, col)                                 # the lamp column, blinking
    c.hline(1, 14, 16, stone[0])
    # unit 3: newer, vented
    c.rect(1, 17, 14, 6, stone[2])
    c.hline(1, 14, 17, stone[3])
    c.hline(3, 10, 19, stone[1])
    c.hline(3, 10, 21, stone[1])
    c.put(12, 19, stone[3])                                # toggle, bat up
    c.put(12, 20, stone[0])
    c.hline(1, 14, 23, stone[0])
    # unit 4: blank plate with punched vents
    c.put(2, 25, stone[2])                                 # screws
    c.put(13, 25, stone[2])
    for vx in (6, 8, 10):
        c.put(vx, 25, stone[0])
    c.hline(1, 14, 27, stone[0])
    # the undressed cable, looping down the right side
    c.put(13, 13, stone[2])                                # its plug
    for cx, cy in ((13, 14), (13, 15), (14, 16), (14, 17), (14, 18),
                   (13, 19), (13, 20), (14, 21), (14, 22), (14, 23)):
        c.put(cx, cy, void[2])


def _draw_rack_b(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """16x32. Tape rack: reel-to-reel drive behind glass (one reel fat, one
    nearly spent), vacuum columns, transport buttons, a mechanical counter."""
    stone = palette.ramp("stone")
    paper = palette.ramp("paper")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    void = palette.ramp("void")
    _rack_frame(c, stone, void)
    # tape transport, y1..14
    c.hline(1, 14, 1, stone[2])
    c.rect(2, 2, 12, 9, void[0])                           # the glass door
    ring = ((-1, -2), (0, -2), (1, -2), (-2, -1), (2, -1), (-2, 0), (2, 0),
            (-2, 1), (2, 1), (-1, 2), (0, 2), (1, 2))
    for dx, dy in ring:                                    # supply reel, still fat
        c.put(4 + dx, 5 + dy, stone[2] if dy == -2 else stone[1])
    for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
        c.put(4 + dx, 5 + dy, void[2])                     # wound tape mass
    c.put(4, 5, stone[3])                                  # hub
    for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
        c.put(11 + dx, 5 + dy, stone[2] if dy == -1 else stone[1])
    c.put(11, 5, stone[3])                                 # take-up reel, nearly spent
    c.put(7, 8, void[2])                                   # the tape path
    c.put(8, 8, stone[3])                                  # capstan glint
    c.put(9, 8, void[2])
    c.vline(4, 11, 13, void[0])                            # vacuum columns
    c.vline(11, 11, 13, void[0])
    c.put(4, 11, void[2])                                  # tape hangs deeper in one
    c.put(4, 12, void[2])
    c.put(11, 11, void[2])
    c.hline(1, 14, 14, stone[0])
    # transport buttons
    for bx, col in ((3, amber[1]), (5, stone[2]), (7, stone[2]), (9, rose[1]), (11, stone[2])):
        c.put(bx, 16, col)
    c.hline(1, 14, 18, stone[0])
    # mechanical counter unit
    c.rect(1, 19, 14, 5, stone[2])
    c.hline(1, 14, 19, stone[3])
    c.rect(4, 21, 6, 2, paper[2])                          # the little white wheels
    c.vline(5, 21, 22, void[1])
    c.vline(7, 21, 22, void[1])
    c.put(9, 21, void[1])
    c.hline(11, 12, 22, stone[0])                          # RESET, engraved
    c.hline(1, 14, 24, stone[0])
    # blank plate below
    c.put(2, 26, stone[2])
    c.put(13, 26, stone[2])


# --- archive shelving ----------------------------------------------------------

def _archive_box(
    c: PixelCanvas, paper: Ramp, stone: Ramp, x: int, y: int, w: int, h: int,
    label: bool = True,
) -> None:
    """One printout box, front face: lit lid edge, shaded left, a spine label."""
    c.rect(x, y, w, h, paper[1])
    c.hline(x, x + w - 1, y, paper[2])
    c.vline(x, y + 1, y + h - 1, paper[0])
    if label:
        lx = x + w // 2 - 1
        c.rect(lx, y + 2, 2, 2, paper[2])
        c.put(lx, y + 3, stone[1])


def _draw_archive_shelf(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """48x32. Steel shelving, state green, sagging under thirty years of
    fanfold printouts — boxes shoulder to shoulder, two slots empty, and the
    box Ada will pull half-out already sitting proud of the line."""
    ship = palette.ramp("ship")
    paper = palette.ramp("paper")
    stone = palette.ramp("stone")
    void = palette.ramp("void")
    # cavity dark first, boards after
    c.rect(0, 0, 48, 30, void[1])
    for by, top in ((0, ship[3]), (10, ship[2]), (20, ship[2])):
        c.hline(0, 47, by, top)
        c.hline(0, 47, by + 1, ship[0])
    # -- top shelf: the tidy decades
    _archive_box(c, paper, stone, 1, 3, 7, 7)
    _archive_box(c, paper, stone, 8, 2, 6, 8)
    _archive_box(c, paper, stone, 14, 4, 7, 6)
    _archive_box(c, paper, stone, 24, 2, 7, 8)
    _archive_box(c, paper, stone, 31, 3, 5, 7, label=False)
    _archive_box(c, paper, stone, 36, 3, 8, 7)
    # -- middle shelf: the pulled box lives here
    _archive_box(c, paper, stone, 1, 13, 6, 7)
    _archive_box(c, paper, stone, 7, 12, 8, 8)
    _archive_box(c, paper, stone, 17, 14, 6, 6, label=False)
    _archive_box(c, paper, stone, 35, 13, 6, 7)
    _archive_box(c, paper, stone, 41, 12, 6, 8)
    # the half-pulled box, proud of the shelf line, lid open, fanfold showing
    c.rect(26, 14, 8, 8, paper[2])                         # front face in the light
    c.vline(26, 14, 21, paper[1])
    c.hline(26, 33, 14, paper[0])                          # the open mouth
    for fx in (27, 29, 31):
        c.put(fx, 13, paper[2])                            # folded printout edges
    c.put(28, 13, paper[1])
    c.put(30, 13, paper[1])
    c.put(30, 17, stone[1])                                # its label, half-read
    c.put(31, 17, stone[1])
    c.put(25, 20, ship[1])                                 # shadow it throws on the board
    c.put(34, 20, ship[1])
    # -- bottom shelf: bundles too heavy for boxes
    c.rect(1, 24, 12, 6, paper[1])
    c.hline(1, 12, 24, paper[2])
    c.hline(1, 12, 26, paper[0])
    c.hline(1, 12, 28, paper[0])
    c.put(13, 27, paper[1])                                # one sheet slipping out
    _archive_box(c, paper, stone, 14, 23, 8, 7)
    _archive_box(c, paper, stone, 24, 22, 8, 8)
    _archive_box(c, paper, stone, 32, 23, 7, 7, label=False)
    c.rect(39, 25, 8, 5, paper[1])
    c.hline(39, 46, 25, paper[2])
    c.hline(39, 46, 27, paper[0])
    # uprights over everything, then base
    c.vline(0, 0, 30, ship[0])
    c.vline(47, 0, 30, ship[2])
    c.vline(23, 0, 30, ship[1])                            # center post
    c.hline(0, 47, 30, ship[0])
    c.hline(0, 44, 31, stone[0])                           # floor shadow, spilling left


# --- doors, boards, machines ----------------------------------------------------

def _draw_office_door(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """16x28. The director's door: varnished wood, frosted pane lit warm from
    inside — Tezcan is in — a plaque, and light leaking under the slab."""
    earth = palette.ramp("earth")
    amber = palette.ramp("amber")
    paper = palette.ramp("paper")
    stone = palette.ramp("stone")
    void = palette.ramp("void")
    # frame
    c.vline(0, 0, 27, earth[0])
    c.vline(15, 0, 27, earth[0])
    c.hline(1, 14, 0, earth[2])
    c.hline(1, 14, 1, earth[1])
    c.vline(1, 2, 27, earth[1])
    c.vline(14, 2, 27, earth[2])
    # slab
    c.rect(2, 2, 12, 26, earth[1])
    c.hline(2, 13, 2, earth[0])                            # shadow under the lintel
    # frosted pane, x4..11 y4..11 — the lamp inside is up high
    c.hline(3, 12, 3, earth[0])
    c.vline(3, 4, 12, earth[0])
    c.vline(12, 4, 12, earth[0])
    c.hline(3, 12, 12, earth[0])
    c.rect(4, 4, 8, 2, amber[2])
    c.dither_rect(4, 6, 8, 1, amber, 1, 2, 0.5)
    c.rect(4, 7, 8, 3, amber[1])
    c.dither_rect(4, 10, 8, 2, amber, 1, 0, 0.4)
    c.put(6, 4, amber[3])                                  # bloom where the lamp sits
    c.put(7, 5, amber[3])
    c.hline(4, 11, 12, earth[2])                           # bevel catches the glow
    # plaque — BAŞ GÖZLEMCİ, too small to read, screwed on straight
    c.rect(4, 15, 6, 2, paper[2])
    c.put(5, 16, stone[1])
    c.put(7, 16, stone[1])
    c.put(8, 16, stone[1])
    c.hline(4, 9, 17, paper[0])
    # handle and keyhole
    c.vline(12, 14, 17, stone[1])
    c.hline(10, 11, 15, stone[3])
    c.put(12, 16, void[0])
    # lower panel inset
    c.hline(4, 11, 20, earth[0])
    c.hline(4, 11, 25, earth[0])
    c.vline(4, 21, 24, earth[0])
    c.vline(11, 21, 24, earth[0])
    c.hline(5, 10, 24, earth[2])
    # grain
    c.put(3, 18, earth[0])
    c.vline(13, 21, 22, earth[0])
    c.put(6, 27, earth[2])
    # the light under the door
    c.hline(2, 13, 27, earth[0])
    c.hline(6, 9, 27, amber[0])


def _draw_whiteboard(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """32x24. The shift whiteboard, wiped but never clean: a ghost plot
    nobody quite erased, a circled point, word-rows gone to smoke. Marker
    tray with two markers and the eraser that did this."""
    stone = palette.ramp("stone")
    paper = palette.ramp("paper")
    rose = palette.ramp("rose")
    ship = palette.ramp("ship")
    void = palette.ramp("void")
    # frame + board
    c.hline(0, 31, 0, stone[3])
    c.vline(0, 1, 19, stone[1])
    c.vline(31, 1, 19, stone[2])
    c.rect(1, 1, 30, 18, paper[2])
    c.hline(1, 30, 1, paper[1])                            # shadow under the top rail
    c.hline(1, 30, 19, stone[1])
    # ghost marks — stone[3] on paper[2], all of them broken by the eraser
    for gx, gy in ((3, 4), (4, 5), (5, 6), (6, 7), (5, 3), (6, 4), (7, 5), (9, 7)):
        c.put(gx, gy, stone[3])                            # one diagonal wipe, twice
    for gy in (4, 5, 6, 8, 9, 11, 12, 13):
        c.put(11, gy, stone[3])                            # y-axis, gap-toothed
    for gx in (11, 12, 13, 15, 16, 18, 19):
        c.put(gx, 14, stone[3])                            # x-axis
    for gx, gy in ((12, 12), (13, 11), (15, 10), (16, 9), (18, 8), (19, 7)):
        c.put(gx, gy, stone[3])                            # the rising curve
    for gx, gy in ((15, 8), (15, 10), (17, 10)):
        c.put(gx, gy, stone[3])                            # a circled point, half gone
    c.hline(22, 24, 4, stone[3])                           # word-rows
    c.hline(26, 28, 4, stone[3])
    c.hline(22, 26, 6, stone[3])
    c.hline(23, 25, 8, stone[3])
    c.hline(27, 28, 8, stone[3])
    c.hline(22, 28, 10, stone[3])                          # a hard underline
    c.put(23, 4, paper[2])                                 # erasure bites
    c.put(24, 6, paper[2])
    c.put(25, 10, paper[2])
    c.vline(24, 12, 13, stone[3])                          # number fragment, lower right
    c.vline(26, 12, 13, stone[3])
    # grubby corners
    c.put(2, 17, paper[1])
    c.put(29, 17, paper[1])
    c.put(16, 18, paper[1])
    # tray with markers and eraser
    c.hline(2, 29, 20, stone[2])
    c.hline(2, 29, 21, stone[1])
    c.hline(8, 9, 20, rose[1])                             # rose marker
    c.put(10, 20, rose[0])                                 # its cap
    c.hline(14, 15, 20, ship[1])                           # green marker
    c.put(16, 20, ship[0])
    c.rect(21, 19, 4, 1, paper[1])                         # the eraser, felt up
    c.rect(21, 20, 4, 1, void[1])
    # wall brackets
    c.put(5, 22, stone[1])
    c.put(5, 23, stone[0])
    c.put(26, 22, stone[1])
    c.put(26, 23, stone[0])


def _draw_printer(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """24x18. The dot-matrix chart printer mid-feed — paper climbing out the
    back, draping down the front, one fold already on the floor."""
    paper = palette.ramp("paper")
    stone = palette.ramp("stone")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    void = palette.ramp("void")
    # the risen sheet, back
    c.hline(7, 14, 0, paper[2])
    c.hline(6, 14, 1, paper[2])
    c.hline(6, 15, 2, paper[2])
    c.hline(8, 10, 1, stone[1])                            # fresh print rows
    c.hline(11, 13, 2, stone[1])
    c.put(7, 1, paper[0])                                  # tractor holes
    c.put(14, 1, paper[0])
    c.put(6, 2, paper[0])
    c.put(15, 2, paper[0])
    # platen bar behind
    c.hline(3, 16, 3, void[1])
    # body
    c.hline(1, 22, 4, paper[2])                            # lid top
    c.rect(1, 5, 22, 7, paper[1])
    c.vline(1, 5, 11, paper[0])
    c.vline(22, 5, 11, paper[2])
    c.hline(4, 15, 5, void[0])                             # the exit slot
    c.hline(2, 16, 6, paper[0])                            # lid seam
    c.put(18, 7, amber[2])                                 # ONLINE
    c.put(20, 7, rose[1])                                  # PAPER, always grumbling
    c.put(18, 9, stone[1])                                 # form-feed buttons
    c.put(20, 9, stone[1])
    c.hline(2, 5, 8, paper[0])                             # vents
    c.hline(2, 5, 10, paper[0])
    c.hline(1, 22, 12, paper[0])                           # base edge
    # shadow under the body, then feet
    c.hline(15, 20, 13, stone[0])
    c.put(2, 13, stone[1])
    c.put(21, 13, stone[1])
    # the front drape, over everything
    c.rect(7, 6, 7, 7, paper[2])
    c.vline(7, 6, 12, paper[0])                            # edges cut from the body
    c.vline(13, 6, 12, paper[1])
    for hy in (7, 10):
        c.put(8, hy, paper[0])                             # tractor holes, both margins
        c.put(12, hy, paper[0])
    c.put(10, 9, stone[1])                                 # the newest rows of print
    c.put(11, 9, stone[1])
    # the fold on the floor
    c.hline(7, 13, 13, paper[1])                           # sheet turning under
    c.hline(5, 14, 14, paper[2])                           # top of the fold, lit
    c.put(6, 14, paper[0])
    c.put(13, 14, paper[0])
    c.hline(5, 14, 15, paper[1])                           # its thickness
    c.hline(4, 15, 16, stone[0])                           # floor shadow
    c.hline(3, 11, 17, stone[0])                           # deeper where the fold shades


def _draw_window_dish(c: PixelCanvas, palette: Palette, rng: random.Random) -> None:
    """24x24. The window that matters: KULAK, the 32-metre dish, up on the
    ridge with its back to us, bowl tilted at The Above. Last light on the
    rim, the beacon already on, Taşlıca's first lamps in the valley."""
    ship = palette.ramp("ship")
    void = palette.ramp("void")
    stone = palette.ramp("stone")
    amber = palette.ramp("amber")
    rose = palette.ramp("rose")
    paper = palette.ramp("paper")
    # frame
    c.hline(0, 23, 0, ship[2])
    c.hline(1, 22, 1, ship[0])
    c.vline(0, 1, 20, ship[1])
    c.vline(1, 2, 20, ship[0])
    c.vline(23, 1, 20, ship[2])
    c.vline(22, 2, 20, ship[0])
    # dusk, darkest overhead, a tall afterglow standing on the ridge
    c.rect(2, 2, 20, 1, void[1])
    c.dither_rect(2, 3, 20, 1, void, 1, 2, 0.4)
    c.rect(2, 4, 20, 1, void[2])
    c.dither_rect(2, 5, 20, 1, void, 2, 3, 0.5)
    c.rect(2, 6, 20, 1, void[3])
    c.hline(2, 21, 7, stone[0])
    c.dither_rect(2, 8, 20, 1, stone, 0, 1, 0.5)
    c.hline(2, 21, 9, stone[1])
    c.dither_rect(2, 10, 10, 1, stone, 1, 2, 0.6)          # glow strongest to the west
    c.dither_rect(12, 10, 10, 1, stone, 1, 2, 0.35)
    c.rect(2, 11, 20, 6, stone[2])                         # the band the ridge will carve
    c.dither_rect(16, 11, 6, 4, stone, 2, 1, 0.3)          # dimming east
    # a bar of cloud lying in the glow
    c.hline(15, 18, 12, void[3])
    c.put(19, 12, void[3])
    # the ridge — black, close, carving the glow
    ridge_top = {2: 17, 3: 16, 4: 17, 5: 17, 6: 16, 7: 16, 8: 15, 9: 15,
                 10: 14, 11: 14, 12: 14, 13: 14, 14: 14, 15: 14, 16: 14,
                 17: 15, 18: 15, 19: 16, 20: 16, 21: 17}
    for rx, rt in ridge_top.items():
        c.vline(rx, rt, 20, void[1])
    # Taşlıca's first lamps, far below in the west
    c.put(3, 18, amber[0])
    c.put(5, 19, amber[0])
    # KULAK — bowl a black silhouette in the afterglow, back to us,
    # tilted up-left at The Above; last light rides the rim
    dish_rows = (
        (5, 15, 17), (6, 13, 17), (7, 11, 16), (8, 10, 14),
        (9, 9, 13), (10, 9, 12), (11, 10, 12),
    )
    for dy, bx0, bx1 in dish_rows:
        c.hline(bx0, bx1, dy, void[1])
    c.put(13, 11, void[1])                                 # rear hub bulge
    for rx, ry in ((15, 5), (16, 5), (17, 5), (13, 6), (14, 6), (11, 7),
                   (12, 7), (10, 8), (9, 9), (9, 10)):
        c.put(rx, ry, stone[3])                            # the lit rim, one unbroken line
    c.put(17, 6, void[0])                                  # mouth shadow inside the rim
    # feed struts closing over the mouth
    for sx in (11, 12, 13, 14):
        c.put(sx, 4, stone[1])
    for sy in (5, 6, 7, 8):
        c.put(9, sy, void[1])
    c.put(10, 4, stone[3])                                 # the feed
    c.put(10, 3, rose[2])                                  # aircraft beacon, already on
    # pedestal down to the crest
    c.vline(12, 12, 13, void[1])
    c.vline(13, 12, 13, void[1])
    # the mullion, then the sill with somebody's forgotten tea
    c.vline(6, 2, 20, ship[1])
    c.put(18, 19, paper[2])                                # glass rim
    c.put(18, 20, amber[1])                                # the tea, long cold
    c.hline(0, 23, 21, ship[3])                            # sill catches the tubes
    c.hline(17, 19, 21, paper[2])                          # its saucer
    c.hline(0, 23, 22, ship[1])
    c.hline(1, 22, 23, ship[0])


# ---------------------------------------------------------------------------
# the printout — clip anchor #1
# ---------------------------------------------------------------------------

def _text_row(
    c: PixelCanvas, rng: random.Random, x0: int, x1: int, y: int, color, h: int = 1
) -> None:
    """A row of illegible print: dashes 2-5px, word gaps, nothing readable."""
    x = x0
    while x <= x1 - 1:
        dash = min(rng.randint(2, 5), x1 - x + 1)
        for dy in range(h):
            c.hline(x, x + dash - 1, y + dy, color)
        x += dash + (3 if rng.random() < 0.22 else 1)


def _emit_printout(
    manifest: dict, palette: Palette, out_root: Path, rng: random.Random, scale: int
) -> None:
    """128x96 art -> 256x192. The Day-1 archived printout: 1986 fanfold,
    tractor holes, illegible survey text, a timestamp block, speckle noise —
    and one thin magenta line that should not be there. Austere on purpose:
    signal-linked art renders a tier below its scene."""
    paper = palette.ramp("paper")
    stone = palette.ramp("stone")
    void = palette.ramp("void")
    signal = palette.ramp("signal", allow_forbidden=True)
    W, H = PRINTOUT_W, PRINTOUT_H
    c = PixelCanvas(W, H, palette, allow_forbidden=True)

    # the sheet
    c.rect(0, 0, W, H, paper[2])
    # faint alternating feed-bar tint between the tractor strips
    for i, y0 in enumerate(range(0, H, 6)):
        if i % 2 == 1:
            c.dither_rect(7, y0, 114, min(6, H - y0), paper, 2, 1, 0.12)
    # tractor strips: perforation dashes, then the holes themselves
    for y in range(H):
        if y % 4 < 2:
            c.put(6, y, paper[1])
            c.put(121, y, paper[1])
    for hy in range(3, H - 2, 6):
        for hx in (2, 124):
            c.rect(hx, hy, 2, 2, TRANSPARENT)
            c.put(hx - 1, hy, paper[1])                    # punched rims
            c.put(hx + 2, hy + 1, paper[1])

    # header: station, survey run, field labels — dense and unreadable
    _text_row(c, rng, 10, 66, 3, void[1], h=2)             # the letterhead, bold
    _text_row(c, rng, 10, 78, 7, stone[1])
    _text_row(c, rng, 10, 60, 10, stone[1])
    _text_row(c, rng, 10, 38, 13, void[1])
    _text_row(c, rng, 44, 70, 13, stone[1])
    c.hline(8, 119, 17, stone[1])                          # rule

    # timestamp block, top right — the date that matters
    c.hline(88, 119, 2, stone[1])
    c.hline(88, 119, 14, stone[1])
    c.vline(88, 3, 13, stone[1])
    c.vline(119, 3, 13, stone[1])
    for i in range(8):                                     # digit blocks
        bx = 91 + i * 3
        c.rect(bx, 4, 2, 3, void[1])
        c.put(bx + rng.randrange(2), 4 + rng.randrange(3), paper[2])
    _text_row(c, rng, 91, 114, 9, stone[1])
    _text_row(c, rng, 91, 108, 12, void[1])

    # the chart frame and its axes
    c.hline(10, 117, 20, stone[1])
    c.hline(10, 117, 86, stone[1])
    c.vline(10, 21, 85, stone[1])
    c.vline(117, 21, 85, stone[1])
    for ty in range(24, 85, 8):
        c.hline(8, 9, ty, stone[1])
    for tx in range(16, 116, 10):
        c.vline(tx, 87, 88, stone[1])

    # printed background noise — the sky as the machine heard it
    for _ in range(150):
        c.put(rng.randrange(12, 116), rng.randrange(22, 85), void[1])
    for _ in range(90):
        c.put(rng.randrange(12, 116), rng.randrange(22, 85), stone[1])

    # THE TRACE — narrowband, wrong, a hair in a photograph. The on/off
    # cadence is countable (the canon broadcast pulses), the drift constant.
    for i, ty in enumerate(range(22, 85)):
        tx = 74 + (i * 6) // 63                            # constant slow drift
        phase = i % 11
        r = rng.random()
        if phase >= 8:                                     # the off-beats
            if r < 0.85:
                continue
        elif r < 0.06:
            continue                                       # dropout mid-burst
        c.put(tx, ty, signal[0])
        if 2 <= phase <= 5 and r > 0.5:
            c.put(tx + 1, ty, signal[0])                   # each burst runs hot mid-pulse

    # footer: operator line, page number
    _text_row(c, rng, 10, 56, 90, stone[1])
    _text_row(c, rng, 108, 116, 90, void[1])
    # corner wear
    c.put(0, 0, paper[1])
    c.put(127, 0, paper[1])
    c.put(0, 95, paper[1])
    c.put(127, 95, paper[1])

    out_png = out_root / manifest.get("out_printout", "props/obs_printout.png")
    c.save(out_png, scale=scale)
    sidecar = {
        "scale": scale,
        "props": {
            "printout_overlay": {
                "region": [0, 0, PRINTOUT_W * scale, PRINTOUT_H * scale],
                "solid": None,
            }
        },
    }
    out_png.with_suffix(".json").write_text(
        json.dumps(sidecar, indent=2) + "\n", encoding="utf-8"
    )
