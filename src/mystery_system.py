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
        'description': "A stone sphinx lies across the passage, woman-faced and lion-bodied. 'Thebes sent me its cleverest,' she says. 'I ate most of them. Answer.'",
        'key_item': None,
        'gold_cost': 0,
        'challenge': {'mode': 'escalator_threshold', 'subject': 'philosophy', 'tier': 3, 'threshold': 2, 'total': 6},
        'reward': {'WIS': 2, 'INT': 1},
        'reward_text': "The Sphinx gives one cry and throws herself from her perch, as her sister did at Thebes. Something of her long patience stays with you. (Wisdom +2, Intelligence +1)",
        'fail_text': "The Sphinx yawns. 'Not clever enough to be worth eating,' she says, and settles back into stone.",
        'invert_result': False,
    },
    'pandora': {
        'name': "Pandora's Coffer",
        'floor_range': (20, 30),
        'symbol': '[',
        'color': (180, 30, 30),  # dark red
        'description': "A coffer of black stone, cold to the touch. One line is cut into the lid: 'Do not open.' The lock looks as though it would yield to a practised hand.",
        'key_item': {'name': "Pandora's Key", 'symbol': 'P', 'color': (180, 30, 30), 'weight': 0.5},
        'gold_cost': 0,
        'challenge': {'mode': 'threshold', 'subject': 'economics', 'tier': 2, 'threshold': 2, 'total': 5},
        'reward': {'effects': ['magic_resist', 'displacement'], 'gold': 300},
        'reward_text': "The lock slips, the lid flies back, and every sorrow in the box goes howling past you into the dark. One small thing is left at the bottom. It is Hope, and it is yours. (Magic Resistance, Displacement, 300 gold)",
        'fail_text': "The lock opens cleanly under your hand. Inside is a neat stack of coin and nothing else. Whatever else was kept here stays shut in.",
        'fail_reward': {'gold': 100},
        'invert_result': True,  # INVERTED: failure quiz = actual reward
    },
    'grail': {
        'name': "Chapel of the Grail",
        'floor_range': (45, 55),
        'symbol': 'U',
        'color': (200, 200, 255),  # silver-blue
        'description': "A ruined chapel, roofless and quiet. The altar stone is bare, with a ring worn into it where a cup once stood.",
        'key_item': {'name': "Tarnished Chalice", 'symbol': 'U', 'color': (200, 200, 255), 'weight': 1.0},
        'gold_cost': 0,
        'challenge': {'mode': 'threshold', 'subject': 'theology', 'tier': 3, 'threshold': 2, 'total': 7},
        'reward': {'max_hp': 30, 'CON': 2},
        'reward_text': "The cup fills from nowhere with clear water. You drink, and the ache of the whole descent leaves you. (Max HP +30, Constitution +2)",
        'fail_text': "The cup stays empty and the chapel stays silent. Galahad's seat is not for everyone.",
        'invert_result': False,
    },
    'fleece': {
        'name': "The Fleece Altar",
        'floor_range': (38, 50),
        'symbol': '+',
        'color': (218, 165, 32),  # golden
        'description': "A bare oak, and beneath it an altar carved with a ram. A great serpent lies coiled in the roots. It has not blinked since Colchis.",
        'key_item': {'name': "Golden Fleece", 'symbol': '+', 'color': (218, 165, 32), 'weight': 2.0},
        'gold_cost': 0,
        'challenge': {'mode': 'chain', 'subject': 'animal', 'tier': 3, 'threshold': 2, 'max_chain': None},
        'reward': {'effects': ['regenerating', 'poison_resist']},
        'reward_text': "The serpent lowers its head and lets you hang the Fleece where it belongs. Its gold warms you through. (Regeneration, Poison Resistance)",
        'fail_text': "The serpent takes the Fleece out of your hands and draws it down into the roots. It did not think much of your woodcraft.",
        'invert_result': False,
    },
    'mimir': {
        'name': "Mimir's Well",
        'floor_range': (42, 55),
        'symbol': 'o',
        'color': (50, 120, 200),  # dark teal-blue
        'description': "A dark well under a root as thick as a tower. A severed head floats in it with its eyes open. 'Odin paid an eye for one horn of this,' says Mimir. 'I do not give credit.'",
        'key_item': None,
        'gold_cost': 0,
        # PER-1 is applied before the quiz starts; it is deliberately KEPT on
        # failure per feedback_resource_loss_is_the_penalty.md — the price
        # of insight is paid up front and does not refund if the player
        # cannot hold the well's knowledge.
        'stat_cost': {'PER': -1},  # applied before quiz starts; not refunded on fail
        'challenge': {'mode': 'chain', 'subject': 'philosophy', 'tier': 4, 'threshold': 3, 'max_chain': None},
        'reward': {'WIS': 1, 'INT': 1},
        'reward_text': "The water is so cold it rings in your teeth. For one breath you see how everything fits. Most of it fades. Enough stays. (Wisdom +1, Intelligence +1)",
        'fail_text': "The water runs through your mind like a sieve. Mimir keeps the price. He always does.",
        'invert_result': False,
    },
    'mjolnir': {
        'name': "Brokkr's Anvil",
        'floor_range': (33, 45),
        'symbol': '^',
        'color': (255, 140, 0),  # orange
        'description': "A dwarven forge, still hot, with the bellows stopped mid-stroke. The story goes that a fly bit the smith's eyelid at the worst moment. Someone has to finish the count.",
        'key_item': {'name': "Unfinished Hammer-Head", 'symbol': '^', 'color': (255, 140, 0), 'weight': 8.0},
        'gold_cost': 0,
        'challenge': {'mode': 'escalator_threshold', 'subject': 'math', 'tier': 3, 'threshold': 2, 'total': 6},
        'reward': {'special': 'forge_mjolnir', 'STR': 2},
        'reward_text': "You keep the bellows steady to the last stroke. The handle still comes out short. Nobody has ever complained about the rest of it. (Strength +2)",
        'fail_text': "The count slips and the iron cools grey. The hammer-head is slag now.",
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
        'reward_text': "The lead shivers, runs bright, and sets as gold. The alchemists were right about one thing. (400 gold)",
        'fail_text': "The crucible spits and goes dark. The lead has boiled away to a grey smear.",
        'invert_result': False,
    },
    'oracle': {
        'name': "The Oracle's Rift",
        'floor_range': (25, 35),
        'symbol': 'D',
        'color': (160, 80, 200),  # purple
        'description': "Sweet smoke rises from a crack in the floor. A priestess sits over it on a three-legged stool, and she has plainly been sitting there a long time. A bronze bowl waits for coin.",
        'key_item': None,
        'gold_cost': 50,
        'challenge': {'mode': 'threshold', 'subject': 'theology', 'tier': 3, 'threshold': 2, 'total': 7},
        'reward': {'special': 'oracle_reveal'},
        'reward_text': "The Oracle speaks. Three hidden paths revealed.",
        'fail_text': "The priestess says something in hexameter that could mean anything. The coin stays in the bowl.",
        'invert_result': False,
    },
    'solomon': {
        'name': "Solomon's Tribunal",
        'floor_range': (30, 42),
        'symbol': '*',
        'color': (255, 220, 50),  # bright gold
        'description': "Two women carved in stone face an empty judgment seat, and a carved infant lies between them. A sword hangs on the wall behind. The inscription is one word: 'Judge.'",
        'key_item': {'name': "Seal of Solomon", 'symbol': '*', 'color': (255, 220, 50), 'weight': 0.5},
        'gold_cost': 0,
        'challenge': {'mode': 'threshold', 'subject': 'history', 'tier': 3, 'threshold': 3, 'total': 4},
        'reward': {'WIS': 2, 'special': 'ring_of_command'},
        'reward_text': "One stone mother lowers her arms and the other turns her face away. The seat finds your judgment sound. (Wisdom +2, and a signet from the throne room)",
        'fail_text': "Your judgment is found wanting.",
        'invert_result': False,
    },
    'fisher_king': {
        'name': "The Fisher King's Hall",
        'floor_range': (58, 72),
        'symbol': '+',
        'color': (100, 220, 100),  # light green
        'description': "A cold hall with a dead hearth. A king lies on a litter beside it, wounded through the thigh, and watches you come in. He seems to be waiting for you to say something.",
        'key_item': {'name': "Healing Herb", 'symbol': '+', 'color': (100, 220, 100), 'weight': 0.5},
        'gold_cost': 0,
        'challenge': {'mode': 'threshold', 'subject': 'theology', 'tier': 4, 'threshold': 2, 'total': 7},
        'reward': {'max_hp': 30, 'special': 'fisher_cooldown'},
        'reward_text': "You ask what ails him, which is all anyone ever had to do. The king stands. Somewhere far above, rain begins to fall on the Waste Land. (Max HP +30. Heaven hears you twice as often.)",
        'fail_text': "You talk of everything but the wound. The king turns his face to the wall.",
        'invert_result': False,
    },
    'sisyphus': {
        'name': "Sisyphus' Hill",
        'floor_range': (78, 92),
        'symbol': '*',
        'color': (140, 140, 140),  # stone gray
        'description': "A steep slope carved into the stone. At its base lies an enormous boulder with a worn handprint.",
        'key_item': {'name': "The Boulder", 'symbol': '*', 'color': (140, 140, 140), 'weight': 20.0},
        'gold_cost': 0,
        'challenge': {'mode': 'physical', 'tiles': 15},  # walk 15 tiles over carry limit while holding boulder
        'reward': {'STR': 2, 'INT': 1},
        'reward_text': "The boulder reaches the top and, for once, stays there. One must imagine you happy. (Strength +2, Intelligence +1)",
        'fail_text': "",
        'invert_result': False,
    },
    'brendan': {
          'name': "The Navigator's Boat",
          'floor_range': (5, 9),
          'symbol': 'B',
          'color': (90, 160, 190),
          'description': 'A leather boat no bigger than a bathtub sits on dry stone, with a sea '
                         'chart nailed to its mast. The chart shows an island with an eye. A note '
                         "beneath it reads: 'Mark where you are, pilgrim, and take what the voyage "
                         "taught me.'",
          'key_item': None,
          'gold_cost': 0,
          'challenge': {   'mode': 'threshold',
                           'subject': 'geography',
                           'tier': 1,
                           'threshold': 2,
                           'total': 3},
          'reward': {'PER': 1, 'gold': 80},
          'reward_text': "You set your finger on the chart and the island's eye winks. Brendan of "
                         'Clonfert said Mass on that island one Easter, until it swam away. It was a '
                         'whale. You will look twice at solid ground from now on, and there are '
                         'coins under the thwart.',
          'fail_text': 'The chart rolls itself up. Wherever you are, it is not where you pointed.',
          'invert_result': False,
          },
    'jerome': {
          'name': "The Translator's Desk",
          'floor_range': (73, 77),
          'symbol': 'J',
          'color': (200, 170, 110),
          'description': "A scholar's desk in a cave, with a skull for a paperweight and a lion "
                         'asleep beneath it like a large dog. A half-translated page lies under the '
                         "lamp. In the margin, in a tired hand: 'Finish the sentence properly or "
                         "leave it alone.'",
          'key_item': None,
          'gold_cost': 0,
          'challenge': {   'mode': 'threshold',
                           'subject': 'grammar',
                           'tier': 4,
                           'threshold': 3,
                           'total': 4},
          'reward': {'WIS': 2, 'INT': 1},
          'reward_text': 'The sentence holds. The lion opens one eye, approves, and goes back to '
                         'sleep. Jerome spent half a lifetime in Bethlehem turning Hebrew and Greek '
                         'into plain Latin, and would not let a hard word go by. Some of his '
                         'stubbornness stays with you.',
          'fail_text': 'The lion sighs. The page is exactly as unfinished as you found it.',
          'invert_result': False,
          },
    'cauldron': {
        'name': "The Black Cauldron",
        'floor_range': (14, 26),
        'symbol': 'Q',
        'color': (40, 140, 100),  # dark green
        'description': "A black cauldron rimmed with pearls, kept warm by no fire you can see. The Welsh say it will not boil a coward's food. It looks hungry.",
        'key_item': None,  # no key -- requires 3 Food items in inventory
        'gold_cost': 0,
        'challenge': {'mode': 'threshold', 'subject': 'cooking', 'tier': 2, 'threshold': 1, 'total': 1},
        'reward': {'effects': ['searching', 'warning']},
        'reward_text': "The cauldron takes all three dishes and boils without complaint. Its steam clears your eyes. (Searching, Danger Sense)",
        'fail_text': "The cauldron goes cold in an instant. It has decided what kind of cook you are.",
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
    # Never the Magic Dungeon Carrot: it is the unicorn's key, found on
    # floors 1 to 19, and the Cauldron (14 to 26) used to eat it.
    return [i for i in player.inventory
            if isinstance(i, Food) and getattr(i, 'id', '') != 'magic_dungeon_carrot'][:3]


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

    # Every quirk has a written hint now (quirk_text.QUIRK_HINT). The old
    # table here covered 12 of 112, so nine answers in ten were "A hidden
    # path remains unexplored."
    try:
        from quirk_text import quirk_hint
    except ImportError:
        quirk_hint = None
    game.add_message("The Oracle speaks:", 'info')
    for qid in chosen:
        hint = (quirk_hint(qid) if quirk_hint else '') or _HINTS.get(
            qid, "A hidden path remains unexplored.")
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
        # Ring of Command is defined in data/items/accessory.json (no +1 WIS
        # effect — Solomon's reward dict already grants WIS+2 and the audit
        # 2026-10-03 flagged the stacked +WIS as a double-dip).
        from items import make_item_by_id
        ring = make_item_by_id('accessory', 'ring_of_command')
        if ring is not None:
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
        self.name         = "Deep Gnome Trader"
        self.symbol       = '@'
        self.color        = (180, 180, 220)   # pale grey-blue (deep gnome skin)
        self.weight       = 0
        self.min_level    = 1
        self.count        = 1
        self.not_pickable = True
        self.identified   = True
        self.item_class   = 'merchant'
        self.lore         = "A small grey trader with a pack twice his size and a lantern he never seems to need. "\
                            "He will not say where his stock comes from, only that the previous owners are past caring."
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

    from items import load_items, is_random_loot
    import copy as _copy

    # Build item pool from multiple categories (never quest / scripted items)
    stock_items = []
    for cat in ('potion', 'scroll', 'weapon', 'armor', 'shield', 'accessory', 'wand', 'food', 'ammo'):
        try:
            pool = [i for i in load_items(cat)
                    if getattr(i, 'min_level', 1) <= level and is_random_loot(i)]
            if pool:
                stock_items.extend(rng.choices(pool, k=min(2, len(pool))))
        except Exception:
            pass

    # 15% chance merchant has a Soul Sphere (loaded from artifact.json).
    if rng.random() < 0.15:
        from items import make_item_by_id
        sphere = make_item_by_id('artifact', 'soul_sphere')
        if sphere is not None:
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

    # Place in a non-starting room. (This used to compare against a
    # hard-coded 3, which is STAIRS_DOWN, so the merchant could only ever
    # stand on the stairs: ~1.7% of floors instead of the intended 20%.)
    from dungeon import FLOOR as _FLOOR_TILE
    candidate_rooms = rooms[1:]
    room = rng.choice(candidate_rooms)
    tiles = [
        (rx, ry)
        for rx, ry in room.inner_tiles()
        if dungeon.tiles[ry][rx] == _FLOOR_TILE
        and not any(gi.x == rx and gi.y == ry for gi in ground_items)
    ]
    if not tiles:
        return None

    mx, my = rng.choice(tiles)
    merchant = MerchantNPC(mx, my, stock, prices)
    return merchant
