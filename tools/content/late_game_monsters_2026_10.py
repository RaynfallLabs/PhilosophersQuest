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
        'lore': ("Hesiod painted the Keres on the shield of Heracles as dark spirits of death with white and gnashing teeth, fighting one another over the fallen, each greedy to drink the dark blood first. Homer set one upon the shield of Achilles, dragging a dead man through the battle by his feet. They never come alone. Any one of them is weak, as death is reckoned in these deeps, but there are always more of them than there are of you, and a wounded man draws the whole flock. Kill them swiftly, therefore, and many at a time."),
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
        'lore': ("Medieval painters showed Hell as a mouth, the gaping jaws of Leviathan, the beast of Job, out of whose mouth go burning lamps. On the Doom paintings over church arches and upon the stages of the mystery plays the damned were herded into it, while men worked the jaws with ropes and blew smoke from the throat. One such mouth lies flat in the floor of the deeps, and its open gullet looks exactly like a stair going down. Every floor has but one way down, so if ever you find two, be sure that one of them is such a mouth, and hungry."),
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
        'lore': ("The Beowulf poet gave no name to Grendel's mother, but only a kind, merewif, the mere-wife, she-wolf of the deep. She rose out of the dark water to avenge her son, and when Beowulf followed her down she dragged him to her hall beneath the mere. There his borrowed sword Hrunting, which had never failed in battle, would not bite upon her hide, and he was forced to wrestle with her until he found a giant's blade on her wall. Her kind lie in wait beneath black water still, and a blade will glance off that hide, but a heavier weapon will not."),
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
        'lore': ("King Saul had driven every medium out of Israel, yet on the night before his last battle he put on a disguise and sought out the one who remained at Endor. At his word she called up the prophet Samuel, an old man wrapped in a mantle, who told Saul that on the morrow he and his sons would be with him among the dead. The craft has descended through all her line. When they call, whatever is listening in the dark comes up, and much of it cannot be seen, so kill the one who is calling before the room fills."),
        'frequency': 2, 'summon_kind': ['darkhelm_shade', 'dread_wraith'],
        'summon_cooldown': 6, 'summon_max': 3, 'perception_range': 10,
    },
    # --- 6. The Furies, greater: three that will not stand still -----------------
    'erinyes_greater': {
        'name': 'Greater Erinys', 'symbol': 'E', 'color': [140, 30, 40],
        'hp': '300d12+1290', 'speed': 13, 'ai_pattern': 'hit_and_run', 'thac0': -15,
        'peak_floor': 86, 'spread': 12, 'peak_weight': 2.0, 'min_level': 80,
        'attacks': [
            atk('Scourge of Serpents', '4d8+16', 'slash', 'feared', 0.3, 3),
            atk('Blood-Weeping Glare', '3d8+16', 'magic', 'blinded', 0.35, 3),
        ],
        'resistances': ['fire', 'cold', 'poison'], 'weaknesses': [],
        'tags': ['outsider'], 'harvest_tier': 4, 'treasure': dict(DEEP_GOLD),
        'lore': ("Three were the Erinyes: Alecto the unceasing, Megaera the grudging and Tisiphone the avenger of murder. In Aeschylus they hunted Orestes for his mother's blood from Argos to Delphi and on to Athens, with snakes in their hair and blood weeping from their eyes, and they slept only when Apollo compelled them. At the last Athena appeased them with a new home beneath the city and a new name, the Kindly Ones, but none in these depths has made them any such offer. They come as three, strike and scatter and come again, and men take flight at the very look of them."),
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
        'lore': ("When Marduk had caught Tiamat the salt sea in his net, as the Babylonian poem of creation tells, he drove the winds into her mouth and split her like a fish for drying, and of the halves he made sky and earth. Then he cut the channels of her blood, and the north wind bore it away to secret places, of which this is one. That blood still crawls, salt and venomous, and it remembers being divided, so that a small cut does no more than make two of it. One great blow, such as a long answer chain gives, will end it outright."),
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
        'lore': ("Snorri Sturluson told how the hall of Hel is furnished: her plate is called Hunger, her knife Famine and her bed Sickbed, and her servants are Ganglati and Ganglot, whose names both mean the slow-walker. Many maids serve Hel now, and all of them are slow. They walk among her dead mending what the living break, and by their touch the same slowness enters into a warm body. Wherever the dead keep getting up again, look for the maid behind them and put her down first."),
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
        'lore': ("Of three sisters Medusa alone was mortal, and death has no power over the others, Stheno the mighty and Euryale the far-roaming. Hesiod gives them brazen hands and golden wings. When Perseus fled with their sister's head they rose from their beds and chased him over the sea until the helm of Hades hid him, and they have sought him ever since. The living turn rigid as stone beneath their gaze, and a killing blow lays either of them low for no more than a moment."),
        'frequency': 0, 'gaze_paralyze': 2, 'gaze_cooldown': 6, 'gaze_group': 'gorgon_sisters',
        'revive_once_on_death': True, 'revive_hp_pct': 0.3,
        'revive_message': "Stheno rises again, for death cannot hold an immortal.",
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
        'lore': ("Pindar tells that Athena devised the music of the pipes to copy one sound, the shrill wailing that Euryale raised over her beheaded sister while the snakes in her hair keened along with her. Euryale has made no end of grieving or of hunting, and she goes nowhere without Stheno. Her wail drives men back and her gaze holds them where they stand, and like her sister she is immortal, so that she may be put down, but not for long. Against her a polished shield or a blindfold is worth more than any sword."),
        'frequency': 0, 'gaze_paralyze': 1, 'gaze_cooldown': 6, 'gaze_group': 'gorgon_sisters',
        # One shared gaze between the sisters (gaze_group), and Euryale's holds
        # a turn: her weapon is the wail. Stheno's still holds two.
        'revive_once_on_death': True, 'revive_hp_pct': 0.3,
        'revive_message': "Euryale rises again, wailing, for death cannot hold an immortal.",
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
        'lore': ("Japanese storytellers of the last century spoke of the gashadokuro, the starving skeleton, fifteen times the height of a man and built from the bones of all who died of hunger or in battle and lay unburied. It walks at night without a sound, and no warning is given but a ringing in the ears, gasha gasha, a moment before it bites off a traveller's head. This one has folded itself into a corner of the dungeon, where it may be taken for a heap of old bones until it stirs. A spear passes between such ribs, but a hammer will find bone there to break."),
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
        'lore': ("Autolycus, the grandfather of Odysseus, outdid all men in thieving and in oaths that meant nothing, and had that gift from Hermes himself. He took a famous boar-tusk helmet out of a locked house and the cattle of Sisyphus out of a guarded field, and he changed their colour lest their owner know them, so that Sisyphus outwitted him only by carving his own name beneath their hooves. His heirs carry on the family trade. They brush against you and are gone, leaving purse or pack the lighter, but run them down and what they took is yours again."),
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
        'lore': ("Ovid in the Fasti describes the strix as a bird of the night, big of head and staring of eye, with a beak made for snatching, grey feathers and hooked claws, that flies in darkness and drinks blood. Whether striges are born birds or are old women changed by a spell, he says that nobody knows. They came for the infant Proca in his cradle, but the nymph Cranae barred them out with a branch of whitethorn at the window. In these halls they hunt in threes, and while one sings you to sleep the others drink."),
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
        'lore': ("At the sound of the third trumpet a great star fell burning upon the rivers and springs, and John gives its name as Wormwood and writes that a third of the waters were turned bitter, and many died of drinking them. Where the ash of that star settled there grew this pale and spreading thing, which drinks the light and breathes out bile. Its spores poison whatever they touch, and the star's ash sheds from it even now and stings the eyes until they are blind."),
    },
    'void_seraph': {
        'attacks': [
            {'name': 'Void Lance', 'type': 'magic', 'piercing': True, 'damage': '5d10+31'},
            atk('Hush of a Dying Star', '4d8+14', 'magic', 'silenced', 0.35, 4, ranged=True),
            atk('Unmaking Gaze', '4d8+14', 'magic', 'teleportitis', 0.3, 8),
        ],
        'lore': ("Isaiah beheld the seraphim above the throne, and each had six wings, two to cover the face, two to cover the feet and two with which to fly. This one fell and kept its wings, and when it lowers the upper pair there is but a hollow behind them where a face and a name used to be. Its voice is the hush of a star going out, and within that hush no spell can be spoken. Its gaze unmakes the place that a thing has in the world, so that whoever it falls upon is forever slipping out of the spot where he stands."),
    },
    'iron_horseman': {
        'can_charge': True, 'charge_bonus_mult': 1.3,
        'lore': ("Four riders appeared to John, one upon a white horse, one upon red, one upon black, and Death upon a pale horse with Hades following after. The iron horseman is none of the four, but of the kind that rides in their dust, with armour welded shut and man and steed grown into one shape of iron. Given a straight run it lowers the lance and charges and will turn aside for nothing, and its hooves leave men senseless on the ground. Do not stand, therefore, at the end of a long corridor when it is near."),
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
        'lore': ("With the turning of the seasons thieves drift in and out of the bandit's trade, wintering in a warm gang and picking pockets in a market town in spring. They love a quiet boot and a turned back better than a duel, and a purse cut in passing better than either, and they have this saying among them: \"the man who shows his sword has already decided he would rather not use it.\" When one of them has your gold he runs, and if you can catch him it is yours again."),
    },
    'leprechaun': {
        'attacks': [
            {'name': 'Hex', 'damage': '1d2+1', 'type': 'magic', 'effect': 'teleportitis',
             'effect_chance': 0.4, 'effect_duration': '1d8'},
            atk('Light Fingers', '1d2', 'physical', steal='gold', steal_chance=0.8),
        ],
        'after_theft': 'teleport',
        'lore': ("The leprechaun of the Irish tales is a solitary cobbler, who is heard tapping at a single shoe beneath a hedge, and whoever catches him may demand his crock of gold, if only he keeps both eyes upon him, for at one glance aside the little man is gone. Those who dwell below have learned that craft backward, and with a touch and a wink your purse grows lighter and he is standing elsewhere upon the floor. He has not left that floor, and if you find him the gold will come back to you."),
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
        'lore': ("Between this world and the next the ethereal filcher slips to and fro, an undead thing without a body, and steals from the living. Bright and magical things draw it, and it carries them away to its hidden lairs in the ether, for its fingers pass through a closed pack as easily as through air. It is seldom fierce unless it is cornered, and once it has its prize it will flee sooner than fight, but if it is slain, whatever it took will fall out of it again."),
    },
    # --- 13. two more invisible creatures by lore
    'air_elemental': {
        'invisible': True,
        'lore': ("Since men first felt the wind they have given it names. The Greeks had four, Boreas, Notus, Eurus and Zephyrus, and said that King Aeolus held the rest shut within a cave, and Paracelsus called the spirits of the air sylphs. An air elemental is a whirlwind with a will of its own, quick as a thrown knife and invisible as the wind of which it is made. It is full of grit and splinters that flay whatever it wraps around. You see nothing of it until it has struck you, and even then you see only the dust that it carries."),
    },
    'poltergeist': {
        'invisible': True,
        'lore': ("Poltergeist is a German word that means 'noisy ghost', and it is given to the spirit of one who died bewildered and has remained so. It has no shape to show but only a temper, by which doors slam and crockery flies and a chair will skate across the room to break against the wall. No eye has ever seen one, though anyone may see what it throws, and from what quarter it was thrown. It has no wish to hunt the living, but rages at them because they are free to leave."),
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
        'lore': ("Talos, the man of bronze, was made by Hephaestus to guard Crete, and three times a day he walked about the island, throwing boulders at any ship that came near. When men landed, he heated himself red-hot in a fire and embraced them. He had a single vein running from neck to ankle and stopped with one bronze nail, but Medea bewitched him with her eyes, the nail came out, and the ichor ran from him like molten lead. His copies guard the deep halls. Swords and hammers ring off them, so seek out the nail with a point or with a spell."),
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
        'lore': ("Cadmus slew the dragon of Ares, and by Athena's counsel he sowed its teeth in a ploughed field, whereupon armed men rose out of the furrows, already clad in bronze and already wrathful. He threw a stone into their midst, and each blamed the man beside him, and they fought until only five were left. Jason reaped the same harvest at Colchis and overcame it by the same device. The sown men still rise in companies and fight as one, but if you confuse them, or throw something into the middle of them, they will turn on each other."),
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
        'lore': ("Parikshit the king, of whom the Mahabharata tells, was cursed to die of a serpent's bite on the seventh day, and he shut himself in a tower upon a single pillar and admitted none but holy men. But Takshaka the serpent king sent his nagas in the guise of holy men bearing fruit, and hid himself within one fruit as a tiny worm the colour of copper. When the king took it up, Takshaka put on his true shape and bit. His brood still hide in fruit, so beware of any perfect apple that you find lying on a dungeon floor."),
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
        'lore': ("Indrajit, the conqueror of Indra, was the son of Ravana, and he made war on Rama's army from within the clouds, where no arrow could find him. With the serpent noose, which was of living snakes, he bound Rama and Lakshmana helpless on the field, until Garuda, the enemy of every serpent, descended and the snakes fled from his shadow. By his maya the army of monkeys saw things that were not there. The rakshasa illusionists who learned from him keep their distance, tie you where you stand and fill your eyes with lies, so you must close the distance, or else kill them from where you are."),
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
        'lore': ("An Egyptian of means took ushabtis with him to the tomb, little workers of blue faience, one for every day of the year, and on them was written the sixth spell of the Book of the Dead: 'O ushabti, if I am called to work in the land of the dead, you shall answer: Here I am.' Over every ten was set an overseer with a whip, to hold them to their labour. The overseers of these depths have outlived their masters, and still they read out the spell and still the workers answer. Break the one who has the whip, and all the rest will fall quiet."),
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
        'lore': ("In the tomb it was a little figure of blue faience no bigger than a man's hand, but here below it has the stature of a man. It carries the hoe and the basket of sand that were painted upon it, and it obeys the sixth spell, answering 'Here I am' and going to its work. There is neither malice nor will in it, and if it throws the sand in your eyes, that is only because the overseer has bidden it."),
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
        'lore': ("Mankind once plotted against Ra, and he sent forth his Eye against them as Sekhmet the lioness, who slaughtered until she waded in blood and would not stop. To save the rest, Ra had seven thousand jars of beer dyed red with ochre and poured over the fields, and she drank it for blood, fell drunk and forgot her wrath. Her lionesses were never given the beer. Their hot breath is the desert wind and each blow they strike makes the next one fiercer, so end the fight quickly, or walk away and let them cool."),
        'frequency': 2, 'fury_per_attack': 0.08, 'fury_cap': 0.8,
        'fury_message': "The eyes of the Lioness of Sekhmet go red, and she is wading in blood now.",
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
        'lore': ("Anubis set the heart of each dead man upon a scale against the feather of Ma'at in the Hall of the Two Truths, and Thoth wrote down the judgment. Beside them crouched Ammit the Devourer, who had a crocodile's head, the forequarters of a lion and the hindquarters of a hippopotamus, and any heart heavier than the feather was hers to eat, so that its owner perished for ever. Her get still weigh every heart they meet, and their bite is gentle upon a clean conscience and savage upon a heavy one."),
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
        'lore': ("The Shahnameh tells how King Kay Kavus marched to conquer Mazandaran, and how the White Div answered him with sorcery. Darkness descended on the Persian host and a hail of stones fell out of it, and when it lifted the king and his men were blind. Then Rostam went alone through seven trials, slew the White Div in his cave, and with drops of the div's blood restored the sight of his king. The divs of Mazandaran still fight from a distance and put out the sight of men, so bring some remedy for the eyes, or else close in swiftly."),
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
        'lore': ("Azhi Dahaka, the dragon of the Avesta with three heads and six eyes, was made by the evil spirit to empty the world of good things. When the hero Thraetaona smote it with his blade, snakes, scorpions, toads and lizards poured from the wound, and he saw that if he cut it to pieces the world would be filled with vermin, and so he chained it beneath Mount Damavand instead. Its brood carries the same curse, and every cut or stab lets loose a swarm, so the wise will club it, burn it or blast it."),
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
        'lore': ("Zoroastrian books give the name khrafstra to the noxious creatures, snakes, scorpions, toads, lizards and stinging flies, that the evil spirit made to mar the good creation. It was accounted a good deed to kill them, and the priests kept a special stick for the purpose. This seething knot spilled out of the wound of a Dahaka, and from that hour it has not ceased to bite."),
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
        'lore': ("When Inanna returned from the underworld, the galla came with her to seize one who should take her place. They eat no food, says the Sumerian poem, they drink no water and accept no gift, and they pull the wife from the husband's arms and the child from the father's knee. They pursued her husband Dumuzi across the steppe, and though the sun god turned him three times into a gazelle that he might escape, three times they found him. In gangs they come to grab and hold and drag away, and they will never give up the chase."),
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
        'lore': ("Gilgamesh came to the twin peaks of Mount Mashu, where the sun goes in and out, and found the gate kept by a scorpion-man and his wife, human to the waist and scorpion below, whose terror was overwhelming and whose glance was death. He told them truly of his grief and they let him pass, but in these depths they will ask no questions. They hunt in pairs, drawing bows as the Babylonian boundary stones show them. Their shells turn both blade and arrow and their sting stops a man where he stands, but a hammer will crack them."),
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
        'lore': ("Asag was the demon of the mountains, so terrible that fish boiled alive in the rivers where he walked, and upon the mountains he fathered an army, and every soldier in it was a stone. So says the Sumerian poem Lugal-e, and it tells how the god Ninurta beat them with Sharur, his talking mace, and afterward judged each kind of stone, blessing some and cursing others, which is why stones are as they are. But some of that army was never judged, and blades, fire, frost and lightning do almost nothing to them, so do as Ninurta did, and bring a mace."),
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
        'lore': ("After the Black Death the walls of churches were painted with the Dance of Death, a long chain of skeletons that led each a living partner by the hand, pope and emperor, peasant and child, and none of them ready. Bernt Notke painted thirty yards of it for Lubeck, and a piece survives in Tallinn. These dancers have stepped down from the wall. They circle and step and are never standing where you struck, and they take you by the hands until your feet begin to follow the steps. Whoever must fight them should set his back to a wall."),
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
        'lore': ("Night was the mother of Lyssa, the spirit of raging madness, whose name is also the Greek word for rabies. Euripides tells that Hera sent her to drive Heracles out of his wits, and that Lyssa herself protested the injustice and yet obeyed, and when he came to himself it was among the bodies of his own family. Her madnesses wander the lowest halls, where they dart in, bite, turn the mind inside out and are gone before it turns back again. Against them a clear head is the only armour."),
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
        'lore': ("Edo storytellers gave the name of jorogumo to a spider that has lived four hundred years and has learned to take the shape of a woman. A woodcutter who rested by the Joren Falls in Izu felt threads winding about his ankle, and he tied them to a stump, which was torn from the ground and dragged beneath the water. In the dungeon she waits in the dark corners of rooms, and the first warning of her is silk about your feet, but she herself has a great fear of fire."),
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
        'lore': ("Vanlandi the king broke faith with his Finnish wife, as the Ynglinga saga tells, and she paid a witch to send a mara against him. The mara trod on him as soon as he slept, and when his men held his head she trampled his legs, and when they held his legs she pressed upon his head until he died. From her name comes our word nightmare. A mara lays her weight on you until you sleep where you stand, and then she tramples, the harder upon a sleeper, and for this cause old households hung a knife of steel over the bed."),
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
    'lore': ("The king of Aram sent an army by night to seize the prophet Elisha at Dothan, and when morning came the prophet's servant saw the city ringed with horses and chariots and cried out. Then Elisha prayed that the young man's eyes be opened, and he looked again and beheld the hills full of horses and chariots of fire. This potion opens the eyes a little way toward such sight, so that for a while the drinker sees what walks unseen."),
    'peak_weight': 0.5,
}


_AFFINITY_KEYS = ('weaknesses', 'resistances', 'shrugs_off', 'status_immune', 'status_weak')


def _typed_like(attacks: list, cur) -> list:
    """A plain 'physical' attack keeps the form the affinity pass gave it."""
    typed = {a.get('name'): a.get('type')
             for a in ((cur or {}).get('attacks') or []) if isinstance(a, dict)}
    return [dict(a, type=typed[a.get('name')])
            if a.get('type') == 'physical' and typed.get(a.get('name')) not in (None, 'physical')
            else a for a in attacks]


def _keep_affinity(want: dict, cur) -> None:
    if not isinstance(cur, dict):
        return
    for k in _AFFINITY_KEYS:
        if k in cur:
            want[k] = cur[k]
    if isinstance(want.get('attacks'), list):
        want['attacks'] = _typed_like(want['attacks'], cur)


def _banded(data: dict) -> dict:
    """The named foes tools/balance/mini_boss_bands.py tunes."""
    sys.path.insert(0, str(ROOT / 'tools' / 'balance'))
    import mini_boss_bands
    return mini_boss_bands.roster(data)


def _seated() -> set:
    """The mini-bosses tools/balance/mini_boss_seats.py seats by lore (with
    the escorts that go where their leader goes)."""
    sys.path.insert(0, str(ROOT / 'tools' / 'balance'))
    import mini_boss_seats
    return set(mini_boss_seats.SEATS) | set(mini_boss_seats.ESCORTS)


def _moved() -> dict:
    """The kinds tools/balance/monster_pass_2026_11_17.py re-placed."""
    sys.path.insert(0, str(ROOT / 'tools' / 'balance'))
    import monster_pass_2026_11_17
    return monster_pass_2026_11_17.MOVES


def apply(data: dict) -> list[str]:
    log = []
    from assign_monster_families import family_for
    for mid, d in NEW.items():
        want = dict(d)
        cur = data.get(mid)
        # Its monster family (tools/content/assign_monster_families.py): the
        # one already written wins, so a regeneration never drops or
        # re-decides it.
        want['family'] = (cur or {}).get('family') or family_for(mid, want)
        # What a creature carries is decided by tools/balance/gold_by_lore.py
        # (economy refactor 2026-10-17, gold by lore): keep its gold and purse,
        # and its treasure chance and kinds (2026-10-18).
        if isinstance(cur, dict) and isinstance(want.get('treasure'), dict):
            tr = dict(want['treasure'])
            for k in ('gold', 'purse', 'treasure_chance', 'treasure_kinds'):
                if k in (cur.get('treasure') or {}):
                    tr[k] = cur['treasure'][k]
            want['treasure'] = tr
        # Its to-hit is decided by tools/balance/rebake_thac0.py (bug bash
        # 3.3.2: rebaked to the armour line): the THAC0 written here is its
        # lore accuracy, kept as thac0_lore; the rebaked thac0 stays.
        if isinstance(cur, dict) and 'thac0_lore' in cur:
            want['thac0_lore'] = cur['thac0_lore']
            want['thac0'] = cur.get('thac0', want.get('thac0'))
        # How each attack lands (tools/content/tag_attack_delivery.py, the
        # armour guards): a delivery already written wins, else the rule.
        if isinstance(want.get('attacks'), list):
            sys.path.insert(0, str(ROOT / 'src'))
            from guards import classify
            had = {a.get('name'): a.get('delivery')
                   for a in ((cur or {}).get('attacks') or []) if isinstance(a, dict)}
            want['attacks'] = [dict(a, delivery=had.get(a.get('name')) or a.get('delivery')
                                    or classify(a)) for a in want['attacks']]
        # What it is weak to, resists and shrugs off, its status lists and
        # the form of each plain blow are decided by
        # tools/content/affinity_pass.py (the monster lore pass, winning
        # build 2026-11-13): the ones already written win.
        _keep_affinity(want, cur)
        # Its pronoun (round 3, 2026-11-14: data/monsters.json `pronoun`):
        # the one already written wins.
        if isinstance(cur, dict) and cur.get('pronoun'):
            want['pronoun'] = cur['pronoun']
        # Its depth, and the numbers baked for it there, are decided by
        # tools/balance/monster_pass_2026_11_17.py (rulings 11 and 12,
        # 2026-11-17: the Mara moved to Fenrir's rime halls): the ones
        # already written win.
        if isinstance(cur, dict) and mid in _moved():
            for k in ('hp', 'peak_floor', 'spread', 'min_level', 'peak_weight', 'thac0',
                      'thac0_lore', 'harvest_tier', 'regeneration'):
                if k in cur:
                    want[k] = cur[k]
            if isinstance(want.get('treasure'), dict) and 'item_tier' in (cur.get('treasure') or {}):
                want['treasure'] = dict(want['treasure'], item_tier=cur['treasure']['item_tier'])
            dmg = {a.get('name'): a.get('damage') for a in (cur.get('attacks') or [])
                   if isinstance(a, dict)}
            want['attacks'] = [dict(a, damage=dmg.get(a.get('name'), a.get('damage')))
                               for a in want.get('attacks') or []]
        # A mini-boss's seat by lore and its signature drop are decided by
        # tools/balance/mini_boss_seats.py (ruling 13, 2026-11-17: Stheno and
        # Euryale come for Medusa's killer on floor 44): the ones already
        # written win.
        if isinstance(cur, dict) and mid in _seated():
            for k in ('peak_floor', 'min_level', 'harvest_tier', 'spawn_chance'):
                if k in cur:
                    want[k] = cur[k]
            if isinstance(want.get('treasure'), dict):
                tr = dict(want['treasure'])
                for k in ('item_tier', 'unique_drop_id', 'gold'):
                    if k in (cur.get('treasure') or {}):
                        tr[k] = cur['treasure'][k]
                want['treasure'] = tr
        # Its health and the weight of its blows, for a named foe, are decided
        # by tools/balance/mini_boss_bands.py (mini-boss tuning, 2026-11-14):
        # the ones already written win.
        if isinstance(cur, dict) and mid in _banded(data):
            want['hp'] = cur.get('hp', want.get('hp'))
            dmg = {a.get('name'): a.get('damage') for a in (cur.get('attacks') or [])
                   if isinstance(a, dict)}
            want['attacks'] = [dict(a, damage=dmg.get(a.get('name'), a.get('damage')))
                               for a in want.get('attacks') or []]
        if cur != want:
            log.append(f'{mid}: {"updated" if mid in data else "added"}')
            data[mid] = want
    for mid, fields in RETUNE.items():
        cur = data[mid]
        for k, v in fields.items():
            if k == 'attacks' and isinstance(v, list):
                from guards import classify
                had = {a.get('name'): a.get('delivery')
                       for a in (cur.get('attacks') or []) if isinstance(a, dict)}
                v = [dict(a, delivery=had.get(a.get('name')) or a.get('delivery')
                          or classify(a)) for a in v]
                v = _typed_like(v, cur)
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
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "balance"))
    import lore_pass_guard
    lore_pass_guard.refuse("late_game_monsters_2026_10")
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
