#!/usr/bin/env python
"""The Tactical Mind's seeded position harness (AI-2, 2026-11-20).

The simulator (difficulty_sim.py) has no map: a fight is a queue at a
doorway. This harness gives it what the Tactical Mind and the archers' lanes
are worth there. It sets real kinds (data/monsters.json) on small hand-made
floors, gives them a scripted hero, runs the REAL Monster.take_turn (the
mind, the lanes, Wait Your Turn, the senses), and counts, with each part on
and off:

  blows     the creatures' blows and shots on the hero per creature slain
  turns     hero turns per creature slain
  closing   hero turns spent walking after an archer per archer slain

The scripted hero:
  camper    stands in his corridor (the corridor trick) and strikes what
            comes beside him; shot at three turns running with nobody beside
            him, he goes out after the shooter, as any player would;
  advancer  walks at the nearest creature he can see and strikes it.
Each strikes for a third of a creature's health (three blows a kill), and
takes no harm (blows are counted, not rolled: the simulator rolls them).

Scenes, per mind (the kinds the mind is given to by lore):
  corridor  a room and a corridor; the hero camps two tiles in
  open      one room; the hero comes in from the side
  dark      the dark-edge kinds against an unlit hero (sight 5) and a lit
            one (sight 9)
  archers   archers behind their own front line (the lanes)

Usage:
    py tools/balance/tactics_scenarios.py [runs]        # the table
    py tools/balance/tactics_scenarios.py --json [runs] # the numbers sim_ai2 reads
"""
from __future__ import annotations

import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'src'))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PQ_NO_BONES', '1')

import lanes  # noqa: E402
import senses  # noqa: E402
import tactical_mind as tm  # noqa: E402
from dungeon import Dungeon, Room, WALL, FLOOR  # noqa: E402
from monster import Monster  # noqa: E402

MONS = json.load(open(os.path.join(REPO, 'data', 'monsters.json'), encoding='utf-8'))
MAX_TURNS = 150          # a fight not over by then is left out of the counts


class Hero:
    """The scripted hero: enough of one for the monsters' side."""
    def __init__(self, x, y, sight=5):
        self.x, self.y = x, y
        self.hp = self.max_hp = 10_000
        self.status_effects = {}
        self.equipped_accessories = []
        self.boons_taken = {}
        self.STR = self.CON = self.DEX = self.INT = self.WIS = self.PER = 10
        self.shield = self.weapon = None
        self.armor_slots = []
        self.inventory = []
        self.sight = sight

    def has_effect(self, name):
        return self.status_effects.get(name, 0) > 0

    def is_burdened(self):
        return False

    def get_ac(self):
        return 10

    def get_sight_radius(self, extra_light=0):
        return self.sight

    def take_damage(self, amount, damage_type='physical'):
        return 0

    def save_bonus_for(self, _stat):
        return 0

    def add_effect(self, name, duration):
        return True


def grid(rows):
    h, w = len(rows), len(rows[0])
    tiles = [[WALL if c == '#' else FLOOR for c in r] for r in rows]
    return Dungeon(tiles, [Room(0, 0, w, h)], w, h, 10)


CORRIDOR = [
    "########################",
    "#.........##############",
    "#.........##############",
    "#.........##############",
    "#.........##############",
    "#......................#",
    "#.........##############",
    "#.........##############",
    "#.........##############",
    "#.........##############",
    "########################",
]
OPEN = ["#" * 24] + ["#" + "." * 22 + "#" for _ in range(12)] + ["#" * 24]

# By mind: the kinds a scene's group is made of (front line, then the rest).
GROUPS = {
    'cunning': [('bandit_thug', 'bandit_thug', 'bandit_archer', 'bandit_captain'),
                ('gnoll_pack_lord', 'bugbear', 'kobold_pack_leader')],
    'soldier': [('hobgoblin', 'hobgoblin', 'orc_archer', 'hobgoblin_captain'),
                ('orc_warrior', 'orc_warrior', 'mercenary_veteran')],
    'trickster': [('drow_warrior', 'huldufolk_raider', 'dark_elf'),
                  ('drow_warrior', 'drow_warrior', 'shadow')],
    'caster': [('hobgoblin', 'kobold_sorcerer', 'goblin_shaman'),
               ('bandit_thug', 'battle_mage', 'dark_cultist')],
}
ARCHERS = [('orc_warrior', 'bandit_archer', 'bandit_archer'),
           ('hobgoblin', 'goblin_sniper', 'gnoll_archer')]


def make(kind, x, y, band=None, role='', leader=None):
    m = Monster({**MONS[kind], 'id': kind}, x, y)
    m._aware = m._tracking = m._alerted = True
    m._opened = True
    if band:
        m._band, m._band_id, m._band_role = band, 'goblin_raiders', role
        if leader is not None:
            m._band_leader = leader
    return m


def _band(mons, d):
    """The last of a group leads it as a band (the captains and chiefs)."""
    uid = 'scene@0,0'
    lead = mons[-1]
    lead._band, lead._band_id, lead._band_role = uid, 'goblin_raiders', 'leader'
    for o in mons[:-1]:
        o._band, o._band_id, o._band_leader = uid, 'goblin_raiders', lead
        o._band_role = 'shooter' if lanes.usable(o) and o.ai_pattern == 'ranged' else 'guard'
    d.band = {'id': 'goblin_raiders', 'uid': uid, 'room': (0, 0, 10, 11),
              'counts': {'guard': len(mons) - 1, 'shooter': 0, 'caster': 0, 'healer': 0}}


def _place(kinds, d, spots, rng, band=False):
    mons = []
    rng.shuffle(spots)
    for kind, (x, y) in zip(kinds, spots):
        mons.append(make(kind, x, y))
    if band and len(mons) >= 3:
        _band(mons, d)
    return mons


def _cheb(a, b):
    return max(abs(a.x - b.x), abs(a.y - b.y))


def run_scene(kinds, scene: str, policy: str, seed: int, band=False, sight=5) -> dict:
    rng = random.Random(seed)
    random.seed(seed)
    if scene == 'corridor':
        d = grid(CORRIDOR)
        hero = Hero(12, 5, sight)
        spots = [(x, y) for x in range(2, 7) for y in range(2, 9)]
        mons = _place(kinds, d, spots, rng, band)
    elif scene == 'strung':
        # Roused one by one, as a floor's creatures are: one near, the rest
        # strung out behind it (the simulator's queue at the doorway).
        d = grid(OPEN)
        hero = Hero(19, 7, sight)
        mons = []
        for i, kind in enumerate(kinds):
            mons.append(make(kind, 16 - 4 * i, 6 + (i % 3)))
        if band and len(mons) >= 3:
            _band(mons, d)
    else:
        d = grid(OPEN)
        hero = Hero(19, 7, sight)
        spots = [(x, y) for x in range(2, 7) for y in range(3, 11)]
        mons = _place(kinds, d, spots, rng, band)
    archers = {id(m) for m in mons if m.ai_pattern == 'ranged'}
    out = {'blows': 0, 'turns': 0, 'slain': 0, 'closing': 0, 'archers_slain': 0, 'mind_turns': 0,
           'fighting': 0, 'together': 0}
    hits = {}
    shot_at = False
    under_fire = 0
    tm.TURN.__init__()
    senses.begin_turn(moved=False, guilty=False, floor=10)
    for t in range(MAX_TURNS):
        live = [m for m in mons if m.alive]
        if not live:
            break
        out['turns'] += 1
        # The hero's turn.
        beside = [m for m in live if m._adjacent_to(hero)]
        if beside:
            out['fighting'] += 1
            out['together'] += 1 if len(beside) >= 2 else 0
        moved = False
        if beside:
            m = min(beside, key=lambda o: (o.y, o.x))
            hits[id(m)] = hits.get(id(m), 0) + 1
            if hits[id(m)] >= 3:
                m.alive = False
                m.hp = 0
                out['slain'] += 1
                if id(m) in archers:
                    out['archers_slain'] += 1
        elif policy == 'advancer' or (policy == 'camper' and under_fire >= 3):
            seen = [m for m in live if senses.clear_view(hero.x, hero.y, m.x, m.y, d)
                    and _cheb(hero, m) <= hero.sight]
            if not seen and shot_at:
                # Shot by something he cannot see: the line names it, and he
                # goes the way the shot came from.
                seen = [min(live, key=lambda o: (_cheb(hero, o), o.y, o.x))]
            if seen:
                tgt = min(seen, key=lambda o: (_cheb(hero, o), o.y, o.x))
                if id(tgt) in archers:
                    out['closing'] += 1
                step = senses.find_path(hero, d, (tgt.x, tgt.y),
                                        blocked={(o.x, o.y) for o in live if o is not tgt})
                if step and step[0] != (tgt.x, tgt.y):
                    hero.x, hero.y = step[0]
                    moved = True
        senses.begin_turn(moved=moved, guilty=False, floor=10)
        tm.begin_turn(type('G', (), {'pets': [], 'turn_count': 1000 + t})())
        # The creatures' turns.
        shot_at = False
        for m in [o for o in mons if o.alive]:
            before = dict(m.__dict__.get('_tm_used') or {})
            if m.take_turn(hero, d, mons):
                out['blows'] += 1
                shot_at = shot_at or not m._adjacent_to(hero)
                m.__dict__.pop('_pack_blow', None)
                m.__dict__.pop('_tm_surprise', None)
            if (m.__dict__.get('_tm_used') or {}) != before:
                out['mind_turns'] += 1
            m.__dict__.pop('_ai_lines', None)
        under_fire = under_fire + 1 if (shot_at and not any(
            o.alive and o._adjacent_to(hero) for o in mons)) else 0
    return out


SCENES = (('corridor', 'camper'), ('corridor', 'advancer'), ('open', 'advancer'),
          ('strung', 'camper'))


def measure(runs: int = 20) -> dict:
    """{mind: {...}} the per-mind effect, and {'lanes': {...}}."""
    res = {}
    for mind, groups in GROUPS.items():
        row = {'scenes': {}}
        for label, on in (('on', True), ('off', False)):
            tm.ENABLED = on
            tot = {'blows': 0, 'turns': 0, 'slain': 0, 'mind_turns': 0, 'fighting': 0, 'together': 0}
            for scene, policy in SCENES:
                st = {'blows': 0, 'turns': 0, 'slain': 0, 'mind_turns': 0, 'fighting': 0,
                      'together': 0}
                for gi, kinds in enumerate(groups):
                    for band in (False, True):
                        for s in range(runs):
                            got = run_scene(kinds, scene, policy, 1000 * gi + s, band)
                            if got['slain'] < len(kinds):
                                row['unfinished'] = row.get('unfinished', 0) + 1
                                continue
                            for k in tot:
                                tot[k] += got[k]
                                st[k] += got[k]
                key = f'{scene}/{policy}'
                row['scenes'].setdefault(key, {})[label] = st['blows'] / max(1, st['slain'])
                if scene == 'strung':
                    row[f'together_{label}'] = st['together'] / max(1, st['fighting'])
            row[label] = tot
        tm.ENABLED = True
        on, off = row['on'], row['off']
        # What a kid does: the three scenes alike.
        ratios = [v['on'] / v['off'] for v in row['scenes'].values()
                  if v.get('on') and v.get('off')] or [1.0]
        row['ratio'] = sum(ratios) / len(ratios)
        row['blows_per_kill_on'] = on['blows'] / max(1, on['slain'])
        row['blows_per_kill_off'] = off['blows'] / max(1, off['slain'])
        row['turns_per_kill_on'] = on['turns'] / max(1, on['slain'])
        row['turns_per_kill_off'] = off['turns'] / max(1, off['slain'])
        row['mind_share'] = on['mind_turns'] / max(1, on['turns'])
        row['extra_blows_per_kill'] = row['blows_per_kill_on'] - row['blows_per_kill_off']
        res[mind] = row
    # The dark edge: unlit and lit.
    dark = {}
    for sight in (5, 9):
        for label, on in (('on', True), ('off', False)):
            tm.ENABLED = on
            tot = {'blows': 0, 'slain': 0, 'turns': 0}
            for s in range(runs):
                for kinds in GROUPS['trickster']:
                    got = run_scene(kinds, 'open', 'advancer', 500 + s, False, sight)
                    if got['slain'] < len(kinds):
                        continue
                    for k in tot:
                        tot[k] += got[k]
            dark[f'{sight}_{label}'] = tot['blows'] / max(1, tot['slain'])
        tm.ENABLED = True
    res['dark'] = dark
    # The lanes.
    ln = {}
    for label, on in (('on', True), ('off', False)):
        lanes.ENABLED = on
        tot = {'blows': 0, 'slain': 0, 'closing': 0, 'archers_slain': 0, 'turns': 0}
        for gi, kinds in enumerate(ARCHERS):
            for scene in ('open', 'corridor'):
                for s in range(runs):
                    got = run_scene(kinds, scene, 'advancer', 2000 + 100 * gi + s)
                    if got['slain'] < len(kinds):
                        continue
                    for k in tot:
                        tot[k] += got[k]
        ln[label] = tot
    lanes.ENABLED = True
    for label in ('on', 'off'):
        t = ln[label]
        ln[f'blows_per_kill_{label}'] = t['blows'] / max(1, t['slain'])
        ln[f'closing_per_archer_{label}'] = t['closing'] / max(1, t['archers_slain'])
    res['lanes'] = ln
    # Wait Your Turn: the corridor queue with no mind at all.
    q = {}
    for label, on in (('on', True), ('off', False)):
        senses.QUEUE = on
        tm.ENABLED = False
        tot = {'blows': 0, 'slain': 0, 'turns': 0}
        for s in range(runs):
            got = run_scene(('cave_bear', 'cave_bear', 'cave_bear'), 'corridor', 'camper', 3000 + s)
            for k in tot:
                tot[k] += got[k]
        q[label] = tot['blows'] / max(1, tot['slain'])
    senses.QUEUE = True
    tm.ENABLED = True
    res['queue'] = q
    return res


def main(argv) -> int:
    as_json = '--json' in argv
    args = [a for a in argv if not a.startswith('--')]
    runs = int(args[0]) if args else 20
    res = measure(runs)
    if as_json:
        print(json.dumps(res, indent=1, default=float))
        return 0
    print(f"The Tactical Mind, {runs} seeds a scene (blows = the creatures' blows and shots "
          f"on the hero per creature slain)")
    print(f"{'mind':<10} {'blows on':>9} {'blows off':>10} {'extra':>7} {'turns on':>9} "
          f"{'turns off':>10} {'thinking':>9} {'ratio':>6}")
    for mind in GROUPS:
        r = res[mind]
        print(f"{mind:<10} {r['blows_per_kill_on']:9.2f} {r['blows_per_kill_off']:10.2f} "
              f"{r['extra_blows_per_kill']:+7.2f} {r['turns_per_kill_on']:9.2f} "
              f"{r['turns_per_kill_off']:10.2f} {r['mind_share']:9.0%} {r['ratio']:6.2f}")
        print('           ' + '  '.join(f"{k}: {v['on']:.2f}/{v['off']:.2f}"
                                       for k, v in r['scenes'].items()))
        print(f"           strung out: two or more on him {r['together_on']:.0%} of the "
              f"fighting turns with the mind, {r['together_off']:.0%} without; "
              f"{r.get('unfinished', 0)} fights not over in {MAX_TURNS} turns left out")
    dk = res['dark']
    print(f"dark edge, blows per kill: unlit on {dk['5_on']:.2f} off {dk['5_off']:.2f}; "
          f"lit on {dk['9_on']:.2f} off {dk['9_off']:.2f}")
    ln = res['lanes']
    print(f"lanes: blows per kill on {ln['blows_per_kill_on']:.2f} off {ln['blows_per_kill_off']:.2f}; "
          f"hero turns closing per archer on {ln['closing_per_archer_on']:.2f} "
          f"off {ln['closing_per_archer_off']:.2f}")
    q = res['queue']
    print(f"queue (beasts, no mind): blows per kill on {q['on']:.2f} off {q['off']:.2f}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
