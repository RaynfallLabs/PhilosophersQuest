#!/usr/bin/env python
"""Write the monster lore pass (2026-11-19) into data/monsters.json, checked.

The lore pass re-authors each ordinary monster's combat numbers from its own
lore (Brandon, 2026-11-19: no smoothing multipliers; "fix the data at the
source"). Its authors write proposals, one file a band
({id: {field: value}}, `_why`, `_tier_moves`); this applies them, after
checking each one keeps to the pass's rules
(docs/design/MONSTER_LORE_PASS_2026_11_19.md):

  * only these fields change: hp, attacks, thac0, speed, multi_attack_count,
    pack, pack_size, opener, peak_floor, spread, min_level, ai_pattern;
  * no existing attack is renamed or removed, and each keeps every key it had;
  * a new attack has a name, damage, type and delivery;
  * dice parse; an opener names one of the attacks and its range is 1-7
    (2+ only for a range, gaze, voice or breath delivery);
  * no named foe (boss, mini-boss, seal demon) is touched;
  * every changed id has a `_why`.

Usage:
    py tools/balance/apply_lore_pass.py <proposal.json> [...] [--write]
Without --write it only checks and prints what would change. The key order
of monsters.json and of each entry is kept; new keys go at the end of an
entry.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'monsters.json')

ALLOWED = {'hp', 'attacks', 'thac0', 'speed', 'multi_attack_count', 'pack', 'pack_size',
           'opener', 'peak_floor', 'spread', 'min_level', 'ai_pattern'}
DICE = re.compile(r"^\d*d\d+([+-]\d+)?$|^\d+$")
RANGED = ('ranged', 'range', 'gaze', 'voice', 'breath')
AI = {'aggressive', 'ranged', 'ambush', 'hit_and_run', 'sessile', 'cowardly', 'summoner', 'healer'}


def check(mid, old, new, why) -> list:
    errs = []
    if old.get('is_boss') or old.get('is_mini_boss') or old.get('is_seal_demon'):
        return [f'{mid}: a named foe']
    bad = set(new) - ALLOWED
    if bad:
        errs.append(f'{mid}: fields not allowed {sorted(bad)}')
    if not why:
        errs.append(f'{mid}: no _why')
    if 'hp' in new and not DICE.match(str(new['hp']).replace(' ', '')):
        errs.append(f'{mid}: hp {new["hp"]!r}')
    atks = new.get('attacks', old.get('attacks') or [])
    if 'attacks' in new:
        by_name = {a.get('name'): a for a in atks if isinstance(a, dict)}
        for a in old.get('attacks') or []:
            n = a.get('name')
            if n not in by_name:
                errs.append(f'{mid}: attack {n!r} removed or renamed')
                continue
            lost = set(a) - set(by_name[n])
            if lost:
                errs.append(f'{mid}: attack {n!r} lost keys {sorted(lost)}')
        old_names = {a.get('name') for a in old.get('attacks') or []}
        for a in atks:
            if not DICE.match(str(a.get('damage', '')).replace(' ', '')):
                errs.append(f'{mid}: attack {a.get("name")!r} damage {a.get("damage")!r}')
            if a.get('name') not in old_names:
                for k in ('name', 'damage', 'type', 'delivery'):
                    if not a.get(k):
                        errs.append(f'{mid}: new attack {a.get("name")!r} has no {k}')
            if a.get('effect') and not (0 < float(a.get('effect_chance', 0) or 0) <= 1):
                errs.append(f'{mid}: attack {a.get("name")!r} effect_chance {a.get("effect_chance")!r}')
    op = new.get('opener')
    if op is not None:
        names = {a.get('name'): a for a in atks}
        if not isinstance(op, dict) or op.get('attack') not in names:
            errs.append(f'{mid}: opener {op!r} names no attack')
        else:
            r = int(op.get('range', 1))
            if not 1 <= r <= 7:
                errs.append(f'{mid}: opener range {r}')
            a = names[op['attack']]
            if r >= 2 and a.get('delivery') not in RANGED and not a.get('ranged'):
                errs.append(f'{mid}: opener range {r} on a {a.get("delivery")!r} blow')
    if 'ai_pattern' in new and new['ai_pattern'] not in AI:
        errs.append(f'{mid}: ai_pattern {new["ai_pattern"]!r}')
    if 'pack_size' in new:
        ps = new['pack_size']
        if not (isinstance(ps, list) and len(ps) == 2 and 1 <= ps[0] <= ps[1] <= 12):
            errs.append(f'{mid}: pack_size {ps!r}')
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('proposals', nargs='+')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args(argv)
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    errs, changes, seen = [], {}, {}
    for p in args.proposals:
        with open(p, encoding='utf-8') as f:
            prop = json.load(f)
        why = prop.get('_why', {})
        for mid, new in prop.items():
            if mid.startswith('_'):
                continue
            if mid in seen:
                errs.append(f'{mid}: in both {seen[mid]} and {p}')
                continue
            seen[mid] = p
            if mid not in data:
                errs.append(f'{mid}: not in monsters.json')
                continue
            if not new:
                continue
            errs += check(mid, data[mid], new, why.get(mid))
            changes[mid] = new
    if errs:
        print(f'{len(errs)} problem(s):')
        for e in errs:
            print('  ', e)
        return 1
    fields = {}
    for new in changes.values():
        for k in new:
            fields[k] = fields.get(k, 0) + 1
    print(f'{len(changes)} monsters change; fields: {dict(sorted(fields.items()))}')
    if not args.write:
        return 0
    for mid, new in changes.items():
        entry = data[mid]
        for k, v in new.items():
            entry[k] = v
    # monsters.json is indent-2 JSON with CRLF line ends and a final one.
    with open(PATH, 'w', encoding='utf-8', newline='') as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False).replace('\n', '\r\n') + '\r\n')
    print('written', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main())
