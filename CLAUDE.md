# THE ABOVE — Claude Work Guide

Claude is the project's design and complex-problem owner. Codex owns routine implementation.
Read this file, `ARCHITECTURE.md`, `PLAN.md`, and `PROGRESS.md` before starting work.

## What Claude owns

Use Claude for work where the correct implementation should be decided before code is written:

- UI/UX direction: screen hierarchy, interaction states, visual language, accessibility, and Godot scene/component plans.
- Complex systems or cross-cutting changes: new game mechanics, persistence or state-model changes, multi-system integrations, performance-sensitive work, export/platform constraints, and security or data-integrity decisions.
- Architecture, story-system design, technical investigation, and resolving requirements that are incomplete or conflicting.

Claude should produce a decision-ready handoff, not implementation code, unless the user explicitly asks Claude to implement it.

## Required handoff to Codex

When the design or investigation is complete, create or update a focused handoff in the repository, normally `docs/decisions/` for durable decisions, or the relevant design document. It must include:

1. Goal and player-facing outcome.
2. Scope: exact files/systems to add or change, plus explicit non-goals.
3. Chosen approach and the important alternatives rejected.
4. UI specification when applicable: layout hierarchy, states, input behaviour, copy/localization keys, visual constraints, and screenshot-tour coverage.
5. Data contracts, invariants, failure behaviour, and migration notes when state is affected.
6. Acceptance criteria and exact validation commands for Codex.

Keep the handoff implementable in a bounded coding pass. If more design decisions emerge while Codex is implementing, Codex must stop and hand the work back rather than choosing a speculative design.

## Claude completion boundary

Once the work has a stable, explicit implementation plan, Claude's task is complete. The user then switches to a Codex-family model for all code, tests, resource generation, and routine documentation.

Do not silently revise `PLAN.md` or `PROGRESS.md` as part of a Claude design pass. Update them only when the user specifically asks or when the agreed project workflow calls for a milestone status change.

## Project facts

- Godot 4.5.2-stable; Compatibility renderer; pixel-art cosmic-horror narrative game.
- The public repository is `krem4d/the-above`; public story material is intentional.
- The current implementation milestone is recorded in `PROGRESS.md`. The delivery sequence is in `PLAN.md`.
- Architecture constraints are authoritative in `ARCHITECTURE.md`. The full creative source is `~/.claude/plans/i-want-to-develop-sunny-coral.md` when available.

## Current status

Milestones complete: M0 (toolchain/skeleton), M1 (pipeline risk burn-down), M-STORY (full 3-act story bible + all Act 1 `.scene` scripts, EN+TR), M2 (core narrative systems + UI slice), M3 (spectrogram/Waterfall mechanic v1 — the `spectro` DSL command now runs a real minigame).

Next up: M4 (Act 1 world & Day 1 playable: real art, room scenes, day-loop scaffolding).

Milestone-by-milestone detail and the commit log live in `PROGRESS.md` (living tracker; update it when a checkbox flips). The forward build list with exit gates is `PLAN.md`. Don't duplicate either here — this file is architecture and gotchas only.

## Repository layout

```
The_Above/
├── Makefile
├── game/                    # Godot project root
│   ├── project.godot, export_presets.cfg
│   ├── scenes/{main,rooms/act1,ui,actors,minigames}/
│   ├── scripts/{autoload,systems,actors,ui}/
│   ├── story/{scripts/act1/*.scene, missions/, signals/}   # runtime data, inside res://
│   ├── locale/              # act1_dialogue.csv, ui.csv -> auto-imported .translation resources
│   ├── assets/{gen/ (artgen output, committed), fonts/, audio/}
│   ├── tools/               # gen_resources.gd, tour.json, screenshot-tour harness
│   ├── tests/  └── addons/gdUnit4/
├── artgen/                  # Python art pipeline (palettes/, manifests/, artgen/)
├── audiogen/                # Python audio synthesis (mirrors artgen, not yet built out)
├── story/                   # design docs: bible.md, secret-bible.md, characters.md, clip-anchors.md
├── docs/decisions/          # ADRs
├── marketing/                # clip-anchor storyboards, itch copy
└── artifacts/               # tour screenshots, exports, test userdir — gitignored
```

`story/secret-bible.md` holds the actual twist/ending. This repo is public by the user's explicit choice, so treat it as already-shared, not held back.

## Autoload boot order

```
Locale → GameState → MetaPersistence → SaveSystem → AudioManager → SceneDirector → DialogueRunner → Debug
```

Autoloads `_ready()` before the main scene enters the tree. Anything needing scene-tree refs (`SceneDirector.world_holder`, `DialogueRunner`'s DialogueBox/ChoiceMenu/FadeRect) gets them from an explicit public setter called in `game/scripts/main.gd`'s `_ready()` — never via `@onready get_node("Main/...")` absolute paths.

## GDScript gotchas

- Variant `==` throws across incompatible types, for example `bool == int`, but compares `int`/`float` safely. Guard with `typeof(a) == typeof(b)` before `==`, or use a plain truthy `if x:` check.
- JSON round-trip collapses `int` to `float` (`JSON.parse_string("5")` then `stringify()` gives `"5.0"`). `SaveSystem` hashes the payload as a stored/read-back string, never re-serializes a parsed Dictionary before checksumming.
- Lambda closures capture locals by value, not reference. `func(): outer += 1` inside a connected signal lambda won't mutate `outer`. Use a single-element `Array` as a mutable box: `var counter := [0]`.
- Turkish İ/ı casing: never call `.to_upper()`, `.to_lower()`, or `.capitalize()` on player-facing text at runtime. GDScript is locale-blind and mangles dotted/dotless I. Casing is baked into translations instead.
- GdUnit4 treats some compiler warnings as fatal during test discovery, including Variant-type-inference warnings and a local shadowing a base-class method name. Annotate types explicitly and avoid name collisions with GdUnitTestSuite members.

## Dialogue / cutscene DSL

Hand-rolled plain-text `.scene` format, not Dialogic, chosen for AI-authorability, diffability, and full localization ownership. Dialogue text is never inline; only keys, resolved against `game/locale/act1_dialogue.csv` (`keys,en,tr`).

Command set: `say`, `choice`/`option`, `label`/`jump`, `setflag`, `if`/`else`/`end`, `move`, `face`, `teleport`, `show`/`hide`, `pan`, `zoom`, `shake`, `wait`, `sfx`, `music`, `fade`, `spectro`, `mode`, `mission`, `goto_room`, `title_variant`, `end_scene`.

`game/scripts/systems/dialogue_parser.gd` (`class_name DialogueParser`, static `parse()`) produces a flat instruction list with pre-resolved label/if-else jump indices. `DialogueRunner` is an await-based coroutine, no threads.

Example:

```text
[scene d2_observatory_intro]
mode cutscene
music obs_hum fade=2.0
move ada door_south
say ada d2.obs.ada.001
choice
  option d2.obs.choice.heard -> heard_it
  option d2.obs.choice.deny  -> denied
label heard_it
setflag ada_admitted_hearing true
...
spectro sig_first_anomaly
mode free_roam
mission d2_find_logbook
```

## Spectrogram / waterfall minigame

The `spectro <id>` DSL command runs a real minigame. Same pure-logic / presentation split as the DSL: `WaterfallSession` (`game/scripts/systems/waterfall_session.gd`) is engine-free per-session state, unit-tested like `DialogueParser`; `WaterfallView` (`game/scripts/ui/waterfall_view.gd` + `scenes/minigames/waterfall_view.tscn`) is the Control that mirrors `ChoiceMenu`'s contract exactly. `start_session()` shows it, `DialogueRunner` awaits `session_closed` the way it awaits `ChoiceMenu.chosen`. `WaterfallCanvas` draws the scrolling spectrogram procedurally.

Session configs live in `game/story/signals/spectro_sessions.json`, parsed by `WaterfallSessionLibrary`, keyed by the exact `spectro <id>` used in the Act 1 `.scene` files. A GdUnit4 test asserts every referenced id exists and that each session can render its trace when tuned.

`kind` selects the win condition: `tutorial` (tune+hold), `beam_scan` (visit all 3 beams), `onoff` (see both states), and `broadcast`/`taxonomy`/`answer_gate`/`keystone` (timed, narrative tags). Fake physics throughout: `drift_mhz_s` moves the target, `cell_seconds > 0` gives the canon 11-minute broadcast a visible on/off cadence, the noise background is deterministic seeded speckle. Timed `events` open payload windows: `shape_burst` is a broadband magenta smear; `decode_text` is a readout line resolving a locale key or the observer name placeholder.

`_do_spectro` in `DialogueRunner` enters `MINIGAME` mode, runs the session, restores the prior mode, and writes `spectro_<id>_done` into GameState so later `.scene` content can branch on it. Design law wiring: no minigame is a fail state; `cancel` always closes; and the ANSWER verb is gated by a per-session flag that no Act 1 session enables.

## Save / meta-persistence

- `user://saves/slot_N.json`: `{version, checksum (sha256 of the payload string), payload}`. Atomic writes: `.tmp` → verify → rename, `.bak` kept and only refreshed from an already-valid slot file. Load falls back checksum-mismatch → `.bak` → clean-new-game; never crashes.
- `user://meta.json` plus a byte-identical shadow copy track language pref, permanent story facts, and per-slot save-generation counters. If meta recorded a higher generation than the save file that exists, the game knows the player deleted it.
- Known accepted gaps, documented inline in code: a narrow crash window between a save's rename and its generation-counter bump; an int flag can come back as a float after a save/load round-trip. Both are low-probability, currently dormant, and no content exercises either path yet.

## Testing

GdUnit4 in `game/tests/` covers engine-level logic: DSL parser, DialogueRunner, Locale, GameState, SaveSystem, MetaPersistence, SceneDirector, and the Turkish-casing-safety grep-test. `artgen/tests/` with pytest covers art-pipeline determinism and palette linting. Rendering correctness is verified visually via the screenshot tour, not asserted in tests.

## Art pipeline

Python/Pillow, single source of truth palette at `artgen/palettes/the_above.json`. `canvas.py` hard-fails on any color outside the palette; shading only via `ramp_shade(light_dir)`; dithering only via an ordered-Bayer helper. Atlas coordinates are append-only: regenerating art must never invalidate a committed `.tres`, TileMapLayer, or scene. Determinism is enforced from manifests only, with byte-equality checks.

## Repo / remote

Public GitHub repo `krem4d/the-above`, deliberately public by the user's explicit call.
