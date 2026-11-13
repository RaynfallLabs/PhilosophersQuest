"""
Keep named body armours and shields above the common armour of their floor.

Offline tooling.  Usage:

    python tools/balance/rebase_unique_armour.py            # report only
    python tools/balance/rebase_unique_armour.py --write    # gear_rules.json, armor.json, shield.json

Why this exists
---------------
A hero finds about ten pieces of common gear a floor deep down and keeps the
best, so by the middle of the run nearly every hero wears the same "par"
armour: the mean worn AC that monster to-hit is baked against
(tools/balance/rebake_thac0.py).  Brandon, 2026-11-12: "whats the point of
better armor? full plate, uniques, etc. should all be driving better
survivability later."  Measured the same day, most named body armours were
one to five points of AC BELOW a common piece found on their own floor
(Sigurd's dragon mail 7 against 12, the Armor of Ragnarok 9 against 13): the
ladder pass gave a named piece its template's base, and its template is
often scale or a brigandine while the commons there are full plate.  A
legendary find was worse than what the hero already wore.

The rule: a named piece found by depth has AC (base + plus) of at least the
common par of its peak floor plus a margin (2 for body armour, whose par
runs 0-13; 1 for a shield, whose par runs 0-8): gear.named_ac_floor.  It is
never lowered, and starting pieces and quest pieces keep theirs (the ladder
pass's own exemptions, unique_armor_ladder_2026_11.found_by_depth).  The
damage cuts and powers are the piece's own and stay as they are.

What --write does:
  1. measures the par line from the game's own spawn functions over a loot
     census, from nothing worn (as rebake_thac0 measures its line), and
     writes it to data/gear_rules.json `named_ac`;
  2. reruns tools/content/unique_armor_ladder_2026_11.py, which raises a
     plain named piece's base to that floor;
  3. raises a chain-equip piece's every tier by the same amount, so its top
     tier meets the floor and its ladder keeps its shape.
After a change to the armour spawn bells or levels, rerun this AND
rebake_thac0.py.
"""
from __future__ import annotations

import json
import os
import random
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools" / "content"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ARMOR_JSON = ROOT / "data" / "items" / "armor.json"
SHIELD_JSON = ROOT / "data" / "items" / "shield.json"
RULES_JSON = ROOT / "data" / "gear_rules.json"
MARGIN = {'body': 2, 'shield': 1}
SHARE_FOUND = 0.90          # as rebake_thac0
SPLIT = {'weapon': 0.45, 'armour': 0.45, 'shield': 0.10}


def par_line(runs: int = 300, seed: int = 3) -> dict:
    """{'body': [floor 1..100 mean AC], 'shield': [...]}, never falling."""
    import items
    from armor_model import load_census, _poisson
    census = load_census(None)
    rng = random.Random(seed)
    slots = list(items.ARMOR_SLOTS)
    bod = {f: [] for f in range(1, 101)}
    shl = {f: [] for f in range(1, 101)}
    for _ in range(runs):
        body = shield = 0
        for f in range(1, 101):
            for _i in range(_poisson(rng, census[f][0] * SHARE_FOUND)):
                r = rng.random()
                if r < SPLIT['weapon']:
                    continue
                if r < SPLIT['weapon'] + SPLIT['shield']:
                    s = items.pick_random_shield_for_floor(f, rng)
                    if s is not None:
                        shield = max(shield, s.ac_bonus + s.enchant_bonus)
                    continue
                if rng.choice(slots) != 'body':
                    continue
                a = items.pick_random_armor_for_floor(f, rng, slot='body')
                if a is not None:
                    body = max(body, a.ac_bonus + a.enchant_bonus)
            bod[f].append(body)
            shl[f].append(shield)
    out = {}
    for kind, data in (('body', bod), ('shield', shl)):
        line, hi = [], 0.0
        for f in range(1, 101):
            hi = max(hi, statistics.mean(data[f]))
            line.append(round(hi, 1))
        out[kind] = line
    return out


def write_rules(par: dict) -> None:
    """Put (or replace) the `named_ac` block at the end of gear_rules.json,
    leaving the hand-aligned rest of the file alone."""
    text = RULES_JSON.read_text(encoding='utf-8')
    block = (
        '  "named_ac": {\n'
        '    "_doc": "The least AC (base + plus) a named body armour or shield found by depth gives: the common par of its peak floor (the mean a hero wears there, from nothing worn, by the game\'s own spawns) plus the margin. Written by tools/balance/rebase_unique_armour.py; read by gear.named_ac_floor and the named-armour ladder pass. Starting and quest pieces keep their own.",\n'
        f'    "margin": {{"body": {MARGIN["body"]}, "shield": {MARGIN["shield"]}}},\n'
        f'    "par_body":   {json.dumps(par["body"])},\n'
        f'    "par_shield": {json.dumps(par["shield"])}\n'
        '  }'
    )
    if '"named_ac"' in text:
        text = re.sub(r'  "named_ac": \{.*?\n  \}', lambda _m: block, text, flags=re.S)
    else:
        i = text.rstrip().rfind('}')
        head = text[:i].rstrip()
        text = head + ',\n\n' + block + '\n}\n'
    json.loads(text)                         # still valid JSON
    RULES_JSON.write_text(text, encoding='utf-8', newline='\n')


def chain_plan(armor: dict, shields: dict) -> list:
    """[(file, id, floor, old AC, new AC)] for chain-equip pieces to raise."""
    import gear
    import unique_armor_ladder_2026_11 as ua
    out = []
    for fname, data, kind in (('armor', armor, 'body'), ('shield', shields, 'shield')):
        for iid, d in data.items():
            if not d.get('is_unique') or not d.get('equip_chain_mode'):
                continue
            if kind == 'body' and d.get('slot', 'body') != 'body':
                continue
            if not ua.found_by_depth(d, iid):
                continue
            old = int(d.get('ac_bonus', 0) or 0) + int(d.get('enchant_bonus', 0) or 0)
            new = gear.named_ac_floor(kind, int(d['peak_floor']))
            if old < new:
                out.append((fname, iid, int(d['peak_floor']), old, new))
    return out


def main(argv: list[str]) -> int:
    import gear
    import jsonfmt
    import unique_armor_ladder_2026_11 as ua
    par = par_line()
    for kind in ('body', 'shield'):
        print(f"par {kind:6} " + '  '.join(f"F{f} {par[kind][f - 1]:.1f}"
                                          for f in (1, 10, 20, 40, 60, 80, 100)))
    if "--write" not in argv:
        print("(report only: --write puts the par line in gear_rules.json and applies it)")
        return 0
    write_rules(par)
    gear.rules.cache_clear()
    ua.main([])
    armor, afmt = jsonfmt.load(ARMOR_JSON)
    shields, sfmt = jsonfmt.load(SHIELD_JSON)
    changes = chain_plan(armor, shields)
    for fname, iid, f, old, new in changes:
        d = (armor if fname == 'armor' else shields)[iid]
        delta = new - old
        d['ac_bonus'] = int(d.get('ac_bonus', 0) or 0) + delta
        for tier in (d.get('tier_bonuses') or {}).values():
            if isinstance(tier, dict) and 'ac_bonus' in tier:
                tier['ac_bonus'] = int(tier['ac_bonus']) + delta
        print(f"  chain {fname:6} F{f:3}  {iid:34} AC {old:3} -> {new:3}")
    jsonfmt.save(ARMOR_JSON, armor, afmt)
    jsonfmt.save(SHIELD_JSON, shields, sfmt)
    print(f"wrote {RULES_JSON}, {ARMOR_JSON} and {SHIELD_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
