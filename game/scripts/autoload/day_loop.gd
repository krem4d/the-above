extends Node
## Autoload: the day loop (M4). Owns the new-game boot and the sleep→wake
## rollover; what happens INSIDE a day belongs to the scenes and
## MissionSystem. Data-driven by convention: day N is over when scene
## content sets the flag "dN_complete"; the loop then waits out the running
## scene, advances GameState.day, autosaves, and runs the next morning's
## wake script (story/scripts/act1/d<N>_wake.scene) — "per-day wake scripts
## consulting long-range flags" per PLAN M4, the consulting happening
## inside the wake scripts themselves via `if <flag>`.

const AUTOSAVE_SLOT := 1

var _rolling := false


func _ready() -> void:
	GameState.flag_changed.connect(_on_flag_changed)


## Fresh Day-1 boot. Title screen / continue-from-save are M5 scope —
## until then every launch is a new observation. Called deferred by
## main.gd once the world and UI exist (never from autoload _ready).
func begin() -> void:
	GameState.reset_new_game()
	_run_wake(GameState.day)


func day_complete_flag(day: int) -> String:
	return "d%d_complete" % day


func wake_scene_name(day: int) -> String:
	return "d%d_wake" % day


func _on_flag_changed(flag_name: String, value: Variant) -> void:
	if flag_name != day_complete_flag(GameState.day):
		return
	if value and not _rolling:
		_roll_day()


func _roll_day() -> void:
	_rolling = true
	if DialogueRunner.is_running():
		await DialogueRunner.scene_finished
	GameState.advance_day()
	# Autosave behind the end-of-day fade — the canonical "sleep. Save."
	# beat. Slot 1 is the running autosave until M5's slot UI exists.
	SaveSystem.save_game(AUTOSAVE_SLOT)
	_rolling = false
	_run_wake(GameState.day)


func _run_wake(day: int) -> void:
	var path := MissionLibrary.scene_script_path(wake_scene_name(day))
	if not FileAccess.file_exists(path):
		push_warning(
			"DayLoop: no wake script for day %d (%s) — end of authored content" % [day, path]
		)
		return
	DialogueRunner.run_scene(path)
