extends GdUnitTestSuite
## MissionLibrary.parse(): pure JSON manifest -> id->config transform, plus
## coverage guards over the REAL act1 manifest (every on_complete_script
## resolves to an authored .scene file; every objective key translates in
## BOTH languages). Mirrors test_waterfall_session_library.gd's shape.

const REAL_MANIFEST_PATH := "res://story/missions/act1.json"


func after_test() -> void:
	Locale.set_language("en")


func test_parses_minimal_valid_manifest() -> void:
	var parsed := MissionLibrary.parse(JSON.stringify({"missions": [{
		"id": "m_x", "objective_key": "k", "allowed_exits": ["door"],
		"complete_on_flag": "f", "on_complete_script": "s",
	}]}))
	assert_bool(parsed["ok"]).is_true()
	assert_bool(parsed["missions"].has("m_x")).is_true()


func test_fails_on_invalid_json() -> void:
	assert_bool(MissionLibrary.parse("{nope")["ok"]).is_false()


func test_fails_on_non_object_root() -> void:
	assert_bool(MissionLibrary.parse("[1]")["ok"]).is_false()


func test_fails_without_missions_array() -> void:
	assert_bool(MissionLibrary.parse('{"notes": "x"}')["ok"]).is_false()


func test_fails_on_duplicate_mission_id() -> void:
	var mission := {
		"id": "m_x", "objective_key": "k", "allowed_exits": ["door"],
		"complete_on_flag": "f", "on_complete_script": "s",
	}
	var parsed := MissionLibrary.parse(JSON.stringify({"missions": [mission, mission]}))
	assert_bool(parsed["ok"]).is_false()
	assert_str(parsed["error"]).contains("duplicate")


func test_fails_on_missing_required_field() -> void:
	var parsed := MissionLibrary.parse(JSON.stringify({"missions": [{
		"id": "m_x", "allowed_exits": ["door"], "complete_on_flag": "f",
	}]}))
	assert_bool(parsed["ok"]).is_false()


func test_fails_on_empty_allowed_exits() -> void:
	var parsed := MissionLibrary.parse(JSON.stringify({"missions": [{
		"id": "m_x", "objective_key": "k", "allowed_exits": [],
		"complete_on_flag": "f", "on_complete_script": "s",
	}]}))
	assert_bool(parsed["ok"]).is_false()


func test_decide_exit_completes_on_allowed_and_refuses_otherwise() -> void:
	var mission := {"allowed_exits": ["home_door"], "complete_on_flag": "left"}
	var allowed := MissionLibrary.decide_exit(mission, "home_door")
	assert_str(allowed["action"]).is_equal("complete")
	assert_str(allowed["flag"]).is_equal("left")
	assert_str(MissionLibrary.decide_exit(mission, "dolmus_stop")["action"]).is_equal("refuse")


func test_refusal_candidates_go_specific_to_generic() -> void:
	var keys := MissionLibrary.refusal_key_candidates("m_d1_town", "home_door")
	assert_str(keys[0]).is_equal("refusal.m_d1_town.home_door")
	assert_str(keys[1]).is_equal("refusal.home_door")
	assert_str(keys[2]).is_equal("refusal.generic")


func test_real_manifest_parses_and_every_script_exists() -> void:
	var parsed := MissionLibrary.parse(FileAccess.get_file_as_string(REAL_MANIFEST_PATH))
	assert_bool(parsed["ok"]).is_true()
	var missions: Dictionary = parsed["missions"]
	assert_int(missions.size()).is_greater(0)
	for id: String in missions.keys():
		var script_path := MissionLibrary.scene_script_path(
			String(missions[id]["on_complete_script"])
		)
		assert_bool(FileAccess.file_exists(script_path)).override_failure_message(
			"mission '%s' points at missing scene script %s" % [id, script_path]
		).is_true()


func test_real_manifest_objectives_translate_in_both_languages() -> void:
	var missions: Dictionary = MissionLibrary.parse(
		FileAccess.get_file_as_string(REAL_MANIFEST_PATH)
	)["missions"]
	for lang in ["en", "tr"]:
		Locale.set_language(lang)
		for id: String in missions.keys():
			var key := String(missions[id]["objective_key"])
			assert_bool(Locale.t(key) != key).override_failure_message(
				"objective key '%s' has no %s translation" % [key, lang]
			).is_true()


func test_refusal_generic_floor_translates_in_both_languages() -> void:
	for lang in ["en", "tr"]:
		Locale.set_language(lang)
		assert_bool(Locale.t("refusal.generic") != "refusal.generic").override_failure_message(
			"refusal.generic missing for %s" % lang
		).is_true()
