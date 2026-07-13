extends SceneTree
## gen_resources — reads artgen sidecars and (re)writes committed Godot resources.
##
## Run (import first so the sheet textures resolve):
##   godot --path game --headless --import
##   godot --path game --headless --script res://tools/gen_resources.gd
##
## Generic since M4: every assets/gen/tiles/<stem>_sheet.json becomes
## <stem>_tileset.tres and every assets/gen/sprites/<stem>_sheet.json
## becomes <stem>_frames.tres. Idempotent: output depends only on the
## sidecars. Atlas contract is append-only (plan section 5) — tile indices
## and sheet rows never move, so regenerating art never invalidates
## committed scenes.

const TILES_DIR := "res://assets/gen/tiles/"
const SPRITES_DIR := "res://assets/gen/sprites/"
const SHEET_SUFFIX := "_sheet.json"

## Fallback for sidecars that predate the "solid" key (M1 graybox).
const DEFAULT_SOLID := ["wall"]


func _initialize() -> void:
	var failed := false
	var built := 0
	for stem in _sheet_stems(TILES_DIR):
		if _build_tileset(stem) == OK:
			built += 1
		else:
			failed = true
	for stem in _sheet_stems(SPRITES_DIR):
		if _build_sprite_frames(stem) == OK:
			built += 1
		else:
			failed = true
	if built == 0:
		push_error("gen_resources: no *_sheet.json sidecars found (run `make art` first)")
		failed = true
	if failed:
		push_error("gen_resources: FAILED")
	else:
		print("gen_resources: wrote %d resources" % built)
	quit(1 if failed else 0)


func _sheet_stems(dir_path: String) -> Array[String]:
	var stems: Array[String] = []
	var dir := DirAccess.open(dir_path)
	if dir == null:
		return stems
	for file in dir.get_files():
		if file.ends_with(SHEET_SUFFIX):
			stems.append(file.trim_suffix(SHEET_SUFFIX))
	stems.sort()  # deterministic build order/output
	return stems


func _load_sidecar(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("gen_resources: missing sidecar %s (run `make art` first)" % path)
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if parsed is not Dictionary:
		push_error("gen_resources: %s is not a JSON object" % path)
		return {}
	return parsed


func _load_texture(path: String) -> Texture2D:
	if not ResourceLoader.exists(path):
		push_error("gen_resources: %s not importable (run `godot --headless --import`)" % path)
		return null
	return load(path)


func _build_tileset(stem: String) -> Error:
	var sidecar := _load_sidecar(TILES_DIR + stem + SHEET_SUFFIX)
	var texture := _load_texture(TILES_DIR + stem + "_sheet.png")
	if sidecar.is_empty() or texture == null:
		return FAILED
	var grid: Dictionary = sidecar.get("grid", {})
	var cell := int(grid.get("cell", 32))
	var cols := int(grid.get("cols", 0))
	var rows := int(grid.get("rows", 1))
	var tile_names: Array = sidecar.get("tiles", [])
	var solid_names: Array = sidecar.get("solid", DEFAULT_SOLID)

	var tile_set := TileSet.new()
	tile_set.tile_size = Vector2i(cell, cell)
	tile_set.add_physics_layer()

	var source := TileSetAtlasSource.new()
	source.texture = texture
	source.texture_region_size = Vector2i(cell, cell)
	# Attach the source BEFORE creating tiles: TileData only sees the
	# TileSet's physics layers once the source belongs to it.
	tile_set.add_source(source, 0)
	var half := cell / 2.0
	var full_cell := PackedVector2Array([
		Vector2(-half, -half), Vector2(half, -half), Vector2(half, half), Vector2(-half, half)
	])
	for row in rows:
		for col in cols:
			var coords := Vector2i(col, row)
			source.create_tile(coords)
			var index := row * cols + col
			if index < tile_names.size() and tile_names[index] in solid_names:
				var data := source.get_tile_data(coords, 0)
				data.add_collision_polygon(0)
				data.set_collision_polygon_points(0, 0, full_cell)
	return ResourceSaver.save(tile_set, TILES_DIR + stem + "_tileset.tres")


func _build_sprite_frames(stem: String) -> Error:
	var sidecar := _load_sidecar(SPRITES_DIR + stem + SHEET_SUFFIX)
	var texture := _load_texture(SPRITES_DIR + stem + "_sheet.png")
	if sidecar.is_empty() or texture == null:
		return FAILED
	var frame_size: Array = sidecar.get("frame", [32, 48])
	var fw := int(frame_size[0])
	var fh := int(frame_size[1])
	var anims: Dictionary = sidecar.get("anims", {})

	var frames := SpriteFrames.new()
	frames.remove_animation("default")
	var anim_names := anims.keys()
	anim_names.sort()  # deterministic .tres output
	for anim_name: String in anim_names:
		var spec: Dictionary = anims[anim_name]
		var row := int(spec.get("row", 0))
		var count := int(spec.get("frames", 1))
		var fps := float(spec.get("fps", 8))
		frames.add_animation(anim_name)
		frames.set_animation_speed(anim_name, fps)
		frames.set_animation_loop(anim_name, true)
		for i in count:
			var atlas := AtlasTexture.new()
			atlas.atlas = texture
			atlas.region = Rect2(i * fw, row * fh, fw, fh)
			frames.add_frame(anim_name, atlas)
	return ResourceSaver.save(frames, SPRITES_DIR + stem + "_frames.tres")
