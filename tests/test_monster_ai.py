"""Tests for the 2026 monster-AI expansion: healer, summoner, mimic, charge,
phase_blink, flanker, pack_dependent, HP-threshold phase change, and overrides
for perception_range / alert_radius / alert_all_tag.

These are unit tests of the take_turn / attack dispatch — no rendering, no
quiz engine. Each test wires the minimum stub state needed to exercise one
mechanic in isolation."""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monster import Monster


# ---------------------------------------------------------------------------
# Stub helpers
# ---------------------------------------------------------------------------

class StubDungeon:
    """Minimal dungeon stub: every tile is floor and walkable."""
    width = 20
    height = 20
    tiles = [[1] * 20 for _ in range(20)]

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y)

    def open_door(self, x, y):
        pass


class StubPlayer:
    """Player stub with enough attributes for monster AI to navigate."""
    def __init__(self, x=10, y=10, hp=50, max_hp=50):
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = max_hp
        self.status_effects = {}
        self.STR = self.CON = self.DEX = self.INT = self.WIS = self.PER = 10

    def has_effect(self, name):
        return self.status_effects.get(name, 0) > 0

    def get_ac(self):
        return 10

    def get_sight_radius(self):
        return 8

    def take_damage(self, amount, damage_type='physical'):
        actual = max(0, amount)
        self.hp = max(0, self.hp - actual)
        return actual

    def add_effect(self, name, duration):
        self.status_effects[name] = duration
        return True


def _make(defn_overrides):
    base = {
        'id': 'test_mob',
        'name': 'test mob',
        'symbol': 'M',
        'color': [200, 200, 200],
        'ai_pattern': 'aggressive',
        'hp': '10',
        'attacks': [{'name': 'bite', 'damage': '1d4', 'type': 'physical'}],
        'speed': 10,
        'thac0': 18,
        'tags': ['beast'],
    }
    base.update(defn_overrides)
    m = Monster(base, x=base.pop('x', 5), y=base.pop('y', 5))
    m._aware = True   # skip detection in most tests
    return m


# ---------------------------------------------------------------------------
# Healer
# ---------------------------------------------------------------------------

def test_healer_heals_wounded_adjacent_ally():
    healer = _make({'id': 'priest', 'name': 'priest',
                    'ai_pattern': 'healer', 'tags': ['humanoid'],
                    'heal_amount_pct': 0.30, 'x': 5, 'y': 5})
    ally = _make({'id': 'priest', 'name': 'priest',  # SAME kind
                  'hp': '20', 'tags': ['humanoid'], 'x': 5, 'y': 6})
    ally.hp = 5  # heavily wounded; max stays 20
    ally.max_hp = 20
    player = StubPlayer(x=10, y=10)
    healer.take_turn(player, StubDungeon(), [healer, ally])
    assert ally.hp > 5, "healer should have healed the wounded ally"
    assert healer._heal_target is ally
    assert healer._heal_amount > 0


def test_healer_falls_back_to_aggressive_when_no_wounded_ally():
    healer = _make({'ai_pattern': 'healer', 'x': 5, 'y': 5})
    player = StubPlayer(x=6, y=5)  # adjacent
    attacked = healer.take_turn(player, StubDungeon(), [healer])
    assert attacked is True, "no wounded ally + adjacent player -> attack"


# ---------------------------------------------------------------------------
# Summoner
# ---------------------------------------------------------------------------

def test_summoner_flags_wants_summon_on_cooldown():
    s = _make({'ai_pattern': 'summoner', 'summon_kind': 'skeleton',
               'summon_cooldown': 3, 'summon_max': 4, 'x': 5, 'y': 5})
    player = StubPlayer(x=10, y=10)
    # First two turns should NOT trigger (cooldown 3)
    s.take_turn(player, StubDungeon(), [s])
    assert s._wants_summon is False
    s.take_turn(player, StubDungeon(), [s])
    assert s._wants_summon is False
    s.take_turn(player, StubDungeon(), [s])
    assert s._wants_summon is True, "cooldown should fire on 3rd turn"
    assert s._summons_made == 1


def test_summoner_exhausts_after_max_summons():
    s = _make({'ai_pattern': 'summoner', 'summon_kind': 'skeleton',
               'summon_cooldown': 1, 'summon_max': 2, 'x': 5, 'y': 5})
    player = StubPlayer(x=10, y=10)
    for _ in range(5):
        s.take_turn(player, StubDungeon(), [s])
    assert s._summons_made == 2, "should cap at summon_max"


# ---------------------------------------------------------------------------
# Mimic
# ---------------------------------------------------------------------------

def test_mimic_lurks_silently_until_player_adjacent():
    m = _make({'ai_pattern': 'mimic', 'x': 5, 'y': 5})
    far_player = StubPlayer(x=15, y=15)
    attacked = m.take_turn(far_player, StubDungeon(), [m])
    assert attacked is False, "mimic should not act when player far"
    assert m.ai_pattern == 'mimic', "should still be in mimic state"


def test_mimic_springs_when_player_adjacent_and_crit_first_hit():
    m = _make({'ai_pattern': 'mimic', 'x': 5, 'y': 5})
    adj_player = StubPlayer(x=6, y=5)
    attacked = m.take_turn(adj_player, StubDungeon(), [m])
    assert attacked is True, "mimic should attack when player adjacent"
    assert m.ai_pattern == 'aggressive', "should reveal as aggressive"
    assert m._mimic_surprise is True, "first attack should crit"

    # The first attack consumes the surprise flag
    random.seed(0)
    _dmg, _msg = m.attack(adj_player)
    assert m._mimic_surprise is False, "surprise should be one-shot"


# ---------------------------------------------------------------------------
# Charge
# ---------------------------------------------------------------------------

def test_charge_arms_when_player_in_straight_line():
    m = _make({'can_charge': True, 'x': 5, 'y': 5})
    player = StubPlayer(x=5, y=8)   # straight south, distance 3
    m.take_turn(player, StubDungeon(), [m])
    assert m._charge_ready is True, "charge should arm in straight line dist 2-5"


def test_charge_does_not_arm_off_axis():
    m = _make({'can_charge': True, 'x': 5, 'y': 5})
    player = StubPlayer(x=8, y=9)   # off-axis (3, 4) — not orthog/diag
    m.take_turn(player, StubDungeon(), [m])
    assert m._charge_ready is False, "off-axis approach should NOT arm charge"


def test_charge_bonus_applies_to_attack_damage_once():
    # 1d10 always produces 1-10. Charge 2.0× -> 2-20. Even a min roll of 1 → 2.
    m = _make({'can_charge': True, 'charge_bonus_mult': 2.0, 'x': 5, 'y': 5,
               'thac0': -5,  # easy hit
               'attacks': [{'name': 'gore', 'damage': '1d10', 'type': 'physical'}]})
    m._charge_ready = True
    player = StubPlayer(x=6, y=5)  # adjacent
    random.seed(7)
    dmg, _msg = m.attack(player)
    # Damage is roll(1d10) * 2.0 — must be >= 2
    assert dmg >= 2, f"charged attack should deal >=2; got {dmg}"
    assert m._charge_ready is False, "charge is one-shot"


# ---------------------------------------------------------------------------
# Pack-dependent
# ---------------------------------------------------------------------------

def test_pack_dependent_flips_to_cowardly_when_alone():
    m = _make({'pack_dependent': True, 'pack_min_allies': 1,
               'ai_pattern': 'aggressive', 'x': 5, 'y': 5})
    player = StubPlayer(x=8, y=5)
    m.take_turn(player, StubDungeon(), [m])
    assert m.ai_pattern == 'cowardly', "alone -> should flip cowardly"


def test_pack_dependent_stays_aggressive_with_allies():
    m = _make({'pack_dependent': True, 'pack_min_allies': 1,
               'ai_pattern': 'aggressive', 'x': 5, 'y': 5})
    ally = _make({'id': 'test_mob', 'x': 6, 'y': 5})
    player = StubPlayer(x=8, y=5)
    m.take_turn(player, StubDungeon(), [m, ally])
    assert m.ai_pattern == 'aggressive', "ally nearby -> stay aggressive"


# ---------------------------------------------------------------------------
# HP-threshold phase change (enrage)
# ---------------------------------------------------------------------------

def test_enrage_swaps_pattern_at_hp_threshold():
    m = _make({'ai_pattern': 'aggressive',
               'enrage_at_hp_pct': 0.25,
               'enraged_pattern': 'fenrir_rage',
               'x': 5, 'y': 5})
    m.max_hp = 100
    m.hp = 50  # above threshold
    player = StubPlayer(x=8, y=5)
    m.take_turn(player, StubDungeon(), [m])
    assert m._enraged is False
    assert m.ai_pattern == 'aggressive'

    m.hp = 20  # below 25% threshold
    m.take_turn(player, StubDungeon(), [m])
    assert m._enraged is True
    assert m.ai_pattern == 'fenrir_rage'
    assert m._enrage_message != ''


def test_enrage_does_not_swap_twice():
    m = _make({'ai_pattern': 'aggressive',
               'enrage_at_hp_pct': 0.50,
               'enraged_pattern': 'ranged',
               'x': 5, 'y': 5})
    m.max_hp = 100
    m.hp = 30
    player = StubPlayer(x=8, y=5)
    m.take_turn(player, StubDungeon(), [m])
    assert m._enraged is True
    m._enrage_message = ''
    m.take_turn(player, StubDungeon(), [m])
    assert m._enrage_message == '', "enrage should fire only once"


# ---------------------------------------------------------------------------
# Perception / alert overrides
# ---------------------------------------------------------------------------

def test_perception_range_override_extends_detection():
    long_sight = _make({'perception_range': 15, '_aware': False, 'x': 5, 'y': 5})
    long_sight._aware = False
    player = StubPlayer(x=18, y=5)   # distance 13
    long_sight.take_turn(player, StubDungeon(), [long_sight])
    assert long_sight._aware is True, "perception 15 should detect at dist 13"


def test_short_perception_range_blinds_to_distant_player():
    blind = _make({'perception_range': 3, '_aware': False, 'x': 5, 'y': 5})
    blind._aware = False
    player = StubPlayer(x=12, y=5)   # distance 7
    blind.take_turn(player, StubDungeon(), [blind])
    assert blind._aware is False, "perception 3 should NOT detect at dist 7"


def test_alert_all_tag_wakes_different_kind_allies():
    leader = _make({'id': 'goblin_warlord', 'tags': ['goblinoid'],
                    'alert_radius': 12, 'alert_all_tag': True, 'x': 5, 'y': 5})
    goblin = _make({'id': 'goblin', 'tags': ['goblinoid'], 'x': 12, 'y': 5})
    hobgoblin = _make({'id': 'hobgoblin', 'tags': ['goblinoid'], 'x': 5, 'y': 12})
    unrelated = _make({'id': 'spider', 'tags': ['beast'], 'x': 6, 'y': 5})
    goblin._alerted = False
    hobgoblin._alerted = False
    unrelated._alerted = False
    leader.alert_nearby([leader, goblin, hobgoblin, unrelated])
    assert goblin._alerted is True, "tag-wide alert should wake same-tag goblin"
    assert hobgoblin._alerted is True, "tag-wide alert should wake same-tag hobgoblin"
    assert unrelated._alerted is False, "beast should NOT be alerted by goblinoid call"
