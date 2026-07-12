class_name WaterfallCanvas
extends Control
## Procedural scrolling spectrogram for the waterfall minigame (M3 v1).
## Y = frequency across the session's configured range (higher = up,
## matching a real waterfall display); X = time, scrolling left as new
## columns arrive. No art-pipeline assets — this is live data
## visualization, generated the same way a real instrument's plot would be,
## so it sits outside artgen/canvas.py's palette enforcement entirely.
##
## Colors are still drawn from the master palette (artgen/palettes/the_above.json)
## for consistency: signal-magenta is reserved for the trace itself, exactly
## the "forbidden" color's documented purpose (plan section 2's signal
## grammar) — never used decoratively here.

const MAX_COLUMNS := 96
const NO_HIT := -1.0

const NOISE_COLOR := Color("2e2a3e")    # palette: stone[0]
const CURSOR_COLOR := Color("3ee68a")   # palette: crt[0]
const SIGNAL_COLOR := Color("ff2fd6")   # palette: forbidden.signal
const TARGET_COLOR := Color("786f5c")   # palette: paper[0]

var _columns: Array[float] = []
var _cursor_ratio: float = 0.5
var _target_ratio: float = 0.5


func reset() -> void:
	_columns.clear()
	_cursor_ratio = 0.5
	queue_redraw()


func set_target_ratio(ratio: float) -> void:
	_target_ratio = ratio
	queue_redraw()


## Appends one time-step of the scrolling history. `freq_ratio` places the
## hit (or the live cursor, regardless of hit) at its 0..1 row.
func push_column(has_signal: bool, freq_ratio: float) -> void:
	_columns.append(freq_ratio if has_signal else NO_HIT)
	if _columns.size() > MAX_COLUMNS:
		_columns.pop_front()
	_cursor_ratio = freq_ratio
	queue_redraw()


func _draw() -> void:
	var size := get_size()
	if size.x <= 0.0 or size.y <= 0.0:
		return
	draw_rect(Rect2(Vector2.ZERO, size), NOISE_COLOR)

	var target_y := (1.0 - _target_ratio) * size.y
	draw_line(Vector2(0.0, target_y), Vector2(size.x, target_y), TARGET_COLOR, 1.0)

	var column_width := size.x / float(MAX_COLUMNS)
	for i in _columns.size():
		var freq_ratio: float = _columns[i]
		if freq_ratio < 0.0:
			continue
		var x := size.x - (_columns.size() - i) * column_width
		var y := (1.0 - freq_ratio) * size.y
		draw_rect(Rect2(Vector2(x, y - 1.0), Vector2(column_width, 3.0)), SIGNAL_COLOR)

	var cursor_y := (1.0 - _cursor_ratio) * size.y
	draw_line(Vector2(0.0, cursor_y), Vector2(size.x, cursor_y), CURSOR_COLOR, 1.0)
