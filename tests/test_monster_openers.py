"""Openers (Brandon, 2026-11-19: "openers for sure"; the powers "dont seem
to make a lot of difference" because a monster died before it used one).

A creature with a signature opening move (monsters.json `opener`) uses it
before the hero can strike: a pounce (range 1) on the turn it closes; from a
distance an archer's first volley at once, a gaze, voice or breath drawn up
for one turn first (the tell). Once a fight; ready again when it has lost
the hero a while.
"""
from __future__ import annotations

import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PQ_NO_BONES', '1')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import monster as monster_mod  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)

RANGED_DELIVERIES = ('range', 'gaze', 'voice', 'breath')


def test_every_opener_in_the_data_names_a_real_attack_and_a_fair_range():
    for mid, m in MONS.items():
        op = m.get('opener') if isinstance(m, dict) else None
        if not op:
            continue
        names = [a.get('name') for a in m.get('attacks') or []]
        assert op.get('attack') in names, (mid, op)
        rng = int(op.get('range', 1))
        assert 1 <= rng <= 7, (mid, op)
        if rng >= 2:
            atk = next(a for a in m['attacks'] if a.get('name') == op['attack'])
            assert atk.get('delivery') in RANGED_DELIVERIES or atk.get('ranged'), (mid, op, atk)
        mon = monster_mod.Monster({**m, 'id': mid}, 0, 0)
        assert mon.opener is not None and mon._opener_attack is not None, mid


_SCREEN = None


def _game(seed=7):
    global _SCREEN
    from main import Game
    from game_states import STATE_PLAYER
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    random.seed(seed)
    g = Game(_SCREEN, player_name='__test_monster_openers__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _open_spot(g, half=4):
    from dungeon import FLOOR
    for y in range(half + 1, g.dungeon.height - half - 1):
        for x in range(half + 1, g.dungeon.width - half - 1):
            if all(g.dungeon.is_walkable(x + i, y + j)
                   for i in range(-half, half + 1) for j in range(-half, half + 1)):
                return x, y
    x = min(max(g.player.x, half + 1), g.dungeon.width - half - 2)
    y = min(max(g.player.y, half + 1), g.dungeon.height - half - 2)
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    return x, y


def _scene(defn, dist):
    g = _game()
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    m = monster_mod.Monster(defn, x + dist, y)
    m._aware = True
    m._alerted = True
    g.monsters = [m]
    return g, m


def _wolf(range_=1):
    return {**MONS['giant_rat'], 'id': 'test_wolf', 'name': 'test wolf', 'ai_pattern': 'aggressive',
            'speed': 12,
            'attacks': [{'name': 'Lunge', 'damage': '1d6', 'type': 'pierce', 'delivery': 'bite'},
                        {'name': 'Snap', 'damage': '1d4', 'type': 'pierce', 'delivery': 'bite'}],
            'opener': {'attack': 'Lunge', 'range': range_}}


def _gazer():
    return {**MONS['giant_rat'], 'id': 'test_gazer', 'name': 'test gazer', 'ai_pattern': 'aggressive',
            'speed': 10,
            'attacks': [{'name': 'Bite', 'damage': '1d4', 'type': 'pierce', 'delivery': 'bite'},
                        {'name': 'Stunning Gaze', 'damage': '1d2', 'type': 'magic', 'delivery': 'gaze',
                         'effect': 'stunned', 'effect_chance': 0.5, 'effect_duration': 2}],
            'opener': {'attack': 'Stunning Gaze', 'range': 4}}


def _turn(g, m):
    return m.take_turn(g.player, g.dungeon, g.monsters)


def test_a_pounce_closes_and_strikes_in_the_same_turn():
    g, m = _scene(_wolf(), 2)
    assert _turn(g, m) is True                       # it attacks this very turn
    assert m._adjacent_to(g.player)
    assert m.__dict__.get('_opener_now', {}).get('name') == 'Lunge'


def test_without_an_opener_closing_ends_its_turn():
    d = _wolf()
    d.pop('opener')
    g, m = _scene(d, 2)
    assert _turn(g, m) is False                      # it closes; the hero strikes first
    assert m._adjacent_to(g.player)


def test_the_opener_is_once_a_fight():
    g, m = _scene(_wolf(), 2)
    _turn(g, m)
    m.__dict__.pop('_opener_now', None)
    assert _turn(g, m) is True                       # adjacent: an ordinary blow
    assert '_opener_now' not in m.__dict__


def test_a_gaze_is_drawn_up_for_a_turn_then_lands():
    g, m = _scene(_gazer(), 3)
    assert _turn(g, m) is False                      # the tell: it fixes its eyes on you
    assert 'eyes on you' in m.__dict__.get('_wind_up_message', '')
    assert (m.x, m.y) == (g.player.x + 3, g.player.y)          # it did not close
    assert _turn(g, m) is True                       # and the gaze comes, from range
    assert m.__dict__.get('_opener_now', {}).get('name') == 'Stunning Gaze'


def test_the_game_says_the_tell_then_the_gaze_lands():
    g, m = _scene(_gazer(), 3)
    seen = []
    m._resolve_blow = lambda atk, player, **k: (seen.append(atk['name']) or (0, 'It misses.'))
    g._sees_monster = lambda mon: True
    before = len(g.msg_log.entries)
    g._do_monster_turns()                            # the tell
    texts = [str(e[0]) for e in g.msg_log.entries[before:]]
    assert any('eyes on you' in t for t in texts), texts
    assert seen == []
    g._do_monster_turns()                            # the gaze, from range
    assert seen == ['Stunning Gaze']


def test_out_of_sight_or_range_it_does_not_open():
    g, m = _scene(_gazer(), 6)                       # range 4: too far
    assert m._opener_from_range(g.player, g.dungeon) is None


def test_it_opens_again_once_it_has_lost_the_hero():
    g, m = _scene(_wolf(), 2)
    _turn(g, m)
    assert m._opened
    import senses
    real = senses.notice
    senses.notice = lambda *a, **k: False
    try:
        for _ in range(monster_mod.OPENER_RESET_TURNS):
            m._spots_player(g.player, g.dungeon, g.monsters, None)
    finally:
        senses.notice = real
    assert not m._opened


def test_an_old_monster_without_the_fields_still_takes_its_turn():
    g, m = _scene(_wolf(), 2)
    for f in ('opener', '_opener_attack', '_opened', '_winding'):
        m.__dict__.pop(f, None)
    assert _turn(g, m) in (True, False)
