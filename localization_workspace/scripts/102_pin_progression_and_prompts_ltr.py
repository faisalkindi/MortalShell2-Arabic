"""Put two-sided screens back in English order where Arabic mirroring swapped them (build 25478144+).

WBP_MGT_Progression (Mether's Breath level-up screen): HB_Menu = [Harbinger panel (LB: level up)] [spacer]
  [Shell panel (RB: distribute shell points, RT: refund)]. Mirrored, the LB panel sat on the right and the RB panel
  on the left (video 2026-10-07). HB_Menu -> LeftToRight. Overlay_Left/Overlay_Right stay inherited (LTR) so
  Anim_FadeIn slides them in from the English sides; the panels' contents go back to the culture (RTL) one level
  down, so everything inside the two panels stays exactly as before.
WBP_ConfirmationPrompt_Default/_Requirement/_ShellStory (e.g. quit): the two buttons sit in BP_HB_Options, which
  steps with d-pad left = -1 / right = +1. Mirrored, left moved right. ScaleBox_Options (its parent; no retainer
  in between) -> LeftToRight. _Dismissable has one button; _MultiOptions has a retainer strip (not touched).
Property-only, same technique as 93b/96/97/101.
Usage: 102_pin_progression_and_prompts_ltr.py MS2   (input ui2_b25478144/..., output bp_stage_ui2_b25478144/...)
"""
import json, os, sys, subprocess, copy, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
UAG = os.path.join(W, "scripts", "_tools", "UAssetGUI_110", "UAssetGUI.exe")
SRCROOT, OUTROOT, JS = os.path.join(W, "ui2_b25478144"), os.path.join(W, "bp_stage_ui2_b25478144"), os.path.join(W, "uag_json")
U = r"MortalShell2\Content\Sparta\UI\Menu"
TARGETS = {
    U + r"\Progression\WBP_MGT_Progression.uasset": {"HB_Menu": "LeftToRight", "ScaleBox_UserScale_HarbingerMenu": "Culture",
                                                      "ScaleBox_UserScale_Prompts": "Culture", "ScaleBox_UserScale_ShellMenu": "Culture"},
    U + r"\Misc\WBP_ConfirmationPrompt_Default.uasset": {"ScaleBox_Options": "LeftToRight"},
    U + r"\Misc\WBP_ConfirmationPrompt_Requirement.uasset": {"ScaleBox_Options": "LeftToRight"},
    U + r"\Misc\WBP_ConfirmationPrompt_ShellStory.uasset": {"ScaleBox_Options": "LeftToRight"},
}
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

def diff(a, b):
    """Every difference between two UAssetGUI dumps, ignoring offsets/sizes."""
    skip, out = {"SerialOffset", "SerialSize", "ScriptSerializationStartOffset", "ScriptSerializationEndOffset", "OtherAssetsFailedToAccess"}, []
    def cmp(x, y, p=""):
        if type(x) != type(y): out.append(p); return
        if isinstance(x, dict):
            for k in set(x) | set(y):
                if k in skip: continue
                if k not in x or k not in y: out.append(p + "/" + k); continue
                cmp(x[k], y[k], p + "/" + k)
        elif isinstance(x, list):
            if len(x) != len(y): out.append(p); return
            for i, (u, v) in enumerate(zip(x, y)): cmp(u, v, p + f"[{i}]")
        elif x != y: out.append(p)
    cmp(a, b)
    return out

def main(usmap):
    for rel, names in TARGETS.items():
        src, out = os.path.join(SRCROOT, rel), os.path.join(OUTROOT, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        base = os.path.splitext(os.path.basename(rel))[0]
        js, chk = os.path.join(JS, base + "_pin.json"), os.path.join(JS, base + "_pin_check.json")
        for f in (js, chk, out, os.path.splitext(out)[0] + ".uexp"):
            if os.path.exists(f): os.remove(f)
        run([UAG, "tojson", src, js, "VER_UE5_6", usmap]); wait(js)
        j = json.load(open(js, encoding="utf-8")); orig = copy.deepcopy(j)
        tpl = next(p for e in j["Exports"] for p in (e.get("Data") or []) if isinstance(p, dict) and "EnumPropertyData" in p.get("$type", ""))
        touched = []
        for name, value in names.items():
            hits = [i for i, e in enumerate(j["Exports"]) if e.get("ObjectName") == name]
            assert len(hits) == 1, (base, name, len(hits))
            e = j["Exports"][hits[0]]; assert "RawExport" not in e["$type"], name
            data = e["Data"]
            assert not any(isinstance(p, dict) and p.get("Name") == PROP for p in data), name + " already pinned"
            p = copy.deepcopy(tpl); p["Name"] = PROP; p["EnumType"] = ENUM; p["Value"] = value
            for k in ("ArrayIndex", "DuplicationIndex"):
                if k in p: p[k] = 0
            if "IsZero" in p: p["IsZero"] = False
            pos = next((i for i, q in enumerate(data) if isinstance(q, dict) and q.get("Name") == "bIsVariable"), len(data))
            data.insert(pos, p); touched.append(hits[0])
        for n in (PROP, ENUM, *names.values()):
            if n not in j["NameMap"]: j["NameMap"].append(n)
        json.dump(j, open(js, "w", encoding="utf-8"), indent=1)
        run([UAG, "fromjson", js, out, usmap]); wait(out); wait(os.path.splitext(out)[0] + ".uexp")
        run([UAG, "tojson", out, chk, "VER_UE5_6", usmap]); wait(chk)
        c = json.load(open(chk, encoding="utf-8"))
        for name, value in names.items():
            e = next(x for x in c["Exports"] if x.get("ObjectName") == name)
            got = [p for p in e["Data"] if isinstance(p, dict) and p.get("Name") == PROP]
            assert got and got[0]["Value"] == value, (name, got)
        allowed = {f"/Exports[{i}]/Data" for i in touched} | {"/NameMap", "/Generations[0]/NameCount", "/SoftObjectPathsOffset",
                                                               "/SearchableNamesOffset", "/ThumbnailTableOffset", "/ImportTypeHierarchiesOffset"}
        extra = [d for d in diff(orig, c) if d not in allowed]
        assert not extra, (base, extra[:5])
        print(f"{base}: {', '.join(f'{n}={v}' for n, v in names.items())} | uexp",
              os.path.getsize(os.path.splitext(src)[0] + ".uexp"), "->", os.path.getsize(os.path.splitext(out)[0] + ".uexp"), "| no other changes")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "MS2")
