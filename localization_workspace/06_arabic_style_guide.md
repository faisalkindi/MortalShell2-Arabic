# Mortal Shell II — Arabic Style Guide

Base: the reusable Arabic Style Guide in `Ai/Mods Dev/LOCALIZATION_METHODOLOGY.md`. This file records the game-specific calibration decisions on top of it.

## Register: SPLIT, not uniform (confirmed via 04_game_context.md + corpus sampling)
This game has two distinct registers in its own English text — Arabic must mirror the split, not flatten it:

1. **Elevated literary فصحى راقية** — lore/flavor text (item descriptions, Seal descriptions), Shell mottos and Memory unlocks, Undermether's dialogue, Zhirelle's dialogue, cutscene/story-critical dialogue. Semi-archaic, aphoristic, proverb-like density — matches the source's "grandiose, elliptical" dark-fantasy diction. NOT verbose classical سجع.
2. **Plain/direct فصحى ميسّرة** — UI labels, tutorial/system text, settings, tooltips, and comic-relief NPC dialogue (Gorf, Baghead, ImmortalBrigand, BlisterBoi's petulant-child register, Merrick's shopkeeper patter, Franz's craftsman warmth).

Per-speaker register is recorded in `character_cards.yaml`. When in doubt for an unassigned line, default by category: `dialogue`/`dialogue_scene` rows from a card-listed speaker use that speaker's register; uncarded system/UI rows use plain.

## Gender defaults
- Harbinger (player character): masculine default per web-guide consensus, unless a specific line's context implies otherwise (rare — Harbinger mostly doesn't speak).
- All named-cast genders are frozen in `character_cards.yaml` from corpus + web evidence. **ImmortalBrigand, BanishedCultist, HubCultist have NO determinable gender in the source — use gender-neutral Arabic phrasing (verbal nouns, avoid gendered verb conjugation) for their lines rather than defaulting to masculine.**
- "Sester"/"Brether" are deliberately WARPED forms of sister/brother. Warp the Arabic, do not
  transliterate: **أُخَيّة / أُخَيّ** (archaic diminutives), plural **الأُخَيّات / الأُخَيّون**.
  Never plain أخت/أخ (loses the warp) and never سستر/بريذر (loses the kinship meaning).
  Frozen in `05_glossary.csv`. The earlier "transliterate as سستر" rule came from the discarded
  third-party draft and is void.

## Frozen glossary
See `05_glossary.csv`. Three real inconsistencies already found in the Asmar base draft that the mechanical QA pass must sweep and fix:
- **Fallgrim**: freeze فولغريم (draft has 3 competing spellings: فالجرام / فالغريم / فالغرين)
- **Marrow Keep**: freeze حصن النخاع (draft also has قلعة العظم — wrong word, "bone" not "marrow")
- **Etching Needles**: freeze إبر النقش (draft also has إبر الحفر once)

## Numbers
Western digits 0-9 (per base style guide default) — **mandatory here**, not just a default: the Fatal Claw project's post-launch bug was exactly ICU's `ar` culture defaulting to Arabic-Indic numerals at runtime for any number the ENGINE formats (not the translated text itself, which never contained Arabic-Indic digits). **Ship this game's Arabic locale under culture code `ar-MA`** from the start (not plain `ar`) — `ar-MA`'s ICU default numbering is Latin 0-9, sidestepping the bug entirely rather than discovering it in a post-release bug report.

## Punctuation
Arabic `،` `؛` `؟`, not ASCII `,` `;` `?`. The Asmar draft has **27 rows mixing ASCII punctuation into Arabic text** — mechanical QA pass must normalize these (find `[؀-ۿ].*[,;?]` and `[,;?].*[؀-ۿ]` patterns, replace with Arabic equivalents, never touch punctuation inside a placeholder/tag).

## Technical (non-negotiable, from base methodology)
- Preserve every `<Tag>`/`</>`/`{X}`/`{Y}`/`%s`/`%d` byte-for-byte, same count and order.
- Never translate the `key`/StringTable row-name.
- 46 rows in `02_needs_scratch_translation.jsonl` have the Asmar draft missing/empty/placeholder-broken — these need fresh translation, not editorial cleanup.
- `Break In` (a UI action, unrelated to the "Break" posture meter) is mistranslated as `السرقة` (theft) in the draft — verify actual meaning against its usage context before fixing; do not assume it's a glossary case.

## Honorifics
No anime-style Japanese suffixes apply (English source, not Japanese). Use natural Arabic address terms per character voice — e.g. Franz calling the player "laddie" needs one frozen Arabic equivalent (candidate: يا فتى), decide and freeze in the pilot batch.

## Layout
UI labels short (~28 chars). Respect `\n` breaks exactly. Watch for terse 2-4 char UI tokens (HP/MP-style) that could overflow when expanded to full Arabic terms — none identified yet in this corpus's short-UI bucket, but check during the ui_settings/ui_tutorial batch review.


## ★ UI vocabulary LOCK (frozen — validator-enforced)

These exact English UI strings have exactly one correct Arabic rendering. They are
enforced by `40_qa_validate.py`; a batch that deviates fails the build.

| English | Arabic (frozen) | Note |
|---|---|---|
| Quit | خروج | NOT الإقلاع — that means aviation "takeoff" |
| Exit Game | الخروج من اللعبة | |
| Continue | متابعة | verbal noun, not the imperative استمر |
| Resume | استئناف | |
| Back | رجوع | no ال |
| Cancel | إلغاء | |
| Confirm | تأكيد | |
| Apply | تطبيق | |
| Accept | قبول | |
| Close | إغلاق | |
| New Game | لعبة جديدة | |
| Load Game | تحميل لعبة | |
| Save | حفظ | |
| Settings | الإعدادات | |
| Options | الخيارات | |
| Restart | إعادة البدء | NOT إعادة التشغيل (that is rebooting a device) |
| Default | الافتراضي | |
| Reset | إعادة تعيين | |
| On / Off | تشغيل / إيقاف | |
| Yes / No | نعم / لا | |
| Credits | الاعتمادات | |
| Audio | الصوت | |

## ★ Anti-examples — what context-free machine translation looks like

The third-party draft this project initially built on was word-for-word MT with no
context. Real defects found in it, kept here as the standard to translate AGAINST:

- `Quit` → **الإقلاع** ("takeoff"). Dictionary sense of "quit/depart", zero awareness
  that this is a game menu button.
- `Piss off.` → **تفضل** ("go ahead, please") — polite invitation instead of an insult.
- `Off-Screen Enemy Indicator` → a label so long it truncated mid-word in the widget.
- `AUDIO` → "Discover a beacon in the darkness." — a description dropped into a tab label.
- `Break In` → **السرقة** ("theft") — wrong sense of "break".
- `And I have yet to find a suitable mate.` → rendered as "and I HAVE found one",
  inverting the character's entire arc.

The test for every row: **would a native Arabic speaker who plays games write this,
knowing where it appears on screen and who is saying it?** If it only makes sense by
mentally mapping back to the English, it is a failed translation — rewrite it.


## ★★ MANDATORY STAGE: the flow pass (after translation, before validation)

Translation accuracy is not the bar. The Arabic must READ well — sentence rhythm,
natural connectors, and paragraph movement — the way Arabic prose actually moves,
not the way English sentences do when carried across.

This pass is run on **contiguous text** (a whole scene, a whole description, a whole
tutorial screen), never row-by-row, because flow is a property of sequence.

What the flow pass fixes:

1. **Translationese sentence shape** — Arabic carried on English clause order. Recast
   with Arabic's own movement: verb-initial where it reads naturally, تقديم/تأخير for
   emphasis, and clauses joined the way Arabic joins them.
2. **Connector poverty** — endless و strung between clauses. Use the real inventory:
   ف، ثم، بل، لكن، إذ، حتى، أما…ف، لولا، وقد. English full stops often become an
   Arabic connected sentence, and one English sentence often becomes two in Arabic.
3. **Rhythm and length** — vary sentence length deliberately. Lore/flavour text wants
   short, weighted clauses that land; a long flat sentence kills the effect.
4. **Redundancy** — English needs "the player character will be able to…"; Arabic says
   it in three words. Cut what Arabic implies. Pronouns, copulas and filler verbs that
   English requires are usually dead weight in Arabic.
5. **Idiom over calque** — if a phrase only makes sense by tracing it back to English,
   it fails. Replace with the Arabic expression that produces the same effect.
6. **Voice continuity across a scene** — the same character should sound like one person
   from line to line, and consecutive lines should read as a conversation, not as
   independently translated fragments.
7. **Diacritics** — light and purposeful only: on the frozen lore terms and where a word
   is genuinely ambiguous. Never blanket tashkeel.

The test: read the passage aloud. If a native Arabic reader would pause, re-read, or
sense "this was English first", rewrite it. Meaning must be preserved exactly —
placeholders, numbers, facts and knowledge boundaries are untouchable.


### Flow-pass model decision (A/B tested 2026-09-01, batch 010)
Opus, not Sonnet. On identical input Opus changed 19/59 rows vs Sonnet's 5; both kept
placeholders intact. The difference was not volume but kind: Opus standardised a control
verb across the whole batch (اضغط مطوّلًا over استمر بالضغط), replaced a doubled purpose-lām
with the ف of consequence, cut filler (عند تنفيذ -> مع كل), and made a knock-on fix to a
sibling row (Release: ارفع -> أفلت). Sonnet fixed only the locally obvious rows.
Flow is a property of a whole passage, so the pass needs the model that reads it as one.
Translation stage stays on Sonnet.
