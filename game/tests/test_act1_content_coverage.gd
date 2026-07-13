extends GdUnitTestSuite
## Content-coverage guard for the M4 exit gate: every name the Day-1 .scene
## files address (rooms, markers, props, actors, exits, locale keys) must
## exist in the room layouts / manifests it will resolve against at
## runtime — the DialogueRunner deliberately no-ops with a warning on a
## missing target, so without this suite a broken beat ships silently
## (same regression class the spectro session-coverage test guards).

const REGISTRY_PATH := "res://story/rooms/registry.json"
const ROOMS_DIR := "res://story/rooms/"
const MISSIONS_PATH := "res://story/missions/act1.json"
const DAY1_SCENES := [
	"res://story/scripts/act1/d1_wake.scene",
	"res://story/scripts/act1/d1_town.scene",
	"res://story/scripts/act1/d1_observatory.scene",
]
## Bodiless voices: no actor node, the runner falls back to speaker.<id>.
const VOICE_SPEAKERS := ["radio", "sys"]

var _registry: Dictionary = {}
var _layouts: Dictionary = {}   ## room_id -> layout Dictionary


func before() -> void:
	_registry = _load_json(REGISTRY_PATH)
	for room_id: String in _registry.keys():
		if room_id == "notes":
			continue
		_layouts[room_id] = _load_json(ROOMS_DIR + room_id + ".json")


func after_test() -> void:
	Locale.set_language("en")


func _load_json(path: String) -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


## Everything resolve_position()/find_in_room() can find in a room.
func _room_names(room_id: String) -> Dictionary:
	var names := {}
	var layout: Dictionary = _layouts.get(room_id, {})
	for marker: String in (layout.get("markers", {}) as Dictionary).keys():
		names[marker] = true
	for prop: Dictionary in layout.get("props", []):
		names[String(prop.get("name", ""))] = true
	for npc: Dictionary in layout.get("npcs", []):
		names[String(npc.get("actor_id", ""))] = true
	for exit_cfg: Dictionary in layout.get("exits", []):
		names[String(exit_cfg.get("id", ""))] = true
	if bool(layout.get("night_tint", false)):
		names["night_tint"] = true
	names["hoca"] = true   # the player instance lives in every room
	return names


func _room_actors(room_id: String) -> Dictionary:
	var actors := {"hoca": true}
	for npc: Dictionary in (_layouts.get(room_id, {}) as Dictionary).get("npcs", []):
		actors[String(npc.get("actor_id", ""))] = true
	return actors


func test_registry_rooms_have_layouts_and_generated_scenes() -> void:
	assert_bool(_layouts.size() >= 4).is_true()
	for room_id: String in _layouts.keys():
		assert_bool(not (_layouts[room_id] as Dictionary).is_empty()).override_failure_message(
			"room '%s' layout JSON missing/invalid" % room_id
		).is_true()
		var scene_path := String(_registry[room_id])
		assert_bool(FileAccess.file_exists(scene_path)).override_failure_message(
			"room '%s' scene not generated at %s (run `make resources`)" % [room_id, scene_path]
		).is_true()


func test_day1_scenes_only_address_things_that_exist() -> void:
	for scene_path: String in DAY1_SCENES:
		var parsed := DialogueParser.parse(FileAccess.get_file_as_string(scene_path))
		assert_bool(parsed["ok"]).override_failure_message(
			"%s failed to parse: %s" % [scene_path, parsed["error"]]
		).is_true()
		var room := ""
		for instr: Dictionary in parsed["instructions"]:
			var cmd: String = instr["cmd"]
			if cmd == "goto_room":
				room = String(instr["arg"])
				assert_bool(_layouts.has(room)).override_failure_message(
					"%s: goto_room '%s' not in registry" % [scene_path, room]
				).is_true()
			elif cmd in ["move", "face", "teleport"]:
				_assert_actor(scene_path, room, String(instr["actor_id"]))
				_assert_target(scene_path, room, String(instr["target"]))
			elif cmd == "pan":
				_assert_target(scene_path, room, String(instr["target"]))
			elif cmd == "show" or cmd == "hide":
				_assert_target(scene_path, room, String(instr["arg"]))
			elif cmd == "say":
				var actor_id := String(instr["actor_id"])
				if not VOICE_SPEAKERS.has(actor_id):
					_assert_actor(scene_path, room, actor_id)


func _assert_target(scene_path: String, room: String, target: String) -> void:
	# Actors resolve first (any room), then named nodes in the current room.
	var names := _room_names(room) if room != "" else {}
	assert_bool(names.has(target)).override_failure_message(
		"%s: target '%s' does not exist in room '%s'" % [scene_path, target, room]
	).is_true()


func _assert_actor(scene_path: String, room: String, actor_id: String) -> void:
	assert_bool(_room_actors(room).has(actor_id)).override_failure_message(
		"%s: actor '%s' is not placed in room '%s'" % [scene_path, actor_id, room]
	).is_true()


func test_voice_speakers_have_localized_names_in_both_languages() -> void:
	for lang in ["en", "tr"]:
		Locale.set_language(lang)
		for voice: String in VOICE_SPEAKERS:
			var key := "speaker." + voice
			assert_bool(Locale.t(key) != key).override_failure_message(
				"missing %s translation for %s" % [lang, key]
			).is_true()


func test_day1_dialogue_keys_translate_in_both_languages() -> void:
	for lang in ["en", "tr"]:
		Locale.set_language(lang)
		for scene_path: String in DAY1_SCENES:
			var parsed := DialogueParser.parse(FileAccess.get_file_as_string(scene_path))
			for instr: Dictionary in parsed["instructions"]:
				if instr["cmd"] == "say":
					_assert_translates(String(instr["key"]), lang, scene_path)
				elif instr["cmd"] == "choice":
					for opt: Dictionary in instr["options"]:
						_assert_translates(String(opt["text_key"]), lang, scene_path)


func _assert_translates(key: String, lang: String, scene_path: String) -> void:
	assert_bool(Locale.t(key) != key).override_failure_message(
		"%s: key '%s' has no %s translation" % [scene_path, key, lang]
	).is_true()


func test_every_mission_exit_exists_in_some_room() -> void:
	var all_exits := {}
	for room_id: String in _layouts.keys():
		for exit_cfg: Dictionary in (_layouts[room_id] as Dictionary).get("exits", []):
			all_exits[String(exit_cfg.get("id", ""))] = true
	var missions: Dictionary = MissionLibrary.parse(
		FileAccess.get_file_as_string(MISSIONS_PATH)
	)["missions"]
	for id: String in missions.keys():
		for exit_id: String in missions[id]["allowed_exits"]:
			assert_bool(all_exits.has(exit_id)).override_failure_message(
				"mission '%s' allows exit '%s' which no room defines" % [id, exit_id]
			).is_true()


func test_name_entry_is_authored_exactly_once_in_day1() -> void:
	# The naming ritual is canon (bible D1-S3) and meta-persistent — twice
	# would re-prompt, zero would leave the observer nameless for canon
	# lock IX's later appearances.
	var count := 0
	for scene_path: String in DAY1_SCENES:
		var parsed := DialogueParser.parse(FileAccess.get_file_as_string(scene_path))
		for instr: Dictionary in parsed["instructions"]:
			if instr["cmd"] == "name_entry":
				count += 1
	assert_int(count).is_equal(1)
