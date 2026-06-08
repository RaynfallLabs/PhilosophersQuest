# Cooking & Recipe Overhaul — Design Proposal

**Date:** 2026-06-07
**Status:** Proposal only (no live files edited)
**Author goal (verbatim):** *"I think we need to make cooking recipes a bigger deal. Make Assorted Monster Parts something like Assorted Monster Jerky that you can just eat, to not starve. But then make the recipes require more parts, or more varied parts, so collecting them and cooking them up is a big deal."*

---

## TL;DR — Headline Recommendations

1. **Jerky as the survival floor.** Turn `assorted_monster_parts` into **"Assorted Monster Jerky"** — a directly-edible, no-quiz, no-poison snack worth **+12 SP, +0 HP**. It becomes the thing you eat to *not starve*. (Today raw assorted parts give 5 SP with a 30% poison risk — too punishing to be a reliable survival food, which is exactly why cooking feels mandatory instead of aspirational.)
2. **Recipes become an investment.** Every recipe class today costs **exactly 4 ingredient slots** with a near-identical shape (`1 anchor + 1 family + 2 assorted`). Raise requirements so a real dish demands **more parts and more variety**, scaling by class:
   - **Basic stew:** `5 assorted` → **`8 assorted`**
   - **Family roast:** `1 family + 3 assorted` → **`2 family + 4 assorted`** (6 slots)
   - **Prime dish:** `1 prime + 1 family + 2 assorted` → **`1 prime + 2 family + 4 assorted`** (7 slots)
   - **Dungeon-keyed:** `1 special + 1 prime + 1 family + 1 assorted` → **`1 special + 1 prime + 2 family + 3 assorted`** (7 slots)
   - **Master (2-monster):** keep the multi-prime identity, bump assorted → **`2 primes + 1 family + 3 assorted`** baseline (varies, see §B)
   - **Trophy (boss):** `1 trophy + 1 family + 3 assorted` → **`1 trophy + 2 family + 5 assorted`** (8 slots) — the permanent-power meal should be a genuine hoard-spend.
3. **Jerky pays the SP tax so recipes don't have to.** Because jerky reliably covers "don't starve," the richer recipes are an **upgrade you choose** (max-HP, stat, temp/permanent powers), not a tax you're forced to grind. Per-floor cook caps (+5 max HP / +1 stat) and the family-T5 60-turn buff are **untouched** — they already prevent runaway power; we're raising the *input cost*, not the *output ceiling*.
4. **Mostly a data change.** Requirements live in `data/items/recipes.json`. The jerky-edible behavior is a **3-line data tweak** to `eat_raw`'s SP map plus a poison-exemption check — no new item class, no new menu.

---

## 1. AUDIT — How the food economy works today (with real numbers)

### 1a. Starvation & the SP economy

- **There is hunger, modeled as SP drain.** `Player.BASE_SP = 200` (+STR). `Game._tick_sp` (`src/main.py:3753`) drains **1 SP per 2 moves** (0.5/move). Ring of Sustenance / `sustained` halves it (1 per 4 moves); beast-family `sp_regen` mastery and a few chain passives stretch it further.
- **Runway:** a full SP pool (200) lasts **~400 moves** before starvation begins. At SP 0, the player takes **1 damage per drain tick** and `defeat_reason='starved'` on death (`src/main.py:3784-3790`).
- **What restores SP/HP:**
  - **Eating raw** (`eat_raw`, `food_system.py:1088`): flat SP by `tier_role` — `universal:5, family:10, dungeon:10, prime:15, trophy:20`. **30% food-poisoning chance** (8-turn poison) unless `poison_resist`.
  - **Eating Food items** (`eat_food`): `bread_ration` 25 SP, `dried_meat` 35 SP, etc. (`data/items/food.json`). No quiz, no risk — but these are floor loot, not craftable.
  - **Cooking** (`_apply_tier_outcome`): the main engine. SP + HP + max-HP + stat + powers, scaled by cook-quiz tier (T0–T5).
  - **Stair-rest** (`on_level_change`): +15 SP, small HP/MP, **first visit to a floor only** (no stair-stomp exploit).
  - **Potions:** `restore_sp` potion ≈ 50 SP.
- **HP regen:** passive 1 HP / 15 turns (`_tick_hp_regen`), blocked while bleeding/poisoned. **No HP on descent** (`STAIR_REST_CAP_DESC = 0`) — damage accumulates, so cooking's HP/max-HP is the real healing economy.

### 1b. Are assorted parts edible directly today?

**Yes, but badly.** From the Eat menu (`z`), an `Ingredient` routes to `eat_raw` → **5 SP and a 30% poison roll.** That's ~10 moves of runway for a coin-flip of self-poisoning. Practically, raw assorted parts are a trap, which forces players into the cooking flow even for basic sustenance. This is the gap the user wants to close.

### 1c. Ingredient acquisition (harvest tiers)

Harvest is an **animal `escalator_chain`** quiz; tiers are **cumulative** (`_harvest_outcome_for_tier`, `food_system.py:50`):

| Cook-quiz tier reached | Ingredients gained (cumulative) |
|---|---|
| T0 | nothing (ruined) |
| T1 | 1× assorted |
| T2 | **2× assorted** |
| T3 | 2× assorted **+ 1× family** |
| T4 | 2× assorted + **2× family** |
| T5 | 2× assorted + 2× family **+ 1× prime/trophy** |

**Typical yield per corpse:** a competent harvester lands ~T2–T3, so **~2 assorted (+ maybe 1 family)** per kill. Assorted parts are the abundant currency; family parts are moderately common (T3+); primes are the T5 payoff; trophies are boss-only.

- **Ingredient bank:** 550 ingredients — `universal:1` (assorted), `family:12`, `prime:516`, `trophy:13`, `dungeon:8` (terrain-foraged: cave mushroom, swamp moss, river salt — the only non-monster, floor/chest-lootable tier).
- Family parts **stack across a whole family** (e.g. any beast → `family_beast` "Beast Meat"), so they accumulate faster than primes.

### 1d. Recipe requirements today — they are trivially cheap & monotonous

**620 recipes.** Ingredient-slot count is nearly uniform: **606 recipes use exactly 4 slots**, 14 use 5. Composition by class (measured):

| Class | Count | Composition (today) | Slots |
|---|---|---|---|
| basic | 1 | `5× assorted` | 5 |
| family | 12 | `1 family + 3 assorted` | 4 |
| prime | 514 | `1 prime + 1 family + 2 assorted` | 4 |
| trophy | 13 | `1 trophy + 1 family + 3 assorted` | 5 |
| master | 51 | mostly `1 family + 3 prime` / `1 assorted + 1 family + 2 prime` | 4 |
| dungeon | 29 | `1 special + 1 prime + 1 family + 1 assorted` | 4 |

**The problem in one line:** the overwhelmingly common pattern is **"1 special part + 1 family + 2 assorted."** Since you net ~2 assorted *per corpse* and family parts stack, you can cook almost any prime dish off a **single good harvest**. Cooking is a freebie, not a project. (Master recipes are the exception — they already demand multiple primes — and are the model to lean toward.)

### 1e. Constraints the overhaul must respect (recent work — do not break)

- **Per-floor cook caps** (`player.py:513`): `PER_FLOOR_HP_CAP = 5`, `PER_FLOOR_STAT_CAP = 1`. Reset on descent. Trophy recipes `bypass=True`.
- **Floor-aware lifetime softcap** on cooking HP (`_COOKING_SOFTCAP_BY_FLOOR`) — diligent L100 cook lands ~139 cooking-HP.
- **All 12 family recipes + `basic_monster_stew` now define `tier_outcomes` 0–5**, and **family T5 grants a themed 60-turn buff** (`temp_power`). The missing-top-tier safety net in `_apply_tier_outcome` (degrade to highest defined tier, never silently to "ruined") stays.
- **Recipes-tab filter** (`get_available_compound_recipes`): only shows recipes with **≥2 distinct ingredient types**. `basic_monster_stew` (all-assorted) is intentionally excluded and reached via the **Single tab anchor** on assorted parts.
- **Single-tab cook consumes exactly ONE ingredient** (the 2026-06-04 bugfix). Compound cook consumes one inventory pop per list entry (duplicates = N copies). **Both honored by this design.**

---

## (A) Jerky-as-Survival-Food

### Design

Rename/recast `assorted_monster_parts` as **"Assorted Monster Jerky"** — a dried, shelf-stable strip that's *meant* to be eaten on the go. Eating it is **instant, no quiz, no poison**, restoring a **modest** amount of SP so the player can always stave off starvation by harvesting and snacking, even with zero cooking skill.

### Numbers (modest by design)

| Field | Today (raw assorted) | Proposed (jerky) |
|---|---|---|
| SP restored (eaten) | 5 | **12** |
| HP restored (eaten) | 0 | **0** (keep HP behind cooking) |
| Food-poison chance | 30% | **0%** (it's cured/dried) |

**Why 12 SP:** ~24 moves of runway per strip. With ~2 jerky per corpse, clearing a handful of monsters on a floor yields enough to never passively starve — but it's strictly worse than a cooked **Basic Stew** (T2 = 65 SP from 8 strips, i.e. ~8 SP/strip but with HP + max-HP/stat at higher tiers). So jerky is the *floor*, cooking is the *upgrade*. It deliberately gives **no HP and no max-HP/stat**, preserving every reason to cook.

> Tuning knob: if 12 feels too generous, 8–10 still clears "don't starve" (16–20 moves/strip). 12 is chosen so a *new* player isn't punished while learning the cooking loop.

### Data + code hook (smallest viable change)

The eat path already exists: Eat menu (`z`) → `eat_raw(player, ingredient)` for any `Ingredient`. Two surgical edits, both in `src/food_system.py:eat_raw`:

1. **Bump the universal SP** in `raw_sp_map`: `'universal': 5` → `'universal': 12`.
2. **Exempt jerky from the poison roll.** Today every raw bite rolls 30% poison. Jerky is cured, so it should never poison. Gate the poison roll on a flag rather than hardcoding the id:
   ```python
   # in eat_raw, before the poison roll:
   is_cured = getattr(ingredient, 'edible_safe', False) or ingredient.id == 'assorted_monster_parts'
   if not is_cured and random.random() < 0.30 and not player.has_effect('poison_resist'):
       ...poison...
   ```
3. **Flavor + data:** in `data/items/ingredient.json`, update the `assorted_monster_parts` entry:
   - `"name": "Assorted Monster Jerky"`
   - `"description": "Strips of mixed monster meat, salted and dried. Tough and gamey, but it keeps — and it keeps you alive."`
   - add `"edible_safe": true` (read by the `getattr` above; harmless to old saves).
   - **Optionally** surface a `"raw_sp"` field on the ingredient so the value is data-driven instead of living in `eat_raw`'s map (nice-to-have, see §D).

**Naming caution:** "Jerky" already appears as *recipe flavor* for some family/prime dishes (e.g. `family_humanoid` = "Humanoid Jerky", `Long-Pig Smoked Jerky`). Calling the universal part **"Assorted Monster Jerky"** does not collide (distinct id, distinct name) but if you'd prefer zero overlap, **"Assorted Monster Strips"** or **"Trail Jerky"** are clean alternates. Recommendation: keep "Assorted Monster Jerky" — it's the user's phrasing and reads well.

**No new item class, no new menu, no new state.** The Single-tab cook anchor on assorted parts (`basic_monster_stew`) and the Recipes tab are unaffected.

---

## (B) Richer Recipes — exact requirement numbers

**Principle:** raise *both* axes the user named — **more parts** (raw quantity) and **more variety** (distinct families/primes) — scaled so the recipe class signals the investment. Variety is the more interesting lever: requiring **2 family parts** means you must have harvested across *two different monster families* (or twice from one), turning a recipe into a small collection quest.

### Proposed requirement table

| Class | Today | **Proposed** | Slots (today→new) | What changed |
|---|---|---|---|---|
| **Basic stew** | `5 assorted` | **`8 assorted`** | 5 → **8** | Pure quantity; the no-skill fallback dish costs a real pile. |
| **Family roast** | `1 family + 3 assorted` | **`2 family + 4 assorted`** | 4 → **6** | +1 family (variety) +1 assorted. Must harvest the family twice (or two members). |
| **Prime dish** (514) | `1 prime + 1 family + 2 assorted` | **`1 prime + 2 family + 4 assorted`** | 4 → **7** | The bulk of the bank. +1 family (variety) +2 assorted (quantity). |
| **Dungeon-keyed** (29) | `1 special + 1 prime + 1 family + 1 assorted` | **`1 special + 1 prime + 2 family + 3 assorted`** | 4 → **7** | +1 family +2 assorted; keeps the foraged-terrain `special` identity. |
| **Master** (51, 2-monster) | varies (`~1 family + 3 prime`) | **normalize to `2 prime + 2 family + 3 assorted`** | 4 → **7** | Keep the dual-prime hook; add a 2nd family + assorted for heft. (The 1 outlier `4 prime` master can stay 4-prime + 3 assorted = 7.) |
| **Trophy** (boss, 13) | `1 trophy + 1 family + 3 assorted` | **`1 trophy + 2 family + 5 assorted`** | 5 → **8** | The permanent-power meal. Biggest spend; you've beaten a boss, now empty the larder. |

### What this feels like in play

- A **prime dish** now needs **1 prime (the T5 harvest jackpot) + 2 family parts (two harvests' worth) + 4 jerky (~2 corpses)** — roughly **3–4 successful harvests** of meaningful variety. That's "I went and collected the makings," not "I cooked the corpse I'm standing on."
- **Variety is enforced** by the `2 family` requirement: families stack within a family, so 2× `family_beast` is two beast harvests, but a player who's killed across families naturally has the spread. It rewards *exploring the bestiary*, which is thematically perfect for a "knowledge is power" roguelike.
- **Trophy meals** become the ceremonial capstone the permanent power deserves: 8 ingredients including the irreplaceable boss trophy.

### Engine compatibility (verified)

- `cook_compound_recipe` consumes **one inventory pop per list entry**, so listing `family_beast` twice consumes 2 copies — the higher counts "just work."
- All proposed compound recipes still have **≥2 distinct types**, so they remain in the **Recipes tab** (the `get_available_compound_recipes` filter is satisfied). `basic_monster_stew` stays all-assorted → stays on the **Single tab anchor**, unaffected by the filter.
- **`tier_outcomes` are untouched** — we change only the `ingredients` array. The recent family-T5 buff and the 0–5 outcome completeness are preserved verbatim.

---

## (C) Balance — keep it rich, not grindy

1. **Jerky covers the floor, so richer recipes are opt-in.** The single most important balance lever: because jerky reliably prevents starvation (§A), the higher recipe costs are **never a survival tax**. A player who hates cooking eats jerky and descends; a player who loves it invests parts for HP/stat/powers. This directly answers the user's "upgrade, not a tax" intent.
2. **Output ceiling unchanged → no power creep.** Per-floor caps (+5 max HP / +1 stat) and the lifetime cooking-HP softcap are **not touched**. We raise *input cost* only. Net effect: the same max power now costs more parts, so cooking *feels* like a project without inflating the curve. (Important: because the per-floor cap already limits you to ~1 meaningful HP/stat meal per floor, raising costs doesn't force *more* cooking — it makes the *one* meal you cook per floor feel earned.)
3. **Anti-grind guardrails:**
   - **Don't raise harvest difficulty or lower yields.** Acquisition stays as-is; we change the *recipe denominator*, not the *drop numerator*. Parts accumulate at today's rate.
   - **Keep assorted abundant.** Jerky (assorted) is the high-volume currency by design; the +assorted bumps are cheap to satisfy and mostly add "heft," while the +family bumps add the interesting variety pressure.
   - **Cap the trophy spend at 8.** Resist the urge to go higher — boss meals should be a satisfying hoard-dump, not a multi-floor farming chore.
   - **No new failure states.** Jerky removes the poison-trap; richer recipes don't add risk, only cost.
4. **Respect the family-T5 buff work.** Family recipes keep their 60-turn themed `temp_power` at T5; we only change their ingredient list (`1 family + 3 assorted` → `2 family + 4 assorted`). The buff is now slightly more earned, consistent with the overhaul's thesis.
5. **Playtest reachability note.** Per the project play-test rule: **jerky eating and basic/family recipe costs are easily reachable in a few minutes** — these need an in-person play-test (eat a jerky, confirm SP +12 and no poison; cook a Basic Stew, confirm it now wants 8 parts). **Prime/master/trophy cost changes are late-game / randomized** — those are validated by a **data-layer test** (load `recipes.json`, assert the new ingredient counts per class) rather than play, per the "play-test isn't realistic" clause.

---

## (D) Data-vs-Code change list & phasing

### Data changes (the bulk — `data/items/`)

| File | Change | Scope |
|---|---|---|
| `data/items/ingredient.json` | `assorted_monster_parts`: rename → "Assorted Monster Jerky", new description, add `"edible_safe": true` (and optionally `"raw_sp": 12`). | 1 entry |
| `data/items/recipes.json` | Rewrite the `ingredients` array per the §B table, keyed by `recipe_class` (and id-prefix for master/dungeon). **`tier_outcomes` left byte-for-byte unchanged.** | ~620 entries via a script |

A small offline migration script (in `data/`, not loaded at runtime — consistent with the existing generator-script convention) should:
- iterate recipes, branch on `recipe_class` / id-prefix,
- rebuild the `ingredients` list to the new composition (preserving the specific prime/trophy/family/special ids already present — only the *counts* of family/assorted change),
- write back with stable key order.

### Code changes (tiny — `src/`)

| File | Change | Lines |
|---|---|---|
| `src/food_system.py` | `eat_raw`: `universal` SP 5 → 12 (or read `ingredient.raw_sp`); add `edible_safe` poison exemption. | ~4 |
| `src/items.py` (optional) | `Ingredient.__init__`: load `self.edible_safe = defn.get('edible_safe', False)` and `self.raw_sp = defn.get('raw_sp', None)` so the data drives behavior. | ~2 |

**No changes** to menus, quiz engine, caps, `_apply_tier_outcome`, or `cook_compound_recipe`.

### Tests to add (`tests/`)

1. **Data-layer:** load `recipes.json`; assert each class matches the new composition counts (e.g. every `prime_*` recipe = 1 prime + 2 family + 4 assorted = 7 slots). Catches a botched migration.
2. **Pure-function (jerky):** call `eat_raw` on an `assorted_monster_parts` Ingredient with a mock player; assert SP +12 and **poison never applied** across many iterations (loop the RNG). Mirrors the existing food-system test style.
3. **Regression:** assert `get_available_compound_recipes` still surfaces a sample prime recipe when the player holds the (now larger) ingredient set, and that `basic_monster_stew` stays off the Recipes tab.

### Phasing

- **Phase 1 — Jerky (survival floor).** Ship §A alone: rename + 12 SP + poison exemption + tests. *This is independently shippable and immediately satisfies "eat to not starve."* **Play-test:** eat a jerky, confirm SP/no-poison.
- **Phase 2 — Richer basic/family recipes.** Apply §B to `basic` + `family` only (the cheap, reachable tiers). **Play-test:** cook a Basic Stew (wants 8) and a Family Roast (wants 2 family + 4 jerky); confirm the family-T5 buff still fires.
- **Phase 3 — Prime/dungeon/master/trophy.** Run the migration over the remaining ~600 recipes; validate with the data-layer test (no play-test needed — late-game/randomized). Commit.
- **Phase 4 — (optional) data-drive the raw-SP value** (`raw_sp` field) so future ingredient tuning is pure-data.

Each phase is a self-contained commit per the project's "commit after each working feature" rule.

---

## Open questions for the user

1. **Jerky SP = 12** the right "modest"? (8–10 is leaner; 12 is forgiving for new players. HP intentionally stays 0.)
2. **Prime dish at 7 slots (`1 prime + 2 family + 4 assorted`)** — does that feel like "a big deal" without tipping into grind? Easy to dial family to 1 or assorted to 3 if it's too steep.
3. **Trophy at 8 slots** — happy to make the boss meal the biggest spend, or keep it merely "large"?
4. Keep the name **"Assorted Monster Jerky"** (your phrasing) vs. "Assorted Monster Strips" to fully avoid the existing recipe-flavor "Jerky" usages?
