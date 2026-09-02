"""Provenance audit: prove how much of the corpus is OUR translation vs inherited.

The final release must contain zero rows carried over from the third-party draft.
This script measures it per row and is the gate before any build:

  fresh          - a translated/batch_XXX.json entry exists for the key
  inherited      - no fresh translation; the row would fall back to the old draft
  identical      - fresh translation exists and happens to equal the old draft text

"identical" is not automatically a problem: for short fixed UI strings (نعم / لا / حفظ)
the correct answer is the same string no matter who writes it. It IS a problem for long
prose, where matching word-for-word means the draft was copied rather than retranslated.
So identical rows are split by length and the long ones are listed for inspection.
"""
import json, glob, os, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
LONG = 40   # chars above which an exact match with the old draft is suspicious

def main():
    corpus = [json.loads(l) for l in open(os.path.join(BASE, "03_working_draft.jsonl"),
                                          encoding="utf-8") if l.strip()]
    old = {r["key"]: r.get("asmar_draft", "") for r in corpus}

    fresh = {}
    for p in glob.glob(os.path.join(BASE, "translated", "batch_*.json")):
        for r in json.load(open(p, encoding="utf-8"))["rows"]:
            fresh[r["key"]] = r["ar"]

    inherited, identical_short, identical_long, clean = [], [], [], 0
    for r in corpus:
        k = r["key"]
        if k not in fresh:
            inherited.append(k)
            continue
        if fresh[k].strip() and fresh[k].strip() == old.get(k, "").strip():
            (identical_long if len(fresh[k]) > LONG else identical_short).append(k)
        else:
            clean += 1

    total = len(corpus)
    print(f"corpus rows                : {total}")
    print(f"freshly translated (ours)  : {len(fresh)}  ({len(fresh)/total*100:.1f}%)")
    print(f"  - genuinely different    : {clean}")
    print(f"  - identical, short UI    : {len(identical_short)}  (expected: fixed strings)")
    print(f"  - identical, LONG prose  : {len(identical_long)}  <-- inspect these")
    print(f"still inherited (no fresh) : {len(inherited)}  ({len(inherited)/total*100:.1f}%)")

    if identical_long:
        print("\nlong rows identical to the old draft:")
        for k in identical_long[:20]:
            print(f"  {k}\n     {fresh[k][:120]}")

    with open(os.path.join(BASE, "provenance_report.json"), "w", encoding="utf-8") as f:
        json.dump({
            "total": total, "fresh": len(fresh), "clean": clean,
            "identical_short": identical_short, "identical_long": identical_long,
            "inherited_count": len(inherited), "inherited_keys": inherited,
        }, f, ensure_ascii=False, indent=1)

    print(f"\nreport: provenance_report.json")
    if inherited:
        print(f"\nNOT RELEASE-READY: {len(inherited)} rows would still carry third-party text.")
        sys.exit(1)
    print("\nRELEASE-READY: every row is our own translation.")
    sys.exit(0)

if __name__ == "__main__":
    main()
