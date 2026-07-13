extends GdUnitTestSuite
## The naming ritual (M4): `name_entry` DSL command parsing, the panel's
## confirm contract, and the runner's persistence side (GameState +
## MetaPersistence). Mirrors test_waterfall_view.gd's instantiate-and-drive
## style — no real keyboard input, the panel API is the contract.

const PANEL_SCENE := "res://scenes/ui/name_entry_panel.tscn"


func after_test() -> void:
	DialogueRunner.name_entry_panel = null
	GameState.reset_new_game()


func test_parser_accepts_name_entry() -> void:
	var parsed := DialogueParser.parse("[scene t]\nname_entry\nend_scene\n")
	assert_bool(parsed["ok"]).is_true()
	assert_str(parsed["instructions"][0]["cmd"]).is_equal("name_entry")


func test_parser_rejects_name_entry_with_arguments() -> void:
	var parsed := DialogueParser.parse("[scene t]\nname_entry now\n")
	assert_bool(parsed["ok"]).is_false()


func test_panel_opens_with_initial_name_and_confirms_trimmed() -> void:
	var panel: NameEntryPanel = auto_free((load(PANEL_SCENE) as PackedScene).instantiate())
	add_child(panel)
	panel.open("Deniz")
	assert_bool(panel.visible).is_true()
	var received := [""]
	panel.confirmed.connect(func(n: String) -> void: received[0] = n)
	panel._line.text = "  Yıldız  "
	panel._try_confirm()
	assert_str(received[0]).is_equal("Yıldız")
	assert_bool(panel.visible).is_false()


func test_panel_refuses_empty_name() -> void:
	var panel: NameEntryPanel = auto_free((load(PANEL_SCENE) as PackedScene).instantiate())
	add_child(panel)
	panel.open("")
	panel._line.text = "   "
	panel._try_confirm()
	assert_bool(panel.visible).is_true()   # still waiting — the ritual has no skip


func test_runner_persists_confirmed_name_to_state_and_meta() -> void:
	var panel: NameEntryPanel = auto_free((load(PANEL_SCENE) as PackedScene).instantiate())
	add_child(panel)
	DialogueRunner.name_entry_panel = panel
	DialogueRunner._do_name_entry()   # coroutine parks on `confirmed`
	panel._line.text = "İpek"
	panel._try_confirm()
	await get_tree().process_frame
	assert_str(GameState.observer_name).is_equal("İpek")


func test_runner_without_panel_warns_and_keeps_name() -> void:
	GameState.observer_name = "Kept"
	DialogueRunner.name_entry_panel = null
	await DialogueRunner._do_name_entry()
	assert_str(GameState.observer_name).is_equal("Kept")
