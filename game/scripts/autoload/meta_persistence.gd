extends Node
## Autoload: meta.json + byte-identical shadow copy (plan section 5).
## Survives save deletion; detects when a player has erased their saves
## (Flowey-inspired meta layer). Third in the boot order — applies the
## saved language preference to Locale (which booted with a default).

const META_PATH := "user://meta.json"
const SHADOW_PATH := "user://meta_shadow.json"

signal player_tried_to_erase_detected

var language: String = Locale.DEFAULT_LANG
var observer_names_used: Array = []
var save_generations: Dictionary = {}   ## slot (String key) -> int generation count
var player_tried_to_erase: bool = false


func _ready() -> void:
	reload()


## Re-reads meta.json/shadow from disk and re-applies the language pref.
## Called by _ready(); also exposed for tests that simulate a fresh boot
## after manipulating the on-disk files.
func reload() -> void:
	_load()
	Locale.set_language(language)


func set_language(lang: String) -> void:
	language = lang
	Locale.set_language(lang)
	_save()


func record_observer_name(observer_name: String) -> void:
	if observer_name != "" and observer_name not in observer_names_used:
		observer_names_used.append(observer_name)
		_save()


func note_save_written(slot: int) -> void:
	var key := str(slot)
	save_generations[key] = save_generations.get(key, 0) + 1
	_save()


## True when meta remembers save-writes for this slot but the slot file is
## now gone — i.e. the player deleted it (title-screen hook, plan section 5).
func has_higher_generation_than_save(slot: int) -> bool:
	return save_generations.get(str(slot), 0) > 0 and not SaveSystem.save_exists(slot)


func _load() -> void:
	var data: Variant = _read_valid(META_PATH)
	var shadow_data: Variant = _read_valid(SHADOW_PATH)
	if data == null and shadow_data != null:
		player_tried_to_erase = true
		data = shadow_data
		player_tried_to_erase_detected.emit()
	else:
		# Explicitly false here (not left untouched) — otherwise a prior
		# detection would leak into every later reload(), even a clean one.
		player_tried_to_erase = false
		if data == null:
			data = {}
	_apply(data)
	_save()   # heals a missing/corrupt meta or shadow copy immediately


func _apply(data: Dictionary) -> void:
	language = data.get("language", Locale.DEFAULT_LANG)
	observer_names_used = (data.get("observer_names_used", []) as Array).duplicate()
	save_generations = (data.get("save_generations", {}) as Dictionary).duplicate()


func _to_dict() -> Dictionary:
	return {
		"language": language,
		"observer_names_used": observer_names_used.duplicate(),
		"save_generations": save_generations.duplicate(),
	}


func _save() -> void:
	var text := JSON.stringify(_to_dict())
	if not _write_atomic(META_PATH, text):
		push_warning("MetaPersistence: meta.json write failed — shadow copy may now be ahead of it")
	if not _write_atomic(SHADOW_PATH, text):
		push_warning("MetaPersistence: shadow copy write failed — it may now be behind meta.json")


func _write_atomic(path: String, text: String) -> bool:
	var tmp_path := path + ".tmp"
	var file := FileAccess.open(tmp_path, FileAccess.WRITE)
	if file == null:
		push_error("MetaPersistence: could not open %s for write" % tmp_path)
		return false
	file.store_string(text)
	file.close()
	var err := DirAccess.rename_absolute(tmp_path, path)
	if err != OK:
		push_error("MetaPersistence: rename failed for %s (error %d)" % [path, err])
		return false
	return true


func _read_valid(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		return null
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if parsed is not Dictionary:
		return null
	return parsed
