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

    return messages
