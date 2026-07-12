extends GdUnitTestSuite
## DialogueParser: golden-output, malformed-input, and real-content tests.


func test_parses_basic_say_sequence() -> void:
	var text := "[scene demo]\nsay hoca demo.001\nsay ada demo.002 mood=tired\nend_scene\n"
	var parsed := DialogueParser.parse(text)

	assert_bool(parsed["ok"]).is_true()
	assert_str(parsed["scene_id"]).is_equal("demo")
	var instructions: Array = parsed["instructions"]
	assert_int(instructions.size()).is_equal(3)
	assert_str(instructions[0]["cmd"]).is_equal("say")
	assert_str(instructions[0]["actor_id"]).is_equal("hoca")
	assert_str(instructions[0]["key"]).is_equal("demo.001")
	assert_str(instructions[0]["mood"]).is_equal("")
	assert_str(instructions[1]["mood"]).is_equal("tired")
	assert_str(instructions[2]["cmd"]).is_equal("end_scene")


func test_strips_full_line_and_trailing_comments() -> void:
	var text := "# a comment\n[scene demo]\nwait 1.0   # trailing comment\n# another\nend_scene\n"
	var parsed := DialogueParser.parse(text)

	assert_bool(parsed["ok"]).is_true()
	assert_int(parsed["instructions"].size()).is_equal(2)
	assert_float(parsed["instructions"][0]["seconds"]).is_equal_approx(1.0, 0.0001)


func test_choice_resolves_option_targets_to_labels() -> void:
	var text := "\n".join([
		"[scene demo]",
		"choice",
		"  option demo.choice.a -> path_a",
		"  option demo.choice.b -> path_b",
		"label path_a",
		"say hoca demo.a",
		"jump done",
		"label path_b",
		"say hoca demo.b",
		"label done",
		"end_scene",
	])
	var parsed := DialogueParser.parse(text)

	assert_bool(parsed["ok"]).is_true()
	var labels: Dictionary = parsed["labels"]
	var instructions: Array = parsed["instructions"]
	var choice_instr: Dictionary = instructions[0]
	assert_str(choice_instr["cmd"]).is_equal("choice")
	assert_int(choice_instr["options"].size()).is_equal(2)
	assert_str(choice_instr["options"][0]["target_label"]).is_equal("path_a")
	assert_str(choice_instr["options"][1]["target_label"]).is_equal("path_b")
	assert_that(labels.has("path_a")).is_true()
	assert_that(labels.has("path_b")).is_true()
	assert_that(labels.has("done")).is_true()


func test_if_else_end_records_matching_indices() -> void:
	var text := "\n".join([
		"[scene demo]",
		"if some_flag",
		"say hoca demo.true",
		"else",
		"say hoca demo.false",
		"end",
		"end_scene",
	])
	var parsed := DialogueParser.parse(text)

	assert_bool(parsed["ok"]).is_true()
	var instructions: Array = parsed["instructions"]
	var if_instr: Dictionary = instructions[0]
	assert_str(if_instr["cmd"]).is_equal("if")
	assert_str(if_instr["flag"]).is_equal("some_flag")
	var else_idx: int = if_instr["else_index"]
	var end_idx: int = if_instr["end_index"]
	assert_str(instructions[else_idx]["cmd"]).is_equal("else")
	assert_str(instructions[end_idx]["cmd"]).is_equal("end")
	assert_int(instructions[else_idx]["end_index"]).is_equal(end_idx)


func test_setflag_coerces_bool_and_number_literals() -> void:
	var text := "\n".join([
		"[scene demo]", "setflag a true", "setflag b false", "setflag c 3", "setflag d hello",
		"end_scene",
	])
	var parsed := DialogueParser.parse(text)
	var instructions: Array = parsed["instructions"]

	assert_bool(instructions[0]["value"]).is_true()
	assert_bool(instructions[1]["value"]).is_false()
	assert_int(instructions[2]["value"]).is_equal(3)
	assert_str(instructions[3]["value"]).is_equal("hello")


func test_fails_on_missing_scene_header() -> void:
	var parsed := DialogueParser.parse("say hoca demo.001\n")
	assert_bool(parsed["ok"]).is_false()
	assert_str(parsed["error"]).contains("line 1")


func test_fails_on_unknown_command() -> void:
	var parsed := DialogueParser.parse("[scene demo]\nteleportt hoca somewhere\n")
	assert_bool(parsed["ok"]).is_false()
	assert_str(parsed["error"]).contains("line 2")
	assert_str(parsed["error"]).contains("unknown command")


func test_fails_on_unclosed_if() -> void:
	var parsed := DialogueParser.parse("[scene demo]\nif some_flag\nsay hoca demo.001\n")
	assert_bool(parsed["ok"]).is_false()
	assert_str(parsed["error"]).contains("never closed")


func test_fails_on_else_without_if() -> void:
	var parsed := DialogueParser.parse("[scene demo]\nelse\n")
	assert_bool(parsed["ok"]).is_false()
	assert_str(parsed["error"]).contains("'else' without a matching 'if'")


func test_fails_on_jump_to_undefined_label() -> void:
	var parsed := DialogueParser.parse("[scene demo]\njump nowhere\nend_scene\n")
	assert_bool(parsed["ok"]).is_false()
	assert_str(parsed["error"]).contains("undefined label")


func test_fails_on_option_missing_text_key() -> void:
	# Regression test: the arrow-position check used to only verify "->" was
	# second-to-last, so "option -> label" (no text_key at all) parsed
	# "successfully" with text_key wrongly set to the arrow itself.
	var parsed := DialogueParser.parse("[scene demo]\nchoice\n  option -> somewhere\nlabel somewhere\nend_scene\n")
	assert_bool(parsed["ok"]).is_false()


func test_fails_on_option_extra_token_before_arrow() -> void:
	var text := "[scene demo]\nchoice\n  option demo.001 extra -> somewhere\nlabel somewhere\nend_scene\n"
	var parsed := DialogueParser.parse(text)
	assert_bool(parsed["ok"]).is_false()


func test_fails_on_option_outside_choice() -> void:
	var parsed := DialogueParser.parse("[scene demo]\noption demo.001 -> somewhere\n")
	assert_bool(parsed["ok"]).is_false()
	assert_str(parsed["error"]).contains("outside a choice block")


func test_fails_on_duplicate_label() -> void:
	var text := "[scene demo]\nlabel a\nlabel a\nend_scene\n"
	var parsed := DialogueParser.parse(text)
	assert_bool(parsed["ok"]).is_false()
	assert_str(parsed["error"]).contains("duplicate label")


func test_parses_real_act1_scene_file() -> void:
	var path := "res://story/scripts/act1/d2_observatory.scene"
	assert_bool(FileAccess.file_exists(path)).is_true()
	var text := FileAccess.get_file_as_string(path)
	var parsed := DialogueParser.parse(text)

	assert_bool(parsed["ok"]).is_true()
	assert_str(parsed["scene_id"]).is_equal("d2_observatory")
	assert_that(parsed["instructions"].size() > 0).is_true()


func test_all_24_act1_scene_files_parse_cleanly() -> void:
	var dir := DirAccess.open("res://story/scripts/act1")
	assert_object(dir).is_not_null()
	dir.list_dir_begin()
	var file_name := dir.get_next()
	var checked := 0
	while file_name != "":
		if file_name.ends_with(".scene"):
			var text := FileAccess.get_file_as_string("res://story/scripts/act1/" + file_name)
			var parsed := DialogueParser.parse(text)
			assert_bool(parsed["ok"]).override_failure_message(
				"%s: %s" % [file_name, parsed.get("error", "")]
			).is_true()
			checked += 1
		file_name = dir.get_next()
	assert_int(checked).is_equal(24)
