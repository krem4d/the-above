extends Actor
## Player-controlled actor: reads move_* input actions each physics tick.
## Positions are rounded after movement for pixel snap (plan section 5).


func _physics_process(_delta: float) -> void:
	var input_dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = input_dir * move_speed
	move_and_slide()
	position = position.round()
	if input_dir != Vector2.ZERO:
		face_toward(input_dir)
		play_walk()
	else:
		play_idle()
