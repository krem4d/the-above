extends GdUnitTestSuite
## DialogueRunner._step(): instruction-pointer stepping for the non-UI
## commands (if/else/end/setflag/jump/label). say/choice need DialogueBox/
## ChoiceMenu and are covered by the e2e tour scene instead of here.
## Regression coverage for a CONFIRMED critical bug: comparing a flag's
## Variant value with `== true` throws for any non-bool flag (setflag
## explicitly allows int/float/string) and silently resets the whole
## scene to instruction 0 instead of raising.

func after_test() -> void:
	GameState.reset_new_game()


func test_if_true_bool_flag_falls_through() -> void:
	GameState.set_flag("flag_a", true)
	var instructions: Array = [
		{"cmd": "if", "line": 1, "flag": "flag_a", "else_index": 2, "end_index": 3},
		{"cmd": "label", "line": 2, "name": "unused"},
		{"cmd": "else", "line": 3, "end_index": 3},
		{"cmd": "end", "line": 4},
	]
	var next_ip: int = await DialogueRunner._step(0, instructions, {})
	assert_int(next_ip).is_equal(1)   # falls into the true-branch body


func test_if_false_bool_flag_jumps_to_else() -> void:
	GameState.set_flag("flag_b", false)
	var instructions: Array = [
		{"cmd": "if", "line": 1, "flag": "flag_b", "else_index": 2, "end_index": 3},
	]
	var next_ip: int = await DialogueRunner._step(0, instructions, {})
	assert_int(next_ip).is_equal(3)   # else_index + 1


func test_if_unset_flag_is_falsy() -> void:
	var instructions: Array = [
		{"cmd": "if", "line": 1, "flag": "never_set", "else_index": -1, "end_index": 2},
	]
	var next_ip: int = await DialogueRunner._step(0, instructions, {})
	assert_int(next_ip).is_equal(3)   # end_index + 1 (no else)


func test_if_with_int_flag_does_not_crash_and_is_truthy() -> void:
	# Regression test: this exact scenario used to throw "Invalid operands
	# 'int' and 'bool' in operator '=='" and silently return ip=0.
	GameState.set_flag("counter", 3)
	var instructions: Array = [
		{"cmd": "if", "line": 1, "flag": "counter", "else_index": -1, "end_index": 5},
	]
	var next_ip: int = await DialogueRunner._step(0, instructions, {})
	assert_int(next_ip).is_equal(1)   # truthy (non-zero int) -> falls through


func test_if_with_zero_int_flag_is_falsy() -> void:
	GameState.set_flag("counter_zero", 0)
	var instructions: Array = [
		{"cmd": "if", "line": 1, "flag": "counter_zero", "else_index": -1, "end_index": 4},
	]
	var next_ip: int = await DialogueRunner._step(0, instructions, {})
	assert_int(next_ip).is_equal(5)


func test_if_with_string_flag_does_not_crash() -> void:
	GameState.set_flag("named_thing", "hello")
	var instructions: Array = [
		{"cmd": "if", "line": 1, "flag": "named_thing", "else_index": -1, "end_index": 3},
	]
	var next_ip: int = await DialogueRunner._step(0, instructions, {})
	assert_int(next_ip).is_equal(1)


func test_else_after_true_branch_skips_to_end_plus_one() -> void:
	var instructions: Array = [{"cmd": "else", "line": 1, "end_index": 7}]
	var next_ip: int = await DialogueRunner._step(0, instructions, {})
	assert_int(next_ip).is_equal(8)


func test_setflag_writes_through_to_gamestate() -> void:
	var instructions: Array = [{"cmd": "setflag", "line": 1, "name": "written", "value": 42}]
	await DialogueRunner._step(0, instructions, {})
	assert_int(GameState.get_flag("written")).is_equal(42)


func test_jump_moves_to_label_index() -> void:
	var instructions: Array = [{"cmd": "jump", "line": 1, "arg": "target"}]
	var next_ip: int = await DialogueRunner._step(0, instructions, {"target": 9})
	assert_int(next_ip).is_equal(9)


func test_end_scene_terminates_at_array_size() -> void:
	var instructions: Array = [{"cmd": "end_scene", "line": 1}, {"cmd": "label", "line": 2, "name": "x"}]
	var next_ip: int = await DialogueRunner._step(0, instructions, {})
	assert_int(next_ip).is_equal(2)   # instructions.size(), loop terminates
