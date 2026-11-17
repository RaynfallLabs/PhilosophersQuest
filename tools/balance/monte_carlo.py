#!/usr/bin/env python
"""The balance Monte Carlo: the win-target cells and the ablations, run on
tools/balance/difficulty_sim.py (kid model, floors 1-100).

Kept from the session scratch scripts the 2026-11-12, 11-13 and 11-16
passes used (mc2.py, mc_now.py), so the next pass starts here. Each cell is
split into CHUNK-run pieces with their own seeds, run across a pool of
worker processes at BELOW-NORMAL priority (the game may be running on the
same machine: it keeps its frames), and merged back into one pickle a cell.

Cells (feedback: the win targets, Brandon 2026-11-13 and 2026-11-16):
  mastery        every system (tactics, context, quests, study...)
  mastery x1.5   the same kid, answering half again as slowly
  mastery_mage   as a caster          mastery_dex  as a Dexterity build
  committed      cooks and prays; no study, tactics, traders or magic
  casual         good at sums, casual about the rest
  m_no_<system>  mastery with one system taken away (the ablation)

Usage:
    py tools/balance/monte_carlo.py <out_dir> <runs> [set ...]
    py tools/balance/monte_carlo_report.py <out_dir>
Sets: targets, ablate, all (default all), defence (the plate and Dexterity
kids, committed, casual and the Secret Builds), builds, or one profile as
profile[@speed] (mastery@1.5). MC_WORKERS (default 12) sets the pool. Writes
<profile>_<tag>_<speed>.pkl into out_dir.
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

CHUNK = 20
ACCURACY = 0.95

# The ablation: mastery with one system taken away.
_M = ds.PROFILES['mastery']
_MK = dict(_M['knobs'])


def _abl(name, knob_drop=(), **prof):
    k = {a: b for a, b in _MK.items() if a not in knob_drop}
    ds.PROFILES[name] = dict(_M, knobs=k, **prof)


_abl('m_no_tactics', ('tactics',))
_abl('m_no_study', ('families', 'study_rate'))
_abl('m_no_cooking', cooks_per_floor=0)
_abl('m_no_quests', ('sword',), quests=False, secrets=False)
_abl('m_no_pet', pet=False)
_abl('m_no_magic', magic=False, casts=False)
_abl('m_no_prayer', prays=False)
_abl('m_no_context', ('untimed',))
_abl('m_no_practice', ('practice',))
_abl('m_no_traders', ('traders',))
_abl('m_no_altars', ('altars',))
ABLATIONS = ('m_no_tactics', 'm_no_study', 'm_no_cooking', 'm_no_quests', 'm_no_pet',
             'm_no_magic', 'm_no_prayer', 'm_no_context', 'm_no_practice', 'm_no_traders',
             'm_no_altars')

# (profile, knob string, tag, answer-time multiplier)
SETS = {
    'targets': [('mastery', '', 'm', 1.0), ('mastery', '', 'm', 1.5),
                ('mastery_mage', '', 'm', 1.0), ('mastery_dex', '', 'm', 1.0),
                ('committed', '', 'base', 1.0), ('casual', '', 'base', 1.0)],
    'ablate': [(n, '', 'abl', 1.0) for n in ABLATIONS],
    # The defence model (2026-11-16): the plate kid (mastery, STR and CON)
    # against the Dexterity kid, the two that ignore systems, and the Secret
    # Builds the kids play (difficulty_sim.BUILD_CELLS).
    'defence': ([('mastery', '', 'm', 1.0), ('mastery_dex', '', 'm', 1.0),
                 ('committed', '', 'base', 1.0), ('casual', '', 'base', 1.0)]
                + [(n, '', 'build', 1.0) for n in ds.BUILD_CELLS]),
    'builds': [(n, '', 'build', 1.0) for n in ds.BUILD_CELLS],
}
SETS['all'] = SETS['targets'] + SETS['ablate']


def _low_priority():
    """Below-normal priority for a worker (Windows; elsewhere a nice of 10)."""
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)      # BELOW_NORMAL_PRIORITY_CLASS
    except Exception:
        try:
            os.nice(10)
        except Exception:
            pass


def _set(name):
    """A named set, or one cell: a profile name, as profile[@speed]."""
    if name in SETS:
        return SETS[name]
    prof, _, speed = name.partition('@')
    if prof not in ds.PROFILES:
        raise SystemExit(f"unknown set or profile {name!r}: sets {', '.join(SETS)}")
    tag = ('abl' if prof.startswith('m_no_') else 'm' if prof.startswith('mastery')
           else 'build' if prof in ds.BUILD_CELLS else 'base')
    return [(prof, '', tag, float(speed or 1.0))]


def cells(sets, trials):
    out = []
    i = 0
    for s in sets:
        for prof, knob, tag, speed in _set(s):
            for c in range(0, trials, CHUNK):
                out.append(dict(profile=prof, accuracy=ACCURACY, trials=min(CHUNK, trials - c),
                                floors=(1, 100), knobs=ds.parse_knobs(knob), speed=speed,
                                seed=7 + 1000 * i + c, variants=24, kid=True,
                                _tag=tag, _key=(prof, tag, speed)))
            i += 1
    return out


def run(kw):
    t0 = time.time()
    tag, key = kw.pop('_tag'), kw.pop('_key')
    res = ds.run_cell(**kw)
    res['key'], res['tag'], res['wall'] = key, tag, time.time() - t0
    return res


def merge(a, b):
    if a is None:
        return b
    ds.merge_stats(a['stats'], b['stats'])
    a['boss_rows'] += b['boss_rows']
    a['trials'] += b['trials']
    a['wall'] += b['wall']
    return a


def main(argv):
    out_dir, trials = argv[0], int(argv[1])
    sets = argv[2:] or ['all']
    os.makedirs(out_dir, exist_ok=True)
    cs = cells(sets, trials)
    workers = min(len(cs), int(os.environ.get('MC_WORKERS') or 12))
    print(f"{len(cs)} chunks x {CHUNK} runs on {workers} workers", flush=True)
    import multiprocessing as mp
    t0 = time.time()
    merged = {}
    with mp.Pool(workers, initializer=_low_priority) as pool:
        for res in pool.imap_unordered(run, cs):
            merged[res['key']] = merge(merged.get(res['key']), res)
            print(f"chunk {res['key']} done ({time.time() - t0:.0f}s)", flush=True)
    for (prof, tag, speed), res in merged.items():
        res['label'] = (prof, ACCURACY, speed, True)
        with open(os.path.join(out_dir, f"{prof}_{tag}_{speed}.pkl"), 'wb') as f:
            pickle.dump(res, f)
    print(f"all done in {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
