"""Armour redesign model: Monte Carlo runs of the plan in
docs/design/ARMOR_REDESIGN_PLAN.md, on the game's own data.

Brandon, 2026-11-07: "tier and pace should be tested via simulation and math;
standard deviations for RNG ... make the math work, deep dive on standard
deviations and find the right balance."

What it reads (never writes):
  * the monster spawn pool of every floor (dungeon._build_spawn_pool: the
    game's own bell weights), every monster's attacks, damage dice, riders
    (effect, chance, duration) and THAC0;
  * floor_curve.HEALTH_BAR (a steady hero's max HP) and ONE_ATTACK (one
    weapon chain's damage) by floor;
  * the armour and shield templates (data/templates);
  * how much gear and how many rings a run finds per floor (a loot census
    output, `tools/balance/loot_census.py --runs 8 --floors 1-100 > file`,
    passed as --census; without it a built-in copy of the 2026-11-07 census
    is used).

What it simulates: N runs of floors 1-100 under the proposal's parameters
(the PROPOSAL dict): every common gear find split weapon / armour / shield,
armour spread over the eight armour slots, a template, a plain-or-enchanted
roll and a tier from the depth bells; the hero keeps the best body armour
and shield, the best protection source (ring or cloak of Protection), and
the best enchantment tier per minor slot.

What it reports (mean, standard deviation, 10th and 90th percentiles across
runs): worn AC by floor; the floor-by-floor hit chance of that floor's
monsters once their THAC0 is rebaked to the AC line; the longest stretch
with no AC upgrade; enchanted options per minor slot per 10 floors; the
floor each tier first reaches a slot; and every enchantment's value in one
currency, the AC point (the expected damage one point of AC turns away on
that floor), with the magnitude each ladder needs to hit its tier's target.

    python tools/balance/armor_model.py                 # the report, 2000 runs
    python tools/balance/armor_model.py --runs 5000 --seed 7
    python tools/balance/armor_model.py --census scratch/census_8x100.txt
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import statistics
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import floor_curve  # noqa: E402

FLOORS = range(1, 101)
BANDS = [range(b * 10 + 1, b * 10 + 11) for b in range(10)]
MINOR_SLOTS = ('head', 'arms', 'hands', 'legs', 'feet', 'cloak', 'shirt')
ARMOUR_SLOTS = ('body',) + MINOR_SLOTS

# ---------------------------------------------------------------- proposal
# Everything the plan sets, in one place, so a tuning pass changes numbers
# here and nowhere else.
PROPOSAL = {
    # Enchantment tier bells: peak floor, spread, first floor.
    'tier_peak':   (6, 26, 46, 66, 86),
    'tier_spread': (9, 11, 11, 11, 11),
    'tier_first':  (1, 12, 30, 50, 70),
    # Share of found pieces with no enchantment: start - slope*(floor-1), floor end.
    'plain_start': 0.40, 'plain_slope': 0.0025, 'plain_end': 0.15,
    # Common gear split (ruling 6: "closer to 45/45/10").
    'split': {'weapon': 0.45, 'armour': 0.45, 'shield': 0.10},
    # Body and shield base AC by template (heavier is better; section 4).
    'body_ac': {'padded': 1, 'leather': 2, 'studded_leather': 3, 'hide': 3,
                'chain_shirt': 3, 'ringmail': 3, 'scale': 4, 'chainmail': 5,
                'breastplate': 5, 'banded': 6, 'splint': 6, 'plate': 7,
                'full_plate': 8},
    'shield_ac': {'buckler': 1, 'light_wooden': 1, 'heavy_wooden': 2,
                  'kite_shield': 2, 'tower_shield': 3},
    # Which weight class of template a find is, by depth: (peak, spread, first
    # floor). A piece's template is drawn by its class's bell (LORE NOT FLOOR:
    # the depth picks what is found, never how strong it is). Plate on floor
    # 3 was the early-AC spike of the first pass.
    'class_bell': {'light': (1, 30, 1), 'medium': (22, 20, 4), 'heavy': (50, 25, 12)},
    'shield_class': {'buckler': 'light', 'light_wooden': 'light',
                     'heavy_wooden': 'medium', 'kite_shield': 'medium',
                     'tower_shield': 'heavy'},
    # The plus a tier gives body armour and shields.
    'plus': (1, 2, 3, 4, 5),
    # Protection source: the best ring of Protection (the first pass also had
    # a cloak of Protection; at a whole AC point a plus it priced 3-5x any
    # other cloak enchantment, so it is a ring only).
    # Revision 3: no AC from rings at all. Priced in section 8, a +1 AC ring
    # (1.0 AC point, every attack) outclasses every other ring; the ring of
    # Protection becomes AD&D's other half, saving throws (every rider).
    # AC = 10 - body - shield - DEX.
    'protection_ac': (0, 0, 0, 0, 0),
    'ring_kinds': 11,          # common ring kinds after ruling 4 (Protection is one)
    'rings_worn': 2,
    'share_found': 0.90,       # of what a floor holds, the hero picks up
    # Monster accuracy rebake: THAC0 = line(peak floor) + 10 + c*(own offset).
    'thac0_spread_keep': 0.5,
    'hit_floor': 0.05,         # ruling 7: the natural 20
}

# Today's loot per floor (2026-11-07 census, 5 runs: common gear, rings),
# used when no --census file is given. Interpolated between these floors.
_CENSUS_DEFAULT = {
    1: (3.4, 0.38), 5: (4.1, 1.0), 10: (4.2, 1.0), 15: (8.9, 1.25),
    20: (8.0, 1.1), 25: (10.0, 0.75), 30: (9.0, 0.6), 40: (9.5, 0.8),
    50: (10.0, 0.8), 60: (10.0, 0.8), 70: (10.5, 0.8), 80: (10.0, 0.8),
    90: (9.5, 0.8), 100: (8.5, 0.8),
}


def _interp(anchors: dict, f: float) -> float:
    ks = sorted(anchors)
    if f <= ks[0]:
        return anchors[ks[0]]
    for a, b in zip(ks, ks[1:]):
        if a <= f <= b:
            return anchors[a] + (anchors[b] - anchors[a]) * (f - a) / (b - a)
    return anchors[ks[-1]]


def load_census(path: str | None) -> dict:
    """{floor: (common gear, rings)} from a loot_census report, or the default."""
    if not path or not os.path.exists(path):
        return {f: (_interp({k: v[0] for k, v in _CENSUS_DEFAULT.items()}, f),
                    _interp({k: v[1] for k, v in _CENSUS_DEFAULT.items()}, f)) for f in FLOORS}
    out = {}
    head = None
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            cols = line.split()
            if cols[:2] == ['F', 'chests']:
                head = cols
                continue
            if head and cols and cols[0].isdigit() and len(cols) == len(head):
                row = dict(zip(head, cols))
                try:
                    out[int(row['F'])] = (float(row['gear']), float(row['ring']))
                except (KeyError, ValueError):
                    pass
            if cols[:1] == ['sum']:
                head = None
    return out if len(out) >= 90 else load_census(None)


# ------------------------------------------------------------------ templates

def load_templates() -> dict:
    """{slot: [(template id, weight class)]} for armour; 'shield': [...]."""
    out = {s: [] for s in ARMOUR_SLOTS}
    out['shield'] = []
    tdir = os.path.join(ROOT, 'data', 'templates')
    for fn in sorted(os.listdir(os.path.join(tdir, 'armor'))):
        if fn.endswith('.json'):
            t = json.load(open(os.path.join(tdir, 'armor', fn), encoding='utf-8'))
            out[t['slot']].append((fn[:-5], t.get('armor_class_tier', 'light')))
    for fn in sorted(os.listdir(os.path.join(tdir, 'shields'))):
        if fn.endswith('.json'):
            out['shield'].append((fn[:-5], None))
    return out


# --------------------------------------------------------------- enchantments

def plain_share(f: int, P=PROPOSAL) -> float:
    return max(P['plain_end'], P['plain_start'] - P['plain_slope'] * (f - 1))


def tier_weights(f: int, P=PROPOSAL) -> list:
    w = []
    for t in range(5):
        if f < P['tier_first'][t]:
            w.append(0.0)
        else:
            d = f - P['tier_peak'][t]
            w.append(math.exp(-(d * d) / (2 * P['tier_spread'][t] ** 2)))
    s = sum(w) or 1.0
    return [x / s for x in w]


def roll_tier(rng, f, P=PROPOSAL) -> int:
    """0 = plain, 1-5 = tier I-V."""
    if rng.random() < plain_share(f, P):
        return 0
    r, acc = rng.random(), 0.0
    for t, x in enumerate(tier_weights(f, P), 1):
        acc += x
        if r <= acc:
            return t
    return 5


# ----------------------------------------------------------------- simulation

def simulate(runs: int, seed: int, census: dict, P=PROPOSAL, templates=None) -> dict:
    """Run the proposal `runs` times. Returns per-run arrays."""
    templates = templates or load_templates()
    rng = random.Random(seed)
    sp = P['split']
    ac_runs, opts_runs, first_tier_runs, plateau_runs, any_runs = [], [], [], [], []
    for _ in range(runs):
        body = shield = prot = 0
        any_up, upgraded = [], False
        best_minor = {s: 0 for s in MINOR_SLOTS}
        first = {s: [None] * 6 for s in MINOR_SLOTS}
        opts = {s: [0] * 10 for s in MINOR_SLOTS}
        ac_by_floor = []
        for f in FLOORS:
            gear_mu, ring_mu = census[f]
            n = _poisson(rng, gear_mu * P['share_found'])
            for _i in range(n):
                r = rng.random()
                if r < sp['weapon']:
                    continue
                tier = roll_tier(rng, f, P)
                if r < sp['weapon'] + sp['shield']:
                    tpl = _pick_template(rng, templates['shield'], f, P, shield=True)
                    ac = P['shield_ac'][tpl] + (P['plus'][tier - 1] if tier else 0)
                    if ac > shield:
                        shield = ac
                        upgraded = True
                    continue
                slot = rng.choice(ARMOUR_SLOTS)
                tpl = _pick_template(rng, templates[slot], f, P)
                if slot == 'body':
                    ac = P['body_ac'][tpl] + (P['plus'][tier - 1] if tier else 0)
                    if ac > body:
                        body = ac
                        upgraded = True
                    continue
                if tier:
                    opts[slot][(f - 1) // 10] += 1
                    if tier > best_minor[slot]:
                        best_minor[slot] = tier
                        upgraded = True
                    for t in range(1, tier + 1):
                        if first[slot][t] is None:
                            first[slot][t] = f
            # Rings: one kind of P['ring_kinds'] is Protection; tiers by the same bells.
            for _i in range(_poisson(rng, ring_mu * P['share_found'])):
                if rng.random() < 1.0 / P['ring_kinds']:
                    t = roll_tier(rng, f, P) or 1
                    if P['protection_ac'][t - 1] > prot:
                        prot = P['protection_ac'][t - 1]
                        upgraded = True
            ac_by_floor.append(10 - body - shield - prot)
            any_up.append(upgraded)
            upgraded = False
        ac_runs.append(ac_by_floor)
        opts_runs.append(opts)
        first_tier_runs.append(first)
        # Longest stretch of floors (5-100) with no AC upgrade, and with no
        # upgrade of any kind (AC, or a minor slot's tier).
        plateau_runs.append(_longest_gap([ac_by_floor[i] < ac_by_floor[i - 1]
                                          for i in range(4, 100)]))
        any_runs.append(_longest_gap(any_up[4:100]))
    return {'ac': ac_runs, 'opts': opts_runs, 'first': first_tier_runs,
            'plateau': plateau_runs, 'any_gap': any_runs}


def _longest_gap(flags) -> int:
    gap = longest = 0
    for up in flags:
        gap = 0 if up else gap + 1
        longest = max(longest, gap)
    return longest


def _class_weight(cls, f, P) -> float:
    peak, spread, first = P['class_bell'][cls or 'light']
    if f < first:
        return 0.0
    return math.exp(-((f - peak) ** 2) / (2 * spread ** 2))


def _pick_template(rng, options, f, P, shield=False) -> str:
    """A template for a find on floor f, drawn by its weight class's bell."""
    ws = []
    for tpl, cls in options:
        if shield:
            cls = P['shield_class'][tpl]
        ws.append(_class_weight(cls, f, P))
    tot = sum(ws)
    if tot <= 0:
        return options[0][0]
    r, acc = rng.random() * tot, 0.0
    for (tpl, _c), x in zip(options, ws):
        acc += x
        if r <= acc:
            return tpl
    return options[-1][0]


def _poisson(rng, mu: float) -> int:
    if mu <= 0:
        return 0
    L, k, p = math.exp(-mu), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def _stats(xs) -> tuple:
    xs = sorted(xs)
    n = len(xs)
    mean = sum(xs) / n
    sd = statistics.pstdev(xs) if n > 1 else 0.0
    return mean, sd, xs[int(0.10 * (n - 1))], xs[int(0.50 * (n - 1))], xs[int(0.90 * (n - 1))]


# -------------------------------------------------------------- monster model

_DELIVERY_RULES = [
    ('breath', r'breath|spit|spray|exhal'),
    ('gaze', r'gaze|stare|glare'),
    ('voice', r'wail|scream|shriek|howl|song|roar|mind|psych|charm|hex|curse|whisper'),
    ('touch', r'touch|drain|pseudopod|engulf'),
    ('bite', r'bite|fang|maw|jaws'),
    ('sting', r'sting|stinger|tail'),
    ('trample', r'trample|stomp|sweep|charge|gore|ram\b'),
    ('grapple', r'constrict|crush|grab|grapple|squeeze|tentacle|hug|wrap'),
]
_RANGED = r'bolt|ray|shard|hurl|arrow|volley|throw|javelin|missile'


def delivery(atk: dict) -> str:
    """How an attack lands (plan section 7.1). The build writes this into
    monsters.json; here it is read from the name, `ranged` and type."""
    n = str(atk.get('name', '')).lower()
    if re.search(_DELIVERY_RULES[0][1], n):
        return 'breath'
    if atk.get('ranged') or re.search(_RANGED, n):
        return 'ranged'
    for d, pat in _DELIVERY_RULES[1:]:
        if re.search(pat, n) or (d == 'voice' and atk.get('type') == 'psionic'):
            return d
    return 'blow'


def dice_mean(expr) -> float:
    s = str(expr or '0').replace(' ', '')
    m = re.fullmatch(r'(\d*)d(\d+)([+-]\d+)?', s)
    if m:
        n = int(m.group(1) or 1)
        return n * (int(m.group(2)) + 1) / 2 + int(m.group(3) or 0)
    try:
        return float(s)
    except ValueError:
        return 0.0


# What a rider costs, in turns of incoming harm ("lost" = the hero's turn is
# gone and the monsters swing free) or in health-bar shares per turn (DoT).
# The coefficients are judgements; --sensitivity varies them by half.
RIDER_COST = {
    'paralyzed': ('lost', 1.0), 'stunned': ('lost', 1.0), 'sleeping': ('lost', 1.0),
    'frozen': ('lost', 1.0), 'immobilized': ('lost', 0.3), 'slowed': ('lost', 0.5),
    'confused': ('lost', 0.3), 'feared': ('lost', 0.5), 'blinded': ('lost', 0.25),
    'weakened': ('lost', 0.2), 'hallucinating': ('lost', 0.1), 'silenced': ('lost', 0.1),
    'teleportitis': ('lost', 0.0),
    'poisoned': ('dot', 0.02), 'burning': ('dot', 0.02), 'bleeding': ('dot', 0.03),
    'diseased': ('dot', 0.02),
}


def floor_model(f: int, ac: float, line_ac, pool_cache: dict, scale=1.0):
    """The floor's monster attacks as a list of dicts with the expected harm
    of each to a hero wearing `ac`, after the THAC0 rebake to `line_ac`."""
    import dungeon
    if f not in pool_cache:
        pool_cache[f] = dungeon._build_spawn_pool(f)
    pool = pool_cache[f]
    hb = floor_curve.health_bar(f)
    one = floor_curve.one_attack(f)
    # Median current THAC0 at each monster's peak floor keeps relative accuracy.
    attacks = []
    for mid, m in pool.items():
        w = float(m['_spawn_freq'])
        atks = m.get('attacks') or []
        if not atks:
            continue
        hp = dice_mean(m.get('hp')) or floor_curve.target_hp(f)
        turns = max(1.0, hp / max(1.0, one))
        pf = int(m.get('peak_floor') or m.get('min_level') or f)
        offset = float(m.get('thac0', 20)) - _median_thac0(pf)
        thac0 = line_ac(pf) + 10 + PROPOSAL['thac0_spread_keep'] * offset
        for a in atks:
            attacks.append({
                'w': w * turns / len(atks), 'm': mid, 'delivery': delivery(a),
                'type': a.get('type', 'physical'), 'dmg': dice_mean(a.get('damage')),
                'effect': a.get('effect'), 'chance': float(dice_mean(a.get('effect_chance'))),
                'dur': dice_mean(a.get('effect_duration')), 'thac0': thac0,
            })
    # Expected harm per monster turn without riders, for the "lost turn" cost.
    tot_w = sum(a['w'] for a in attacks) or 1.0
    for a in attacks:
        a['p'] = _hit_p(a['thac0'], ac)
    per_turn = sum(a['w'] * a['p'] * a['dmg'] for a in attacks) / tot_w
    for a in attacks:
        a['rider'] = _rider_cost(a, per_turn, hb, scale)
    return attacks, hb


def _hit_p(thac0, ac) -> float:
    return min(0.95, max(PROPOSAL['hit_floor'], (21 - (thac0 - ac)) / 20.0))


def _rider_cost(a, per_turn, hb, scale) -> float:
    eff = a['effect']
    if not eff or eff not in RIDER_COST:
        return 0.0
    kind, k = RIDER_COST[eff]
    k *= scale
    dur = max(1.0, a['dur'])
    if kind == 'lost':
        return a['chance'] * k * dur * per_turn
    return a['chance'] * k * hb * dur


_THAC0_MED = {}


def _median_thac0(pf: int) -> float:
    if not _THAC0_MED:
        mons = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
        by = {}
        for m in mons.values():
            p = int(m.get('peak_floor') or m.get('min_level') or 1)
            by.setdefault(min(9, (p - 1) // 10), []).append(float(m.get('thac0', 20)))
        for b, v in by.items():
            _THAC0_MED[b] = statistics.median(v)
    return _THAC0_MED.get(min(9, (max(1, pf) - 1) // 10), 20.0)


def ehl(attacks, guard=None) -> float:
    """Expected harm per weighted monster turn (damage + rider cost), with an
    optional guard(a) -> (share of damage kept, share of rider kept)."""
    tot = 0.0
    for a in attacks:
        dk, rk = guard(a) if guard else (1.0, 1.0)
        tot += a['w'] * a['p'] * (a['dmg'] * dk + a['rider'] * rk)
    return tot


def ac_point(attacks) -> float:
    """The harm one point of AC turns away (each hit chance down 0.05)."""
    tot = 0.0
    for a in attacks:
        if PROPOSAL['hit_floor'] < a['p'] < 0.95:
            tot += a['w'] * 0.05 * (a['dmg'] + a['rider'])
    return tot


# The stable's guard and might ladders, as what each one touches (plan 7.2).
# kind: 'rider' (shrug off listed riders from listed deliveries), 'damage'
# (turn aside a share of listed deliveries' damage), 'element' (a damage
# type from every source, and its rider), 'parry' (melee blows), 'might'
# (more damage: fights shorter by x/(1+x)), 'ac' (protection, defense).
# Revision 3 (after the first pass priced revision 2's narrow guards: six of
# them could not reach a fifth of an AC point even at 100%, because what they
# guard is too rare where they are found). Every guard now covers a FAMILY:
#   ('riders', {riders}, None or {deliveries})  shrug those riders off
#   ('delivery', {deliveries})                  turn aside those attacks'
#                                               damage AND their riders
#   ('element', {damage types}, {riders})       a damage type from every
#                                               source, and its riders
#   ('parry',) a landed melee blow parried      ('might',) more damage
_MIND = {'confused', 'feared', 'hallucinating', 'sleeping'}
_LOCK = {'paralyzed', 'immobilized', 'frozen'}
_PACE = {'slowed', 'immobilized', 'frozen'}
_BLOOD = {'poisoned', 'diseased', 'bleeding', 'weakened'}
#   ('combo', {deliveries}, {riders})          those deliveries' damage and
#                                               riders, AND those riders from
#                                               any other attack
# The second pass (narrow single-family guards) priced the head, feet and
# shirt guards under a fifth of an AC point at tier V; a slot guard has to
# own its whole theme to be worth a slot. The roster below is the result.
STABLE = {
    'head': {
        'Iron Will (voice, gaze; mind, stun, blind riders)':
            ('combo', {'voice', 'gaze'}, _MIND | {'stunned', 'blinded'}),
    },
    'hands': {
        'Life-Grip (touch, grapple; paralysis, holds)':
            ('combo', {'touch', 'grapple'}, _LOCK),
        'Striking (your damage)': ('might',),
    },
    'arms': {
        'Deflection (ranged; their riders)': ('combo', {'ranged'}, set()),
        'Parrying (melee blows)': ('parry',),
    },
    'legs': {
        'Mailed Shins (bites, stings; poison, disease)':
            ('combo', {'bite', 'sting'}, {'poisoned', 'diseased'}),
    },
    'feet': {
        # Footing: what comes at you low and what pins you to the ground.
        'Free Stride (trample; slowed, held, frozen; knocked down)':
            ('multi', [('combo', {'trample'}, _PACE), ('riders', {'stunned'}, {'blow'})]),
    },
    'cloak': {
        'Elementward (fire, cold, lightning, acid)':
            ('element', {'fire', 'cold', 'lightning', 'acid'}, {'burning', 'frozen'}),
        'Vapourward (breath; burning, frozen)': ('combo', {'breath'}, {'burning', 'frozen'}),
    },
    'shirt': {
        # What gets under the armour: poison, drain and necrotic damage from
        # any source, and the riders that work on the blood.
        'Vigor (poison, drain, necrotic; blood riders)':
            ('element', {'poison', 'drain', 'necrotic'}, _BLOOD),
    },
}

# Rings after ruling 4 (the iconic powers moved to gear): priced on the
# same scale, so a ring of Protection is balanced against the others.
RING_STABLE = {
    # For comparison only: why a ring gives no AC (one AC point, every attack).
    '(a +1 AC ring, for comparison)': ('ac',),
    # The rings that stay rings (elements went to the cloak, free action to
    # gloves and boots, the mind to the helm: one home per power).
    'Protection (saving throws: every rider, any attack)':
        ('riders', set(RIDER_COST), None),
    'Spell Turning (magic, shadow, psionic damage)':
        ('element', {'magic', 'shadow', 'psionic'}, set()),
}
_MELEE = {'blow', 'bite', 'sting', 'trample', 'grapple', 'touch'}


def _guard_fn(spec):
    kind = spec[0]
    if kind == 'riders':
        risers, dels = spec[1], spec[2]
        return lambda a: (1.0, 0.0 if (a['effect'] in risers and (not dels or a['delivery'] in dels)) else 1.0)
    if kind == 'delivery':
        dels = spec[1]
        return lambda a: (0.0, 0.0) if a['delivery'] in dels else (1.0, 1.0)
    if kind == 'delivery+':
        dels, risers = spec[1], spec[2]
        return lambda a: ((0.0, 0.0) if a['delivery'] in dels else
                          (1.0, 0.0 if a['effect'] in risers else 1.0))
    if kind == 'element':
        typs, risers = spec[1], spec[2]
        return lambda a: (0.0 if a['type'] in typs else 1.0,
                          0.0 if a['effect'] in risers else 1.0)
    if kind == 'parry':
        return lambda a: (0.0, 0.0) if a['delivery'] in _MELEE else (1.0, 1.0)
    if kind == 'combo':
        dels, risers = spec[1], spec[2]
        return lambda a: ((0.0, 0.0) if a['delivery'] in dels else
                          (1.0, 0.0 if a['effect'] in risers else 1.0))
    if kind == 'multi':
        parts = [_guard_fn(s) for s in spec[1]]

        def g(a):
            ks = [p(a) for p in parts]
            return min(k[0] for k in ks), min(k[1] for k in ks)
        return g
    return None


def value_per_unit(spec, attacks, base) -> float:
    """Harm turned away by one unit of the ladder (100% shrug or turn-aside,
    +100% damage), in AC points (`base` = what one AC point turns away)."""
    if spec[0] == 'might':
        return ehl(attacks) * 0.5 / base       # +100% damage: fights half as long
    if spec[0] == 'ac':
        return 1.0
    g = _guard_fn(spec)
    return (ehl(attacks) - ehl(attacks, g)) / base


# -------------------------------------------------------------------- report

def report(runs: int, seed: int, census_path: str | None, sensitivity: bool = False):
    census = load_census(census_path)
    templates = load_templates()
    sim = simulate(runs, seed, census, PROPOSAL, templates)
    w = print
    w(f"ARMOUR MODEL  {runs} runs, seed {seed}, census "
      f"{'file' if census_path and os.path.exists(census_path) else 'built-in'}")

    # 1. Worn AC by floor.
    w("\n1. Worn AC (10 - body - shield; DEX 10; no starting kit) across runs")
    w("   floor   mean    sd    p10   p50   p90")
    line = {}
    for f in FLOORS:
        m, sd, p10, p50, p90 = _stats([r[f - 1] for r in sim['ac']])
        line[f] = m
        if f in (1, 5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100):
            w(f"   {f:5}  {m:5.1f}  {sd:4.2f}  {p10:4}  {p50:4}  {p90:4}")
    # Smooth, monotone line through the mean (what monster accuracy is rebaked to).
    smooth = {}
    lo = None
    for f in FLOORS:
        lo = line[f] if lo is None else min(lo, line[f])
        smooth[f] = lo
    line_ac = lambda pf: smooth[min(100, max(1, int(pf)))]
    sds = [_stats([r[f - 1] for r in sim['ac']])[1] for f in FLOORS]
    w(f"   largest across-run SD on any floor: {max(sds):.2f} (floor {sds.index(max(sds)) + 1})")

    # 2. Plateaus.
    m, sd, p10, p50, p90 = _stats(sim['plateau'])
    w(f"\n2. Longest run of floors (5-100) with no AC upgrade: "
      f"mean {m:.1f}, sd {sd:.1f}, p50 {p50}, p90 {p90}")
    m, sd, p10, p50, p90 = _stats(sim['any_gap'])
    w(f"   ... with no upgrade of any kind (AC or a minor slot's tier): "
      f"mean {m:.1f}, sd {sd:.1f}, p50 {p50}, p90 {p90}")

    # 3. Options per minor slot per band.
    w("\n3. Enchanted options per minor slot per 10 floors (all slots pooled)")
    w("   floors    mean   sd   P(>=1) P(>=2) P(>=3)")
    for b in range(10):
        xs = [o[s][b] for o in sim['opts'] for s in MINOR_SLOTS]
        m, sd, *_ = _stats(xs)
        p = lambda k: sum(1 for x in xs if x >= k) / len(xs)
        w(f"   {b*10+1:3}-{b*10+10:<4} {m:5.2f} {sd:4.2f}  {p(1):5.2f}  {p(2):5.2f}  {p(3):5.2f}")

    # 4. Tier pace: first floor a minor slot holds tier N.
    w("\n4. First floor a minor slot holds tier N (all slots pooled)")
    w("   tier   mean    sd   p10  p50  p90   never by 100")
    for t in range(1, 6):
        xs = [fr[s][t] for fr in sim['first'] for s in MINOR_SLOTS]
        got = [x for x in xs if x is not None]
        never = 1 - len(got) / len(xs)
        m, sd, p10, p50, p90 = _stats(got)
        w(f"   {t:4}  {m:5.1f}  {sd:4.1f}  {p10:4}  {p50:4}  {p90:4}   {never:5.1%}")

    # 5. Hit chance after the rebake, against each run's own AC.
    w("\n5. Hit chance of the floor's monsters (THAC0 rebaked to the mean AC line)")
    w("   floor   vs mean AC   across runs: p10   p50   p90")
    cache = {}
    for f in (1, 10, 20, 30, 50, 70, 90, 100):
        atk, _hb = floor_model(f, smooth[f], line_ac, cache)
        tw = sum(a['w'] for a in atk) or 1.0
        hit = lambda ac: sum(a['w'] * _hit_p(a['thac0'], ac) for a in atk) / tw
        per_run = sorted(hit(r[f - 1]) for r in sim['ac'])
        n = len(per_run)
        w(f"   {f:5}     {hit(smooth[f]):5.1%}        "
          f"{per_run[int(.1*(n-1))]:5.1%} {per_run[int(.5*(n-1))]:5.1%} {per_run[int(.9*(n-1))]:5.1%}")

    # 6. The stable in AC points, and the schedule the data can carry.
    w("\n6. The stable in AC points: harm a ladder turns away at 100%, over the harm")
    w("   one AC point turns away, averaged over the floors each tier is found on")
    w("   (weighted by its share there); cv = that value's spread across them.")
    scales = (0.5, 1.0, 1.5) if sensitivity else (1.0,)
    priced = {}
    for scale in scales:
        if sensitivity:
            w(f"\n   -- rider costs x{scale}")
        w("   slot   enchantment                                        value/100% T1..T5          cv max")
        for slot, ench in STABLE.items():
            for name, spec in ench.items():
                vals, cvs = [], []
                for t in range(5):
                    v, cv = _tier_value(spec, t, smooth, line_ac, cache, scale)
                    vals.append(v)
                    cvs.append(cv)
                priced[(scale, slot, name)] = (vals, cvs)
                w(f"   {slot:6} {name:50} " + ' '.join(f"{v:5.2f}" for v in vals)
                  + f"   {max(cvs):4.2f}")
        sched = feasible_schedule({k[1:]: v for k, v in priced.items() if k[0] == scale})
        w("   The schedule (largest rising per-tier value every slot can reach with a")
        w(f"   guard at most {LADDER_CAP:.0%}): " + ', '.join(f"T{t+1} {v:.2f}" for t, v in enumerate(sched))
          + " AC points")
        w("   Each ladder: the rising magnitudes closest to the schedule (isotonic")
        w("   regression on log need, capped), then value / budget per tier; a tier")
        w(f"   outside {AVAIL_LO:.2f}-{AVAIL_HI:.2f}x budget is one the enchantment does not roll at (--).")
        ladders = {}
        for slot, ench in STABLE.items():
            for name, spec in ench.items():
                vals, _cv = priced[(scale, slot, name)]
                mags, ratio, avail = fit_ladder(vals, sched, spec)
                ladders[(slot, name)] = (mags, avail)
                w(f"     {slot:6} {name.split(' (')[0]:13} " + '  '.join(
                    (f"{m:4.0%}" if a else '  --') for m, a in zip(mags, avail))
                  + "   x budget " + ' '.join(f"{r:4.2f}" for r in ratio))
        sim.setdefault('schedule', {})[scale] = sched
        sim.setdefault('ladders', {})[scale] = ladders
    sim['priced'] = priced

    # 7. The fight simulator: mean AND spread of harm, and dangerous fights.
    sched = sim['schedule'][1.0]
    w("\n7. Fights, simulated (one hero against one monster of the floor, to the")
    w("   death of one; harm as a share of the health bar). Per fight: mean, sd,")
    w("   and P(a fight costs over half the health bar). Without, and with each")
    w("   guard at its ladder for that tier.")
    w("   Common random numbers (each variant fights the same fights); 'dP' is")
    w("   the change in P(>50%) against plain, with its paired standard error.")
    for t, fl in ((0, 6), (2, 46), (4, 86)):
        fseed = seed * 7919 + fl
        base = fight_stats(fl, smooth[fl], line_ac, cache, fseed, None, 0.0, n=FIGHTS)
        bh = base[3]
        w(f"\n   tier {t+1}, floor {fl}: plain        mean {base[0]:5.1%}  sd {base[1]:5.1%}  P(>50%) {base[2]:5.2%}")

        def show(label, r):
            d = [(a > 0.5) - (b > 0.5) for a, b in zip(r[3], bh)]
            dp = sum(d) / len(d)
            se = statistics.pstdev(d) / math.sqrt(len(d))
            w(f"   {'':16}{label:13} mean {r[0]:5.1%}  sd {r[1]:5.1%}  P(>50%) {r[2]:5.2%}"
              f"  dP {dp:+6.2%} +/- {se:.2%}")

        show('one AC point', fight_stats(fl, smooth[fl] - 1, line_ac, cache, fseed, None, 0.0, n=FIGHTS))
        for slot, ench in STABLE.items():
            for name, spec in ench.items():
                mags, avail = sim['ladders'][1.0][(slot, name)]
                if not avail[t]:
                    continue
                mag = mags[t]
                show(f"{name.split(' (')[0]} {mag:.0%}",
                     fight_stats(fl, smooth[fl], line_ac, cache, fseed, spec, mag, n=FIGHTS))

    # 8. Rings, on the same scale.
    w("\n8. Rings (after ruling 4), priced the same way: value at 100% per tier")
    for name, spec in RING_STABLE.items():
        vals = [_tier_value(spec, t, smooth, line_ac, cache, 1.0)[0] for t in range(5)]
        w(f"   {name:58} " + ' '.join(f"{v:5.2f}" for v in vals))
    w("   (A +1 AC ring is one AC point on every attack: no other ring reaches it.)")
    return sim


FIGHTS = 12000


LADDER_CAP = 0.80            # no ladder above 80% (shrug, turn-aside, parry)
AVAIL_LO, AVAIL_HI = 0.67, 1.5


def fit_ladder(vals, sched, spec) -> tuple:
    """Rising magnitudes m_1 <= ... <= m_5 closest (in log) to sched/vals,
    by pool-adjacent-violators, capped at LADDER_CAP for guards. Returns
    (magnitudes, value/budget per tier, available per tier)."""
    need = [sched[t] / v if v > 0 else 10.0 for t, v in enumerate(vals)]
    logs = [[math.log(max(1e-6, n))] for n in need]
    # PAV: merge adjacent blocks while a block's mean exceeds the next one's.
    blocks = [[x[0], 1] for x in logs]       # [sum, count]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] / blocks[i][1] > blocks[i + 1][0] / blocks[i + 1][1]:
            blocks[i] = [blocks[i][0] + blocks[i + 1][0], blocks[i][1] + blocks[i + 1][1]]
            del blocks[i + 1]
            i = max(0, i - 1)
        else:
            i += 1
    fitted = []
    for s, c in blocks:
        fitted += [math.exp(s / c)] * c
    cap = 1.0 if spec[0] in ('might',) else LADDER_CAP
    mags = [min(cap, m) for m in fitted]
    ratio = [m * v / sched[t] if sched[t] else 0.0 for t, (m, v) in enumerate(zip(mags, vals))]
    avail = [AVAIL_LO <= r <= AVAIL_HI for r in ratio]
    return mags, ratio, avail


def feasible_schedule(priced: dict, min_step: float = 0.05) -> list:
    """The schedule V_t = a + b*(t-1), rising by at least `min_step` a tier,
    with the largest total value such that every slot keeps at least one
    GUARD (not might, which can match anything) able to reach V_t at
    LADDER_CAP on every tier. Within a slot all options are priced to the
    same V_t; across slots they need not be (every slot is worn; the equip
    threshold carries the difference, ruling 3)."""
    guards = {}
    for (slot, name), (vals, _cv) in priced.items():
        spec = STABLE[slot][name]
        if spec[0] in ('might', 'parry', 'ac'):
            continue
        best = guards.setdefault(slot, [0.0] * 5)
        for t in range(5):
            best[t] = max(best[t], LADDER_CAP * vals[t])
    F = [min(b[t] for b in guards.values()) for t in range(5)]
    best, best_sched = -1.0, [0.0] * 5
    for ai in range(1, 101):
        a = ai / 100
        for bi in range(int(min_step * 100), 41):
            b = bi / 100
            s = [a + b * t for t in range(5)]
            if all(s[t] <= F[t] + 1e-9 for t in range(5)) and sum(s) > best:
                best, best_sched = sum(s), s
    if best < 0:
        # No rising schedule fits every slot: the weakest slot sets a flat line.
        return [min(F)] * 5
    return best_sched


def _roll(expr, rng) -> float:
    s = str(expr or '0').replace(' ', '')
    m = re.fullmatch(r'(\d*)d(\d+)([+-]\d+)?', s)
    if not m:
        return dice_mean(s)
    return sum(rng.randint(1, int(m.group(2))) for _ in range(int(m.group(1) or 1))) + int(m.group(3) or 0)


def fight_stats(fl, ac, line_ac, cache, rng, spec, mag, n=6000) -> tuple:
    """Simulated one-on-one fights on floor `fl`: (mean harm, sd, P(harm >
    half the health bar)), harm as a share of the health bar. The hero hits
    for one_attack each turn he can act; each monster turn is one attack
    (chosen at random, as Monster.take_turn does). A guard at `mag` keeps
    (1 - mag) of the damage or rider it guards; Striking adds mag to damage;
    Parrying parries a landed melee blow with chance mag."""
    import dungeon
    if fl not in cache:
        cache[fl] = dungeon._build_spawn_pool(fl)
    pool = cache[fl]
    names = [k for k, m in pool.items() if m.get('attacks')]
    weights = [float(pool[k]['_spawn_freq']) for k in names]
    hb = floor_curve.health_bar(fl)
    one = floor_curve.one_attack(fl)
    g = _guard_fn(spec) if spec and spec[0] not in ('might', 'parry') else None
    might = mag if spec and spec[0] == 'might' else 0.0
    parry = mag if spec and spec[0] == 'parry' else 0.0
    harms = []
    base_seed = rng.randrange(1 << 30) if isinstance(rng, random.Random) else int(rng)
    for i in range(n):
        # Common random numbers: fight i starts from the same seed for every
        # variant, so two guards are compared on the same fights.
        rng = random.Random(base_seed * 1_000_003 + i)
        m = pool[rng.choices(names, weights)[0]]
        mhp = max(1.0, _roll(m.get('hp'), rng))
        pf = int(m.get('peak_floor') or m.get('min_level') or fl)
        thac0 = line_ac(pf) + 10 + PROPOSAL['thac0_spread_keep'] * (float(m.get('thac0', 20)) - _median_thac0(pf))
        p = _hit_p(thac0, ac)
        harm, lost, turns = 0.0, 0.0, 0
        while mhp > 0 and turns < 60 and harm < 2.0 * hb:
            turns += 1
            if lost >= 1.0:
                lost -= 1.0
            else:
                mhp -= one * (1 + might)
                if mhp <= 0:
                    break
            a = rng.choice(m['attacks'])
            if rng.random() >= p:
                continue
            d = delivery(a)
            fake = {'delivery': d, 'type': a.get('type', 'physical'), 'effect': a.get('effect')}
            dk, rk = g(fake) if g else (1.0, 1.0)
            if parry and d in _MELEE and rng.random() < parry:
                continue
            harm += _roll(a.get('damage'), rng) * (1 - (1 - dk) * mag if g else 1.0)
            eff = a.get('effect')
            if eff in RIDER_COST and rng.random() < dice_mean(a.get('effect_chance')) * (1 - (1 - rk) * mag if g else 1.0):
                kind, k = RIDER_COST[eff]
                dur = max(1.0, _roll(a.get('effect_duration'), rng))
                if kind == 'lost':
                    lost += k * dur
                else:
                    harm += k * hb * dur
        harms.append(harm / hb)
    mean = sum(harms) / n
    sd = statistics.pstdev(harms)
    return mean, sd, sum(1 for h in harms if h > 0.5) / n, harms


def _tier_value(spec, t, smooth, line_ac, cache, scale) -> tuple:
    """(weighted mean value per 100%, coefficient of variation) of a ladder
    over the floors tier t+1 is found on, weighted by the tier's share."""
    pts = []
    for fl in range(1, 101, 2):
        share = tier_weights(fl)[t] * (1 - plain_share(fl))
        if share < 0.05:
            continue
        atk, _ = floor_model(fl, smooth[fl], line_ac, cache, scale)
        base = ac_point(atk) or 1.0
        pts.append((share, value_per_unit(spec, atk, base)))
    if not pts:
        return 0.0, 0.0
    tw = sum(s for s, _ in pts)
    mean = sum(s * v for s, v in pts) / tw
    var = sum(s * (v - mean) ** 2 for s, v in pts) / tw
    return mean, (math.sqrt(var) / mean if mean > 0 else 0.0)


def cadence(levels: int, runs: int, seed: int, census: dict, P=PROPOSAL) -> dict:
    """Upgrade cadence over floors 5-80 with 5 or 10 enchantment levels (10:
    two per tier, bells every 10 floors; the core plus stays the tier). An
    upgrade is a better body armour, shield or minor-slot level."""
    if levels == 5:
        peaks, spread, first = P['tier_peak'], 11.0, P['tier_first']
    else:
        peaks = [3 + 10 * i for i in range(10)]
        spread = 6.5
        first = [1] + [max(1, 10 * i - 4) for i in range(1, 10)]
    rng = random.Random(seed)
    tpl = load_templates()
    any_gap, ac_gap, interval = [], [], []
    for _ in range(runs):
        body = shield = 0
        best = {s: 0 for s in MINOR_SLOTS}
        ups, acs = [], []
        for f in FLOORS:
            up = False
            for _i in range(_poisson(rng, census[f][0] * P['share_found'])):
                r = rng.random()
                if r < P['split']['weapon']:
                    continue
                lv = 0
                if rng.random() >= plain_share(f, P):
                    ws = [0.0 if f < first[i] else
                          math.exp(-((f - peaks[i]) ** 2) / (2 * spread ** 2))
                          for i in range(len(peaks))]
                    x, acc, lv = rng.random() * (sum(ws) or 1.0), 0.0, len(ws)
                    for i, wv in enumerate(ws):
                        acc += wv
                        if x <= acc:
                            lv = i + 1
                            break
                plus = lv if levels == 5 else (lv + 1) // 2
                if r < P['split']['weapon'] + P['split']['shield']:
                    v = P['shield_ac'][_pick_template(rng, tpl['shield'], f, P, shield=True)] + plus
                    if v > shield:
                        shield, up = v, True
                    continue
                slot = rng.choice(ARMOUR_SLOTS)
                if slot == 'body':
                    v = P['body_ac'][_pick_template(rng, tpl['body'], f, P)] + plus
                    if v > body:
                        body, up = v, True
                elif lv > best[slot]:
                    best[slot], up = lv, True
            acs.append(10 - body - shield)
            ups.append(up)
        any_gap.append(_longest_gap(ups[4:80]))
        ac_gap.append(_longest_gap([acs[i] < acs[i - 1] for i in range(4, 80)]))
        interval.append(76 / max(1, sum(ups[4:80])))
    return {'any_gap': _stats(any_gap), 'ac_gap': _stats(ac_gap),
            'interval': _stats(interval)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--runs', type=int, default=2000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--census', default=None)
    ap.add_argument('--sensitivity', action='store_true')
    ap.add_argument('--cadence', action='store_true',
                    help='only the 5- vs 10-level upgrade cadence (floors 5-80)')
    a = ap.parse_args(argv)
    if a.cadence:
        census = load_census(a.census)
        for lv in (5, 10):
            c = cadence(lv, a.runs, a.seed, census)
            print(f"{lv:2} levels: mean floors between upgrades {c['interval'][0]:.2f}; "
                  f"longest dry stretch mean {c['any_gap'][0]:.1f} (p90 {c['any_gap'][4]}); "
                  f"longest with no AC change mean {c['ac_gap'][0]:.1f} (p90 {c['ac_gap'][4]})")
        return 0
    report(a.runs, a.seed, a.census, a.sensitivity)
    return 0


if __name__ == '__main__':
    sys.exit(main())
