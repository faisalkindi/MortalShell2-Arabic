# -*- coding: utf-8 -*-
"""Apply the 47 from-scratch translations (Asmar draft had these missing/empty/stale)
into 03_working_draft.jsonl. Human/context-driven translation using the frozen
glossary (05_glossary.csv) + character_cards.yaml + style guide.
"""
import json, os

BASE = r"C:\Users\Faisal\Ai\Mods Dev\MortalShell2\localization_workspace"

TRANSLATIONS = {
    "gland/MethersSeveranceDescription": "عظمة هشة تشبه النصل. في يدٍ ماهرة، يمكن استخدامها لكسر الرابطة بين الغلاف وحامله. أفلم يكن كل من اختير جديرًا في النهاية؟",
    "gland/MethersSeveranceEffect": "أحضرها إلى زيريل، حارسة الأغلفة، لقطع رابطتك مع أحد الأغلفة",
    "gland/MethersSeveranceName": "فصل ميثر",
    "ST_Core_Locations/BagheadCamp": "معسكر باغهيد",
    "ST_Core_Locations/S1AshenWilds": "التلة القاحلة",
    "ST_Core_Locations/s1CavernEntrance": "مدخل الكهف",
    "ST_Core_Locations/S1WoodedPath": "الفسحة المتنازع عليها",
    "ST_Core_Locations/S1Ravine": "شلالات ظل الظلمة",
    "ST_Core_Locations/S2MushroomKeep": "شرفة اللورد الأعلى",
    "ST_Core_Menu_Shellkeeper/ShellSeveranceCost": "اقطع رابطتك مع",
    "ST_Core_Menu_Shellkeeper/ShellSeveranceName": "فصل الغلاف",
    "ST_Core_Options_Game/SwapSwitchControllerGlyphs": "تبديل رموز يد تحكم Switch",
    "ST_Core_Tarstones_Fragile/FragileTarstone_Goldstone_Durability": "تنخفض عند اكتساب <Bold>العملات</>",
    "ST_Core_Tarstones_Fragile/FragileTarstone_Gloomstone_Durability": "تنخفض عند اكتساب <Bold>الظلمة</>",
    "ST_Core_Tarstones_Fragile/FragileStone_DungeonRespawn_Durability": "تنخفض عند التفعيل",
    "ST_Core_Tarstones_Fragile/FragileTarstone_Glimpse_Durability": "تنخفض عند هزيمة الأعداء",
    "ST_Core_Tarstones_Fragile/FragileTarstone_Durability": "المتانة",
    "ST_Core_Tarstones_Fragile/FragileTarstone_DurabilityConsumed": "المتانة المستهلكة",
    "ST_Core_Tarstones_Fragile/FragileHeader_Durability": "المتانة:",
    "ST_Core_Tarstones_Fragile/FragileHeader_Effect": "التأثير:",
    "ST_Core_Tarstones_Fragile/FragileStoneName_DungeonRespawn": "حجر إيغون",
    "ST_Core_Tarstones_Fragile/FragileStoneHeader": "هش",
    "ST_Core_Tarstones_Fragile/FragileTarstone_BreakEvent": "انكسر حجر تارستون الهش",
    "ST_Core_Tarstones_Fragile/FragileStoneName_Glimpse": "حجر اللمحة",
    "ST_Core_Tarstones_Fragile/FragileStone_Glimpse_Break": "يمنح {X} لمحات",
    "ST_Core_Tarstones_Fragile/FragileTarstone_Gloomstone_Break": "يمنح {Y} من <Bold>الظلمة</>",
    "ST_Core_Tarstones_Fragile/FragileTarstone_Goldstone_Break": "يمنح {Y} من العملات",
    "ST_Core_Tarstones_Fragile/FragileTarstone_Goldstone_Effect": "احصل على {X} من العملات من الأعداء المهزومين",
    "ST_Core_Tarstones_Fragile/FragileTarstone_Gloomstone_Efffect": "احصل على {X} من الظلمة من الأعداء المهزومين",
    "ST_Core_Tarstones_Fragile/FragileHeader_Break": "عند الانكسار:",
    "ST_Core_Tarstones_Fragile/FragileStone_DungeonRespawn_Break": "يمنع فقدان <Bold>الظلمة</> عند هذا الموت",
    "ST_Core_Tarstones_Fragile/FragileTarstone_Depleted": "نفد حجر تارستون",
    "ST_Core_Tarstones_Fragile/FragileStone_DungeonRespawn_Effect": "عند الموت داخل <Bold>زنزانة</>، يمنحك خيار الإحياء عند مدخلها",
    "ST_Core_Tutorials/Tutorial_Fragile_Tarstones_Heading_3": "الانكسار",
    "ST_Core_Tutorials/Tutorial_Fragile_Tarstones_Heading_1": "المتانة",
    "ST_Core_Tutorials/Tutorial_Tarstones_3_Title": "أحجار تارستون الهشة",
    "ST_Core_Tutorials/Tutorial_Fragile_Tarstones_Desc_3": "غالبًا ما يكون لأحجار تارستون الهشة تأثير عند انكسارها. يختلف هذا التأثير باختلاف الحجر.",
    "ST_Core_Tutorials/Tutorial_Fragile_Tarstones_Heading_2": "سلبي",
    "ST_Core_Tutorials/Tutorial_Fragile_Tarstones_Desc_2": "تمنح بعض أحجار تارستون الهشة تأثيرًا سلبيًا طالما أنها مجهّزة وسليمة.",
    "ST_Core_Tutorials/Tutorial_Fragile_Tarstones_Desc_1": "بعض أحجار تارستون هشة ولها متانة، ما يعني أنها ستنكسر عند تكرار تحقق شرط معين. يختلف هذا الشرط باختلاف الحجر.",
    "ST_Core_WelcomeScreen/WelcomeScreenDescription_1": (
        "أيها النذيرون، ثمة رقعة جديدة قد ظهرت.\n\n"
        "حان وقت أول تحديث كبير للعبة، يجلب محتوى جديدًا إلى جانب إصلاحات واسعة، وتحسينات في الأداء، "
        "وتنقيحات في القتال، وإعادة صياغة لاقتصادَي اللمحة وتارستون، وضررًا متدرجًا للطعنات المرتدة، "
        "وتغييرات مهمة في التقدم والاستكشاف وجودة الحياة.\n\n"
        "من بين الإضافات أحجار تارستون هشة جديدة، وطريقة جديدة لإعادة توزيع مهارات غلافك، "
        "وأشياء أخرى كثيرة بانتظار اكتشافها.\n\n"
        "كما أضفنا المزيد من المنارات، وحسّنّا مسار الاستكشاف ليصبح التنقل في العالم أكثر تروٍّ وأفضل إيقاعًا.\n\n"
        "هناك الكثير المضمّن في هذا التحديث أكثر مما يمكننا سرده هنا، فراجع ملاحظات الرقعة الكاملة للاطلاع على كل التفاصيل.\n\n"
        "شكرًا لكم على اللعب، وعلى ملاحظاتكم، وعلى مرافقتكم لنا في هذه الرحلة!"
    ),
    "ST_LandingAreaNames/LandingArea_Slice1_DryVillage": "نصب ماتكا التذكاري",
    "ST_Settings/IncreasedGeometryBudgetsDesc": "فعّل هذا الخيار إذا لاحظت وميضًا شديدًا في الهندسة، وقد يكون سببه دقة شاشة مرتفعة جدًا مع أعلى الإعدادات. تفعيل هذا الخيار يزيد استهلاك ذاكرة الفيديو (VRAM).",
    "ST_Settings/IncreasedGeometryBudgetsTitle": "زيادة ميزانيات الهندسة",
    "ST_Settings_Advanced/ST_SwapSwitchControllerGlyphs": "فعّل هذا الإعداد إذا كان خيار 'استخدام تخطيط أزرار Nintendo' معطّلًا ضمن إعدادات Steam الخاصة بيد التحكم.",
    "ST_Skills_Smert/ShellSkillSmertDevotion_Effect_2": "أثناء كونك <Faith>مؤمنًا</>، أي زيادة في <Resolve>العزيمة</> لديها احتمال {Y} لملء <Resolve>العزيمة</> بالكامل",
    "ST_Tarstones_Effects/TarstoneEffect_KatanasAbility_4": "تُلحق كل ضربة {W} من تراكمات <Fragile>الهشاشة</>",
}


def main():
    path = os.path.join(BASE, "03_working_draft.jsonl")
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]

    applied = 0
    still_missing = []
    for r in rows:
        if r.get("fix_status") == "needs_scratch":
            if r["key"] in TRANSLATIONS:
                r["current_ar"] = TRANSLATIONS[r["key"]]
                r["fix_status"] = "scratch_translated"
                applied += 1
            else:
                still_missing.append(r["key"])

    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"applied: {applied}")
    print(f"still missing: {len(still_missing)}")
    for k in still_missing:
        print("  MISSING:", k)


if __name__ == "__main__":
    main()
