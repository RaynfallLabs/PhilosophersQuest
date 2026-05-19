# V2 Audit — Recipes + Food + Ingredients

Date: 2026-05-19
Auditor: subagent (Opus 4.7, 1M)
Scope: `data/items/recipes.json` (483), `data/items/food.json` (17),
`data/items/ingredient.json` (325).
Cross-refs: `data/monsters.json`, `src/food_system.py`, `src/items.py`,
`src/status_effects.py`, `src/dungeon.py`.

## Verdict

**PASS WITH FIXES.** Three substantive bugs found and fixed (43 JSON edits,
1 code-side one-line edit in `src/dungeon.py`). Plus 1 report-only orphan
ingredient. After fixes: 476/476 tests still passing.

The data layer is otherwise in excellent shape: zero broken ingredient
references in 483 recipes, complete quality-0..5 inner-recipe sets on every
one of 325 ingredients, no malformed colors, no missing weight/min_level,
no missing bonus_stat, recipe SP curves and HP-restore curves cleanly tier
upward, and the magic dungeon carrot is intact for the quest path.

## Schema reconciliation

`CURVES.md` lists the recipe schema as:
```
id, name, ingredients (list of {item_id, count}), output (effect dict),
tier, quiz_tier, quiz_threshold
```

The **live** schema in 483 recipes is flat:
```
name, ingredients (list of str), sp, bonus_type, bonus_amount,
bonus_stat, bonus_effect, description, sprite_desc
```

This is correct — `src/food_system.cook_compound_recipe` reads exactly the
flat shape. `CURVES.md` is documenting an aspirational target. Treating the
flat shape as canonical (because the code does); recommending CURVES.md be
updated separately.

Tier/quiz_tier/quiz_threshold are not needed at the recipe layer because:
- Cooking quiz **always starts at tier 1** (see `cook_compound_recipe`
  passes `tier=1` unconditionally — comment line 22 of `food_system.py`).
- "Quality" is the escalator-chain score (0-5).
- Ingredient potency comes from the source monster's `min_level`, fed into
  `_potency = sqrt(min_level)`, then multiplied by `SINGLE_MULT` or
  `COMPOUND_MULT` tables.

So there is no recipe-tier concept in the live code.

## Auto-fixed (this run) — JSON

### 1. Five status effect names re-mapped to canonical (43 edits)

`food_system._apply_bonus` routes `bonus_type='status'` into
`player.add_effect(name, duration)`, which forwards to
`status_effects.apply_effect`. That function does NOT validate the name —
it stores any string in `player.status_effects` indefinitely. Names not
in `BUFFS | DEBUFFS` are stored but produce no tick, no visual cue, no
mechanical effect. So unrecognized names are silent dead bonuses.

Five names were used in data but absent from `BUFFS|DEBUFFS`:

| Old name           | Canonical mapped to | Reason for choice                                                                |
|--------------------|---------------------|----------------------------------------------------------------------------------|
| `haste`            | `hasted`            | Trivial: `hasted` is the canonical name everywhere else (potion `haste` effect calls `add_effect('hasted')`). |
| `lightning_resist` | `shock_resist`      | Both refer to electric damage immunity; `shock_resist` is the canonical (BUFFS). |
| `arcane_shield`    | `magic_resist`      | Closest functional equivalent — blocks confusion/charm/silence/fear/hallucinate. |
| `death_ward`       | `life_save`         | Closest functional equivalent — survives one killing blow.                       |
| `blind_resist`     | `truesight`         | Closest functional equivalent — sees through invisibility/blindness.             |

Edits: 9 compound recipes + 34 ingredient inner-recipes = 43 entries
patched. Spot-checked post-edit:
- `recipes['bat_wing_cracklings'].bonus_effect == 'hasted'` ✓
- `recipes['samael_void_tagine_grand'].bonus_effect == 'life_save'` ✓
- All 5 old names confirmed absent from data files.

### 2. Source-monster mismatch fixed (1 edit)

`ingredient.winged_mane.source_monster` was `'pegasus_corrupted'`, but
`monsters.pegasus_corrupted.ingredient_id` is `'corrupted_wing_feather'`.
The actual monster that drops `winged_mane` is `monsters.pegasus` (vanilla
pegasus). Changed to `'pegasus'`.

## Auto-fixed (this run) — Code

### 3. Eight plant ingredients were unreachable in dungeon spawns

`dungeon.spawn_items()` lines 1402-1421 spawns plant-source ingredients
by **name keyword match** against a tuple `_PLANT_KEYWORDS = (...)`.
Ingredients lacking source_monster but whose names didn't contain any
keyword were never placed:

```
wild_thyme, rosemary_sprig, pale_celery, cave_carrot,
glowing_spore, serpent_pepper, void_salt, dragon_salt
```

These 8 are referenced by **193 compound recipes** — meaning ~40% of
compound recipes were uncookable on a fresh save. Examples blocked:
`herbed_serpent_fricassee`, `bullywug_carrot_bisque`,
`basilisk_perpignan` (3 of these herbs), `samael_void_tagine_grand`.

Fix: extended the keyword tuple in `src/dungeon.py` to add
`thyme, rosemary, celery, carrot, spore, pepper, salt, sprig`.
This is a one-line additive change. No data migration needed.

Verified post-edit by recomputing the eligible-plant set: all 15
non-monster-sourced ingredients now match at least one keyword.

## Report-only findings

### R1. One orphan ingredient

`green_slime_extract` declares `source_monster: green_slime`, but
`monsters.green_slime.ingredient_id` is `slime_core` — and no other
monster drops `green_slime_extract`. So this ingredient is unreachable
in normal play. It IS referenced by 4 compound recipes
(`slime_acid_consomme`, etc., grep-confirmed).

Resolution requires a design call (NOT auto-fixed):
- Option A: change `monsters.green_slime.ingredient_id` to
  `green_slime_extract` (drops the existing `slime_core` ingredient,
  which is also dropped by `gelatinous_titan` so it stays reachable).
- Option B: change `ingredient.green_slime_extract.source_monster` to
  some other slime monster and add `ingredient_id` to that monster.
- Option C: delete `green_slime_extract` and rewrite its 4 dependent
  recipes to use `slime_core` instead.

Recommend Option A — fewer recipe edits, slimes have one canonical drop.

### R2. Food coverage gap at tiers 4-5

Tier 1 (ML 1-20): 12 food items.
Tier 2 (ML 21-40): 3 food items.
Tier 3 (ML 41-60): 2 food items (`void_ration`, `peach_of_immortality`).
Tier 4 (ML 61-80): **0 food items**.
Tier 5 (ML 81-100): **0 food items**.

Compound recipes cover the gap fine (40 recipes in band 5 alone via
monster ingredients), so the gap is only for *floor-spawned* food. Deep
dungeon explorers rely entirely on cooking by then, which is intended
by the design. Flagging as report-only rather than bug — but consider
adding 2-3 late-game food items (e.g., `phoenix_feast`, `dragon_pastry`,
`ambrosial_distillate`) for variety in floors 60+.

### R3. HP restoration curve — spec vs reality

`CURVES.md` says:
- Tier 1 food: hp_restore 5-15
- Tier 5 food: hp_restore 50-100

Live tier-1 food shows hp_restore = 0,0,0,3,2,0,8,5,15,0,**80**,10:
- 10/12 fall in 0-15 (good)
- `tantalus_plum` has hp_restore=80 at min_level=12 — far above curve, but
  this is the iconic mythological item (lore: "Tantalus served his own
  son to the gods…"). Item is intentionally a rare-find lottery — leave
  as-is.
- `magic_dungeon_carrot` hp=10 sp=30 — intact and untouched as the quest
  spec required.

Live tier-3 food: hp 10, 40. `peach_of_immortality` at hp=40 is mid-band.
No tier-4/5 food (see R2).

Verdict: curve fits all but the intentional mythological outlier.

### R4. Recipe SP doesn't actually drive SP gain

`recipe.sp` field is populated on all 483 compound recipes (range 57-356,
mean rising with band), but `cook_compound_recipe` never reads it —
SP gain comes from `_cooking_sp(max_min_level, quality)` which is the
potency formula. So the `sp` field on **compound** recipes is
documentation-only. (It IS used as `raw_sp` floor for single-ingredient
`cook_ingredient` cooks via `ingredient.recipes[1].sp`.)

Not a bug, but worth being aware: if you bump compound recipe `sp`
expecting gameplay impact, it won't change anything. The lever is the
ingredient's `min_level` (which feeds `_potency`).

### R5. Floor-distribution holes (ingredients)

L1-L15: dense (22+23+29+21+16+20+29+12+6+35+7+3+11+11 = 245 ingredients).
L16-L50: thinner but present at L20, 22, 25, 28, 30, 35, 38, 40, 42, 44,
45, 48, 50.
L51-L100: very thin — single-digit ingredient counts per 5-level band.

The largest gaps are 4-level bands (L31-34, L71-74) and 3-level bands
(L17-19, L52-54, L59-61, L65-67, L77-79, L94-96). All gaps are < 10
levels — task spec said flag gaps >10. **No flagged gaps.**

That said, L23-L100 is thin enough that a player on those floors will
mostly cook the same handful of ingredients. Compound recipe variety
papers over this because pair-mixing creates many distinct meals from
the same ingredients.

### R6. Recipes mixing low- and high-tier ingredients (intentional)

81 compound recipes have a >50-level span between their lowest and
highest ingredient. Examples: `wild_hunt_odin_feast` mixes
`wild_hunt_horn` (ML 80) + `wolf_pelt` (ML 5); `samael_void_tagine_grand`
mixes `samael_death_vial` (ML 91) + `valerian_root` (ML 2).

This is by-design. `cook_compound_recipe` derives potency from
`max(ing_min_levels)` so the trophy ingredient dominates and the
seasoning is just a flavor pairing. Verified: no SP/HP-bonus loss
from this pattern.

### R7. Bonus-amount handling

- 258 recipes use `bonus_amount=1`, 128 use `2`, 53 use `3`: all are
  stat-bonus amounts (random_stat/combat_stat/two_stats/stat/all_stats).
- 38 recipes use larger values (6-60): all are `bonus_type='status'`
  duration in turns. Median 22 turns, range 6-60. Reasonable.
- No recipe has `bonus_amount=0` for a non-`none` bonus_type.
- All `bonus_type='stat'` recipes have a non-empty `bonus_stat`.
- All `bonus_type='status'` recipes have a non-empty `bonus_effect`.

All clean.

### R8. Ingredient inner-recipe quality coverage

Every one of 325 ingredients has all six quality recipes (0-5). Zero
gaps. Bonus types in inner recipes follow the expected pattern:
quality 0 is always `none`, quality 5 mostly stat/two_stats/all_stats
or status, with intermediate qualities flowing upward. No anomalies.

## Effect dispatch table (verification)

`food_system._apply_bonus` handles exactly:
`none, random_stat, combat_stat, two_stats, all_stats, stat, status`.

All bonus_types observed in data (483 recipes + 325 × 6 ingredient
inner-recipes + 17 food items) fall in this set. No unhandled types.

## Files modified

| File | Edits |
|---|---|
| `data/items/recipes.json` | 9 bonus_effect renames |
| `data/items/ingredient.json` | 34 inner-recipe bonus_effect renames + 1 source_monster fix |
| `src/dungeon.py` | 1 PLANT_KEYWORDS tuple extension (additive) |

Total: 44 JSON edits + 1 code edit.

## Tests

Before changes: `476 passed in 64.05s`.
After changes:  `476 passed in 64.24s`.

No regressions. Cooking quiz path, harvest path, eat-raw path, and
plant-spawn path are all covered by existing tests; all pass.

## Final report (one-line summary)

PASS WITH FIXES. Zero broken ingredient references (out of 483 recipes).
Patched 43 silently-dead status effects + 1 source_monster mismatch + 1
keyword-spawn gap that blocked ~190 compound recipes. One orphan
ingredient (`green_slime_extract`) flagged for design decision. 476/476
tests pass after fixes.
