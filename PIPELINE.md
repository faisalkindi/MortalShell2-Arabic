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
3. Re-patch from the new sources: `90` (Language BP, byte splice, check its offsets), `94_swap_settings_save_ptbr.py` (settings save: same-length in-place `pt-BR`→`ar-MA` key swap; NEVER grow that bytecode, a 16th map entry crashes the game in `execLocalVariable`, verified on 25478144), `93b` (tab bars) + `98_pin_inventory_filter_ltr.py` (replaces `tools_src/FlowPin`: pins `ScrollBox_InventoryFilter` AND its container `HorizontalBox_0`). Mappings `MS2` still round-trips new builds byte-for-byte; check that first.
4. `170_update_b25478144.py`: new strings/overrides, tag-parity check, locres import, corpus sync. `DefaultEngine.ini` = new stock + the 14-line RTL block after `t.Streamline.Reflex.Enable=0`.
5. `retoc to-zen --version UE5_6 <stage> zzz_ArabicLang_P.utoc` (stage root holds the new `scriptobjects.bin`), `repak pack --version V11 -p 97545662` for the loose pak (give a full `.pak` output path).
6. Test by launching the game with the full mod (it crashed ~15 s after launch when broken; fixed builds stay up). Bisect crashes by parking `pakchunk9998_*`/`zzz_*` files and by building partial containers with `retoc to-zen -f <asset>`.

## Cutscene subtitles (engine canvas path)

Cutscene VO lines are SoundWave `Subtitles` cues (StringTable text), drawn by Unreal's canvas subtitle renderer, not by any widget (`SubtitleFontName` = `Trajan_Pro_SemiBold_Font_Subtitles`). It lays text out left-to-right with no bidi, so logical Arabic comes out mirrored. Only two tables feed it: `ST_WakeUpLevelSequence` and `ST_ShellKeeperIntroLevelSequence` (15 short lines). `scripts/170_update_b25478144.py` ships those strings pre-shaped (Presentation Forms-B) in visual order via `scripts/arabic_visual.py`; the corpus stays logical. Needs `pip install arabic-reshaper` (use a venv). Animatic subtitles (`ST_InitialAnimatic`/`ST_EndingAnimatic`) use `WBP_Subtitle_Base` (a normal TextBlock) and are left alone. Other widgets (`WBP_HUD_Dialogue` rich text) render normally.

## Map pans backwards under Arabic (render-transform mirroring)

Slate negates a widget's render-transform X translation (and rotation) when it is arranged under a right-to-left flow. The shipped `Slate.ShouldFollowCultureByDefault=1` makes default-flow widgets RTL under ar-MA, so anything moved with `SetRenderTranslation` pans/slides backwards horizontally. The world map pans `WBP_MapBase.Overlay_Root` that way (`WBP_MGT_WorldMap.UpdateOffset`). `scripts/96_pin_map_pan_ltr.py` pins `Overlay_Root` and its parent `ScaleBox_Root` to LeftToRight (property-only; adds the `WBP_MapBase` package to the zzz container). Other widgets that animate via render transforms (rotating markers, sliders) may need the same pin if reported.

## Level-up screen: overlap, reversed brackets, arrows (mirrored layouts built for LTR)

Under RTL flow Slate mirrors panel arrangement but not images or glyphs. `WBP_Tooltip_Requirement` (the "Gloom (owned/required)" bar) overlays a Fill-aligned name box and a right-aligned numbers box, built for LTR, so mirroring stacks them on one side (overlap) and the separate `(` / `)` TextBlocks come out as `)4360(`. In `WBP_Progression_Harbinger`, row `HorizontalBox_98` (Level 10 > [< 11 >]) uses static arrow images, so mirrored they point at the old level and the buttons point inward. `scripts/97_pin_levelup_ltr.py` pins `WBP_Tooltip_Requirement.ScaleBox_Main` and `WBP_Progression_Harbinger.HorizontalBox_98` to LeftToRight (property-only). Rule of thumb: any widget that mixes arrows/brackets/fixed-side alignment and was designed LTR is a candidate for the same pin.

## Inventory filter strip

**Final v1.4 design.** Do not pin `ScrollBox_InventoryFilter` or its wrappers (`Overlay_InventoryFilter`, `RetainerBox_InventoryFilter`): the strip then scrolls the wrong way, the selected tab leaves the view and no highlight shows (video test 2026-10-07). Left mirrored, the tabs run right to left (All at the right) and scrolling/highlight work. Only `HorizontalBox_0` (the `[LT][strip][RT]` icon row) is pinned (`scripts/98_pin_inventory_filter_ltr.py`) so LT sits on the left and RT on the right. With a mirrored strip LT would step right, so `scripts/99_swap_inventory_filter_shoulders.py` byte-patches `BP_HorizontalBoxContainer.HandleInput` (same length) to swap the deltas for the inventory-top legend only. Gotcha: `EInterfaceInput` entries are not in numeric order; `NewEnumerator6/7` (what `WBP_IL_Inventory_Top` listens to) are values 11/12, so read the enum asset's Names tuples. Main/Options tab bars use values 9/10 and are untouched. UAssetGUI re-saving `BP_HorizontalBoxContainer` drops class-level data, so patch its stock `.uexp` bytes directly. The container is 9 packages (the 8 above plus `BP_HorizontalBoxContainer`); `retoc to-zen` output is not byte-reproducible.

## Retainer boxes, mask materials and per-screen input remaps (v1.4.1)

- **Retainer boxes reset flow direction.** A `RetainerBox` paints its child in a separate pass whose layout starts from the culture direction, so a `FlowDirectionPreference` set above a retainer does not reach inside it (the inventory and fast-travel tab rows stay right-to-left whatever their parents say). Pin inside the retainer only if you accept that horizontal `ScrollBox` scroll-into-view then misbehaves (v1.4 inventory test).
- **Mask materials are not mirrored.** `WBP_MGT_FastTravel.RB_Map` overlaps the panel by design and hides the overlap with its `EffectMaterial` fade (`MI_FastTravelMapMask`). Mirrored, the hard edge landed on the menu. `scripts/101_pin_fasttravel_ltr.py` pins the root (`ScaleBox_Main`) LTR so frame, slides (`Anim_FadeIn`, `Anim_ToggleMapMode`) and mask match English, and hands `Overlay_Contents` (list + scrollbar) and `ScaleBox_UserScale_Prompts` back to `Culture` so they look as before.
- **Per-screen LB/RB remap.** The fast-travel region tabs (RTL inside `RetainerBox_Filters`) use values 9/10, shared with the Main/Options tab bars, so the shared delta table cannot change. Instead the screen's own listener `WBP_IL_FastTravel_Filter` gets an `InterfaceInputs` override `{NewEnumerator4: IA_Menu_Right_Secondary, NewEnumerator5: IA_Menu_Left_Secondary}`; `WBP_InputListener` broadcasts the map key whose value is the triggered action, so LB sends +1 (next tab, leftwards). The instance is a RawExport: unversioned header fragments `0x0207 0x0201 0x031F` (#7 AcceptedInputs, #9 InterfaceInputs, #41 unchanged), map = NumKeysToRemove 0, Num 2, (FName key, FPackageIndex) pairs; two InputAction imports added and listed in the export's CreateBeforeSerialization deps.
- **Two-panel screens and confirmation prompts.** `scripts/102_pin_progression_and_prompts_ltr.py`: `WBP_MGT_Progression.HB_Menu` LTR (Harbinger/LB panel left, Shell/RB panel right; panel contents back to `Culture`, `Overlay_Left/Right` stay LTR for their slide-in), and `ScaleBox_Options` LTR in `WBP_ConfirmationPrompt_Default/_Requirement/_ShellStory` (d-pad left/right were reversed). `_MultiOptions` is handled by `scripts/103_multioptions_arrows.py`: its strip stays RTL inside `RB_Options`, so the arrows' mirrored positions already match their meaning (LeftArrow = previous = rightwards); only their images (`Direction`, rotation-based, not mirrored by Slate) are swapped, and its listener gets the same per-window map override (left/right primary) so the d-pad moves the way it is pressed.
- **UAssetGUI and BP-class instances.** It decodes an instance of a Blueprint widget class (listeners, arrow buttons) only when that class asset and its dependencies sit beside the file under the same `Content` tree (missing ones are listed in `OtherAssetsFailedToAccess`); alone, those exports load as `RawExport`. It cannot write them back once decoded, so edit them raw and use a decode beside the class assets as the check. Unversioned layout: uint16 fragments (skip | 0x100 last | values << 9), the values, then a 4-byte trailer.
- The container is 15 packages. Game-extracted sources: `ft_b25478144/`, `ui2_b25478144/` (not committed).
