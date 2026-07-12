"""Palette loading — the ONLY legal way for generators to obtain a color."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

RGBA = tuple[int, int, int, int]


def _hex_to_rgba(value: str) -> RGBA:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"palette colors must be #rrggbb, got {value!r}")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), 255)


@dataclass(frozen=True)
class Ramp:
    """An ordered dark->light run of colors."""

    name: str
    colors: tuple[RGBA, ...]

    def __getitem__(self, idx: int) -> RGBA:
        return self.colors[idx]

    def __len__(self) -> int:
        return len(self.colors)

    @property
    def darkest(self) -> RGBA:
        return self.colors[0]

    @property
    def lightest(self) -> RGBA:
        return self.colors[-1]


class Palette:
    """Master palette with hard membership checks.

    Forbidden ramps (the signal-magenta grammar) are excluded from
    ``allowed`` unless the caller explicitly opts in.
    """

    def __init__(self, path: Path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.name: str = data["name"]
        self.ramps: dict[str, Ramp] = {
            name: Ramp(name, tuple(_hex_to_rgba(c) for c in colors))
            for name, colors in data["ramps"].items()
        }
        self.forbidden_ramps: dict[str, Ramp] = {
            name: Ramp(name, tuple(_hex_to_rgba(c) for c in colors))
            for name, colors in data.get("forbidden", {}).items()
        }
        overlap = {c for r in self.ramps.values() for c in r.colors} & {
            c for r in self.forbidden_ramps.values() for c in r.colors
        }
        if overlap:
            raise ValueError(f"forbidden colors overlap base palette: {overlap}")

    def ramp(self, name: str, *, allow_forbidden: bool = False) -> Ramp:
        if name in self.ramps:
            return self.ramps[name]
        if name in self.forbidden_ramps:
            if not allow_forbidden:
                raise PermissionError(
                    f"ramp {name!r} is forbidden (signal grammar) — "
                    "pass allow_forbidden=True only in signal-connected generators"
                )
            return self.forbidden_ramps[name]
        raise KeyError(f"unknown ramp {name!r}")

    def allowed_colors(self, *, allow_forbidden: bool = False) -> frozenset[RGBA]:
        colors = {c for r in self.ramps.values() for c in r.colors}
        if allow_forbidden:
            colors |= {c for r in self.forbidden_ramps.values() for c in r.colors}
        return frozenset(colors)
