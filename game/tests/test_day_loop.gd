extends GdUnitTestSuite
## DayLoop: the sleep->wake rollover contract. UI is never set up here, so
## wake scripts no-op with a warning — the loop's day/save mechanics are
## what this suite pins down; the full chain runs in the Day-1 probe.


func before_test() -> void:
	GameState.reset_new_game()
	SceneDirector.current_mission_id = ""
	SaveSystem.delete_save(DayLoop.AUTOSAVE_SLOT)


func after_test() -> void:
	GameState.reset_new_game()
	SaveSystem.delete_save(DayLoop.AUTOSAVE_SLOT)


func test_flag_and_scene_naming_convention() -> void:
	assert_str(DayLoop.day_complete_flag(1)).is_equal("d1_complete")
	assert_str(DayLoop.wake_scene_name(4)).is_equal("d4_wake")
	assert_str(MissionLibrary.scene_script_path("d4_wake")) \
		.is_equal("res://story/scripts/act1/d4_wake.scene")


func test_day_complete_flag_advances_day_and_autosaves() -> void:
	assert_int(GameState.day).is_equal(1)
	GameState.set_flag("d1_complete", true)
	# No scene is running, so the rollover happens synchronously.
	assert_int(GameState.day).is_equal(2)
	assert_bool(SaveSystem.save_exists(DayLoop.AUTOSAVE_SLOT)).is_true()


func test_wrong_day_completion_flag_is_ignored() -> void:
	assert_int(GameState.day).is_equal(1)
	GameState.set_flag("d5_complete", true)
	assert_int(GameState.day).is_equal(1)


func test_rollover_is_not_retriggered_by_reasserting_the_flag() -> void:
	GameState.set_flag("d1_complete", true)
	assert_int(GameState.day).is_equal(2)
	# Re-setting day 1's flag must not roll day 2 over.
	GameState.set_flag("d1_complete", true)
	assert_int(GameState.day).is_equal(2)


func test_every_act1_day_has_a_wake_script() -> void:
	for day in range(1, 8):
		var path := MissionLibrary.scene_script_path(DayLoop.wake_scene_name(day))
		assert_bool(FileAccess.file_exists(path)).override_failure_message(
			"missing wake script for day %d (%s)" % [day, path]
		).is_true()
