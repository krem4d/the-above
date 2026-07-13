# THE ABOVE — Forward Plan (M3 → M6)

What we still need to build to ship the Act 1 vertical slice (the free browser prologue + marketing
funnel). This is the **actionable** distillation of the canonical master plan
(`~/.claude/plans/i-want-to-develop-sunny-coral.md`) — read that for the full creative/technical
rationale. Track completion in [`PROGRESS.md`](PROGRESS.md); architecture in [`CLAUDE.md`](CLAUDE.md).

**Where we are:** M0/M1/M-STORY/M2 done. All narrative *systems* and all Act 1 *scripts* exist, but
there is no playable world, no core minigame, and no real art yet — those are M3–M6.

**Order is deliberate:** build the core verb (M3) before the content that uses it (M4/M5), then polish
and ship (M6). Every milestone exits on `make test` + `make pytest` green and a reviewed `make tour`.

---

## M3 — Spectrogram (Waterfall) mechanic v1  ✅ (details in PROGRESS.md)

The signature interactive centrepiece — a radio-spectrogram waterfall the player tunes to isolate a
voice from noise. It replaces Undertale's combat and is the horror-delivery mechanism. Ship it as a
self-contained minigame driven by the existing `spectro` DSL command before any content leans on it.

**Build:**
- [x] `SignalField` model — deterministic, **fake the physics** (no FFT). Authored curves (center
      freq, bandwidth, drift, timed events) drawn into seeded noise. *(Shipped as `WaterfallSession`.)*
- [x] Signal data format — single manifest `game/story/signals/spectro_sessions.json` covering all 7
      authored `spectro` ids *(deviation from one-file-per-signal; `sig_first_anomaly` never existed
      in the authored scenes — see PROGRESS.md M3)*.
- [x] `SpectroOverlay` scene — shipped as `WaterfallView`/`WaterfallCanvas`
      (`game/scenes/minigames/`): scrolling waterfall over seeded noise, tuning input (align drift),
      sustained-proximity hold → reveal flags.
- [x] Signal "events" carry horror payloads — `shape_burst` shipped (authored on `sig_long_call`). The
      typed-name decode (`decode_text`) stays **permanently dormant** — canon lock IX resolved (2026-07-13):
      the observer name never appears in Act 1. Capability remains implemented + tested, unauthored.
- [~] Audio paths: `AudioStreamGenerator` on desktop; pre-baked crossfaded OGG loops on web —
      **deferred to the M6 audio pass** (AudioManager is still the wired-later stub; audiogen/ is M6).
- [x] Wire `spectro <signal_id>` in `DialogueRunner` — blocks the coroutine, sets result flags, returns.
- [x] Tests: spectro-model determinism (GdUnit4); signal-JSON schema validation.

**Exit gate:** one full discovery scene runs end-to-end via the `spectro` DSL command (tune → isolate
→ reveal → set flag) ✅ desktop (headless-verified); ⏳ web build + tour PNG await a machine with a
display/export templates.

---

## M4 — Act 1 world & Day 1 playable

First real art and the first genuinely playable slice: wake → town → observatory → printout
discovery → sleep.

**Build:**
- [ ] Tilesets via artgen: **home**, **town** (Taşlıca), **observatory** — 16×16 art-px → 32×32 PNG,
      hue-shifted ramps, palette hard-fail respected, append-only atlas contract.
- [ ] Character sheets + portraits: **Deniz (Hoca)**, the cat **Yıldız**, 4–6 townsfolk. 4-frame
      4-dir walks; portraits ~96–128 px. Iterate hero art hardest via the screenshot harness.
- [ ] All Act 1 Room scenes (`game/scenes/rooms/act1/`) extending `room.gd`: 4 TileMapLayers, Props,
      NPCs, Area2D Triggers, named Marker2D SpawnPoints, CameraRig.
- [ ] Day-loop scaffolding — per-day wake scripts consulting long-range flags; `ControlMode` gating
      (CUTSCENE / FREE_ROAM / MISSION / MINIGAME); missions as data (`game/story/missions/act1.json`):
      allowed exits, completion flag, on-complete script, diegetic refusal on blocked exits.
- [ ] Day 1 fully playable against the existing `d1_*.scene` scripts.
- [ ] `make resources` regenerates SpriteFrames/TileSet `.tres` from sidecars (committed once).

**Exit gate:** Day 1 playable start-to-finish, pixel-crisp at 3×/6×, tour captures every beat; the
`spectro` discovery from M3 fires inside the real observatory room.

---

## M5 — Full vertical-slice content (Days 2–7)

All escalating Act 1 content against the already-authored scripts. **In progress** — decomposed into
slices in [`docs/decisions/0003-m5-vertical-slice-decomposition.md`](docs/decisions/0003-m5-vertical-slice-decomposition.md);
**M5.1 (Days 2–7 playable spine) is done** (arc plays start→`act1_complete`, `--day7-probe` PASS). The
remaining work (staging: rooms + NPC art + markers; title/meta; anomalies; keystone polish; save-resume)
maps onto the bullets below.

**Build:**
- [ ] Days 2–7 wired and playable: verification gauntlet (drift/nodding/RFI/microwave-peryton beat),
      second-dish confirmation call, the transgression (the ANSWER verb), the **11-minute keystone
      whiteboard scene** (gets disproportionate polish — load-bearing), the "it knows which dish is
      yours" scene, the send-off (emotional peak + neighbour's object), launch.
- [ ] Title screen + meta variants (typed observer name, `title_variant`, `player_tried_to_erase`).
- [ ] Cold open (20 s wordless corridor) + post-credit corridor-with-one-difference (both scripts
      exist: `cold_open.scene`, `post_credit.scene`).
- [ ] The **9 town anomalies** (demo collectible / spot-the-wrongness participatory content).
- [ ] Localization completeness gate: every referenced key has non-empty EN **and** TR; no
      read-never-set flags; TR line-length warnings reviewed.

**Exit gate:** full 7-day scripted playthrough via the tour's auto-advance capturing every beat;
localization gate green; a manual play-session by the user.

---

## M6 — Polish & itch demo (ship)

**Build:**
- [ ] Audio: ambient beds + the signal interval motif + first crew leitmotifs (`audiogen/`, mirrors
      artgen — not yet built out).
- [ ] SSTV/ARG layer embedded in shipping OGGs (decodable spectrogram images, star charts).
- [ ] TR proofread pass; options menu; **share-capture tool** (one-click 4× nearest-neighbour PNG/GIF
      export — platform compression murders 1× pixel art).
- [ ] Web export re-verified on Chrome **and** Firefox (single-threaded, `thread_support=false`;
      audio-unlock click gate; IndexedDB save persistence).
- [ ] itch.io page (copy in `marketing/`), announce trailer cut from clip anchors, tag `v0.1-demo`.

**Exit gate:** the browser matrix passes, the demo is uploaded to itch, `v0.1-demo` tagged.

---

## Cross-cutting constraints (apply to every milestone)

- **No fail states, ever** — fear is the price of answers the player chooses to seek; curiosity is the
  only difficulty.
- **Art guardrails** — palette hard-fail, `ramp_shade` only, ordered-Bayer dithering only, append-only
  atlas; review every tour PNG by eye. No pillow-shading, no pure-black outlines.
- **signal-magenta** appears only with the signal; the abstraction gradient renders signal-linked art
  one fidelity tier lower than its scene.
- **Turkish İ/ı** — never runtime `.to_upper/.to_lower/.capitalize` on player-facing text; casing baked
  into translations (grep-test enforced).
- **Meta tricks** — one per act, each justified by fiction, never touching real user data.
- **Determinism** — art seeded from manifests only; every visual change reviewable as a generator diff.
- **Model policy** — Fable 5 exclusively for the rest of the project, UI and code alike (no switching).

## Top risks to watch (from research)

1. The 11-minute keystone scene failing to land → give it the most writing/playtest budget (M5).
2. Slow burn boring streamers → cold-open flash-forward + printout discovery by ~minute 15 (already
   structured in; verify it reads on stream).
3. Programmatic art looking soulless → per-asset handcrafted drawing code + human review of every PNG.
4. Web-export pitfalls → single-threaded export, audio-unlock gate, pre-baked spectro loops, Chrome +
   Firefox only. Re-run the gate at M6, not just M1.
