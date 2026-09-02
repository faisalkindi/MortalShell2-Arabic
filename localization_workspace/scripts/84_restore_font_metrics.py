"""Fix Arabic clipping by restoring each merged font's ORIGINAL vertical metrics.

Merging SST's Arabic into the game fonts expanded head.yMax/yMin and replaced
hhea/OS-2 metrics with SST's taller ones. UE FontFace assets using BoundingBox
layout derive the baseline from head yMax/yMin (they ignore hhea entirely), so a
taller box drops the baseline and the text clips.

Fix per the playbook: copy the ORIGINAL font's metrics back over the merged font.
Glyph outlines are NOT touched - shifting Arabic outlines would break shaping and
GPOS mark positioning.

CRITICAL: TTFont(..., recalcBBoxes=False) or save() silently recomputes and
overwrites the bbox we just set.
"""
import io, os, struct
from fontTools.ttLib import TTFont

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
STAGE = os.path.join(BASE, "release", "staging")
MERGE_WORK = os.path.join(BASE, "font_build", "merge_work")
TRAJAN_WORK = os.path.join(BASE, "font_build", "trajan_work")

RELS = [
    r"MortalShell2\Content\Sparta\UI\Fonts\CrimsonText-Bold.ufont",
    r"MortalShell2\Content\Sparta\UI\Fonts\CrimsonText-Italic.ufont",
    r"MortalShell2\Content\Sparta\UI\Fonts\CrimsonText-Regular.ufont",
    r"MortalShell2\Content\Sparta\UI\Fonts\CrimsonText-SemiBold.ufont",
    r"MortalShell2\Content\Sparta\UI\Fonts\Cormorant\CormorantUnicase-Bold.ufont",
    r"MortalShell2\Content\Sparta\UI\Fonts\Cormorant\CormorantUnicase-Regular.ufont",
    r"MortalShell2\Content\Sparta\UI\Fonts\PTSerif\PTSerif-Bold.ufont",
    r"MortalShell2\Content\Sparta\UI\Fonts\PTSerif\PTSerif-Italic.ufont",
    r"MortalShell2\Content\Sparta\UI\Fonts\PTSerif\PTSerif-Regular.ufont",
    r"MortalShell2\Content\Sparta\UI\Fonts\Trajan_Pro_Regular.ufont",
    r"MortalShell2\Content\Sparta\UI\Fonts\Trajan_Pro_SemiBold.ufont",
    r"MortalShell2\Content\UltraVolumetrics\Core\Widgets\Fonts\Afacad-Bold.ufont",
    r"MortalShell2\Content\UltraVolumetrics\Core\Widgets\Fonts\Afacad-Medium.ufont",
    r"MortalShell2\Content\UltraVolumetrics\Core\Widgets\Fonts\Afacad-Regular.ufont",
    r"MortalShell2\Content\UltraVolumetrics\Core\Widgets\Fonts\Afacad-SemiBold.ufont",
]

def unwrap(raw):
    n = struct.unpack("<I", raw[:4])[0]
    return raw[4:4 + n]

def wrap(b):
    return struct.pack("<I", len(b)) + b + struct.pack("<I", 0)

def find_original(name):
    """Originals live in merge_work (normal merges) or trajan_work (CFF converts)."""
    for d in (MERGE_WORK, TRAJAN_WORK):
        p = os.path.join(d, name + ".ttf")
        if os.path.exists(p):
            return p
    return None

def main():
    fixed, missing = [], []
    for rel in RELS:
        name = os.path.basename(rel)
        dest = os.path.join(STAGE, rel)
        origp = find_original(name)
        if not origp or not os.path.exists(dest):
            missing.append(name)
            continue

        orig = TTFont(origp, recalcBBoxes=False, recalcTimestamp=False)
        merged = TTFont(io.BytesIO(unwrap(open(dest, "rb").read())),
                        recalcBBoxes=False, recalcTimestamp=False)

        before = (merged["head"].yMax, merged["head"].yMin,
                  merged["hhea"].ascent, merged["hhea"].descent)

        # head bbox drives BoundingBox layout
        merged["head"].yMax = orig["head"].yMax
        merged["head"].yMin = orig["head"].yMin
        merged["head"].xMax = orig["head"].xMax
        merged["head"].xMin = orig["head"].xMin
        # hhea/OS-2 drive Metrics layout and line height
        for f in ("ascent", "descent", "lineGap"):
            setattr(merged["hhea"], f, getattr(orig["hhea"], f))
        if "OS/2" in merged and "OS/2" in orig:
            for f in ("sTypoAscender", "sTypoDescender", "sTypoLineGap",
                      "usWinAscent", "usWinDescent"):
                if hasattr(orig["OS/2"], f):
                    setattr(merged["OS/2"], f, getattr(orig["OS/2"], f))

        after = (merged["head"].yMax, merged["head"].yMin,
                 merged["hhea"].ascent, merged["hhea"].descent)

        buf = io.BytesIO()
        merged.save(buf)
        open(dest, "wb").write(wrap(buf.getvalue()))
        fixed.append((name, before, after))

    for n, b, a in fixed:
        print(f"{n:34} yMax/yMin/asc/desc {b} -> {a}")
    print(f"\nfixed: {len(fixed)}   missing originals: {missing}")

    # verify written files still parse and kept Arabic
    print("\nverify:")
    for rel in RELS:
        dest = os.path.join(STAGE, rel)
        if not os.path.exists(dest):
            continue
        f = TTFont(io.BytesIO(unwrap(open(dest, "rb").read())), recalcBBoxes=False)
        cm = f.getBestCmap()
        print(f"  {os.path.basename(rel):34} arabic={0x627 in cm} latin={0x41 in cm} "
              f"cyr={0x410 in cm} yMax={f['head'].yMax} yMin={f['head'].yMin}")

if __name__ == "__main__":
    main()
