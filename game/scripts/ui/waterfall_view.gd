class_name WaterfallView
extends Control
## Spectrogram/waterfall minigame (M3 v1). Presentational + input handling,
## driven by a WaterfallSession (pure logic, game/scripts/systems/).
## Mirrors ChoiceMenu's contract exactly: start_session() shows the UI and
## begins ticking; DialogueRunner awaits `session_closed` the same way it
## awaits ChoiceMenu.chosen — see dialogue_runner.gd's _do_spectro().
##
## Controls reuse the existing input map (no new bindings beyond `answer`,
## project.godot): move_up/down retune frequency; move_left/right cycle
## beams (beam_scan) or toggle on/off-source (onoff); interact is the
## primary verb (LISTEN/RECORD/LOG per config) and, once the objective is
## met, closes the session; cancel always closes it (design law: no fail
## states, the player can never be soft-locked in a minigame); answer is
## its own dedicated key — deliberately not interact/cancel, so the ANSWER
## verb (bible D5-S4, "nothing prompts, nothing rewards") can never be
## triggered by mashing the safe buttons.

signal session_closed(result: Dictionary)

const FREQ_STEP_MHZ := 0.1

@onready var _canvas: WaterfallCanvas = %WaterfallCanvas
@onready var _prompt_label: Label = %PromptLabel
@onready var _freq_label: Label = %FreqLabel
@onready var _context_label: Label = %ContextLabel
@onready var _taxonomy_label: Label = %TaxonomyLabel
@onready var _verb_hint_label: Label = %VerbHintLabel
@onready var _answer_hint_label: Label = %AnswerHintLabel
@onready var _exit_hint_label: Label = %ExitHintLabel

var _session: WaterfallSession = null
var _config: Dictionary = {}
var _decode_showing := false


func _ready() -> void:
	visible = false
	set_process(false)


func start_session(session_id: String, config: Dictionary) -> void:
	_config = config
	_decode_showing = false
	_session = WaterfallSession.new(session_id, config)
	# Noise seed derives from the session id: deterministic per session
	# (PLAN M3 determinism requirement), different between sessions.
	_canvas.reset(session_id.hash())
	_canvas.set_target_ratio(_session.target_ratio())
	_prompt_label.text = Locale.t(String(config.get("prompt_key", "")))
	_context_label.visible = _session.kind in ["beam_scan", "onoff"]
	_taxonomy_label.visible = _session.kind == "taxonomy"
	_answer_hint_label.visible = _session.answer_available
	if _session.answer_available:
		_answer_hint_label.text = Locale.t("spectro.hint.answer", {"verb": Locale.t("spectro.verb.answer")})
	# When ANSWER is on the table, the safe exit is labeled for what it is —
	# PLAN M3: "DO NOT ANSWER is always an available button". Same key
	# (cancel), same behavior; only the label sharpens.
	_exit_hint_label.text = Locale.t(
		"spectro.hint.dont_answer" if _session.answer_available else "spectro.hint.exit"
	)
	_update_labels()
	visible = true
	set_process(true)


func close_session() -> void:
	set_process(false)
	visible = false
	var result: Dictionary = _session.to_result() if _session != null else {}
	session_closed.emit(result)


func _process(delta: float) -> void:
	if _session == null:
		return
	_session.tick(delta)
	# Re-sync the target guide every tick — with drift_mhz_s the target
	# moves, and the guide line is how the player sees what to chase.
	_canvas.set_target_ratio(_session.target_ratio())
	var event := _session.active_event()
	var is_burst: bool = String(event.get("kind", "")) == "shape_burst"
	_canvas.push_column(_session.signal_present(), _session.freq_ratio(), is_burst)
	_update_labels()
	_update_event_readout(event)


## Renders a decode_text event's payload on the taxonomy/readout label —
## and clears it again the moment the window closes, so duration_seconds
## bounds the flash's end as well as its start (a horror beat that lingers
## forever isn't a flash, it's a caption). Payload text is resolved HERE,
## not in the pure session: text_key -> a locale string; text_source
## "observer_name" -> the player's typed name (a reserved capability —
## canon lock IX limits where the observer name may appear, so no authored
## Act 1 session uses it; see PROGRESS.md).
func _update_event_readout(event: Dictionary) -> void:
	if String(event.get("kind", "")) != "decode_text":
		if _decode_showing:
			_decode_showing = false
			_taxonomy_label.text = ""
			# Taxonomy sessions keep the label (its text is re-derived every
			# tick by _update_labels); everything else hides it again.
			_taxonomy_label.visible = _session.kind == "taxonomy"
		return
	_decode_showing = true
	_taxonomy_label.visible = true
	if String(event.get("text_source", "")) == "observer_name":
		_taxonomy_label.text = Locale.t(
			"spectro.decode.line", {"text": GameState.observer_name}
		)
	elif event.has("text_key"):
		_taxonomy_label.text = Locale.t(
			"spectro.decode.line", {"text": Locale.t(String(event["text_key"]))}
		)


func _unhandled_input(event: InputEvent) -> void:
	if _session == null or not visible:
		return
	if event.is_action_pressed("move_up"):
		get_viewport().set_input_as_handled()
		_session.adjust_frequency(FREQ_STEP_MHZ)
	elif event.is_action_pressed("move_down"):
		get_viewport().set_input_as_handled()
		_session.adjust_frequency(-FREQ_STEP_MHZ)
	elif event.is_action_pressed("move_left"):
		get_viewport().set_input_as_handled()
		_handle_cycle(-1)
	elif event.is_action_pressed("move_right"):
		get_viewport().set_input_as_handled()
		_handle_cycle(1)
	elif event.is_action_pressed("interact"):
		get_viewport().set_input_as_handled()
		_handle_primary()
	elif event.is_action_pressed("answer"):
		get_viewport().set_input_as_handled()
		_session.press_answer()
	elif event.is_action_pressed("cancel"):
		get_viewport().set_input_as_handled()
		close_session()


func _handle_cycle(direction: int) -> void:
	match _session.kind:
		"beam_scan":
			_session.cycle_beam(direction)
		"onoff":
			_session.toggle_on_source()
		_:
			pass


func _handle_primary() -> void:
	if _session.is_objective_met():
		close_session()
	else:
		_session.press_verb(String(_config.get("primary_verb", "listen")))


func _update_labels() -> void:
	_freq_label.text = Locale.t("spectro.label.freq", {"freq": "%.1f" % _session.current_freq_mhz})
	if _session.kind == "beam_scan":
		_context_label.text = Locale.t("spectro.label.beam", {"beam": _session.current_beam})
	elif _session.kind == "onoff":
		var key := "spectro.label.on_source" if _session.on_source else "spectro.label.off_source"
		_context_label.text = Locale.t(key)
	if _session.kind == "taxonomy":
		var label_key := _session.current_taxonomy_label_key()
		_taxonomy_label.text = Locale.t(label_key) if label_key != "" else ""
	if _session.is_objective_met():
		_verb_hint_label.text = Locale.t("spectro.hint.close")
	else:
		var verb_key := "spectro.verb." + String(_config.get("primary_verb", "listen"))
		_verb_hint_label.text = Locale.t("spectro.hint.primary", {"verb": Locale.t(verb_key)})
