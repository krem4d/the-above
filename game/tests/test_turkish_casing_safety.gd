extends GdUnitTestSuite
## Static grep-test (plan section 5): GDScript's to_upper()/to_lower()/
## capitalize() are locale-blind and mangle İ/ı. Player-facing text must be
## authored pre-cased in the locale CSVs, never case-transformed at runtime.
## Fails the build the moment such a call is (re-)introduced anywhere in
## game/scripts or game/scenes.

const BANNED := [".to_upper()", ".to_lower()", ".capitalize()"]
const SCAN_ROOTS := ["res://scripts", "res://scenes"]


func test_no_runtime_case_transforms_in_source() -> void:
	var offenders: Array[String] = []
	for root in SCAN_ROOTS:
		_scan_dir(root, offenders)
	assert_bool(offenders.is_empty()).override_failure_message(
		"Turkish casing violations found:\n" + "\n".join(offenders)
	).is_true()


func _scan_dir(path: String, offenders: Array[String]) -> void:
	var dir := DirAccess.open(path)
	if dir == null:
		return
	dir.list_dir_begin()
	var entry := dir.get_next()
	while entry != "":
		var full_path := path.path_join(entry)
		if dir.current_is_dir():
			_scan_dir(full_path, offenders)
		elif entry.ends_with(".gd"):
			_scan_file(full_path, offenders)
		entry = dir.get_next()


func _scan_file(path: String, offenders: Array[String]) -> void:
	var text := FileAccess.get_file_as_string(path)
	var lines := text.split("\n")
	for i in lines.size():
		for pattern in BANNED:
			if lines[i].contains(pattern):
				offenders.append("%s:%d: %s" % [path, i + 1, lines[i].strip_edges()])
