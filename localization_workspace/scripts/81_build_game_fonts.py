"""Replace the game's own UI/design fonts with SST Arabic Medium.

The engine-fallback-only swap (NotoNaskhArabicUI-Regular.ttf) is not necessarily
in this game's font chain, so Arabic can still render blank. This replaces the
game's actual design fonts, which is what Asmar's working mod does.

IMPORTANT format detail: the game's .ufont files are WRAPPED as
    [uint32 payload_size][raw TTF bytes][uint32 0]
(verified against the shipped originals). Asmar shipped RAW ttf with no wrapper;
we write the correct wrapped form to match the originals.

Deliberately EXCLUDED (so CJK keeps working): NotoSansKR/SC/TC, NotoSerifJP.
SST has Latin coverage, so Latin-script languages still render (in SST's design).
"""
import os, struct

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
SST = r"C:\Users\Faisal\Ai\Mods Dev\FF7Classic\localization_workspace\build\FF7_Arabic_Handover\source_font\SST-Arabic-Medium_sanitized.ttf"
STAGE = os.path.join(BASE, "release", "staging")

# game font faces to replace (pak-relative paths), CJK faces intentionally omitted
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

def wrap_ufont(ttf_bytes):
    return struct.pack("<I", len(ttf_bytes)) + ttf_bytes + struct.pack("<I", 0)

def main():
    ttf = open(SST, "rb").read()
    payload = wrap_ufont(ttf)
    for rel in TARGETS:
        dest = os.path.join(STAGE, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(payload)
    print(f"wrote {len(TARGETS)} .ufont files, {len(payload)} bytes each")
    print(f"  (wrapper: 4-byte size={len(ttf)} + ttf + 4-byte 0)")
    print("excluded (CJK preserved): NotoSansKR/SC/TC, NotoSerifJP")

if __name__ == "__main__":
    main()
