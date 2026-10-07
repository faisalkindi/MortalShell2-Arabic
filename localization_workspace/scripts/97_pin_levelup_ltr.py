"""Pin the level-up screen's gloom requirement bar and level row to LeftToRight (build 25478144+).

Symptoms under Arabic (RTL flow):
 - WBP_Tooltip_Requirement (the "Gloom (owned/required)" bar): name and numbers overlap and the brackets read
   ")4360(" - the bar is an Overlay of an Fill-aligned HorizontalBox (icon+name) and a right-aligned HorizontalBox
   (numbers), built for LTR; mirroring swaps both onto the same side, and the "(" / ")" glyphs are separate
   TextBlocks that are not mirrored.
 - WBP_Progression_Harbinger.HorizontalBox_98 (Level 10 > [< 11 >]): arrow IMAGES are not mirrored by Slate, so under
   RTL the arrow points back at the old level and the </> buttons point inward.
Fix: FlowDirectionPreference=LeftToRight on WBP_Tooltip_Requirement.ScaleBox_Main and
WBP_Progression_Harbinger.HorizontalBox_98 (property-only, same technique as 93b/96).
Usage: 97_pin_levelup_ltr.py MS2
"""
import json, os, sys, subprocess, copy, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
UAG = os.path.join(W, "scripts", "_tools", "UAssetGUI_110", "UAssetGUI.exe")
SRCROOT = os.path.join(W, "ui_b25478144")
OUTROOT = os.path.join(W, "bp_stage_ui_b25478144")
JS = os.path.join(W, "uag_json")
TARGETS = {
    r"MortalShell2\Content\Sparta\UI\Menu\Tooltips\WBP_Tooltip_Requirement.uasset": ["ScaleBox_Main"],
    r"MortalShell2\Content\Sparta\UI\Menu\Progression\WBP_Progression_Harbinger.uasset": ["HorizontalBox_98"],
}
PROP, ENUM, VALUE = "FlowDirectionPreference", "EFlowDirectionPreference", "LeftToRight"

def run(a):
    r = subprocess.run(a, capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or "Unhandled exception" in r.stdout + r.stderr:
        raise SystemExit("UAssetGUI failed: " + " ".join(a) + (r.stdout + r.stderr)[:600])

def main(usmap):
    os.makedirs(JS, exist_ok=True)
    for rel, names in TARGETS.items():
        src, out = os.path.join(SRCROOT, rel), os.path.join(OUTROOT, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        base = os.path.splitext(os.path.basename(rel))[0]
        js = os.path.join(JS, base + "_pin.json")
        run([UAG, "tojson", src, js, "VER_UE5_6", usmap])
        j = json.load(open(js, encoding="utf-8"))
        tpl = next(p for e in j["Exports"] for p in (e.get("Data") or []) if isinstance(p, dict) and "EnumPropertyData" in p.get("$type", ""))
        for name in names:
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
        run([UAG, "fromjson", js, out, usmap])
        if not os.path.exists(out): raise SystemExit("fromjson wrote nothing for " + rel)
        chk = os.path.join(JS, base + "_pin_check.json")
        run([UAG, "tojson", out, chk, "VER_UE5_6", usmap])
        c = json.load(open(chk, encoding="utf-8"))
        for name in names:
            e = next(x for x in c["Exports"] if x.get("ObjectName") == name)
            got = [p for p in e["Data"] if isinstance(p, dict) and p.get("Name") == PROP]
            assert got and got[0]["Value"] == VALUE, (name, got)
            print(f"verified: {base}.{name}.{PROP} = {got[0]['Value']}  (uexp {os.path.getsize(os.path.splitext(src)[0] + '.uexp')} -> {os.path.getsize(os.path.splitext(out)[0] + '.uexp')})")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "MS2")
