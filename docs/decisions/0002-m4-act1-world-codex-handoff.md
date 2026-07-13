# 0002 — M4 Act 1 World & Day 1 Playable: implementation handoff

Status: **approved design, implementation in progress** — Claude (Fable) design pass complete
2026-07-13. This is the Codex work order for finishing M4 per `AGENTS.md`.

## 1. Goal and player-facing outcome

M4 per `PLAN.md`: the first genuinely playable slice — wake at home → walk through Taşlıca →
ride İsmet's dolmuş up the switchbacks → the observatory → the printout discovery (the M3
`spectro` minigame firing inside the real observatory room) → night walk home → sleep → Day 2
wake. Real art everywhere, pixel-crisp at 3×/6×, bilingual EN+TR throughout.

**Exit gate (verbatim from PLAN.md):** Day 1 playable start-to-finish, pixel-crisp at 3×/6×,
tour captures every beat; the `spectro` discovery from M3 fires inside the real observatory room.

## 2. State of the working tree — read before touching anything

The uncommitted working tree **is the approved partial implementation**, produced and unit-verified
before the Claude/Codex split was adopted. Preserve all of it; nothing in it is stale or abandoned.

### Complete and verified (do not redesign)

| Slice | Files | Verified how |
|---|---|---|
| Missions as data | `game/scripts/systems/mission_library.gd`, `game/scripts/autoload/mission_system.gd`, `game/story/missions/act1.json` | GdUnit: `test_mission_library.gd`, `test_mission_system.gd` |
| Day loop | `game/scripts/autoload/day_loop.gd` (autosave slot 1, `dN_complete` → advance → `dN+1_wake`) | GdUnit: `test_day_loop.gd` |
| Naming ritual | `name_entry` DSL command (parser + runner), `name_entry_panel.gd/.tscn`, authored once in `d1_observatory.scene` | GdUnit: `test_name_entry.gd` |
| Objective HUD | `objective_hud.gd/.tscn` (visible only in MISSION mode; day counter + objective key) | Manual + tour (pending) |
| Runner extensions | `dialogue_runner.gd`: `scene_finished` signal, speaker-key fallback (`speaker.<id>`), portrait moods, `show_barrier_line()` (diegetic refusals) | Existing runner suite still green |
| Exit triggers | `room.gd` rewrite: `Triggers/<exit_id>` Area2D → `MissionSystem.on_exit_touched` | `test_mission_system.gd` |
| Room codegen | `game/tools/gen_rooms.gd` (layout JSON → .tscn per node contract), generic `gen_resources.gd` | Runs; output verification pending art |
| Room layouts | `game/story/rooms/{home,town,dolmus,obs,registry}.json` — every marker/prop/NPC/exit the `d1_*.scene` files address | GdUnit: `test_act1_content_coverage.gd` (partially red until `make resources`, see §5) |
| Day-1 driver | `game/tools/day1_probe.gd` (full Day-1 auto-play, beat PNGs under xvfb) | Written, not yet run end-to-end |
| Art: home | `artgen/manifests/tiles_home.json`, `tiles/home_interior.py` → `home_sheet` + `home_props` | pytest green, visually reviewed |
| Art: town | `tiles_town.json`, `tiles/town_exterior.py` → `town_sheet` + `town_props` | pytest green, visually reviewed |
| Art: dolmuş | `tiles_dolmus.json`, `tiles/dolmus_interior.py` → `dolmus_sheet` + `dolmus_props` | pytest green (8/8, byte-identical double build), visually reviewed 2026-07-13 |
| Cast parameters | `artgen/cast/characters.json` — canonical appearance data for all 11 characters | Design artifact, treat as spec |

New autoloads `MissionSystem` and `DayLoop` are **appended after `Debug`** in `project.godot`.
The canonical boot order in `ARCHITECTURE.md` is unchanged for the original eight; do not reorder.

### Remaining implementation (the Codex scope)

1. **Observatory art** — the only missing environment. New manifest `artgen/manifests/tiles_obs.json`
   + generator `artgen/artgen/tiles/obs_interior.py` emitting:
   - `tiles/obs_sheet.png` + sidecar — tiles exactly `["floor_lino", "floor_lino_var",
     "wall_panel", "window_sky"]` (names must match `game/story/rooms/obs.json` `tile_legend`),
     sidecar `solid: ["wall_panel", "window_sky"]`. 16×16 art px baked at 2× → 32×32.
   - `props/obs_props.png` + sidecar with **exactly** these keys (from `obs.json`): `window_dish`,
     `console_bank`, `console_chair`, `printer`, `whiteboard`, `rack_a`, `rack_b`, `office_door`,
     `archive_shelf`.
   - `props/obs_printout.png` + sidecar with the single key `printout_overlay` — the dot-matrix
     printout close-up (D1 discovery beat; `show printout_overlay` in `d1_observatory.scene`,
     z_index 50). Roughly 128×96 final px, paper ramp, and the anomaly trace drawn in
     signal-magenta `#ff2fd6` — this is the **one sanctioned magenta use** in obs art (diegetic
     signal representation per the signal-grammar law).
   - Direction: 1970s-institutional Turkish state observatory — worn lino (paper/stone ramps),
     painted panel walls, dusk sky through `window_sky` and the dish silhouette in `window_dish`
     (amber→rose→void gradient, golden-hour canon). Console CRTs use the `crt` ramp; racks get
     static LED speckle. No green foliage anywhere (palette has no green; autumn-gold canon).
2. **Cast walk sheets** — one manifest (suggest `artgen/manifests/cast.json`) + generator
   (suggest `artgen/artgen/sprites/cast.py`) emitting per character
   `sprites/<id>_sheet.png` + sidecar for: `hoca` (replaces the graybox placeholder **at the same
   path with the same sidecar shape**), `yildiz`, `fadime`, `musa`, `sukru`, `elif`, `kadir`,
   `ismet`, `metin`, `ebru`, `tezcan`. Appearance data: `artgen/cast/characters.json`.
   Sidecar contract is fixed by the existing `hoca_sheet.json`: `frame [32,48]` (adults; `yildiz`
   uses `[32,32]`), `cols 4`, `rows 5`, anims `idle_s` (1 frame) + `walk_s/n/e/w` (4 frames, fps 8).
   `gen_resources.gd` picks these up by stem — no engine change needed or allowed.
   Derive each character's RNG from the manifest seed + character id (town per-asset precedent)
   so adding a character never reflows another's pixels.
3. **Portraits** — `sprites/portraits/<id>.png` for all 11 ids above, plus hoca moods
   `hoca_tired.png`, `hoca_wry.png`, `hoca_listening.png` (paths hard-wired in `gen_rooms.gd`).
   **64×64 final px** (32×32 art at 2×) — see decision D2 below. Emit from the same cast generator.
4. **Pipeline run-through + verification** — §5 in order.
5. **PROGRESS.md milestone record** at completion only (see §7), including the deviations in D1–D5.

### Non-goals (do not touch)

- Audio: `AudioManager` stays a wired-later stub; `audiogen/` is M6.
- Days 2–7 content, web export verification, `answer_available` enabling (reserved, tested stub).
- The save/meta known-accepted gaps listed in `ARCHITECTURE.md` — documented, dormant, not bugs.
- `PLAN.md` edits of any kind.

## 3. Decisions already made (with rejected alternatives)

- **D1 — one manifest + one generator per room's art**, emitting tile sheet and prop sheet
  together (rejected: per-asset manifests — atlas append-only contract is easier to honour with
  one authority per room; matches home/town/dolmuş precedent).
- **D2 — portraits are 64×64 final px**, not PLAN's "~96–128px". The DialogueBox portrait slot is
  64×64; integer-perfect beats letterboxed larger art. Record as a PLAN deviation in PROGRESS.md.
- **D3 — 9 townsfolk + hoca + yıldız**, exceeding PLAN's "4–6 townsfolk": every named NPC placed
  in the four room layouts must render or the content-coverage suite fails. Cutting cast would
  mean cutting authored story beats — rejected.
- **D4 — autumn-gold town, no green**: palette deliberately has no green ramp; all foliage
  (poplars) is amber/earth. Canon: Day 1 is golden hour. Do not add palette colors (closed set —
  hand back to Claude if art genuinely cannot be expressed in it).
- **D5 — mission completion always flows through `GameState.flag_changed`** — `setflag` in a
  scene and an exit-touch take the identical path. Scene chaining is serialized on
  `DialogueRunner.scene_finished`. Do not add a second completion channel.
- **D6 — refusal lines cascade** `refusal.<mission_id>.<exit_id>` → `refusal.<exit_id>` →
  `refusal.generic` (first key that translates wins); authored floor exists in `ui.csv`.

## 4. Data contracts (already implemented — for reference, not redesign)

- **Room layout JSON** (`game/story/rooms/*.json`): positions in **tile units** (×32 at bake);
  `tile_legend` maps layer glyphs → tile names that must exist in the room's tile sidecar;
  `props[].name` is the node name, optional `props[].prop` aliases the sheet key (dolmuş window
  strips reuse `window_valley` three times); `npcs[].frames`/`portrait` name sprite stems;
  `exits[]` become `Triggers/<id>` Area2Ds; `night_tint: true` adds the hidden CanvasModulate.
- **Tile sidecar**: `{grid: {cell, cols, rows}, tiles: [names...], solid: [names...]}`.
- **Prop sidecar**: `{scale, props: {name: {region: [x,y,w,h] final px, solid: [x,y,w,h]|null}}}` —
  solid rects are bottom-slice footprints (see `home_props.json` for the pattern).
- **Mission JSON** (`game/story/missions/act1.json`): `{id, objective_key, allowed_exits[],
  complete_on_flag, on_complete_script}`; parsed by `MissionLibrary.parse` (never raises).
- Scene-script names resolve via `MissionLibrary.scene_script_path()` — one shared resolver.

## 5. Validation sequence (run in this order)

```
make pytest      # determinism (double build byte-identical) + palette lint — all manifests
make art         # regenerate; then visually review every new/changed sheet upscaled
make resources   # import + gen_resources + gen_rooms → .tres + room .tscn (committed once)
make test        # full GdUnit — test_act1_content_coverage.gd must flip fully green here
```

Then the Day-1 end-to-end probe (exit code 0 = pass):

```
~/apps/godot-4.5.2/godot --path game --headless --script res://tools/day1_probe.gd
xvfb-run -a -s "-screen 0 1280x720x24" ~/apps/godot-4.5.2/godot --path game \
    --rendering-driver opengl3 --script res://tools/day1_probe.gd   # + beat PNGs
xvfb-run -a -s "-screen 0 1280x720x24" make tour                    # full tour PNGs
```

Review every PNG by eye (beat shots in `artifacts/shots/day1/`, tour in `artifacts/shots/`).
The tour run also captures the deferred M3 `waterfall` tour PNG — closes that PROGRESS.md box.

Known-red baseline before art lands: `test_act1_content_coverage.gd`'s generated-scene check
fails until `make resources` has run with obs art present. Everything else was green at
145/145 when the engine work landed.

## 6. Stop-and-hand-back triggers (per AGENTS.md)

- Any need to extend the palette, the DSL command set, autoload order, or the DialogueBox
  portrait slot size.
- `day1_probe` failing for a **design** reason (mission/day-loop/mode-gating logic wrong) rather
  than an implementation bug.
- Room layouts turning out to need re-blocking against the `.scene` choreography (camera pans
  revealing void, walk paths through solids) beyond marker/position nudges in the layout JSONs.
- Art direction judgment beyond §2 and `artgen/cast/characters.json` (new characters, new rooms,
  changed story beats).

## 7. Completion and commit

When the full §5 sequence is green and reviewed: update `PROGRESS.md` (M4 section: checkboxes,
deviations D1–D5, the M3 tour-PNG closure), commit the whole M4 slice on `feat/m4-act1-world`,
fast-forward merge to `master` (M3 precedent), and push `master` to `origin`
(sanctioned by AGENTS.md at a Codex-to-Claude handoff). Keep generated art, `.tres`, room
`.tscn`, and `.import` files in the commit — generated output is deliberately committed.

## 8. Outcome (M4 closed)

Shipped complete: 4 room tilesets, 11 cast walk sheets + 14 portraits, 4 codegen room scenes, the
mission/day-loop/name-entry systems, and Day 1 playable end-to-end (`--day1-probe` PASS through the
Day-2 roll). Validation green: 151/151 GdUnit, 8/8 pytest, tour + 8 Day-1 beat PNGs reviewed.

Post-implementation adversarial review surfaced 6 findings (verifier pass truncated by a model usage
limit, so triaged by hand). Two were genuine Day-1 defects and are fixed in this slice:

1. `d1.town.sys.001` showed a literal `{name}` (`_do_say` passes no format params). Fixed by removing
   the token, **not** substituting — canon lock IX bars the observer name from Act 1 dialogue (it may
   appear only in save slots / the phantom slot / one Act 3 inscription; same precedent as the dormant
   spectro `decode_text`).
2. `d1_observatory` armed `mission m_d2_morning` before its closing `fade`, enabling MISSION-mode exits
   during the fade. Removed; day-2 setup is `d2_wake`'s job. New authoring rule: after
   `setflag dN_complete`, only `fade`/`end_scene` may follow (DayLoop awaits `scene_finished`).

The remaining four are M5 scope (Days 2–7 wiring) and are logged in `PROGRESS.md` → Known open items:
wake scripts don't arm their morning mission (soft-lock past Day 1); end-of-day observatory tails and
`m_d7_sendoff` need the same audit; autosave doesn't yet persist `current_mission_id` for a
continue-from-save.
