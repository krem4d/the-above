class_name MissionLibrary
extends RefCounted
## Pure JSON -> mission-config transform for game/story/missions/act1.json
## (M4 "missions as data"). Same shape and testing story as
## WaterfallSessionLibrary: static, engine-free, never raises — malformed
## input returns {ok:false, error:...}.
##
## A mission config: {id, objective_key, allowed_exits: Array[String],
## complete_on_flag, on_complete_script}. MissionSystem (autoload) owns the
## runtime behaviour; this class only parses and answers pure questions.


static func parse(json_text: String) -> Dictionary:
	var result := {"ok": false, "error": "", "missions": {}}
	var parsed: Variant = JSON.parse_string(json_text)
	if parsed == null:
		result["error"] = "not valid JSON"
		return result
	if parsed is not Dictionary:
		result["error"] = "root must be a JSON object"
		return result
	var root: Dictionary = parsed
	if root.get("missions") is not Array:
		result["error"] = "missing 'missions' array"
		return result
	var missions := {}
	for entry: Variant in root["missions"]:
		if entry is not Dictionary:
			result["error"] = "every mission must be an object"
			return result
		var mission: Dictionary = entry
		var id := String(mission.get("id", ""))
		if id == "":
			result["error"] = "mission with empty/missing id"
			return result
		if missions.has(id):
			result["error"] = "duplicate mission id '%s'" % id
			return result
		for field in ["objective_key", "complete_on_flag", "on_complete_script"]:
			if String(mission.get(field, "")) == "":
				result["error"] = "mission '%s' missing '%s'" % [id, field]
				return result
		if mission.get("allowed_exits") is not Array or (mission["allowed_exits"] as Array).is_empty():
			result["error"] = "mission '%s' needs a non-empty 'allowed_exits' array" % id
			return result
		missions[id] = mission
	result["ok"] = true
	result["missions"] = missions
	return result


static func get_mission(missions: Dictionary, id: String) -> Dictionary:
	return missions.get(id, {})


const SCENE_SCRIPT_DIR := "res://story/scripts/act1/"


## Bare script name (as used by on_complete_script and the wake scripts)
## -> res:// path. One shared resolver so MissionSystem and DayLoop can
## never drift apart on the convention.
static func scene_script_path(scene_name: String) -> String:
	return SCENE_SCRIPT_DIR + scene_name + ".scene"


## What touching `exit_id` under `mission` means. Pure decision, unit-tested
## without a scene tree: {"action": "complete", "flag": <complete_on_flag>}
## or {"action": "refuse"}. The runtime maps "refuse" to a diegetic line.
static func decide_exit(mission: Dictionary, exit_id: String) -> Dictionary:
	var allowed: Array = mission.get("allowed_exits", [])
	if allowed.has(exit_id):
		return {"action": "complete", "flag": String(mission.get("complete_on_flag", ""))}
	return {"action": "refuse"}


## Locale keys to try for a blocked exit, most specific first. The runtime
## uses the first key that actually translates; authoring a per-mission
## line is optional, the generic one is the guaranteed floor.
static func refusal_key_candidates(mission_id: String, exit_id: String) -> Array[String]:
	return [
		"refusal.%s.%s" % [mission_id, exit_id],
		"refusal.%s" % exit_id,
		"refusal.generic",
	]
