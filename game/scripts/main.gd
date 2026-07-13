extends Node2D
## Root scene. Never replaced; SceneDirector swaps Room instances under WorldHolder.

const PINNED_VERSION_MINOR := 5  # ADR 0001: Godot 4.5.x only
const ROOM_REGISTRY_PATH := "res://story/rooms/registry.json"


func _ready() -> void:
	_check_engine_version()
	SceneDirector.world_holder = $WorldHolder
	DialogueRunner.setup_ui(
		$UILayer/DialogueBox, $UILayer/ChoiceMenu, $UILayer/FadeRect, $UILayer/WaterfallView,
		$UILayer/NameEntryPanel
	)
	_register_rooms()
	# Boot the day loop only for a real play session: the screenshot tour
	# (user args after "--") mounts its own scenes under this main scene,
	# and a Day-1 cutscene fighting the tour for the UI would corrupt both.
	if OS.get_cmdline_user_args().is_empty():
		DayLoop.begin.call_deferred()


func _register_rooms() -> void:
	if not FileAccess.file_exists(ROOM_REGISTRY_PATH):
		push_warning("Main: room registry missing at %s" % ROOM_REGISTRY_PATH)
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ROOM_REGISTRY_PATH))
	if parsed is not Dictionary:
		push_error("Main: %s must be a JSON object of room_id -> scene path" % ROOM_REGISTRY_PATH)
		return
	for room_id: String in (parsed as Dictionary).keys():
		if room_id == "notes":
			continue
		SceneDirector.register_room_path(room_id, String(parsed[room_id]))


func _check_engine_version() -> void:
	var v: Dictionary = Engine.get_version_info()
	if v.major != 4 or v.minor != PINNED_VERSION_MINOR:
		push_warning(
			"Engine is %s — project is pinned to 4.%d.x (see docs/decisions/0001-godot-version.md)"
			% [v.string, PINNED_VERSION_MINOR]
		)
