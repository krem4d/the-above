# THE ABOVE — Progress Tracker

Living record of what is built, verified, and shipped. Update this file at the close of every
milestone (and whenever a checkbox flips). For **what to build next**, see [`PLAN.md`](PLAN.md); for
**how the project works**, see [`CLAUDE.md`](CLAUDE.md); the canonical master plan lives at
`~/.claude/plans/i-want-to-develop-sunny-coral.md`.

**Snapshot (2026-07-13):** M0, M1, M-STORY, M2 complete. Next up: **M3 — Spectrogram (Waterfall)
mechanic v1**. Branch `master`, 6 commits, public remote `krem4d/the-above`.

Legend: `[x]` done · `[~]` partial / in progress · `[ ]` not started

---

## Milestone status

| Milestone | Title | State |
|---|---|---|
| M0 | Toolchain & skeleton | ✅ complete |
| M1 | Pipeline risk burn-down | ✅ complete |
| M-STORY | Full 3-act story bible + Act 1 scripts | ✅ complete |
| M2 | Core narrative systems + UI slice | ✅ complete |
| **M3** | **Spectrogram (Waterfall) mechanic v1** | ⬜ **next** |
| M4 | Act 1 world & Day 1 playable | ⬜ pending |
| M5 | Full vertical-slice content (Days 2–7) | ⬜ pending |
| M6 | Polish & itch demo | ⬜ pending |

---

## M0 — Toolchain & skeleton ✅

- [x] Godot 4.5.2-stable pinned (`~/apps/godot-4.5.2/godot`), ADR `docs/decisions/0001-godot-version.md`
- [x] `git init`, repo layout scaffolded
- [x] `project.godot` — 640×360 viewport, `stretch/mode=viewport`, integer scale, Nearest filter,
      pixel-snap, font AA off; Compatibility (GL) renderer on all platforms
- [x] Input map, GdUnit4 harness under `game/addons/gdUnit4/`
- [x] artgen skeleton + master 28-colour palette (`artgen/palettes/the_above.json`)
- [x] `Makefile` build orchestration (see targets in `CLAUDE.md`)

## M1 — Pipeline risk burn-down ✅

- [x] Gray-box room through the full artgen path
- [x] Movement + pixel-perfect camera verified at 2×/3×/4×
- [x] Screenshot tour end-to-end (`make tour` → `artifacts/shots/`), `game/tools/tour.json`
- [x] Determinism: artgen double-build byte-equality (pytest), palette lint
- [~] Web export privately on itch.io + desktop presets — **re-verify before M6** (browser gate)

## M-STORY — Story bible ✅

- [x] `story/bible.md`, `story/characters.md`, `story/clip-anchors.md`
- [x] `story/secret-bible.md` — canonical internal truth (repo is deliberately public)
- [x] All Act 1 `.scene` scripts authored (`game/story/scripts/act1/`): cold_open, d1–d7
      (wake/town/observatory per day), d7 sendoff + launch, post_credit — 24 scenes
- [x] EN + TR dialogue keys in `game/locale/act1_dialogue.csv`

## M2 — Core narrative systems + UI slice ✅

- [x] `.scene` DSL parser (`dialogue_parser.gd`, `class_name DialogueParser`, static `parse()`)
- [x] `DialogueRunner` autoload — await-based coroutine, pre-resolved jump indices
- [x] DialogueBox (typewriter / portraits / paging), ChoiceMenu
- [x] Locale autoload + EN/TR CSV → `.translation`, language toggle
- [x] GameState (typed flags, day counter, `flag_changed`)
- [x] SaveSystem (slot JSON, sha256 checksum, atomic `.tmp`→rename, `.bak` fallback)
- [x] MetaPersistence (`meta.json` + shadow copy, save-generation counters, `player_tried_to_erase`)
- [x] Turkish-safe pixel font; İ/ı casing grep-test gate
- [x] Autoload boot order wired via explicit setters in `main.gd`

---

## Test & verification status

| Suite | Command | State |
|---|---|---|
| GdUnit4 engine logic (parser, runner, Locale, GameState, Save, Meta, SceneDirector) | `make test` | ✅ green |
| Turkish casing safety (static grep-test) | `make test` | ✅ green |
| artgen determinism + palette lint (pytest) | `make pytest` | ✅ green |
| Screenshot tour (visual review) | `make tour` | ✅ 5 entries |
| Web export browser gate (Chrome DevTools MCP) | manual | ⏳ re-verify pre-M6 |

---

## Known open items (tracked, not bugs to reflex-fix)

- `game/project.godot` currently shows uncommitted — a Godot-editor re-save that reordered sections
  and dropped three keys equal to engine defaults (`text_to_speech`, `stretch/aspect`,
  `locale/fallback`); effective config unchanged. Decide whether to commit the normalized form.
- **Accepted save/meta gaps** (documented inline): narrow crash window between a save's rename and its
  generation-counter bump; an `int` flag can return as `float` after a save/load round-trip. Both
  low-probability, dormant, no content exercises them yet.
- **Web export gate** not re-run since M1 — must pass again before the M6 itch demo.

---

## Commit log (master)

```
48ef7f2 docs: add project CLAUDE.md for session onboarding
939f122 feat: M2 core narrative systems
f4671d6 feat: dialogue UI widgets + Turkish-safe pixel font (M2 UI slice)
9870995 feat: full story bible + Act 1 scripts, EN+TR complete
e30f697 feat: M1 pipeline risk burn-down
5865e90 chore: bootstrap THE ABOVE — Godot 4.5.2 skeleton, artgen pipeline core, GdUnit4 harness
```
