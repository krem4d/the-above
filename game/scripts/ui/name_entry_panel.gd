class_name NameEntryPanel
extends Control
## The naming ritual's input panel (M4; bible D1-S3): the observatory
## logbook terminal prompts OBSERVER: and waits for a typed name. Modal,
## mandatory (there is no cancel — the ritual is the point), max 12 chars.
## Purely presentational like DialogueBox: DialogueRunner opens it and
## awaits `confirmed`; persistence (GameState/MetaPersistence) is the
## runner's job. Turkish input arrives as typed — no case transforms here,
## ever (İ/ı safety; the grep-test watches this file too).

signal confirmed(observer_name: String)

const MAX_NAME_LENGTH := 12

@onready var _prompt: Label = %PromptLabel
@onready var _line: LineEdit = %NameLine
@onready var _confirm: Button = %ConfirmButton


func _ready() -> void:
	visible = false
	_line.max_length = MAX_NAME_LENGTH
	_line.text_submitted.connect(_on_text_submitted)
	_confirm.pressed.connect(_try_confirm)


func open(initial_name: String = "") -> void:
	_prompt.text = Locale.t("name.prompt")
	_confirm.text = Locale.t("name.confirm")
	_line.text = initial_name
	visible = true
	_line.grab_focus()
	_line.caret_column = _line.text.length()


func _on_text_submitted(_text: String) -> void:
	_try_confirm()


func _try_confirm() -> void:
	var typed := _line.text.strip_edges()
	if typed == "":
		# An empty log entry is not a name; keep the terminal waiting.
		_line.grab_focus()
		return
	visible = false
	confirmed.emit(typed)
