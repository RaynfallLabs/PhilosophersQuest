"""The MONSTERS AND MAGIC kinds of 2026-11-19 (slice M): thirty-two new kinds
from real lore and the upgrades the plan kept, written into every data file
they touch. The data itself is in tools/content/mm_kinds_data.py and
tools/content/mm_kitchen_data.py (the research: _mm_2026_11_19/A/).

Offline tooling (not loaded at runtime). Idempotent: a second run changes
nothing.

    py tools/content/add_mm_kinds_2026_11.py            # report
    py tools/content/add_mm_kinds_2026_11.py --write    # write the data

What it writes:
  data/monsters.json            the new kinds (at the end) and the upgrades;
                                each kind's five affinity lists come from the
                                affinity pass (tools/content/affinity_pass.py)
  data/family_affinity.json     the new kinds' own affinity entries
  data/monster_sizes.json, data/senses.json (two new senses: breath, blood scent)
  data/items/harvest_map.json, ingredient.json, recipes.json
  tools/content/kitchen/part_freq.json, dish_art.json (records)
  assets/tiles/items/<part>.png  each new part's picture (a reviewed part picture
                                of the same kind), listed in installed_items.json
  data/packs.json               the new kinds that come in groups (herds)
  data/tells.json               the new powers' tells
  data/hints.json               Recall Lore hints

Then run `py tools/balance/gold_by_lore.py --write` for the purse.
LORE, NOT FLOOR: every number is the creature's own.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import affinity_pass  # noqa: E402
from mm_kinds_data import AFFINITY, HARVEST_SHARE, NEW, PEOPLE, SENSE_RANGES, SENSES, SIZES  # noqa: E402
from mm_kitchen_data import INGREDIENTS, KIN_LINES, RECIPES, RETIRED_KIN_LINES  # noqa: E402

D = ROOT / 'data'
ITEMS = D / 'items'
ART = ROOT / 'assets' / 'tiles' / 'items'


def _load(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def _dump(p: Path, d, indent: int, ascii_: bool) -> None:
    p.write_text(json.dumps(d, indent=indent, ensure_ascii=ascii_) + '\n', encoding='utf-8')


# ---------------------------------------------------------------------------
# Upgrades to existing kinds: only the fields the plan names, by lore.
# ---------------------------------------------------------------------------
def _attack(m, name):
    return next(a for a in m['attacks'] if a.get('name') == name)


def upgrade(mons: dict, changed: list) -> None:
    def put(kid, key, val):
        if mons[kid].get(key) != val:
            mons[kid][key] = val
            changed.append(f'{kid}.{key}')

    def put_atk(kid, aname, **kw):
        a = _attack(mons[kid], aname)
        for k, v in kw.items():
            if a.get(k) != v:
                a[k] = v
                changed.append(f'{kid}.{aname}.{k}')

    # The each-uisce's hide sticks to the rider (its lore): a hold, not a
    # paralysis, and it drags you toward the water.
    put_atk('each_uisce', 'Drown Drag', effect='immobilized', effect_chance=0.4, effect_duration=3)
    put('each_uisce', 'pull_chance', 0.3)
    # Jenny Greenteeth's long arms pull you to her pool.
    put('green_hag', 'pull_chance', 0.25)
    # The mummy's rotting touch: a wound that will not mend for a while.
    put_atk('mummy', 'Rotting Touch', effect='heal_blocked', effect_chance=0.4, effect_duration=10)
    # The ghast's reek (its lore already says soldiers retch): a stench aura
    # (the aura primitive is slice AI-3's; the field waits for it).
    put('ghast', 'aura', {'kind': 'stench', 'radius': 1, 'effect': 'weakened', 'chance': 0.25,
                          'turns': 3, 'save': 'CON',
                          'line': "The reek of the opened grave rolls off the Ghast, and you retch."})
    # The Komodo's venom keeps blood from clotting (its lore): it bleeds you,
    # and it follows the blood (data/senses.json 'blood_scent').
    put_atk('komodo_brute', 'Venomous Bite', effect='bleeding', effect_chance=0.5, effect_duration=8)
    # Nosferatu's rats, as they came off the ship at Wisborg (Murnau, 1922).
    put('nosferatu', 'summon_kind', 'giant_rat')
    put('nosferatu', 'summon_max', 3)
    put('nosferatu', 'summon_cooldown', 12)
    old = "a thing of plague cellars that hunts alone."
    new = "a thing of plague cellars, and the rats come when it calls, as they came off its ship at Wisborg."
    if old in mons['nosferatu']['lore']:
        mons['nosferatu']['lore'] = mons['nosferatu']['lore'].replace(old, new)
        changed.append('nosferatu.lore')
    # The jiangshi's paper talisman (its lore: pressed to its forehead it
    # stops it cold): any scroll read with one in sight holds it.
    put('jiangshi', 'talisman', {'turns': 2,
                                 'line': "You hold up the written page, and the Jiangshi stops dead, "
                                         "as if a talisman had been pressed to its forehead."})
    # The catoblepas must heave its heavy head up before it can look at you
    # (its lore): the gaze is drawn up for a turn, and needs a rest after
    # (attack `recharge`: slice AI-1's breath recharge reads it).
    op = dict(mons['catoblepas'].get('opener') or {})
    want = {'attack': 'Death Gaze', 'range': 3,
            'wind_up': "{name} heaves {his} heavy head up off the ground."}
    if op != want:
        mons['catoblepas']['opener'] = want
        changed.append('catoblepas.opener')
    put_atk('catoblepas', 'Death Gaze', recharge=4)
    # The roc lifts an elephant and drops it on the rocks (Marco Polo).
    put_atk('roc_adult', 'Talon Crush',
            carry_off={'chance': 0.2, 'tiles': [8, 15], 'share': 0.05,
                       'line': "The Roc's talons close on you and it lifts you into the dark!",
                       'landed': "It drops you far away.",
                       'nowhere': "It finds nowhere to set you down, and you fall where you were."})
    # The lindworm sheds a skin for each of the ten shifts (Kong Lindorm):
    # twice in a fight it throws off its wounds; its HP is a tenth less to pay
    # for the skins.
    put('lindworm', 'hp', '29d10+110')
    put('lindworm', 'sheds_skin', {'at': [0.66, 0.33], 'heal_share': 0.08,
                                   'line': "The Lindworm sheds a skin, and its wounds come away with it!"})


# ---------------------------------------------------------------------------
# Text inserts for the files that are not plain json.dumps layouts.
# ---------------------------------------------------------------------------
PACK_HERDS = [
    ("Yoked pairs, herds and nests: the bronze bulls of Colchis come two by two, centaurs ride in a "
     "herd, gold-digging ants keep their heaps together, and each of them fights for itself.",
     ['khalkotauros', 'centaur', 'myrmekes']),
    ("Spirits and sea-folk who gather but fight each alone: the bell-ringing biloko, the Blue Men "
     "of the Minch, the Ponaturi ashore at night, the dog-headed psoglavci, and the relic "
     "guardians set in pairs.",
     ['eloko', 'blue_men_of_the_minch', 'ponaturi', 'psoglav', 'bhuta_vahana_yanta']),
]


def herd_text(why, kinds):
    ks = ', '.join(json.dumps(k) for k in kinds)
    return f',\n      {{"why": {json.dumps(why)},\n       "kinds": [{ks}]}}'


def add_herds(text: str, changed: list) -> str:
    end = '\n    ]\n  }\n}'
    assert text.rstrip().endswith(end.strip()), 'packs.json layout changed'
    idx = text.rstrip().rfind(end)
    add = ''
    for why, kinds in PACK_HERDS:
        if f'"{kinds[0]}"' not in text:
            add += herd_text(why, kinds)
    if not add:
        return text
    changed.append('packs herds')
    head = text.rstrip()[:idx]
    return head + add + end + '\n'


# The new powers' tells (data/tells.json; src/tells.py, src/lore_powers.py).
# 'sign' is one sentence of what the eye sees and never names the mechanic.
TELLS = {
    'countdown_voice': {
        'sign': "{The} stands silent and watches you, its great chest filling.",
        'does': "{He} barks three times, slowly; whoever is still in {his} sight at the third bark is "
                "overtaken by terror.",
        'counter': "Get out of {his} sight before the third bark: a wall or a corner is shelter, as a "
                   "house was in the Highlands. Wax in the ears stops the bark too."},
    'metal_eater': {
        'sign': "Needles, spoons and spear-heads bristle half-swallowed from {the}'s hide.",
        'does': "{He} eats iron: a blade of iron or steel that bites {him} may be gnawed blunt, and "
                "every mouthful mends {him}.",
        'counter': "Strike {him} with something {he} cannot eat: fire, a coating of fire oil, a "
                   "silver, bronze or wooden weapon, or a named blade."},
    'corpse_hop': {
        'sign': "{The} grins with a face that does not fit the body {he} wears.",
        'does': "When the body {he} wears falls, the spirit slips into the nearest corpse and gets up "
                "again.",
        'counter': "Harvest or search the dead lying near the fight before you finish {him}, or "
                   "cast Banishment on {him}: a spirit sent away finds no body."},
    'parley': {
        'sign': "{The} rises from the water and calls out, as if waiting for an answer.",
        'does': "{He} and {his} kin ask a riddle in verse; a good answer lets you pass, and a poor one "
                "brings the storm down on you.",
        'counter': "Answer well: it is a question of words and the way a sentence is built."},
    'appeased_by': {
        'sign': "{The} sniffs at your pack with a starving look.",
        'does': "Hunger drives {him}, and a gift of food can turn {him} away.",
        'counter': "Set down a ration or some plain food near {him}: {he} eats it and leaves "
                   "you be."},
    'on_stunned': {
        'sign': "Water slops in a dish on the top of {the}'s head.",
        'does': "{His} strength is in the water on {his} head.",
        'counter': "Knock {him} senseless and the water spills: {his} arms go weak."},
    'hidden_overhead': {
        'sign': "Something hangs among the shadows of the roof above {the}.",
        'does': "{He} hangs overhead in the dark and drops on whoever passes under.",
        'counter': "Carry a light: in its glow you see {him} waiting above you."},
    'weak_spot_chain': {
        'sign': "{The}'s matted hide is thick as tree bark, except at the belly.",
        'does': "{His} hide turns weak blows; only the soft place at {his} navel gives.",
        'counter': "Only a long chain of right answers finds the soft place: fire works too."},
    'sheds_skin': {
        'sign': "Old skins hang in tatters from {the}'s coils.",
        'does': "When {he} is badly hurt {he} sheds a skin and the worst of {his} wounds with it, but "
                "{he} has only so many skins.",
        'counter': "Press on through each shedding: the skins run out."},
    'carry_off': {
        'sign': "{The}'s talons are big enough to close round a horse.",
        'does': "{He} can snatch you up and drop you far away, hurt and alone.",
        'counter': "A heavy load makes you harder to lift: weighed down by your gear, you are "
                   "snatched half as often."},
    'ranged_pull': {
        'sign': "The air moves toward {the} as {he} breathes.",
        'does': "{He} breathes in, and the pull of {his} breath drags you toward {his} coils from far "
                "away.",
        'counter': "Stay out of {his} sight, or fight {him} where you want to be: the breath only "
                   "draws you in."},
    'gold_gatherer': {
        'sign': "Glittering sand clings to {the}'s legs.",
        'does': "{He} lives for gold and follows a thief by scent.",
        'counter': "Drop a little gold and {he} stops to gather it, as the camels of Herodotus' "
                   "tale were let go to slow the ants."},
    'steal_offering': {
        'sign': "{The}'s needle-thin throat works as {he} looks at your pack.",
        'does': "{He} snatches food out of your pack and crams it down, and it is gone.",
        'counter': "Keep your rations few when {he} is near, or set one down for {him} freely: "
                   "an offering quiets {him}."},
    'fumbling': {
        'sign': "Bad luck hangs round {the} like smoke.",
        'does': "Ill luck clings to whoever {he} touches: for a long while your plans keep going "
                "wrong.",
        'counter': "Put out {his} eye or finish {him} fast; a prayer or an altar lifts the ill luck."},
    'strangulation': {
        'sign': "{The} has long, strong fingers that never stop moving.",
        'does': "{He} grips you by the throat and holds you under.",
        'counter': "Break free fast and keep out of {his} grip; a free hand is your best friend."},
    'heal_blocked': {
        'sign': "A smell of old spices and rot hangs round {the}.",
        'does': "{His} touch leaves a wound that will not mend for a while, by potion or by prayer.",
        'counter': "Do not let {him} touch you, or fight {him} with fire: old linen burns."},
    'talisman': {
        'sign': "{The} hops stiffly, arms out, a strip of yellow paper fluttering at {his} brow.",
        'does': "{He} finds a living man by his breath.",
        'counter': "Read any scroll with {him} in your sight: the written page stops {him} like "
                   "a talisman. Standing still holds your breath from {him}."},
}

NEW_SENSES = {
    'breath': {'range': 6, 'through_walls': False, 'sees_invisible': True, 'fails_at_rest': True,
               'lines': {'known': "{The} turns {his} head, sniffing. {He} has found your breath; stand "
                                  "still and hold it, and {he} loses you.",
                         'seen': "{The} turns {his} head, sniffing, and hops toward you.",
                         'unseen': "Somewhere close, something takes a long, slow sniff."}},
    'blood_scent': {'range': 24, 'through_walls': True, 'sees_invisible': True, 'needs_bleeding': True,
                    'lines': {'known': "{The} lifts {his} head, tasting the air. {He} smells your blood, "
                                       "and will follow it anywhere until it stops.",
                              'seen': "{The} lifts {his} head, tasting the air, and turns toward you.",
                              'unseen': "Somewhere a long tongue flickers, tasting the air."}},
}
# Phrases, as the others are ("He finds his prey by touch alone and the
# breath of the living."): never a capital mid-sentence.
SENSE_NAMES = {'breath': 'the breath of the living', 'blood_scent': 'the smell of blood'}
SENSES_UPGRADE = {'jiangshi': ['blind', 'breath'], 'komodo_brute': ['blood_scent']}

HINTS = {
    # The pool is full after slices G and AI-1 (test_hint_pool: each tier
    # within ten of its old count, 420 in all): the Cu-Sith's door, the
    # Preta's freely given meal and the Ponaturi's morning wait for a swap.
    # The Amazon conch and the Visayas drums were cut: they told of noise
    # against a swallower, which is not built.
    '3': ["Herodotus says that the gold-diggers of India let a camel go now and then as the ants gained on them, and gold will slow a greedy pursuer as well as a camel does."],
    '4': ["The Serbian smith who blinded Likho escaped beneath a sheepskin, for ill luck that cannot see you cannot follow you."],
}


def add_tells(text: str, changed: list) -> str:
    d = json.loads(text)
    # A tell already written whose words changed: each string in place (the
    # file's layout kept).
    for k, e in TELLS.items():
        old = d['effects'].get(k)
        if not old:
            continue
        for field in ('sign', 'does', 'counter'):
            if old.get(field) != e[field]:
                was = json.dumps(old[field], ensure_ascii=False)
                assert text.count(was) == 1, ('tells.json', k, field)
                text = text.replace(was, json.dumps(e[field], ensure_ascii=False))
                changed.append(f'tell {k}.{field}')
    d = json.loads(text)
    new = [k for k in TELLS if k not in d['effects']]
    if not new:
        return text
    # 'order': append before the closing bracket of the list.
    i = text.index('"order": [')
    j = text.index(']', i)
    keys = ', '.join(json.dumps(k) for k in new)
    text = text[:j] + ',\n            ' + keys + text[j:]
    # 'effects': before the file's last two closing braces.
    body = ''
    for k in new:
        e = TELLS[k]
        body += (f',\n    {json.dumps(k)}: {{\n      "sign": {json.dumps(e["sign"], ensure_ascii=False)},'
                 f'\n      "does": {json.dumps(e["does"], ensure_ascii=False)},'
                 f'\n      "counter": {json.dumps(e["counter"], ensure_ascii=False)}\n    }}')
    end = text.rstrip()
    assert end.endswith('}\n  }\n}') or end.endswith('}\n  }\n}'.replace('\n', '\r\n')), 'tells.json layout changed'
    cut = end.rfind('\n  }\n}')
    text = end[:cut] + body + end[cut:] + '\n'
    changed.append('tells ' + ','.join(new))
    return text


# ---------------------------------------------------------------------------
def main(argv) -> int:
    write = '--write' in argv
    changed: list = []

    mons = _load(D / 'monsters.json')
    for kid, defn in NEW.items():
        old = mons.get(kid) or {}
        fresh = json.loads(json.dumps(defn))
        if old.get('treasure'):
            fresh['treasure'] = old['treasure']          # the purse gold_by_lore.py wrote
        for key in ('weaknesses', 'resistances', 'shrugs_off', 'status_immune', 'status_weak'):
            if key in old:
                fresh[key] = old[key]                    # what the affinity pass wrote (below)
        if old.get('lore') and not defn.get('lore'):
            fresh['lore'] = old['lore']
        if old != fresh:
            mons[kid] = fresh
            changed.append(kid)
    upgrade(mons, changed)

    prof_path = D / 'family_affinity.json'
    prof = _load(prof_path)
    for kid, entry in AFFINITY.items():
        if prof['kinds'].get(kid) != entry:
            prof['kinds'][kid] = entry
            changed.append(f'affinity {kid}')
    # Each new kind's five lists, as the pass writes them (it is the one rule:
    # tests/test_affinity_lore.py). The lists start from the kind's own data.
    for kid in NEW:
        base = dict(mons[kid])
        base['weaknesses'] = list(NEW[kid]['weaknesses'])
        base['resistances'] = list(NEW[kid]['resistances'])
        base['shrugs_off'] = list(NEW[kid]['shrugs_off'])
        want = affinity_pass.resolve(kid, base, prof)
        for key, val in want.items():
            if mons[kid].get(key) != val:
                mons[kid][key] = val
                changed.append(f'{kid}.{key}')

    sizes = _load(D / 'monster_sizes.json')
    for kid, sz in SIZES.items():
        if sizes['sizes'].get(kid) != sz:
            sizes['sizes'][kid] = sz
            changed.append(f'size {kid}')

    senses = _load(D / 'senses.json')
    for s, spec in NEW_SENSES.items():
        if senses['senses'].get(s) != spec:
            senses['senses'][s] = spec
            changed.append(f'sense {s}')
        if senses['sense_names'].get(s) != SENSE_NAMES[s]:
            senses['sense_names'][s] = SENSE_NAMES[s]
            changed.append(f'sense name {s}')
    for kid, ss in {**SENSES, **SENSES_UPGRADE}.items():
        if senses['monsters'].get(kid) != ss:
            senses['monsters'][kid] = ss
            changed.append(f'senses {kid}')
    for kid, r in SENSE_RANGES.items():
        if senses['monster_ranges'].get(kid) != r:
            senses['monster_ranges'][kid] = r
            changed.append(f'sense range {kid}')

    hmap = _load(ITEMS / 'harvest_map.json')
    for item in INGREDIENTS:
        kid = item['def']['source_monster']
        if hmap['monsters'].get(kid) != item['id']:
            hmap['monsters'][kid] = item['id']
            changed.append(f'harvest {kid}')
    for kid, iid in HARVEST_SHARE.items():
        if hmap['monsters'].get(kid) != iid:
            hmap['monsters'][kid] = iid
            changed.append(f'harvest {kid}')
    for kid in PEOPLE:
        hmap['monsters'].pop(kid, None)
        if kid not in hmap['people']:
            hmap['people'].append(kid)
            changed.append(f'people {kid}')
    if list(hmap['monsters']) != sorted(hmap['monsters']):
        hmap['monsters'] = dict(sorted(hmap['monsters'].items()))
    if hmap['people'] != sorted(hmap['people']):
        hmap['people'] = sorted(hmap['people'])

    ings = _load(ITEMS / 'ingredient.json')
    for item in INGREDIENTS:
        if ings.get(item['id']) != item['def']:
            ings[item['id']] = item['def']
            changed.append(f'ingredient {item["id"]}')
    for iid, line in RETIRED_KIN_LINES.items():
        desc = ings[iid]['description']
        if line in desc:
            ings[iid]['description'] = desc.replace(' ' + line, '').replace(line, '').rstrip()
            changed.append(f'kin line off {iid}')
    for iid, line in KIN_LINES.items():
        desc = ings[iid]['description']
        if line not in desc:
            ings[iid]['description'] = desc.rstrip() + ' ' + line
            changed.append(f'kin line {iid}')

    recs = _load(ITEMS / 'recipes.json')
    floors = {k: v['min_level'] for k, v in ings.items()}
    food = _load(ITEMS / 'food.json')
    floors.update({k: v.get('min_level', 1) for k, v in food.items() if isinstance(v, dict)})
    for rid, r in RECIPES.items():
        want = dict(r)
        fl = [floors[p] for p in r['ingredients']]
        if len(set(r['ingredients'])) > 1 and min(fl) <= 20 and max(fl) >= 40:
            want['cross_depth'] = True
        if rid in recs and recs[rid].get('art'):
            want['art'] = recs[rid]['art']          # the picture dish_art.py picked (fix_art)
        if recs.get(rid) != want:
            recs[rid] = want
            changed.append(f'recipe {rid}')

    freq_path = HERE / 'kitchen' / 'part_freq.json'
    freq = _load(freq_path)
    for item in INGREDIENTS:
        if item['id'] not in freq['parts']:
            # Not yet measured by part_freq.py: counted as a part no run turns
            # up, which the recipe rules pair only with common partners.
            freq['parts'][item['id']] = {'share_of_runs': 0.0, 'mean_count': 0.0,
                                         'median_first_floor': None}
            changed.append(f'part_freq {item["id"]}')
    freq['parts'] = dict(sorted(freq['parts'].items()))

    art_path = HERE / 'kitchen' / 'dish_art.json'
    dish_art = _load(art_path)
    for rid in RECIPES:
        if dish_art.get(rid) != recs[rid]['art']:
            dish_art[rid] = recs[rid]['art']
    doc = dish_art.pop('_doc')
    dish_art = {'_doc': doc, **dict(sorted(dish_art.items()))}

    inst_path = HERE / 'genart' / 'installed_items.json'
    installed = _load(inst_path)
    pictures = []
    for item in INGREDIENTS:
        dst = ART / f"{item['id']}.png"
        src = ART / f"{item['picture']}.png"
        assert src.exists(), src
        if not dst.exists():
            pictures.append((src, dst))
            changed.append(f'picture {item["id"]}')
        if item['id'] not in installed['items']:
            installed['items'].append(item['id'])
    installed['items'] = sorted(set(installed['items']))

    packs_path = D / 'packs.json'
    packs_text = add_herds(packs_path.read_text(encoding='utf-8'), changed)
    tells_path = D / 'tells.json'
    tells_text = add_tells(tells_path.read_text(encoding='utf-8'), changed)

    hints = _load(D / 'hints.json')
    for tier, lst in HINTS.items():
        for h in lst:
            if h not in hints[tier]:
                hints[tier].append(h)
                changed.append(f'hint {tier}')

    print('changes:', ', '.join(changed) if changed else 'none')
    if write and changed:
        _dump(D / 'monsters.json', mons, 2, False)
        _dump(prof_path, prof, 2, False)
        _dump(D / 'monster_sizes.json', sizes, 1, True)
        _dump(D / 'senses.json', senses, 2, True)
        _dump(ITEMS / 'harvest_map.json', hmap, 1, True)
        _dump(ITEMS / 'ingredient.json', ings, 2, False)
        _dump(ITEMS / 'recipes.json', recs, 1, False)
        _dump(freq_path, freq, 1, True)
        _dump(art_path, dish_art, 1, True)
        _dump(inst_path, installed, 2, True)
        _dump(D / 'hints.json', hints, 2, True)
        packs_path.write_text(packs_text, encoding='utf-8')
        tells_path.write_text(tells_text, encoding='utf-8')
        for src, dst in pictures:
            shutil.copyfile(src, dst)
        print('written')
        if fix_art():
            print('dish pictures picked by dish_art.py: written')
    return 0


def fix_art() -> bool:
    """Each new dish shows the picture tools/content/kitchen/dish_art.py picks
    for its name, tier and benefit (the rule build_kitchen.py follows and
    tests/test_dish_art.py checks), read from the data just written."""
    sys.path.insert(0, str(ROOT / 'src'))
    sys.path.insert(0, str(HERE / 'kitchen'))
    import dish_art as _da
    import kitchen as _kitchen
    have = _da.drawn(str(ART))
    recs = _load(ITEMS / 'recipes.json')
    art_path = HERE / 'kitchen' / 'dish_art.json'
    record = _load(art_path)
    moved = False
    for rid in RECIPES:
        rec = {'id': rid, **recs[rid]}
        art = _da.recipe_art(rid, rec, _kitchen.dish_tier(rec), have)
        if recs[rid].get('art') != art or record.get(rid) != art:
            recs[rid]['art'] = art
            record[rid] = art
            moved = True
    if moved:
        _dump(ITEMS / 'recipes.json', recs, 1, False)
        _dump(art_path, record, 1, True)
    return moved


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
