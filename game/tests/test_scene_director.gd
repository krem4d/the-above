extends GdUnitTestSuite
## SceneDirector: ControlMode switching, actor registry, room swap.
## Injects a throwaway Node2D as world_holder (dependency injection, not the
## real Main.tscn) so this suite never depends on Main being in the tree.

var _fake_world_holder: Node2D
var _previous_world_holder: Node2D


func before_test() -> void:
	_previous_world_holder = SceneDirector.world_holder
	_fake_world_holder = auto_free(Node2D.new())
	add_child(_fake_world_holder)
	SceneDirector.world_holder = _fake_world_holder
	SceneDirector.register_room_path("graybox_test", "res://scenes/rooms/act1/graybox.tscn")


func after_test() -> void:
	SceneDirector.world_holder = _previous_world_holder
	SceneDirector.mode = SceneDirector.ControlMode.CUTSCENE
	SceneDirector.current_room = null


func test_mode_defaults_to_cutscene_and_changes() -> void:
	assert_int(SceneDirector.mode).is_equal(SceneDirector.ControlMode.CUTSCENE)
	SceneDirector.mode = SceneDirector.ControlMode.FREE_ROAM
	assert_int(SceneDirector.mode).is_equal(SceneDirector.ControlMode.FREE_ROAM)


func test_actor_registry_register_get_unregister() -> void:
	var fake_actor: Node2D = auto_free(Node2D.new())
	SceneDirector.register_actor("test_actor", fake_actor)
	assert_object(SceneDirector.get_actor("test_actor")).is_equal(fake_actor)
	SceneDirector.unregister_actor("test_actor")
	assert_object(SceneDirector.get_actor("test_actor")).is_null()


func test_resolve_position_returns_null_for_unknown_target() -> void:
	assert_object(SceneDirector.resolve_position("nothing_named_this")).is_null()


func test_resolve_position_finds_registered_actor() -> void:
	var fake_actor: Node2D = auto_free(Node2D.new())
	fake_actor.global_position = Vector2(42, 17)
	SceneDirector.register_actor("marker_actor", fake_actor)
	var pos: Variant = SceneDirector.resolve_position("marker_actor")
	assert_bool(pos == Vector2(42, 17)).is_true()
	SceneDirector.unregister_actor("marker_actor")


func test_goto_room_swaps_world_holder_child() -> void:
	SceneDirector.goto_room("graybox_test")
	assert_int(_fake_world_holder.get_child_count()).is_equal(1)
	assert_object(SceneDirector.current_room).is_not_null()


func test_goto_room_unknown_id_does_not_crash() -> void:
	SceneDirector.goto_room("not_a_real_room")
	assert_int(_fake_world_holder.get_child_count()).is_equal(0)


func test_mode_changed_signal_fires_only_on_real_change() -> void:
	var emit_count := [0]
	SceneDirector.mode_changed.connect(func(_m: int) -> void: emit_count[0] += 1)
	SceneDirector.mode = SceneDirector.ControlMode.MISSION
	SceneDirector.mode = SceneDirector.ControlMode.MISSION   # same value again — must not re-fire
	assert_int(emit_count[0]).is_equal(1)


func test_start_mission_sets_id_and_switches_to_mission_mode() -> void:
	SceneDirector.start_mission("m_d1_morning")
	assert_str(SceneDirector.current_mission_id).is_equal("m_d1_morning")
	assert_int(SceneDirector.mode).is_equal(SceneDirector.ControlMode.MISSION)
