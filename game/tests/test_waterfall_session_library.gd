extends GdUnitTestSuite
## WaterfallSessionLibrary.parse(): pure JSON manifest -> id->config transform.
## Mirrors test_dialogue_parser.gd's ok/error-dict assertions.

const REAL_MANIFEST_PATH := "res://story/signals/spectro_sessions.json"

## Every id referenced by an actual `spectro <id>` line in an Act 1 .scene
## file — a missing one here would silently push_warning and no-op in play.
const REQUIRED_SESSION_IDS := [
	"cal_pulsar", "sig_beam_check", "sig_first_listen", "sig_onoff_test",
	"sig_taxonomy", "sig_cell_listen", "sig_long_call",
]


func test_parses_minimal_valid_manifest() -> void:
	var parsed := WaterfallSessionLibrary.parse('{"sessions": {"demo": {"kind": "tutorial"}}}')
	assert_bool(parsed["ok"]).is_true()
	assert_bool(parsed["sessions"].has("demo")).is_true()


func test_fails_on_non_object_root() -> void:
	var parsed := WaterfallSessionLibrary.parse("[1, 2, 3]")
	assert_bool(parsed["ok"]).is_false()
	assert_str(parsed["error"]).is_not_empty()


func test_fails_on_invalid_json() -> void:
	var parsed := WaterfallSessionLibrary.parse("{not valid json")
	assert_bool(parsed["ok"]).is_false()


func test_fails_when_sessions_key_missing() -> void:
	var parsed := WaterfallSessionLibrary.parse('{"notes": "no sessions here"}')
	assert_bool(parsed["ok"]).is_false()


func test_fails_when_sessions_is_not_an_object() -> void:
	var parsed := WaterfallSessionLibrary.parse('{"sessions": [1, 2]}')
	assert_bool(parsed["ok"]).is_false()


func test_get_session_config_returns_empty_dict_for_unknown_id() -> void:
	var config := WaterfallSessionLibrary.get_session_config({"a": {"kind": "tutorial"}}, "nope")
	assert_bool(config.is_empty()).is_true()


func test_get_session_config_returns_the_matching_config() -> void:
	var sessions := {"a": {"kind": "tutorial", "target_freq_mhz": 1400.0}}
	var config := WaterfallSessionLibrary.get_session_config(sessions, "a")
	assert_float(config["target_freq_mhz"]).is_equal_approx(1400.0, 0.001)


func test_real_manifest_file_parses_and_contains_every_referenced_session() -> void:
	assert_bool(FileAccess.file_exists(REAL_MANIFEST_PATH)).is_true()
	var text := FileAccess.get_file_as_string(REAL_MANIFEST_PATH)
	var parsed := WaterfallSessionLibrary.parse(text)
	assert_bool(parsed["ok"]).is_true()
	var sessions: Dictionary = parsed["sessions"]
	for id in REQUIRED_SESSION_IDS:
		assert_bool(sessions.has(id)).override_failure_message(
			"spectro_sessions.json is missing session '%s'" % id
		).is_true()


func test_real_manifest_sessions_construct_valid_waterfall_sessions() -> void:
	var text := FileAccess.get_file_as_string(REAL_MANIFEST_PATH)
	var parsed := WaterfallSessionLibrary.parse(text)
	var sessions: Dictionary = parsed["sessions"]
	for id: String in REQUIRED_SESSION_IDS:
		var config: Dictionary = WaterfallSessionLibrary.get_session_config(sessions, id)
		var session := WaterfallSession.new(id, config)
		assert_str(session.kind).is_not_empty()
		# freq_min <= start <= freq_max: an authoring slip here would put
		# the player's initial tuning outside the drawable/tunable range.
		assert_bool(session.current_freq_mhz >= session.freq_min_mhz).is_true()
		assert_bool(session.current_freq_mhz <= session.freq_max_mhz).is_true()


func test_every_real_session_can_render_its_trace_when_perfectly_tuned() -> void:
	# Guards against the whole-mechanic-dead regression (review must-fix #1):
	# a session whose trace can NEVER appear is worse than useless. For each
	# real session, tune exactly to target (and, for beam_scan, move to the
	# signal's beam) at cell-start, then assert the trace shows.
	var text := FileAccess.get_file_as_string(REAL_MANIFEST_PATH)
	var sessions: Dictionary = WaterfallSessionLibrary.parse(text)["sessions"]
	for id: String in REQUIRED_SESSION_IDS:
		var config: Dictionary = WaterfallSessionLibrary.get_session_config(sessions, id)
		var session := WaterfallSession.new(id, config)
		session.set_frequency(session.target_freq_mhz)
		if session.kind == "beam_scan":
			while session.current_beam != session.signal_beam:
				session.cycle_beam(1)
		assert_bool(session.signal_present()).override_failure_message(
			"session '%s' can never render its trace even when perfectly tuned" % id
		).is_true()
