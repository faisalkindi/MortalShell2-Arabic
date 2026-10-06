# Pipeline notes (for contributors)

Working files, not needed to play. Everything player-facing is in the README and the Releases page.

## Layout

| Path | What |
|---|---|
| `localization_workspace/00_file_audit.md` | Recon: pak layout, locres/locmeta locations, fonts, gate risks |
| `localization_workspace/04_game_context.md`, `04b_corpus_speaker_notes.md`, `character_cards.yaml` | World, cast, voices, gender evidence |
| `localization_workspace/05_glossary.csv` | Frozen terminology (200+ terms) |
| `localization_workspace/06_arabic_style_guide.md` | Split-register decision (elevated lore فصحى vs plainer UI/tutorial), locked rules |
| `localization_workspace/04_final_corpus.jsonl` | Final merged Arabic corpus, 9,751 rows, per-row provenance |
| `localization_workspace/review_findings/` | Dual-model semantic review findings |
| `localization_workspace/scripts/` | Numbered pipeline scripts (corpus → batches → QA → fonts → patches) |
| `localization_workspace/installer/` | .NET 8 WinForms installer source |
| `localization_workspace/release/payload/` | The six shipped mod files |
| `localization_workspace/release/dist/` | Nexus texts and media |

## Facts

- Game: Mortal Shell II, Steam AppID `2584270`, install dir `Sparta`, UE5 cook, legacy unencrypted paks (no AES).
- Text: `MortalShell2/Content/Localization/Game/<culture>/Game.locres` — 9,751 keys, 15 shipped cultures; Arabic added as the 16th via a `Game.locmeta` append (`60_patch_locmeta.py`).
- Delivery: six loose files in `MortalShell2\Content\Paks\` — `pakchunk9998-Windows_P.{pak,ucas,utoc}` + `zzz_ArabicLang_P.{pak,ucas,utoc}`. No original file modified.
- Fonts: SST Arabic merged as Arabic-only sub-typeface routing (no base font replaced); vertical metrics restored and descender clipping fixed (`80–85_*.py`).
- Language persistence: `92_patch_settings_save_languages.py` patches the settings save object so the Arabic choice survives restarts.
- RTL: menus/inventory mirrored; tab bars pinned LTR (`93_pin_tab_bars_ltr.py`).

## Stages (numbered scripts)

1. `01_build_corpus.py` tag corpus (English source; fr/es/it exports cross-referenced for gender/number)
2. `100_build_batches.py` context-rich batches → primary draft → editorial pass
3. `140_build_review_chunks.py` → dual-model semantic review → `150_apply_findings.py`
4. `50_mechanical_fix.py` deterministic sweep · `40_qa_validate.py` blocking validator
5. `130_assemble_final.py` merge with provenance (`120_provenance_audit.py`)
6. Fonts `80–85`, locmeta `60`, language BP/save patches `90–93`, glossary enforcement `91`
7. Pack + installer: `installer/` (.NET 8, self-contained single file; payload = the six mod files)

## Rebuilding

Needs the game installed (Steam), `repak`, UnrealLocres, UAssetGUI, Python 3 with `fontTools`. Game files, extracted assets and built binaries are not committed.

Installer: `cd localization_workspace/installer && dotnet publish -c Release -r win-x64 --self-contained -p:PublishSingleFile=true -o publish` after regenerating `payload.zip` from `release/payload/`.

## Updating after a game patch

The mod overrides five compiled packages (`BP_UIO_Language`, `SpartaSettingsSaveObject`, `WBP_MGT_Main/Options/Character`) and ships a copy of `DefaultEngine.ini`. A game patch can change any of them, and a stale copy crashes the game. Last rebased onto build 25478144 (2026-09-25); the previous payload (build 25005568) is kept in `release/payload/`.

1. Hardlink the stock `global`/`pakchunk*` `.utoc/.ucas/.pak` into a scratch folder (so the mod's own files are excluded) and `retoc to-legacy -f <asset> --version UE5_6 --no-shaders` the five assets into `src_<build>/`; the whole folder is needed so `scriptobjects.bin` is produced.
2. Diff stock vs previous: assets, `Game.locmeta`, `DefaultEngine.ini`, English `Game.locres` keys.
3. Re-patch from the new sources: `90` (Language BP, byte splice, check its offsets), `94_swap_settings_save_ptbr.py` (settings save: same-length in-place `pt-BR`→`ar-MA` key swap; NEVER grow that bytecode, a 16th map entry crashes the game in `execLocalVariable`, verified on 25478144), `93b` (tab bars) + `tools_src/FlowPin` (`ScrollBox_InventoryFilter`, value `LeftToRight`). Mappings `MS2` still round-trips new builds byte-for-byte; check that first.
4. `170_update_b25478144.py`: new strings/overrides, tag-parity check, locres import, corpus sync. `DefaultEngine.ini` = new stock + the 14-line RTL block after `t.Streamline.Reflex.Enable=0`.
5. `retoc to-zen --version UE5_6 <stage> zzz_ArabicLang_P.utoc` (stage root holds the new `scriptobjects.bin`), `repak pack --version V11 -p 97545662` for the loose pak (give a full `.pak` output path).
6. Test by launching the game with the full mod (it crashed ~15 s after launch when broken; fixed builds stay up). Bisect crashes by parking `pakchunk9998_*`/`zzz_*` files and by building partial containers with `retoc to-zen -f <asset>`.

## Cutscene subtitles (engine canvas path)

Cutscene VO lines are SoundWave `Subtitles` cues (StringTable text), drawn by Unreal's canvas subtitle renderer, not by any widget (`SubtitleFontName` = `Trajan_Pro_SemiBold_Font_Subtitles`). It lays text out left-to-right with no bidi, so logical Arabic comes out mirrored. Only two tables feed it: `ST_WakeUpLevelSequence` and `ST_ShellKeeperIntroLevelSequence` (15 short lines). `scripts/170_update_b25478144.py` ships those strings pre-shaped (Presentation Forms-B) in visual order via `scripts/arabic_visual.py`; the corpus stays logical. Needs `pip install arabic-reshaper` (use a venv). Animatic subtitles (`ST_InitialAnimatic`/`ST_EndingAnimatic`) use `WBP_Subtitle_Base` (a normal TextBlock) and are left alone. Other widgets (`WBP_HUD_Dialogue` rich text) render normally.
