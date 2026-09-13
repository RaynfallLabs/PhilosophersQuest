# Weapons audit — v2.15.0 readiness

**Scope:** `data/items/weapon.json` (96 uniques), `data/materials/weapons/*.json` (54 files after the v2.14.0 material rebuild), `tools/balance/generated/templates/weapons/*.json` (22 base templates), `src/combat.py` and `src/items.py` (Weapon class + all `getattr(weapon, ...)` reads), plus the three design docs (`chain_combat_v2.md`, `weapon_specials_v2_14.md`, `uniques_v2_14.md`).

Read-only audit — no code was changed.

---

## Severity summary

| Sev | Count | Notes |
|-----|-------|-------|
| P0  | 0     | No load / equip / attack crash paths found. |
| P1  | 4     | Camel/snake `baseDamage` mismatches make 4 uniques deal the wrong damage at runtime (camel wins); common `weapon_class='blunt'/'polearm'` templates dispatch to a key with no chain-special ladder — every common mace/warhammer/quarterstaff/flail/glaive/maul/club skips class specials entirely; 6 unique clubs likewise get no ladder; three uniques still carry the retired `cleave_at_max` `class_mechanic` that now double-fires alongside the class ladder. |
| P2  | 3     | Dead JSON flags (`ignore_armor`, `equipped_sound_radius_modifier`, `equipped_monster_aggro_radius`) on iconic uniques; Boomstick's `ranged` + `shell` ammo routes to the bow special ladder instead of the crossbow one (design intent was crossbow); `punch_in_the_face` load-time `baseDamage 9999` produces one-shot 9999-damage hits (min_level 9999 keeps it out of RNG but any code path that grants it is one-shot). |
| P3  | 3     | 14 materials referenced by uniques have no file in `data/materials/weapons/` — non-fatal (uniques bake damage in) but reference is inconsistent; 77 uniques carry legacy `chainMultipliers` values that differ from their `chain_multipliers` twin — camel wins at load and drives `max_chain_length`, but 21 also differ in length so the "which array is authoritative" is invisible to a reader; Chandrahas + Chandrahasa are two live entries with confusingly similar names. |
| P4  | 3     | Floor-spawn totals are lumpy (81-100 band = 24%, 61-80 band = 18%, vs ~20% target); `_curve_note` fossil fields on ~40 uniques are stale (reference tier bases and formulas from before the v2.14.0 rebase); 11 template `class_mechanic` values (`bleed_on_chain3`, `stun_on_chain3`, `cleave_plus_bleed`, `cleave_on_kill`, `primitive`, `range_8`, `ranged_precision`, `clean`, `stun_plus_anti_heavy`, `cheap_ammo`, `reach_1`) never match any branch in `combat.py` — legacy strings kept for lore only. |

---

## Coverage matrix (top-line)

- **Formula compliance.** 96/96 uniques carry `chain_exponent` (default 1.15) so the polynomial damage path always fires. No unique is stranded on the array path.
- **Iconic-bump table (uniques_v2_14.md §"Iconic exception bumps").** All 21 named iconic weapons carry `base_damage` values matching or close to the doc's target: Excalibur 16, Anduril 16, Aiglos 16, Kusanagi 16, Mjolnir 32, Dawnbreaker 30, Stormbringer 24, Tyrfing 26, Sword of Michael 18, Trident of Poseidon 18, Chandrahasa 18, Gram 18, Mistilteinn 18, Gungnir 15, Ruyi Jingu Bang 24, Laevateinn 26, Wendigo's Fang 12, Soul Reaver 14, Sudarshana 14, Fail-not 10 (base_damage) / 16 in `baseDamage` — see P1-3, Gandiva 12.
- **Boss unique_drop_id → weapon uniques.** 4 weapons are boss-only drops (`echidna → echidna_fang`, `cacus → vulcans_brand`, `wendigo → wendigo_fang`, `wild_hunt_captain → hunt_captains_sword`). All 4 have `min_level: 9999`, empty `floorSpawnWeight`, and never appear in RNG loot — correct.
- **Quest items (broken_gram, gram, sword_of_michael, punch_in_the_face).** All 4 have `min_level: 9999`, empty `floorSpawnWeight` — correct.
- **Character-locked (boomstick, chainsaw_prosthetic, witcher_silver_blade, zireael).** All 4 have `min_level: 9999`, empty `floorSpawnWeight` — correct.
- **Material integration.** 40 unique-referenced material strings resolve to files in `data/materials/weapons/`; 14 do not (see P3-1). None of the 14 causes a crash because unique damage is baked in and `_load_material_tags` falls through silently when a material id is missing.
- **`weapon_class_chain` values.** 96/96 uniques carry one of the three legacy values (`normal`, `heavy`, `finesse`) — mostly cosmetic under chain combat v2 (the polynomial replaced per-rung arrays); safe to leave.

---

## P0 — Crash paths

None found. `Weapon.__init__` uses `.get(...)` with typed defaults for every field, so missing keys never raise. `_apply_chain_class_post_damage` no-ops on unknown weapon keys and unknown chain thresholds. `_load_material_tags` silently returns 1.0 for unknown materials.

---

## P1 — Broken mechanics / silent misfires

### P1-1  Common maces/warhammers/quarterstaves/flails/clubs/mauls/glaives fire NO chain-special ladder
- **Files:** `src/combat.py:128-159` (`_weapon_key`); `tools/balance/generated/templates/weapons/{mace,warhammer,flail,quarterstaff,club,maul}.json` (all `weapon_class: "blunt"`); `glaive.json` (`weapon_class: "polearm"`).
- **Symptom:** `instantiate_weapon` (items.py:1746-1747) copies `tpl.weapon_class` into both `class` and `weapon_class` on the built weapon. `_weapon_key` maps sword/axe/spear/dagger/staff/rapier/scimitar/morningstar/warhammer/zweihander/ranged to implemented ladder keys but has NO case for `blunt` or `polearm`; it falls through to `return wc`. The ladder dispatcher (`_apply_chain_class_post_damage`) has no `blunt` or `polearm` branch and returns an empty side-effects dict.
- **Impact:** every common mace / warhammer / flail / quarterstaff / club / maul / glaive that spawns from the material×template loot pipeline chains through the polynomial for damage but never applies `stunned`, `armor_crack`, `sundered`, `bleeding`, `slowed`, cleave AoE, or any of the design-doc rung effects. Only UNIQUE weapons with the correct `class` value (mace, warhammer, glaive, staff — set explicitly per unique) fire the ladder.
- **Fix sketch:** add `if wc == 'blunt': ...` to `_weapon_key` mapping to 'mace' or '2h_warhammer' by hand-weight / two-handed check, and `if wc == 'polearm': return 'glaive'`. Ideal: rename the templates' `weapon_class` to the design-doc names.
- **Severity:** P1 — half the common weapon roster is quietly missing its chain-5/10/15/20 identity.

### P1-2  `baseDamage` (camelCase) overrides `base_damage` (snake_case) at load — 4 uniques deal wrong damage
- **File:** `src/items.py:306` — `self.base_damage: int = int(defn.get('baseDamage', defn.get('base_damage', 5)))`. `.get('baseDamage', ...)` wins whenever the camel key is present.
- **The rebase mismatches (camel wins):**
  - `chandrahas` — `baseDamage: 32`, `base_damage: 14` → runtime base **32** (T4 scimitar; target ~15 per formula, so 2× too high, chain-5 ≈ 208 vs peer T4 median ≈ 90).
  - `punch_in_the_face` — `baseDamage: 9999`, `base_damage: 35` → runtime base **9999** (see P2-3).
  - `sword_of_damocles` — `baseDamage: 11`, `base_damage: 8` → runtime base **11** (minor).
  - `atalanta_bow` — `baseDamage: 10`, `base_damage: 7` → runtime base **10** (minor).
  - `meleager_spear` — `baseDamage: 23`, `base_damage: 8` → runtime base **23** (T2 spear, target 12 per formula, so 2× too high; chain-5 ≈ 150 on a T2 weapon — outsized).
- **Root cause:** the doc's rebase script (`tools/balance/rebase_uniques_v2_14.py`, per uniques_v2_14.md §"Per-unique execution plan") wrote `base_damage` but never removed or updated `baseDamage`. The load-order in items.py preserves the LEGACY value.
- **Fix sketch:** either (a) strip `baseDamage` from all 96 uniques where it duplicates `base_damage`, or (b) flip the fallback order in items.py so snake_case wins. Option (a) is safer; option (b) affects ALL Weapon fields at once (any camel key would be silently ignored, breaking any weapon with only camel written).
- **Severity:** P1 — 3 of the 5 are minor overshoots but `chandrahas` and `meleager_spear` land at ~2× tier-peer damage, and `punch_in_the_face` becomes a one-shot god.

### P1-3  Three uniques still carry `class_mechanic: cleave_at_max` after the v2.14.0 "retired" sweep
- **Files:** `data/items/weapon.json` — `caladbolg` line 788, `parashu` line 2210, `labrys` line 2286.
- **Doc reference:** `uniques_v2_14.md` §"Redundant class_mechanic values retired" explicitly names `cleave_at_max` as a retired value that "the class chain-special ladder covers … for free" and says "Leaving them in double-fires the effect."
- **Symptom:** Combat pipeline runs the class-ladder cleave at chain 5+/10+/15+/20+ (for 2h_axe / 2h_sword / axe / glaive) AND the legacy `class_mechanic == 'cleave_at_max'` branch in `combat.py:1876` at max chain, producing a second AoE 0.5× hit on adjacent monsters. Two AoE sweeps per swing, doubled sundered / bleeding statuses.
- **Fix sketch:** delete the `class_mechanic: "cleave_at_max"` line from those three unique entries. Also delete `labrys`' duplicate `class_mechanic_desc`.
- **Severity:** P1 — the rebase design explicitly forbids this shape; three iconic axes fire cleave twice per max-chain swing.

### P1-4  6 unique clubs get NO chain-special ladder
- **Files:** `data/items/weapon.json` — `sigurds_shovel`, `sharur`, `heracles_club`, `theseus_club`, `cain_club`, `cuchulainn_hurley` (all `class: "club"`).
- **Symptom:** `_weapon_key` has no `club` case → returns `'club'` → no branch in the dispatch → empty side-effects. Every unique club chains for damage but applies no bleed/stun/sunder/AoE at any threshold. Design docs list only 16 canonical classes (`chain_combat_v2.md` §"Weapon classes (16)"), none named "club" — the class was informally added to weapon.json for lore but never made the ladder.
- **Impact:** Cain's Club, Hercules's Olive-Club, Theseus's Club, and three others feel numerically similar to a generic weapon at every chain rung — no signature "the club stuns," no cleave, no AoE. Contrast with maces/warhammers (which do get the ladder when unique-authored with class='mace' etc.).
- **Fix sketch:** either add a `club → mace` case to `_weapon_key` (design-consistent — clubs are blunt-family) OR re-class each unique's `class` field to `mace` or `club`-under-`blunt` after resolving P1-1.
- **Severity:** P1 — 6 iconic weapons across floors 12-49 land unfulfilled.

---

## P2 — Balance / dead-flag issues

### P2-1  Dead JSON flags on iconic uniques
- **Files:** `data/items/weapon.json` (fields load only, never read):
  - `talos_sickle` — `ignore_armor: 1` (line 6648). **Zero** consumer in `src/`. Not even loaded in `items.py`. The doc-promised "cuts through armor" identity does nothing; probably meant to set the standard `ignoreShield: true` or add to `class_mechanic: armor_pierce_at_max`.
  - `fragarach_the_whisperer` — `equipped_sound_radius_modifier: -0.5` (line 3254). Loaded in `items.py:531`, but grep across `src/` shows **no consumer** — no code path applies the sound-radius modifier to the player or monster hearing radius. "Assassins' silent companion" is inert.
  - `cain_club` — `equipped_monster_aggro_radius: 2` (line 6811). Loaded in `items.py:505`, but grep shows **no consumer** — no code path adjusts beast aggro range for the equipped weapon. "Beasts sense the mark of Cain" is inert.
- **Fix sketch:** either wire the consumers (each is a ~5-line change in the aggro / sound / attack paths) or drop the flags from the JSON.
- **Severity:** P2 — three named uniques advertise mechanics that never fire; the item feels legendary but plays as generic.

### P2-2  Boomstick routes to the bow ladder, not the crossbow ladder
- **File:** `src/combat.py:150-158` (`_weapon_key`); `data/items/weapon.json` boomstick line 4611 (`class: "ranged"`, `requiresAmmo: "shell"`, no `infiniteAmmo`).
- **Symptom:** `_weapon_key` checks `if 'bolt' in ammo_type.lower(): return 'crossbow'` and `if infinite_ammo: return 'sling'`, else `return 'bow'`. `"shell"` contains neither `"bolt"` nor sets infinite, so Boomstick fires **bow** chain-specials (bleed → blinded → bypass DR → vitals x2) instead of crossbow (bypass DR from chain 5 + skip reloads + Ballista pierce). Design intent per `template_basis: "crossbow"` + `weapon_class_chain: "heavy"` was the crossbow ladder.
- **Fix sketch:** add `if 'shell' in ammo_type.lower(): return 'crossbow'` to the ranged dispatch, or set `requiresAmmo: "bolt"` on the Boomstick (breaks lore).
- **Severity:** P2 — cosmetic mismatch, still fires SOMETHING, but shotgun shells should punch through armor not blind.

### P2-3  `punch_in_the_face` deals 9999 damage per hit at runtime
- **File:** `data/items/weapon.json` line 3337 (`baseDamage: 9999`) vs line 3382 (`base_damage: 35`).
- **Symptom:** per P1-2, camelCase wins. Runtime `Weapon.base_damage = 9999`. `chain_multipliers` = `[1.0]` length 1, so `max_chain_length = 1` — but the polynomial path takes over (`chain_exponent = 1.15`) and computes `mult = 1**1.15 = 1.0`. Damage = 9999 × 1.0 = 9999 per swing. Fist swing one-shots anything short of a boss-tagged monster (which has bosses in the multi-thousands HP range, but even 9999 is close to boss max HP).
- **Blocking factor:** `min_level: 9999`, empty `floorSpawnWeight`, no spawn path in monster drops. Only reachable via a debug or scripted grant. The lore says "Dad-tier meta joke Easter egg; not part of the balance curve" (uniques_v2_14.md line 92) — so 35 was the intended iconic bump.
- **Fix sketch:** delete `baseDamage: 9999` from the entry (per P1-2 sweep).
- **Severity:** P2 — currently only reachable via non-RNG grants but if any wizard-mode / cheat / debug path exposes it, it's one-shot immortal.

---

## P3 — Reference / data-consistency drift

### P3-1  14 unique-referenced materials have no file in `data/materials/weapons/`
- **Missing materials (with users):**
  - `bone` (wendigo_fang, gae_bolg_fragment)
  - `dad` (punch_in_the_face) — joke material, ignore
  - `dark_iron` (penitents_blade, khopesh_of_anubis)
  - `divine` (sword_of_michael)
  - `divine_bronze` (vel_of_murugan)
  - `divine_iron` (ruyi_jingu_bang)
  - `enchanted_iron` (carnwennan, caliburn, green_chapel_axe)
  - `fang` (echidna_fang)
  - `gold` (sword_of_damocles)
  - `hardwood` (thyrsus, pharaohs_crook, bow_of_rama, staff_of_moses, cain_club, cuchulainn_hurley, mwindo_axe) — 7 uniques
  - `leather` (sling_of_david)
  - `legendary` (24 uniques — hrunting, fail_not, mistilteinn, laevateinn, ridill, kladenets, fragarach_the_whisperer, naegling, chandrahasa, aiglos, akinakes_acrisius, anduril, atalanta_bow, bellerophon_lance, cadmus_sword, glamdring, hector_javelin, heracles_club, hofud, meleager_spear, pelops_sword, stormbringer, talos_sickle, theseus_club)
  - `spectral_iron` (hunt_captains_sword)
  - `wood` (prometheus_torch)
- **Impact:** `_load_material_tags` silently falls through with `1.0` multipliers for these — the unique still deals its baked-in damage but never picks up any material `effective_against` bonus. Uniques generally carry their own `effective_against` array, so downstream behavior is correct in practice.
- **Fix sketch:** add stub JSON files for these material ids (name, damage_mult 1.0, effective_against based on lore) so the reference table is complete and future common weapons could use them. Or clean up the string on the uniques to point at an existing material.
- **Severity:** P3 — not a bug, but a data-integrity red flag.

### P3-2  `chainMultipliers` vs `chain_multipliers` twin arrays disagree on 77/96 uniques; length differs on 21
- **File:** `data/items/weapon.json` throughout; `src/items.py:309-310` — `defn.get('chainMultipliers', defn.get('chain_multipliers', [0.5, 1.0, 1.5, 2.0, 2.5]))`. CamelCase wins on load.
- **Which array actually matters?** Under chain combat v2, `chain_multipliers` is not used for damage (the polynomial from `chain_exponent` takes over), BUT `max_chain_length` (a property in `items.py:630-632`) is `len(chain_multipliers)`, and max-chain gates a lot of unique triggers: `damoclean_counter`, `boss_doom_dot_at_chain_5`, `multi_arrow_at_chain_5`, `return_to_hand_ward`, `chain_no_reset_on_tag`, `reveal_tag_on_chain_5_kill`, `damage_double_vs_resistant_at_max`, `petrify_on_crit`.
- **Length-differs cases (camel wins, so the LONGER camel is authoritative):** gram (9 vs 5), broken_gram (3 vs 5), hunt_captains_sword (8 vs 5), wendigo_fang (7 vs 5), echidna_fang (8 vs 5), vulcans_brand (7 vs 5), sword_of_michael (6 vs 5), sudarshana (10 vs 5), several others. In all cases the AUTHOR intent (long chain for a hero weapon) survives via camel, but the code reader has to spot which array wins.
- **Fix sketch:** strip the snake_case `chain_multipliers` when it merely duplicates the class-template default and is shorter than the camel, or normalize on ONE spelling for all uniques (recommend snake_case, since the rest of items.py prefers it).
- **Severity:** P3 — no runtime bug, but the JSON is confusing and future edits will race the two spellings.

### P3-3  Two live "Chandrahas" entries with confusingly close names
- **File:** `data/items/weapon.json` — `chandrahas` (T4 scimitar) at line 2289; `chandrahasa` (T5 sword) at line 5446.
- **Note:** The two seem to be different re-tellings of the same Indian myth (Ravana's moon-blade). Design might be intentional (two variants for two floors), but the name similarity + the base_damage bug on `chandrahas` (see P1-2) make it hard to reason about which one a playtester is holding.
- **Severity:** P3 — the name collision is a UX foot-gun; also worth cross-checking `known_item_ids` / identify UI doesn't conflate them.

---

## P4 — Nits / cosmetic

### P4-1  Floor-spawn totals are lumpy
- **Data:** total floorSpawnWeight per band across all 96 uniques = 36 (1-20) / 36 (21-40) / 36 (41-60) / 34 (61-80) / **44 (81-100)**. Ratio 20/20/20/19/24. Target was ~20% each (see task item 7).
- **Cause:** the F80s got extra fill from the recent LOTR / Norse bump additions (aiglos, anduril, glamdring, hofud, stormbringer, mistilteinn, laevateinn) with weight 2 each.
- **Fix sketch:** trim one of the F81-100 entries by 2 weight or add 2 weight to a mid-tier candidate. Non-blocking.
- **Severity:** P4.

### P4-2  Stale `_curve_note` fields on ~40 uniques
- **Files:** `data/items/weapon.json` throughout — searches for `_curve_note` return ~40 hits, most referencing formulas like `curve.weapon_base_damage(87) x 1.65` from a pre-v2.14 balance pass. These are comments about how the base_damage USED to be derived; they no longer match the current `base_damage` values (see P1-2 where chandrahas has stale curve_note "peak=87, base=34" but base_damage is now 14).
- **Severity:** P4 — code doesn't read them, but a future rebase reader would be misled.

### P4-3  11 template `class_mechanic` values never match any handler
- **File:** `tools/balance/generated/templates/weapons/*.json`. Dead values: `bleed_on_chain3`, `stun_on_chain3`, `cleave_plus_bleed`, `cleave_on_kill`, `primitive`, `range_8`, `ranged_precision`, `clean`, `stun_plus_anti_heavy`, `cheap_ammo`, `reach_1`. None match a string in `combat.py`. Presumably the templates were written to a pre-v2.14 vocabulary and never renamed.
- **Impact:** commons carry a `class_mechanic` string that displays in the Kit / Examine info panel (via `class_mechanic_info` in `combat.py:80-93`) as a Title-Cased humanized version with empty description — a menu that promises "Bleed On Chain3" but says nothing about what it does.
- **Fix sketch:** rename each template's `class_mechanic` to a value the code branches on (e.g. `bleed_on_chain3` → `bleed_at_max`, `cleave_on_kill` → `cleave_at_max`, `stun_plus_anti_heavy` → `stun_at_max` + `anti_heavy_at_max` split, etc.), or drop the field.
- **Severity:** P4 — cosmetic UI clutter, not a mechanical issue.

---

## Notes for follow-up (out of scope for this audit)

- The `_weapon_key` mapping has an implicit design coupling to `class` vs `weapon_class` values that isn't documented — every future template/unique add needs to remember to use `mace/warhammer/glaive/spear/staff` (not `blunt/polearm`) or the ladder silently misses.
- 2H warhammer ladder fires from `class='warhammer'` regardless of `variant='1h'` (Mjolnir gets 2-tile AoE). Intentional per lore but worth documenting.
- `net_of_hephaestus` (class='net') gets no chain-special ladder — this IS intentional per `uniques_v2_14.md` §"Removed / demoted" ("its identity is entangle-on-hit, not a chain builder"). Confirmed correct.
- Design doc `chain_combat_v2.md` §"Migration order" step 6 says the material rebuild targets 27 files; actual folder has 54. The extra 27 are legitimate additions (blackthorn, cobalt_steel, damascus_steel, dragonbone, elven_silver, ghost_iron, glassteel, godweave, hardened_gold, hematite, leviathan_rib, meteoric_iron, obsidian, petrified_dragon, petrified_wood, pig_iron, primordial_stone, quicksilver, soulsteel, starmetal, tempered_bronze, tin, titanforged, treant_heart, tungsten, willow, wormwood). Consider a follow-up doc pass to reflect the expanded material palette.
