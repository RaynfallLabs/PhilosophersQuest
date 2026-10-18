"""DEEDS_KARMA_DESIGN 8.2: the karma-budget Monte Carlo on the SHIPPED data,
asserted (Phase 3, gate on). tools/balance/karma_sim.py is the simulator;
this runs it seeded at N = 4,000 per style and checks Brandon's bands
(section 11, decision 10, and 3.5):

| Style        | Sword (karma >= 8 at Judgment) |
|--------------|--------------------------------|
| Saint        | at least 85% (accepted ~99%)   |
| Naive helper | at most 5%                     |
| Pragmatist   | at most 2%                     |
| Inconsistent | at most 3%                     |
| Villain      | 0%                             |

The saint earns the Sword about 99% of runs: every block offers two or three
chances (decision 5) and a saint who takes the principled path 80% of the time
nearly always fills all ten slots. Brandon ACCEPTED this (2026-10-17): real
players never see karma or which option is principled, so their rate is lower,
and naive helpers stay under 5%. The saint test now only guards that a saint
reliably earns it (at least 85%), so a later change that makes principled play
stop paying is caught.

Slow (about 30 s): run with --run-slow (CI does).
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

N = 4000
SEED = 1

pytestmark = pytest.mark.slow


@pytest.fixture(scope='module')
def report():
    from tools.balance import karma_sim
    rep = karma_sim.run(n=N, seed=SEED)
    # Printed for the record (-s): P(karma < 0 at floor 30), for the unicorn.
    for name, r in rep['styles'].items():
        print(f"{name:13s} sword {r['sword']:.4f}  below zero at 30 {r['below_zero_at_30']:.4f}")
    return rep


def test_the_simulation_ran_on_the_shipped_data(report):
    import karma
    assert report['n'] == N and report['untyped_karma_options'] == 0
    assert report['oracle_max'] <= 12                     # 10 block slots + constancy 2
    assert karma.gate_enabled() is True                   # as shipped


def test_naive_kindness_almost_never_earns_the_sword(report):
    assert report['styles']['naive_helper']['sword'] <= 0.05


def test_the_pragmatist_does_not_earn_the_sword(report):
    assert report['styles']['pragmatist']['sword'] <= 0.02


def test_the_inconsistent_player_does_not_earn_the_sword(report):
    assert report['styles']['inconsistent']['sword'] <= 0.03


def test_the_villain_never_earns_the_sword(report):
    assert report['styles']['villain']['sword'] == 0.0
    assert report['styles']['villain']['below_zero'] >= 0.95


def test_a_saint_reliably_earns_the_sword(report):
    """Brandon, 2026-10-17: accepted that a principled-all-run player nearly
    always earns the Sword; guard that principle keeps paying."""
    assert report['styles']['saint']['sword'] >= 0.85
