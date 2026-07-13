"""sprites.cast_portraits — 64x64 dialogue portraits for the Act 1 cast (M4).

One manifest -> game/assets/gen/sprites/portraits/<id>.png for every id in
cast/characters.json, plus hoca's mood variants (hoca.png is the neutral
mood; hoca_tired / hoca_wry / hoca_listening share the exact same head and
differ only in brows, lids, mouth and eye direction). Art is 32x32, baked
2x -> exactly 64x64 — the DialogueBox slot, integer-perfect.

One camera for the whole cast: bust (head + shoulders) filling ~90% of the
frame, 3/4 view facing slightly LEFT (toward the dialogue text), light from
above-right — crowns, near temples and right shoulders catch it; the
turned-away face front carries the form shadow under brow, nose and jaw.

Facial grid shared by every human (so the cast holds one camera): brows y9,
lash y11, iris y12 with the pupil toward the text, nose bump breaking the
silhouette at x6, mouth y16. Skin's deep accents borrow the warm dark of
earth[] the way SNES portraits extend a ramp; broad shading stays on amber.

Character truth (ramps, features, moods) comes from artgen/cast/
characters.json via manifest["cast"] — the same file sprites.cast_sheets
consumes, so walk sheets and portraits agree (tortie face split, notched
ear, grey temples, the pencil). json content affects drawing but never RNG
state: rng (seeded from manifest["seed"] only) hands every id a fixed kit
of cloth-weave ticks up front, drawn at fixed garment-relative coordinates.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from types import SimpleNamespace

from ..canvas import PixelCanvas
from ..palette import Palette, RGBA

ART = 32
HOCA_MOODS = ("neutral", "tired", "wry", "listening")

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
    cast_path = Path(manifest["_path"]).parent / manifest["cast"]
    cast = json.loads(cast_path.read_text(encoding="utf-8"))
    chars: dict[str, dict] = cast["characters"]

    # RNG is consumed in id order before any drawing — json content never
    # shifts it (same discipline as sprites.cast_sheets).
    rng = random.Random(manifest["seed"])
    weave = {cid: _pick_weave(rng) for cid in chars}

    out_dir = Path(out_root) / str(manifest.get("out_dir", "sprites/portraits"))
    P = _kit(palette)
    for cid, spec in chars.items():
        if cid == "hoca":
            for mood in HOCA_MOODS:
                c = PixelCanvas(ART, ART, palette)
                _draw_hoca(c, P, spec, weave[cid], mood)
                c.outline(P.void)
                name = "hoca" if mood == "neutral" else f"hoca_{mood}"
                c.save(out_dir / f"{name}.png", scale=scale)
        else:
            c = PixelCanvas(ART, ART, palette)
            _DRAWERS[cid](c, P, spec, weave[cid])
            c.outline(P.void)
            c.save(out_dir / f"{cid}.png", scale=scale)


def _pick_weave(rng: random.Random) -> tuple[tuple[int, int], ...]:
    """Three cloth-weave ticks per character, fixed garment-relative coords."""
    return tuple((rng.randrange(18), rng.randrange(4)) for _ in range(3))


def _kit(palette: Palette) -> SimpleNamespace:
    return SimpleNamespace(
        pal=palette,
        void=palette.ramp("void"),
        stone=palette.ramp("stone"),
        earth=palette.ramp("earth"),
        amber=palette.ramp("amber"),
        rose=palette.ramp("rose"),
        ship=palette.ramp("ship"),
        paper=palette.ramp("paper"),
    )


# ---------------------------------------------------------------------------
# shared bust plumbing
# ---------------------------------------------------------------------------

# (y, x0, x1) row runs. Facing left: chin biased left, skull mass right.
_HEAD_LEAN = (
    (3, 10, 17), (4, 9, 19), (5, 8, 20), (6, 8, 21), (7, 7, 21),
    (8, 7, 21), (9, 7, 21), (10, 7, 21), (11, 7, 21), (12, 7, 21),
    (13, 7, 21), (14, 7, 21), (15, 7, 20), (16, 8, 20), (17, 8, 19),
    (18, 8, 18), (19, 9, 15), (20, 10, 13),
)
_HEAD_BROAD = (
    (3, 10, 18), (4, 8, 20), (5, 7, 21), (6, 7, 22), (7, 7, 22),
    (8, 7, 22), (9, 7, 22), (10, 7, 22), (11, 7, 22), (12, 7, 22),
    (13, 7, 22), (14, 7, 22), (15, 7, 21), (16, 8, 21), (17, 8, 20),
    (18, 9, 19), (19, 10, 16), (20, 11, 14),
)
_HEAD_SQUARE = (
    (3, 9, 19), (4, 8, 20), (5, 7, 21), (6, 7, 22), (7, 7, 22),
    (8, 7, 22), (9, 7, 22), (10, 7, 22), (11, 7, 22), (12, 7, 22),
    (13, 7, 22), (14, 7, 22), (15, 7, 22), (16, 8, 21), (17, 8, 21),
    (18, 8, 20), (19, 9, 16), (20, 10, 14),
)
_HEAD_CHILD = (
    (4, 9, 19), (5, 8, 20), (6, 7, 21), (7, 7, 22), (8, 7, 22),
    (9, 7, 22), (10, 7, 22), (11, 7, 22), (12, 7, 22), (13, 7, 22),
    (14, 7, 21), (15, 8, 21), (16, 8, 20), (17, 9, 18), (18, 10, 16),
    (19, 11, 14),
)


def _rows(c: PixelCanvas, color: RGBA, rows: tuple, dx: int = 0, dy: int = 0) -> None:
    for y, x0, x1 in rows:
        c.hline(x0 + dx, x1 + dx, y + dy, color)


def _neck(
    c: PixelCanvas, sk: RGBA, sh: RGBA,
    x0: int = 12, x1: int = 17, top: int = 19, bot: int = 25, dx: int = 0,
) -> None:
    for y in range(top, bot + 1):
        c.hline(x0 + dx, x1 + dx, y, sk)
    # the jaw casts down onto the throat — the signature of top light
    c.hline(x0 + dx, x1 + dx, top, sh)
    c.hline(x0 + dx, x1 + dx, top + 1, sh)
    c.vline(x0 + dx, top, bot, sh)


def _face_light(c: PixelCanvas, sk: RGBA, sh: RGBA, hi: RGBA, dx: int = 0) -> None:
    """Above-right light on a left-turned face: the near temple and cheek
    carry a lit plane; the front edge turns away under the brow."""
    c.hline(11 + dx, 15 + dx, 6, hi)          # forehead top
    c.hline(13 + dx, 16 + dx, 7, hi)
    c.put(15 + dx, 8, hi)                     # temple wedge
    c.put(16 + dx, 8, hi)
    c.put(16 + dx, 9, hi)
    c.put(14 + dx, 13, hi)                    # near cheekbone
    c.put(15 + dx, 13, hi)
    c.put(15 + dx, 14, hi)
    c.vline(7 + dx, 8, 9, sh)                 # brow front turns from the light
    c.hline(13 + dx, 15 + dx, 19, sh)         # jaw turns under, toward the ear
    c.hline(10 + dx, 13 + dx, 20, sh)         # chin bottom in its own shade


def _ear(c: PixelCanvas, sk: RGBA, sh: RGBA, hi: RGBA, x: int = 17, y: int = 11) -> None:
    c.rect(x, y, 2, 3, sk)
    c.put(x + 1, y, hi)                       # rim catch
    c.put(x, y + 1, sh)                       # bowl in shadow


def _brows(c: PixelCanvas, color: RGBA, dx: int = 0, y: int = 9) -> None:
    c.hline(8 + dx, 9 + dx, y, color)
    c.hline(12 + dx, 14 + dx, y, color)


def _eyes_open(
    c: PixelCanvas, P,
    *, dx: int = 0, pupil: RGBA | None = None, white: RGBA | None = None,
) -> None:
    """Both eyes on the y11-12 grid, pupils toward the text (left)."""
    pupil = pupil or P.void[0]
    white = white or P.paper[2]
    c.hline(8 + dx, 9 + dx, 11, P.void[0])    # far eye, foreshortened
    c.put(8 + dx, 12, pupil)
    c.put(9 + dx, 12, white)
    c.hline(12 + dx, 14 + dx, 11, P.void[0])  # near eye
    c.put(12 + dx, 12, pupil)
    c.put(13 + dx, 12, white)
    c.put(14 + dx, 12, P.void[0])             # lash corner closes the almond
    c.put(14 + dx, 11, P.void[0])


def _nose(c: PixelCanvas, sk: RGBA, sh: RGBA, dx: int = 0) -> None:
    c.put(6 + dx, 12, sk)                     # the profile bump
    c.put(6 + dx, 13, sk)
    c.put(7 + dx, 14, sh)                     # one quiet under-nose shade


def _mouth(
    c: PixelCanvas, P, x0: int = 8, x1: int = 11, y: int = 16,
    *, lip: RGBA | None = None,
) -> None:
    c.hline(x0, x1, y, P.earth[1])
    if lip is not None:
        c.hline(x0 + 1, x1 - 1, y + 1, lip)   # lower lip catches the light


def _shoulder_rows(top: int, x0: int, x1: int, inset: tuple = (6, 3, 1)) -> tuple:
    """Trapezius slope then full width down to the frame's bottom edge."""
    rows = []
    y = top
    for step in inset:
        rows.append((y, x0 + step, x1 - step))
        y += 1
    while y < ART:
        rows.append((y, x0, x1))
        y += 1
    return tuple(rows)


def _garment(
    c: PixelCanvas, rows: tuple, base: RGBA, dk: RGBA, lt: RGBA,
    weave: tuple = (),
) -> None:
    _rows(c, base, rows)
    for y, x0, x1 in rows:
        c.put(x0, y, dk)                      # left edge shaded
        c.put(x1, y, lt)                      # right edge lit
    # lit line along the right shoulder slope, shade along the left
    for i in range(len(rows) - 1):
        y, x0, x1 = rows[i]
        _, nx0, nx1 = rows[i + 1]
        for x in range(x1 + 1, nx1):
            c.put(x, y + 1, lt)
        for x in range(nx0 + 1, x0):
            c.put(x, y + 1, dk)
    # fixed weave ticks so the big flat chest never reads as vector fill
    top, x0, x1 = rows[-1][0] - 3, rows[-1][1], rows[-1][2]
    for wx, wy in weave:
        x = x0 + 2 + (wx % max(1, x1 - x0 - 3))
        y = top + (wy % 4)
        c.put(x, y, dk)


# ---------------------------------------------------------------------------
# HOCA — Dr. Deniz Aydın, 47. Lean, tired kind eyes, faint stubble, grey
# temples, earth wool coat over a paper shirt. Four moods, one head.
# ---------------------------------------------------------------------------

def _draw_hoca(c: PixelCanvas, P, spec: dict, weave: tuple, mood: str) -> None:
    sk = _ref(P.pal, spec["skin"])
    sh = _ref(P.pal, spec["skin_shade"])
    hi = P.amber[2]
    hair = _ref(P.pal, spec["hair"]["color"])
    grey = _ref(P.pal, spec["hair"]["highlight"])
    earth, paper = P.earth, P.paper

    _neck(c, sk, sh)
    _rows(c, sk, _HEAD_LEAN)
    _face_light(c, sk, sh, hi)
    _ear(c, sk, sh, hi)
    # short neat hair, sheen on the lit crown, grey flecked at the temples
    c.hline(10, 17, 3, hair)
    c.hline(9, 19, 4, hair)
    c.hline(8, 20, 5, hair)
    c.put(8, 6, hair)                          # front hairline corner
    c.rect(17, 6, 5, 5, hair)                  # side mass above the ear
    c.rect(19, 11, 3, 3, hair)                 # behind the ear
    c.hline(19, 20, 14, hair)                  # trimmed nape
    c.hline(13, 16, 3, P.void[2])              # crown sheen, light side
    c.put(17, 4, P.void[2])
    c.put(18, 5, P.void[3])
    c.put(8, 5, grey)                          # grey: front temple...
    c.put(16, 6, grey)                         # ...and above the ear
    c.put(17, 7, grey)
    # faint stubble: upper-lip shadow and a field hugging the jaw edge,
    # kept clear of the mouth row so the two never fuse into a goatee
    c.hline(8, 9, 15, sh)
    c.hline(9, 11, 18, sh)
    c.hline(12, 13, 17, sh)
    _nose(c, sk, sh)
    _hoca_mood(c, P, sk, sh, mood)
    # wool coat over a paper shirt: lapels meet low over the top button
    rows = _shoulder_rows(23, 5, 26)
    _garment(c, rows, earth[2], earth[1], earth[3], weave)
    c.put(11, 23, earth[1])                    # collar roll, shaded side
    c.put(12, 23, earth[1])
    c.put(18, 23, earth[3])                    # lit side
    c.put(19, 24, earth[3])
    c.hline(13, 16, 24, paper[2])              # shirt V between the lapels
    c.hline(14, 15, 25, paper[2])
    c.put(14, 26, paper[1])                    # shirt falls into shadow
    c.put(15, 26, paper[1])
    c.vline(12, 24, 26, earth[1])              # lapel creases
    c.put(13, 25, earth[1])
    c.put(13, 26, earth[1])
    c.vline(17, 24, 26, earth[1])
    c.put(16, 26, earth[1])
    c.put(14, 27, earth[0])                    # top button closes the coat
    c.put(15, 27, earth[0])


def _hoca_mood(c: PixelCanvas, P, sk: RGBA, sh: RGBA, mood: str) -> None:
    """Brows, lids, mouth, eye direction ONLY — the head never moves."""
    if mood == "neutral":
        _brows(c, P.void[1])
        _eyes_open(c, P)
        c.put(13, 13, sh)                      # the baseline tiredness
        _mouth(c, P, 8, 10)
    elif mood == "tired":
        _brows(c, P.void[1])
        c.hline(8, 9, 11, P.void[0])           # lash lines...
        c.hline(12, 14, 11, P.void[0])
        c.put(8, 12, P.void[0])                # pupils still toward the text
        c.put(9, 12, sh)                       # ...but the lids sag over them
        c.put(12, 12, P.void[0])
        c.put(13, 12, sh)
        c.put(14, 12, sh)
        c.hline(8, 9, 13, sh)                  # bags under both eyes
        c.hline(12, 13, 13, sh)
        _mouth(c, P, 8, 9)                     # mouth shorter, heavier
        c.put(10, 17, sh)                      # corner drops
    elif mood == "wry":
        c.hline(8, 9, 9, P.void[1])            # far brow stays level
        c.hline(12, 14, 8, P.void[1])          # near brow up
        _eyes_open(c, P)
        c.put(13, 13, sh)
        _mouth(c, P, 8, 10)
        c.put(11, 15, P.earth[1])              # near corner lifts
    else:  # listening — the signature: eyes up and off-frame right
        _brows(c, P.void[1], y=8)              # both brows raised high
        c.put(8, 12, P.paper[2])               # whites low-left...
        c.put(9, 11, P.void[0])                # ...pupils high-right
        c.put(9, 12, P.paper[2])
        c.hline(12, 13, 12, P.paper[2])
        c.put(14, 11, P.void[0])
        c.put(14, 12, P.paper[2])
        c.put(13, 11, P.void[0])
        _mouth(c, P, 8, 9)                     # mouth still


# ---------------------------------------------------------------------------
# YILDIZ — elderly tortoiseshell cat. Head + chest, half-lidded amber stare,
# the facing (left) ear notched and patch-colored, exactly as on her sheet.
# ---------------------------------------------------------------------------

def _draw_yildiz(c: PixelCanvas, P, spec: dict, weave: tuple) -> None:
    coat = _refs(P.pal, spec["coat"])
    base, patch, fleck, chest = coat
    eye = _ref(P.pal, spec["eyes"])
    patch_lt = P.earth[2]
    rim = P.void[3]

    # chest first — the head overlaps it
    c.hline(9, 21, 19, base)
    c.hline(8, 22, 20, base)
    for y in range(21, ART):
        c.hline(7, 23, y, base)
    c.vline(23, 21, 31, rim)                   # rim light down the lit side
    c.put(22, 20, rim)
    c.rect(18, 22, 5, 6, patch)                # patch over the near shoulder
    c.put(18, 22, base)
    c.put(22, 22, patch_lt)                    # its lit edge
    c.vline(22, 23, 26, patch_lt)
    # the chest smudge — a soft tuft, not a bib
    c.put(12, 22, chest)
    c.hline(11, 14, 23, chest)
    c.hline(11, 15, 24, chest)
    c.hline(11, 15, 25, chest)
    c.hline(12, 14, 26, chest)
    c.put(12, 27, chest)
    c.put(13, 27, P.paper[2])                  # one bright tuft catches light
    c.put(14, 24, P.paper[2])
    c.put(11, 24, P.paper[0])                  # shaded side of the tuft
    c.put(11, 25, P.paper[0])
    c.put(12, 26, P.paper[0])
    c.put(8, 24, fleck)                        # stray amber flecks
    c.put(9, 28, fleck)
    c.put(17, 29, P.void[2])                   # fur ticks in the dark coat
    c.put(9, 22, P.void[2])
    c.put(20, 29, P.void[2])
    # ears — tall triangles; the facing ear wears the patch and the notch
    c.put(10, 1, patch)
    c.hline(9, 11, 2, patch)
    c.hline(10, 11, 3, patch)                  # outer edge bites in: the notch
    c.hline(8, 11, 4, patch)
    c.put(10, 4, P.rose[1])                    # inner ear
    c.put(18, 1, base)
    c.hline(17, 19, 2, base)
    c.hline(17, 19, 3, base)
    c.hline(16, 20, 4, base)
    c.put(18, 4, P.rose[1])
    c.put(19, 2, rim)                          # lit ear edge
    c.put(19, 3, rim)
    c.put(20, 4, rim)
    # head — broad, cheek tufts breaking the silhouette
    head = (
        (5, 8, 20), (6, 7, 21), (7, 6, 22), (8, 6, 22), (9, 6, 23),
        (10, 6, 23), (11, 6, 23), (12, 6, 23), (13, 6, 23), (14, 7, 22),
        (15, 7, 22), (16, 8, 21), (17, 10, 20), (18, 12, 19),
    )
    _rows(c, base, head)
    c.put(5, 13, base)                         # cheek fur tufts
    c.put(5, 14, base)
    c.put(24, 12, base)
    c.put(24, 13, base)
    # tortie patches: the facing half of the face is earth, like her sheet
    c.rect(6, 6, 5, 4, patch)
    c.put(6, 6, base)
    c.hline(7, 9, 5, patch)
    c.rect(16, 5, 5, 4, patch)                 # crown patch behind the ear
    c.put(16, 5, base)
    c.put(20, 5, base)
    c.hline(17, 19, 5, patch_lt)               # patch catches the top light
    c.put(9, 6, patch_lt)
    c.put(10, 6, patch_lt)
    c.put(13, 7, fleck)                        # amber flecks
    c.put(21, 11, fleck)
    c.put(19, 15, fleck)
    c.hline(12, 17, 4, rim)                    # crown sheen between the ears
    c.put(18, 6, P.void[2])
    c.vline(22, 7, 11, P.void[2])              # lit back of head
    c.vline(23, 9, 13, rim)
    # the unimpressed half-lidded stare — big flat lids, slit pupils
    c.hline(7, 10, 10, P.void[0])              # lids, dead level
    c.hline(13, 16, 10, P.void[0])
    c.hline(7, 10, 11, eye)
    c.hline(13, 16, 11, eye)
    c.put(8, 11, P.void[0])                    # slit pupils, toward the text
    c.put(14, 11, P.void[0])
    c.hline(7, 10, 12, base)                   # lower lid closes the eye
    c.hline(13, 16, 12, base)
    # muzzle: lighter, nose leading left
    c.rect(7, 13, 5, 3, P.void[2])
    c.put(7, 13, base)
    c.hline(7, 8, 13, P.rose[1])               # nose
    c.put(7, 14, P.void[0])                    # mouth falls from the nose
    c.hline(8, 9, 15, P.void[0])
    c.put(10, 14, P.void[0])                   # whisker roots
    c.put(11, 13, P.void[0])
    c.put(9, 16, fleck)                        # amber chin, as on the sheet
    # ruff line where head settles into chest
    for x in (9, 12, 15, 18, 21):
        c.put(x, 18, P.void[0])


# ---------------------------------------------------------------------------
# FADİME — baker, 55. Broad warm face framed by a paper yemeni knotted at
# the side; rose dress under a flour-dusted apron; flour on one cheek.
# ---------------------------------------------------------------------------

def _draw_fadime(c: PixelCanvas, P, spec: dict, weave: tuple) -> None:
    sk = _ref(P.pal, spec["skin"])
    sh = _ref(P.pal, spec["skin_shade"])
    hi = P.amber[2]
    paper, rose = P.paper, P.rose

    _neck(c, sk, sh, x0=12, x1=17, top=20)
    _rows(c, sk, _HEAD_BROAD)
    _face_light(c, sk, sh, hi)
    # yemeni: crown, back wrap curving under the jaw, side knot with tails
    c.hline(10, 18, 2, paper[2])
    c.hline(8, 20, 3, paper[2])
    c.hline(7, 21, 4, paper[2])
    c.hline(7, 21, 5, paper[2])
    c.put(7, 6, paper[2])                      # frames the far temple
    c.put(7, 7, paper[1])
    c.rect(16, 6, 6, 5, paper[2])              # side/back wrap
    c.rect(17, 11, 5, 4, paper[2])
    c.rect(17, 15, 4, 2, paper[2])             # curves toward the jaw
    c.hline(16, 19, 17, paper[2])
    c.hline(11, 18, 18, paper[2])              # passes under the chin
    c.hline(12, 16, 19, paper[1])              # its underside in shadow
    c.hline(8, 9, 2, paper[1])                 # crown shade, far side
    c.put(7, 4, paper[1])
    c.put(7, 5, paper[1])
    c.vline(16, 7, 10, paper[1])               # fold where the wrap turns
    c.vline(17, 12, 16, paper[1])
    c.hline(12, 16, 2, paper[2])
    # oya dots along the face edge — the printed border of the scarf
    c.put(9, 4, rose[2])
    c.put(13, 3, rose[2])
    c.put(17, 5, rose[2])
    # the side knot, tied by feel forty years running
    c.rect(6, 12, 2, 3, paper[2])
    c.put(6, 12, paper[1])
    c.put(5, 14, paper[1])                     # tails
    c.put(6, 15, paper[1])
    c.put(5, 16, paper[2])
    # broad warm face: apple cheeks, the smile arrives before she does
    _brows(c, P.void[1])
    _eyes_open(c, P)
    c.put(9, 13, sh)                           # cheeks push up under the eyes
    c.put(12, 13, sh)
    _nose(c, sk, sh)
    _mouth(c, P, 8, 11, 15, lip=hi)            # smile sits high, lip catches
    c.put(12, 14, P.earth[1])                  # corner up
    c.put(8, 16, sh)                           # smile line
    c.hline(13, 14, 17, paper[2])              # flour along the jaw — wiped
    c.put(13, 18, paper[2])                    # there with the back of a hand
    # rose dress, apron bib pinned over it
    rows = _shoulder_rows(23, 4, 27, (7, 4, 1))
    _garment(c, rows, rose[1], rose[0], rose[2], weave)
    c.hline(12, 17, 23, rose[0])               # round dress collar
    c.rect(11, 27, 9, 5, paper[2])             # apron bib
    c.vline(11, 27, 31, paper[1])
    c.hline(12, 18, 27, paper[1])              # bib hem line
    c.put(13, 29, paper[1])                    # flour crease
    c.put(16, 30, paper[1])
    c.put(10, 24, paper[2])                    # straps up over the shoulders
    c.put(10, 25, paper[2])
    c.put(10, 26, paper[1])
    c.put(20, 24, paper[2])
    c.put(20, 25, paper[2])
    c.put(20, 26, paper[1])


# ---------------------------------------------------------------------------
# MUSA — grocer, 45. Stocky, moustache first, friendly squint; earth knit
# vest over a paper shirt.
# ---------------------------------------------------------------------------

def _draw_musa(c: PixelCanvas, P, spec: dict, weave: tuple) -> None:
    sk = _ref(P.pal, spec["skin"])
    sh = _ref(P.pal, spec["skin_shade"])
    hi = P.amber[2]
    hair = _ref(P.pal, spec["hair"]["color"])
    earth, paper = P.earth, P.paper

    _neck(c, sk, sh, x0=11, x1=18, top=19, bot=23)
    _rows(c, sk, _HEAD_BROAD)
    _face_light(c, sk, sh, hi)
    _ear(c, sk, sh, hi, x=18)
    # short thick hair, low hairline
    c.hline(10, 18, 3, hair)
    c.hline(8, 20, 4, hair)
    c.hline(7, 21, 5, hair)
    c.hline(7, 21, 6, hair)
    c.put(7, 7, hair)
    c.rect(18, 7, 4, 4, hair)
    c.rect(20, 11, 2, 3, hair)
    c.hline(13, 17, 3, P.void[2])              # sheen
    c.put(18, 4, P.void[2])
    # the friendly squint: pushed-up lower lids, warmth without whites
    _brows(c, hair)
    c.hline(8, 9, 11, P.void[0])               # lash
    c.hline(12, 14, 11, P.void[0])
    c.put(8, 12, P.void[0])                    # a slit of eye survives
    c.put(12, 12, P.void[0])
    c.put(9, 12, sh)                           # cheek pushes up
    c.hline(13, 14, 12, sh)
    c.put(15, 12, sh)                          # crow's feet
    _nose(c, sk, sh)
    # the moustache — it reads before he does
    c.hline(7, 13, 14, hair)
    c.hline(7, 12, 15, hair)
    c.put(6, 15, hair)                         # tips droop past the mouth
    c.put(13, 15, hair)
    c.put(6, 16, hair)
    c.put(13, 16, hair)
    c.hline(9, 11, 17, P.earth[1])             # lower lip under the brush
    c.put(10, 18, sh)                          # chin crease
    # knit vest over the shirt, stocky shoulders high
    rows = _shoulder_rows(22, 3, 28, (7, 4, 1))
    _garment(c, rows, earth[1], earth[0], earth[2], weave)
    c.rect(12, 24, 6, 8, paper[1])             # shirt in the vest's V
    c.vline(12, 24, 31, paper[0])
    c.put(13, 23, paper[2])                    # collar points
    c.put(12, 23, paper[2])
    c.put(17, 23, paper[2])
    c.put(16, 24, paper[2])
    c.vline(11, 24, 31, earth[0])              # vest edges
    c.vline(18, 24, 31, earth[0])
    c.put(19, 25, earth[2])                    # lit vest edge
    c.put(19, 27, earth[2])
    c.put(14, 26, paper[0])                    # shirt buttons
    c.put(14, 29, paper[0])
    for y in (26, 28, 30):                     # knit ribs
        c.put(6, y, earth[0])
        c.put(22, y, earth[0])


# ---------------------------------------------------------------------------
# ŞÜKRÜ — retired teacher, 74. Thin and stooped, white hair combed back off
# a high forehead, sharp pale eyes, deep smile lines; buttoned cardigan.
# ---------------------------------------------------------------------------

def _draw_sukru(c: PixelCanvas, P, spec: dict, weave: tuple) -> None:
    sk = _ref(P.pal, spec["skin"])
    sh = _ref(P.pal, spec["skin_shade"])
    hi = P.amber[2]
    hair = _ref(P.pal, spec["hair"]["color"])   # stone[3] white
    rose, paper, stone = P.rose, P.paper, P.stone
    dx = -1                                     # the stoop carries him forward

    _neck(c, sk, sh, x0=12, x1=16, top=19, dx=dx)
    _rows(c, sk, _HEAD_LEAN, dx=dx)
    _face_light(c, sk, sh, hi, dx=dx)
    _ear(c, sk, sh, hi, x=16)
    # white hair combed straight back — high forehead, volume at the crown
    c.hline(8 + dx, 17 + dx, 3, hair)
    c.hline(12 + dx, 19 + dx, 4, hair)
    c.hline(15 + dx, 20 + dx, 5, hair)
    c.rect(16 + dx, 6, 5, 4, hair)
    c.rect(18 + dx, 10, 3, 4, hair)
    c.put(8 + dx, 4, hair)                     # temple wisp
    c.hline(12 + dx, 15 + dx, 3, paper[2])     # white catches the light
    c.put(17 + dx, 4, paper[2])
    c.put(10 + dx, 4, stone[2])                # comb tracks
    c.put(14 + dx, 4, stone[2])
    c.put(17 + dx, 7, stone[2])
    # age: forehead line, hollow cheek, deep smile lines
    c.hline(9 + dx, 12 + dx, 7, sh)
    c.put(10 + dx, 14, sh)                     # cheek hollow
    c.put(10 + dx, 15, sh)
    _brows(c, stone[2], dx=dx)                 # white brows
    _eyes_open(c, P, dx=dx, pupil=P.ship[3])   # sharp pale eyes, dark-lashed
    c.put(14 + dx, 13, sh)                     # crow's feet
    c.put(15 + dx, 13, sh)
    _nose(c, sk, sh, dx=dx)
    _mouth(c, P, 7, 9)
    c.put(10, 15, P.earth[1])                  # the year-round almost-smile
    c.put(6, 15, sh)                           # smile lines, carved deep
    c.put(11, 16, sh)
    # thin frame, rounded upper back: the right slope rises into a hump
    rows = ((22, 16, 21),) + _shoulder_rows(23, 6, 24, (5, 2, 0))
    _garment(c, rows, rose[0], rose[0], rose[1], weave)
    c.hline(17, 20, 22, rose[1])               # light rakes the stooped back
    c.put(21, 23, rose[1])
    c.vline(6, 26, 31, P.void[1])              # cardigan hangs off him
    # buttoned placket, shirt only at the collar
    c.put(11, 23, paper[1])
    c.put(12, 23, paper[1])
    c.put(12, 24, paper[1])
    c.vline(13, 24, 31, rose[1])               # placket edge catches light
    c.put(13, 25, rose[2])                     # buttons, done up to the top
    c.put(13, 28, rose[2])
    c.put(13, 31, rose[2])


# ---------------------------------------------------------------------------
# ELİF — schoolgirl, 11. Big attentive eyes, mouth open mid-question, high
# ponytail with a rose tie; teal school cardigan, paper collar.
# ---------------------------------------------------------------------------

def _draw_elif(c: PixelCanvas, P, spec: dict, weave: tuple) -> None:
    sk = _ref(P.pal, spec["skin"])
    sh = _ref(P.pal, spec["skin_shade"])
    hi = P.amber[2]
    hair = _ref(P.pal, spec["hair"]["color"])
    ship, paper, rose = P.ship, P.paper, P.rose

    _neck(c, sk, sh, x0=12, x1=16, top=19)
    _rows(c, sk, _HEAD_CHILD)
    c.hline(12, 15, 8, hi)                     # round young face: soft light
    c.put(13, 14, hi)
    c.put(14, 14, hi)
    c.put(7, 15, sh)
    c.hline(11, 13, 19, sh)
    # full fringe with a soft edge, side falls framing the face
    c.hline(9, 19, 4, hair)
    c.hline(8, 20, 5, hair)
    c.hline(7, 21, 6, hair)
    c.put(8, 7, hair)                          # fringe bites, just two
    c.put(15, 7, hair)
    c.vline(7, 7, 10, hair)                    # far side fall
    c.rect(17, 7, 5, 5, hair)                  # near side mass
    c.rect(19, 12, 3, 4, hair)
    c.put(18, 16, hair)                        # tip curls at the jaw
    c.hline(12, 16, 4, P.void[3])              # young hair shines
    c.put(17, 5, P.void[2])
    # high ponytail: sprouts at the crown, swings out right
    c.rect(16, 2, 3, 2, hair)
    c.hline(18, 20, 3, hair)
    c.rect(19, 4, 3, 2, hair)
    c.put(22, 5, hair)
    c.put(21, 6, hair)
    c.put(22, 6, P.void[3])                    # tail tip flicks light
    c.put(16, 3, rose[2])                      # the rose tie
    c.put(17, 3, rose[2])
    # big attentive eyes — a full row taller than the adults', catchlights on
    c.hline(8, 9, 8, P.void[1])                # thin brows, raised
    c.hline(13, 14, 8, P.void[1])
    c.hline(7, 9, 10, P.void[0])               # far eye
    c.put(7, 11, P.void[0])
    c.put(8, 11, paper[2])
    c.put(7, 12, P.void[0])
    c.put(8, 12, paper[2])
    c.hline(12, 15, 10, P.void[0])             # near eye, wider
    c.put(12, 11, P.void[0])
    c.put(13, 11, paper[2])
    c.put(14, 11, paper[2])
    c.put(15, 11, P.void[0])
    c.put(12, 12, P.void[0])
    c.put(13, 12, paper[2])
    c.put(14, 12, P.void[0])
    _nose(c, sk, sh)
    # mouth slightly open, mid-question
    c.hline(9, 10, 15, P.earth[1])
    c.put(9, 16, P.earth[1])
    c.put(10, 16, sh)
    # small shoulders, school cardigan, collar points
    rows = _shoulder_rows(24, 7, 24, (5, 2, 0))
    _garment(c, rows, ship[2], ship[1], ship[3], weave)
    c.put(12, 24, paper[2])                    # collar
    c.put(13, 24, paper[2])
    c.put(13, 25, paper[2])
    c.put(16, 24, paper[2])
    c.put(15, 25, paper[2])
    c.vline(14, 26, 31, ship[1])               # button track
    c.put(14, 27, ship[3])
    c.put(14, 30, ship[3])


# ---------------------------------------------------------------------------
# KADİR — tea house owner, 58. Balding, heavy brows, the softest eyes in
# town behind a grey moustache; dark vest over a paper shirt.
# ---------------------------------------------------------------------------

def _draw_kadir(c: PixelCanvas, P, spec: dict, weave: tuple) -> None:
    sk = _ref(P.pal, spec["skin"])
    sh = _ref(P.pal, spec["skin_shade"])
    hi = P.amber[2]
    grey = P.stone[2]
    void, paper = P.void, P.paper

    _neck(c, sk, sh, x0=11, x1=18, top=19, bot=23)
    _rows(c, sk, _HEAD_BROAD)
    _face_light(c, sk, sh, hi)
    _ear(c, sk, sh, hi, x=18)
    c.hline(12, 16, 3, hi)                     # the bald crown takes the light
    c.put(17, 4, hi)
    # grey horseshoe: sides and back only
    c.put(7, 6, grey)
    c.vline(7, 7, 8, grey)
    c.rect(18, 6, 4, 5, grey)
    c.rect(20, 11, 2, 3, grey)
    c.put(19, 6, P.stone[3])                   # lit grey wing
    c.put(21, 7, P.stone[3])
    # heavy brows over soft eyes
    c.hline(7, 9, 9, void[1])
    c.put(8, 8, void[1])
    c.hline(12, 15, 9, void[1])
    c.hline(13, 14, 8, void[1])
    _eyes_open(c, P)
    c.put(9, 13, sh)                           # warm bags — he laughs a lot
    c.hline(12, 13, 13, sh)
    _nose(c, sk, sh)
    # grey moustache, fuller than Musa's, hiding the smile
    c.hline(7, 13, 14, grey)
    c.hline(6, 13, 15, grey)
    c.put(6, 16, grey)
    c.put(13, 16, grey)
    c.put(8, 14, P.stone[3])                   # lit strands
    c.put(11, 14, P.stone[3])
    c.hline(9, 11, 17, P.earth[1])             # the smile it fails to hide
    c.put(12, 16, P.earth[1])
    c.put(9, 18, sh)
    # barrel chest: widest shoulders in the cast, vest over shirt
    rows = _shoulder_rows(22, 2, 29, (8, 4, 1))
    _garment(c, rows, void[2], void[1], void[3], weave)
    c.rect(12, 24, 6, 8, paper[2])             # shirt front
    c.vline(12, 24, 31, paper[1])
    c.put(12, 23, paper[2])                    # open collar
    c.put(13, 23, paper[2])
    c.put(17, 23, paper[2])
    c.put(16, 23, paper[2])
    c.put(14, 22, sk)                          # throat shows
    c.put(15, 22, sk)
    c.vline(11, 24, 31, void[1])               # vest edges
    c.vline(18, 24, 31, void[1])
    c.put(19, 25, void[3])                     # lit edge
    c.put(19, 28, void[3])
    c.put(14, 27, paper[1])                    # buttons
    c.put(14, 30, paper[1])


# ---------------------------------------------------------------------------
# İSMET — dolmuş driver, 48. Kasket pulled low, eyes in its shadow, one of
# them squinted shut against thirty years of switchback sun.
# ---------------------------------------------------------------------------

def _draw_ismet(c: PixelCanvas, P, spec: dict, weave: tuple) -> None:
    sk = _ref(P.pal, spec["skin"])
    sh = _ref(P.pal, spec["skin_shade"])
    hi = P.amber[2]
    earth, ship, paper = P.earth, P.ship, P.paper

    _neck(c, sk, sh, x0=12, x1=17, top=19)
    _rows(c, sk, _HEAD_LEAN)
    _face_light(c, sk, sh, hi)
    _ear(c, sk, sh, hi)
    # the kasket: round crown, brim jutting forward, worn low
    c.hline(9, 18, 2, earth[1])
    c.hline(8, 20, 3, earth[1])
    c.hline(7, 21, 4, earth[1])
    c.hline(7, 21, 5, earth[1])
    c.hline(7, 21, 6, earth[1])
    c.hline(15, 19, 2, earth[2])               # crown catches the light
    c.hline(17, 20, 3, earth[2])
    c.put(13, 2, earth[0])                     # crown button
    c.vline(14, 3, 5, earth[0])                # panel seam
    c.hline(4, 13, 7, earth[0])                # the brim, thrust out
    c.hline(5, 12, 8, earth[0])
    c.hline(14, 21, 7, earth[1])               # band back to the nape
    c.hline(8, 13, 9, sh)                      # brim shadow drowns the brow
    c.put(7, 9, sh)
    # one eye open, one squinted against the sun
    c.hline(8, 9, 11, P.void[0])               # open far eye
    c.put(8, 12, P.void[0])
    c.put(9, 12, paper[2])
    c.hline(12, 14, 11, P.void[0])             # near eye: a weathered slit
    c.hline(12, 14, 12, sh)
    c.put(15, 12, sh)                          # crow's feet
    c.put(15, 13, sh)
    _nose(c, sk, sh)
    c.put(9, 14, sh)                           # lean cheeks, drawn in
    c.put(16, 14, sh)
    _mouth(c, P, 8, 10)
    # work jacket, half-zipped; wiry shoulders
    rows = _shoulder_rows(23, 4, 26, (6, 3, 1))
    _garment(c, rows, ship[1], ship[0], ship[2], weave)
    c.put(11, 23, ship[0])                     # stand collar
    c.put(12, 23, ship[0])
    c.put(17, 23, ship[2])
    c.put(18, 23, ship[2])
    c.hline(13, 16, 24, paper[1])              # shirt in the open V
    c.put(13, 23, paper[1])
    c.put(16, 23, paper[1])
    c.vline(14, 25, 31, ship[2])               # zip track
    c.vline(15, 25, 31, ship[0])
    c.put(14, 25, ship[3])                     # zip pull
    c.vline(12, 25, 27, ship[0])               # placket crease
    c.vline(17, 25, 27, ship[2])


# ---------------------------------------------------------------------------
# METİN — observatory night operator, 58. Square jaw set, grey brush cut,
# grey stubble; ship work shirt held up by earth suspenders.
# ---------------------------------------------------------------------------

def _draw_metin(c: PixelCanvas, P, spec: dict, weave: tuple) -> None:
    sk = _ref(P.pal, spec["skin"])
    sh = _ref(P.pal, spec["skin_shade"])
    hi = P.amber[2]
    grey = P.stone[2]
    ship, earth, stone = P.ship, P.earth, P.stone

    _neck(c, sk, sh, x0=11, x1=18, top=19, bot=23)
    _rows(c, sk, _HEAD_SQUARE)
    _face_light(c, sk, sh, hi)
    _ear(c, sk, sh, hi, x=18)
    # the brush cut: dead flat on top, clippered tight at the sides
    c.hline(9, 19, 2, grey)
    c.hline(8, 20, 3, grey)
    c.hline(8, 20, 4, grey)
    c.put(7, 5, stone[1])                      # clipper fade at the temples
    c.rect(19, 5, 3, 5, stone[1])
    c.put(21, 10, stone[1])
    c.hline(14, 18, 2, stone[3])               # flat top catches the light
    # calm straight brows, steady eyes
    _brows(c, grey)
    _eyes_open(c, P)
    _nose(c, sk, sh)
    _mouth(c, P, 8, 11)                        # jaw set — a longer, firmer line
    c.put(8, 15, sh)                           # deep nasolabial cut
    # grey stubble: a shadow field hugging the jaw silhouette
    c.hline(9, 11, 18, stone[1])
    c.hline(10, 13, 19, stone[1])
    c.put(8, 17, stone[1])
    c.put(14, 18, stone[1])
    c.hline(16, 17, 16, sh)                    # jowl line at the jaw corner
    # broad shoulders, work shirt, suspenders doing their job
    rows = _shoulder_rows(22, 2, 29, (8, 4, 1))
    _garment(c, rows, ship[2], ship[1], ship[3], weave)
    c.put(12, 22, ship[1])                     # open collar points
    c.put(13, 23, ship[1])
    c.put(17, 22, ship[3])
    c.put(16, 23, ship[3])
    c.put(14, 22, sk)                          # throat in the open collar
    c.put(15, 22, sk)
    c.put(14, 23, sh)
    c.vline(9, 25, 31, earth[1])               # suspender straps
    c.vline(10, 25, 31, earth[1])
    c.vline(19, 25, 31, earth[1])
    c.vline(20, 25, 31, earth[1])
    c.put(9, 26, earth[0])                     # stitched edges
    c.put(19, 26, earth[0])
    c.put(10, 29, earth[2])                    # light rakes the near strap
    c.put(20, 28, earth[2])


# ---------------------------------------------------------------------------
# EBRU — PhD student, 27. Bright, sleep-deprived; loose strand at the
# temple, low ponytail over the shoulder, pencil behind the ear.
# ---------------------------------------------------------------------------

def _draw_ebru(c: PixelCanvas, P, spec: dict, weave: tuple) -> None:
    sk = _ref(P.pal, spec["skin"])
    sh = _ref(P.pal, spec["skin_shade"])
    hi = P.amber[2]
    hair = _ref(P.pal, spec["hair"]["color"])   # earth[0]
    rose, paper, earth = P.rose, P.paper, P.earth

    _neck(c, sk, sh, x0=12, x1=16, top=19)
    _rows(c, sk, _HEAD_LEAN)
    _face_light(c, sk, sh, hi)
    _ear(c, sk, sh, hi, x=16)
    # dark hair, swept back over the ear into a low tail
    c.hline(10, 17, 3, hair)
    c.hline(9, 19, 4, hair)
    c.hline(8, 20, 5, hair)
    c.put(8, 6, hair)
    c.rect(17, 6, 4, 5, hair)
    c.rect(18, 11, 3, 3, hair)
    c.hline(12, 15, 3, earth[1])               # sheen along the part
    c.put(17, 4, earth[1])
    c.put(18, 6, earth[1])
    # the loose strand she never pins back
    c.put(9, 5, hair)
    c.put(8, 7, hair)
    c.put(8, 8, hair)
    c.put(9, 9, hair)
    # low ponytail slipping over the near shoulder
    c.rect(19, 14, 3, 4, hair)
    c.rect(20, 18, 3, 5, hair)
    c.put(22, 23, hair)
    c.put(21, 24, hair)
    c.vline(21, 15, 19, earth[1])              # gathered strands catch light
    c.put(22, 21, earth[1])
    # the pencil behind the ear — her one piece of lab equipment
    c.hline(16, 20, 10, earth[3])
    c.put(21, 10, earth[1])                    # cut tip
    c.put(15, 10, P.void[1])                   # graphite point
    # bright eyes, thin brows, sleep shadows
    _brows(c, hair)
    _eyes_open(c, P)
    c.put(8, 13, sh)                           # the deadline under-eyes
    c.hline(12, 13, 13, sh)
    _nose(c, sk, sh)
    _mouth(c, P, 8, 10, lip=hi)
    c.put(11, 15, P.earth[1])                  # quick half-smile
    # oversized sweater: wide soft slope, collar peeking at the neck
    rows = _shoulder_rows(23, 4, 27, (6, 3, 1))
    _garment(c, rows, rose[1], rose[0], rose[2], weave)
    c.hline(12, 13, 22, paper[2])              # collar points peeking out
    c.hline(16, 17, 22, paper[2])
    c.hline(11, 18, 23, rose[0])               # wide loose neckline
    c.hline(6, 9, 26, rose[0])                 # slouched fold lines
    c.hline(20, 24, 27, rose[0])
    c.hline(5, 26, 31, rose[0])                # heavy ribbed hem
    for x in range(6, 26, 3):
        c.put(x, 31, rose[1])


# ---------------------------------------------------------------------------
# TEZCAN — observatory director, 63. Round glasses catching the light so you
# never quite see the eyes; suit, tie, administrator calm.
# ---------------------------------------------------------------------------

def _draw_tezcan(c: PixelCanvas, P, spec: dict, weave: tuple) -> None:
    sk = _ref(P.pal, spec["skin"])
    sh = _ref(P.pal, spec["skin_shade"])
    hi = P.amber[2]
    grey = P.stone[2]
    lens = P.stone[3]
    stone, paper, rose = P.stone, P.paper, P.rose

    _neck(c, sk, sh, x0=12, x1=17, top=19)
    _rows(c, sk, _HEAD_BROAD)
    _face_light(c, sk, sh, hi)
    _ear(c, sk, sh, hi, x=18)
    c.hline(12, 16, 3, hi)                     # bald crown, lit
    c.put(17, 4, hi)
    c.put(7, 6, grey)                          # grey confined to the sides
    c.put(7, 7, grey)
    c.rect(18, 6, 4, 5, grey)
    c.rect(20, 11, 2, 3, grey)
    c.put(19, 6, stone[3])
    # thin brows kept well above the frames
    c.hline(8, 9, 8, grey)
    c.hline(12, 14, 8, grey)
    # round glasses, both lenses full of window light
    c.rect(7, 10, 3, 3, lens)
    c.put(7, 10, stone[1])                     # round: corners knocked dark
    c.put(9, 12, stone[1])
    c.rect(12, 10, 3, 3, lens)
    c.put(14, 10, stone[1])
    c.put(12, 12, stone[1])
    c.hline(10, 11, 11, stone[1])              # bridge
    c.hline(15, 17, 11, stone[1])              # temple arm to the ear
    _nose(c, sk, sh)
    _mouth(c, P, 8, 10)                        # perfectly level. unreadable.
    c.hline(15, 16, 15, sh)                    # careful jowls
    # the suit: square shoulders, lapels, the rose tie
    rows = _shoulder_rows(23, 3, 28, (7, 3, 1))
    _garment(c, rows, stone[1], stone[0], stone[2], weave)
    c.put(12, 23, paper[2])                    # shirt V
    c.hline(13, 16, 24, paper[2])
    c.put(17, 23, paper[2])
    c.put(14, 23, rose[1])                     # tie knot
    c.put(15, 23, rose[1])
    c.vline(14, 25, 30, rose[1])               # the tie
    c.vline(15, 25, 29, rose[0])
    c.put(14, 31, rose[0])                     # its point
    c.vline(12, 24, 31, stone[0])              # lapel lines
    c.vline(13, 25, 31, stone[0])
    c.vline(17, 24, 31, stone[0])
    c.vline(16, 25, 31, stone[0])
    c.put(18, 25, stone[2])                    # lit lapel edge
    c.put(18, 28, stone[2])


_DRAWERS = {
    "yildiz": _draw_yildiz,
    "fadime": _draw_fadime,
    "musa": _draw_musa,
    "sukru": _draw_sukru,
    "elif": _draw_elif,
    "kadir": _draw_kadir,
    "ismet": _draw_ismet,
    "metin": _draw_metin,
    "ebru": _draw_ebru,
    "tezcan": _draw_tezcan,
}
