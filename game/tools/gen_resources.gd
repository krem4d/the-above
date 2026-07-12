extends SceneTree
## gen_resources — reads artgen sidecars and (re)writes committed Godot resources.
##
## Run (import first so the sheet textures resolve):
##   godot --path game --headless --import
##   godot --path game --headless --script res://tools/gen_resources.gd
##
## Idempotent: output depends only on the sidecars. Atlas contract is
## append-only (plan section 5) — tile indices and sheet rows never move,
## so regenerating art never invalidates committed scenes.

const TILES_SHEET := "res://assets/gen/tiles/graybox_sheet.png"
const TILES_SIDECAR := "res://assets/gen/tiles/graybox_sheet.json"
const TILESET_OUT := "res://assets/gen/tiles/graybox_tileset.tres"

const HOCA_SHEET := "res://assets/gen/sprites/hoca_sheet.png"
const HOCA_SIDECAR := "res://assets/gen/sprites/hoca_sheet.json"
const FRAMES_OUT := "res://assets/gen/sprites/hoca_frames.tres"

const SOLID_TILES := ["wall"]  # tiles that get a full-cell collision polygon


func _initialize() -> void:
	var failed := false
	if _build_tileset() != OK:
		failed = true
	if _build_sprite_frames() != OK:
		failed = true
	if failed:
		push_error("gen_resources: FAILED")
	else:
		print("gen_resources: wrote %s and %s" % [TILESET_OUT, FRAMES_OUT])
	quit(1 if failed else 0)


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


func _build_tileset() -> Error:
	var sidecar := _load_sidecar(TILES_SIDECAR)
	var texture := _load_texture(TILES_SHEET)
	if sidecar.is_empty() or texture == null:
		return FAILED
	var grid: Dictionary = sidecar.get("grid", {})
	var cell := int(grid.get("cell", 32))
	var cols := int(grid.get("cols", 0))
	var rows := int(grid.get("rows", 1))
	var tile_names: Array = sidecar.get("tiles", [])

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
			if index < tile_names.size() and tile_names[index] in SOLID_TILES:
				var data := source.get_tile_data(coords, 0)
				data.add_collision_polygon(0)
				data.set_collision_polygon_points(0, 0, full_cell)
	return ResourceSaver.save(tile_set, TILESET_OUT)


func _build_sprite_frames() -> Error:
	var sidecar := _load_sidecar(HOCA_SIDECAR)
	var texture := _load_texture(HOCA_SHEET)
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
	return ResourceSaver.save(frames, FRAMES_OUT)
