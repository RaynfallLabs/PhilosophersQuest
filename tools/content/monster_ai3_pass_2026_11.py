"""
Monster behaviour, third wave (AI-3, 2026-11-20): the data the behaviours
read, written onto EXISTING kinds by their lore, their numbers and lines in
data/monster_ai.json, and their tells.

Offline tooling (not loaded at runtime). Idempotent: every run sets the same
values; nothing is appended twice.

    py tools/content/monster_ai3_pass_2026_11.py            # report
    py tools/content/monster_ai3_pass_2026_11.py --write    # write the data

data/monsters.json and data/monster_ai.json keep their layout (json indent
2, CRLF: the dump reproduces each file byte for byte); data/tells.json is
edited as text, its new entries set after 'light_shy' and its order keys
after 'immobilized' and 'light_shy', so its compact lists stay as they are.

What each block is for, and the lore behind it, is in the comments by it
and in docs/systems/monsters.md, 'Monster behaviour, third wave'.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MONSTERS = ROOT / 'data' / 'monsters.json'
AI_RULES = ROOT / 'data' / 'monster_ai.json'
TELLS = ROOT / 'data' / 'tells.json'
HINTS = ROOT / 'data' / 'hints.json'

# Recall Lore hints (data/hints.json): the source, never the mechanic, no
# number or key (tests/test_hint_pool.py). Tiers 4 and 5, where the pool
# has room.
HINTS_NEW: dict = {
    '4': [
        "Jonah came out of the great fish alive. Whatever takes a man whole can be cut open from within.",
        "A bandit captain carries something for a bad day. Make his a short one, and whatever he saved is yours.",
        "Ask any Irishman: a leprechaun pays only when there is nowhere left for him to run.",
    ],
    '5': [
        "A spell takes a breath to say. A blow struck in that breath is worth two struck after it.",
        "The dead in their mounds guard what is theirs and no more. Leave the barrow, and the barrow lets you go.",
        "Stand beside a fire elemental or a frost giant and you burn or freeze, though neither has struck you.",
    ],
}


def _ward(sid, name, share=0.5, turns=4, below=0.5, cast=None, weight=6, cooldown=12):
    s = {'id': sid, 'kind': 'ward', 'name': name, 'share': share, 'turns': turns,
         'cooldown': cooldown, 'weight': weight, 'wind_up': True,
         'when': {'self_hp_below': below}}
    if cast:
        s['cast'] = cast
    return s


def _curse(sid, name, effect, duration, delivery='voice', above=0.5, weight=4, cooldown=10,
           cast=None, wind_up=True):
    s = {'id': sid, 'kind': 'control', 'name': name, 'effect': effect, 'duration': duration,
         'delivery': delivery, 'cooldown': cooldown, 'weight': weight, 'wind_up': wind_up,
         'when': {'hero_hp_above': above}}
    if cast:
        s['cast'] = cast
    return s


def _mend(sid='mend', below=0.5, weight=5):
    return {'id': sid, 'kind': 'heal', 'cooldown': 0, 'weight': weight,
            'when': {'ally_hp_below': below}}


def _escape(sid, name, cast=None, below=0.6, weight=7, cooldown=10):
    s = {'id': sid, 'kind': 'escape', 'name': name, 'cooldown': cooldown, 'weight': weight,
         'when': {'adjacent': True, 'self_hp_below': below}}
    if cast:
        s['cast'] = cast
    return s


def _dispel(sid='unmaking', name='Word of Unmaking', weight=5, cooldown=8):
    return {'id': sid, 'kind': 'dispel', 'name': name, 'cooldown': cooldown, 'weight': weight,
            'when': {'hero_buffed': True}}


def _dark(sid='darkness', name='Darkness', weight=3, cooldown=12, cast=None):
    s = {'id': sid, 'kind': 'darkness', 'name': name, 'cooldown': cooldown, 'weight': weight,
         'when': {'hero_lit': True}}
    if cast:
        s['cast'] = cast
    return s


# ---------------------------------------------------------------------------
# The Caster's Book (src/caster_ai.py): each caster's spells, by its lore.
# Wards when hurt (the shaman's protective charm), a curse on a hero who is
# winning (the witch's evil eye and binding, Circe's sleep), a prayer that
# mends a badly hurt friend, the hag's vanishing, the lich's word that
# unmakes, the dark elf's darkness (the dokkalfar of the Eddas live in it).
# ---------------------------------------------------------------------------
BOOKS: dict = {
    'goblin_shaman': [
        _ward('smoke_ward', 'Smoke Ward',
              cast="{The}'s chant ends: greasy smoke wraps about {him}, and blows slide off it."),
        _curse('smoke_eyes', 'Smoke in the Eyes', 'blinded', 2,
               cast="{The} flings a pinch of smoke at your face."),
    ],
    'orc_shaman': [
        _ward('bone_ward', 'Bone Ward'),
        _curse('blood_dread', 'Blood Dread', 'feared', 2,
               cast="{The} howls the name of {his} god at you."),
    ],
    'kobold_sorcerer': [
        _dark(cast="{The} spits a word, and your light gutters out."),
    ],
    'cult_priest': [
        _mend(),
        _curse('binding_litany', 'Binding Litany', 'immobilized', 2,
               cast="{The}'s litany ends, and your feet will not move."),
    ],
    'cult_hierophant': [
        _dispel(),
        _curse('void_dread', 'Dread of the Void', 'feared', 3, above=0.6),
    ],
    'dark_cultist': [
        _curse('whispered_dread', 'Whispered Dread', 'feared', 2,
               cast="{The} whispers what waits for you below."),
    ],
    'necromancer_apprentice': [
        _ward('grave_ward', 'Grave Ward',
              cast="{The}'s chant ends: grave-dust rises about {him} and hangs in the air."),
    ],
    'battle_mage': [
        _ward('arcane_shield', 'Arcane Shield', turns=3,
              cast="{The}'s chant ends: a shimmer of force wraps about {him}."),
        _escape('blink', 'Blink'),
    ],
    'drow_mage': [
        _dark(),
        _escape('shadow_step', 'Shadow Step',
                cast="{The} steps into a shadow and out of another, four paces off."),
    ],
    'drow_priestess': [
        _dark(),
        _mend(),
        _curse('spider_hold', "Spider's Hold", 'immobilized', 2,
               cast="{The}'s prayer ends, and threads you cannot see bind your legs."),
    ],
    'harrow_witch': [
        _curse('harrow_eye', 'Harrowing Eye', 'slowed', 3, delivery='gaze',
               cast="{The} fixes you with the evil eye."),
    ],
    'plague_witch': [
        _mend(),
        _ward('rag_ward', 'Ward of Plague Rags', share=0.4,
              cast="{The}'s chant ends: buzzing flies swarm about {him}, thick as a cloak."),
    ],
    'green_hag': [
        _curse('evil_eye', 'Evil Eye', 'slowed', 3, delivery='gaze',
               cast="{The} fixes you with the evil eye."),
        _escape('hag_vanish', 'Vanish', cast="{The} cackles and is gone, four paces off."),
    ],
    'annis_hag': [
        _curse('evil_eye', 'Evil Eye', 'feared', 2, delivery='gaze',
               cast="{The} fixes you with the evil eye."),
        _escape('hag_vanish', 'Vanish', cast="{The} cackles and is gone, four paces off."),
    ],
    'night_hag': [
        _curse('nightmare', 'Nightmare', 'sleeping', 2, above=0.6,
               cast="{The} croons a lullaby of bad dreams."),
        _escape('hag_vanish', 'Vanish', cast="{The} cackles and is gone, four paces off."),
    ],
    'sea_hag': [
        _escape('hag_vanish', 'Vanish', cast="{The} cackles and is gone in a smell of brine."),
    ],
    'lich_apprentice': [
        _ward('bone_ward', 'Bone Ward'),
    ],
    'death_mage': [
        _ward('grave_ward', 'Grave Ward',
              cast="{The}'s chant ends: grave-dust rises about {him} and hangs in the air."),
    ],
    'lich': [
        _ward('lich_ward', 'Ward of the Dead', below=0.6),
        _dispel(),
        _curse('lich_hold', 'Grave-Hold', 'paralyzed', 2, above=0.4,
               cast="{The} speaks one cold word, and your limbs lock."),
    ],
    'greater_lich': [
        _ward('lich_ward', 'Ward of the Dead', below=0.6),
        _dispel(),
        _curse('lich_hold', 'Grave-Hold', 'paralyzed', 2, above=0.4,
               cast="{The} speaks one cold word, and your limbs lock."),
    ],
    'lich_lord': [
        _ward('lich_ward', 'Ward of the Dead', below=0.6),
        _dispel(),
    ],
    'arch_lich': [
        _ward('lich_ward', 'Ward of the Dead', below=0.6),
        _dispel(),
        _curse('lich_hold', 'Grave-Hold', 'paralyzed', 2, above=0.4,
               cast="{The} speaks one cold word, and your limbs lock."),
    ],
    'veiled_inquisitor': [
        _curse('seal_of_silence', 'Seal of Silence', 'silenced', 3, above=0.4,
               cast="{The} seals your lips with a word: no spell, no scroll."),
        _curse('binding_litany', 'Binding Litany', 'immobilized', 2, above=0.6, weight=3,
               cast="{The}'s litany ends, and your feet will not move."),
    ],
    'deep_one_priest': [
        _ward('tide_ward', 'Tide Ward',
              cast="{The}'s chant ends: cold sea-water swirls about {him} and will not fall."),
    ],
    'orc_priest': [
        _ward('blood_ward', 'Blood Ward',
              cast="{The}'s prayer ends: {he} daubs {himself} with blood, and blows turn on it."),
    ],
    'goblin_warpriest': [
        _ward('smoke_ward', 'Smoke Ward',
              cast="{The}'s chant ends: greasy smoke wraps about {him}, and blows slide off it."),
    ],
    'rakshasa_illusionist': [
        _escape('maya_step', 'Maya', cast="{The} is not where you struck: {he} stands four paces off."),
    ],
}

# ---------------------------------------------------------------------------
# Held Fast (src/holds.py). The python's coil (natural history), the naga's,
# the Midgard Serpent's brood, the sea serpent of the sagas; the darkmantle
# and the vine that wrap what passes; the gelatinous cube and its titan that
# take a man inside (the swallow); the each-uisge that drags its rider into
# the loch, Grendel's mother hauling Beowulf to the bottom of the mere, the
# crocodile's death roll (Sobek's). Each hold replaces the old stand-in
# rider on that attack (the "slowed" or "paralysed" that played the coil).
# ---------------------------------------------------------------------------
def _hold(kind, dtype, share=0.10, save='STR'):
    return {'kind': kind, 'type': dtype, 'break_share': share, 'max_turns': 4, 'save': save}


_NO_RIDER = {'effect': None, 'effect_chance': None, 'effect_duration': None}
HOLDS: dict = {
    ('rock_python', 'Constrict'): {'hold': _hold('constrict', 'blunt'), **_NO_RIDER},
    ('naga_guardian', 'Constrict'): {'hold': _hold('constrict', 'blunt'), **_NO_RIDER},
    ('assassin_vine', 'Constrict'): {'hold': _hold('constrict', 'blunt', 0.15), **_NO_RIDER},
    ('darkmantle', 'Constrict'): {'hold': _hold('constrict', 'blunt', 0.15)},
    ('sea_serpent_norse', 'Coil Crush'): {'hold': _hold('constrict', 'cold'), **_NO_RIDER},
    ('jormungandr_spawn', 'Constrict'): {'hold': _hold('constrict', 'blunt'), **_NO_RIDER},
    ('void_leviathan', 'Crushing Coil'): {'hold': _hold('constrict', 'blunt'), **_NO_RIDER},
    ('gelatinous_cube', 'Engulf'): {'hold': _hold('swallow', 'acid', 0.15, 'DEX'), **_NO_RIDER},
    ('gelatinous_titan', 'Engulf'): {'hold': _hold('swallow', 'acid', 0.15, 'DEX'), **_NO_RIDER},
    # Slice M wrote the taniwha's swallow with a 'share' the engine does not
    # read (the squeeze is the attack's own dice): set to the shape it reads.
    ('taniwha', 'Gulping Jaws'): {'hold': _hold('swallow', 'acid', 0.15)},
    ('each_uisce', 'Drown Drag'): {'hold': _hold('drag', 'cold', 0.10), **_NO_RIDER},
    ('mere_wife', 'Drag to the Mere'): {'hold': _hold('drag', 'blunt', 0.08), **_NO_RIDER},
    ('sobek_warrior', 'Death Roll'): {'hold': _hold('drag', 'slash', 0.10), **_NO_RIDER},
    # Lurkers whose surprise blow (x1.75) went over the rubric's one-turn cap
    # (25% of the hero's health at their peak floor; the AI-3 audit, D8). By
    # lore their power is the drop, not the dice: the piercer's plunge is a
    # snail's weight on a spike, the treant's slam and the gashadokuro's bite
    # are slow and terrible, and both come first from hiding.
    ('piercer', 'Plunge'): {'damage': '2d6'},
    ('corrupted_treant', 'Slam'): {'damage': '6d10+20'},
    ('gashadokuro', 'Bite Off the Head'): {'damage': '7d10+30'},
}

# ---------------------------------------------------------------------------
# Auras (src/auras.py). Dread: the dullahan, whose sight is death (Irish), the
# death and dread knights, a lich, the old dragons, the draugr whose eyes
# Grettir could not bear (Grettis saga). Heat: Paracelsus's salamanders, the
# fire elementals; Surtr's kin of Muspell. Cold: the frost elementals, the
# frost giants and rime-thurses of Jotunheim, the ice troll. (Slice M's
# stench kinds, the ghast, the mapinguari and the upas tree, keep theirs.)
# ---------------------------------------------------------------------------
def _fear(turns=3, radius=2, line=None):
    a = {'kind': 'fear', 'radius': radius, 'turns': turns}
    if line:
        a['line'] = line
    return a


def _heat(share, radius=1, kind='heat'):
    return {'kind': kind, 'radius': radius, 'share': share}


AURAS: dict = {
    'dullahan_spawn': _fear(3, 3, "To look on {the} is to see your own death coming. You turn to run!"),
    'death_knight': _fear(3, 2),
    'dread_knight': _fear(2, 2),
    'lich': _fear(3, 2),
    'elder_dragon': _fear(3, 3, "The dread of {the} falls on you like a shadow. You turn to run!"),
    'ancient_dragon': _fear(3, 3, "The dread of {the} falls on you like a shadow. You turn to run!"),
    'draugr': _fear(3, 2, "{The}'s eyes catch the light, and you cannot bear to look. You turn to run!"),
    'fire_elemental': _heat(0.03),
    'greater_fire_elemental': _heat(0.03),
    'primordial_fire_elemental': _heat(0.04, 2),
    'magma_elemental': _heat(0.03),
    'lava_elemental': _heat(0.04),
    'fire_giant': _heat(0.02),
    'fire_giant_king': _heat(0.03, 2),
    'ice_elemental': _heat(0.02, 1, 'cold'),
    'primordial_ice_elemental': _heat(0.04, 2, 'cold'),
    'frost_giant': _heat(0.02, 1, 'cold'),
    'frost_giant_jarl': _heat(0.03, 2, 'cold'),
    'rime_thurs': _heat(0.03, 1, 'cold'),
    'ice_troll': _heat(0.02, 1, 'cold'),
}

# ---------------------------------------------------------------------------
# Home Ground (src/home_ground.py): the barrow and mound dead (Karr the Old,
# Glamr), the tomb's guardians and the mummy in his house, the trolls under
# bridge and hill, Polyphemus in his cave, the Nibelung's hoard-keeper, the
# lindworm and the dragons on their gold (Fafnir on Gnitaheath), the sphinx
# on the road to Thebes, Grendel's mother in her mere.
# ---------------------------------------------------------------------------
def _lair(radius, where):
    return {'territorial': True, 'lair_radius': radius,
            'lair_line': f"{{The}} stops at the edge of {{his}} {where} and watches you go."}


LAIRS: dict = {
    'draugr': _lair(8, 'mound'), 'draugr_wight': _lair(8, 'mound'),
    'barrow_wight': _lair(6, 'barrow'), 'cairn_wight': _lair(6, 'cairn'),
    'tomb_guardian': _lair(7, 'tomb'), 'grave_guardian': _lair(6, 'grave'),
    'mummy': _lair(8, 'tomb'), 'anubis_guardian': _lair(7, 'tomb'),
    'troll': _lair(7, 'lair'), 'cave_troll': _lair(7, 'cave'),
    'cyclops': _lair(8, 'cave'), 'nibelung_hoardwarden': _lair(8, 'hoard'),
    'lindworm': _lair(8, 'lair'), 'young_red_dragon': _lair(9, 'hoard'),
    'young_black_dragon': _lair(9, 'hoard'), 'young_dragon': _lair(9, 'hoard'),
    'adult_dragon': _lair(10, 'hoard'), 'sphinx_lesser': _lair(6, 'road'),
    'sphinx_guardian': _lair(6, 'road'), 'mere_wife': _lair(9, 'mere'),
}

# ---------------------------------------------------------------------------
# Uses What It Carries (src/monster_kit.py): a brigand's or a hired sword's
# physic, an orc chief's fire pot (the Byzantines threw Greek fire in clay
# pots), a witch's own draught. Shallow potions only: a pot of fire oil burns
# a man the same on any floor.
# ---------------------------------------------------------------------------
def _k(item, chance):
    return {'item': item, 'chance': chance}


KITS: dict = {
    'bandit_captain': [_k('potion_of_healing', 0.3)],
    'bandit_kingpin': [_k('potion_of_extra_healing', 0.4), _k('flask_of_fire_oil', 0.3)],
    # A thug's is a rag-stoppered pot of lamp oil, badly thrown: far weaker
    # than the alchemist's flask (the audit: the flask's own 16 fire was
    # 37-46% of a floor-4 hero's health), and it breaks as he falls.
    'bandit_thug': [{'item': 'flask_of_fire_oil', 'chance': 0.15,
                     'throw': {'name': 'Pot of Lamp Oil', 'damage': '1d4+1', 'burn': 2},
                     'drops': False}],
    'mercenary_veteran': [_k('potion_of_healing', 0.3)],
    'veteran_knight': [_k('potion_of_extra_healing', 0.3)],
    'orc_warchief': [_k('flask_of_fire_oil', 0.35), _k('potion_of_healing', 0.25)],
    'orc_marauder': [_k('flask_of_fire_oil', 0.3)],
    'hobgoblin_captain': [_k('potion_of_healing', 0.25)],
    'hobgoblin_marshal': [_k('potion_of_extra_healing', 0.3)],
    'goblin_king': [_k('potion_of_healing', 0.25)],
    'bugbear_chieftain': [_k('potion_of_healing', 0.25)],
    'battle_mage': [_k('potion_of_healing', 0.2)],
    'harrow_witch': [_k('potion_of_healing', 0.25)],
    'drow_warrior': [_k('potion_of_healing', 0.2)],
}

# ---------------------------------------------------------------------------
# Skittish, Not Suicidal (src/skittish.py): a caught leprechaun bargains his
# gold for his freedom (Irish folklore).
# ---------------------------------------------------------------------------
_LEP = {'gold_mult': 1.5,
        'line': "{The}, cornered, holds up a fat purse: 'Let me go and it's yours!'",
        'accept_line': "{The} tosses the purse at your feet and is gone in a flash of green.",
        'refuse_line': "'Then you'll get nothing!' {The} squares up to you."}
BARGAINS: dict = {'leprechaun': _LEP, 'leprechaun_hostile': _LEP}


def kind_fields() -> dict:
    out: dict = {}
    for k, v in BOOKS.items():
        out.setdefault(k, {})['spells'] = v
    for k, v in AURAS.items():
        out.setdefault(k, {})['aura'] = v
    for k, v in LAIRS.items():
        out.setdefault(k, {}).update(v)
    for k, v in KITS.items():
        out.setdefault(k, {})['kit'] = v
    for k, v in BARGAINS.items():
        out.setdefault(k, {})['bargain'] = v
    return out


# ---------------------------------------------------------------------------
# data/monster_ai.json: the numbers and lines (one section a behaviour)
# ---------------------------------------------------------------------------
RULES: dict = {
    'casters': {
        '_doc': "src/caster_ai.py (The Caster's Book). A kind's 'spells' (monsters.json) are cast by need: the ready spell whose 'when' holds with the highest 'weight' (ties: the first written). Kinds: ward (Monster.damage_ward 'share' for 'turns'), control (an 'effect' for 'duration' through the rider's road), heal (src/faction.py), escape (a blink four paces off), dispel (one of buff_words' statuses), darkness (light_shy.snuff 'dark'), hurt (pick_attack's weight for one of its own attacks). 'wind_up' spells are chanted a turn first; a blow breaks the chant. 'reach' is how far a spell is aimed; 'cooldown' the default turns before a spell is ready again. Lines: a spell's own 'wind_up' / 'cast' line, else lines.<key>_<kind>, else lines.<key>; {spell} is its name, {buff} the dispelled status.",
        'reach': 6,
        'cooldown': 6,
        'lines': {
            'wind_up': "{The} begins a chant, hands raised.",
            'wind_up_control': "{The} begins a low chant, {his} eyes on you.",
            'cast': "{The}'s chant ends.",
            'cast_ward': "{The}'s chant ends: a ward of bone and smoke rises about {him}.",
            'cast_control': "{The}'s chant ends in a curse.",
            'cast_dispel': "{The} speaks a word of unmaking: your {buff} is torn away!",
            'cast_darkness': "{The} closes {his} fist, and the dark comes down.",
            'cast_escape': "{The} steps into nothing and is four paces off.",
            'spoil': "The blow breaks {the}'s chant!",
            'spoil_held': "{The}'s chant falls silent, broken.",
            'ward_fades': "The ward about {the} fades away.",
            'gaze_blind': "You cannot meet a gaze you cannot see.",
            'resisted': "The curse finds no hold on you.",
            'turned': "Your spell turning throws the curse back on {the}!",
        },
        'unseen': {'wind_up': "Somewhere near, a voice begins to chant.",
                   'darkness': "Somewhere near, a voice speaks, and your light goes out.",
                   'curse': "Somewhere near, a voice speaks a curse.",
                   'dispel': "Somewhere near, a voice speaks a word of unmaking: your {buff} is torn away!"},
        'buff_words': {'hasted': 'haste', 'shielded': 'shield', 'displacement': 'displacement',
                       'fire_shield': 'fire shield', 'cold_shield': 'cold shield',
                       'reflecting': 'reflection', 'magic_resist': 'magic resistance',
                       'invisible': 'invisibility', 'regenerating': 'regeneration'},
    },
    'holds': {
        '_doc': "src/holds.py (Held Fast). An attack's 'hold' {kind: constrict|swallow|drag, type, break_share, max_turns<=4, save: STR|DEX} that lands takes the hero (a DEX save slips it: the 'held' status). Each holder turn it squeezes for that attack's own dice (no roll to hit), typed; a drag first hauls him a tile toward water within drag_reach and at the water's edge pulls him under (drown_mult). A blow or blows on the holder of break_share of its health between two of its turns frees him; so does a STR or DEX struggle (his step) against the hold's DC plus struggle_dc_add, the holder dying, sleeping, held, afraid or broken, Loosed, the Coif of Beowulf, or the status running out. Then he is Recovering (no hold at once again). Lines: <key>_<kind> before <key>; {damage}.",
        'break_share': 0.10,
        'drag_reach': 10,
        'drown_mult': 1.5,
        'struggle_dc_add': 0,
        'lines': {
            'start_constrict': "{The}'s coils close round you!",
            'start_swallow': "{The} swallows you whole! It is dark, and {his} gut closes round you.",
            'start_drag': "{The} seizes you and starts to drag you toward the water!",
            'loosed_loosed': "{The}'s grip slides off you: nothing can hold you.",
            'loosed_grendel': "Grendel-grip: {the} cannot get a hold on you.",
            'squeeze_constrict': "{The}'s coils squeeze you for {damage} damage!",
            'squeeze_swallow': "{The}'s gut burns you for {damage} damage!",
            'squeeze': "{The} holds you fast and crushes you for {damage} damage!",
            'drag': "{The} drags you a step toward the water! ({damage} damage)",
            'under': "{The} pulls you under the black water! You choke for {damage} damage!",
            'struggle_fail_constrict': "You strain against {the}'s coils, but they hold.",
            'struggle_fail': "You fight {the}'s grip, but it holds you fast.",
            'free_struggle_constrict': "You twist out of {the}'s coils!",
            'free_struggle': "You wrench yourself free of {the}!",
            'free_cut_constrict': "{The}'s coils break apart! You are free.",
            'free_cut_swallow': "{The}'s gut splits open, and you climb out!",
            'free_cut': "{The}'s grip breaks! You are free.",
            'free_dead_swallow': "You climb out of {the}'s body.",
            'free_dead': "{The}'s grip goes slack. You are free.",
            'free_held': "{The}'s grip goes slack. You are free.",
            'free_scared': "{The} lets go of you!",
            'free_apart': "You are out of {the}'s reach, and free.",
            'free_loosed': "Nothing can hold you: you slip out of {the}'s grip!",
            'free_grendel': "Grendel-grip: you wrench free of {the}!",
        },
    },
    'auras': {
        '_doc': "src/auras.py (Auras). A kind's 'aura' {kind: fear|stench|heat|cold, radius 1-3, ...} works on the hero each world turn he is within its radius: fear once a fight when he sees it (a WIS save; 'turns'), stench each turn until he once masters his stomach (a CON check; 'effect' for 'turns' at 'chance'), heat and cold a 'share' of his own health a turn (at most twice the strongest at once). A kind's own 'line' / 'steady_line' before these; {damage}.",
        'lines': {
            'fear': "Dread rolls off {the} like a cold wind, and you turn to run!",
            'fear_steady': "Dread rolls off {the}, but you stand your ground. It will not shake you again.",
            'stench': "The reek of {the} turns your stomach.",
            'stench_steady': "You master your stomach against the reek of {the}.",
            'heat': "The heat of {the} scorches you for {damage} damage.",
            'cold': "The cold of {the} bites into you for {damage} damage.",
        },
        'unseen': {
            'heat': "Heat beats at you from somewhere close. ({damage} damage)",
            'cold': "A bitter cold reaches you from somewhere close. ({damage} damage)",
            'stench': "A foul reek from somewhere close turns your stomach.",
            'stench_steady': "You master your stomach against the reek.",
        },
    },
    'home_ground': {
        '_doc': "src/home_ground.py (Home Ground). A 'territorial' kind lets the hero go once he is more than lair_radius + slack tiles from its home and walks back; it knows him again within lair_radius; on its own ground it never breaks. A kind's 'lair_line' before 'line'.",
        'lair_radius': 8,
        'slack': 2,
        'line': "{The} stops at the edge of {his} ground and watches you go.",
        'line_unseen': '',
        'roused_turns': 5,
        'roused_line': "{The} turns on you: {he} will not be struck and walk away.",
    },
    'kit': {
        '_doc': "src/monster_kit.py (Uses What It Carries). A kind's 'kit' [{item, chance}] is rolled once. Under drink_below of its health a healing potion it carries (or stole) is drunk with its turn; a flask of fire oil is thrown at a hero throw_range tiles off with a clear throw. What is left falls where it dies. {potion} {potion_bare} {flask} {amount}.",
        'drink_below': 0.35,
        'throw_range': [2, 4],
        'drink': "{The} gulps down {potion}, and {his} wounds close!",
        'drink_stolen': "{The} gulps down your own {potion_bare}, and {his} wounds close!",
        'drink_wasted': "{The} gulps down {potion}, but {his} wound will not close.",
        'drink_unseen': "Somewhere near, glass clinks and something drinks.",
        'throw': "{The} hurls {flask} at you!",
        'throw_unseen': "Something sails out of the dark at you!",
    },
    'skittish': {
        '_doc': "src/skittish.py (Skittish, Not Suicidal). A cowardly kind keeps keep_near to keep_far tiles off and darts in when the hero's last step took him away from it. Cornered, a kind with a 'bargain' offers its purse once (its treasure roll times gold_mult); the hero is asked (ask_line).",
        'keep_near': 3,
        'keep_far': 5,
        'gold_mult': 1.5,
        'dart_line': "{The} darts in behind you!",
        'offer_line': "{The}, cornered, offers you gold to let {him} go.",
        'accept_line': "{The} drops {his} purse and is gone.",
        'refuse_line': "{The} squares up to you.",
        'ask_line': "He holds up a fat purse: his gold for his freedom. Take it and let him go?",
        'void_line': "The chance is gone, and the purse with it.",
    },
    'surprise': {
        '_doc': "src/surprise.py (Lurkers Keep Their Promise). An ambusher springs when the hero is within spring_reach tiles with nothing between them; unseen till then, its first blow that lands is a surprise (x1.75, as a mimic's). Spotted first, or a mimic of a kind he knows, it surprises no one.",
        'spring_reach': 2,
    },
}

# ---------------------------------------------------------------------------
# Tells (data/tells.json): what the eye sees, what it does, what to do.
# ---------------------------------------------------------------------------
TELLS_AFTER_IMMOBILIZED = ['hold_swallow', 'hold_constrict', 'hold_drag', 'aura_fear',
                           'casts_curse']
TELLS_AFTER_LIGHT_SHY = ['aura_heat', 'aura_cold', 'aura_stench', 'second_shape', 'casts_ward',
                         'casts_dispel', 'casts_darkness', 'casts_escape', 'carries_fire',
                         'carries_potion', 'territorial', 'bargains', 'skittish']
TELLS_NEW: dict = {
    'hold_constrict': {
        'sign': "{The} moves in long, slow loops and is never quite still.",
        'does': "{He} wraps round you and squeezes every turn, and while {he} has you, you cannot walk away.",
        'counter': "One hard blow on {him} breaks the coils, or struggle free. The Galdr of Loosing keeps any coil off you.",
    },
    'hold_swallow': {
        'sign': "{The} is wide enough to take a man whole.",
        'does': "{He} takes you inside {him}, and {his} gut eats at you every turn, though nothing else can reach you there.",
        'counter': "Cut your way out: one hard blow from inside frees you. The Galdr of Loosing keeps {him} from taking you.",
    },
    'hold_drag': {
        'sign': "{The} keeps glancing toward the water.",
        'does': "{He} seizes you and drags you toward the water, and at its edge pulls you under.",
        'counter': "Strike {him} hard to tear free, and keep away from the water's edge. The Galdr of Loosing keeps {his} grip off you.",
    },
    'aura_fear': {
        'sign': "The air goes cold and still wherever {the} turns.",
        'does': "Dread rolls off {him}: the first time you see {him} close, your will must hold or you flee.",
        'counter': "A strong will or a ward against fear keeps you steady, and once you have stood it, {he} cannot frighten you again this fight.",
    },
    'casts_curse': {
        'sign': "{The} mutters under {his} breath and will not meet your eye.",
        'does': "{He} draws a curse up for a turn, then lays it on you: a binding, a dread, a darkness of the eyes.",
        'counter': "Strike {him} while {he} chants and the curse breaks; wax in your ears stops a spoken one, and a mirror an evil eye.",
    },
    'aura_heat': {
        'sign': "The air shimmers with heat round {the}.",
        'does': "Standing beside {him} scorches you every turn.",
        'counter': "A fire ward or a draught against fire turns the heat or halves it; a sling, a bow or a wand keeps you out of it.",
    },
    'aura_cold': {
        'sign': "Frost creeps over the stones where {the} stands.",
        'does': "Standing beside {him} numbs you with cold every turn.",
        'counter': "A draught against cold halves it and a cold shield turns it; a sling, a bow or a wand keeps you out of it.",
    },
    'aura_stench': {
        'sign': "A heavy reek hangs in the air round {the}.",
        'does': "Standing in {his} reek can turn your stomach, until you get used to it.",
        'counter': "Stand it once and it no longer touches you this fight; or fight {him} from beyond {his} reek.",
    },
    'second_shape': {
        'sign': "Something animal moves behind {the}'s eyes.",
        'does': "Badly hurt, {he} changes shape into a beast, with new and harder blows.",
        'counter': "Finish {him} before half {his} health is gone, and bring what the beast fears.",
    },
    'casts_ward': {
        'sign': "Old charms and fetishes hang about {the}.",
        'does': "Hurt, {he} chants a ward up about {himself}, and your blows land weak until it fades.",
        'counter': "Strike {him} while {he} chants and the ward never rises; a spell, a wand or a thrown flask goes through it.",
    },
    'casts_dispel': {
        'sign': "{The}'s fingers trace signs that unravel in the air.",
        'does': "{He} can tear one of your spells off you: a haste, a shield, a ward of fire.",
        'counter': "Silence {him} first, or cast your strongest spell when {he} is spent.",
    },
    'casts_darkness': {
        'sign': "Shadows gather in {the}'s cupped hands.",
        'does': "{He} puts out the light you carry and ends your Light spell.",
        'counter': "Carry a light that never goes out, or a spare torch; silence {him} and the dark stays away.",
    },
    'casts_escape': {
        'sign': "{The} never stands with {his} back to a wall.",
        'does': "Hurt and caught beside you, {he} steps into nothing and is four paces off.",
        'counter': "Hold {him} still before you close in, or reach {him} with a sling, a bow or a wand.",
    },
    'carries_fire': {
        'sign': "{The} carries a clay pot stopped with a rag.",
        'does': "From a few paces off {he} throws it: oil that bursts into flame on you.",
        'counter': "Close in before {he} throws, or keep stone between you; a fire ward halves the flames.",
    },
    'carries_potion': {
        'sign': "A stoppered flask hangs at {the}'s belt.",
        'does': "Badly hurt, {he} drinks it and {his} wounds close.",
        'counter': "Strike hard before {he} can drink, and the potion is yours when {he} falls.",
    },
    'territorial': {
        'sign': "{The} keeps close to one place, as if guarding it.",
        'does': "{He} will not follow you far from {his} ground, and on it {he} never runs.",
        'counter': "Hurt, leave {his} ground and {he} lets you go; rest, and come back.",
    },
    'bargains': {
        'sign': "{The} jingles a heavy purse and grins.",
        'does': "{He} keeps out of reach and darts in when you turn your back; caught, {he} offers {his} gold for {his} freedom.",
        'counter': "Back {him} into a corner: take the purse, or refuse and fight for all {he} carries.",
    },
    'skittish': {
        'sign': "{The} flits about at the edge of sight.",
        'does': "{He} keeps a few paces off and darts in when you turn your back.",
        'counter': "Back {him} into a corner, or reach {him} with a sling, a bow or a wand.",
    },
}


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

def _dump(d) -> str:
    return (json.dumps(d, indent=2, ensure_ascii=False) + '\n').replace('\n', '\r\n')


def apply_monsters(d: dict) -> list:
    changes = []
    for kind, fields in kind_fields().items():
        m = d.get(kind)
        if not isinstance(m, dict):
            raise SystemExit(f"no kind {kind!r} in monsters.json")
        if m.get('is_boss') or m.get('is_mini_boss') or m.get('is_seal_demon'):
            raise SystemExit(f"{kind} is a named foe: this pass leaves them alone")
        for k, v in fields.items():
            if m.get(k) != v:
                m[k] = v
                changes.append(f"{kind}: {k}")
    for (kind, aname), fields in HOLDS.items():
        m = d.get(kind)
        if not isinstance(m, dict):
            raise SystemExit(f"no kind {kind!r} in monsters.json")
        atk = next((a for a in m.get('attacks') or () if a.get('name') == aname), None)
        if atk is None:
            raise SystemExit(f"{kind} has no attack {aname!r}")
        for k, v in fields.items():
            if v is None:
                if k in atk:
                    del atk[k]
                    changes.append(f"{kind}/{aname}: -{k}")
            elif atk.get(k) != v:
                atk[k] = v
                changes.append(f"{kind}/{aname}: {k}")
    return changes


def apply_rules(d: dict) -> list:
    changes = []
    doc = d.get('_doc', '')
    tail = (" The third wave (AI-3, 2026-11-20): casters, holds, auras, home_ground, kit,"
            " skittish and surprise; the per-kind fields spells, aura, territorial, lair_radius,"
            " lair_line, kit, bargain and, on an attack, hold ('Monster behaviour, third wave').")
    if tail not in doc:
        d['_doc'] = doc + tail
        changes.append('_doc')
    for k, v in RULES.items():
        if d.get(k) != v:
            d[k] = v
            changes.append(f"rules {k}")
    return changes


def _entry_text(key: str, e: dict) -> str:
    body = ',\r\n'.join(f'      {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}'
                        for k, v in e.items())
    return f'    {json.dumps(key)}: {{\r\n{body}\r\n    }}'


def _insert_order(raw: str, after: str, keys: list, d: dict) -> tuple:
    new = [k for k in keys if k not in d['order']]
    if not new:
        return raw, []
    old = f'"{after}", '
    if raw.count(old) != 1:
        raise SystemExit(f"tells order: {old!r} found {raw.count(old)} times")
    raw = raw.replace(old, old + ''.join(f'"{k}", ' for k in new), 1)
    return raw, [f"order {k}" for k in new]


def apply_tells(raw: str) -> tuple:
    d = json.loads(raw)
    changes = []
    raw, ch = _insert_order(raw, 'immobilized', TELLS_AFTER_IMMOBILIZED, d)
    changes += ch
    raw, ch = _insert_order(raw, 'light_shy', TELLS_AFTER_LIGHT_SHY, d)
    changes += ch
    d = json.loads(raw)
    # The new entries go together, after the light_shy entry.
    missing = [k for k in TELLS_AFTER_IMMOBILIZED + TELLS_AFTER_LIGHT_SHY if k not in d['effects']]
    if missing:
        start = raw.index('    "light_shy": {')
        end = raw.index('\r\n    },', start) + len('\r\n    },')
        block = ''.join(_entry_text(k, TELLS_NEW[k]) + ',\r\n' for k in missing)
        raw = raw[:end] + '\r\n' + block.rstrip('\r\n').rstrip(',') + ',' + raw[end:]
        changes += [f"tell {k}" for k in missing]
    d = json.loads(raw)
    for k, e in TELLS_NEW.items():
        for part, text in e.items():
            cur = d['effects'][k].get(part)
            if cur == text:
                continue
            old = f'"{part}": {json.dumps(cur, ensure_ascii=False)}'
            seg_start = raw.index(f'    "{k}": {{')
            seg_end = raw.index('    }', seg_start)
            seg = raw[seg_start:seg_end]
            if seg.count(old) != 1:
                raise SystemExit(f"tell {k}.{part}: old text not found once")
            seg = seg.replace(old, f'"{part}": {json.dumps(text, ensure_ascii=False)}')
            raw = raw[:seg_start] + seg + raw[seg_end:]
            changes.append(f"tell {k}.{part}")
    d = json.loads(raw)
    for k, e in TELLS_NEW.items():
        if d['effects'].get(k) != e:
            raise SystemExit(f"tell {k} differs from the tool's text")
    return raw, changes


# Hints first written wrong (the AI-3 audit, 2026-11-20): there is no
# salamander kind and a frost giant's cold is felt only beside him; the
# brigand carries no kit.
HINTS_REPLACED = {
    "A brigand carries something for a bad day. Make his a short one, and whatever he saved is yours.":
        "A bandit captain carries something for a bad day. Make his a short one, and whatever he saved is yours.",
    "The salamander's heat and the frost giant's cold reach a pace beyond their hands.":
        "Stand beside a fire elemental or a frost giant and you burn or freeze, though neither has struck you.",
}


def apply_hints(d: dict) -> list:
    changes = []
    for tier, lines in d.items():
        for i, h in enumerate(lines):
            if h in HINTS_REPLACED:
                lines[i] = HINTS_REPLACED[h]
                changes.append(f"hint {tier} rewritten: {h[:30]}")
    for tier, lines in HINTS_NEW.items():
        for h in lines:
            if h not in d[tier]:
                d[tier].append(h)
                changes.append(f"hint {tier}: {h[:30]}")
    return changes


def main(argv) -> int:
    write = '--write' in argv
    raw_h = HINTS.read_bytes().decode('utf-8')
    dh = json.loads(raw_h)
    ch_h = apply_hints(dh)
    raw_m = MONSTERS.read_text(encoding='utf-8')
    dm = json.loads(raw_m)
    ch_m = apply_monsters(dm)
    raw_r = AI_RULES.read_bytes().decode('utf-8')
    dr = json.loads(raw_r)
    ch_r = apply_rules(dr)
    raw_t = TELLS.read_bytes().decode('utf-8')
    new_t, ch_t = apply_tells(raw_t)
    for c in ch_m + ch_r + ch_t + ch_h:
        print(c)
    print(f"{len(ch_m)} monster changes, {len(ch_r)} rule changes, {len(ch_t)} tell changes")
    if write:
        if ch_m:
            with open(MONSTERS, 'w', encoding='utf-8', newline='') as f:
                f.write(_dump(dm))
        if ch_r:
            with open(AI_RULES, 'w', encoding='utf-8', newline='') as f:
                f.write(_dump(dr))
        if ch_t:
            with open(TELLS, 'w', encoding='utf-8', newline='') as f:
                f.write(new_t)
        if ch_h:
            with open(HINTS, 'w', encoding='utf-8', newline='') as f:
                f.write(_dump(dh))
        print("written")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
