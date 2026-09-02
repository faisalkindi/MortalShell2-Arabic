"""Merge all register_patch_*.jsonl files into 03_working_draft.jsonl.
Each patch line: {"key": ..., "old_ar": ..., "new_ar": ...}
Verifies old_ar matches current state before applying (catches stale patches
from a stage that ran before another patch already touched the same row).
"""
import json, glob, os, re

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}|%[sd]|<[^<>]+>")

def main():
    draft_path = os.path.join(BASE, "03_working_draft.jsonl")
    rows = [json.loads(l) for l in open(draft_path, encoding="utf-8") if l.strip()]
    by_key = {r["key"]: r for r in rows}

    patch_files = sorted(glob.glob(os.path.join(BASE, "register_patch_*.jsonl")))
    print(f"found {len(patch_files)} patch files")

    applied = 0
    stale = 0
    placeholder_rejected = 0
    unknown_key = 0

    for pf in patch_files:
        name = os.path.basename(pf)
        file_applied = 0
        for line in open(pf, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            p = json.loads(line)
            key = p["key"]
            if key not in by_key:
                unknown_key += 1
                print(f"  [{name}] UNKNOWN KEY: {key}")
                continue
            row = by_key[key]
            current = row.get("current_ar", "")
            if p.get("old_ar", current) != current:
                stale += 1
                print(f"  [{name}] STALE (current changed since patch was written): {key}")
                continue
            # placeholder integrity guard
            en_ph = PLACEHOLDER_RE.findall(row["source_en"])
            new_ph = PLACEHOLDER_RE.findall(p["new_ar"])
            if en_ph != new_ph:
                placeholder_rejected += 1
                print(f"  [{name}] REJECTED (placeholder mismatch): {key}")
                print(f"    EN placeholders: {en_ph}")
                print(f"    new_ar placeholders: {new_ph}")
                continue
            row["current_ar"] = p["new_ar"]
            row["register_pass_source"] = name
            applied += 1
            file_applied += 1
        print(f"  {name}: {file_applied} applied")

    with open(draft_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print()
    print(f"total applied: {applied}")
    print(f"stale (skipped): {stale}")
    print(f"placeholder-rejected (skipped): {placeholder_rejected}")
    print(f"unknown keys (skipped): {unknown_key}")

if __name__ == "__main__":
    main()
