extends GdUnitTestSuite
## MissionSystem runtime: exit gating against the REAL act1 manifest and
## the completion -> on_complete_script hand-off. UI-dependent paths (the
## refusal line box) are covered by the Day-1 runtime probe, not here —
## DialogueRunner.run_scene no-ops with a warning when setup_ui was never
## called, which is exactly what these headless tests rely on.


func before_test() -> void:
	GameState.reset_new_game()
	SceneDirector.current_mission_id = ""
	SceneDirector.mode = SceneDirector.ControlMode.CUTSCENE


func after_test() -> void:
	GameState.reset_new_game()
	SceneDirector.current_mission_id = ""
	SceneDirector.mode = SceneDirector.ControlMode.CUTSCENE


func test_real_missions_manifest_loads() -> void:
	assert_bool(MissionSystem.missions().size() > 0).is_true()


func test_exit_touch_outside_mission_mode_is_ignored() -> void:
	SceneDirector.start_mission("m_d1_morning")
	SceneDirector.mode = SceneDirector.ControlMode.CUTSCENE
	MissionSystem.on_exit_touched("home_door")
	assert_bool(bool(GameState.get_flag("d1_left_home"))).is_false()


func test_allowed_exit_sets_completion_flag_and_clears_mission() -> void:
	SceneDirector.start_mission("m_d1_morning")   # sets MISSION mode
	MissionSystem.on_exit_touched("home_door")
	assert_bool(bool(GameState.get_flag("d1_left_home"))).is_true()
	# Completion clears the mission and freezes control for the hand-off.
	assert_str(SceneDirector.current_mission_id).is_equal("")
	assert_int(SceneDirector.mode).is_equal(SceneDirector.ControlMode.CUTSCENE)


func test_blocked_exit_does_not_complete() -> void:
	SceneDirector.start_mission("m_d1_town")
	MissionSystem.on_exit_touched("home_door")   # not allowed for this mission
	assert_bool(bool(GameState.get_flag("d1_boarded_dolmus"))).is_false()
	assert_str(SceneDirector.current_mission_id).is_equal("m_d1_town")


func test_completion_via_direct_setflag_takes_same_path() -> void:
	# A scene's `setflag` must complete a mission exactly like an exit touch.
	SceneDirector.start_mission("m_d1_town")
	GameState.set_flag("d1_boarded_dolmus", true)
	assert_str(SceneDirector.current_mission_id).is_equal("")


func test_refusal_text_prefers_specific_key_then_generic() -> void:
	Locale.set_language("en")
	var specific := MissionSystem.refusal_text("m_d1_town", "home_door")
	assert_str(specific).is_equal(Locale.t("refusal.m_d1_town.home_door"))
	assert_bool(specific != "refusal.m_d1_town.home_door").is_true()
	var generic := MissionSystem.refusal_text("m_d1_morning", "nonexistent_exit")
	assert_str(generic).is_equal(Locale.t("refusal.generic"))


func test_completion_flag_of_inactive_mission_does_nothing() -> void:
	SceneDirector.current_mission_id = ""
	GameState.set_flag("d1_left_home", true)
	assert_str(SceneDirector.current_mission_id).is_equal("")
