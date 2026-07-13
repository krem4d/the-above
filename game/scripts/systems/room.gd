class_name Room
extends Node2D
## Base script for every location scene (plan section 5). Room scenes are
## generated from layout JSON by tools/gen_rooms.gd (M4) with the node
## contract: TileMapLayers (Ground/FloorDecor/Walls/Above), a y-sorted
## World holding Props + NPCs + the Player, SpawnPoints (named Marker2D),
## Triggers (Area2D exits named by exit_id), and an optional night_tint
## CanvasModulate the DSL toggles with show/hide.

@export var room_id: String = ""
## Room footprint in tiles, baked by gen_rooms — drives runtime camera
## limits (property overrides on the nested Camera2D don't survive
## PackedScene.pack(), so limits must be applied here, not baked).
@export var room_size: Vector2i = Vector2i.ZERO

const CELL := 32


func _ready() -> void:
	_apply_camera_limits()
	var triggers := get_node_or_null("Triggers")
	if triggers == null:
		return
	for child in triggers.get_children():
		if child is Area2D:
			# The trigger's node name IS the exit id (unique by tree rules).
			(child as Area2D).body_entered.connect(_on_exit_body_entered.bind(child.name))


## Clamp the player camera to the room; when the room is smaller than the
## design viewport on an axis, center it with symmetric void borders
## instead of letting the camera anchor to one edge.
func _apply_camera_limits() -> void:
	if room_size == Vector2i.ZERO:
		return
	var camera := get_node_or_null("World/Player/Camera2D") as Camera2D
	if camera == null:
		return
	var view_w := int(ProjectSettings.get_setting("display/window/size/viewport_width", 640))
	var view_h := int(ProjectSettings.get_setting("display/window/size/viewport_height", 360))
	var room_px := Vector2i(room_size.x * CELL, room_size.y * CELL)
	var overhang_x := maxi(0, (view_w - room_px.x) / 2)
	var overhang_y := maxi(0, (view_h - room_px.y) / 2)
	camera.limit_left = -overhang_x
	camera.limit_right = room_px.x + overhang_x
	camera.limit_top = -overhang_y
	camera.limit_bottom = room_px.y + overhang_y


func _on_exit_body_entered(body: Node2D, exit_id: String) -> void:
	# Only the protagonist trips exits — NPCs walking cutscene paths must
	# never complete a mission by brushing a doorway.
	if body != SceneDirector.get_actor("hoca"):
		return
	# Deferred: mission completion can cascade into goto_room, which frees
	# this room's collision objects — illegal inside a physics callback.
	MissionSystem.on_exit_touched.call_deferred(exit_id)
