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
