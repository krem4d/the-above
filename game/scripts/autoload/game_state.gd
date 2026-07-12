extends Node
## Autoload: typed story flags, day counter, observer name (plan section 5).
## Second in the autoload order. Pure state — no file I/O; SaveSystem reads
## to_dict()/from_dict() to persist and restore it.

signal flag_changed(flag_name: String, value: Variant)
signal day_changed(day: int)

const NEW_GAME_DAY := 1

var day: int = NEW_GAME_DAY
var observer_name: String = ""
var current_room_id: String = ""

var _flags: Dictionary = {}


func set_flag(flag_name: String, value: Variant = true) -> void:
	var current: Variant = _flags.get(flag_name)
	# typeof() guard first: GDScript's == throws a runtime type error across
	# incompatible Variant types (e.g. bool vs int), which setflag's value
	# coercion can easily produce if a flag name is reused with a new kind
	# of value across scenes. Different types are trivially "not equal".
	if typeof(current) == typeof(value) and current == value:
		return
	_flags[flag_name] = value
	flag_changed.emit(flag_name, value)


func get_flag(flag_name: String, default: Variant = false) -> Variant:
	return _flags.get(flag_name, default)


func has_flag(flag_name: String) -> bool:
	return _flags.has(flag_name)


func advance_day() -> void:
	day += 1
	day_changed.emit(day)


func reset_new_game() -> void:
	day = NEW_GAME_DAY
	observer_name = ""
	current_room_id = ""
	_flags.clear()


func to_dict() -> Dictionary:
	return {
		"day": day,
		"observer_name": observer_name,
		"current_room_id": current_room_id,
		"flags": _flags.duplicate(true),
	}


func from_dict(data: Dictionary) -> void:
	day = data.get("day", NEW_GAME_DAY)
	observer_name = data.get("observer_name", "")
	current_room_id = data.get("current_room_id", "")
	# Known accepted gap: an int-valued flag saved via SaveSystem can come
	# back as a float after the JSON round-trip (Godot's parser does not
	# reliably preserve the int/float distinction). Harmless today — no
	# flag is ever compared with strict typeof() checks, and GDScript's ==
	# safely compares int/float (unlike bool vs int/float/String, which
	# throws) — but would need real fixing if that ever changes.
	_flags = (data.get("flags", {}) as Dictionary).duplicate(true)
