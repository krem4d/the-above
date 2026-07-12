extends GdUnitTestSuite
## WaterfallCanvas: seeded-noise determinism (PLAN M3's spectro-model
## determinism requirement) and column-history state. Headless-safe — state
## methods and the pure static hash only, never a rendered frame.


## Real seeds come from session_id.hash() (uint32 range, e.g.
## "sig_long_call".hash() == 4034537810) — with large x these drive hash01's
## stage-1 sum through int64 wraparound and negative-operand >>, semantics
## the runtime permits but the parser rejects when constant-folded. Pin them
## on the ADR-pinned engine so an engine bump that changes them fails loudly.
const PRODUCTION_RANGE_SEEDS := [0, 12345, 4034537810, 4294967295]


func test_hash01_is_deterministic() -> void:
	for seed_value: int in PRODUCTION_RANGE_SEEDS:
		for x in [0, 1, 17, 4096, 9223372036]:
			for y in [0, 3, 51]:
				var a := WaterfallCanvas.hash01(x, y, seed_value)
				var b := WaterfallCanvas.hash01(x, y, seed_value)
				assert_float(a).is_equal_approx(b, 0.0)


func test_hash01_output_stays_in_unit_range() -> void:
	for seed_value: int in PRODUCTION_RANGE_SEEDS:
		for i in 200:
			var v := WaterfallCanvas.hash01(i * 7919, i * 104729, seed_value)
			assert_bool(v >= 0.0 and v <= 1.0).override_failure_message(
				"hash01 escaped [0,1]: %f at i=%d seed=%d" % [v, i, seed_value]
			).is_true()


func test_hash01_differs_across_seeds() -> void:
	# Not a strict guarantee for every input, but across 64 samples two
	# different seeds must not produce an identical sequence.
	var same := true
	for i in 64:
		if not is_equal_approx(WaterfallCanvas.hash01(i, 0, 1), WaterfallCanvas.hash01(i, 0, 2)):
			same = false
			break
	assert_bool(same).is_false()


func test_push_column_bounds_history_and_tracks_bursts() -> void:
	var canvas: WaterfallCanvas = auto_free(WaterfallCanvas.new())
	canvas.reset(42)
	for i in WaterfallCanvas.MAX_COLUMNS + 10:
		canvas.push_column(true, 0.5, i == 0)
	assert_int(canvas._columns.size()).is_equal(WaterfallCanvas.MAX_COLUMNS)
	assert_int(canvas._burst_rows.size()).is_equal(WaterfallCanvas.MAX_COLUMNS)
	assert_bool(canvas._burst_rows[0] < 0.0).is_true()   # the burst column scrolled off
	assert_int(canvas._columns_pushed).is_equal(WaterfallCanvas.MAX_COLUMNS + 10)


func test_burst_anchor_is_frozen_at_push_time() -> void:
	# Regression (review): bursts used to re-anchor to the LIVE target row on
	# every redraw, so under drift the recorded history visibly slid. The
	# anchor must be captured at push time, like trace cells freeze freq_ratio.
	var canvas: WaterfallCanvas = auto_free(WaterfallCanvas.new())
	canvas.reset(1)
	canvas.set_target_ratio(0.8)
	canvas.push_column(true, 0.5, true)
	canvas.set_target_ratio(0.2)   # target drifts on after the burst
	assert_float(canvas._burst_rows.back()).is_equal_approx(0.8, 0.001)


func test_canvas_clips_its_contents() -> void:
	# Regression (review): a burst anchored near a range edge spans past the
	# plot; without clipping the magenta smear painted over the labels below.
	var canvas: WaterfallCanvas = auto_free(WaterfallCanvas.new())
	add_child(canvas)   # _ready runs on tree entry
	assert_bool(canvas.clip_contents).is_true()


func test_reset_clears_history_and_reseeds() -> void:
	var canvas: WaterfallCanvas = auto_free(WaterfallCanvas.new())
	canvas.push_column(true, 0.5)
	canvas.reset(7)
	assert_int(canvas._columns.size()).is_equal(0)
	assert_int(canvas._burst_rows.size()).is_equal(0)
	assert_int(canvas._columns_pushed).is_equal(0)
	assert_int(canvas._noise_seed).is_equal(7)
