"""Pipeline determinism: a double build must be byte-identical (plan 4.4).

Runs every manifest twice against the real output tree and compares hashes.
Generators may only draw from random.Random(manifest["seed"]) — wall-clock
or global-RNG leakage shows up here as a diff.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from artgen import OUT_ROOT
from artgen.build import build


def _hash_tree(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(Path(root).rglob("*")):
        if path.suffix in (".png", ".json") and path.is_file():
            hashes[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def test_double_build_is_byte_identical() -> None:
    assert build() == 0, "first build failed (generator or lint error)"
    first = _hash_tree(OUT_ROOT)
    assert first, "build produced no PNG/JSON outputs"
    assert build() == 0, "second build failed"
    second = _hash_tree(OUT_ROOT)
    changed = {k for k in first if first[k] != second.get(k, "")}
    missing = set(first) ^ set(second)
    assert not changed and not missing, (
        f"non-deterministic outputs — changed: {sorted(changed)}, set-diff: {sorted(missing)}"
    )
