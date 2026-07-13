extends Node
## day7_probe — drives the ENTIRE Act 1 day chain end-to-end through the real
## game boot, the same way day1_probe drives Day 1, but runs all seven days to
## the launch instead of stopping at the Day-2 rollover:
##
##   DayLoop.begin -> d1_wake -> m_d1_morning -> d1_town -> d1_observatory
##   -> (rollover) d2_wake -> … -> d7_wake -> d7_observatory -> d7_sendoff
##   -> d7_launch -> setflag act1_complete
##
## It auto-answers every prompt: dialogue advance, first choice option, the
## Day-1 naming ritual, exit touches, and — unlike day1_probe — it CLOSES every
## spectro session immediately rather than winning it. No session is a fail
## state and cancel always closes (design law), so closing proves the DSL /
## mission chain without per-kind minigame logic (the minigames are covered by
## the M3 suites).
##
## This is the M5.1 exit-gate evidence: with the Days 2–7 wiring in place the
## whole arc is logically playable with no soft-lock. Missing M5 staging
## content (the obs_breakroom whiteboard room, unplaced NPCs, absent markers)
## degrades to no-op warnings, NOT stalls — SceneDirector.goto_room to an
## unknown room returns early and leaves the player in the previous valid room,
## so every mission exit still resolves.
##
## Launched (autoloads can't exist under a bare --script main loop):
##   godot --path game -- --day7-probe
##
## Exit code 0 = act1_complete reached; 1 = timeout/stall.

const MAX_FRAMES := 120000
const TIME_SCALE := 8.0
const PROBE_NAME := "Deniz"

var _frames := 0
var _beats: Array[String] = []
var _last_day := 0


func _ready() -> void:
	Engine.time_scale = TIME_SCALE
	SceneDirector.room_changed.connect(_on_room_changed)
	DayLoop.begin.call_deferred()
	_drive.call_deferred()


func _on_room_changed(room_id: String) -> void:
	_note("d%d:room:%s" % [GameState.day, room_id])


func _note(beat: String) -> void:
	if _beats.has(beat):
		return
	_beats.append(beat)
	print("day7_probe BEAT %s (frame %d)" % [beat, _frames])


func _drive() -> void:
	while _frames < MAX_FRAMES:
		await get_tree().process_frame
		_frames += 1
		if GameState.day != _last_day:
			_last_day = GameState.day
			_note("DAY %d" % GameState.day)
		_pump_dialogue()
		_pump_choice()
		_pump_name_entry()
		_pump_waterfall()
		_pump_mission_exit()
		if _frames % 2000 == 0:
			_dump_stall_state()
		if GameState.get_flag("act1_complete"):
			_note("act1_complete")
			await _finish(true)
			return
	await _finish(false)


## One-line state dump so a stalled run says WHAT it is waiting on.
func _dump_stall_state() -> void:
	var view := DialogueRunner.waterfall_view
	var wf := "off"
	if view != null and view.visible and view._session != null:
		wf = "id=%s" % view._session.session_id
	print("day7_probe STATE f=%d day=%d mode=%d scene_running=%s dlg=%s waterfall[%s] instr=%s" % [
		_frames, GameState.day, SceneDirector.mode, DialogueRunner.is_running(),
		DialogueRunner.dialogue_box != null and DialogueRunner.dialogue_box.visible,
		wf, JSON.stringify(DialogueRunner.debug_current_instr),
	])


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
	_note("d%d:choice" % GameState.day)
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
	_note("d%d:waterfall:%s" % [GameState.day, view._session.session_id])
	# Close immediately — cancel always closes; the scene continues regardless
	# of the (non-fail-state) result.
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
		_note("d%d:exit:%s" % [GameState.day, exit_id])
		(hoca as Node2D).global_position = (trigger as Node2D).global_position


func _finish(success: bool) -> void:
	Engine.time_scale = 1.0
	print("day7_probe beats: %s" % ", ".join(_beats))
	if success:
		print("day7_probe PASS — Act 1 played to act1_complete in %d frames" % _frames)
	else:
		print("day7_probe FAIL — timed out at frame %d (day %d)" % [_frames, GameState.day])
	# One drained frame so queued frees settle before teardown.
	await get_tree().process_frame
	get_tree().quit(0 if success else 1)
