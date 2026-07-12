extends Node2D
## Tour-only demo driver for the waterfall minigame — stages a live
## WaterfallView session so the screenshot harness can capture it
## (`make tour-scene SCENE=waterfall`). Not shipped gameplay.
##
## Loads the REAL sig_long_call session (Day 6 keystone: the 11-minute
## recording) so the tour shows the actual mechanic — steady beam-2 trace in
## reserved signal-magenta, RECORD verb, live frequency readout — rather than
## a hand-faked panel. WaterfallView._process then scrolls the waterfall over
## the harness's wait_frames, filling the canvas with trace history.

const DEMO_SESSION := "sig_long_call"
const LIBRARY_PATH := "res://story/signals/spectro_sessions.json"

@onready var _view: WaterfallView = %WaterfallDemoView


func _ready() -> void:
	_view.start_session(DEMO_SESSION, _load_demo_config())


func _load_demo_config() -> Dictionary:
	if FileAccess.file_exists(LIBRARY_PATH):
		var parsed := WaterfallSessionLibrary.parse(FileAccess.get_file_as_string(LIBRARY_PATH))
		if parsed["ok"]:
			var config: Dictionary = WaterfallSessionLibrary.get_session_config(
				parsed["sessions"], DEMO_SESSION
			)
			if not config.is_empty():
				return config
	# Fallback so the tour never renders an empty panel if the manifest moves.
	return {
		"kind": "keystone", "target_freq_mhz": 1421.6, "tolerance_mhz": 0.5,
		"freq_min_mhz": 1411.6, "freq_max_mhz": 1431.6, "start_freq_mhz": 1421.6,
		"signal_beam": 2, "duration_seconds": 34.0, "primary_verb": "record",
		"prompt_key": "spectro.sig_long_call.prompt",
	}
