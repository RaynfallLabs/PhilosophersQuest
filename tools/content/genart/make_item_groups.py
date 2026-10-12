"""Split the game's items into work groups for the sprite pass.

    python tools/content/genart/make_item_groups.py

Writes _genart/item_groups/iNN.json. Weapons and armour that are a template in a
material (iron longsword, bronze longsword...) are NOT listed one by one: their
group lists each TEMPLATE once, to be drawn in neutral grey and tinted per material
by install_items.py. Everything else is listed by id with the facts a brief needs.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content', 'art'))
import manifest

KEEP = ('id', 'name', 'category', 'about', 'unidentified_name', 'material', 'template', 'template_basis', 'class',
        'weapon_class', 'slot', 'tier', 'two_handed', 'effect', 'family', 'source_monster', 'tier_role', 'outcome_id',
        'ingredients', 'is_unique', 'color')
DONE = ('mystery_altar_', 'apothecary_chest', 'iron_lockbox', 'warlord_warchest', 'scholar_satchel', 'gilded_chest',
        'ornate_chest', 'jewelry_box', 'crypt_chest', 'merchant_strongbox', 'reliquary')
# ids that are <material>_<template> though the data does not mark them as combos
LOOSE_MATERIALS = ('diamond', 'hardwood', 'wood', 'bone', 'dragonbone', 'hardened_gold', 'iron', 'steel', 'adamantine')
LOOSE_TEMPLATES = {'arrow', 'bolt', 'axe', 'club', 'crossbow', 'dagger', 'flail', 'greataxe', 'halberd', 'hammer', 'lockpick',
                   'longbow', 'longsword', 'mace', 'morningstar', 'rapier', 'scimitar', 'shortbow', 'staff', 'sword',
                   'warhammer', 'zweihander'}


def loose(rid):
    for m in LOOSE_MATERIALS:
        if rid.startswith(m + '_') and rid[len(m) + 1:] in LOOSE_TEMPLATES:
            return m, rid[len(m) + 1:]
    return None


def slim(r):
    return {k: r[k] for k in KEEP if r.get(k) not in (None, '', [])}


def main():
    recs = [r for r in manifest.build() if r['folder'] == 'items' and not r['id'].startswith(DONE)]
    W = [r for r in recs if r['kind'] == 'weapon']; A = [r for r in recs if r['kind'] == 'armor']
    M = [r for r in recs if r['kind'] == 'magic']; F = [r for r in recs if r['kind'] == 'food']
    X = [r for r in recs if r['kind'] == 'extras']
    groups = []

    def add(title, note, items, size=60):
        items = list(items)
        n = max(1, -(-len(items) // size))
        per = -(-len(items) // n)
        for i in range(n):
            groups.append({'title': title + (f' ({i + 1} of {n})' if n > 1 else ''), 'note': note, 'items': items[i * per:(i + 1) * per]})

    def templates(rs, prefix):
        t = {}
        for r in rs:
            tp = r.get('template') if r.get('combo') else (loose(r['id']) or (None, None))[1]
            if tp:
                e = t.setdefault(tp, {'id': f'{prefix}{tp}', 'template': tp, 'materials': set(), 'example_ids': []})
                e['materials'].add(r.get('material') or loose(r['id'])[0])
                for k in ('weapon_class', 'slot', 'category'):
                    if r.get(k):
                        e[k] = r[k]
                if len(e['example_ids']) < 3:
                    e['example_ids'].append(r['id'])
        return [dict(e, materials=sorted(e['materials'])) for _, e in sorted(t.items())]

    single_w = [r for r in W if not r.get('combo') and not loose(r['id'])]
    single_a = [r for r in A if not r.get('combo')]
    add('Weapon templates', 'TEMPLATES: draw each once in neutral grey (see the brief). One brief per template, id as given.',
        templates(W, 'tpl_w_'), size=40)
    add('Armour and shield templates', 'TEMPLATES: draw each once in neutral grey (see the brief). One brief per template, id as given.',
        templates(A, 'tpl_a_'), size=50)
    add('Named and unique weapons', 'One picture each, in its own true colours.',
        [slim(r) for r in sorted(single_w, key=lambda r: (r.get('template_basis') or r.get('class') or '', r['id']))], size=56)
    add('Named and unique armour', 'One picture each, in its own true colours.',
        [slim(r) for r in sorted(single_a, key=lambda r: (r.get('slot') or r.get('category') or '', r.get('template_basis') or '', r['id']))], size=67)
    by = lambda c: [slim(r) for r in sorted(M, key=lambda r: r['id']) if r['category'] == c]
    add('Accessories', 'One picture each. The unidentified_name says what it looks like.', by('accessory'), size=60)
    add('Artifacts, containers, keys and oddments', 'One picture each.',
        by('artifact') + by('container') + by('lockpick') + [slim(r) for r in X], size=60)
    add('Wands', 'One picture each; the wands must differ from one another by material and tip.', by('wand'), size=56)
    add('Potions', 'One picture each; bottle shape and liquid colour from the unidentified_name.', by('potion'), size=53)
    add('Spellbooks', 'One picture each; binding and clasp from the unidentified_name and lore.', by('spellbook'), size=74)
    add('Scrolls', 'One picture each.', by('scroll'), size=51)
    add('Rings and amulets', 'One picture each; the id names the stone or metal.', by('ring') + by('amulet'), size=78)
    add('Food, rations and boss trophies', 'One picture each.',
        [slim(r) for r in F if r['category'] == 'food' or r.get('tier_role') == 'trophy'], size=60)
    add('Monster parts', 'One picture each: a horn, gland, feather, scale and so on, cut from a monster.',
        [slim(r) for r in sorted(F, key=lambda r: r['id']) if r['category'] == 'ingredient_part'], size=79)
    primes = [slim(r) for r in sorted(F, key=lambda r: r['id']) if r.get('tier_role') == 'prime']
    groups.append({'title': 'Prime cuts (design task)',
                   'note': 'DESIGN TASK: 500-odd prime cuts, one per monster. Do not draw one each. Sort them into kinds '
                           'by what the NAME says the cut is (ichor, sac, haunch, heart...) and by family, draw one '
                           'picture per kind, and write map.json. See the brief.', 'items': primes})
    recipes = [slim(r) for r in sorted(F, key=lambda r: r['id']) if r['category'] == 'recipe']
    outcomes = json.load(open(os.path.join(ROOT, 'data', 'items', 'cook_outcomes.json'), encoding='utf-8'))
    groups.append({'title': 'Cooked dishes (design task)',
                   'note': 'DESIGN TASK: 893 recipes. Each recipe has an outcome_id; draw ONE dish picture per outcome_id '
                           '(about 144), id "dish_<outcome_id>", and write map.json sending every recipe id to its dish. '
                           'The outcomes are described in data/items/cook_outcomes.json.',
                   'items': recipes, 'outcomes': sorted({r.get('outcome_id') for r in recipes if r.get('outcome_id')})})
    out = os.path.join(ROOT, '_genart', 'item_groups')
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    for i, g in enumerate(groups, 1):
        json.dump(g, open(os.path.join(out, f'i{i:02d}.json'), 'w', encoding='utf-8'), indent=1)
        print(f'i{i:02d}: {len(g["items"]):4d}  {g["title"]}')
    covered = sum(len(g['items']) for g in groups if 'TEMPLATES' not in g['note'])
    combos = sum(1 for r in W + A if r.get('combo') or loose(r['id']))
    print('listed singly', covered, '+ template-and-material', combos, '=', covered + combos, 'of', len(recs))


if __name__ == '__main__':
    main()
