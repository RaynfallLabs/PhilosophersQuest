"""Phase 5 of the rebalance (2026-10): who you are.

Decision D5: a hero's named weapon grows with the dungeon instead of being
thrown away on floor 12; the starting edge fades on its own.
"""
import copy
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import floor_curve  # noqa: E402
import items  # noqa: E402

SIGNATURE = ('achilles_spear', 'romulus_spear', 'prometheus_torch',
             'witcher_silver_blade', 'zireael', 'boomstick')


def _weapon(wid, grows=True):
    w = copy.copy(next(x for x in items.load_items('weapon') if x.id == wid))
    if grows:
        w.grows_with_depth = True
    return w


# ------------------------------------------------------------ traits (quirks), D6

def test_trait_stat_points_are_paid_from_an_allowance_that_grows_with_depth():
    from player import Player
    p = Player()
    assert p.quirk_stat_room() == 4
    p._quirk_grant = True
    p.apply_stat_bonus('STR', 3)                     # a trait's reward
    p.apply_stat_bonus('CON', 5)                     # another: only 1 fits today
    p._quirk_grant = False
    assert p.STR == 13 and p.CON == 11 and p.quirk_stat_room() == 0
    assert p.quirk_stat_owed == [['CON', 4]]         # nothing earned is lost
    p.deepest_floor_reached = 16                     # allowance 4 + 2
    assert p.pay_quirk_stats_owed() == [('CON', 2)] and p.CON == 13
    assert p.quirk_stat_owed == [['CON', 2]]
    p.deepest_floor_reached = 100                    # allowance 16
    assert p.pay_quirk_stats_owed() == [('CON', 2)] and not p.quirk_stat_owed
    p.apply_stat_bonus('DEX', 9)                     # not a trait: no allowance involved
    assert p.DEX == 19
    p._quirk_grant = True
    p.apply_stat_bonus('STR', -2)                    # a trait that costs a stat still costs it
    p._quirk_grant = False
    assert p.STR == 11


def test_a_traits_clock_seconds_become_counted_wisdom():
    import types
    import quirk_system
    from player import Player
    p = Player()
    msgs = []
    qs = quirk_system.QuirkSystem.__new__(quirk_system.QuirkSystem)
    qs.game = types.SimpleNamespace(player=p, add_message=lambda t, k='info': msgs.append(t))

    def reward(pl):
        pl.quiz_timer_bonuses['math'] = pl.quiz_timer_bonuses.get('math', 0) + 3
    wis = p.WIS
    qs._apply_within_caps(reward)
    assert p.quiz_timer_bonuses.get('math', 0) == 0 and p.WIS == wis + 3
    assert p.get_quiz_timer('math') == 10 + 3
    qs._apply_within_caps(reward)                    # allowance (4) nearly spent
    assert p.WIS == wis + 4 and p.quirk_stat_owed == [['WIS', 2]]
    assert any('Held For You' in m for m in msgs)
    assert p._quirk_grant is False


def test_every_trait_award_goes_through_the_caps():
    src = open(os.path.join(ROOT, 'src', 'quirk_system.py'), encoding='utf-8').read()
    assert src.count('self._apply_within_caps(apply_fn)') == 2
    assert 'apply_fn(self._pl)' not in src
    main = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    assert 'pay_quirk_stats_owed()' in main


# --------------------------------------------------------------- curses, D7

def test_an_item_marked_cannot_be_cursed_is_never_found_cursed():
    import random
    import types
    from dungeon import _assign_buc
    rng = random.Random(1)
    holy = types.SimpleNamespace(item_class='armor', can_be_cursed=False, buc='uncursed')
    plain = types.SimpleNamespace(item_class='armor', buc='uncursed')
    seen_holy, seen_plain = set(), set()
    for _ in range(600):
        _assign_buc(holy, 90, rng)
        seen_holy.add(holy.buc)
        _assign_buc(plain, 90, rng)
        seen_plain.add(plain.buc)
    assert 'cursed' not in seen_holy and 'cursed' in seen_plain
    marked = [i for cls in ('armor', 'shield', 'accessory') for i in items.load_items(cls)
              if not getattr(i, 'can_be_cursed', True)]
    assert len(marked) > 50                                   # the field is read now
    unmarked = [i for i in items.load_items('armor') if getattr(i, 'can_be_cursed', True)]
    assert unmarked                                           # absent means it can be


def test_chest_and_drop_loot_is_still_never_cursed():
    """Decision D7: cursed loot comes from the ground only."""
    for name in ('container_system.py', 'game_combat.py'):
        src = open(os.path.join(ROOT, 'src', name), encoding='utf-8').read()
        assert 'buc=False' in src, name
