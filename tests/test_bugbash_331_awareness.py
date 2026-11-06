"""Bug bash 3.3.1, B3: summoner, healer and ranged monsters use the same
detection check as every other hunting monster (Monster._spots_player).

Before: the summoner pattern never set _aware, so it never summoned (0
summons in 20 turns standing next to the hero); healers went straight for a
hero the Helm of Darkness hid; and ranged monsters became aware at a flat 8
tiles whatever stealth gear the hero wore.

Unit tests of Monster.take_turn against stub state, like test_monster_ai.py.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monster import Monster  # noqa: E402


class StubDungeon:
    width = 30
    height = 30

    def __init__(self):
        self.tiles = [[1] * 30 for _ in range(30)]

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y)

    def open_door(self, x, y):
        pass


class StubPlayer:
    def __init__(self, x=10, y=10):
        self.x, self.y = x, y
        self.hp = self.max_hp = 50
        self.status_effects = {}
        self.equipped_accessories = []
        self.STR = self.CON = self.DEX = self.INT = self.WIS = self.PER = 10

    def has_effect(self, name):
        return self.status_effects.get(name, 0) > 0

    def get_ac(self):
        return 10


class _SilentWalk:
    passive_silent_walk = True


def _make(pattern, x, y, **extra):
    d = {'id': 'test_' + pattern, 'name': 'test ' + pattern, 'symbol': 'M',
         'color': [200, 200, 200], 'ai_pattern': pattern, 'hp': '10',
         'attacks': [{'name': 'staff', 'damage': '1d4', 'type': 'physical'},
                     {'name': 'bolt', 'damage': '1d6', 'type': 'magic', 'ranged': True}],
         'speed': 10, 'thac0': 18, 'tags': ['humanoid']}
    d.update(extra)
    return Monster(d, x, y)


def _hide_with_helm(monkeypatch):
    """The Helm of Darkness's stealth in the dark, as chain_passives answers it."""
    import chain_passives
    monkeypatch.setattr(chain_passives, 'is_player_hidden_from',
                        lambda player, monster, dungeon=None: True)


def test_b3_summoner_next_to_the_hero_summons():
    s = _make('summoner', 11, 10, summon_kind='skeleton', summon_cooldown=3, summon_max=4)
    p = StubPlayer(10, 10)
    dun = StubDungeon()
    made = 0
    for _ in range(20):
        s.x, s.y = 11, 10
        s.take_turn(p, dun, [s])
        made += 1 if s._wants_summon else 0
    assert made >= 4, f"a summoner beside the hero summoned {made} times in 20 turns"


def test_b3_summoner_out_of_sight_range_does_not_summon():
    s = _make('summoner', 25, 25, summon_kind='skeleton', summon_cooldown=1, summon_max=4)
    p = StubPlayer(2, 2)
    for _ in range(5):
        s.take_turn(p, StubDungeon(), [s])
        assert not s._wants_summon


def test_b3_healer_does_not_see_through_the_helm_of_darkness(monkeypatch):
    h = _make('healer', 13, 10)
    p = StubPlayer(10, 10)
    _hide_with_helm(monkeypatch)
    for _ in range(5):
        assert h.take_turn(p, StubDungeon(), [h]) is False
    assert not getattr(h, '_aware', False)


def test_b3_healer_still_mends_an_ally_while_the_hero_is_hidden(monkeypatch):
    h = _make('healer', 5, 5, heal_amount_pct=0.3)
    ally = _make('healer', 5, 6)
    ally.max_hp, ally.hp = 20, 5
    _hide_with_helm(monkeypatch)
    h.take_turn(StubPlayer(20, 20), StubDungeon(), [h, ally])
    assert ally.hp > 5


def test_b3_ranged_monster_does_not_see_through_the_helm_of_darkness(monkeypatch):
    r = _make('ranged', 14, 10)
    p = StubPlayer(10, 10)
    _hide_with_helm(monkeypatch)
    for _ in range(5):
        assert r.take_turn(p, StubDungeon(), [r]) is False, "it shot at a hero it cannot see"


def test_b3_ranged_monster_honours_the_hand_of_glory():
    """Silent walk halves perception: an archer 6 tiles off (perception 8,
    halved to 4) does not notice the wearer."""
    r = _make('ranged', 16, 10)
    p = StubPlayer(10, 10)
    p.equipped_accessories = [_SilentWalk()]
    for _ in range(3):
        r.x, r.y = 16, 10
        assert r.take_turn(p, StubDungeon(), [r]) is False
    assert not getattr(r, '_aware', False)
    # Without the Hand it spots him at the same distance and shoots.
    r2 = _make('ranged', 16, 10)
    p2 = StubPlayer(10, 10)
    assert r2.take_turn(p2, StubDungeon(), [r2]) is True
