"""Monster spawn curve vs the balance anchors (2026-10 content pass).

Before this pass each monster's HP was scaled to the anchor for its
`min_level`, but it actually spawned around a `peak_floor` 6 to 12 floors
deeper, so the monsters met on floors 8 to 35 had a fifth to a half of the
intended HP and died to a one-answer chain. `tools/balance/respawn_by_hp.py`
re-seated every random spawn on the floor its own HP fits. These tests keep
the data from drifting back.

Play-testing 100 floors of spawn RNG is not realistic, so this is the
data-layer guard.
"""
import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import respawn_by_hp as rs  # noqa: E402
from dungeon import _build_spawn_pool  # noqa: E402


@pytest.fixture(scope='module')
def monsters():
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope='module')
def placement(monsters):
    return {mid: (d['peak_floor'], d['spread'], d['min_level'])
            for mid, d in monsters.items() if rs.is_random_spawn(d)}


def test_tool_mirror_matches_the_real_spawn_pool(monsters, placement):
    """The tool's pool model must be the game's pool, or every number below
    is about a different game."""
    for lvl in (1, 7, 20, 33, 50, 68, 85, 100):
        real = {k: v['_spawn_freq'] for k, v in _build_spawn_pool(lvl).items()}
        model = rs.pool_at(monsters, placement, lvl)
        assert set(real) == set(model), lvl
        for k in real:
            assert real[k] == pytest.approx(model[k]), (lvl, k)


def test_median_monster_hp_tracks_the_anchor_on_every_floor(monsters, placement):
    """The typical monster on a floor has between 0.55x and 1.25x the anchor
    HP for that floor (CURVE.md bands are roughly 0.55x to 1.45x)."""
    off = []
    for lvl in range(1, 101):
        st = rs.floor_stats(monsters, placement, lvl)
        ratio = st['hp50'] / rs.target_hp(lvl)
        if not 0.55 <= ratio <= 1.25:
            off.append((lvl, round(ratio, 2)))
    assert not off, off


def test_every_floor_has_variety(monsters, placement):
    """No floor is down to a handful of monster kinds."""
    thin = []
    for lvl in range(1, 101):
        st = rs.floor_stats(monsters, placement, lvl)
        if st['kinds'] < 20 or st['neff'] < 8:
            thin.append((lvl, st['kinds'], round(st['neff'], 1)))
    assert not thin, thin


def test_no_early_one_shot_spikes(monsters, placement):
    """A monster may first appear only on floors where its hardest single
    attack is under 5x the floor's anchor damage. (An air elemental hitting
    for 19 could be met on floor 4 before this pass.)"""
    bad = []
    for mid, (peak, _spread, min_level) in placement.items():
        spike = rs.max_attack(monsters[mid])
        if spike > 5.0 * rs.target_dmg(min_level):
            bad.append((mid, min_level, spike))
    assert not bad, bad


def test_weak_monsters_do_not_linger_deep(monsters, placement):
    """A monster stops spawning once the floor's anchor HP is more than about
    eight times its own. (Giant rats were still in the pool on floor 35.)"""
    bad = []
    for mid, (peak, spread, _min) in placement.items():
        hp = rs.dice_avg(monsters[mid]['hp'])
        last = max((lvl for lvl in range(1, 101)
                    if mid in rs.pool_at(monsters, {mid: placement[mid]}, lvl)), default=peak)
        if rs.target_hp(last) > 8.0 * hp:
            bad.append((mid, hp, last))
    assert not bad, bad[:10]


def test_respawn_tool_is_idempotent(monsters, placement):
    """Running the tool on its own output proposes no change, so a future
    hand-edit that drifts off the curve shows up as a diff."""
    copy = json.loads(json.dumps(monsters))
    assert rs.apply_stat_fixes(copy) == []
    assert rs.plan(copy) == placement


def test_named_foes_outlast_the_ordinary_monsters_around_them(monsters):
    """Mini-bosses and seal demons have at least ~2x the anchor HP of their
    floor. (Seal demons had 370 to 520 HP on floors where a common monster
    had 1,100.)"""
    weak = []
    for mid, d in monsters.items():
        if not (d.get('is_mini_boss') or d.get('is_seal_demon')):
            continue
        want = 1.9 * rs.target_hp(d['peak_floor'])
        if rs.dice_avg(d['hp']) < want:
            weak.append((mid, rs.dice_avg(d['hp']), round(want)))
    assert not weak, weak


def test_giant_ladder_follows_the_lore(monsters):
    """stone < frost < fire < cloud < storm, all under the giant kings."""
    hp = {k: rs.dice_avg(monsters[k]['hp']) for k in (
        'hill_giant', 'stone_giant', 'frost_giant', 'fire_giant', 'cloud_giant',
        'storm_giant', 'frost_giant_jarl', 'fire_giant_king', 'elder_storm_giant')}
    order = ['hill_giant', 'stone_giant', 'frost_giant', 'fire_giant',
             'cloud_giant', 'storm_giant', 'elder_storm_giant']
    for a, b in zip(order, order[1:]):
        assert hp[a] < hp[b], (a, hp[a], b, hp[b])
    assert hp['frost_giant'] < hp['frost_giant_jarl']
    assert hp['fire_giant'] < hp['fire_giant_king']


def test_young_red_dragon_does_not_out_hit_the_adult(monsters):
    assert rs.max_attack(monsters['young_red_dragon']) < rs.max_attack(monsters['adult_red_dragon'])
