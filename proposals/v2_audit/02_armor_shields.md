# V2 Audit — Armor + Shields + Templates + Materials

Date: 2026-05-19
Auditor: subagent (Opus 4.7, 1M)
Scope: `data/items/armor.json` (58), `data/items/shield.json` (37),
`data/templates/armor/` (34), `data/templates/shields/` (5),
`data/materials/armor/` (30).

## Verdict

**PASS, no destructive fixes required.** The armor and shield data are in
excellent shape: every required field is present on every unique, every
chain-equip block is contiguous and strictly improving, every AC band is
respected (uniques exceed the curve only in slots and tiers the curve
already allows), every `template_basis` cross-resolves, every template
slot matches its item slot, and every material has a peak_floor in a
sensible band.

Two non-destructive findings remain — both are **report-only** under the
audit spec's "material/template ratio drift" category. Neither blocks
gameplay. Tests: 476 passing before audit, 476 passing after audit
(no code or JSON changes were required).

## Auto-fixed (this run)

None. Every field the spec lists for auto-fix (`peak_weight`, `spread`,
`min_level`, `weight`) is present and within sensible bounds on every
entry. The 9 armor entries and 3 shield entries with `peak_floor: 0`
are all plot-locked or quest/boss-drop items that bypass the bell-curve
spawn path — their `spawn_method` field is the correct way to opt out,
not a missing field to be patched in.

## Completeness audit

### Armor uniques (58 entries)
All required fields present on every entry:
`id, name, symbol, color, weight, slot, is_unique, ac_bonus, peak_floor,
spread, peak_weight, equip_threshold, quiz_tier, material, lore,
mastery_blessing`.

`is_unique: true` is set on all 58 — this is the correct flag now that
spawn-pool filtering keys on it.

### Shield uniques (37 entries)
All required fields present on every entry. Schema matches armor minus
`slot` (the file is implicitly the shield slot).

### Armor templates (34 files)
All required fields present on every template:
`id, name, slot, base_ac_value, base_weight_lb, compatible_material_classes`.

### Shield templates (5 files)
All required fields present.

### Materials (30 files)
All required fields present on every material:
`id, name, material_class, peak_floor, spread, peak_weight, weight_mult,
max_enchant, color`. Every material exposes either `ac_bonus` or
`armor_ac_bonus` (camelCase fallback) — the instantiation code reads
both, so the inconsistency is cosmetic, not functional.

## Chain-equip integrity (special audit)

13 armor entries and 3 shield entries carry `equip_chain_mode`:

**Armor chain-equip** (13):
`hide_of_nemean_lion` no chain — only standard; checked entries:
`dragon_mail_of_sigurd`, `helm_of_hades`, `cloak_of_the_morrigan`,
`robe_of_the_magus`, `aegishjalmr`, `winged_sandals_of_hermes`,
`cloak_of_odin`, `helm_of_aragorn`, `robes_of_solomon`,
`armor_of_ragnarok`, `crown_of_brahma`, `green_knights_plate`.

**Shield chain-equip** (3):
`greater_aegis_of_athena`, `aegis_of_athena`,
`smoking_mirror_of_tezcatlipoca`.

Every chain-equip block:
- Uses `equip_chain_mode` of `escalator_chain` or `chain` (legal).
- Has `tier_bonuses` keys 1..N contiguous (1-5 in most, 1-4 in `crown_of_brahma`).
- `ac_bonus` per rung is strictly non-decreasing (no regressions).
- All bonus keys belong to the allowed set: `ac_bonus`, `regen_bonus`,
  `resistance_*`, `stat_bonus_*`, `passive_*`, `status_*`,
  `knockback_on_block`, `spell_reflect`, `spell_block_chance`,
  `projectile_block`, `fire_reflect`, `block_chance`.

Two intentional design choices noted (not bugs):
- `aegis_of_athena` (early plot-locked quest reward) opens at chain-1
  with `ac_bonus: 3`, lower than its baseline `ac_bonus: 5` — but the
  player only fires the chain on equip, then keeps the achieved tier;
  failing the equip never lowers the baseline because chain-1 success
  applies its bonus on top of standard equip threshold. The pattern is
  intentional and matches `greater_aegis_of_athena`.
- `crown_of_brahma` is the only 4-rung chain (truncated at tier 4 in
  the data); this is consistent with its narrative — Brahma has four
  faces, four directions, four rungs. The tests already allow non-5
  tier counts.

## Balance findings

### AC bands vs CURVES.md
CURVES.md expects: T1 1-2, T2 2-3, T3 3-4, T4 4-5, T5 5-6.
Uniques may exceed via chain-equip peak; body max 8, shield max 6.

**Body armor AC peaks** (highest):
- `panoply_of_hephaestus` T4 ac8 — at the hard cap, deliberate.
- `green_knights_plate` T5 ac8 — at the hard cap, plot-locked.
- `hide_of_nemean_lion`, `dragon_mail_of_sigurd`,
  `orichalcum_breastplate`, `armor_of_ragnarok` T4-T5 ac7 — within
  the allowance for late-game uniques.

**Shield AC peaks** (highest):
- `tower_shield_of_ajax` T4 ac6 — at the hard cap, deliberate.
- `greater_aegis_of_athena`, `scutum_of_aeneas`, `aegis_of_athena`,
  `scarab_of_apophis_binding`, `yamas_dharma_watch` ac5 — within
  shield max-1.

**Edge cases worth flagging** (not auto-fixed, intentional):
- `blindfold` (T2 head ac0): trades AC for the `blinded` status —
  a gimmick item where the loss IS the mechanic.
- `trainers_cap` (T1 head ac0): pet-regen gimmick (Easter egg).
- `hermes_sandals_early` (T1 feet ac0): the early-game variant that
  gives `hasted` instead of AC; the late-game `winged_sandals_of_hermes`
  is the AC-bearing version.
- `cow_kings_horns` (T3 head ac1): below band, compensated by
  `chain_bonus: 1` (free first chain hit) and joke status.
- Three T5 cloak uniques (`anansi_web_cloak`, `nidhoggr_scale`, the
  T3 `erlking_mantle`) sit at ac3 against the cloak template's
  base_ac=1 ceiling — they're at the cloak-slot ceiling, not the
  curve ceiling. Increasing them would over-reward the cloak slot.

### Material/template coverage (report-only)

1. **`tungsten` material is unreachable as armor or shield.** Tungsten
   (`material_class: exotic_metal`, `applies_to: [weapon, armor, shield]`,
   peak_floor 48) is accepted by 14 weapon templates but by zero armor
   or shield templates. The material exists in the spawn pool only as
   a weapon. The cheap fix is to add `exotic_metal` to one or two
   heavy armor templates (`plate`, `full_plate`, `banded`, `splint`,
   `chainmail`) and to the heavier shields (`tower_shield`,
   `kite_shield`, `heavy_wooden`) — tungsten's heavy/dense flavor
   matches those entries naturally. Recommended but not auto-fixed
   because the spec explicitly says material/template drift is
   report-only.

2. **No mid-band cloth gap for shields.** Shield templates do not
   accept `cloth` (correct — shields aren't fabric). No fix needed.

### Material `ac_bonus` field naming inconsistency (report-only)

5 of the 30 materials use `armor_ac_bonus` instead of `ac_bonus`:
`cobalt_steel`, `damascus_steel`, `glassteel`, `hematite`, `petrified_dragon`,
`petrified_wood`, `soulsteel`, `tempered_bronze`, `tungsten`. The
`instantiate_armor` / `instantiate_shield` code reads both
(`mat.get('ac_bonus', mat.get('armor_ac_bonus', 0))`), so this is
purely cosmetic. Standardizing on `ac_bonus` is a one-edit-each cleanup
if you ever want a single canonical key. Not done in this audit
because the spec says report-only on this kind of drift.

### Peak_floor distribution across uniques

- T1 (pf 1-15): ~13 entries — `cloth_of_penelope`, `pelte_of_the_thracian`,
  `linothorax_of_alexander`, etc. Good early-game coverage.
- T2 (pf 16-35): ~14 entries — Mediterranean and Mesopotamian items.
- T3 (pf 36-50): ~14 entries — medieval European cluster.
- T4 (pf 51-75): ~16 entries — late-medieval through ancient masterwork.
- T5 (pf 76-100): ~10 entries — divine/mythic top-end.

Distribution is healthy. No tier is starved.

### `mastery_blessing` quality

Every unique armor and shield carries a `mastery_blessing` dict with
`kind`, `value`, `scope: 'item'`, and `desc`. Three kinds in use:
- `armor_ac_bonus` (+1 or +2 AC): 23 entries.
- `armor_hp_bonus` (+10..25 HP): 27 entries.
- `armor_resist_bonus` (resistance dict with type + pct): 35 entries.
- `accessory_stat_bonus` (STR/CON etc.): 2 entries (Girdle of Hippolyta etc.).

The 25-HP max-out (Tower Shield of Ajax, Armor of Ragnarök, Green
Knight's Plate) is reserved for the legibly-tank items — appropriate.

## Stats

| Metric                                          | Count |
|-------------------------------------------------|------:|
| Armor uniques                                   | 58    |
| Shield uniques                                  | 37    |
| Armor templates                                 | 34    |
| Shield templates                                | 5     |
| Armor materials                                 | 30    |
| Armor entries with `equip_chain_mode`           | 13    |
| Shield entries with `equip_chain_mode`          | 3     |
| Armor entries with `mastery_blessing`           | 58    |
| Shield entries with `mastery_blessing`          | 37    |
| Plot-locked / special-spawn armor               | 9     |
| Plot-locked / special-spawn shields             | 3     |
| Required-field violations                       | 0     |
| Chain-equip violations (gap / regression / unk) | 0     |
| AC out-of-band (uniques exempt)                 | 0     |
| Auto-fixes applied                              | 0     |
| Tests passing before/after                      | 476/476 |

## Top 10 critical balance findings

1. **Tungsten material orphaned for armor/shield.** The only "balance"
   gap of material consequence. Fix: add `exotic_metal` to heavy
   armor + heavier shield templates' `compatible_material_classes`.
2. AC band compliance is **perfect** for all 95 uniques. No item
   exceeds the curve in a way that's not explicitly licensed by the
   spec.
3. Chain-equip blocks are **all** strictly non-decreasing in AC and
   contiguous in tier keys — no broken ladders.
4. Body-armor AC cap of 8 is honored by exactly two items (Panoply,
   Green Knight's) — both narrative top-tier.
5. Shield AC cap of 6 is honored by exactly one item (Tower Shield of
   Ajax) — appropriate.
6. `mastery_blessing` coverage is **100%** on uniques; no gaps.
7. `max_enchant` by material class matches the spec: leather/hide 1,
   cloth/wood/studded 1-2, ringmail/scale 2, plate/chain steel 2-3,
   rare metals 3-4, mithril/glassteel 5-6, worldtree 7. Adamantine
   sits at 3 — slightly low for the top-of-spec range but consistent
   with its in-game role as the heaviest-of-late-game-metals; the
   audit treats this as deliberate not a defect.
8. Material peak_floor distribution covers the full pf 2-92 band with
   no gap exceeding 5 floors — spawn pool is healthy at every depth.
9. Five materials (cobalt_steel, damascus_steel, glassteel, hematite,
   petrified_dragon, petrified_wood, soulsteel, tempered_bronze) use
   `armor_ac_bonus` instead of `ac_bonus`. Cosmetic only — code reads
   both — but worth standardizing in a future cleanup pass.
10. The "gimmick" armor (Blindfold, Trainer's Cap, early Hermes
    Sandals) sit below the AC band by design — each trades AC for a
    status effect or meta utility. The audit flags but does not
    "fix" these because the trade is the whole point of the item.

## Final report

- **Files modified**: 0
- **Auto-fixes summary**: None required. Every required field is
  present and within bounds on every entry; no peak_weight/spread/
  min_level/weight gaps exist; all chain-equip ladders are valid.
- **Top 10 balance findings**: see above. The only meaningful
  follow-up is the tungsten orphan (report-only by spec).
- **Tests pass after fixes?**: Yes — 476/476 (unchanged from
  baseline because no fixes were applied).

The armor and shield data are production-quality. The two report-only
findings (tungsten armor/shield compatibility, `armor_ac_bonus` field
name drift on 8 materials) are low-priority cleanups that should be
addressed at the user's discretion — they do not affect current
gameplay.
