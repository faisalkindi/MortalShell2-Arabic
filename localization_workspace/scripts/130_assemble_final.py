"""Assemble the final Arabic corpus from OUR translations only.

Hard guarantee requested by the owner: nothing from the third-party draft may reach
the release. This script is the only sanctioned path to a shippable locres, and it
CANNOT fall back to the old draft - if a key has no fresh translation, it aborts.

Refuses to produce output when:
  - any corpus key is missing from translated/          (would otherwise inherit)
  - any translated row is empty
  - placeholders differ from the English source
  - a long row is byte-identical to the old draft       (possible copy, needs review)

Writes 04_final_corpus.jsonl (key, source_en, ar) for the locres build.
"""
import json, glob, os, io, sys, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
PH = re.compile(r"\{[^{}]*\}|%[sd]|<[^<>]+>")
LONG = 40
ALLOWLIST = os.path.join(BASE, "provenance_allowlist.json")  # reviewed convergence rows

def main():
    corpus = [json.loads(l) for l in open(os.path.join(BASE, "03_working_draft.jsonl"),
                                          encoding="utf-8") if l.strip()]
    fresh = {}
    for p in glob.glob(os.path.join(BASE, "translated", "batch_*.json")):
        for r in json.load(open(p, encoding="utf-8"))["rows"]:
            fresh[r["key"]] = r["ar"]

    allow = set()
    if os.path.exists(ALLOWLIST):
        allow = set(json.load(open(ALLOWLIST, encoding="utf-8")))

    missing, empty, ph_bad, copied = [], [], [], []
    out = []
    for r in corpus:
        k, en = r["key"], r["source_en"]
        if k not in fresh:
            missing.append(k); continue
        ar = fresh[k]
        if en.strip() and not ar.strip():
            empty.append(k); continue
        if PH.findall(en) != PH.findall(ar):
            ph_bad.append(k); continue
        if (len(ar) > LONG and ar.strip() == r.get("asmar_draft", "").strip()
                and k not in allow):
            copied.append(k); continue
        out.append({"key": k, "source_en": en, "ar": ar})

    print(f"corpus rows      : {len(corpus)}")
    print(f"assembled        : {len(out)}")
    print(f"missing fresh    : {len(missing)}")
    print(f"empty            : {len(empty)}")
    print(f"placeholder bad  : {len(ph_bad)}")
    print(f"identical to old : {len(copied)}  (long rows, not allowlisted)")

    blocking = len(missing) + len(empty) + len(ph_bad) + len(copied)
    if blocking:
        print(f"\nREFUSING TO BUILD: {blocking} rows fail the provenance/integrity gate.")
        if missing:
            print(f"  first missing keys: {missing[:5]}")
        if copied:
            print(f"  identical-to-draft keys: {copied[:5]}")
            print("  review each; if it is genuine convergence on a formulaic line,")
            print("  add the key to provenance_allowlist.json with a reason.")
        sys.exit(1)

    with open(os.path.join(BASE, "04_final_corpus.jsonl"), "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("\nOK: 04_final_corpus.jsonl written - 100% our own translation.")
    sys.exit(0)

if __name__ == "__main__":
    main()
