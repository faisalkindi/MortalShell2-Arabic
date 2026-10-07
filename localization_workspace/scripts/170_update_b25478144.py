"""Rebase the Arabic locres onto game build 25478144 (2026-09-25 patch).

English source = new stock en/Game.locres; Arabic = shipped corpus by key, plus OVERRIDES for
the strings the patch added or materially changed. Whitespace-only English changes keep the
existing Arabic. Validates tag/placeholder parity for every row, then imports into the new en locres.
"""
import csv, json, re, subprocess, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"
NB = W + r"\b25478144_inputs"      # en.csv/en.locres = stock en Game.locres of build 25478144; ar_old.csv = shipped ar-MA locres exported
L = os.path.join(W, "scripts", "_tools", "UnrealLocres.exe")
rd = lambda p: {r["key"]: r["source"] for r in csv.DictReader(open(p, encoding="utf-8", newline=""))}
en = rd(NB + r"\en.csv"); ar = rd(NB + r"\ar_old.csv")

K = lambda stem: next(k for k in en if k.endswith(stem))
OV = {
 K("Dialogue_Dlg_Hub_Ruk_Greeting_01/00FA914047DD9EF6B440C58CDD7384A6"): "روك.",
 K("ST_Core_Misc/MiscCoOp"): "تعاوني",
 K("ST_Core_Misc/MiscCoOpExperimental"): "تعاوني (تجريبي)",
 K("ST_Settings_Advanced/ST_AdaptiveDifficulty_Name"): "الصعوبة التكيّفية",
 K("ST_Settings_Advanced/ST_AdaptiveDifficulty_Description"): "يضبط هذا الإعداد التجريبي توازن اللعبة تلقائيًا ليصبح أسهل أو أصعب بحسب أدائك.\r\n\r\nتُعدَّل الصعوبة آليًا بحسب سجلّك. فكلما زاد عدد مرات موتك، خُفِّف التحدي مؤقتًا. وكلما هزمتَ أعداءً أكثر دون أن تموت، ازداد التحدي، حتى يتجاوز الصعوبة المعتادة بكثير.\r\n\r\n(لا يُخفَّف الوضع الليلي أبدًا، بل يزداد صعوبةً فقط.)",
 K("ST_Settings_Advanced/ST_NightModeAmbience_Name"): "أجواء الوضع الليلي",
 K("ST_Settings_Advanced/ST_NightModeAmbience_AshNight"): "ليلة الرماد",
 K("ST_Settings_Advanced/ST_NightModeAmbience_DayLight"): "ضوء النهار",
 K("ST_Settings_Advanced/ST_NightModeAmbience_OvercastNight"): "الغيم الأبديّ",
 K("ST_Settings_Advanced/ST_NightModeAmbience_NightLight"): "ضوء القمر",
 # same English line already shipped under another key
 K("Dialogue_DLG_HubCultist_NewGameGreeting/0129565E4839F38170EB4AB56251675E"): "أهلًا بعودتكِ، أيتها الأُخَيّة الكُبرى.",
 K("Dialogue_Dlg_Ruk_Interact_01/9D73C97F48CE0D6AAF4A57849D50B730"): "واصل.",
 K("Dialogue_Dlg_Ruk_Interact_00/A119C3324EDC8F12C6C3EC8A46DD739D"): "واصل.",
 K("Dialogue_Dlg_Ruk_Interact_01/4E9D820948BDF6EC3EAEBEBBBEA602A2"): "اذهب الآن.",
 K("Dialogue_Dlg_Ruk_Interact_MapFragment_01/78EFB5CC46E6A059F13088AC78DCEA29"): "سيُكشف كل شيء... مع الوقت.",
 K("Dialogue_Dlg_Ruk_Interact_MapFragment_01/2C40E6674012AF8A86B232B38E214A6C"): "فتّش هذه الأرض.",
 K("Dialogue_Dlg_Ruk_Interact_MapFragment_01/3F78CE9E4489889F1E98BB8889F4AEB3"): "معًا...",
 K("Dialogue_Dlg_Ruk_Interact_MapFragment_01/383A484B40BA43B9D98066937453732F"): "سنرسم خريطة هذا المكان.",
 # materially changed English
 K("Dialogue_Dlg_Ruk_Boss_ScholarPrince_Interact/1B78CD0B47ED207CF3E66095C6ACB59C"): "هذا الأمير العالم...",
 K("gland/SacredGlandEffect"): "بقيّةٌ من المُكرَّم. هي مفتاح إطلاق قوّةٍ عظيمة.",
 K("gland/SacredGland_CathedralEffect"): "بقيّةٌ من المُكرَّم. هي مفتاح إطلاق قوّةٍ عظيمة.",
 K("gland/SacredGland_SnowEffect"): "بقيّةٌ من المُكرَّم. هي مفتاح إطلاق قوّةٍ عظيمة.",
 K("ST_Core_Tarstones/ID_Melee_DualWieldProficiencyDesc"): "تُصيب سلسلة هجمات <Bold>سلاحك</> الخفيفة <Bold>مرتين</>، وتُلحق كل ضربة <Bold>80%</> من الضرر، ويقلّ اكتساب <Resolve>العزيمة</> إلى <Bold>25%</>.",
 K("ST_Core_WelcomeScreen/WelcomeScreenDescription_1"): "أهلًا بعودتكم أيها النُّذُر\r\n\r\nتحديثٌ جديد صدر، يجلب إصلاحاتٍ واسعة للاستقرار وللحالات التي يتعذّر فيها التقدّم، وتعديلاتٍ على القتال والضربات المضادة، وإعادة صياغةٍ للمواجهات، ومراجعةً شاملة للتصادم وكشف الإصابات، وتحسيناتٍ في الأداء والصوت وجودة التجربة عمومًا.\r\n\r\nخيارٌ تجريبي جديد: الصعوبة التكيّفية خيارٌ يضبط التحدي بحسب طريقة لعبك الفعلية، في الاتجاهين. فإن واصلتَ هزيمة الأعداء دون أن تموت، اشتدّت مقاومة العالم أكثر مما كانت لتكون (بما يتجاوز الحدّ الأقصى المعتاد بكثير). وإن متَّ مرارًا، خفّ التحدي بهدوء حتى تستعيد توازنك. وهو معطَّل افتراضيًا ويوجد ضمن الخيارات، فتبقى اللعبة كما عهدتها ما لم تُفعّله.\r\n\r\nكعادتنا، في هذا التحديث تفاصيل أكثر مما يسعنا سرده هنا، فراجعوا ملاحظات الرقعة الكاملة على الإنترنت لمعرفة التفاصيل كلها.",
 K("ST_Skills_Sariel/SarielSkillAfflictionDesc"): "يمتد الضرر الذي يُلحَق بعدو <Curse>ملعون</> إلى جميع الأعداء الملعونين الآخرين، أو يُصيب الأعداء القريبين غير الملعونين بـ<Curse>اللعنة</>.",
 K("ST_Skills_Sariel/SarielSkillAffliction_Effect_1"): "يتلقى الأعداء <Curse>الملعونون</> الآخرون حتى {X} من الضرر الأصلي، ويتلقى غير الملعونين {Y} من طبقات <Curse>اللعنة</>.",
 K("ST_Skills_Sariel/SarielSkillMaxPain"): "كلّما ازداد <Pain>ألم</> سارييل، ازداد سرعةً:",
 K("ST_Tarstones_Effects/TarstoneEffectHeavyHoldAttackMelee_1"): "تُعيد الهجمة المشحونة {Y} من <Health>الصحة</> عند توجيه <Critical>ضربة حاسمة</>.",
 K("ST_Tarstones_Effects/TarstoneEffectHeavyHoldAttackMelee_2"): "تمنح الهجمة المشحونة {X} من تقليل الضرر وتُعيد {Y} من <Health>الصحة</> عند توجيه <Critical>ضربة حاسمة</>.",
}
# Later translation fixes (readability/rhyme/meaning), key -> Arabic; wins over everything above.
_fx = W + r"\translation_fixes_b25478144.json"
if os.path.exists(_fx):
    FIXES = json.load(open(_fx, encoding="utf-8"))
    missing = [k for k in FIXES if k not in en]
    assert not missing, f"fix keys not in the game's locres: {missing[:3]}"
    OV.update(FIXES)
tok = lambda s: sorted(re.findall(r"<[^>]*>|\{[^}]*\}|%[sd]", s))
rows, bad, nov = [], [], 0
for k, e in en.items():
    t = OV.get(k) or ar.get(k)
    if k in OV: nov += 1
    if t is None: bad.append((k, "NO ARABIC")); continue
    if tok(e) != tok(t):
        # tags legitimately differ only where English casing differs from the shipped tag content - report all
        bad.append((k, f"token mismatch en={tok(e)} ar={tok(t)}"))
    rows.append((k, e, t))
print("keys", len(rows), "overrides", nov, "parity problems", len(bad))
for b in bad[:15]: print("  ", b[0][-50:], b[1][:140])
# Cutscene VO subtitles (SoundWave.Subtitles) are drawn by the engine's canvas renderer: LTR, no bidi.
# Ship those 15 strings pre-shaped and in visual order (see scripts/arabic_visual.py); corpus stays logical.
sys.path.insert(0, W + r"\scripts")
from arabic_visual import to_visual
ENGINE_SUBTITLE_TABLES = ("ST_WakeUpLevelSequence/", "ST_ShellKeeperIntroLevelSequence/")
nvis = 0
with open(NB + r"\ar_new.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n"); w.writerow(["key", "source", "target"])
    for k, e, t in rows:
        if k.startswith(ENGINE_SUBTITLE_TABLES): t = to_visual(t); nvis += 1
        w.writerow([k, e, t])
print("visual-order subtitle strings:", nvis)
res = subprocess.run([L, "import", "en.locres", "ar_new.csv", "-o", "ar_new.locres"], capture_output=True, text=True, cwd=NB)
print(res.stdout[-120:], res.stderr[-300:])

# keep 04_final_corpus.jsonl in step with the shipped locres
cp = W + r"\04_final_corpus.jsonl"
cur = {}
for l in open(cp, encoding="utf-8"):
    x = json.loads(l); cur[x["key"]] = x
for k, e, t in rows: cur[k] = {"key": k, "source_en": e, "ar": t}
with open(cp, "w", encoding="utf-8", newline="\n") as fh:
    for k in en: fh.write(json.dumps(cur[k], ensure_ascii=False) + "\n")
print("corpus rows", len(en))
