extends GdUnitTestSuite
## GameState: flags, day counter, and to_dict()/from_dict() round-trip.


func after_test() -> void:
	GameState.reset_new_game()


func test_set_and_get_flag_round_trip() -> void:
	GameState.set_flag("saw_the_star", true)
	assert_bool(GameState.get_flag("saw_the_star")).is_true()
	assert_bool(GameState.has_flag("saw_the_star")).is_true()


func test_get_flag_returns_default_when_unset() -> void:
	assert_bool(GameState.get_flag("never_set")).is_false()
	assert_str(GameState.get_flag("never_set", "fallback")).is_equal("fallback")


func test_flag_changed_signal_fires_only_on_real_change() -> void:
	# GDScript lambdas capture locals by value, so a plain int can't be
	# mutated from inside one — box it in an Array (captured by reference).
	var emit_count := [0]
	GameState.flag_changed.connect(func(_name: String, _value: Variant) -> void: emit_count[0] += 1)
	GameState.set_flag("x", true)
	GameState.set_flag("x", true)   # same value again — must not re-fire
	assert_int(emit_count[0]).is_equal(1)


func test_advance_day_increments_and_emits() -> void:
	var start_day := GameState.day
	var seen_day := [-1]
	GameState.day_changed.connect(func(d: int) -> void: seen_day[0] = d)
	GameState.advance_day()
	assert_int(GameState.day).is_equal(start_day + 1)
	assert_int(seen_day[0]).is_equal(start_day + 1)


func test_to_dict_from_dict_round_trip() -> void:
	GameState.day = 4
	GameState.observer_name = "Deniz"
	GameState.current_room_id = "obs"
	GameState.set_flag("d3_complete", true)

	var data := GameState.to_dict()
	GameState.reset_new_game()
	assert_int(GameState.day).is_equal(1)

	GameState.from_dict(data)
	assert_int(GameState.day).is_equal(4)
	assert_str(GameState.observer_name).is_equal("Deniz")
	assert_str(GameState.current_room_id).is_equal("obs")
	assert_bool(GameState.get_flag("d3_complete")).is_true()


func test_set_flag_survives_cross_type_reuse_of_same_name() -> void:
	# Regression test: the dedup guard used to do `current == value` directly,
	# which throws a runtime type error comparing bool against int/float/
	# String — silently dropping the new value instead of storing it.
	GameState.set_flag("reused_name", true)
	GameState.set_flag("reused_name", 2)
	assert_int(GameState.get_flag("reused_name")).is_equal(2)
	GameState.set_flag("reused_name", "text now")
	assert_str(GameState.get_flag("reused_name")).is_equal("text now")


func test_reset_new_game_clears_everything() -> void:
	GameState.day = 7
	GameState.set_flag("anything", true)
	GameState.reset_new_game()
	assert_int(GameState.day).is_equal(1)
	assert_bool(GameState.has_flag("anything")).is_false()
