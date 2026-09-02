"""Corpus-wide duplicate-English divergence check.

If the same English string is translated two different ways, one of them is usually wrong.
This is the cheapest detector we have for a whole class of bugs - drifted terminology,
half-applied fixes, and Arabic pasted onto the wrong key - and it needs no scene order,
which most of this corpus does not have.

Credit: proposed by a reviewer after the confirmed row-swap turned out to be detectable
this way via its second corroboration.
"""
import json, glob, os, io, sys, re
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"

def norm(s):
    return re.sub(r"\s+", " ", s).strip()

def main():
    src = {}
    for p in sorted(glob.glob(os.path.join(BASE, "batches", "batch_*.json"))):
        for r in json.load(open(p, encoding="utf-8"))["rows"]:
            src[r["key"]] = r["source_en"]
    ar = {}
    for p in sorted(glob.glob(os.path.join(BASE, "translated", "batch_*.json"))):
        for r in json.load(open(p, encoding="utf-8"))["rows"]:
            ar[r["key"]] = r["ar"]

    groups = defaultdict(list)
    for k, e in src.items():
        if k in ar and norm(e):
            groups[norm(e)].append((k, ar[k]))

    dup = {e: v for e, v in groups.items() if len(v) > 1}
    diverging = {e: v for e, v in dup.items() if len({norm(a) for _, a in v}) > 1}

    print(f"distinct English strings   : {len(groups)}")
    print(f"appearing more than once   : {len(dup)}")
    print(f"with DIVERGENT Arabic      : {len(diverging)}")
    print()
    for e, v in sorted(diverging.items(), key=lambda x: -len(x[1]))[:40]:
        print(f"EN  {e[:96]}")
        for k, a in v:
            print(f"    {a[:92]}")
        print()
    json.dump({e: [{"key": k, "ar": a} for k, a in v] for e, v in diverging.items()},
              open(os.path.join(BASE, "duplicate_divergence.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("full report: duplicate_divergence.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
