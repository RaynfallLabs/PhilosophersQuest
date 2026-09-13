# COOKING / HARVEST / FOOD / INGREDIENTS — v2.15.0 Readiness Audit

**Audit date:** 2026-09-12
**Scope:** `src/food_system.py`, `data/items/{food,ingredient,recipes,cook_outcomes,prime_cuts}.json`, `data/monsters.json`, `src/game_menus.py` cook + eat + harvest paths, `src/game_render.py` cook menu UI, `src/main.py` `_cook_item`/`_cook_compound`/`_harvest` callers, `src/player.py` cook-cap system.
**Read-only.** No code changes.

| Severity | Count |
|---|---|
| P0 | 1 |
| P1 | 3 |
| P2 | 1 |
| P3 | 5 |
| P4 | 3 |
| **Total** | **13** |

## Systemic patterns

- **Cook menu is compound-only** (`_COOK_TABS = [('Recipes', 'compound')]`) but `get_available_compound_recipes` still filters out `len(set(ings)) < 2` — the "Single tab is reserved for solo cooks" contract from its docstring is broken now that the Single tab was removed (2026-06-07). Only 77 of 614 recipes are reachable; 537 are silently unreachable. This is the ROOT CAUSE of finding-1, finding-2, and finding-3.
- **Post-2026-05-31 harvest-redesign UI text was not swept.** Docstrings + user-visible strings still describe "escalator-chain quiz", "Assorted Monster Parts" harvest, "quality N" outcome, "Chain outcomes" — none of which are how the system actually behaves after the 2026-09-01 (v2.6.5 harvest) and 2026-09-02 (v2.6.4 cook one-Q) redesigns.
- **Ingredient `temp_power` metadata is dead data.** Every `_prime` and `_trophy` carries a `temp_power`, `stat_grant`, `temp_duration` — but nothing reads them; only `outcome_id`-referenced entries in `cook_outcomes.json` actually fire. This is confusing but not broken; noted for future cleanup.

## Findings

---

### P0-cook-trophy-recipes-unreachable

**dimension:** cooking / progression
**severity:** P0
**title:** All 14 boss trophy recipes are unreachable from the cook menu — Class Ascension can never fire
**systems:** [food_system, cook_menu, class_ascension, boss_rewards]
**status:** open

**Evidence**
- `src/main.py:4669-4671`: `_COOK_TABS = [('Recipes', 'compound')]` — only the compound tab remains after the 2026-06-07 UX change.
- `src/food_system.py:153-172` (`get_available_compound_recipes`): filters `if not ings or len(set(ings)) < 2: continue`. Its own docstring (lines 157-161) still claims solo cooks "are reachable from the Single tab via `_find_recipe_for_ingredient`" — but the Single tab was removed.
- `tests/test_class_ascension.py:82-84`: explicitly locks in `trophy_asterion_minotaur_recipe['ingredients'] == ['asterion_minotaur_trophy']` (one trophy, one ingredient, per v2.6.5 "trophies are precious"). All 14 trophy recipes are `len(ings) == 1` (verified by walking `data/items/recipes.json`).
- Direct simulation: loading Asterion trophy into an inventory and calling `get_available_compound_recipes([asterion_trophy])` returns `[]`. Zero recipes offered.
- `src/food_system.py:344-347`: `class_ascension` signal is emitted only from `_apply_recipe_outcome`, which only runs when a trophy recipe is cooked.

**Impact**
Cooking Asterion (F20), Medusa (F40), Fafnir (F60), and Fenrir (F80) trophies is the SOLE trigger for the Class Ascension picker (`_open_ascension_menu`). Because trophies never appear in the cook menu, the four ascension gates never open. Class progression is broken end-to-end.

The nine boss trophy `permanent_power` outcomes (`chromatic_resist_all`, `one_time_death_save`, `fire_immunity`, `cold_immunity`, `plus_2_con_petrify_immune`, `revive_once_at_half_hp`, `max_mp_per_floor_descent_and_poison_immunity`, `plus_2_wis_auto_reveal_secret_doors`, `all_stats_plus_1` for Abaddon) are all wired in `_apply_permanent_power` (`src/food_system.py:377-438`) but the dispatch never runs.

**Suggested fix**
Drop the `len(set(ings)) < 2` filter in `get_available_compound_recipes`, or add a trophy-specific pass-through. The Recipes tab should list solo-ingredient recipes when the anchor ingredient is a trophy (or a `u_*` utility, or a prime with a defined per-monster recipe).

---

### P1-cook-prime-recipes-unreachable

**dimension:** cooking / content
**severity:** P1
**title:** 457 of 516 monster prime recipes (88.6%) have no reachable cook path
**systems:** [food_system, cook_menu, prime_cuts]
**status:** open

**Evidence**
- `data/items/ingredient.json`: 516 `_prime` ingredients.
- `data/items/recipes.json`: 516 `prime_{monster}_recipe` entries, each with `ingredients: [f"{monster}_prime"]` — a single ingredient.
- Same `len(set(ings)) < 2` filter in `get_available_compound_recipes` (`src/food_system.py:168`) drops every single-ingredient recipe.
- Cross-check: of the 516 primes, only 59 (11.4%) appear in ANY multi-ingredient recipe (family_*_recipe or combo_*_recipe). Confirmed by scanning `recipes.json`.
- Sample unreachable primes: `mimic_prime`, `cave_spider_prime`, `fire_beetle_prime`, `ghoul_prime`, `dire_rat_prime`, `orc_warrior_prime`, `dark_elf_prime`, `basilisk_prime`, `medusa_prime`, `vampire_spawn_prime`, `fire_elemental_prime`, `goblin_prime` (base goblin!).
- Same simulation as P0: inventory of `[goblin_prime]`, or `[goblin_prime × 3]`, or `[goblin_prime, cave_mushroom]` — `get_available_compound_recipes` returns `[]` in each case (goblin_prime has no combo recipe pairing it with any dungeon ingredient).

**Impact**
Player harvests corpses, gets prime cuts, and the vast majority of them have no cook path. The only exits for these primes are (a) eat raw for 10-30 SP, or (b) discard. The per-monster prime recipe SP/HP/temp-power outcomes designed in `cook_outcomes.json` never fire for these 457 monsters. The system feels dead for common early-mid game primes (goblin, kobold, orc_warrior) where the player has plenty of one ingredient but no combo counterpart.

**Suggested fix**
Same as P0 (relax the `< 2` filter). Alternatively, add a data-driven "solo cook" pass or auto-generate combo recipes so every prime has at least one reachable outlet.

---

### P1-quirks-unreachable-cook-callback-missing

**dimension:** progression / quirks
**severity:** P1
**title:** `on_food_eaten` is called only from dead code — Tantalus, Persephone, and Circe quirks can never unlock
**systems:** [quirk_system, cooking]
**status:** open

**Evidence**
- `src/quirk_system.py:662-684`: `on_food_eaten(quality, source_monster, bonus_type, ingredient_id)` gates three quirk unlocks:
  - Tantalus (`#16`): 15 quality-0 ruined meals
  - Persephone (`#34`): quality-5 meals from 5 distinct ingredient sources
  - Circe (`#39`): cooks from each of 5 distinct `bonus_type` categories
- Only caller: `src/main.py:4705` inside `_cook_item.on_complete`. `_cook_item`'s own docstring at `src/main.py:4715-4719` explicitly states it is "unreachable post 2026-06-07 cook overhaul (the SINGLE tab was removed; _COOK_TABS only lists 'compound')."
- `_cook_compound.on_complete` (`src/main.py:4726-4740`) — the ACTUAL callback for the only reachable cook path — never calls `on_food_eaten` on `quirk_system`.
- Additionally, `_cook_item.on_complete` extracts quality via `_re.search(r'quality\s+(\d)', _m)` on the messages list — but the v2.6.4 outcome message strings ("You prepare X.", "You eat it: +N SP, +N HP.", "The meal fortifies you permanently.") never contain the substring "quality N". So even if `_cook_item` were reachable, the callback would always receive `quality=0`.
- `game_menus.py:244` `_eat_menu` calls `eat_food`/`eat_raw` for Food and Ingredient items but does not notify `quirk_system.on_food_eaten` either.

**Impact**
Three quirks (Tantalus, Persephone, Circe) are permanently locked because their unlock gates never fire. Persephone specifically enables the ruined-cook half-recovery behavior gated on `quirk_progress.persephone_active` (`src/food_system.py:252-268`) — that grace mechanic is unreachable.

**Suggested fix**
Add a `quirk_system.on_food_eaten(quality=5 or 0, source_monster=..., bonus_type=..., ingredient_id=...)` call inside `_cook_compound.on_complete`, deriving quality from whether `_ascend` is truthy or the messages contain "ruin"/"wasted". Also decide whether pure `_eat_menu` consumption should notify quirks (currently intent is unclear).

---

### P1-utility-solo-recipes-unreachable

**dimension:** cooking / content
**severity:** P1
**title:** Six utility `u_*` recipes for foraged dungeon ingredients cannot be cooked
**systems:** [food_system, cook_menu, dungeon_ingredients]
**status:** open

**Evidence**
- `data/items/recipes.json` contains 7 `u_*` recipes; 6 have a single ingredient:
  - `u_mushroom_tea` (`[cave_mushroom]`)
  - `u_holy_broth` (`[holy_water]`)
  - `u_incense_tea` (`[altar_incense]`)
  - `u_moss_broth` (`[swamp_moss]`)
  - `u_crystal_tonic` (`[crystal_shard]`)
  - `u_iron_broth` (`[deep_iron]`)
  - `u_kelp_broth` (`[abyssal_kelp]`)
  - Only `u_salted_kelp` (`[abyssal_kelp, river_salt]`) survives the `≥2 unique types` filter.
- Same `get_available_compound_recipes` filter drops these.
- Dungeon ingredients spawn as floor loot via `src/dungeon.py:1509-1518` (only `tier_role == 'dungeon'` items are eligible), so players do pick them up.
- `_find_recipe_for_ingredient` (`src/food_system.py:560-593`) has branches for `_trophy`, `_prime`, `family_`, and `assorted_monster_parts` — but NO branch for dungeon ingredients. So the dead Single-tab path wouldn't have worked for them either.

**Impact**
Every solo cook of a dungeon foragable is impossible. Their single-ingredient outcomes (mushroom tea = `t1_snack_perception`, holy broth = `t2_meal_dark_grace`, etc.) never fire. If the player holds only, say, `cave_mushroom`, the cook menu opens with "You have no recipes you can make yet".

**Suggested fix**
Same root cause as P0/P1-primes. As a secondary fix, `_find_recipe_for_ingredient` needs a dungeon-tier branch (e.g. look up `u_{ingredient_id}_...` or a canonical field).

---

### P2-find-recipe-missing-dungeon-branch

**dimension:** cooking / code
**severity:** P2
**title:** `_find_recipe_for_ingredient` has no lookup path for `tier_role == 'dungeon'` ingredients
**systems:** [food_system]
**status:** open

**Evidence**
- `src/food_system.py:560-593`: the resolver's branch order is: (1) `_trophy` → `trophy_{monster}_recipe`, (2) `_prime` → `prime_{monster}_recipe`, (3) `family_` → `{iid}_recipe` (no `family_*` ingredients exist anymore, so branch is dead), (4) `assorted_monster_parts` → `basic_monster_stew` (both are deleted, dead branch). Nothing matches `cave_mushroom`, `holy_water`, `crystal_shard`, `river_salt`, `swamp_moss`, `deep_iron`, `altar_incense`, `abyssal_kelp`.
- Returns `None` → `cook_ingredient` short-circuits with "You don't know what to do with the X."
- Currently harmless because `cook_ingredient`'s only caller (`_cook_item`) is itself unreachable dead code. But if the Single tab is ever restored (which is one plausible fix for P0/P1), this resolver leaves dungeon ingredients broken.

**Suggested fix**
Add a `tier_role == 'dungeon'` branch that scans `_raw_recipes()` for the canonical `u_{name}_*` recipe, or key it via a data field on the ingredient. Prune the dead `family_` and `assorted_monster_parts` branches at the same time.

---

### P3-cook-menu-stale-context-line

**dimension:** UI / cooking
**severity:** P3
**title:** Cook menu context line still says "escalator-chain quiz" — cook is now one-question threshold
**systems:** [game_render, cook_menu]
**status:** open

**Evidence**
- `src/game_render.py:4479-4480`:
  ```
  ("Cooking uses an escalator-chain quiz. Higher chains improve the meal.",
   FP.FADED_TEXT, self.font_sm),
  ```
  This line is drawn inside the Cook menu context box (visible to the player).
- Actual cook engine (`food_system.cook_compound_recipe` and `cook_ingredient`, `src/food_system.py:459-492` / `596-630`) uses `mode='threshold', threshold=1, total_qs=1`. Per `PLAYABILITY_PASS_AUDIT.md:56`, this was swapped from `escalator_chain` in the v3 overhaul.

**Suggested fix**
Replace with the wording already used in the recipe detail lines (`src/game_render.py:2828`): "Answer one cooking question. Right = full recipe; wrong = ruined dish."

---

### P3-recipe-detail-chain-outcomes-label

**dimension:** UI / cooking
**severity:** P3
**title:** Recipe detail panel labels the outcome section "Chain outcomes" — outcomes are no longer chain-scaled
**systems:** [game_render, cook_menu]
**status:** open

**Evidence**
- `src/game_render.py:2825`: `lines += [("Chain outcomes", FP.GOLD_BRIGHT, self.font_sm), (preview, FP.SUCCESS_TEXT, self.font_sm)]`.
- Post-v2.6.4 recipes reference a single `outcome_id` archetype (`data/items/cook_outcomes.json`), not `tier_outcomes` per-chain-rung. `_menu_recipe_preview` at the same site (lines 2751-2802) already renders `"T{tier}: {bits}"` — a single outcome, not a chain.

**Suggested fix**
Rename label to "Outcome" or "This meal grants". Same file also has a legacy `tier_outcomes` fallback (2782-2801) that renders "T1: ... | T2: ..." — that legacy path can stay for old saves but should not drive the current in-repo cookbook.

---

### P3-legacy-ingredient-migration-log-lies

**dimension:** logs / migration
**severity:** P3
**title:** Legacy-ingredient migration print says "Translated N legacy ingredients to Assorted Monster Parts" but the code drops them
**systems:** [save_migration]
**status:** open

**Evidence**
- `src/main.py:1154`: `print(f'[Migration] Translated {total} legacy ingredients to Assorted Monster Parts')`
- Actual behavior per `src/main.py:1128-1143` (`_migrate_list`): "v2.6.5: assorted_monster_parts + family_* were deleted. Old saves carrying those Ingredients have nothing to swap to (no equivalent survives). Drop them from the list; reconcile the rest." The code does `items_list.pop(i)` — no translation.
- Companion stale comment at `src/main.py:548-552` says the migration will "Replace them with assorted_monster_parts so the inventory stays usable" — inconsistent with the delete-only behavior.

**Suggested fix**
Change log to `f'[Migration] Dropped {total} legacy ingredients from inventory (no v2.6.5 equivalent).'` and update the block comment at 548-552.

---

### P3-harvest-comment-still-claims-assorted-monster-parts

**dimension:** docstrings / harvest
**severity:** P3
**title:** Harvest code comments still describe the old "every corpse yields Assorted Monster Parts at T1+" outcome
**systems:** [main, food_system, dev-docs]
**status:** open

**Evidence**
- `src/main.py:4620-4621`: `# Per 2026-05-31 redesign: EVERY corpse yields Assorted Monster Parts / # at T1+, regardless of monster_id. No pre-skip.` — but the current v2.6.5 (2026-09-03) `_harvest_outcome_for_tier` returns exactly one prime cut or one trophy, and never yields `assorted_monster_parts` (which no longer exists).
- `src/food_system.py:34-46`: the module-header outcome-shape comment still lists "T1: 1x Assorted Monster Parts (universal); T2: 2x Assorted Monster Parts; T3: +1x family ingredient (12 families); T4: +1 more family ..." — all invalidated by the v2.6.5 harvest rewrite (which the actual function docstring at 58-67 correctly documents).

**Suggested fix**
Sync the comment text with the actual v2.6.5 behavior (`_harvest_outcome_for_tier` returns `[f"{monster}_prime"]` or `[f"{monster}_trophy"]`; tier only affects the quiz difficulty).

---

### P3-find-recipe-dead-branches-basic-monster-stew

**dimension:** dead code
**severity:** P3
**title:** `_find_recipe_for_ingredient` still has `assorted_monster_parts` → `basic_monster_stew` and `family_*` branches after both were deleted
**systems:** [food_system]
**status:** open

**Evidence**
- `src/food_system.py:585-592`:
  ```
  # Family ingredient: recipe id is `family_{fam}_recipe`
  if iid.startswith('family_'):
      rid = f'{iid}_recipe'
      if rid in recipes:
          return {'id': rid, **recipes[rid]}
  # Universal: basic_monster_stew
  if iid == 'assorted_monster_parts':
      if 'basic_monster_stew' in recipes:
          return {'id': 'basic_monster_stew', **recipes['basic_monster_stew']}
  ```
- Neither `family_*` ingredients nor `assorted_monster_parts` exist in `ingredient.json`. Neither `basic_monster_stew` nor any `family_*_recipe` on a `family_*` iid exists. Both branches are permanent no-ops.

**Suggested fix**
Prune the branches. Add a `dungeon`-tier branch instead (see P2). This keeps the resolver focused on the tiers that actually exist.

---

### P4-abyssal-locust-heavenly-angel-inconsistent-harvest-fields

**dimension:** data quality
**severity:** P4
**title:** `abyssal_locust` and `heavenly_angel` have `harvest_tier=0` + `ingredient_id=null` in monsters.json but valid prime_cuts entries
**systems:** [data_monsters, food_system, prime_cuts]
**status:** open

**Evidence**
- `data/monsters.json` for both: `harvest_tier: 0`, `harvest_threshold: 99`, `ingredient_id: null`.
- `data/items/prime_cuts.json` defines both: `abyssal_locust_prime` (Abyssal Locust Pure Ichor, fire_resist) and `heavenly_angel_prime` (Heavenly Angel Radiant Mote, blessed_status).
- `food_system.harvest_corpse` (`src/food_system.py:521-523`) reads `ht = int(getattr(corpse, 'harvest_tier', 1) or 0)` then `tier = max(1, min(5, ht)) if ht > 0 else 1` — so `ht=0` falls back to `tier=1` (not skipped). On success it calls `_harvest_outcome_for_tier(1, monster_id)` which reads `prime_cuts.json` and returns `[abyssal_locust_prime]` / `[heavenly_angel_prime]` regardless of the `harvest_tier=0` intent.
- No corpse-suppression flag (`leaves_corpse=False` is not set anywhere in `monsters.json`). Corpses always drop for any monster (`game_combat._make_corpse` fires unconditionally on death).

**Impact**
The "unharvestable" intent recorded in monsters.json is silently ignored — both monsters can be harvested for their primes. Abaddon's floor-100 locust spawn (3-5 per turn) becomes a stream of harvestable ichor. Minor at this scale, but the data contradicts itself.

**Suggested fix**
Either wire a `leaves_corpse=False` path (skip `_make_corpse` for these two) and drop them from prime_cuts.json, or grant them full harvest_tier + valid `ingredient_id` and let them harvest normally. Pick one story.

---

### P4-claude-agents-quiz-modes-table-stale

**dimension:** docs
**severity:** P4
**title:** `CLAUDE.md`/`AGENTS.md` Quiz Modes example still lists cooking as `escalator_chain`
**systems:** [docs]
**status:** open

**Evidence**
- `CLAUDE.md:10` (and `AGENTS.md:10`): `**escalator_chain** — Questions get harder each round; chain until failure (e.g., cooking)`. Cooking has been threshold-1Q since v2.6.4 (2026-09-02).
- Same for `docs/quiz/subjects/cooking.md:5,11,28`, `docs/quiz/cooking_strategies.md:47`, `docs/quiz/subjects/animal.md:5,13`, `docs/quiz/animal_strategies.md:44` — all describe old chain/escalator_chain modes and 42s/34s timer notes tuned for those old modes.

**Impact**
Docs-only, doesn't affect players. But bank-authoring subagents reading these files will mis-anchor cooking/animal question length + shape to the pre-v3 chain-mode budget.

**Suggested fix**
Choose one: revise the docs to match the current threshold-1Q reality, or add a "post-2026-09 note" callout to each subject file pointing at `PLAYABILITY_PASS_AUDIT.md`. The subject-facing quiz mode has changed but the char-budget targets probably still hold — worth an explicit call.

---

### P4-mystery-cooking-challenge-still-escalator-chain

**dimension:** design consistency
**severity:** P4
**title:** Mystery-event cooking challenge is still `escalator_chain` while normal cooking is `threshold`
**systems:** [mystery_system]
**status:** open

**Evidence**
- `src/mystery_system.py:181`: `'challenge': {'mode': 'escalator_chain', 'subject': 'cooking', 'tier': 2, 'threshold': 5, 'max_chain': None}`.
- Per `PLAYABILITY_PASS_AUDIT.md:165`, mystery-event challenges were INTENTIONALLY left on the old escalator_chain contract because they are low-frequency "chain is the point" events. Recording as P4 for design-consistency reference only.

**Impact / Suggested fix**
None required — flagged so future audits recognize this as intentional divergence, not a leftover-rot slip.

---

## Data-integrity checks that PASSED (no findings)

- **All 525 harvestable monsters have `harvest_tier`, `harvest_threshold`, and `ingredient_id` fields** (only 2 monsters explicitly marked unharvestable, both with the P4 inconsistency above).
- **All 527 monsters have a matching entry in `prime_cuts.json`.**
- **Every `prime_cuts.json` entry's derived ingredient id exists in `ingredient.json`** (516 primes + 14 trophies, no orphans).
- **Every recipe's ingredients exist in `ingredient.json`** (614/614 clean).
- **Every recipe's `outcome_id` exists in `cook_outcomes.json`** (614/614 clean).
- **Every `_prime` ingredient has a `prime_{monster}_recipe`** (reachability is the P1 issue above; the recipes themselves exist).
- **Every `_trophy` ingredient has a `trophy_{monster}_recipe`** (same — data present, reachability broken).
- **Every `temp_power` referenced in `cook_outcomes.json`, `prime_cuts.json`, `ingredient.json` resolves via `EFFECT_INFO` or the `_TEMP_POWER_REMAP` table** (0 unresolved).
- **All 32 `cook_outcomes` entries with a positive `stat_grant` carry a `stat_grant_default`.**
- **`cook_outcomes` SP/HP tier bands are healthy**: T1 avg SP 58.7 (range 55-70), T5 avg SP 151.9 (range 140-165), no outliers. Max `max_hp_bonus` = 4 (Abaddon trophy). Trophy `permanent_power` matches the 13-key dispatcher in `_apply_permanent_power`.
- **Food items SP/HP are all sane**: T1 (ml 1) SP 38-70 HP 0-8, endgame (ml 40-60) SP 95-115 HP 30-80. Ambrosia (ml 40, all_stats +1) is the top item — consistent with legendary tier.
- **Raw prime SP scales cleanly with monster tier** (10 → 30 across 516 primes; distribution: 10:310, 15:70, 20:63, 25:44, 30:29). Matches the "raw prime 10-30 SP emergency" spec in memory.
- **Cook per-floor caps + floor-scaling softcaps are correctly wired** (`Player.try_apply_cook_stat_gain` / `try_apply_cook_hp_gain`, `_COOKING_SOFTCAP_BY_FLOOR`, `_COOKING_STAT_SOFTCAP_BY_FLOOR`). F100 HP cap = 139 (well below the old 1000). F100 per-stat cap = +15.
- **All four class-ascension trophies (Asterion/Medusa/Fafnir/Fenrir) carry `class_ascension: true` on their outcome; Abaddon does not.** Verified by test_class_ascension.py invariants. (The bug is reachability, not the data.)
