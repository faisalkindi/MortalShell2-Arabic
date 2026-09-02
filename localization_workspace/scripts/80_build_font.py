"""Build the Arabic font payloads for Mortal Shell II.

Replaces UE's stock engine-level Arabic fallback font
(Engine/Content/Slate/Fonts/NotoNaskhArabicUI-Regular.ttf, a RAW .ttf - no UE wrapper)
with SST Arabic Medium. This is the low-risk path: it needs no .usmap, no UAssetGUI,
and does NOT touch any of the game's own design fonts (CrimsonText/Cormorant/PTSerif/
Trajan) or its per-language CJK fonts (NotoSansKR/SC/TC, NotoSerifJP), so Latin and
CJK rendering are untouched.

Produces two variants:
  A) sst_stock.ttf     - SST unmodified
  B) sst_bbox_fixed.ttf - SST with head.yMax/yMin overridden to match the ORIGINAL
     font's bbox ratio (scaled for differing unitsPerEm). Per the playbook's
     font-vertical-position fix: UE FontFace assets using BoundingBox layout position
     the baseline from head yMax/yMin and ignore hhea/OS-2, so a replacement font with
     a proportionally taller bbox renders too low. Ship A first; if Arabic sits low
     in-game, swap to B. Do NOT shift glyph outlines (breaks Arabic shaping/GPOS).
"""
import io, os, shutil
from fontTools.ttLib import TTFont

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
SST_SRC = r"C:\Users\Faisal\Ai\Mods Dev\FF7Classic\localization_workspace\build\FF7_Arabic_Handover\source_font\SST-Arabic-Medium_sanitized.ttf"
ORIG_FALLBACK = os.path.join(BASE, "extracted", "orig_NotoNaskhArabicUI-Regular.ttf")
OUT_DIR = os.path.join(BASE, "font_build")

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # variant A - stock SST
    stock_path = os.path.join(OUT_DIR, "sst_stock.ttf")
    shutil.copyfile(SST_SRC, stock_path)

    # read original bbox ratios
    orig = TTFont(ORIG_FALLBACK, recalcBBoxes=False)
    o_upem = orig["head"].unitsPerEm
    o_ymax_ratio = orig["head"].yMax / o_upem
    o_ymin_ratio = orig["head"].yMin / o_upem

    # variant B - bbox matched to the original's proportions
    sst = TTFont(SST_SRC, recalcBBoxes=False)  # MUST disable recalc or save() overwrites bbox
    s_upem = sst["head"].unitsPerEm
    before = (sst["head"].yMax, sst["head"].yMin)
    sst["head"].yMax = round(o_ymax_ratio * s_upem)
    sst["head"].yMin = round(o_ymin_ratio * s_upem)
    after = (sst["head"].yMax, sst["head"].yMin)

    buf = io.BytesIO()
    sst.save(buf)
    fixed_path = os.path.join(OUT_DIR, "sst_bbox_fixed.ttf")
    open(fixed_path, "wb").write(buf.getvalue())

    print(f"original fallback: upem={o_upem} yMax={orig['head'].yMax} yMin={orig['head'].yMin}"
          f" (ratios {o_ymax_ratio:.4f} / {o_ymin_ratio:.4f})")
    print(f"variant A (stock):     {stock_path}  {os.path.getsize(stock_path)} bytes")
    print(f"variant B (bbox fix):  {fixed_path}  {os.path.getsize(fixed_path)} bytes"
          f"  head yMax/yMin {before} -> {after}")

    # sanity: both must still parse and keep Arabic coverage
    for p in (stock_path, fixed_path):
        f = TTFont(p)
        cmap = f.getBestCmap()
        assert 0x0627 in cmap and 0x0628 in cmap, f"Arabic glyphs missing in {p}"
        assert "DSIG" not in f, f"DSIG present in {p} (exit-crash risk)"
    print("sanity: both variants parse, Arabic coverage present, no DSIG")

if __name__ == "__main__":
    main()
