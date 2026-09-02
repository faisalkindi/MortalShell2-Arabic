"""Safe corpus sweep helper.

Chained str.replace() is unsafe: an earlier replacement can produce text that a later
pattern matches again, silently corrupting rows. It bit this project twice - "موجة صدم"
-> "موجة صدمية" re-matched into "صدميةية", and "زيّ الفاني" -> "زيّ الفانين" into
"الفانينن". Both shipped into the corpus before a duplicate-check caught them.

apply_map() does ONE simultaneous pass with a single alternation regex, longest pattern
first, so no replacement output is ever re-scanned.
"""
import json, glob, os, io, sys, re

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"

def apply_map(mapping, where=None, label="sweep"):
    """mapping: {find: replace}. where: fn(source_en, key) -> bool, or None for all rows."""
    src = {}
    for p in sorted(glob.glob(os.path.join(BASE, "batches", "batch_*.json"))):
        for r in json.load(open(p, encoding="utf-8"))["rows"]:
            src[r["key"]] = r["source_en"]

    pat = re.compile("|".join(re.escape(k) for k in
                              sorted(mapping, key=len, reverse=True)))
    changed = 0
    for p in sorted(glob.glob(os.path.join(BASE, "translated", "batch_*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        n = 0
        for r in d["rows"]:
            if where and not where(src.get(r["key"], ""), r["key"]):
                continue
            new = pat.sub(lambda m: mapping[m.group(0)], r["ar"])
            if new != r["ar"]:
                r["ar"] = new
                n += 1
        if n:
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            changed += n
    print(f"{label}: {changed} rows")
    return changed
