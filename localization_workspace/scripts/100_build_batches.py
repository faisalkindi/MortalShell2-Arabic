"""Batch compiler - the unit of work for the real translation pass.

Every row goes to a translator WITH its compiled context, never as a naked string.
That is the thing that was missing: the previous build inherited Asmar's flat MT
prose for ~9,400 rows and only patched defects on top.

Emits batches/batch_XXX.json, each a self-contained job:
  - the rows (key, source_en, category, namespace, speaker, layout budget,
    exact placeholder list, the existing draft as REFERENCE ONLY)
  - the speaker's character card + register
  - only the glossary terms that actually occur in that batch
  - the style rules that apply to that category

Batch order follows the methodology (terminology-locking categories first,
dialogue last, grouped by speaker so voice stays consistent within a job).
"""
import json, os, re, csv, io, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
OUT = os.path.join(BASE, "batches")
PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}|%[sd]|<[^<>]+>")

# category -> (register, batch priority) ; lower priority number = translated earlier
CATEGORY_PLAN = {
    "ui_settings":              ("plain",    1),
    "ui_tutorial":              ("plain",    1),
    "system_misc":              ("plain",    2),
    "item_tarstone":            ("elevated", 3),
    "item_equipment":           ("elevated", 3),
    "npc_name":                 ("elevated", 3),
    "location_name":            ("elevated", 3),
    "skill":                    ("elevated", 4),
    "flavor_or_lore_untagged":  ("elevated", 5),
    "dialogue":                 ("per_speaker", 6),
    "dialogue_scene":           ("per_speaker", 6),
    "credits":                  ("plain",    7),
    "store_meta":               ("plain",    8),
    "other":                    ("plain",    5),
}
MAX_ROWS = 60          # small: translation output is dense, unlike an edit pass
MAX_CHARS = 9000

def load_glossary():
    g = []
    with open(os.path.join(BASE, "05_glossary.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["status"] == "approved" and r["approved_ar"]:
                g.append((r["source_term"], r["approved_ar"], r["type"]))
    return g

def load_cards():
    """Cheap YAML-ish read - we only need the per-speaker block as raw text."""
    txt = open(os.path.join(BASE, "character_cards.yaml"), encoding="utf-8").read()
    cards, cur, buf = {}, None, []
    for line in txt.splitlines():
        if line and not line[0].isspace() and line.rstrip().endswith(":"):
            if cur:
                cards[cur] = "\n".join(buf).strip()
            cur, buf = line.rstrip()[:-1], []
        elif cur:
            buf.append(line)
    if cur:
        cards[cur] = "\n".join(buf).strip()
    return cards

def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))

    rows = [json.loads(l) for l in open(os.path.join(BASE, "03_working_draft.jsonl"), encoding="utf-8") if l.strip()]
    glossary = load_glossary()
    cards = load_cards()

    # group: dialogue by speaker (voice consistency), everything else by category
    groups = defaultdict(list)
    for r in rows:
        cat = r.get("category", "other")
        reg, prio = CATEGORY_PLAN.get(cat, ("plain", 9))
        if reg == "per_speaker":
            spk = r.get("speaker") or "UNKNOWN"
            groups[(prio, f"dialogue__{spk}")].append(r)
        else:
            groups[(prio, cat)].append(r)

    batch_id = 0
    manifest = []
    for (prio, gname) in sorted(groups.keys()):
        grows = groups[(prio, gname)]
        speaker = gname.split("__", 1)[1] if gname.startswith("dialogue__") else None
        card = cards.get(speaker) if speaker else None
        register = "elevated" if (card and "elevated" in card) else \
                   ("plain" if speaker else CATEGORY_PLAN.get(gname, ("plain", 9))[0])

        chunk, chars = [], 0
        def flush():
            nonlocal chunk, chars, batch_id
            if not chunk:
                return
            batch_id += 1
            terms = []
            blob = " ".join(x["source_en"] for x in chunk)
            for term, ar, ttype in glossary:
                if re.search(r"\b" + re.escape(term) + r"\b", blob):
                    terms.append({"en": term, "ar": ar, "type": ttype})
            job = {
                "batch": batch_id,
                "group": gname,
                "speaker": speaker,
                "register": register,
                "character_card": card,
                "glossary": terms,
                "rows": [{
                    "key": x["key"],
                    "source_en": x["source_en"],
                    "category": x.get("category"),
                    "namespace": x.get("namespace"),
                    "placeholders": PLACEHOLDER_RE.findall(x["source_en"]),
                    "max_chars_hint": (28 if x.get("category") in ("ui_settings", "ui_tutorial")
                                       and len(x["source_en"]) <= 32 else None),
                    "existing_draft_reference_only": x["current_ar"],
                } for x in chunk],
            }
            with open(os.path.join(OUT, f"batch_{batch_id:03d}.json"), "w", encoding="utf-8") as f:
                json.dump(job, f, ensure_ascii=False, indent=1)
            manifest.append({"batch": batch_id, "group": gname, "speaker": speaker,
                             "register": register, "rows": len(chunk)})
            chunk, chars = [], 0

        for r in grows:
            L = len(r["source_en"]) + len(r["current_ar"])
            if chunk and (len(chunk) >= MAX_ROWS or chars + L > MAX_CHARS):
                flush()
            chunk.append(r); chars += L
        flush()

    with open(os.path.join(BASE, "batches_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print(f"batches: {len(manifest)}   rows: {sum(m['rows'] for m in manifest)}")
    by_group = defaultdict(int)
    for m in manifest:
        by_group[m["group"]] += m["rows"]
    for g, n in sorted(by_group.items(), key=lambda x: -x[1])[:22]:
        print(f"   {g:34} {n:5}")

if __name__ == "__main__":
    main()
