extends Node2D
## Root scene. Never replaced; SceneDirector swaps Room instances under WorldHolder.

const PINNED_VERSION_MINOR := 5  # ADR 0001: Godot 4.5.x only


func _ready() -> void:
	_check_engine_version()
	SceneDirector.world_holder = $WorldHolder
	DialogueRunner.setup_ui($UILayer/DialogueBox, $UILayer/ChoiceMenu, $UILayer/FadeRect)


func _check_engine_version() -> void:
	var v: Dictionary = Engine.get_version_info()
	if v.major != 4 or v.minor != PINNED_VERSION_MINOR:
		push_warning(
			"Engine is %s — project is pinned to 4.%d.x (see docs/decisions/0001-godot-version.md)"
			% [v.string, PINNED_VERSION_MINOR]
		)
