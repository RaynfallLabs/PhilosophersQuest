"""The monster lore pass (winning-build plan 2026-11-13, section 3.2): write
every kind's weaknesses, resistances, shrugs_off, status_immune and
status_weak into data/monsters.json from data/family_affinity.json, narrow
holy to the unholy, and give every plain 'physical' monster attack a form
(slash, pierce or blunt) by its name and delivery.

    py tools/content/affinity_pass.py            # report (dry run)
    py tools/content/affinity_pass.py --write    # write monsters.json

Idempotent: a second run changes nothing. Format-preserving: monsters.json
is written back byte for byte the way it was (tools/content/jsonfmt.py), so
the diff is the fields this pass touched.

How a kind is resolved (data/family_affinity.json `_schema`):
  * FORM (slash, pierce, blunt): wholly from the layers, family -> group ->
    kind, each may say weak / resist / shrugs_off / neutral. A named foe
    keeps the forms written on it unless `kinds` names its form.
  * ELEMENTS and SUBSTANCES: the kind's own lists stay; a family or tag rule
    adds softly (never against the kind's own opposite word); a group or a
    kind adds by force; `drop` removes. Then holy weakness is taken from
    every kind that is not unholy (undead, demon, or named cursed).
  * STATUS: family list, replaced by the group's or kind's when given; the
    tag rules add immunities; anything immune leaves status_weak; the
    fear_of_fire token is not kept on a kind that resists fire, nor on a
    named foe (a boss, mini-boss or seal demon is never routed:
    Monster.resists_control, Monster._after_typed_hit).
tests/test_affinity_lore.py checks monsters.json equals resolve_all() of
itself, so a kind added by hand without running this pass is caught.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))

FORMS = ('slash', 'pierce', 'blunt')
STATES = ('weak', 'resist', 'shrugs_off', 'neutral')
_LIST = {'weak': 'weaknesses', 'resist': 'resistances', 'shrugs_off': 'shrugs_off'}


def load_profiles(path=None) -> dict:
    path = path or os.path.join(ROOT, 'data', 'family_affinity.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def is_named(m: dict) -> bool:
    return bool(m.get('is_boss') or m.get('is_mini_boss') or m.get('is_seal_demon'))


def group_of(kind: str, prof: dict):
    for gid, g in (prof.get('groups') or {}).items():
        if kind in (g.get('kinds') or ()):
            return gid, g
    return None, {}


def is_unholy(kind: str, m: dict, prof: dict) -> bool:
    u = prof.get('unholy') or {}
    return bool(set(m.get('tags') or ()) & set(u.get('tags') or ())) or kind in (u.get('cursed') or {})


def _form_state(m: dict, f: str) -> str:
    if f in (m.get('weaknesses') or ()):
        return 'weak'
    if f in (m.get('shrugs_off') or ()):
        return 'shrugs_off'
    if f in (m.get('resistances') or ()):
        return 'resist'
    return 'neutral'


def _ordered(old: list, keep: set, extra: list) -> list:
    """`old`'s members that stay, in their order, then the new ones in
    `extra`'s order: the smallest diff."""
    out = [x for x in old if x in keep]
    for x in extra:
        if x in keep and x not in out:
            out.append(x)
    return out


def resolve(kind: str, m: dict, prof: dict) -> dict:
    """The five lists for one kind: {'weaknesses', 'resistances',
    'shrugs_off', 'status_immune', 'status_weak'}."""
    fam = (prof.get('families') or {}).get(m.get('family'), {}) or {}
    _gid, grp = group_of(kind, prof)
    ko = (prof.get('kinds') or {}).get(kind, {}) or {}
    tags = list(m.get('tags') or ())
    tag_rules = [(t, r) for t, r in (prof.get('tag_rules') or {}).items() if t in tags]

    old = {k: list(m.get(k) or []) for k in ('weaknesses', 'resistances', 'shrugs_off')}

    # ---- forms ---------------------------------------------------------
    if is_named(m) and 'form' not in ko:
        forms = {f: _form_state(m, f) for f in FORMS}
    else:
        forms = {f: 'neutral' for f in FORMS}
        for layer in (fam, grp, ko):
            for f, st in (layer.get('form') or {}).items():
                forms[f] = st

    # ---- elements and substances ---------------------------------------
    cur = {lst: [x for x in old[lst] if x not in FORMS] for lst in old}

    def put(t, state, force):
        target = _LIST[state]
        others = [v for k, v in _LIST.items() if v != target]
        if not force and any(t in cur[o] for o in others):
            return
        for o in others:
            if t in cur[o]:
                cur[o].remove(t)
        if t not in cur[target]:
            cur[target].append(t)

    soft_layers = [fam] + [r for _t, r in tag_rules]
    for layer, force in [(x, False) for x in soft_layers] + [(grp, True), (ko, True)]:
        el = layer.get('elements') or {}
        for state in ('weak', 'resist', 'shrugs_off'):
            for t in el.get(state) or ():
                put(t, state, force)
        for t in el.get('drop') or ():
            for lst in cur:
                if t in cur[lst]:
                    cur[lst].remove(t)
    if not is_unholy(kind, m, prof) and 'holy' in cur['weaknesses']:
        cur['weaknesses'].remove('holy')

    for f, st in forms.items():
        if st != 'neutral':
            cur[_LIST[st]].append(f)

    out = {lst: _ordered(old[lst], set(cur[lst]), cur[lst]) for lst in cur}

    # ---- status ---------------------------------------------------------
    immune = list(fam.get('status_immune') or [])
    weak = list(fam.get('status_weak') or [])
    for layer in (grp, ko):
        if 'status_immune' in layer:
            immune = list(layer['status_immune'])
        if 'status_weak' in layer:
            weak = list(layer['status_weak'])
    for _t, r in tag_rules:
        for e in r.get('status_immune') or ():
            if e not in immune:
                immune.append(e)
    weak = [e for e in weak if e not in immune]
    # Fire routs nothing that resists it, and no named foe: he is too wilful
    # to be put to flight (Monster.resists_control), so on him the token was
    # only a line that lied ("Fire puts it to flight."; bug bash WB-B03).
    if 'fear_of_fire' in weak and ('fire' in out['resistances'] or 'fire' in out['shrugs_off']
                                   or is_named(m)):
        weak.remove('fear_of_fire')
    out['status_immune'] = immune
    out['status_weak'] = weak
    return out


# ---------------------------------------------------------------------------
# Typed attacks: a plain 'physical' attack gets a form by its name and delivery
# ---------------------------------------------------------------------------
# By exact name first (the odd ones), then by words in the name, then by how
# it lands. A bite, sting, gore, horn or thrust pierces; a claw, rake, talon
# or blade cuts; a slam, fist, club, tail, trample, crush, headbutt, grab or
# engulfing crushes.
_BY_NAME = {
    'horn blast': 'blunt', 'beak cleave': 'slash', 'beak slash': 'slash',
    'six-headed strike': 'pierce', 'tail spike': 'pierce', 'spine whip': 'pierce',
    'shortsword': 'pierce', 'crushing claw': 'blunt', 'talon crush': 'blunt',
    'paw crush': 'blunt', 'mandible crush': 'blunt', 'jab': 'blunt',
    'second flurry': 'slash', 'death roll': 'slash', 'bone hurl': 'blunt',
    'morningstar': 'blunt', 'beard barbs': 'pierce', 'dagger throw': 'pierce',
    'web spray': 'blunt', 'silk line': 'blunt', 'bronze feather volley': 'pierce',
    'thorn volley': 'pierce', 'bone arrow': 'pierce', 'shoot': 'pierce',
    'pincers': 'blunt', 'pinch': 'blunt', 'raptorial strike': 'slash',
    'pounce': 'slash', 'saw limbs': 'slash', 'wind slash': 'slash',
    'chain lash': 'blunt', 'bone lash': 'slash', 'crushing bite': 'pierce',
    'crushing maw': 'pierce', 'engulfing maw': 'blunt', 'treasure maw': 'pierce',
    'tongue lash': 'blunt', 'tendril lash': 'blunt', 'tendril whip': 'blunt',
    'vine whip': 'blunt', 'whip strike': 'slash', 'scourging strike': 'slash',
    'tail lash': 'blunt', 'talon grip': 'slash', 'battleaxe': 'slash', 'longsword': 'slash',
    'devouring embrace': 'blunt',
}
_BLUNT_WORDS = ('engulf', 'envelop', 'pseudopod', 'smother', 'tail', 'tongue', 'tentacle',
                'chain', 'slam', 'smash', 'crush', 'club', 'maul', 'hammer', 'fist', 'stomp',
                'trample', 'ram', 'headbutt', 'buffet', 'bash', 'hoof', 'kick', 'boulder',
                'rock', 'debris', 'constrict', 'hug', 'grab', 'grasp', 'embrace', 'throttle',
                'flail', 'staff', 'shillelagh', 'web', 'entangl', 'strands', 'sticky', 'adhesive')
_PIERCE_WORDS = ('bite', 'fang', 'snap', 'maw', 'devour', 'tusk', 'gore', 'horn', 'sting',
                 'spike', 'barb', 'spine', 'peck', 'beak', 'stab', 'thrust', 'spear', 'pike',
                 'lance', 'arrow', 'bolt', 'dagger', 'knife', 'plunge', 'hook', 'thorn')
_SLASH_WORDS = ('claw', 'rake', 'talon', 'rend', 'slash', 'cleave', 'axe', 'sword', 'scimitar',
                'katana', 'khopesh', 'glaive', 'blade', 'saw', 'whip', 'lash', 'flurry')
_BY_DELIVERY = {'bite': 'pierce', 'sting': 'pierce', 'ranged': 'pierce'}


# Teeth and stings outrank the crushing words ('crushing bite' is still
# teeth); a word matches when a word of the name starts with it, so 'ram'
# does not match 'tRAMple' nor 'horn' 'tHORN'.
_PIERCE_BITE = ('bite', 'fang', 'snap', 'maw', 'devour', 'tusk', 'gore', 'sting')


def _word_match(name: str, words) -> bool:
    toks = re.findall(r'[a-z]+', name)
    return any(any(t.startswith(w) for t in toks) for w in words)


def attack_form(atk: dict) -> str:
    """slash, pierce or blunt for a plain physical attack: its exact name,
    else the first word group a word of its name starts with (teeth and
    stings, then the crushing words, then the other points, then the
    edges), else how it lands (a bite or sting pierces, a shot pierces,
    anything else crushes)."""
    name = str(atk.get('name', '') or '').lower().strip()
    if name in _BY_NAME:
        return _BY_NAME[name]
    for group, form in ((_PIERCE_BITE, 'pierce'), (_BLUNT_WORDS, 'blunt'),
                        (_PIERCE_WORDS, 'pierce'), (_SLASH_WORDS, 'slash')):
        if _word_match(name, group):
            return form
    return _BY_DELIVERY.get(str(atk.get('delivery', '') or ''), 'blunt')


def resolve_attacks(m: dict) -> list:
    """The kind's attacks with every plain 'physical' one given a form."""
    out = []
    for atk in m.get('attacks') or []:
        a = dict(atk)
        if a.get('type') == 'physical':
            a['type'] = attack_form(a)
        out.append(a)
    return out


def resolve_all(mons: dict, prof: dict) -> dict:
    """{kind: (lists, attacks)} for every kind."""
    return {k: (resolve(k, m, prof), resolve_attacks(m)) for k, m in mons.items()}


def apply(mons: dict, prof: dict) -> collections.Counter:
    """Write the pass into `mons` in place; returns what changed."""
    changed = collections.Counter()
    for kind, m in mons.items():
        lists = resolve(kind, m, prof)
        for key in ('weaknesses', 'resistances', 'shrugs_off', 'status_immune', 'status_weak'):
            if key not in m or list(m.get(key) or []) != lists[key]:
                m[key] = lists[key]
                changed[key] += 1
        atks = resolve_attacks(m)
        if atks != m.get('attacks'):
            for a_old, a_new in zip(m['attacks'], atks):
                if a_old.get('type') != a_new.get('type'):
                    a_old['type'] = a_new['type']
                    changed['attack_type'] += 1
    return changed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    import jsonfmt
    path = os.path.join(ROOT, 'data', 'monsters.json')
    mons, fmt = jsonfmt.load(path)
    prof = load_profiles()
    changed = apply(mons, prof)
    for k, n in sorted(changed.items()):
        print(f"{k:16} {n:5} kinds/attacks changed")
    if not changed:
        print("nothing to change (the pass is up to date)")
    if a.write and changed:
        jsonfmt.save(path, mons, fmt)
        print("written:", path)
    elif changed:
        print("(dry run: --write to write)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
