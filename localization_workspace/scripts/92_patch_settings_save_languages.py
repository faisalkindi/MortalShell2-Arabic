"""Add ar-MA to SpartaSettingsSaveObject's SupportedLanguages map.

Why this is a SECOND patch: BP_UIO_Language holds the map the OPTIONS MENU renders,
which is why Arabic already appears there and selecting it works. But SpartaSettingsSaveObject
holds its OWN SupportedLanguages map, and its InitLocalization runs at startup: it reads the
saved LocCulture, validates it against THAT map, and falls back to GetSystemLanguage when the
culture is absent. ar-MA was absent, so every launch reverted to English.

This asset serialises strings tag-first, not length-first (unlike BP_UIO_Language):
    0x1F <ascii bytes> 0x00                 ASCII string
    0x34 <utf-16-le bytes> 0x00 0x00        UTF-16 string
    0x29 0x02                               FText header preceding each display name
Map: int32 count at 31665, entries follow, map ends at 32336.

Growing .uexp requires repairing .uasset or the package will not load:
  export table: stride 96, starts at 14781, 23 exports; offset 31665 lands in export #13
  - export #13 SerialSize  += delta
  - exports #14..#23 SerialOffset += delta
  - summary BulkDataStartOffset (int64 @255) += delta
"""
import struct, os, io, sys, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
SRC = os.path.join(BASE, "ui_extract", "MortalShell2", "Content", "Sparta", "Core",
                   "Player", "Save", "SpartaSettingsSaveObject")
OUT = os.path.join(BASE, "settings_bp_patched", "MortalShell2", "Content", "Sparta",
                   "Core", "Player", "Save")

NEW_CULTURE = "ar-MA"
NEW_DISPLAY = "العربية (Arabic)"

COUNT_OFF = 31665
MAP_END   = 32336
EXPORT_START, EXPORT_STRIDE, EXPORT_COUNT = 14781, 96, 23
TARGET_EXPORT = 12          # 0-based index of export #13
BULK_OFF = 255

def rd_str(d, o):
    t = d[o]
    if t == 0x1F:
        e = d.index(b"\x00", o + 1)
        return d[o + 1:e].decode("ascii"), e + 1
    if t == 0x34:
        o2 = o + 1
        while not (d[o2] == 0 and d[o2 + 1] == 0):
            o2 += 2
        return d[o + 1:o2].decode("utf-16-le"), o2 + 2
    raise ValueError(f"unknown string tag {t:02x} at {o}")

def wr_ascii(s):
    return b"\x1f" + s.encode("ascii") + b"\x00"

def wr_utf16(s):
    return b"\x34" + s.encode("utf-16-le") + b"\x00\x00"

def parse_map(d):
    count = struct.unpack_from("<i", d, COUNT_OFF)[0]
    o = COUNT_OFF + 4
    out = []
    for _ in range(count):
        k, o = rd_str(d, o)
        assert d[o] == 0x29 and d[o + 1] == 0x02, f"FText header missing at {o}"
        o += 2
        v, o = rd_str(d, o)
        out.append((k, v))
    return count, out, o

def main():
    uexp = bytearray(open(SRC + ".uexp", "rb").read())
    uasset = bytearray(open(SRC + ".uasset", "rb").read())
    orig_len = len(uexp)

    count, entries, end = parse_map(uexp)
    assert count == 15 and end == MAP_END, f"layout changed: count={count} end={end}"
    assert all(k != NEW_CULTURE for k, _ in entries), "ar-MA already present"
    print(f"parsed {count} entries, map ends at {end}")

    entry = wr_ascii(NEW_CULTURE) + b"\x29\x02" + wr_utf16(NEW_DISPLAY)
    delta = len(entry)
    print(f"new entry {NEW_CULTURE} -> {NEW_DISPLAY} ({delta} bytes)")

    struct.pack_into("<i", uexp, COUNT_OFF, count + 1)
    uexp = uexp[:MAP_END] + entry + uexp[MAP_END:]

    sz_off = EXPORT_START + TARGET_EXPORT * EXPORT_STRIDE
    old = struct.unpack_from("<q", uasset, sz_off)[0]
    struct.pack_into("<q", uasset, sz_off, old + delta)
    print(f"export#{TARGET_EXPORT+1} SerialSize {old} -> {old + delta}")

    for i in range(TARGET_EXPORT + 1, EXPORT_COUNT):
        off_off = EXPORT_START + i * EXPORT_STRIDE + 8
        o = struct.unpack_from("<q", uasset, off_off)[0]
        struct.pack_into("<q", uasset, off_off, o + delta)

    b = struct.unpack_from("<q", uasset, BULK_OFF)[0]
    struct.pack_into("<q", uasset, BULK_OFF, b + delta)
    print(f"BulkDataStartOffset {b} -> {b + delta}")

    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, "SpartaSettingsSaveObject")
    open(dst + ".uasset", "wb").write(bytes(uasset))
    open(dst + ".uexp", "wb").write(bytes(uexp))

    v = bytearray(open(dst + ".uexp", "rb").read())
    c2, e2, end2 = parse_map(v)
    assert c2 == 16 and e2[-1][0] == NEW_CULTURE, "verification failed"
    assert len(v) == orig_len + delta
    # every export must still fit inside the grown uexp
    for i in range(EXPORT_COUNT):
        so = EXPORT_START + i * EXPORT_STRIDE
        sz = struct.unpack_from("<q", uasset, so)[0]
        of = struct.unpack_from("<q", uasset, so + 8)[0] - len(uasset)
        assert 0 <= of and of + sz <= len(v), f"export#{i+1} out of bounds"
    print(f"\nverified: {c2} entries, ends at {end2}, all exports in bounds")
    for k, d_ in e2:
        print(f"   {k:9s} {d_}")

if __name__ == "__main__":
    main()
