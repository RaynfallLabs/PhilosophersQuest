"""List every sprite file the game ships and say what it is a picture of.

Offline tooling (not loaded at runtime).

    python tools/content/art/manifest.py <out.json>

One record per PNG under assets/tiles/{monsters,items,env}: its folder, id,
`kind` (which drawing module owns it) and whatever the data files say about
it (name, colour, tags, slot, material, template, effect, ...). The drawing
modules work from these records, never from file names alone.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TILES = ROOT / 'assets' / 'tiles'

HUMANOID_TAGS = ('humanoid', 'goblinoid', 'goblin', 'orc', 'giant', 'bandit', 'cultist', 'kobold',
                 'gnoll', 'troll', 'caster', 'fey')
FAMILY_ORDER = ('dragon', 'undead', 'demon', 'celestial', 'construct', 'elemental', 'aberration',
                'plant') + HUMANOID_TAGS + ('reptile', 'beast', 'shapeshifter', 'outsider')
GROUP = {
    'A': set(HUMANOID_TAGS),
    'B': {'undead', 'demon', 'celestial', 'construct', 'elemental', 'aberration', 'outsider', 'other'},
    'C': {'dragon', 'plant', 'reptile', 'beast', 'shapeshifter'},
}
KEEP = ('name', 'color', 'symbol', 'tags', 'peak_floor', 'slot', 'material', 'template_basis', 'class',
        'weapon_class', 'tier', 'effect', 'spell_family', 'unidentified_name', 'is_unique', 'family',
        'source_monster', 'tier_role', 'requires_ammo', 'two_handed', 'damage_type', 'base_damage',
        'outcome_id', 'ingredients', 'bonus_type', 'school', 'element')


def _load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _slim(d: dict) -> dict:
    out = {k: d[k] for k in KEEP if k in d and d[k] not in (None, '', [], {})}
    lore = d.get('lore') or d.get('description') or ''
    if lore:
        out['about'] = lore[:220]
    if d.get('attacks'):
        out['attacks'] = [f"{a.get('name', '')} ({a.get('type', 'physical')})" for a in d['attacks'][:4]]
    if d.get('size'):
        out['size'] = d['size']
    return out


def monster_family(tags) -> str:
    for t in FAMILY_ORDER:
        if t in (tags or ()):
            return t
    return 'other'


def build() -> list[dict]:
    recs: list[dict] = []
    mons = _load(ROOT / 'data' / 'monsters.json')
    for f in sorted(os.listdir(TILES / 'monsters')):
        if not f.endswith('.png'):
            continue
        mid = f[:-4]
        if mid in mons and isinstance(mons[mid], dict):
            fam = monster_family(mons[mid].get('tags'))
            grp = next(g for g, fams in GROUP.items() if fam in fams)
            r = {'folder': 'monsters', 'id': mid, 'kind': f'monster_{grp}', 'body': fam, **_slim(mons[mid])}
            r['named'] = bool({'boss', 'legendary'} & set(mons[mid].get('tags') or ())
                              or (mons[mid].get('treasure') or {}).get('boss_scroll_id'))
        elif mid.startswith('npc_'):
            r = {'folder': 'monsters', 'id': mid, 'kind': 'monster_A', 'body': 'npc'}
        else:
            r = {'folder': 'monsters', 'id': mid, 'kind': 'monster_C', 'body': 'pet'}
        recs.append(r)

    for f in sorted(os.listdir(TILES / 'env')):
        if not f.endswith('.png'):
            continue
        eid = f[:-4]
        if eid.startswith('player'):
            recs.append({'folder': 'env', 'id': eid, 'kind': 'monster_A', 'body': 'player'})
        else:
            recs.append({'folder': 'env', 'id': eid, 'kind': 'env'})

    if not (TILES / 'env' / 'rock.png').exists():
        recs.append({'folder': 'env', 'id': 'rock', 'kind': 'env', 'new': True})

    # ---- items
    data = {}
    for p in glob.glob(str(ROOT / 'data' / 'items' / '*.json')):
        cat = os.path.basename(p)[:-5]
        d = _load(p)
        if isinstance(d, dict):
            data[cat] = {k: v for k, v in d.items() if isinstance(v, dict)}
    templates, materials = {}, {}
    for cat, sub in (('weapon', 'weapons'), ('armor', 'armor'), ('shield', 'shields')):
        for p in glob.glob(str(ROOT / 'data' / 'templates' / sub / '*.json')):
            templates[os.path.basename(p)[:-5]] = (cat, _load(p))
    for p in glob.glob(str(ROOT / 'data' / 'materials' / '**' / '*.json'), recursive=True):
        materials[os.path.basename(p)[:-5]] = _load(p)
    mat_ids = sorted(materials, key=len, reverse=True)
    OWNER = {'weapon': 'weapon', 'ammo': 'weapon', 'armor': 'armor', 'shield': 'armor',
             'accessory': 'magic', 'wand': 'magic', 'scroll': 'magic', 'potion': 'magic',
             'spellbook': 'magic', 'artifact': 'magic', 'container': 'magic', 'lockpick': 'magic',
             'food': 'food', 'ingredient': 'food', 'prime_cuts': 'food', 'recipes': 'food',
             'cook_outcomes': 'food'}
    LEGACY = {  # old combo names that are not a current template
        'weapon': ('sword', 'axe', 'dagger', 'mace', 'bow', 'crossbow', 'spear', 'club', 'flail', 'glaive',
                   'halberd', 'hammer', 'maul', 'staff', 'rapier', 'scimitar', 'sling', 'morningstar',
                   'zweihander', 'lance', 'whip', 'javelin', 'trident', 'pike', 'scythe', 'sickle', 'arrow',
                   'bolt', 'katana', 'blade', 'pick'),
        'armor': ('armor', 'mail', 'plate', 'helm', 'boots', 'bracers', 'greaves', 'shirt', 'gloves',
                  'gauntlets', 'cloak', 'robe', 'cap', 'hood', 'leggings', 'coif', 'vambraces', 'chausses',
                  'hauberk', 'cuirass', 'sabatons', 'sandals', 'cowl', 'armet', 'bascinet', 'sallet',
                  'brigandine', 'breastplate', 'tunic', 'jerkin', 'hide', 'padded', 'leather', 'ringmail',
                  'chainmail', 'splint', 'scale', 'banded'),
        'shield': ('shield', 'buckler', 'wooden', 'targe', 'pavise'),
    }
    for f in sorted(os.listdir(TILES / 'items')):
        if not f.endswith('.png'):
            continue
        iid = f[:-4]
        r = {'folder': 'items', 'id': iid}
        cat = next((c for c in data if iid in data[c]), None)
        if cat:
            r.update(kind=OWNER.get(cat, 'magic'), category=cat, **_slim(data[cat][iid]))
        elif iid.startswith('recipe_'):
            r.update(kind='food', category='recipe')
            _rv = (data.get('recipes') or {}).get(iid[len('recipe_'):])
            if _rv:
                r.update(new=True, **_slim(_rv))
        else:
            mat = next((m for m in mat_ids if iid.startswith(m + '_')), None)
            rest = iid[len(mat) + 1:] if mat else iid
            if mat and rest in templates:
                cat, tpl = templates[rest]
                r.update(kind=OWNER[cat], category=cat, combo=True, material=mat, template=rest,
                         material_color=materials[mat].get('color'), **{k: v for k, v in _slim(tpl).items()
                                                                        if k in ('slot', 'class', 'weapon_class', 'two_handed')})
            else:
                words = set(rest.split('_'))
                legacy = next((c for c, keys in LEGACY.items() if words & set(keys)
                               or any(rest.endswith(k) for k in keys)), None)
                if legacy and (mat or rest in templates or legacy):
                    r.update(kind=OWNER[legacy], category=legacy, combo=bool(mat), template=rest)
                    if mat:
                        r.update(material=mat, material_color=materials[mat].get('color'))
                elif iid.startswith(('ring_', 'amulet_', 'belt_', 'bracelet_', 'necklace_', 'charm_',
                                     'wand_', 'scroll_', 'potion_', 'spellbook_', 'tome_', 'chest', 'key')):
                    r.update(kind='magic', category=iid.split('_')[0])
                else:
                    r.update(kind='food', category='ingredient_part')   # a monster part or foraged thing
        recs.append(r)
    # ---- anything the data files define that has no picture yet gets one
    have = {(r['folder'], r['id']) for r in recs}
    for cat, d in data.items():
        # Not rings, amulets, wands, scrolls or books: an unidentified one is
        # shown by a stand-in picture on purpose, and a picture of its own
        # would give away what it is.
        if cat not in ('ingredient', 'armor', 'shield', 'weapon', 'ammo', 'artifact', 'food', 'container'):
            continue
        for iid, v in d.items():
            if ('items', iid) not in have:
                recs.append({'folder': 'items', 'id': iid, 'kind': OWNER.get(cat, 'magic'),
                             'category': cat, 'new': True, **_slim(v)})
    # Every recipe: the menu asks for recipe_<recipe id>. The 364 pictures
    # that existed were named for an older recipe set, so not one was shown.
    for rid, v in (data.get('recipes') or {}).items():
        if ('items', f'recipe_{rid}') not in have:
            recs.append({'folder': 'items', 'id': f'recipe_{rid}', 'kind': 'food', 'category': 'recipe',
                         'new': True, **_slim(v)})
    # Every material x template pair the game can make. A third had no picture
    # and borrowed another material's (leather gloves drawn as teal plate).
    have = {(r['folder'], r['id']) for r in recs}
    for cat, sub, mdirs in (('weapon', 'weapons', ('weapons',)), ('armor', 'armor', ('armor',)),
                            ('shield', 'shields', ('armor', 'weapons'))):
        mats = {}
        for md in mdirs:
            for p in glob.glob(str(ROOT / 'data' / 'materials' / md / '*.json')):
                mats.setdefault(os.path.basename(p)[:-5], _load(p))
        for tid, (tcat, tpl) in templates.items():
            if tcat != cat:
                continue
            accepts = set(tpl.get('compatible_material_classes') or ())
            for mid, mat in mats.items():
                mclass = str(mat.get('material_class', ''))
                if accepts and not (accepts & (set(mclass.split(',')) | {mclass})):
                    continue
                iid = f'{mid}_{tid}'
                if ('items', iid) in have:
                    continue
                have.add(('items', iid))
                recs.append({'folder': 'items', 'id': iid, 'kind': OWNER[cat], 'category': cat,
                             'combo': True, 'new': True, 'material': mid, 'template': tid,
                             'material_color': mat.get('color'),
                             **{k: v for k, v in _slim(tpl).items()
                                if k in ('slot', 'class', 'weapon_class', 'two_handed')}})
    for mid, v in mons.items():
        if isinstance(v, dict) and ('monsters', mid) not in have:
            fam = monster_family(v.get('tags'))
            grp = next(g for g, fams in GROUP.items() if fam in fams)
            recs.append({'folder': 'monsters', 'id': mid, 'kind': f'monster_{grp}', 'body': fam,
                         'new': True, **_slim(v)})
    # ---- map objects defined in code (Death, gold, the trader, mystery shrines)
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'extras'))
    import extras
    own = {(r['folder'], r['id']) for r in extras.records()}
    recs = [r for r in recs if (r['folder'], r['id']) not in own] + extras.records()
    return recs


if __name__ == '__main__':
    recs = build()
    out = sys.argv[1] if len(sys.argv) > 1 else 'manifest.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(recs, f, indent=1, ensure_ascii=False)
    from collections import Counter
    print(len(recs), Counter(r['kind'] for r in recs))
    print(Counter((r['kind'], r.get('category') or r.get('body')) for r in recs))
