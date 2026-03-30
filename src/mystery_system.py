"""
mystery_system.py -- Mystery altars, key items, and encounter logic.

Each mystery is a special encounter that can appear once per dungeon run
within a specific floor range. The player must approach an altar, meet
requirements, and complete a challenge (quiz or physical) to earn rewards.
"""

import random


# ---------------------------------------------------------------------------
# MYSTERIES dictionary
# ---------------------------------------------------------------------------

MYSTERIES = {
    'sphinx': {
        'name': "The Sphinx",
        'floor_range': (22, 35),
        'symbol': 'W',
        'color': (218, 165, 32),  # gold
        'description': "A towering stone sphinx fixes you with ancient eyes. 'Answer my riddles or perish.'",
        'key_item': None,
        'gold_cost': 0,
        'challenge': {'mode': 'escalator_threshold', 'subject': 'philosophy', 'tier': 3, 'threshold': 4, 'total': 6},
        'reward': {'WIS': 2, 'INT': 1},
        'reward_text': "The Sphinx crumbles. Ancient wisdom floods your mind. WIS+2, INT+1.",
        'fail_text': "The Sphinx dismisses you. Perhaps another time.",
        'invert_result': False,
    },
    'pandora': {
        'name': "Pandora's Coffer",
        'floor_range': (20, 30),
        'symbol': '[',
        'color': (180, 30, 30),  # dark red
        'description': "A sealed obsidian coffer. A warning is etched: 'Do not open.' The keyhole glows red.",
        'key_item': {'name': "Pandora's Key", 'symbol': 'P', 'color': (180, 30, 30), 'weight': 0.5},
        'gold_cost': 0,
        'challenge': {'mode': 'threshold', 'subject': 'economics', 'tier': 2, 'threshold': 4, 'total': 5},
        'reward': {'effects': ['magic_resist', 'displacement'], 'gold': 300},
        'reward_text': "The box opens wrong -- chaos floods out... and so does Hope. Permanent magic resist, displacement, +300 gold.",
        'fail_text': "You open it 'correctly' -- but nothing is inside. Only gold.",
        'fail_reward': {'gold': 100},
        'invert_result': True,  # INVERTED: failure quiz = actual reward
    },
    'grail': {
        'name': "Chapel of the Grail",
        'floor_range': (45, 55),
        'symbol': 'U',
        'color': (200, 200, 255),  # silver-blue
        'description': "A ruined chapel. A chalice rests on the altar, glowing faintly.",
        'key_item': {'name': "A Chalice", 'symbol': 'U', 'color': (200, 200, 255), 'weight': 1.0},
        'gold_cost': 0,
        'challenge': {'mode': 'threshold', 'subject': 'theology', 'tier': 3, 'threshold': 5, 'total': 7},
        'reward': {'max_hp': 30, 'CON': 2},
        'reward_text': "You are found worthy. Max HP+30, CON+2.",
        'fail_text': "You are not yet worthy of the Grail.",
        'invert_result': False,
    },
    'fleece': {
        'name': "The Fleece Altar",
        'floor_range': (38, 50),
        'symbol': '+',
        'color': (218, 165, 32),  # golden
        'description': "An altar carved with the image of a ram. Hung above it should be the Golden Fleece.",
        'key_item': {'name': "Golden Fleece", 'symbol': '+', 'color': (218, 165, 32), 'weight': 2.0},
        'gold_cost': 0,
        'challenge': {'mode': 'chain', 'subject': 'animal', 'tier': 3, 'threshold': 5, 'max_chain': None},
        'reward': {'effects': ['regenerating', 'poison_resist']},
        'reward_text': "The Fleece accepts you. Permanent regeneration and poison resistance.",
        'fail_text': "The serpent guardian rejects your attempt.",
        'invert_result': False,
    },
    'mimir': {
        'name': "Mimir's Well",
        'floor_range': (42, 55),
        'symbol': 'o',
        'color': (50, 120, 200),  # dark teal-blue
        'description': "A dark well with runes carved around its rim. The water below holds all wisdom. A price is implied.",
        'key_item': None,
        'gold_cost': 0,
        'stat_cost': {'PER': -1},  # applied before quiz starts
        'challenge': {'mode': 'chain', 'subject': 'philosophy', 'tier': 4, 'threshold': 6, 'max_chain': None},
        'reward': {'INT': 3, 'all_timer_bonus': 1},
        'reward_text': "You drink deep. INT+3, all quiz timers+1s. You feel slightly less perceptive.",
        'fail_text': "Your mind cannot hold the well's knowledge. The cost was paid for nothing.",
        'invert_result': False,
    },
    'mjolnir': {
        'name': "The Dwarven Forge",
        'floor_range': (33, 45),
        'symbol': '^',
        'color': (255, 140, 0),  # orange
        'description': "A dwarven forge, still hot. The anvil awaits a hammer worthy of reforging.",
        'key_item': {'name': "Mjolnir (unfinished)", 'symbol': '^', 'color': (255, 140, 0), 'weight': 8.0},
        'gold_cost': 0,
        'challenge': {'mode': 'escalator_threshold', 'subject': 'math', 'tier': 3, 'threshold': 4, 'total': 6},
        'reward': {'special': 'forge_mjolnir', 'STR': 2},
        'reward_text': "The dwarves' work is complete. Mjolnir reforged (+4 enchant). STR+2.",
        'fail_text': "The rhythm falters. The hammer remains unfinished.",
        'invert_result': False,
    },
    'crucible': {
        'name': "Alchemist's Crucible",
        'floor_range': (10, 22),
        'symbol': 'V',
        'color': (150, 150, 160),  # gray
        'description': "An alchemist's crucible. The inscription reads: 'From base matter, golden truth.'",
        'key_item': {'name': "Lead Ingot", 'symbol': 'V', 'color': (150, 150, 160), 'weight': 5.0},
        'gold_cost': 0,
        'challenge': {'mode': 'threshold', 'subject': 'philosophy', 'tier': 1, 'threshold': 3, 'total': 4},
        'reward': {'gold': 400},
        'reward_text': "The lead transmutes. 400 gold coins appear.",
        'fail_text': "The transmutation fails. The lead remains lead.",
        'invert_result': False,
    },
    'oracle': {
        'name': "The Oracle's Rift",
        'floor_range': (25, 35),
        'symbol': 'D',
        'color': (160, 80, 200),  # purple
        'description': "A smoking rift in the stone, tended by a stone priestess. Visions await those who offer tribute.",
        'key_item': None,
        'gold_cost': 50,
        'challenge': {'mode': 'threshold', 'subject': 'theology', 'tier': 3, 'threshold': 5, 'total': 7},
        'reward': {'special': 'oracle_reveal'},
        'reward_text': "The Oracle speaks. Three hidden paths revealed.",
        'fail_text': "The Oracle falls silent. Your tribute is forfeit.",
        'invert_result': False,
    },
    'solomon': {
        'name': "Solomon's Tribunal",
        'floor_range': (30, 42),
        'symbol': '*',
        'color': (255, 220, 50),  # bright gold
        'description': "A throne room with two doors. A stone inscription reads: 'Judge wisely and be rewarded.'",
        'key_item': {'name': "Seal of Solomon", 'symbol': '*', 'color': (255, 220, 50), 'weight': 0.5},
        'gold_cost': 0,
        'challenge': {'mode': 'threshold', 'subject': 'history', 'tier': 3, 'threshold': 6, 'total': 8},
        'reward': {'WIS': 2, 'special': 'ring_of_command'},
        'reward_text': "Your wisdom is acknowledged. WIS+2. A Ring of Command placed in your hand.",
        'fail_text': "Your judgment is found wanting.",
        'invert_result': False,
    },
    'fisher_king': {
        'name': "The Fisher King's Hall",
        'floor_range': (58, 72),
        'symbol': '+',
        'color': (100, 220, 100),  # light green
        'description': "A desolate hall. A wounded king lies motionless. Something nearby could help -- if you ask rightly.",
        'key_item': {'name': "Healing Herb", 'symbol': '+', 'color': (100, 220, 100), 'weight': 0.5},
        'gold_cost': 0,
        'challenge': {'mode': 'threshold', 'subject': 'theology', 'tier': 4, 'threshold': 5, 'total': 7},
        'reward': {'max_hp': 30, 'special': 'fisher_cooldown'},
        'reward_text': "The king heals. He blesses you: Max HP+30, prayer cooldown halved forever.",
        'fail_text': "You asked the wrong thing. The king remains wounded.",
        'invert_result': False,
    },
    'sisyphus': {
        'name': "Sisyphus' Hill",
        'floor_range': (78, 92),
        'symbol': '*',
        'color': (140, 140, 140),  # stone gray
        'description': "A steep slope carved into the stone. At its base lies an enormous boulder with a worn handprint.",
        'key_item': {'name': "The Boulder", 'symbol': '*', 'color': (140, 140, 140), 'weight': 30.0},
        'gold_cost': 0,
        'challenge': {'mode': 'physical', 'tiles': 25},  # walk 25 tiles over carry limit while holding boulder
        'reward': {'STR': 3, 'INT': 1},
        'reward_text': "The boulder vanishes. Your body is transformed by the effort. STR+3, INT+1.",
        'fail_text': "",
        'invert_result': False,
    },
    'cauldron': {
        'name': "The Black Cauldron",
        'floor_range': (14, 26),
        'symbol': 'Q',
        'color': (40, 140, 100),  # dark green
        'description': "A bubbling cauldron of Celtic make. It demands a tribute of three prepared meals.",
        'key_item': None,  # no key -- requires 3 Food items in inventory
        'gold_cost': 0,
        'challenge': {'mode': 'escalator_chain', 'subject': 'cooking', 'tier': 2, 'threshold': 5, 'max_chain': None},
        'reward': {'effects': ['searching', 'warning']},
        'reward_text': "The cauldron's magic fills you. Permanent searching and danger-warning.",
        'fail_text': "The cauldron rejects your cooking skill.",
        'invert_result': False,
    },
}


# ---------------------------------------------------------------------------
# Non-Item classes (sit in ground_items like GoldPile)
# ---------------------------------------------------------------------------

class MysteryKeyItem:
    """A key item required to activate a mystery altar. Can be picked up."""

    def __init__(self, mystery_id: str, name: str, symbol: str, color: tuple, weight: float):
        self.mystery_id   = mystery_id
        self.id           = f'mystery_key_{mystery_id}'
        self.name         = name
        self.symbol       = symbol
        self.color        = tuple(color)
        self.weight       = float(weight)
        self.min_level    = 1
        self.count        = 1
        self.not_pickable = False
        self.x: int = 0
        self.y: int = 0
        # For item display compatibility
        self.lore         = ''
        self.identified   = True
        self.item_class   = 'mystery_key'


class MysteryAltar:
    """An altar that the player interacts with to trigger a mystery. Cannot be picked up."""

    def __init__(self, mystery_id: str, x: int, y: int):
        self.mystery_id   = mystery_id
        self.id           = f'mystery_altar_{mystery_id}'
        m                 = MYSTERIES[mystery_id]
        self.name         = m['name']
        self.symbol       = m['symbol']
        self.color        = tuple(m['color'])
        self.weight       = 0
        self.min_level    = 1
        self.count        = 1
        self.not_pickable = True
        self.activated    = False
        self.x            = x
        self.y            = y
        self.lore         = ''
        self.identified   = True
        self.item_class   = 'mystery_altar'


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def get_mystery_altar(mystery_id: str, x: int, y: int) -> MysteryAltar:
    """Create a MysteryAltar for the given mystery at (x, y)."""
    return MysteryAltar(mystery_id, x, y)


def get_mystery_key(mystery_id: str, x: int, y: int) -> MysteryKeyItem:
    """Create a MysteryKeyItem for the given mystery at (x, y)."""
    m   = MYSTERIES[mystery_id]
    ki  = m['key_item']
    key = MysteryKeyItem(
        mystery_id,
        ki['name'],
        ki['symbol'],
        ki['color'],
        ki['weight'],
    )
    key.x = x
    key.y = y
    return key


# ---------------------------------------------------------------------------
# Spawn function
# ---------------------------------------------------------------------------

def spawn_mystery_for_level(level: int, rooms, dungeon, ground_items: list,
                             rng: random.Random):
    """
    Optionally place a mystery altar (and key item) for the given level.

    Returns (altar, key_item_or_None) or None if no mystery spawns.
    Caller appends both objects to ground_items.
    """
    # Build list of mysteries eligible for this level
    eligible = [
        mid for mid, m in MYSTERIES.items()
        if m['floor_range'][0] <= level <= m['floor_range'][1]
    ]
    if not eligible:
        return None

    # 60% chance to spawn a mystery if any are eligible
    if rng.random() > 0.60:
        return None

    mystery_id = rng.choice(eligible)
    m          = MYSTERIES[mystery_id]

    # Need at least 2 rooms besides start: one for altar, one for key
    non_start_rooms = rooms[1:]
    if not non_start_rooms:
        return None

    # Place altar in a random non-start room
    altar_room = rng.choice(non_start_rooms)
    ax, ay     = _random_walkable_tile(altar_room, dungeon, ground_items, rng)
    if ax is None:
        return None

    altar = get_mystery_altar(mystery_id, ax, ay)

    key_item = None
    if m['key_item'] is not None:
        # Place key in a DIFFERENT room (if possible)
        key_rooms = [r for r in non_start_rooms if r is not altar_room]
        if not key_rooms:
            key_rooms = non_start_rooms[:]
        key_room = rng.choice(key_rooms)
        kx, ky   = _random_walkable_tile(key_room, dungeon, ground_items, rng)
        if kx is not None:
            key_item = get_mystery_key(mystery_id, kx, ky)

    return altar, key_item


def _random_walkable_tile(room, dungeon, ground_items: list, rng: random.Random):
    """Return a random walkable tile in the room that isn't already occupied."""
    tiles = list(room.inner_tiles())
    rng.shuffle(tiles)
    for tx, ty in tiles:
        if not dungeon.is_walkable(tx, ty):
            continue
        if any(i.x == tx and i.y == ty for i in ground_items):
            continue
        return tx, ty
    return None, None


# ---------------------------------------------------------------------------
# Activation requirements
# ---------------------------------------------------------------------------

def can_activate(mystery_id: str, player, player_gold: int) -> tuple:
    """
    Check whether the player meets requirements to activate this mystery.

    Returns (True, '') if requirements are met, or (False, reason_string).
    """
    m = MYSTERIES[mystery_id]

    # Gold cost
    if m.get('gold_cost', 0) > 0:
        if player_gold < m['gold_cost']:
            return False, f"You need {m['gold_cost']} gold as tribute."

    # Key item requirement
    if m['key_item'] is not None and mystery_id != 'sisyphus':
        key = get_key_item_from_inventory(mystery_id, player)
        if key is None:
            ki_name = m['key_item']['name']
            return False, f"You need {ki_name}."

    # Sisyphus: boulder must be in inventory (treated as key item)
    if mystery_id == 'sisyphus':
        key = get_key_item_from_inventory(mystery_id, player)
        if key is None:
            return False, "You need The Boulder."

    # Cauldron: requires 3 prepared Food items
    if mystery_id == 'cauldron':
        foods = get_cauldron_food_items(player)
        if len(foods) < 3:
            have = len(foods)
            return False, f"The cauldron demands three prepared meals. You have {have}."

    return True, ''


def get_key_item_from_inventory(mystery_id: str, player) -> object:
    """Return the matching MysteryKeyItem from player inventory, or None."""
    for item in player.inventory:
        if hasattr(item, 'mystery_id') and item.mystery_id == mystery_id:
            return item
    return None


def consume_key_item(mystery_id: str, player) -> bool:
    """Remove the key item for mystery_id from player inventory. Returns True if removed."""
    key = get_key_item_from_inventory(mystery_id, player)
    if key is not None:
        if key in player.inventory:
            player.inventory.remove(key)
            return True
    return False


def get_cauldron_food_items(player) -> list:
    """Return up to 3 Food items from player inventory (cooked food only)."""
    from items import Food
    return [i for i in player.inventory if isinstance(i, Food)][:3]


# ---------------------------------------------------------------------------
# Oracle reveal helper
# ---------------------------------------------------------------------------

def _oracle_reveal_quirks(player, game):
    """Show cryptic hints about 3 locked quirks after Oracle success."""
    try:
        from quirk_system import _QUIRK_EFFECTS
    except ImportError:
        game.add_message("The Oracle sees strange things... but cannot speak them.", 'info')
        return

    locked = [qid for qid in _QUIRK_EFFECTS
              if qid not in getattr(player, 'unlocked_quirks', set())]
    if not locked:
        game.add_message("The Oracle sees you have walked all paths. Remarkable.", 'info')
        return

    chosen = random.sample(locked, min(3, len(locked)))

    _HINTS = {
        'odin':        "Some wait long enough to perceive all things.",
        'mithridates': "The great king survived every poison by tasting each one.",
        'tiresias':    "The blind prophet answered correctly while he could not see.",
        'penelope':    "She wove and unwove, ever patient. Armor is her art.",
        'orpheus':     "Music calmed beasts. He descended to find those he had lost.",
        'hermes':      "Speed is earned through many small steps.",
        'atalanta':    "Swiftness and precision over brute force.",
        'musashi':     "One precise strike, not many hurried ones.",
        'scheherazade':"She read and told stories before anyone knew their name.",
        'merlin':      "Wands were used before they were understood.",
        'prometheus':  "Suffering repeated and survived becomes strength.",
        'ragnarok':    "Descend so deep, with so little -- and survive.",
    }

    game.add_message("The Oracle speaks:", 'info')
    for qid in chosen:
        hint = _HINTS.get(qid, "A hidden path remains unexplored.")
        game.add_message(f"  \u2022 {hint}", 'info')


# ---------------------------------------------------------------------------
# Reward application
# ---------------------------------------------------------------------------

def apply_mystery_reward(mystery_id: str, player, game, success: bool):
    """Apply the reward (or fail_reward) for a completed mystery challenge."""
    m = MYSTERIES[mystery_id]

    if not success:
        # Apply fail_reward if any
        fail_rew = m.get('fail_reward', {})
        if 'gold' in fail_rew:
            game.player_gold = getattr(game, 'player_gold', 0) + fail_rew['gold']
            game.add_message(f"You find {fail_rew['gold']} gold inside.", 'loot')
        if m['fail_text']:
            game.add_message(m['fail_text'], 'warning')
        return

    reward = m['reward']

    # --- Stat bonuses ---
    for stat in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
        if stat in reward:
            player.apply_stat_bonus(stat, reward[stat])

    # --- Max HP bonus ---
    if 'max_hp' in reward:
        player.max_hp += reward['max_hp']
        player.hp = min(player.hp + reward['max_hp'], player.max_hp)

    # --- Permanent status effects ---
    for eff in reward.get('effects', []):
        player.add_effect(eff, -1)

    # --- Gold ---
    if 'gold' in reward:
        game.player_gold = getattr(game, 'player_gold', 0) + reward['gold']

    # --- All quiz timer bonus (Mimir) ---
    if 'all_timer_bonus' in reward:
        amt = reward['all_timer_bonus']
        for subj in ('math', 'geography', 'history', 'animal', 'cooking',
                     'science', 'philosophy', 'grammar', 'economics', 'theology'):
            b = getattr(player, 'quiz_timer_bonuses', {})
            b[subj] = b.get(subj, 0) + amt
            player.quiz_timer_bonuses = b

    # --- Special rewards ---
    special = reward.get('special')
    if special == 'forge_mjolnir':
        from items import Weapon
        mjolnir_def = {
            'id': 'mjolnir',
            'name': 'Mjolnir',
            'symbol': '^',
            'color': [255, 140, 0],
            'weight': 8.0,
            'min_level': 1,
            'item_class': 'weapon',
            'damage': '3d6',
            'damage_type': 'physical',
            'enchant_bonus': 4,
            'two_handed': True,
            'identified': True,
            'unidentified_name': 'Mjolnir',
            'quiz_tier': 5,
            'container_loot_tier': 'legendary',
            'baseDamage': 18,
            'damageTypes': ['blunt'],
            'chainMultipliers': [0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
        }
        weapon = Weapon(mjolnir_def)
        # Remove the old key item from inventory
        old = next((i for i in player.inventory
                    if getattr(i, 'mystery_id', None) == 'mjolnir'), None)
        if old:
            player.inventory.remove(old)
        player.add_to_inventory(weapon)
        game.add_message("Mjolnir, fully forged, appears in your pack!", 'loot')

    elif special == 'ring_of_command':
        from items import Accessory
        ring_def = {
            'id': 'ring_of_command',
            'name': 'Ring of Command',
            'symbol': '=',
            'color': [255, 220, 50],
            'weight': 0.1,
            'min_level': 1,
            'item_class': 'accessory',
            'effects': {'stat': 'WIS', 'amount': 1},
            'slot': 'ring',
            'identified': True,
            'unidentified_name': 'Ring of Command',
            'quiz_tier': 5,
        }
        ring = Accessory(ring_def)
        player.add_to_inventory(ring)
        game.add_message("A Ring of Command appears in your pack.", 'loot')

    elif special == 'oracle_reveal':
        _oracle_reveal_quirks(player, game)

    elif special == 'fisher_cooldown':
        # Mark player for permanent halved prayer cooldown
        player.quirk_progress['fisher_king_mystery_active'] = True

    game.add_message(m['reward_text'], 'loot')


# ---------------------------------------------------------------------------
# Merchant NPC
# ---------------------------------------------------------------------------

# How many items the merchant stocks at different level brackets
_MERCHANT_STOCK_COUNTS = [
    (1,  20,  4),
    (21, 50,  5),
    (51, 99,  6),
]

# Price multipliers by item class
_PRICE_MULT = {
    'weapon':     2.5,
    'armor':      2.0,
    'shield':     1.8,
    'accessory':  3.0,
    'scroll':     1.5,
    'potion':     1.2,
    'wand':       2.0,
    'spellbook':  2.5,
    'food':       0.8,
    'ammo':       0.6,
}
_BASE_PRICE = 20


def _merchant_price(item) -> int:
    """Compute a gold cost for one merchant item.  Price is intrinsic to the
    item (tier, class, weight) — better items cost more naturally."""
    weight = max(0.1, getattr(item, 'weight', 1.0))
    tier   = getattr(item, 'quiz_tier', 1) or 1
    ic     = getattr(item, 'item_class', 'misc')
    mult   = _PRICE_MULT.get(ic, 1.0)
    price  = int(_BASE_PRICE * mult * tier * weight)
    return max(5, price)


class MerchantNPC:
    """
    A travelling merchant placed on a dungeon floor.
    Not pickable; player presses T nearby to open the shop.
    """

    def __init__(self, x: int, y: int, stock: list, prices: list[int]):
        self.x            = x
        self.y            = y
        self.id           = 'merchant_npc'
        self.name         = "Svirfneblin Trader"
        self.symbol       = '@'
        self.color        = (180, 180, 220)   # pale grey-blue (deep gnome skin)
        self.weight       = 0
        self.min_level    = 1
        self.count        = 1
        self.not_pickable = True
        self.identified   = True
        self.item_class   = 'merchant'
        self.lore         = "A deep gnome trader who navigates the subterranean passages with ease, "\
                            "hauling wares between settlements no surface-dweller has ever seen."
        self.stock        = stock     # list of Item objects for sale
        self.prices       = prices    # parallel list of int prices
        self.sold_out     = False


def spawn_merchant(level: int, rooms, dungeon, ground_items: list,
                   rng: random.Random) -> 'MerchantNPC | None':
    """
    20% chance per floor to place a merchant in a non-starting room.
    Returns the MerchantNPC if placed, otherwise None.
    (Caller should append the result to ground_items.)
    """
    if rng.random() > 0.20:
        return None
    if len(rooms) < 3:
        return None

    from items import load_items
    import copy as _copy

    # Build item pool from multiple categories
    stock_items = []
    for cat in ('potion', 'scroll', 'weapon', 'armor', 'shield', 'accessory', 'wand', 'food', 'ammo'):
        try:
            pool = [i for i in load_items(cat) if getattr(i, 'min_level', 1) <= level]
            if pool:
                stock_items.extend(rng.choices(pool, k=min(2, len(pool))))
        except Exception:
            pass

    # 15% chance merchant has a Soul Sphere
    if rng.random() < 0.15:
        from items import Artifact
        sphere = Artifact({
            'id': 'soul_sphere',
            'name': 'Soul Sphere',
            'symbol': 'O',
            'color': [255, 80, 80],
            'item_class': 'artifact',
            'weight': 0.5,
            'min_level': 1,
            'lore': 'A sphere of crimson and ivory that hums with trapped souls. '
                    'Ancient texts say these vessels were used to bind creature spirits. '
                    'One wonders what might happen if it were hurled with force...',
        })
        stock_items.append(sphere)

    if not stock_items:
        return None

    # Deduplicate by id and cap count
    seen_ids: set = set()
    unique_stock = []
    for it in stock_items:
        iid = getattr(it, 'id', None)
        if iid and iid not in seen_ids:
            seen_ids.add(iid)
            unique_stock.append(_copy.copy(it))

    # Determine stock size for this level bracket
    n_stock = 4
    for lo, hi, n in _MERCHANT_STOCK_COUNTS:
        if lo <= level <= hi:
            n_stock = n
            break
    rng.shuffle(unique_stock)
    stock = unique_stock[:n_stock]
    prices = [_merchant_price(it) for it in stock]

    # Place in a non-starting room
    candidate_rooms = rooms[1:]
    room = rng.choice(candidate_rooms)
    tiles = [
        (rx, ry)
        for rx, ry in room.inner_tiles()
        if dungeon.tiles[ry][rx] == 3  # FLOOR constant
        and not any(gi.x == rx and gi.y == ry for gi in ground_items)
    ]
    if not tiles:
        return None

    mx, my = rng.choice(tiles)
    merchant = MerchantNPC(mx, my, stock, prices)
    return merchant
