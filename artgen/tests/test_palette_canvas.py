"""Palette + canvas contract tests (AAA style)."""

import pytest

from artgen import PALETTE_PATH
from artgen.canvas import PixelCanvas
from artgen.palette import Palette


@pytest.fixture()
def palette() -> Palette:
    return Palette(PALETTE_PATH)


def test_master_palette_has_28_base_colors(palette: Palette) -> None:
    assert len(palette.allowed_colors()) == 28


def test_forbidden_signal_color_excluded_by_default(palette: Palette) -> None:
    signal = palette.ramp("signal", allow_forbidden=True)[0]
    assert signal not in palette.allowed_colors()
    assert signal in palette.allowed_colors(allow_forbidden=True)


def test_forbidden_ramp_requires_opt_in(palette: Palette) -> None:
    with pytest.raises(PermissionError):
        palette.ramp("signal")


def test_canvas_rejects_out_of_palette_color(palette: Palette) -> None:
    canvas = PixelCanvas(4, 4, palette)
    with pytest.raises(ValueError):
        canvas.put(0, 0, (128, 128, 128, 255))


def test_canvas_rejects_forbidden_color_without_opt_in(palette: Palette) -> None:
    canvas = PixelCanvas(4, 4, palette)
    signal = palette.ramp("signal", allow_forbidden=True)[0]
    with pytest.raises(ValueError):
        canvas.put(0, 0, signal)


def test_dither_rejects_non_adjacent_ramp_steps(palette: Palette) -> None:
    canvas = PixelCanvas(8, 8, palette)
    with pytest.raises(ValueError):
        canvas.dither_rect(0, 0, 8, 8, palette.ramp("stone"), 0, 2, 0.5)


def test_save_bakes_nearest_neighbor_scale(tmp_path, palette: Palette) -> None:
    canvas = PixelCanvas(2, 2, palette)
    ramp = palette.ramp("stone")
    canvas.put_ramp(0, 0, ramp, 0)
    out = tmp_path / "t.png"

    canvas.save(out, scale=2)

    from PIL import Image

    img = Image.open(out)
    assert img.size == (4, 4)
    assert img.getpixel((0, 0)) == img.getpixel((1, 1)) == ramp[0]
