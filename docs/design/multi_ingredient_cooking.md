# Multi-Ingredient Cooking — Design Rules

**Date:** 2026-10-03 (locked)
**Reference:** `../../COOKING_EXPANSION_PLAN.md` for the strategic plan + current-state data.

---

## Scope

Expand the cooking system from 77 multi-ingredient recipes (65 two-ing + 12 three-ing + 0 four-ing + 0 five-ing) to ~315 (200 two-ing + 80 three-ing + 25 four-ing + 10 five-ing). The 537 single-ingredient recipes stay as the "easy daily cook" layer.

## Ingredient-count → bonus tier mapping

| Ing count | Fraction with PERMANENT bonus | Typical reward |
|---|---|---|
| 1 | ~3% (existing 14 T5 cooks only) | Unchanged |
| 2 | ~10% | `+1 stat` OR `+3 max_hp` OR narrow resist |
| 3 | ~50% | `+1 stat` OR `+5 max_hp` OR mid-tier resist |
| 4 | 100% | `+2 stat` OR `+10 max_hp` OR named resist |
| 5 | 100% | Two-slot legendary bonus (e.g. `+1 stat + resist`, `+5 max_hp + +1 WIS`, immunity + `carry_bonus`) |

## Hard caps (do not break)

- **No single recipe grants more than +2 to a single stat.** Period.
- **No immunity bigger than the tier-matched resist** for 4-ingredient. Immunities (permanent full damage block) are reserved for 5-ingredient legendary recipes.
- **SP soft-boundary floor preserved** — every recipe's SP output must be ≥ the raw-eat emergency floor for its tier so cooking is never worse than not cooking.
- **No duplicate ingredient-tuples.** A recipe is defined by its sorted ingredient-id tuple. Two recipes with the same tuple is a bug.

## Phasing is automatic

- Rely on each ingredient's `min_level` field. A recipe effectively unlocks at the max `min_level` of its ingredients.
- NO new `discovery_floor` or similar field. Phasing emerges from ingredient availability.
- Per-floor-band authoring agents must still enforce their band — don't author an F1-F10 recipe whose ingredients span F50+.

## Naming — mandatory

- Every recipe gets a **unique, fantastical name based on its ingredients**. Not generic ("Hearty Stew"). Evocative:
  - 2-ing: *"Troll-Hoof and Elderberry Pot"*, *"Ymir's-Breath Chowder"*
  - 3-ing: *"The Deep-Mother's Three-Flesh Ragout"*, *"Thrice-Blessed Golem Terrine"*
  - 4-ing: *"The Alchemist's Quartet of Fangs"*
  - 5-ing: *"Ragnarok's Last Feast"*, *"The Nine-World Soup of Yggdrasil"*
- The name must call out at least one ingredient (so a kid can read "Troll-Hoof" and think "I have one of those!"). No kennings so dense that the ingredient disappears.
- No duplicate names.

## Flavor text

- One sentence of cooking narration. Taste, smell, ritual, warning — anything evocative.
- Does NOT reveal the keyed outcome. ("Rich and heady" is fine. "Grants permanent STR +1" is a leak.)

## 5-ingredient legendary cadence

- **Exactly 10 legendary 5-ingredient recipes across the 100-floor run.** Not more. Scarcity is the point.
- Distribution: F51-F60: 2, F61-F70: 2, F71-F80: 2, F81-F90: 2, F91-F100: 2.
- Each legendary 5-ing recipe gets a mythic-tier name invoking its specific ingredient collection.

## Outcome archetypes

- Live in `data/items/cook_outcomes.json → outcomes`.
- New archetype IDs follow the convention: `t<tier>_combo_<theme>` (2-ing), `t<tier>_tri_<theme>` (3-ing), `t<tier>_quartet_<theme>` (4-ing), `t<tier>_mythic_<theme>` (5-ing).
- Preserve all existing 120 outcomes. APPEND only; never rewrite or delete.
- Field shape matches the existing outcomes (`id`, `tier`, `sp`, `hp`, `temp_power`, `temp_duration`, `stat_bump`, `permanent_power`, `max_hp_bump`, `archetype`, `flavor`).
- Field `permanent_power` ids must come from the known 15-id set (`petrify_immune`, `fire_immune`, `cold_immune`, `poison_immune`, `confuse_immune`, elemental resists, +stat permanent). Any new power_id requires a corresponding dispatch branch in `_apply_permanent_power` in `food_system.py`.

## Floor-band author assignments (10 parallel agents)

| Agent | Floor band | New 2-ing | New 3-ing | New 4-ing | New 5-ing | Total |
|---|---|---|---|---|---|---|
| 1 | F1-F10 | 40 | 0 | 0 | 0 | 40 |
| 2 | F11-F20 | 35 | 10 | 0 | 0 | 45 |
| 3 | F21-F30 | 25 | 15 | 0 | 0 | 40 |
| 4 | F31-F40 | 20 | 15 | 5 | 0 | 40 |
| 5 | F41-F50 | 15 | 10 | 5 | 0 | 30 |
| 6 | F51-F60 | 10 | 10 | 5 | 2 | 27 |
| 7 | F61-F70 | 10 | 10 | 5 | 2 | 27 |
| 8 | F71-F80 | 5 | 5 | 3 | 2 | 15 |
| 9 | F81-F90 | 5 | 5 | 2 | 2 | 14 |
| 10 | F91-F100 | 0 | 0 | 0 | 2 | 2 |
| **Totals** | | **165** (we already have 65) | **80** (we have 12) | **25** | **10** | **280 new** |

Wait — adding 165 2-ing recipes to the existing 65 gives us 230. Target was 200. We can either (a) drop 30 from the per-band schedule, or (b) accept 230 as the new total. Going with (b): more variety at no cost. Updated target total: ~335 multi-ingredient recipes (230 + 80 + 25 + 10) + existing 537 single = 872 total recipes.

## Write targets

- **Outcomes agent writes:** `data/items/cook_outcomes.json` (append-only).
- **Each floor-band agent writes:** `$CLAUDE_JOB_DIR/tmp/recipes_fXX.json` (intermediate — merged into `data/items/recipes.json` after all 10 complete).
- No agent touches `data/items/recipes.json` directly during Phase 2 to avoid write collisions.

## Validation gate (Phase 3)

Automated script checks:
1. Every recipe's `outcome_id` resolves to an entry in `cook_outcomes.json`.
2. Every recipe's `ingredients` list contains real ids in `ingredient.json`.
3. No duplicate sorted-ingredient-tuples across recipes (new OR existing).
4. Every multi-ingredient recipe's `max(min_level of ingredients)` falls in the authoring agent's floor band (±5 tolerance).
5. Permanent-bonus caps per phase respected (`+2 stat` max, no immunities outside 5-ing).
6. SP output ≥ raw-eat emergency floor for each outcome.

Any violation → log + reroute to a quick-fix Opus agent.

---

## User-approved decisions (locked 2026-10-03)

1. **Discovery mechanic:** rely on ingredient `min_level` alone. No new field.
2. **Legendary cadence:** exactly 10 five-ingredient recipes across the run.
3. **Permanent-bonus caps:** +2/stat max; immunities 5-ing-only.
4. **Naming style:** unique, fantastical names based on ingredients. One per recipe.
5. **Author strategy:** 10 parallel per-floor-band agents.
