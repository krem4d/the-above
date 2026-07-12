extends GdUnitTestSuite
## WaterfallSession: pure per-session state machine (M3). Mirrors
## test_dialogue_parser.gd's approach — literal config Dictionaries in,
## behavior asserted directly, no scene/engine dependencies.

func test_tutorial_signal_present_only_within_tolerance() -> void:
	var session := WaterfallSession.new("t", {
		"kind": "tutorial", "target_freq_mhz": 1400.0, "tolerance_mhz": 0.5,
		"freq_min_mhz": 1390.0, "freq_max_mhz": 1410.0, "start_freq_mhz": 1390.0,
	})
	assert_bool(session.signal_present()).is_false()
	session.set_frequency(1400.2)
	assert_bool(session.signal_present()).is_true()
	session.set_frequency(1405.0)
	assert_bool(session.signal_present()).is_false()


func test_tutorial_objective_requires_holding_lock() -> void:
	var session := WaterfallSession.new("t", {
		"kind": "tutorial", "target_freq_mhz": 1400.0, "tolerance_mhz": 0.5,
		"freq_min_mhz": 1390.0, "freq_max_mhz": 1410.0, "start_freq_mhz": 1400.0,
		"hold_seconds": 1.0,
	})
	assert_bool(session.is_objective_met()).is_false()
	session.tick(0.5)
	assert_bool(session.is_objective_met()).is_false()
	session.tick(0.6)
	assert_bool(session.is_objective_met()).is_true()


func test_tutorial_losing_lock_resets_hold_timer() -> void:
	var session := WaterfallSession.new("t", {
		"kind": "tutorial", "target_freq_mhz": 1400.0, "tolerance_mhz": 0.5,
		"freq_min_mhz": 1390.0, "freq_max_mhz": 1410.0, "start_freq_mhz": 1400.0,
		"hold_seconds": 1.0,
	})
	session.tick(0.8)
	session.set_frequency(1405.0)   # drift off-target
	session.tick(0.1)
	session.set_frequency(1400.0)
	session.tick(0.8)
	assert_bool(session.is_objective_met()).is_false()   # accumulator restarted, only 0.8s held this time


func test_beam_scan_signal_only_in_configured_beam() -> void:
	var session := WaterfallSession.new("b", {
		"kind": "beam_scan", "target_freq_mhz": 1421.6, "tolerance_mhz": 0.5,
		"signal_beam": 2, "start_freq_mhz": 1421.6, "start_beam": 1,
	})
	assert_bool(session.signal_present()).is_false()
	session.cycle_beam(1)
	assert_int(session.current_beam).is_equal(2)
	assert_bool(session.signal_present()).is_true()


func test_beam_scan_objective_needs_all_three_beams_visited() -> void:
	var session := WaterfallSession.new("b", {"kind": "beam_scan", "signal_beam": 2, "start_beam": 1})
	assert_bool(session.is_objective_met()).is_false()
	session.cycle_beam(1)
	assert_bool(session.is_objective_met()).is_false()
	session.cycle_beam(1)
	assert_bool(session.is_objective_met()).is_true()


func test_beam_scan_cycle_wraps_both_directions() -> void:
	var session := WaterfallSession.new("b", {"kind": "beam_scan", "start_beam": 1})
	session.cycle_beam(-1)
	assert_int(session.current_beam).is_equal(3)
	session.cycle_beam(1)
	assert_int(session.current_beam).is_equal(1)


func test_beam_scan_cycle_is_a_noop_for_other_kinds() -> void:
	var session := WaterfallSession.new("t", {"kind": "tutorial", "start_beam": 1})
	session.cycle_beam(1)
	assert_int(session.current_beam).is_equal(1)


func test_onoff_signal_present_only_when_on_source_and_in_tolerance() -> void:
	var session := WaterfallSession.new("o", {
		"kind": "onoff", "target_freq_mhz": 1421.6, "tolerance_mhz": 0.5,
		"start_freq_mhz": 1421.6, "start_on_source": true,
	})
	assert_bool(session.signal_present()).is_true()
	session.toggle_on_source()
	assert_bool(session.on_source).is_false()
	assert_bool(session.signal_present()).is_false()


func test_onoff_objective_needs_both_states_observed() -> void:
	var session := WaterfallSession.new("o", {"kind": "onoff", "start_on_source": true})
	assert_bool(session.is_objective_met()).is_false()   # only on-source seen so far
	session.toggle_on_source()
	assert_bool(session.is_objective_met()).is_true()


func test_non_beam_scan_session_shows_trace_despite_signal_beam() -> void:
	# Regression (review must-fix #1): broadcast/taxonomy/answer_gate/keystone
	# sessions set signal_beam=2 but never let the player change beams, so
	# gating signal_present() on current_beam (frozen at 1) rendered the trace
	# permanently absent. The beam gate now applies only to beam_scan.
	for kind: String in ["broadcast", "taxonomy", "answer_gate", "keystone"]:
		var session := WaterfallSession.new("s", {
			"kind": kind, "target_freq_mhz": 1421.6, "tolerance_mhz": 0.5,
			"freq_min_mhz": 1411.6, "freq_max_mhz": 1431.6, "start_freq_mhz": 1421.6,
			"signal_beam": 2, "duration_seconds": 100.0,
		})
		assert_bool(session.signal_present()).override_failure_message(
			"kind '%s' with signal_beam=2 must still show the trace when tuned" % kind
		).is_true()


func test_cell_seconds_produces_a_countable_on_off_cadence() -> void:
	# The canon 11-minute cell (bible D2-S5): with cell_seconds set, the trace
	# is present only in the first half of each cell, so the player can count.
	var session := WaterfallSession.new("c", {
		"kind": "broadcast", "target_freq_mhz": 1421.6, "tolerance_mhz": 0.5,
		"freq_min_mhz": 1411.6, "freq_max_mhz": 1431.6, "start_freq_mhz": 1421.6,
		"signal_beam": 2, "cell_seconds": 10.0, "duration_seconds": 100.0,
	})
	assert_bool(session.signal_present()).is_true()    # elapsed 0 — first half of cell 1
	session.tick(6.0)
	assert_bool(session.signal_present()).is_false()   # elapsed 6 — second half, silent
	session.tick(5.0)
	assert_bool(session.signal_present()).is_true()    # elapsed 11 — first half of cell 2


func test_zero_cell_seconds_gives_a_steady_trace() -> void:
	var session := WaterfallSession.new("t", {
		"kind": "broadcast", "target_freq_mhz": 1421.6, "tolerance_mhz": 0.5,
		"freq_min_mhz": 1411.6, "freq_max_mhz": 1431.6, "start_freq_mhz": 1421.6,
		"duration_seconds": 100.0,
	})
	assert_bool(session.signal_present()).is_true()
	session.tick(50.0)
	assert_bool(session.signal_present()).is_true()   # no cadence — never blinks off


func test_broadcast_kind_completes_after_duration() -> void:
	var session := WaterfallSession.new("br", {"kind": "broadcast", "duration_seconds": 2.0})
	session.tick(1.0)
	assert_bool(session.is_objective_met()).is_false()
	session.tick(1.5)
	assert_bool(session.is_objective_met()).is_true()


func test_answer_gate_press_answer_requires_availability() -> void:
	var blocked := WaterfallSession.new("a", {"kind": "answer_gate", "answer_available": false})
	assert_bool(blocked.press_answer()).is_false()
	assert_bool(blocked.was_answered()).is_false()

	var open_session := WaterfallSession.new("a", {"kind": "answer_gate", "answer_available": true})
	assert_bool(open_session.press_answer()).is_true()
	assert_bool(open_session.was_answered()).is_true()


func test_answer_is_never_required_for_objective_completion() -> void:
	# Design law: no fail states, ANSWER is always avoidable (bible D5-S4:
	# "entirely avoidable... nothing prompts, nothing rewards").
	var session := WaterfallSession.new("a", {
		"kind": "answer_gate", "answer_available": true, "duration_seconds": 1.0,
	})
	session.tick(1.5)
	assert_bool(session.is_objective_met()).is_true()
	assert_bool(session.was_answered()).is_false()


func test_taxonomy_label_advances_through_segments_in_order() -> void:
	var session := WaterfallSession.new("tx", {
		"kind": "taxonomy", "duration_seconds": 30.0,
		"segments": [
			{"at_seconds": 0.0, "label_key": "spectro.taxonomy.dawn_song"},
			{"at_seconds": 10.0, "label_key": "spectro.taxonomy.contact_call"},
		],
	})
	assert_str(session.current_taxonomy_label_key()).is_equal("spectro.taxonomy.dawn_song")
	session.tick(10.5)
	assert_str(session.current_taxonomy_label_key()).is_equal("spectro.taxonomy.contact_call")


func test_taxonomy_label_empty_before_first_segment() -> void:
	var session := WaterfallSession.new("tx", {
		"kind": "taxonomy",
		"segments": [{"at_seconds": 5.0, "label_key": "spectro.taxonomy.dawn_song"}],
	})
	assert_str(session.current_taxonomy_label_key()).is_equal("")


func test_freq_ratio_and_target_ratio_map_into_unit_range() -> void:
	var session := WaterfallSession.new("t", {
		"target_freq_mhz": 1400.0, "freq_min_mhz": 1390.0, "freq_max_mhz": 1410.0,
		"start_freq_mhz": 1390.0,
	})
	assert_float(session.freq_ratio()).is_equal_approx(0.0, 0.001)
	assert_float(session.target_ratio()).is_equal_approx(0.5, 0.001)
	session.set_frequency(1410.0)
	assert_float(session.freq_ratio()).is_equal_approx(1.0, 0.001)


func test_adjust_frequency_clamps_to_configured_range() -> void:
	var session := WaterfallSession.new("t", {
		"freq_min_mhz": 1390.0, "freq_max_mhz": 1410.0, "start_freq_mhz": 1390.0,
	})
	session.adjust_frequency(-5.0)
	assert_float(session.current_freq_mhz).is_equal_approx(1390.0, 0.001)
	session.adjust_frequency(100.0)
	assert_float(session.current_freq_mhz).is_equal_approx(1410.0, 0.001)


func test_to_result_shape() -> void:
	var session := WaterfallSession.new("cal_pulsar", {"kind": "broadcast", "duration_seconds": 0.0})
	var result := session.to_result()
	assert_str(result["session_id"]).is_equal("cal_pulsar")
	assert_bool(result["objective_met"]).is_true()
	assert_bool(result["answered"]).is_false()


func test_press_verb_is_flavor_only_and_never_gates_completion() -> void:
	var session := WaterfallSession.new("br", {"kind": "broadcast", "duration_seconds": 5.0})
	session.press_verb("listen")
	assert_str(session.last_verb()).is_equal("listen")
	assert_bool(session.is_objective_met()).is_false()   # verb press alone never completes a timed session
