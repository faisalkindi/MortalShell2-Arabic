"""Build independent semantic-review chunks: does the Arabic say what the English says?

This exists because the mechanical QA (placeholders, frozen terms, punctuation) passes rows
that are fluent Arabic, use every frozen term correctly, and still state the wrong fact.
Every such row in the first build was caught by a human on screen, not by review.

Chunk size ~90 rows, not the ~400 used for edit passes: verify output is dense per row
regardless of whether the row changes, so edit-pass sizing hits the output ceiling.

Usage:
  python scripts/140_build_review_chunks.py              # whole corpus
  python scripts/140_build_review_chunks.py 1-40,90-112  # only these batches (flow-complete)
"""
import json, glob, os, io, sys, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
OUT = os.path.join(BASE, "review_chunks")
ROWS_PER_CHUNK = 90

# Facts a reviewer cannot infer from the rows but will file false findings without.
STANDING_NOTES = [
    "Franz the Blacksmith personifies his forge (Tarforge) as FEMALE. Feminine agreement in "
    "his forge lines is deliberate, though مِصهَر القار is grammatically masculine.",
    "Rows whose source_en is a bracketed dev marker ([10th Dialogue], [Quest Completed]) are "
    "unfilled VO / editor markers; the Arabic is deliberately identical to the English. "
    "[Hold] and [Press] are the exception - those ARE player-facing and are translated.",
    "Where a speaker's gender is genuinely unknown, first-person forms were deliberately "
    "written gender-neutral. Do not convert them to gendered adjectives.",
    "scene_order is the real in-scene position, parsed from the key's numeric node/line tail "
    "(Egon_Interact_09_20 -> [9,20]). It is null for the ~60% of keys that end in a 32-hex "
    "hash, because those carry NO recoverable order - do not infer sequence from row position "
    "for those, and do not file a row-misalignment finding on order alone. Where scene_order "
    "is present, consecutive values in one namespace are consecutive lines of one scene.",
]

def parse_ranges(spec):
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return out

def main():
    only = parse_ranges(sys.argv[1]) if len(sys.argv) > 1 else None

    src, meta = {}, {}
    card_by_speaker = {}
    for p in sorted(glob.glob(os.path.join(BASE, "batches", "batch_*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        b = d["batch"]
        if d.get("speaker") and d.get("character_card"):
            card_by_speaker.setdefault(d["speaker"], d["character_card"])
        meta[b] = {"group": d.get("group"), "speaker": d.get("speaker"),
                   "register": d.get("register"), "character_card": d.get("character_card")}
        if only is not None and b not in only:
            continue
        # Scene order is only recoverable when the key carries a numeric node/line tail
        # (Egon_Interact_09_20). ~60% of keys end in a 32-hex hash, which is unordered -
        # emitting a positional index for those would assert an order that does not exist
        # and quietly weaken the row-misalignment check. Those get null.
        for r in d["rows"]:
            ns = r.get("namespace") or ""
            m = re.search(r"_(\d+)_(\d+)$|_(\d+)$", r["key"].split("/")[0])
            order = None
            if m:
                g = [x for x in m.groups() if x is not None]
                order = tuple(int(x) for x in g)
            src.setdefault(r["key"], {
                "key": r["key"], "source_en": r["source_en"], "batch": b,
                "category": r.get("category"), "namespace": ns,
                "scene_order": list(order) if order else None,
            })

    # a batch with no card of its own inherits the card for that speaker from elsewhere
    for b, m in meta.items():
        if not m.get("character_card") and m.get("speaker"):
            m["character_card"] = card_by_speaker.get(m["speaker"])

    ar = {}
    for p in glob.glob(os.path.join(BASE, "translated", "batch_*.json")):
        for r in json.load(open(p, encoding="utf-8"))["rows"]:
            ar[r["key"]] = r["ar"]

    missing = [k for k in src if k not in ar]
    if missing:
        print(f"WARNING: {len(missing)} rows have no translation; excluded")

    rows = [dict(src[k], ar=ar[k]) for k in src if k in ar]
    rows.sort(key=lambda r: (r["batch"], r["namespace"], r["scene_order"] or [], r["key"]))

    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "chunk_*.json")):
        if not os.path.basename(f).startswith("chunk_9"):   # keep seeded controls
            os.remove(f)

    n = 0
    for i in range(0, len(rows), ROWS_PER_CHUNK):
        n += 1
        part = rows[i:i + ROWS_PER_CHUNK]
        json.dump({"chunk": n,
                   "standing_notes": STANDING_NOTES,
                   "batch_context": {str(b): meta[b] for b in sorted({r["batch"] for r in part})},
                   "rows": part},
                  open(os.path.join(OUT, f"chunk_{n:03d}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    print(f"batches included : {'all' if only is None else len(only)}")
    print(f"rows to review   : {len(rows)}")
    print(f"chunks written   : {n} ({ROWS_PER_CHUNK} rows each) -> review_chunks/")
    return 0

if __name__ == "__main__":
    sys.exit(main())
