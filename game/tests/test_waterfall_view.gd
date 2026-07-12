extends GdUnitTestSuite
## WaterfallView: session lifecycle, input-delegate methods, and the
## session_closed contract DialogueRunner awaits (mirrors ChoiceMenu's
## `chosen` signal). Headless-safe: never awaits a rendered frame — this
## suite drives WaterfallView's methods directly instead of simulating real
## InputEvents, the same way test_dialogue_runner.gd calls _step() directly.

const VIEW_SCENE := "res://scenes/minigames/waterfall_view.tscn"


func _make_view() -> WaterfallView:
	var view: WaterfallView = auto_free((load(VIEW_SCENE) as PackedScene).instantiate())
	add_child(view)
	return view


func _tutorial_config() -> Dictionary:
	return {
		"kind": "tutorial", "target_freq_mhz": 1400.0, "tolerance_mhz": 0.5,
		"freq_min_mhz": 1390.0, "freq_max_mhz": 1410.0, "start_freq_mhz": 1391.0,
		"hold_seconds": 0.3, "primary_verb": "listen", "answer_available": false,
		"prompt_key": "",
	}


# Synthetic answer_available:true config exercising the reserved ANSWER
# capability. No shipped Act 1 session enables it (Day 5's answer is a
# dialogue choice in d5_observatory.scene) — these tests prove the capability
# still works for a future console-native ANSWER verb.
func _answer_gate_config() -> Dictionary:
	return {
		"kind": "answer_gate", "target_freq_mhz": 1421.6, "tolerance_mhz": 0.5,
		"freq_min_mhz": 1411.6, "freq_max_mhz": 1431.6, "start_freq_mhz": 1421.6,
		"signal_beam": 2, "duration_seconds": 5.0, "primary_verb": "listen",
		"answer_available": true, "prompt_key": "",
	}


func _beam_scan_config() -> Dictionary:
	return {
		"kind": "beam_scan", "target_freq_mhz": 1421.6, "tolerance_mhz": 0.5,
		"freq_min_mhz": 1411.6, "freq_max_mhz": 1431.6, "start_freq_mhz": 1421.6,
		"start_beam": 1, "signal_beam": 2, "duration_seconds": 40.0,
		"primary_verb": "log", "answer_available": false, "prompt_key": "",
	}


func test_start_session_shows_view_and_close_hides_it() -> void:
	var view := _make_view()
	assert_bool(view.visible).is_false()
	view.start_session("cal_pulsar", _tutorial_config())
	assert_bool(view.visible).is_true()
	view.close_session()
	assert_bool(view.visible).is_false()


func test_close_session_emits_result_matching_session_state() -> void:
	var view := _make_view()
	view.start_session("cal_pulsar", _tutorial_config())
	var results: Array = []
	view.session_closed.connect(func(r: Dictionary) -> void: results.append(r))
	view.close_session()
	assert_int(results.size()).is_equal(1)
	assert_str(results[0]["session_id"]).is_equal("cal_pulsar")
	assert_bool(results[0]["objective_met"]).is_false()


func test_tutorial_freq_adjust_and_hold_meets_objective() -> void:
	var view := _make_view()
	view.start_session("cal_pulsar", _tutorial_config())
	for _i in 90:   # 9.0 MHz toward target (1391.0 -> 1400.0) in 0.1 MHz steps
		view._session.adjust_frequency(WaterfallView.FREQ_STEP_MHZ)
	assert_bool(view._session.signal_present()).is_true()
	for _i in 5:
		view._session.tick(0.1)
	assert_bool(view._session.is_objective_met()).is_true()


func test_primary_interact_closes_once_objective_met_but_not_before() -> void:
	var view := _make_view()
	view.start_session("cal_pulsar", _tutorial_config())
	view._handle_primary()
	assert_bool(view.visible).is_true()   # objective not met yet — stays open
	for _i in 90:
		view._session.adjust_frequency(WaterfallView.FREQ_STEP_MHZ)
	for _i in 5:
		view._session.tick(0.1)
	view._handle_primary()
	assert_bool(view.visible).is_false()


func test_answer_hint_visibility_matches_config() -> void:
	var view := _make_view()
	view.start_session("cal_pulsar", _tutorial_config())
	assert_bool(view._session.answer_available).is_false()
	view.close_session()
	view.start_session("answer_capable_demo", _answer_gate_config())
	assert_bool(view._session.answer_available).is_true()


func test_answer_gate_session_records_answer_in_result() -> void:
	var view := _make_view()
	view.start_session("answer_capable_demo", _answer_gate_config())
	var results: Array = []
	view.session_closed.connect(func(r: Dictionary) -> void: results.append(r))
	view._session.press_answer()
	view.close_session()
	assert_bool(results[0]["answered"]).is_true()


func test_answer_gate_can_close_without_ever_answering() -> void:
	# Design law: no fail states — cancel must always be safe, never routed
	# through ANSWER (bible D5-S4).
	var view := _make_view()
	view.start_session("answer_capable_demo", _answer_gate_config())
	var results: Array = []
	view.session_closed.connect(func(r: Dictionary) -> void: results.append(r))
	view.close_session()
	assert_bool(results[0]["answered"]).is_false()


func test_beam_scan_cycle_marks_all_beams_logged() -> void:
	var view := _make_view()
	view.start_session("sig_beam_check", _beam_scan_config())
	view._handle_cycle(1)
	view._handle_cycle(1)
	assert_bool(view._session.is_objective_met()).is_true()


func test_cycle_is_a_noop_when_kind_has_no_cycle_control() -> void:
	var view := _make_view()
	view.start_session("cal_pulsar", _tutorial_config())
	var beam_before: int = view._session.current_beam
	view._handle_cycle(1)
	assert_int(view._session.current_beam).is_equal(beam_before)


func test_exit_hint_reads_dont_answer_only_when_answer_is_available() -> void:
	# PLAN M3: "DO NOT ANSWER is always an available button" — when ANSWER is
	# on the table, the safe exit is labeled explicitly, not as generic EXIT.
	var view := _make_view()
	view.start_session("answer_capable_demo", _answer_gate_config())
	assert_str(view._exit_hint_label.text).is_equal(Locale.t("spectro.hint.dont_answer"))
	view.close_session()
	view.start_session("cal_pulsar", _tutorial_config())
	assert_str(view._exit_hint_label.text).is_equal(Locale.t("spectro.hint.exit"))


func test_shape_burst_event_pushes_a_burst_column() -> void:
	var config := _tutorial_config()
	config["kind"] = "keystone"
	config["duration_seconds"] = 30.0
	config["events"] = [{"at_seconds": 0.0, "duration_seconds": 5.0, "kind": "shape_burst"}]
	var view := _make_view()
	view.start_session("burst_demo", config)
	view._process(0.016)
	assert_bool(view._canvas._burst_rows.back() >= 0.0).is_true()


func test_decode_readout_clears_when_its_window_closes() -> void:
	# Regression (review): the decoded line used to stay on screen forever
	# after its window closed — a permanent caption instead of a flash. The
	# window's close must clear the label on non-taxonomy sessions.
	var view := _make_view()
	view.start_session("cal_pulsar", _tutorial_config())
	view._update_event_readout(
		{"kind": "decode_text", "text_key": "spectro.taxonomy.dawn_song"}
	)
	assert_bool(view._taxonomy_label.visible).is_true()
	view._update_event_readout({})   # window closed — active_event() returns {}
	assert_str(view._taxonomy_label.text).is_equal("")
	assert_bool(view._taxonomy_label.visible).is_false()   # non-taxonomy kind hides it again


func test_decode_text_event_resolves_observer_name_from_gamestate() -> void:
	# Reserved capability check (canon lock IX limits where the typed name
	# may appear — no authored Act 1 session uses this; the capability must
	# still work for the future beat that will).
	GameState.observer_name = "DENIZ"
	var view := _make_view()
	view.start_session("cal_pulsar", _tutorial_config())
	view._update_event_readout(
		{"kind": "decode_text", "text_source": "observer_name"}
	)
	assert_str(view._taxonomy_label.text).is_equal(
		Locale.t("spectro.decode.line", {"text": "DENIZ"})
	)
	GameState.reset_new_game()


func test_decode_text_event_resolves_locale_text_key() -> void:
	var view := _make_view()
	view.start_session("cal_pulsar", _tutorial_config())
	view._update_event_readout(
		{"kind": "decode_text", "text_key": "spectro.taxonomy.dawn_song"}
	)
	assert_str(view._taxonomy_label.text).is_equal(
		Locale.t("spectro.decode.line", {"text": Locale.t("spectro.taxonomy.dawn_song")})
	)
