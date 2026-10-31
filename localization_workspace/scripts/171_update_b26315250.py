"""Rebase the Arabic locres onto game build 26315250 (2026-10-31 patch: photo mode, new dialogue, +770/-319 keys).

English source = new stock en/Game.locres. Arabic, in priority order:
  1. NEW (new_strings_b26315250.json, key -> Arabic) and OV (lines whose English changed)
  2. the corpus row for the same key, if its English is unchanged
  3. the corpus Arabic of another key with the same English text (keys the patch re-IDed)
Keys with no Arabic are left out, so the game shows their English. Validates tag/placeholder parity,
imports into the new en locres, then rewrites 04_final_corpus.jsonl to the new key set.
"""
import csv, json, re, subprocess, sys, io, os, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
NB = W + r"\b26315250_inputs"      # en.csv/en.locres = stock en Game.locres of build 26315250
L = os.path.join(W, "scripts", "_tools", "UnrealLocres.exe")
with open(NB + r"\en.csv", encoding="utf-8-sig", newline="") as f:
    r = csv.reader(f); next(r); en = {row[0]: row[1] for row in r if row}
cp = W + r"\04_final_corpus.jsonl"
corp = {}
for l in open(cp, encoding="utf-8"):
    x = json.loads(l); corp[x["key"]] = x
norm = lambda s: re.sub(r"\s+", " ", s.translate({0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"'})).strip()
by_text = collections.defaultdict(collections.Counter)
for x in corp.values(): by_text[norm(x["source_en"])][x["ar"]] += 1

OV = {
 "Dialogue_Dlg_Ruk_MapFragmentInteract_02/003F19104ABEFF9F0509EA9FCD62C50B": "ظننتُ يومًا أني سأجد البُيوض.",
 "ST_Settings/ScalabilityDesc": "يضبط مستوى الجودة العام عدة خيارات للصورة دفعة واحدة. جرّب بضعة خيارات لترى ما يناسب ذوقك وأداء جهازك.\r\n\r\n"
   "منخفض - يرفع الأداء إلى أقصى حد على حساب جودة الصورة.\r\n"
   "متوسط - يوازن بين الأداء وجودة الصورة مع تقديم الأداء. الإعداد الافتراضي.\r\n"
   "مرتفع - يوازن بين جودة الصورة والأداء مع تقديم جودة الصورة.\r\n"
   "فائق - يقدّم أعلى جودة صورة يستطيع المحرك دعمها بثبات، مع كلفة كبيرة على الأداء. يُنصح به للأجهزة القوية فقط.\r\n"
   "خيالي - يعطّل بعض التحسينات ليتجاوز بجودة الصورة مستوى «فائق». قد يسبب عدم استقرار أيًّا كان جهازك. تجريبي؛ استخدمه على مسؤوليتك.",
 "ST_Settings/FrameGenerationNeedsEnablingTooltip": "خيار توليد الإطارات المحدَّد لا يتيح تغيير عدد الإطارات المولَّدة.",
 "ST_Tarstones_Effects/TarstoneEffect_Tiltshot_1": "تدور المقذوفات المربوطة بسرعة {X}",
 "ST_Tarstones_Effects/TarstoneEffect_Tiltshot_2": "تدور المقذوفات المربوطة بسرعة {X} وتُلحق الضرر بوتيرة أعلى",
}
_nw = NB + r"\new_strings_b26315250.json"
NEW = json.load(open(_nw, encoding="utf-8")) if os.path.exists(_nw) else {}
OV.update(NEW)
missing = [k for k in OV if k not in en]
assert not missing, f"override keys not in the game's locres: {missing[:3]}"

tok = lambda s: sorted(re.findall(r"<[^>]*>|\{[^}]*\}|%[sd]", s))
rows, bad, src = [], [], collections.Counter()
for k, e in en.items():
    if k in OV: t, how = OV[k], "override"
    elif k in corp and norm(corp[k]["source_en"]) == norm(e): t, how = corp[k]["ar"], "same key"
    elif by_text[norm(e)]: t, how = by_text[norm(e)].most_common(1)[0][0], "same text"
    else: src["english (untranslated)"] += 1; continue
    src[how] += 1
    if tok(e) != tok(t): bad.append((k, f"token mismatch en={tok(e)} ar={tok(t)}"))
    rows.append((k, e, t))
print("keys", len(en), dict(src), "parity problems", len(bad))
for b in bad[:15]: print("  ", b[0][-50:], b[1][:140])
# Cutscene VO subtitles are drawn by the engine's canvas renderer (LTR, no bidi): ship them pre-shaped.
sys.path.insert(0, W + r"\scripts")
from arabic_visual import to_visual
ENGINE_SUBTITLE_TABLES = ("ST_WakeUpLevelSequence/", "ST_ShellKeeperIntroLevelSequence/")
with open(NB + r"\ar_new.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n"); w.writerow(["key", "source", "target"])
    for k, e, t in rows:
        w.writerow([k, e, to_visual(t) if k.startswith(ENGINE_SUBTITLE_TABLES) else t])
res = subprocess.run([L, "import", "en.locres", "ar_new.csv", "-o", "ar_new.locres"], capture_output=True, text=True, cwd=NB)
print(res.stdout[-120:], res.stderr[-300:])

with open(cp, "w", encoding="utf-8", newline="\n") as fh:
    for k, e, t in rows: fh.write(json.dumps({"key": k, "source_en": e, "ar": t}, ensure_ascii=False) + "\n")
print("corpus rows", len(rows))
