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
