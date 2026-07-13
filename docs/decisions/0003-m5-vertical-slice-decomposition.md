# 0003 — M5: Full vertical-slice content (Days 2–7) — decomposition & handoff

Status: **M5.1 implemented & verified** (2026-07-13) · ⚑ canon-lock-IX **resolved: hold the line** (see §3).
Remaining ⚑ (anomaly UX) still open for its slice. Follows [`0002-m4-act1-world-codex-handoff.md`](0002-m4-act1-world-codex-handoff.md).

> **Scope correction (post-survey).** The initial draft assumed M5 was "wiring only" because the
> *localization* is complete. A deeper survey during M5.1 found that the M4 room layouts contain only
> Day-1 NPCs/markers, so Days 2–7 reference **~13 unplaced NPCs, three missing rooms
> (`obs_breakroom`, `ship_corridor`, `ship_corridor_seven`), and many absent markers/props**. This is
> real content ("staging") debt — see the new slice **M5.S** in §1. It does **not** block playability:
> `SceneDirector.goto_room` to an unknown room returns early and leaves the player in the previous valid
> room, and every mission's `allowed_exits[0]` resolves in the room the player is actually left in, so
> the arc plays end-to-end; the missing content degrades to no-op warnings (absent bodies, pans to
> nothing), not soft-locks.

## 0. Why this is a decomposition, not a single handoff

CLAUDE.md requires each Codex handoff to be "implementable in a bounded coding pass." M5 as written in
`PLAN.md` is not one pass — it spans mission wiring, a title/meta system, two wordless bookend cutscenes,
a collectible/anomaly layer, the keystone whiteboard scene, and a localization gate. This document splits
M5 into five slices, each independently shippable and testable, and **fully specifies the first (M5.1)**.
M5.2–M5.5 are scoped with their open design decisions called out; they become their own bounded handoffs
once the decisions marked ⚑ are made.

Survey finding that reshapes the milestone: **all Act-1 content already exists.** The 22 day scenes and 2
bookends are authored; all 355 referenced dialogue keys are present in `act1_dialogue.csv` with non-empty
EN **and** TR (verified: 0 missing, 0 empty). M5 is therefore a **wiring and verification** milestone, not
a writing one. The risk is dead code paths and soft-locks, not blank strings.

## 1. Slice map

| Slice | Title | Blocks on | State |
|---|---|---|---|
| **M5.1** | Days 2–7 playable spine (mission wiring + finale robustness + lint gate + 7-day probe) | nothing | ✅ **done** (§2) |
| **M5.S** | Staging: build the 3 missing rooms, place ~13 NPCs (+ their art), fill markers/props | needs NPC art | needs its own handoff |
| **M5.2** | Boot & finale flow (cold_open → title → sendoff → launch → post_credit; title screen + meta variants) | M5.S rooms; ⚑ canon-lock-IX **resolved** | needs its own handoff |
| **M5.3** | Town-anomaly layer (the 9 spot-the-wrongness collectibles) | ⚑ anomaly-UX model | needs its own handoff |
| **M5.4** | Keystone 11-minute whiteboard scene polish (load-bearing) | M5.S (`obs_breakroom`) + story-owner writing pass | needs its own handoff |
| **M5.5** | Save/resume + localization gate close-out (`current_mission_id` persistence, TR length review) | M5.1 | small, follows M5.1 |

Recommended order: **M5.1** (done — unblocks manual playtesting of the whole arc) → **M5.S** (the arc
plays but is visually empty until the rooms/NPCs exist; it gates the honest address/staging lint and the
keystone scene) → M5.5 (cheap, makes the arc resumable) → M5.2/M5.3/M5.4. M5.S is the single biggest
remaining chunk because it carries NPC art generation, not just placement.

---

## 2. M5.1 — Days 2–7 playable spine  *(this handoff is ready for Codex)*

### 2.1 Goal / player-facing outcome

A player who finishes Day 1 can play Days 2 through 7 to the end of Act 1 (the launch) without ever getting
stuck. Today they cannot: reaching Day 2 drops them into an unplayable room with no way to progress.

### 2.2 Root cause — two systematic wiring defects

Both are the *same class* of defect the M4 adversarial review fixed for Day 1, now found across Days 2–7.

**Bug A — wake scripts don't arm their morning mission (soft-lock).**
`d1_wake` ends `mode free_roam` → `mission m_d1_morning` → `end_scene`. `d2_wake`…`d7_wake` end
`mode free_roam` → `end_scene` with **no** `mission` command. In FREE_ROAM, `MissionSystem.on_exit_touched`
returns early (exits are mission verbs, not doors), so the player has no armed exit and cannot leave home.
Every day after Day 1 dead-ends at wake.

**Bug B — the next day's morning mission is armed in the previous day's closing tail (day-roll race).**
After `setflag dN_complete`, `DayLoop._roll_day` awaits `scene_finished`, then advances the day and runs
`d(N+1)_wake`. Five tails arm `mission m_d(N+1)_morning` *before* their closing `fade out`, i.e. after the
`dN_complete` boundary. This is exactly the `d1_observatory` defect fixed in M4: it puts the game in MISSION
mode across the fade and duplicates day-N+1 setup that belongs to the wake script. The established authoring
rule from M4 §Outcome: **after `setflag dN_complete`, only `fade` / `end_scene` may follow.**

The fix for Bug A and Bug B is a single move: the morning-mission arm relocates from the prior day's tail
(Bug B) to that day's own wake script (Bug A), making every day mirror the Day-1 template.

### 2.3 Exact edits

**Non-goal / do NOT touch:** the *within-day* mission arms are correct and stay untouched —
`mission m_dN_town` in each `dN_town` (Days 1–5), `mission m_d6_evening` in `d6_observatory`,
`mission m_d7_sendoff` in `d7_observatory`, `mission m_d7_launch` in `d7_sendoff`. These arm the **next beat
of the same day**, gated by an exit the player walks to; there is no `dN_complete` boundary between them, so
the day-roll rule does not apply. (They arm just before a `fade out`, which leaves player input live for the
fade's duration — a cosmetic nit, not a soft-lock; logged for M5.4 polish, not fixed here.)

**Add (Bug A)** — one line before `end_scene`, immediately after the existing `mode free_roam`, matching
`d1_wake`:

| File | Add line |
|---|---|
| `game/story/scripts/act1/d2_wake.scene` | `mission m_d2_morning` |
| `game/story/scripts/act1/d3_wake.scene` | `mission m_d3_morning` |
| `game/story/scripts/act1/d4_wake.scene` | `mission m_d4_morning` |
| `game/story/scripts/act1/d5_wake.scene` | `mission m_d5_morning` |
| `game/story/scripts/act1/d6_wake.scene` | `mission m_d6_morning` |
| `game/story/scripts/act1/d7_wake.scene` | `mission m_d7_morning` |

**Remove (Bug B)** — delete the `mission m_d(N+1)_morning` line sitting between `setflag dN_complete` and
`fade out`, leaving `setflag dN_complete` → `fade out …` → `end_scene`:

| File | Remove line |
|---|---|
| `game/story/scripts/act1/d2_observatory.scene` | `mission m_d3_morning` (after `setflag d2_complete`) |
| `game/story/scripts/act1/d3_observatory.scene` | `mission m_d4_morning` (after `setflag d3_complete`) |
| `game/story/scripts/act1/d4_observatory.scene` | `mission m_d5_morning` (after `setflag d4_complete`) |
| `game/story/scripts/act1/d5_observatory.scene` | `mission m_d6_morning` (after `setflag d5_complete`) |
| `game/story/scripts/act1/d6_town.scene`        | `mission m_d7_morning` (after `setflag d6_complete`) |

(Day 6 ends its day in the teahouse — `d6_town`, not an observatory — hence the last row. Day 7 has no
`d7_complete`: it ends Act 1 via `setflag act1_complete` in `d7_launch`, no day-roll.)

No changes to `act1.json` — every referenced mission id already exists there with correct
`allowed_exits` / `complete_on_flag` / `on_complete_script`.

### 2.4 Turn the M4 authoring rules into enforced lints (regression firewall)

The two bugs above shipped because the rules ("wake arms its mission", "nothing after `dN_complete`") lived
only in prose. Add them as static tests so they can never regress. Extend
`game/tests/test_act1_content_coverage.gd`:

1. **Generalize the *localization* coverage to all 22 day scenes** (`ALL_DAY_SCENES` = `d1_wake`…`d7_launch`;
   `cold_open`/`post_credit` excluded — they address the not-yet-built `ship_corridor*` rooms). This is the M5
   **localization completeness gate**: `test_all_day_dialogue_keys_translate_in_both_languages` (every
   `say`/`option` key non-empty in EN and TR) and `test_name_entry_is_authored_exactly_once` (across the whole
   arc). Both pass — the survey confirmed all 355 keys are present in both languages.
   **Note:** the *address-existence* check (`…scenes_only_address_things_that_exist`) stays Day-1-scoped for
   now. Generalizing it would fail on the M5.S staging debt (unplaced NPCs, missing markers/rooms), so it is
   the exit gate for **M5.S**, not M5.1 — as each NPC/marker is placed, extend it toward `ALL_DAY_SCENES`.
2. **New `test_every_wake_arms_its_morning_mission`** — for each `dN_wake` (N=1..7), parse it and assert it
   contains exactly one `mission` instruction whose arg is `m_dN_morning`. (Directly forbids Bug A.)
3. **New `test_nothing_runs_after_day_complete_flag`** — for every scene, scan instructions after any
   `setflag dN_complete true`; assert only `fade` and `end_scene` commands follow. (Directly forbids Bug B.)
4. **New `test_every_armed_mission_exists_and_resolves`** — collect every `mission <id>` armed by any scene;
   assert each id is in `act1.json`, its `on_complete_script` names an existing `.scene`, and (orphan check)
   every mission in `act1.json` is armed by exactly one scene **or** is the boot mission `m_d1_morning`.

These are pure-parse tests (no engine boot), the same shape as the existing suite — GdUnit4-safe with
explicit types.

### 2.5 Full-arc verification harness

Add `game/tools/day7_probe.gd`, generalizing `day1_probe.gd` (which stays). The pumps are already
day-agnostic — dialogue-advance, choice[0], name-entry, waterfall-honest-win, mission-exit-touch drive
whatever is on screen. Changes:

- **Exit condition:** success when `GameState.get_flag("act1_complete")` is set (d7_launch), not
  `day >= 2 && d1_complete`.
- **Frame budget:** raise `MAX_FRAMES` for a 7-day chain (headless the logic runs in well under the current
  60000 at `time_scale = 4`; give generous headroom, e.g. ×4).
- **Wire `--day7-probe`** in `game/scripts/autoload/debug.gd` alongside `--day1-probe`.
- **Beat shots** (only under a display): keep the per-room capture; optionally tag shots with the current
  `GameState.day`. Headless still verifies the full logic chain, which is the gate.

The probe drives `DayLoop.begin` → `d1_wake` → … → `d7_launch` = `act1_complete`. It does **not** cover the
`cold_open`/title/`post_credit` bookends (M5.2) — those wrap the day chain, they aren't in it.

### 2.6 Acceptance criteria & exact validation

```bash
make test        # GdUnit4: all suites green, INCLUDING the 3 new lints + generalized coverage
make pytest      # artgen determinism/palette lint unchanged: 8 green
# Full 7-day spine, headless, exit 0 = act1_complete reached with no stall:
xvfb-run -a -s "-screen 0 1280x720x24" ~/apps/godot-4.5.2/godot --path game \
  --rendering-driver opengl3 -- --day7-probe
echo "probe exit: $?"   # expect 0
```

Done when: all three commands pass; the probe log shows beats for every day (`room:home`/`town`/`dolmus`/`obs`
recurring, `choice`, `name_entry`, `waterfall`, `exit:*`) through to a final `act1_complete`; and the new
lints fail loudly if either bug is reintroduced. Manual spot-play of Days 2–7 by the user is the human gate
(PLAN M5 exit gate) but is not required for the Codex pass to be considered complete.

### 2.7 Invariants / failure behaviour

- No new save-format or persistence change → no migration.
- `DialogueRunner` already no-ops unknown targets with a warning, so a mis-typed mission id degrades to "exit
  does nothing" rather than a crash; lint #4 catches it at test time instead.
- No fail states, no runtime casing transforms, no new player-facing strings introduced.

### 2.8 Outcome (M5.1 shipped)

Implemented as specified, plus one fix the probe surfaced:

- **11 wiring edits** — 6 wakes arm their morning mission, 5 tails drop the cross-day arm.
- **3 structural lints** (`test_every_wake_arms_its_morning_mission`, `test_nothing_runs_after_a_day_complete_flag`,
  `test_every_armed_mission_exists_and_is_armed_once`) + the generalized loc gate. All green.
- **Finale-robustness fix (`MissionSystem`).** The day7 probe stalled at the launch: `d7_sendoff` walks Deniz
  *onto* the dolmuş stop (`move hoca dolmus_stop`) before arming `m_d7_launch`, and `body_entered` only fires
  on entry — so the mission could never complete (a soft-lock at the emotional peak). Added an **arm-time
  overlap check**: when a mission arms, if the player already overlaps an allowed exit `Area2D`, it trips that
  exit exactly as `body_entered` would. General (not Day-7-specific), guarded against over-firing by a unit
  test; the day7 probe is the positive-path integration test (`overlaps_body` needs a live physics scene).
  This closes the previously-logged "`m_d7_sendoff` armed while standing on the exit" open item for the whole arc.
- **`day7_probe`** (`--day7-probe`) drives `DayLoop.begin` → `act1_complete`. **PASS** in 4784 frames, no stall.
- Verification: **155/155 GdUnit** (18 suites), **8/8 pytest**, day7 probe PASS.

---

## 3. M5.2 — Boot & finale flow  *(needs its own handoff; ⚑ decision required)*

Wire the two authored wordless bookends and the title/meta system around the day chain:

- **Rooms to build:** `ship_corridor` (cold_open) and `ship_corridor_seven` (post_credit) — the only
  registry gap; `post_credit` is the same corridor "with one difference" (5 suits, 2 empty hooks).
- **Overlays to build:** `title_card_the_above`, `title_end_act_one` (used by `d7_launch`), and the
  main-menu title screen.
- **`title_variant` handling:** the command appears in `d7_launch` (`post_act1`), `post_credit`
  (`version_plus_one`), and per the plan reacts to `player_tried_to_erase`. This is the Act-1 meta trick:
  the menu's version string / title state changes based on meta-persistent facts. Needs a small
  `TitleVariant` resolver reading `MetaPersistence`.
- **Boot flow:** first launch → `cold_open` → title screen → new game boots `DayLoop`. Finale:
  `d7_launch` → credits → `post_credit`. Define where cold_open sits relative to the title screen and
  save/continue.

✅ **Story-owner decision — canon lock IX: RESOLVED, hold the line** (2026-07-13, user). The typed observer
name never surfaces in Act 1 — not on the title card, not in a "continue as {name}" line, not via a spectro
decode. It remains reserved for the three canon-lock-IX surfaces only (save slots, the one phantom slot, the
one Act 3 inscription). The withheld name is the engine of the Act-3 reveal; every Act-1 appearance would
spend that payoff early. Consequences: the spectro `decode_text` capability stays **permanently dormant**
(tested, unauthored); M5.2's title/meta layer must render its variants from meta-facts *other than the name*
(day reached, `player_tried_to_erase`, completion state). This settles the same question left open in M3
(`decode_text`) and applied conservatively in M4 (the Day-1 save line) — it is now closed for the project.

## 4. M5.3 — Town-anomaly layer  *(needs its own handoff; ⚑ decision required)*

The 9 "wrong notes" are already flagged in the scripts (`anomaly_moving_star`, `anomaly_dogs`, …) — set by
existing dialogue choices. What's undesigned is whether the player *sees* their collection.

⚑ **Design decision — anomaly UX model.** Options: (a) **invisible** — the `anomaly_*` flags stay pure
story state, no UI, discovered only by the attentive (purest, zero new UI, but no demo-collectible hook);
(b) **quiet tally** — an end-of-act count ("You noticed 6 of 9 wrong things") on the Act-1 outro, no in-run
HUD; (c) **journal** — a togglable log that fills in as anomalies are flagged (most participatory, most new
UI, closest to PLAN's "demo collectible"). Recommendation: **(b)** — honours "spot the wrongness" as a
reward for attention without a HUD that turns dread into a checklist, and it's a bounded pass. This slice
also needs the audit that all 9 `anomaly_*` flags are actually reachable and counted.

## 5. M5.4 — Keystone scene polish  *(needs its own handoff; story-owner writing pass)*

The 11-minute whiteboard scene is the milestone's top risk (PLAN risk #1) and gets disproportionate budget.
The script exists; this slice is a focused writing/timing/staging pass with the user, plus the cosmetic
"input-live-during-fade" cleanup for the within-day mission arms noted in §2.3. Best done after M5.1 makes it
playable in context.

## 6. M5.5 — Save/resume + gate close-out  *(small; follows M5.1)*

- **`current_mission_id` persistence.** `GameState.to_dict` persists `day`, `observer_name`,
  `current_room_id`, and flags but not `SceneDirector.current_mission_id`. A continue-from-save that lands
  mid-day would restore the room but not the armed mission → the §2.2 Bug-A soft-lock, from a save. Add it to
  the payload (versioned; a legacy save with no field re-derives the mission from the day's wake on load, or
  falls back to re-arming the morning mission). Dormant until the M5.2 slot-load UI exists, but it's the same
  serialization pass, so land it with M5.1's spine.
- **Localization gate close-out.** With §2.4's generalized coverage green, add the two remaining PLAN gate
  items: a read-never-set flag scan (every `if`/branch flag is `setflag`-set somewhere) and a TR
  line-length warning review for the dialogue box.

---

## 7. Cross-cutting constraints (unchanged, apply to every slice)

No fail states; no runtime `.to_upper/.to_lower/.capitalize` on player-facing text (casing baked into
translations, grep-test enforced); every player-facing string translates in EN **and** TR; observer name
governed by canon lock IX per the ⚑ decision above; autoload boot order load-bearing; atlas/anim contracts
append-only; art palette hard-fail + `ramp_shade`/ordered-Bayer only.

## 8. Decisions summary

1. ✅ **Canon lock IX** — **resolved: hold the line** (name never appears in Act 1; `decode_text` permanently
   dormant). Closed for the project.
2. ⚑ **Anomaly UX** (blocks M5.3): invisible / end-of-act tally / journal. Recommend end-of-act tally. *Open.*
3. ✅ **M5.1 slice** — implemented this pass (§2.8); the remaining order is M5.S → M5.5 → M5.2/M5.3/M5.4.
4. **M5.S is the next big rock** — building 3 rooms + ~13 NPCs (with art) is the gate for a *staged* (not just
   *playable*) arc, the keystone whiteboard scene (M5.4), and the honest address-existence lint.
