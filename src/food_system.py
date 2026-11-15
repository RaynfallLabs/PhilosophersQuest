from naming import quantity
import json
import random
from paths import data_path

_INGREDIENT_PATH = data_path('data', 'items', 'ingredient.json')
_RECIPE_PATH     = data_path('data', 'items', 'recipes.json')
_ingredient_cache: dict | None = None
_recipe_cache: dict | None = None

_STAT_LABELS = {
    'STR': 'strength', 'CON': 'constitution', 'DEX': 'dexterity',
    'INT': 'intelligence', 'WIS': 'wisdom',   'PER': 'perception',
}
_ALL_STATS    = list(_STAT_LABELS.keys())
_COMBAT_STATS = ['STR', 'CON']

# ----------------------------------------------------------------------
# Harvest + Cook: ONE animal question to harvest (tier from the corpse) and
# ONE cooking question to cook (tier from the dish). Right = the full yield
# or the full dish; wrong = ruined, and the corpse or the ingredients are
# consumed either way. No chain, no partial credit, no stun on failure. See
# [[feedback-flow-over-gradient]] and [[feedback-resource-loss-is-the-penalty]].
#
# The kitchen (src/kitchen.py, rebuilt 2026-11-14) knows the book: what a
# corpse yields (data/items/harvest_map.json: close kin share one
# ingredient), the recipe book (data/items/recipes.json) and every number a
# dish gives (data/cooking_rules.json). This module runs the two quizzes.
# ----------------------------------------------------------------------

_monster_floor_cache: dict | None = None


def _monster_band_tier(monster_id: str) -> int:
    """Depth band (1-5) of the floor a monster is seated on; 5 if unknown."""
    global _monster_floor_cache
    if _monster_floor_cache is None:
        try:
            with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
                _monster_floor_cache = {
                    k: int(v.get('peak_floor') or v.get('min_level') or 1)
                    for k, v in json.load(f).items() if isinstance(v, dict)}
        except (OSError, ValueError):
            _monster_floor_cache = {}
    floor = _monster_floor_cache.get(monster_id)
    if floor is None or floor > 100:
        return 5
    return max(1, min(5, floor // 20 + 1))


def _nearest_kin_ingredient(monster_id: str) -> str | None:
    """The ingredient of the nearest creature of the same family and depth,
    for a monster the harvest map does not name (a creature added later)."""
    import kitchen
    _monster_band_tier(monster_id)                     # fills the floor cache
    floors = _monster_floor_cache or {}
    here = floors.get(monster_id, 1)
    try:
        with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
            all_defs = json.load(f)
    except (OSError, ValueError):
        all_defs = {}
    family = (all_defs.get(monster_id) or {}).get('family')
    best = None
    for mid, ing_id in (kitchen.harvest_map().get('monsters') or {}).items():
        if (kitchen.ingredients().get(ing_id) or {}).get('tier_role') != 'prime':
            continue
        same = (all_defs.get(mid) or {}).get('family') == family
        score = (0 if same else 1, abs(floors.get(mid, 999) - here))
        if best is None or score < best[0]:
            best = (score, ing_id)
    return best[1] if best else None


def _harvest_outcome_for_tier(tier: int, monster_id: str) -> list[str]:
    """What a corpse yields: exactly ONE ingredient, its kin's
    (data/items/harvest_map.json: every goblin gives Goblin Gristle; a
    named creature or a boss keeps its own; a boss with a trophy gives the
    trophy). The tier is used only for the harvest question; tier 0
    (ruined) yields nothing."""
    if tier <= 0:
        return []
    import kitchen
    ing_id = kitchen.ingredient_for_monster(monster_id) if monster_id else None
    if ing_id is None and monster_id:
        # A creature the map does not name still feeds the pot.
        ing_id = _nearest_kin_ingredient(monster_id)
    return [ing_id] if ing_id else []


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
    """Every dish the pack can cook now (kitchen.ready_dishes): ingredients
    and the rations a dish calls for, stacks counted, old ids read as the
    kept ones. Single dishes first, then by size and name."""
    import kitchen
    return kitchen.ready_dishes(inventory)


def get_recipes_for_ingredient(ingredient_id: str) -> list[dict]:
    """Every dish that calls for this ingredient."""
    import kitchen
    return kitchen.dishes_with(ingredient_id)


# Map redesign-friendly temp_power names to canonical status_effects entries.
# Names on the LEFT are older data names (no live data uses them since the
# kitchen rebuild of 2026-11-14: a dish names a real status); names on the
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


def temp_power_label(name: str) -> str:
    """Player-facing name of a recipe's temporary power.

    Recipes name powers by data id ("tactics_buff"); the engine remaps
    them to a status ("crit_buff") whose display name lives in
    EFFECT_INFO ("Rallied Strike"). The cook log used to print the raw
    status id and the cook menu printed the raw data id, so the same buff
    had two different, equally unreadable names.
    """
    from status_effects import EFFECT_INFO
    canonical = _resolve_temp_power(name)
    info = EFFECT_INFO.get(canonical)
    if info:
        return info[0]
    return str(canonical).replace('_', ' ').title()


def _resolve_temp_power(name: str) -> str:
    """Resolve a redesign-friendly temp_power name to the canonical status
    effect. Returns the input unchanged if already canonical."""
    return _TEMP_POWER_REMAP.get(name, name)


# The first line of every ruined cook (Game._cook_compound reads it to tell a
# ruined dish from a good one; a dish's own name may hold the letters "ruin").
RUINED_PREFIX = "You ruin the preparation"


def _apply_recipe_outcome(player, recipe: dict, ruined: bool = False) -> list[str]:
    """A dish cooked: right, everything it gives (kitchen.apply_dish);
    wrong, the ingredients are gone and that is all.

    Persephone's Descent (`persephone_active`): a ruined dish still gives
    half its SP, healing and mana ("the seed still returns from the
    dark"); no max HP, stat, power or permanent bonus."""
    import kitchen
    meal_name = recipe.get('name', 'mysterious dish')
    if ruined:
        if getattr(player, 'quirk_progress', {}).get('persephone_active'):
            return kitchen.salvage_dish(player, recipe)
        return [f"{RUINED_PREFIX}. The {meal_name} is wasted."]
    msgs = kitchen.apply_dish(player, recipe)
    # The Fatted Calf (a trait): a legendary feast heals the hero fully.
    if (kitchen.is_legendary(recipe)
            and (getattr(player, 'quirk_progress', None) or {}).get('fatted_calf_active')
            and player.hp < player.max_hp):
        player.restore_hp(player.max_hp - player.hp)
        msgs = list(msgs) + ["You rise from the feast whole: every wound has closed."]
    return msgs


# A cooked meal heals at least this share of the health bar: about 10% for a
# snack, 16% for a plain dish, 20-30% for a good one and a third of it for a
# feast (healing potion 20%, prayer 25%, extra healing 40%). Until 2026-11-12
# it was hp / 180 to at most 12% (a feast 12%, a snack 2%): Brandon, "meals
# need to restore more health than they do now". The difficulty simulator
# found survival unchanged and cooking became the careful player's main way
# back to health (25-47% of the bar a floor, from 10-24%), in place of
# prayers and spells: health comes from cooking.
MEAL_SHARE_BASE = 0.06
MEAL_SHARE_PER_HP = 1.0 / 80.0
MEAL_SHARE_CAP = 0.35


def meal_mend_share(written_hp: float) -> float:
    """Least share of max HP a cooked meal heals, by its written heal
    (data/cooking_rules.json every_dish.heal_written: 3 at tier 1, 20 at
    tier 5)."""
    return min(MEAL_SHARE_CAP, MEAL_SHARE_BASE + float(written_hp) * MEAL_SHARE_PER_HP)


# Permanent-power dispatcher for the boss trophies (each trophy's dish, and
# any feast that holds the trophy: kitchen.apply_dish).
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
        try:
            player.add_effect('petrify_immune', -1)
        except Exception:
            from game_log import log_error
            log_error('food_system._apply_permanent_power: recovered from an error')
        return "Permanent +2 CON, immunity to petrification. " + (desc or "")
    elif power_id == 'plus_2_wis_auto_reveal_secret_doors':
        player.apply_stat_bonus('WIS', 2)
        # 'searching' is the live effect that reveals hidden things nearby.
        try:
            player.add_effect('searching', -1)
        except Exception:
            from game_log import log_error
            log_error('food_system._apply_permanent_power: recovered from an error')
        return "Permanent +2 WIS, and hidden doors near you reveal themselves. " + (desc or "")
    elif power_id == 'fire_immunity':
        # fire_resist halves fire damage and stops the wearer being set
        # alight (it was a full immunity until 2026-10).
        try:
            player.add_effect('fire_resist', -1)
        except Exception:
            from game_log import log_error
            log_error('food_system._apply_permanent_power: recovered from an error')
        return "Permanent fire resistance: fire does half damage. " + (desc or "")
    elif power_id == 'cold_immunity':
        try:
            player.add_effect('cold_resist', -1)
        except Exception:
            from game_log import log_error
            log_error('food_system._apply_permanent_power: recovered from an error')
        return "Permanent cold resistance. " + (desc or "")
    elif power_id == 'petrify_immunity':
        try:
            player.add_effect('petrify_immune', -1)
        except Exception:
            from game_log import log_error
            log_error('food_system._apply_permanent_power: recovered from an error')
        return "Permanent petrification immunity. " + (desc or "")
    elif power_id == 'chromatic_resist_all':
        # A dragon's hide, not five full immunities: three levels of each
        # chromatic element's resistance (the mechanism chain-equip
        # resistances use: Player.CHAIN_RESIST_STEP, 8% a level, so about
        # a fifth less a hit). It said "each hurt 3 less", the flat rule
        # the chain resistances had before they became a share.
        res = getattr(player, 'damage_resistances', None)
        if res is not None:
            for elt in ('fire', 'cold', 'lightning', 'poison', 'acid'):
                res[elt] = int(res.get(elt, 0)) + 3
        return ("Dragon-scale hardiness: fire, cold, lightning, poison and "
                "acid each hurt you about a fifth less. " + (desc or ""))
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
        try:
            player.add_effect('poison_resist', -1)
        except Exception:
            from game_log import log_error
            log_error('food_system._apply_permanent_power: recovered from an error')
        return ("+2 max MP per descent + permanent poison resistance: "
                "poison cannot take hold, and does half damage. " + (desc or ""))
    elif power_id == 'lifesteal_5pct_on_melee':
        player._blood_archon_lifesteal = 0.05
        return "+5% lifesteal on all melee attacks. " + (desc or "")
    elif power_id == 'plus_2_str_confuse_immune':
        # Asterion (v2.6.4 cook redesign): the Minotaur's cunning + navigation
        player.apply_stat_bonus('STR', 2)
        try:
            player.add_effect('confuse_immune', -1)
        except Exception:
            from game_log import log_error
            log_error('food_system._apply_permanent_power: recovered from an error')
        return "Permanent +2 STR, immunity to confusion. " + (desc or "")
    return desc or f"You feel a permanent change ({power_id})."


def recipe_is_trophy(recipe: dict) -> bool:
    """True for a dish shown in gold: a boss trophy's dish or a legendary
    feast (it gives a permanent bonus)."""
    import kitchen
    return kitchen.is_trophy(recipe) or kitchen.is_legendary(recipe)


def _recipe_quiz_tier(recipe: dict) -> int:
    """The cooking question's tier: the dish's tier, the band of its
    deepest ingredient (kitchen.dish_tier)."""
    import kitchen
    return kitchen.dish_tier(recipe)


def consume_ingredients(player, recipe: dict, inventory: list) -> None:
    """Take what a dish calls for out of the pack: one for each listing,
    ingredients and rations alike, from stacks, old ids read as the kept
    ones."""
    import kitchen
    from items import Food, Ingredient
    for part_id in list(recipe.get('ingredients', [])):
        for item in list(inventory):
            if (isinstance(item, (Ingredient, Food))
                    and kitchen.resolve(getattr(item, 'id', '')) == part_id):
                player.remove_from_inventory(item)
                break


def cook_compound_recipe(player, recipe: dict, inventory: list, quiz_engine, on_complete):
    """One cooking question at the dish's tier. Right = everything the dish
    gives; wrong = ruined, ingredients consumed either way. No chain, no
    partial credit: see [[feedback-flow-over-gradient]] +
    [[feedback-resource-loss-is-the-penalty]].
    """
    # Consume what the dish calls for up front (the resource is the stake).
    consume_ingredients(player, recipe, inventory)

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
    """Return a fresh Ingredient instance for ingredient_id (an old id reads
    as the kept one), or None if unknown."""
    import kitchen
    from items import Ingredient
    raw = _raw_ingredients()
    ingredient_id = kitchen.resolve(ingredient_id)
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
    # Never harder than the band the monster now lives in. Monsters were
    # re-seated by HP several times and their harvest tiers were not: 156
    # creatures of floors 1 to 19 asked tier 3, 4 or 5 animal questions.
    tier = min(tier, _monster_band_tier(monster_id))

    def _callback(result):
        if getattr(result, 'success', False):
            ingredient_ids = _harvest_outcome_for_tier(tier, monster_id)
            # Hunter's Harvest / Herbalist (monster family knowledge,
            # src/family_edges.py harvest_bonus): one more portion of the
            # main cut from a family the hero has learned to butcher.
            # A boss's trophy is one of a kind (one heart, one tooth): never
            # a second portion. Two of Fenrir's Tooth gave its +3 STR twice,
            # past every cap (bug bash 3.5.1 A).
            _extra_note = ''
            try:
                import family_edges
                _more, _ab = family_edges.harvest_bonus(player, monster_id)
            except ImportError:
                _more, _ab = 0, None
            if ingredient_ids:
                import kitchen as _kitchen
                if _kitchen.part_kind(ingredient_ids[0]) == 'trophy':
                    _more = 0
            if _more and ingredient_ids:
                ingredient_ids = list(ingredient_ids) + [ingredient_ids[0]] * int(_more)
                _extra_note = ' ' + family_edges.line_for((_ab or {}).get('trigger_msg', '') or '')
            ingredients = [ing for ing_id in ingredient_ids
                           if (ing := load_ingredient_for(ing_id)) is not None]
            # The part remembers the creature it came from (close kin share
            # one ingredient; Siegfried's Bath reads the creature eaten).
            for ing in ingredients:
                if monster_id:
                    ing.source_monster = monster_id
            counts: dict[str, int] = {}
            for ing in ingredients:
                counts[ing.name] = counts.get(ing.name, 0) + 1
            parts = [f"{c}x {n}" if c > 1 else n for n, c in counts.items()]
            msg = (f"You harvest the {corpse.name}: "
                   f"{', '.join(parts)}." if parts
                   else f"You harvest the {corpse.name}, but it yields nothing usable.")
            on_complete(ingredients, (msg + _extra_note).rstrip())
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
    """The one dish that cooks this ingredient on its own (every ingredient
    has exactly one: kitchen.single_dish_for), or None."""
    import kitchen
    return kitchen.single_dish_for(getattr(ingredient, 'id', ''))


def cook_ingredient(player, ingredient, quiz_engine, on_complete):
    """Cook the ONE selected ingredient as its single dish.

    The caller (`Game._cook_item`) has ALREADY removed that single ingredient
    from inventory, so this consumes nothing further: it runs the cooking
    quiz and applies the dish.

    BUGFIX 2026-06-04: this once delegated to `cook_compound_recipe`, which
    re-consumed the recipe's whole ingredient list on top of the caller's
    removal, so cooking one part could devour a stack. It costs exactly the
    one ingredient picked.
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
    """A food's own bonus (food.json `bonus_type`): philosopher's tea, the
    golden apple, ambrosia. A rare food is its own gift, outside the one
    cooking lesson a floor (it took that lesson, so tea after a meal did
    nothing, and ambrosia's "all stats" raised one stat). Each stat still
    stops at what food can teach it at this depth (cooking_stat_softcap,
    shared with cooking): BALANCE_REVIEW_LOOT_AND_FOOD_2026_10_26, F1."""
    bonus_type   = recipe.get('bonus_type', 'none')
    bonus_amount = int(recipe.get('bonus_amount', 0))
    messages     = []

    def _grant(stat: str, amt: int):
        """The stat raised under its lifetime food cap. Returns the amount
        applied. Falls back to apply_stat_bonus for a player without the
        cooking caps (harness mocks)."""
        if hasattr(player, 'apply_cooking_stat_bonus'):
            return player.apply_cooking_stat_bonus(stat, amt)
        player.apply_stat_bonus(stat, amt)
        return amt

    def _capped(stat: str) -> str:
        return (f"Your {_STAT_LABELS[stat].title()} has learned all food can teach it "
                f"at this depth.")

    if bonus_type == 'none' or bonus_amount == 0:
        pass
    elif bonus_type in ('random_stat', 'combat_stat', 'stat'):
        if bonus_type == 'stat':
            stat = recipe.get('bonus_stat', '')
        else:
            stat = random.choice(_ALL_STATS if bonus_type == 'random_stat' else _COMBAT_STATS)
        if stat in _STAT_LABELS:
            applied = _grant(stat, bonus_amount)
            messages.append(f"Your {_STAT_LABELS[stat].title()} increases by {applied}!"
                            if applied > 0 else _capped(stat))
    elif bonus_type in ('two_stats', 'all_stats'):
        chosen = random.sample(_ALL_STATS, 2) if bonus_type == 'two_stats' else list(_ALL_STATS)
        raised = []
        for stat in chosen:
            applied = _grant(stat, bonus_amount)
            if applied > 0:
                raised.append(f"{_STAT_LABELS[stat].title()} +{applied}")
        if raised:
            lead = "A glow spreads through you" if bonus_type == 'all_stats' else "It does you good"
            messages.append(f"{lead}: {', '.join(raised)}.")
        else:
            messages.append("Your body has learned all food can teach it at this depth. "
                            "The dish is filling, no more.")
    elif bonus_type == 'status':
        effect = recipe.get('bonus_effect', '')
        if effect:
            player.add_effect(effect, bonus_amount)
            messages.append(f"You feel a {effect.replace('_', ' ')} effect for {quantity(bonus_amount, 'turn')}!")

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
    if (getattr(player, 'quirk_progress', None) or {}).get('widows_jar_active'):
        sp = sp + sp // 2           # The Widow's Jar (a trait): plain food goes further

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


# Fafnir's Blood: what each step of the bird-speech chain adds. Sigurd tasted
# the dragon's blood and understood the birds, who told him what he needed to
# know. How much the drinker takes from it depends on how well they listen.
FAFNIR_BLOOD_STEPS = (
    (1, 'heal'),          # the wounds close
    (2, 'hint'),          # the birds' words come clear (the Gram secret)
    (3, 'fire_resist'),   # hard to burn, for good
    (4, 'warning'),       # the birds warn you, as they warned Sigurd of Regin
    (5, 'wisdom'),        # you understand more than birds
)


def apply_fafnirs_blood(player, chain: int) -> list:
    """Apply Fafnir's Blood for a bird-speech chain of `chain` (0 to 5).

    It used to be a free drink: full heal, permanent fire protection and the
    Gram hint, the same in every run that killed him. Now the drinker earns
    each part by following what the birds say (an animal quiz, started by
    MenuMixin._drink_fafnirs_blood). Rewards are cumulative.
    """
    chain = max(0, min(5, int(chain)))
    msgs = []
    if chain == 0:
        burn = max(1, player.max_hp // 5)
        player.hp = max(1, player.hp - burn)
        msgs.append("The blood scalds your mouth and throat, and that is all it does.")
        msgs.append("Birds are making a noise somewhere overhead. It is only noise.")
        return msgs
    earned = {name for need, name in FAFNIR_BLOOD_STEPS if chain >= need}
    if 'heal' in earned:
        player.restore_hp(player.max_hp - player.hp)
        msgs.append("The blood scalds all the way down. Then the pain is gone, "
                    "and every wound with it.")
    if 'hint' in earned:
        msgs.append("Two birds are talking overhead, and the words are plain: "
                    "a broken sword, a one-eyed god's stone, a throw.")
    else:
        msgs.append("Two birds are talking overhead. You almost follow them.")
    if 'fire_resist' in earned:
        player.add_effect('fire_resist', -1)
        msgs.append("Fire will never bite you as deep again.")
    if 'warning' in earned:
        player.add_effect('warning', -1)
        msgs.append("The birds go on talking, and now they are talking to you. "
                    "Nothing will come up on you unannounced again.")
    if 'wisdom' in earned:
        player.apply_stat_bonus('WIS', 1)
        msgs.append("You find you understand rather more than birds.")
    return msgs


# Least a healing potion restores, as a share of max HP.
POTION_HEAL_SHARE = 0.20
POTION_EXTRA_HEAL_SHARE = 0.40


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
        # The dice, or a fixed share of max HP if that is more: a potion
        # has to stay worth drinking once hit points grow with depth.
        amt = int(max(roll_dice(power) if power else 10,
                      player.max_hp * POTION_HEAL_SHARE) * _heal_mult)
        player.restore_hp(amt)
        messages.append(f"Warmth floods through you. (+{amt} HP)")

    elif effect == 'extra_heal':
        amt = int(max(roll_dice(power) if power else 25,
                      player.max_hp * POTION_EXTRA_HEAL_SHARE) * _heal_mult)
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
        messages.append(f"The world slows around you. You are Hasted ({quantity(dur, 'turn')}).")

    elif effect == 'invisibility':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('invisible', dur)
        messages.append(f"You fade from sight. Invisible ({quantity(dur, 'turn')}).")

    elif effect == 'regeneration':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('regenerating', dur)
        messages.append(f"You feel an uncanny resilience -- Regenerating ({quantity(dur, 'turn')}).")

    elif effect == 'heroism':
        dur = max(1, int(duration * _buff_mult))
        already_active = player.has_effect('heroism')
        player.add_effect('heroism', dur)
        if not already_active:
            messages.append(f"Surging strength fills your limbs! STR +2, Heroic ({quantity(dur, 'turn')}).")
        else:
            messages.append(f"The heroic surge is renewed ({quantity(dur, 'turn')}).")

    elif effect == 'brilliance':
        dur = max(1, int(duration * _buff_mult))
        already_active = player.has_effect('brilliance')
        player.add_effect('brilliance', dur)
        if not already_active:
            messages.append(f"Your mind blazes with clarity! INT +1, WIS +1, Brilliant ({quantity(dur, 'turn')}).")
        else:
            messages.append(f"Your mental clarity is renewed ({quantity(dur, 'turn')}).")

    elif effect == 'levitation':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('levitating', dur)
        messages.append(f"Your feet leave the ground. Levitating ({quantity(dur, 'turn')}).")

    elif effect == 'see_invisible':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('see_invisible', dur)
        messages.append(f"Your eyes are opened: you see what walks unseen. See Invisible ({quantity(dur, 'turn')}).")

    elif effect == 'restore_str':
        # Restore STR to base value (undoes disease drain)
        # What disease took, as the disease tick records it. This read
        # `_base_STR`, which nothing ever set: the one cure in the game for
        # drained Strength always said "already at its peak".
        loss = int(getattr(player, '_str_lost_to_disease', 0) or 0)
        player._str_lost_to_disease = 0
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
            player._str_lost_to_disease = int(getattr(player, '_str_lost_to_disease', 0) or 0) + amt
            messages.append(f"Something vital drains away. STR -{amt}!")

    elif effect == 'drain_con':
        if buc == 'blessed':
            messages.append("A draining sensation passes harmlessly through you.")
        else:
            amt = 2 if buc == 'cursed' else 1
            player.apply_stat_bonus('CON', -amt)
            from status_effects import note_stat_drain
            note_stat_drain(player, 'CON', amt)      # a physician can restore it
            messages.append(f"Your vitality ebbs. CON -{amt}!")

    elif effect == 'drain_wis':
        if buc == 'blessed':
            messages.append("A draining sensation passes harmlessly through you.")
        else:
            amt = 2 if buc == 'cursed' else 1
            player.apply_stat_bonus('WIS', -amt)
            from status_effects import note_stat_drain
            note_stat_drain(player, 'WIS', amt)      # a physician can restore it
            messages.append(f"Your clarity clouds. WIS -{amt}!")

    elif effect == 'drain_int':
        if buc == 'blessed':
            messages.append("A draining sensation passes harmlessly through you.")
        else:
            amt = 2 if buc == 'cursed' else 1
            player.apply_stat_bonus('INT', -amt)
            from status_effects import note_stat_drain
            note_stat_drain(player, 'INT', amt)      # a physician can restore it
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
        messages.append(f"Heat rolls off you harmlessly. Fire Resist ({quantity(dur, 'turn')}).")

    elif effect == 'cold_resist':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('cold_resist', dur)
        messages.append(f"The cold cannot touch you. Cold Resist ({quantity(dur, 'turn')}).")

    elif effect == 'shock_resist':
        dur = max(1, int(duration * _buff_mult))
        player.add_effect('shock_resist', dur)
        messages.append(f"Electricity crackles and disperses. Shock Resist ({quantity(dur, 'turn')}).")

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
        # The Blood is drunk through MenuMixin._drink_fafnirs_blood, which
        # asks the bird-speech quiz first. Reached any other way it is only
        # a scalding mouthful.
        messages.extend(apply_fafnirs_blood(player, 0))

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

    The corpse carries no ingredient of its own: the harvest looks up what
    its kin yields (data/items/harvest_map.json) by monster_id at harvest
    time, with one animal question at the corpse's harvest_tier (see
    harvest_corpse).
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
