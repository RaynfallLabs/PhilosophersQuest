"""Bug bash 3.3.2: Pokemon-style lines when a hit meets a weakness or a
resistance (Brandon: "so you know it when you are blocked or effective").

src/affinity.py, data/affinity_lines.json. The hero's blows and shots are
noted by combat.strike_damage (form and substance after every bypass),
spells, wands and breath by Monster.take_damage; the game says one line
for each way creatures were struck at the end of the action.
"""
import json
import os
import random
import string
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import affinity  # noqa: E402
import combat  # noqa: E402
import items  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _mon(**over):
    d = dict(MONS['giant_rat'], id='giant_rat')
    d.update(over)
    return Monster(d, 1, 0)


@pytest.fixture(autouse=True)
def _clean():
    affinity.drain()
    yield
    affinity.drain()


def test_every_pool_is_full_and_formats():
    data = affinity.lines()
    fields = {'name', 'the', 'word', 'word_cap'}
    for pool in ('weak', 'resisted', 'weak_many', 'resisted_many'):
        assert len(data[pool]) >= 2, pool
        for line in data[pool]:
            used = {f for _, f, _, _ in string.Formatter().parse(line) if f}
            assert used <= fields, (pool, line)
    assert len(data['weak']) >= 6 and len(data['resisted']) >= 6
    assert any('super effective' in s.lower() for s in data['weak'])
    assert any('not very effective' in s.lower() for s in data['resisted'])


def test_a_blow_on_a_weakness_is_noted_with_what_met_it():
    p = Player()
    p.weapon = None                                   # a fist crushes
    m = _mon(weaknesses=['blunt'], resistances=[])
    combat.strike_damage(p, m, 3, consume=True)
    assert affinity.drain() == [(m, 'weak', 'blunt')]


def test_a_resisted_blow_is_noted_and_a_preview_is_not():
    p = Player()
    p.weapon = items.instantiate_weapon('longsword', 'iron')
    m = _mon(resistances=list(combat.blow_forms_of(p.weapon)), weaknesses=[])
    combat.strike_damage(p, m, 3, consume=False)      # the combat strip's preview
    assert affinity.drain() == []
    combat.strike_damage(p, m, 3, consume=True)
    notes = affinity.drain()
    assert notes and notes[0][1] == 'resisted'


def test_a_plain_blow_says_nothing():
    p = Player()
    p.weapon = None
    combat.strike_damage(p, _mon(weaknesses=[], resistances=[]), 3, consume=True)
    assert affinity.drain() == []


def test_a_spell_of_its_weakness_is_noted_a_burn_ticking_is_not():
    m = _mon(weaknesses=['fire'], resistances=['cold'], hp=500)
    m.take_damage(5, 'fire')
    m.take_damage(5, 'cold')
    m.take_damage(5, 'physical')
    assert affinity.drain() == [(m, 'weak', 'fire'), (m, 'resisted', 'cold')]
    m._dot_tick = True
    m.take_damage(5, 'fire')
    m._dot_tick = False
    assert affinity.drain() == []


def test_one_line_a_kind_naming_the_creature_or_all_of_them():
    a, b = _mon(), _mon()
    rng = random.Random(1)
    one = affinity.say([(a, 'weak', 'silver')], rng)
    assert len(one) == 1 and one[0][1] == 'weak'
    from monster import the_name
    pool = [s.format(name=the_name(a), the=the_name(a, lower=True), word='silver', word_cap='Silver')
            for s in affinity.lines()['weak']]
    assert one[0][0] in pool
    both = affinity.say([(a, 'resisted', 'fire'), (b, 'resisted', 'fire'), (a, 'weak', 'holy')], rng)
    assert [k for _t, k in both] == ['weak', 'resisted']
    many = [s.format(word='fire', word_cap='Fire') for s in affinity.lines()['resisted_many']]
    assert both[1][0] in many


def test_the_game_says_it_at_the_end_of_the_action(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_affinity__')
    g.monsters = []
    g.state = STATE_PLAYER
    seen = []
    monkeypatch.setattr(g, 'add_message', lambda text, kind='info', *a, **k: seen.append((text, kind)))
    from monster import the_name
    rat = _mon()
    affinity.note(rat, 'resisted', 'cold')
    g._advance_turn()
    lines = [t for t, k in seen if k == 'warning']
    pool = [s.format(name=the_name(rat), the=the_name(rat, lower=True), word='cold', word_cap='Cold')
            for s in affinity.lines()['resisted']]
    assert any(t in pool for t in lines)
    assert affinity.drain() == []
