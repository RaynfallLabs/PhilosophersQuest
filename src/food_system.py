import json
import math
import random
from paths import data_path

_INGREDIENT_PATH = data_path('data', 'items', 'ingredient.json')
_RECIPE_PATH     = data_path('data', 'items', 'recipes.json')
_PRIME_CUTS_PATH = data_path('data', 'items', 'prime_cuts.json')
_ingredient_cache: dict | None = None
_recipe_cache: dict | None = None
_prime_cuts_cache: dict | None = None

_STAT_LABELS = {
    'STR': 'strength', 'CON': 'constitution', 'DEX': 'dexterity',
    'INT': 'intelligence', 'WIS': 'wisdom',   'PER': 'perception',
}
_ALL_STATS    = list(_STAT_LABELS.keys())
_COMBAT_STATS = ['STR', 'CON']

# ----------------------------------------------------------------------
# Harvest + Cook — cadence rewritten 2026-09-01 (v2.6.1 harvest, v2.6.2 cook)
#
# Both actions now use ONE animal/cooking question, tiered to the target's
# power (corpse.harvest_tier for harvest, recipe_class for cook). Right
# answer = full tier-appropriate outcome. Wrong = ruined; the resource
# (corpse or ingredients) is consumed either way. No chain, no partial
# credit, no stun on failure. See [[feedback-flow-over-gradient]] and
# [[feedback-resource-loss-is-the-penalty]].
#
# The tier→outcome tables below still drive the reward SHAPE (what a T3
# monster yields vs a T5 one; what a family recipe gives vs a trophy).
# Only the CADENCE changed — from up-to-5 escalating Qs to a single one.
#
# Harvest outcome shape (per _harvest_outcome_for_tier):
#   T0: ruined — no ingredients (wrong-answer path only)
#   T1: 1x Assorted Monster Parts (universal)
#   T2: 2x Assorted Monster Parts
#   T3: +1x family ingredient (12 families)
#   T4: +1 more family (so 2x family total)
#   T5: +1x prime cut (unique to monster) OR trophy ingredient (boss-only)
#
# Cook outcome shape (per recipe's tier_outcomes; v3 always passes T5 on
# success and T0 on failure):
#   T5: full peak reward (SP + HP + max-HP + stat + temp/permanent power)
#   T0: ruined dish, ingredients consumed
# ----------------------------------------------------------------------

def _load_prime_cuts() -> dict:
    """Return the 527-entry prime_cuts.json keyed by monster_id."""
    global _prime_cuts_cache
    if _prime_cuts_cache is None:
        with open(_PRIME_CUTS_PATH, encoding='utf-8') as f:
            _prime_cuts_cache = json.load(f).get('primes', {})
    return _prime_cuts_cache


def _harvest_outcome_for_tier(tier: int, monster_id: str) -> list[str]:
    """v2.6.5 (2026-09-03): harvest yields exactly ONE ingredient — the
    monster's identifying prime cut (or trophy for bosses). Tier is used
    ONLY for the harvest quiz difficulty; the outcome is the same
    ingredient regardless of tier. tier=0 (ruined) -> empty list.

    Prior versions returned a cumulative T1-T5 stack of assorted +
    family + prime; that meant 87% of monsters never dropped their own
    prime (only T5 corpses reached the prime slot). See harvest audit
    2026-09-03 for the details of the redesign.
    """
    if tier <= 0:
        return []
    primes = _load_prime_cuts()
    prime_info = primes.get(monster_id)
    if not prime_info:
        # Defensive — monster has no prime_cut mapping. Nothing to harvest.
        return []
    is_trophy = bool(prime_info.get('is_trophy'))
    ing_id = f'{monster_id}_trophy' if is_trophy else f'{monster_id}_prime'
    return [ing_id]

# ------------------------------------------------------------------
# Potency-based cooking formulas (replaces tier lookup tables)
# Ingredient power comes from the source monster's min_level.
# Potency = sqrt(min_level) gives a ~10:1 range (L100 vs L1).
# Quiz ALWAYS starts at T1 regardless of ingredient.
# ------------------------------------------------------------------

SINGLE_MULT   = {1: 0.3, 2: 0.6, 3: 0.9, 4: 1.5, 5: 2.2}
COMPOUND_MULT = {1: 0.6, 2: 1.1, 3: 1.8, 4: 3.0, 5: 4.5}


def _potency(min_level: int) -> float:
    """Ingredient potency derived from source monster's min_level."""
    return math.sqrt(max(1, min_level))


def _single_max_hp(min_level: int, quality: int) -> int:
    """Permanent max HP from a single-ingredient cook."""
    if quality < 1:
        return 0
    return max(1, int(_potency(min_level) * SINGLE_MULT[quality]))


def _compound_max_hp(max_min_level: int, quality: int, n_ingredients: int = 2) -> int:
    """Permanent max HP from a compound recipe. Potency = highest ingredient level."""
    if quality < 1:
        return 0
    ing_bonus = 1.0 + 0.15 * (n_ingredients - 2)
    return max(1, int(_potency(max_min_level) * COMPOUND_MULT[quality] * ing_bonus))


def _cooking_heal(min_level: int, quality: int) -> int:
    """Immediate HP restored from eating the cooked meal."""
    if quality < 1:
        return 0
    return max(1, int(_potency(min_level) * quality * 1.5))


def _cooking_sp(min_level: int, quality: int, raw_sp: int = 10) -> int:
    """SP restored from eating the cooked meal.
    Q1 = raw SP (same as eating raw, but no poisoning risk).
    Q2-Q5 scale upward so cooking skill is always rewarded."""
    if quality < 1:
        return 0
    formula = int(5 * _potency(min_level) * quality)
    # Ensure Q1 >= raw, then each quality step adds at least 15% over raw
    scaled = int(raw_sp * (1.0 + 0.15 * (quality - 1)))
    return max(formula, scaled)


# ------------------------------------------------------------------
# Data loading
# ------------------------------------------------------------------

def _raw_ingredients() -> dict:
    global _ingredient_cache
    if _ingredient_cache is None:
        with open(_INGREDIENT_PATH, encoding='utf-8') as f:
            _ingredient_cache = json.load(f)
    return _ingredient_cache


def _raw_recipes() -> dict:
    global _recipe_cache
    if _recipe_cache is None:
        with open(_RECIPE_PATH, encoding='utf-8') as f:
            _recipe_cache = json.load(f)
    return _recipe_cache


# ------------------------------------------------------------------
# Compound recipe helpers
# ------------------------------------------------------------------

def get_available_compound_recipes(inventory: list) -> list[dict]:
    """Return compound recipe dicts where the player has ALL required
    ingredients AND the recipe combines >=2 distinct ingredient TYPES.

    Solo cooks (recipes whose ingredients list is one type repeated, e.g.
    basic_monster_stew = 5x assorted_monster_parts) are excluded — they
    are reachable from the Single tab via _find_recipe_for_ingredient
    on the canonical anchor ingredient. The Recipes tab is reserved for
    multi-type combinations per the 2026-06-01 cooking-menu UX contract.
    """
    from items import Ingredient
    held_ids = {item.id for item in inventory if isinstance(item, Ingredient)}
    out = []
    for rid, rdef in _raw_recipes().items():
        ings = rdef.get('ingredients', [])
        if not ings or len(set(ings)) < 2:
            continue
        if all(ing in held_ids for ing in ings):
            out.append({'id': rid, **rdef})
    return out


def get_recipes_for_ingredient(ingredient_id: str) -> list[dict]:
    """Return all compound recipes that list this ingredient_id."""
    return [
        {'id': rid, **rdef}
        for rid, rdef in _raw_recipes().items()
        if ingredient_id in rdef.get('ingredients', [])
    ]


# Map redesign-friendly temp_power names to canonical status_effects entries.
# Names on the LEFT come from prime_cuts.json + recipes.json; names on the
# RIGHT are real status effects in src/status_effects.py:EFFECT_INFO that
# have actual consumers in combat/get_ac/etc.
_TEMP_POWER_REMAP = {
    'acid_resist':           'shock_resist',      # closest tier-1 elemental resist
    'berserk_short':         'berserk',
    'bleeding_resist':       'regenerating',      # regen counters bleed effectively
    'blessed_status':        'blessed',
    'charm_resist':          'save_guard_WIS',    # mind ward (WIS save)
    'confused_resist':       'save_guard_WIS',    # mind ward (WIS save)
    'cursed_resist':         'magic_resist',
    'damage_resist_phys':    'shielded',
    'detect_magic':          'searching',         # close enough — surfaces info
    'detect_monster':        'warning',
    'drain_heals_self_temp': 'drain_resist',      # closest mechanical match
    'feared_resist':         'save_guard_WIS',    # mind ward (WIS save)
    'gold_drip':             'identify_sight',    # quirky proxy — no real "gold/turn" buff
    'hallucinate_resist':    'save_guard_WIS',    # mind ward (WIS save)
    'lightning_resist':      'shock_resist',
    'mp_regen':              'brilliance',        # brilliance boosts mental stats
    'night_vision':          'dark_vision',
    'paralyze_resist':       'save_guard_CON',    # body ward (CON save)
    'passive_regen':         'regenerating',
    'petrify_resist':        'save_guard_CON',    # body ward (CON save)
    'quiz_timer_bonus':      'brilliance',
    'rust_proof':            'shielded',
    'silenced_resist':       'magic_resist',      # silence isn't a SAVE_STAT effect
    'stealth_in_dark':       'invisible',
    'stunned_resist':        'save_guard_CON',    # body ward (CON save)
    'tactics_buff':          'crit_buff',
}


def _resolve_temp_power(name: str) -> str:
    """Resolve a redesign-friendly temp_power name to the canonical status
    effect. Returns the input unchanged if already canonical."""
    return _TEMP_POWER_REMAP.get(name, name)


_OUTCOMES_CACHE: dict | None = None


def _load_outcomes() -> dict:
    """Load and cache the cook v2.6.4 outcome archetype catalog."""
    global _OUTCOMES_CACHE
    if _OUTCOMES_CACHE is None:
        from paths import data_path
        p = data_path('data', 'items', 'cook_outcomes.json')
        with open(p, encoding='utf-8') as f:
            _OUTCOMES_CACHE = json.load(f).get('outcomes', {})
    return _OUTCOMES_CACHE


def _apply_recipe_outcome(player, recipe: dict, ruined: bool = False) -> list[str]:
    """v2.6.4 cook dispatch — one recipe -> one outcome archetype.

    Recipe carries an `outcome_id` referencing data/items/cook_outcomes.json.
    Right answer -> apply the referenced outcome (recovery + optional buff +
    optional +max HP + optional +stat + optional permanent_power). Wrong ->
    ingredients already consumed, one message, no reward.

    Persephone's Descent quirk (`persephone_active`): even a ruined prep
    still yields half the recovery (SP + HP only) -- "the seed still returns
    from the dark". Buffs, +max HP, +stat, and permanent_power are lost.
    """
    meal_name = recipe.get('name', 'mysterious dish')
    if ruined:
        if getattr(player, 'quirk_progress', {}).get('persephone_active'):
            outcome_id = recipe.get('outcome_id')
            outcome = _load_outcomes().get(outcome_id) or {}
            sp = int(outcome.get('sp', 0)) // 2
            hp = int(outcome.get('hp', 0)) // 2
            msg = [f"You ruin the preparation of {meal_name}, "
                   f"but Persephone's grace saves the seed."]
            if sp > 0:
                player.restore_sp(sp)
            if hp > 0:
                player.restore_hp(hp)
            if sp > 0 or hp > 0:
                bits = []
                if sp > 0: bits.append(f"+{sp} SP")
                if hp > 0: bits.append(f"+{hp} HP")
                msg.append("You salvage what you can: " + ", ".join(bits) + ".")
            return msg
        return [f"You ruin the preparation. The {meal_name} is wasted."]
    outcome_id = recipe.get('outcome_id')
    outcome = _load_outcomes().get(outcome_id)
    if outcome is None:
        return [f"You prepare {meal_name}, but the effect eludes you (unknown outcome {outcome_id!r})."]
    return _apply_outcome_body(player, recipe, outcome)


def _apply_outcome_body(player, recipe: dict, outcome: dict) -> list[str]:
    """Apply the mechanical body of an outcome archetype to the player.
    Returns a list of user-facing messages (first line is the meal name)."""
    meal_name = recipe.get('name', 'mysterious dish')
    messages: list[str] = [f"You prepare {meal_name}."]

    # SP + HP restore
    sp = int(outcome.get('sp', 0))
    if sp > 0:
        player.restore_sp(sp)
    hp = int(outcome.get('hp', 0))
    if hp > 0:
        player.restore_hp(hp)
    if sp > 0 or hp > 0:
        bits = []
        if sp > 0: bits.append(f"+{sp} SP")
        if hp > 0: bits.append(f"+{hp} HP")
        messages.append("You eat it: " + ", ".join(bits) + ".")

    # +max HP (per-floor softcap unless bypassed)
    max_hp_bonus = int(outcome.get('max_hp_bonus', 0))
    if max_hp_bonus > 0:
        bypass = bool(outcome.get('permanent_power'))
        if hasattr(player, 'try_apply_cook_hp_gain'):
            applied = player.try_apply_cook_hp_gain(max_hp_bonus, bypass=bypass)
        else:
            applied = max_hp_bonus
            player.increase_max_hp(applied, from_cooking=True)
        if applied > 0:
            messages.append(f"The meal fortifies you permanently. (+{applied} max HP)")
        elif not bypass:
            messages.append("You feel sated, but your body is already full of nourishment this floor.")

    # +1 stat (per-floor softcap unless bypassed)
    stat_grant_amount = int(outcome.get('stat_grant', 0))
    if stat_grant_amount > 0:
        bypass = bool(outcome.get('permanent_power'))
        stat = outcome.get('stat_grant_default') or 'STR'
        if hasattr(player, 'try_apply_cook_stat_gain'):
            applied = player.try_apply_cook_stat_gain(stat, stat_grant_amount, bypass=bypass)
        else:
            applied = stat_grant_amount
            player.apply_stat_bonus(stat, applied)
        if applied > 0:
            messages.append(f"Your {_STAT_LABELS.get(stat, stat)} increases by {applied}!")

    # Temp power (status effect)
    tp = outcome.get('temp_power')
    if tp:
        canonical = _resolve_temp_power(tp)
        try:
            player.add_effect(canonical, int(outcome.get('temp_duration', 60)))
            # save_guard_* wards carry a magnitude in player._save_guard;
            # save_bonus_for() reads it while the companion status is active.
            if canonical.startswith('save_guard_'):
                cat = canonical[len('save_guard_'):]  # 'CON'|'WIS'|'DEX'|'all'
                amount = min(3, int(outcome.get('temp_amount', 2) or 2))
                if not hasattr(player, '_save_guard') or player._save_guard is None:
                    player._save_guard = {}
                player._save_guard[cat] = amount
        except Exception:
            pass
        messages.append(f"A short {canonical.replace('_', ' ')} lingers.")

    # Class-ascension outcomes (four boss trophies at floors 20/40/60/80):
    # emit the signal INSTEAD of firing the permanent_power directly; the
    # cook caller opens the Ascension picker and the class node applies
    # the power. See test_class_ascension.
    if outcome.get('class_ascension'):
        messages.append('_class_ascension')
        return messages

    # Permanent power (non-ascension trophy)
    perm = outcome.get('permanent_power')
    if perm:
        # Fake a "recipe with permanent_power" shape so _apply_permanent_power
        # (unchanged from v2.6.3) still works.
        fake_recipe = dict(recipe)
        fake_recipe['permanent_power'] = perm
        fake_recipe['permanent_desc'] = outcome.get('permanent_desc', '')
        applied_msg = _apply_permanent_power(player, perm, fake_recipe)
        if applied_msg:
            messages.append(applied_msg)

    return messages


# Legacy shim: some code paths still reference _apply_tier_outcome
def _apply_tier_outcome(player, recipe: dict, tier: int) -> list[str]:
    """LEGACY (pre-v2.6.4). Routes to _apply_recipe_outcome.
    tier=0 -> ruined, anything else -> normal outcome (v2.6.4 doesn't do
    partial tiers)."""
    return _apply_recipe_outcome(player, recipe, ruined=(tier == 0))


# Permanent-power dispatcher for trophy recipes
def _apply_permanent_power(player, power_id: str, recipe: dict) -> str:
    """Apply a permanent-power trophy effect. Returns a flavor message."""
    desc = recipe.get('permanent_desc', '')
    # Each power_id maps to a concrete mutation
    if power_id == 'all_stats_plus_1':
        # Abaddon's apotheosis: every stat permanently +1
        for s in _ALL_STATS:
            player.apply_stat_bonus(s, 1)
        return ("APOTHEOSIS — every stat permanently +1. "
                + (desc or "The dungeon recognizes you."))
    elif power_id == 'plus_3_str':
        player.apply_stat_bonus('STR', 3)
        return "Permanent +3 STR. " + (desc or "")
    elif power_id == 'plus_2_con_petrify_immune':
        player.apply_stat_bonus('CON', 2)
        # Petrify immunity as a permanent status effect
        try: player.add_effect('petrify_immune', -1)
        except Exception: pass
        return "Permanent +2 CON, immunity to petrification. " + (desc or "")
    elif power_id == 'plus_2_wis_auto_reveal_secret_doors':
        player.apply_stat_bonus('WIS', 2)
        try: player.add_effect('auto_reveal_secret_3', -1)
        except Exception: pass
        return "Permanent +2 WIS, secret doors revealed nearby. " + (desc or "")
    elif power_id == 'fire_immunity':
        try: player.add_effect('fire_immune', -1)
        except Exception: pass
        return "Permanent fire immunity. " + (desc or "")
    elif power_id == 'cold_immunity':
        try: player.add_effect('cold_immune', -1)
        except Exception: pass
        return "Permanent cold immunity. " + (desc or "")
    elif power_id == 'petrify_immunity':
        try: player.add_effect('petrify_immune', -1)
        except Exception: pass
        return "Permanent petrification immunity. " + (desc or "")
    elif power_id == 'chromatic_resist_all':
        for elt in ('fire_resist', 'cold_resist', 'shock_resist',
                    'poison_resist', 'acid_resist'):
            try: player.add_effect(elt, -1)
            except Exception: pass
        return "Permanent 25% resist to all chromatic elements. " + (desc or "")
    elif power_id == 'one_time_death_save':
        player._asmodeus_pact = True  # consumed by player.is_dead() check
        return "The Pact is signed. The next death will not claim you. " + (desc or "")
    elif power_id == 'revive_once_at_half_hp':
        player._green_knight_revive = True
        return "Once per run, when you die, you return at half HP. " + (desc or "")
    elif power_id == 'max_hp_per_floor_descent':
        player._fafnir_per_descent_hp = 2
        return "+2 max HP each new floor you descend. " + (desc or "")
    elif power_id == 'max_mp_per_floor_descent_and_poison_immunity':
        player._nidhogg_per_descent_mp = 2
        try: player.add_effect('poison_immune', -1)
        except Exception: pass
        return "+2 max MP per descent + permanent poison immunity. " + (desc or "")
    elif power_id == 'lifesteal_5pct_on_melee':
        player._blood_archon_lifesteal = 0.05
        return "+5% lifesteal on all melee attacks. " + (desc or "")
    elif power_id == 'plus_2_str_confuse_immune':
        # Asterion (v2.6.4 cook redesign): the Minotaur's cunning + navigation
        player.apply_stat_bonus('STR', 2)
        try: player.add_effect('confuse_immune', -1)
        except Exception: pass
        return "Permanent +2 STR, immunity to confusion. " + (desc or "")
    return desc or f"You feel a permanent change ({power_id})."


def _recipe_quiz_tier(recipe: dict) -> int:
    """Cook v3 Q tier — the outcome's tier is the quiz difficulty.

    v2.6.4 (2026-09-02) simplification: each recipe references an outcome
    archetype (`outcome_id`), and the outcome carries its own tier. The
    old recipe_class -> tier map is retired.
    """
    outcome_id = recipe.get('outcome_id')
    if outcome_id:
        o = _load_outcomes().get(outcome_id)
        if o:
            return max(1, min(5, int(o.get('tier', 3))))
    # Legacy fallback (old-schema recipes with recipe_class)
    legacy = {'family': 2, 'prime': 3, 'master_prime': 4,
              'trophy': 5, 'dungeon_keyed': 5}
    return legacy.get(recipe.get('recipe_class'), 3)


def cook_compound_recipe(player, recipe: dict, inventory: list, quiz_engine, on_complete):
    """One cooking question at the recipe's derived tier. Right = full
    peak outcome for that recipe (T5-defined block); wrong = ruined,
    ingredients consumed either way. No chain, no partial credit — see
    [[feedback-flow-over-gradient]] + [[feedback-resource-loss-is-the-penalty]].
    """
    from items import Ingredient

    # Consume required ingredients up-front (one inventory pop per ingredient
    # listing — duplicates in the list mean we need that many copies).
    needed = list(recipe.get('ingredients', []))
    for ing_id in needed:
        for item in list(inventory):
            if isinstance(item, Ingredient) and item.id == ing_id:
                player.remove_from_inventory(item)
                break

    def _callback(result):
        messages = _apply_recipe_outcome(player, recipe,
                                         ruined=not getattr(result, 'success', False))
        on_complete(messages)

    quiz_engine.start_quiz(
        mode='threshold',
        subject='cooking',
        tier=_recipe_quiz_tier(recipe),
        callback=_callback,
        threshold=1,
        total_qs=1,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('cooking'),
        base_seconds=player.get_quiz_timer('cooking'),
    )


def load_ingredient_for(ingredient_id: str):
    """Return a fresh Ingredient instance for ingredient_id, or None if unknown."""
    from items import Ingredient
    raw = _raw_ingredients()
    if ingredient_id not in raw:
        return None
    defn = {**raw[ingredient_id], 'id': ingredient_id, 'item_class': 'ingredient'}
    return Ingredient(defn)


# ------------------------------------------------------------------
# Harvest
# ------------------------------------------------------------------

def harvest_corpse(player, corpse, quiz_engine, on_complete, extra_seconds: int = 0):
    """Animal one-question harvest, tier scaled to the corpse's harvest_tier.

    ONE animal question at the corpse's harvest_tier (1-5). Right = the
    corpse yields its full harvest for that tier (see
    `_harvest_outcome_for_tier`). Wrong = corpse ruined, no ingredients.
    No chain, no partial credit, no stun on failure — losing the corpse
    IS the cost. See [[feedback-flow-over-gradient]] +
    [[feedback-resource-loss-is-the-penalty]].

    on_complete(ingredients_list, message: str) is called when the quiz ends.
    """
    monster_id = getattr(corpse, 'monster_id', '')
    ht = int(getattr(corpse, 'harvest_tier', 1) or 0)
    tier = max(1, min(5, ht)) if ht > 0 else 1

    def _callback(result):
        if getattr(result, 'success', False):
            ingredient_ids = _harvest_outcome_for_tier(tier, monster_id)
            ingredients = [ing for ing_id in ingredient_ids
                           if (ing := load_ingredient_for(ing_id)) is not None]
            counts: dict[str, int] = {}
            for ing in ingredients:
                counts[ing.name] = counts.get(ing.name, 0) + 1
            parts = [f"{c}x {n}" if c > 1 else n for n, c in counts.items()]
            msg = (f"You harvest the {corpse.name} (T{tier}/5): "
                   f"{', '.join(parts)}." if parts
                   else f"You harvest the {corpse.name}, but it yields nothing usable.")
            on_complete(ingredients, msg)
        else:
            on_complete([], f"You botch the harvest. The {corpse.name} is ruined.")

    _player_extra = getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('animal')
    quiz_engine.start_quiz(
        mode='threshold',
        subject='animal',
        tier=tier,
        callback=_callback,
        threshold=1,
        total_qs=1,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=_player_extra + extra_seconds,
        base_seconds=player.get_quiz_timer('animal'),
    )


# ------------------------------------------------------------------
# Cooking
# ------------------------------------------------------------------

def _find_recipe_for_ingredient(ingredient) -> dict | None:
    """Locate the canonical recipe that uses this ingredient as its anchor.

    Priority order:
      1. Trophy recipe (if ingredient is a trophy)
      2. Prime recipe matching this monster (if prime)
      3. Family recipe matching this ingredient's family (if family-tier)
      4. Basic recipe (for assorted_monster_parts)
    Returns the recipe dict (with 'id' key set) or None.
    """
    recipes = _raw_recipes()
    iid = ingredient.id
    # Trophy: recipe id is `trophy_{monster}_recipe`
    if iid.endswith('_trophy'):
        monster_id = iid[:-len('_trophy')]
        rid = f'trophy_{monster_id}_recipe'
        if rid in recipes:
            return {'id': rid, **recipes[rid]}
    # Prime: recipe id is `prime_{monster}_recipe`
    if iid.endswith('_prime'):
        monster_id = iid[:-len('_prime')]
        rid = f'prime_{monster_id}_recipe'
        if rid in recipes:
            return {'id': rid, **recipes[rid]}
    # Family ingredient: recipe id is `family_{fam}_recipe`
    if iid.startswith('family_'):
        rid = f'{iid}_recipe'
        if rid in recipes:
            return {'id': rid, **recipes[rid]}
    # Universal: basic_monster_stew
    if iid == 'assorted_monster_parts':
        if 'basic_monster_stew' in recipes:
            return {'id': 'basic_monster_stew', **recipes['basic_monster_stew']}
    return None


def cook_ingredient(player, ingredient, quiz_engine, on_complete, max_chain: int = 5):
    """Cook the ONE selected ingredient (the Single tab).

    The caller (`Game._cook_item`) has ALREADY removed that single ingredient
    from inventory, so this consumes nothing further — it just runs the cooking
    quiz and applies the canonical recipe's tier outcome.

    BUGFIX 2026-06-04: previously this delegated to `cook_compound_recipe`, which
    RE-consumed the canonical recipe's full ingredient list (e.g.
    basic_monster_stew lists assorted_monster_parts x5). Combined with the
    caller's own removal, cooking a single part could devour an entire stack.
    Single-tab cooking now costs exactly one ingredient — the one you picked.
    """
    recipe = _find_recipe_for_ingredient(ingredient)
    if recipe is None:
        on_complete([f"You don't know what to do with the {ingredient.name}."])
        return

    def _callback(result):
        messages = _apply_recipe_outcome(player, recipe,
                                         ruined=not getattr(result, 'success', False))
        on_complete(messages)

    quiz_engine.start_quiz(
        mode='threshold',
        subject='cooking',
        tier=_recipe_quiz_tier(recipe),
        callback=_callback,
        threshold=1,
        total_qs=1,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('cooking'),
        base_seconds=player.get_quiz_timer('cooking'),
    )


def _apply_bonus(player, recipe) -> list[str]:
    bonus_type   = recipe.get('bonus_type', 'none')
    bonus_amount = int(recipe.get('bonus_amount', 0))
    messages     = []

    def _grant(stat: str, amt: int):
        """Route cookable stat bonuses through the floor-softcap path.
        Returns the actual amount applied (after diminishing returns).

        Falls back to apply_stat_bonus if the player doesn't yet have the
        cooking-cap method (old saves, harness mocks)."""
        if hasattr(player, 'apply_cooking_stat_bonus'):
            return player.apply_cooking_stat_bonus(stat, amt)
        player.apply_stat_bonus(stat, amt)
        return amt

    if bonus_type == 'none' or bonus_amount == 0:
        pass
    elif bonus_type == 'random_stat':
        stat = random.choice(_ALL_STATS)
        applied = _grant(stat, bonus_amount)
        if applied > 0:
            messages.append(f"Your {_STAT_LABELS[stat]} increases by {applied}!")
        else:
            messages.append(f"Your {_STAT_LABELS[stat]} resists further growth.")
    elif bonus_type == 'combat_stat':
        stat = random.choice(_COMBAT_STATS)
        applied = _grant(stat, bonus_amount)
        if applied > 0:
            messages.append(f"Your {_STAT_LABELS[stat]} increases by {applied}!")
        else:
            messages.append(f"Your {_STAT_LABELS[stat]} resists further growth.")
    elif bonus_type == 'two_stats':
        chosen = random.sample(_ALL_STATS, 2)
        any_gained = False
        for stat in chosen:
            applied = _grant(stat, bonus_amount)
            if applied > 0:
                messages.append(f"Your {_STAT_LABELS[stat]} increases by {applied}!")
                any_gained = True
        if not any_gained:
            messages.append("The dish is satisfying, but your body resists further change.")
    elif bonus_type == 'all_stats':
        any_gained = False
        for stat in _ALL_STATS:
            applied = _grant(stat, bonus_amount)
            if applied > 0:
                any_gained = True
        if any_gained:
            messages.append("A glow spreads — most of your stats edge upward.")
        else:
            messages.append("Your body resists further change. The dish is filling, no more.")
    elif bonus_type == 'stat':
        stat = recipe.get('bonus_stat', '')
        if stat in _STAT_LABELS:
            applied = _grant(stat, bonus_amount)
            if applied > 0:
                messages.append(f"Your {_STAT_LABELS[stat]} increases by {applied}!")
            else:
                messages.append(f"Your {_STAT_LABELS[stat]} cannot grow further from food.")
    elif bonus_type == 'status':
        effect = recipe.get('bonus_effect', '')
        if effect:
            player.add_effect(effect, bonus_amount)
            messages.append(f"You feel a {effect.replace('_', ' ')} effect for {bonus_amount} turns!")

    return messages


# ------------------------------------------------------------------
# Eating
# ------------------------------------------------------------------

def eat_food(player, food_item) -> list[str]:
    """
    Directly consume a Food item. Returns list of messages.
    Restores SP and optionally HP; may apply a bonus.
    """
    messages = []
    sp = food_item.sp_restore
    hp = food_item.hp_restore

    player.restore_sp(sp)
    messages.append(f"You eat the {food_item.name}. ({sp} SP restored)")

    if hp > 0:
        player.restore_hp(hp)
        messages.append(f"The food soothes your wounds. (+{hp} HP)")

    bonus_recipe = {
        'bonus_type':   food_item.bonus_type,
        'bonus_stat':   food_item.bonus_stat,
        'bonus_effect': food_item.bonus_effect,
        'bonus_amount': food_item.bonus_amount,
    }
    messages.extend(_apply_bonus(player, bonus_recipe))
    return messages


def drink_potion(player, potion) -> list[str]:
    """
    Consume a Potion. Returns a list of message strings.
    No quiz required. Effect applied immediately.
    """
    from dice import roll as roll_dice

    effect   = potion.effect
    power    = potion.power
    duration = potion.duration
    messages = []
    buc      = getattr(potion, 'buc', 'uncursed')

    # --- BUC multipliers ---
    # Healing: blessed ×1.5, cursed ×0.5
    # Buff duration: blessed ×1.5, cursed ×0.5
    # Harmful effects: blessed = blocked, cursed = duration ×1.5
    # Stat drains: blessed = no drain, cursed = drain ×2
    _heal_mult = 1.5 if buc == 'blessed' else (0.5 if buc == 'cursed' else 1.0)
    _buff_mult = 1.5 if buc == 'blessed' else (0.5 if buc == 'cursed' else 1.0)
    _harm_mult = 0.0 if buc == 'blessed' else (1.5 if buc == 'cursed' else 1.0)

    # --- Binary-effect potions: magnitude is meaningless (a teleport either
    # fires or it doesn't), so BUC acts on RELIABILITY, not size:
    #   blessed -> chance the dose isn't used up (_preserve; the quaff
    #              caller re-adds a preserved potion to inventory)
    #   cursed  -> chance the magic fails outright (_fizzle)
    _BINARY_EFFECTS = {'teleport', 'cure_poison', 'cure_disease', 'cure_all',
                       'restore_str', 'gain_level'}
    _is_binary = effect in _BINARY_EFFECTS
    _preserve_chance = 0.0
    _fizzle = False
    if _is_binary:
        if buc == 'blessed':
            _preserve_chance += 0.25
        elif buc == 'cursed':
            _fizzle = roll_dice('1d4') == 1

    # --- Identification on use ---
    potion.identified = True

    if _is_binary and _fizzle:
        messages.append("The cursed potion curdles on your tongue -- its magic fails entirely.")
        return messages

    if effect == 'heal':
        amt = int((roll_dice(power) if power else 10) * _heal_mult)
        player.restore_hp(amt)
        messages.append(f"Warmth floods through you. (+{amt} HP)")

    elif effect == 'extra_heal':
        amt = int((roll_dice(power) if power else 25) * _heal_mult)
        player.restore_hp(amt)
        messages.append(f"Deep wounds knit closed with startling speed. (+{amt} HP)")

    elif effect == 'full_heal':
        # Blessed full-healing scours away ALL debuffs FIRST, so a
        # heal-blocking debuff (heal_blocked / diseased) can't stop the heal that
        # follows. Order matters: restore_hp is a no-op while heal_blocked, so the
        # cleanse must run before it -- otherwise you'd be cured but still at 1 HP.
        cleared = []
        if buc == 'blessed':
            from status_effects import DEBUFFS
            cleared = [d.replace('_', ' ') for d in list(DEBUFFS)
                       if player.status_effects.pop(d, None) is not None]
        if buc == 'cursed':
            amt = int((player.max_hp - player.hp) * 0.5)
        else:
            amt = player.max_hp - player.hp
        player.restore_hp(amt)
        messages.append("Every wound closes. You feel completely whole.")
        if cleared:
            messages.append(f"The draught also burns away: {', '.join(cleared)}.")

    elif effect == 'restore_sp':
        amt = int((roll_dice(power) if power else 50) * _heal_mult)
        player.restore_sp(amt)
        messages.append(f"Stamina surges back into your limbs. (+{amt} SP)")

    elif effect == 'cure_poison':
        removed = player.status_effects.pop('poisoned', None)
        if removed is not None:
            messages.append("The poison is purged from your blood.")
        else:
            messages.append("You feel briefly nauseous -- nothing to cure.")

    elif effect == 'cure_disease':
        removed = player.status_effects.pop('diseased', None)
        if removed is not None:
            messages.append("The disease burns away. You feel yourself recovering.")
        else:
            messages.append("You feel a sterile flush -- nothing to cure.")

    elif effect == 'cure_all':
        cured = []
        from status_effects import DEBUFFS
        for debuff in list(DEBUFFS):
            if player.status_effects.pop(debuff, None) is not None:
                cured.append(debuff.replace('_', ' '))
        if cured:
            messages.append(f"Silver fire scours your body. Cured: {', '.join(cured)}.")
        else:
            messages.append("You feel pristine -- nothing to cure.")

    elif effect == 'haste':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('hasted', dur)
        messages.append(f"The world slows around you. You are Hasted ({dur} turns).")

    elif effect == 'invisibility':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('invisible', dur)
        messages.append(f"You fade from sight. Invisible ({dur} turns).")

    elif effect == 'regeneration':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('regenerating', dur)
        messages.append(f"You feel an uncanny resilience -- Regenerating ({dur} turns).")

    elif effect == 'heroism':
        dur = max(1, int(duration * _buff_mult))
        already_active = player.has_effect('heroism')
        player.add_effect('heroism', dur)
        if not already_active:
            player.apply_stat_bonus('STR', 2)
            messages.append(f"Surging strength fills your limbs! STR +2, Heroic ({dur} turns).")
        else:
            messages.append(f"The heroic surge is renewed ({dur} turns).")

    elif effect == 'brilliance':
        dur = max(1, int(duration * _buff_mult))
        already_active = player.has_effect('brilliance')
        player.add_effect('brilliance', dur)
        if not already_active:
            player.apply_stat_bonus('INT', 1)
            player.apply_stat_bonus('WIS', 1)
            messages.append(f"Your mind blazes with clarity! INT +1, WIS +1, Brilliant ({dur} turns).")
        else:
            messages.append(f"Your mental clarity is renewed ({dur} turns).")

    elif effect == 'levitation':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('levitating', dur)
        messages.append(f"Your feet leave the ground. Levitating ({dur} turns).")

    elif effect == 'restore_str':
        # Restore STR to base value (undoes disease drain)
        base_str = getattr(player, '_base_STR', player.STR)
        loss = base_str - player.STR
        if loss > 0:
            player.apply_stat_bonus('STR', loss)
            messages.append(f"Strength floods back into your muscles. STR +{loss}.")
        else:
            messages.append("Your strength is already at its peak.")

    elif effect == 'gain_level':
        # Signal to main.py to ascend one floor
        messages.append("_gain_level")

    elif effect == 'confusion':
        if _harm_mult == 0.0:
            messages.append("You feel briefly dizzy -- your blessed constitution resists.")
        else:
            from status_effects import apply_debuff_with_save
            _, msg = apply_debuff_with_save(
                player, 'confused', max(1, int(duration * _harm_mult)), dc=13)
            if msg:
                messages.append(msg)

    elif effect == 'blindness':
        if _harm_mult == 0.0:
            messages.append("Your eyes water briefly -- your blessed constitution resists.")
        else:
            applied = player.add_effect('blinded', max(1, int(duration * _harm_mult)))
            if applied:
                messages.append("Darkness closes in! You are Blinded.")
            else:
                messages.append("Your eyes water -- nothing happens.")

    elif effect == 'poison':
        if _harm_mult == 0.0:
            messages.append("You feel fine -- your blessed constitution purges the poison.")
        else:
            applied = player.add_effect('poisoned', max(1, int(20 * _harm_mult)))
            if applied:
                messages.append("You feel violently ill. You are Poisoned!")
            else:
                messages.append("You feel fine -- your body resists the poison.")

    elif effect == 'paralysis':
        if _harm_mult == 0.0:
            messages.append("A brief stiffness passes -- your blessed constitution resists.")
        else:
            from status_effects import apply_debuff_with_save
            _, msg = apply_debuff_with_save(
                player, 'paralyzed', max(1, int(duration * _harm_mult)), dc=13)
            if msg:
                messages.append(msg)

    elif effect == 'hallucination':
        if _harm_mult == 0.0:
            messages.append("You feel briefly strange -- your blessed constitution resists.")
        else:
            applied = player.add_effect('hallucinating', max(1, int(duration * _harm_mult)))
            if applied:
                messages.append("The walls breathe. The floor shifts. You are Hallucinating!")
            else:
                messages.append("You feel briefly strange -- nothing happens.")

    elif effect == 'sleep':
        if _harm_mult == 0.0:
            messages.append("Drowsiness touches you and passes -- your blessed constitution resists.")
        else:
            from status_effects import apply_debuff_with_save
            _, msg = apply_debuff_with_save(
                player, 'sleeping', max(1, int(duration * _harm_mult)), dc=13)
            if msg:
                messages.append(msg)

    elif effect == 'weakness':
        if _harm_mult == 0.0:
            messages.append("A wave of fatigue passes harmlessly -- your blessed constitution resists.")
        else:
            applied = player.add_effect('weakened', max(1, int(duration * _harm_mult)))
            if applied:
                messages.append("Your muscles go soft. You feel Weakened!")
            else:
                messages.append("You feel a brief fatigue -- nothing takes hold.")

    elif effect == 'slow':
        if _harm_mult == 0.0:
            messages.append("Time flickers and steadies -- your blessed constitution resists.")
        else:
            from status_effects import apply_debuff_with_save
            _, msg = apply_debuff_with_save(
                player, 'slowed', max(1, int(duration * _harm_mult)), dc=13)
            if msg:
                messages.append(msg)

    elif effect == 'teleport':
        messages.append("_teleport")
        messages.append("Space folds -- you are elsewhere!")

    elif effect == 'drain_str':
        if buc == 'blessed':
            messages.append("A draining sensation passes harmlessly through you.")
        else:
            amt = 2 if buc == 'cursed' else 1
            player.apply_stat_bonus('STR', -amt)
            messages.append(f"Something vital drains away. STR -{amt}!")

    elif effect == 'drain_con':
        if buc == 'blessed':
            messages.append("A draining sensation passes harmlessly through you.")
        else:
            amt = 2 if buc == 'cursed' else 1
            player.apply_stat_bonus('CON', -amt)
            messages.append(f"Your vitality ebbs. CON -{amt}!")

    elif effect == 'drain_wis':
        if buc == 'blessed':
            messages.append("A draining sensation passes harmlessly through you.")
        else:
            amt = 2 if buc == 'cursed' else 1
            player.apply_stat_bonus('WIS', -amt)
            messages.append(f"Your clarity clouds. WIS -{amt}!")

    elif effect == 'drain_int':
        if buc == 'blessed':
            messages.append("A draining sensation passes harmlessly through you.")
        else:
            amt = 2 if buc == 'cursed' else 1
            player.apply_stat_bonus('INT', -amt)
            messages.append(f"Thoughts slip away. INT -{amt}!")

    elif effect == 'sickness':
        if _harm_mult == 0.0:
            messages.append("Your stomach turns briefly -- your blessed constitution resists.")
        else:
            applied = player.add_effect('diseased', max(1, int(duration * _harm_mult)))
            if applied:
                messages.append("A gnawing sickness spreads through you. You are Diseased!")
            else:
                messages.append("Your stomach turns -- your constitution holds.")

    elif effect == 'fumbling':
        if _harm_mult == 0.0:
            messages.append("Your hands twitch briefly -- your blessed constitution resists.")
        else:
            applied = player.add_effect('fumbling', max(1, int(duration * _harm_mult)))
            if applied:
                messages.append("Your hands won't cooperate. You are Fumbling!")
            else:
                messages.append("You feel clumsy for a moment -- nothing lasts.")

    elif effect == 'fear':
        if _harm_mult == 0.0:
            messages.append("A shadow of dread passes -- your blessed constitution resists.")
        else:
            from status_effects import apply_debuff_with_save
            _, msg = apply_debuff_with_save(
                player, 'feared', max(1, int(duration * _harm_mult)), dc=13)
            if msg:
                messages.append(msg)

    elif effect == 'fire_resist':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('fire_resist', dur)
        messages.append(f"Heat rolls off you harmlessly. Fire Resist ({dur} turns).")

    elif effect == 'cold_resist':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('cold_resist', dur)
        messages.append(f"The cold cannot touch you. Cold Resist ({dur} turns).")

    elif effect == 'shock_resist':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('shock_resist', dur)
        messages.append(f"Electricity crackles and disperses. Shock Resist ({dur} turns).")

    elif effect == 'restore_mp':
        amt = roll_dice(power) if power else 15      # dice expr like '2d8+6'
        before = player.mp
        player.restore_mp(amt)
        gained = player.mp - before
        if gained > 0:
            messages.append(f"Arcane energy suffuses you. (+{gained} MP)")
        else:
            messages.append("Your mana is already full.")

    elif effect == 'brilliance_mp':
        amt = roll_dice(power) if power else 40      # dice expr like '4d8+22'
        before = player.mp
        player.restore_mp(amt)
        gained = player.mp - before
        if gained > 0:
            messages.append(f"Pure magical brilliance floods your channels. (+{gained} MP)")
        else:
            messages.append("Your mana reserves are already brimming.")

    elif effect == 'fafnirs_blood':
        # Full heal + permanent fire resistance + lore hint about secret reforge
        amt = player.max_hp - player.hp
        player.restore_hp(amt)
        player.add_effect('fire_resist', -1)  # permanent
        messages.append("The dragon's blood sears your throat — then fills you with ancient power!")
        messages.append("You are fully healed and gain permanent fire resistance.")
        messages.append(
            "As the blood settles, visions flash: a broken blade tumbling through the air "
            "over a sacred altar... and being reborn in divine fire."
        )

    else:
        messages.append("The potion does nothing obvious.")

    # Binary-potion reliability payoff: a blessed dose may linger.
    if _is_binary and _preserve_chance > 0 and not _fizzle:
        if roll_dice('1d100') <= int(round(_preserve_chance * 100)):
            messages.append("_preserve")
            messages.append("You drew the draught out so skillfully a dose remains.")

    return messages


def make_corpse(monster_id: str, x: int, y: int):
    """Create a Corpse item for dungeon generation (graveyard rooms, etc.).

    Per 2026-05-31 redesign: corpse no longer carries an ingredient_id —
    the harvest looks up the prime cut from prime_cuts.json keyed by
    monster_id at harvest time. (v3 2026-09-01: harvest is now a single
    animal question at the corpse's harvest_tier; see harvest_corpse.)
    """
    from items import Corpse
    monsters_path = data_path('data', 'monsters.json')
    with open(monsters_path, encoding='utf-8') as f:
        all_defs = json.load(f)
    defn = all_defs.get(monster_id, {})
    name = defn.get('name', monster_id.replace('_', ' ').title())
    harvest_tier = defn.get('harvest_tier', 1)
    harvest_threshold = defn.get('harvest_threshold', 2)
    # ingredient_id kept for legacy save-compat — passed but harvest ignores it.
    # peak_floor (+ optional explicit id_tier) drives the identify tier.
    return Corpse(name, monster_id, x, y,
                  harvest_tier=harvest_tier,
                  harvest_threshold=harvest_threshold,
                  ingredient_id=defn.get('ingredient_id'),
                  monster_def={'peak_floor': defn.get('peak_floor', 0),
                               'id_tier': defn.get('id_tier', 0),
                               'tags': defn.get('tags', [])})


def eat_raw(player, ingredient) -> list[str]:
    """Eat an ingredient raw (no quiz, no cooking benefits).
    30% chance of food poisoning — cooking eliminates this risk.

    Per 2026-05-31 redesign: raw eating gives a flat SP amount based on
    the ingredient's tier_role (richer ingredients restore more even raw).

    Cooking-overhaul (2026-06-07): Assorted Monster Jerky (assorted_monster_parts)
    is the dried, shelf-stable SURVIVAL FLOOR — it is eaten instantly with NO
    food-poison risk and a bumped SP yield so the player can always stave off
    starvation by harvesting and snacking, even with zero cooking skill. Any
    ingredient carrying `edible_safe` (or a data-driven `raw_sp`) is treated the
    same way. Richer recipes are then the upgrade you CHOOSE, never a survival tax.
    """
    import random
    tier_role = getattr(ingredient, 'tier_role', 'universal')
    raw_sp_map = {
        'universal': 12,   # Assorted Monster Jerky — the don't-starve floor (+12 SP)
        'family':    10,
        'dungeon':   10,
        'prime':     15,
        'trophy':    20,
    }
    # Data-driven SP override (ingredient.raw_sp) wins; else the tier_role map.
    raw_sp = getattr(ingredient, 'raw_sp', None)
    sp = int(raw_sp) if raw_sp is not None else raw_sp_map.get(tier_role, 5)
    player.restore_sp(sp)

    # Cured / dried foods (jerky) are safe to eat — no poison roll.
    is_cured = (getattr(ingredient, 'edible_safe', False)
                or ingredient.id == 'assorted_monster_parts')
    if is_cured:
        messages = [f"You tear into the {ingredient.name}. "
                    f"Tough and gamey, but it keeps you going. (+{sp} SP)."]
        return messages

    messages = [f"You choke down the raw {ingredient.name}. ({sp} SP, unpleasant)."]
    if random.random() < 0.30 and not player.has_effect('poison_resist'):
        player.add_effect('poisoned', 8)
        messages.append("Your stomach churns... food poisoning! (-1 HP/turn for 8 turns)")
    return messages
