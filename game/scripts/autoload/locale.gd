extends Node
## Autoload: EN/TR translation lookup + named-placeholder formatting.
## Wraps Godot's built-in TranslationServer over the CSV-imported
## act1_dialogue/ui .translation resources (plan section 5).
##
## First in the autoload order — boots with DEFAULT_LANG. MetaPersistence
## (loaded later) calls set_language() once the saved preference is known.

signal language_changed(lang: String)

const DEFAULT_LANG := "en"
const SUPPORTED_LANGS := ["en", "tr"]

var _lang: String = DEFAULT_LANG


func _ready() -> void:
	TranslationServer.set_locale(DEFAULT_LANG)


func set_language(lang: String) -> void:
	if lang not in SUPPORTED_LANGS:
		push_warning("Locale: unsupported language '%s'" % lang)
		return
	_lang = lang
	TranslationServer.set_locale(lang)
	language_changed.emit(lang)


func get_language() -> String:
	return _lang


## Translate `key` and substitute named {placeholder} tokens from `params`.
## Missing keys return Godot's own tr() fallback (the key itself) — the
## localization-completeness test suite is what actually guards against
## missing keys ever shipping, not a runtime fallback here.
func t(key: String, params: Dictionary = {}) -> String:
	var template := tr(key)
	if params.is_empty():
		return template
	return template.format(params)
