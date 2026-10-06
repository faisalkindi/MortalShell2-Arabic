"""Stop the world map from panning backwards under Arabic.

Symptom: with the game in Arabic, pushing the stick left pans the map right and vice versa (horizontal only).
Cause: the map pans by SetRenderTranslation on WBP_MapBase.Overlay_Root (WBP_MGT_WorldMap.UpdateOffset eases
RenderTransform.Translation toward CurrentOffsetX/Y). Slate negates a widget's render-transform X translation
(and rotation) when it is arranged under a right-to-left flow direction, and the shipped config
(Slate.ShouldFollowCultureByDefault=1) makes every default-flow widget RTL under ar-MA.
Fix: pin the widget that gets translated and its arranging parent to LeftToRight (a map is geography; it should
not mirror). Property-only change (same technique as 93b); no bytecode touched.
Usage: 96_pin_map_pan_ltr.py MS2
"""
import json, os, sys, subprocess, copy, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
UAG = os.path.join(W, "scripts", "_tools", "UAssetGUI_110", "UAssetGUI.exe")
REL = os.path.join("MortalShell2", "Content", "Sparta", "UI", "World", "Map", "Widgets", "WBP_MapBase.uasset")
SRC = os.path.join(W, "map_b25478144", REL)
OUT = os.path.join(W, "bp_stage_map_b25478144", REL)
JS = os.path.join(W, "uag_json")
TARGETS = ["Overlay_Root", "ScaleBox_Root"]
PROP, ENUM, VALUE = "FlowDirectionPreference", "EFlowDirectionPreference", "LeftToRight"

def run(a):
    r = subprocess.run(a, capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or "Unhandled exception" in r.stdout + r.stderr:
        raise SystemExit("UAssetGUI failed: " + " ".join(a) + (r.stdout + r.stderr)[:600])

def main(usmap):
    os.makedirs(os.path.dirname(OUT), exist_ok=True); os.makedirs(JS, exist_ok=True)
    js = os.path.join(JS, "mapbase_patch.json")
    run([UAG, "tojson", SRC, js, "VER_UE5_6", usmap])
    j = json.load(open(js, encoding="utf-8"))
    tpl = next(p for e in j["Exports"] for p in (e.get("Data") or [])
               if isinstance(p, dict) and "EnumPropertyData" in p.get("$type", ""))
    for name in TARGETS:
        e = next(x for x in j["Exports"] if x.get("ObjectName") == name)
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
    chk = os.path.join(JS, "mapbase_patch_check.json")
    run([UAG, "tojson", OUT, chk, "VER_UE5_6", usmap])
    c = json.load(open(chk, encoding="utf-8"))
    for name in TARGETS:
        e = next(x for x in c["Exports"] if x.get("ObjectName") == name)
        got = [p for p in e["Data"] if isinstance(p, dict) and p.get("Name") == PROP]
        assert got and got[0]["Value"] == VALUE, (name, got)
        print(f"verified: {name}.{PROP} = {got[0]['Value']}  props={[p['Name'] for p in e['Data']]}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "MS2")
