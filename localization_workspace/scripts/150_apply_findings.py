"""Apply semantic-review findings to the translations.

Two independent review passes run over every chunk (different models, neither reading the
other). Their findings are UNIONED here, because measurement on a seeded control showed the
models are complementary: each caught real bugs the other missed.

Safety rules:
  - a finding is applied ONLY if the row's current Arabic still matches what the reviewer
    saw. If the text moved since the review, the finding is stale and is skipped, not forced.
  - if the two passes disagree on the same key, neither is applied - it is reported for a
    human ruling instead.
  - placeholders must survive; a suggestion that breaks them is rejected.
  - a suggestion may not introduce an Arabic term that the glossary freezes for a DIFFERENT
    English concept. A reviewer once "fixed" Disciple to المُريد, which is Acolyte - Tiel's
    title. Character-title terms are the dangerous ones: they read as naming a specific person.
  - a suggestion may not REMOVE the currently-frozen rendering for a term that is in the row's
    English. Reviews are written against a snapshot of the glossary; when a term is re-frozen
    afterwards (Hexapod went descriptive -> transliterated so a pun would survive), stale
    suggestions would silently roll it back. The glossary on disk always wins.
"""
import json, glob, os, io, sys, re, csv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
PH = re.compile(r"\{[^{}]*\}|%[sd]|<[^<>]+>")

def load_frozen():
    """every frozen term: (english, approved_arabic)"""
    path = os.path.join(BASE, "05_glossary.csv")
    return [(r["source_term"].strip(), r["approved_ar"].strip())
            for r in csv.DictReader(open(path, encoding="utf-8")) if r["approved_ar"].strip()]

def load_titles():
    """frozen renderings that name a SPECIFIC character/rank - never valid for another term"""
    out = []
    path = os.path.join(BASE, "05_glossary.csv")
    for row in csv.DictReader(open(path, encoding="utf-8")):
        if row["type"] in ("character", "honorific/title") and row["approved_ar"].strip():
            out.append((row["source_term"].strip(), row["approved_ar"].strip()))
    return out

def main():
    titles = load_titles()
    frozen = load_frozen()
    src = {}
    for p in sorted(glob.glob(os.path.join(BASE, "batches", "batch_*.json"))):
        for r in json.load(open(p, encoding="utf-8"))["rows"]:
            src[r["key"]] = r["source_en"]

    by_key = {}
    for p in sorted(glob.glob(os.path.join(BASE, "review_findings", "*chunk_*.json"))):
        if "chunk_900" in p:            # seeded control, already handled
            continue
        for f in json.load(open(p, encoding="utf-8")).get("findings", []):
            if not f.get("suggested_ar"):
                continue
            by_key.setdefault(f["key"], []).append(f)

    conflicts = {k: v for k, v in by_key.items()
                 if len({x["suggested_ar"].strip() for x in v}) > 1}

    applied, stale, ph_bad, title_clash, stale_term = 0, [], [], [], []
    for p in sorted(glob.glob(os.path.join(BASE, "translated", "batch_*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        n = 0
        for r in d["rows"]:
            fs = by_key.get(r["key"])
            if not fs or r["key"] in conflicts:
                continue
            f = fs[0]
            if r["ar"].strip() != f.get("ar", "").strip():
                stale.append(r["key"]); continue
            new = f["suggested_ar"]
            if PH.findall(src.get(r["key"], "")) != PH.findall(new):
                ph_bad.append(r["key"]); continue
            en = src.get(r["key"], "")
            clash = next((t for t, ar in titles
                          if ar and ar in new and ar not in r["ar"]
                          and not re.search(re.escape(t), en, re.I)), None)
            if clash:
                title_clash.append((r["key"], clash)); continue
            rollback = next((t for t, ar in frozen
                             if ar and ar in r["ar"] and ar not in new
                             and re.search(re.escape(t), en, re.I)), None)
            if rollback:
                stale_term.append((r["key"], rollback)); continue
            r["ar"] = new; n += 1
        if n:
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            applied += n

    print(f"findings with a suggestion : {len(by_key)}")
    print(f"applied                    : {applied}")
    print(f"stale (row moved since)    : {len(stale)}")
    print(f"rejected (placeholder)     : {len(ph_bad)}")
    print(f"rejected (title clash)     : {len(title_clash)}")
    for k, t in title_clash:
        print(f"     {k[-45:]} would import the frozen term for '{t}'")
    print(f"rejected (stale glossary)  : {len(stale_term)}")
    for k, t in stale_term:
        print(f"     {k[-45:]} would roll back the frozen term for '{t}'")
    print(f"conflicts (needs a ruling) : {len(conflicts)}")
    for k, v in conflicts.items():
        print(f"  {k[-50:]}")
        for x in v:
            print(f"     [{x['type']}] {x['suggested_ar'][:70]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
