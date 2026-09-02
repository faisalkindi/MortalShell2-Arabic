"""Stage 4 (deterministic mechanical post-process) per LOCALIZATION_METHODOLOGY.md.
Fixes: glossary-variant sweep, ASCII '?' -> Arabic '؟' normalization, one known duplicate-tag bug.
Idempotent. Emits per-row audit log. Never touches placeholder/tag content itself.
Outputs 03_working_draft.jsonl with a `current_ar` field + `fix_status`.
"""
import json, re, os, unicodedata

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"

GLOSSARY_VARIANTS = {
    "الأصداف": "الأغلفة",  # seashells -> our frozen Shell term (Zhirelle dialogue mistranslation, 6 rows)
    "فالجرام": "فولغريم",
    "فالغرين": "فولغريم",
    "فالغريم": "فولغريم",   # normalize the "correct-looking" variant too - freeze on فولغريم exactly
    "قلعة العظم": "حصن النخاع",
    "إبر الحفر": "إبر النقش",
}

PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}|%[sd]|<[^<>]+>")

ASCII_TO_ARABIC_PUNCT = {"?": "؟", ",": "،", ";": "؛"}

def fix_ascii_punct(text):
    if not any(c in text for c in ASCII_TO_ARABIC_PUNCT):
        return text, False
    if not re.search(r"[؀-ۿ]", text):
        return text, False
    spans = [m.span() for m in PLACEHOLDER_RE.finditer(text)]
    def in_span(i):
        return any(s <= i < e for s, e in spans)
    def between_placeholders(i):
        before = text[:i].rstrip()
        after = text[i+1:].lstrip()
        return before.endswith("}") and after.startswith("{")
    out = []
    changed = False
    for i, ch in enumerate(text):
        if ch in ASCII_TO_ARABIC_PUNCT and not in_span(i) and not (ch == "," and between_placeholders(i)):
            out.append(ASCII_TO_ARABIC_PUNCT[ch])
            changed = True
        else:
            out.append(ch)
    return "".join(out), changed

# Known one-off content bugs found by manual QA (not sweepable mechanically)
KNOWN_ROW_FIXES = {
    "ST_Dialogue_Baghead/Baghead_Ineract_02_60": "في أي مكان إلا هنا.",
    "Dialogue_DLG_SmertMemory_TheRedemption_SMM7_HierarchEnters/E7C60C7345A4EC2D740FE8883054E2F5": "ماذا؟ أنت حي؟",
    "Dialogue_Dlg_Ruk_Boss_TarGolem_Interact/FF009B234026874085735DA89C79E8FA": "شيء خطير.",
    "Dialogue_DLG_Tavern_Drunk_Interact01/32706B3D4633BAF33434998A5A1D7FCA": "أظن أنك أُغمي عليك فحسب، أليس كذلك؟",
    "ST_Dialogue_Egon/Egon_Interact_Lazlo_10_10": "كنتَ هناك أيضًا.",
    "ST_Dialogue_Egon/Egon_PostTribute_Lazlo_17_20": "أنت تعرف ما الذي سيفعله.",
    "Dialogue_Dlg_Gorf_Interact_10/CB310E484E7C0A1987647884B35B0748": "لن أحتاج إلى المزيد من الفطر.",
    "Dialogue_Dlg_Gorf_Interact_10/F173BB5345F472AC32E587B5ECB2FB9C": "ولا إلى أي جرعات شهية.",
    "Dialogue_Dlg_Gorf_Interact_10/837840824D30F790A56D3191BA2E6887": "ربما يشفيك أيضًا.",
    "Dialogue_Dlg_Shellkeeper_Interact_01/286A90FC47EBC7873955C0A485613E8C": "أنا زيريل، حارسة الأغلفة.",
    "ST_Core_Shells/KnightLadyTagline": "الغاية تمنح الروح شكلها.",  # Proxima motto - Asmar draft had it swapped with an unrelated Smert skin name (Sanguine Prophet)
    # Smert skill line: draft has a duplicated <Resolve></> tag pair not present in source
    "ST_Skills_Smert/ShellSkillSmertDevotion_Effect_2": (
        "أثناء كونك <Faith>مؤمنًا</>، هناك احتمال قدره {Y} لأن تملأ أي زيادة في <Resolve>العزيمة</> بالكامل"
    ),
}

# Rows whose Asmar "translation" is stale/wrong content (patch-notes drift, not a mechanical fix case)
FORCE_SCRATCH_KEYS = {
    "ST_Core_WelcomeScreen/WelcomeScreenDescription_1",  # Arabic text is an OLDER patch's welcome message, unrelated to current EN source
}

def main():
    corpus_path = os.path.join(BASE, "01_extracted_strings.jsonl")
    rows = [json.loads(l) for l in open(corpus_path, encoding="utf-8") if l.strip()]

    audit = []
    scratch = []
    out_rows = []

    for r in rows:
        key = r["key"]
        bare_key = key[1:] if key.startswith("/") else key
        en = r["source_en"]
        ar = r["asmar_draft"]
        fix_status = "clean"

        if bare_key in FORCE_SCRATCH_KEYS or r["asmar_missing"] or not ar.strip():
            fix_status = "needs_scratch"
            scratch.append(r)
            out_rows.append({**r, "current_ar": "", "fix_status": fix_status})
            continue

        if bare_key in KNOWN_ROW_FIXES:
            new_ar = KNOWN_ROW_FIXES[bare_key]
            if new_ar != ar:
                audit.append({"key": key, "rule": "known_row_fix", "before": ar, "after": new_ar})
            ar = new_ar
            fix_status = "mechanically_fixed"

        # glossary variant sweep (idempotent - safe to run repeatedly)
        for bad, good in GLOSSARY_VARIANTS.items():
            if bad in ar and bad != good:
                new_ar = ar.replace(bad, good)
                if new_ar != ar:
                    audit.append({"key": key, "rule": "glossary_variant", "bad": bad, "good": good})
                    ar = new_ar
                    fix_status = "mechanically_fixed"

        # ASCII '?' -> Arabic '؟'
        new_ar, changed = fix_ascii_punct(ar)
        if changed:
            audit.append({"key": key, "rule": "ascii_punct", "before": ar, "after": new_ar})
            ar = new_ar
            fix_status = "mechanically_fixed"

        # placeholder-integrity re-check post-fix (never let a mechanical fix break parity)
        if PLACEHOLDER_RE.findall(en) != PLACEHOLDER_RE.findall(ar):
            fix_status = "needs_scratch"
            scratch.append({**r, "asmar_draft": ar})
            out_rows.append({**r, "current_ar": "", "fix_status": fix_status})
            continue

        out_rows.append({**r, "current_ar": ar, "fix_status": fix_status})

    with open(os.path.join(BASE, "03_working_draft.jsonl"), "w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(os.path.join(BASE, "50_mechanical_fix_audit.jsonl"), "w", encoding="utf-8") as f:
        for a in audit:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    with open(os.path.join(BASE, "02_needs_scratch_translation.jsonl"), "w", encoding="utf-8") as f:
        seen = set()
        for r in scratch:
            if r["key"] in seen:
                continue
            seen.add(r["key"])
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"total rows: {len(out_rows)}")
    print(f"mechanical fixes applied (audit entries): {len(audit)}")
    print(f"rows needing scratch translation: {len(set(r['key'] for r in scratch))}")

if __name__ == "__main__":
    main()
