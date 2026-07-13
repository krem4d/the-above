extends SceneTree
## gen_rooms — builds committed Room scenes (.tscn) from layout JSON (M4).
##
##   godot --path game --headless --import        # textures must resolve
##   godot --path game --headless --script res://tools/gen_rooms.gd
##
## One JSON per room under res://story/rooms/ (registry.json excluded).
## Layouts are the reviewable source of truth; the .tscn is codegen output,
## committed like the artgen PNGs. Deterministic: output depends only on
## the JSON + sidecars. Node contract (see room.gd): Ground/FloorDecor/
## Walls TileMapLayers, y-sorted World (Props, NPCs, Player), Above layer
## over actors, SpawnPoints (Marker2D), Triggers (Area2D exits, node name
## = exit id), optional night_tint CanvasModulate (hidden; DSL show/hide).
##
## All layout positions are in TILE units (floats allowed), cell = 32 px.
## Prop/NPC/marker positions are the object's BASE-CENTER (feet), which is
## also what y-sort compares.

const ROOMS_DIR := "res://story/rooms/"
const PROPS_DIR := "res://assets/gen/props/"
const SPRITES_DIR := "res://assets/gen/sprites/"
const TILES_DIR := "res://assets/gen/tiles/"
const OUT_DIR := "res://scenes/rooms/act1/"
const ROOM_SCRIPT := "res://scripts/systems/room.gd"
const PLAYER_SCENE := "res://scenes/actors/player.tscn"
const ACTOR_SCENE := "res://scenes/actors/actor.tscn"
const CELL := 32
const TILE_LAYERS := ["ground", "floor_decor", "walls", "above"]
const LAYER_NODE_NAMES := {
	"ground": "Ground", "floor_decor": "FloorDecor", "walls": "Walls", "above": "Above",
}
const NIGHT_TINT_COLOR := Color(0.42, 0.45, 0.72)

var _prop_sidecars: Dictionary = {}


func _initialize() -> void:
	var failed := false
	var built := 0
	var dir := DirAccess.open(ROOMS_DIR)
	if dir == null:
		push_error("gen_rooms: cannot open %s" % ROOMS_DIR)
		quit(1)
		return
	var files := dir.get_files()
	files.sort()
	for file in files:
		if not file.ends_with(".json") or file == "registry.json":
			continue
		if _build_room(ROOMS_DIR + file) == OK:
			built += 1
		else:
			failed = true
	if built == 0:
		push_error("gen_rooms: no room layouts found in %s" % ROOMS_DIR)
		failed = true
	print("gen_rooms: wrote %d room scene(s)" % built)
	quit(1 if failed else 0)


func _build_room(layout_path: String) -> Error:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(layout_path))
	if parsed is not Dictionary:
		push_error("gen_rooms: %s is not a JSON object" % layout_path)
		return FAILED
	var layout: Dictionary = parsed
	var room_id := String(layout.get("room_id", ""))
	if room_id == "":
		push_error("gen_rooms: %s missing room_id" % layout_path)
		return FAILED

	var root := Node2D.new()
	# No case transforms anywhere in this repo (Turkish İ/ı law) — the
	# layout provides an explicit scene_name or the raw id is used.
	root.name = String(layout.get("scene_name", room_id))
	root.set_script(load(ROOM_SCRIPT))
	root.set("room_id", room_id)

	var legend: Dictionary = layout.get("tile_legend", {})
	var layers: Dictionary = layout.get("layers", {})
	var tileset_path := String(layout.get("tileset", ""))
	var tile_names := _tileset_tile_names(tileset_path)
	var ground: Array = layers.get("ground", [])
	var room_h := ground.size()
	var room_w := 0
	if room_h > 0:
		room_w = String(ground[0]).length()

	for layer_key in TILE_LAYERS:
		if layer_key == "above":
			continue  # added after World so it draws over actors
		_add_tile_layer(root, layout, layer_key, legend, tile_names, tileset_path)

	var world := Node2D.new()
	world.name = "World"
	world.y_sort_enabled = true
	root.add_child(world)
	world.owner = root

	for prop: Dictionary in layout.get("props", []):
		if _add_prop(world, root, prop) != OK:
			return FAILED

	for npc: Dictionary in layout.get("npcs", []):
		_add_npc(world, root, npc)

	_add_player(world, root, layout, room_w, room_h)

	_add_tile_layer(root, layout, "above", legend, tile_names, tileset_path)

	var spawns := Node2D.new()
	spawns.name = "SpawnPoints"
	root.add_child(spawns)
	spawns.owner = root
	var markers: Dictionary = layout.get("markers", {})
	var marker_names := markers.keys()
	marker_names.sort()
	for marker_name: String in marker_names:
		var marker := Marker2D.new()
		marker.name = marker_name
		marker.position = _tile_to_px(markers[marker_name])
		spawns.add_child(marker)
		marker.owner = root

	var triggers := Node2D.new()
	triggers.name = "Triggers"
	root.add_child(triggers)
	triggers.owner = root
	for exit_cfg: Dictionary in layout.get("exits", []):
		_add_exit(triggers, root, exit_cfg)

	if bool(layout.get("edge_collision", false)):
		_add_edge_walls(root, room_w, room_h)

	if bool(layout.get("night_tint", false)):
		var tint := CanvasModulate.new()
		tint.name = "night_tint"
		tint.color = NIGHT_TINT_COLOR
		tint.visible = false
		root.add_child(tint)
		tint.owner = root

	var out_path := String(layout.get("out", OUT_DIR + room_id + ".tscn"))
	var packed := PackedScene.new()
	if packed.pack(root) != OK:
		push_error("gen_rooms: pack failed for %s" % room_id)
		root.free()
		return FAILED
	var err := ResourceSaver.save(packed, out_path)
	root.free()
	if err != OK:
		push_error("gen_rooms: save failed for %s (%d)" % [out_path, err])
		return FAILED
	print("gen_rooms: wrote %s" % out_path)
	return OK


func _tile_to_px(pos: Variant) -> Vector2:
	var arr: Array = pos
	return Vector2(float(arr[0]) * CELL, float(arr[1]) * CELL)


func _tileset_tile_names(tileset_path: String) -> Array:
	# The sidecar next to the sheet is authoritative for atlas order.
	var sidecar_path := tileset_path.replace("_tileset.tres", "_sheet.json")
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(sidecar_path))
	if parsed is Dictionary:
		return (parsed as Dictionary).get("tiles", [])
	return []


func _add_tile_layer(
	root: Node2D, layout: Dictionary, layer_key: String, legend: Dictionary,
	tile_names: Array, tileset_path: String,
) -> void:
	var rows: Array = (layout.get("layers", {}) as Dictionary).get(layer_key, [])
	var layer := TileMapLayer.new()
	layer.name = LAYER_NODE_NAMES[layer_key]
	if tileset_path != "" and ResourceLoader.exists(tileset_path):
		layer.tile_set = load(tileset_path)
	for y in rows.size():
		var row := String(rows[y])
		for x in row.length():
			var ch := row[x]
			if ch == " ":
				continue
			var tile_name := String(legend.get(ch, ""))
			if tile_name == "":
				push_warning("gen_rooms: %s layer %s has unmapped glyph '%s'" % [
					layout.get("room_id"), layer_key, ch,
				])
				continue
			var index := tile_names.find(tile_name)
			if index == -1:
				push_warning("gen_rooms: tile '%s' not in %s" % [tile_name, tileset_path])
				continue
			layer.set_cell(Vector2i(x, y), 0, Vector2i(index, 0))
	root.add_child(layer)
	layer.owner = root


func _prop_sidecar(sheet: String) -> Dictionary:
	if not _prop_sidecars.has(sheet):
		var parsed: Variant = JSON.parse_string(
			FileAccess.get_file_as_string(PROPS_DIR + sheet + ".json")
		)
		_prop_sidecars[sheet] = parsed if parsed is Dictionary else {}
	return _prop_sidecars[sheet]


func _add_prop(world: Node2D, root: Node2D, prop: Dictionary) -> Error:
	var node_name := String(prop.get("name", ""))
	var sheet := String(prop.get("sheet", ""))
	var prop_key := String(prop.get("prop", node_name))
	var sidecar := _prop_sidecar(sheet)
	var entry: Dictionary = (sidecar.get("props", {}) as Dictionary).get(prop_key, {})
	if node_name == "" or entry.is_empty():
		push_error("gen_rooms: prop '%s' (key '%s') not found in sheet '%s'" % [
			node_name, prop_key, sheet,
		])
		return FAILED
	var region: Array = entry.get("region", [0, 0, 0, 0])
	var w := float(region[2])
	var h := float(region[3])

	var holder := Node2D.new()
	holder.name = node_name
	holder.position = _tile_to_px(prop.get("pos", [0, 0]))
	holder.visible = not bool(prop.get("hidden", false))
	holder.z_index = int(prop.get("z_index", 0))
	world.add_child(holder)
	holder.owner = root

	var sprite := Sprite2D.new()
	sprite.name = "Sprite"
	var atlas := AtlasTexture.new()
	atlas.atlas = load(PROPS_DIR + sheet + ".png")
	atlas.region = Rect2(float(region[0]), float(region[1]), w, h)
	sprite.texture = atlas
	sprite.position = Vector2(0, -h / 2.0)  # node origin = base-center (y-sort key)
	holder.add_child(sprite)
	sprite.owner = root

	var solid: Variant = entry.get("solid")
	if solid is Array and (solid as Array).size() == 4:
		var s: Array = solid
		var body := StaticBody2D.new()
		body.name = "Solid"
		holder.add_child(body)
		body.owner = root
		var shape := CollisionShape2D.new()
		var rect := RectangleShape2D.new()
		rect.size = Vector2(float(s[2]), float(s[3]))
		shape.shape = rect
		# solid coords are relative to the region's top-left; origin is base-center.
		shape.position = Vector2(
			-w / 2.0 + float(s[0]) + float(s[2]) / 2.0,
			-h + float(s[1]) + float(s[3]) / 2.0
		)
		body.add_child(shape)
		shape.owner = root
	return OK


func _add_npc(world: Node2D, root: Node2D, npc: Dictionary) -> void:
	var instance: Node2D = (load(ACTOR_SCENE) as PackedScene).instantiate()
	var actor_id := String(npc.get("actor_id", ""))
	instance.name = "npc_" + actor_id if actor_id != "" else "Npc"
	instance.position = _tile_to_px(npc.get("pos", [0, 0]))
	instance.set("actor_id", actor_id)
	instance.set("display_name", String(npc.get("display_name", "")))
	instance.set("facing", String(npc.get("facing", "s")))
	var frames_path := SPRITES_DIR + String(npc.get("frames", actor_id)) + "_frames.tres"
	if ResourceLoader.exists(frames_path):
		(instance.get_node("Sprite") as AnimatedSprite2D).sprite_frames = load(frames_path)
	else:
		push_warning("gen_rooms: no frames at %s (npc '%s' keeps defaults)" % [frames_path, actor_id])
	var portrait_path := SPRITES_DIR + "portraits/" + String(npc.get("portrait", actor_id)) + ".png"
	if ResourceLoader.exists(portrait_path):
		instance.set("portrait", load(portrait_path))
	world.add_child(instance)
	instance.owner = root


func _add_player(world: Node2D, root: Node2D, layout: Dictionary, room_w: int, room_h: int) -> void:
	var player_cfg: Dictionary = layout.get("player", {})
	var instance: Node2D = (load(PLAYER_SCENE) as PackedScene).instantiate()
	instance.position = _tile_to_px(player_cfg.get("spawn", [1, 1]))
	instance.set("facing", String(player_cfg.get("facing", "s")))
	if ResourceLoader.exists(SPRITES_DIR + "portraits/hoca.png"):
		instance.set("portrait", load(SPRITES_DIR + "portraits/hoca.png"))
		var moods := {}
		for mood in ["tired", "wry", "listening"]:
			var mood_path := SPRITES_DIR + "portraits/hoca_%s.png" % mood
			if ResourceLoader.exists(mood_path):
				moods[mood] = load(mood_path)
		instance.set("portrait_moods", moods)
	var camera: Camera2D = instance.get_node("Camera2D")
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = room_w * CELL
	camera.limit_bottom = room_h * CELL
	world.add_child(instance)
	instance.owner = root


## Invisible static walls hugging the map bounds, for exterior rooms whose
## tilesets have no solid tiles (town, dolmuş) — the camera limits already
## clamp the view; this clamps the body.
func _add_edge_walls(root: Node2D, room_w: int, room_h: int) -> void:
	var body := StaticBody2D.new()
	body.name = "EdgeWalls"
	root.add_child(body)
	body.owner = root
	var w := room_w * CELL
	var h := room_h * CELL
	var edges := [
		[Vector2(w / 2.0, -CELL / 2.0), Vector2(w, CELL)],
		[Vector2(w / 2.0, h + CELL / 2.0), Vector2(w, CELL)],
		[Vector2(-CELL / 2.0, h / 2.0), Vector2(CELL, h)],
		[Vector2(w + CELL / 2.0, h / 2.0), Vector2(CELL, h)],
	]
	for edge: Array in edges:
		var shape := CollisionShape2D.new()
		var rect := RectangleShape2D.new()
		rect.size = edge[1]
		shape.shape = rect
		shape.position = edge[0]
		body.add_child(shape)
		shape.owner = root


func _add_exit(triggers: Node2D, root: Node2D, exit_cfg: Dictionary) -> void:
	var area := Area2D.new()
	area.name = String(exit_cfg.get("id", "exit"))
	var pos: Array = exit_cfg.get("pos", [0, 0])
	var size: Array = exit_cfg.get("size", [1, 1])
	area.position = Vector2(
		(float(pos[0]) + float(size[0]) / 2.0) * CELL,
		(float(pos[1]) + float(size[1]) / 2.0) * CELL
	)
	triggers.add_child(area)
	area.owner = root
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(float(size[0]) * CELL, float(size[1]) * CELL)
	shape.shape = rect
	area.add_child(shape)
	shape.owner = root
