extends Node
## Autoload: runtime half of "missions as data" (M4 day-loop scaffolding).
## MissionLibrary parses story/missions/act1.json; SceneDirector records
## WHICH mission is active (start_mission, from the DSL `mission` command);
## this system gives the mission meaning: which room exits work, the
## diegetic refusal line on blocked ones, and running on_complete_script
## once the completion flag flips.
##
## Appended after the original autoload order — CLAUDE.md calls that order
## load-bearing, and appending preserves every existing relative position.
## Other autoloads are referenced only inside handlers, never via
## _ready-time tree lookups.

const MISSIONS_PATH := "res://story/missions/act1.json"

var _missions: Dictionary = {}
var _loaded := false
var _refusing := false
var _pending_scenes: Array[String] = []
var _draining := false


func _ready() -> void:
	GameState.flag_changed.connect(_on_flag_changed)
	SceneDirector.mission_changed.connect(_on_mission_changed)


func missions() -> Dictionary:
	if not _loaded:
		_missions = _load_missions()
		_loaded = true
	return _missions


func current_mission_config() -> Dictionary:
	return MissionLibrary.get_mission(missions(), SceneDirector.current_mission_id)


## Room exit Area2Ds report here (wired by room.gd). Only MISSION mode
## reacts: cutscenes drive movement themselves, and FREE_ROAM has no gate
## data — exits are mission verbs, not doors.
func on_exit_touched(exit_id: String) -> void:
	if SceneDirector.mode != SceneDirector.ControlMode.MISSION:
		return
	var mission := current_mission_config()
	if mission.is_empty():
		return
	var decision := MissionLibrary.decide_exit(mission, exit_id)
	if decision["action"] == "complete":
		# Completion itself runs via _on_flag_changed, so a scene that sets
		# the flag directly (setflag) takes exactly the same path.
		GameState.set_flag(decision["flag"], true)
	else:
		_refuse(String(mission.get("id", "")), exit_id)


func _refuse(mission_id: String, exit_id: String) -> void:
	if _refusing or DialogueRunner.is_running():
		return
	_refusing = true
	var previous_mode: int = SceneDirector.mode
	SceneDirector.mode = SceneDirector.ControlMode.CUTSCENE
	await DialogueRunner.show_barrier_line(refusal_text(mission_id, exit_id))
	SceneDirector.mode = previous_mode
	_refusing = false


## First refusal key that actually translates wins; "refusal.generic" is
## the guaranteed floor (a Locale-completeness test asserts it exists).
func refusal_text(mission_id: String, exit_id: String) -> String:
	for key in MissionLibrary.refusal_key_candidates(mission_id, exit_id):
		var line := Locale.t(key)
		if line != key:
			return line
	return "..."


func _on_flag_changed(flag_name: String, value: Variant) -> void:
	var mission := current_mission_config()
	if mission.is_empty():
		return
	if flag_name != String(mission.get("complete_on_flag", "")):
		return
	# Truthy `if value:` — never `== true`; setflag values may be any type
	# (the Variant `==` gotcha fixed twice already in this codebase).
	if value:
		_complete(mission)


func _complete(mission: Dictionary) -> void:
	SceneDirector.current_mission_id = ""
	# Freeze the player for the hand-off; the queued scene's own
	# `mode cutscene` takes over from here.
	SceneDirector.mode = SceneDirector.ControlMode.CUTSCENE
	_run_after_current_scene(String(mission["on_complete_script"]))


## Serialized scene queue: waits out any running scene, then runs each
## pending script in arrival order. Fired without await (signal context);
## the guard keeps a single drain loop alive.
func _run_after_current_scene(scene_name: String) -> void:
	_pending_scenes.append(scene_name)
	if _draining:
		return
	_draining = true
	while not _pending_scenes.is_empty():
		if DialogueRunner.is_running():
			await DialogueRunner.scene_finished
		var next: String = _pending_scenes.pop_front()
		await DialogueRunner.run_scene(MissionLibrary.scene_script_path(next))
	_draining = false


func _on_mission_changed(mission_id: String) -> void:
	if mission_id == "":
		return
	if MissionLibrary.get_mission(missions(), mission_id).is_empty():
		push_warning("MissionSystem: unknown mission '%s' (not in %s)" % [mission_id, MISSIONS_PATH])
		return
	# A cutscene can leave the player already standing on an allowed exit — the
	# Day-7 send-off walks Deniz onto the dolmuş stop before arming the launch.
	# body_entered only fires on entry, so without this the mission never
	# completes: a soft-lock at the emotional peak. Deferred so start_mission
	# has finished setting mode and the physics overlap state is live, and
	# because completion cascades into goto_room (frees collision objects),
	# which is illegal inside a physics callback.
	_complete_if_standing_on_allowed_exit.call_deferred(mission_id)


## If the freshly-armed mission's player already overlaps one of its allowed
## exit Area2Ds, trip it exactly as a body_entered would (see room.gd). No-op
## when the player is not on an exit — only a real overlap completes.
func _complete_if_standing_on_allowed_exit(mission_id: String) -> void:
	if SceneDirector.current_mission_id != mission_id \
			or SceneDirector.mode != SceneDirector.ControlMode.MISSION:
		return
	var room: Node = SceneDirector.current_room
	var hoca: Node = SceneDirector.get_actor("hoca")
	if room == null or hoca == null:
		return
	var triggers := room.get_node_or_null("Triggers")
	if triggers == null:
		return
	var mission := current_mission_config()
	if mission.is_empty():
		return
	for exit_id: String in mission["allowed_exits"]:
		var trigger := triggers.get_node_or_null(exit_id)
		if trigger is Area2D and (trigger as Area2D).overlaps_body(hoca):
			on_exit_touched(exit_id)
			return


func _load_missions() -> Dictionary:
	if not FileAccess.file_exists(MISSIONS_PATH):
		push_warning("MissionSystem: missions file not found at %s" % MISSIONS_PATH)
		return {}
	var parsed := MissionLibrary.parse(FileAccess.get_file_as_string(MISSIONS_PATH))
	if not parsed["ok"]:
		push_warning("MissionSystem: missions parse error: %s" % parsed["error"])
		return {}
	return parsed["missions"]
