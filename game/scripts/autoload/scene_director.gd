extends Node
## Autoload: ControlMode state machine + actor/room registry (plan section 5).
## Third-from-last in the boot order but "SceneDirector" in the plan's
## autoload list; owns WHICH room is loaded and WHO can move.
##
## M2 scope is deliberately narrow: ControlMode + name-based lookups the
## DialogueRunner needs to execute move/face/teleport/show/hide/pan/zoom/
## shake/goto_room. Mission-gated room transitions (allowed_exits, HUD
## objectives) are M4's "day-loop scaffolding" — this only records which
## mission is active.

enum ControlMode { CUTSCENE, FREE_ROAM, MISSION, MINIGAME }

signal mode_changed(mode: ControlMode)
signal room_changed(room_id: String)

## Set explicitly by main.gd once Main.tscn is in the tree — autoloads
## _ready() before the main scene exists, so an absolute get_node() path
## here would silently resolve to nothing.
var world_holder: Node2D = null

var mode: ControlMode = ControlMode.CUTSCENE:
	set(value):
		if mode == value:
			return
		mode = value
		mode_changed.emit(mode)

var current_room: Node = null
var current_mission_id: String = ""

var _actors: Dictionary = {}   ## actor_id (String) -> Node
var _camera: Camera2D = null
var _room_registry: Dictionary = {}   ## room_id (String) -> res:// path


func register_room_path(room_id: String, scene_path: String) -> void:
	_room_registry[room_id] = scene_path


func register_actor(actor_id: String, actor: Node) -> void:
	if actor_id == "":
		return
	_actors[actor_id] = actor


func unregister_actor(actor_id: String) -> void:
	_actors.erase(actor_id)


func get_actor(actor_id: String) -> Node:
	return _actors.get(actor_id)


func register_camera(camera: Camera2D) -> void:
	_camera = camera


func get_camera() -> Camera2D:
	return _camera


## Resolves a DSL target name (used by move/face/teleport/pan) to a world
## position: another registered actor's position, else a named node
## (Marker2D or prop) found anywhere under the current room. Returns null
## (not a crash) if nothing matches — dev-content gap, not a player-facing
## fail state.
func resolve_position(target_name: String) -> Variant:
	var actor: Node = get_actor(target_name)
	if actor is Node2D:
		return (actor as Node2D).global_position
	if current_room == null:
		push_warning("SceneDirector: no current room; can't resolve '%s'" % target_name)
		return null
	var node := current_room.find_child(target_name, true, false)
	if node is Node2D:
		return (node as Node2D).global_position
	push_warning("SceneDirector: could not resolve target '%s'" % target_name)
	return null


## Finds any named node (prop, title card, overlay) under the current room,
## for the DSL's show/hide commands.
func find_in_room(node_name: String) -> Node:
	if current_room == null:
		return null
	return current_room.find_child(node_name, true, false)


func start_mission(mission_id: String) -> void:
	current_mission_id = mission_id
	mode = ControlMode.MISSION


## Swaps WorldHolder's child to the room registered under `room_id` (or a
## direct res:// path). Actors from the previous room are dropped from the
## registry; the new room's Actors self-register in their own _ready().
func goto_room(room_id: String) -> void:
	if world_holder == null:
		push_error("SceneDirector: world_holder not set (main.gd must assign it)")
		return
	var scene_path: String = room_id if room_id.begins_with("res://") \
		else _room_registry.get(room_id, "")
	if scene_path == "" or not ResourceLoader.exists(scene_path):
		push_error("SceneDirector: unknown room '%s'" % room_id)
		return
	for child in world_holder.get_children():
		world_holder.remove_child(child)
		child.queue_free()
	_actors.clear()
	_camera = null
	var packed: PackedScene = load(scene_path)
	var instance: Node = packed.instantiate()
	world_holder.add_child(instance)
	current_room = instance
	room_changed.emit(room_id)
