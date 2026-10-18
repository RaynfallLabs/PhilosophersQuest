"""Band analysis of the monster catalog (MONSTER_CATALOG_AUDIT.md).

Offline tooling. Prints the audit's markdown tables for a monsters.json:

    python tools/balance/monster_catalog_bands.py [path/to/monsters.json] [--deep]

It mirrors dungeon._build_spawn_pool exactly (bell around peak_floor, the
min_level gate, the 0.005 cut, the 0.02 floor weight), takes every monster's
share of each floor's pool and averages the shares over the ten floors of a
band. "Effective faces" is exp(Shannon entropy) of a band's shares: how many
equally common monsters would give the same variety. --deep adds the per-kind
lists for floors 61-100 that the late-game judgement was made from.

Threat traits are read from the data the same way the audit read them (an
attack named with a ranged word or flagged `ranged`, the caster tag, each
attack's `effect`), plus the 2026-10 mechanics: steal, splits, disguise.
"""
from __future__ import annotations

import collections
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_RANGED_WORDS = {'shoot', 'arrow', 'bolt', 'dart', 'spit', 'hurl',
                 'volley', 'ray', 'blast', 'breath', 'spike', 'gaze',
                 'song', 'wail', 'charm', 'psionic', 'disintegrat',
                 'cast', 'bow', 'sling', 'javelin', 'spore', 'shock', 'hex'}

STATUS = {
    'poison': {'poisoned', 'diseased'},
    'paralysis/hold': {'paralyzed', 'frozen', 'sleeping', 'stunned', 'immobilized'},
    'fear': {'feared'}, 'confusion': {'confused', 'hallucinating'},
    'blind': {'blinded'}, 'slow': {'slowed'}, 'weaken': {'weakened'},
    'bleed/burn': {'bleeding', 'burning'}, 'silence': {'silenced'}, 'teleport': {'teleportitis'},
}
ELEM = {'fire', 'cold', 'lightning', 'poison', 'acid', 'magic', 'drain', 'shadow', 'necrotic', 'holy'}
FORMS = {'slash', 'pierce', 'blunt'}


def traits(v: dict) -> set:
    t = set()
    atks = v.get('attacks') or []

    def is_r(a):
        return a.get('ranged') or any(w in a.get('name', '').lower() for w in _RANGED_WORDS)
    if any(not is_r(a) for a in atks):
        t.add('melee')
    if v.get('ai_pattern') in ('ranged', 'dragon') or any(is_r(a) for a in atks):
        t.add('ranged')
    if 'caster' in (v.get('tags') or []) or any(a.get('type') in ('magic', 'psionic') for a in atks):
        t.add('caster')
    effs = {a.get('effect') for a in atks if a.get('effect') and (a.get('effect_chance') or 0) > 0}
    for cat, s in STATUS.items():
        if effs & s:
            t.add('st:' + cat)
    if any(a.get('type') == 'drain' for a in atks) or v.get('drain_heals_self') or v.get('sp_drain'):
        t.add('st:drain')
    if v.get('gaze_paralyze'):
        t.add('st:paralysis/hold')
    if any(a.get('steal') for a in atks):
        t.add('st:steal')
    if any(x.startswith('st:') for x in t):
        t.add('any_status')
    if v.get('summon_kind') or v.get('ai_pattern') == 'summoner':
        t.add('summon')
    if v.get('ai_pattern') in ('ambush', 'mimic'):
        t.add('stealth')
    if v.get('can_phase_walls') or v.get('can_phase_blink') or v.get('ai_pattern') == 'hit_and_run':
        t.add('phase/blink')
    if v.get('regeneration') or v.get('ai_pattern') == 'healer':
        t.add('regen/heal')
    res = set(v.get('resistances') or [])
    if res & FORMS:
        t.add('resist_weapon_form')
    if len(res & ELEM) >= 3:
        t.add('resist_3+_elements')
    t.add('swarm' if v.get('pack') else 'solo')
    if v.get('splits'):
        t.add('splits')
    if v.get('invisible'):
        t.add('invisible')
    return t


def pool(defs: dict, level: int) -> dict:
    out = {}
    for k, v in defs.items():
        pw = v.get('peak_weight', 0) or 0
        if pw <= 0 or v.get('min_level', 1) > level:
            continue
        pf = v.get('peak_floor', v.get('min_level', 1))
        sp = max(1, v.get('spread', 10))
        bell = math.exp(-((level - pf) ** 2) / (2 * sp ** 2))
        if bell < 0.005:
            continue
        out[k] = max(0.02, pw * bell)
    return out


def bands(defs: dict) -> list[dict]:
    rows = []
    for lo, hi in [(i * 10 + 1, i * 10 + 10) for i in range(10)]:
        share = collections.Counter()
        for f in range(lo, hi + 1):
            p = pool(defs, f)
            tot = sum(p.values())
            for k, w in p.items():
                share[k] += w / tot / (hi - lo + 1)
        H = -sum(s * math.log(s) for s in share.values() if s > 0)
        pat, tr, patn = collections.Counter(), collections.Counter(), collections.Counter()
        for k, s in share.items():
            v = defs[k]
            pat[v['ai_pattern']] += s
            if s >= 0.005:
                patn[v['ai_pattern']] += 1
            for t in traits(v):
                tr[t] += s
        rows.append(dict(band=f'{lo}-{hi}', any=len(share), ge1=sum(s >= 0.01 for s in share.values()),
                         eff=math.exp(H), top3=sum(s for _, s in share.most_common(3)),
                         pat=pat, patn=patn, tr=tr, share=share,
                         top=[(defs[k]['name'], s) for k, s in share.most_common(5)]))
    return rows


def pct(x: float) -> str:
    return f'{100 * x:.0f}' if x >= 0.005 else ('<1' if x > 0 else '0')


PATS = ['aggressive', 'ranged', 'ambush', 'mimic', 'hit_and_run', 'summoner', 'healer',
        'dancer', 'sessile', 'cowardly']
THREATS = [('melee', 'Melee'), ('ranged', 'Ranged'), ('caster', 'Caster'), ('any_status', 'Any status'),
           ('summon', 'Summon'), ('stealth', 'Stealth (ambush/mimic)'), ('invisible', 'Invisible'),
           ('phase/blink', 'Phase/blink'), ('regen/heal', 'Regen/heal'), ('swarm', 'Swarm (pack)'),
           ('splits', 'Splits'), ('resist_weapon_form', 'Resists a weapon form'),
           ('resist_3+_elements', 'Resists 3+ elements')]
STATUSES = [('st:poison', 'Poison/disease'), ('st:paralysis/hold', 'Paralysis/stun/hold/sleep'),
            ('st:drain', 'Drain'), ('st:fear', 'Fear'), ('st:confusion', 'Confusion'),
            ('st:blind', 'Blind'), ('st:slow', 'Slow'), ('st:weaken', 'Weaken'),
            ('st:bleed/burn', 'Bleed/burn'), ('st:silence', 'Silence'), ('st:teleport', 'Teleportitis'),
            ('st:steal', 'Steal')]


def markdown(rows: list[dict]) -> str:
    out = ['### Faces per band\n',
           '| Band | Eligible kinds | Kinds at >=1% of spawns | Effective faces | Top 3 kinds share | Most common |',
           '|---|---|---|---|---|---|']
    for r in rows:
        out.append(f"| {r['band']} | {r['any']} | {r['ge1']} | {r['eff']:.0f} | {pct(r['top3'])}% | "
                   + ', '.join(f'{n} {pct(s)}%' for n, s in r['top'][:3]) + ' |')
    out += ['\n### AI pattern mix (share of spawns, %; kinds at >=0.5% in brackets)\n',
            '| Band | ' + ' | '.join(PATS) + ' | other |', '|---|' + '---|' * (len(PATS) + 1)]
    for r in rows:
        other = 1 - sum(r['pat'][p] for p in PATS)
        out.append(f"| {r['band']} | " + ' | '.join(f"{pct(r['pat'][p])} ({r['patn'][p]})" for p in PATS)
                   + f' | {pct(other)} |')
    out += ['\n### Threat types (share of spawns carrying it, %)\n',
            '| Band | ' + ' | '.join(n for _, n in THREATS) + ' |', '|---|' + '---|' * len(THREATS)]
    for r in rows:
        out.append(f"| {r['band']} | " + ' | '.join(pct(r['tr'][k]) for k, _ in THREATS) + ' |')
    out += ['\n### Status effects (share of spawns that can inflict it, %)\n',
            '| Band | ' + ' | '.join(n for _, n in STATUSES) + ' |', '|---|' + '---|' * len(STATUSES)]
    for r in rows:
        out.append(f"| {r['band']} | " + ' | '.join(pct(r['tr'][k]) for k, _ in STATUSES) + ' |')
    return '\n'.join(out)


def deep(defs: dict, rows: list[dict]) -> str:
    out = []
    for r in rows[6:]:
        out.append(f"\n{r['band']}: effective faces {r['eff']:.1f}")
        for k, s in r['share'].most_common():
            if s < 0.004:
                break
            v = defs[k]
            out.append(f"  {100 * s:5.1f}%  {v['name']:<28} {v['ai_pattern']:<12} "
                       + ','.join(sorted(t[3:] for t in traits(v) if t.startswith('st:'))))
    return '\n'.join(out)


def main(argv: list[str]) -> int:
    paths = [a for a in argv if not a.startswith('--')]
    path = Path(paths[0]) if paths else ROOT / 'data' / 'monsters.json'
    defs = json.loads(path.read_text(encoding='utf-8'))
    rows = bands(defs)
    print(markdown(rows))
    if '--deep' in argv:
        print(deep(defs, rows))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
