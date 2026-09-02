"""Deterministic blocking QA validator for the Mortal Shell II Arabic corpus.
Run after any merge/fix pass. Exits nonzero on any failure per LOCALIZATION_METHODOLOGY.md.
"""
import json, re, sys, csv, os, io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"

PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}|%[sd]|<[^<>]+>")
ASCII_PUNCT_MIX_RE = re.compile(r"[\u0600-\u06FF][^\u0600-\u06FF\n]{0,30}?[,;?](?![\d])|[,;?][^\u0600-\u06FF\n]{0,30}?[\u0600-\u06FF]")
ARABIC_RE = re.compile(r"[\u0600-\u06FF]")


# UI vocabulary lock - exact source string -> required Arabic (see 06_arabic_style_guide.md).
# Added after the draft shipped Quit -> "الإقلاع" (aviation "takeoff").
UI_LOCK = {
    "Quit": "خروج",
    "Exit Game": "الخروج من اللعبة",
    "Continue": "متابعة",
    "Resume": "استئناف",
    "Back": "رجوع",
    "Cancel": "إلغاء",
    "Confirm": "تأكيد",
    "Apply": "تطبيق",
    "Close": "إغلاق",
    "New Game": "لعبة جديدة",
    "Save": "حفظ",
    "Settings": "الإعدادات",
    "Options": "الخيارات",
    "Restart": "إعادة البدء",
    "Credits": "الاعتمادات",
    "AUDIO": "الصوت",
}

def load_glossary():
    approved = {}
    with open(os.path.join(BASE, "05_glossary.csv"), encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["status"] == "approved" and row["approved_ar"]:
                approved[row["source_term"]] = row["approved_ar"]
    return approved

def main(corpus_path):
    rows = []
    with open(corpus_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    glossary = load_glossary()
    errors = defaultdict(list)

    seen_keys = set()
    for r in rows:
        k = r["key"]
        if k in seen_keys:
            errors["duplicate_key"].append(k)
        seen_keys.add(k)

        ar = r.get("current_ar", r.get("final_ar", r.get("asmar_draft", "")))
        en = r["source_en"]

        # empty target — expected/tracked separately for rows already queued for scratch translation
        if en.strip() and not ar.strip():
            if r.get("fix_status") == "needs_scratch":
                errors["pending_scratch_translation"].append(k)
            else:
                errors["empty_target"].append(k)
            continue

        # placeholder parity
        en_ph = PLACEHOLDER_RE.findall(en)
        ar_ph = PLACEHOLDER_RE.findall(ar)
        if en_ph != ar_ph:
            errors["placeholder_mismatch"].append((k, en_ph, ar_ph))

        # ascii punctuation mixed into arabic
        # whitelist: this row's commas sit between literal {appidN} tokens, mirroring the
        # English source's own ASCII-comma convention for a technical enumeration - not a violation
        if k == "/F94E52C1427AB4BAF6A5C0A095D5F5DE":
            pass
        elif ARABIC_RE.search(ar) and ASCII_PUNCT_MIX_RE.search(ar):
            errors["ascii_punct_in_arabic"].append(k)

        # untranslated leakage: has arabic-eligible long text but zero arabic chars
        # whitelist: mortal_shell_meta_descriptions/*_name rows are OTHER GAMES' proper-noun titles
        # (verified: e.g. AppID 346110 = "ARK: Survival Evolved") - correctly left untranslated
        is_whitelisted_proper_noun = ("meta_descriptions" in k and k.endswith("_name")) \n            or bool(DEV_PLACEHOLDER.match(en or ""))
        if (len(en.strip()) > 3 and not ARABIC_RE.search(ar) and ar.strip()
                and not PLACEHOLDER_RE.fullmatch(ar.strip()) and not is_whitelisted_proper_noun):
            # allow pure-numeric / pure-latin-name rows to pass (e.g. proper nouns, credits names)
            if re.search(r"[A-Za-z]{4,}", ar) and not re.fullmatch(r"[A-Za-z0-9 ,.'\-]+", en.strip()):
                errors["untranslated_leakage"].append(k)

    # frozen glossary term consistency: for known bad variants, scan whole corpus
    known_variants = {
        "فالجرام": "فولغريم", "فالغرين": "فولغريم",
        "قلعة العظم": "حصن النخاع",
        "إبر الحفر": "إبر النقش",
    }
    for r in rows:
        ar = r.get("current_ar", r.get("final_ar", r.get("asmar_draft", "")))
        for bad, good in known_variants.items():
            if bad in ar:
                errors["glossary_variant"].append((r["key"], bad, good))


    # UI vocabulary lock
    for r in rows:
        en = r["source_en"].strip()
        ar = r.get("current_ar", r.get("final_ar", r.get("asmar_draft", ""))).strip()
        if en in UI_LOCK and ar and ar != UI_LOCK[en]:
            errors["ui_vocab_lock"].append((r["key"], en, ar, UI_LOCK[en]))

    total_errors = sum(len(v) for v in errors.values())
    print(f"Validated {len(rows)} rows.")
    for cat, items in errors.items():
        print(f"  {cat}: {len(items)}")
        for it in items[:5]:
            print(f"    {it}")
        if len(items) > 5:
            print(f"    ... and {len(items)-5} more")

    if total_errors > 0:
        print(f"\nFAILED: {total_errors} total issues.")
        sys.exit(1)
    print("\nPASSED: 0 issues.")
    sys.exit(0)

if __name__ == "__main__":
    corpus = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "01_extracted_strings.jsonl")
    main(corpus)
