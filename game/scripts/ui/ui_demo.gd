extends Node2D
## Tour-only demo driver for DialogueBox/ChoiceMenu visual verification.
## Not shipped gameplay: each demo scene sets `variant` and _ready stages a
## deterministic frame (typewriter skipped) for the screenshot harness.
## The TR line is the M2 localization gate: ğ ü ş ı ö ç İ I must render.

@export_enum("dialogue_en", "dialogue_tr", "choice") var variant := "dialogue_en"

@onready var _dialogue: DialogueBox = %DemoDialogueBox
@onready var _choices: ChoiceMenu = %DemoChoiceMenu


func _ready() -> void:
	var portrait := _placeholder_portrait()
	match variant:
		"dialogue_en":
			_dialogue.show_line(
				"Same interval, same drift. You could set a clock by it. Noise doesn't keep appointments.",
				"Deniz"
			)
			_dialogue.skip_to_end()
		"dialogue_tr":
			_dialogue.show_line(
				"Taşlıca'da her şey yerli yerinde. Çanağı gördüm; ışığı söndürülmüş, İĞŞ ığş — gözlemevi yine çağırıyor.",
				"Deniz",
				portrait
			)
			_dialogue.skip_to_end()
		"choice":
			_dialogue.show_line("Dün gece kaydı sen de dinledin mi?", "Ada")
			_dialogue.skip_to_end()
			var options: Array[String] = ["Duydum. Sen de duydun.", "Bir şey duymadım.", "..."]
			_choices.present(options)


func _placeholder_portrait() -> Texture2D:
	var atlas := AtlasTexture.new()
	atlas.atlas = load("res://assets/gen/sprites/hoca_sheet.png")
	atlas.region = Rect2(0, 144, 32, 48)
	return atlas
