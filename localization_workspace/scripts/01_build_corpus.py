"""Build 01_extracted_strings.jsonl from the exported locres CSVs + Asmar draft.
Case B (English source): join en/fr/es/it by key for gender/number cross-reference.
Uses REAL StringTable namespaces (not GUID heuristics) for category/speaker extraction.
"""
import csv, json, re, os
from collections import Counter

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
EXT = os.path.join(BASE, "extracted")

def load_csv(path):
    d = {}
    with open(path, encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if not row:
                continue
            d[row[0]] = row[1] if len(row) > 1 else ""
    return d

en = load_csv(os.path.join(EXT, "en.csv"))
fr = load_csv(os.path.join(EXT, "fr.csv"))
es = load_csv(os.path.join(EXT, "es.csv"))
it = load_csv(os.path.join(EXT, "it.csv"))
asmar = load_csv(os.path.join(EXT, "asmar_en.csv"))

PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}|%[sd]|<[^<>]+>")
GUID_RE = re.compile(r"^[0-9A-F]{32}$")

DIALOGUE_SPEAKER_TABLES = {
    "ST_Dialogue_Egon": "Egon",
    "ST_Dialogue_Blacksmith": "Blacksmith",
    "ST_Dialogue_Hilga": "Hilga",
    "ST_Dialogue_Baghead": "Baghead",
    "ST_GorfDialogues": "Gorf",
}
SKILL_SHELL_TABLES = {
    "ST_Skills_Tiel": "Tiel", "ST_Skills_Eredrim": "Eredrim", "ST_Skills_Proxima": "Proxima",
    "ST_Skills_Gragu": "Gragu", "ST_Skills_Smert": "Smert", "ST_Skills_Lazlo": "Lazlo",
    "ST_Skills_Sariel": "Sariel", "ST_Skill_Genessa": "Genessa",
}

def classify(key):
    body = key[1:] if key.startswith("/") else key
    if "/" in body:
        ns, k = body.rsplit("/", 1)
    else:
        ns, k = "", body

    if GUID_RE.match(ns) or (not ns and GUID_RE.match(k)):
        return {"category": "flavor_or_lore_untagged", "namespace": "", "speaker": None, "scene": None}

    if ns in DIALOGUE_SPEAKER_TABLES:
        return {"category": "dialogue", "namespace": ns, "speaker": DIALOGUE_SPEAKER_TABLES[ns], "scene": None}
    if ns in SKILL_SHELL_TABLES:
        return {"category": "skill", "namespace": ns, "speaker": SKILL_SHELL_TABLES[ns], "scene": None}
    if ns.startswith("ialogue_Dlg_") or ns.startswith("Dlg_") or "Dlg_" in ns:
        # e.g. Dlg_Hub_Cultist_Weirdo_GraguReact / Dlg_Baghead_Interact_MoonshineQuestStart
        parts = re.split(r"Dlg_", ns, maxsplit=1)[-1].split("_")
        return {"category": "dialogue_scene", "namespace": ns, "speaker": parts[0] if parts else None, "scene": ns}
    if ns.startswith("ST_Core_Tarstones") or ns.startswith("ST_Tarstones_Effects") or ns.startswith("ST_Core_Menu_Tarstones") or ns.startswith("ST_Core_Tarforge") or ns.startswith("ST_Core_Menu_Tarforge"):
        return {"category": "item_tarstone", "namespace": ns, "speaker": None, "scene": None}
    if ns.startswith("ST_Core_Weapons") or ns.startswith("ST_Core_Sidearms") or ns.startswith("ST_Core_Shells"):
        return {"category": "item_equipment", "namespace": ns, "speaker": None, "scene": None}
    if ns.startswith("ST_Core_MiniBosses") or ns.startswith("ST_Core_NpcNames"):
        return {"category": "npc_name", "namespace": ns, "speaker": None, "scene": None}
    if ns.startswith("ST_Core_Dungeons") or ns.startswith("ST_Core_Locations") or ns.startswith("ST_LandingAreaNames"):
        return {"category": "location_name", "namespace": ns, "speaker": None, "scene": None}
    if ns.startswith("ST_Core_Tutorials") or ns.startswith("ST_Core_Interactions") or ns.startswith("ST_Core_Actions") or ns.startswith("ST_Core_Player_Abilities"):
        return {"category": "ui_tutorial", "namespace": ns, "speaker": None, "scene": None}
    if ns.startswith("ST_Settings") or ns.startswith("ST_Core_Options_Game") or ns.startswith("ST_Core_Progression") or ns.startswith("ST_Core_Stats"):
        return {"category": "ui_settings", "namespace": ns, "speaker": None, "scene": None}
    if ns.startswith("ST_CreditsRoles") or ns.startswith("ST_CreditsTitles"):
        return {"category": "credits", "namespace": ns, "speaker": None, "scene": None}
    if ns.startswith("ortal_shell_meta_descriptions"):
        return {"category": "store_meta", "namespace": ns, "speaker": None, "scene": None}
    if ns.startswith("ST_StatusEffects") or ns.startswith("ST_Core_PPItems") or ns.startswith("ST_Core_Misc"):
        return {"category": "system_misc", "namespace": ns, "speaker": None, "scene": None}
    return {"category": "other", "namespace": ns, "speaker": None, "scene": None}

rows = []
for key, src in en.items():
    meta = classify(key)
    rows.append({
        "key": key,
        "source_en": src,
        "fr": fr.get(key, ""),
        "es": es.get(key, ""),
        "it": it.get(key, ""),
        "asmar_draft": asmar.get(key, ""),
        "asmar_missing": key not in asmar,
        "has_placeholder": bool(PLACEHOLDER_RE.search(src)),
        "char_len": len(src),
        **meta,
    })

out_path = os.path.join(BASE, "01_extracted_strings.jsonl")
with open(out_path, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

cats = Counter(r["category"] for r in rows)
print("total rows:", len(rows))
for c, n in cats.most_common():
    print(f"  {c}: {n}")

# QA: rows needing FULL retranslation (asmar draft missing/empty, or placeholder-broken)
def ph_list(s):
    return PLACEHOLDER_RE.findall(s)

needs_scratch = []
for r in rows:
    a = r["asmar_draft"]
    if r["asmar_missing"] or not a.strip():
        needs_scratch.append(r)
    elif r["has_placeholder"] and ph_list(r["source_en"]) != ph_list(a):
        needs_scratch.append(r)

print()
print("rows needing from-scratch translation (missing/empty/placeholder-broken in Asmar draft):", len(needs_scratch))
with open(os.path.join(BASE, "02_needs_scratch_translation.jsonl"), "w", encoding="utf-8") as f:
    for r in needs_scratch:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# speaker/namespace breakdown for dialogue
speakers = Counter(r["speaker"] for r in rows if r["category"] in ("dialogue","dialogue_scene","skill") and r["speaker"])
print()
print("=== speaker/scene-prefix breakdown (dialogue_scene + dialogue) ===")
for s, n in speakers.most_common(40):
    print(n, s)
