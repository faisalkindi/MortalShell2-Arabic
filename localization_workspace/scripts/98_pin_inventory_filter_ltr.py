"""Inventory filter strip: pin ONLY the LT/strip/RT icon row (WBP_MGT_Character.HorizontalBox_0) to LeftToRight.

Final v1.4 design. ScrollBox_InventoryFilter is deliberately NOT pinned: pinning it (or its wrappers) makes the strip
scroll the wrong way, so the selected tab leaves the view and no highlight is visible. Left mirrored, the strip's
tabs run right to left (All at the right) and its scrolling/highlight work. HorizontalBox_0 holds
[WBP_Prompt_Left_Main (LT)] [filter strip] [WBP_Prompt_Right_Main (RT)]; pinning it puts LT on the left and RT on the
right as on the controller. The matching step direction is fixed by 99_swap_inventory_filter_shoulders.py.
Usage: 98_pin_inventory_filter_ltr.py MS2
"""
import json, os, sys, subprocess, copy, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
UAG = os.path.join(W, "scripts", "_tools", "UAssetGUI_110", "UAssetGUI.exe")
REL = os.path.join("MortalShell2", "Content", "Sparta", "UI", "Menu", "WBP_MGT_Character.uasset")
SRC = os.path.join(W, "src_b25478144", REL)
OUT = os.path.join(W, "bp_stage_charfilter_b25478144", REL)
JS = os.path.join(W, "uag_json")
TARGETS = ["HorizontalBox_0"]
PROP, ENUM, VALUE = "FlowDirectionPreference", "EFlowDirectionPreference", "LeftToRight"

def run(a):
    r = subprocess.run(a, capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or "Unhandled exception" in r.stdout + r.stderr:
        raise SystemExit("UAssetGUI failed: " + " ".join(a) + (r.stdout + r.stderr)[:600])

def main(usmap):
    os.makedirs(os.path.dirname(OUT), exist_ok=True); os.makedirs(JS, exist_ok=True)
    js = os.path.join(JS, "char_filter_patch.json")
    run([UAG, "tojson", SRC, js, "VER_UE5_6", usmap])
    j = json.load(open(js, encoding="utf-8"))
    ex = j["Exports"]
    tpl = next(p for e in ex for p in (e.get("Data") or []) if isinstance(p, dict) and "EnumPropertyData" in p.get("$type", ""))
    for name in TARGETS:
        hits = [e for e in ex if e.get("ObjectName") == name]
        assert len(hits) == 1, (name, len(hits))
        e = hits[0]
        assert "RawExport" not in e["$type"], name
        data = e["Data"]
        assert not any(isinstance(p, dict) and p.get("Name") == PROP for p in data), name + " already pinned"
        p = copy.deepcopy(tpl); p["Name"] = PROP; p["EnumType"] = ENUM; p["Value"] = VALUE
        for k in ("ArrayIndex", "DuplicationIndex"):
            if k in p: p[k] = 0
        if "IsZero" in p: p["IsZero"] = False
        pos = next((i for i, q in enumerate(data) if isinstance(q, dict) and q.get("Name") == "bIsVariable"), len(data))
        data.insert(pos, p)
    for n in (PROP, ENUM, VALUE):
        if n not in j["NameMap"]: j["NameMap"].append(n)
    json.dump(j, open(js, "w", encoding="utf-8"), indent=1)
    run([UAG, "fromjson", js, OUT, usmap])
    if not os.path.exists(OUT): raise SystemExit("fromjson wrote nothing")
    chk = os.path.join(JS, "char_filter_patch_check.json")
    run([UAG, "tojson", OUT, chk, "VER_UE5_6", usmap])
    c = json.load(open(chk, encoding="utf-8"))
    for name in TARGETS:
        e = next(x for x in c["Exports"] if x.get("ObjectName") == name)
        got = [p for p in e["Data"] if isinstance(p, dict) and p.get("Name") == PROP]
        assert got and got[0]["Value"] == VALUE, (name, got)
        print(f"verified: {name}.{PROP} = {got[0]['Value']}")
    print("uexp", os.path.getsize(os.path.splitext(SRC)[0] + ".uexp"), "->", os.path.getsize(os.path.splitext(OUT)[0] + ".uexp"))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "MS2")
