extends SceneTree
## day1_probe — drives the ENTIRE Day 1 chain end-to-end through the real
## game boot (main.tscn -> DayLoop.begin -> d1_wake -> missions -> d1_town
## -> d1_observatory -> rollover to Day 2), auto-answering every player
## prompt: dialogue advance, first choice option, the naming ritual, exit
## touches, and an honest waterfall win (tunes to target, holds the lock).
##
##   godot --path game --headless --script res://tools/day1_probe.gd
##
## Under a real display (xvfb works) it also captures a PNG per story beat
## into artifacts/shots/day1/ — the M4 exit-gate "tour captures every
## beat" evidence. Headless it still verifies the full logic chain.
##
## Exit code 0 = Day 2 reached with d1_complete set; 1 = timeout/failure.

const MAX_FRAMES := 60000
const TIME_SCALE := 4.0
const OUT_DIR := "res://../artifacts/shots/day1"
const PROBE_NAME := "Deniz"

var _frames := 0
var _beats: Array[String] = []
var _shot_index := 0
var _captured: Dictionary = {}
var _can_capture := false


func _initialize() -> void:
	Engine.time_scale = TIME_SCALE
	_can_capture = DisplayServer.get_name() != "headless"
	if _can_capture:
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_DIR))
	var main_scene: PackedScene = load("res://scenes/main/main.tscn")
	var instance: Node = main_scene.instantiate()
	root.add_child(instance)
	current_scene = instance
	SceneDirector.room_changed.connect(_on_room_changed)
	_drive.call_deferred()


func _on_room_changed(room_id: String) -> void:
	_note("room:" + room_id)


func _note(beat: String) -> void:
	if _beats.has(beat):
		return
	_beats.append(beat)
	print("day1_probe BEAT %s (frame %d)" % [beat, _frames])


func _drive() -> void:
	while _frames < MAX_FRAMES:
		await process_frame
		_frames += 1
		_pump_dialogue()
		_pump_choice()
		_pump_name_entry()
		_pump_waterfall()
		_pump_mission_exit()
		await _pump_beat_shots()
		if GameState.day >= 2 and GameState.get_flag("d1_complete"):
			_note("day2_reached")
			await _finish(true)
			return
	await _finish(false)


func _pump_dialogue() -> void:
	var box := DialogueRunner.dialogue_box
	if box == null or not box.visible:
		return
	if box.is_typing():
		box.skip_to_end()
	else:
		box.advance_requested.emit()


func _pump_choice() -> void:
	var menu := DialogueRunner.choice_menu
	if menu == null or not menu.visible:
		return
	_note("choice")
	menu.visible = false
	menu.chosen.emit(0)


func _pump_name_entry() -> void:
	var panel := DialogueRunner.name_entry_panel
	if panel == null or not panel.visible:
		return
	_note("name_entry")
	panel._line.text = PROBE_NAME
	panel._try_confirm()


func _pump_waterfall() -> void:
	var view := DialogueRunner.waterfall_view
	if view == null or not view.visible or view._session == null:
		return
	_note("waterfall")
	# Play it straight: stay tuned on the drifting target until the hold
	# completes, then close — the same inputs a player's fingers would make.
	view._session.set_frequency(view._session.target_freq_mhz)
	if view._session.is_objective_met():
		view.close_session()


func _pump_mission_exit() -> void:
	if SceneDirector.mode != SceneDirector.ControlMode.MISSION:
		return
	if DialogueRunner.is_running():
		return
	var mission := MissionSystem.current_mission_config()
	if mission.is_empty() or SceneDirector.current_room == null:
		return
	var exit_id := String((mission["allowed_exits"] as Array)[0])
	var trigger := SceneDirector.current_room.get_node_or_null("Triggers/" + exit_id)
	var hoca: Node = SceneDirector.get_actor("hoca")
	if trigger is Area2D and hoca is Node2D:
		_note("exit:" + exit_id)
		(hoca as Node2D).global_position = (trigger as Node2D).global_position


func _pump_beat_shots() -> void:
	if not _can_capture:
		return
	await _capture_once("home", SceneDirector.current_room != null \
		and SceneDirector.current_room.get("room_id") == "home")
	await _capture_once("town", _room_is("town"))
	await _capture_once("dolmus", _room_is("dolmus"))
	await _capture_once("obs", _room_is("obs"))
	await _capture_once("name_entry", DialogueRunner.name_entry_panel != null \
		and DialogueRunner.name_entry_panel.visible)
	await _capture_once("waterfall", DialogueRunner.waterfall_view != null \
		and DialogueRunner.waterfall_view.visible)
	await _capture_once("printout", _node_visible("printout_overlay"))
	await _capture_once("town_night", _node_visible("night_tint") and _room_is("town"))


func _room_is(room_id: String) -> bool:
	var room := SceneDirector.current_room
	return room != null and String(room.get("room_id")) == room_id


func _node_visible(node_name: String) -> bool:
	var node := SceneDirector.find_in_room(node_name)
	return node is CanvasItem and (node as CanvasItem).visible


func _capture_once(beat: String, condition: bool) -> void:
	if not condition or _captured.has(beat):
		return
	_captured[beat] = true
	# Let the moment settle so the shot shows the beat, not its first frame.
	for _i in 12:
		await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_viewport().get_texture().get_image()
	var path := ProjectSettings.globalize_path(
		"%s/%02d_%s.png" % [OUT_DIR, _shot_index, beat]
	)
	_shot_index += 1
	if image.save_png(path) == OK:
		print("day1_probe SHOT %s" % path)


func _finish(success: bool) -> void:
	Engine.time_scale = 1.0
	print("day1_probe beats: %s" % ", ".join(_beats))
	if success:
		print("day1_probe PASS — Day 1 end-to-end in %d frames" % _frames)
	else:
		print("day1_probe FAIL — timed out at frame %d" % _frames)
	# One drained frame so queued frees settle before teardown.
	await process_frame
	quit(0 if success else 1)
