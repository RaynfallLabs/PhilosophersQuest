"""The counter items the MONSTERS AND MAGIC kinds' lore names (slice M,
2026-11-19): what the old stories used against them.

Offline tooling (not loaded at runtime). Idempotent.

    py tools/content/add_mm_counters_2026_11.py            # report
    py tools/content/add_mm_counters_2026_11.py --write    # write the data

  seed_handful      A Handful of Seed (thrown; tier 2): a vampire must stop and
                    count every grain (Balkan and Slavic grave custom; Paul
                    Barber, Vampires, Burial and Death, 1988): held 3 turns,
                    once for each creature. data/items/flask.json 'throw'
                    'counting' (coatings.throw_at).
  upas_latex        Upas Latex (coating; tier 3): the milky sap of the upas
                    tree, the ipoh poison of the island blowguns.
  eitr_venom        A Vial of Eitr (coating; tier 5): the first poison of the
                    Norse world, crawling and freezing (Gylfaginning 5).
  whitethorn_branch A Sprig of Whitethorn (carried; tier 2): Cranae's branch at
                    the window kept the striges from the cradle (Ovid, Fasti
                    6.131-168): a strix will not strike the one who carries it.
  caged_cockerel    A Caged Cockerel (applied; tier 1): the crow of a rooster
                    kills the cockatrice and drives back the basilisk (the
                    bestiaries; Pliny 8.79) and the hopping dead (Chinese folk
                    practice): once a floor.

The poison ladder of coatings is viper venom (tier 1), upas latex (3), the
Hydra's blood (4) and eitr (5). Each is sold where the shelves sell flasks
and found as loot by its floorSpawnWeight; the seed, the whitethorn and the
cockerel are on the apothecary's shelf now and then.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D = ROOT / 'data'

VAMPIRES = ['vampire', 'vampire_spawn', 'strigoi', 'vrykolakas', 'nosferatu']

FLASKS = {
    'seed_handful': {
        'name': 'Handful of Seed', 'symbol': '!', 'color': [205, 180, 110], 'weight': 0.2,
        'min_level': 20, 'tier': 2, 'can_be_cursed': False,
        'throw': {'damage_type': 'blunt', 'damage': 0, 'sized_at': 25,
                  'counting': {'kinds': VAMPIRES, 'turns': 3}},
        'floorSpawnWeight': {'21-40': 5, '41-60': 2},
        'lore': ("A cloth twist of millet and poppy seed. In the Balkans and across the Slavic lands "
                 "mourners scattered seed on a new grave and along the road home, for a vampire that "
                 "rises must stop and count every grain before it can go on, and dawn comes first. "
                 "Thrown at one of the blood-drinking dead, it holds the creature a few turns while it "
                 "counts. Each creature counts it once; after that it knows the trick."),
    },
    'upas_latex': {
        'name': 'Upas Latex', 'symbol': '!', 'color': [235, 230, 205], 'weight': 0.2,
        'min_level': 44, 'tier': 3,
        'coat': {'substance': 'poison', 'blows': 12, 'rider': {'effect': 'poisoned', 'chance': 1.0, 'turns': 5}},
        'floorSpawnWeight': {'41-60': 6, '61-80': 3, '81-100': 1},
        'lore': ("A stoppered gourd of the milky sap of the upas tree of Java, the ipoh poison that "
                 "island hunters smeared on their blowgun darts. The London Magazine once claimed the "
                 "tree killed every living thing for fifteen miles; the truth is smaller and still "
                 "deadly. Worked into an edge, it turns each cut into a poisoned one. It does nothing to "
                 "what has no blood."),
    },
    'eitr_venom': {
        'name': 'Vial of Eitr', 'symbol': '!', 'color': [60, 120, 90], 'weight': 0.2,
        'min_level': 80, 'tier': 5,
        'coat': {'substance': 'poison', 'blows': 16, 'rider': {'effect': 'poisoned', 'chance': 1.0, 'turns': 8}},
        'floorSpawnWeight': {'81-100': 4},
        'lore': ("A thick black-green venom in a vial of rime-crusted glass, so cold it smokes. Snorri "
                 "says the eitr flowed out of Niflheim in the poisonous rivers of the beginning and "
                 "hardened like slag; a little never hardened. Painted along a blade it is the worst "
                 "poison there is, and nothing with blood in it shrugs it off for long."),
    },
}

ACCESSORIES = {
    'whitethorn_branch': {
        'name': 'Sprig of Whitethorn', 'symbol': '&', 'color': [230, 235, 225], 'weight': 0.2,
        'min_level': 22, 'slot': 'none', 'equip_threshold': 1, 'quiz_tier': 2, 'effects': {},
        'identified': True, 'id_level': 5, 'can_be_cursed': False, 'counters': ['whitethorn'],
        'unidentified_name': 'a sprig of white blossom on a thorny twig',
        'lore': ("A sprig of hawthorn in white flower, the whitethorn of the hedgerows. Ovid tells how "
                 "the striges came by night to the cradle of the child Proca, and the nymph Cranae "
                 "touched the doorposts three times with arbutus and set a branch of whitethorn at the "
                 "window, and they never came again. Carried, no strix will come at you."),
        'floorSpawnWeight': {'21-40': 2, '41-60': 1},
        'is_unique': False,
    },
    'caged_cockerel': {
        'name': 'Caged Cockerel', 'symbol': '&', 'color': [200, 80, 50], 'weight': 4.0,
        'min_level': 4, 'slot': 'none', 'equip_threshold': 1, 'quiz_tier': 1, 'effects': {},
        'identified': True, 'id_level': 5, 'can_be_cursed': False, 'counters': ['cock_crow'],
        'unidentified_name': 'a red cockerel in a wicker cage',
        'lore': ("A red cockerel in a little wicker cage, ill-tempered and loud. The bestiaries say the "
                 "crow of a cock is death to the cockatrice and the basilisk, as the weasel is, and in "
                 "China a rooster's crow sends the hopping dead back to their coffins at dawn. Let it "
                 "crow (Apply) and every cockatrice or lesser basilisk in earshot is struck down, and a "
                 "basilisk or a jiangshi reels. It crows once a floor; after that it sulks."),
        'floorSpawnWeight': {'1-20': 2, '21-40': 1},
        'is_unique': False,
    },
}

TECHNIQUES = {
    'whitethorn': {
        'name': 'whitethorn', 'carried': True, 'kinds': ['strix'],
        'line': "{The} shies from the whitethorn you carry and will not strike you.",
        'card': "Carried, no strix will strike you: the whitethorn at the window kept them from the cradle.",
    },
    'cock_crow': {
        'name': "a cock's crow", 'apply': 'crow',
        'kills': ['cockatrice', 'basilisk_lesser'], 'drives': ['basilisk', 'jiangshi'],
        'share': 0.5, 'flee_turns': 5, 'stun_turns': 2, 'reach': 8,
        'crow': "The cockerel throws back its head and crows!",
        'kill_line': "{The} shrieks at the crow and reels away, smoking!",
        'drive_line': "{The} staggers at the crow, stunned.",
        'nothing': "Nothing here fears a cock's crow.",
        'tired': "The cockerel is hoarse; it will crow again on the next floor.",
        'card': "Apply to let it crow, once a floor: it strikes down a cockatrice or a lesser basilisk and stuns a basilisk or a jiangshi nearby.",
    },
}

WORTH = {'whitethorn_branch': 0.25, 'caged_cockerel': 0.2}
APOTHECARY_STOCK = [
    {'id': 'whitethorn_branch', 'cat': 'accessory', 'chance': 0.2},
    {'id': 'caged_cockerel', 'cat': 'accessory', 'chance': 0.2},
]
POISON_OFFER_OLD = '"poison": {"probe": {"element": "poison"}, "take": "venom", "offers": [{"class": "flask", "ids": ["viper_venom", "hydras_blood"]}]},'
POISON_OFFER_NEW = '"poison": {"probe": {"element": "poison"}, "take": "venom", "offers": [{"class": "flask", "ids": ["viper_venom", "upas_latex", "hydras_blood", "eitr_venom"]}]},'


def _flask_text(fid: str, d: dict) -> str:
    """One flask entry in flask.json's own layout (small dicts on one line)."""
    lines = [f'  {json.dumps(fid)}: {{']
    items = list(d.items())
    for i, (k, v) in enumerate(items):
        val = json.dumps(v, ensure_ascii=False)
        comma = ',' if i < len(items) - 1 else ''
        lines.append(f'    {json.dumps(k)}: {val}{comma}')
    lines.append('  }')
    return '\n'.join(lines)


def main(argv) -> int:
    write = '--write' in argv
    changed = []

    fpath = D / 'items' / 'flask.json'
    ftext = fpath.read_text(encoding='utf-8')
    fdata = json.loads(ftext)
    add = [fid for fid in FLASKS if fid not in fdata]
    if add:
        body = ftext.rstrip()
        assert body.endswith('}\n}') or body.endswith('}\n}'.replace('\n', '\r\n')), 'flask.json layout'
        cut = body.rfind('\n}')
        body = body[:cut] + ''.join(',\n' + _flask_text(fid, FLASKS[fid]) for fid in add) + body[cut:]
        ftext = body + '\n'
        json.loads(ftext)
        changed += [f'flask {f}' for f in add]

    apath = D / 'items' / 'accessory.json'
    acc = json.loads(apath.read_text(encoding='utf-8'))
    for aid, d in ACCESSORIES.items():
        if acc.get(aid) != d:
            acc[aid] = d
            changed.append(f'accessory {aid}')

    arpath = D / 'arsenal.json'
    artext = arpath.read_text(encoding='utf-8')
    ar = json.loads(artext)
    for t, spec in TECHNIQUES.items():
        was = ar['counters']['techniques'].get(t)
        if was is not None and was != spec:
            line = json.dumps(was, ensure_ascii=False)
            assert artext.count(line) == 1, ('arsenal.json', t)
            artext = artext.replace(line, json.dumps(spec, ensure_ascii=False))
            json.loads(artext)
            changed.append(f'technique {t} words')
    new_t = [t for t in TECHNIQUES if t not in ar['counters']['techniques']]
    if new_t:
        anchor = '\n    },\n    "stop_ears": {'
        assert artext.count(anchor) == 1, 'arsenal.json layout'
        ins = ''.join(f',\n      {json.dumps(t)}: {json.dumps(TECHNIQUES[t], ensure_ascii=False)}' for t in new_t)
        artext = artext.replace(anchor, ins + anchor)
        json.loads(artext)
        changed += [f'technique {t}' for t in new_t]

    wpath = D / 'item_worth.json'
    worth = json.loads(wpath.read_text(encoding='utf-8'))
    for k, v in WORTH.items():
        if worth['share_by_id'].get(k) != v:
            worth['share_by_id'][k] = v
            changed.append(f'worth {k}')

    tpath = D / 'traders.json'
    ttext = tpath.read_text(encoding='utf-8')
    if POISON_OFFER_OLD in ttext:
        ttext = ttext.replace(POISON_OFFER_OLD, POISON_OFFER_NEW)
        changed.append('stall poison offers')
    old_stock = '        {"id": "beeswax_earplugs", "cat": "accessory", "chance": 0.4}\n      ],'
    if '"whitethorn_branch"' not in ttext:
        assert ttext.count(old_stock) == 1, 'traders.json layout'
        extra = ''.join(',\n        ' + json.dumps(s) for s in APOTHECARY_STOCK)
        ttext = ttext.replace(old_stock, old_stock[:-len('\n      ],')] + extra + '\n      ],')
        changed.append('apothecary stock')
    json.loads(ttext)

    print('changes:', ', '.join(changed) if changed else 'none')
    if write and changed:
        fpath.write_text(ftext, encoding='utf-8')
        apath.write_text(json.dumps(acc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        arpath.write_text(artext, encoding='utf-8')
        wpath.write_text(json.dumps(worth, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
        tpath.write_text(ttext, encoding='utf-8')
        print('written')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
