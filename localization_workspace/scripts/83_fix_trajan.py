"""Trajan Pro is CFF/PostScript, so Arabic TrueType glyphs can't be merged into it
directly - the earlier build replaced it wholesale with SST, which is why English
menus changed appearance.

Fix: convert Trajan's CFF outlines to TrueType (quadratic) via cu2qu, then merge
SST's Arabic subset in. Result keeps Trajan's original Latin design AND gains Arabic.
"""
import io, os, struct, subprocess
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.subset import Subsetter, Options
from fontTools.merge import Merger
from fontTools.ttLib.scaleUpem import scale_upem

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
SST = r"C:\Users\Faisal\Ai\Mods Dev\FF7Classic\localization_workspace\build\FF7_Arabic_Handover\source_font\SST-Arabic-Medium_sanitized.ttf"
STAGE = os.path.join(BASE, "release", "staging")
REPAK = r"C:\Users\Faisal\Ai\Tools\repak\repak.exe"
PAK4 = r"F:\SteamLibrary\steamapps\common\Sparta\MortalShell2\Content\Paks\pakchunk4-Windows.pak"
WORK = os.path.join(BASE, "font_build", "trajan_work")

TARGETS = [
    "MortalShell2/Content/Sparta/UI/Fonts/Trajan_Pro_Regular.ufont",
    "MortalShell2/Content/Sparta/UI/Fonts/Trajan_Pro_SemiBold.ufont",
]

ARABIC_RANGES = list(range(0x0600, 0x0700)) + list(range(0x0750, 0x0780)) + \
                list(range(0x08A0, 0x0900)) + list(range(0xFB50, 0xFE00)) + \
                list(range(0xFE70, 0xFF00))

MAX_ERR = 1.0  # cu2qu conversion tolerance in font units

def unwrap(raw):
    n = struct.unpack("<I", raw[:4])[0]
    return raw[4:4 + n]

def wrap(b):
    return struct.pack("<I", len(b)) + b + struct.pack("<I", 0)

def otf_to_ttf(font):
    """Convert CFF outlines to TrueType glyf IN PLACE on the loaded font, so every
    other table (cmap/name/OS-2/GSUB/GPOS/GDEF/hmtx) is preserved byte-for-byte."""
    glyph_order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()
    glyf_glyphs = {}
    for name in glyph_order:
        pen = TTGlyphPen(None)
        glyph_set[name].draw(Cu2QuPen(pen, MAX_ERR, reverse_direction=True))
        glyf_glyphs[name] = pen.glyph()

    glyf = newTable("glyf")
    glyf.glyphOrder = glyph_order
    glyf.glyphs = glyf_glyphs
    for g in glyf_glyphs.values():
        g.recalcBounds(glyf)

    del font["CFF "]
    font["glyf"] = glyf
    font["loca"] = newTable("loca")
    font.sfntVersion = chr(0) + chr(1) + chr(0) + chr(0)
    font["head"].indexToLocFormat = 0
    font["head"].glyphDataFormat = 0
    # CFF fonts ship maxp 0.5; TrueType needs 1.0 with the glyf-derived counters
    mx = font["maxp"]
    mx.tableVersion = 0x00010000
    # maxp 1.0 carries hinting counters a CFF-origin maxp 0.5 never had; we ship
    # unhinted quadratic outlines, so zeros are correct
    for field, val in (("maxZones", 2), ("maxTwilightPoints", 0), ("maxStorage", 0),
                       ("maxFunctionDefs", 0), ("maxInstructionDefs", 0),
                       ("maxStackElements", 0), ("maxSizeOfInstructions", 0),
                       ("maxComponentElements", 0), ("maxComponentDepth", 0)):
        setattr(mx, field, val)
    mx.recalc(font)
    if "post" in font:
        font["post"].formatType = 2.0
        font["post"].glyphOrder = glyph_order
        font["post"].extraNames = []
        font["post"].mapping = {}
    return font

def arabic_subset(upem):
    f = TTFont(SST)
    opts = Options()
    opts.layout_features = ["*"]
    opts.notdef_outline = True
    opts.recalc_bounds = False
    sub = Subsetter(options=opts)
    sub.populate(unicodes=ARABIC_RANGES)
    sub.subset(f)
    if f["head"].unitsPerEm != upem:
        scale_upem(f, upem)
    buf = io.BytesIO()
    f.save(buf)
    return buf.getvalue()

def main():
    os.makedirs(WORK, exist_ok=True)
    for rel in TARGETS:
        name = os.path.basename(rel)
        raw_path = os.path.join(WORK, name)
        with open(raw_path, "wb") as out:
            subprocess.run([REPAK, "get", PAK4, rel], stdout=out, stderr=subprocess.DEVNULL)
        orig_ttf = unwrap(open(raw_path, "rb").read())

        src = TTFont(io.BytesIO(orig_ttf))
        assert "CFF " in src, f"{name} is not CFF - use the normal merge path"
        upem = src["head"].unitsPerEm

        converted = otf_to_ttf(src)
        conv_path = os.path.join(WORK, name + ".ttf")
        buf = io.BytesIO()
        converted.save(buf)
        open(conv_path, "wb").write(buf.getvalue())

        ar_path = os.path.join(WORK, name + ".arabic.ttf")
        open(ar_path, "wb").write(arabic_subset(upem))

        merged = Merger().merge([conv_path, ar_path])
        mbuf = io.BytesIO()
        merged.save(mbuf)

        dest = os.path.join(STAGE, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(wrap(mbuf.getvalue()))

        chk = TTFont(io.BytesIO(mbuf.getvalue()))
        cm = chk.getBestCmap()
        print(f"{name:28} upem={upem} latin={0x41 in cm} arabic={0x627 in cm} "
              f"glyphs={len(cm)} outlines={'glyf' if 'glyf' in chk else 'CFF'}")

if __name__ == "__main__":
    main()
