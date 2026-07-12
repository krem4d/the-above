extends Node
## Autoload: await-based coroutine executing DialogueParser output against
## DialogueBox/ChoiceMenu/GameState/Locale/SceneDirector/AudioManager
## (plan section 5). No threads — every DSL command is one `await` step.
##
## setup_ui() must be called once by main.gd before run_scene()/run_parsed()
## — see the SceneDirector.world_holder comment for why this can't be an
## @onready absolute path (autoloads _ready() before the main scene exists).

var dialogue_box: DialogueBox = null
var choice_menu: ChoiceMenu = null
var fade_rect: ColorRect = null

var _running := false
var _mode_names: Dictionary = {}


func _ready() -> void:
	_mode_names = {
		"cutscene": SceneDirector.ControlMode.CUTSCENE,
		"free_roam": SceneDirector.ControlMode.FREE_ROAM,
		"mission": SceneDirector.ControlMode.MISSION,
		"minigame": SceneDirector.ControlMode.MINIGAME,
	}


func setup_ui(box: DialogueBox, menu: ChoiceMenu, fade: ColorRect) -> void:
	dialogue_box = box
	choice_menu = menu
	fade_rect = fade
	dialogue_box.hide_box()


func is_running() -> bool:
	return _running


func run_scene(scene_path: String) -> void:
	var parsed := load_and_parse(scene_path)
	if not parsed["ok"]:
		push_error("DialogueRunner: %s (%s)" % [parsed["error"], scene_path])
		return
	await run_parsed(parsed)


func load_and_parse(scene_path: String) -> Dictionary:
	if not FileAccess.file_exists(scene_path):
		return {"ok": false, "error": "file not found: %s" % scene_path}
	var text := FileAccess.get_file_as_string(scene_path)
	return DialogueParser.parse(text)


func run_parsed(parsed: Dictionary) -> void:
	_running = true
	var instructions: Array = parsed["instructions"]
	var labels: Dictionary = parsed["labels"]
	var ip := 0
	while ip < instructions.size():
		ip = await _step(ip, instructions, labels)
	if dialogue_box:
		dialogue_box.hide_box()
	_running = false


func _step(ip: int, instructions: Array, labels: Dictionary) -> int:
	var instr: Dictionary = instructions[ip]
	var cmd: String = instr["cmd"]

	if cmd == "say":
		await _do_say(instr)
	elif cmd == "choice":
		return await _do_choice(instr, labels)
	elif cmd == "jump":
		return labels[instr["arg"]]
	elif cmd == "label":
		pass
	elif cmd == "if":
		# Plain truthy check, not `== true`: GDScript's `==` throws a runtime
		# type error comparing bool against int/float/String, and setflag
		# allows all of those (dialogue_parser.gd's _coerce_value). `if x:`
		# uses Variant booleanize() instead, which is safe for any type.
		if GameState.get_flag(instr["flag"]):
			pass
		elif instr["else_index"] != -1:
			return instr["else_index"] + 1
		else:
			return instr["end_index"] + 1
	elif cmd == "else":
		return instr["end_index"] + 1
	elif cmd == "end":
		pass
	elif cmd == "setflag":
		GameState.set_flag(instr["name"], instr["value"])
	elif cmd == "move":
		await _do_move(instr)
	elif cmd == "face":
		_do_face(instr)
	elif cmd == "teleport":
		_do_teleport(instr)
	elif cmd == "show" or cmd == "hide":
		_do_showhide(instr)
	elif cmd == "pan":
		await _do_pan(instr)
	elif cmd == "zoom":
		await _do_zoom(instr)
	elif cmd == "shake":
		await _do_shake(instr)
	elif cmd == "wait":
		await get_tree().create_timer(instr["seconds"]).timeout
	elif cmd == "sfx":
		AudioManager.play_sfx(instr["arg"])
	elif cmd == "music":
		AudioManager.play_music(instr["name"], instr["fade"])
	elif cmd == "fade":
		await _do_fade(instr)
	elif cmd == "spectro":
		push_warning("DialogueRunner: spectro '%s' is M3 scope, skipping" % instr["arg"])
	elif cmd == "mode":
		_do_mode(instr)
	elif cmd == "mission":
		SceneDirector.start_mission(instr["arg"])
	elif cmd == "goto_room":
		SceneDirector.goto_room(instr["arg"])
	elif cmd == "title_variant":
		push_warning("DialogueRunner: title_variant '%s' is M5 scope, skipping" % instr["arg"])
	elif cmd == "end_scene":
		return instructions.size()
	return ip + 1


func _do_say(instr: Dictionary) -> void:
	var actor: Node = SceneDirector.get_actor(instr["actor_id"])
	# Fallback is the raw actor_id, never a case-transform of it (Turkish
	# İ/ı casing safety, plan section 5) — real content sets display_name.
	var speaker_name: String = instr["actor_id"]
	var portrait: Texture2D = null
	if actor != null:
		if "display_name" in actor and actor.display_name != "":
			speaker_name = actor.display_name
		if "portrait" in actor and actor.portrait != null:
			portrait = actor.portrait
	dialogue_box.show_line(Locale.t(instr["key"]), speaker_name, portrait)
	await dialogue_box.advance_requested


func _do_choice(instr: Dictionary, labels: Dictionary) -> int:
	var options: Array[String] = []
	for opt: Dictionary in instr["options"]:
		options.append(Locale.t(opt["text_key"]))
	choice_menu.present(options)
	var index: int = await choice_menu.chosen
	return labels[instr["options"][index]["target_label"]]


func _do_move(instr: Dictionary) -> void:
	var actor: Node = SceneDirector.get_actor(instr["actor_id"])
	if actor == null:
		push_warning("DialogueRunner: move — unknown actor '%s'" % instr["actor_id"])
		return
	var target: Variant = SceneDirector.resolve_position(instr["target"])
	if target == null:
		return
	await actor.walk_to(target)


func _do_face(instr: Dictionary) -> void:
	var actor: Node = SceneDirector.get_actor(instr["actor_id"])
	if actor == null:
		return
	var target: Variant = SceneDirector.resolve_position(instr["target"])
	if target == null:
		return
	actor.face_toward(target - actor.global_position)


func _do_teleport(instr: Dictionary) -> void:
	var actor: Node = SceneDirector.get_actor(instr["actor_id"])
	if actor == null:
		return
	var target: Variant = SceneDirector.resolve_position(instr["target"])
	if target == null:
		return
	actor.global_position = target
	if actor.has_method("play_idle"):
		actor.play_idle()


func _do_showhide(instr: Dictionary) -> void:
	var node: Node = SceneDirector.find_in_room(instr["arg"])
	if node == null:
		push_warning("DialogueRunner: %s — node '%s' not found" % [instr["cmd"], instr["arg"]])
		return
	if node is CanvasItem:
		(node as CanvasItem).visible = (instr["cmd"] == "show")


func _do_pan(instr: Dictionary) -> void:
	var camera := SceneDirector.get_camera()
	if camera == null:
		return
	var target: Variant = SceneDirector.resolve_position(instr["target"])
	if target == null:
		return
	var tween := create_tween()
	tween.tween_property(camera, "global_position", target, instr["seconds"])
	await tween.finished


func _do_zoom(instr: Dictionary) -> void:
	var camera := SceneDirector.get_camera()
	if camera == null:
		return
	var tween := create_tween()
	tween.tween_property(camera, "zoom", Vector2(instr["level"], instr["level"]), instr["seconds"])
	await tween.finished


func _do_shake(instr: Dictionary) -> void:
	var camera := SceneDirector.get_camera()
	if camera == null:
		await get_tree().create_timer(instr["seconds"]).timeout
		return
	const STEP := 0.05
	var duration: float = instr["seconds"]
	var tween := create_tween()
	var elapsed := 0.0
	while elapsed < duration:
		tween.tween_property(camera, "offset", Vector2(randf_range(-4, 4), randf_range(-4, 4)), STEP)
		elapsed += STEP
	tween.tween_property(camera, "offset", Vector2.ZERO, STEP)
	await tween.finished


func _do_fade(instr: Dictionary) -> void:
	if fade_rect == null:
		await get_tree().create_timer(instr["seconds"]).timeout
		return
	var target_alpha: float = 1.0 if instr["direction"] == "out" else 0.0
	var tween := create_tween()
	tween.tween_property(fade_rect, "color:a", target_alpha, instr["seconds"])
	await tween.finished


func _do_mode(instr: Dictionary) -> void:
	var mode_name: String = instr["arg"]
	if _mode_names.has(mode_name):
		SceneDirector.mode = _mode_names[mode_name]
	else:
		push_warning("DialogueRunner: unknown mode '%s'" % mode_name)
