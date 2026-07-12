class_name DialogueBox
extends Control
## Undertale-style dialogue textbox: typewriter reveal, optional speaker name
## and portrait, blinking advance indicator. Purely presentational — the
## DialogueRunner (M2) drives it and awaits its signals.

signal line_finished        ## typewriter reached the end of the current line
signal advance_requested    ## player pressed interact on a completed line

const CHARS_PER_SECOND := 40.0
const INDICATOR_BLINK_SECONDS := 0.4

@onready var _name_label: Label = %NameLabel
@onready var _text_label: RichTextLabel = %TextLabel
@onready var _portrait: TextureRect = %Portrait
@onready var _indicator: Label = %AdvanceIndicator

var _typing := false
var _reveal_accumulator := 0.0
var _blink_accumulator := 0.0


func _ready() -> void:
	visible = false
	_indicator.visible = false


func show_line(text: String, speaker: String = "", portrait: Texture2D = null) -> void:
	visible = true
	_name_label.text = speaker
	_name_label.visible = speaker != ""
	_portrait.texture = portrait
	_portrait.visible = portrait != null
	_text_label.text = text
	_text_label.visible_characters = 0
	_reveal_accumulator = 0.0
	_indicator.visible = false
	_typing = true


func skip_to_end() -> void:
	if not _typing:
		return
	_text_label.visible_characters = -1
	_finish_typing()


func is_typing() -> bool:
	return _typing


func hide_box() -> void:
	visible = false
	_typing = false


func _process(delta: float) -> void:
	if _typing:
		_reveal_accumulator += delta * CHARS_PER_SECOND
		var target := int(_reveal_accumulator)
		if target >= _text_label.get_total_character_count():
			_text_label.visible_characters = -1
			_finish_typing()
		else:
			_text_label.visible_characters = target
	elif visible:
		_blink_accumulator += delta
		if _blink_accumulator >= INDICATOR_BLINK_SECONDS:
			_blink_accumulator = 0.0
			_indicator.visible = not _indicator.visible


func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if event.is_action_pressed("interact"):
		get_viewport().set_input_as_handled()
		if _typing:
			skip_to_end()
		else:
			advance_requested.emit()


func _finish_typing() -> void:
	_typing = false
	_blink_accumulator = 0.0
	_indicator.visible = true
	line_finished.emit()
