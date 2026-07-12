class_name WaterfallCanvas
extends Control
## Procedural scrolling spectrogram for the waterfall minigame (M3 v1).
## Y = frequency across the session's configured range (higher = up,
## matching a real waterfall display); X = time, scrolling left as new
## columns arrive. No art-pipeline assets — this is live data
## visualization, generated the same way a real instrument's plot would be,
## so it sits outside artgen/canvas.py's palette enforcement entirely.
##
## The background is deterministic seeded speckle noise (PLAN M3: "authored
## curves drawn into seeded noise") — hash01() is a pure integer mix, so the
## same seed + column sequence always renders identical noise (unit-tested;
## no RandomNumberGenerator state to leak between sessions).
##
## Colors are still drawn from the master palette (artgen/palettes/the_above.json)
## for consistency: signal-magenta is reserved for the trace itself — and for
## event bursts, which ARE the signal (broadband smears of it) — exactly the
## "forbidden" color's documented purpose (plan section 2's signal grammar).
## Never used decoratively here.

const MAX_COLUMNS := 96
const NO_HIT := -1.0
const NOISE_ROW_STEP := 3
const NOISE_DENSITY := 0.08
const BURST_BAND_RATIO := 0.45

const NOISE_COLOR := Color("2e2a3e")     # palette: stone[0]
const SPECKLE_COLOR := Color("4a4460")   # palette: stone[1]
const CURSOR_COLOR := Color("3ee68a")    # palette: crt[0]
const SIGNAL_COLOR := Color("ff2fd6")    # palette: forbidden.signal
const TARGET_COLOR := Color("786f5c")    # palette: paper[0]

var _columns: Array[float] = []
## Parallel to _columns: the burst's anchor row (0..1) frozen at push time,
## or NO_HIT for non-burst columns. Anchoring at push time keeps recorded
## history immutable under a drifting target — the whole premise of a
## scrolling waterfall is that what was drawn stays where it was drawn.
var _burst_rows: Array[float] = []
var _columns_pushed := 0
var _noise_seed := 0
var _cursor_ratio := 0.5
var _target_ratio := 0.5


func _ready() -> void:
	# Bursts span 45% of the plot height; without clipping, a burst anchored
	# near a range edge would smear signal-magenta over the labels below.
	clip_contents = true


func reset(noise_seed: int = 0) -> void:
	_columns.clear()
	_burst_rows.clear()
	_columns_pushed = 0
	_noise_seed = noise_seed
	_cursor_ratio = 0.5
	queue_redraw()


func set_target_ratio(ratio: float) -> void:
	if is_equal_approx(_target_ratio, ratio):
		return
	_target_ratio = ratio
	queue_redraw()


## Appends one time-step of the scrolling history. `freq_ratio` places the
## hit (or the live cursor, regardless of hit) at its 0..1 row. `burst`
## marks an event column — rendered as a broadband smear anchored to the
## target row AS OF THIS PUSH (frozen, like trace cells freeze freq_ratio).
func push_column(has_signal: bool, freq_ratio: float, burst: bool = false) -> void:
	_columns.append(freq_ratio if has_signal else NO_HIT)
	_burst_rows.append(_target_ratio if burst else NO_HIT)
	if _columns.size() > MAX_COLUMNS:
		_columns.pop_front()
		_burst_rows.pop_front()
	_columns_pushed += 1
	_cursor_ratio = freq_ratio
	queue_redraw()


## Deterministic 0..1 hash of an (x, y, seed) triple — integer mixing only,
## no RNG object. Same inputs always give the same output on every platform,
## which is what makes the noise field seedable and testable.
static func hash01(x: int, y: int, seed_value: int) -> float:
	var h := x * 374761393 + y * 668265263 + seed_value * 2147483647
	h = (h ^ (h >> 13)) * 1274126177
	h = h ^ (h >> 16)
	return float(h & 0xFFFF) / 65535.0


func _draw() -> void:
	var size := get_size()
	if size.x <= 0.0 or size.y <= 0.0:
		return
	draw_rect(Rect2(Vector2.ZERO, size), NOISE_COLOR)

	var column_width := size.x / float(MAX_COLUMNS)

	# Seeded background speckle, keyed to each column's ABSOLUTE index so
	# the noise scrolls left in lockstep with the trace history.
	var first_abs_index := _columns_pushed - _columns.size()
	for i in _columns.size():
		var abs_index := first_abs_index + i
		var x := size.x - (_columns.size() - i) * column_width
		var row := 0
		while row * NOISE_ROW_STEP < int(size.y):
			if hash01(abs_index, row, _noise_seed) < NOISE_DENSITY:
				draw_rect(
					Rect2(Vector2(x, row * NOISE_ROW_STEP), Vector2(column_width, 1.0)),
					SPECKLE_COLOR
				)
			row += 1

	var target_y := (1.0 - _target_ratio) * size.y
	draw_line(Vector2(0.0, target_y), Vector2(size.x, target_y), TARGET_COLOR, 1.0)

	var burst_half := size.y * BURST_BAND_RATIO * 0.5
	for i in _columns.size():
		var x2 := size.x - (_columns.size() - i) * column_width
		if _burst_rows[i] >= 0.0:
			# Broadband event: a tall smear centered on the signal's row as
			# recorded at push time — visible whatever the player is tuned
			# to, like a real burst, and frozen in history like everything
			# else on the plot.
			var burst_y := (1.0 - _burst_rows[i]) * size.y
			draw_rect(
				Rect2(Vector2(x2, burst_y - burst_half), Vector2(column_width, burst_half * 2.0)),
				SIGNAL_COLOR
			)
			continue
		var freq_ratio: float = _columns[i]
		if freq_ratio < 0.0:
			continue
		var y := (1.0 - freq_ratio) * size.y
		draw_rect(Rect2(Vector2(x2, y - 1.0), Vector2(column_width, 3.0)), SIGNAL_COLOR)

	var cursor_y := (1.0 - _cursor_ratio) * size.y
	draw_line(Vector2(0.0, cursor_y), Vector2(size.x, cursor_y), CURSOR_COLOR, 1.0)
