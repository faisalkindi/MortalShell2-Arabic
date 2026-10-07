"""Swap the LT/RT step direction for the inventory filter strip only (byte patch, same length).

The strip is left mirrored (tabs run right to left), so the stock mapping LT = previous (-1), RT = next (+1) sends LT
right and RT left. WBP_IL_Inventory_Top listens to EInterfaceInput NewEnumerator6/7. The enum is NOT in numeric order:
those names are values 11 and 12 (read the Names tuples of the EInterfaceInput asset, not the NewEnumeratorN suffix).
BP_HorizontalBoxContainer.HandleInput initialises 33 Temp_int_Variable_N constants (EX_Let + EX_IntConst, 39 bytes
apart) and a switch maps value 11 -> Temp_int_Variable_19 (-1), value 12 -> Temp_int_Variable_18 (+1). Swapping those
two 4-byte constants changes only the inventory strip: Main/Options use values 9/10, the item grid uses others.
UAssetGUI re-saving this blueprint drops class-level data, so patch the stock legacy .uexp bytes directly.
Input: hbc_b25478144/<rel> (retoc to-legacy of stock BP_HorizontalBoxContainer). Output: bp_stage_nav_b25478144/<rel>.
"""
import os, shutil, struct
W = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
REL = r"MortalShell2\Content\Sparta\UI\Core\Navigation\BP_HorizontalBoxContainer"
SRC, DST = W + r"\hbc_b25478144" + "\\" + REL, W + r"\bp_stage_nav_b25478144" + "\\" + REL
PATTERN = [0, 0, 0, 1, -1] + [0] * 13 + [1, -1, 1, -1, 1, 1, -1, -1, 0, 1, 0, -1, 0, 0, 0]   # the 33 init constants, in order
b = bytearray(open(SRC + ".uexp", "rb").read())
hits = [i for i in range(len(b) - 5) if b[i] == 0x1D and struct.unpack("<i", b[i + 1:i + 5])[0] in (-1, 0, 1)]
found = []
for k in range(len(hits) - 32):
    w = hits[k:k + 33]
    if [struct.unpack("<i", b[x + 1:x + 5])[0] for x in w] == PATTERN and len({w[i + 1] - w[i] for i in range(32)}) == 1:
        found.append(w)
assert len(found) == 1, f"expected one constant table, found {len(found)}"
w = found[0]
for idx, (old, new) in {18: (1, -1), 19: (-1, 1)}.items():
    o = w[idx]
    assert struct.unpack("<i", b[o + 1:o + 5])[0] == old
    b[o + 1:o + 5] = struct.pack("<i", new)
os.makedirs(os.path.dirname(DST), exist_ok=True)
shutil.copyfile(SRC + ".uasset", DST + ".uasset")
open(DST + ".uexp", "wb").write(b)
print("patched Temp_int_Variable_18/19; bytes changed:", sum(x != y for x, y in zip(open(SRC + ".uexp", "rb").read(), b)))
