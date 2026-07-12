extends Actor
## Player-controlled actor: reads move_* input actions each physics tick.
## Positions are rounded after movement for pixel snap (plan section 5).
## Input is dead outside FREE_ROAM/MISSION (plan section 5, "directed vs
## free-roam") — during cutscenes the DialogueRunner drives movement instead.


func _ready() -> void:
	super._ready()
	var camera := get_node_or_null("Camera2D")
	if camera is Camera2D:
		SceneDirector.register_camera(camera)


func _physics_process(_delta: float) -> void:
	if _walking:
		return   # a DSL `move` command is driving this body via walk_to(); don't fight it with input
	var free_to_move := SceneDirector.mode in [
		SceneDirector.ControlMode.FREE_ROAM, SceneDirector.ControlMode.MISSION,
	]
	var input_dir := Input.get_vector("move_left", "move_right", "move_up", "move_down") \
		if free_to_move else Vector2.ZERO
	velocity = input_dir * move_speed
	move_and_slide()
	position = position.round()
	if input_dir != Vector2.ZERO:
		face_toward(input_dir)
		play_walk()
	else:
		play_idle()
