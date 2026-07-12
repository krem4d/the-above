extends Node2D
## Tour-only end-to-end proof for M2: loads a REAL room via SceneDirector,
## then runs a REAL Act 1 .scene file through DialogueRunner — unlike
## ui_demo.gd (M2's UI slice), nothing here calls DialogueBox directly.
## Missing M4 content (rooms/actors the .scene references that don't exist
## yet) is expected to no-op with warnings, not crash — the point is
## proving the DSL parser -> runner -> UI pipeline works on real content.

const SCENE_PATH := "res://story/scripts/act1/d2_observatory.scene"


func _ready() -> void:
	SceneDirector.goto_room("res://scenes/rooms/act1/graybox.tscn")
	SceneDirector.mode = SceneDirector.ControlMode.CUTSCENE
	DialogueRunner.run_scene(SCENE_PATH)
	# Force the typewriter to full reveal a few frames in, purely so the
	# tour screenshot shows complete text instead of a mid-reveal fragment.
	for _i in 6:
		await get_tree().process_frame
	if DialogueRunner.dialogue_box.is_typing():
		DialogueRunner.dialogue_box.skip_to_end()
