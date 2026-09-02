"""A/B the flow pass: Opus vs Sonnet on the same batch.

Shows only rows where the two models actually differ, so the comparison is about
real disagreement rather than scrolling identical lines. Also reports churn rate -
a model that rewrites everything is not automatically better, just louder.
"""
import json, io, sys, os, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
BATCH = 10
PH = re.compile(r"\{[^{}]*\}|%[sd]|<[^<>]+>")

def load(p):
    return {r["key"]: r for r in json.load(open(p, encoding="utf-8"))["rows"]}

def main():
    src = {r["key"]: r for r in json.load(
        open(os.path.join(BASE, f"batches/batch_{BATCH:03d}.json"), encoding="utf-8"))["rows"]}
    base = {r["key"]: r["ar"] for r in json.load(
        open(os.path.join(BASE, f"translated/batch_{BATCH:03d}.json"), encoding="utf-8"))["rows"]}
    op = load(os.path.join(BASE, f"flow_ab/opus_batch{BATCH:03d}.json"))
    so = load(os.path.join(BASE, f"flow_ab/sonnet_batch{BATCH:03d}.json"))

    op_changed = sum(1 for k in base if op.get(k, {}).get("ar") != base[k])
    so_changed = sum(1 for k in base if so.get(k, {}).get("ar") != base[k])
    print(f"rows: {len(base)}")
    print(f"opus changed:   {op_changed}  ({op_changed/len(base)*100:.0f}%)")
    print(f"sonnet changed: {so_changed}  ({so_changed/len(base)*100:.0f}%)")

    # integrity: neither model may break placeholders
    for name, m in (("opus", op), ("sonnet", so)):
        bad = [k for k in base
               if k in m and PH.findall(src[k]["source_en"]) != PH.findall(m[k]["ar"])]
        print(f"{name} placeholder breaks: {len(bad)} {bad[:3] if bad else ''}")

    both = [k for k in base if op.get(k, {}).get("ar") != so.get(k, {}).get("ar")]
    print(f"\nrows where the two models DISAGREE: {len(both)}\n")
    for k in both:
        print(f"KEY {k}")
        print(f"  EN     : {src[k]['source_en'][:150]}")
        print(f"  BASE   : {base[k][:150]}")
        print(f"  OPUS   : {op.get(k,{}).get('ar','(missing)')[:150]}")
        print(f"  SONNET : {so.get(k,{}).get('ar','(missing)')[:150]}")
        wo, ws = op.get(k, {}).get("why"), so.get(k, {}).get("why")
        if wo: print(f"    opus why  : {wo[:110]}")
        if ws: print(f"    sonnet why: {ws[:110]}")
        print()

if __name__ == "__main__":
    main()
