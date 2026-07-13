extends Node
## Debug autoload — screenshot harness (plan section 5, "verification").
##
## Inert unless launched with user args after "--":
##   godot --path game -- --screenshot-tour --out=../artifacts/shots
##   godot --path game -- --screenshot-scene <id> --out=../artifacts/shots
## Tour entries live in res://tools/tour.json: [{id, scene, wait_frames}, ...]

const TOUR_PATH := "res://tools/tour.json"
const DEFAULT_OUT_DIR := "../artifacts/shots"
const CAPTURE_SIZE := Vector2i(1280, 720)


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		return
	if args.has("--day1-probe"):
		# In-game Day-1 end-to-end driver (see tools/day1_probe.gd) — runs
		# inside the booted game because autoloads don't exist under a bare
		# --script main loop.
		if DisplayServer.get_name() != "headless":
			get_window().size = CAPTURE_SIZE
		await get_tree().process_frame
		add_child((load("res://tools/day1_probe.gd") as GDScript).new())
		return
	var opts := _parse_args(args)
	if not (opts.tour or opts.scene_id != ""):
		return
	# Deterministic window size: 1280x720 = exactly 2x the 640x360 viewport.
	get_window().size = CAPTURE_SIZE
	# Defer until the main scene exists (autoloads _ready before it is added).
	await get_tree().process_frame
	await _run_tour(opts.scene_id, opts.out_dir)


func _parse_args(args: PackedStringArray) -> Dictionary:
	var opts := {"tour": false, "scene_id": "", "out_dir": DEFAULT_OUT_DIR}
	var i := 0
	while i < args.size():
		var arg := args[i]
		if arg == "--screenshot-tour":
			opts.tour = true
		elif arg == "--screenshot-scene" and i + 1 < args.size():
			i += 1
			opts.scene_id = args[i]
		elif arg.begins_with("--out="):
			opts.out_dir = arg.trim_prefix("--out=")
		i += 1
	return opts


func _run_tour(only_id: String, out_dir: String) -> void:
	var entries := _load_tour_entries()
	if only_id != "":
		entries = entries.filter(func(e: Dictionary) -> bool: return e.get("id", "") == only_id)
		if entries.is_empty():
			push_error("Debug: no tour entry with id %s in %s" % [only_id, TOUR_PATH])
			get_tree().quit(1)
			return
	if entries.is_empty():
		push_error("Debug: no tour entries loaded from %s" % TOUR_PATH)
		get_tree().quit(1)
		return
	var abs_out := _absolutize(out_dir)
	var mkdir_err := DirAccess.make_dir_recursive_absolute(abs_out)
	if mkdir_err != OK:
		push_error("Debug: cannot create output dir %s (error %d)" % [abs_out, mkdir_err])
		get_tree().quit(1)
		return
	var failures := 0
	for entry: Dictionary in entries:
		if not await _capture_entry(entry, abs_out):
			failures += 1
	get_tree().quit(1 if failures > 0 else 0)


func _load_tour_entries() -> Array:
	if not FileAccess.file_exists(TOUR_PATH):
		return []
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(TOUR_PATH))
	if parsed is not Array:
		push_error("Debug: %s must contain a JSON array" % TOUR_PATH)
		return []
	return parsed


func _capture_entry(entry: Dictionary, abs_out: String) -> bool:
	var id: String = entry.get("id", "")
	var scene_path: String = entry.get("scene", "")
	var wait_frames := int(entry.get("wait_frames", 10))
	var packed: PackedScene = load(scene_path) if ResourceLoader.exists(scene_path) else null
	if id == "" or packed == null:
		push_error("Debug: bad tour entry %s (scene: %s)" % [id, scene_path])
		return false
	var instance := packed.instantiate()
	var host: Node = get_tree().current_scene if get_tree().current_scene else get_tree().root
	host.add_child(instance)
	for _i in wait_frames:
		await RenderingServer.frame_post_draw
	if bool(entry.get("hide_dialogue", false)) and DialogueRunner.dialogue_box != null:
		# An earlier entry (e2e demo) may have left the shared DialogueBox
		# mid-line; room shots want the bare scene.
		DialogueRunner.dialogue_box.hide_box()
		await RenderingServer.frame_post_draw
	var ok := _save_viewport_png(abs_out.path_join(id + ".png"))
	instance.free()
	await get_tree().process_frame
	return ok


func _save_viewport_png(path: String) -> bool:
	var img := get_viewport().get_texture().get_image()
	if img.get_size() != CAPTURE_SIZE:
		# Viewport-stretch renders at 640x360; bake the crisp 2x upscale.
		img.resize(CAPTURE_SIZE.x, CAPTURE_SIZE.y, Image.INTERPOLATE_NEAREST)
	var err := img.save_png(path)
	if err != OK:
		push_error("Debug: failed to save %s (error %d)" % [path, err])
		return false
	print("Debug: captured %s" % path)
	return true


func _absolutize(path: String) -> String:
	if path.is_absolute_path():
		return path
	if path.begins_with("res://") or path.begins_with("user://"):
		return ProjectSettings.globalize_path(path)
	# Relative paths resolve against the project root (game/).
	return ProjectSettings.globalize_path("res://").path_join(path).simplify_path()
