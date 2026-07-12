"""PixelCanvas — a palette-enforcing drawing surface over Pillow.

Structural anti-ugliness guards (plan section 4.4):
- every pixel must come from the palette (hard fail otherwise)
- shading only via ramp indices (no ad-hoc RGB math)
- outlines default to the ramp's darkest color, never pure black
- dithering only via the ordered-Bayer helper, max 2 adjacent ramp steps
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from .palette import Palette, Ramp, RGBA

TRANSPARENT: RGBA = (0, 0, 0, 0)

# 4x4 ordered Bayer matrix, thresholds 0..15
_BAYER4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


class PixelCanvas:
    def __init__(
        self,
        width: int,
        height: int,
        palette: Palette,
        *,
        allow_forbidden: bool = False,
    ) -> None:
        self.width = width
        self.height = height
        self.palette = palette
        self._allowed = palette.allowed_colors(allow_forbidden=allow_forbidden)
        self._img = Image.new("RGBA", (width, height), TRANSPARENT)
        self._px = self._img.load()

    # -- primitives ---------------------------------------------------------

    def put(self, x: int, y: int, color: RGBA) -> None:
        if color != TRANSPARENT and color not in self._allowed:
            raise ValueError(f"color {color} is not in palette {self.palette.name!r}")
        if 0 <= x < self.width and 0 <= y < self.height:
            self._px[x, y] = color

    def put_ramp(self, x: int, y: int, ramp: Ramp, idx: int) -> None:
        self.put(x, y, ramp[max(0, min(idx, len(ramp) - 1))])

    def get(self, x: int, y: int) -> RGBA:
        return self._px[x, y]

    def rect(self, x0: int, y0: int, w: int, h: int, color: RGBA) -> None:
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.put(x, y, color)

    def hline(self, x0: int, x1: int, y: int, color: RGBA) -> None:
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.put(x, y, color)

    def vline(self, x: int, y0: int, y1: int, color: RGBA) -> None:
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.put(x, y, color)

    # -- guarded helpers ----------------------------------------------------

    def dither_rect(
        self, x0: int, y0: int, w: int, h: int, ramp: Ramp, idx_a: int, idx_b: int, density: float
    ) -> None:
        """Ordered-Bayer blend between two ADJACENT ramp steps.

        ``density`` in [0,1] biases toward idx_b. Only adjacent steps are
        allowed — anything wider reads as noise-confetti.
        """
        if abs(idx_a - idx_b) > 1:
            raise ValueError("dither only between adjacent ramp steps")
        threshold = max(0.0, min(density, 1.0)) * 16.0
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                use_b = _BAYER4[y % 4][x % 4] < threshold
                self.put_ramp(x, y, ramp, idx_b if use_b else idx_a)

    def outline(self, ramp: Ramp) -> None:
        """1px outline around all opaque regions, in the ramp's darkest color."""
        src = self._img.copy()
        px = src.load()
        for y in range(self.height):
            for x in range(self.width):
                if px[x, y][3] != 0:
                    continue
                touches = any(
                    0 <= x + dx < self.width
                    and 0 <= y + dy < self.height
                    and px[x + dx, y + dy][3] != 0
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                )
                if touches:
                    self.put(x, y, ramp.darkest)

    def paste(self, other: "PixelCanvas", x: int, y: int) -> None:
        for sy in range(other.height):
            for sx in range(other.width):
                c = other.get(sx, sy)
                if c[3] != 0:
                    self.put(x + sx, y + sy, c)

    # -- output -------------------------------------------------------------

    def to_image(self) -> Image.Image:
        return self._img.copy()

    def save(self, path: Path, *, scale: int = 1) -> None:
        """Save as PNG; ``scale`` bakes nearest-neighbor upscale (the 2x world contract)."""
        img = self._img
        if scale != 1:
            img = img.resize((self.width * scale, self.height * scale), Image.NEAREST)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Fixed parameters keep byte-identical output across runs (determinism contract).
        img.save(path, format="PNG", optimize=False)
