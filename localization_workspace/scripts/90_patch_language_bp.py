"""Add Arabic as a genuine 16th entry to BP_UIO_Language's SupportedLanguages map.

This is the real fix for "Arabic isn't in the language list": the list is NOT a
hardcoded C++ array (the shipping exe contains zero culture codes) - it's a
Blueprint map property inside BP_UIO_Language.uexp.

Layout (decoded from the shipped asset):
  uexp offset 469 : int32 map element count (15)
  uexp offset 473 : entries, each =
        FString key            (int32 len incl NUL, ascii bytes + NUL)
        FText   display name   (uint32 Flags=2, int8 HistoryType=0xFF,
                                int32 bHasCultureInvariantString=1, FString)
  map ends at offset 1334

Adding bytes to .uexp requires fixing the .uasset export table, or the package
fails to load (same class of bug as the SerialSize repatch lesson in the playbook):
  - export #2 SerialSize  += delta   (the export containing this map)
  - exports #3..#9 SerialOffset += delta
  - summary BulkDataStartOffset += delta
"""
import struct, shutil, os, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
SRC = os.path.join(BASE, "lang_bp", "MortalShell2", "Content", "Sparta", "UI", "Core", "Options", "BP_UIO_Language")
OUT_DIR = os.path.join(BASE, "lang_bp_patched", "MortalShell2", "Content", "Sparta", "UI", "Core", "Options")

NEW_CULTURE = "ar-MA"
NEW_DISPLAY = "العربية (Arabic)"

COUNT_OFF = 469
MAP_END = 1334
EXPORT_SIZE_OFFS = [4794, 4890, 4986, 5082, 5178, 5274, 5370, 5466, 5562]  # stride 96
TARGET_EXPORT_IDX = 1          # 0-based: export #2 holds the map
BULK_OFF = 245                 # summary BulkDataStartOffset

def fstring(s):
    """UE FString: ascii -> positive length incl NUL; non-ascii -> negative length, UTF-16."""
    try:
        s.encode("ascii")
        b = s.encode("ascii") + b"\x00"
        return struct.pack("<i", len(b)) + b
    except UnicodeEncodeError:
        b = s.encode("utf-16-le") + b"\x00\x00"
        return struct.pack("<i", -(len(b) // 2)) + b

def ftext(display):
    return struct.pack("<I", 2) + bytes([0xFF]) + struct.pack("<i", 1) + fstring(display)

def read_fstring(d, o):
    (n,) = struct.unpack_from("<i", d, o); o += 4
    if n >= 0:
        return d[o:o+n-1].decode("ascii", "replace"), o + n
    n = -n
    return d[o:o+(n-1)*2].decode("utf-16-le", "replace"), o + n * 2

def parse_map(d, count_off, first_off):
    (count,) = struct.unpack_from("<i", d, count_off)
    o = first_off
    out = []
    for _ in range(count):
        key, o = read_fstring(d, o)
        o += 4 + 1 + 4               # flags, history type, bHasCultureInvariantString
        disp, o = read_fstring(d, o)
        out.append((key, disp))
    return count, out, o

def main():
    uexp = bytearray(open(SRC + ".uexp", "rb").read())
    uasset = bytearray(open(SRC + ".uasset", "rb").read())

    count, entries, end = parse_map(uexp, COUNT_OFF, 473)
    assert count == 15 and end == MAP_END, f"unexpected layout: count={count} end={end}"
    assert all(k != NEW_CULTURE for k, _ in entries), "culture already present"
    print(f"parsed {count} entries, map ends at {end}")

    new_entry = fstring(NEW_CULTURE) + ftext(NEW_DISPLAY)
    delta = len(new_entry)
    print(f"new entry: {NEW_CULTURE} -> {NEW_DISPLAY}  ({delta} bytes)")

    # 1. bump count, 2. splice entry in at map end
    struct.pack_into("<i", uexp, COUNT_OFF, count + 1)
    uexp = uexp[:MAP_END] + new_entry + uexp[MAP_END:]

    # 3. fix export table
    sz_off = EXPORT_SIZE_OFFS[TARGET_EXPORT_IDX]
    old_sz = struct.unpack_from("<q", uasset, sz_off)[0]
    struct.pack_into("<q", uasset, sz_off, old_sz + delta)
    print(f"export#{TARGET_EXPORT_IDX+1} SerialSize {old_sz} -> {old_sz + delta}")

    for i, so in enumerate(EXPORT_SIZE_OFFS):
        if i <= TARGET_EXPORT_IDX:
            continue
        off_off = so + 8
        old_off = struct.unpack_from("<q", uasset, off_off)[0]
        struct.pack_into("<q", uasset, off_off, old_off + delta)
        print(f"export#{i+1} SerialOffset {old_off} -> {old_off + delta}")

    old_bulk = struct.unpack_from("<q", uasset, BULK_OFF)[0]
    struct.pack_into("<q", uasset, BULK_OFF, old_bulk + delta)
    print(f"BulkDataStartOffset {old_bulk} -> {old_bulk + delta}")

    os.makedirs(OUT_DIR, exist_ok=True)
    dst = os.path.join(OUT_DIR, "BP_UIO_Language")
    open(dst + ".uasset", "wb").write(bytes(uasset))
    open(dst + ".uexp", "wb").write(bytes(uexp))

    # verify by re-parsing the patched output
    v = bytearray(open(dst + ".uexp", "rb").read())
    c2, e2, end2 = parse_map(v, COUNT_OFF, 473)
    print(f"\nverified: {c2} entries, map ends at {end2}")
    for k, disp in e2:
        print(f"   {k:8} -> {disp}")
    assert c2 == 16 and e2[-1][0] == NEW_CULTURE
    assert len(v) == len(open(SRC + ".uexp", "rb").read()) + delta
    print("\nOK")

if __name__ == "__main__":
    main()
