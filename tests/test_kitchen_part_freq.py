"""A recipe book a run can actually cook (kitchen rebuild, slice K1b).

The simulator measured how often each harvestable part turns up in a mastery
run (tools/content/kitchen/part_freq.json, made by part_freq.py). Brandon's
aim: big payoff meals a kid earns by hunting and saving parts, not by luck.
These data tests read the game data and that file and pin the rules:

1. a legendary feast's gate is its trophy (or the boss part a trophy-less
   feast is keyed to, its first ingredient); every other part is common, or an
   early part a saving hero reliably banks;
2. an ordinary multi-dish holds at most one uncommon part;
3. about a third of the multi-dishes span depths, mostly joining an early
   common part (saved parts, rations, cheese) with a deep one;
4. every ingredient is still in exactly one single dish and two or more
   multi-dishes, and every tab has dishes at every depth band.

Whether saving a part for a deep dish FEELS worth it is a play-test question.
"""
import json
import os
from collections import Counter

ROOT = os.path.join(os.path.dirname(__file__), '..')


def _json(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return json.load(f)


RECIPES = _json('data', 'items', 'recipes.json')
INGS = _json('data', 'items', 'ingredient.json')
FOOD = _json('data', 'items', 'food.json')
FREQ = _json('tools', 'content', 'kitchen', 'part_freq.json')
RULES = FREQ['rules']
PARTS = FREQ['parts']
RARE_FOOD = {fid for fid, r in FOOD.items()
             if r.get('floor_spawn_weight') and max(r['floor_spawn_weight'].values()) < RULES['rare_food_weight']}


def _parts(r):
    return list(dict.fromkeys(r['ingredients']))


def _is_helper(p):
    """Food or a foraged find (no frequency: food spawns, forage is found and sold)."""
    return p in FOOD or INGS.get(p, {}).get('tier_role') == 'dungeon'


def _share(p):
    if _is_helper(p):
        return 0.0 if p in RARE_FOOD else 1.0
    return PARTS[p]['share_of_runs']


def _common(p):
    if _is_helper(p):
        return p not in RARE_FOOD
    return _share(p) >= RULES['common_share']


def _banked(p):
    if _is_helper(p):
        return False
    ff = PARTS[p]['median_first_floor']
    return ff is not None and ff <= RULES['early_floor'] and _share(p) >= RULES['early_share']


def _floor(p):
    return INGS[p]['min_level'] if p in INGS else FOOD[p]['min_level']


def _multis():
    return {k: v for k, v in RECIPES.items() if len(_parts(v)) > 1}


def test_the_frequency_file_covers_every_harvestable_part_and_says_where_it_came_from():
    assert 'part_freq.py' in FREQ['_doc'] and FREQ['runs'] >= 10
    harvestable = {k for k, v in INGS.items() if v['tier_role'] in ('prime', 'trophy')}
    assert harvestable <= set(PARTS), sorted(harvestable - set(PARTS))[:10]
    assert {'philosopher_tea', 'deep_fungi', 'void_ration'} <= RARE_FOOD
    assert not RARE_FOOD & {'bread_ration', 'hard_cheese', 'trail_rations', 'dried_meat', 'apple'}


def test_rule_1_a_feast_is_gated_by_its_trophy_and_effort_not_luck():
    feasts = {k: v for k, v in RECIPES.items() if v.get('legendary')}
    assert len(feasts) == 36
    for fid, r in feasts.items():
        ps = _parts(r)
        trophies = [p for p in ps if INGS.get(p, {}).get('tier_role') == 'trophy']
        assert len(trophies) <= 1, fid
        if trophies:
            assert ps[0] == trophies[0], (fid, 'the trophy is the gate')
        for p in ps[1:]:
            assert _common(p) or _banked(p), (fid, r['name'], p, _share(p))
        given_gate = 1.0
        for p in ps[1:]:
            given_gate *= _share(p)
        assert given_gate >= 0.5, (fid, given_gate)


def test_rule_2_an_ordinary_dish_holds_at_most_one_uncommon_part():
    for rid, r in _multis().items():
        if r.get('legendary') or r.get('song'):
            continue        # a song's dish is two rare foods by design (songs.py)
        rare = [p for p in _parts(r) if not _common(p)]
        assert len(rare) <= 1, (rid, r['name'], rare)


def test_a_part_no_run_turns_up_is_secret_or_paired_with_common_partners():
    never = [p for p, f in PARTS.items() if f['share_of_runs'] == 0]
    assert never, 'the file should still show the parts the simulator never meets'
    for p in never:
        dishes = [r for r in _multis().values() if p in r['ingredients']]
        assert len(dishes) >= 2, p
        for r in dishes:
            assert all(_common(q) for q in _parts(r) if q != p), (p, r['name'])


def test_rule_3_about_a_third_span_depths_mostly_from_an_early_common_part():
    multis = _multis()
    cross = [r for r in multis.values() if r.get('cross_depth')]
    assert 0.28 <= len(cross) / len(multis) <= 0.42, (len(cross), len(multis))
    early_common = [r for r in cross if any(_floor(p) <= 20 and _common(p) for p in _parts(r))]
    early_part = [r for r in cross if any(_floor(p) <= 20 and _common(p) and not _is_helper(p)
                                         for p in _parts(r))]
    assert len(early_common) >= 0.8 * len(cross), (len(early_common), len(cross))
    assert len(early_part) >= 0.5 * len(cross), (len(early_part), len(cross))


def test_rule_4_every_ingredient_keeps_one_single_and_two_multis_and_every_tab_every_band():
    singles, multis = Counter(), Counter()
    for r in RECIPES.values():
        ps = _parts(r)
        for p in ps:
            (singles if len(ps) == 1 else multis)[p] += 1
    for iid in INGS:
        assert singles[iid] == 1 and multis[iid] >= 2, (iid, singles[iid], multis[iid])
    import sys
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import kitchen
    seen = Counter()
    for r in kitchen.book():
        if not kitchen.is_secret(r):
            seen[(kitchen.dish_tab(r), kitchen.dish_tier(r))] += 1
    for tab in kitchen.MENU_TABS:
        for band in range(1, 6):
            assert seen[(tab, band)] >= 2, (tab, band)


def test_a_rare_part_found_means_its_dishes_can_be_cooked():
    """Most of the book is cookable in at least half of runs, and every feast
    once its trophy is won (the lead's measure before K1b: 112 of 257 multis,
    8 of 36 feasts)."""
    multis = _multis()

    def chance(ps):
        x = 1.0
        for p in ps:
            x *= _share(p) if not _is_helper(p) else 1.0
        return x
    half = sum(1 for r in multis.values() if chance(_parts(r)) >= 0.5)
    assert half >= 0.55 * len(multis), (half, len(multis))


def test_no_dish_is_named_just_like_an_ingredient():
    ing_names = {v['name'].lower() for v in INGS.values()}
    clash = [(k, r['name']) for k, r in RECIPES.items() if r['name'].lower() in ing_names]
    assert not clash, clash
