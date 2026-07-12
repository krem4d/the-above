extends GdUnitTestSuite
## Harness smoke test — proves the GdUnit4 CLI pipeline runs (make test).


func test_project_boots_with_pinned_settings() -> void:
	# Arrange / Act
	var stretch_mode: String = ProjectSettings.get_setting("display/window/stretch/mode")
	var filter_mode: int = ProjectSettings.get_setting(
		"rendering/textures/canvas_textures/default_texture_filter"
	)

	# Assert — the two settings pixel crispness depends on (plan section 5)
	assert_str(stretch_mode).is_equal("viewport")
	assert_int(filter_mode).is_equal(0)
