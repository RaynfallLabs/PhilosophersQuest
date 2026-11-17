"""The mini-bosses' signature drops, depth-appropriate (Brandon's ruling 13,
2026-11-16: "mini-bosses with cool unique drops ... gear they drop should be
depth appropriate").

Offline content pass over data/items/*.json, the record of what was done.
Idempotent. Run after tools/balance/mini_boss_seats.py, then the ladder
passes that derive the rest:

    py tools/content/mini_boss_drops_2026_11_17.py --write
    py tools/content/unique_armor_ladder_2026_11.py          # AC, plus, levels
    py tools/content/known_by_hand_thresholds_2026_11.py     # thresholds
    py tools/content/ring_kinds_2026_11.py                   # named rings / amulets

The rule: a mini-boss's drop has the tier of the band it lives in,
tier = (floor - 1) // 20 + 1 (a floor-15 foe drops a tier-1 unique, never a
tier-4 one). Each drop is its own legend's (mini_boss_seats.DROPS) and is
`plot_locked`: it comes only from its foe, so the named-armour ladder keeps
the tier written here instead of raising it a step over the commons, and
traders refuse it. Its peak_floor is its foe's seat (the floor the census and
the armour tests weigh it at). A weapon's base damage is UNIQUE_MULT times the
median of the commons of its class at that floor
(tools/balance/rebase_unique_weapons.py), raised or lowered with the move.

What changed, by band (old tier -> new):
  1  Arachne's Silk Cloak 2 -> 1; the Hide of the Nemean Lion 5 -> 1 (it keeps
     the halving of every blow that is not magic, its whole legend, and loses
     the resistances that stacked on it); NEW the Hide of the Calydonian Boar,
     the Eyes of Lamia.
  2  the Mantle of the Erlking 3 -> 2; the Obsidian Talisman 3 -> 2;
     Echidna's Fang 2 (re-based at floor 37); NEW the Club of Polyphemus.
  3  the Sphinx's Crown 2 -> 3 (Wisdom +3) and Anubis's Scales 2 -> 3
     (Constitution +3), an amulet's +tier; Baba Yaga's Iron Mortar 4 -> 3;
     Vulcan's Brand 3 (re-based at floor 47); NEW the Patriarch's Gavel, the
     Brazen Hands of Stheno, Rangda's Keris.
  4  Serpent Scale Mail, the Green Girdle, the Vambraces of the First Winter,
     Wendigo's Fang, the Hunt Captain's Sword 5 -> 4; the Sailor's Amulet
     2 -> 4; NEW the Crone's Burial Veil.
  5  the Ring of Iron Grip 2 -> 5 (Strength +5); Anansi's Web Cloak 5 (kept);
     NEW the Exsanguinating Blade.

    py tools/content/mini_boss_drops_2026_11_17.py [--write]
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import jsonfmt  # noqa: E402

ITEMS = os.path.join(ROOT, 'data', 'items')

# id: (file, tier, extra fields). The seat (peak_floor) comes from the foe.
RETIER = {
    'arachne_silk_cloak': ('armor', 1, {}),
    'hide_of_nemean_lion': ('armor', 1, {
        'damage_resistances': {},
        'material': 'hide',
        'special': "Halves every cut, stab and blow a creature without magic lands on you.",
        'unidentified_name': 'a rough amber pelt of unnatural density',
    }),
    'erlking_mantle': ('armor', 2, {}),
    'obsidian_talisman': ('accessory', 2, {}),
    'echidna_fang': ('weapon', 2, {}),
    'sphinx_crown': ('accessory', 3, {'effects': {'stat': 'WIS', 'amount': 3}}),
    'anubis_scales': ('accessory', 3, {'effects': {'stat': 'CON', 'amount': 3}}),
    'iron_mortar_wand': ('wand', 3, {}),
    'vulcans_brand': ('weapon', 3, {}),
    'serpent_scale_mail': ('armor', 4, {}),
    'green_girdle': ('armor', 4, {}),
    'vambraces_of_the_first_winter': ('armor', 4, {}),
    'sailors_amulet': ('accessory', 4, {}),
    'wendigo_fang': ('weapon', 4, {}),
    'hunt_captains_sword': ('weapon', 4, {}),
    'anansi_web_cloak': ('armor', 5, {}),
    'ring_of_iron_grip': ('accessory', 5, {'effects': {'stat': 'STR', 'amount': 5}}),
    # Kept at their tier, seated where their foe now lives.
    'bronze_aegis': ('shield', 1, {}),
    'hrungnirs_stone_shield': ('shield', 5, {}),
    'mantle_of_muspelheim': ('armor', 5, {}),
    'nidhoggr_scale': ('armor', 5, {}),
    'ruby_rod': ('wand', 5, {}),
}

_HEAVY = [0.75, 0.9, 1.0, 1.3, 1.75]
_NORMAL = [0.5, 0.85, 1.0, 1.45, 2.0]
_FINESSE = [0.2, 0.55, 1.0, 1.8, 3.0]


def _weapon(name, cls, template, two_handed, chain, chain_kind, types, colour, weight, unid, lore,
            **extra):
    d = {
        'name': name, 'is_unique': True, 'class': cls, 'weapon_class': cls,
        'variant': '2h' if two_handed else '1h', 'twoHanded': two_handed, 'two_handed': two_handed,
        'template_basis': template, 'baseDamage': 1, 'base_damage': 1,
        'chainMultipliers': list(chain), 'chain_multipliers': list(chain),
        'maxChainLength': 5, 'max_chain_length': 5, 'weapon_class_chain': chain_kind,
        'damageTypes': list(types), 'damage_types': list(types),
        'min_level': 9999, 'peak_floor': 0, 'spread': 0, 'peak_weight': 0.0, 'max_enchant': 3,
        'symbol': ')', 'color': list(colour), 'weight': weight, 'material': 'legendary',
        'unidentified_name': unid, 'identified': False, 'id_level': 0, 'can_be_cursed': False,
        'enchant_bonus': 0, 'reach': 1, 'requiresAmmo': None, 'ignoreShield': False,
        'chain_exponent': 1.15, 'floorSpawnWeight': {}, 'plot_locked': True, 'lore': lore,
    }
    d.update(extra)
    return d


# The new drops: (file, tier, data). Sources were checked on Grokipedia first,
# then Wikipedia (and Homer on Perseus for the Cyclops' club).
NEW = {
    'calydonian_boar_hide': ('armor', 1, {
        'name': 'Hide of the Calydonian Boar', 'symbol': '[', 'color': [70, 55, 45],
        'weight': 14.0, 'min_level': 9999, 'slot': 'body', 'material': 'hide',
        'ac_bonus': 3, 'enchant_bonus': 1, 'equip_threshold': 4,
        'damage_resistances': {'slash': 0.8},
        'can_be_cursed': False, 'cursed': False, 'identified': False, 'id_level': 0,
        'unidentified_name': 'a coat of bristled black hide with a tusked hood',
        'floorSpawnWeight': {}, 'value': 900, 'max_enchant': 2, 'spread': 0, 'peak_weight': 0.0,
        'template_basis': 'hide', 'is_unique': True, 'plot_locked': True, 'metal': False,
        'special': "Its bristles stand like spear shafts: a blade's cut glances off it.",
        'lore': ("King Oeneus of Calydon forgot Artemis at the harvest offerings, and she sent a "
                 "boar bigger than a bull, with bristles like spear shafts and tusks like an "
                 "elephant's. Half the heroes of Greece hunted it. Atalanta drew first blood with "
                 "an arrow and Meleager killed it with his spear, then gave her the hide and the "
                 "tusked head as the prize. His uncles took them from her, and he killed them for "
                 "it. Pausanias saw the hide rotting in Athena's temple at Tegea. This is it, before "
                 "the moths."),
    }),
    'eyes_of_lamia': ('accessory', 1, {
        'name': 'The Eyes of Lamia', 'symbol': '"', 'color': [210, 180, 60], 'weight': 0.2,
        'min_level': 0, 'slot': 'amulet', 'equip_threshold': 5, 'quiz_tier': 1,
        'effects': {'status': 'sleep_resist', 'duration': -1},
        'can_be_cursed': False, 'unidentified_name': 'a small glass jar with something floating in it',
        'floorSpawnWeight': {}, 'peak_floor': 0, 'spread': 10, 'peak_weight': 0.0,
        'plot_locked': True, 'is_unique': True, 'identified': False, 'id_level': 0, 'tier': 1,
        'special': "Hera never let her eyes close: whoever wears them cannot be put to sleep or held still.",
        'lore': ("Lamia was a queen of Libya whom Zeus loved, and Hera killed her children for it. "
                 "Grief made her a monster, and Hera made sure she could never close her eyes on "
                 "what she had lost. Zeus, in pity, gave her the power to take her eyes out and set "
                 "them aside so that she could rest. Plutarch says she kept them in a jar at home "
                 "and put them back in when she went out hunting. These are the eyes, in the jar. "
                 "They have not blinked since."),
    }),
    'club_of_polyphemus': ('weapon', 2, _weapon(
        "Club of Polyphemus", 'club', 'maul', True, _HEAVY, 'heavy', ['blunt'], (120, 105, 80), 9.0,
        'a huge log of grey olive wood, cut off square at one end',
        ("Odysseus found it lying beside the sheep-pens in the Cyclops' cave: a staff of green "
         "olive wood that Polyphemus had cut to carry when it dried, as long as the mast of a "
         "black ship of twenty oars. Odysseus cut a fathom off the end, sharpened it, hardened "
         "the point in the fire and drove it into the giant's one eye while he slept off the "
         "wine. The rest of the club is still a club. It is heavy enough that a blow from it "
         "leaves the one it lands on reeling."),
        stun_chance=0.25, stunChance=0.25, knockback=True, value=420, weapon_class='blunt')),
    'patriarchs_gavel': ('weapon', 3, _weapon(
        "The Patriarch's Gavel", 'warhammer', 'warhammer', False, _NORMAL, 'normal', ['blunt'],
        (60, 55, 60), 6.0, 'a black iron hammer with a head like a judge\'s gavel',
        ("The Iron Patriarch outlived every son, grandson and usurper of his line and sat on in "
         "his coronation plate until the kingdom gave out beneath him. He still granted every "
         "visitor a hearing. It was short, and this ended it: a black iron hammer with a head "
         "like a judge's gavel, banded in gold, with a little iron crown for a pommel. Whatever "
         "it lands on is in no state to answer back."),
        stun_chance=0.25, stunChance=0.25, value=760, weapon_class='blunt')),
    'rangdas_keris': ('weapon', 3, _weapon(
        "Rangda's Keris", 'dagger', 'dagger', False, _FINESSE, 'finesse', ['pierce'],
        (110, 110, 120), 1.0, 'a wavy-bladed dagger with a carved demon hilt',
        ("On Bali, Rangda is the widow-witch, queen of the leyaks, who fights the Barong forever "
         "and never quite loses. In the temple dance her spell falls on the Barong's warriors and "
         "they turn their own keris daggers against their chests, and only the Barong's magic "
         "keeps the blades from going in. This is her own keris: a blade that waves like a "
         "snake, with a little demon crouched on the hilt. A wound from it leaves the wounded "
         "unsure which side he is on."),
        confuse_chance=0.2, confuseChance=0.2, value=740)),
    'exsanguinating_blade': ('weapon', 5, _weapon(
        "The Exsanguinating Blade", 'sword', 'longsword', False, _NORMAL, 'normal', ['slash'],
        (130, 30, 35), 3.5, 'a longsword with a blade the colour of dried blood',
        ("The Blood Archon kept his accounts in blood, and this was his pen. He fought the way he "
         "traded: he opened a vein, stood back and waited for the debt to come due. The blade is "
         "the colour of dried blood and the groove down its middle never quite dries. What it "
         "lets out of the one it cuts, it pays back in part to the hand that holds it. The "
         "interest is what it has always been."),
        bleed_chance=0.3, bleedChance=0.3, lifesteal_percent=0.12, lifestealPercent=0.12,
        value=9000)),
    'brazen_hands_of_stheno': ('armor', 3, {
        'name': 'Brazen Hands of Stheno', 'symbol': '[', 'color': [180, 130, 70], 'weight': 2.5,
        'min_level': 9999, 'slot': 'hands', 'material': 'bronze', 'ac_bonus': 0, 'enchant_bonus': 0,
        'equip_threshold': 6, 'damage_resistances': {}, 'can_be_cursed': False, 'cursed': False,
        'identified': False, 'id_level': 0, 'unidentified_name': 'a pair of clawed gauntlets of scaled bronze',
        'floorSpawnWeight': {}, 'value': 3200, 'max_enchant': 2, 'spread': 0, 'peak_weight': 0.0,
        'template_basis': 'plate_gauntlets', 'is_unique': True, 'plot_locked': True, 'ench_id': 'ogre_power',
        'special': "A gorgon's grip of bronze: they add to your Strength while you wear them.",
        'lore': ("Apollodorus describes the three Gorgons: heads twined with the scales of serpents, "
                 "tusks like a boar's, wings of gold, and hands of bronze. Medusa was the only "
                 "mortal one. Her sisters Stheno and Euryale cannot die, and Stheno's name means "
                 "strength. These are her hands, or what she left in them when she went down: "
                 "scaled bronze, clawed at every finger. Whoever wears them has a gorgon's grip."),
    }),
    'crones_burial_veil': ('armor', 4, {
        'name': "The Crone's Burial Veil", 'symbol': '[', 'color': [200, 195, 175], 'weight': 0.3,
        'min_level': 9999, 'slot': 'head', 'material': 'cloth', 'ac_bonus': 0, 'enchant_bonus': 0,
        'equip_threshold': 6, 'damage_resistances': {}, 'can_be_cursed': False, 'cursed': False,
        'identified': False, 'id_level': 0, 'unidentified_name': 'a hooded veil of old grey linen',
        'floorSpawnWeight': {}, 'value': 5200, 'max_enchant': 2, 'spread': 0, 'peak_weight': 0.0,
        'template_basis': 'leather_cap', 'is_unique': True, 'plot_locked': True, 'ench_id': 'iron_will',
        'special': "She heard her own death foretold every night in the grave: no gaze and no terror takes hold of whoever wears it.",
        'lore': ("The market town buried the fortune-teller alive in this veil for telling fortunes "
                 "too plainly: which child would not see spring, which husband would not come home. "
                 "In the dark she went on whispering, and in time the dead whispered back. Every one "
                 "of them heard his own death foretold in her voice, the day and the hour. She heard "
                 "her own every night for years and stopped being afraid of anything. The veil "
                 "remembers how."),
    }),
}

# The named minor pieces' enchantment, chosen by lore (unique_armor_ladder PICKS).
PICKS = {
    'brazen_hands_of_stheno': ('ogre_power', "Stheno's name means strength, the mighty one of the three, and Apollodorus gives the Gorgons hands of bronze: the gorgon's grip is Ogre Power (Strength)."),
    'crones_burial_veil': ('iron_will', 'She heard her own death foretold in the grave every night until nothing could frighten her; Iron Will turns aside the gaze and shrugs off fear, the thing her whisper did to every listener.'),
}


def seats() -> dict:
    """{item id: the floor of the foe that drops it}."""
    import mini_boss_seats as ms
    return {drop: ms.SEATS[mid][0] for mid, (drop, _why) in ms.DROPS.items()
            if drop and mid in ms.SEATS and not drop.startswith('armor:')}


def _weapon_base(wid: str, d: dict, floor: int) -> int:
    import rebase_unique_weapons as rb
    return int(round(rb.UNIQUE_MULT * rb.class_median(floor, d.get('weapon_class', d['class']))))


def apply(files: dict) -> list:
    log = []
    where = seats()
    for iid, (fname, tier, data) in NEW.items():
        if iid not in files[fname]:
            files[fname][iid] = dict(data)
            log.append(f"{iid}: new ({fname})")
        elif fname == 'weapon' and files[fname][iid].get('weapon_class') != data.get('weapon_class'):
            files[fname][iid]['weapon_class'] = data['weapon_class']
            log.append(f"{iid}: weapon_class -> {data['weapon_class']}")
    rows = {iid: (f, t, x) for iid, (f, t, x) in RETIER.items()}
    rows.update({iid: (f, t, {}) for iid, (f, t, _d) in NEW.items()})
    for iid, (fname, tier, extra) in rows.items():
        d = files[fname][iid]
        want = dict(extra)
        want.update(tier=tier, quiz_tier=tier, peak_floor=where[iid], plot_locked=True)
        # A floor written for the piece's old depth, deeper than its foe now
        # lives, says nothing true: it is a drop only (never rolled).
        if int(d.get('min_level', 0) or 0) > where[iid]:
            want['min_level'] = 9999
        if fname == 'weapon':
            want['mathTier'] = tier
            base = _weapon_base(iid, {**d, **want}, where[iid])
            want['baseDamage'] = want['base_damage'] = base
        for k, v in want.items():
            if d.get(k) != v:
                log.append(f"{iid}: {k} {d.get(k)!r} -> {v!r}")
                d[k] = v
        if fname == 'armor' and iid == 'hide_of_nemean_lion':
            for k in ('damage_resistances',):
                d[k] = want[k]
    return log


def main(argv) -> int:
    paths = {f: os.path.join(ITEMS, f + '.json') for f in ('armor', 'shield', 'accessory', 'weapon', 'wand')}
    loaded = {f: jsonfmt.load(p) for f, p in paths.items()}
    files = {f: v[0] for f, v in loaded.items()}
    log = apply(files)
    for line in log:
        print('  ' + line)
    if '--write' in argv:
        for f, p in paths.items():
            jsonfmt.save(p, files[f], loaded[f][1])
        print('wrote', ', '.join(paths))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
