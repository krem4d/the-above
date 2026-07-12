class_name WaterfallSessionLibrary
extends RefCounted
## Parses the spectro session manifest (res://story/signals/spectro_sessions.json)
## into a plain session_id -> config Dictionary. Pure text -> data transform,
## no FileAccess here — mirrors DialogueParser's split from DialogueRunner's
## own file I/O (see dialogue_runner.gd's load_and_parse()).
##
## parse() never raises; on malformed input it returns {ok:false, error:...}
## the same shape as DialogueParser.parse().

static func parse(json_text: String) -> Dictionary:
	var result := {"ok": true, "error": "", "sessions": {}}
	var parsed: Variant = JSON.parse_string(json_text)
	if typeof(parsed) != TYPE_DICTIONARY:
		result["ok"] = false
		result["error"] = "root is not a JSON object"
		return result
	var sessions_raw: Variant = (parsed as Dictionary).get("sessions", null)
	if typeof(sessions_raw) != TYPE_DICTIONARY:
		result["ok"] = false
		result["error"] = "'sessions' key missing or not an object"
		return result
	result["sessions"] = sessions_raw
	return result


## Returns {} (never null, never crashes) for an unknown id — dev-content
## gap, not a player-facing fail state, matching SceneDirector.resolve_position.
static func get_session_config(sessions: Dictionary, session_id: String) -> Dictionary:
	var config: Variant = sessions.get(session_id, null)
	if typeof(config) != TYPE_DICTIONARY:
		return {}
	return config
