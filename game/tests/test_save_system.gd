extends GdUnitTestSuite
## SaveSystem: round-trip, checksum-corruption fallback, .bak recovery.
## Uses high slot numbers (900+) reserved for tests so a real playthrough's
## slots 1-3 are never touched even if --user-data-dir isolation is bypassed.

const TEST_SLOT := 901


func before_test() -> void:
	SaveSystem.delete_save(TEST_SLOT)
	GameState.reset_new_game()


func after_test() -> void:
	SaveSystem.delete_save(TEST_SLOT)
	GameState.reset_new_game()


func test_save_then_load_round_trip() -> void:
	GameState.day = 5
	GameState.observer_name = "Test Observer"
	GameState.set_flag("wrong_note_seen", true)

	assert_bool(SaveSystem.save_game(TEST_SLOT)).is_true()
	assert_bool(SaveSystem.save_exists(TEST_SLOT)).is_true()

	GameState.reset_new_game()
	assert_bool(SaveSystem.load_game(TEST_SLOT)).is_true()
	assert_int(GameState.day).is_equal(5)
	assert_str(GameState.observer_name).is_equal("Test Observer")
	assert_bool(GameState.get_flag("wrong_note_seen")).is_true()


func test_load_missing_slot_returns_false() -> void:
	assert_bool(SaveSystem.load_game(TEST_SLOT)).is_false()


func test_corrupted_slot_falls_back_to_backup() -> void:
	GameState.day = 2
	SaveSystem.save_game(TEST_SLOT)   # writes slot, no .bak yet (first write)
	GameState.day = 3
	SaveSystem.save_game(TEST_SLOT)   # this write backs up the day=2 slot to .bak

	var slot_path := "user://saves/slot_%d.json" % TEST_SLOT
	var file := FileAccess.open(slot_path, FileAccess.WRITE)
	file.store_string("{ this is not valid json")
	file.close()

	GameState.reset_new_game()
	assert_bool(SaveSystem.load_game(TEST_SLOT)).is_true()
	assert_int(GameState.day).is_equal(2)   # recovered from .bak, not the corrupted slot


func test_corrupted_slot_and_missing_backup_fails_cleanly() -> void:
	GameState.day = 9
	SaveSystem.save_game(TEST_SLOT)

	var slot_path := "user://saves/slot_%d.json" % TEST_SLOT
	var file := FileAccess.open(slot_path, FileAccess.WRITE)
	file.store_string("not json at all")
	file.close()

	GameState.reset_new_game()
	assert_bool(SaveSystem.load_game(TEST_SLOT)).is_false()
	assert_int(GameState.day).is_equal(1)   # GameState untouched, caller starts a new game
