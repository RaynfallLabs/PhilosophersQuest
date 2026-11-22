#!/usr/bin/env python
"""The balance study (Brandon, 2026-11-17: "this feels too easy... I am
steamrolling everything just a couple levels in. But, I am not my kids").

Runs named cells on tools/balance/difficulty_sim.py, each one a player (a
profile, the kid model or a flat accuracy, an answer speed), a floor range,
knobs, how many monsters fight at once, and simulator constants to change.
Each cell is cut into CHUNK-run pieces, run on a pool of worker processes at
below-normal priority (monte_carlo._low_priority) and merged into
<out_dir>/<cell>.pkl.

The players:
  adult        Brandon, measured from his own answer_times.json and save
               (2026-11-17): tier-1 sums in 1.6 s on average (speed 0.85 of
               the simulator's 1.8 s median), 95% right; every system, as
               the mastery profile plays them.
  kid          the simulator's kid model (KID_ACC by tier, 1.8 s a tier-1
               sum); kid@1.5 and kid@2 answer half again and twice as slowly.

Usage:
    py tools/balance/balance_study.py <out_dir> <runs> <set> [set ...]
    py tools/balance/balance_study.py --report <out_dir> [lo-hi]
Sets: see SETS below; late[:<overlay.json>] and late_more[:<overlay.json>] are the
late game's instruments (late_set). MC_WORKERS (default 10) sets the pool.
A cell's late-game table: py tools/balance/sim_late.py --summary <out_dir>/<cell>.pkl
"""
import os
import pickle
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'src'))
os.environ['PQ_NO_BONES'] = '1'
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import difficulty_sim as ds  # noqa: E402
import monte_carlo as mc  # noqa: E402  (its profiles and _low_priority)

CHUNK = 20
ADULT_SPEED = 0.85      # 1.59 s mean over 1,088 tier-1 sums / (1.8 s x lognormal mean 1.046)
ADULT_ACC = 0.95        # 96.5% over every run on this machine; 93.3% this run


def cell(name, profile='mastery', who='kid', speed=1.0, knobs='', floors=(1, 30),
         engagers=1, consts=None):
    kid = who == 'kid'
    return dict(name=name, profile=profile, kid=kid, accuracy=0.95 if kid else ADULT_ACC,
                speed=speed, knobs=knobs, floors=floors, engagers=engagers,
                consts=dict(consts or {}))


def players(prefix, knobs='', floors=(1, 30), engagers=1, consts=None):
    """The four players the early-game question turns on."""
    return [cell(f'{prefix}adult', 'mastery', 'adult', ADULT_SPEED, knobs, floors, engagers, consts),
            cell(f'{prefix}kid', 'mastery', 'kid', 1.0, knobs, floors, engagers, consts),
            cell(f'{prefix}kid15', 'mastery', 'kid', 1.5, knobs, floors, engagers, consts),
            cell(f'{prefix}kid2', 'mastery', 'kid', 2.0, knobs, floors, engagers, consts)]


# Levers for the sweep: (tag, knobs, engagers, consts). Each is something the
# data or the monsters' play could really change; the knob is its stand-in.
LEVERS = [
    ('dmg125', 'mon_dmg=1.25', 1, None),
    ('dmg150', 'mon_dmg=1.5', 1, None),
    ('dmg200', 'mon_dmg=2.0', 1, None),
    ('hp125', 'mon_hp=1.25', 1, None),
    ('hp150', 'mon_hp=1.5', 1, None),
    ('hit2', 'mon_hit=2', 1, None),
    ('hit4', 'mon_hit=4', 1, None),
    ('count13', 'mon_count=1.3', 1, None),
    ('pack2', '', 2, None),                        # two of a group fight at once
    ('pack3', '', 3, None),
    ('first', '', 1, {'FAST_SPEED': 11}),          # more monsters strike first
    ('pots50', 'potions=0.5', 1, None),
    ('heal75', 'heal=0.75', 1, None),
    ('rest50', 'rest=0.5,regen=0.5', 1, None),
    ('timer80', 'timer=0.8', 1, None),
    ('dmg150p2', 'mon_dmg=1.5', 2, None),          # a combination
    ('hp125p2', 'mon_hp=1.25', 2, None),
    # Early-only schedules (11 points, floor 1 to 100): the top of the
    # dungeon given teeth, the deep left as it is (its win rates are right).
    ('edmg150', 'mon_dmg=1.5:1.5:1.5:1.25:1:1:1:1:1:1:1', 1, None),
    ('edmg200', 'mon_dmg=2:2:2:1.5:1:1:1:1:1:1:1', 1, None),
    ('edmg150p2', 'mon_dmg=1.5:1.5:1.5:1.25:1:1:1:1:1:1:1', 2, None),
    ('ehit3', 'mon_hit=3:3:3:2:0:0:0:0:0:0:0', 1, None),
    # Cooking carries the game (the ablation: 87% of healing is meals, and
    # every point of max HP above the start): less from it.
    ('heal60', 'heal=0.6', 1, None),
    ('php80', 'player_hp=0.8', 1, None),
    # Ordinary monsters only: boss_hp / boss_dmg cancel the knob for named
    # foes (mini-bosses, gate bosses, seal demons), whose fights already
    # carry the danger (the first sweep: a flat x1.5-2 blow mostly made the
    # mini-bosses lethal while ordinary fights stayed cheap).
    ('o_d150', 'mon_dmg=1.5,boss_dmg=0.6667', 1, None),
    ('o_d200', 'mon_dmg=2,boss_dmg=0.5', 1, None),
    ('o_h150', 'mon_hp=1.5,boss_hp=0.6667', 1, None),
    ('o_h150d150', 'mon_hp=1.5,boss_hp=0.6667,mon_dmg=1.5,boss_dmg=0.6667', 1, None),
    ('o_h125d150p2', 'mon_hp=1.25,boss_hp=0.8,mon_dmg=1.5,boss_dmg=0.6667', 2, None),
    ('o_d150p2', 'mon_dmg=1.5,boss_dmg=0.6667', 2, None),
    ('o_h150d200', 'mon_hp=1.5,boss_hp=0.6667,mon_dmg=2,boss_dmg=0.5', 1, None),
    # The sweet spot (Brandon, 2026-11-18: "maybe 1.75x harder?... find the
    # sweet spot"); mon_hit has no named-foe twin, so +2 reaches them too.
    ('o_d175', 'mon_dmg=1.75,boss_dmg=0.5714', 1, None),
    ('o_d175h2', 'mon_dmg=1.75,boss_dmg=0.5714,mon_hit=2', 1, None),
]

# Brandon's kids answer at "about .5-.7x my speed" (2026-11-18): 1.52 s / 0.7
# to / 0.5 = 2.2-3.0 s a tier-1 sum, 1.2x and 1.7x the sim kid's 1.8 s.
KID_FAST, KID_SLOW = 1.2, 1.7


def ordinary(points):
    """Knobs for ordinary monsters' blows on a floor@value schedule, with
    the named foes' twin cancelling it at every point."""
    dmg = ';'.join(f"{x:g}@{f}" for f, x in points)
    boss = ';'.join(f"{1.0 / x:.4f}@{f}" for f, x in points)
    return f"mon_dmg={dmg},boss_dmg={boss}"


# Shaped schedules (2026-11-18): flat 1.75x killed new heroes on floor 1
# (archers and casters shooting a 30-HP hero), while floors 10-19 stayed the
# easiest band at any flat multiplier (health from meals outgrows the blows
# there). Gentle at the top, strongest in the teens and twenties.
SHAPES = {
    'shA': [(1, 1.25), (3, 1.25), (6, 1.75), (12, 2.0), (28, 2.0), (36, 1.75)],
    'shB': [(1, 1.25), (3, 1.25), (6, 2.0), (12, 2.5), (28, 2.5), (36, 1.75)],
    'shC': [(1, 1.25), (3, 1.25), (6, 1.75), (12, 2.25), (28, 2.25), (40, 2.0)],
    'shD': [(1, 1.25), (3, 1.25), (6, 1.85), (12, 2.25), (28, 2.25), (36, 1.75)],
}


def shape_set():
    out = []
    for tag, pts in SHAPES.items():
        kn = ordinary(pts)
        out += [cell(f'S_{tag}_adult', 'mastery', 'adult', ADULT_SPEED, kn, (1, 100)),
                cell(f'S_{tag}_kidA', 'mastery', 'kid', KID_FAST, kn, (1, 100)),
                cell(f'S_{tag}_kidB', 'mastery', 'kid', KID_SLOW, kn, (1, 100))]
    return out


def sweet_set():
    out = []
    for tag, kn, eng, co in [('base', '', 1, None)] + [lv for lv in LEVERS if lv[0] in (
            'o_d150', 'o_d175', 'o_d200', 'o_d175h2')]:
        out += [cell(f'S_{tag}_adult', 'mastery', 'adult', ADULT_SPEED, kn, (1, 100), eng, co),
                cell(f'S_{tag}_kidA', 'mastery', 'kid', KID_FAST, kn, (1, 100), eng, co),
                cell(f'S_{tag}_kidB', 'mastery', 'kid', KID_SLOW, kn, (1, 100), eng, co)]
    return out

# Which system makes the early fights free: mastery with one system taken
# away (monte_carlo's m_no_* profiles), the sim kid, floors 1-30.
ABLATE = [cell('A_' + n[5:], n) for n in mc.ABLATIONS] + [
    cell('A_none', 'prepared'), cell('A_bare', 'unprepared')]

SETS = {
    'ablate': ABLATE,
    'sweet': sweet_set(),
    'shapes': shape_set(),
    # Where we are: the early game for each player, and the other profiles.
    'base': (players('') + [
        cell('adult_committed', 'committed', 'adult', ADULT_SPEED),
        cell('adult_casual', 'casual', 'adult', ADULT_SPEED),
        cell('kid_committed', 'committed'), cell('kid_casual', 'casual'),
        cell('b_fianna', 'b_fianna'), cell('b_fluffs', 'b_fluffs'),
        cell('b_corwin', 'b_corwin'), cell('b_cain', 'b_cain'),
        cell('kid_mage', 'mastery_mage'), cell('kid_dex', 'mastery_dex')]),
    # The whole game, for the win rates the options must keep.
    'full': [cell('F_adult', 'mastery', 'adult', ADULT_SPEED, floors=(1, 100)),
             cell('F_kid', floors=(1, 100)), cell('F_kid15', speed=1.5, floors=(1, 100)),
             cell('F_kid2', speed=2.0, floors=(1, 100)),
             cell('F_casual', 'casual', floors=(1, 100)),
             cell('F_committed', 'committed', floors=(1, 100))],
    'levers': [c for tag, kn, eng, co in LEVERS for c in players(f'L_{tag}_', kn, (1, 30), eng, co)],
    'olevers': [c for tag, kn, eng, co in LEVERS if tag.startswith('o_')
                for c in players(f'L_{tag}_', kn, (1, 30), eng, co)],
}

# The group fight (2026-11-20, tools/balance/sim_groups.py): a room's group
# met two at a time (a careful kid in doorways and corridors) and eight (in
# the open), with the group mechanics on and all off; and the walk-through
# kid (difficulty_sim's `walkthrough` profile) in the open.
GROUP_OFF = ','.join(f'{k}=0' for k in ds.sim_groups.KNOBS)


def groupfight_set():
    out = []
    for e in (2, 8):
        for who, sp in (('kidA', KID_FAST), ('kidB', KID_SLOW)):
            out += [cell(f'G{e}_{who}_on', 'mastery', 'kid', sp, '', (1, 100), e),
                    cell(f'G{e}_{who}_off', 'mastery', 'kid', sp, GROUP_OFF, (1, 100), e)]
    out.append(cell('W8_walk_kidA', 'walkthrough', 'kid', KID_FAST, '', (1, 100), 8))
    return out


SETS['groupfight'] = groupfight_set()


# The late game's instruments (2026-11-20, tools/balance/sim_late.py): the
# careful kid (mastery, KID_FAST, two at once, the whole game) with each knob
# alone, and with them together; set name `late` (no overlay cell) or
# `late:<overlay.json>` (tools/balance/bane_synth.py writes one). `late_more`
# adds the cook-only and walk-through kids, bare and with every knob.
def late_set(overlay='', more=False):
    ov = f'overlay={overlay}' if overlay else ''
    rows = [('base', ''), ('hp17', 'hp_target=1.7'), ('sup1', 'supply=1'), ('sig15', 'sig=1.5'),
            ('camp4', 'campaign=4')]
    if ov:
        rows.insert(1, ('synth', ov))
        rows.append(('all', ov + ',hp_target=1.7,supply=1,sig=1.5,recoat=1'))
    out = [cell(f'LT_{tag}', 'mastery', 'kid', KID_FAST, kn, (1, 100), 2) for tag, kn in rows]
    if more:
        every = ','.join(x for x in (ov, 'hp_target=1.7,supply=1,sig=1.5,recoat=1') if x)
        for prof in ('cookonly', 'walkthrough'):
            out += [cell(f'LT_{prof}_base', prof, 'kid', KID_FAST, '', (1, 100), 2),
                    cell(f'LT_{prof}_all', prof, 'kid', KID_FAST, every, (1, 100), 2)]
    return out


def full_lever_set(tags):
    """The whole game under the chosen levers (set name full:<tag>+<tag>)."""
    out = []
    for tag, kn, eng, co in LEVERS:
        if tag in tags:
            out += [cell(f'FL_{tag}_adult', 'mastery', 'adult', ADULT_SPEED, kn, (1, 100), eng, co),
                    cell(f'FL_{tag}_kid', 'mastery', 'kid', 1.0, kn, (1, 100), eng, co),
                    cell(f'FL_{tag}_kid15', 'mastery', 'kid', 1.5, kn, (1, 100), eng, co),
                    cell(f'FL_{tag}_casual', 'casual', 'kid', 1.0, kn, (1, 100), eng, co)]
    return out


def chunks(cells, runs):
    out = []
    for i, c in enumerate(cells):
        for k in range(0, runs, CHUNK):
            out.append(dict(c, trials=min(CHUNK, runs - k), seed=11 + 1000 * i + k))
    return out


# A pool worker runs many jobs: the kid flag and the constants a job changes
# are put back before each one (run_cell only ever sets KID_MODEL on).
_CONST_DEFAULTS = {}


def run(job):
    t0 = time.time()
    for k, v in _CONST_DEFAULTS.items():
        setattr(ds, k, v)
    ds.KID_MODEL = bool(job['kid'])
    for k, v in job['consts'].items():
        _CONST_DEFAULTS.setdefault(k, getattr(ds, k))
        setattr(ds, k, v)
    res = ds.run_cell(profile=job['profile'], accuracy=job['accuracy'], trials=job['trials'],
                      floors=tuple(job['floors']), knobs=ds.parse_knobs(job['knobs']),
                      speed=job['speed'], engagers=job['engagers'], seed=job['seed'],
                      variants=24, kid=job['kid'])
    res['cell'] = {k: v for k, v in job.items() if k not in ('trials', 'seed')}
    res['wall'] = time.time() - t0
    return res


def merge(a, b):
    if a is None:
        return b
    ds.merge_stats(a['stats'], b['stats'])
    a['boss_rows'] += b['boss_rows']
    a['trials'] += b['trials']
    a['wall'] += b['wall']
    ds.sim_late.merge_late(a, b)          # the late game's parts (campaign, the blow meter)
    return a


def main(argv):
    out_dir, runs = argv[0], int(argv[1])
    cells = []
    for s in argv[2:]:
        if s.startswith('full:'):
            cells += full_lever_set(set(s[5:].split('+')))
        elif s.split(':', 1)[0] in ('late', 'late_more'):
            cells += late_set(s.split(':', 1)[1] if ':' in s else '', s.startswith('late_more'))
        elif s in SETS:
            cells += SETS[s]
        else:
            cells += [c for group in SETS.values() for c in group if c['name'] == s]
    os.makedirs(out_dir, exist_ok=True)
    todo = [c for c in cells if not os.path.exists(os.path.join(out_dir, c['name'] + '.pkl'))]
    jobs = chunks(todo, runs)
    workers = min(len(jobs), int(os.environ.get('MC_WORKERS') or 10)) or 1
    print(f"{len(todo)} cells, {len(jobs)} chunks x {CHUNK} runs on {workers} workers", flush=True)
    import multiprocessing as mp
    t0 = time.time()
    merged, left = {}, {}
    for j in jobs:
        left[j['name']] = left.get(j['name'], 0) + 1
    # A worker keeps about 100 MB of every chunk it plays (30 of them took 40 GB
    # fourteen cells into a sweep, 2026-11-22): a fresh one every two chunks.
    with mp.Pool(workers, initializer=mc._low_priority, maxtasksperchild=2) as pool:
        for res in pool.imap_unordered(run, jobs):
            name = res['cell']['name']
            merged[name] = merge(merged.get(name), res)
            left[name] -= 1
            if not left[name]:
                with open(os.path.join(out_dir, name + '.pkl'), 'wb') as f:
                    pickle.dump(merged.pop(name), f)
                print(f"cell {name} done ({time.time() - t0:.0f}s)", flush=True)
    print(f"all done in {time.time() - t0:.0f}s", flush=True)
    return 0


# =============================================================================
# The report: what a fight costs, floor by floor
# =============================================================================

SPANS = [(1, 3), (4, 6), (7, 9), (10, 14), (15, 19), (21, 25), (26, 30)]


def span_row(res, a, b):
    st = res['stats']
    fl = [f for f in st if a <= f <= b]
    if not fl:
        return None
    s = {}
    for f in fl:
        for k, v in st[f].items():
            if isinstance(v, (int, float)):
                s[k] = s.get(k, 0) + v
    v = max(1, s.get('visits', 0))
    of = max(1, s.get('ofights', 0))
    kills = max(1, s.get('kills', 0))
    return dict(
        fights=s.get('ofights', 0) / v,
        cost=s.get('ofight_cost', 0.0) / of,
        free=s.get('ofree', 0) / of,
        scary=s.get('oscary', 0) / of,
        close=s.get('oclose', 0) / of,
        low=s.get('floor_low', 0.0) / v,
        low50=s.get('floor_low50', 0) / v,
        hp_lost=s.get('hp_lost', 0.0) / v,
        atk=s.get('atk_sum', 0) / kills,
        one=s.get('one_shots', 0) / kills,
        p_die=s.get('deaths', 0) / v,
        max_hp=s.get('max_hp', 0) / v,
        turns=s.get('ofight_turns', 0) / of,
        chain=s.get('chain_sum', 0) / max(1, s.get('attacks', 0)),
    )


def survival(res, upto):
    trials = res['trials']
    dead = sum(fs.get('first_deaths', 0) for f, fs in res['stats'].items() if f <= upto)
    return 1.0 - dead / max(1, trials)


def load(out_dir):
    out = {}
    for fn in sorted(os.listdir(out_dir)):
        if fn.endswith('.pkl'):
            with open(os.path.join(out_dir, fn), 'rb') as f:
                out[fn[:-4]] = pickle.load(f)
    return out


def report(out_dir, spans=SPANS, out=sys.stdout):
    cells = load(out_dir)
    w = out.write
    w("cell                 floors  fights cost/  free  scary close  floor  low<50  HP lost  atk/  1-shot chain  P(die) maxHP\n")
    w("                             /floor fight%  %     %     %     low%   %flrs   %/floor  kill   %      mean   %/flr\n")
    for name, res in cells.items():
        lo, hi = res['floors']
        for a, b in spans:
            if b < lo or a > hi:
                continue
            r = span_row(res, a, b)
            if not r:
                continue
            w(f"{name:<20} {a:>2}-{b:<3}  {r['fights']:5.1f} {100 * r['cost']:5.1f}  {100 * r['free']:4.0f}  "
              f"{100 * r['scary']:4.1f}  {100 * r['close']:4.1f}  {100 * r['low']:5.0f}  {100 * r['low50']:5.0f}   "
              f"{100 * r['hp_lost']:6.0f}  {r['atk']:4.2f}  {100 * r['one']:4.0f}  {r['chain']:5.1f}  "
              f"{100 * r['p_die']:5.2f} {r['max_hp']:5.0f}\n")
        w(f"{'':<20} survive to {hi}: {100 * survival(res, hi):.1f}%   ({res['trials']} runs)\n")


def lever_table(base_dir, lever_dir, out=sys.stdout, spans=((1, 9), (10, 19), (21, 30))):
    """Each lever against the baseline, per player: what an ordinary fight
    costs, how many fights drop him under half, and deaths per floor."""
    base = load(base_dir)
    lev = load(lever_dir)
    who = ('adult', 'kid', 'kid15', 'kid2')
    w = out.write
    for a, b in spans:
        w(f"\nfloors {a}-{b}: fight cost % / fights under half HP % / deaths per 100 floors"
          f" / survive to 30 %\n")
        w(f"{'lever':<11}" + ''.join(f"{p:>27}" for p in who) + "\n")
        tags = ['base'] + [t for t, *_ in LEVERS]
        for tag in tags:
            row = f"{tag:<11}"
            for p in who:
                res = base.get(p) if tag == 'base' else lev.get(f'L_{tag}_{p}')
                if not res:
                    row += f"{'-':>27}"
                    continue
                r = span_row(res, a, b)
                row += (f"{100 * r['cost']:7.1f} {100 * r['scary']:5.1f} {100 * r['p_die']:5.2f}"
                        f" {100 * survival(res, 30):6.1f}")
            w(row + "\n")


if __name__ == '__main__':
    if sys.argv[1:2] == ['--report']:
        report(sys.argv[2])
        sys.exit(0)
    if sys.argv[1:2] == ['--levers']:
        lever_table(sys.argv[2], sys.argv[3])
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
