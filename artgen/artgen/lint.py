"""pixel-lint — re-open every emitted PNG and verify the palette contract."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from .palette import Palette


def lint_png(path: Path, palette: Palette) -> list[str]:
    """Return a list of violations (empty = clean)."""
    errors: list[str] = []
    img = Image.open(path).convert("RGBA")
    allowed = palette.allowed_colors(allow_forbidden=True)
    seen = {c for _, c in img.getcolors(maxcolors=1 << 20) or []}
    for color in seen:
        if color[3] == 0:
            continue
        if color[3] != 255:
            errors.append(f"{path.name}: semi-transparent pixel {color}")
        elif color not in allowed:
            errors.append(f"{path.name}: color {color} outside palette")
    return errors


def lint_tree(root: Path, palette: Palette) -> list[str]:
    errors: list[str] = []
    for png in sorted(Path(root).rglob("*.png")):
        errors.extend(lint_png(png, palette))
    return errors
