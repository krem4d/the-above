extends Node
## Autoload: slot saves with version + checksum + atomic write (plan
## section 5). Never crashes on a bad file — load falls back checksum
## mismatch -> .bak -> caller treats false as "start a clean new game".

const SAVE_DIR := "user://saves"
const CURRENT_VERSION := 1

signal save_completed(slot: int, success: bool)
signal load_completed(slot: int, success: bool)


func save_exists(slot: int) -> bool:
	return FileAccess.file_exists(_slot_path(slot))


func save_game(slot: int) -> bool:
	DirAccess.make_dir_recursive_absolute(SAVE_DIR)
	# Payload is embedded as a JSON-encoded STRING, not a nested Dictionary:
	# Godot's JSON parser collapses int/float on round-trip (5 -> 5.0), so
	# re-stringifying a parsed Dictionary would never reproduce the exact
	# original bytes. Hashing a string that's stored and read back verbatim
	# sidesteps that entirely.
	var payload_text := JSON.stringify(GameState.to_dict())
	var record := {
		"version": CURRENT_VERSION,
		"checksum": payload_text.sha256_text(),
		"payload": payload_text,
	}

	var tmp_path := _tmp_path(slot)
	var file := FileAccess.open(tmp_path, FileAccess.WRITE)
	if file == null:
		push_error("SaveSystem: could not open %s for write" % tmp_path)
		save_completed.emit(slot, false)
		return false
	file.store_string(JSON.stringify(record))
	file.close()

	# Re-read and verify the tmp file before trusting it with anything —
	# store_string()/close() don't reliably surface a partial write (disk
	# full, I/O error) any other way, and an unverified tmp file would
	# otherwise get renamed straight into the trusted slot path below.
	if _load_valid(tmp_path) == null:
		push_error("SaveSystem: tmp write for slot %d failed verification, aborting save" % slot)
		DirAccess.remove_absolute(tmp_path)
		save_completed.emit(slot, false)
		return false

	# Only refresh .bak from a slot file that is itself still valid — never
	# let an already-corrupt slot file overwrite the last known-good backup.
	if _load_valid(_slot_path(slot)) != null:
		var copy_err := DirAccess.copy_absolute(_slot_path(slot), _bak_path(slot))
		if copy_err != OK:
			push_warning("SaveSystem: could not refresh .bak for slot %d (error %d)" % [slot, copy_err])

	var err := DirAccess.rename_absolute(tmp_path, _slot_path(slot))
	if err != OK:
		push_error("SaveSystem: rename failed for slot %d (error %d)" % [slot, err])
		save_completed.emit(slot, false)
		return false
	# Known accepted gap: a crash in the gap between this rename succeeding
	# and note_save_written() running desyncs the generation counter from
	# a save that really exists. Recording the generation bump BEFORE the
	# rename would trade this for a worse failure mode (a false "you erased
	# a save" accusation when nothing was ever saved), so the order stays
	# as-is; this window is a single function call wide.
	MetaPersistence.note_save_written(slot)
	save_completed.emit(slot, true)
	return true


func load_game(slot: int) -> bool:
	var payload: Variant = _load_valid(_slot_path(slot))
	if payload == null:
		payload = _load_valid(_bak_path(slot))
	if payload == null:
		load_completed.emit(slot, false)
		return false
	GameState.from_dict(payload)
	load_completed.emit(slot, true)
	return true


func delete_save(slot: int) -> void:
	for path in [_slot_path(slot), _bak_path(slot)]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(path)


func _slot_path(slot: int) -> String:
	return "%s/slot_%d.json" % [SAVE_DIR, slot]


func _bak_path(slot: int) -> String:
	return _slot_path(slot) + ".bak"


func _tmp_path(slot: int) -> String:
	return _slot_path(slot) + ".tmp"


## Returns the parsed PAYLOAD dictionary if the file is valid JSON, has the
## expected shape, and its checksum matches — else null. Never raises.
func _load_valid(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		return null
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if parsed is not Dictionary:
		return null
	var record: Dictionary = parsed
	if not (record.has("checksum") and record.has("payload") and record.has("version")):
		return null
	var payload_text: Variant = record["payload"]
	if payload_text is not String or payload_text.sha256_text() != record["checksum"]:
		return null
	var payload: Variant = JSON.parse_string(payload_text)
	if payload is not Dictionary:
		return null
	return _migrate(record["version"], payload)


## No migrations exist yet (CURRENT_VERSION has only ever been 1); future
## schema bumps add version-keyed transform steps here.
func _migrate(_version: Variant, payload: Dictionary) -> Dictionary:
	return payload
