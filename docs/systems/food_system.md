# Food System — Cook v2 + Harvest v4

**Status:** Live in v2.18. Harvest v4 shipped v2.6.5 (2026-09-03). Cook v2 shipped v2.6.4 (2026-09-02). Quirk-hook wiring + prime_cuts.json dead-field sweep landed in v2.18 (commit `409e15d`).

**Owner:** Brandon (RaynfallLabs).

**Supersedes:** Harvest v3 (chain-mode, up-to-5 escalating Qs, cumulative T1–T5 ingredient stack), Cook v2.6.3 (potency formulas `SINGLE_MULT`/`COMPOUND_MULT`), the Single-ingredient cook tab (removed 2026-06-07), the retired `_apply_tier_outcome` dispatcher, and the pre-v2.6.4 `recipe_class` → tier map.

---

## 1. Core design rules

Three memory rules govern every decision in this system — rebalance against them, not against each other:

- **Flow over gradient.** Harvest and cook are high-frequency quiz-gated actions, so they get **one** question with a binary outcome. Escalator chains sound rewarding on paper, but in practice they ruin the moment-to-moment game pace. See `feedback_flow_over_gradient.md`.
- **Resource loss IS the penalty.** The corpse (harvest) or the ingredient stack (cook) is consumed on the attempt, whether or not the quiz succeeds. There is **no** stun/debuff on failure; losing the resource is the whole cost. See `feedback_resource_loss_is_the_penalty.md`.
- **SP soft boundary via generous supply.** Starvation damage still exists as a failsafe (SP=0 still hurts), but normal play never bottoms the tank because cook SP is high and food is dense. SP is a currency the game trusts the player to spend; it is not a punisher. See `feedback_sp_soft_boundary.md`.

---

## 2. Code map

| File | Role |
|------|------|
| `src/food_system.py` | Harvest, cook, outcome application. Pure module — no pygame, no Game state. |
| `src/main.py::Game._harvest` (L4670) | Harvest call site. Pops corpse, kicks the quiz, routes the ingredient list back to inventory. |
| `src/main.py::Game._cook_compound` (L4788) | Compound-recipe cook call site. Pops the recipe's ingredients and routes the outcome back to messages + the quirk hook. |
| `src/main.py::Game._cook_item` (L4735) | **Dead path.** Single-tab cook; unreachable since 2026-06-07. Pinned by legacy tests. |
| `src/main.py::_outcome_bonus_category` (L98) | Coarse `permanent / stat / temp_power / max_hp / recovery` label for Circe's quirk unlock. |
| `src/items.py::Corpse` (L1027) | The `%` ground item. Carries `monster_id`, `harvest_tier`, `harvest_threshold`, `monster_def`, `id_level`, `id_tier`. |
| `src/items.py::Ingredient` (L1001) | The `~` inventory item. Carries `source_monster`, `tier_role`, `family`, plus the raw-eating fields `edible_safe` + `raw_sp`. |
| `src/items.py::Food` (L1115) | Ready-to-eat ration. Carries `sp_restore`, `hp_restore`, `bonus_type`, `bonus_stat`, `bonus_effect`, `bonus_amount`. |
| `src/player.py::try_apply_cook_hp_gain` (L549) | Per-floor max-HP cap + lifetime softcap for cooked HP gains. |
| `src/player.py::try_apply_cook_stat_gain` (L527) | Per-floor stat cap + per-stat lifetime softcap for cooked stat gains. |
| `src/player.py::apply_cooking_stat_bonus` (L585) | Diminishing-return + hard-cap stat delivery. |
| `src/player.py::increase_max_hp` (L610) | Diminishing-return max-HP delivery, floored at +1. |
| `src/player.py::reset_floor_cook_caps` (L579) | Called from `Game._change_level`. Resets the per-floor counters. |
| `src/quirk_system.py::on_food_eaten` (L707) | Tantalus / Persephone / Circe + Siegfried routing. |

Data files (all under `data/items/`):

| File | Rows | Role |
|------|-----:|------|
| `ingredient.json` | 538 | Raw ingredient catalog. 516 primes (`<monster_id>_prime`), 14 trophies (`<monster_id>_trophy`), plus universal / family / dungeon-foraged entries. |
| `prime_cuts.json` | 527 | Harvest lookup table. `monster_id → {ingredient_id, is_trophy, family, ingredient_name}`. |
| `recipes.json` | 614 | Recipe catalog. Each row carries `name`, `ingredients: [str]`, `outcome_id`, `flavor`. |
| `cook_outcomes.json` | 120 | Outcome archetype catalog. Many recipes → one archetype. |
| `food.json` | 17 | Ready-to-eat rations (bread, cheese, fruit, jerky…). |

There is **no** `corpse.json`. Corpses are built at harvest-spawn time via `food_system.make_corpse` reading `data/monsters.json`.

### 2.1 `Corpse` fields

Set at creation (`make_corpse` in `food_system.py:1043`):

| Field | Source | Role |
|-------|--------|------|
| `monster_id` | passed in | Key into `prime_cuts.json` + `monsters.json`. Load-bearing for harvest + identify. |
| `monster_name` | `monsters[id].name` | Display only. |
| `harvest_tier` | `monsters[id].harvest_tier` (1–5) | Harvest quiz difficulty. |
| `harvest_threshold` | `monsters[id].harvest_threshold` | **Dead field** — v4 uses threshold=1 unconditionally. |
| `ingredient_id` | `monsters[id].ingredient_id` | **Dead field** — v4 derives the ingredient from `monster_id` via `prime_cuts.json`. Kept for save-compat. |
| `monster_def` | `{peak_floor, id_tier, tags}` | Feeds the identify path + the quirk hook's `attacks` lookup. |
| `id_level` | 0 (unstudied), 5 (fully identified) | Written only by the identify system; `>=4` sets the `lore_identified` back-compat property. |
| `id_tier` | derived | explicit `id_tier` kwarg > monster `id_tier` > `_floor_band_tier(peak_floor)` > `harvest_tier` > 1. Identify quiz difficulty. |

### 2.2 `Ingredient` fields

Loaded from `data/items/ingredient.json` by `food_system.load_ingredient_for`:

| Field | Role |
|-------|------|
| `source_monster` | Monster id this ingredient came from — fed to `on_food_eaten` for the Siegfried quirk. |
| `tier_role` | `universal` / `family` / `prime` / `trophy` / `dungeon`. Spawn gate (only `dungeon` can appear as floor/chest loot) + raw-SP map default. |
| `family` | One of the 12 monster families (see §3.6). Used by family-ingredient recipes. |
| `recipes` | Legacy quality 0–5 recipe inline map. Unread by v2 cook; survives for save-compat. |
| `floor_spawn_weight` | Band → weight map for dungeon-foraged ingredients. |
| `edible_safe` | True → raw-eating never rolls food-poison (jerky + cured foods). |
| `raw_sp` | Int override for raw-eat SP. Falls back to `tier_role` map. |
| `mp_restore` | MP delta on raw-eat for mana-ingredients (rare). |
| `identified`, `unidentified_name` | Raw ingredients are always identified; the fields exist for Item-base compat. |

### 2.3 `Food` fields

Loaded from `data/items/food.json`:

| Field | Role |
|-------|------|
| `sp_restore` | 20–115 across the 17 rations. |
| `hp_restore` | 0 or a small int for the healing foods. |
| `bonus_type` | `none` / `random_stat` / `combat_stat` / `two_stats` / `all_stats` / `stat` / `status`. Drives `_apply_bonus`. |
| `bonus_stat` | Specific stat for `bonus_type='stat'`. |
| `bonus_effect` | Status-effect id for `bonus_type='status'`. |
| `bonus_amount` | Stat points / status turns, depending on `bonus_type`. |
| `floor_spawn_weight` | Band → weight for dungeon spawning. |

---

## 3. Harvest v4 — one animal question

### 3.1 Entry point

The player stands on a corpse (`%`) and presses the harvest key. `Game._harvest` (`src/main.py:4670`) looks up the corpse at the player's tile, removes it from `ground_items` **before** the quiz fires (resource-loss rule), and calls `food_system.harvest_corpse(player, corpse, quiz_engine, on_complete, extra_seconds)`.

A +5s timer bonus is applied if `corpse.monster_id ∈ player.lore_known_monster_ids` — identified corpses are easier to butcher.

### 3.2 Quiz shape

```python
quiz_engine.start_quiz(
    mode='threshold',
    subject='animal',
    tier=max(1, min(5, corpse.harvest_tier)),
    threshold=1,
    total_qs=1,
    wisdom=player.WIS,
    timer_modifier=player.get_quiz_timer_modifier(),
    extra_seconds=player.get_quiz_extra_seconds('animal') + lore_bonus,
    base_seconds=player.get_quiz_timer('animal'),
)
```

`SUBJECT_TIMER['animal'] = (34, 1.6)` — flat 34s base at WIS 10, with the WIS modifier applied by the engine.

### 3.3 Outcome resolution

| Result | Yield |
|--------|-------|
| Right | `_harvest_outcome_for_tier(tier, monster_id)` → `[f'{monster_id}_prime']` **or** `[f'{monster_id}_trophy']` (bosses) |
| Wrong | `[]` — "You botch the harvest. The <name> is ruined." |

Tier is used **only** for the quiz difficulty. Every corpse yields its own identifying prime cut (one ingredient, named for the monster), regardless of tier. Bosses are the exception: their prime_cuts.json row carries `is_trophy: true` and the yield is the themed trophy ingredient (`<monster_id>_trophy`) instead.

This is a load-bearing change from v3: the pre-2026-09-03 harvest returned a cumulative T1–T5 stack of `assorted_monster_parts` + family + prime, which meant ~87% of monsters never dropped their own prime (only T5-capable corpses ever reached the prime slot). V4 collapses the stack to a single themed drop so **every** monster delivers its own identifying piece.

### 3.4 Defensive edges

- If `monster_id` is missing from `prime_cuts.json` the yield list is empty — the harvest reports "yields nothing usable" without raising.
- If the ingredient id resolves but `load_ingredient_for` returns `None` (missing `ingredient.json` row), it is silently dropped from the list.
- Overflow goes to the ground: `Game._harvest.on_complete` loops and, for any ingredient that fails `player.add_to_inventory`, drops it on the harvest tile with a `"Too heavy -- X dropped."` warning.

### 3.5 Quirk hook

`quirk_system.on_harvest(monster_kind=corpse.monster_id, success=success, monster_applies_poisoned=...)` fires on every attempt. Mithridates (ate 5 species that poisoned you) is the main consumer. `monster_applies_poisoned` is derived from `corpse.monster_def['attacks']` — any attack with `effect: 'poisoned'` flips the flag.

### 3.6 Family distribution (527 primes + trophies)

The 12 families in `prime_cuts.json`:

| Family | Count | Notes |
|--------|------:|-------|
| undead | 117 | Largest group — skeletons, ghosts, wights, vampires. |
| beast | 108 | Natural fauna, worms, dire variants. |
| humanoid | 104 | Goblinoids, giants, bandits, boss humanoids. |
| demon | 60 | Lower planes. |
| aberration | 43 | Mind-bending outsiders. |
| fey | 22 | Satyr, dryad, pixie, redcap. |
| construct | 20 | Golems, animated objects, war-machines. |
| elemental | 19 | Fire / earth / air / water / para-elementals. |
| dragon | 14 | Chromatic + metallic + the four trophied unique dragons. |
| plant | 9 | Shriekers, treants, carnivorous flora. |
| reptile | 8 | Lizardfolk, basilisks, non-dragon serpents. |
| celestial | 3 | Angelic — Abaddon's family. |

The family drives recipe choice at the `_find_recipe_for_ingredient` family-tier fallback — not every family currently has a dedicated `family_<name>_recipe` row, which is why only 77/614 recipes are true compound (multi-type) recipes.

---

## 4. Cook v2 — one cooking question

### 4.1 Entry point

The player opens the cook menu (`C` → Recipes tab). `_COOK_TABS = [('Recipes', 'compound')]` — the old Single tab was deleted 2026-06-07 along with `basic_monster_stew`, because every surviving recipe needs ≥2 ingredient types.

`get_available_compound_recipes(inventory)` filters `recipes.json` to rows where (a) the player has every listed ingredient id and (b) `len(set(ingredients)) >= 2`. Solo cooks (one ingredient id repeated) are excluded — they are reachable in principle from the dead Single tab via `_find_recipe_for_ingredient`.

### 4.2 Flow

`Game._cook_compound(recipe)`:

1. Looks up `recipe['outcome_id']` in `cook_outcomes.json` and snapshots `outcome.tier` + an anchor-ingredient `source_monster` string for the quirk hook (the raw recipe JSON doesn't carry `source_monster`, only the live `Ingredient` instances do).
2. Calls `food_system.cook_compound_recipe(player, recipe, player.inventory, quiz_engine, on_complete)`.
3. That helper pops the ingredients up-front (one `remove_from_inventory` per listing — a recipe with duplicate ids in its list consumes that many copies), then starts the cooking quiz.
4. The outcome is applied by `_apply_recipe_outcome` (either peak or ruined branch) and the resulting message list is handed back to `on_complete`.

### 4.3 Quiz shape

```python
quiz_engine.start_quiz(
    mode='threshold',
    subject='cooking',
    tier=_recipe_quiz_tier(recipe),   # outcome.tier, clamped 1..5
    threshold=1,
    total_qs=1,
    wisdom=player.WIS,
    timer_modifier=player.get_quiz_timer_modifier(),
    extra_seconds=player.get_quiz_extra_seconds('cooking'),
    base_seconds=player.get_quiz_timer('cooking'),
)
```

`SUBJECT_TIMER['cooking'] = (44, 1.6)` — flat 44s base at WIS 10, because cooking stems carry full-sentence choices and recipe context.

### 4.4 Right vs wrong

| Result | Branch |
|--------|--------|
| Right | `_apply_recipe_outcome(player, recipe, ruined=False)` → the full peak reward for the recipe's `outcome_id`. |
| Wrong | `_apply_recipe_outcome(player, recipe, ruined=True)` → one `"You ruin the preparation. The <name> is wasted."` message. Ingredients are already gone. |

Resource loss is the whole penalty. No stun, no debuff, no partial credit.

### 4.5 Persephone override (ruined branch)

If `player.quirk_progress.get('persephone_active')` is set, the ruined branch instead delivers **half** of the archetype's `sp` + `hp` ("the seed still returns from the dark"). Buffs, `max_hp_bonus`, `stat_grant`, and `permanent_power` are **not** salvaged — only recovery is. See §12.

---

## 5. The recipe → outcome resolution chain

```
recipes.json[rid].outcome_id  ->  cook_outcomes.json.outcomes[outcome_id]
                                       │
                                       └─ _apply_outcome_body(player, recipe, outcome)
```

- 614 recipes reference 59 distinct outcome archetypes (120 archetypes exist in total; 61 are currently unused, parked as design headroom).
- Zero orphan recipes — the SYSTEMS_AUDIT confirms every `outcome_id` resolves.
- Many-to-one is the whole point of the design: `rat_kidney_sauteed_mushroom` and `kobold_kidney_sauteed_mushroom` both route to `t1_snack_perception`, so a shared archetype rebalance moves both at once.

`_recipe_quiz_tier(recipe)` reads `outcome.tier` and clamps to 1..5. A legacy fallback handles the pre-v2.6.4 `recipe_class` field (`family→2, prime→3, master_prime→4, trophy→5, dungeon_keyed→5`). All 614 current recipes carry `outcome_id`, so the legacy branch is cold code kept for save-compat and offline-generator safety.

### 5.1 Recipe inventory

Of 614 recipes:

- **537 solo recipes** (single ingredient type, possibly repeated). Reachable only via the dead Single tab + `_find_recipe_for_ingredient`.
- **77 compound recipes** (≥2 distinct ingredient ids). The Recipes tab shows the subset the player has the ingredients for.
- **14 trophy recipes** (`trophy_<boss>_recipe`) — nested inside the solo count; each takes exactly the `<boss>_trophy` ingredient and references a `trophy_<boss>` outcome.
- **~12 family recipes** (`family_<name>_recipe`) — nested inside the solo count; take any ingredient with `family: <name>`.

### 5.2 `_find_recipe_for_ingredient` priority order

Used only by the dead Single-tab path. Priority: **trophy → prime → family → universal**.

```
iid = ingredient.id
if iid.endswith('_trophy'):     return recipes[f'trophy_{monster}_recipe']
if iid.endswith('_prime'):      return recipes[f'prime_{monster}_recipe']
if iid.startswith('family_'):   return recipes[f'{iid}_recipe']
if iid == 'assorted_monster_parts': return recipes['basic_monster_stew']  # deleted 2026-06-07
return None
```

The `basic_monster_stew` branch is a tombstone — the recipe row and the `assorted_monster_parts` ingredient id were both deleted in the 2026-06-07 cooking overhaul. The branch stays as a comment anchor for save-compat.

---

## 6. `cook_outcomes.json` schema

Each outcome under `outcomes.<id>` has:

| Field | Type | Role |
|-------|-----:|------|
| `tier` | int 1–5 | Quiz difficulty + archetype band. |
| `sp` | int | SP restored on success. 0 means no SP leg. |
| `hp` | int | HP restored on success. (The JSON stores an int; the schema allows dice but no live archetype uses one.) |
| `max_hp_bonus` | int, optional | Permanent +max HP from this cook. Routed through `try_apply_cook_hp_gain`. |
| `stat_grant` | int, optional | Permanent +stat amount. Routed through `try_apply_cook_stat_gain` with `stat_grant_default`. |
| `stat_grant_default` | str, optional | Which stat gets the bump (`'STR'`, `'DEX'`, …). Default `'STR'` when `stat_grant` is set but no stat named. |
| `temp_power` | str, optional | Status effect name (post-remap it is a key in `status_effects.EFFECT_INFO`). |
| `temp_amount` | int, optional | For `save_guard_*` wards, the magnitude written to `player._save_guard[cat]` (clamped at 3). |
| `temp_duration` | int, optional | Turns the status effect lasts. Default 60 when `temp_power` is set but no duration named. |
| `permanent_power` | str, optional | Key into `_apply_permanent_power` dispatcher. Trophies only (14 of them). |
| `permanent_desc` | str, optional | Flavor appended after the mechanical message. |
| `desc` | str, optional | Author-visible blurb. Not read at runtime. |

### 6.1 Tier bands (from the file's `_meta.tier_bands` + verified from the data)

| Tier | SP band (avg) | HP band | Buff turns | Softcap bumps |
|------|---------------|---------|------------|----------------|
| T1 | **55–70** (avg 58.7, n=15) | 2–6 | 30t | rare `max_hp_bonus: 1` |
| T2 | 75–100 (avg 81.9, n=26) | 4–10 | 60t | occasional `max_hp_bonus: 1` |
| T3 | 100–120 (avg 106.5, n=30) | 4–15 | 80t | regular `max_hp_bonus: 1–2` |
| T4 | 120–135 (avg 127.0, n=23) | 12–20 | 100t | `max_hp_bonus: 2`, occasional `stat_grant: 1` |
| T5 non-trophy | 140–165 (avg 151.9, n=26) | 18–25 | 120t | `max_hp_bonus: 3` + `stat_grant: 1` |
| T5 trophy | per-boss | per-boss | per-boss | per-boss + `permanent_power` |

### 6.2 Archetype "shape" taxonomy

The audit docstring lists four archetype shapes — this is a conceptual grouping of outcome rows by field pattern, not an enumerated field in the JSON:

| Shape | Field pattern | Example |
|-------|---------------|---------|
| **success** | `sp` + `hp` + optional buff/`max_hp_bonus`/`stat_grant` | `t3_meal_perception`, `t5_light_apex` |
| **salvage** | Half-strength success delivered via the Persephone ruin override | (no dedicated row; shaped by `_apply_recipe_outcome(ruined=True)`) |
| **ruined** | No row — the ruin path short-circuits before the outcome body is applied | (produces the "wasted" message) |
| **legacy** | T5 trophy with `permanent_power` + `permanent_desc` | `trophy_asterion`, `trophy_medusa`, `trophy_fafnir`, … |

The 6 `_comment_t1`..`_comment_t5trophy` keys at `outcomes.<_comment_*>` are author-only annotations. `_load_outcomes()` returns the dict as-is; if a recipe were ever authored with `outcome_id: "_comment_t1"` the resulting `outcome` dict would be a plain string and `_apply_outcome_body` would AttributeError. SYSTEMS_AUDIT flags this as P5 cleanup — not live-reachable, but a trip-wire. See §13.

---

## 7. Outcome application — `_apply_outcome_body`

Order of operations when `_apply_recipe_outcome` dispatches on a successful cook:

1. **SP + HP recovery.** `restore_sp(outcome.sp)`, `restore_hp(outcome.hp)`. One message line: `"You eat it: +X SP, +Y HP."`
2. **Permanent +max HP.** `try_apply_cook_hp_gain(max_hp_bonus, bypass=bool(permanent_power))`. Trophies bypass the per-floor cap. If the cap is used up, the message changes to `"You feel sated, but your body is already full of nourishment this floor."` (non-trophy only).
3. **Permanent +stat.** `try_apply_cook_stat_gain(stat_grant_default or 'STR', stat_grant, bypass=bool(permanent_power))`. Same per-floor cap logic. On success: `"Your <stat> increases by N!"`
4. **Temp power.** `_resolve_temp_power(temp_power)` normalises the name (see §9), then `player.add_effect(canonical, temp_duration or 60)`. For `save_guard_*` the magnitude from `temp_amount` (clamped to 3) is written to `player._save_guard[cat]` so `Player.save_bonus_for` can pick it up. One message line: `"A short <effect> lingers."`
5. **Permanent power.** For trophies, `_apply_permanent_power(player, outcome.permanent_power, fake_recipe)` runs — see §10. Returns a flavor message that is appended to the output.

Steps 2–5 are each `if present` — a plain T1 recovery outcome stops after step 1 and returns `["You prepare X.", "You eat it: +Y SP, +Z HP."]`.

### 7.1 Per-floor cook caps

Non-trophy cooks compete for two per-floor budgets, both reset by `Game._change_level` via `player.reset_floor_cook_caps()`:

| Budget | Cap | Field | Behaviour at cap |
|--------|----:|-------|------------------|
| Max HP from cooking this floor | **+5** | `_cook_hp_gain_this_floor` | Further `max_hp_bonus` cooks on this floor deliver 0 (message: "already full of nourishment"). |
| Stat points from cooking this floor | **+1** | `_cook_stat_gain_this_floor` | Further `stat_grant` cooks on this floor are silent. |

Trophy outcomes bypass both. The lifetime diminishing softcap in `increase_max_hp(from_cooking=True)` and the per-stat softcap in `apply_cooking_stat_bonus` still apply either way — the floor cap is additive atop the lifetime one, not a replacement.

---

## 8. SP soft-boundary (verified in SYSTEMS_AUDIT)

The audit confirms the memory numbers are live-correct:

| Source | SP range |
|--------|---------|
| **Cooked outcomes T1** | 55–70 (avg **58.7**) |
| **Cooked outcomes T5 non-trophy** | 140–165 (avg **151.9**) |
| **Food rations** (`data/items/food.json`) | 20–115 SP |
| **Raw prime cut** (`eat_raw`, `tier_role: 'prime'`) | 15 SP (defaults; `ingredient.raw_sp` can override, usually 10–30) |
| **Trophy raw** (`tier_role: 'trophy'`) | 20 SP |
| **Universal (Assorted Monster Jerky)** | 12 SP, **no food-poison roll** (see §11.2) |

The soft boundary is softness-by-supply: cook SP alone pulls the player off the starvation floor each session, and raw jerky is a free emergency because it never hits the 30% food-poison roll. **Starvation damage at SP=0 is unchanged** — it is the failsafe that makes SP mean something. Do not remove it when retuning.

---

## 9. `_TEMP_POWER_REMAP` — redesign aliases

`food_system._TEMP_POWER_REMAP` (L148) maps 26 redesign-friendly temp_power names (used by prime_cuts.json legacy fields + older recipes) onto 11 canonical status effects actually consumed by combat, FOV, etc.

As of v2.18 **only one entry is live-reachable**: `'petrify_resist' → 'save_guard_CON'`. The remap used to serve two populations:

- **The prime_cuts.json legacy fields** — `temp_power`, `temp_duration`, `temp_desc`, `stat_grant`, `trophy_desc`, `trophy_permanent_power`, `trophy_recipe_name`. All 7 were **deleted from prime_cuts.json in v2.18** (527 entries × 7 fields = 3,689 field deletions). What remains per prime_cut row is only the lookup data: `monster_id`, `monster_name`, `family`, `is_trophy`, `ingredient_id`, `ingredient_name`.
- **`cook_outcomes.json` authored under the redesign names.** The 2026-09 trophy_medusa archetype used `temp_power: 'petrify_resist'`, which `_resolve_temp_power` rewrites to `save_guard_CON`. In v2.18 that row was **canonicalized directly** — `trophy_medusa.temp_power` is now stored as `'save_guard_CON'` and the remap is no longer invoked for it.

The 25 other remap entries are dormant: nothing in the live JSON references them. They are kept as a one-pass shim in case future authored data reaches for the redesign names (an offline generator in `tools/balance` still speaks the old vocabulary when seeding ingredient drafts).

The remap is a one-way alias table. Any value *not* in the map is returned unchanged — recipes authoring `blessed`, `shielded`, `brilliance`, etc. flow straight through.

---

## 10. `_apply_permanent_power` dispatch — 14 trophy powers + fallback

Each trophy outcome in `cook_outcomes.json` carries a `permanent_power` string. `food_system._apply_permanent_power(player, power_id, recipe)` (L320) switches on that string:

| `permanent_power` | Trophy | Effect |
|-------------------|--------|--------|
| `all_stats_plus_1` | `trophy_abaddon` | +1 to all six stats (apotheosis). |
| `plus_3_str` | `trophy_fenrir`, `trophy_blood_archon` | Permanent +3 STR. |
| `plus_2_con_petrify_immune` | `trophy_hrungnir` | +2 CON + permanent `petrify_immune` effect. |
| `plus_2_wis_auto_reveal_secret_doors` | `trophy_whispering_crone` | +2 WIS + permanent `auto_reveal_secret_3` effect. |
| `plus_2_str_confuse_immune` | `trophy_asterion` | +2 STR + permanent `confuse_immune` effect. |
| `fire_immunity` | `trophy_surtur` | Permanent `fire_immune`. |
| `cold_immunity` | `trophy_ymir` | Permanent `cold_immune`. |
| `petrify_immunity` | `trophy_medusa` | Permanent `petrify_immune`. |
| `chromatic_resist_all` | `trophy_tiamat` | Permanent 25% resist to fire / cold / shock / poison / acid. |
| `one_time_death_save` | `trophy_asmodeus` | Sets `player._asmodeus_pact = True`; next lethal hit skipped, flag cleared. |
| `revive_once_at_half_hp` | `trophy_green_knight` | Sets `player._green_knight_revive = True`; on death, revive at half HP once per run. |
| `max_hp_per_floor_descent` | `trophy_fafnir` | Sets `player._fafnir_per_descent_hp = 2`; +2 max HP each new descent (read in `_change_level`). |
| `max_mp_per_floor_descent_and_poison_immunity` | `trophy_nidhoggr` | Sets `player._nidhogg_per_descent_mp = 2` + permanent `poison_immune`. |
| `lifesteal_5pct_on_melee` | `trophy_blood_archon` (shared id with Fenrir's `plus_3_str` elsewhere) | Sets `player._blood_archon_lifesteal = 0.05`; 5% melee lifesteal. |
| *(fallback)* | — | Returns `desc or f"You feel a permanent change ({power_id})."` so a typo in `cook_outcomes.json` is visible, not silent. |

That is 14 explicit targets + 1 default branch — 15 arms total. The 14 trophy outcomes in `cook_outcomes.json` each slot into exactly one target. The `trophy_<boss>_recipe` entries in `recipes.json` are the 14 recipe rows whose `outcome_id` points at these trophy outcomes.

Trophy flavor: when the trophy outcome has both a `temp_power` and a `permanent_power`, the ladder is temp-first (the body applies the ward) then permanent-last (the dispatcher applies the enduring mutation). The player sees a timed buff *and* an irreversible stat/effect in one meal — the "cooking a boss transforms you" fantasy the design banks on.

---

## 11. Eating paths (non-quiz)

### 11.1 `eat_food(player, food_item)` — rations (`data/items/food.json`)

17 rations: bread, cheese, apple, mushroom, jerky, pie, etc. Each row carries `sp_restore` (20–115), optional `hp_restore`, and an optional `bonus_type` with the same vocabulary as the dead `_apply_bonus` branch (`none / random_stat / combat_stat / two_stats / all_stats / stat / status`). Eating fires the bonus via `_apply_bonus(player, bonus_recipe)` — this bonus-dispatcher still routes through `player.apply_cooking_stat_bonus` when it falls through to a stat gain, so ration stats share the lifetime softcap with cooking stats.

No quiz. No chance of ruin.

### 11.2 `eat_raw(player, ingredient)` — raw ingredient fallback

The survival floor. No quiz, no cooking benefits. Flat SP from `ingredient.raw_sp` (if set) or the `tier_role` map:

| `tier_role` | Raw SP |
|-------------|-------:|
| `universal` (Assorted Monster Jerky) | 12 |
| `family` | 10 |
| `dungeon` (cave mushroom, river salt, …) | 10 |
| `prime` | 15 |
| `trophy` | 20 |

**Food-poisoning:** 30% chance to apply `poisoned` for 8 turns (-1 HP/turn), unless the player has `poison_resist` or the ingredient is `edible_safe` / `assorted_monster_parts`. Jerky and cured foods never poison — that is the whole point of the Jerky survival floor.

### 11.3 `drink_potion(player, potion)` — potions

Potions live in the food module only because the eating/drinking surface is co-located; mechanically they are a separate system (BUC multipliers for heal / buff / harm, binary-effect fizzle-or-preserve). See the Potions section in `[items](items.md)` for the full effect list — this doc covers only the fact that `food_system.drink_potion` is where that dispatch lives.

---

## 12. Cook quirks — Tantalus, Persephone, Circe

Three quirks hang off the cook pipeline. Before v2.18 only the dead `_cook_item` path called `on_food_eaten`, so **none of them could unlock in normal play**. The v2.18 fix wires the compound-cook path (`Game._cook_compound.on_complete`) to call `on_food_eaten` with the real outcome tier + a derived bonus category.

### 12.1 Tantalus (ID 16) — "Tantalus' Resolve"

- **Trigger.** `on_food_eaten(quality=0, ...)` 15 times. Quality 0 = any ruined cook.
- **Reward.** Permanent +1 STR.
- **Flavor.** "Even the worst meal nourishes the will to eat better next time."
- **How to grind.** Deliberately fail easy T1 cooks on cheap ingredients. The ruin branch still counts.

### 12.2 Persephone (ID 34) — "Persephone's Descent"

- **Trigger.** `on_food_eaten(quality=5, ..., ingredient_id)` from **5 distinct `ingredient_id` values**. Quality 5 = any T5 success.
- **Reward.** Sets `player.quirk_progress['persephone_active'] = True`. From that point on, ruined cooks still deliver **half the archetype's SP + HP** (buffs / `max_hp_bonus` / `stat_grant` / `permanent_power` are **not** salvaged — only recovery is).
- **Code path.** `_apply_recipe_outcome(..., ruined=True)` inspects `player.quirk_progress['persephone_active']`; if set, it fetches the archetype from `cook_outcomes.json` anyway and applies `sp // 2`, `hp // 2`. The salvage message is `"You ruin the preparation of <name>, but Persephone's grace saves the seed. You salvage what you can: +X SP, +Y HP."`
- **Flavor.** "To descend is not defeat — some seeds only bloom in the dark."
- **Related mystery mechanic.** Pandora's `invert_result: True` in `mystery_system.py` is a parallel "lose = win" shape: losing the quiz triggers the reward. Persephone is the per-run cook-side equivalent, but implemented via the ruin branch of `_apply_recipe_outcome` rather than a quiz-result inversion.

### 12.3 Circe (ID 39) — "Circe's Cauldron"

- **Trigger.** `on_food_eaten(bonus_type=...)` with **5 distinct `bonus_type` categories**. The compound-cook callback runs `_outcome_bonus_category(outcome)` (`src/main.py:98`) to turn the outcome shape into one of five coarse labels:
  - `permanent` — `outcome.permanent_power` set.
  - `stat` — `outcome.stat_grant > 0`.
  - `temp_power` — `outcome.temp_power` set.
  - `max_hp` — `outcome.max_hp_bonus > 0`.
  - `recovery` — anything else (just SP + HP).
- **Reward.** `self._timer_bonus('cooking', 4)` — +4s on the cooking quiz timer, applied via `player.quiz_timer_bonuses['cooking']`.
- **Flavor.** "I transform nothing arbitrarily. Each change reveals what was inside."
- **Grind.** Cook five archetype-shapes: one plain recovery, one with a temp buff, one with a stat bonus, one with a max_hp bump, one trophy.

### 12.4 Pre-v2.18 state

Prior to the v2.18 wiring fix, `_cook_compound` built up `_qs_cook` references but never called `on_food_eaten`. The marked-unreachable `_cook_item` was the only call site. All three quirks were effectively unobtainable through normal play — the audit flagged this as a P1 live bug. v2.18 wires both call sites and derives `_quality` from the outcome tier (not from legacy "quality N" message-string grep) and `_bonus_type` from `_outcome_bonus_category(outcome)`.

---

## 13. Known live state (from SYSTEMS_AUDIT)

### 13.1 Live bugs still open (post-v2.18)

- `mystery_system.py:181` — mystery cooking challenges use `escalator_chain` with threshold 5. This violates the one-Q cook flow. Any cook-quiz triggered by a mystery bypasses the v2 model. Scope-limited to the mystery system; the normal cook path is unaffected.
- Six `_comment_*` string entries live in `cook_outcomes.outcomes`. A recipe mis-authored with `outcome_id: "_comment_t1"` would AttributeError inside `_apply_outcome_body`. Low-risk (no recipe currently references one), but `_load_outcomes()` should filter keys starting with `_`.

### 13.2 Verified-OK (as of v2.18)

- Cook cadence: 1 Q, threshold=1, subject=cooking, tier from `outcome.tier`.
- Harvest cadence: 1 Q, threshold=1, subject=animal, tier from `corpse.harvest_tier`.
- Harvest outcome map: 527 prime_cut IDs all resolve to real `ingredient.json` rows.
- Recipe → outcome wiring: all 614 recipes have `outcome_id`; zero orphans.
- Persephone salvage branch reads the correct archetype on the ruined path.
- Corpse + ingredient resource-loss semantics correct (consumed pre-callback).
- Container `quiz_threshold=1` across the board.

### 13.3 Dead code (annotated, kept)

- `food_system.cook_ingredient` (`src/food_system.py:543`). The Single-tab solo cook. Pinned by `tests/test_bugbatch_2_0_3.py` + `tests/test_harvest_cook_integration.py` + `tests/test_cooking_overhaul.py` as a regression harness for the 2026-06-04 "cooking one ingredient devours a stack" fix. **Do not delete** without first retiring those tests.
- `Game._cook_item` (`src/main.py:4735`). Unreachable since 2026-06-07 (the Single tab was removed from `_COOK_TABS`). Kept as the companion call site for `cook_ingredient`; same test-pin applies.
- `_TEMP_POWER_REMAP` entries 2–26 — see §9. One live entry (`petrify_resist`), 25 dormant.
- `_apply_tier_outcome` — the v2.6.3 legacy shim was removed from `food_system.py` on 2026-09-27 after an audit confirmed zero call sites. SP/HP potency helpers (`SINGLE_MULT`, `COMPOUND_MULT`, `_potency`, `_single_max_hp`, `_compound_max_hp`, `_cooking_sp`, `_cooking_heal`) were removed in the same sweep. An offline copy survives in `tools/balance/` for the ingredient-draft generator.

### 13.4 Dead JSON fields swept in v2.18

Seven text fields were removed from every row of `prime_cuts.json` (527 rows affected):

| Field | Previous role | Why dead |
|-------|---------------|----------|
| `temp_power` | Short status effect on raw-eat / cook. | Raw-eat path doesn't read it (uses `raw_sp` + `tier_role`); cook path reads it only from `cook_outcomes.json`. |
| `temp_duration` | Turns of the above. | Same. |
| `temp_desc` | Flavor blurb for the above. | Never surfaced; no reader. |
| `stat_grant` | Default stat for cooked outcomes. | Moved to `cook_outcomes.outcomes[*].stat_grant_default`. |
| `trophy_desc` | Trophy flavor on the raw ingredient. | Trophy flavor now lives on the trophy outcome (`permanent_desc`). |
| `trophy_permanent_power` | Trophy's permanent-power id. | Moved to `cook_outcomes.outcomes[trophy_*].permanent_power`. |
| `trophy_recipe_name` | The trophy recipe's display name. | Lives on `recipes.json[trophy_*_recipe].name` already. |

Four other dead fields the audit flagged live outside this module (`harvest_threshold` on monsters, `ingredient_id` on corpses, `quiz_threshold` on containers, the `trap` block on chests). They are documented in the audit; the food system itself ignores them.

### 13.5 Stale text still open

- `player.py:446::on_level_change` docstring still references the retired quality gradient / Q3+ singles.
- `food_system.py:120-125` docstring references "Q1 = raw SP … Q2-Q5 scale upward" from the retired potency formulas.
- `main.py:4710::_cook_item` uses the string "mediocre", which no v2.6.4 outcome ever emits.

These are cosmetic — behaviour is correct, the comments lag.

---

## 14. Save-file compatibility

Three legacy surfaces are tolerated for old saves and intentionally not migrated unless the user asks:

- `Corpse.__setstate__` translates old `lore_identified: bool` → `id_level ≥ 4` (see `src/items.py:1084`).
- `Corpse.ingredient_id` is still accepted on load (via `make_corpse`) but ignored by harvest — v4 keys off `monster_id`.
- `monsters.json::*.ingredient_id` is a cold field — 525/527 monsters still write it. Harvest doesn't read it. Bestiary `_draw_bestiary_page` at `id_level >= 2` *does* `load_ingredient_for(subject.ingredient_id)`, which returns `None` for the old scheme ids (`rat_meat`, `goblin_flesh`, …) that aren't in `ingredient.json`. The "Ingredient:" / "Solo cook:" / recipe hint lines simply never render. Audit flagged as a P1 live bug on the bestiary side — not fixed here.

---

## 15. Worked example — cook a Trophy Medusa recipe

Setup: the player has killed the Medusa boss (floor 69), harvested her corpse with the right-answer path (`medusa_gorgon_trophy` ingredient in inventory), and opened the cook menu.

1. The Recipes tab shows `trophy_medusa_gorgon_recipe` as cookable because the ingredient list `['medusa_gorgon_trophy']` is held.
2. Player selects it. `Game._cook_compound(recipe)` fires:
   - `recipe['outcome_id'] = 'trophy_medusa'`.
   - `_load_outcomes()['trophy_medusa'] = {tier: 5, sp: 140, hp: 20, max_hp_bonus: 3, stat_grant: 1, stat_grant_default: 'DEX', temp_power: 'save_guard_CON', temp_amount: 3, temp_duration: 200, permanent_power: 'petrify_immunity', ...}`
   - `_outcome_tier = 5`. `_outcome_bonus_category(outcome) = 'permanent'` (because `permanent_power` is set).
   - `_anchor_id = 'medusa_gorgon_trophy'`; `_source_monster = 'medusa_gorgon'` (read off the live `Ingredient` instance).
3. `cook_compound_recipe` pops the trophy ingredient from inventory, kicks the cooking quiz at tier 5.
4. Player answers correctly. `_apply_recipe_outcome(player, recipe, ruined=False)` → `_apply_outcome_body`:
   - `restore_sp(140)`, `restore_hp(20)`.
   - `try_apply_cook_hp_gain(3, bypass=True)` — bypasses the +5/floor cap, applies through lifetime softcap.
   - `try_apply_cook_stat_gain('DEX', 1, bypass=True)` — same bypass.
   - `_resolve_temp_power('save_guard_CON') = 'save_guard_CON'` (unchanged — already canonical in v2.18). `player.add_effect('save_guard_CON', 200)`; `player._save_guard['CON'] = min(3, temp_amount=3) = 3`.
   - `_apply_permanent_power(player, 'petrify_immunity', fake_recipe)` → `player.add_effect('petrify_immune', -1)`.
5. Messages: `"You prepare Gorgon's Antitoxin." / "You eat it: +140 SP, +20 HP." / "The meal fortifies you permanently. (+3 max HP)" / "Your dexterity increases by 1!" / "A short save guard CON lingers." / "Permanent petrification immunity. Never again will stone claim you."`
6. `on_complete`: logs chronicle entry if first compound cook, adds "Gorgon's Antitoxin" to `_cooked_recipes`, calls `_qs_cook.on_food_eaten(quality=5, source_monster='medusa_gorgon', bonus_type='permanent', ingredient_id='medusa_gorgon_trophy')`.
   - Persephone progress: `persephone_quality5` set gains `'medusa_gorgon_trophy'`. If this is the 5th distinct id → quirk unlocks.
   - Circe progress: `circe_bonus_types` gains `'permanent'`. If this is the 5th distinct category → quirk unlocks.
7. `_advance_turn()`.

Contrast with the ruined branch (same recipe, wrong answer): ingredient is already gone, no message other than `"You ruin the preparation. The Gorgon's Antitoxin is wasted."`, Tantalus's `ruined_meals` counter increments by 1. If `persephone_active` is set, the player instead gets `+70 SP, +10 HP` and no buff/stat/permanent-power.

---

## 16. Cross-links

- [items](items.md) — `Corpse`, `Ingredient`, `Food`, `Potion` class contracts; the harvest-tier source on monsters.
- [monsters](monsters.md) — `monsters.json` schema, including `harvest_tier` (used), `harvest_threshold` (dead), `peak_floor` (used by corpse `id_tier`).
- [progression](progression.md) — the cook quirks sit in the broader quirk ladder; Mithridates / Siegfried also hang off `on_harvest` + `on_food_eaten`.
- [status_effects](status_effects.md) — canonical temp_power names (`save_guard_CON`, `blessed`, `regenerating`, `fire_resist`, …) that `_resolve_temp_power` targets; `BUFFS` / `DEBUFFS` lists; `_save_guard` consumer.
- `feedback_flow_over_gradient.md` — the "one question per attempt" rule.
- `feedback_resource_loss_is_the_penalty.md` — the "consumed on attempt" rule.
- `feedback_sp_soft_boundary.md` — the SP-via-generous-supply rule; keep starvation damage.

---

## 17. Change log

| Version | Date | Change |
|---------|------|--------|
| v2.6.1 | 2026-09-01 | Harvest cadence rewritten to one animal Q, threshold=1, tier from `corpse.harvest_tier`. |
| v2.6.2 | 2026-09-01 | Cook cadence rewritten to one cooking Q, threshold=1, tier from recipe class. No chain, no partial credit. |
| v2.6.3 | 2026-09-02 | Potency-based cooking formulas (`SINGLE_MULT`, `COMPOUND_MULT`, `_potency`, `_single_max_hp`, `_compound_max_hp`, `_cooking_sp`, `_cooking_heal`). |
| v2.6.4 | 2026-09-02 | Outcome-archetype dispatch. `cook_outcomes.json` added; `recipes.json` rows now carry `outcome_id`; `_apply_tier_outcome` retired (shim kept until 2026-09-27). |
| v2.6.5 | 2026-09-03 | Harvest outcome collapsed to one themed drop per corpse (`<monster_id>_prime` / `<monster_id>_trophy`) regardless of tier. |
| 2026-09-27 | — | Dead-code sweep: `_apply_tier_outcome`, `SINGLE_MULT`, `COMPOUND_MULT`, `_potency`, `_single_max_hp`, `_compound_max_hp`, `_cooking_sp`, `_cooking_heal` removed from `src/food_system.py`. Offline copies retained in `tools/balance/`. |
| v2.18 | 2026-10-01 | Compound-cook path now calls `on_food_eaten`, unlocking Tantalus / Persephone / Circe. Quality is read from `outcome.tier`; bonus category is derived via `_outcome_bonus_category`. `trophy_medusa.temp_power` canonicalised to `save_guard_CON` directly. 7 dead text fields removed from all 527 `prime_cuts.json` rows. |
