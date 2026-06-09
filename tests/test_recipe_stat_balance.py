"""Cooking stat grants must be spread roughly evenly across the SIX real stats
(2026-06-08).

User: "how many of these recipes give +1 strength? I have found very few that
give other." STR was 35% of recipes (216/620) because the bestiary is brute-
heavy and each prime recipe inherits its source monster's stat affinity; PER was
starved at 7%, and one recipe granted CHA -- which isn't a stat (apply_stat_bonus
would no-op). Rebalanced to ~17% each.
"""
import json
from collections import Counter
from pathlib import Path

_RECIPES = json.loads((Path(__file__).resolve().parents[1] / 'data' / 'items'
                       / 'recipes.json').read_text(encoding='utf-8'))
_VALID = {'STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'}


def _stat(rec):
    return rec.get('stat_grant') or rec.get('stat_grant_default') or 'STR'


def _counts():
    return Counter(_stat(r) for r in _RECIPES.values())


def test_no_recipe_grants_an_invalid_stat():
    bad = {s for s in _counts() if s not in _VALID}
    assert not bad, f"recipes grant non-stats (player has no such attr): {bad}"


def test_every_stat_is_well_represented():
    c = _counts()
    n = len(_RECIPES)
    even = n / 6
    for s in _VALID:
        # no stat below ~70% of an even share (i.e. not "starved" like old PER 7%)
        assert c[s] >= even * 0.7, f"{s} starved: {c[s]}/{n} (even≈{even:.0f})"


def test_str_is_not_dominant():
    c = _counts()
    # STR was 35%; after the rebalance no single stat may exceed ~20%.
    top = c.most_common(1)[0]
    assert top[1] <= len(_RECIPES) * 0.20, f"{top[0]} still dominates: {top[1]}/{len(_RECIPES)}"
