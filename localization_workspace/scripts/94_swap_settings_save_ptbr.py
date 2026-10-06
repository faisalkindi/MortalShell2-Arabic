"""Make SpartaSettingsSaveObject accept ar-MA WITHOUT changing the asset size (build 25478144+).

InitLocalization validates the saved LocCulture against a 15-entry SupportedLanguages map built from
constants in the function's bytecode. Growing that bytecode (adding a 16th entry) crashes the game with
EXCEPTION_ACCESS_VIOLATION in UObject::execLocalVariable (verified in-game on 25478144, even when the
size fields are updated correctly). The shipped approach is a same-length in-place swap: the key
`pt-BR` -> `ar-MA` (both 5 chars). Net effect: ar-MA is a valid saved culture; a saved pt-BR falls back
to the system language (BP_UIO_Language still lists pt-BR; only the persistence check differs).
"""
import os, shutil, sys
W = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
REL = os.path.join("MortalShell2", "Content", "Sparta", "Core", "Player", "Save", "SpartaSettingsSaveObject")
SRC = os.path.join(W, "src_b25478144", REL)
OUT = os.path.join(W, "settings_bp_patched_b25478144", REL)
OLD, NEW = b"\x1fpt-BR\x00", b"\x1far-MA\x00"
uexp = open(SRC + ".uexp", "rb").read()
assert len(OLD) == len(NEW) and uexp.count(OLD) == 1 and uexp.count(NEW) == 0, uexp.count(OLD)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
shutil.copyfile(SRC + ".uasset", OUT + ".uasset")
open(OUT + ".uexp", "wb").write(uexp.replace(OLD, NEW))
d = [i for i in range(len(uexp)) if uexp[i] != open(OUT + ".uexp", "rb").read()[i]]
print("OK, bytes changed:", len(d), "size", os.path.getsize(OUT + ".uexp"))
