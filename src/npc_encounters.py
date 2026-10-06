"""
NPC moral encounter system: one encounter per 10-level block, chosen from
the candidates in data/npc_encounters.json.

Flow: bump NPC → encounter text (ENTER) → 3 options (1-3) → outcome (ENTER).
Options show action + justification only, no outcomes, no karma labels.
The player is never cruel; even selfish options are framed as pragmatic necessity.
One encounter guaranteed per 10-level block, chosen from 3 candidates.
"""
import random

# Boss levels where NPCs cannot spawn
_BOSS_LEVELS = frozenset({20, 40, 60, 80, 100})

# Level blocks: (block_number, min_level, max_level)
_BLOCKS = [
    (1,  3,  9),
    (2,  11, 19),
    (3,  21, 29),
    (4,  31, 39),
    (5,  41, 49),
    (6,  51, 59),
    (7,  61, 69),
    (8,  71, 79),
    (9,  81, 89),
    (10, 91, 98),
]

# ── Encounter definitions ──────────────────────────────────────────────
#
# Each encounter has:
#   tag         - unique id (prevents duplicates per run)
#   name        - NPC display name
#   symbol      - tile character
#   color       - RGB tuple
#   block       - which 10-level block (1-10)
#   trigger_item - (optional) item_id that spawns 1-3 levels before NPC
#   trigger_level_offset - (optional) how many levels before NPC the item spawns
#   text        - encounter description (screen 1)
#   options     - list of dicts:
#       label   - what the player sees (screen 2), NO outcomes
#       karma   - -1, 0, or +1
#       outcome - shown after selection (screen 3)
#       cost    - dict or None  (what the good/neutral deed costs)
#       reward  - dict or None  (what the selfish choice gains)
#
# Cost types:
#   {'type': 'food'}              - give 1 Food (inventory selection)
#   {'type': 'healing_potion'}    - give 1 healing potion (inventory selection)
#   {'type': 'potion'}            - give 1 potion, any kind (inventory selection)
#   {'type': 'scroll'}            - give 1 scroll (inventory selection)
#   {'type': 'weapon'}            - give 1 weapon (inventory selection)
#   {'type': 'gold', 'amount': N} - pay N gold
#   {'type': 'hp_percent', 'amount': N}   - lose N% of current HP
#   {'type': 'max_hp', 'amount': N}       - lose N max HP permanently
#   {'type': 'sp', 'amount': N}           - lose N stamina
#   {'type': 'triggered_item'}            - return the trigger item
#   {'type': 'accept_item', 'item_id': X} - receive a cursed/burden item
#
# Reward types:
#   {'type': 'gold', 'min': A, 'max': B}
#   {'type': 'random_weapon'}
#   {'type': 'random_armor'}
#   {'type': 'random_shield'}
#   {'type': 'random_accessory'}
#   {'type': 'random_potion', 'count': N}
#   {'type': 'random_scroll', 'count': N}
#   {'type': 'random_food', 'count': N}
#   {'type': 'stat', 'stat': 'CON', 'amount': N}
#   {'type': 'specific_item', 'item_type': 'weapon', 'item_id': X}
#   {'type': 'multi', 'rewards': [...]}

def _load_encounters() -> list:
    """The encounter definitions live in data/npc_encounters.json (they were a
    1,750-line literal in this module until the 2026-10 quest pass)."""
    import json
    from paths import data_path
    with open(data_path('data', 'npc_encounters.json'), encoding='utf-8') as f:
        return json.load(f)


ENCOUNTERS = _load_encounters()


# ── Spawn level selection ────────────────────────────────────────────

def select_encounter_levels(seed: int | None = None) -> dict:
    """Return {level_num: encounter_dict} for a game run.

    One encounter guaranteed per 10-level block, chosen from 3 candidates.
    Never spawns on boss levels (20, 40, 60, 80, 100).
    """
    rng = random.Random(seed)
    placements: dict[int, dict] = {}

    for block_num, block_lo, block_hi in _BLOCKS:
        candidates = [e for e in ENCOUNTERS if e['block'] == block_num
                       and not e.get('trigger_item')]
        triggered  = [e for e in ENCOUNTERS if e['block'] == block_num
                       and e.get('trigger_item')]

        # Pool: all non-triggered + up to 1 triggered
        pool = list(candidates)
        if triggered:
            pool.append(rng.choice(triggered))
        if not pool:
            continue
        rng.shuffle(pool)

        enc = pool[0]

        # Pick a level within the block, excluding boss levels
        valid_levels = [lv for lv in range(block_lo, block_hi + 1)
                        if lv not in _BOSS_LEVELS]
        if not valid_levels:
            continue
        level = rng.choice(valid_levels)
        placements[level] = enc

    # Gold costs and rewards at today's scale (economy.py), once, here.
    import economy
    return {lvl: economy.price_encounter(enc) for lvl, enc in placements.items()}


def get_trigger_item_levels(placements: dict) -> dict:
    """Return {item_id: spawn_level} for triggered encounters.

    The trigger item spawns `trigger_level_offset` levels before the NPC.
    """
    triggers: dict[str, int] = {}
    for level, enc in placements.items():
        item_id = enc.get('trigger_item')
        if item_id:
            offset = enc.get('trigger_level_offset', 1)
            spawn_level = max(1, level - offset)
            triggers[item_id] = spawn_level
    return triggers


# ── Cost / reward checking ───────────────────────────────────────────

def can_pay_cost(player, cost: dict | None, player_gold: int) -> tuple[bool, str]:
    """Check if the player can afford a cost. Returns (can_pay, fail_message)."""
    if cost is None:
        return True, ''

    ctype = cost['type']

    if ctype == 'food':
        from items import Food, Ingredient
        has = any(isinstance(i, (Food, Ingredient)) for i in player.inventory)
        return (True, '') if has else (False, "You have no food to give.")

    if ctype == 'healing_potion':
        from items import Potion, Scroll, Wand
        # Accept: healing potions, heal spell (costs MP), healing scrolls, healing wands
        has_potion = any(isinstance(i, Potion) and getattr(i, 'effect', '') in ('heal', 'extra_heal', 'full_heal')
                         for i in player.inventory)
        has_spell = 'heal_spell' in getattr(player, 'known_spells', {}) and player.mp >= player.known_spells.get('heal_spell', 99)
        has_scroll = any(isinstance(i, Scroll) and 'heal' in getattr(i, 'effect', '').lower()
                         for i in player.inventory)
        has_wand = any(isinstance(i, Wand) and 'heal' in getattr(i, 'effect', '').lower()
                       and getattr(i, 'charges', 0) > 0
                       for i in player.inventory)
        has = has_potion or has_spell or has_scroll or has_wand
        return (True, '') if has else (False, "You have no way to heal them.")

    if ctype == 'potion':
        from items import Potion
        has = any(isinstance(i, Potion) for i in player.inventory)
        return (True, '') if has else (False, "You have no potions to give.")

    if ctype == 'scroll':
        from items import Scroll
        has = any(isinstance(i, Scroll) for i in player.inventory)
        return (True, '') if has else (False, "You have no scrolls to spare.")

    if ctype == 'weapon':
        from items import Weapon
        has = any(isinstance(i, Weapon) for i in player.inventory)
        return (True, '') if has else (False, "You have no weapon to give.")

    if ctype == 'gold':
        amt = cost['amount']
        return (True, '') if player_gold >= amt else (False, f"You need {amt} gold.")

    if ctype == 'hp_percent':
        pct = cost['amount']
        cost_hp = max(5, int(player.hp * pct / 100))
        if player.hp > cost_hp + 5:
            return True, ''
        return False, "You are too injured to survive that."

    if ctype == 'max_hp':
        if player.max_hp > cost['amount'] + 10:
            return True, ''
        return False, "You are too frail to survive that."

    if ctype == 'sp':
        if player.sp >= cost['amount']:
            return True, ''
        return False, "You are too exhausted."

    if ctype == 'random_item':
        # Used as a cost, check if player has an item of the requested category
        from items import Scroll, Potion, Food, Weapon
        cat = cost.get('category', 'scroll')
        cat_map = {'scroll': Scroll, 'potion': Potion, 'food': Food, 'weapon': Weapon}
        cls = cat_map.get(cat)
        if cls and any(isinstance(i, cls) for i in player.inventory):
            return True, ''
        return False, f"You have no {cat} to offer."

    if ctype == 'hp':
        if player.hp > cost['amount'] + 5:
            return True, ''
        return False, "You are too injured to afford that."

    if ctype == 'mp':
        if player.mp >= cost['amount']:
            return True, ''
        return False, "You don't have enough mana."

    if ctype == 'triggered_item':
        # The trigger item should be in inventory, checked by caller
        return True, ''

    if ctype == 'accept_item':
        # Accepting a burden always possible
        return True, ''

    if ctype == 'spawn_deadite_ambush':
        # Always possible, the Deadite attacks you
        return True, ''

    return True, ''


def get_inventory_filter(cost: dict | None) -> str | None:
    """Return the inventory filter type for costs that need item selection.

    Returns None if no inventory selection is needed.
    """
    if cost is None:
        return None
    ctype = cost['type']
    if ctype in ('food', 'healing_potion', 'potion', 'scroll', 'weapon'):
        return ctype
    return None


# ── Judgment ─────────────────────────────────────────────────────────

_JUDGMENT_TIERS = [
    (-10, -6, 'abaddon_empowered',
     "Michael weighs your soul and recoils.\n"
     "\"You have walked in darkness.\"\n"
     "The scales crash to the ground. A terrible power surges\n"
     "toward the Pit below.\n\n"
     "Below, the Destroyer grows stronger on what was done above."),

    (-5, -1, 'locusts_strengthened',
     "Michael weighs your soul and frowns.\n"
     "\"Your deeds are wanting.\"\n"
     "The scales tip toward shadow. A buzzing fills the air.\n\n"
     "THE LOCUST SWARMS GROW LARGER AND MORE NUMEROUS."),

    (0, 0, 'silence',
     "Michael weighs your soul.\n"
     "The scales balance perfectly, and remain cold.\n"
     "\"You have done nothing worthy of praise or condemnation.\"\n\n"
     "The altar falls silent. Michael has nothing to hand you."),

    (1, 7, 'scales_granted',
     "Michael weighs your soul and nods.\n"
     "\"You have walked in light.\"\n"
     "The scales glow with golden fire. They lift from the altar\n"
     "and float into your hands.\n\n"
     "YOU RECEIVE THE SCALES OF MICHAEL."),

    # The Sword at 8 or more. It used to need exactly 10, and a run offers
    # exactly ten chances at +1: one missed encounter in a hundred floors
    # put the game's best reward out of reach.
    (8, 10, 'sword_and_scales',
     "Michael descends in a pillar of white fire. He kneels.\n"
     "\"In all the ages of this world, few mortals have walked\n"
     "as you have walked. You gave when you had nothing.\n"
     "You sacrificed when it would have been easier to take.\"\n"
     "He places a flaming sword in your hands and anoints\n"
     "your brow with light.\n"
     "\"Rise, Paladin. Chosen of God.\n"
     "The Destroyer will know your name.\"\n\n"
     "YOU RECEIVE THE SWORD AND SCALES OF MICHAEL.\n"
     "YOU ARE ANOINTED PALADIN AND CHOSEN OF GOD."),
]


def judge_karma(karma: int) -> tuple[str, str]:
    """Return (outcome_key, narrative_text) for the given karma score."""
    karma = max(-10, min(10, karma))
    for lo, hi, key, text in _JUDGMENT_TIERS:
        if lo <= karma <= hi:
            return key, text
    # Fallback (should be unreachable since loop covers clamped range)
    if karma >= 8:
        return _JUDGMENT_TIERS[4][2], _JUDGMENT_TIERS[4][3]
    if karma > 0:
        return _JUDGMENT_TIERS[3][2], _JUDGMENT_TIERS[3][3]
    if karma < -5:
        return _JUDGMENT_TIERS[0][2], _JUDGMENT_TIERS[0][3]
    if karma < 0:
        return _JUDGMENT_TIERS[1][2], _JUDGMENT_TIERS[1][3]
    return _JUDGMENT_TIERS[2][2], _JUDGMENT_TIERS[2][3]


# Assign NPC sprites for map rendering
_KARMA_SPRITES = {
    'elara_amulet': 'npc_lost_girl', 'brother_aldous': 'npc_dying_monk',
    'marta_ratchatcher': 'npc_rat_catcher', 'sir_aldric': 'npc_burdened_knight',
    'tam_thief': 'npc_young_thief', 'helena_cartographer': 'npc_injured_scholar',
    'marcus_sword': 'npc_grieving_father', 'blinded_soldier': 'npc_blinded_soldier',
    'dying_messenger': 'npc_dying_courier', 'deadite_woman': 'npc_deadite_woman',
    'sister_marguerite': 'npc_starving_nun', 'chained_priest': 'npc_chained_priest',
    'old_konstantin': 'npc_old_warrior', 'apprentice_healer': 'npc_poisoned_herbalist',
    'ghost_grave': 'npc_ghost_edwin', 'deserter': 'npc_deserter',
    'blind_seer': 'npc_blind_seer', 'trapped_seraph': 'npc_caged_angel',
    'weeping_mother': 'npc_weeping_ghost', 'ser_brennan': 'npc_dying_knight',
    'cursed_scholar': 'npc_cursed_scholar', 'fairy_jar': 'npc_trapped_fairy',
    'penitent': 'npc_penitent', 'roderic_shield': 'npc_young_knight',
    'forgotten_prisoner': 'npc_forgotten_prisoner', 'fallen_paladin': 'npc_fallen_paladin',
    'azarael_demon': 'npc_bound_demon', 'child_shrine': 'npc_small_shrine',
    'dying_prophet': 'npc_dying_prophet', 'petrified_adventurer': 'npc_stone_statue',
    'last_merchant': 'npc_lost_merchant',
}
for _enc in ENCOUNTERS:
    if 'sprite_id' not in _enc:
        _enc['sprite_id'] = _KARMA_SPRITES.get(_enc['tag'], 'npc_traveler')
