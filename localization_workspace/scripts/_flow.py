# -*- coding: utf-8 -*-
"""Flow-pass helpers: dump a batch side-by-side; apply keyed edits + write flow log."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load(n):
    src = json.load(open(f"{ROOT}/batches/batch_{n:03d}.json", encoding="utf-8"))
    tr  = json.load(open(f"{ROOT}/translated/batch_{n:03d}.json", encoding="utf-8"))
    return src, tr

def dump(n):
    src, tr = _load(n)
    armap = {r["key"]: r["ar"] for r in tr["rows"]}
    print(f"### BATCH {n}  group={src.get('group')} speaker={src.get('speaker')} register={src.get('register')}")
    cc = src.get("character_card")
    if cc: print("CARD:", json.dumps(cc, ensure_ascii=False))
    for i, r in enumerate(src["rows"]):
        k = r["key"]
        print(f"--{i} [{k}] ({r.get('category')})")
        print("EN:", r["source_en"])
        print("AR:", armap.get(k))

TAG = re.compile(r"(<[^>]*>|\{[A-Za-z0-9_]+\}|%[sd])")

def sig(s):
    return sorted(TAG.findall(s))

def apply(n, edits, why):
    """edits: {key: new_ar}; why: {key: reason}"""
    src, tr = _load(n)
    srcmap = {r["key"]: r["source_en"] for r in src["rows"]}
    log = []
    for r in tr["rows"]:
        k = r["key"]
        if k in edits and edits[k] != r["ar"]:
            log.append({"key": k, "before": r["ar"], "after": edits[k], "why": why.get(k, "flow")})
            r["ar"] = edits[k]
    bad = [k for k in edits if k not in srcmap]
    if bad: raise SystemExit(f"unknown keys: {bad}")
    with open(f"{ROOT}/translated/batch_{n:03d}.json", "w", encoding="utf-8") as f:
        json.dump(tr, f, ensure_ascii=False, indent=1)
    with open(f"{ROOT}/flow_logs/flow_batch_{n:03d}.json", "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    print(f"batch {n}: {len(log)}/{len(tr['rows'])} rows changed")
    return log

def verify(lo, hi):
    tot = chg = 0; errs = []
    for n in range(lo, hi + 1):
        src, tr = _load(n)
        sk = [r["key"] for r in src["rows"]]
        tk = [r["key"] for r in tr["rows"]]
        if sk != tk: errs.append(f"batch {n}: key order/set mismatch")
        armap = {r["key"]: r["ar"] for r in tr["rows"]}
        for r in src["rows"]:
            a, b = sig(r["source_en"]), sig(armap[r["key"]])
            if a != b: errs.append(f"batch {n} [{r['key']}]: placeholders {a} != {b}")
        tot += len(sk)
        p = f"{ROOT}/flow_logs/flow_batch_{n:03d}.json"
        if os.path.exists(p): chg += len(json.load(open(p, encoding="utf-8")))
    print(f"rows={tot} changed={chg} errors={len(errs)}")
    for e in errs[:60]: print(" ", e)
    return errs

if __name__ == "__main__":
    if sys.argv[1] == "dump": dump(int(sys.argv[2]))
    elif sys.argv[1] == "verify": verify(int(sys.argv[2]), int(sys.argv[3]))
