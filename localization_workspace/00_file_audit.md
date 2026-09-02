# Mortal Shell II — Arabic localization: File Audit

## Game
- Steam AppID `2584270`, install dir codename **Sparta**, path `F:\SteamLibrary\steamapps\common\Sparta\MortalShell2`
- Studio: Cold Symmetry (UK) / publisher Playstack — **dev/original language is ENGLISH** (Western studio, unlike Fatal Claw's Korean source). This is Methodology **Case B**: English is authoritative source, but gender/number/register cross-reference from Romance-language exports is required since English underspecifies.
- Engine: has shipped `Engine/` folder (UE5.x cook, not UE4.27 like Fatal Claw). Exact minor version not yet pinned — verify via `Engine/Binaries/Win64/*.exe` PE version resource before assuming.
- Build id 25005568, ~73GB installed, already owned/played by Faisal (MS2SaveShield tool exists for saves).
- No IoStore blocker: **all game paks are legacy loose `.pak` format** (pakchunk0–6, 11), unencrypted, no AES key needed — `repak.exe list/get` works directly. (Simpler than Fatal Claw, which needed the 4-gate locmeta/widget patch dance — same dance likely still needed here, see below.)

## Where the text lives
- `MortalShell2/Content/Localization/Game/{culture}/Game.locres` + `Game.locmeta`, all inside **pakchunk0-Windows.pak**.
- Shipped cultures (15, no Arabic): `de, en, es, es-419, fr, it, ja, ko, pl, pt, pt-BR, ru, uk, zh-Hans, zh-Hant`.
- `Game.locmeta` binary layout confirmed **identical to Fatal Claw's**: 16-byte hash + version + native culture string `en` + native locres path `en/Game.locres` + count(15) + culture-name list. Appending `ar` (count→16) is the same proven byte-safe patch from the Fatal Claw session.
- Corpus size: **9,751 keys** in `Game.locres` (English) — ~2.7x Fatal Claw's 3,559. Namespace/key format is per-string GUID hashes (`/HEXHASH...`) plus a handful of human-named keys (e.g. `/ElectricConduitFlavorText`) — no visible category/namespace grouping in the key itself; category must be inferred from asset path context or content shape (item flavor text, UI label, dialogue, tutorial, etc.) during the classify-corpus step.
- `DefaultGame.ini`'s `CulturesToStage` is a **cook-time-only** setting (irrelevant post-ship, do not bother editing).

## Gate risk (to verify, same shape as Fatal Claw's 4 gates)
Not yet confirmed whether the in-game language picker is:
- (a) **data-driven from `Game.locmeta`'s compiled-culture list at runtime** (likely — game uses Epic's own `GameSettings` plugin, a newer data-driven settings framework, not a hand-rolled Blueprint widget like Fatal Claw's `WBP_OptionNew`), in which case the locmeta append alone may suffice, **or**
- (b) still backed by a hardcoded display-name StringTable / DataTable (`LANGUAGE_ARABIC`-style key) that needs an added row + Arabic display label.
No `WBP_Option`/`WBP_GameSetting`/`Language`-named uasset turned up in a filename grep — settings menu is likely built from the `GameSettings.uplugin` registry (C++ config, not Blueprint), so the failure mode may differ from Fatal Claw's. **Verify in-engine after the locmeta-only patch before assuming a widget patch is needed** (don't repeat Fatal Claw's mistake of patching blind).

## Fonts (found, pakchunk4)
`MortalShell2/Content/Sparta/UI/Fonts/`: Cormorant (Unicase Bold/Regular), CrimsonText (Bold/Italic/Regular/SemiBold), PTSerif (Bold/Italic/Regular), Trajan Pro (Regular/SemiBold), plus per-CJK-language faces: NotoSansKR (6 weights), NotoSansSC (6), NotoSansTC (6), NotoSerifJP (6). No pre-existing Cyrillic/Arabic override family — Latin/Cyrillic likely covered by the base serif fonts (CrimsonText/PTSerif), CJK routed via composite-font sub-typefaces exactly like Fatal Claw. **Same composite-font-add pattern applies**: add SST Arabic Medium as a new sub-typeface routed only to Arabic Unicode blocks, do NOT replace any base font wholesale (that's the bug that broke CJK labels in Fatal Claw v1-3).
- Reusable Arabic font asset already built and proven: `FatalClaw/localization_workspace/font_add/Faces/SSTArabic-Medium.{uasset,uexp,ufont}` + raw clean ttf at `FF7Classic/localization_workspace/build/FF7_Arabic_Handover/source_font/SST-Arabic-Medium_sanitized.ttf`.

## Tools available (proven, reused from Elliot/Fatal Claw projects — no re-research needed)
- `Ai/Tools/repak/repak.exe` — pak list/get/pack (legacy pak, works on this game directly).
- `Ai/Mods Dev/Elliot/localization_workspace/scripts/_tools/UnrealLocres.exe` (v1.1.0, akintos) — `export`/`import`/`merge` locres↔csv/po. Verified: `export en.locres -f csv` → clean `key,source,target` CSV, 9,751 rows.
- `Ai/Tools/UAssetGUI/UAssetGUI.exe` — for any StringTable/widget uasset edits if gate (b) above turns out true.
- CUE4Parse-based C# tools (source vendored at `FatalClaw/localization_workspace/scripts/_tools/_cue4src/`, prebuilt `EnExtract`/`ElliotLocExtract`/`WidgetEdit`) — for texture/widget/blueprint dumps if UAssetGUI's tojson route is insufficient.

## Extracted so far (this workspace)
`localization_workspace/extracted/`: `en.locres/.csv`, `ja.locres`, `ko.locres`, `fr.csv`, `es.csv`, `it.csv` (Romance-language cross-reference exports for gender/number recovery per Case B), `Game.locmeta`, `DefaultGame.ini`, `DefaultEngine.ini`, `DefaultSparta.ini`, `DefaultSpartaConfig.ini`.

## Next steps (per LOCALIZATION_METHODOLOGY.md 7 foundation artifacts)
1. ~~File audit~~ (this doc)
2. Source corpus — classify all 9,751 EN rows by category/speaker/gender using fr/es/it cross-reference for addressee gender (Case B)
3. Game-context file — Mortal Shell II plot/characters/world/tone (needs research: souls-like, 8 playable Shells/Harbinger warriors, open-world, Cold Symmetry's established EN VO tone)
4. Glossary — Shell names (Tiel/Eredrim/Proxima/etc.), Gloom, Resolve, Beacon, Tarstone, Seal, Undermether, etc.
5. Style guide — reuse the reusable Arabic Style Guide section of LOCALIZATION_METHODOLOGY.md; register decision TBD (souls-like dark-fantasy tone, likely elevated/literary MSA per the FFT precedent, not everyday-adventure default — confirm in pilot)
6. QA validator — port Fatal Claw's `scripts/40_qa_validate.py` pattern
7. Enforcement package (glossary/character-cards/scenes/style compiler)
