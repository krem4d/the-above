class_name DialogueParser
extends RefCounted
## Parses .scene DSL text into a flat, label-resolved instruction list
## (plan section 5, "hand-rolled plain-text DSL"). Pure data transform, no
## engine dependencies — fully unit-testable headless.
##
## parse() never raises; on malformed input it returns {ok:false, error:
## "line N: message"}. Command grammar is grounded in the 24 real Act 1
## .scene files, not just the plan's illustrative example.

const COMMANDS_ONE_ARG := [
	"jump", "show", "hide", "sfx", "spectro", "mode", "mission", "goto_room", "title_variant",
]
const COMMANDS_TWO_ARGS := ["move", "face", "teleport"]


static func parse(text: String) -> Dictionary:
	var result := {"ok": true, "error": "", "scene_id": "", "instructions": [], "labels": {}}
	var lines := text.split("\n")
	var scene_id := ""
	var instructions: Array = []
	var labels: Dictionary = {}
	var if_stack: Array = []
	var current_choice: Dictionary = {}

	for i in lines.size():
		var line_no := i + 1
		var stripped := _strip_comment_and_whitespace(lines[i])
		if stripped == "":
			continue

		var header := _match_scene_header(stripped)
		if header != "":
			if scene_id != "":
				return _fail(result, line_no, "duplicate [scene ...] header")
			scene_id = header
			continue
		if scene_id == "":
			return _fail(result, line_no, "expected [scene <id>] header before any command")

		var tokens: PackedStringArray = stripped.split(" ", false)
		var cmd: String = tokens[0]
		var rest: PackedStringArray = tokens.slice(1)

		if cmd == "option":
			if current_choice.is_empty():
				return _fail(result, line_no, "'option' outside a choice block")
			var opt := _parse_option(rest)
			if opt.is_empty():
				return _fail(result, line_no, "'option' expects <text_key> -> <label>")
			current_choice["options"].append(opt)
			continue

		# Any non-option line closes an in-progress choice block.
		if not current_choice.is_empty():
			instructions.append(current_choice)
			current_choice = {}

		if cmd == "choice":
			current_choice = {"cmd": "choice", "line": line_no, "options": []}
		elif cmd == "if":
			if rest.size() != 1:
				return _fail(result, line_no, "'if' expects exactly one flag name")
			if_stack.append(instructions.size())
			instructions.append(
				{"cmd": "if", "line": line_no, "flag": rest[0], "else_index": -1, "end_index": -1}
			)
		elif cmd == "else":
			if if_stack.is_empty():
				return _fail(result, line_no, "'else' without a matching 'if'")
			var if_idx: int = if_stack[if_stack.size() - 1]
			if instructions[if_idx]["else_index"] != -1:
				return _fail(result, line_no, "'if' has more than one 'else'")
			instructions[if_idx]["else_index"] = instructions.size()
			instructions.append({"cmd": "else", "line": line_no})
		elif cmd == "end":
			if if_stack.is_empty():
				return _fail(result, line_no, "'end' without a matching 'if'")
			var if_idx2: int = if_stack.pop_back()
			var end_idx := instructions.size()
			instructions[if_idx2]["end_index"] = end_idx
			var else_idx: int = instructions[if_idx2]["else_index"]
			if else_idx != -1:
				instructions[else_idx]["end_index"] = end_idx
			instructions.append({"cmd": "end", "line": line_no})
		elif cmd == "label":
			if rest.size() != 1:
				return _fail(result, line_no, "'label' expects exactly one name")
			if labels.has(rest[0]):
				return _fail(result, line_no, "duplicate label '%s'" % rest[0])
			labels[rest[0]] = instructions.size()
			instructions.append({"cmd": "label", "line": line_no, "name": rest[0]})
		elif cmd == "setflag":
			if rest.size() != 2:
				return _fail(result, line_no, "'setflag' expects <name> <value>")
			instructions.append(
				{"cmd": "setflag", "line": line_no, "name": rest[0], "value": _coerce_value(rest[1])}
			)
		elif cmd == "say":
			if rest.size() < 2:
				return _fail(result, line_no, "'say' expects <actor_id> <locale_key> [mood=...]")
			var say_kwargs := _parse_kwargs(rest.slice(2))
			instructions.append({
				"cmd": "say", "line": line_no, "actor_id": rest[0], "key": rest[1],
				"mood": say_kwargs.get("mood", ""),
			})
		elif cmd == "music":
			if rest.size() < 1:
				return _fail(result, line_no, "'music' expects <name> [fade=...]")
			var music_kwargs := _parse_kwargs(rest.slice(1))
			instructions.append({
				"cmd": "music", "line": line_no, "name": rest[0],
				"fade": float(music_kwargs.get("fade", "0.0")),
			})
		elif cmd == "fade":
			if rest.size() != 2 or (rest[0] != "in" and rest[0] != "out"):
				return _fail(result, line_no, "'fade' expects 'in'|'out' <seconds>")
			instructions.append(
				{"cmd": "fade", "line": line_no, "direction": rest[0], "seconds": float(rest[1])}
			)
		elif cmd == "pan":
			if rest.size() != 2:
				return _fail(result, line_no, "'pan' expects <target> <seconds>")
			instructions.append(
				{"cmd": "pan", "line": line_no, "target": rest[0], "seconds": float(rest[1])}
			)
		elif cmd == "zoom":
			if rest.size() != 2:
				return _fail(result, line_no, "'zoom' expects <level> <seconds>")
			instructions.append(
				{"cmd": "zoom", "line": line_no, "level": float(rest[0]), "seconds": float(rest[1])}
			)
		elif cmd == "shake":
			if rest.size() != 1:
				return _fail(result, line_no, "'shake' expects <seconds>")
			instructions.append({"cmd": "shake", "line": line_no, "seconds": float(rest[0])})
		elif cmd == "wait":
			if rest.size() != 1:
				return _fail(result, line_no, "'wait' expects <seconds>")
			instructions.append({"cmd": "wait", "line": line_no, "seconds": float(rest[0])})
		elif cmd == "end_scene":
			if not rest.is_empty():
				return _fail(result, line_no, "'end_scene' takes no arguments")
			instructions.append({"cmd": "end_scene", "line": line_no})
		elif COMMANDS_ONE_ARG.has(cmd):
			if rest.size() != 1:
				return _fail(result, line_no, "'%s' expects exactly one argument" % cmd)
			instructions.append({"cmd": cmd, "line": line_no, "arg": rest[0]})
		elif COMMANDS_TWO_ARGS.has(cmd):
			if rest.size() != 2:
				return _fail(result, line_no, "'%s' expects exactly two arguments" % cmd)
			instructions.append({"cmd": cmd, "line": line_no, "actor_id": rest[0], "target": rest[1]})
		else:
			return _fail(result, line_no, "unknown command '%s'" % cmd)

	if not current_choice.is_empty():
		instructions.append(current_choice)
	if not if_stack.is_empty():
		var open_line: int = instructions[if_stack[0]]["line"]
		return _fail(result, open_line, "'if' at line %d never closed with 'end'" % open_line)
	if scene_id == "":
		return _fail(result, lines.size(), "file contains no [scene <id>] header")

	for instr: Dictionary in instructions:
		if instr["cmd"] == "jump" and not labels.has(instr["arg"]):
			return _fail(result, instr["line"], "jump to undefined label '%s'" % instr["arg"])
		if instr["cmd"] == "choice":
			if instr["options"].is_empty():
				return _fail(result, instr["line"], "'choice' has no options")
			for opt: Dictionary in instr["options"]:
				if not labels.has(opt["target_label"]):
					return _fail(
						result, instr["line"], "option target undefined label '%s'" % opt["target_label"]
					)

	result["scene_id"] = scene_id
	result["instructions"] = instructions
	result["labels"] = labels
	return result


static func _fail(result: Dictionary, line_no: int, msg: String) -> Dictionary:
	result["ok"] = false
	result["error"] = "line %d: %s" % [line_no, msg]
	return result


static func _strip_comment_and_whitespace(raw: String) -> String:
	var hash_index := raw.find("#")
	var without_comment := raw if hash_index == -1 else raw.substr(0, hash_index)
	return without_comment.strip_edges()


static func _match_scene_header(line: String) -> String:
	if not (line.begins_with("[scene ") and line.ends_with("]")):
		return ""
	return line.substr(7, line.length() - 8).strip_edges()


static func _parse_option(rest: PackedStringArray) -> Dictionary:
	# Exactly 3 tokens with "->" in the middle — not just "arrow somewhere
	# near the end", which let a missing text_key (arrow in slot 0) or an
	# extra stray token before the arrow parse "successfully" and silently
	# discard/misassign data instead of failing.
	if rest.size() != 3 or rest[1] != "->":
		return {}
	return {"text_key": rest[0], "target_label": rest[2]}


static func _parse_kwargs(tokens: PackedStringArray) -> Dictionary:
	var kwargs := {}
	for token in tokens:
		var eq := token.find("=")
		if eq == -1:
			continue
		kwargs[token.substr(0, eq)] = token.substr(eq + 1)
	return kwargs


static func _coerce_value(raw: String) -> Variant:
	if raw == "true":
		return true
	if raw == "false":
		return false
	if raw.is_valid_int():
		return raw.to_int()
	if raw.is_valid_float():
		return raw.to_float()
	return raw
