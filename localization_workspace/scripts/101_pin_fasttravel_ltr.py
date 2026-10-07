"""Mether's Breath fast-travel screen: English frame, Arabic content (WBP_MGT_FastTravel).

Symptom (Arabic, video 2026-10-07): the map is drawn over half of the menu. Overlay_Menu draws [HB_Background, HB_Menu
(the panel), RB_Map] - the map on top. In English the panel sits left and RB_Map sits right (RenderTransform X=1100;
Anim_FadeIn slides the panel in from -500 and the map from +1920; Anim_ToggleMapMode moves RB_Map 1100->800 and the
panel SB_Left 0->-200). RB_Map overlaps the panel and hides that overlap with its EffectMaterial, a fade mask. Under RTL
Slate mirrors the layout and the translations, but not the mask texture, so the map's hard edge lands on the menu.
Fix: ScaleBox_Main (root) = LeftToRight, so frame, slides and mask match English; then hand the three content groups
that were already right in Arabic back to the culture (RTL) so they stay exactly as before:
  Overlay_Contents           place list + its scrollbar (rows are RTL inside RetainerBox_FastTravel)
  ScaleBox_UserScale_Prompts bottom button prompts
Region tabs: the icon row HorizontalBox_0 [LB][tabs][RB] follows the root (LB left, RB right, as on the controller),
but the tabs sit in RetainerBox_Filters, whose content lays out RTL regardless of outer pins (first tab on the right).
LB sends EInterfaceInput value 9 (= delta -1) and would step right. Values 9/10 are shared with the Main/Options tab
bars, so the shared delta table cannot change; instead this screen's listener WBP_IL_FastTravel_Filter gets its own
InterfaceInputs map {NewEnumerator4: IA_Menu_Right_Secondary, NewEnumerator5: IA_Menu_Left_Secondary}. The listener
broadcasts the map KEY whose value is the triggered action, so LB now sends value 10 (+1, the next tab = leftwards)
and RB sends 9. The instance is a RawExport (unversioned): header gains a fragment for property #9 (InterfaceInputs;
#7 is AcceptedInputs) and the map is written as NumKeysToRemove=0, Num=2, (FName key, FPackageIndex value) pairs.
Property-only, same technique as 93b/96/97.
Usage: 101_pin_fasttravel_ltr.py MS2   (input ft_b25478144/..., output bp_stage_fasttravel_b25478144/...)
"""
import json, os, sys, subprocess, copy, time, io, base64, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
UAG = os.path.join(W, "scripts", "_tools", "UAssetGUI_110", "UAssetGUI.exe")
REL = os.path.join("MortalShell2", "Content", "Sparta", "UI", "Menu", "LandingArea", "WBP_MGT_FastTravel.uasset")
SRC, OUT = os.path.join(W, "ft_b25478144", REL), os.path.join(W, "bp_stage_fasttravel_b25478144", REL)
JS = os.path.join(W, "uag_json")
TARGETS = {"ScaleBox_Main": "LeftToRight", "Overlay_Contents": "Culture", "ScaleBox_UserScale_Prompts": "Culture"}
PROP, ENUM = "FlowDirectionPreference", "EFlowDirectionPreference"

def run(a):
    r = subprocess.run(a, capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or "Unhandled exception" in r.stdout + r.stderr:
        raise SystemExit("UAssetGUI failed: " + " ".join(a) + (r.stdout + r.stderr)[:600])

def wait(p):
    for _ in range(40):
        if os.path.exists(p): time.sleep(1); return
        time.sleep(0.5)
    raise SystemExit("missing " + p)

def main(usmap):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    js = os.path.join(JS, "ft_pin.json")
    run([UAG, "tojson", SRC, js, "VER_UE5_6", usmap]); wait(js)
    j = json.load(open(js, encoding="utf-8"))
    tpl = next(p for e in j["Exports"] for p in (e.get("Data") or []) if isinstance(p, dict) and "EnumPropertyData" in p.get("$type", ""))
    for name, VALUE in TARGETS.items():
        hits = [e for e in j["Exports"] if e.get("ObjectName") == name]
        assert len(hits) == 1, (name, len(hits))
        e = hits[0]; assert "RawExport" not in e["$type"], name
        data = e["Data"]
        assert not any(isinstance(p, dict) and p.get("Name") == PROP for p in data), name + " already pinned"
        p = copy.deepcopy(tpl); p["Name"] = PROP; p["EnumType"] = ENUM; p["Value"] = VALUE
        for k in ("ArrayIndex", "DuplicationIndex"):
            if k in p: p[k] = 0
        if "IsZero" in p: p["IsZero"] = False
        pos = next((i for i, q in enumerate(data) if isinstance(q, dict) and q.get("Name") == "bIsVariable"), len(data))
        data.insert(pos, p)
    for n in (PROP, ENUM, *TARGETS.values()):
        if n not in j["NameMap"]: j["NameMap"].append(n)
    # --- per-screen LB/RB remap on the region-tab listener ---------------------------------------------------
    nmap, imps = j["NameMap"], j["Imports"]
    def name(n):
        if n not in nmap: nmap.append(n)
        return nmap.index(n)
    def add_import(pkg_path, obj, cls_pkg, cls):
        for n in (pkg_path, obj, cls_pkg, cls, "/Script/CoreUObject", "Package"): name(n)
        imps.append({"$type": "UAssetAPI.Import, UAssetAPI", "ObjectName": pkg_path, "OuterIndex": 0, "ClassPackage": "/Script/CoreUObject",
                     "ClassName": "Package", "PackageName": None, "bImportOptional": False})
        pkg_idx = -len(imps)
        imps.append({"$type": "UAssetAPI.Import, UAssetAPI", "ObjectName": obj, "OuterIndex": pkg_idx, "ClassPackage": cls_pkg,
                     "ClassName": cls, "PackageName": None, "bImportOptional": False})
        return -len(imps)
    A = "/Game/Sparta/Core/Input/Actions/Menu/"
    ia_left = add_import(A + "IA_Menu_Left_Secondary", "IA_Menu_Left_Secondary", "/Script/EnhancedInput", "InputAction")
    ia_right = add_import(A + "IA_Menu_Right_Secondary", "IA_Menu_Right_Secondary", "/Script/EnhancedInput", "InputAction")
    il = next(e for e in j["Exports"] if e.get("ObjectName") == "WBP_IL_FastTravel_Filter")
    assert "RawExport" in il["$type"]
    raw = base64.b64decode(il["Data"])
    k4, k5, tail = name("EInterfaceInput::NewEnumerator4"), name("EInterfaceInput::NewEnumerator5"), name("FocusToLocation")
    stock = struct.pack("<HHi", 0x0207, 0x0321, 2) + struct.pack("<ii", k4, 0) + struct.pack("<ii", k5, 0) + struct.pack("<ii", tail, 0)
    assert raw == stock, "WBP_IL_FastTravel_Filter bytes changed: " + raw.hex()
    new = (struct.pack("<HHH", 0x0207, 0x0201, 0x031F)                         # #7 AcceptedInputs, #9 InterfaceInputs, #41 (unchanged)
           + struct.pack("<i", 2) + struct.pack("<ii", k4, 0) + struct.pack("<ii", k5, 0)            # AcceptedInputs = [4, 5]
           + struct.pack("<ii", 0, 2) + struct.pack("<iii", k4, 0, ia_right) + struct.pack("<iii", k5, 0, ia_left)
           + struct.pack("<ii", tail, 0))
    il["Data"] = base64.b64encode(new).decode()
    for ia in (ia_left, ia_right):
        if ia not in il["CreateBeforeSerializationDependencies"]: il["CreateBeforeSerializationDependencies"].append(ia)
    print("listener remap: LB -> NewEnumerator5 (+1), RB -> NewEnumerator4 (-1); imports", ia_left, ia_right)
    json.dump(j, open(js, "w", encoding="utf-8"), indent=1)
    for f in (OUT, os.path.splitext(OUT)[0] + ".uexp"):
        if os.path.exists(f): os.remove(f)
    run([UAG, "fromjson", js, OUT, usmap]); wait(OUT); wait(os.path.splitext(OUT)[0] + ".uexp")
    chk = os.path.join(JS, "ft_pin_check.json")
    run([UAG, "tojson", OUT, chk, "VER_UE5_6", usmap]); wait(chk)
    c = json.load(open(chk, encoding="utf-8"))
    for name, VALUE in TARGETS.items():
        e = next(x for x in c["Exports"] if x.get("ObjectName") == name)
        got = [p for p in e["Data"] if isinstance(p, dict) and p.get("Name") == PROP]
        assert got and got[0]["Value"] == VALUE, (name, got)
        print(f"verified: {name}.{PROP} = {got[0]['Value']}")
    cil = next(e for e in c["Exports"] if e.get("ObjectName") == "WBP_IL_FastTravel_Filter")
    cb = base64.b64decode(cil["Data"]); cn = c["NameMap"]; ci = c["Imports"]
    # layout: header 6 | AcceptedInputs count 6, keys 10/18 | map NumKeysToRemove 26, Num 30, (key 34, value 42), (key 46, value 54) | tail 58
    assert len(cb) == 66 and struct.unpack_from("<ii", cb, 26) == (0, 2), cb.hex()
    k4i, k5i, vR, vL = struct.unpack_from("<i", cb, 34)[0], struct.unpack_from("<i", cb, 46)[0], struct.unpack_from("<i", cb, 42)[0], struct.unpack_from("<i", cb, 54)[0]
    assert cn[struct.unpack_from("<i", cb, 10)[0]].endswith("NewEnumerator4") and cn[struct.unpack_from("<i", cb, 18)[0]].endswith("NewEnumerator5")
    assert cn[k4i].endswith("NewEnumerator4") and cn[k5i].endswith("NewEnumerator5") and cn[struct.unpack_from("<i", cb, 58)[0]] == "FocusToLocation"
    print("verified listener map:", cn[k4i], "->", ci[-vR - 1]["ObjectName"], "|", cn[k5i], "->", ci[-vL - 1]["ObjectName"])
    assert ci[-vR - 1]["ObjectName"] == "IA_Menu_Right_Secondary" and ci[-vL - 1]["ObjectName"] == "IA_Menu_Left_Secondary"
    print("uexp", os.path.getsize(os.path.splitext(SRC)[0] + ".uexp"), "->", os.path.getsize(os.path.splitext(OUT)[0] + ".uexp"))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "MS2")
