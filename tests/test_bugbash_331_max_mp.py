"""Bug bash 3.3.1, A8: the First Insight wiped gear's max MP.

Game._check_philosopher_thresholds (25 identifications, +1 INT) did
``p.INT += 1; p.max_mp = p.BASE_MP + p.INT``: the maximum was rebuilt from
scratch, so every point of max MP lent by gear (and every trophy and cooked
point) was thrown away. Wearing the Robe of the Magus: 43 -> 24, and 1 once
the robe came off and took its share back. The point now goes through
Player.apply_stat_bonus, which moves max MP by the one point.

The real Game method, on a real Player wearing the real robe (attuned by
chain_equip.apply_tier_bonuses, as the attune quiz does).
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import items  # noqa: E402
from player import Player  # noqa: E402


class _Harness:
    """Just enough of the Game for the threshold method (no Pygame)."""
    def __init__(self):
        self.player = Player()
        self.lines = []

    def add_message(self, t, _typ='info'):
        self.lines.append(t)

    def _chron(self, kind, text, **kw):
        pass


def _first_insight(h):
    import main
    h.player.total_identifies = 25
    main.Game._check_philosopher_thresholds(h)


def _wear_robe(p, tier=5):
    from chain_equip import apply_tier_bonuses
    robe = items.make_item_by_id('armor', 'robe_of_the_magus')
    apply_tier_bonuses(p, robe, tier)
    p._apply_equip(robe)
    return robe


def test_first_insight_keeps_the_max_mp_gear_lends():
    h = _Harness()
    p = h.player
    plain = p.max_mp
    robe = _wear_robe(p)
    worn = p.max_mp
    assert worn > plain + 10                         # the robe lends a lot
    int0 = p.INT
    _first_insight(h)
    assert p.INT == int0 + 1
    assert p.max_mp == worn + 1                      # one point more, nothing lost
    # The robe off again: back to the plain maximum plus the point earned.
    idx = p.armor_slots.index(robe)
    p.armor_slots[idx] = None
    p.shed_worn_grants(robe)
    assert p.max_mp == plain + 1


def test_first_insight_still_gives_the_point_of_mp_now():
    h = _Harness()
    p = h.player
    p.mp = p.max_mp - 5
    before = p.mp
    _first_insight(h)
    assert p.mp == before + 1


def test_first_insight_keeps_trophy_mp():
    """Max MP from anything but INT (a trophy, a cooked meal) is kept too."""
    h = _Harness()
    p = h.player
    p.max_mp += 7
    grown = p.max_mp
    _first_insight(h)
    assert p.max_mp == grown + 1
