# THE ABOVE — Progress Tracker

Living record of what is built, verified, and shipped. Update this file at the close of every
milestone (and whenever a checkbox flips). For **what to build next**, see [`PLAN.md`](PLAN.md); for
**how the project works**, see [`CLAUDE.md`](CLAUDE.md); the canonical master plan lives at
`~/.claude/plans/i-want-to-develop-sunny-coral.md`.

**Snapshot (2026-07-13):** M0, M1, M-STORY, M2, **M3** complete. Next up: **M4 — Act 1 world &
Day 1 playable**. Public remote `krem4d/the-above`; M3 developed on `feat/m3-waterfall`, merged to
`master`.

Legend: `[x]` done · `[~]` partial / in progress · `[ ]` not started

---

## Milestone status

| Milestone | Title | State |
|---|---|---|
| M0 | Toolchain & skeleton | ✅ complete |
| M1 | Pipeline risk burn-down | ✅ complete |
| M-STORY | Full 3-act story bible + Act 1 scripts | ✅ complete |
| M2 | Core narrative systems + UI slice | ✅ complete |
| M3 | Spectrogram (Waterfall) mechanic v1 | ✅ complete (audio + web-verify deferred, see below) |
| **M4** | **Act 1 world & Day 1 playable** | ⬜ **next** |
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

## M3 — Spectrogram (Waterfall) mechanic v1 ✅

- [x] `WaterfallSession` pure model (`game/scripts/systems/`) — fake physics per PLAN: authored
      drift (`drift_mhz_s`, the "align the drift" verb), tolerance lock + sustained-proximity hold,
      countable cell cadence (canon 11-minute cells), per-kind objectives, timed event windows
- [x] Signal data format `game/story/signals/spectro_sessions.json` — **deliberate deviation from
      PLAN's one-file-per-signal:** a single manifest, one tested parse path, covering all 7
      `spectro <id>`s actually authored in the Act 1 scenes. (PLAN names `sig_first_anomaly` as the
      first signal — that id exists only in CLAUDE.md's illustrative example, not in any authored
      `.scene`; the real Day 1/2 signals are `cal_pulsar` and `sig_beam_check`.)
- [x] `WaterfallView` + `WaterfallCanvas` (`game/scenes/minigames/`) — scrolling waterfall drawn
      over deterministic seeded noise (`hash01`, unit-tested), tuning input, drift-tracking guide
      line, reveal flags (`spectro_<id>_done` via DialogueRunner)
- [x] Signal events with payloads — `shape_burst` (broadband smear) authored on `sig_long_call`;
      `decode_text` implemented + tested but **unauthored**: PLAN's "burst decodes to the player's
      typed name" bullet conflicts with secret-bible **canon lock IX** (the observer name may appear
      only in save slots, one phantom slot, one Act 3 inscription) — needs a story-owner decision
      before any Act 1 session uses it
- [x] `DO NOT ANSWER` always available — cancel always exits every session; the exit hint reads
      "[X] DO NOT ANSWER" whenever ANSWER is offered. No Act 1 session offers ANSWER: Day 5's
      transgression stays the authored dialogue choice (`answered_signal`, read by d7); the
      minigame-native ANSWER (`answer_available` + dedicated R key) is a reserved, tested capability
- [x] `spectro <id>` wired in `DialogueRunner` — blocks the coroutine, MINIGAME mode enter/restore,
      result flags, unknown-id no-crash
- [x] Tests: 55 new GdUnit4 cases (suite total 111, green) — model determinism, manifest schema
      validation, session-coverage + trace-renderability guards, view lifecycle/contract
- [~] Audio paths (AudioStreamGenerator desktop / pre-baked OGG web) — **deferred**: AudioManager is
      still the M2 no-op stub and `audiogen/` is M6 scope; the dev sandbox also had no audio device
      to verify against. Revisit alongside M6 audio work.
- [~] Exit gate, web half + tour PNG — desktop logic verified headless (111 tests + runtime demo
      probe); `make tour-scene SCENE=waterfall` entry exists but PNG capture and the web build need
      a machine with a display / export templates (same gate class as M1's browser item)

---

## Test & verification status

| Suite | Command | State |
|---|---|---|
| GdUnit4 engine logic (parser, runner, Locale, GameState, Save, Meta, SceneDirector, waterfall ×4 suites) | `make test` | ✅ green (111 cases) |
| Turkish casing safety (static grep-test) | `make test` | ✅ green |
| artgen determinism + palette lint (pytest) | `make pytest` | ✅ green |
| Screenshot tour (visual review) | `make tour` | ✅ 6 entries (waterfall PNG pending a display) |
| Web export browser gate (Chrome DevTools MCP) | manual | ⏳ re-verify pre-M6 |

---

## Known open items (tracked, not bugs to reflex-fix)

- **PLAN.md M3 vs canon lock IX:** PLAN's "a burst decodes to the player's typed name" is
  implemented as the `decode_text` event capability but deliberately not authored anywhere —
  secret-bible canon lock IX enumerates the only places the observer name may appear, and a
  spectro decode is not one of them. Either amend the canon lock or drop the bullet; until then
  the capability stays dormant (tested, documented in the manifest notes).
- `game/project.godot` currently shows uncommitted — a Godot-editor re-save that reordered sections
  and dropped three keys equal to engine defaults (`text_to_speech`, `stretch/aspect`,
  `locale/fallback`); effective config unchanged. Decide whether to commit the normalized form.
- **Accepted save/meta gaps** (documented inline): narrow crash window between a save's rename and its
  generation-counter bump; an `int` flag can return as `float` after a save/load round-trip. Both
  low-probability, dormant, no content exercises them yet.
- **Web export gate** not re-run since M1 — must pass again before the M6 itch demo.

---

## Commit log (as of this update; `git log --oneline` is authoritative)

```
45d207d feat: M3 spectrogram/waterfall minigame v1
b9ed405 docs: add PROGRESS tracker and forward PLAN (M3-M6)
48ef7f2 docs: add project CLAUDE.md for session onboarding
939f122 feat: M2 core narrative systems
f4671d6 feat: dialogue UI widgets + Turkish-safe pixel font (M2 UI slice)
9870995 feat: full story bible + Act 1 scripts, EN+TR complete
e30f697 feat: M1 pipeline risk burn-down
5865e90 chore: bootstrap THE ABOVE — Godot 4.5.2 skeleton, artgen pipeline core, GdUnit4 harness
```
(The M3 gap-close commit — drift, seeded noise, events, DO NOT ANSWER — lands immediately after
this file's update, same branch.)
