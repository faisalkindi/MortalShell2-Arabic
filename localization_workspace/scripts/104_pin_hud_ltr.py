"""In-game HUD: English layout for the bars, item slots and currencies under Arabic (build 25478144+).

Symptoms (Arabic, photos 2026-10-12): health/stamina bars fill from the right and the status icons sit at the bars' far
end; the item slots run Y/LT/X/LT+RT reversed, their counts sit on the left (the LT item's "42" hides behind the
picture) and the whole row is pushed toward the middle; the currency row is reversed.
Causes:
 - WBP_Player_HUD places each group on CanvasPanel_Player_HUD_Primary (anchors are not mirrored by SConstraintCanvas)
   and nudges some with render translations (ScaleBox_AbilityIndicators X=+120, ScaleBox_Currency X=+100). Slate
   negates a child's X translation when its parent arranges right-to-left, and WBP_AbilityIndicators' own row adds
   +400/+300/+200/+100 per slot: under RTL the slots slide up to ~640 units toward the middle. ProgressBar flips its
   LeftToRight fill under RTL (SProgressBar.cpp).
 - WBP_AbilityIndicator and WBP_Player_HUD_Currency have an InvalidationBox at the root. When it caches it is an
   invalidation root and restarts its content at the culture direction unless that content (its first child) has a
   preference of its own (SlateInvalidationRoot.cpp / SInvalidationPanel.cpp, UE 5.6).
Fix (property-only, same technique as 93b/96/97/101/102):
  WBP_Player_HUD          CanvasPanel_Player_HUD_Primary = LeftToRight (bars, item slots, charges, currencies,
                          crosshair, night-mode icon: English layout and nudges); the groups that carry Arabic text
                          or were not reported keep the culture, exactly as before: ScaleBox_BossHealth,
                          ScaleBox_EffectBars, ScaleBox_ContexualPrompt = Culture.
                          CanvasPanel_Player_HUD_Secondary (dialogue, notifications, prompts) is untouched.
  WBP_AbilityIndicator    SizeBox_AbilityIndicator (under the InvalidationBox) = LeftToRight: count bottom-right.
  WBP_Player_HUD_Currency VerticalBox_0 (under the InvalidationBox) = LeftToRight: "17472 coins  2956 gloom".
Usage: 104_pin_hud_ltr.py MS2   (input hud_b25478144/..., stock legacy copies; output bp_stage_hud_b25478144/...)
"""
import json, os, sys, subprocess, copy, time, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
UAG = os.path.join(W, "scripts", "_tools", "UAssetGUI_110", "UAssetGUI.exe")
SRCROOT, OUTROOT, JS = os.path.join(W, "hud_b25478144"), os.path.join(W, "bp_stage_hud_b25478144"), os.path.join(W, "uag_json")
U = r"MortalShell2\Content\Sparta\UI"
TARGETS = {
    U + r"\Player\WBP_Player_HUD.uasset": {"CanvasPanel_Player_HUD_Primary": "LeftToRight", "ScaleBox_BossHealth": "Culture",
                                           "ScaleBox_EffectBars": "Culture", "ScaleBox_ContexualPrompt": "Culture"},
    U + r"\Abilites\WBP_AbilityIndicator.uasset": {"SizeBox_AbilityIndicator": "LeftToRight"},
    U + r"\Player\WBP_Player_HUD_Currency.uasset": {"VerticalBox_0": "LeftToRight"},
}
PROP, ENUM = "FlowDirectionPreference", "EFlowDirectionPreference"
TMP = os.path.join(os.environ["TEMP"], "ms2_104")

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
        # parse each asset alone: with another target's class asset beside it, UAssetGUI decodes that BP instance and
        # then cannot write it back
        src, out = os.path.join(TMP, os.path.basename(rel)), os.path.join(OUTROOT, rel)
        shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP)
        for ext in (".uasset", ".uexp"): shutil.copyfile(os.path.splitext(os.path.join(SRCROOT, rel))[0] + ext, os.path.splitext(src)[0] + ext)
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
    shutil.rmtree(TMP, ignore_errors=True)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "MS2")
