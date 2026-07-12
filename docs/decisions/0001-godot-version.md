# ADR 0001: Pin Godot 4.5.2-stable (official binary)

**Status:** accepted (2026-07-12)

## Decision

The project uses **Godot 4.5.2-stable, official build** (`4.5.2.stable.official.6ce3de25a`), kept at
`~/apps/godot-4.5.2/godot`, invoked via the `GODOT` variable in the top-level `Makefile`.

The system `pacman` Godot (4.7.x at time of writing) is NOT used: Arch is rolling and would bump the
engine mid-production, and the research phase flagged 4.6+/4.7 web-export regressions for features we
don't need. 4.5.x has mature Web export, `Parallax2D`, and the stable `TileMapLayer` API.

## Consequences

- `main.gd` performs a startup check and pushes a warning if `Engine.get_version_info()` doesn't
  match `4.5.x` — catches accidental runs with the system binary.
- Renderer is **Compatibility (GL)** on all platforms (web only supports Compatibility; desktop uses
  it too for parity).
- Upgrading the engine is a deliberate ADR-superseding decision, never a side effect.
