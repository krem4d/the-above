extends Node
## Autoload: music/sfx interface (plan section 5). Deliberately a safe no-op
## stub for M2 — no audio assets exist yet (audiogen/ programmatic synthesis
## is M6 scope). DialogueRunner calls this real interface now so wiring
## real playback later is a drop-in, not a DialogueRunner rewrite.

var current_music: String = ""


func play_music(track_name: String, fade_seconds: float = 0.0) -> void:
	if track_name == "none":
		stop_music(fade_seconds)
		return
	current_music = track_name


func stop_music(_fade_seconds: float = 0.0) -> void:
	current_music = ""


func play_sfx(_sfx_name: String) -> void:
	pass
