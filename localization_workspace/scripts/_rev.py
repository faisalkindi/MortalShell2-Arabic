# -*- coding: utf-8 -*-
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def dump(n):
    d = json.load(open(f"{ROOT}/review_chunks/chunk_{n:03d}.json", encoding="utf-8"))
    print(f"### CHUNK {n}  rows={len(d['rows'])}")
    for i, r in enumerate(d["rows"]):
        print(f"--{i} [{r['key']}] b{r['batch']} so={r['scene_order']}")
        print("EN:", r["source_en"])
        print("AR:", r["ar"])
def write(n, findings):
    d = json.load(open(f"{ROOT}/review_chunks/chunk_{n:03d}.json", encoding="utf-8"))
    keys = {r["key"]: r for r in d["rows"]}
    out = []
    for f in findings:
        r = keys[f["key"]]
        out.append({"key": f["key"], "type": f["type"], "severity": f["severity"],
                    "source_en": r["source_en"], "ar": r["ar"],
                    "issue": f["issue"], "suggested_ar": f["suggested_ar"]})
    res = {"chunk": n, "rows_reviewed": len(d["rows"]), "findings": out}
    os.makedirs(f"{ROOT}/review_findings", exist_ok=True)
    with open(f"{ROOT}/review_findings/chunk_{n:03d}.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(f"chunk {n}: {len(out)} findings / {len(d['rows'])} rows")
if __name__ == "__main__":
    dump(int(sys.argv[1]))
