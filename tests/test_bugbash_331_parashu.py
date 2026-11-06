"""Bug bash 3.3.1, combat A1: the Parashu carry turned a miss into a hit.

The carry (chain_no_reset_on_tag) was added to a chain of 0, so after one
real kill a wrong first answer still landed; each kill stored the
carry-boosted chain, so it grew (five wrong answers in a row, five kills).
It also worked with any weapon in hand and never expired.

These drive the real combat.player_attack and effective_chain, and a real
Game for the floor change. A floor-61 unique cannot be play-tested in a
sitting.
"""
import json
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import combat  # noqa: E402
import items  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    _DEFS = json.load(_f)


def _unique(wid):
    return next(w for w in items.load_items('weapon') if w.id == wid)


def _target(kind='kobold', hp=10 ** 8):
    m = Monster(dict(_DEFS[kind], id=kind), 6, 5)
    m.hp = m.max_hp = hp
    return m


def _player(weapon=None):
    p = Player()
    p.x, p.y = 5, 5
    p.hp = p.max_hp = 10 ** 6
    if weapon is not None:
        if getattr(weapon, 'requires_ammo', None) is not None:
            p.ranged_weapon = weapon
        else:
            p.weapon = weapon
    return p


class _Quiz:
    """Stands in for QuizEngine: the attack's callback gets ``score``."""
    def __init__(self, score, struck_early=False):
        self.score = score
        self.struck_early = struck_early

    def start_quiz(self, callback=None, **_kw):
        callback(types.SimpleNamespace(score=self.score, success=True,
                                       struck_early=self.struck_early))


def _attack(p, m, score, struck_early=False, ranged=False):
    """(damage, killed, chain) of one real attack at quiz score ``score``."""
    got = []
    combat.player_attack(p, m, _Quiz(score, struck_early),
                         lambda dmg, killed, chain, *a, **k: got.append((dmg, killed, chain)),
                         ranged=ranged)
    return got[0]


def _kill_one(p, score=3):
    """A real kill of a humanoid with the Parashu: that is what sets the carry."""
    victim = _target('kobold', hp=1)
    dmg, killed, chain = _attack(p, victim, score)
    assert killed and dmg > 0
    return chain


# ---------------------------------------------------------------- A1 Parashu

def test_parashu_carry_never_turns_a_wrong_first_answer_into_a_hit():
    p = _player(_unique('parashu'))
    _kill_one(p)
    assert int(getattr(p, '_chain_carry', 0) or 0) > 0          # the rhythm is kept
    dmg, killed, chain = _attack(p, _target('kobold'), 0)
    assert (dmg, chain) == (0, 0)                               # a miss is a miss


def test_five_wrong_answers_after_one_kill_are_five_misses():
    p = _player(_unique('parashu'))
    _kill_one(p)
    for _ in range(5):
        victim = _target('kobold', hp=1)
        dmg, killed, chain = _attack(p, victim, 0)
        assert (dmg, killed, chain) == (0, False, 0)


def test_parashu_carry_is_spent_by_a_miss():
    p = _player(_unique('parashu'))
    _kill_one(p)
    _attack(p, _target('kobold'), 0)
    assert int(getattr(p, '_chain_carry', 0) or 0) == 0
    # The next landed blow is the plain chain again.
    assert combat.effective_chain(p, _target('kobold'), p.weapon, 2, consume=False) == 2


def test_parashu_carry_does_not_grow_kill_after_kill():
    p = _player(_unique('parashu'))
    first = _kill_one(p, score=3)
    assert p._chain_carry == first == 3
    for _ in range(4):
        _kill_one(p, score=3)
        assert p._chain_carry == 3          # the chain this attack earned, not 6, 9, 12...


def test_parashu_carry_only_counts_with_the_parashu_in_hand():
    p = _player(_unique('parashu'))
    _kill_one(p)
    assert p._chain_carry > 0
    other = items.instantiate_weapon('longsword', 'iron')
    p.weapon = other
    assert combat.effective_chain(p, _target('kobold'), other, 2, consume=False) == 2


def test_putting_the_parashu_down_loses_its_rhythm():
    p = _player(_unique('parashu'))
    _kill_one(p)
    assert p._chain_carry > 0
    p._remove_weapon_passives(p.weapon)
    assert int(getattr(p, '_chain_carry', 0) or 0) == 0


def test_parashu_carry_does_not_survive_a_floor_change(monkeypatch, tmp_path):
    import pygame
    import bones
    import save_system
    from main import Game
    pygame.init()
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__bb331__', secret_build=None)
    g.player._chain_carry = 4
    g._change_level(2, True)
    assert int(getattr(g.player, '_chain_carry', 0) or 0) == 0
    g.player._chain_carry = 4
    g._change_level(1, False)                   # back up to a floor already seen
    assert int(getattr(g.player, '_chain_carry', 0) or 0) == 0
