extends GdUnitTestSuite
## MetaPersistence: shadow-copy resurrection + save-deletion detection.
## Manipulates the real meta.json/shadow files directly (test runs are
## isolated via `make test`'s --user-data-dir, so this never touches a
## real player's meta) and calls reload() to simulate a fresh boot.

const TEST_SLOT := 902


func before_test() -> void:
	SaveSystem.delete_save(TEST_SLOT)


func after_test() -> void:
	SaveSystem.delete_save(TEST_SLOT)
	MetaPersistence.reload()   # restore real on-disk state for later tests


func test_record_observer_name_persists_across_reload() -> void:
	MetaPersistence.record_observer_name("Deniz Aydın")
	MetaPersistence.reload()
	assert_bool(MetaPersistence.observer_names_used.has("Deniz Aydın")).is_true()


func test_note_save_written_increments_generation() -> void:
	var before_count: int = MetaPersistence.save_generations.get(str(TEST_SLOT), 0)
	MetaPersistence.note_save_written(TEST_SLOT)
	assert_int(MetaPersistence.save_generations[str(TEST_SLOT)]).is_equal(before_count + 1)


func test_detects_deleted_save_via_generation_mismatch() -> void:
	SaveSystem.save_game(TEST_SLOT)
	assert_bool(MetaPersistence.has_higher_generation_than_save(TEST_SLOT)).is_false()

	SaveSystem.delete_save(TEST_SLOT)
	assert_bool(MetaPersistence.has_higher_generation_than_save(TEST_SLOT)).is_true()


func test_shadow_copy_resurrects_a_missing_meta_file() -> void:
	MetaPersistence.record_observer_name("Shadow Witness")
	assert_bool(FileAccess.file_exists(MetaPersistence.META_PATH)).is_true()
	assert_bool(FileAccess.file_exists(MetaPersistence.SHADOW_PATH)).is_true()

	DirAccess.remove_absolute(MetaPersistence.META_PATH)
	assert_bool(FileAccess.file_exists(MetaPersistence.META_PATH)).is_false()

	MetaPersistence.reload()
	assert_bool(MetaPersistence.player_tried_to_erase).is_true()
	assert_bool(MetaPersistence.observer_names_used.has("Shadow Witness")).is_true()
	# reload() heals the missing file from the shadow immediately.
	assert_bool(FileAccess.file_exists(MetaPersistence.META_PATH)).is_true()

	# Regression test: player_tried_to_erase used to only ever get set to
	# true, never reset — a second, clean reload() must clear it back down.
	MetaPersistence.reload()
	assert_bool(MetaPersistence.player_tried_to_erase).is_false()


func test_deleting_both_files_wins_and_resets_cleanly() -> void:
	MetaPersistence.record_observer_name("Erased Name")
	DirAccess.remove_absolute(MetaPersistence.META_PATH)
	DirAccess.remove_absolute(MetaPersistence.SHADOW_PATH)

	MetaPersistence.reload()
	assert_bool(MetaPersistence.player_tried_to_erase).is_false()
	assert_bool(MetaPersistence.observer_names_used.is_empty()).is_true()
