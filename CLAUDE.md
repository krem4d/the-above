# THE ABOVE — Project Guide for Claude Code

Pixel-art cosmic-horror narrative game. Undertale-structured (cutscene-driven, mission-gated
exploration), bilingual EN+TR, set in a fictional Turkish mountain town (Taşlıca) beneath a national
observatory. This file is the onboarding doc for a fresh Claude Code session — read it before touching
code.

**Full creative/technical master plan (canonical source of truth):**
`/home/rocket/.claude/plans/i-want-to-develop-sunny-coral.md` — story bible summary, art direction,
audio direction, virality plan, full technical architecture, repo layout, milestone list M0–M6, risks.
Read that file for anything not covered below.

## Model workflow policy

**Use Fable 5 for the rest of this project. Do not switch models between UI and code work** — an
earlier Fable5-for-UI/Sonnet5-for-code split was tried and has been dropped. No warning or pause
before UI work is needed anymore.

## Current status (as of 2026-07-13)

Milestones complete: **M0** (toolchain/skeleton), **M1** (pipeline risk burn-down), **M-STORY** (full
3-act story bible + all Act 1 `.scene` scripts, EN+TR), **M2** (core narrative systems + UI slice),
**M3** (spectrogram/Waterfall mechanic v1 — the `spectro` DSL command now runs a real minigame).

Next up: **M4** (Act 1 world & Day 1 playable: real art, room scenes, day-loop scaffolding).

Milestone-by-milestone detail and the commit log live in **`PROGRESS.md`** (living tracker; update it
when a checkbox flips). The forward build list with exit gates is **`PLAN.md`**. Don't duplicate
either here — this file is architecture and gotchas only.

## Engine & pinned version

Godot **4.5.2-stable** official binary, kept at `~/apps/godot-4.5.2/godot`, referenced via the
`GODOT` variable in the top-level `Makefile`. See `docs/decisions/0001-godot-version.md` — do not
upgrade the engine casually; it's a deliberate ADR-superseding decision, not a side effect. Renderer is
Compatibility (GL) on every platform (desktop matches the web-export-only-supported renderer).

## Key commands (top-level `Makefile`)

```
make run            # launch the game (windowed)
make test            # GdUnit4 headless suite, isolated --user-data-dir under artifacts/
make pytest           # artgen's Python test suite (byte-identical determinism, palette lint)
make art              # regenerate all art via artgen/
make tour              # full screenshot tour (game/tools/tour.json) -> artifacts/shots/
make tour-scene SCENE=<id>   # single-scene screenshot, tight iteration loop
make resources          # (re)import + regenerate SpriteFrames/TileSet .tres from artgen sidecars
make export-web / export-linux / export-windows
```

**Never run tests without the Makefile's `--user-data-dir`** — a relative path silently falls back to
the real Godot save directory (`~/.local/share/godot/app_userdata/The Above/`) instead of erroring.

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

`story/secret-bible.md` holds the actual twist/ending — this repo is **public** by the user's explicit
choice, so treat it as already-shared, not held back.

## Autoload boot order (load-bearing — do not reorder)

```
Locale → GameState → MetaPersistence → SaveSystem → AudioManager → SceneDirector → DialogueRunner → Debug
```

Autoloads `_ready()` **before** the main scene enters the tree. Anything needing scene-tree refs
(`SceneDirector.world_holder`, `DialogueRunner`'s DialogueBox/ChoiceMenu/FadeRect) gets them from an
explicit public setter called in `game/scripts/main.gd`'s `_ready()` — never via `@onready
get_node("Main/...")` absolute paths.

## GDScript gotchas that have already bitten this project

- **Variant `==` throws across incompatible types** (e.g. `bool == int`) but compares `int`/`float`
  safely. Guard with `typeof(a) == typeof(b)` before `==`, or use a plain truthy `if x:` check. Real
  bugs fixed this way in `dialogue_runner.gd` and `game_state.gd`'s `set_flag`.
- **JSON round-trip collapses `int` → `float`** (`JSON.parse_string("5")` then re-`stringify()` gives
  `"5.0"`). `SaveSystem` hashes the payload as a stored/read-back **string**, never re-serializes a
  parsed Dictionary before checksumming.
- **Lambda closures capture locals by value, not reference** — `func(): outer += 1` inside a connected
  signal lambda won't mutate `outer`. Use a single-element `Array` as a mutable box: `var counter :=
  [0]`.
- **Turkish İ/ı casing**: never call `.to_upper()/.to_lower()/.capitalize()` on player-facing text at
  runtime — GDScript is locale-blind and mangles dotted/dotless I. Casing is baked into translations
  instead. Enforced by `game/tests/test_turkish_casing_safety.gd`, a static grep-test over
  `game/scripts` and `game/scenes`.
- **GdUnit4 treats some compiler warnings as fatal** during test discovery (Variant-type-inference
  warnings, a local shadowing a base-class method name) — annotate types explicitly and avoid name
  collisions with GdUnitTestSuite members.

## Dialogue/cutscene DSL

Hand-rolled plain-text `.scene` format (not Dialogic) — chosen for AI-authorability, diffability, and
full localization ownership. Dialogue text is never inline; only keys, resolved against
`game/locale/act1_dialogue.csv` (`keys,en,tr`).

Command set: `say`, `choice`/`option`, `label`/`jump`, `setflag`, `if`/`else`/`end`, `move`, `face`,
`teleport`, `show`/`hide`, `pan`, `zoom`, `shake`, `wait`, `sfx`, `music`, `fade`, `spectro`, `mode`,
`mission`, `goto_room`, `title_variant`, `end_scene`.

`game/scripts/systems/dialogue_parser.gd` (`class_name DialogueParser`, static `parse()`) produces a
flat instruction list with pre-resolved label/if-else jump indices — no runtime nesting, just integer
instruction-pointer jumps. `DialogueRunner` (autoload) is an await-based coroutine, no threads.

Example (`game/story/scripts/act1/d2_observatory_intro.scene`):
```
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

## Spectrogram / waterfall minigame (M3)

The `spectro <id>` DSL command runs a real minigame (was a no-op stub through M2). Same pure-logic /
presentation split as the DSL: `WaterfallSession` (`game/scripts/systems/waterfall_session.gd`) is
engine-free per-session state, unit-tested like `DialogueParser`; `WaterfallView`
(`game/scripts/ui/waterfall_view.gd` + `scenes/minigames/waterfall_view.tscn`) is the Control that
mirrors `ChoiceMenu`'s contract exactly — `start_session()` shows it, `DialogueRunner` awaits
`session_closed` the way it awaits `ChoiceMenu.chosen`. `WaterfallCanvas` draws the scrolling
spectrogram procedurally (live data-viz, outside artgen's palette enforcement, but still only paints
signal-magenta `#ff2fd6` for the trace — never decoratively).

Session configs live in `game/story/signals/spectro_sessions.json` (parsed by
`WaterfallSessionLibrary`), keyed by the exact `spectro <id>` used in the Act 1 `.scene` files — a
GdUnit4 test asserts every referenced id exists and that each session can actually render its trace
when tuned (guards the "whole mechanic silently dead" regression class). `kind` selects the win
condition: `tutorial` (tune+hold), `beam_scan` (visit all 3 beams — `signal_beam` is a live gate
*only here*, the "beam 2 only" fault), `onoff` (see both states), and `broadcast`/`taxonomy`/
`answer_gate`/`keystone` (timed; distinct only as narrative tags). Fake physics throughout:
`drift_mhz_s` moves the target (the "align the drift" verb — the guide line re-syncs every tick);
`cell_seconds > 0` gives the canon 11-minute broadcast a visible, countable on/off cadence; the
noise background is deterministic seeded speckle (`WaterfallCanvas.hash01`, seeded from the session
id). Timed `events` open payload windows: `shape_burst` = broadband magenta smear; `decode_text` =
readout line resolving a locale key or (reserved, unauthored — canon lock IX) the observer name.

`_do_spectro` (DialogueRunner) enters `MINIGAME` mode, runs the session, restores the prior mode, and
writes `spectro_<id>_done` (bool) into GameState so later `.scene` content can branch on it. **Design
law wiring:** no minigame is a fail state — `cancel` always closes; and the ANSWER verb (own dedicated
`answer` input, keycode R — never `interact`/`cancel`, so it can't be mashed into) is gated by the
per-session `answer_available` flag, which **no Act 1 session enables** — Day 5's transgression answer
is authored as a *dialogue choice* in `d5_observatory.scene` (`setflag answered_signal`, read by
`d7_observatory.scene`). The `answer_available` path is a documented, tested, reserved capability for a
future console-native ANSWER (same "wired-later stub" pattern as `AudioManager`); enabling it on a
session without also feeding the canonical narrative flag would create a phantom answer the story never
reads (an adversarial review caught exactly that and it was reverted).

## Save / meta-persistence

- `user://saves/slot_N.json`: `{version, checksum (sha256 of the payload string), payload}`. Atomic
  writes: `.tmp` → verify → rename, `.bak` kept and only refreshed from an already-valid slot file.
  Load falls back checksum-mismatch → `.bak` → clean-new-game; never crashes.
- `user://meta.json` + a byte-identical shadow copy track language pref, permanent story facts, and
  per-slot **save-generation counters** — if meta recorded a higher generation than the save file that
  exists, the game knows the player deleted it (`player_tried_to_erase`, a title-screen hook).
- **Known accepted gaps** (documented inline in code, not bugs to "fix" reflexively): a narrow
  crash window between a save's rename and its generation-counter bump; an int flag can come back as a
  float after a save/load round-trip. Both are low-probability, currently dormant, and no content
  exercises either path yet.

## Testing

GdUnit4 (`game/tests/`) for engine-level logic: DSL parser, DialogueRunner, Locale, GameState,
SaveSystem, MetaPersistence, SceneDirector, Turkish-casing-safety grep-test. `artgen/tests/` (pytest)
covers art-pipeline determinism (byte-identical double-build) and palette linting. Rendering
correctness is verified visually via the screenshot tour (`make tour`), not asserted in tests.

## Art pipeline (`artgen/`)

Python/Pillow, single source of truth palette at `artgen/palettes/the_above.json`. `canvas.py` hard-
fails on any color outside the palette; shading only via `ramp_shade(light_dir)`; dithering only via an
ordered-Bayer helper — these are structural guards against pillow-shading/amateur gradients, not style
suggestions to relax. Atlas coordinates are append-only: regenerating art must never invalidate a
committed `.tres`/TileMapLayer/scene. Determinism is enforced (seeded from manifests only, pytest
double-build byte-equality).

## Repo / remote

Public GitHub repo `krem4d/the-above` (deliberately public — user's explicit call, overriding the
default recommendation to keep the pre-reveal story content private).
