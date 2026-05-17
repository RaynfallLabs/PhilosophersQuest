"""Tests for the 2026 prayer-system rebuild:
- 8 named prayers registered with required fields
- Situational gates evaluate correctly
- Karma-tier verses are wired
- Specialty prayers refuse at karma <= -6; Damned at -10 keeps only Pater Noster
- _any_cursed_worn helper
- _karma_tier mapping
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import game_divine


# ---------------------------------------------------------------------------
# Registry / structure
# ---------------------------------------------------------------------------

def test_eight_prayers_registered():
    assert len(game_divine.PRAYERS) == 8


def test_each_prayer_has_required_fields():
    required = {'id', 'name', 'lore'}
    for p in game_divine.PRAYERS:
        missing = required - set(p.keys())
        assert not missing, f"{p.get('id')} missing {missing}"


def test_specialty_prayers_are_correct():
    """Pater Noster, Ave Maria, Confiteor are always available — never specialty."""
    by_id = {p['id']: p for p in game_divine.PRAYERS}
    assert by_id['pater_noster'].get('specialty', False) is False
    assert by_id['ave_maria'].get('specialty', False) is False
    assert by_id['confiteor'].get('specialty', False) is False
    assert by_id['memorare'].get('specialty', False) is True
    assert by_id['saint_michael'].get('specialty', False) is True
    assert by_id['saint_raphael'].get('specialty', False) is True
    assert by_id['saint_anthony'].get('specialty', False) is True
    assert by_id['anima_christi'].get('specialty', False) is True


# ---------------------------------------------------------------------------
# karma_tier mapping
# ---------------------------------------------------------------------------

def test_karma_tier_buckets():
    f = game_divine._karma_tier
    assert f(10) == 'saintly'
    assert f(6)  == 'saintly'
    assert f(5)  == 'righteous'
    assert f(1)  == 'righteous'
    assert f(0)  == 'neutral'
    assert f(-1) == 'slipping'
    assert f(-5) == 'slipping'
    assert f(-6) == 'fallen'
    assert f(-10) == 'fallen'


def test_karma_verses_have_full_chains():
    """escalator_chain caps at tier 5 — verses indexed 1-5 (plus 0 for fallen
    'examine your conscience' silence)."""
    for tier in ('saintly', 'righteous', 'neutral', 'slipping'):
        for chain in range(1, 6):
            assert chain in game_divine._KARMA_VERSES[tier], (
                f"{tier} missing chain {chain} verse")
    # Fallen has chain 0 ("examine your conscience")
    assert 0 in game_divine._KARMA_VERSES['fallen']
    for chain in range(1, 6):
        assert chain in game_divine._KARMA_VERSES['fallen'], (
            f"fallen missing chain {chain} verse")


# ---------------------------------------------------------------------------
# _any_cursed_worn helper
# ---------------------------------------------------------------------------

class _StubItem:
    def __init__(self, buc='uncursed'):
        self.buc = buc
        self.name = 'stub'


class _StubPlayer:
    def __init__(self):
        self.weapon = None
        self.ranged_weapon = None
        self.shield = None
        self.armor_slots = [None] * 8
        self.amulet_slot = None
        self.accessory_slots = [None, None]


def test_any_cursed_worn_false_when_clean():
    p = _StubPlayer()
    assert not game_divine._any_cursed_worn(p)


def test_any_cursed_worn_true_for_each_slot():
    # weapon
    p = _StubPlayer()
    p.weapon = _StubItem('cursed')
    assert game_divine._any_cursed_worn(p)
    # armor slot
    p = _StubPlayer()
    p.armor_slots[2] = _StubItem('cursed')
    assert game_divine._any_cursed_worn(p)
    # shield
    p = _StubPlayer()
    p.shield = _StubItem('cursed')
    assert game_divine._any_cursed_worn(p)
    # accessory
    p = _StubPlayer()
    p.accessory_slots[0] = _StubItem('cursed')
    assert game_divine._any_cursed_worn(p)
    # amulet
    p = _StubPlayer()
    p.amulet_slot = _StubItem('cursed')
    assert game_divine._any_cursed_worn(p)


# ---------------------------------------------------------------------------
# Prayer-menu gate construction (uses a stub game)
# ---------------------------------------------------------------------------

class _StubMonster:
    def __init__(self, tags, x=5, y=5, alive=True):
        self.tags = tags
        self.x = x
        self.y = y
        self.alive = alive


class _StubGame:
    """Minimal Game stub for _start_pray gate evaluation."""
    def __init__(self, hp=100, max_hp=100, karma=0, monsters=None,
                 inventory=None, weapon_buc='uncursed'):
        class _P:
            pass
        self.player = _P()
        self.player.hp = hp
        self.player.max_hp = max_hp
        self.player.weapon = _StubItem(weapon_buc)
        self.player.ranged_weapon = None
        self.player.shield = None
        self.player.armor_slots = [None] * 8
        self.player.amulet_slot = None
        self.player.accessory_slots = [None, None]
        self.player.inventory = inventory or []
        self.karma = karma
        self.monsters = monsters or []
        self.visible = {(m.x, m.y) for m in self.monsters}


def test_memorare_gate_requires_low_hp():
    spec = next(p for p in game_divine.PRAYERS if p['id'] == 'memorare')
    g_full_hp = _StubGame(hp=100, max_hp=100)
    g_low_hp = _StubGame(hp=15, max_hp=100)
    assert spec['gate'](g_full_hp) is False
    assert spec['gate'](g_low_hp) is True


def test_saint_michael_gate_requires_visible_demon():
    spec = next(p for p in game_divine.PRAYERS if p['id'] == 'saint_michael')
    g_no_demons = _StubGame()
    g_with_demon = _StubGame(monsters=[_StubMonster(['demon'], 5, 5)])
    g_with_undead = _StubGame(monsters=[_StubMonster(['undead'], 5, 5)])
    assert spec['gate'](g_no_demons) is False
    assert spec['gate'](g_with_demon) is True
    assert spec['gate'](g_with_undead) is False


def test_saint_anthony_gate_requires_unknown_items():
    spec = next(p for p in game_divine.PRAYERS if p['id'] == 'saint_anthony')
    class _Item:
        def __init__(self, identified):
            self.identified = identified
    g_empty = _StubGame(inventory=[])
    g_known = _StubGame(inventory=[_Item(True), _Item(True)])
    g_unknown = _StubGame(inventory=[_Item(True), _Item(False)])
    assert spec['gate'](g_empty) is False
    assert spec['gate'](g_known) is False
    assert spec['gate'](g_unknown) is True


def test_anima_christi_gate_requires_visible_undead():
    spec = next(p for p in game_divine.PRAYERS if p['id'] == 'anima_christi')
    g_no_undead = _StubGame()
    g_with_undead = _StubGame(monsters=[_StubMonster(['undead'], 5, 5)])
    assert spec['gate'](g_no_undead) is False
    assert spec['gate'](g_with_undead) is True


def test_confiteor_gate_requires_cursed_worn():
    spec = next(p for p in game_divine.PRAYERS if p['id'] == 'confiteor')
    g_clean = _StubGame()
    g_cursed = _StubGame(weapon_buc='cursed')
    assert spec['gate'](g_clean) is False
    assert spec['gate'](g_cursed) is True


def test_prayer_quiz_uses_max_chain_5():
    """escalator_chain caps at tier 5; max_chain must match that ceiling so
    the chain score never exceeds the meaningful difficulty range."""
    import inspect
    src = inspect.getsource(game_divine.DivineMixin._begin_specific_prayer)
    assert 'max_chain=5' in src, "_begin_specific_prayer must pass max_chain=5"
    assert 'max_chain=8' not in src, "stale max_chain=8 should not appear"
