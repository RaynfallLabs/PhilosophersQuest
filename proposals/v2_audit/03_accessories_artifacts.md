# V2 audit -- Accessories + Artifacts

Audit date: 2026-05-19.
Reference: `proposals/v2_audit/CURVES.md`, `src/items.py` (Accessory L230-264, Artifact L334-336).

## Scope

| File | Entries | Uniques | Common |
|------|---------|---------|--------|
| `data/items/accessory.json` | 199 | 75 | 124 |
| `data/items/artifact.json`  | 26 | 26 | 0 |

The accessory count includes 2 "easter egg" items (`dreamspun_sketchbook`, `charmander_stuffie`) with `slot:"none"` and absurd `min_level:999` / `peak_floor:1004` -- deliberately unreachable. They are unique-tagged with valid mastery_blessing.

## Completeness checks

### Required-field passes

All 199 accessory entries have: `name, symbol, color, weight, slot, effects, equip_threshold, quiz_tier, min_level`.
All 26 artifact entries have: `name, symbol, color, weight, lore` + `is_unique:true`.

### Common-accessory schema -- 124/124 clean

All non-unique accessories carry slot, effects dict, equip_threshold, quiz_tier, min_level, plus the bell-curve trio (`peak_floor, spread, peak_weight`). No common accessory has a stray `mastery_blessing` (0/124).

### Unique-accessory schema -- 75/75 clean post-fix

Pre-fix, 8 plot-locked uniques were missing the bell-curve trio. Auto-fixed (see below). All 75 uniques now have `peak_floor, spread, peak_weight, lore, mastery_blessing`. Every `mastery_blessing.kind` is one of the two allowed values (`accessory_stat_bonus`, `accessory_passive_strength`).

### Artifact schema -- 26/26 clean

All 26 carry the artifact-required quintet plus `is_unique:true`. The 14 entries with no `peak_floor`/`spread`/`peak_weight` keys are all `plot_locked:true` (philosophers_stone, bronze_bull, gleipnir, 7 seals, scales_of_michael, cursed_lodestone, sealed_dispatch). The `Item.__init__` defaults handle missing keys safely (`int(defn.get('peak_floor', 0) or 0)` etc.). Explicit zeros are NOT required for plot-locked artifacts because they spawn through dedicated paths (boss drops, quest assembly, NPC encounters).

The 12 spawnable artifacts (`eye_of_graeae`, `cats_footstep` and 5 sibling Gleipnir-components, `leather_scrap`, `palladium`, `tablet_of_destinies`, `pandoras_box`, `aladdins_lamp`, `vidars_sandal`) all carry full bell-curve fields. `vidars_sandal` is special-shaped: `peak_floor:79, spread:1, peak_weight:0.0, plot_locked:true` -- the 0.0 weight ensures it never natural-spawns, but it has the fields anyway. Correct.

## Chain-equip integrity -- 9/9 clean

| ID | Mode | tier_bonuses keys | T1 -> T5 peak |
|---|---|---|---|
| ring_of_solomon       | escalator_chain | 1-5 | +INT/WIS 1 -> +3 each + telepathy + pacify demon + solomonic_key |
| necklace_of_harmonia  | escalator_chain | 1-5 | +WIS 2 -2 CON -> +WIS 5 -2 CON + max_mp + beautiful_ruin |
| heart_of_ahriman      | escalator_chain | 1-5 | +INT 2 -> +INT 5 + spell crit/dmg + anti_being |
| tyet_of_isis          | escalator_chain | 1-5 | +WIS 2 -> +WIS 3 + life_save + reassembly |
| idunn_apple_charm     | chain            | 1-5 | +CON 2 -> +CON 5 + hunger_slow + aesir_young |
| ring_of_gawain        | chain            | 1-5 | +STR 1 -> +STR 3 + chain_cap + hasted + three_oclock |
| ring_of_scheherazade  | chain            | 1-5 | +INT 2 -> +INT 4 + grammar_chain + one_thousand_and_one |
| anklet_of_atalanta    | chain            | 1-5 | +DEX 2 -> +DEX 5 + free_move + atalantas_choice |
| kavacha_kundala       | escalator_chain | 1-5 | +CON 3 fire_resist -> +CON 5 + suryas_gift + first_hit_absorb |

All 9 have contiguous keys "1","2","3","4","5", non-empty bonus dicts, and monotonically-improving stat lines. The `necklace_of_harmonia` trade-off (WIS up, CON down) is design-intentional ("Beautiful Ruin").

## Balance findings

### Common-accessory stat-bonus range

Most common rings/amulets sit at 1-3 per stat as expected. Five outliers above the +3 ceiling:

| ID | Stat | Amount | quiz_tier | peak_floor |
|---|---|---|---|---|
| ring_strength_dragonbone     | STR | +4 | 4 | 50 |
| ring_constitution_diamond    | CON | +4 | 4 | 50 |
| ring_intellect_prismatic_deep| INT | +4 | 4 | 50 |
| amulet_titan_constitution    | CON | +5 | 5 | 70 |
| amulet_archmage_intellect    | INT | +5 | 5 | 70 |

These are deep-floor T4/T5 items -- the higher quiz tier compensates and these scale matches the unique-accessory ceiling. Acceptable design choice; flagged for visibility only. No change.

### Unique-accessory stat-bonus range

0 outliers above the +5 ceiling. Highest is +5 (kavacha_kundala T5 CON, anklet_of_atalanta T5 DEX, idunn_apple_charm T5 CON, necklace_of_harmonia T5 WIS).

### equip_threshold vs quiz_tier guideline (CURVES.md spec)

Spec says T1=2, T2=3, T3=3-4, T4=4, T5=5. The actual histogram across all 199 accessories:

| qt | th=1 | th=2 | th=3 | th=4 | th=5 |
|----|------|------|------|------|------|
| 1  | -    | 13   | 31   | -    | -    |
| 2  | 2    | 20   | 37   | -    | -    |
| 3  | -    | 15   | 20   | -    | -    |
| 4  | -    | 9    | 21   | 1    | -    |
| 5  | -    | 3    | 7    | 19   | 1    |

127 of 199 sit off-spec. The pattern shows the spec is descriptive-but-not-strict: "warning" and "searching" rings are T1 but use threshold 3 (1-of-3 is a low bar, fits the cheap-utility flavor). T5 items skew toward th=4 (the modal cell). I read this as the design intent being "threshold within 1 of the spec, can dip lower on utility items, can sit lower than ceiling on T5 because the questions are already hard." Recommend updating CURVES.md to widen the bands, not changing the items.

### Special-mechanic uniques verified

- `hand_of_glory`: `paralyze_charges: 3` (set), `peak_floor: 30`, `peak_weight: 0.5`. OK.
- `pandoras_box` (artifact): full 20-row `chaos_table` + `chaos_table_failure_skew.available_rolls_remap` complete. `use_quiz_subject: theology, use_quiz_tier: 3, use_quiz_threshold: 3, use_quiz_total: 4`. OK.
- `aladdins_lamp` (artifact): full `wish_categories: ['item','power','entity']`, `wish_menu` with all 3 branches populated, 5 `wish_fallback_effects`. `use_quiz_tier: 5, escalator_threshold`. OK.
- `ankh_of_isis` (resurrect_on_death=true, pf 70), `jade_cicada` (death_save=true, pf 25), `draupnir` (gold_multiplier 2.0, pf 50), `eye_of_horus` (passive_regen 1, pf 30), `seal_of_solomon` (pacify_chance 0.2, pf 65), `torc_of_boudicca` (surrounded_ac_bonus 2, pf 40) -- all special fields set as code expects (`src/items.py` L243-249 defaults match).

## Cross-file ID dupes

Scanned 14 item JSON files in `data/items/`: 1,032 unique IDs across the corpus, **0 dupes**. The "already audited" finding holds.

## Auto-fixes applied

8 plot-locked unique accessories were missing the bell-curve trio (`peak_floor, spread, peak_weight`). All have `floorSpawnWeight: {}` and `plot_locked: true`, so they never natural-spawn -- but the schema requires the fields on uniques. Auto-set to the "no bell weighting" sentinel:

| ID | Spawn path | Added |
|---|---|---|
| sphinx_crown        | sphinx-quest drop  | peak_floor:0, spread:10, peak_weight:0.0 |
| sailors_amulet      | maritime-quest     | peak_floor:0, spread:10, peak_weight:0.0 |
| anubis_scales       | undead-quest       | peak_floor:0, spread:10, peak_weight:0.0 |
| ring_of_iron_grip   | ravana drop        | peak_floor:0, spread:10, peak_weight:0.0 |
| obsidian_talisman   | xibalba quest      | peak_floor:0, spread:10, peak_weight:0.0 |
| saints_reliquary    | monk NPC drop      | peak_floor:0, spread:10, peak_weight:0.0 |
| officers_signet     | legion NPC drop    | peak_floor:0, spread:10, peak_weight:0.0 |
| prophets_amulet     | prophet NPC drop   | peak_floor:0, spread:10, peak_weight:0.0 |

These values are interpreted by `dungeon._item_eligible_weighted` as "exclude from bell-curve spawn"; the items continue to enter the game through their dedicated quest/drop paths. No behaviour change at runtime; pure schema completeness.

## Report-only flags

1. **CURVES.md threshold spec is too strict** -- 127/199 accessories are off-spec under the literal reading. The actual data clusters around "threshold within ~1 of spec, can be looser on utility items". Recommend updating CURVES.md text rather than changing items.
2. **5 common accessories at +4/+5 stat bonus** -- listed above. T4/T5 deep-floor items that overlap with the unique-accessory peak band. Design-intentional given their quiz_tier; flag for awareness, not action.
3. **`necklace_of_harmonia`** -- T1 already grants -1 CON; T5 grants -2 CON. Negative stat trade-off is by design (the item's identity), but worth a play-test once the chain-equip UI surfaces this clearly.

## Files modified

- `data/items/accessory.json` -- 8 entries gained `peak_floor`, `spread`, `peak_weight`.

## Summary

- Files modified: 1 (`data/items/accessory.json`).
- Auto-fixes: 8 unique accessories backfilled with bell-curve trio.
- Required-field passes: 199/199 accessories, 26/26 artifacts.
- Chain-equip integrity: 9/9 clean.
- Mastery-blessing kind validity: 75/75 uniques OK.
- Cross-file ID dupes: 0.
- Top balance flags: 5 common accessories at +4/+5 stat (deep-floor T4/T5, design-intentional); CURVES.md equip_threshold spec needs widening to match data.
- Tests: `py -m pytest tests/ -q` -- **476 passed in 63.86s**.
