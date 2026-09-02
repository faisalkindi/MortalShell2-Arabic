"""Fix rows where the Asmar draft stored Arabic as pre-shaped Presentation Forms
(U+FB50-FDFF / U+FE70-FEFF) in VISUAL order instead of plain logical-order Unicode.
This engine (UE5) has a native shaper - feeding it presentation-forms text causes
double-shaping (broken/disconnected glyphs). Fix: NFKC-normalize (recovers base
letterforms) then reverse (undoes the visual-order storage) -> logical-order text.

Operates directly on 03_working_draft.jsonl's `current_ar` field IN PLACE.
Does NOT touch source_en/asmar_draft or re-derive from them - safe to run any time
after register patches have been merged, without losing that work.

Validation gate (per the debake methodology): only accept a fix if the result
contains zero remaining presentation-forms codepoints and at least one Arabic letter.
"""
import json, re, os, unicodedata

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
PF_RE = re.compile(r"[\uFB50-\uFDFF\uFE70-\uFEFF]")
ARABIC_LETTER_RE = re.compile(r"[\u0621-\u064A]")

# One known post-fix artifact: reversing merges "إلى" + "الارتباط" into a doubled
# alef ("االرتباط"). Manual correction after the automated fix, keyed by row key.
POST_FIX_OVERRIDES = {
    "ST_ShellKeeperIntroLevelSequence/Line07_YearningForYourBond": "يتوقون إلى الارتباط بك.",
}

def debake(text):
    fixed = unicodedata.normalize("NFKC", text)[::-1]
    if PF_RE.search(fixed):
        return None  # validation failed - leave untouched
    if not ARABIC_LETTER_RE.search(fixed):
        return None
    return fixed

def main():
    path = os.path.join(BASE, "03_working_draft.jsonl")
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]

    fixed_count = 0
    failed_validation = []
    for r in rows:
        ar = r.get("current_ar", "")
        if not PF_RE.search(ar):
            continue
        bare_key = r["key"][1:] if r["key"].startswith("/") else r["key"]
        if bare_key in POST_FIX_OVERRIDES:
            r["current_ar"] = POST_FIX_OVERRIDES[bare_key]
            r["debaked"] = True
            fixed_count += 1
            continue
        fixed = debake(ar)
        if fixed is None:
            failed_validation.append(r["key"])
            continue
        r["current_ar"] = fixed
        r["debaked"] = True
        fixed_count += 1

    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"fixed: {fixed_count}")
    print(f"failed validation (left untouched): {len(failed_validation)}")
    for k in failed_validation:
        print("  ", k)

if __name__ == "__main__":
    main()
