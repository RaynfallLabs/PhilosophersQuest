"""
One plain sentence on the card of every named armor piece and shield whose
rule cannot be read off its numbers, plus the small data corrections from
the 2026-10-08 item-by-item verification.

Offline tooling (not loaded at runtime). Idempotent.

    python tools/content/unique_armor_specials_2026_10.py --write

Each sentence states what the verification measured the piece doing in play,
not what its lore hopes. Pieces whose whole effect is already printed by the
card (resistances, Dodge, Toughness, Combat Clock, chain length, reflection)
get no sentence.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ARMOR_SPECIAL = {
    'hide_of_nemean_lion': "Halves every cut, stab and blow, on top of its resistances.",
    'carapace_of_the_hydra': "A monster that poisons you has a 40% chance of being poisoned itself.",
    'panoply_of_hephaestus': "While it is worn, your weapon can be enchanted one step higher.",
    'breastplate_of_joan': "Once a floor, a blow that would kill you leaves you at 1 health. Blessed while worn.",
    'lorica_hamata_of_caesar': "The first monster to wound you is marked: you deal half again as much damage to it.",
    'orichalcum_breastplate': "Now and then it hums, and for that moment you are Shielded.",
    'helm_of_achilles': "Each monster that first sees you has a 40% chance of fleeing in fear.",
    'great_helm_of_galahad': "Lifts the curse from everything you wear, and from anything you put on later.",
    'vambraces_of_achilles': "Standing on an altar restores 2 mana and 2 stamina a turn.",
    'gauntlets_of_mars': "Armor improves by 1 while you stand beside a door.",
    'greaves_of_hermes': "Hasted while worn.",
    'leggings_of_enkidu': "Your pet takes a fifth less damage.",
    'mantle_of_elijah': "+3 maximum mana while worn.",
    'boots_of_seven_leagues': "Hasted while worn. Once a floor, a power dashes you up to 7 tiles.",
    'brigandine_of_william_wallace': "Armor improves by 2 in a corridor or with your back in a corner.",
    'cuirass_of_hannibal': "With three or more enemies beside you, armor improves by 2 and your blows land harder.",
    'hermes_sandals_early': "The first arrow, bolt or hex aimed at you on each floor misses.",
    'blindfold': "Blinded while worn, but you feel every monster within 3 tiles, and no gaze can catch you.",
    'trainers_cap': "Your pet heals faster and gains a level on each new floor you reach.",
    'cloth_of_penelope': "You regenerate while it is worn, and faster when badly hurt.",
    'bracers_of_cu_chulainn': "Every third blow you land opens a bleeding wound.",
    'cloak_of_sun_wukong': "Blows sometimes land where you are not, and every tenth that would hit misses outright.",
    'coat_of_cu_chulainn': "Below a quarter health the frenzy takes you: +3 Strength for 10 turns, at 1 health a turn.",
    'babr_e_bayan': "Soaks up the first blow that lands on each floor.",
    'tarnhelm': "Once a floor, falling below 30% health turns you invisible for 5 turns.",
    'linothorax_of_alexander': "Standing on an altar heals 2 health a turn.",
    'coif_of_beowulf': "Nothing holds you: paralysis, sleep, stuns, ice and strangling grips break at once.",
    'kilt_of_the_pharaoh': "If you die wearing it, one thing you wore is kept whole in your grave for whoever finds it.",
    'scale_of_dilmun': "Beside water or a fountain, armor improves by 2 and you heal 1 health a turn.",
    'helm_of_gilgamesh': "Once a floor, a power pays a thinking creature in sight to stand aside.",
    'sandals_of_theseus': "When a monster hits you, 1 time in 5 an ailment you are suffering passes to it.",
    'bracers_of_arjuna': "Your first shot on each floor hits half again as hard.",
    'girdle_of_hippolyta': "After four steps in a straight line, your next blow hits half again as hard.",
    'helm_of_leonidas': "When you are badly hurt, your blows land 15% harder.",
    'cloak_of_mulan': "Once a floor, stepping onto an altar restores you completely.",
    'haramaki_of_yoshitsune': "Hasted for 5 turns each time you go down a stair. Blessed while worn.",
    'boots_of_thor': "Each turn, 1 chance in 20 that lightning takes a twentieth of the health of a monster beside you.",
    'duck_of_doom': "It will not come off. Be patient with it.",
}
SHIELD_SPECIAL = {
    'svalinn': "No fire can hurt you behind it.",
    'aegis_of_athena': "A gaze meant for you freezes the one who looked.",
}

# field corrections: (file, id, field, value); value None removes the field
FIXES = [
    # tier and quiz tier disagreed
    ('armor', 'cloak_of_sun_wukong', 'quiz_tier', 2),
    ('armor', 'winged_sandals_of_hermes', 'quiz_tier', 3),
    # only its monster carries it: the old weight table made it random loot too
    ('armor', 'hide_of_nemean_lion', 'floorSpawnWeight', {}),
    # fields nothing reads
    ('armor', 'cow_kings_horns', 'bovine_fury', None),
    ('armor', 'tarnhelm', 'invisibility_cooldown', None),
    ('armor', 'greaves_of_qin', 'resistances', None),
]
LORE = [
    ('armor', 'bracers_of_cu_chulainn',
     'These bracers kept a little of that. The wearer hits harder and minds his own cuts less.',
     'These bracers kept a little of that. Every third blow the wearer lands tears a wound that will not close.'),
]


def main(argv):
    write = '--write' in argv
    data = {}
    for cat in ('armor', 'shield'):
        p = ROOT / 'data' / 'items' / f'{cat}.json'
        raw = open(p, encoding='utf-8', newline='').read()
        data[cat] = (p, raw, json.loads(raw))
    n = 0
    for cat, table in (('armor', ARMOR_SPECIAL), ('shield', SHIELD_SPECIAL)):
        d = data[cat][2]
        for iid, text in table.items():
            assert iid in d and d[iid].get('is_unique'), iid
            if d[iid].get('special') != text:
                d[iid]['special'] = text
                n += 1
    for cat, iid, field, value in FIXES:
        e = data[cat][2][iid]
        if value is None:
            if field in e:
                del e[field]
                n += 1
        elif e.get(field) != value:
            e[field] = value
            n += 1
    for cat, iid, old, new in LORE:
        e = data[cat][2][iid]
        if old in e['lore']:
            e['lore'] = e['lore'].replace(old, new)
            n += 1
    print(f'{n} changes')
    if write:
        for p, raw, d in data.values():
            out = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
            open(p, 'w', encoding='utf-8', newline='').write(out.replace('\n', '\r\n') if '\r\n' in raw else out)
        print('written')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
