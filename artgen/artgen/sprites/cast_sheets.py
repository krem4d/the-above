"""sprites.cast_sheets — the Act 1 cast walk/idle sheets (M4).

One manifest -> eleven sheets under sprites/<id>_sheet.png (+ .json sidecar):
hoca, yildiz (cat), fadime, musa, sukru, elif, kadir, ismet, metin, ebru,
tezcan. Humans are 16x24 art frames baked 2x -> 32x48; the cat is 16x16 ->
32x32. Sheet rows (append-only atlas contract; hoca's first five rows keep
the committed M1 layout exactly): idle_s(1), walk_s(4), walk_n(4),
walk_e(4), walk_w(4 — baked mirror of east), then idle_n(1), idle_e(1),
idle_w(1).

Character truth (ramps, heights, builds, signature features) comes from
artgen/cast/characters.json via manifest["cast"] — the same file the
portrait generator consumes, so sheets and portraits agree. characters.json
content affects drawing but never RNG state: rng (seeded from
manifest["seed"] only) hands each character id a fixed set of cloth-weave
accent positions up front, and those accents are drawn at the same
torso-relative coordinates on every frame so nothing shimmers.

Walk grammar: 4-frame contact/passing cycle. Feet planted on the frame's
bottom rows; contact frames (0, 2) drop the body 1px — the gait's low
point — and open the stride; passing frames (1, 3) carry the secondary
motion (ponytails, skirts, coat hems, the cat's tail) one px behind the
body. Arms counter-swing on contact. Global light from above, slightly
right: right edges lit, left edges shaded.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from types import SimpleNamespace

from ..canvas import PixelCanvas
from ..palette import Palette, RGBA

ART_W, ART_H = 16, 24  # human art frame
CAT_W, CAT_H = 16, 16  # yildiz art frame
COLS = 4
# (kind, direction, frame_count) per sheet row — append-only atlas contract.
ROWS = (
    ("idle", "s", 1),
    ("walk", "s", 4),
    ("walk", "n", 4),
    ("walk", "e", 4),
    ("walk", "w", 4),
    ("idle", "n", 1),
    ("idle", "e", 1),
    ("idle", "w", 1),
)
IDLE_FPS = 1

_REF_RE = re.compile(r"([a-z]+)\[(\d+)\]")


def _refs(palette: Palette, text: str) -> list[RGBA]:
    """Every ``ramp[idx]`` reference in a characters.json prose field, in order."""
    return [palette.ramp(m.group(1))[int(m.group(2))] for m in _REF_RE.finditer(text)]


def _ref(palette: Palette, text: str) -> RGBA:
    return _refs(palette, text)[0]


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def generate(manifest: dict, palette: Palette, out_root: Path) -> None:
    scale = int(manifest.get("scale", 2))
    walk_fps = int(manifest.get("walk_fps", 8))
    cast_path = Path(manifest["_path"]).parent / manifest["cast"]
    cast = json.loads(cast_path.read_text(encoding="utf-8"))
    chars: dict[str, dict] = cast["characters"]

    # RNG state depends on the id list order only, never on spec content:
    # every character draws its accent kit before any drawing happens.
    rng = random.Random(manifest["seed"])
    accents = {cid: _pick_accents(rng) for cid in chars}

    out_dir = str(manifest.get("out_dir", "sprites"))
    for cid, spec in chars.items():
        if spec.get("species") == "cat":
            sheet = _cat_sheet(palette, spec, accents[cid])
            fw, fh = CAT_W, CAT_H
        else:
            style = _build_style(cid, spec, palette, accents[cid])
            sheet = _human_sheet(palette, style)
            fw, fh = ART_W, ART_H
        out_png = Path(out_root) / out_dir / f"{cid}_sheet.png"
        sheet.save(out_png, scale=scale)
        sidecar = {
            "frame": [fw * scale, fh * scale],
            "cols": COLS,
            "rows": len(ROWS),
            "anims": {
                "idle_s": {"row": 0, "frames": 1, "fps": IDLE_FPS},
                "walk_s": {"row": 1, "frames": 4, "fps": walk_fps},
                "walk_n": {"row": 2, "frames": 4, "fps": walk_fps},
                "walk_e": {"row": 3, "frames": 4, "fps": walk_fps},
                "walk_w": {"row": 4, "frames": 4, "fps": walk_fps},
                "idle_n": {"row": 5, "frames": 1, "fps": IDLE_FPS},
                "idle_e": {"row": 6, "frames": 1, "fps": IDLE_FPS},
                "idle_w": {"row": 7, "frames": 1, "fps": IDLE_FPS},
            },
        }
        out_png.with_suffix(".json").write_text(
            json.dumps(sidecar, indent=2) + "\n", encoding="utf-8"
        )


def _pick_accents(rng: random.Random) -> tuple[tuple[int, int], ...]:
    """Three (side, row-offset) cloth-weave ticks, fixed per character."""
    return tuple((rng.randrange(2), 1 + rng.randrange(7)) for _ in range(3))


# ---------------------------------------------------------------------------
# shared frame plumbing
# ---------------------------------------------------------------------------

def _human_sheet(palette: Palette, s: SimpleNamespace) -> PixelCanvas:
    sheet = PixelCanvas(ART_W * COLS, ART_H * len(ROWS), palette)
    for row, (kind, direction, frame_count) in enumerate(ROWS):
        for phase in range(frame_count):
            frame = _human_frame(palette, s, kind, direction, phase)
            sheet.paste(frame, phase * ART_W, row * ART_H)
    return sheet


def _human_frame(
    palette: Palette, s: SimpleNamespace, kind: str, direction: str, phase: int
) -> PixelCanvas:
    c = PixelCanvas(ART_W, ART_H, palette)
    if direction == "w":
        _paste_mirrored(c, _human_frame(palette, s, kind, "e", phase))
        return c
    # Contact frames sink the body one px (gait low point); feet stay planted.
    dy = 1 if kind == "walk" and phase in (0, 2) else 0
    swing = 0
    if kind == "walk":
        swing = 1 if phase == 0 else (-1 if phase == 2 else 0)
    # Secondary motion (hair/skirt/tails) lags the body on passing frames.
    sway = 0
    if kind == "walk":
        sway = -1 if phase == 1 else (1 if phase == 3 else 0)
    if direction in ("s", "n"):
        s.legs_front(c, s, kind, phase)
        _torso_front(c, s, dy)
        s.torso_extra(c, s, direction, dy, phase)
        _arms_front(c, s, dy, swing)
        _head(c, s, direction, dy, sway)
    else:
        s.legs_side(c, s, kind, phase)
        _torso_side(c, s, dy)
        s.torso_extra_side(c, s, dy, phase)
        _arm_side(c, s, dy, swing)
        _head(c, s, "e", dy, sway)
    c.outline(s.outline_ramp)
    return c


def _paste_mirrored(dst: PixelCanvas, src: PixelCanvas) -> None:
    for y in range(src.height):
        for x in range(src.width):
            color = src.get(x, y)
            if color[3] != 0:
                dst.put(src.width - 1 - x, y, color)


# ---------------------------------------------------------------------------
# generic humanoid parts (parameterized by style; signature bits are hooks)
# ---------------------------------------------------------------------------

def _head(c: PixelCanvas, s: SimpleNamespace, direction: str, dy: int, sway: int) -> None:
    top = s.top + dy
    ft = top + s.face_off  # first face row (brow)
    if direction == "s":
        _face_front(c, s, ft)
        s.hair_front(c, s, top, sway)
        s.face_extra(c, s, ft)
    elif direction == "n":
        s.hair_back(c, s, top, sway)
    else:
        _face_side(c, s, ft)
        s.hair_side(c, s, top, sway)


def _face_front(c: PixelCanvas, s: SimpleNamespace, ft: int) -> None:
    """Four face rows x5..10: brow / eyes / cheeks / jaw."""
    c.rect(5, ft, 6, 4, s.skin)
    c.put(10, ft, s.skin_hi)          # brow catches the top-right light
    c.put(6, ft + 1, s.eye)
    c.put(9, ft + 1, s.eye)
    c.put(5, ft + 2, s.skin_sh)       # left cheek turns away
    c.put(10, ft + 2, s.skin_hi)      # right cheek lit
    c.put(5, ft + 3, s.skin_sh)       # jaw shade, chin narrows via outline
    c.put(10, ft + 3, s.skin_sh)


def _face_side(c: PixelCanvas, s: SimpleNamespace, ft: int) -> None:
    """Profile facing east: face block x7..10, nose bump at x11."""
    xo = s.head_fwd  # stoop pushes the whole head forward
    c.rect(7 + xo, ft, 4, 4, s.skin)
    c.put(10 + xo, ft, s.skin_hi)
    c.put(9 + xo, ft + 1, s.eye)      # single forward eye
    c.put(11 + xo, ft + 2, s.skin)    # nose
    c.put(7 + xo, ft + 3, s.skin_sh)  # jaw base in shade
    c.put(10 + xo, ft + 3, s.skin_sh)


def _torso_front(c: PixelCanvas, s: SimpleNamespace, dy: int) -> None:
    ty = s.top + s.face_off + 4 + dy  # shoulder row
    c.rect(s.tx0, ty, s.tw, s.hem - ty, s.torso)
    c.vline(s.tx0, ty, s.hem - 1, s.torso_dk)             # shaded left edge
    c.vline(s.tx0 + s.tw - 1, ty, s.hem - 1, s.torso_lt)  # lit right edge
    c.put(s.tx0 + s.tw - 2, ty, s.torso_lt)               # right shoulder cap
    # fixed per-character weave ticks (same coords every frame — no shimmer)
    for side, off in s.accents:
        ax = s.tx0 + (1 if side == 0 else s.tw - 2)
        ay = ty + 1 + off
        if ty + 1 < ay < s.hem - 1:
            c.put(ax, ay, s.torso_dk)


def _torso_side(c: PixelCanvas, s: SimpleNamespace, dy: int) -> None:
    ty = s.top + s.face_off + 4 + dy
    c.rect(s.sx0, ty, s.sw, s.hem - ty, s.torso)
    c.vline(s.sx0, ty, s.hem - 1, s.torso_dk)             # back edge shaded
    c.vline(s.sx0 + s.sw - 1, ty, s.hem - 1, s.torso_lt)  # chest edge lit
    c.put(s.sx0 + s.sw - 2, ty, s.torso_lt)


def _arms_front(c: PixelCanvas, s: SimpleNamespace, dy: int, swing: int) -> None:
    sh = s.top + s.face_off + 4
    _arm_col(c, s, s.tx0 - 1, sh + 1 + dy + swing)
    _arm_col(c, s, s.tx0 + s.tw, sh + 1 + dy - swing)


def _arm_col(c: PixelCanvas, s: SimpleNamespace, x: int, y0: int) -> None:
    if s.roll:  # rolled sleeves: cloth above, bare forearm below
        c.vline(x, y0, y0 + s.roll - 1, s.sleeve)
        c.vline(x, y0 + s.roll, y0 + s.arm_len - 1, s.skin)
    else:
        c.vline(x, y0, y0 + s.arm_len - 1, s.sleeve)
    c.put(x, y0 + s.arm_len, s.skin)  # hand


def _arm_side(c: PixelCanvas, s: SimpleNamespace, dy: int, swing: int) -> None:
    sh = s.top + s.face_off + 4
    x = s.sx0 + s.sw // 2 - 1 + swing
    y0 = sh + 1 + dy
    if s.roll:
        c.rect(x, y0, 2, s.roll, s.sleeve)
        c.rect(x, y0 + s.roll, 2, s.arm_len - s.roll, s.skin)
    else:
        c.rect(x, y0, 2, s.arm_len, s.sleeve)
    c.put(x, y0 + s.arm_len, s.skin)  # hand


def _legs_front(c: PixelCanvas, s: SimpleNamespace, kind: str, phase: int) -> None:
    lift_l = 1 if kind == "walk" and phase == 0 else 0
    lift_r = 1 if kind == "walk" and phase == 2 else 0
    for x, lift in ((s.legs_x[0], lift_l), (s.legs_x[1], lift_r)):
        c.rect(x, s.legs_top - lift, 2, 22 - s.legs_top, s.legs_col)
        c.rect(x, 22 - lift, 2, 2, s.shoes_col)


def _legs_side(c: PixelCanvas, s: SimpleNamespace, kind: str, phase: int) -> None:
    if kind == "walk" and phase == 0:
        _side_leg(c, s, 9, s.legs_col, toe=1)       # near leg forward
        _side_leg(c, s, 4, s.legs_dk, heel_up=1)    # far leg trailing
    elif kind == "walk" and phase == 2:
        _side_leg(c, s, 4, s.legs_col, heel_up=1)   # near leg trailing
        _side_leg(c, s, 9, s.legs_dk, toe=1)        # far leg forward
    else:
        _side_leg(c, s, 6, s.legs_dk)
        _side_leg(c, s, 8, s.legs_col, toe=1)


def _side_leg(
    c: PixelCanvas,
    s: SimpleNamespace,
    x: int,
    color: RGBA,
    *,
    toe: int = 0,
    heel_up: int = 0,
) -> None:
    c.rect(x, s.legs_top, 2, 22 - s.legs_top - heel_up, color)
    c.rect(x, 22 - heel_up, 2, 2, s.shoes_col)
    if toe:
        c.put(x + 2, 23, s.shoes_col)


def _hook_noop(c: PixelCanvas, s: SimpleNamespace, *args) -> None:
    pass


# ---------------------------------------------------------------------------
# style assembly
# ---------------------------------------------------------------------------

def _build_style(
    cid: str, spec: dict, palette: Palette, accents: tuple
) -> SimpleNamespace:
    height = int(spec["height_px"])
    s = SimpleNamespace(
        cid=cid,
        p=palette,
        top=ART_H - height,
        face_off=2,          # rows from hair top to brow row
        tw=8, tx0=4,         # front torso span
        sw=6, sx0=5,         # side torso span
        hem=18,              # first row below the torso block
        legs_top=18,
        legs_x=(5, 9),
        arm_len=6,
        roll=0,              # rolled-sleeve rows (0 = full sleeve)
        head_fwd=0,          # side-view stoop
        skin=_ref(palette, spec["skin"]),
        skin_sh=_ref(palette, spec["skin_shade"]),
        skin_hi=palette.ramp("amber")[2],
        eye=palette.ramp("void")[0],
        hair=_ref(palette, spec["hair"]["color"]),
        legs_col=_ref(palette, spec["outfit"]["legs"]),
        shoes_col=_ref(palette, spec["outfit"]["shoes"]),
        outline_ramp=palette.ramp("void"),
        accents=accents,
        hair_front=_hook_noop,
        hair_back=_hook_noop,
        hair_side=_hook_noop,
        face_extra=_hook_noop,
        torso_extra=_hook_noop,
        torso_extra_side=_hook_noop,
        legs_front=_legs_front,
        legs_side=_legs_side,
    )
    s.legs_dk = _one_darker(palette, s.legs_col)
    _STYLERS[cid](s, spec, palette)
    return s


def _one_darker(palette: Palette, color: RGBA) -> RGBA:
    """The ramp step below ``color`` (or itself at a ramp's floor)."""
    for ramp in palette.ramps.values():
        for i, c in enumerate(ramp.colors):
            if c == color:
                return ramp[max(0, i - 1)]
    return color


# ---------------------------------------------------------------------------
# HOCA — Dr. Deniz Aydın, 47. Lean and upright in a long earth wool coat over
# a paper shirt; short neat hair going grey at the temples; faint stubble.
# ---------------------------------------------------------------------------

def _style_hoca(s: SimpleNamespace, spec: dict, p: Palette) -> None:
    earth, paper = p.ramp("earth"), p.ramp("paper")
    s.tw, s.tx0 = 6, 5           # lean
    s.sw, s.sx0 = 6, 5
    s.torso, s.torso_dk, s.torso_lt = earth[2], earth[1], earth[3]
    s.sleeve = earth[1]
    s.shirt = paper[2]
    s.grey = _ref(p, spec["hair"]["highlight"])
    s.legs_top = 20              # the coat owns y18..19
    s.legs_x = (6, 9)
    s.outline_ramp = earth
    s.hair_front, s.hair_back, s.hair_side = _hoca_hair_f, _hoca_hair_b, _hoca_hair_s
    s.face_extra = _hoca_face
    s.torso_extra, s.torso_extra_side = _hoca_torso, _hoca_torso_side
    s.legs_front, s.legs_side = _hoca_legs_f, _hoca_legs_s


def _hoca_hair_f(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 2, s.hair)
    c.put(10, top, _ramp_at(s.p, "void", 2))   # sheen, light side
    c.put(5, top + 2, s.grey)                  # grey-flecked temples
    c.put(10, top + 2, s.grey)


def _hoca_hair_b(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 6, s.hair)
    c.put(10, top, _ramp_at(s.p, "void", 2))
    c.put(5, top + 3, s.grey)                  # temples read from behind too
    c.put(10, top + 3, s.grey)
    c.hline(6, 9, top + 5, _ramp_at(s.p, "void", 2))  # trimmed nape line


def _hoca_hair_s(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 2, s.hair)               # short crop, face open at x8..11
    c.rect(5, top + 2, 3, 3, s.hair)           # full back of head
    c.put(10, top, _ramp_at(s.p, "void", 2))
    c.put(7, top + 3, s.grey)                  # temple, over the ear
    c.put(7, top + 5, s.skin_sh)               # ear shadow at the jaw


def _hoca_face(c: PixelCanvas, s: SimpleNamespace, ft: int) -> None:
    c.hline(6, 9, ft + 3, s.skin_sh)           # faint stubble across the jaw


def _hoca_torso(
    c: PixelCanvas, s: SimpleNamespace, direction: str, dy: int, phase: int
) -> None:
    ty = s.top + 6 + dy
    if direction == "s":
        c.vline(7, ty, ty + 3, s.shirt)        # coat open on the shirt
        c.vline(8, ty, ty + 3, s.shirt)
        c.put(8, ty + 4, s.torso_dk)           # coat closes; button track
        c.put(8, ty + 6, _ramp_at(s.p, "earth", 0))
        c.put(8, ty + 8, _ramp_at(s.p, "earth", 0))
    else:
        c.vline(8, ty + 1, s.hem - 1, s.torso_dk)  # back seam


def _hoca_torso_side(c: PixelCanvas, s: SimpleNamespace, dy: int, phase: int) -> None:
    ty = s.top + 6 + dy
    c.put(s.sx0 + s.sw - 1, ty, s.shirt)       # collar point at the throat


def _hoca_legs_f(c: PixelCanvas, s: SimpleNamespace, kind: str, phase: int) -> None:
    _legs_front(c, s, kind, phase)
    earth = s.p.ramp("earth")
    # long coat skirt: flares one px past the torso, hem swings when walking
    sway = 0
    if kind == "walk":
        sway = -1 if phase == 1 else (1 if phase == 3 else 0)
    c.rect(4, 18, 8, 2, earth[2])
    c.vline(4, 18, 19, earth[1])
    c.vline(11, 18, 19, earth[3])
    c.put(8, 18, earth[1])                     # coat split
    c.put(8, 19, earth[1])
    if sway:                                   # hem corner kicks on passing
        c.put(4 if sway < 0 else 11, 20, earth[1])


def _hoca_legs_s(c: PixelCanvas, s: SimpleNamespace, kind: str, phase: int) -> None:
    _legs_side(c, s, kind, phase)
    earth = s.p.ramp("earth")
    c.rect(4, 18, 8, 2, earth[2])              # coat skirt in profile
    c.vline(4, 18, 19, earth[1])
    c.vline(11, 18, 19, earth[3])
    if kind == "walk" and phase in (0, 2):     # hem swings open mid-stride
        c.put(3, 19, earth[1])


# ---------------------------------------------------------------------------
# FADIME — baker, 55. Solid; paper yemeni headscarf knotted at the side; rose
# dress under a flour-dusted paper apron; rose skirt down to earth shoes.
# ---------------------------------------------------------------------------

def _style_fadime(s: SimpleNamespace, spec: dict, p: Palette) -> None:
    rose, paper = p.ramp("rose"), p.ramp("paper")
    s.tw, s.tx0 = 8, 4
    s.sw, s.sx0 = 7, 5
    s.torso, s.torso_dk, s.torso_lt = rose[1], rose[0], rose[2]
    s.sleeve = rose[0]
    s.roll = 3                    # capable forearms
    s.arm_len = 5
    s.hem = 17
    s.scarf, s.scarf_sh = paper[2], paper[1]
    s.hair_front, s.hair_back, s.hair_side = _fadime_scarf_f, _fadime_scarf_b, _fadime_scarf_s
    s.torso_extra, s.torso_extra_side = _fadime_torso, _fadime_torso_side
    s.legs_front, s.legs_side = _fadime_legs_f, _fadime_legs_s


def _fadime_scarf_f(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 2, s.scarf)              # crown
    c.put(5, top, s.scarf_sh)
    c.vline(5, top + 2, top + 4, s.scarf_sh)   # scarf frames the face
    c.vline(10, top + 2, top + 4, s.scarf)
    c.put(5, top + 5, s.scarf_sh)              # wrap tucks at the jaw corners
    c.put(10, top + 5, s.scarf)
    c.rect(4, top + 3, 1, 2, s.scarf)          # side knot against the cheek
    c.put(4, top + 5, s.scarf_sh)              # knot tail
    c.put(3, top + 4, s.scarf_sh)


def _fadime_scarf_b(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 6, s.scarf)
    c.put(5, top, s.scarf_sh)
    c.vline(5, top + 1, top + 5, s.scarf_sh)   # shaded left of the wrap
    c.hline(6, 9, top + 3, s.scarf_sh)         # fold line across the back
    c.rect(10, top + 4, 2, 2, s.scarf)         # knot shows past the head
    c.put(11, top + 6, s.scarf_sh)


def _fadime_scarf_s(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 2, s.scarf)
    c.put(5, top, s.scarf_sh)
    c.rect(5, top + 2, 3, 3, s.scarf)          # covers the back of the head
    c.vline(5, top + 2, top + 4, s.scarf_sh)   # face stays open from x8 forward
    c.rect(4, top + 3, 1, 2, s.scarf_sh)       # knot at the nape
    c.put(4, top + 5, s.scarf_sh)              # its tail


def _fadime_torso(
    c: PixelCanvas, s: SimpleNamespace, direction: str, dy: int, phase: int
) -> None:
    ty = s.top + 6 + dy
    if direction == "s":
        paper = s.p.ramp("paper")
        # apron: narrow bib over the chest, wider panel from the waist —
        # the rose dress must show at the shoulders or she reads as a nun
        c.rect(7, ty + 2, 2, 2, paper[2])                # bib
        c.rect(6, ty + 4, 4, s.hem - ty - 4, paper[2])   # waist panel
        c.vline(6, ty + 4, s.hem - 1, paper[1])
        c.put(8, ty + 6, paper[1])                       # flour-creased fold
    else:
        c.hline(5, 10, ty + 5, s.torso_dk)               # apron ties, bow knot
        c.put(7, ty + 6, s.torso_dk)
        c.put(8, ty + 6, s.torso_dk)


def _fadime_torso_side(c: PixelCanvas, s: SimpleNamespace, dy: int, phase: int) -> None:
    ty = s.top + 6 + dy
    paper = s.p.ramp("paper")
    c.vline(s.sx0 + s.sw - 1, ty + 3, s.hem - 1, paper[2])  # apron front edge
    c.vline(s.sx0 + s.sw - 2, ty + 4, s.hem - 1, paper[2])


def _fadime_legs_f(c: PixelCanvas, s: SimpleNamespace, kind: str, phase: int) -> None:
    rose, paper = s.p.ramp("rose"), s.p.ramp("paper")
    sway = 0
    if kind == "walk":
        sway = -1 if phase == 1 else (1 if phase == 3 else 0)
    # rose skirt, widening to the hem; apron falls over its front
    c.rect(4, 17, 8, 2, s.legs_col)
    c.rect(3, 19, 10, 3, s.legs_col)
    c.vline(3, 19, 21, _one_darker(s.p, s.legs_col))
    c.vline(12, 19, 21, rose[1])                     # lit right fall
    c.rect(6, 17, 4, 4, paper[2])                    # apron skirt panel
    c.vline(6, 17, 20, paper[1])
    c.hline(6, 9, 21, s.legs_col)                    # skirt hem below the apron
    if sway:                                         # hem swishes on passing
        c.put(3 if sway < 0 else 12, 18, s.legs_col)
    # shoes peeking out, stepping alternately
    lift_l = 1 if kind == "walk" and phase == 0 else 0
    lift_r = 1 if kind == "walk" and phase == 2 else 0
    c.rect(5, 22 - lift_l, 2, 2, s.shoes_col)
    c.rect(9, 22 - lift_r, 2, 2, s.shoes_col)


def _fadime_legs_s(c: PixelCanvas, s: SimpleNamespace, kind: str, phase: int) -> None:
    rose, paper = s.p.ramp("rose"), s.p.ramp("paper")
    stride = 1 if kind == "walk" and phase in (0, 2) else 0
    # skirt triangle: nips at the waist, kicks at the hem when striding
    c.rect(5, 17, 7, 2, s.legs_col)
    c.rect(4, 19, 9 + stride, 3, s.legs_col)
    c.vline(4, 19, 21, _one_darker(s.p, s.legs_col))
    c.vline(12 + stride, 19, 21, rose[1])
    c.vline(11, 17, 20, paper[2])                    # apron front fall
    c.vline(10, 18, 20, paper[1])
    if kind == "walk" and phase == 0:
        c.rect(9, 22, 2, 2, s.shoes_col)
        c.put(11, 23, s.shoes_col)
        c.rect(5, 22, 2, 2, s.shoes_col)
    elif kind == "walk" and phase == 2:
        c.rect(5, 22, 2, 2, s.shoes_col)
        c.rect(9, 22, 2, 2, s.shoes_col)
        c.put(4, 23, s.shoes_col)
    else:
        c.rect(6, 22, 2, 2, s.shoes_col)
        c.rect(8, 22, 2, 2, s.shoes_col)
        c.put(10, 23, s.shoes_col)


# ---------------------------------------------------------------------------
# MUSA — grocer, 45. Stocky; thick moustache; earth knit vest over a paper
# shirt with the sleeves rolled; stone trousers.
# ---------------------------------------------------------------------------

def _style_musa(s: SimpleNamespace, spec: dict, p: Palette) -> None:
    earth, paper = p.ramp("earth"), p.ramp("paper")
    s.tw, s.tx0 = 8, 4
    s.sw, s.sx0 = 7, 5
    s.torso, s.torso_dk, s.torso_lt = paper[1], paper[0], paper[2]  # shirt base
    s.sleeve = paper[1]
    s.roll = 4                   # rolled, but still mostly sleeve
    s.legs_x = (5, 9)
    s.outline_ramp = earth
    s.hair_front, s.hair_back, s.hair_side = _musa_hair_f, _musa_hair_b, _musa_hair_s
    s.face_extra = _musa_face
    s.torso_extra, s.torso_extra_side = _musa_torso, _musa_torso_side


def _musa_hair_f(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 2, s.hair)
    c.put(10, top, _ramp_at(s.p, "void", 2))


def _musa_hair_b(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 6, s.hair)
    c.put(10, top, _ramp_at(s.p, "void", 2))
    c.put(5, top + 4, _ramp_at(s.p, "void", 2))


def _musa_hair_s(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 2, s.hair)
    c.rect(5, top + 2, 3, 3, s.hair)           # full back of head
    c.put(10, top, _ramp_at(s.p, "void", 2))
    c.put(10, top + 4, s.hair)                 # the moustache leads in profile
    c.put(11, top + 4, s.hair)


def _musa_face(c: PixelCanvas, s: SimpleNamespace, ft: int) -> None:
    c.hline(6, 9, ft + 2, s.hair)              # the moustache reads first
    c.put(5, ft + 3, s.hair)                   # tips droop past the jaw
    c.put(10, ft + 3, s.hair)


def _musa_torso(
    c: PixelCanvas, s: SimpleNamespace, direction: str, dy: int, phase: int
) -> None:
    ty = s.top + 6 + dy
    earth = s.p.ramp("earth")
    # knit vest over the shirt, open in a V
    c.rect(4, ty + 2, 8, s.hem - ty - 2, earth[1])
    c.vline(4, ty + 2, s.hem - 1, earth[0])
    c.vline(11, ty + 2, s.hem - 1, earth[2])
    if direction == "s":
        c.put(7, ty + 2, s.torso)              # shirt in the vest's V-neck
        c.put(8, ty + 2, s.torso)
        c.put(6, ty + 5, earth[0])             # knit rib ticks
        c.put(9, ty + 7, earth[0])
    else:
        c.put(7, ty + 4, earth[0])             # back rib
        c.put(8, ty + 8, earth[0])


def _musa_torso_side(c: PixelCanvas, s: SimpleNamespace, dy: int, phase: int) -> None:
    ty = s.top + 6 + dy
    earth = s.p.ramp("earth")
    c.rect(s.sx0, ty + 2, s.sw - 1, s.hem - ty - 2, earth[1])
    c.vline(s.sx0, ty + 2, s.hem - 1, earth[0])
    c.vline(s.sx0 + s.sw - 2, ty + 2, s.hem - 1, earth[2])
    c.vline(s.sx0 + s.sw - 1, ty + 1, s.hem - 1, s.torso)  # shirt at the chest


# ---------------------------------------------------------------------------
# ŞÜKRÜ — retired teacher, 74. Thin, slightly stooped; white hair combed
# back off a high forehead; dark rose cardigan buttoned over a paper shirt.
# ---------------------------------------------------------------------------

def _style_sukru(s: SimpleNamespace, spec: dict, p: Palette) -> None:
    rose = p.ramp("rose")
    s.tw, s.tx0 = 6, 5
    s.sw, s.sx0 = 6, 5
    s.torso, s.torso_dk, s.torso_lt = rose[0], rose[0], rose[1]
    s.sleeve = rose[0]
    s.legs_x = (6, 9)
    s.head_fwd = 1               # the stoop, seen from the side
    s.hair_front, s.hair_back, s.hair_side = _sukru_hair_f, _sukru_hair_b, _sukru_hair_s
    s.torso_extra, s.torso_extra_side = _sukru_torso, _sukru_torso_side


def _sukru_hair_f(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    # combed back: hairline sits high, forehead open
    c.hline(5, 10, top, s.hair)
    c.hline(5, 10, top + 1, s.skin)            # high forehead
    c.put(5, top + 1, s.hair)                  # hair holds the temples
    c.put(10, top + 1, s.hair)
    c.put(10, top, _ramp_at(s.p, "paper", 2))  # white catches the light


def _sukru_hair_b(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 5, s.hair)               # thins before the collar
    c.put(10, top, _ramp_at(s.p, "paper", 2))
    c.hline(6, 9, top + 5, s.skin)             # bare neck below the trim line
    c.put(7, top + 2, _ramp_at(s.p, "stone", 2))  # comb tracks, sparse
    c.put(9, top + 3, _ramp_at(s.p, "stone", 2))
    c.put(5, top + 4, _ramp_at(s.p, "stone", 2))


def _sukru_hair_s(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    xo = s.head_fwd
    c.hline(5 + xo, 10 + xo, top, s.hair)      # swept straight back
    c.rect(5 + xo, top + 1, 3, 3, s.hair)      # neck shows beneath
    c.put(10 + xo, top, _ramp_at(s.p, "paper", 2))
    c.put(5 + xo, top + 4, s.hair)             # nape wisp
    c.put(4, top + 6, s.torso)                 # rounded upper back
    c.put(5, top + 5, s.torso)


def _sukru_torso(
    c: PixelCanvas, s: SimpleNamespace, direction: str, dy: int, phase: int
) -> None:
    ty = s.top + 6 + dy
    if direction == "s":
        paper, rose = s.p.ramp("paper"), s.p.ramp("rose")
        c.put(7, ty, paper[1])                 # shirt at the collar V
        c.put(8, ty, paper[1])
        c.put(8, ty + 1, paper[1])
        c.put(8, ty + 3, rose[2])              # buttons down the placket
        c.put(8, ty + 5, rose[2])
        c.put(8, ty + 7, rose[2])
        # shoulders sit a little high on a thin frame
        c.put(5, ty, s.torso)
        c.put(10, ty, s.torso_lt)


def _sukru_torso_side(c: PixelCanvas, s: SimpleNamespace, dy: int, phase: int) -> None:
    ty = s.top + 6 + dy
    c.put(s.sx0 + s.sw - 1, ty + 1, _ramp_at(s.p, "paper", 1))  # shirt point
    c.put(s.sx0 + 1, ty, s.torso)              # hunched back line


# ---------------------------------------------------------------------------
# ELİF — schoolgirl, 11. Small; high ponytail with a rose tie; teal school
# cardigan with a paper collar; stone skirt, ship socks, and a backpack that
# shows when she walks away.
# ---------------------------------------------------------------------------

def _style_elif(s: SimpleNamespace, spec: dict, p: Palette) -> None:
    ship, paper = p.ramp("ship"), p.ramp("paper")
    s.face_off = 4               # ponytail owns the top two rows
    s.tw, s.tx0 = 6, 5
    s.sw, s.sx0 = 5, 6
    s.torso, s.torso_dk, s.torso_lt = ship[2], ship[1], ship[3]
    s.sleeve = ship[1]
    s.arm_len = 4
    s.hem = 17
    s.socks = _refs(p, spec["outfit"]["legs"])[1]
    s.outline_ramp = ship
    s.hair_front, s.hair_back, s.hair_side = _elif_hair_f, _elif_hair_b, _elif_hair_s
    s.torso_extra, s.torso_extra_side = _elif_torso, _elif_torso_side
    s.legs_front, s.legs_side = _elif_legs_f, _elif_legs_s


def _elif_hair_f(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    rose, void = s.p.ramp("rose"), s.p.ramp("void")
    c.rect(5, top + 2, 6, 2, s.hair)           # hair cap
    c.put(9, top + 2, void[3])                 # sheen, light side
    c.put(10, top + 2, void[3])
    c.put(5, top + 4, s.hair)                  # fringe corners
    c.put(10, top + 4, s.hair)
    # high ponytail: tuft above the crown, pink tie where it gathers
    c.put(8, top, s.hair)
    c.put(9 + max(sway, 0), top, s.hair)       # tip flips with the step
    c.rect(8, top + 1, 2, 1, s.hair)
    c.put(8, top + 2, rose[2])                 # the tie sits on the hair
    c.put(9, top + 2, rose[2])


def _elif_hair_b(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    rose, void = s.p.ramp("rose"), s.p.ramp("void")
    c.rect(5, top + 2, 6, 5, s.hair)           # hair to the collar
    c.put(5, top + 6, s.skin)                  # neck shows at the corners
    c.put(10, top + 6, s.skin)
    c.put(10, top + 2, void[3])
    c.put(8, top, s.hair)                      # tuft over the crown
    c.put(9 + max(sway, 0), top, s.hair)
    c.rect(8, top + 1, 2, 1, s.hair)
    c.put(8, top + 2, rose[2])                 # tie
    c.put(9, top + 2, rose[2])
    c.vline(8, top + 3, top + 6, void[3])      # tail falls bright over the hair
    c.put(8 + sway, top + 7, void[3])          # its end swings as she walks


def _elif_hair_s(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    rose = s.p.ramp("rose")
    c.rect(5, top + 2, 6, 2, s.hair)
    c.rect(5, top + 4, 3, 3, s.hair)           # back of head
    c.put(10, top + 2, _ramp_at(s.p, "void", 3))
    c.rect(5, top, 2, 2, s.hair)               # ponytail leans back off the crown
    c.put(4 + sway, top + 1, s.hair)           # tip swings as she walks
    c.put(4 + sway, top + 2, s.hair)
    c.put(6, top + 2, rose[2])                 # tie


def _elif_torso(
    c: PixelCanvas, s: SimpleNamespace, direction: str, dy: int, phase: int
) -> None:
    ty = s.top + s.face_off + 4 + dy
    if direction == "s":
        paper = s.p.ramp("paper")
        c.put(7, ty, paper[2])                 # collar points
        c.put(8, ty, paper[2])
        c.put(8, ty + 1, s.torso_dk)           # cardigan button
    else:
        earth = s.p.ramp("earth")
        # the backpack — worn every day of Act 1
        c.rect(6, ty, 4, 4, earth[1])
        c.vline(6, ty, ty + 3, earth[0])
        c.vline(9, ty, ty + 3, earth[2])
        c.hline(6, 9, ty, earth[2])            # top flap lit
        c.put(8, ty + 2, earth[0])             # buckle
        c.put(5, ty, earth[0])                 # straps over the shoulders
        c.put(10, ty, earth[0])


def _elif_torso_side(c: PixelCanvas, s: SimpleNamespace, dy: int, phase: int) -> None:
    ty = s.top + s.face_off + 4 + dy
    earth = s.p.ramp("earth")
    c.rect(4, ty, 2, 3, earth[1])              # backpack in profile
    c.vline(4, ty, ty + 2, earth[0])
    c.put(5, ty, earth[2])
    c.put(6, ty + 1, earth[0])                 # strap


def _elif_legs_f(c: PixelCanvas, s: SimpleNamespace, kind: str, phase: int) -> None:
    lift_l = 1 if kind == "walk" and phase == 0 else 0
    lift_r = 1 if kind == "walk" and phase == 2 else 0
    # skirt flares wide of the cardigan — the one crisp angle she has
    c.rect(5, 17, 6, 1, s.legs_col)
    c.rect(4, 18, 8, 1, s.legs_col)
    c.put(4, 18, _one_darker(s.p, s.legs_col))
    c.hline(9, 11, 18, _ramp_at(s.p, "stone", 2))  # hem catches the light
    for x, lift in ((5, lift_l), (9, lift_r)):
        c.rect(x, 19 - lift, 2, 2, s.skin)
        c.put(x, 21 - lift, s.socks)
        c.put(x + 1, 21 - lift, s.socks)
        c.rect(x, 22 - lift, 2, 2, s.shoes_col)


def _elif_legs_s(c: PixelCanvas, s: SimpleNamespace, kind: str, phase: int) -> None:
    stride = 1 if kind == "walk" and phase in (0, 2) else 0
    c.rect(6, 17, 5, 1, s.legs_col)
    c.rect(5, 18, 7 + stride, 1, s.legs_col)
    c.put(5, 18, _one_darker(s.p, s.legs_col))
    if kind == "walk" and phase == 0:
        legs = ((9, s.skin, 1), (5, s.skin_sh, 0))
    elif kind == "walk" and phase == 2:
        legs = ((5, s.skin, 0), (9, s.skin_sh, 1))
    else:
        legs = ((6, s.skin_sh, 0), (8, s.skin, 1))
    for x, col, toe in legs:
        c.rect(x, 19, 2, 2, col)
        c.put(x, 21, s.socks)
        c.put(x + 1, 21, s.socks)
        c.rect(x, 22, 2, 2, s.shoes_col)
        if toe:
            c.put(x + 2, 23, s.shoes_col)


# ---------------------------------------------------------------------------
# KADİR — tea house owner, 58. Barrel-chested; balding crown with grey sides
# and a grey moustache; dark vest over a paper shirt, stone waist apron.
# ---------------------------------------------------------------------------

def _style_kadir(s: SimpleNamespace, spec: dict, p: Palette) -> None:
    paper = p.ramp("paper")
    s.tw, s.tx0 = 10, 3          # barrel chest
    s.sw, s.sx0 = 8, 4
    s.torso, s.torso_dk, s.torso_lt = paper[2], paper[1], paper[2]  # shirt base
    s.sleeve = paper[1]
    s.roll = 4                   # rolled, forearms bare only below the elbow
    s.legs_top = 20              # the apron owns y13..19
    s.legs_x = (5, 9)
    s.grey = _ramp_at(p, "stone", 2)
    s.hair_front, s.hair_back, s.hair_side = _kadir_hair_f, _kadir_hair_b, _kadir_hair_s
    s.face_extra = _kadir_face
    s.torso_extra, s.torso_extra_side = _kadir_torso, _kadir_torso_side


def _kadir_hair_f(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.hline(6, 9, top, s.skin)                 # bald crown
    c.put(9, top, s.skin_hi)                   # scalp shine, light side
    c.put(5, top, s.grey)                      # grey wings
    c.put(10, top, s.grey)
    c.rect(5, top + 1, 1, 2, s.grey)
    c.rect(10, top + 1, 1, 2, s.grey)
    c.hline(6, 9, top + 1, s.skin)


def _kadir_hair_b(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(6, top, 4, 3, s.skin)               # crown from behind
    c.put(9, top, s.skin_hi)
    c.vline(5, top, top + 4, s.grey)           # horseshoe of grey
    c.vline(10, top, top + 4, s.grey)
    c.rect(5, top + 3, 6, 2, s.grey)
    c.hline(6, 9, top + 5, _ramp_at(s.p, "stone", 1))  # nape shadow


def _kadir_hair_s(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.hline(6, 10, top, s.skin)                # bald dome in profile
    c.put(10, top, s.skin_hi)
    c.put(5, top, s.grey)
    c.rect(5, top + 1, 2, 4, s.grey)           # grey over the ear
    c.put(7, top + 2, s.grey)
    c.put(10, top + 4, s.grey)                 # moustache leads the profile
    c.put(11, top + 4, s.grey)


def _kadir_face(c: PixelCanvas, s: SimpleNamespace, ft: int) -> None:
    c.hline(6, 9, ft + 2, s.grey)              # the moustache hides the smile
    # jaw stays bare skin — with drooping tips he read as fully bearded


def _kadir_torso(
    c: PixelCanvas, s: SimpleNamespace, direction: str, dy: int, phase: int
) -> None:
    ty = s.top + 6 + dy
    void, stone = s.p.ramp("void"), s.p.ramp("stone")
    # vest over the shirt (shirt shows at shoulders + a V at the chest)
    c.rect(4, ty + 1, 8, 6, void[2])
    c.vline(4, ty + 1, ty + 6, void[1])
    c.vline(11, ty + 1, ty + 6, void[3])
    if direction == "s":
        c.put(7, ty + 1, s.torso)              # shirt V
        c.put(8, ty + 1, s.torso)
        c.put(8, ty + 2, s.torso)
        c.put(8, ty + 4, void[3])              # vest buttons
        c.put(8, ty + 6, void[3])
    # stone waist apron: steps in from the vest so the silhouette breaks
    c.rect(5, 13, 6, 7, stone[0])
    c.vline(10, 13, 19, stone[1])              # lit right fall
    c.hline(5, 10, 13, stone[1])               # waist fold catches light
    if direction == "n":
        c.put(7, 12, stone[1])                 # tie knot at the back
        c.put(8, 12, stone[1])


def _kadir_torso_side(c: PixelCanvas, s: SimpleNamespace, dy: int, phase: int) -> None:
    ty = s.top + 6 + dy
    void, stone = s.p.ramp("void"), s.p.ramp("stone")
    c.rect(4, ty + 1, 7, 6, void[2])
    c.vline(4, ty + 1, ty + 6, void[1])
    c.vline(10, ty + 1, ty + 6, void[3])
    c.put(11, ty + 1, s.torso)                 # shirt at the throat
    c.put(11, ty + 2, s.torso)
    c.rect(4, 13, 7, 7, stone[0])
    c.vline(10, 13, 19, stone[1])
    c.hline(4, 10, 13, stone[1])
    c.put(12, ty + 5, void[2])                 # the chest leads the walk


# ---------------------------------------------------------------------------
# İSMET — dolmuş driver, 48. Wiry; earth flat cap (kasket) pulled low; ship
# work jacket half-zipped over a paper shirt.
# ---------------------------------------------------------------------------

def _style_ismet(s: SimpleNamespace, spec: dict, p: Palette) -> None:
    ship = p.ramp("ship")
    s.tw, s.tx0 = 6, 5
    s.sw, s.sx0 = 6, 5
    s.torso, s.torso_dk, s.torso_lt = ship[1], ship[0], ship[2]
    s.sleeve = ship[0]
    s.legs_x = (6, 9)
    s.cap = _ramp_at(p, "earth", 1)
    s.cap_brim = _ramp_at(p, "earth", 0)
    s.cap_lt = _ramp_at(p, "earth", 2)
    s.outline_ramp = ship
    s.hair_front, s.hair_back, s.hair_side = _ismet_cap_f, _ismet_cap_b, _ismet_cap_s
    s.face_extra = _ismet_face
    s.torso_extra, s.torso_extra_side = _ismet_torso, _ismet_torso_side


def _ismet_cap_f(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.hline(5, 10, top, s.cap)                 # crown
    c.put(10, top, s.cap_lt)
    c.hline(4, 11, top + 1, s.cap)             # cap sits wider than the head
    c.put(4, top + 1, s.cap_brim)
    c.put(11, top + 1, s.cap_lt)
    c.hline(5, 10, top + 2, s.cap_brim)        # brim shades the brow


def _ismet_cap_b(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.hline(5, 10, top, s.cap)
    c.put(10, top, s.cap_lt)
    c.hline(4, 11, top + 1, s.cap)
    c.put(4, top + 1, s.cap_brim)
    c.rect(5, top + 2, 6, 2, s.cap)            # crown falls to the band
    c.hline(5, 10, top + 3, s.cap_brim)        # band
    c.rect(5, top + 4, 6, 2, s.hair)           # hair at the nape


def _ismet_cap_s(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.hline(5, 10, top, s.cap)
    c.put(10, top, s.cap_lt)
    c.hline(4, 12, top + 1, s.cap)             # brim juts over the eye
    c.put(12, top + 1, s.cap_brim)
    c.put(4, top + 1, s.cap_brim)
    c.put(5, top + 2, s.hair)                  # hair at the ear
    c.rect(5, top + 3, 2, 2, s.hair)


def _ismet_face(c: PixelCanvas, s: SimpleNamespace, ft: int) -> None:
    # years of switchback sun: cheeks shaded under the brim, eyes in its dark
    c.put(5, ft + 1, s.skin_sh)
    c.put(10, ft + 1, s.skin_sh)


def _ismet_torso(
    c: PixelCanvas, s: SimpleNamespace, direction: str, dy: int, phase: int
) -> None:
    ty = s.top + 6 + dy
    if direction == "s":
        paper, ship = s.p.ramp("paper"), s.p.ramp("ship")
        c.put(7, ty + 1, paper[1])             # shirt in the half-zip V
        c.put(8, ty + 1, paper[1])
        c.put(8, ty + 2, ship[3])              # zip pull
        c.vline(8, ty + 3, s.hem - 2, ship[2])  # zip track, catching light
        c.put(5, ty, s.torso_dk)               # collar
        c.put(10, ty, s.torso_lt)


def _ismet_torso_side(c: PixelCanvas, s: SimpleNamespace, dy: int, phase: int) -> None:
    ty = s.top + 6 + dy
    c.put(s.sx0 + s.sw - 1, ty + 1, _ramp_at(s.p, "paper", 1))  # shirt at collar


# ---------------------------------------------------------------------------
# METİN — observatory night operator, 58. Heavy-set and deliberate; grey
# brush cut, grey stubble; ship work shirt held by earth suspenders.
# ---------------------------------------------------------------------------

def _style_metin(s: SimpleNamespace, spec: dict, p: Palette) -> None:
    ship = p.ramp("ship")
    s.tw, s.tx0 = 8, 4
    s.sw, s.sx0 = 8, 4
    s.torso, s.torso_dk, s.torso_lt = ship[2], ship[1], ship[3]
    s.sleeve = ship[1]
    s.legs_x = (5, 9)
    s.grey = _ramp_at(p, "stone", 2)
    s.outline_ramp = ship
    s.hair_front, s.hair_back, s.hair_side = _metin_hair_f, _metin_hair_b, _metin_hair_s
    s.face_extra = _metin_face
    s.torso_extra, s.torso_extra_side = _metin_torso, _metin_torso_side


def _metin_hair_f(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.hline(5, 10, top, s.grey)                # flat brush-cut line
    c.hline(5, 10, top + 1, s.grey)
    c.put(10, top, _ramp_at(s.p, "stone", 3))
    c.put(5, top + 1, _ramp_at(s.p, "stone", 1))


def _metin_hair_b(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 6, s.grey)
    c.put(10, top, _ramp_at(s.p, "stone", 3))
    c.hline(5, 10, top + 4, _ramp_at(s.p, "stone", 1))  # clippered nape
    c.hline(6, 9, top + 5, _ramp_at(s.p, "stone", 1))


def _metin_hair_s(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.hline(5, 10, top, s.grey)
    c.hline(5, 9, top + 1, s.grey)
    c.put(10, top, _ramp_at(s.p, "stone", 3))
    c.rect(5, top + 2, 2, 3, s.grey)
    c.put(5, top + 4, _ramp_at(s.p, "stone", 1))


def _metin_face(c: PixelCanvas, s: SimpleNamespace, ft: int) -> None:
    c.put(6, ft + 3, _ramp_at(s.p, "stone", 1))  # grey stubble jaw pixels
    c.put(8, ft + 3, _ramp_at(s.p, "stone", 1))


def _metin_torso(
    c: PixelCanvas, s: SimpleNamespace, direction: str, dy: int, phase: int
) -> None:
    ty = s.top + 6 + dy
    earth, ship = s.p.ramp("earth"), s.p.ramp("ship")
    # the belly: torso swells a px each side below the chest
    c.vline(3, ty + 4, s.hem - 1, s.torso_dk)
    c.vline(12, ty + 4, s.hem - 1, s.torso_lt)
    c.vline(4, ty + 4, s.hem - 1, s.torso)     # refill over the old edges
    c.vline(11, ty + 4, s.hem - 1, s.torso)
    # high trouser waistband — suspenders need something to hold up
    c.hline(4, 11, s.hem - 1, ship[1])
    c.hline(4, 11, s.hem - 2, ship[0])
    # suspenders run inboard, over the chest, down to their clips
    c.vline(6, ty, s.hem - 2, earth[1])
    c.vline(9, ty, s.hem - 2, earth[1])
    c.put(6, s.hem - 1, earth[0])              # clips on the waistband
    c.put(9, s.hem - 1, earth[0])


def _metin_torso_side(c: PixelCanvas, s: SimpleNamespace, dy: int, phase: int) -> None:
    ty = s.top + 6 + dy
    earth, ship = s.p.ramp("earth"), s.p.ramp("ship")
    c.vline(12, ty + 4, s.hem - 1, s.torso_lt)  # belly leads
    c.vline(3, ty + 5, s.hem - 1, s.torso_dk)
    c.hline(4, 11, s.hem - 1, ship[1])         # waistband wraps around
    c.vline(7, ty, s.hem - 2, earth[1])        # one suspender visible
    c.put(7, s.hem - 1, earth[0])              # its clip


# ---------------------------------------------------------------------------
# EBRU — PhD student, 27. Quick and light; low earth ponytail over one
# shoulder; oversized rose sweater, sleeves pushed up; jeans, rose sneakers.
# ---------------------------------------------------------------------------

def _style_ebru(s: SimpleNamespace, spec: dict, p: Palette) -> None:
    rose = p.ramp("rose")
    s.tw, s.tx0 = 8, 4           # the sweater is oversized, she is not
    s.sw, s.sx0 = 6, 5
    s.torso, s.torso_dk, s.torso_lt = rose[1], rose[0], rose[2]
    s.sleeve = rose[0]
    s.roll = 3
    s.arm_len = 5
    s.hem = 16                   # short sweater, long legs
    s.legs_top = 16
    s.legs_x = (6, 9)
    s.hair_front, s.hair_back, s.hair_side = _ebru_hair_f, _ebru_hair_b, _ebru_hair_s
    s.torso_extra, s.torso_extra_side = _ebru_torso, _ebru_torso_side
    s.legs_front = _ebru_legs_f
    s.legs_side = _ebru_legs_s


def _ebru_hair_f(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 2, s.hair)
    c.put(10, top, _ramp_at(s.p, "earth", 1))  # sheen
    c.put(5, top + 2, s.hair)                  # loose strand at the temple
    c.put(5, top + 3, s.hair)
    # low ponytail slung over one shoulder — beside the face, never on it
    c.vline(11, top + 3, top + 5, s.hair)
    c.rect(10, top + 6 + max(sway, 0), 2, 2, s.hair)  # tail tip swings
    c.put(11, top + 4, _ramp_at(s.p, "earth", 1))


def _ebru_hair_b(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 6, s.hair)
    c.put(10, top, _ramp_at(s.p, "earth", 1))
    # gathered low, tail slipping over the right shoulder
    c.put(9, top + 5, _ramp_at(s.p, "earth", 1))
    c.vline(10, top + 6, top + 7, s.hair)
    c.put(10 + max(sway, 0), top + 8, s.hair)


def _ebru_hair_s(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(5, top, 6, 2, s.hair)
    c.rect(5, top + 2, 2, 3, s.hair)
    c.put(10, top, _ramp_at(s.p, "earth", 1))
    c.put(6, top + 1, _ramp_at(s.p, "earth", 1))
    # ponytail hangs at the front of her shoulder, swinging with the stride
    c.vline(4, top + 3, top + 5, s.hair)
    c.put(4 + sway, top + 6, s.hair)
    c.put(4 + sway, top + 7, s.hair)


def _ebru_torso(
    c: PixelCanvas, s: SimpleNamespace, direction: str, dy: int, phase: int
) -> None:
    ty = s.top + 6 + dy
    if direction == "s":
        paper = s.p.ramp("paper")
        c.put(7, ty, paper[2])                 # collar peeking out
        c.put(8, ty, paper[2])
        c.hline(5, 9, s.hem - 1, s.torso_dk)   # heavy ribbed hem
    else:
        c.hline(5, 10, s.hem - 1, s.torso_dk)


def _ebru_torso_side(c: PixelCanvas, s: SimpleNamespace, dy: int, phase: int) -> None:
    ty = s.top + 6 + dy
    c.put(s.sx0 + s.sw - 1, ty, _ramp_at(s.p, "paper", 2))
    c.hline(s.sx0, s.sx0 + s.sw - 1, s.hem - 1, s.torso_dk)


def _ebru_legs_f(c: PixelCanvas, s: SimpleNamespace, kind: str, phase: int) -> None:
    paper = s.p.ramp("paper")
    lift_l = 1 if kind == "walk" and phase == 0 else 0
    lift_r = 1 if kind == "walk" and phase == 2 else 0
    for x, lift in ((s.legs_x[0], lift_l), (s.legs_x[1], lift_r)):
        c.rect(x, s.legs_top - lift, 2, 22 - s.legs_top, s.legs_col)
        c.put(x, 22 - lift, s.shoes_col)       # rose sneakers
        c.put(x + 1, 22 - lift, s.shoes_col)
        c.put(x, 23 - lift, paper[2])          # white soles
        c.put(x + 1, 23 - lift, paper[2])


def _ebru_legs_s(c: PixelCanvas, s: SimpleNamespace, kind: str, phase: int) -> None:
    paper = s.p.ramp("paper")
    if kind == "walk" and phase == 0:
        legs = ((9, s.legs_col, 1), (4, s.legs_dk, 0))
    elif kind == "walk" and phase == 2:
        legs = ((4, s.legs_col, 0), (9, s.legs_dk, 1))
    else:
        legs = ((6, s.legs_dk, 0), (8, s.legs_col, 1))
    for x, col, toe in legs:
        c.rect(x, s.legs_top, 2, 22 - s.legs_top, col)
        c.put(x, 22, s.shoes_col)
        c.put(x + 1, 22, s.shoes_col)
        c.put(x, 23, paper[2])
        c.put(x + 1, 23, paper[2])
        if toe:
            c.put(x + 2, 23, paper[2])


# ---------------------------------------------------------------------------
# TEZCAN — observatory director, 63. Square and careful; balding with grey
# sides; round glasses that catch the light; stone suit, paper shirt, rose tie.
# ---------------------------------------------------------------------------

def _style_tezcan(s: SimpleNamespace, spec: dict, p: Palette) -> None:
    stone = p.ramp("stone")
    s.tw, s.tx0 = 8, 4
    s.sw, s.sx0 = 7, 5
    s.torso, s.torso_dk, s.torso_lt = stone[1], stone[0], stone[2]
    s.sleeve = stone[0]
    s.legs_x = (5, 9)
    s.grey = stone[2]
    s.lens = stone[3]
    s.outline_ramp = stone
    s.hair_front, s.hair_back, s.hair_side = _tezcan_hair_f, _tezcan_hair_b, _tezcan_hair_s
    s.face_extra = _tezcan_face
    s.torso_extra, s.torso_extra_side = _tezcan_torso, _tezcan_torso_side


def _tezcan_hair_f(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.hline(6, 9, top, s.skin)                 # bald crown
    c.put(9, top, s.skin_hi)
    c.put(5, top, s.grey)
    c.put(10, top, s.grey)
    c.hline(6, 9, top + 1, s.skin)
    c.put(5, top + 1, s.grey)
    c.put(10, top + 1, s.grey)


def _tezcan_hair_b(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.rect(6, top, 4, 3, s.skin)
    c.put(9, top, s.skin_hi)
    c.vline(5, top, top + 4, s.grey)
    c.vline(10, top, top + 4, s.grey)
    c.rect(5, top + 3, 6, 2, s.grey)
    c.hline(6, 9, top + 5, _ramp_at(s.p, "stone", 1))


def _tezcan_hair_s(c: PixelCanvas, s: SimpleNamespace, top: int, sway: int) -> None:
    c.hline(6, 10, top, s.skin)                # bald dome...
    c.hline(6, 10, top + 1, s.skin)            # ...slopes unbroken to the brow
    c.put(10, top, s.skin_hi)
    c.put(5, top, s.grey)
    c.rect(5, top + 1, 2, 4, s.grey)           # grey at the back and ear
    c.put(7, top + 3, _ramp_at(s.p, "stone", 1))  # hint of the glasses arm
    c.put(9, top + 3, s.lens)                  # lens catches the light edge-on
    c.put(10, top + 3, s.lens)


def _tezcan_face(c: PixelCanvas, s: SimpleNamespace, ft: int) -> None:
    # round glasses catching the light — you never quite see the eyes;
    # bare skin between the lenses, or the row reads as a blindfold
    c.put(6, ft + 1, s.lens)
    c.put(9, ft + 1, s.lens)


def _tezcan_torso(
    c: PixelCanvas, s: SimpleNamespace, direction: str, dy: int, phase: int
) -> None:
    ty = s.top + 6 + dy
    if direction == "s":
        paper, rose = s.p.ramp("paper"), s.p.ramp("rose")
        c.put(6, ty, paper[2])                 # shirt collar V
        c.put(9, ty, paper[2])
        c.put(7, ty, rose[0])                  # tie knot
        c.put(8, ty, rose[0])
        c.vline(7, ty + 1, ty + 4, rose[1])    # the tie
        c.vline(8, ty + 1, ty + 5, rose[1])
        c.vline(5, ty + 1, ty + 6, s.torso_dk)   # lapel creases
        c.vline(10, ty + 1, ty + 6, s.torso_dk)
        c.put(8, ty + 7, _ramp_at(s.p, "stone", 3))  # jacket button
    else:
        c.vline(8, ty + 1, s.hem - 1, s.torso_dk)    # center vent seam


def _tezcan_torso_side(c: PixelCanvas, s: SimpleNamespace, dy: int, phase: int) -> None:
    ty = s.top + 6 + dy
    c.put(s.sx0 + s.sw - 1, ty, _ramp_at(s.p, "paper", 2))  # collar point
    c.put(s.sx0 + s.sw - 1, ty + 1, _ramp_at(s.p, "rose", 1))  # sliver of tie


_STYLERS = {
    "hoca": _style_hoca,
    "fadime": _style_fadime,
    "musa": _style_musa,
    "sukru": _style_sukru,
    "elif": _style_elif,
    "kadir": _style_kadir,
    "ismet": _style_ismet,
    "metin": _style_metin,
    "ebru": _style_ebru,
    "tezcan": _style_tezcan,
}


def _ramp_at(palette: Palette, name: str, idx: int) -> RGBA:
    return palette.ramp(name)[idx]


# ---------------------------------------------------------------------------
# YILDIZ — the cat. Elderly tortoiseshell: void base, big earth patches,
# small amber flecks, paper chest smudge, amber eyes, one notched ear, tail
# usually up. She walks like she owns the town (she does); when she stops,
# she sits.
# ---------------------------------------------------------------------------

def _cat_sheet(palette: Palette, spec: dict, accents: tuple) -> PixelCanvas:
    coat = _refs(palette, spec["coat"])
    cat = SimpleNamespace(
        p=palette,
        base=coat[0],          # void[1]
        patch=coat[1],         # earth[1]
        fleck=coat[2],         # amber[0]
        chest=coat[3],         # paper[1]
        eye=_ref(palette, spec["eyes"]),
        hi=palette.ramp("void")[2],
        accents=accents,
    )
    sheet = PixelCanvas(CAT_W * COLS, CAT_H * len(ROWS), palette)
    for row, (kind, direction, frame_count) in enumerate(ROWS):
        for phase in range(frame_count):
            frame = _cat_frame(palette, cat, kind, direction, phase)
            sheet.paste(frame, phase * CAT_W, row * CAT_H)
    return sheet


def _cat_frame(
    palette: Palette, cat: SimpleNamespace, kind: str, direction: str, phase: int
) -> PixelCanvas:
    c = PixelCanvas(CAT_W, CAT_H, palette)
    if direction == "w":
        _paste_mirrored(c, _cat_frame(palette, cat, kind, "e", phase))
        return c
    if kind == "idle":
        _cat_sit(c, cat, direction)
    elif direction == "e":
        _cat_walk_side(c, cat, phase)
    elif direction == "s":
        _cat_walk_front(c, cat, phase)
    else:
        _cat_walk_back(c, cat, phase)
    c.outline(cat.p.ramp("void"))
    return c


def _cat_walk_side(c: PixelCanvas, cat: SimpleNamespace, phase: int) -> None:
    """Facing east: head right, tail up at the left, diagonal leg pairs."""
    bob = 1 if phase in (0, 2) else 0
    # tail up, tip flicking through the cycle
    tip_x = (2, 1, 2, 3)[phase]
    c.put(3, 8 + bob, cat.base)
    c.put(2, 7 + bob, cat.base)
    c.put(tip_x, 6 + bob, cat.patch)           # earth-tipped tail
    # body: round-shouldered, a little low-slung with age
    c.rect(3, 9 + bob, 8, 4, cat.base)
    c.hline(4, 9, 8 + bob, cat.hi)             # light along the spine
    c.put(9, 8 + bob, cat.base)                # shoulder hump
    c.rect(5, 9 + bob, 4, 3, cat.patch)        # big tortie patch on the flank
    c.put(4, 12 + bob, cat.fleck)              # amber flecks
    c.put(9, 10 + bob, cat.fleck)
    # head: ears up, muzzle forward; the near ear carries the notch
    c.put(11, 6 + bob, cat.base)               # back ear
    c.put(14, 6 + bob, cat.patch)              # notched ear: 1px against 2
    c.put(10, 6 + bob, cat.base)
    c.rect(10, 7 + bob, 5, 3, cat.base)
    c.put(15, 8 + bob, cat.base)               # muzzle
    c.put(13, 8 + bob, cat.eye)                # eye
    c.put(14, 9 + bob, cat.fleck)              # amber chin patch
    c.rect(10, 10 + bob, 2, 2, cat.chest)      # chest smudge
    # legs: diagonal pairs, feet planted at y15
    if phase == 0:
        pairs = ((13, 0), (10, 1), (5, 1), (7, 0))
    elif phase == 2:
        pairs = ((10, 0), (13, 1), (7, 1), (5, 0))
    elif phase == 1:
        pairs = ((11, 0), (12, 1), (5, 0), (6, 1))
    else:
        pairs = ((12, 1), (11, 0), (6, 1), (5, 0))
    for x, lift in pairs:
        c.vline(x, 13 + bob, 15 - lift, cat.base)


def _cat_walk_front(c: PixelCanvas, cat: SimpleNamespace, phase: int) -> None:
    """Facing south: triangular ears, tortie-split face, paws padding."""
    bob = 1 if phase in (0, 2) else 0
    y = 6 + bob
    # ear tips first, one px each, so the outline cuts them into triangles
    c.put(5, y, cat.patch)                     # left ear wears the patch side
    c.put(10, y, cat.base)
    # head widens under the ears; split-color face — classic tortie asymmetry
    c.rect(5, y + 1, 6, 3, cat.base)
    c.rect(5, y + 1, 3, 3, cat.patch)
    c.put(6, y + 2, cat.eye)
    c.put(9, y + 2, cat.eye)
    c.put(8, y + 3, cat.fleck)                 # amber muzzle fleck
    # body narrower than the head, chest smudge small and proud
    c.rect(6, y + 4, 4, 4, cat.base)
    c.rect(7, y + 4, 2, 2, cat.chest)
    c.put(6, y + 4, cat.patch)                 # patch rides one shoulder
    c.put(6, y + 5, cat.patch)
    # tail tip swinging into view at her hip
    tail_x = (10, 10, 11, 10)[phase]
    c.put(tail_x, y + 6, cat.patch)
    # paws alternate; feet planted at y15
    lift_l = 1 if phase == 0 else 0
    lift_r = 1 if phase == 2 else 0
    c.rect(6, 14 - lift_l, 2, 2, cat.base)
    c.rect(9, 14 - lift_r, 2, 2, cat.base)


def _cat_walk_back(c: PixelCanvas, cat: SimpleNamespace, phase: int) -> None:
    """Facing north: the tail-up walk — her signature exit."""
    bob = 1 if phase in (0, 2) else 0
    y = 6 + bob
    c.put(5, y, cat.patch)                     # ear tips from behind
    c.put(10, y, cat.base)
    c.rect(5, y + 1, 6, 3, cat.base)           # back of head
    c.rect(5, y + 1, 3, 2, cat.patch)
    c.rect(5, y + 4, 6, 3, cat.base)           # back
    c.rect(6, y + 7, 4, 1, cat.base)           # hips taper toward the ground
    c.rect(8, y + 4, 3, 3, cat.patch)          # saddle patch
    c.put(5, y + 6, cat.fleck)
    # the tail, straight up and talking — seen from behind it crosses her
    # own silhouette, so it draws over the head (and stays inside height 10)
    sway = (0, -1, 0, 1)[phase]
    c.vline(7, y + 3, y + 6, cat.hi)           # raised tail, lit against her back
    c.vline(7 + sway, y, y + 2, cat.hi)        # upper tail leans with the step
    c.put(7 + sway, y - 1, cat.patch)          # earth tip beside the ears
    # hind feet stepping
    lift_l = 1 if phase == 0 else 0
    lift_r = 1 if phase == 2 else 0
    c.rect(6, 14 - lift_l, 2, 2, cat.base)
    c.rect(9, 14 - lift_r, 2, 2, cat.base)


def _cat_sit(c: PixelCanvas, cat: SimpleNamespace, direction: str) -> None:
    """Idle = seated. An elderly cat does not hover; she settles."""
    if direction == "s":
        c.put(5, 6, cat.patch)                 # ear tips
        c.put(10, 6, cat.base)
        c.rect(5, 7, 6, 3, cat.base)           # split face
        c.rect(5, 7, 3, 3, cat.patch)
        c.put(6, 8, cat.eye)                   # the unimpressed stare
        c.put(9, 8, cat.eye)
        c.rect(6, 10, 4, 4, cat.base)          # chest column, narrower than head
        c.rect(7, 10, 2, 2, cat.chest)         # the smudge
        c.put(6, 10, cat.patch)
        c.rect(5, 12, 6, 3, cat.base)          # haunches spread with the sit
        c.put(5, 12, cat.patch)
        c.put(5, 13, cat.patch)
        c.put(10, 13, cat.fleck)
        c.put(7, 15, cat.base)                 # front paws tucked neat
        c.put(8, 15, cat.fleck)                # one odd amber toe
        c.hline(3, 5, 15, cat.patch)           # tail curled around the paws
        c.put(3, 14, cat.base)
    elif direction == "n":
        c.put(5, 6, cat.patch)                 # ear tips
        c.put(10, 6, cat.base)
        c.rect(5, 7, 6, 3, cat.base)
        c.rect(5, 7, 3, 2, cat.patch)
        c.rect(4, 10, 8, 6, cat.base)          # broad seated back, a soft pear
        c.hline(5, 10, 10, cat.hi)             # light across the shoulders
        c.rect(8, 11, 4, 3, cat.patch)
        c.put(4, 13, cat.fleck)
        c.vline(12, 9, 12, cat.base)           # tail hooked up beside her
        c.put(12, 8, cat.patch)
    else:  # east profile sit
        c.put(11, 5, cat.base)                 # ears
        c.put(14, 5, cat.patch)                # notched front ear
        c.rect(10, 6, 5, 3, cat.base)          # head high, dignified
        c.put(13, 7, cat.eye)
        c.put(15, 7, cat.base)                 # muzzle
        c.put(14, 8, cat.fleck)
        c.rect(11, 9, 2, 2, cat.chest)         # chest
        # seated body: a slope from shoulder down to the settled haunch
        c.rect(5, 10, 8, 6, cat.base)          # haunch rests on the ground
        c.put(5, 9, cat.base)
        c.hline(5, 9, 9, cat.hi)               # spine light
        c.rect(6, 10, 4, 3, cat.patch)         # flank patch
        c.put(11, 13, cat.fleck)
        c.vline(12, 11, 15, cat.base)          # straight, dignified front leg
        c.put(13, 15, cat.base)                # paw
        c.hline(3, 5, 15, cat.patch)           # tail wrapped round the front
        c.put(3, 14, cat.base)
