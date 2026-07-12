"""Deterministic, palette-locked pixel-art pipeline for THE ABOVE."""

from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent.parent
PALETTE_PATH = PKG_ROOT / "palettes" / "the_above.json"
MANIFESTS_DIR = PKG_ROOT / "manifests"
# Output goes directly into the Godot tree (plan section 4/5).
OUT_ROOT = PKG_ROOT.parent / "game" / "assets" / "gen"
