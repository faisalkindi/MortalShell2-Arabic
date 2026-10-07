"""WBP_ConfirmationPrompt_MultiOptions: arrows point the way they move, d-pad left moves left (build 25478144+).

Layout: ScaleBox_Options > HorizontalBox_0 [LeftArrow] [RB_Options (RetainerBox) > ScrollBox_Options > BP_HB_Options]
[RightArrow]. Under Arabic everything is mirrored and the options strip (inside the retainer) runs right to left, so
"previous" (index-1) is to the right. The arrows' positions already agree with that: LeftArrow (click = previous,
disabled at index 0) sits on the right, RightArrow (click = next, disabled at the end) on the left. Two things were off:
 - images: WBP_ArrowButton.UpdateDirection rotates by Direction (0 = points left, 1 = 180 deg); Slate does not mirror
   images, so both arrows pointed inward. Fix: LeftArrow.Direction = 1, RightArrow.Direction = 0 (the default).
 - d-pad: WBP_IL_Prompt sends NewEnumerator2 (value 5, -1) for left, so left moved right. Fix: this window's listener
   gets its own InterfaceInputs {NewEnumerator2: IA_Menu_Right_Primary, NewEnumerator3: IA_Menu_Left_Primary}
   (WBP_InputListener broadcasts the key whose value is the triggered action), so left sends value 7 (+1 = leftwards).
Scrolling, the strip and the click handlers are untouched.
How: UAssetGUI decodes these BP-class instances only when their class assets sit beside the file (it lists what it
could not find in OtherAssetsFailedToAccess), and it cannot write them back once decoded. So the asset is parsed alone
(instances stay RawExport) and the unversioned bytes are edited by hand (header fragments: uint16 skip | 0x100 last |
values << 9; then the values; then a 4-byte trailer), and the result is re-parsed beside its class assets to check
every value. ui2_b25478144/ holds the stock asset plus those class assets (copied from a full Sparta/UI extract).
Usage: 103_multioptions_arrows.py MS2   (output bp_stage_ui2_b25478144/...)
"""
import json, os, sys, subprocess, shutil, struct, base64, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
UAG = os.path.join(W, "scripts", "_tools", "UAssetGUI_110", "UAssetGUI.exe")
REL = os.path.join("MortalShell2", "Content", "Sparta", "UI", "Menu", "Misc", "WBP_ConfirmationPrompt_MultiOptions")
TREE = os.path.join(W, "ui2_b25478144")
SRC, OUT = os.path.join(TREE, REL), os.path.join(W, "bp_stage_ui2_b25478144", REL)
JS = os.path.join(W, "uag_json")
TMP = os.path.join(os.environ["TEMP"], "ms2_103")
A = "/Game/Sparta/Core/Input/Actions/Menu/"
USMAP = "MS2"

def run(a):
    r = subprocess.run(a, capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or "Unhandled exception" in r.stdout + r.stderr:
        raise SystemExit("UAssetGUI failed: " + " ".join(a) + (r.stdout + r.stderr)[:600])

def wait(p):
    for _ in range(40):
        if os.path.exists(p): time.sleep(1); return
        time.sleep(0.5)
    raise SystemExit("missing " + p)

def tojson(asset, js):
    if os.path.exists(js): os.remove(js)
    run([UAG, "tojson", asset, js, "VER_UE5_6", USMAP]); wait(js)
    return json.load(open(js, encoding="utf-8"))

def frag(skip, values, last=False):
    return struct.pack("<H", skip | (0x100 if last else 0) | (values << 9))

def main():
    shutil.rmtree(TMP, ignore_errors=True)
    lone = os.path.join(TMP, "lone", REL); os.makedirs(os.path.dirname(lone))
    for ext in (".uasset", ".uexp"): shutil.copyfile(SRC + ext, lone + ext)
    j = tojson(lone + ".uasset", os.path.join(JS, "multioptions_raw.json"))
    ex, nmap, imps = j["Exports"], j["NameMap"], j["Imports"]
    def export(n):
        hits = [e for e in ex if e.get("ObjectName") == n]
        assert len(hits) == 1 and "RawExport" in hits[0]["$type"], n
        return hits[0]
    raw = lambda e: base64.b64decode(e["Data"])
    def setraw(e, b): e["Data"] = base64.b64encode(b).decode()

    # arrows (WBP_ArrowButton_C schema: #3 Direction (1-byte enum), #42 Slot)
    left, right = export("LeftArrow"), export("RightArrow")
    lb, rb = raw(left), raw(right)
    assert lb[:2] == frag(42, 1, True) and len(lb) == 10, lb.hex()
    assert rb[:4] == frag(3, 1) + frag(38, 1, True) and rb[4] == 1 and len(rb) == 13, rb.hex()
    setraw(left, frag(3, 1) + frag(38, 1, True) + b"\x01" + lb[2:])       # Direction = 1 (points right)
    setraw(right, frag(42, 1, True) + rb[5:])                              # Direction back to the default 0 (points left)

    # listener (WBP_InputListener_C schema: #2 IgnoreBlockAll, #7 AcceptedInputs, #9 InterfaceInputs, #41 Slot)
    def add_import(pkg_path, obj):
        for n in (pkg_path, obj, "/Script/CoreUObject", "Package", "/Script/EnhancedInput", "InputAction"):
            if n not in nmap: nmap.append(n)
        imps.append({"$type": "UAssetAPI.Import, UAssetAPI", "ObjectName": pkg_path, "OuterIndex": 0, "ClassPackage": "/Script/CoreUObject",
                     "ClassName": "Package", "PackageName": None, "bImportOptional": False})
        p = -len(imps)
        imps.append({"$type": "UAssetAPI.Import, UAssetAPI", "ObjectName": obj, "OuterIndex": p, "ClassPackage": "/Script/EnhancedInput",
                     "ClassName": "InputAction", "PackageName": None, "bImportOptional": False})
        return -len(imps)
    ia_left = add_import(A + "IA_Menu_Left_Primary", "IA_Menu_Left_Primary")
    ia_right = add_import(A + "IA_Menu_Right_Primary", "IA_Menu_Right_Primary")
    il = export("WBP_IL_Prompt"); ib = raw(il)
    k2, k3 = nmap.index("EInterfaceInput::NewEnumerator2"), nmap.index("EInterfaceInput::NewEnumerator3")
    assert ib[:6] == frag(2, 1) + frag(4, 1) + frag(33, 1, True) and len(ib) == 51, ib.hex()
    acc = ib[7:43]                                                         # count + 4 FNames
    assert struct.unpack_from("<iii", acc, 0) == (4, k2, 0) and struct.unpack_from("<i", acc, 12)[0] == k3
    new = (frag(2, 1) + frag(4, 1) + frag(1, 1) + frag(31, 1, True) + ib[6:7] + acc
           + struct.pack("<ii", 0, 2) + struct.pack("<iii", k2, 0, ia_right) + struct.pack("<iii", k3, 0, ia_left)
           + ib[43:])                                                      # Slot + trailer, unchanged
    setraw(il, new)
    for ia in (ia_left, ia_right): il["CreateBeforeSerializationDependencies"].append(ia)

    js = os.path.join(JS, "multioptions_patch.json")
    json.dump(j, open(js, "w", encoding="utf-8"), indent=1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for ext in (".uasset", ".uexp"):
        if os.path.exists(OUT + ext): os.remove(OUT + ext)
    run([UAG, "fromjson", js, OUT + ".uasset", USMAP]); wait(OUT + ".uasset"); wait(OUT + ".uexp")

    # check: decode the result beside its class assets
    chk = os.path.join(TMP, "tree"); shutil.copytree(TREE, chk)
    for ext in (".uasset", ".uexp"): shutil.copyfile(OUT + ext, os.path.join(chk, REL) + ext)
    c = tojson(os.path.join(chk, REL) + ".uasset", os.path.join(JS, "multioptions_patch_check.json"))
    assert not c["OtherAssetsFailedToAccess"], c["OtherAssetsFailedToAccess"]
    get = lambda n: next(e for e in c["Exports"] if e.get("ObjectName") == n)
    val = lambda e, n: next((p["Value"] for p in e["Data"] if p.get("Name") == n), None)
    assert val(get("LeftArrow"), "Direction") == "Enum_ArrowButton::NewEnumerator1" and val(get("LeftArrow"), "Slot") == 45
    assert val(get("RightArrow"), "Direction") is None and val(get("RightArrow"), "Slot") == 44
    ilc = get("WBP_IL_Prompt"); ci = c["Imports"]
    assert val(ilc, "IgnoreBlockAll") is True and val(ilc, "Slot") == 72
    assert [x["Value"] for x in val(ilc, "AcceptedInputs")] == [f"EInterfaceInput::NewEnumerator{n}" for n in (2, 3, 8, 9)]
    got = {k["Value"]: ci[-v["Value"] - 1]["ObjectName"] for k, v in val(ilc, "InterfaceInputs")}
    assert got == {"EInterfaceInput::NewEnumerator2": "IA_Menu_Right_Primary", "EInterfaceInput::NewEnumerator3": "IA_Menu_Left_Primary"}, got
    print("verified (decoded with class assets): LeftArrow Direction=1, RightArrow Direction=default 0, listener map", got)
    print("uexp", os.path.getsize(SRC + ".uexp"), "->", os.path.getsize(OUT + ".uexp"))
    shutil.rmtree(TMP, ignore_errors=True)

if __name__ == "__main__":
    if len(sys.argv) > 1: USMAP = sys.argv[1]
    main()
