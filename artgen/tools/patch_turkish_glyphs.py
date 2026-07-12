"""Patch missing Turkish glyphs (ğ Ğ ş Ş İ) into Pixel Operator TTFs.

The 2018 dafont release lacks exactly these five codepoints. The font already
ships `breve` and `cedilla` accent glyphs and builds its other accented
letters as TTF composites (odieresis = dieresis + o), so we extend it the
same way. Offsets are derived from the font's own metrics so the script
works across the regular/bold/8px variants without hardcoded numbers.
"""
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
import sys

# (new glyph name, codepoint, base glyph, accent glyph, placement)
# placement: "above" lifts accent 1px above base top; "below" keeps accent's
# natural below-baseline position and only centers horizontally.
ADDITIONS = [
    ("gbreve",     0x011F, "g", "breve",   "above"),
    ("Gbreve",     0x011E, "G", "breve",   "above"),
    ("scedilla",   0x015F, "s", "cedilla", "below"),
    ("Scedilla",   0x015E, "S", "cedilla", "below"),
    ("Idotaccent", 0x0130, "I", "period",  "above"),
]


def bbox(glyf, name):
    g = glyf[name]
    g.recalcBounds(glyf)
    return g.xMin, g.yMin, g.xMax, g.yMax


def one_pixel(tt):
    # The period glyph is a single pixel in a pixel font; its height IS the grid.
    x0, y0, x1, y1 = bbox(tt["glyf"], "period")
    return y1 - y0


def patch(path):
    tt = TTFont(path)
    glyf, hmtx, cmap_table = tt["glyf"], tt["hmtx"], tt["cmap"]
    order = tt.getGlyphOrder()
    px = one_pixel(tt)
    added = []

    for new_name, code, base, accent, placement in ADDITIONS:
        if new_name in order:
            continue
        bx0, _, bx1, b_top = bbox(glyf, base)
        ax0, a_bot, ax1, _ = bbox(glyf, accent)
        dx = ((bx0 + bx1) - (ax0 + ax1)) // 2  # center accent over base
        dy = (b_top + px) - a_bot if placement == "above" else 0

        pen = TTGlyphPen(glyf)
        pen.addComponent(base, (1, 0, 0, 1, 0, 0))
        pen.addComponent(accent, (1, 0, 0, 1, dx, dy))
        # glyf.__setitem__ appends to the font's shared glyphOrder itself.
        glyf[new_name] = pen.glyph()
        hmtx[new_name] = hmtx[base]
        added.append((new_name, code, dx, dy))
    for table in cmap_table.tables:
        if table.isUnicode():
            for new_name, code, _, _ in added:
                table.cmap[code] = new_name

    tt.save(path)
    return added


if __name__ == "__main__":
    for path in sys.argv[1:]:
        added = patch(path)
        print(path.split("/")[-1], "->", [(n, f"dx={dx}", f"dy={dy}") for n, _, dx, dy in added])
