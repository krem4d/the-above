class_name WaterfallSession
extends RefCounted
## Pure logic for one spectro minigame session (M3, "spectrogram/waterfall
## mechanic v1"). No engine/UI dependencies — constructed from a resolved
## config Dictionary (see WaterfallSessionLibrary for the JSON source), so
## it is fully unit-testable the same way DialogueParser is.
##
## `kind` drives which player action gates completion:
##   tutorial   — tune current_freq_mhz onto target_freq_mhz and hold it
##                (with drift_mhz_s the target moves — "align the drift")
##   beam_scan  — visit all three beams (cycle_beam); the trace lives only in
##                signal_beam, so the player feels the "beam 2 only" fault
##   onoff      — observe both on-source and off-source states
##   broadcast, answer_gate, keystone, taxonomy — timed; complete once
##                elapsed_seconds reaches duration_seconds. These four are
##                distinct only as narrative tags (which Day's session this
##                is) — mechanically they are the same timer.
##
## Fake physics throughout (PLAN M3): authored numbers, no FFT. drift_mhz_s
## moves the target; cell_seconds pulses the trace; `events` opens timed
## payload windows (active_event()) the view renders.
##
## press_answer() is gated by the orthogonal `answer_available` flag, NOT by
## `kind`. It is never required for completion and is a no-op unless the
## session opted in — design law: no fail states, and the ANSWER verb must
## always be avoidable and never rewarded (bible D5-S4). No Act 1 session
## currently enables it: Day 5's transgression answer is authored as a
## dialogue choice in d5_observatory.scene (setflag answered_signal). The
## capability is kept, documented, and tested for a future console-native
## ANSWER, the same way AudioManager ships as a wired-later stub.

const SIGNAL_OMNIPRESENT_BEAM := -1

var session_id: String
var kind: String
var target_freq_mhz: float
var tolerance_mhz: float
var freq_min_mhz: float
var freq_max_mhz: float
var signal_beam: int
var hold_seconds: float
var duration_seconds: float
var cell_seconds: float
var drift_mhz_s: float
var answer_available: bool
var segments: Array
var events: Array

var current_freq_mhz: float
var current_beam: int
var on_source: bool
var elapsed_seconds: float = 0.0

var _hold_accum: float = 0.0
var _beams_logged: Dictionary = {}
var _seen_on: bool = false
var _seen_off: bool = false
var _answered: bool = false
var _last_verb: String = ""


func _init(id: String, config: Dictionary) -> void:
	session_id = id
	kind = String(config.get("kind", "broadcast"))
	target_freq_mhz = float(config.get("target_freq_mhz", 1421.6))
	tolerance_mhz = float(config.get("tolerance_mhz", 0.5))
	freq_min_mhz = float(config.get("freq_min_mhz", target_freq_mhz - 10.0))
	freq_max_mhz = float(config.get("freq_max_mhz", target_freq_mhz + 10.0))
	signal_beam = int(config.get("signal_beam", SIGNAL_OMNIPRESENT_BEAM))
	hold_seconds = float(config.get("hold_seconds", 1.5))
	duration_seconds = float(config.get("duration_seconds", 20.0))
	cell_seconds = float(config.get("cell_seconds", 0.0))
	drift_mhz_s = float(config.get("drift_mhz_s", 0.0))
	answer_available = bool(config.get("answer_available", false))
	segments = config.get("segments", [])
	events = config.get("events", [])

	current_freq_mhz = float(config.get("start_freq_mhz", target_freq_mhz))
	current_beam = int(config.get("start_beam", 1))
	on_source = bool(config.get("start_on_source", true))

	if kind == "beam_scan":
		_beams_logged[current_beam] = true
	if kind == "onoff":
		if on_source:
			_seen_on = true
		else:
			_seen_off = true


func adjust_frequency(delta_mhz: float) -> void:
	current_freq_mhz = clampf(current_freq_mhz + delta_mhz, freq_min_mhz, freq_max_mhz)


func set_frequency(value_mhz: float) -> void:
	current_freq_mhz = clampf(value_mhz, freq_min_mhz, freq_max_mhz)


## 0..1 position of current_freq_mhz across [freq_min_mhz, freq_max_mhz],
## for the view's cursor line.
func freq_ratio() -> float:
	if freq_max_mhz <= freq_min_mhz:
		return 0.0
	return clampf((current_freq_mhz - freq_min_mhz) / (freq_max_mhz - freq_min_mhz), 0.0, 1.0)


## Same mapping for target_freq_mhz, for the view's guide line. NOT static:
## with drift_mhz_s the target moves every tick, so the view must re-read
## this per frame (it does — see waterfall_view.gd's _process).
func target_ratio() -> float:
	if freq_max_mhz <= freq_min_mhz:
		return 0.0
	return clampf((target_freq_mhz - freq_min_mhz) / (freq_max_mhz - freq_min_mhz), 0.0, 1.0)


func cycle_beam(direction: int) -> void:
	if kind != "beam_scan":
		return
	current_beam = ((current_beam - 1 + direction) % 3 + 3) % 3 + 1
	_beams_logged[current_beam] = true


func toggle_on_source() -> void:
	if kind != "onoff":
		return
	on_source = not on_source
	if on_source:
		_seen_on = true
	else:
		_seen_off = true


func tick(delta: float) -> void:
	elapsed_seconds += delta
	# Fake physics (PLAN M3): the source drifts as an authored rate, not an
	# FFT. The player's "align the drift" verb is chasing target_freq_mhz.
	# Clamped to the tunable range so a long session can't drift the target
	# somewhere the player literally cannot follow (no fail states).
	if drift_mhz_s != 0.0:
		target_freq_mhz = clampf(target_freq_mhz + drift_mhz_s * delta, freq_min_mhz, freq_max_mhz)
	if kind == "tutorial":
		if signal_present():
			_hold_accum += delta
		else:
			_hold_accum = 0.0


## Whether the trace is currently visible — the same test the view's
## canvas uses to decide whether to paint a magenta cell this tick.
func signal_present() -> bool:
	if kind == "onoff":
		return on_source and _freq_in_tolerance() and _cell_active()
	# The beam gate is only meaningful where the player can actually change
	# beams: beam_scan's whole mechanic is "the trace is only under beam 2".
	# Every other T1 session is parked on the dish's beam-2 output with no
	# beam control, so gating on current_beam there (which stays at its
	# start value, 1) would render the trace permanently absent — signal_beam
	# on those sessions is canon annotation, not a live gate.
	if kind == "beam_scan" and signal_beam != SIGNAL_OMNIPRESENT_BEAM:
		return current_beam == signal_beam and _freq_in_tolerance() and _cell_active()
	return _freq_in_tolerance() and _cell_active()


## The signal broadcasts in cells (canon: 11-minute cells the player counts,
## bible D2-S5). When cell_seconds > 0 the trace is present only during the
## first half of each cell, giving a visible, countable on/off cadence — the
## "count the interval" prompt made real. cell_seconds == 0 (tutorial,
## beam_scan, onoff) means a steady, uninterrupted trace.
func _cell_active() -> bool:
	if cell_seconds <= 0.0:
		return true
	return fmod(elapsed_seconds, cell_seconds) < cell_seconds * 0.5


func is_objective_met() -> bool:
	match kind:
		"tutorial":
			return _hold_accum >= hold_seconds
		"beam_scan":
			return _beams_logged.size() >= 3
		"onoff":
			return _seen_on and _seen_off
		_:
			return elapsed_seconds >= duration_seconds


## Records which of LISTEN/RECORD/LOG the player last pressed (the config's
## primary_verb). Never gates completion and not currently surfaced in the
## UI — the view builds its hint from config directly; this is a hook for
## future logging/telemetry. The bible never pins the three verbs to
## distinct mechanical effects, so all three simply confirm intent.
func press_verb(verb: String) -> void:
	_last_verb = verb


func last_verb() -> String:
	return _last_verb


func press_answer() -> bool:
	if not answer_available:
		return false
	_answered = true
	return true


func was_answered() -> bool:
	return _answered


## The timed signal event whose window contains the current elapsed time,
## or {} when none is active (PLAN M3: "signal events carry horror
## payloads"). Events are authored as {at_seconds, duration_seconds, kind,
## ...} in the manifest; the view decides how each kind renders
## (shape_burst -> broadband smear on the canvas; decode_text -> readout
## line). Pure data here — the session never resolves payload text itself.
func active_event() -> Dictionary:
	for event: Dictionary in events:
		var start := float(event.get("at_seconds", 0.0))
		var length := float(event.get("duration_seconds", 0.0))
		if elapsed_seconds >= start and elapsed_seconds < start + length:
			return event
	return {}


## Locale key of the taxonomy tag active at the current elapsed time, or ""
## before the first segment. Assumes `segments` is sorted ascending by
## at_seconds (true of the authored manifest).
func current_taxonomy_label_key() -> String:
	var current_key := ""
	for seg: Dictionary in segments:
		if elapsed_seconds >= float(seg.get("at_seconds", 0.0)):
			current_key = String(seg.get("label_key", ""))
		else:
			break
	return current_key


func to_result() -> Dictionary:
	return {
		"session_id": session_id,
		"objective_met": is_objective_met(),
		"answered": _answered,
	}


func _freq_in_tolerance() -> bool:
	return absf(current_freq_mhz - target_freq_mhz) <= tolerance_mhz
