"""Give Arabic descenders room without moving the baseline.

84_restore_font_metrics.py copied each game font's ORIGINAL vertical metrics back
over the merged font, which fixed the baseline-drop clipping. But the originals are
Latin fonts: their head.yMin is shallower than SST's Arabic glyphs reach, so tails
(ج ح خ ع غ م ي ...) were cut off along the bottom of every line.

UE FontFace BoundingBox layout derives the baseline from head.yMax, and the line box
height from (yMax - yMin). So LOWERING yMin alone adds descender room while leaving
the baseline exactly where 84 put it. yMax is never touched here.

hhea.descent and OS/2 usWinDescent/sTypoDescender are moved in step so the non-
BoundingBox layout paths agree with head.

CRITICAL: TTFont(..., recalcBBoxes=False), or save() recomputes head and undoes this.
"""
import io, os, struct, sys
from fontTools.ttLib import TTFont

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
STAGE = os.path.join(BASE, "release", "staging")
MARGIN = 40          # font units of slack under the deepest glyph

def read_ufont(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[:4])[0]
    return b[4:4 + n], b[4 + n:]

def write_ufont(path, ttf_bytes, tail):
    with open(path, "wb") as f:
        f.write(struct.pack("<I", len(ttf_bytes)))
        f.write(ttf_bytes)
        f.write(tail)

def deepest_arabic(font):
    glyf = font["glyf"] if "glyf" in font else None
    if not glyf:
        return 0
    low = 0
    for cp, gn in font.getBestCmap().items():
        if 0x0600 <= cp <= 0x06FF or 0xFB50 <= cp <= 0xFEFF:
            if gn in glyf:
                g = glyf[gn]
                if g.numberOfContours != 0 and hasattr(g, "yMin") and g.yMin < low:
                    low = g.yMin
    return low

def main():
    changed = 0
    for root, _, files in os.walk(STAGE):
        for fn in sorted(files):
            if not fn.endswith(".ufont"):
                continue
            path = os.path.join(root, fn)
            ttf, tail = read_ufont(path)
            font = TTFont(io.BytesIO(ttf), recalcBBoxes=False)
            head = font["head"]
            deep = deepest_arabic(font)
            need = deep - MARGIN
            if need >= head.yMin:
                font.close(); continue
            old = head.yMin
            head.yMin = need
            if "hhea" in font:
                font["hhea"].descent = min(font["hhea"].descent, need)
            if "OS/2" in font:
                os2 = font["OS/2"]
                os2.usWinDescent = max(os2.usWinDescent, abs(need))
                os2.sTypoDescender = min(os2.sTypoDescender, need)
            buf = io.BytesIO()
            font.save(buf)
            font.close()
            write_ufont(path, buf.getvalue(), tail)
            print(f"  {fn:34s} yMin {old:5d} -> {need:5d}  (yMax unchanged)")
            changed += 1
    print(f"\nfonts adjusted: {changed}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
