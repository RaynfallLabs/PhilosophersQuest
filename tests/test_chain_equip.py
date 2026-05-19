"""Tests for the chain-equip mechanic on legendary unique armor/accessories.

Established 2026-05-18 from the legendary-uniques design pass:

  - Items with `equip_chain_mode` ('escalator' or 'chain') + `tier_bonuses` dict
    trigger a chain quiz on equip instead of threshold.
  - The chain length reached -> achieved_tier -> tier_bonuses[tier] applied.
  - Fresh quiz every equip (no sticky state).
  - apply_tier_bonuses mutates player state; revert_tier_bonuses undoes.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
pygame.init()
pygame.font.init()


def _make_shield(**overrides):
    from items import Shield
    defn = {
        'id': 'test_shield', 'name': 'test shield', 'symbol': ']',
        'color': [200, 200, 200], 'ac_bonus': 2, 'slot': 'shield',
    }
    defn.update(overrides)
    return Shield(defn)


def _make_armor(**overrides):
    from items import Armor
    defn = {
        'id': 'test_armor', 'name': 'test armor', 'symbol': '[',
        'color': [200, 200, 200], 'ac_bonus': 3, 'slot': 'body',
    }
    defn.update(overrides)
    return Armor(defn)


def _make_accessory(**overrides):
    from items import Accessory
    defn = {
        'id': 'test_ring', 'name': 'test ring', 'symbol': '=',
        'color': [200, 200, 200], 'slot': 'ring',
        'effects': {'stat': 'STR', 'amount': 1},
    }
    defn.update(overrides)
    return Accessory(defn)


class FakePlayer:
    def __init__(self):
        self.STR = self.CON = self.DEX = self.INT = self.WIS = self.PER = 10
        self.status_effects = {}
        self.damage_resistances = {}
        self.regen_bonus = 0
        self._stat_bonus_log = []

    def apply_stat_bonus(self, stat, amount):
        cur = getattr(self, stat)
        setattr(self, stat, cur + amount)
        self._stat_bonus_log.append((stat, amount))


# ---------------------------------------------------------------------------
# Detection: is_chain_equip
# ---------------------------------------------------------------------------

def test_is_chain_equip_false_for_default_item():
    from chain_equip import is_chain_equip
    s = _make_shield()
    assert is_chain_equip(s) is False


def test_is_chain_equip_true_when_both_mode_and_bonuses_set():
    from chain_equip import is_chain_equip
    s = _make_shield(equip_chain_mode='escalator',
                     tier_bonuses={'1': {'ac_bonus': 3}})
    assert is_chain_equip(s) is True


def test_is_chain_equip_false_with_mode_but_no_bonuses():
    from chain_equip import is_chain_equip
    s = _make_shield(equip_chain_mode='escalator')  # no tier_bonuses
    assert is_chain_equip(s) is False


# ---------------------------------------------------------------------------
# Subject defaulting
# ---------------------------------------------------------------------------

def test_chain_subject_defaults_to_geography_for_shield():
    from chain_equip import get_chain_subject
    s = _make_shield(equip_chain_mode='escalator', tier_bonuses={'1': {}})
    assert get_chain_subject(s) == 'geography'


def test_chain_subject_defaults_to_history_for_ring():
    from chain_equip import get_chain_subject
    a = _make_accessory(equip_chain_mode='escalator', tier_bonuses={'1': {}})
    assert get_chain_subject(a) == 'history'


def test_chain_subject_override_takes_precedence():
    from chain_equip import get_chain_subject
    a = _make_accessory(equip_chain_mode='chain',
                         equip_chain_subject='math',
                         tier_bonuses={'1': {}})
    assert get_chain_subject(a) == 'math'


# ---------------------------------------------------------------------------
# get_tier_bonuses
# ---------------------------------------------------------------------------

def test_get_tier_bonuses_returns_empty_for_unknown_tier():
    from chain_equip import get_tier_bonuses
    s = _make_shield(equip_chain_mode='escalator',
                     tier_bonuses={'1': {'ac_bonus': 3}})
    assert get_tier_bonuses(s, 2) == {}


def test_get_tier_bonuses_accepts_int_or_str_keys():
    from chain_equip import get_tier_bonuses
    s_str = _make_shield(equip_chain_mode='escalator',
                         tier_bonuses={'3': {'ac_bonus': 5}})
    s_int = _make_shield(equip_chain_mode='escalator',
                         tier_bonuses={3: {'ac_bonus': 5}})
    assert get_tier_bonuses(s_str, 3) == {'ac_bonus': 5}
    assert get_tier_bonuses(s_int, 3) == {'ac_bonus': 5}


# ---------------------------------------------------------------------------
# apply_tier_bonuses
# ---------------------------------------------------------------------------

def test_apply_ac_bonus_overrides_item_ac():
    from chain_equip import apply_tier_bonuses
    p = FakePlayer()
    s = _make_shield(ac_bonus=2, equip_chain_mode='escalator',
                     tier_bonuses={'3': {'ac_bonus': 6}})
    apply_tier_bonuses(p, s, 3)
    assert s.ac_bonus == 6
    assert s.achieved_tier == 3


def test_apply_resistance_adds_to_player():
    from chain_equip import apply_tier_bonuses
    p = FakePlayer()
    s = _make_shield(equip_chain_mode='escalator',
                     tier_bonuses={'2': {'resistance_fear': 2}})
    apply_tier_bonuses(p, s, 2)
    assert p.damage_resistances.get('fear') == 2


def test_apply_stat_bonus_increases_player_stat():
    from chain_equip import apply_tier_bonuses
    p = FakePlayer()
    a = _make_accessory(equip_chain_mode='escalator',
                         tier_bonuses={'2': {'stat_bonus_WIS': 2}})
    base = p.WIS
    apply_tier_bonuses(p, a, 2)
    assert p.WIS == base + 2


def test_apply_passive_stored_on_item():
    from chain_equip import apply_tier_bonuses
    p = FakePlayer()
    s = _make_shield(equip_chain_mode='escalator',
                     tier_bonuses={'5': {'passive_aura_of_awe': True}})
    apply_tier_bonuses(p, s, 5)
    assert s._chain_passives.get('aura_of_awe') is True


def test_apply_unknown_key_stored_verbatim():
    from chain_equip import apply_tier_bonuses
    p = FakePlayer()
    s = _make_shield(equip_chain_mode='escalator',
                     tier_bonuses={'4': {'reflect_spell_chance': 0.15}})
    apply_tier_bonuses(p, s, 4)
    assert s._chain_passives.get('reflect_spell_chance') == 0.15


# ---------------------------------------------------------------------------
# revert_tier_bonuses (unequip)
# ---------------------------------------------------------------------------

def test_revert_restores_baseline_ac():
    from chain_equip import apply_tier_bonuses, revert_tier_bonuses
    p = FakePlayer()
    s = _make_shield(ac_bonus=2, equip_chain_mode='escalator',
                     tier_bonuses={'5': {'ac_bonus': 6}})
    apply_tier_bonuses(p, s, 5)
    assert s.ac_bonus == 6
    revert_tier_bonuses(p, s)
    assert s.ac_bonus == 2
    assert s.achieved_tier == 0


def test_revert_removes_resistance():
    from chain_equip import apply_tier_bonuses, revert_tier_bonuses
    p = FakePlayer()
    s = _make_shield(equip_chain_mode='escalator',
                     tier_bonuses={'2': {'resistance_fire': 2}})
    apply_tier_bonuses(p, s, 2)
    revert_tier_bonuses(p, s)
    assert 'fire' not in p.damage_resistances


def test_revert_reverts_stat_bonus():
    from chain_equip import apply_tier_bonuses, revert_tier_bonuses
    p = FakePlayer()
    a = _make_accessory(equip_chain_mode='escalator',
                         tier_bonuses={'3': {'stat_bonus_INT': 3}})
    base = p.INT
    apply_tier_bonuses(p, a, 3)
    revert_tier_bonuses(p, a)
    assert p.INT == base


def test_revert_safe_when_no_chain_applied():
    """Calling revert on an item that was never apply'd should not error."""
    from chain_equip import revert_tier_bonuses
    p = FakePlayer()
    s = _make_shield()
    revert_tier_bonuses(p, s)  # no-op
    assert s.achieved_tier == 0


# ---------------------------------------------------------------------------
# Round-trip: apply + revert leaves player baseline
# ---------------------------------------------------------------------------

def test_round_trip_leaves_player_unchanged():
    from chain_equip import apply_tier_bonuses, revert_tier_bonuses
    p = FakePlayer()
    baseline = (p.STR, p.CON, p.DEX, p.INT, p.WIS, p.PER,
                dict(p.damage_resistances), p.regen_bonus)
    a = _make_accessory(equip_chain_mode='escalator',
                         tier_bonuses={
                             '5': {
                                 'stat_bonus_WIS': 3,
                                 'stat_bonus_INT': 2,
                                 'resistance_fire': 1,
                                 'resistance_magic': 2,
                                 'regen_bonus': 2,
                                 'passive_named_ability': True,
                             }
                         })
    apply_tier_bonuses(p, a, 5)
    revert_tier_bonuses(p, a)
    after = (p.STR, p.CON, p.DEX, p.INT, p.WIS, p.PER,
             dict(p.damage_resistances), p.regen_bonus)
    assert baseline == after


# ---------------------------------------------------------------------------
# Regression: main.py:_start_chain_equip_quiz reads result.score (NOT .chain).
# QuizResult dataclass only has success/score/correct/asked. A previous version
# read result.chain which silently always returned 0, breaking all 24 uniques.
# ---------------------------------------------------------------------------

def test_quiz_result_score_not_chain():
    """The quiz result attribute is `.score`, not `.chain`. Lock this in."""
    from quiz_engine import QuizResult
    # QuizResult is a dataclass; instantiate one and confirm fields
    qr = QuizResult(success=True, score=4, correct=4, asked=4)
    assert qr.score == 4
    assert not hasattr(qr, 'chain'), (
        'QuizResult gained a .chain attribute — main.py:_start_chain_equip_quiz '
        'previously read .chain which always returned 0 default. If you add '
        '.chain, update the callback to prefer it or this comment becomes stale.'
    )


def test_chain_equip_callback_uses_score_attribute():
    """The chain-equip on_complete callback in main.py must read result.score
    (not .chain). String-grep test that catches the regression directly."""
    import os
    main_py = os.path.join(os.path.dirname(__file__), '..', 'src', 'main.py')
    with open(main_py, encoding='utf-8') as f:
        src = f.read()
    # Find the chain-equip on_complete body. The callback lives inside
    # _start_chain_equip_quiz; we just want to confirm `getattr(result, 'chain'`
    # does NOT appear in that file.
    assert "getattr(result, 'chain'" not in src, (
        'main.py reads result.chain — this attribute does not exist on '
        'QuizResult. Use result.score instead. See commit history for context.'
    )
    assert 'getattr(result, "chain"' not in src
