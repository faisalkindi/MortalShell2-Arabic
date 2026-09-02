"""Enforce frozen glossary renderings across the corpus.

The Asmar draft transliterates several names inconsistently (Egon as إيجون vs the
frozen إيغون, Genessa as جنسا, Merrick as ميرك, ...). Blind string replacement is
unsafe where the wrong form is a PREFIX of the right one (لوسيا -> لوسيان would
turn an already-correct لوسيان into لوسيانن), so each rule uses a negative
lookahead for the completing letters.

Operates in place on 03_working_draft.jsonl `current_ar`. Idempotent.
"""
import json, re, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PATH = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace\03_working_draft.jsonl"

# (wrong form, correct form, completing-suffix guard or None)
RULES = [
    ("إيجون",   "إيغون",    None),
    ("جنسا",    "جينيسا",   None),
    ("فرنز",    "فرانز",    None),
    ("جورف",    "غورف",     None),
    ("هيلجا",   "هيلغا",    None),
    ("بروكسما", "بروكسيما", None),
    ("ميرك",    "ميريك",    "ي"),   # ميريك already correct -> don't rewrite
    ("لوسيا",   "لوسيان",   "ن"),
    ("غراغ",    "غراغو",    "و"),
    ("فلا",     "فلاس",     "س"),
]

def main():
    rows = [json.loads(l) for l in open(PATH, encoding="utf-8") if l.strip()]
    counts = {}
    for wrong, right, guard in RULES:
        pat = re.escape(wrong) + (f"(?!{re.escape(guard)})" if guard else "")
        rx = re.compile(pat)
        n = 0
        for r in rows:
            ar = r["current_ar"]
            if wrong not in ar:
                continue
            new = rx.sub(right, ar)
            if new != ar:
                r["current_ar"] = new
                n += 1
        counts[f"{wrong} -> {right}"] = n

    with open(PATH, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    for k, v in counts.items():
        print(f"  {k:26} rows changed: {v}")
    print(f"\ntotal rules applied: {sum(counts.values())}")

    # guard check: correct forms must not have been double-suffixed
    bad = []
    for r in rows:
        for _, right, _ in RULES:
            if right + right[-1] in r["current_ar"]:
                bad.append((r["key"], right))
    print("double-suffix corruption:", bad if bad else "none")

if __name__ == "__main__":
    main()
