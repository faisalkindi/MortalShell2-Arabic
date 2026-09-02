"""Merge SST Arabic glyphs INTO the game's original fonts.

Replacing the game's fonts wholesale with SST killed Cyrillic (SST has none),
which broke Russian. This instead ADDS SST's Arabic coverage to each original
font, so the original's Latin AND Cyrillic survive.

Per font:
  - TrueType (glyf) originals -> subset SST to Arabic-only, scale to the
    original's unitsPerEm if it differs, then merge. Disjoint cmaps (originals
    have no Arabic), so no codepoint conflicts.
  - CFF/PostScript originals (Trajan Pro) -> cannot merge TrueType outlines into
    CFF, so replace wholesale. Trajan has no Cyrillic, so nothing is lost but its
    own Latin styling.

Output: wrapped .ufont ([uint32 size][ttf][uint32 0]) into the release staging dir.
"""
import io, os, struct, subprocess, sys, tempfile
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
from fontTools.merge import Merger
from fontTools.ttLib.scaleUpem import scale_upem

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
SST = r"C:\Users\Faisal\Ai\Mods Dev\FF7Classic\localization_workspace\build\FF7_Arabic_Handover\source_font\SST-Arabic-Medium_sanitized.ttf"
STAGE = os.path.join(BASE, "release", "staging")
REPAK = r"C:\Users\Faisal\Ai\Tools\repak\repak.exe"
GAME_PAKS = [r"F:\SteamLibrary\steamapps\common\Sparta\MortalShell2\Content\Paks\pakchunk4-Windows.pak", r"F:\SteamLibrary\steamapps\common\Sparta\MortalShell2\Content\Paks\pakchunk11-Windows.pak"]
WORK = os.path.join(BASE, "font_build", "merge_work")

ARABIC_RANGES = list(range(0x0600, 0x0700)) + list(range(0x0750, 0x0780)) + \
                list(range(0x08A0, 0x0900)) + list(range(0xFB50, 0xFE00)) + \
                list(range(0xFE70, 0xFF00))

TARGETS = [
    "MortalShell2/Content/Sparta/UI/Fonts/CrimsonText-Bold.ufont",
    "MortalShell2/Content/Sparta/UI/Fonts/CrimsonText-Italic.ufont",
    "MortalShell2/Content/Sparta/UI/Fonts/CrimsonText-Regular.ufont",
    "MortalShell2/Content/Sparta/UI/Fonts/CrimsonText-SemiBold.ufont",
    "MortalShell2/Content/Sparta/UI/Fonts/Cormorant/CormorantUnicase-Bold.ufont",
    "MortalShell2/Content/Sparta/UI/Fonts/Cormorant/CormorantUnicase-Regular.ufont",
    "MortalShell2/Content/Sparta/UI/Fonts/PTSerif/PTSerif-Bold.ufont",
    "MortalShell2/Content/Sparta/UI/Fonts/PTSerif/PTSerif-Italic.ufont",
    "MortalShell2/Content/Sparta/UI/Fonts/PTSerif/PTSerif-Regular.ufont",
    "MortalShell2/Content/Sparta/UI/Fonts/Trajan_Pro_Regular.ufont",
    "MortalShell2/Content/Sparta/UI/Fonts/Trajan_Pro_SemiBold.ufont",
    "MortalShell2/Content/UltraVolumetrics/Core/Widgets/Fonts/Afacad-Bold.ufont",
    "MortalShell2/Content/UltraVolumetrics/Core/Widgets/Fonts/Afacad-Medium.ufont",
    "MortalShell2/Content/UltraVolumetrics/Core/Widgets/Fonts/Afacad-Regular.ufont",
    "MortalShell2/Content/UltraVolumetrics/Core/Widgets/Fonts/Afacad-SemiBold.ufont",
]

def unwrap(raw):
    n = struct.unpack("<I", raw[:4])[0]
    return raw[4:4+n]

def wrap(ttf_bytes):
    return struct.pack("<I", len(ttf_bytes)) + ttf_bytes + struct.pack("<I", 0)

def extract_original(rel_path, dest):
    for pak in GAME_PAKS:
        with open(dest, "wb") as out:
            r = subprocess.run([REPAK, "get", pak, rel_path], stdout=out, stderr=subprocess.PIPE)
        if r.returncode == 0 and os.path.getsize(dest) > 1000:
            return True
    return False

def make_arabic_subset(target_upem):
    """SST subset to Arabic-only, scaled to target upem."""
    f = TTFont(SST)
    opts = Options()
    opts.layout_features = ["*"]     # keep init/medi/fina/liga - Arabic shaping needs them
    opts.notdef_outline = True
    opts.recalc_bounds = False
    opts.drop_tables = []
    sub = Subsetter(options=opts)
    sub.populate(unicodes=ARABIC_RANGES)
    sub.subset(f)
    if f["head"].unitsPerEm != target_upem:
        scale_upem(f, target_upem)
    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    return buf

def main():
    os.makedirs(WORK, exist_ok=True)
    merged, replaced, failed = [], [], []
    sst_raw = open(SST, "rb").read()

    for rel in TARGETS:
        name = os.path.basename(rel)
        orig_path = os.path.join(WORK, name)
        if not extract_original(rel, orig_path):
            failed.append((name, "extract failed"))
            continue

        orig_ttf = unwrap(open(orig_path, "rb").read())
        orig_clean = os.path.join(WORK, name + ".ttf")
        open(orig_clean, "wb").write(orig_ttf)

        f = TTFont(io.BytesIO(orig_ttf))
        is_cff = "CFF " in f
        upem = f["head"].unitsPerEm
        del f

        dest = os.path.join(STAGE, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        if is_cff:
            open(dest, "wb").write(wrap(sst_raw))
            replaced.append((name, "CFF outlines - wholesale replace"))
            continue

        try:
            arabic_buf = make_arabic_subset(upem)
            arabic_path = os.path.join(WORK, name + ".arabic.ttf")
            open(arabic_path, "wb").write(arabic_buf.getvalue())

            merger = Merger()
            out = merger.merge([orig_clean, arabic_path])
            buf = io.BytesIO()
            out.save(buf)
            open(dest, "wb").write(wrap(buf.getvalue()))
            merged.append((name, f"upem={upem}"))
        except Exception as e:
            # fail loud, do not silently ship a broken font
            failed.append((name, f"merge failed: {type(e).__name__}: {e}"))

    print(f"merged: {len(merged)}")
    for n, d in merged:
        print("   ", n, d)
    print(f"replaced (CFF): {len(replaced)}")
    for n, d in replaced:
        print("   ", n, d)
    print(f"FAILED: {len(failed)}")
    for n, d in failed:
        print("   ", n, d)

    # verify what we wrote
    print("\nverification:")
    for rel in TARGETS:
        dest = os.path.join(STAGE, rel.replace("/", os.sep))
        if not os.path.exists(dest):
            print(f"  MISSING {os.path.basename(rel)}")
            continue
        ttf = unwrap(open(dest, "rb").read())
        f = TTFont(io.BytesIO(ttf))
        cm = f.getBestCmap()
        print(f"  {os.path.basename(rel):34} latin={0x41 in cm} cyr={0x410 in cm} arabic={0x627 in cm} glyphs={len(cm)}")

if __name__ == "__main__":
    main()
