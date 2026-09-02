import json, sys

def apply(batch_num, ar_list):
    src = f"batches/batch_{batch_num:03d}.json"
    dst = f"translated/batch_{batch_num:03d}.json"
    d = json.load(open(src, encoding="utf-8"))
    rows = d["rows"]
    if len(rows) != len(ar_list):
        raise SystemExit(f"batch {batch_num}: {len(rows)} rows but {len(ar_list)} translations given")
    out_rows = []
    for r, ar in zip(rows, ar_list):
        out_rows.append({"key": r["key"], "ar": ar})
    out = {"batch": batch_num, "rows": out_rows}
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"wrote {dst} ({len(out_rows)} rows)")
