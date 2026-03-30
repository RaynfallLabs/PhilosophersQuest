"""
Flavor NPC encounters — non-karmic dungeon encounters that add lore,
trade opportunities, and world-building. Separate from the moral
encounter system in npc_encounters.py.

Spawn rate: ~40% per floor, independent of karma NPCs.
One-shot: each encounter can only be triggered once per run.
"""
import random

# ---------------------------------------------------------------------------
# Encounter definitions
# ---------------------------------------------------------------------------
# Each encounter is a dict with:
#   tag          -- unique string ID
#   name         -- NPC display name
#   symbol       -- single char for map rendering
#   color        -- RGB tuple
#   min_level    -- earliest dungeon level this can appear
#   max_level    -- latest dungeon level this can appear
#   text         -- description shown when player bumps the NPC
#   options      -- list of choice dicts, each with:
#       label    -- button text
#       cost     -- None, or dict: {type: 'food'|'gold'|'item'|'hp'|'sp'|'mp', amount: N}
#                   type 'item' uses item_class or item_id to find something in inventory
#       reward   -- None, or dict: {type: 'gold'|'hp'|'sp'|'mp'|'effect'|'stat'|'message', ...}
#       outcome  -- text shown after choosing this option
#   sprite_id    -- optional, monster sprite ID for rendering (defaults to NPC symbol)

FLAVOR_ENCOUNTERS: list[dict] = [
    # ══════════════════════════════════════════════════════════════
    # STAGE 1: Levels 1-20 — Fellow newcomers, lost souls, merchants
    # ══════════════════════════════════════════════════════════════
    {
        'tag': 'flv_wandering_merchant',
        'name': 'Wandering Merchant',
        'symbol': '@',
        'color': (180, 160, 100),
        'min_level': 2, 'max_level': 18,
        'text': (
            "A stout man sits behind a makeshift blanket spread with goods. "
            "\"Business is slow this deep,\" he says, polishing a dented lantern. "
            "\"But I've got a few things you won't find on the floor.\""
        ),
        'options': [
            {
                'label': 'Trade food for a random potion',
                'cost': {'type': 'food'},
                'reward': {'type': 'random_item', 'category': 'potion'},
                'outcome': '"Pleasure doing business." He wraps the potion carefully and hands it over.',
            },
            {
                'label': 'Trade 50 gold for a random scroll',
                'cost': {'type': 'gold', 'amount': 50},
                'reward': {'type': 'random_item', 'category': 'scroll'},
                'outcome': '"Fine parchment, that. Handle it gently." He pockets the coins with a grin.',
            },
            {
                'label': '"Just browsing."',
                'cost': None,
                'reward': None,
                'outcome': '"Suit yourself. I\'ll be here — not like I have anywhere else to go."',
            },
        ],
    },
    {
        'tag': 'flv_old_traveler',
        'name': 'Old Traveler',
        'symbol': '@',
        'color': (140, 140, 160),
        'min_level': 1, 'max_level': 15,
        'text': (
            "An old man in a broad-brimmed hat leans on a gnarled staff, "
            "one eye bright and the other hidden beneath shadow. "
            "\"You look like you could use some wisdom, young one,\" "
            "he says with a voice like distant thunder. \"Share your bread "
            "with a weary traveler?\""
        ),
        'options': [
            {
                'label': 'Share food with him',
                'cost': {'type': 'food'},
                'reward': {'type': 'stat', 'stat': 'WIS', 'amount': 1},
                'outcome': (
                    "He eats slowly, savoring each bite. When he finishes, "
                    "he places a hand on your forehead. A warmth spreads through "
                    "your mind. \"Remember: the wise man knows what he does not know.\" "
                    "Your Wisdom increases."
                ),
            },
            {
                'label': '"I need my supplies."',
                'cost': None,
                'reward': None,
                'outcome': (
                    "He nods without judgment. \"Every traveler must weigh "
                    "their own burdens.\" He tips his hat and walks into the dark. "
                    "You notice his footsteps make no sound."
                ),
            },
        ],
    },
    {
        'tag': 'flv_frightened_goblin',
        'name': 'Cowering Goblin',
        'symbol': 'g',
        'color': (100, 160, 80),
        'min_level': 1, 'max_level': 12,
        'text': (
            "A small goblin huddles in the corner, shaking. It holds up "
            "a shiny trinket in trembling claws. \"No hurt! No hurt! "
            "Gikk trade! Gikk give shiny for not-stabbing!\""
        ),
        'options': [
            {
                'label': 'Accept the trinket',
                'cost': None,
                'reward': {'type': 'random_item', 'category': 'accessory'},
                'outcome': (
                    "Gikk shoves the trinket into your hands and scrambles away, "
                    "disappearing into a crack in the wall you didn\'t notice before. "
                    "The trinket is surprisingly well-made."
                ),
            },
            {
                'label': 'Give Gikk some food',
                'cost': {'type': 'food'},
                'reward': {'type': 'random_item', 'category': 'accessory'},
                'outcome': (
                    "Gikk\'s eyes go wide. \"Food? FOOD! Gikk never get food-gift before!\" "
                    "He shoves the trinket at you and produces a second one from somewhere "
                    "unspeakable. \"Two shinies! For food-friend!\" "
                    "You receive two items."
                ),
                'bonus_reward': {'type': 'random_item', 'category': 'potion'},
            },
            {
                'label': 'Shoo him away',
                'cost': None,
                'reward': None,
                'outcome': (
                    "Gikk yelps and bolts, taking his shiny with him. "
                    "You hear tiny footsteps fading into the dark, "
                    "followed by what might be sobbing."
                ),
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════
    # STAGE 2: Levels 21-40 — Adventurers, scholars, the desperate
    # ══════════════════════════════════════════════════════════════
    {
        'tag': 'flv_dwarven_smith',
        'name': 'Dwarven Smith',
        'symbol': '@',
        'color': (200, 150, 80),
        'min_level': 21, 'max_level': 40,
        'text': (
            "A dwarf sits beside a portable anvil, hammer resting across his knees. "
            "\"I can sharpen that blade of yours,\" he says, eyeing your weapon. "
            "\"Won't cost much. Fifty gold and I'll put an edge on it "
            "that'll last the rest of your descent — or your life, "
            "whichever ends first.\""
        ),
        'options': [
            {
                'label': 'Pay 80 gold to enchant your weapon (+1)',
                'cost': {'type': 'gold', 'amount': 80},
                'reward': {'type': 'enchant_weapon', 'amount': 1},
                'outcome': (
                    "The dwarf works with practiced ease, sparks flying in rhythmic bursts. "
                    "When he hands the weapon back, it hums faintly. \"There. She'll bite "
                    "deeper now.\" Your weapon gains +1 enchantment."
                ),
            },
            {
                'label': '"Maybe next time."',
                'cost': None,
                'reward': None,
                'outcome': (
                    "\"Your loss, surfacer.\" He goes back to polishing his anvil, "
                    "humming a dwarven work-song under his breath."
                ),
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════
    # STAGE 3: Levels 41-60 — Mystics, scholars, otherworldly beings
    # ══════════════════════════════════════════════════════════════
    {
        'tag': 'flv_blind_oracle',
        'name': 'Blind Oracle',
        'symbol': '@',
        'color': (200, 180, 255),
        'min_level': 41, 'max_level': 60,
        'text': (
            "A woman sits cross-legged on the stone floor, eyes bound with silk. "
            "Candles float in the air around her, burning without wax. "
            "\"I know why you came,\" she says. \"Everyone comes for the same reason. "
            "Sit. I will show you what your questions cannot reach.\""
        ),
        'options': [
            {
                'label': 'Offer 30 SP to meditate with her',
                'cost': {'type': 'sp', 'amount': 30},
                'reward': {'type': 'effect', 'effect': 'clairvoyant', 'duration': 50},
                'outcome': (
                    "You sit across from her. The candles dim. Behind your closed eyes, "
                    "the dungeon unfolds like a map drawn in starlight. When you open them, "
                    "she is gone — but the vision remains. Clairvoyance fills your mind."
                ),
            },
            {
                'label': 'Ask about the dungeon ahead',
                'cost': None,
                'reward': {'type': 'message'},
                'outcome': (
                    "\"The dragon sleeps on gold and grief. The wolf eats the sun. "
                    "The destroyer waits where faith is the only weapon.\" "
                    "She smiles. \"But you already knew that, didn't you?\""
                ),
            },
            {
                'label': 'Leave quietly',
                'cost': None,
                'reward': None,
                'outcome': (
                    "You back away. The candles follow you for three steps, "
                    "then return to orbit her. She says nothing."
                ),
            },
        ],
    },
]

# Load generated encounters from JSON data file
import json
import os
from paths import data_path
_GEN_PATH = os.path.join(data_path('data'), 'flavor_encounters.json')
if os.path.exists(_GEN_PATH):
    with open(_GEN_PATH, encoding='utf-8') as _f:
        FLAVOR_ENCOUNTERS.extend(json.load(_f))


# ---------------------------------------------------------------------------
# Spawn logic
# ---------------------------------------------------------------------------

def select_flavor_encounters(level_count: int = 100) -> dict[int, dict]:
    """Select which floors get flavor encounters for this run.
    Returns {level: encounter_dict} for ~40% of floors.
    """
    BOSS_LEVELS = {20, 40, 60, 80, 100}
    eligible_by_level = {}
    for level in range(1, level_count + 1):
        if level in BOSS_LEVELS:
            continue  # no flavor NPCs on boss floors
        pool = [e for e in FLAVOR_ENCOUNTERS
                if e['min_level'] <= level <= e['max_level']]
        if pool:
            eligible_by_level[level] = pool

    selected = {}
    used_tags = set()
    levels = list(eligible_by_level.keys())
    random.shuffle(levels)

    for level in levels:
        if random.random() > 0.40:
            continue  # ~40% spawn rate
        pool = [e for e in eligible_by_level[level] if e['tag'] not in used_tags]
        if not pool:
            continue
        enc = random.choice(pool)
        selected[level] = enc
        used_tags.add(enc['tag'])

    return selected
