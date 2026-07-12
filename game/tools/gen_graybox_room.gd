extends SceneTree
## One-shot builder for the M1 gray-box room scene. Kept for reproducibility:
##   godot --path game --headless --script res://tools/gen_graybox_room.gd
## Writes res://scenes/rooms/act1/graybox.tscn (committed; safe to re-run).

const TILESET := "res://assets/gen/tiles/graybox_tileset.tres"
const PLAYER_SCENE := "res://scenes/actors/player.tscn"
const ROOM_SCRIPT := "res://scripts/systems/room.gd"
const OUT := "res://scenes/rooms/act1/graybox.tscn"

const ROOM_W := 30
const ROOM_H := 14
const CELL := 32
# Atlas columns (append-only order from the graybox sidecar).
const FLOOR := Vector2i(0, 0)
const WALL := Vector2i(1, 0)
const FLOOR_VAR := Vector2i(2, 0)
const MARKER := Vector2i(3, 0)
const SPAWN_CELL := Vector2i(15, 11)


func _initialize() -> void:
	var root := Node2D.new()
	root.name = "Graybox"
	root.set_script(load(ROOM_SCRIPT))
	root.set("room_id", "act1_graybox")

	var tiles := TileMapLayer.new()
	tiles.name = "Tiles"
	tiles.tile_set = load(TILESET)
	_lay_out_room(tiles)
	root.add_child(tiles)
	tiles.owner = root

	var spawn := Marker2D.new()
	spawn.name = "spawn_south"
	spawn.position = Vector2(
		SPAWN_CELL.x * CELL + CELL / 2.0, SPAWN_CELL.y * CELL + CELL / 2.0
	)
	root.add_child(spawn)
	spawn.owner = root

	var player: Node2D = (load(PLAYER_SCENE) as PackedScene).instantiate()
	player.position = spawn.position
	root.add_child(player)
	player.owner = root
	var camera: Camera2D = player.get_node("Camera2D")
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = ROOM_W * CELL
	camera.limit_bottom = ROOM_H * CELL

	var packed := PackedScene.new()
	var pack_err := packed.pack(root)
	if pack_err != OK:
		push_error("gen_graybox_room: pack failed (%d)" % pack_err)
		quit(1)
		return
	var save_err := ResourceSaver.save(packed, OUT)
	root.free()
	if save_err != OK:
		push_error("gen_graybox_room: save failed (%d)" % save_err)
		quit(1)
		return
	print("gen_graybox_room: wrote %s" % OUT)
	quit(0)


func _lay_out_room(tiles: TileMapLayer) -> void:
	for y in ROOM_H:
		for x in ROOM_W:
			var is_edge := x == 0 or y == 0 or x == ROOM_W - 1 or y == ROOM_H - 1
			tiles.set_cell(Vector2i(x, y), 0, _pick_tile(x, y, is_edge))


func _pick_tile(x: int, y: int, is_edge: bool) -> Vector2i:
	if is_edge:
		return WALL
	if Vector2i(x, y) == SPAWN_CELL:
		return MARKER
	if (x * 7 + y * 13) % 19 == 0:
		return FLOOR_VAR  # deterministic sprinkle, no RNG
	return FLOOR
