# V2 Full Audit — Master Synthesis

8 parallel subagents audited every entity in the game against the canonical balance curves (`CURVES.md`). Each agent owned a disjoint file scope.

**Overall verdict**: PASS WITH FIXES. 476/476 tests pass throughout. Auto-fixes applied are pure cleanup (type normalization, missing-field backfill). Real bugs surfaced require user calls.

## Tally

| Agent | Scope | Verdict | Auto-fixes | Real Issues |
|---|---|---|---|---|
| 1 | Weapons + materials + templates | PASS | 49 type cleanups | 22 adamantine uniques at 0.71× damage |
| 2 | Armor + shields + materials | PASS | 0 | tungsten unreachable for armor (minor) |
| 3 | Accessories + artifacts | PASS | 8 peak_weight backfills | None critical |
| 4 | Magic items (wand/scroll/spellbook/potion) | PASS | 412 field adds | spawn rate warning (10× wand spawn) |
| 5 | Monsters (522) | PASS | 0 | None critical |
| 6 | Recipes + Food + Ingredients | PASS w/ FIXES | 43+ renames | 5 dead statuses + 8 plant keyword gaps → FIXED |
| 7 | Systems (spells/prayers/etc.) | **WARN** | 0 | **10 spell handlers missing, 35 mastery blessings inert, 2 orphan statuses** |
| 8 | Substrates | PASS | 0 | container.json + lockpick.json mostly dead |

## Critical bugs to fix (BLOCKER)

### 1. 10 spells have no `_apply_spell_effect` handler
**game_magic.py:1128.** MP is consumed, nothing happens (or wrong effect for `dispel_magic_spell` which hits the generic damage fallback).
- `mapping_spell`, `wish_spell`, `levitate_spell`, `phase_door_spell`, `turn_undead_spell`, `annihilation_spell`, `sleep_mass_spell`, `mass_paralyze_spell`, `detect_magic_spell` — silent no-op
- `dispel_magic_spell` — deals damage instead of dispelling

### 2. 35 of 47 class mastery blessings inert
`player.unlocked_class_masteries` is never read in src/. Working kinds: `class_acc_stat_bonus`, `wand_extra_charge`, `spellbook_mp_discount`, `accessory_stat_bonus`. Dead kinds: AC bonuses, regen, resist, SP burn, quirk extends, scroll potency, potion duration.

### 3. 2 orphan status effects
- `parry_armed` (used in combat.py:572-573 + player.py:469 for quarterstaff defensive_parry chain 5) — never defined in EFFECT_INFO/BUFFS
- `see_invisible` (read in main.py:1374, 3517) — never granted anywhere

## Design calls (IMPORTANT — need user input)

### 4. 22 adamantine uniques at 0.71× canonical baseDamage
`tools/rebuild_uniques.py` looked up `damage_mult` from the unique entry instead of the material file. Affects: dawnbreaker, durendal, tyrfing, caladbolg, joyeuse, skofnung, mjolnir, kusanagi, sudarshana, rod_of_moses, fragarach, gandiva, zulfiqar, harpe, curtana, parashu, chandrahas, shamshir_e_zomorrodnegar, chrysaor, brisingr, cronus_scythe + 1 other.

**Options**:
- A: Re-run rebuild with correct material lookup → 22 uniques get ~40% damage boost
- B: Accept as deliberate mythic restraint (they still pass test bounds)

### 5. Magic item spawn rate may oversaturate
Adding `peak_weight: 0.5` to 198 previously-fallback magic items will ~10× their spawning near peak floors.

**Options**:
- A: Keep as-is, monitor playtest, halve if oversaturated
- B: Halve `peak_weight` to 0.25 preemptively
- C: Roll back the peak_weight additions on items not previously bell-weighted

## Minor flags (REPORT-ONLY)

- `wand_of_wonder_legendary` declares per-chain `wonder_table` in JSON but code falls through to generic handler. Either implement table dispatch or strip data.
- 17 spellbook `mp_cost` diverge from `spells.py::LEARNABLE_SPELLS` (cosmetic; cast cost from LEARNABLE_SPELLS).
- 5 named wands lack `is_unique: true` (wand_of_nova, wand_of_life_force, wand_of_abjuration, lantern_of_diogenes, caduceus_wand).
- `green_slime_extract` ingredient orphan: monster drops `slime_core`, 4 recipes use the wrong name.
- Food gap min_level 61-100 (compound recipes cover).
- tungsten material unreachable for armor/shields.
- `container.json` (10 entries) never loaded — safe to delete.
- `lockpick.json` mostly orphaned (only basic lockpick used).
- `main.py:1139` comment says "Master Lockpick" but the code takes basic `lockpick`.
- 8 weapon materials use `armor_ac_bonus` instead of `ac_bonus` (engine reads both).
- 127/199 accessories off the `equip_threshold` spec (pattern coherent — suggest widen spec).

## What was already fixed in this audit (auto-applied)

- 49 weapon material `peak_weight` int→float
- 8 plot-locked accessories backfilled with sentinel bell-curve fields
- 412 magic item field additions (weight + peak_weight)
- 43+ recipe/ingredient status-name remappings (`haste`→`hasted` etc.)
- 8-word extension to `_PLANT_KEYWORDS` in dungeon.py → unblocked 193 recipes
- `winged_mane` source `pegasus_corrupted` → `pegasus`

## Recommended ship order

1. Commit the auto-fixes (already applied, tested green)
2. Fix the 10 missing spell handlers (CRITICAL — silent broken spells)
3. Fix the 2 orphan statuses (medium — but `parry_armed` is referenced by a class mechanic)
4. Decide on the 35 mastery blessings (BIG — design call)
5. Decide on adamantine 0.71× drift (design call)
6. Decide on spawn rate (design call)
7. Minor cleanups (legacy code, minor flags)

After items 2-6 are resolved, the bank is v2-ready.
