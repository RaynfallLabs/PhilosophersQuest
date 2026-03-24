import json
import math
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


def _cooking_sp(min_level: int, quality: int) -> int:
    """SP restored from eating the cooked meal."""
    if quality < 1:
        return 0
    return max(10, int(5 * _potency(min_level) * quality))


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


def cook_compound_recipe(player, recipe: dict, inventory: list, quiz_engine, on_complete):
    """
    Remove all required ingredients from inventory, then run an escalator_chain
    cooking quiz. Quality 0 = total ruin; 1-5 = meal with potency-scaled rewards.
    on_complete(messages: list[str]) is called when the quiz ends.
    """
    from items import Ingredient
    # Resolve ingredient min_levels before consuming them
    raw_ings = _raw_ingredients()
    ing_min_levels = []
    for ing_id in recipe.get('ingredients', []):
        ing_def = raw_ings.get(ing_id, {})
        ing_min_levels.append(ing_def.get('min_level', 1))

    # Consume all required ingredients now (before quiz)
    for ing_id in recipe.get('ingredients', []):
        for item in list(inventory):
            if isinstance(item, Ingredient) and item.id == ing_id:
                player.remove_from_inventory(item)
                break

    max_min_level = max(ing_min_levels) if ing_min_levels else 1
    n_ingredients = len(recipe.get('ingredients', []))

    def _callback(result):
        quality = min(5, result.score)
        messages = []
        meal_name = recipe['name']

        if quality == 0:
            messages.append(f"You ruin the preparation. The {meal_name} is wasted.")
        else:
            sp = _cooking_sp(max_min_level, quality)
            player.restore_sp(sp)
            heal = _cooking_heal(max_min_level, quality)
            if heal > 0:
                player.restore_hp(heal)

            if quality <= 2:
                messages.append(f"You produce a {'rough' if quality == 1 else 'decent'} {meal_name} (quality {quality}/5).")
            else:
                messages.append(f"You masterfully prepare {meal_name}! (quality {quality}/5)")
            messages.append(f"You eat it and restore {sp} SP" + (f" and {heal} HP." if heal > 0 else "."))

            messages.extend(_apply_bonus(player, recipe))
            # Permanent max HP bonus from compound recipe (potency-based)
            hp_bonus = _compound_max_hp(max_min_level, quality, n_ingredients)
            if hp_bonus > 0:
                player.increase_max_hp(hp_bonus, from_cooking=True)
                messages.append(f"The nourishing meal strengthens you permanently. (+{hp_bonus} max HP)")

        on_complete(messages)

    quiz_engine.start_quiz(
        mode='escalator_chain',
        subject='cooking',
        tier=1,
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

def harvest_corpse(player, corpse, quiz_engine, on_complete, extra_seconds: int = 0):
    """
    Trigger an animal threshold quiz to harvest a corpse.
    on_complete(ingredient_or_None, message: str) is called when the quiz ends.
    The corpse is consumed regardless of success.
    extra_seconds: bonus time (e.g. +5s for lore-identified monsters).
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

    _player_extra = getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('animal')
    quiz_engine.start_quiz(
        mode='threshold',
        subject='animal',
        tier=getattr(corpse, 'harvest_tier', 1),
        callback=_callback,
        threshold=getattr(corpse, 'harvest_threshold', 2),
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=_player_extra + extra_seconds,
        base_seconds=player.get_quiz_timer('animal'),
    )


# ------------------------------------------------------------------
# Cooking
# ------------------------------------------------------------------

def cook_ingredient(player, ingredient, quiz_engine, on_complete, max_chain: int = 5):
    """
    Trigger a cooking escalator_chain quiz (always starts at T1).
    Chain length 0-5 = meal quality. Rewards scale with ingredient potency
    (sqrt of source monster's min_level).
    on_complete(messages: list[str]) is called when the quiz ends.
    max_chain: maximum chain length (default 5; pass 6 if Persephone quirk is active).
    """
    min_level = ingredient.min_level

    def _callback(result):
        quality   = min(5, result.score)
        recipe    = ingredient.recipes.get(str(quality), ingredient.recipes.get('0', {}))
        meal_name = recipe.get('name', 'mysterious dish')
        messages  = []

        if quality == 0:
            messages.append(f"You ruin the {ingredient.name}. Inedible {meal_name}.")
        else:
            sp_amount = _cooking_sp(min_level, quality)
            messages.append(f"You cook {meal_name}  (quality {quality}/5).")
            player.restore_sp(sp_amount)
            messages.append(f"You eat it and restore {sp_amount} SP.")
            # HP heal scales with potency
            hp = _cooking_heal(min_level, quality)
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
            # Permanent max HP bonus from single cook (potency-based)
            hp_bonus = _single_max_hp(min_level, quality)
            if hp_bonus > 0:
                player.increase_max_hp(hp_bonus, from_cooking=True)
                messages.append(f"The nourishing meal fortifies you. (+{hp_bonus} max HP)")

        # Status effects (e.g. invisible, regenerating) from ingredient data are still applied
        bonus_type = recipe.get('bonus_type', 'none')
        if bonus_type == 'status':
            messages.extend(_apply_bonus(player, recipe))

        on_complete(messages)

    quiz_engine.start_quiz(
        mode='escalator_chain',
        subject='cooking',
        tier=1,
        callback=_callback,
        max_chain=max_chain,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('cooking'),
        base_seconds=player.get_quiz_timer('cooking'),
    )


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
    buc      = getattr(potion, 'buc', 'uncursed')

    # --- BUC multipliers ---
    # Healing: blessed ×1.5, cursed ×0.5
    # Buff duration: blessed ×1.5, cursed ×0.5
    # Harmful effects: blessed = blocked, cursed = duration ×1.5
    # Stat drains: blessed = no drain, cursed = drain ×2
    _heal_mult = 1.5 if buc == 'blessed' else (0.5 if buc == 'cursed' else 1.0)
    _buff_mult = 1.5 if buc == 'blessed' else (0.5 if buc == 'cursed' else 1.0)
    _harm_mult = 0.0 if buc == 'blessed' else (1.5 if buc == 'cursed' else 1.0)

    # --- Identification on use ---
    potion.identified = True

    if effect == 'heal':
        amt = int((roll_dice(power) if power else 10) * _heal_mult)
        player.restore_hp(amt)
        messages.append(f"Warmth floods through you. (+{amt} HP)")

    elif effect == 'extra_heal':
        amt = int((roll_dice(power) if power else 25) * _heal_mult)
        player.restore_hp(amt)
        messages.append(f"Deep wounds knit closed with startling speed. (+{amt} HP)")

    elif effect == 'full_heal':
        if buc == 'cursed':
            amt = int((player.max_hp - player.hp) * 0.5)
        else:
            amt = player.max_hp - player.hp
        player.restore_hp(amt)
        messages.append("Every wound closes. You feel completely whole.")

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
            applied = player.add_effect('confused', max(1, int(duration * _harm_mult)))
            if applied:
                messages.append("Your thoughts spin out of control! You are Confused.")
            else:
                messages.append("You feel briefly dizzy -- nothing happens.")

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
            applied = player.add_effect('paralyzed', max(1, int(duration * _harm_mult)))
            if applied:
                messages.append("Your body locks up! You are Paralyzed.")
            else:
                messages.append("You feel a brief stiffness -- nothing happens.")

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
            applied = player.add_effect('sleeping', max(1, int(duration * _harm_mult)))
            if applied:
                messages.append("Irresistible drowsiness claims you. You fall Asleep!")
            else:
                messages.append("You feel briefly drowsy -- your will resists.")

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
            applied = player.add_effect('slowed', max(1, int(duration * _harm_mult)))
            if applied:
                messages.append("Time thickens around you. You are Slowed.")
            else:
                messages.append("You feel momentarily sluggish -- it passes.")

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
            applied = player.add_effect('feared', max(1, int(duration * _harm_mult)))
            if applied:
                messages.append("Terror grips your heart. You are Feared!")
            else:
                messages.append("A shadow of dread passes -- your courage holds.")

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

    return messages


def make_corpse(monster_id: str, x: int, y: int):
    """Create a Corpse item for dungeon generation (graveyard rooms, etc.).
    Uses monster_id to look up basic info; returns a Corpse item at (x, y)."""
    from items import Corpse
    # Load monster data for the name
    monsters_path = data_path('data', 'monsters.json')
    with open(monsters_path, encoding='utf-8') as f:
        all_defs = json.load(f)
    defn = all_defs.get(monster_id, {})
    name = defn.get('name', monster_id.replace('_', ' ').title())
    ingredient_id = defn.get('ingredient_id', None)
    harvest_tier = defn.get('harvest_tier', 1)
    harvest_threshold = defn.get('harvest_threshold', 2)
    return Corpse(name, monster_id, x, y,
                  harvest_tier=harvest_tier,
                  harvest_threshold=harvest_threshold,
                  ingredient_id=ingredient_id)


def eat_raw(player, ingredient) -> list[str]:
    """Eat an ingredient raw (quality 1 recipe, no quiz)."""
    recipe = ingredient.recipes.get('1', ingredient.recipes.get('0', {}))
    sp = int(recipe.get('sp', 5))
    player.restore_sp(sp)
    return [f"You choke down the raw {ingredient.name}. ({sp} SP, unpleasant)."]
