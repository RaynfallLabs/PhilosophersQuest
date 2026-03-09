import json
import os
import random

_INGREDIENT_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'items', 'ingredient.json'
)
_ingredient_cache: dict | None = None

_STAT_LABELS = {
    'STR': 'strength', 'CON': 'constitution', 'DEX': 'dexterity',
    'INT': 'intelligence', 'WIS': 'wisdom',   'PER': 'perception',
}
_ALL_STATS    = list(_STAT_LABELS.keys())
_COMBAT_STATS = ['STR', 'CON']


# ------------------------------------------------------------------
# Data loading
# ------------------------------------------------------------------

def _raw_ingredients() -> dict:
    global _ingredient_cache
    if _ingredient_cache is None:
        with open(_INGREDIENT_PATH, encoding='utf-8') as f:
            _ingredient_cache = json.load(f)
    return _ingredient_cache


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
    )


# ------------------------------------------------------------------
# Cooking
# ------------------------------------------------------------------

def cook_ingredient(player, ingredient, quiz_engine, on_complete):
    """
    Trigger a cooking escalator_chain quiz.
    Chain length 0-5 = meal quality. Meal is auto-consumed; SP restored + stat bonuses.
    on_complete(messages: list[str]) is called when the quiz ends.
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

        messages.extend(_apply_bonus(player, recipe))
        on_complete(messages)

    quiz_engine.start_quiz(
        mode='escalator_chain',
        subject='cooking',
        tier=1,
        callback=_callback,
        max_chain=5,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
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


def eat_raw(player, ingredient) -> list[str]:
    """Eat an ingredient raw (quality 1 recipe, no quiz)."""
    recipe = ingredient.recipes.get('1', ingredient.recipes.get('0', {}))
    sp = int(recipe.get('sp', 5))
    player.restore_sp(sp)
    return [f"You choke down the raw {ingredient.name}. ({sp} SP, unpleasant)."]
