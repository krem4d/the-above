class_name Room
extends Node2D
## Base script for every location scene (plan section 5). Room scenes are
## generated from layout JSON by tools/gen_rooms.gd (M4) with the node
## contract: TileMapLayers (Ground/FloorDecor/Walls/Above), a y-sorted
## World holding Props + NPCs + the Player, SpawnPoints (named Marker2D),
## Triggers (Area2D exits named by exit_id), and an optional night_tint
## CanvasModulate the DSL toggles with show/hide.

@export var room_id: String = ""


func _ready() -> void:
	var triggers := get_node_or_null("Triggers")
	if triggers == null:
		return
	for child in triggers.get_children():
		if child is Area2D:
			# The trigger's node name IS the exit id (unique by tree rules).
			(child as Area2D).body_entered.connect(_on_exit_body_entered.bind(child.name))


func _on_exit_body_entered(body: Node2D, exit_id: String) -> void:
	# Only the protagonist trips exits — NPCs walking cutscene paths must
	# never complete a mission by brushing a doorway.
	if body != SceneDirector.get_actor("hoca"):
		return
	MissionSystem.on_exit_touched(exit_id)
