"""Build entry point: run every generator declared by a manifest, then lint.

Each manifest in ``manifests/*.json`` names a generator module
(``"generator": "tiles.town_exterior"``) whose ``generate(manifest, palette,
out_root)`` writes PNG sheets + JSON sidecars into game/assets/gen/.
Determinism contract: generators seed ``random.Random(manifest["seed"])``
only — never the global RNG, never wall-clock.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from . import MANIFESTS_DIR, OUT_ROOT, PALETTE_PATH
from .lint import lint_tree
from .palette import Palette


def load_manifests(only: str | None = None) -> list[dict]:
    manifests = []
    for path in sorted(MANIFESTS_DIR.glob("*.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["_path"] = str(path)
        if only is None or only in (path.stem, manifest.get("generator", "")):
            manifests.append(manifest)
    return manifests


def build(only: str | None = None) -> int:
    palette = Palette(PALETTE_PATH)
    manifests = load_manifests(only)
    if not manifests:
        print(f"no manifests matched (looked in {MANIFESTS_DIR})")
        return 0
    for manifest in manifests:
        module = importlib.import_module(f"artgen.{manifest['generator']}")
        print(f"generating {manifest['generator']} -> {OUT_ROOT}")
        module.generate(manifest, palette, OUT_ROOT)
    errors = lint_tree(OUT_ROOT, palette)
    if errors:
        for err in errors:
            print(f"LINT: {err}", file=sys.stderr)
        return 1
    print(f"build OK ({len(manifests)} manifest(s)), lint clean")
    return 0
