class_name Actor
extends CharacterBody2D
## Shared 4-direction actor for NPCs and the player (plan section 5).
## Expects an AnimatedSprite2D child named "Sprite" whose SpriteFrames
## provides walk_n/walk_s/walk_e/walk_w (idle_* optional; falls back).

signal arrived

const ARRIVE_EPSILON := 1.0
const STALL_GIVE_UP_SECONDS := 0.6

## DSL actor id (e.g. "hoca", "ada") this instance registers under with
## SceneDirector — move/face/teleport/say address actors by this name.
@export var actor_id: String = ""
@export var display_name: String = ""   ## falls back to the raw actor_id if empty
@export var portrait: Texture2D = null
## Optional mood -> Texture2D overrides for `say ... mood=<mood>` (M4).
## Only characters with authored mood portraits (hoca) populate this.
@export var portrait_moods: Dictionary = {}

@export var move_speed: float = 70.0

## Per-character SpriteFrames, baked by gen_rooms as a ROOT-level property —
## setting it on the nested $Sprite child directly does not survive
## PackedScene.pack() (same trap as the player camera limits). Null keeps
## the actor.tscn default (hoca's frames).
@export var sprite_frames: SpriteFrames = null

@export var facing: String = "s":
	set(value):
		if value not in ["n", "s", "e", "w"]:
			push_warning("Actor: invalid facing %s" % value)
			return
		facing = value
		if not _walking:
			play_idle()

var _walking := false

@onready var sprite: AnimatedSprite2D = $Sprite


func _ready() -> void:
	if sprite_frames != null:
		sprite.sprite_frames = sprite_frames
	play_idle()
	if actor_id != "":
		SceneDirector.register_actor(actor_id, self)


func _exit_tree() -> void:
	if actor_id != "":
		SceneDirector.unregister_actor(actor_id)


## Portrait for a dialogue line: the mood override if one is authored,
## else the neutral portrait (possibly null — the box hides the slot).
func get_portrait(mood: String = "") -> Texture2D:
	if mood != "" and portrait_moods.has(mood):
		var override: Variant = portrait_moods[mood]
		if override is Texture2D:
			return override
	return portrait


## Coroutine: walk in a straight line to `target` (global), then emit `arrived`.
## Usage: `await actor.walk_to(pos)` or connect to `arrived`.
##
## Blocked-walk watchdog: cutscene choreography must ALWAYS complete (design
## law — the story can never soft-lock). If a solid pins the body so it stops
## making progress, give it a beat, then snap to the authored mark with a
## warning. A one-frame visual pop in a broken authored path beats a locked
## game; the warning surfaces the bad marker/solid in probe and tour logs.
func walk_to(target: Vector2) -> void:
	_walking = true
	var stalled_seconds := 0.0
	while _walking and is_inside_tree():
		await get_tree().physics_frame
		var to_target := target - global_position
		var step := move_speed * get_physics_process_delta_time()
		if to_target.length() <= maxf(step, ARRIVE_EPSILON):
			global_position = target.round()
			_walking = false
			break
		var before := global_position
		velocity = to_target.normalized() * move_speed
		face_toward(to_target)
		play_walk()
		move_and_slide()
		position = position.round()
		if global_position.distance_to(before) < step * 0.25:
			stalled_seconds += get_physics_process_delta_time()
			if stalled_seconds >= STALL_GIVE_UP_SECONDS:
				push_warning("Actor '%s': walk_to blocked at %s en route to %s — snapping (check the room's solids)" % [
					actor_id, global_position, target,
				])
				global_position = target.round()
				_walking = false
				break
		else:
			stalled_seconds = 0.0
	velocity = Vector2.ZERO
	_walking = false
	play_idle()
	arrived.emit()


func stop_walking() -> void:
	_walking = false


func face_toward(direction: Vector2) -> void:
	if direction == Vector2.ZERO:
		return
	if absf(direction.x) >= absf(direction.y):
		facing = "e" if direction.x > 0.0 else "w"
	else:
		facing = "s" if direction.y > 0.0 else "n"


func play_walk() -> void:
	_play_animation("walk_" + facing)


func play_idle() -> void:
	var idle_name := "idle_" + facing
	var walk_name := "walk_" + facing
	if _has_animation(idle_name):
		_play_animation(idle_name)
	elif _has_animation(walk_name):
		# No dedicated idle for this facing: freeze the walk cycle's first frame.
		if sprite.animation == walk_name and not sprite.is_playing() and sprite.frame == 0:
			return
		_play_animation(walk_name)
		sprite.pause()
		sprite.frame = 0
	else:
		_play_animation("idle_s")


func _play_animation(anim_name: String) -> void:
	if sprite == null or not _has_animation(anim_name):
		return
	if sprite.animation != anim_name or not sprite.is_playing():
		sprite.play(anim_name)


func _has_animation(anim_name: String) -> bool:
	return sprite != null and sprite.sprite_frames != null \
		and sprite.sprite_frames.has_animation(anim_name)
