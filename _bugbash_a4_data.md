# A4: Data Integrity Audit

Surface: JSON game data under `data/`. Cross-references against `src/`.

Methodology: 12-phase scan (JSON syntax, cross-file dup IDs, code-vs-JSON references, mandatory fields, mastery_blessing schema, material/template combos, monster refs, mastery_class lookups, color shape, tier coverage, material descriptors, JSON syntax). All phases ran via offline Python scripts (`_audit_a4*.py`).

---

## Phantom items (declared in JSON, unreachable from code)

### [CRITICAL] `pandoras_box` is unreachable — cannot spawn AND cannot be used
**File(s)**: `data/items/artifact.json`
**ID(s)**: `pandoras_box`
**What I see**: Full JSON definition with `min_level: 30`, `peak_floor: 50`, `spread: 15`, `peak_weight: 0.3`, plus rich mechanics (`use_quiz_subject: theology`, `use_quiz_mode: threshold`, 20-entry `chaos_table`, failure-skew table, `consumed_on_use: true`, `score_bonus_on_use: 5000`). **Zero references in `src/`** — not in any spawn pool, not in any chest template, not handled by any use-quiz dispatcher (no source matches for `chaos_table`, `use_quiz_subject`, `consumed_on_use`, `wish_menu`). `dungeon.spawn_items()` only spawns from pools `('weapon','armor','shield')` for uniques and `('accessory','wand','scroll','spellbook')` for magic — artifacts are excluded from random spawns. Chest templates don't reference it either.
**Why it matters**: A fully-authored "wonder relic" that the player can never obtain or use. Hours of design work invisible to the game.
**Suggested fix**: Either (a) wire up an artifact spawn pool / chest entry + write the `consumed_on_use` + `chaos_table` use-quiz handler in `game_magic.py`, or (b) remove from `artifact.json` if shelved. The JSON spec is internally complete enough to drive an implementation — file is a design doc with no consumer.
**Confidence**: HIGH

### [CRITICAL] `aladdins_lamp` is unreachable — cannot spawn AND cannot be used
**File(s)**: `data/items/artifact.json`
**ID(s)**: `aladdins_lamp`
**What I see**: Same shape as `pandoras_box`. `min_level: 35`, `peak_floor: 60`, full `wish_menu` (item/power/entity categories), `wish_fallback_effects`, `consumed_on_use`, `use_quiz_subject: theology`, escalator_threshold T5 4/5. **Zero references in `src/`**. No spawn path, no use handler.
**Why it matters**: Identical to pandoras_box — phantom item with rich mechanics no code reads.
**Suggested fix**: Same as pandoras_box — wire it up or delete from JSON.
**Confidence**: HIGH

### [CRITICAL] `palladium` cannot spawn — handler exists but loot tables exclude it
**File(s)**: `data/items/artifact.json`
**ID(s)**: `palladium`
**What I see**: Has effect handler at `src/main.py:1349` (`_has_palladium = any(... 'palladium' ...)`). JSON declares `spawn_method: 'random_lore_quest_mid_dungeon'`, `min_level: 45`, `peak_floor: 50`, `spread: 19`. **No code handles the `random_lore_quest_*` spawn methods** (zero grep hits). `dungeon.spawn_items()` does not include artifacts in any roll-able pool. Chest templates do not list `palladium`. `tests/test_artifact_mechanics.py:137` confirms the artifact loads from JSON — but loading ≠ spawning.
**Why it matters**: Player code branch is dead — the effect (mid-fight quiz reroll? per the `_has_palladium` usage at main.py:1349) can never fire because the item can never enter inventory.
**Suggested fix**: Implement a `random_lore_quest_mid_dungeon` spawn hook in `level_manager.py` or `dungeon.py`, OR add `palladium` to an appropriate chest template at L40-L60, OR remove the dead JSON.
**Confidence**: HIGH

### [CRITICAL] `tablet_of_destinies` cannot spawn — same shape as palladium
**File(s)**: `data/items/artifact.json`
**ID(s)**: `tablet_of_destinies`
**What I see**: Has effect handler at `src/main.py:3553-3555` (`_has_tablet_of_destinies`) and is checked in `src/game_combat.py:1332, 1378, 1496` for the quiz-reroll bonus. JSON declares `spawn_method: 'random_lore_quest_deep_dungeon'`, `min_level: 70`. **No `random_lore_quest_*` handler in source**.
**Why it matters**: Implemented combat feature (free quiz reroll once per combat) that no player will ever experience.
**Suggested fix**: Same as palladium — implement the deep-dungeon spawn hook OR add to a high-tier chest template (`reliquary`, `gilded_chest`, etc.) OR remove.
**Confidence**: HIGH

---

## Mastery system holes

### [WARN] 26 artifacts have no `mastery_blessing` and `_default_mastery_for` doesn't handle `Artifact`
**File(s)**: `data/items/artifact.json`, `src/game_magic.py:2607-2614, 2683-2712`
**ID(s)**: `philosophers_stone`, `bronze_bull`, `eye_of_graeae`, `cats_footstep`, `womans_beard`, `mountain_root`, `fish_breath`, `bird_spittle`, `bear_sinew`, `gleipnir`, `leather_scrap`, `seal_of_wrath`, `seal_of_pestilence`, `seal_of_famine`, `seal_of_war`, `seal_of_death`, `seal_of_earthquake`, `seal_of_silence`, `scales_of_michael`, `cursed_lodestone`, `sealed_dispatch`, `palladium`, `tablet_of_destinies`, `vidars_sandal`, `pandoras_box`, `aladdins_lamp`
**What I see**: Every artifact is flagged `is_unique: true` (302 total uniques bank-wide; 26 of them in artifact.json). None have `mastery_blessing` set. The fallback `_default_mastery_for(item)` only branches on `Weapon/Armor/Shield/Accessory/Wand/Scroll/Spellbook/Potion` — no `Artifact` branch. In `_claim_mastery`: if `blessing` is None, function returns silently AFTER the message "You have mastered the {item.name}!" already printed (game_magic.py:2557-2560). The artifact's `id_level` becomes 5 and `unlocked_masteries` is NOT updated. `_needs_identify` filter for uniques is `item.id not in player.unlocked_masteries` (game_menus.py:647), so **the mastered artifact stays in the identify menu forever**, and re-quizzing it shows no progress.
**Why it matters**: If any of these spawnable artifacts (e.g. philosophers_stone, vidars_sandal, scales_of_michael) reaches chain-5 in identify, the player sees a "Mastery!" success message but: (a) gets no blessing, (b) no follow-up "Mastery gained: …" message, (c) the artifact remains in the identify menu and can be re-quizzed indefinitely. Confusing UX bug.
**Suggested fix**: Either (a) add an `Artifact` branch to `_default_mastery_for` returning a conservative blessing (e.g. `{'kind': 'no_effect', 'desc': 'Your understanding of the {name} feels complete.'}`) AND record into `unlocked_masteries` even with no-op effects, OR (b) author per-artifact `mastery_blessing` entries for the spawnable plot artifacts in JSON, OR (c) short-circuit the artifact path early so chain-5 sets `unlocked_masteries[id] = {'kind': 'plot_item'}` to dequeue from the menu.
**Confidence**: HIGH

---

## Dead material data

### [WARN] `data/materials/armor/tungsten.json` cannot spawn as armor or shield
**File(s)**: `data/materials/armor/tungsten.json`
**ID(s)**: `tungsten`
**What I see**: `material_class: "exotic_metal"`. Walked every template in `data/templates/armor/*.json` and `data/templates/shields/*.json` — **no template's `compatible_material_classes` lists `exotic_metal`**. `pick_random_armor_for_floor` and `pick_random_shield_for_floor` filter materials to those accepted by at least one template, so tungsten is rejected. `data/materials/weapons/tungsten.json` is fine (accepted by `club`, `flail`, `mace`, `maul`, `warhammer` templates).
**Why it matters**: An entire authored armor material — peak_floor 48 anti-mage gear — is unreachable. Players never see tungsten boots / breastplates / tower-shields.
**Suggested fix**: Add `"exotic_metal"` to `compatible_material_classes` in at least one heavy armor template (`plate.json`, `full_plate.json`, `breastplate.json` are good candidates given the design notes about heavy/dense) and at least one shield template (`tower_shield.json` already accepts `exotic_organic`, so adding `exotic_metal` matches). Alternative: delete `data/materials/armor/tungsten.json`.
**Confidence**: HIGH

---

## Grammar bugs in item names (cosmetic + affects mastery_class slug)

### [MINOR] Four accessory names use grammatical errors in `name` field
**File(s)**: `data/items/accessory.json`
**ID(s)**: `ring_levitate`, `ring_invisible`, `ring_hasted`, `ring_clairvoy`
**What I see**:
- `ring_levitate` → `name: "ring of levitating"` (should be "ring of levitation")
- `ring_invisible` → `name: "ring of invisible"` (should be "ring of invisibility")
- `ring_hasted` → `name: "ring of hasted"` (should be "ring of haste")
- `ring_clairvoy` → `name: "ring of clairvoyant"` (should be "ring of clairvoyance")

Mastery-class slug is derived from `name` via `class_masteries._slugify`, so these become bare-class entries `ring_of_levitating`, `ring_of_invisible`, `ring_of_hasted`, `ring_of_clairvoyant` that don't match the authored CLASS_MASTERY_BLESSINGS keys (`ring_of_invisibility`, `ring_of_speed`, `ring_of_clairvoyance` etc.). They fall through to `default_blessing_for_class` (which still produces a usable buff-duration bonus, so they aren't broken — just don't get the bespoke `class_acc_quirk` blessings designed for the proper-named variants).
**Why it matters**: Player-facing display string is grammatically wrong ("ring of hasted" sounds like a child's typo). Also the bespoke class blessings for haste/invisibility/levitation/clairvoyance in `CLASS_MASTERY_BLESSINGS` never apply to these specific items.
**Suggested fix**: Rename `name` in JSON to the correct noun form. No id change needed (id is internal). The mastery-class slug will then naturally match the existing `CLASS_MASTERY_BLESSINGS` entries.
**Confidence**: HIGH

---

## Cross-class mastery_blessing kind (semantic oddity)

### [MINOR] Armor item uses accessory-kind mastery_blessing
**File(s)**: `data/items/armor.json`
**ID(s)**: `girdle_of_hippolyta`
**What I see**: `slot: 'legs'`, `item_class: armor` (injected at load), but `mastery_blessing.kind: 'accessory_stat_bonus'`. The handler in `_apply_mastery_once` routes by kind (not item type), and `accessory_stat_bonus` calls `p.apply_stat_bonus(stat, amount)` — so it works correctly (player gets +2 STR permanent). But semantically it's an armor piece awarding accessory-style permanent stat. This is the only cross-class kind usage bank-wide.
**Why it matters**: None for gameplay — it works. But future schema validation (and the lift-discovered-rules pattern from memory) would normally flag this. Likely intentional given Hippolyta's belt is conceptually accessory-like.
**Suggested fix**: Either accept the cross-class kind as intentional and document it, or rename the kind to `armor_stat_bonus` and add a matching branch in `_apply_mastery_once` (alias). No urgent action.
**Confidence**: MEDIUM (intentional design likely)

---

## Stale / dead data carriers

### [MINOR] Seven `seal_of_*` artifacts in JSON are never instantiated as game items
**File(s)**: `data/items/artifact.json`
**ID(s)**: `seal_of_wrath`, `seal_of_pestilence`, `seal_of_famine`, `seal_of_war`, `seal_of_death`, `seal_of_earthquake`, `seal_of_silence`
**What I see**: The seal-tracking mechanism in `game_combat.py:641-650` computes `seal_id = 'seal_of_' + monster.kind.replace('seal_demon_', '')` and adds to `self.seals_broken: set`. The set tracks integer count (0/7 → 7/7); no `Artifact` instance is ever created for these IDs and they never enter the player's inventory. JSON entries have `plot_locked: true` and `plot_role: seal_demon_drop` but the "drop" is conceptual — no code spawns them on the ground.
**Why it matters**: 7 entries in artifact.json that exist only as documentation. They'd never appear in the identify menu (never picked up) and contribute to phase-5 artifact-no-mastery-blessing list above (false positive). Not actively broken, just redundant data.
**Suggested fix**: Either (a) delete from `artifact.json` since `seals_broken: set` is the actual state tracker, or (b) author them as fragments that DO spawn on the corpse of each seal demon (would require monster `treasure` entries linking the seal artifacts) so the seal-counter has visible "things". Option (b) is closer to the design intent in JSON (`plot_role: seal_demon_drop`).
**Confidence**: HIGH

---

## False positives investigated (clean — listed for the record)

- **Phase 1: cross-file duplicate item IDs in `data/items/*.json` — 0 found.** User-noted `girdle_of_hippolyta` duplicate has been resolved (only in `armor.json` now).
- **Phase 2: items referenced in `src/` but missing from JSON — 9 found, all false positives.** All 9 (`abyssal_shimmer`, `complete_tablet_of_second_death`, `flux_capacitor`, `philosophers_wrench`, `scroll_deaths_bane`, `scroll_lake_of_fire`, `soul_sphere`, `unusual_soul_sphere`, `tablet_of_second_death`) are intentionally created via factory functions in `items.py:1158-1280` or inline `Artifact(...)` constructors in dungeon/main/mystery_system — deep-lore items not loaded from JSON by design.
- **Phase 4: mandatory fields (`id`, `name`, `symbol`, `color`, `weight`) — 0 missing.** Every item has them.
- **Phase 6: material × template combos — 0 crashes.** 770 weapon, 1020 armor, 235 shield combinations all instantiated cleanly (355 weapon combos succeeded despite class mismatch — fine because random pickers filter at the higher level).
- **Phase 7: monster IDs referenced in `src/` missing from `monsters.json` — 0 found.**
- **Phase 9: color tuples — all 3-int, all 0-255. 0 bad.**
- **Phase 10: `quiz_tier` values out of 1..5 — 0 found.** 596 quizable items; tier distribution {1: 122, 2: 150, 3: 129, 4: 99, 5: 96}.
- **Phase 11: material descriptors (`name`, `material_class`, `peak_floor`, `unidentified_descriptor`, `lore_descriptor`) — 0 missing across all 65 material files.** Material `id` field matches filename stem in all 65.
- **Phase 12: JSON syntax — all 218 files parse cleanly.**
- **Templates: `id` matches filename stem in 61/61. Compatible_material_classes only references the 12 known material classes.**
- **Recipes: all 483 recipes' ingredients point to valid `ingredient.json` or `food.json` entries.**
- **Chest templates: loot tables reference valid item categories.** No missing item references.
- **Monsters: 522 entries, all have mandatory fields, valid colors, valid `ingredient_id` references.**

---

## Summary

| Severity   | Count |
|------------|-------|
| CRITICAL   | 4     |
| WARN       | 2     |
| MINOR      | 3     |
| **Total**  | **9** |

**Headline**: Four artifact "wonder relics" (`pandoras_box`, `aladdins_lamp`, `palladium`, `tablet_of_destinies`) are fully authored in JSON but unreachable from code — they cannot spawn. Two of them (palladium, tablet_of_destinies) have effect handlers waiting in source — that code path is dead. The other 22 artifacts in `artifact.json` are uniques without a `mastery_blessing` and fall into a silent-no-op path on chain-5 identify, leaving them stuck in the identify menu forever after "mastery". One armor material (`tungsten`) is class-orphaned. Four accessory names have grammar bugs that prevent the kid-specific class blessings (haste/invisibility/levitation/clairvoyance) from binding.

The audit also confirms the data layer is otherwise extremely clean — 218 JSON files parse, 0 cross-file dup IDs, 0 missing mandatory fields, 0 color-shape errors, 0 monster-ref misses, all 2,025 material×template combos instantiate without crash.
