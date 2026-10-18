"""DEEDS_KARMA_DESIGN 8.2: the karma-budget Monte Carlo on the SHIPPED data,
asserted (Phase 3, gate on). tools/balance/karma_sim.py is the simulator;
this runs it seeded at N = 4,000 per style and checks Brandon's bands
(section 11, decision 10, and 3.5):

| Style        | Sword (karma >= 8 at Judgment) |
|--------------|--------------------------------|
| Saint        | 60% to 80% ("about 7 in 10")   |
| Naive helper | at most 5%                     |
| Pragmatist   | at most 2%                     |
| Inconsistent | at most 3%                     |
| Villain      | 0%                             |

The saint's band is NOT met by the shipped content (about 99%: every block
offers two or three certain chances, decision 5, and a saint who takes the
principled path 80% of the time nearly always fills all ten slots). Swapping
a few +1s cannot reach it while every block keeps two expected chances; see
ENCOUNTER_STORIES_DRAFT.md Part J6. That test is a strict xfail until Brandon
decides between the two targets: when content or rules bring the saint into
the band it fails as XPASS, and the marker must come off.

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


@pytest.mark.xfail(strict=True, reason=(
    "Brandon's decision pending (Phase 3 report, ENCOUNTER_STORIES_DRAFT J6): the "
    "saint earns the Sword about 99% of runs with two to three certain chances a "
    "block; the 60-80% band and decision 5 cannot both hold without a rules or "
    "content change he has to choose."))
def test_a_saint_earns_the_sword_about_seven_in_ten(report):
    assert 0.60 <= report['styles']['saint']['sword'] <= 0.80
