# Fonts

Pixel Operator v1.4 (2018) by Jayvee Enaguas (HarvettFox96), CC0 — see LICENSE.txt.

**These TTFs are NOT the stock release.** The stock 1.4 build is missing five
Turkish codepoints (ğ Ğ ş Ş İ). All four files here were patched with
`artgen/tools/patch_turkish_glyphs.py`, which adds them as TTF composite
glyphs built from the font's own `breve`, `cedilla`, and `period` glyphs —
same mechanism the font already uses for ö/ü/etc. Re-running the script on a
stock download reproduces these files exactly.

Usage contract (plan §5):
- `PixelOperator.ttf` (+Bold) — 16 px dialogue text
- `PixelOperator8.ttf` (+Bold) — 8 px UI / ticker text

Godot must import these with antialiasing off, hinting off, subpixel off
(project-wide defaults already force this).
