"""Mini-bosses spread through the whole game by lore (Brandon's ruling 13,
2026-11-16): "mini-bosses with cool unique drops are supposed to be spread
through the whole game, maybe one or two every 20 floors; gear they drop
should be depth appropriate... Use lore to determine weaker vs later bosses."

The seats and the drops are data, written by tools/balance/mini_boss_seats.py
and tools/content/mini_boss_drops_2026_11_17.py; the plan is
level_manager.plan_mini_bosses. These are the data and plan tests: whether a
mini-boss fight FEELS decisive on its floor is Brandon's play-test (the
simulator's numbers are in the report of 2026-11-17).
"""
import json
import os
import pickle
import random
import statistics
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))

import pytest  # noqa: E402

import items  # noqa: E402
import level_manager  # noqa: E402
import mini_boss_seats as ms  # noqa: E402

BANDS = ((1, 20), (21, 40), (41, 60), (61, 80), (81, 100))
GATES = {20, 40, 60, 80, 100}
SEALS = set(level_manager.LevelManager._SEAL_DEMON_LEVELS)


def _data(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return json.load(f)


MONS = _data('data', 'monsters.json')


def band_of(floor):
    return (int(floor) - 1) // 20 + 1


def peak(mid):
    return int(MONS[mid]['peak_floor'])


# ------------------------------------------------------------------ the plan

def test_every_band_meets_one_or_two_named_foes():
    """Guaranteed: a run meets one or two mini-bosses in every 20-floor
    band, never none and never three, the legendary ones included."""
    rng = random.Random(20261117)
    per_band = {b: [] for b in range(1, 6)}
    for _ in range(600):
        plan = level_manager.plan_mini_bosses(
            MONS, rng, bands=level_manager.LevelManager._MINI_BOSS_BANDS,
            first=level_manager.LevelManager._MINI_BOSS_FIRST_CHANCE,
            second=level_manager.LevelManager._MINI_BOSS_SECOND_CHANCE,
            taken=GATES | SEALS)
        assert len(set(plan.values())) == len(plan)
        for floor, mid in plan.items():
            assert floor not in GATES and floor not in SEALS, (floor, mid)
            assert band_of(floor) == band_of(peak(mid)), (floor, mid)    # met in its own band
        for b in range(1, 6):
            per_band[b].append(sum(1 for f in plan if band_of(f) == b))
    for b, counts in per_band.items():
        assert min(counts) >= 1 and max(counts) <= 2, (b, min(counts), max(counts))
        assert 1.2 <= statistics.mean(counts) <= 1.4, (b, statistics.mean(counts))


def test_the_game_s_plan_is_the_band_plan():
    for _ in range(40):
        plan = level_manager.LevelManager()._planned_mini_bosses
        for b in range(1, 6):
            assert 1 <= sum(1 for f in plan if band_of(f) == b) <= 2, plan
        assert not [m for m in plan.values() if m.startswith('seal_demon')]


def test_an_old_save_meets_the_new_bands_ahead():
    """A run saved under the old plan keeps what is behind it and is planned
    by the bands for the floors still ahead (LevelManager._replan_ahead)."""
    import items as _items
    _items.bind_unique_registry(set())
    lm = level_manager.LevelManager()
    lm.max_level_reached = 33
    lm._saved = {}
    lm._planned_mini_bosses = {9: 'arachne', 55: 'nemean_lion', 85: 'tiamat', 90: 'surtur'}
    lm._placed_mini_bosses = {'arachne'}
    del lm.__dict__['_plan_version']                     # a save from before the field
    lm2 = pickle.loads(pickle.dumps(lm))
    plan = lm2._planned_mini_bosses
    assert lm2._plan_version == level_manager.LevelManager._PLAN_VERSION
    assert plan.get(9) == 'arachne'                      # behind the hero: kept
    assert 55 not in plan and 85 not in plan             # the old floors ahead: planned again
    for b in (3, 4, 5):
        assert 1 <= sum(1 for f in plan if band_of(f) == b) <= 2, plan
    for f, mid in plan.items():
        if f > 33:
            assert band_of(f) == band_of(peak(mid)), (f, mid)
    # A save made under the band plan is left as it is.
    lm3 = level_manager.LevelManager()
    assert pickle.loads(pickle.dumps(lm3))._planned_mini_bosses == lm3._planned_mini_bosses


# ------------------------------------------------------------- the seats

def test_the_seats_are_the_data():
    copy = json.loads(json.dumps(MONS))
    assert ms.apply(copy) == []
    rolled = {mid for lo, hi in BANDS for mid, _d, _p in level_manager.band_candidates(MONS, lo, hi)}
    assert rolled == set(ms.SEATS), sorted(rolled ^ set(ms.SEATS))
    for mid, (seat, why) in ms.SEATS.items():
        assert peak(mid) == seat and len(why) > 30, mid
        assert seat not in GATES and seat not in SEALS and seat % 20 != 19, (mid, seat)
    assert peak('euryale_gorgon') == peak('stheno_gorgon')


def test_every_band_has_a_field_of_four_or_more():
    for lo, hi in BANDS:
        n = len(level_manager.band_candidates(MONS, lo, hi))
        assert 4 <= n <= 8, (lo, hi, n)


def test_lore_orders_them():
    # The weaker legends shallow (Brandon: "a boar, a lamia, a bonnacon").
    assert peak('bonnacon') < peak('arachne') < peak('calydonian_boar') < peak('lamia') <= 20
    # The Nemean Lion is Heracles' first labour, the Hydra his second.
    assert peak('nemean_lion') < peak('hydra')
    # Talos guards Crete: the last before Minos' Labyrinth.
    assert max(peak(m) for m in ms.SEATS if peak(m) <= 20) == peak('talos')
    # The mother of monsters in the Gorgons' temple, the Sphinx after her.
    assert band_of(peak('echidna')) == 2 and peak('echidna') < peak('the_sphinx')
    # Medusa's sisters come for her killer after her floor.
    assert 40 < peak('stheno_gorgon') < 50
    # The winter things are Fenrir's.
    for mid in ('wendigo', 'wild_hunt_captain', 'ymir_last_spawn', 'jormungandr_juvenile'):
        assert 61 <= peak(mid) <= 79, mid
    # The world's end is Abaddon's.
    for mid in ('tiamat', 'surtur', 'asmodeus', 'nidhoggr_fragment', 'hrungnirs_ghost'):
        assert 81 <= peak(mid) <= 99, mid
    # The seven seals keep their floors (Abaddon's arc).
    for floor, mid in level_manager.LevelManager._SEAL_DEMON_LEVELS.items():
        assert peak(mid) == floor


# ------------------------------------------------------------- the drops

def _drop_tier(uid):
    made = items.made_drop(uid)
    if made is not None:
        import gear
        return gear.tier_for_level(int(made.ench_level)), made
    for cat in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll'):
        raw = _data('data', 'items', f'{cat}.json')
        if uid in raw:
            d = raw[uid]
            return int(d.get('tier') or d.get('quiz_tier')), d
    return None, None


def test_each_drop_is_one_signature_piece_of_its_band_s_tier():
    for mid, (seat, _why) in ms.SEATS.items():
        tr = MONS[mid]['treasure']
        uid = tr.get('unique_drop_id')
        if mid == 'tiamat':
            # Her five breaths: the Scroll of Chromatic Doom is her signature.
            assert not uid and tr['boss_scroll_id'] == 'scroll_of_chromatic_doom'
            assert _data('data', 'items', 'scroll.json')['scroll_of_chromatic_doom']['tier'] == 5
            continue
        assert uid == ms.DROPS[mid][0], mid
        tier, d = _drop_tier(uid)
        assert tier == band_of(seat), (mid, uid, tier, seat)
        if isinstance(d, dict):
            assert d.get('is_unique') and d.get('plot_locked'), uid
            assert int(d.get('quiz_tier', tier)) == tier, uid
            assert int(d.get('peak_floor')) == seat, uid
            if 'mathTier' in d:
                assert d['mathTier'] == tier, uid


def test_no_drop_is_random_loot_or_for_sale():
    import traders
    for mid in ms.SEATS:
        uid = MONS[mid]['treasure'].get('unique_drop_id')
        if not uid or uid.startswith('armor:'):
            continue
        cat = next(c for c in ('weapon', 'armor', 'shield', 'accessory', 'wand')
                   if uid in _data('data', 'items', f'{c}.json'))
        it = items.make_item_by_id(cat, uid)
        assert not items.is_random_loot(it), uid
        assert items.withheld(it), uid                     # no thief, no price takes it
        assert traders.is_quest_piece(it), uid             # no trader buys it


NEW_DROPS = ('calydonian_boar_hide', 'eyes_of_lamia', 'club_of_polyphemus', 'patriarchs_gavel',
             'brazen_hands_of_stheno', 'rangdas_keris', 'crones_burial_veil', 'exsanguinating_blade')


@pytest.mark.parametrize('uid', NEW_DROPS)
def test_a_new_drop_is_named_painted_and_told(uid):
    cat = next(c for c in ('weapon', 'armor', 'accessory') if uid in _data('data', 'items', f'{c}.json'))
    d = _data('data', 'items', f'{cat}.json')[uid]
    assert d['name'][0].isupper() and len(d['lore']) > 200, uid
    assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', f'{uid}.png')), uid
    assert uid in _data('tools', 'content', 'genart', 'installed_items.json')['items']
    it = items.make_item_by_id(cat, uid)
    assert it is not None and it.is_unique
    if cat == 'weapon':
        assert any(float(getattr(it, a, 0) or 0) > 0 for a in
                   ('stun_chance', 'confuse_chance', 'bleed_chance', 'lifesteal_percent')), uid
    else:
        assert str(getattr(it, 'special', '') or '').strip(), uid


def test_the_lion_s_hide_keeps_its_legend_at_its_new_tier():
    d = _data('data', 'items', 'armor.json')['hide_of_nemean_lion']
    assert d['tier'] == 1 and d['unskinnable'] is True
    assert d['damage_resistances'] == {}           # the halving alone: no stacked resistances


# ------------------------------------------------------- the new foe

def test_polyphemus_is_wired_into_every_system():
    import family_lore
    import tells
    from monster import Monster
    m = MONS['polyphemus']
    assert m['is_mini_boss'] and m['peak_weight'] == 0 and m['family'] == 'giants'
    assert m['omen'] and m['kill_chronicle'] and len(m['lore']) > 200
    assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters', 'polyphemus.png'))
    assert 'polyphemus' in _data('tools', 'content', 'genart', 'installed.json')
    family_lore.reload()
    assert family_lore._kinds()['polyphemus'] == ('giants', True)       # a keystone kind
    assert tells.abilities(Monster({**m, 'id': 'polyphemus'}, 0, 0))
    hm = _data('data', 'items', 'harvest_map.json')
    assert hm['monsters']['polyphemus'] == hm['monsters']['cyclops']    # the cyclopes' kin
    assert 'polyphemus' not in hm['people']
    assert _data('data', 'monster_sizes.json')['sizes']['polyphemus'] == 'huge'
    ach = {a['id']: a for a in _data('data', 'achievements.json')['achievements']}
    assert ach['quest_polyphemus']['trigger']['where']['monster'] == 'polyphemus'
    assert os.path.exists(os.path.join(ROOT, 'assets', 'achievements', 'quest_polyphemus.png'))


# ------------------------------------------------- the census and the sim

def test_the_census_finds_a_drop_where_its_foe_lives():
    import tier_census as tc
    for mid, (seat, _why) in ms.SEATS.items():
        uid = MONS[mid]['treasure'].get('unique_drop_id')
        if uid and not uid.startswith('armor:'):
            assert tc._dropped_by_mini_bosses()[uid] == seat, uid


def test_the_simulator_picks_up_the_signature_drop():
    import difficulty_sim as ds
    for mid in ms.SEATS:
        uid = MONS[mid]['treasure'].get('unique_drop_id')
        if uid:
            assert ds._signature_drop(uid) is not None, uid
