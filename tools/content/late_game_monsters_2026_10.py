"""
The October 2026 late-game monster pass: all fourteen proposals of
MONSTER_CATALOG_AUDIT.md (Brandon approved them) plus a lore-first deep set
chosen after re-running the audit's band analysis (Part 2 of the task).

Offline tooling (not loaded at runtime). Idempotent.

    python tools/content/late_game_monsters_2026_10.py            # report
    python tools/content/late_game_monsters_2026_10.py --write    # write data

then `python tools/balance/respawn_by_hp.py --write` seats every new monster
on the floor its HP was built for.

LORE, NOT FLOOR: every number below is the creature's own, written for the
floor its story puts it on (HP on the respawn_by_hp anchor for that floor,
attacks beside the neighbours met there). Nothing scales it in play. A
creature met in numbers (a pack) carries a share of a solo monster's HP and
is seated by `respawn_by_hp.SWARM_SEAT_MULT`, so it still lands on its floor.

New mechanics these monsters use are generic and data-driven:
    steal / after_theft       src/theft.py        thieves take gold or an item and run
    splits                    src/splitting.py    a blow of the wrong kind makes two
    disguise {'tile': ...}    src/false_stairs.py a mimic posing as the down stair
    pack_size                 dungeon.py          exact pack sizes
    escort                    level_manager.py    a mini-boss arrives with company
    weighs_heart              monster.py          blows weighed against the hero's karma
    fearless                  monster.py          never flees, cannot be frightened
    quarrelsome               monster.py          confused, it strikes its own kind
    quarrels_when_struck_by_thrown                Jason's stone among the Sown Men
    bonus_vs                  monster.py          a blow that is worse on a held hero
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'tools' / 'balance'))
import jsonfmt  # noqa: E402

MONSTERS = ROOT / 'data' / 'monsters.json'
SIZES_PATH = ROOT / 'data' / 'monster_sizes.json'
POTIONS = ROOT / 'data' / 'items' / 'potion.json'

DEEP_GOLD = {'gold': [140, 380], 'item_chance': 0.55, 'item_tier': 5}
MID_GOLD = {'gold': [110, 300], 'item_chance': 0.45, 'item_tier': 4}


def atk(name, damage, typ, effect=None, chance=0.0, duration=0, **extra):
    a = {'name': name, 'damage': damage, 'type': typ}
    if effect:
        a.update(effect=effect, effect_chance=chance, effect_duration=duration)
    a.update(extra)
    return a


# =============================================================================
# PART 1: the fourteen proposals
# =============================================================================

NEW = {
    # --- 2. Keres: the first real deep swarm ---------------------------------
    'ker': {
        'name': 'Ker', 'symbol': 'K', 'color': [90, 20, 30],
        'hp': '160d12+1060', 'speed': 13, 'ai_pattern': 'aggressive', 'thac0': -14,
        'peak_floor': 92, 'spread': 12, 'peak_weight': 2.5, 'min_level': 86,
        'attacks': [
            atk('Blood-Drinking Talons', '3d8+14', 'slash', 'bleeding', 0.4, 4),
            atk("Death's Grip", '2d8+16', 'drain'),
        ],
        'resistances': ['cold', 'poison', 'drain'], 'weaknesses': ['holy'],
        'tags': ['outsider'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD, item_chance=0.3),
        'lore': ("Hesiod painted the Keres on the shield of Heracles: dark death-spirits with white "
                 "gnashing teeth, fighting each other over the men who fell, each wanting to drink "
                 "the dark blood first. Homer put one on the shield of Achilles, dragging a dead man "
                 "through the battle by his feet. They never come alone. Each one is weak as death "
                 "goes down here, but there are always more of them than there are of you, and a "
                 "wounded man draws the whole flock. Kill them fast, and many at a time."),
        'frequency': 3, 'pack': True, 'pack_size': [3, 5],
    },
    # --- 3. Hellmouth: the map lies to you --------------------------------------
    'hellmouth': {
        'name': 'Hellmouth', 'symbol': '>', 'color': [150, 40, 30],
        'hp': '470d12+3110', 'speed': 5, 'ai_pattern': 'mimic', 'thac0': -16,
        'peak_floor': 90, 'spread': 12, 'peak_weight': 1.0, 'min_level': 84,
        'attacks': [
            atk("Leviathan's Jaws", '5d10+20', 'acid', 'immobilized', 0.5, 2),
            atk('Gullet Fire', '4d8+18', 'fire', 'burning', 0.4, 3),
        ],
        'resistances': ['fire', 'acid', 'poison'], 'weaknesses': ['holy', 'cold'],
        'tags': ['demon', 'aberration'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("Medieval painters drew Hell as a mouth: the gaping jaws of Leviathan, the beast of "
                 "Job, out of whose mouth go burning lamps. On the Doom paintings over church arches "
                 "and on the mystery-play stages the damned were herded into it, and the stagehands "
                 "worked its jaws with ropes and blew smoke out of its throat. One of them lies flat "
                 "in the floor down here with its gullet open, and its gullet looks exactly like a "
                 "stair going down. A floor has one way down. When you find two, one of them is "
                 "hungry."),
        'frequency': 1, 'disguise': {'tile': 'stairs_down', 'name': 'staircase leading down'},
    },
    # --- 4. Grendel's Mother: the mere-wife ---------------------------------------
    'mere_wife': {
        'name': 'Mere-Wife', 'symbol': 'M', 'color': [70, 90, 80],
        'hp': '420d12+2670', 'speed': 11, 'ai_pattern': 'ambush', 'thac0': -15,
        'peak_floor': 84, 'spread': 12, 'peak_weight': 2.0, 'min_level': 78,
        'attacks': [
            atk('Drag to the Mere', '4d10+18', 'blunt', 'immobilized', 0.3, 2),
            atk('Broad Seax', '4d8+20', 'pierce', 'bleeding', 0.4, 4),
        ],
        'resistances': ['slash', 'pierce', 'cold'], 'weaknesses': ['holy'],
        'tags': ['giant', 'humanoid'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("The Beowulf poet never names Grendel's mother. He gives her a kind instead: "
                 "merewif, the mere-wife, the she-wolf of the deep. She came up out of the dark water "
                 "to avenge her son, and when Beowulf followed her down she dragged him to her hall "
                 "under the mere. His borrowed sword Hrunting, which had never failed in battle, "
                 "would not bite her hide, and he had to wrestle her until he found a giant's blade "
                 "on her wall. Her kind still wait under black water. A blade turns on that hide; "
                 "something heavier does not."),
        'frequency': 2, 'pull_chance': 0.35,
    },
    # --- 5. The Witch of Endor's line: kill the caster first ---------------------
    'endor_medium': {
        'name': 'Medium of Endor', 'symbol': 'w', 'color': [120, 90, 140],
        'hp': '415d12+2700', 'speed': 10, 'ai_pattern': 'summoner', 'thac0': -15,
        'peak_floor': 84, 'spread': 12, 'peak_weight': 2.0, 'min_level': 78,
        'attacks': [
            atk('Grave Whisper', '3d10+18', 'magic', 'feared', 0.3, 3, ranged=True),
            atk('Bone Knife', '3d8+16', 'pierce', 'bleeding', 0.3, 3),
        ],
        'resistances': ['drain', 'cold', 'necrotic'], 'weaknesses': ['holy', 'fire'],
        'tags': ['humanoid', 'caster'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("King Saul had driven every medium out of Israel, and then, the night before his "
                 "last battle, he put on a disguise and went to the one left at Endor. At his word "
                 "she called up the prophet Samuel, an old man wrapped in a mantle, who told Saul "
                 "that by tomorrow he and his sons would be with him among the dead. Her line kept "
                 "the craft. They call, and whatever is listening in the dark comes up, and much of "
                 "what comes up cannot be seen. Kill the one calling before the room fills."),
        'frequency': 2, 'summon_kind': ['darkhelm_shade', 'dread_wraith'],
        'summon_cooldown': 6, 'summon_max': 3, 'perception_range': 10,
    },
    # --- 6. The Furies, greater: three that will not stand still -----------------
    'erinyes_greater': {
        'name': 'Greater Erinyes', 'symbol': 'E', 'color': [140, 30, 40],
        'hp': '300d12+1290', 'speed': 13, 'ai_pattern': 'hit_and_run', 'thac0': -15,
        'peak_floor': 86, 'spread': 12, 'peak_weight': 2.0, 'min_level': 80,
        'attacks': [
            atk('Scourge of Serpents', '4d8+16', 'slash', 'feared', 0.3, 3),
            atk('Blood-Weeping Glare', '3d8+16', 'magic', 'blinded', 0.35, 3),
        ],
        'resistances': ['fire', 'cold', 'poison'], 'weaknesses': [],
        'tags': ['outsider'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("Alecto the unceasing, Megaera the grudging, Tisiphone the avenger of murder. In "
                 "Aeschylus they hunted Orestes from Argos to Delphi to Athens for his mother's "
                 "blood, snakes in their hair and blood weeping from their eyes, and they slept only "
                 "when Apollo made them. Athena talked them down at last with a new home under "
                 "the city and a new name, the Kindly Ones. Nobody down here has offered them one. "
                 "They come as three, strike, scatter and come again, and the look of them puts men "
                 "to flight."),
        'frequency': 2, 'pack': True, 'pack_size': [3, 3],
    },
    # --- 7. Blood of Tiamat: splits under a weak blow ----------------------------
    'tiamat_blood': {
        'name': 'Blood of Tiamat', 'symbol': 'P', 'color': [120, 20, 60],
        'hp': '480d12+3200', 'speed': 9, 'ai_pattern': 'aggressive', 'thac0': -16,
        'peak_floor': 92, 'spread': 12, 'peak_weight': 2.0, 'min_level': 86,
        'attacks': [
            atk('Brine Lash', '4d10+20', 'cold', 'slowed', 0.35, 3),
            atk('Venom of the Eleven', '3d10+18', 'poison', 'poisoned', 0.45, 6),
        ],
        'resistances': ['poison', 'cold', 'acid'], 'weaknesses': ['fire'],
        'tags': ['aberration', 'outsider'], 'harvest_tier': 4,
        'treasure': {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 5},
        'lore': ("In the Babylonian creation poem Marduk caught Tiamat, the salt sea, in his net, "
                 "drove the winds into her mouth and split her in two like a fish for drying: half "
                 "became the sky and half the earth. Then he cut the channels of her blood and the "
                 "north wind carried it away to secret places. This is one of them. Her blood still "
                 "crawls, salt and venomous, and it remembers being divided: a small cut only makes "
                 "two of it. One great blow, the kind a long answer chain gives, ends it outright."),
        'frequency': 2, 'splits': {'by': 'weak_blow', 'share': 0.10, 'max': 8},
    },
    # --- 8. Ganglot, Hel's handmaid: heal the dead -------------------------------
    'hels_handmaid': {
        'name': 'Handmaid of Hel', 'symbol': 'h', 'color': [150, 160, 170],
        'hp': '410d12+2700', 'speed': 8, 'ai_pattern': 'healer', 'thac0': -15,
        'peak_floor': 84, 'spread': 12, 'peak_weight': 2.0, 'min_level': 78,
        'heal_amount_pct': 0.2,
        'attacks': [
            atk("Slow-Walker's Touch", '4d8+16', 'cold', 'slowed', 0.45, 4),
            atk('Breath of the Sickbed', '3d8+16', 'cold', 'diseased', 0.3, 6, ranged=True),
        ],
        'resistances': ['cold', 'drain', 'poison'], 'weaknesses': ['fire', 'holy'],
        'tags': ['undead', 'caster'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("Snorri Sturluson furnished Hel's hall for us: her plate is called Hunger, her knife "
                 "Famine, her bed Sickbed, and her servants are Ganglati and Ganglot, both names "
                 "meaning the slow-walker. Hel keeps many maids now, and all of them are slow. They "
                 "walk among her dead mending what the living break, and their touch puts the same "
                 "slowness into a warm body. Wherever the dead keep getting up again, look for the "
                 "maid behind them and put her down first."),
        'frequency': 2,
    },
    # --- 9. Stheno and Euryale: a named pair (mini-bosses, once per run) ---------
    'stheno_gorgon': {
        'name': 'Stheno the Gorgon', 'symbol': 'G', 'color': [150, 130, 60],
        'hp': '1380d10+1360', 'speed': 11, 'ai_pattern': 'dancer', 'thac0': -9,
        'peak_floor': 67, 'spread': 2, 'peak_weight': 0.0, 'min_level': 64,
        'attacks': [
            atk('Bronze Claws', '4d8+20', 'slash', 'bleeding', 0.35, 4),
            atk('Serpent Hair', '3d8+18', 'poison', 'poisoned', 0.4, 6),
        ],
        'resistances': ['poison'], 'weaknesses': [],
        'tags': ['humanoid'], 'harvest_tier': 4,
        'treasure': {'gold': [1900, 3600], 'item_chance': 1.0, 'item_tier': 5},
        'lore': ("Medusa was the only mortal one of three. Her sisters Stheno, the mighty, and "
                 "Euryale, the far-roaming, cannot die. Hesiod gives them brazen hands and golden "
                 "wings, and when Perseus fled with their sister's head they rose from their beds "
                 "and chased him over the sea until the helm of Hades hid him. They have been "
                 "looking for him ever since. Their gaze turns the living rigid as stone, and a "
                 "killing blow only puts them down for a moment."),
        'frequency': 0, 'gaze_paralyze': 2, 'gaze_cooldown': 6, 'gaze_group': 'gorgon_sisters',
        'revive_once_on_death': True, 'revive_hp_pct': 0.3,
        'revive_message': "Stheno rises again. An immortal does not stay dead.",
        'is_mini_boss': True, 'spawn_chance': 0.4, 'escort': ['euryale_gorgon'],
        'omen': "Somewhere on this floor two women are hissing at each other, and then both fall silent.",
        # Each sister has her own line; the pair's line waits for the second (MON-10).
        'kill_chronicle': ("Put Stheno down twice. The old stories call her the mighty one, and the "
                           "first time she got up as if I had only tripped her."),
        'kill_pair': 'euryale_gorgon',
        'kill_pair_chronicle': "Put down Medusa's sisters. Twice each. I am not sure it will last.",
    },
    'euryale_gorgon': {
        'name': 'Euryale the Gorgon', 'symbol': 'G', 'color': [110, 140, 70],
        'hp': '1380d10+1360', 'speed': 11, 'ai_pattern': 'dancer', 'thac0': -9,
        'peak_floor': 67, 'spread': 2, 'peak_weight': 0.0, 'min_level': 64,
        'attacks': [
            atk("Euryale's Wail", '3d8+16', 'magic', 'feared', 0.35, 3),
            atk('Serpent Hair', '4d8+20', 'poison', 'poisoned', 0.4, 6),
        ],
        'resistances': ['poison'], 'weaknesses': [],
        'tags': ['humanoid'], 'harvest_tier': 4,
        'treasure': {'gold': [1900, 3600], 'item_chance': 1.0, 'item_tier': 5},
        'lore': ("Pindar says Athena invented the music of the pipes to copy one sound: the shrill "
                 "wailing Euryale raised over her beheaded sister, with the snakes in her hair "
                 "keening along. Euryale has not stopped grieving and she has not stopped hunting. "
                 "She goes nowhere without Stheno. Her wail drives men back, her gaze holds them "
                 "where they stand, and like her sister she is immortal: she can be put down, but "
                 "not for long. A polished shield or a blindfold is worth more here than a sword."),
        'frequency': 0, 'gaze_paralyze': 1, 'gaze_cooldown': 6, 'gaze_group': 'gorgon_sisters',
        # One shared gaze between the sisters (gaze_group), and Euryale's holds
        # a turn: her weapon is the wail. Stheno's still holds two.
        'revive_once_on_death': True, 'revive_hp_pct': 0.3,
        'revive_message': "Euryale rises again, wailing. An immortal does not stay dead.",
        'is_mini_boss': True, 'spawn_chance': 0.0,
        'kill_chronicle': ("Put Euryale down twice. She was wailing for Medusa when she fell, and "
                           "wailing when she rose, and the second time she went quiet."),
        'kill_pair': 'stheno_gorgon',
        'kill_pair_chronicle': "Put down Medusa's sisters. Twice each. I am not sure it will last.",
    },
    # --- 10. Gashadokuro: a huge deep ambusher -----------------------------------
    'gashadokuro': {
        'name': 'Gashadokuro', 'symbol': 'Z', 'color': [220, 210, 190],
        'hp': '350d12+2290', 'speed': 9, 'ai_pattern': 'ambush', 'thac0': -13,
        'peak_floor': 78, 'spread': 9, 'peak_weight': 2.0, 'min_level': 73,
        'attacks': [
            atk('Bite Off the Head', '5d10+15', 'pierce', 'bleeding', 0.4, 4),
            atk('Grasp of the Starved', '4d8+18', 'blunt', 'immobilized', 0.3, 2),
        ],
        'resistances': ['pierce', 'cold', 'poison', 'drain'], 'weaknesses': ['blunt', 'holy', 'fire'],
        'tags': ['undead', 'giant'], 'harvest_tier': 4, 'treasure': dict(MID_GOLD),
        'lore': ("Japanese tales of the last century tell of the gashadokuro, the starving skeleton: "
                 "fifteen times the height of a man, built from the bones of everyone who died of "
                 "hunger or in battle and was never buried. It walks at night without a sound, and "
                 "the only warning is a ringing in the ears, gasha gasha, a moment before it bites "
                 "off a traveller's head. This one has folded itself into a corner of the dungeon "
                 "and lies there like a heap of old bones. It is not a heap of old bones. A spear "
                 "goes between the ribs; a hammer does not."),
        'frequency': 2, 'footprint': [2, 2],
    },
    # --- 11. Autolycus' heir: a deep thief ----------------------------------------
    'autolycus_heir': {
        'name': 'Heir of Autolycus', 'symbol': '@', 'color': [140, 110, 70],
        'hp': '270d10+1380', 'speed': 13, 'ai_pattern': 'hit_and_run', 'thac0': -9,
        'peak_floor': 66, 'spread': 9, 'peak_weight': 2.0, 'min_level': 61,
        'attacks': [
            atk("Hermes' Sleight", '2d8+14', 'pierce', steal='any', steal_chance=0.6),
            atk("Thief's Knife", '3d8+18', 'pierce', 'bleeding', 0.35, 4),
        ],
        'resistances': [], 'weaknesses': [],
        'tags': ['humanoid'], 'harvest_tier': 3, 'treasure': dict(MID_GOLD, item_chance=0.6),
        'lore': ("Odysseus's grandfather Autolycus outdid all men in thieving and in oaths that "
                 "meant nothing, and Hermes himself gave him the gift. He stole a famous boar-tusk "
                 "helmet out of a locked house and the cattle of Sisyphus out of a guarded field, "
                 "and he changed their colour so the owner could not know them. Sisyphus beat him "
                 "only by carving his name under the hooves. His heirs keep the family trade: a "
                 "brush against you, a purse or a pack lighter, and they are gone. Run them down and "
                 "it is yours again."),
        'frequency': 2, 'after_theft': 'flee',
    },
    # --- 12. Strix: the floor 21-30 swarm -----------------------------------------
    'strix': {
        'name': 'Strix', 'symbol': 'B', 'color': [140, 130, 120],
        'hp': '24d10+60', 'speed': 13, 'ai_pattern': 'hit_and_run', 'thac0': 7,
        'peak_floor': 27, 'spread': 5, 'peak_weight': 3.0, 'min_level': 24,
        'attacks': [
            atk('Blood-Drinking Beak', '1d6+2', 'drain'),
            atk('Night Song', '1d4+2', 'magic', 'sleeping', 0.3, 3),
        ],
        'resistances': [], 'weaknesses': ['fire'],
        'tags': ['beast'], 'harvest_tier': 2,
        'treasure': {'gold': [10, 40], 'item_chance': 0.1, 'item_tier': 2},
        'lore': ("Ovid describes the strix in the Fasti: a big-headed night bird with staring eyes, "
                 "a beak made for snatching, grey feathers and hooked claws, that flies by night "
                 "and drinks blood. Whether striges are born birds or are old women changed by a "
                 "spell, he says, nobody knows. They came for the infant Proca in his cradle, and "
                 "the nymph Cranae kept them out with a branch of whitethorn at the window. Down "
                 "here they hunt in threes: one sings you to sleep and the others drink."),
        'frequency': 4, 'pack': True, 'pack_size': [3, 3],
    },
}

# Stat and status re-tunes of existing creatures, by their own lore.
# {id: {field: new value}}; attacks are rewritten whole.
RETUNE = {
    # --- 1. the five deep regulars (about half of all spawns on floors 81-100)
    'wormwood_blight': {
        'attacks': [
            atk('Bitter Spore', '4d8+17', 'poison', 'poisoned', 0.5, 8),
            atk('Falling Star-Ash', '5d10+18', 'poison', 'blinded', 0.35, 3),
        ],
        'lore': ("At the third trumpet a great star fell burning on the rivers and springs. John "
                 "gives its name as Wormwood, and writes that a third of the waters turned bitter "
                 "and many died of drinking them. This is what grew where the star's ash settled: a "
                 "pale, spreading thing that drinks light and breathes out bile. Its spores poison "
                 "whatever they touch, and the ash of the star still sheds from it and stings the "
                 "eyes blind."),
    },
    'void_seraph': {
        'attacks': [
            {'name': 'Void Lance', 'type': 'magic', 'piercing': True, 'damage': '5d10+31'},
            atk('Hush of a Dying Star', '4d8+14', 'magic', 'silenced', 0.35, 4, ranged=True),
            atk('Unmaking Gaze', '4d8+14', 'magic', 'teleportitis', 0.3, 8),
        ],
        'lore': ("Isaiah saw the seraphim above the throne, each with six wings: two to cover the "
                 "face, two to cover the feet, and two to fly. This one fell and kept the wings. When "
                 "it lowers the upper pair there is nothing behind them, only a hollow where a face "
                 "and a name used to be. Its voice is the hush of a star going out, and in that hush "
                 "no spell can be spoken. Its gaze unmakes a thing's place in the world, and whoever "
                 "it falls on keeps slipping out of where he stands."),
    },
    'iron_horseman': {
        'can_charge': True, 'charge_bonus_mult': 1.3,
        'lore': ("John saw four riders: one on a white horse, one on red, one on black, and Death on "
                 "a pale horse with Hades following after. This is none of the four. It is the kind "
                 "of thing that rides in their dust, armor welded shut, rider and mount grown into "
                 "one iron shape. Given a straight run it lowers the lance and charges, and it does "
                 "not turn aside. Its hooves leave men senseless on the ground. Do not stand at the "
                 "end of a long corridor."),
    },
    'apocalypse_herald': {
        'attacks': [
            atk('Trumpet Blast', '4d8+14', 'magic', 'feared', 0.4, 3),
            atk('Sickle of the Harvest', '5d10+18', 'slash', 'bleeding', 0.5, 4),
        ],
    },
    # pit_executioner keeps its bleed (Great Cleaver) unchanged.

    # --- 11. thieves that steal
    'bandit_thief': {
        'attacks': [
            atk('Backstab', '1d6+2', 'pierce', 'bleeding', 0.4, 4),
            atk('Cut Purse', '1d4+1', 'slash', steal='gold', steal_chance=0.7),
        ],
        'after_theft': 'flee',
        'lore': ("Thieves drift in and out of bandit work as the seasons demand: winter in a warm "
                 "gang, spring picking pockets in a market town. They prefer a quiet boot and a "
                 "turned back to a duel, and a purse cut in passing to either. They have a saying: "
                 "the man who shows his sword has already decided he would rather not use it. One "
                 "who has your gold runs. Catch him and it is yours again."),
    },
    'leprechaun': {
        'attacks': [
            {'name': 'Hex', 'damage': '1d2+1', 'type': 'magic', 'effect': 'teleportitis',
             'effect_chance': 0.4, 'effect_duration': '1d8'},
            atk('Light Fingers', '1d2', 'physical', steal='gold', steal_chance=0.8),
        ],
        'after_theft': 'teleport',
        'lore': ("Irish tales make the leprechaun a solitary cobbler, heard tapping at a single shoe "
                 "under a hedge. A captor who keeps both eyes on him can demand his crock of gold. "
                 "One glance away and he is gone. The ones down here have learned the trick in "
                 "reverse: a touch, a wink, your purse is lighter, and he is standing somewhere else "
                 "on the floor entirely. He has not left it. Find him and the gold comes back."),
    },
    'leprechaun_hostile': {
        'attacks': [
            {'name': 'Shillelagh', 'damage': '1d2+1', 'type': 'physical'},
            {'name': 'Gold Curse', 'damage': '1d2+1', 'type': 'magic', 'effect': 'confused',
             'effect_chance': 0.4, 'effect_duration': 5},
            atk('Light Fingers', '1d2', 'physical', steal='gold', steal_chance=0.8),
        ],
        'after_theft': 'teleport',
    },
    'ethereal_filcher': {
        'attacks': [
            {'name': 'Steal', 'damage': '1d3', 'type': 'physical', 'effect': 'confused',
             'effect_chance': 0.2, 'effect_duration': 2, 'steal': 'item', 'steal_chance': 0.7},
        ],
        'after_theft': 'flee',
        'lore': ("An incorporeal undead that slips between this world and the next to steal from "
                 "the living. Filchers are drawn to bright and magical things and carry them off to "
                 "hidden ethereal lairs. They are rarely aggressive unless cornered. A filcher's "
                 "fingers pass through a closed pack as easily as through air, and once it has "
                 "something it flees rather than fight. Whatever it took falls out of it when it "
                 "dies."),
    },
    # --- 13. two more invisible creatures by lore
    'air_elemental': {
        'invisible': True,
        'lore': ("The wind has always had names. The Greeks kept four of them, Boreas, Notus, Eurus "
                 "and Zephyrus, and said King Aeolus held the rest shut in a cave. Paracelsus called "
                 "the spirits of the air sylphs. An air elemental is a whirlwind with a will: "
                 "invisible as the wind it is made of, quick as a thrown knife, and full of grit and "
                 "splinters that flay whatever it wraps around. You see the dust it carries, and "
                 "only once it has hit you."),
    },
    'poltergeist': {
        'invisible': True,
        'lore': ("The word is German for 'noisy ghost'. A poltergeist has no shape to show, only a "
                 "temper: doors slam, crockery flies, a chair skates across the room and breaks "
                 "against the wall. It is the spirit of someone who died bewildered and has stayed "
                 "that way. Nobody has ever seen one; you see what it throws, and where it came "
                 "from. It does not hunt the living. It rages at them for being able to leave."),
    },
    # --- 7. the black pudding gets the classic split its lore already describes
    'black_pudding': {
        'splits': {'by': ['slash', 'lightning'], 'max': 6},
    },
}

# =============================================================================
# PART 2: a lore-first deep set (see the "after" section of the audit)
# =============================================================================

NEW.update({
    # --- Greek ----------------------------------------------------------------
    'bronze_sentinel': {
        'name': 'Bronze Sentinel', 'symbol': 'T', 'color': [190, 130, 60],
        'hp': '310d12+1360', 'speed': 9, 'ai_pattern': 'aggressive', 'thac0': -10,
        'peak_floor': 70, 'spread': 9, 'peak_weight': 2.0, 'min_level': 65,
        'attacks': [
            atk('Hurled Boulder', '4d8+18', 'blunt', 'stunned', 0.2, 2, ranged=True),
            atk('Red-Hot Embrace', '5d10+12', 'fire', 'burning', 0.45, 3),
        ],
        'resistances': ['slash', 'blunt', 'fire', 'cold', 'lightning', 'poison'],
        'weaknesses': ['pierce', 'magic'],
        'tags': ['construct'], 'harvest_tier': 3, 'treasure': dict(MID_GOLD),
        'lore': ("Hephaestus made Talos of bronze to guard Crete. He walked round the island three "
                 "times a day, threw boulders at any ship that came near, and when men landed he "
                 "heated himself red-hot in a fire and hugged them. He had one vein, running from "
                 "his neck to his ankle, stopped with a single bronze nail. Medea bewitched him with "
                 "her eyes and the nail came out, and the ichor ran out of him like molten lead. "
                 "His copies guard the deep halls. Swords and hammers ring off them. Find the nail, "
                 "with a point or with a spell."),
        'frequency': 2,
    },
    'sown_warrior': {
        'name': 'Sown Warrior', 'symbol': 'S', 'color': [170, 140, 80],
        'hp': '150d10+390', 'speed': 10, 'ai_pattern': 'aggressive', 'thac0': -10,
        'peak_floor': 72, 'spread': 9, 'peak_weight': 2.0, 'min_level': 67,
        'attacks': [
            atk('Dragon-Tooth Spear', '3d8+14', 'pierce', 'bleeding', 0.3, 3),
            atk('Shield Bash', '3d6+14', 'blunt', 'stunned', 0.15, 1),
        ],
        'resistances': ['slash'], 'weaknesses': ['holy'],
        'tags': ['humanoid'], 'harvest_tier': 3,
        'treasure': {'gold': [40, 120], 'item_chance': 0.25, 'item_tier': 4},
        'lore': ("Cadmus killed the dragon of Ares and, on Athena's advice, sowed its teeth in a "
                 "ploughed field. Armed men came up out of the furrows, already in bronze, already "
                 "angry. Cadmus threw a stone into the middle of them; each blamed the man beside "
                 "him, and they fought until only five were left. Jason met the same harvest at "
                 "Colchis and beat it the same way. They still come up in companies and fight as "
                 "one. Confuse them, or throw something into the middle, and they turn on each "
                 "other."),
        'frequency': 3, 'pack': True, 'pack_size': [4, 5],
        'quarrelsome': True, 'quarrels_when_struck_by_thrown': 4,
    },
    # --- Hindu ------------------------------------------------------------------
    'takshaka_brood': {
        'name': 'Brood of Takshaka', 'symbol': 'N', 'color': [170, 110, 60],
        'hp': '320d10+2160', 'speed': 11, 'ai_pattern': 'mimic', 'thac0': -12,
        'peak_floor': 74, 'spread': 9, 'peak_weight': 1.5, 'min_level': 69,
        'attacks': [
            atk("Takshaka's Venom", '4d10+16', 'poison', 'poisoned', 0.5, 6),
            atk('Coils', '3d8+18', 'blunt', 'immobilized', 0.3, 2),
        ],
        'resistances': ['poison'], 'weaknesses': ['cold'],
        'tags': ['beast', 'reptile'], 'harvest_tier': 4, 'treasure': dict(MID_GOLD),
        'lore': ("The Mahabharata tells how King Parikshit was cursed to die of a snakebite on the "
                 "seventh day. He shut himself in a tower on a single pillar and let no one in but "
                 "holy men. The serpent king Takshaka sent his nagas dressed as holy men, carrying "
                 "fruit, and hid himself inside one fruit as a tiny copper-coloured worm. When the "
                 "king picked it up, Takshaka took his true shape and bit. His brood still hides in "
                 "fruit. Be wary of a perfect apple lying on a dungeon floor."),
        'frequency': 2, 'disguise': {'item': 'apple', 'name': 'ripe apple'},
    },
    'rakshasa_illusionist': {
        'name': 'Rakshasa Illusionist', 'symbol': 'R', 'color': [160, 60, 120],
        'hp': '370d12+2510', 'speed': 11, 'ai_pattern': 'ranged', 'thac0': -14,
        'peak_floor': 80, 'spread': 9, 'peak_weight': 2.5, 'min_level': 75,
        'attacks': [
            atk('Serpent Noose', '3d8+16', 'magic', 'immobilized', 0.4, 2, ranged=True),
            atk('Maya', '3d8+14', 'psionic', 'hallucinating', 0.4, 5, ranged=True),
            atk('Tiger Claws', '4d8+20', 'slash', 'bleeding', 0.3, 3),
        ],
        'resistances': ['magic', 'fire'], 'weaknesses': ['holy'],
        'tags': ['demon', 'caster'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("Ravana's son Indrajit, the conqueror of Indra, fought Rama's army from inside the "
                 "clouds where no arrow could find him. He bound Rama and Lakshmana with the "
                 "serpent noose, living snakes that held them helpless on the field, until Garuda, "
                 "enemy of every serpent, came down and the snakes fled at his shadow. His maya "
                 "showed the monkey army things that were not there. The rakshasa illusionists who "
                 "learned from him keep their distance, tie you where you stand and fill your eyes "
                 "with lies. Close the distance, or kill them from where you are."),
        'frequency': 2, 'can_phase_blink': True, 'phase_blink_chance': 0.2,
        'perception_range': 10,
    },
    # --- Egyptian --------------------------------------------------------------
    'ushabti_overseer': {
        'name': 'Ushabti Overseer', 'symbol': 'u', 'color': [60, 140, 160],
        'hp': '350d12+2290', 'speed': 10, 'ai_pattern': 'summoner', 'thac0': -13,
        'peak_floor': 78, 'spread': 9, 'peak_weight': 2.0, 'min_level': 73,
        'attacks': [
            atk("Overseer's Whip", '4d8+18', 'slash', 'bleeding', 0.35, 3),
            atk('Words of the Sixth Spell', '3d8+14', 'magic', 'stunned', 0.25, 1, ranged=True),
        ],
        'resistances': ['poison', 'drain', 'cold'], 'weaknesses': ['blunt'],
        'tags': ['construct'], 'harvest_tier': 3, 'treasure': dict(MID_GOLD, item_chance=0.6),
        'lore': ("An Egyptian of means was buried with ushabtis: little blue faience workers, one for "
                 "every day of the year, written with the sixth spell of the Book of the Dead. 'O "
                 "ushabti, if I am called to work in the land of the dead, you shall answer: Here I "
                 "am.' For every ten workers there was an overseer with a whip, to keep them at it. "
                 "The overseers down here have outlived their masters and still read out the spell, "
                 "and the workers still answer. Break the one with the whip and the rest fall "
                 "quiet."),
        'frequency': 2, 'summon_kind': 'ushabti_worker', 'summon_cooldown': 4, 'summon_max': 5,
    },
    'ushabti_worker': {
        'name': 'Ushabti Worker', 'symbol': 'u', 'color': [80, 170, 190],
        'hp': '120d10+560', 'speed': 10, 'ai_pattern': 'aggressive', 'thac0': -10,
        'peak_floor': 78, 'spread': 9, 'peak_weight': 0.0, 'min_level': 73,
        'attacks': [
            atk('Bronze Hoe', '3d8+12', 'pierce'),
            atk('Basket of Sand', '2d8+12', 'physical', 'blinded', 0.3, 2),
        ],
        'resistances': ['poison', 'drain', 'cold'], 'weaknesses': ['blunt'],
        'tags': ['construct'], 'harvest_tier': 1,
        'treasure': {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1},
        'lore': ("A little worker of blue faience the size of a man's hand in the tomb, and the size "
                 "of a man down here. It carries a hoe and a basket of sand, because those are the "
                 "tools painted on it, and it does what the sixth spell says: it answers 'Here I am' "
                 "and it works. It has no malice and no will. It throws the sand in your eyes because "
                 "the overseer told it to."),
        'frequency': 0,
    },
    'sekhmet_lioness': {
        'name': 'Lioness of Sekhmet', 'symbol': 'f', 'color': [200, 120, 50],
        'hp': '400d12+2560', 'speed': 13, 'ai_pattern': 'aggressive', 'thac0': -15,
        'peak_floor': 82, 'spread': 12, 'peak_weight': 2.0, 'min_level': 76,
        'attacks': [
            atk('Claws of the Eye', '4d10+14', 'slash', 'bleeding', 0.4, 4),
            atk('Desert-Wind Breath', '3d8+16', 'fire', 'burning', 0.35, 3),
        ],
        'resistances': ['fire'], 'weaknesses': ['cold'],
        'tags': ['beast', 'outsider'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("When mankind plotted against Ra, he sent his Eye against them as Sekhmet, the "
                 "lioness, and she slaughtered until she waded in blood and would not stop. To save "
                 "the rest Ra had seven thousand jars of beer dyed red with ochre and poured over the "
                 "fields. She drank it for blood, fell drunk, and forgot. Her lionesses were never "
                 "given the beer. Their hot breath is the desert wind, and every blow makes the next "
                 "one fiercer: end the fight quickly, or walk away and let them cool."),
        'frequency': 2, 'fury_per_attack': 0.08, 'fury_cap': 0.8,
        'fury_message': "The Lioness of Sekhmet's eyes go red. She is wading in it now.",
    },
    'ammit_devourer': {
        'name': 'Devourer of Hearts', 'symbol': 'A', 'color': [150, 120, 70],
        'hp': '450d12+2990', 'speed': 10, 'ai_pattern': 'aggressive', 'thac0': -16,
        'peak_floor': 88, 'spread': 12, 'peak_weight': 2.0, 'min_level': 82,
        'attacks': [
            atk('Crocodile Jaws', '5d10+20', 'pierce', 'bleeding', 0.35, 4),
            atk('Weighing of the Heart', '3d10+18', 'drain'),
        ],
        'resistances': ['fire'], 'weaknesses': [],
        'tags': ['beast', 'outsider'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("In the Hall of the Two Truths Anubis set the dead man's heart on a scale against "
                 "the feather of Ma'at, and Thoth wrote down the result. Beside the scale crouched "
                 "Ammit, the Devourer: the head of a crocodile, the forequarters of a lion, the "
                 "hindquarters of a hippopotamus. A heart heavier than the feather was hers to eat, "
                 "and its owner was gone for good. Her get still weigh every heart they meet. They "
                 "bite gently into a clean conscience and savagely into a heavy one."),
        'frequency': 2, 'weighs_heart': True,
    },
    # --- Persian ---------------------------------------------------------------
    'mazandaran_div': {
        'name': 'Mazandaran Div', 'symbol': 'D', 'color': [220, 220, 210],
        'hp': '420d12+2670', 'speed': 10, 'ai_pattern': 'ranged', 'thac0': -15,
        'peak_floor': 84, 'spread': 12, 'peak_weight': 2.5, 'min_level': 78,
        'attacks': [
            atk('Sorcerous Darkness', '3d10+16', 'magic', 'blinded', 0.4, 4, ranged=True),
            atk('Hail of Stones', '4d8+18', 'blunt', 'stunned', 0.2, 1, ranged=True),
            atk('Div Claws', '4d10+18', 'slash'),
        ],
        'resistances': ['cold', 'magic'], 'weaknesses': ['holy'],
        'tags': ['demon', 'caster'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("In the Shahnameh, King Kay Kavus marched into Mazandaran to conquer it, and the "
                 "White Div answered with sorcery: a darkness came down on the Persian army, a hail "
                 "of stones fell out of it, and when it lifted the king and his men were blind. "
                 "Rostam went alone through seven trials, killed the White Div in his cave, and "
                 "cured the king's eyes with drops of the div's blood. The divs of Mazandaran still "
                 "fight from a distance and still put out a man's sight. Bring something for the "
                 "eyes, or close in fast."),
        'frequency': 2, 'perception_range': 10,
    },
    'dahaka_wyrm': {
        'name': 'Dahaka Wyrm', 'symbol': 'W', 'color': [110, 90, 60],
        'hp': '500d12+3220', 'speed': 9, 'ai_pattern': 'aggressive', 'thac0': -17,
        'peak_floor': 94, 'spread': 12, 'peak_weight': 2.0, 'min_level': 88,
        'attacks': [
            atk('Three Jaws', '5d10+22', 'pierce', 'bleeding', 0.35, 4),
            atk('Breath of Vermin', '4d8+18', 'poison', 'poisoned', 0.45, 6),
        ],
        'resistances': ['fire', 'poison'], 'weaknesses': ['blunt', 'holy'],
        'tags': ['dragon', 'reptile', 'demon'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("Azhi Dahaka was the three-headed, six-eyed dragon of the Avesta, made by the evil "
                 "spirit to empty the world of good things. When the hero Thraetaona struck it with "
                 "his blade, snakes, scorpions, toads and lizards poured out of the wound, and he "
                 "saw that if he cut it to pieces the world would be filled with vermin. So he "
                 "chained it under Mount Damavand instead. Its brood carries the same curse. Every "
                 "cut or stab lets out a swarm. Club it, burn it, or blast it."),
        'frequency': 2, 'splits': {'by': ['slash', 'pierce'], 'into': 'khrafstra_swarm', 'max': 6},
    },
    'khrafstra_swarm': {
        'name': 'Khrafstra Swarm', 'symbol': 'v', 'color': [90, 110, 60],
        'hp': '90d10+400', 'speed': 12, 'ai_pattern': 'aggressive', 'thac0': -12,
        'peak_floor': 94, 'spread': 12, 'peak_weight': 0.0, 'min_level': 88,
        'attacks': [
            atk('Stings and Bites', '3d8+14', 'poison', 'poisoned', 0.4, 5),
        ],
        'resistances': ['poison'], 'weaknesses': ['fire', 'cold'],
        'tags': ['beast'], 'harvest_tier': 1,
        'treasure': {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1},
        'lore': ("The Zoroastrian books call them khrafstra: the noxious creatures, snakes, "
                 "scorpions, toads, lizards and stinging flies, which the evil spirit made to spoil "
                 "the good creation. Killing them was a good deed, and priests kept a special stick "
                 "for it. This seething knot of them spilled out of a Dahaka's wound and has not "
                 "stopped biting since."),
        'frequency': 0,
    },
    # --- Mesopotamian ----------------------------------------------------------
    'galla_demon': {
        'name': 'Galla', 'symbol': 'g', 'color': [110, 90, 80],
        'hp': '160d10+530', 'speed': 12, 'ai_pattern': 'aggressive', 'thac0': -12,
        'peak_floor': 76, 'spread': 9, 'peak_weight': 2.0, 'min_level': 71,
        'attacks': [
            atk('Seize', '3d8+12', 'blunt', 'immobilized', 0.3, 2),
            atk('Underworld Club', '3d8+14', 'blunt'),
        ],
        'resistances': ['drain', 'poison'], 'weaknesses': ['holy'],
        'tags': ['demon', 'outsider'], 'harvest_tier': 3,
        'treasure': {'gold': [40, 120], 'item_chance': 0.2, 'item_tier': 4},
        'lore': ("When Inanna came back up from the underworld, the galla came with her to collect "
                 "someone to take her place. The Sumerian poem says what they are: they eat no food, "
                 "drink no water, take no gift, and pull the wife from the husband's arms and the "
                 "child from the father's knee. They chased her husband Dumuzi across the steppe, "
                 "and three times the sun god turned him into a gazelle to escape, and three times "
                 "they found him. They come in gangs and they never give up the chase. They grab, "
                 "they hold, and they drag."),
        'frequency': 3, 'pack': True, 'pack_size': [4, 6], 'fearless': True, 'pull_chance': 0.25,
    },
    'girtablilu': {
        'name': 'Scorpion-Man', 'symbol': 'x', 'color': [150, 100, 50],
        'hp': '310d12+2070', 'speed': 10, 'ai_pattern': 'aggressive', 'thac0': -16,
        'peak_floor': 90, 'spread': 12, 'peak_weight': 2.0, 'min_level': 84,
        'attacks': [
            atk('Scorpion Sting', '4d10+18', 'poison', 'paralyzed', 0.25, 2),
            atk('Bow of the Sunrise Gate', '4d8+18', 'pierce', ranged=True),
        ],
        'resistances': ['slash', 'pierce', 'fire'], 'weaknesses': ['blunt', 'cold'],
        'tags': ['outsider'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("At the twin peaks of Mount Mashu, where the sun goes in and out, Gilgamesh found the "
                 "gate guarded by a scorpion-man and his wife: men to the waist, scorpions below, "
                 "whose terror was overwhelming and whose glance was death. Babylonian boundary stones "
                 "show them drawing bows. Gilgamesh got past by telling them the truth about his "
                 "grief. Down here they will not ask. They hunt in pairs, their shells turn a blade "
                 "or an arrow, and the sting stops a man where he stands. A hammer cracks them."),
        'frequency': 2, 'pack': True, 'pack_size': [2, 2],
    },
    'asag_stone_warrior': {
        'name': 'Stone Warrior of Asag', 'symbol': 'O', 'color': [130, 120, 110],
        'hp': '510d12+3300', 'speed': 8, 'ai_pattern': 'aggressive', 'thac0': -17,
        'peak_floor': 96, 'spread': 12, 'peak_weight': 2.0, 'min_level': 90,
        'attacks': [
            atk('Stone Fist', '5d10+24', 'blunt', 'stunned', 0.3, 2),
            atk('Hurled Boulder', '4d8+18', 'blunt', 'slowed', 0.3, 3, ranged=True),
        ],
        'resistances': ['slash', 'pierce', 'fire', 'cold', 'lightning', 'poison', 'drain'],
        'weaknesses': ['blunt'],
        'tags': ['elemental', 'construct'], 'harvest_tier': 3, 'treasure': dict(DEEP_GOLD),
        'lore': ("The Sumerian poem Lugal-e tells of Asag, the demon of the mountains, so terrible "
                 "that fish boiled alive in the rivers where he walked. He fathered an army on the "
                 "mountains, and the army was stones. The god Ninurta beat them with his talking mace "
                 "Sharur, and afterwards judged each kind of stone in turn, blessing some and cursing "
                 "others, which is why stones are as they are. Some of the army was never judged. "
                 "Blades, fire, frost and lightning do almost nothing to them. Do what Ninurta did, "
                 "and bring a mace."),
        'frequency': 2,
    },
    # --- Medieval --------------------------------------------------------------
    'totentanz_dancer': {
        'name': 'Totentanz Dancer', 'symbol': 'Z', 'color': [220, 215, 200],
        'hp': '200d10+590', 'speed': 12, 'ai_pattern': 'dancer', 'thac0': -12,
        'peak_floor': 75, 'spread': 9, 'peak_weight': 2.0, 'min_level': 70,
        'attacks': [
            atk('Join the Dance', '3d8+14', 'magic', 'confused', 0.35, 3),
            atk('Bony Hand', '3d8+16', 'drain'),
        ],
        'resistances': ['cold', 'poison', 'drain', 'pierce'], 'weaknesses': ['blunt', 'holy'],
        'tags': ['undead'], 'harvest_tier': 2,
        'treasure': {'gold': [30, 100], 'item_chance': 0.2, 'item_tier': 4},
        'lore': ("After the Black Death, painters covered church walls with the Dance of Death: a "
                 "long chain of skeletons, each leading a living partner by the hand, the pope and "
                 "the emperor and the peasant and the child, and none of them ready. Bernt Notke "
                 "painted thirty yards of it for Lubeck, and a piece survives in Tallinn. These "
                 "dancers have come off the wall. They circle and step and never stand where you "
                 "struck, they take your hands, and your feet start to follow the steps. Fight them "
                 "with your back to a wall."),
        'frequency': 3, 'pack': True, 'pack_size': [3, 4],
    },
    # --- Greek, the very deep ---------------------------------------------------
    'lyssa_madness': {
        'name': 'Madness of Lyssa', 'symbol': 'L', 'color': [170, 40, 90],
        'hp': '510d12+3380', 'speed': 14, 'ai_pattern': 'hit_and_run', 'thac0': -17,
        'peak_floor': 97, 'spread': 12, 'peak_weight': 2.0, 'min_level': 91,
        'attacks': [
            atk('Goad of Madness', '4d8+16', 'magic', 'confused', 0.45, 3),
            atk('Rabid Bite', '5d10+16', 'pierce', 'weakened', 0.3, 4),
        ],
        'resistances': ['magic', 'poison'], 'weaknesses': ['holy'],
        'tags': ['outsider'], 'harvest_tier': 3, 'treasure': dict(DEEP_GOLD),
        'lore': ("Lyssa was the daughter of Night and the spirit of mad rage; her name is also the "
                 "Greek word for rabies. In Euripides, Hera sends her to drive Heracles out of his "
                 "mind, and Lyssa herself protests that it is unjust, and then obeys. Heracles came "
                 "to himself among the bodies of his own family. Her madnesses wander the lowest "
                 "halls: they dart in, bite, turn the mind inside out, and are gone before it turns "
                 "back. A clear head is the only armour against them."),
        'frequency': 2, 'can_phase_blink': True, 'phase_blink_chance': 0.25,
    },
    # --- Japanese, the very deep ----------------------------------------------
    'jorogumo': {
        'name': 'Jorogumo', 'symbol': 's', 'color': [180, 60, 70],
        'hp': '500d12+3220', 'speed': 11, 'ai_pattern': 'ambush', 'thac0': -17,
        'peak_floor': 94, 'spread': 12, 'peak_weight': 2.0, 'min_level': 88,
        'attacks': [
            atk('Silk Line', '4d8+16', 'physical', 'immobilized', 0.4, 2, ranged=True),
            atk('Venom Fangs', '4d10+18', 'poison', 'poisoned', 0.5, 6),
        ],
        'resistances': ['poison', 'cold'], 'weaknesses': ['fire'],
        'tags': ['beast', 'shapeshifter'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("Edo-period storytellers told of the jorogumo, a spider that lives for four hundred "
                 "years and learns to take a woman's shape. At the Joren Falls in Izu a woodcutter "
                 "resting on the bank felt threads winding round his ankle; he tied them to a tree "
                 "stump, and the stump was torn out of the ground and dragged under the water. In "
                 "the dungeon she waits in the dark corners of rooms. The first warning is the silk "
                 "around your feet. Fire is what she fears."),
        'frequency': 2,
    },
    # --- Norse ------------------------------------------------------------------
    'mara': {
        'name': 'Mara', 'symbol': 'm', 'color': [60, 50, 80],
        'hp': '510d12+3290', 'speed': 11, 'ai_pattern': 'aggressive', 'thac0': -17,
        'peak_floor': 96, 'spread': 12, 'peak_weight': 2.0, 'min_level': 90,
        'attacks': [
            atk('Night-Weight', '4d8+16', 'magic', 'sleeping', 0.4, 3),
            atk('Trample', '5d10+20', 'blunt', bonus_vs={'sleeping': 1.5, 'paralyzed': 1.5}),
        ],
        'resistances': ['cold', 'drain', 'magic'], 'weaknesses': ['iron', 'holy'],
        'tags': ['outsider', 'fey'], 'harvest_tier': 3, 'treasure': dict(DEEP_GOLD),
        'lore': ("The Ynglinga saga tells how King Vanlandi broke his word to his Finnish wife, and "
                 "she paid a witch to send a mara after him. As soon as he slept it trod on him. His "
                 "men held his head and it trampled his legs; they held his legs and it pressed on "
                 "his head until he died. Our word nightmare is her name. A mara lays its weight on "
                 "you until you sleep where you stand, and then it tramples, harder on a sleeper. "
                 "Old households hung a knife of steel over the bed."),
        'frequency': 2,
    },
})

# Lore-chosen corpse sizes (data/monster_sizes.json).
SIZES = {
    'ker': 'small', 'hellmouth': 'huge', 'mere_wife': 'large', 'endor_medium': 'medium',
    'erinyes_greater': 'medium', 'tiamat_blood': 'medium', 'hels_handmaid': 'medium',
    'stheno_gorgon': 'large', 'euryale_gorgon': 'large', 'gashadokuro': 'huge',
    'autolycus_heir': 'medium', 'strix': 'small',
    'bronze_sentinel': 'huge', 'sown_warrior': 'medium', 'takshaka_brood': 'large',
    'rakshasa_illusionist': 'medium', 'ushabti_overseer': 'medium', 'ushabti_worker': 'medium',
    'sekhmet_lioness': 'large', 'ammit_devourer': 'large', 'mazandaran_div': 'large',
    'dahaka_wyrm': 'huge', 'khrafstra_swarm': 'small', 'galla_demon': 'medium',
    'girtablilu': 'large', 'asag_stone_warrior': 'large', 'totentanz_dancer': 'small',
    'mara': 'medium', 'lyssa_madness': 'tiny', 'jorogumo': 'large',
}

# --- 14. a common way to see the unseen ----------------------------------------
POTION_ID = 'potion_of_see_invisible'
POTION = {
    'name': 'potion of see invisible',
    'unidentified_name': 'pale mirror-bright potion',
    'symbol': '!',
    'color': [225, 230, 245],
    'weight': 0.4,
    'min_level': 28,
    'effect': 'see_invisible',
    'power': '',
    'duration': 150,
    'floorSpawnWeight': {'1-20': 0, '21-40': 15, '41-60': 30, '61-80': 40, '81-100': 45},
    'lore': ("The king of Aram sent an army by night to take the prophet Elisha at Dothan, and "
             "in the morning his servant saw the city ringed with horses and chariots and cried "
             "out. Elisha prayed that the young man's eyes be opened, and he looked again and saw "
             "the hills full of horses and chariots of fire. This potion opens the eyes a little "
             "way in the same direction: for a while the drinker sees what walks unseen."),
    'peak_weight': 0.5,
}


def apply(data: dict) -> list[str]:
    log = []
    for mid, d in NEW.items():
        want = dict(d)
        cur = data.get(mid)
        # What a creature carries is decided by tools/balance/gold_by_lore.py
        # (economy refactor 2026-10-17, gold by lore): keep its gold and purse.
        if isinstance(cur, dict) and isinstance(want.get('treasure'), dict):
            tr = dict(want['treasure'])
            for k in ('gold', 'purse'):
                if k in (cur.get('treasure') or {}):
                    tr[k] = cur['treasure'][k]
            want['treasure'] = tr
        if cur != want:
            log.append(f'{mid}: {"updated" if mid in data else "added"}')
            data[mid] = want
    for mid, fields in RETUNE.items():
        cur = data[mid]
        for k, v in fields.items():
            if cur.get(k) != v:
                cur[k] = v
                log.append(f'{mid}: {k}')
    return log


def apply_sizes(sizes: dict) -> list[str]:
    table = sizes['sizes']
    log = [f'{mid}: size {s}' for mid, s in SIZES.items() if table.get(mid) != s]
    if log:
        was_sorted = list(table) == sorted(table)
        table.update(SIZES)
        if was_sorted:
            sizes['sizes'] = dict(sorted(table.items()))
    return log


def apply_potion(pots: dict) -> list[str]:
    if pots.get(POTION_ID) == POTION:
        return []
    pots[POTION_ID] = dict(POTION)
    return [f'{POTION_ID}: added']


def main():
    write = '--write' in sys.argv
    for path, fn in ((MONSTERS, apply), (SIZES_PATH, apply_sizes), (POTIONS, apply_potion)):
        data, fmt = jsonfmt.load(path)
        log = fn(data)
        print(f'{path.name}:', '\n  '.join([''] + log) if log else 'nothing to change')
        if write and log:
            jsonfmt.save(path, data, fmt)
            print('  written')


if __name__ == '__main__':
    main()
