# THE ABOVE — Progress Tracker

Living record of what is built, verified, and shipped. Update this file at the close of every
milestone (and whenever a checkbox flips). For **what to build next**, see [`PLAN.md`](PLAN.md); for
**how the project works**, see [`CLAUDE.md`](CLAUDE.md); the canonical master plan lives at
`~/.claude/plans/i-want-to-develop-sunny-coral.md`.

**Snapshot (2026-07-13):** M0, M1, M-STORY, M2, M3, **M4** complete. **M5 in progress** — slice
**M5.1 (Days 2–7 playable spine) is done & verified**; the full 7-day arc now plays start→`act1_complete`.
Decomposition + remaining slices in [`docs/decisions/0003-m5-vertical-slice-decomposition.md`](docs/decisions/0003-m5-vertical-slice-decomposition.md).
Public remote `krem4d/the-above`.

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
| M4 | Act 1 world & Day 1 playable | ✅ complete (Day 1 end-to-end; Days 2–7 wiring is M5) |
| **M5** | **Full vertical-slice content (Days 2–7)** | 🔄 **in progress** — M5.1 spine done; M5.S staging + M5.2–M5.5 remain |
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
- [x] Exit gate, desktop + tour PNG — **closed in M4**: the waterfall PNG (`05_waterfall.png`) and
      the full tour now capture under `xvfb-run … --rendering-driver opengl3`; every beat reviewed by
      eye. Web build half still pending (export templates / browser gate, same class as M1's item).

---

## M4 — Act 1 world & Day 1 playable ✅

Handoff/decision record: [`docs/decisions/0002-m4-act1-world-codex-handoff.md`](docs/decisions/0002-m4-act1-world-codex-handoff.md).
Day 1 plays start-to-finish; Days 2–7 wiring is deliberately M5 (see Known open items).

- [x] Tilesets via artgen — **home, town (Taşlıca), observatory, dolmuş**: 16-art-px → 32 px,
      hue-shifted ramps, palette hard-fail respected, atlas append-only. (`artgen/.../tiles/`,
      `game/assets/gen/tiles/`)
- [x] Cast art — **11 walk sheets** (Deniz/Hoca + Yıldız the cat + 9 townsfolk) and **14 portraits**
      (64×64), 8-row idle/walk ×4-dir layout, driven from `artgen/manifests/cast_sheets.json` /
      `cast_portraits.json`. Placeholder hoca sheet removed.
- [x] Room scenes `game/scenes/rooms/act1/{home,town,dolmus,obs}.tscn` — codegen from layout JSON
      (`game/story/rooms/*.json`, tile-unit positions) via `tools/gen_rooms.gd`; TileMapLayers, Props,
      NPCs, exit Area2Ds, named SpawnPoints, CameraRig.
- [x] Day-loop scaffolding — `DayLoop` autoload (dN_complete → await scene → advance_day → autosave
      slot 1 → dN+1_wake), `MissionSystem` + `MissionLibrary` (missions as data, allowed exits,
      completion flag, on-complete script, diegetic refusal), `name_entry` DSL/panel, `ControlMode`
      gating. Appended to the autoload order (existing relative positions preserved).
- [x] Day 1 fully playable against the `d1_*.scene` scripts — verified end-to-end by the in-game
      `--day1-probe` driver: wake → home → town → dolmuş → observatory → name-entry → spectro →
      printout → night → save → **rolls to Day 2**. 10/10 beats, no stalls.
- [x] `make resources` / `make rooms` regenerate SpriteFrames/TileSet/room `.tres`+`.tscn` from
      sidecars (committed once, deterministic).
- [x] Verification — 151/151 GdUnit (18 suites), 8/8 pytest, day1_probe PASS, 8 Day-1 beat PNGs +
      full tour captured under xvfb and reviewed. `spectro` fires inside the real observatory room.

**Adversarial review (this milestone):** ran a finder→verifier workflow over the branch; the verifier
pass was cut short by a model usage limit, so the 6 surfaced findings were triaged by hand against the
code and the M4 scope. Two were genuine **Day-1 (M4)** defects and are fixed:

- **`d1.town.sys.001` rendered a literal `{name}`.** `_do_say` calls `Locale.t(key)` with no params, so
  `String.format` never runs. Fixed by removing the token from the line entirely — **not** by
  substituting the name: canon lock IX enumerates the only surfaces the typed observer name may appear
  (save slots / the phantom slot / one Act 3 inscription), and Act 1 dialogue is not one of them. Same
  precedent already applied to the spectro `decode_text` capability. New copy: `SAVED. OBSERVER LOG.
  DAY 1.` / `KAYDEDİLDİ. GÖZLEMCİ KAYDI. GÜN 1.`
- **`mission m_d2_morning` armed mid-scene before the closing `fade out`** in `d1_observatory`, putting
  the game in MISSION mode with live town exits during the 2 s fade. Removed — Day-2 setup belongs to
  `d2_wake` per the day-loop convention. Established authoring rule: after `setflag dN_complete`, only
  `fade` / `end_scene` may follow (DayLoop awaits `scene_finished`; anything that mutates mode or queues
  a scene races the day-roll).

The other four findings are **M5 scope** (Days 2–7 wiring, explicit non-goals in 0002) — see Known open
items.

---

## M5 — Full vertical-slice content (Days 2–7) 🔄

Decomposition/handoff: [`docs/decisions/0003-m5-vertical-slice-decomposition.md`](docs/decisions/0003-m5-vertical-slice-decomposition.md).
Survey finding: all 22 day scenes + 355 dialogue keys (EN+TR) already exist — M5 is **wiring + staging**,
not writing. M5 is split into M5.1 (spine ✅), M5.S (staging), M5.2 (boot/finale), M5.3 (anomalies),
M5.4 (keystone), M5.5 (save-resume + loc close-out).

### M5.1 — Days 2–7 playable spine ✅

- [x] **Wiring (11 edits):** `d2_wake`…`d7_wake` now arm their `m_dN_morning` (Bug A — the soft-lock);
      the cross-day `mission m_d(N+1)_morning` armed after `setflag dN_complete` removed from
      `d2/d3/d4/d5_observatory` + `d6_town` (Bug B — the M4 day-roll rule, applied arc-wide).
- [x] **Finale robustness (`MissionSystem`):** arm-time overlap check completes a mission if the player
      is already standing on an allowed exit (`d7_sendoff` walks Deniz onto the dolmuş stop before arming
      `m_d7_launch`; `body_entered` never re-fires → was a finale soft-lock). Closes the logged
      "armed while standing on the exit" item for the whole arc.
- [x] **Regression firewall (3 lints in `test_act1_content_coverage.gd`):** every wake arms exactly its
      morning mission; nothing but `fade`/`end_scene` after `setflag dN_complete`; every armed mission
      exists in `act1.json`, resolves its `on_complete_script`, and is armed exactly once. Plus the loc
      gate generalized to all 22 scenes, name-entry-exactly-once across the arc, and a guard test that the
      arm-time check never over-fires.
- [x] **Full-arc probe (`--day7-probe`, `tools/day7_probe.gd`):** drives `DayLoop.begin` → `act1_complete`.
      **PASS** in 4784 frames, no stall, no script errors.
- **Playable, not yet staged:** the arc plays because `goto_room` to a missing room leaves the player in the
      previous valid room and every mission exit still resolves. Missing content degrades to no-op warnings.
      Staging it is **M5.S** (below).

### Remaining M5 slices (not started)

- [ ] **M5.S staging** — build `obs_breakroom` / `ship_corridor` / `ship_corridor_seven`; place ~13 unplaced
      NPCs (needs their walk-sheet art) + the absent markers/props Days 2–7 reference; then extend the
      address-existence lint toward all 22 scenes. Biggest remaining chunk (carries NPC art generation).
- [ ] **M5.2** boot & finale flow (cold_open → title → post_credit; `title_variant` meta trick, name-free per
      the canon decision below). [ ] **M5.3** town-anomaly UX. [ ] **M5.4** keystone whiteboard polish
      (needs `obs_breakroom`). [ ] **M5.5** `current_mission_id` save-resume + loc close-out.

**Canon lock IX — resolved (hold the line, 2026-07-13):** the typed observer name never appears in Act 1
(no title card, no decode). Reserved for save slots / phantom slot / the Act 3 inscription only. The spectro
`decode_text` capability stays permanently dormant. This closes the M3/M4/M5 recurring question.

---

## Test & verification status

| Suite | Command | State |
|---|---|---|
| GdUnit4 engine logic (parser, runner, Locale, GameState, Save, Meta, SceneDirector, mission/day-loop, waterfall, act1-content lints) — 18 suites | `make test` | ✅ green (**155 cases**) |
| Turkish casing safety (static grep-test) | `make test` | ✅ green |
| artgen determinism + palette lint (pytest) | `make pytest` | ✅ green (8 cases) |
| Day 1 end-to-end (`--day1-probe`, in-game driver under xvfb) | see M4 notes | ✅ PASS (10 beats) |
| **Full Act 1 arc (`--day7-probe`, DayLoop.begin → `act1_complete`)** | `godot … -- --day7-probe` | ✅ **PASS** (4784 frames, no stall) |
| Screenshot tour + Day-1 beats (visual review) | `make tour` / probe | ✅ captured under xvfb, all reviewed |
| Web export browser gate (Chrome DevTools MCP) | manual | ⏳ re-verify pre-M6 |

---

## Known open items (tracked, not bugs to reflex-fix)

- **M5.S — staging debt (the next big rock).** The M4 room layouts hold only Day-1 NPCs/markers, so Days 2–7
  reference **~13 unplaced NPCs** (ada, veli, tarik, husnu, havva, cemal, saniye, zeliha, osman, nurten,
  ferit, ayse, …), **three missing rooms** (`obs_breakroom` — the keystone whiteboard; `ship_corridor` /
  `ship_corridor_seven` — the cold-open/post-credit bookends), and many absent markers/props (roadside,
  break_room, landline, barber_door, degirmen_street, dish_view, whiteboard, saniye_door, …). The arc plays
  regardless (missing targets no-op), but it is visually empty. Building this (incl. NPC walk-sheet art) is
  M5.S; then extend `test_..._only_address_things_that_exist` from Day-1 toward all 22 scenes.
- **M5.5 — autosave is not yet resumable.** `GameState.to_dict` persists `day`, `observer_name`,
  `current_room_id`, and flags, but **not** `SceneDirector.current_mission_id`; a continue-from-save
  (M5.2 slot UI) must also restore the active mission. Dormant today — no load path exists yet.
- **Accepted save/meta gaps** (documented inline): narrow crash window between a save's rename and its
  generation-counter bump; an `int` flag can return as `float` after a save/load round-trip. Both
  low-probability, dormant, no content exercises them yet.
- **Web export gate** not re-run since M1 — must pass again before the M6 itch demo.

**Resolved in M5.1** (2026-07-13): ~~wake scripts don't arm their morning mission~~ (all wakes now arm,
lint-enforced); ~~end-of-day tails must follow the `dN_complete` rule + `m_d7_sendoff` standing-on-exit~~
(Bug B removed arc-wide + lint; arm-time overlap check completes any mission armed while standing on its
exit); ~~PLAN M3 vs canon lock IX~~ (resolved: hold the line — `decode_text` permanently dormant);
~~`project.godot` shows uncommitted~~ (working tree clean).

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
(Older entries trimmed; `git log --oneline` is authoritative. M3 landed via `feat/m3-waterfall`.
The M4 commit — Act 1 art, room codegen, mission/day-loop systems, Day-1 review fixes, and this
update — lands on `feat/m4-act1-world` and ff-merges to `master`.)
