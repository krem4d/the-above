extends GdUnitTestSuite
## Locale: EN/TR switching + named-placeholder substitution.


func after_test() -> void:
	Locale.set_language("en")   # never leak language state into later tests


func test_translates_default_english() -> void:
	assert_str(Locale.t("ui.menu.quit")).is_equal("QUIT")


func test_switches_to_turkish_and_back() -> void:
	Locale.set_language("tr")
	assert_str(Locale.get_language()).is_equal("tr")
	assert_str(Locale.t("ui.menu.quit")).is_equal("ÇIK")
	Locale.set_language("en")
	assert_str(Locale.t("ui.menu.quit")).is_equal("QUIT")


func test_placeholder_substitution() -> void:
	assert_str(Locale.t("ui.hud.day_counter", {"day": 3})).is_equal("DAY 3")


func test_rejects_unsupported_language() -> void:
	Locale.set_language("fr")
	assert_str(Locale.get_language()).is_equal("en")
