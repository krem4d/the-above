"""sprites.placeholder_hoca — M1 placeholder character sheet for Hoca.

16x24 art px per frame, baked 2x -> 32x48. Sheet: 4 cols x 5 rows
(row 0 idle_s, rows 1-4 walk s/n/e/w; west = mirrored east frames).
Palette contract: ONLY ``earth`` (coat/hair) + ``amber`` (skin) ramps.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..canvas import PixelCanvas
from ..palette import Palette, Ramp

FRAME_W = 16
FRAME_H = 24
COLS = 4
# (kind, direction, frame_count) per sheet row — append-only atlas contract.
ROWS = (
    ("idle", "s", 1),
    ("walk", "s", 4),
    ("walk", "n", 4),
    ("walk", "e", 4),
    ("walk", "w", 4),
)
IDLE_FPS = 1


def generate(manifest: dict, palette: Palette, out_root: Path) -> None:
    art_w, art_h = manifest.get("art_frame", [FRAME_W, FRAME_H])
    if (art_w, art_h) != (FRAME_W, FRAME_H):
        raise ValueError(f"placeholder_hoca draws {FRAME_W}x{FRAME_H} frames only")
    scale = int(manifest.get("scale", 2))
    walk_fps = int(manifest.get("walk_fps", 8))

    sheet = PixelCanvas(FRAME_W * COLS, FRAME_H * len(ROWS), palette)
    for row, (kind, direction, frame_count) in enumerate(ROWS):
        for phase in range(frame_count):
            frame = _draw_frame(palette, kind, direction, phase)
            sheet.paste(frame, phase * FRAME_W, row * FRAME_H)

    out_png = Path(out_root) / manifest.get("out", "sprites/hoca_sheet.png")
    sheet.save(out_png, scale=scale)
    sidecar = {
        "frame": [FRAME_W * scale, FRAME_H * scale],
        "cols": COLS,
        "rows": len(ROWS),
        "anims": {
            "idle_s": {"row": 0, "frames": 1, "fps": IDLE_FPS},
            "walk_s": {"row": 1, "frames": 4, "fps": walk_fps},
            "walk_n": {"row": 2, "frames": 4, "fps": walk_fps},
            "walk_e": {"row": 3, "frames": 4, "fps": walk_fps},
            "walk_w": {"row": 4, "frames": 4, "fps": walk_fps},
        },
    }
    out_png.with_suffix(".json").write_text(
        json.dumps(sidecar, indent=2) + "\n", encoding="utf-8"
    )


def _draw_frame(palette: Palette, kind: str, direction: str, phase: int) -> PixelCanvas:
    canvas = PixelCanvas(FRAME_W, FRAME_H, palette)
    earth = palette.ramp("earth")
    amber = palette.ramp("amber")
    if direction == "w":
        # West is the mirrored east frame (baked, per plan).
        east = _draw_frame(palette, kind, "e", phase)
        _paste_mirrored(canvas, east)
        return canvas
    # Passing frames bob the upper body up one pixel; feet stay planted.
    bob = -1 if kind == "walk" and phase in (1, 3) else 0
    if direction in ("s", "n"):
        _draw_front_or_back(canvas, earth, amber, direction, kind, phase, bob)
    else:
        _draw_side(canvas, earth, amber, kind, phase, bob)
    canvas.outline(earth)
    return canvas


def _draw_front_or_back(
    c: PixelCanvas, earth: Ramp, amber: Ramp, direction: str, kind: str, phase: int, bob: int
) -> None:
    # Head (rows 2-7): hair over face for south, full hair for north.
    if direction == "s":
        c.rect(5, 2 + bob, 6, 2, earth[1])
        c.rect(5, 4 + bob, 6, 4, amber[1])
        c.rect(8, 4 + bob, 3, 1, amber[2])  # light from top-right (global light)
        c.put(6, 6 + bob, earth[0])
        c.put(9, 6 + bob, earth[0])
    else:
        c.rect(5, 2 + bob, 6, 6, earth[1])
        c.rect(8, 2 + bob, 3, 1, earth[2])  # hair sheen, same light side
    # Coat torso (bottom edge fixed at y=17 so only the top bobs).
    c.rect(4, 8 + bob, 8, 10 - bob, earth[2])
    c.rect(4, 8 + bob, 1, 10 - bob, earth[1])  # shaded left edge
    c.rect(11, 8 + bob, 1, 10 - bob, earth[3])  # lit right edge
    # Arms swing opposite to the leading leg.
    swing = 0
    if kind == "walk":
        swing = 1 if phase == 0 else (-1 if phase == 2 else 0)
    c.rect(3, 9 + bob + swing, 1, 6, earth[1])
    c.rect(12, 9 + bob - swing, 1, 6, earth[1])
    c.put(3, 15 + bob + swing, amber[1])
    c.put(12, 15 + bob - swing, amber[1])
    # Legs: contact frames lift one foot a pixel.
    left_lift = 1 if kind == "walk" and phase == 0 else 0
    right_lift = 1 if kind == "walk" and phase == 2 else 0
    _front_leg(c, earth, 5, left_lift)
    _front_leg(c, earth, 9, right_lift)


def _front_leg(c: PixelCanvas, earth: Ramp, x: int, lift: int) -> None:
    c.rect(x, 18 - lift, 2, 4, earth[1])
    c.rect(x, 22 - lift, 2, 2, earth[0])


def _draw_side(
    c: PixelCanvas, earth: Ramp, amber: Ramp, kind: str, phase: int, bob: int
) -> None:
    # Head in profile: hair at back (left), face forward (right).
    c.rect(5, 2 + bob, 6, 2, earth[1])
    c.rect(5, 4 + bob, 3, 4, earth[1])
    c.rect(8, 4 + bob, 3, 4, amber[1])
    c.put(9, 5 + bob, earth[0])
    # Coat torso.
    c.rect(4, 8 + bob, 8, 10 - bob, earth[2])
    c.rect(4, 8 + bob, 1, 10 - bob, earth[1])  # back edge shaded
    c.rect(11, 8 + bob, 1, 10 - bob, earth[3])  # front edge lit
    # Single visible arm swings with the stride.
    swing = 0
    if kind == "walk":
        swing = 1 if phase == 0 else (-1 if phase == 2 else 0)
    arm_x = 7 + swing
    c.rect(arm_x, 9 + bob, 2, 6, earth[1])
    c.put(arm_x, 15 + bob, amber[1])
    # Legs: stride open on contact frames, together on passing/idle.
    if kind == "walk" and phase == 0:
        _side_leg(c, earth, 9, near=True)
        _side_leg(c, earth, 4, near=False)
    elif kind == "walk" and phase == 2:
        _side_leg(c, earth, 4, near=True)
        _side_leg(c, earth, 9, near=False)
    else:
        _side_leg(c, earth, 6, near=False)
        _side_leg(c, earth, 8, near=True)


def _side_leg(c: PixelCanvas, earth: Ramp, x: int, *, near: bool) -> None:
    c.rect(x, 18, 2, 4, earth[2] if near else earth[1])
    c.rect(x, 22, 2, 2, earth[0])


def _paste_mirrored(dst: PixelCanvas, src: PixelCanvas) -> None:
    for y in range(src.height):
        for x in range(src.width):
            color = src.get(x, y)
            if color[3] != 0:
                dst.put(src.width - 1 - x, y, color)
