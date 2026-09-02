"""Patch Game.locmeta to register ar-MA as a compiled culture.
Byte format verified: 16-byte hash + version(1) + native-culture FString +
native-locres-path FString + culture-count(u32) + N x culture-name FString.
Each FString = u32 length-prefix (includes trailing NUL) + ascii bytes + NUL.
This exact structure was verified working on the Fatal Claw project.
"""
import struct, os

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
SRC = os.path.join(BASE, "extracted", "Game.locmeta")
OUT = os.path.join(BASE, "extracted", "Game_patched.locmeta")

NEW_CULTURE = "ar-MA"

def read_fstring(data, offset):
    (length,) = struct.unpack_from("<I", data, offset)
    offset += 4
    s = data[offset:offset + length - 1].decode("ascii")  # strip trailing NUL
    offset += length
    return s, offset

def write_fstring(s):
    b = s.encode("ascii") + b"\x00"
    return struct.pack("<I", len(b)) + b

def main():
    data = open(SRC, "rb").read()
    off = 0
    file_hash = data[off:off+16]; off += 16
    version = data[off]; off += 1
    native_culture, off = read_fstring(data, off)
    native_path, off = read_fstring(data, off)
    (count,) = struct.unpack_from("<I", data, off); off += 4

    cultures = []
    for _ in range(count):
        c, off = read_fstring(data, off)
        cultures.append(c)

    assert off == len(data), f"parse mismatch: consumed {off}, total {len(data)}"
    print("parsed cultures:", cultures)
    assert NEW_CULTURE not in cultures, "already present"

    cultures.append(NEW_CULTURE)
    new_count = len(cultures)

    out = bytearray()
    out += file_hash
    out.append(version)
    out += write_fstring(native_culture)
    out += write_fstring(native_path)
    out += struct.pack("<I", new_count)
    for c in cultures:
        out += write_fstring(c)

    with open(OUT, "wb") as f:
        f.write(out)

    print(f"wrote {OUT} ({len(out)} bytes, was {len(data)})")
    print(f"cultures: {new_count} (was {count})")

    # round-trip verify
    check = open(OUT, "rb").read()
    off2 = 16 + 1
    nc, off2 = read_fstring(check, off2)
    npth, off2 = read_fstring(check, off2)
    (cnt2,) = struct.unpack_from("<I", check, off2); off2 += 4
    got = []
    for _ in range(cnt2):
        c, off2 = read_fstring(check, off2)
        got.append(c)
    assert off2 == len(check)
    assert got == cultures
    assert nc == native_culture and npth == native_path
    print("round-trip verified OK:", got)

if __name__ == "__main__":
    main()
