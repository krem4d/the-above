extends Control
## Day + mission-objective HUD (M4 day-loop scaffolding). Visible only in
## MISSION mode with a known mission; cutscenes and minigames own the whole
## frame. Sits UNDER the FadeRect in main.tscn so it fades with the world.

@onready var _day_label: Label = %DayLabel
@onready var _objective_label: Label = %ObjectiveLabel


func _ready() -> void:
	SceneDirector.mode_changed.connect(_on_state_changed)
	SceneDirector.mission_changed.connect(_on_state_changed)
	GameState.day_changed.connect(_on_state_changed)
	Locale.language_changed.connect(_on_state_changed)
	_refresh()


func _on_state_changed(_value: Variant) -> void:
	_refresh()


func _refresh() -> void:
	var mission := MissionSystem.current_mission_config()
	var mission_active := SceneDirector.mode == SceneDirector.ControlMode.MISSION \
		and not mission.is_empty()
	visible = mission_active
	if not mission_active:
		return
	_day_label.text = Locale.t("ui.hud.day_counter", {"day": GameState.day})
	_objective_label.text = Locale.t(String(mission["objective_key"]))
