import json
import os
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

# Permanent +max_hp from compound recipes (tier, quality) -> bonus
# Only quality 3+ grants max HP.  Primary source of HP growth.
_COMPOUND_MAX_HP = {
    (1, 3):  6, (1, 4): 10, (1, 5): 15,
    (2, 3): 10, (2, 4): 16, (2, 5): 22,
    (3, 3): 14, (3, 4): 21, (3, 5): 29,
    (4, 3): 17, (4, 4): 24, (4, 5): 33,
    (5, 3): 20, (5, 4): 30, (5, 5): 40,
}

# Permanent +max_hp from single ingredient cooks (T4-T5 only, quality 3+)
_SINGLE_MAX_HP = {
    (4, 3):  2, (4, 4):  3, (4, 5):  5,
    (5, 3):  3, (5, 4):  5, (5, 5):  8,
}


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
    """Return compound recipe dicts where the player has ALL required ingredients."""
    from items import Ingredient
    held_ids = {item.id for item in inventory if isinstance(item, Ingredient)}
    return [
        {'id': rid, **rdef}
        for rid, rdef in _raw_recipes().items()
        if all(ing in held_ids for ing in rdef.get('ingredients', []))
    ]


def get_recipes_for_ingredient(ingredient_id: str) -> list[dict]:
    """Return all compound recipes that list this ingredient_id."""
    return [
        {'id': rid, **rdef}
        for rid, rdef in _raw_recipes().items()
        if ingredient_id in rdef.get('ingredients', [])
    ]


def cook_compound_recipe(player, recipe: dict, inventory: list, quiz_engine, on_complete,
                         dungeon_level: int = 1):
    """
    Remove all required ingredients from inventory, then run an escalator_chain
    cooking quiz. Quality 0 = total ruin; 1-2 = partial; 3-5 = full bonus.
    on_complete(messages: list[str]) is called when the quiz ends.
    dungeon_level: current floor (used to scale max HP bonus tier).
    """
    from items import Ingredient
    # Consume all required ingredients now (before quiz)
    for ing_id in recipe.get('ingredients', []):
        for item in list(inventory):
            if isinstance(item, Ingredient) and item.id == ing_id:
                player.remove_from_inventory(item)
                break

    def _callback(result):
        quality = min(5, result.score)
        messages = []
        meal_name = recipe['name']

        if quality == 0:
            messages.append(f"You ruin the preparation. The {meal_name} is wasted.")
        elif quality < 3:
            sp = max(10, recipe.get('sp', 100) // 4)
            player.restore_sp(sp)
            messages.append(f"You produce a mediocre {meal_name} (quality {quality}/5).")
            messages.append(f"You force it down and restore {sp} SP.")
        else:
            sp = recipe.get('sp', 100)
            player.restore_sp(sp)
            messages.append(f"You masterfully prepare {meal_name}! (quality {quality}/5)")
            messages.append(f"You savour it and restore {sp} SP.")
            messages.extend(_apply_bonus(player, recipe))
            # Permanent max HP bonus from compound recipes (Q3+)
            # Use max of recipe tier and floor tier so deep cooking is always rewarding
            recipe_tier = recipe.get('tier', 1)
            floor_tier = max(1, min(5, (dungeon_level - 1) // 20 + 1))
            tier = max(recipe_tier, floor_tier)
            hp_bonus = _COMPOUND_MAX_HP.get((tier, quality), 0)
            if hp_bonus > 0:
                player.increase_max_hp(hp_bonus)
                messages.append(f"The nourishing meal strengthens you permanently. (+{hp_bonus} max HP)")

        on_complete(messages)

    quiz_engine.start_quiz(
        mode='escalator_chain',
        subject='cooking',
        tier=recipe.get('tier', 1),
        callback=_callback,
        max_chain=5,
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

def harvest_corpse(player, corpse, quiz_engine, on_complete):
    """
    Trigger an animal threshold quiz to harvest a corpse.
    on_complete(ingredient_or_None, message: str) is called when the quiz ends.
    The corpse is consumed regardless of success.
    """
    def _callback(result):
        if result.success:
            ingredient = load_ingredient_for(corpse.ingredient_id)
            if ingredient:
                on_complete(ingredient, f"You harvest {ingredient.name} from the {corpse.name}.")
            else:
                on_complete(None, f"The {corpse.name} yields nothing useful.")
        else:
            on_complete(None, f"You botch the harvest. The {corpse.name} is ruined.")

    quiz_engine.start_quiz(
        mode='threshold',
        subject='animal',
        tier=getattr(corpse, 'harvest_tier', 1),
        callback=_callback,
        threshold=getattr(corpse, 'harvest_threshold', 2),
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('animal'),
        base_seconds=player.get_quiz_timer('animal'),
    )


# ------------------------------------------------------------------
# Cooking
# ------------------------------------------------------------------

def cook_ingredient(player, ingredient, quiz_engine, on_complete, max_chain: int = 5,
                    dungeon_level: int = 1):
    """
    Trigger a cooking escalator_chain quiz.
    Chain length 0-5 = meal quality. Single-ingredient meals restore SP + HP (scaled by
    quality and ingredient tier) only -- permanent stat bonuses come exclusively from
    multi-ingredient compound recipes.
    on_complete(messages: list[str]) is called when the quiz ends.
    max_chain: maximum chain length (default 5; pass 6 if Persephone quirk is active).
    dungeon_level: current floor (used to scale max HP bonus tier).
    """
    def _callback(result):
        quality   = min(5, result.score)
        recipe    = ingredient.recipes.get(str(quality), ingredient.recipes.get('0', {}))
        meal_name = recipe.get('name', 'mysterious dish')
        sp_amount = int(recipe.get('sp', 0))
        messages  = []

        if quality == 0:
            messages.append(f"You ruin the {ingredient.name}. Inedible {meal_name}.")
        else:
            messages.append(f"You cook {meal_name}  (quality {quality}/5).")
            player.restore_sp(sp_amount)
            messages.append(f"You eat it and restore {sp_amount} SP.")
            # HP bonus scales with ingredient tier and cooking quality (no stat bonuses here)
            hp = _cooking_hp_bonus(ingredient.min_level, quality)
            if hp > 0:
                player.restore_hp(hp)
                messages.append(f"The meal soothes your wounds. (+{hp} HP)")
            # MP restore from ingredient (e.g. undead ingredients restore mana)
            mp_base = getattr(ingredient, 'mp_restore', 0)
            if mp_base > 0:
                mp_gained = max(1, int(mp_base * quality / 5)) if quality > 0 else 0
                if mp_gained > 0:
                    player.restore_mp(mp_gained)
                    messages.append(f"The essence of the ingredient restores {mp_gained} MP.")
            # Small permanent max HP bonus for high-tier single cooks (T4-T5, Q3+)
            ing_tier = max(1, min(5, (ingredient.min_level - 1) // 20 + 1))
            floor_tier = max(1, min(5, (dungeon_level - 1) // 20 + 1))
            eff_tier = max(ing_tier, floor_tier)
            hp_bonus = _SINGLE_MAX_HP.get((eff_tier, quality), 0)
            if hp_bonus > 0:
                player.increase_max_hp(hp_bonus)
                messages.append(f"The potent essence fortifies you. (+{hp_bonus} max HP)")

        # Status effects (e.g. invisible, regenerating) from ingredient data are still applied
        bonus_type = recipe.get('bonus_type', 'none')
        if bonus_type == 'status':
            messages.extend(_apply_bonus(player, recipe))

        on_complete(messages)

    # Derive cooking tier from ingredient's min_level: levels 1-20 -> tier 1, 21-40 -> tier 2, etc.
    ing_tier = max(1, min(5, (ingredient.min_level - 1) // 20 + 1))
    quiz_engine.start_quiz(
        mode='escalator_chain',
        subject='cooking',
        tier=ing_tier,
        callback=_callback,
        max_chain=max_chain,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('cooking'),
        base_seconds=player.get_quiz_timer('cooking'),
    )


def _cooking_hp_bonus(min_level: int, quality: int) -> int:
    """
    HP restored by cooking a single monster ingredient.
    Scales with the ingredient's dungeon-depth tier (every 20 levels) and quality (3-5).
    Quality 1-2 gives no HP -- just SP. Quality 3+ adds a small heal.
    Tier 1 (L1-20): Q3=3  Q4=5  Q5=8
    Tier 2 (L21-40): Q3=5  Q4=8  Q5=12
    Tier 3 (L41-60): Q3=8  Q4=12 Q5=18
    Tier 4 (L61-80): Q3=12 Q4=18 Q5=25
    Tier 5 (L81-100): Q3=18 Q4=25 Q5=35
    """
    if quality < 3:
        return 0
    tier = max(1, min(5, (min_level - 1) // 20 + 1))
    table = {1: (3, 5, 8), 2: (5, 8, 12), 3: (8, 12, 18), 4: (12, 18, 25), 5: (18, 25, 35)}
    return table[tier][quality - 3]


def _apply_bonus(player, recipe) -> list[str]:
    bonus_type   = recipe.get('bonus_type', 'none')
    bonus_amount = int(recipe.get('bonus_amount', 0))
    messages     = []

    if bonus_type == 'none' or bonus_amount == 0:
        pass
    elif bonus_type == 'random_stat':
        stat = random.choice(_ALL_STATS)
        player.apply_stat_bonus(stat, bonus_amount)
        messages.append(f"Your {_STAT_LABELS[stat]} increases by {bonus_amount}!")
    elif bonus_type == 'combat_stat':
        stat = random.choice(_COMBAT_STATS)
        player.apply_stat_bonus(stat, bonus_amount)
        messages.append(f"Your {_STAT_LABELS[stat]} increases by {bonus_amount}!")
    elif bonus_type == 'two_stats':
        chosen = random.sample(_ALL_STATS, 2)
        for stat in chosen:
            player.apply_stat_bonus(stat, bonus_amount)
            messages.append(f"Your {_STAT_LABELS[stat]} increases by {bonus_amount}!")
    elif bonus_type == 'all_stats':
        for stat in _ALL_STATS:
            player.apply_stat_bonus(stat, bonus_amount)
        messages.append(f"All your stats increase by {bonus_amount}!")
    elif bonus_type == 'stat':
        stat = recipe.get('bonus_stat', '')
        if stat in _STAT_LABELS:
            player.apply_stat_bonus(stat, bonus_amount)
            messages.append(f"Your {_STAT_LABELS[stat]} increases by {bonus_amount}!")
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

    # --- Identification on use ---
    potion.identified = True

    if effect == 'heal':
        amt = roll_dice(power) if power else 10
        player.restore_hp(amt)
        messages.append(f"Warmth floods through you. (+{amt} HP)")

    elif effect == 'extra_heal':
        amt = roll_dice(power) if power else 25
        player.restore_hp(amt)
        messages.append(f"Deep wounds knit closed with startling speed. (+{amt} HP)")

    elif effect == 'full_heal':
        amt = player.max_hp - player.hp
        player.restore_hp(amt)
        messages.append("Every wound closes. You feel completely whole.")

    elif effect == 'restore_sp':
        amt = roll_dice(power) if power else 50
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
        player.add_effect('hasted', duration)
        messages.append(f"The world slows around you. You are Hasted ({duration} turns).")

    elif effect == 'invisibility':
        player.add_effect('invisible', duration)
        messages.append(f"You fade from sight. Invisible ({duration} turns).")

    elif effect == 'regeneration':
        player.add_effect('regenerating', duration)
        messages.append(f"You feel an uncanny resilience -- Regenerating ({duration} turns).")

    elif effect == 'heroism':
        already_active = player.has_effect('heroism')
        player.add_effect('heroism', duration)
        if not already_active:
            player.apply_stat_bonus('STR', 2)
            messages.append(f"Surging strength fills your limbs! STR +2, Heroic ({duration} turns).")
        else:
            messages.append(f"The heroic surge is renewed ({duration} turns).")

    elif effect == 'brilliance':
        already_active = player.has_effect('brilliance')
        player.add_effect('brilliance', duration)
        if not already_active:
            player.apply_stat_bonus('INT', 1)
            player.apply_stat_bonus('WIS', 1)
            messages.append(f"Your mind blazes with clarity! INT +1, WIS +1, Brilliant ({duration} turns).")
        else:
            messages.append(f"Your mental clarity is renewed ({duration} turns).")

    elif effect == 'levitation':
        player.add_effect('levitating', duration)
        messages.append(f"Your feet leave the ground. Levitating ({duration} turns).")

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
        applied = player.add_effect('confused', duration)
        if applied:
            messages.append("Your thoughts spin out of control! You are Confused.")
        else:
            messages.append("You feel briefly dizzy -- nothing happens.")

    elif effect == 'blindness':
        applied = player.add_effect('blinded', duration)
        if applied:
            messages.append("Darkness closes in! You are Blinded.")
        else:
            messages.append("Your eyes water -- nothing happens.")

    elif effect == 'poison':
        applied = player.add_effect('poisoned', 20)
        if applied:
            messages.append("You feel violently ill. You are Poisoned!")
        else:
            messages.append("You feel fine -- your body resists the poison.")

    elif effect == 'paralysis':
        applied = player.add_effect('paralyzed', duration)
        if applied:
            messages.append("Your body locks up! You are Paralyzed.")
        else:
            messages.append("You feel a brief stiffness -- nothing happens.")

    elif effect == 'hallucination':
        applied = player.add_effect('hallucinating', duration)
        if applied:
            messages.append("The walls breathe. The floor shifts. You are Hallucinating!")
        else:
            messages.append("You feel briefly strange -- nothing happens.")

    elif effect == 'sleep':
        applied = player.add_effect('sleeping', duration)
        if applied:
            messages.append("Irresistible drowsiness claims you. You fall Asleep!")
        else:
            messages.append("You feel briefly drowsy -- your will resists.")

    elif effect == 'weakness':
        applied = player.add_effect('weakened', duration)
        if applied:
            messages.append("Your muscles go soft. You feel Weakened!")
        else:
            messages.append("You feel a brief fatigue -- nothing takes hold.")

    elif effect == 'slow':
        applied = player.add_effect('slowed', duration)
        if applied:
            messages.append("Time thickens around you. You are Slowed.")
        else:
            messages.append("You feel momentarily sluggish -- it passes.")

    elif effect == 'teleport':
        messages.append("_teleport")
        messages.append("Space folds -- you are elsewhere!")

    elif effect == 'drain_str':
        player.apply_stat_bonus('STR', -1)
        messages.append("Something vital drains away. STR -1!")

    elif effect == 'drain_con':
        player.apply_stat_bonus('CON', -1)
        messages.append("Your vitality ebbs. CON -1!")

    elif effect == 'drain_wis':
        player.apply_stat_bonus('WIS', -1)
        messages.append("Your clarity clouds. WIS -1!")

    elif effect == 'drain_int':
        player.apply_stat_bonus('INT', -1)
        messages.append("Thoughts slip away. INT -1!")

    elif effect == 'sickness':
        applied = player.add_effect('diseased', duration)
        if applied:
            messages.append("A gnawing sickness spreads through you. You are Diseased!")
        else:
            messages.append("Your stomach turns -- your constitution holds.")

    elif effect == 'fumbling':
        applied = player.add_effect('fumbling', duration)
        if applied:
            messages.append("Your hands won't cooperate. You are Fumbling!")
        else:
            messages.append("You feel clumsy for a moment -- nothing lasts.")

    elif effect == 'fear':
        applied = player.add_effect('feared', duration)
        if applied:
            messages.append("Terror grips your heart. You are Feared!")
        else:
            messages.append("A shadow of dread passes -- your courage holds.")

    elif effect == 'fire_resist':
        player.add_effect('fire_resist', duration)
        messages.append(f"Heat rolls off you harmlessly. Fire Resist ({duration} turns).")

    elif effect == 'cold_resist':
        player.add_effect('cold_resist', duration)
        messages.append(f"The cold cannot touch you. Cold Resist ({duration} turns).")

    elif effect == 'shock_resist':
        player.add_effect('shock_resist', duration)
        messages.append(f"Electricity crackles and disperses. Shock Resist ({duration} turns).")

    elif effect == 'restore_mp':
        try:
            amt = int(power) if power else 15
        except (ValueError, TypeError):
            from dice import roll
            amt = roll(str(power))
        before = player.mp
        player.restore_mp(amt)
        gained = player.mp - before
        if gained > 0:
            messages.append(f"Arcane energy suffuses you. (+{gained} MP)")
        else:
            messages.append("Your mana is already full.")

    elif effect == 'brilliance_mp':
        try:
            amt = int(power) if power else 40
        except (ValueError, TypeError):
            from dice import roll
            amt = roll(str(power))
        before = player.mp
        player.restore_mp(amt)
        gained = player.mp - before
        if gained > 0:
            messages.append(f"Pure magical brilliance floods your channels. (+{gained} MP)")
        else:
            messages.append("Your mana reserves are already brimming.")

    else:
        messages.append("The potion does nothing obvious.")

    return messages


def eat_raw(player, ingredient) -> list[str]:
    """Eat an ingredient raw (quality 1 recipe, no quiz)."""
    recipe = ingredient.recipes.get('1', ingredient.recipes.get('0', {}))
    sp = int(recipe.get('sp', 5))
    player.restore_sp(sp)
    return [f"You choke down the raw {ingredient.name}. ({sp} SP, unpleasant)."]
