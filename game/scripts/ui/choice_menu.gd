class_name ChoiceMenu
extends Control
## Vertical choice list with a blinking signal-dot cursor. Presentational:
## present() shows the options, `chosen` fires with the selected index.
## Navigation wraps; interact confirms; cancel is deliberately ignored —
## design rule 1: choices can never be backed out of, only made.

signal chosen(index: int)

const CURSOR := "• "
const CURSOR_PAD := "  "

@onready var _list: VBoxContainer = %OptionList

var _labels: Array[Label] = []
var _selected := 0


func _ready() -> void:
	visible = false


func present(options: Array[String]) -> void:
	for label in _labels:
		label.queue_free()
	_labels.clear()
	for option_text in options:
		var label := Label.new()
		label.text = CURSOR_PAD + option_text
		label.add_theme_color_override("font_color", Color("b0a890"))
		_list.add_child(label)
		_labels.append(label)
	_selected = 0
	_apply_selection()
	visible = true


func _apply_selection() -> void:
	for i in _labels.size():
		var label := _labels[i]
		var bare := label.text.trim_prefix(CURSOR).trim_prefix(CURSOR_PAD)
		if i == _selected:
			label.text = CURSOR + bare
			label.add_theme_color_override("font_color", Color("f9dfa6"))
		else:
			label.text = CURSOR_PAD + bare
			label.add_theme_color_override("font_color", Color("b0a890"))


func _unhandled_input(event: InputEvent) -> void:
	if not visible or _labels.is_empty():
		return
	if event.is_action_pressed("move_down"):
		get_viewport().set_input_as_handled()
		_selected = (_selected + 1) % _labels.size()
		_apply_selection()
	elif event.is_action_pressed("move_up"):
		get_viewport().set_input_as_handled()
		_selected = (_selected - 1 + _labels.size()) % _labels.size()
		_apply_selection()
	elif event.is_action_pressed("interact"):
		get_viewport().set_input_as_handled()
		visible = false
		chosen.emit(_selected)
