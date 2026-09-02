"""Pin the two tab strips to LeftToRight so RB/LB still step visually right/left under RTL.

Why: Slate.ShouldFollowCultureByDefault=1 mirrors every Inherit HorizontalBox under ar-MA,
which is what we want everywhere EXCEPT the tab strips: the game steps tabs by index on
RB/LB, so a mirrored strip walks the wrong way. Setting FlowDirectionPreference=LeftToRight
on just those two HorizontalBoxes keeps their child order fixed. Explicit LTR is identical to
today's behaviour for every other language, so nothing changes outside Arabic.

Route: UAssetGUI 1.1.0 (tojson/fromjson) WITH the game's .usmap - these assets are
unversioned, so without mappings every export is an opaque RawExport. No byte splicing.

Targets:
  WBP_MGT_Main.uasset     export 'HorizontalBox_TopBar'   (game menu: bag / tarstones / map)
  WBP_MGT_Options.uasset  export 'HorizontalBox_0'        (options: game / display / audio / ...)
"""
import json, os, sys, glob, shutil, subprocess, copy, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
UAG  = os.path.join(BASE, "scripts", "_tools", "UAssetGUI_110", "UAssetGUI.exe")
SRC  = os.path.join(BASE, "ui_tabs", "MortalShell2", "Content", "Sparta", "UI", "Menu")
OUT  = os.path.join(BASE, "bp_stage_flow", "MortalShell2", "Content", "Sparta", "UI", "Menu")
JS   = os.path.join(BASE, "uag_json")
TARGETS = {"WBP_MGT_Main": "HorizontalBox_TopBar", "WBP_MGT_Options": "HorizontalBox_0"}
ENUM, VALUE, PROP = "EFlowDirectionPreference", "EFlowDirectionPreference::LeftToRight", "FlowDirectionPreference"

def run(args):
    r = subprocess.run(args, capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or "Unhandled exception" in (r.stdout + r.stderr):
        raise SystemExit(f"UAssetGUI failed: {' '.join(args)}\n{(r.stdout + r.stderr)[:800]}")

def find_enum_template(j):
    """clone the JSON shape of an existing enum-typed property from the same file"""
    for e in j["Exports"]:
        for p in e.get("Data") or []:
            if isinstance(p, dict) and "EnumPropertyData" in p.get("$type", ""):
                return p
    return None

def main(usmap):
    # UAssetGUI 1.1.0 CLI takes a mappings NAME resolved from %LOCALAPPDATA%/UAssetGUI/Mappings, not a path
    if "/" in usmap or "\\" in usmap or usmap.endswith(".usmap"):
        raise SystemExit("pass the mappings NAME (e.g. MS2) present in %LOCALAPPDATA%/UAssetGUI/Mappings")
    os.makedirs(JS, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    for asset, target in TARGETS.items():
        src = os.path.join(SRC, asset + ".uasset")
        js  = os.path.join(JS, asset + ".typed.json")
        run([UAG, "tojson", src, js, "VER_UE5_6", usmap])
        j = json.load(open(js, encoding="utf-8"))
        exps = j["Exports"]
        raw = [e["ObjectName"] for e in exps if "RawExport" in e.get("$type", "")]
        tgt = next((e for e in exps if e.get("ObjectName") == target), None)
        if tgt is None:
            raise SystemExit(f"{asset}: export {target} not found")
        if "RawExport" in tgt.get("$type", ""):
            raise SystemExit(f"{asset}: target {target} is Raw - mappings not applied")
        print(f"{asset}: {len(exps)} exports, {len(raw)} raw (BP-generated, passed through untouched), target is typed")
        data = tgt.setdefault("Data", [])
        if any(isinstance(p, dict) and p.get("Name") == PROP for p in data):
            print(f"{asset}/{target}: {PROP} already present, setting value")
            for p in data:
                if p.get("Name") == PROP: p["Value"] = VALUE; p["EnumType"] = ENUM
        else:
            tpl = find_enum_template(j)
            if tpl is None:
                raise SystemExit(f"{asset}: no EnumPropertyData template in file - stop and inspect {js}")
            p = copy.deepcopy(tpl)
            p["Name"] = PROP; p["EnumType"] = ENUM; p["Value"] = VALUE
            for k in ("ArrayIndex", "DuplicationIndex"):
                if k in p: p[k] = 0
            if "IsZero" in p: p["IsZero"] = False
            data.append(p)
            print(f"{asset}/{target}: appended {PROP}={VALUE} (template from '{tpl.get('Name')}')")
        for n in (PROP, ENUM, VALUE):                       # names must exist in the NameMap
            if n not in j["NameMap"]: j["NameMap"].append(n)
        json.dump(j, open(js, "w", encoding="utf-8"), indent=1)
        dst = os.path.join(OUT, asset + ".uasset")
        run([UAG, "fromjson", js, dst, usmap])
        # read back and confirm the property is there
        chk = os.path.join(JS, asset + ".check.json")
        run([UAG, "tojson", dst, chk, "VER_UE5_6", usmap])
        c = json.load(open(chk, encoding="utf-8"))
        t2 = next(e for e in c["Exports"] if e.get("ObjectName") == target)
        got = [p for p in t2.get("Data") or [] if isinstance(p, dict) and p.get("Name") == PROP]
        assert got and got[0].get("Value") == VALUE, f"{asset}: readback failed: {got}"
        print(f"  verified in written asset: {target}.{PROP} = {got[0]['Value']}")
    print("\nOK - patched assets in bp_stage_flow/. Next: add BP_UIO_Language + SpartaSettingsSaveObject(swap) + scriptobjects.bin, retoc to-zen, verify, install.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "MS2")
