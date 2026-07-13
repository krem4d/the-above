# THE ABOVE — Technical Architecture

This document is the technical source of truth for implementation constraints. Product sequencing and
scope live in [`PLAN.md`](PLAN.md); current completion state lives in [`PROGRESS.md`](PROGRESS.md).

## Platform baseline

- Engine: **Godot 4.5.2-stable**, using `~/apps/godot-4.5.2/godot` through the top-level `Makefile`.
  Do not upgrade casually; see `docs/decisions/0001-godot-version.md`.
- Renderer: Compatibility (GL) on every target. The web build is single-threaded
  (`thread_support=false`); generator audio is latency-fragile there.
- Game: 640×360 pixel-art cosmic-horror narrative game, rendered pixel-crisp using nearest-neighbour
  scaling. Player-facing English and Turkish strings are localization data, not inline dialogue.

## Repository map

```text
The_Above/
├── Makefile                       # project commands and isolated test setup
├── game/                          # Godot project root (res://)
│   ├── scenes/{main,rooms/act1,ui,actors,minigames}/
│   ├── scripts/{autoload,systems,actors,ui}/
│   ├── story/{scripts/act1,missions,signals}/
│   ├── locale/                    # CSV -> imported translation resources
│   ├── assets/{gen,fonts,audio}/  # generated art is committed
│   ├── tools/                     # resource generation and screenshot tour
│   └── tests/                     # GdUnit4 tests
├── artgen/                        # deterministic Python/Pillow art pipeline
├── audiogen/                      # future deterministic audio tooling
├── story/                         # story/design source documents
├── docs/decisions/                # architecture decision records
├── marketing/                     # clip anchors and store copy
└── artifacts/                     # generated screenshots, exports, test user data; ignored
```

`story/secret-bible.md` contains the ending. This repository is deliberately public, so it is not a
secret-management boundary.

## Runtime ownership and boot order

Autoloads must load in this exact order:

```text
Locale → GameState → MetaPersistence → SaveSystem → AudioManager → SceneDirector → DialogueRunner → Debug
```

Autoload `_ready()` runs before the main scene enters the tree. Autoloads requiring scene-tree nodes
receive them through explicit public setters from `game/scripts/main.gd`'s `_ready()`. Do not use
absolute `@onready get_node("Main/...")` paths from an autoload.

`ControlMode` gates player interaction between cutscene, free-roam, mission, and minigame states.
Room scenes extend `room.gd`; use named `Marker2D` spawn points and keep the room's tile, props, NPC,
trigger, and camera responsibilities separated.

## Dialogue and localization contracts

The hand-authored `.scene` DSL is the narrative runtime format. It is parsed by
`game/scripts/systems/dialogue_parser.gd` (`DialogueParser.parse()`) into a flat instruction list with
pre-resolved label and conditional jumps. `DialogueRunner` is an await-based coroutine, not a threaded
system.

Supported commands: `say`, `choice`/`option`, `label`/`jump`, `setflag`, `if`/`else`/`end`, `move`,
`face`, `teleport`, `show`/`hide`, `pan`, `zoom`, `shake`, `wait`, `sfx`, `music`, `fade`, `spectro`,
`mode`, `mission`, `goto_room`, `title_variant`, and `end_scene`.

Dialogue text never appears inline in a `.scene`; it uses keys resolved from
`game/locale/act1_dialogue.csv` (`keys,en,tr`). Do not apply runtime uppercase/lowercase/capitalization
to player-facing text: GDScript is locale-blind and corrupts Turkish dotted/dotless I. The static
Turkish-casing safety test enforces this in game scripts and scenes.

## State and persistence (no database)

There is no server or relational database. Persistence is local, versioned JSON under `user://`:

| File | Responsibility | Invariant |
|---|---|---|
| `user://saves/slot_N.json` | Per-slot game state | `{version, checksum, payload}`; checksum is SHA-256 of the stored payload string. |
| `user://saves/slot_N.json.bak` | Recovery copy | Refreshed only from a valid slot file. |
| `user://meta.json` + byte-identical shadow | Language, permanent facts, save-generation counters | Detects deleted/replaced saves via generation counters. |

Save writes are atomic: write `.tmp`, verify, then rename; retain `.bak`. Load must fall back from a
checksum mismatch to `.bak`, then to a clean new game, never crash. Because JSON round-tripping turns
integers into floats, do not parse and re-serialize a payload before verifying its checksum. The known
accepted edge cases are a narrow crash window before the generation-counter bump and an integer flag
returning as a float after load; do not "fix" either without an approved migration design.

## GDScript correctness constraints

- Comparing incompatible `Variant` types with `==` can throw. Guard with matching `typeof()` values,
  or use an appropriate truthy check.
- Lambda closures capture locals by value. For a mutable counter across a signal lambda, use a
  single-element `Array` box.
- GdUnit4 test discovery treats several warnings as fatal. Add explicit types where needed and avoid
  locals that shadow `GdUnitTestSuite` members.
- `DialogueRunner`, `GameState`, save/meta code, and autoload order are load-bearing. Do not change
  their contracts opportunistically.

## Asset and generated-resource rules

`artgen/` is Python/Pillow. Its palette (`artgen/palettes/the_above.json`) is the sole color source:
the canvas fails on out-of-palette colors, shading uses `ramp_shade(light_dir)`, and dithering uses the
ordered-Bayer helper. Atlas coordinates are append-only; regenerated art must not invalidate committed
`.tres`, `TileMapLayer`, or scene data. Determinism is mandatory and covered by pytest byte-equality.

Use `make resources` to regenerate SpriteFrames/TileSet `.tres` files from sidecars. Do not hand-edit
generated output unless the relevant generator contract explicitly requires it.

## Verification and commands

```text
make run                         # launch windowed game
make test                        # GdUnit4, isolated user-data dir
make pytest                      # art pipeline determinism and palette lint
make art                         # regenerate art
make resources                   # regenerate Godot resource data
make tour                        # screenshot tour -> artifacts/shots/
make tour-scene SCENE=<id>       # focused screenshot tour
make export-web|export-linux|export-windows
```

Always run tests via the Makefile. Its `--user-data-dir` isolation is required; running Godot tests
without it can mutate the real local save directory.

Milestone exit gates require the relevant automated checks to be green and a reviewed `make tour`.
For exported web work, verify Chrome and Firefox, the audio-unlock click gate, and IndexedDB save
persistence before declaring the browser target done.

## Git and collaboration boundaries

The remote is public GitHub repository `krem4d/the-above`. Keep commits small, focused, and verified.
The working tree may contain user work; preserve it and never use destructive cleanup commands. Codex
implements approved work under [`AGENTS.md`](AGENTS.md); Claude designs UI and resolves complex or
cross-cutting decisions under [`CLAUDE.md`](CLAUDE.md).
