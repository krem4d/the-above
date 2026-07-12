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


func _ready() -> void:
	visible = false
	set_process(false)
	_exit_hint_label.text = Locale.t("spectro.hint.exit")


func start_session(session_id: String, config: Dictionary) -> void:
	_config = config
	_session = WaterfallSession.new(session_id, config)
	_canvas.reset()
	_canvas.set_target_ratio(_session.target_ratio())
	_prompt_label.text = Locale.t(String(config.get("prompt_key", "")))
	_context_label.visible = _session.kind in ["beam_scan", "onoff"]
	_taxonomy_label.visible = _session.kind == "taxonomy"
	_answer_hint_label.visible = _session.answer_available
	if _session.answer_available:
		_answer_hint_label.text = Locale.t("spectro.hint.answer", {"verb": Locale.t("spectro.verb.answer")})
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
	_canvas.push_column(_session.signal_present(), _session.freq_ratio())
	_update_labels()


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
