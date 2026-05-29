"""Tests for QOL panels (Kit comparison + Discoveries record).

These tests focus on the pure-data layer of the panels — no pygame
rendering. They cover:

- _kit_visible_level: gating rule for how much the player has 'earned' to see
- _kit_avg_damage: dice notation parsing
- _kit_collect_items: assembles inventory + equipped + floor items
- _kit_filter_for_tab: routes items to their tab
- _kit_collect_spells: pulls from player.known_spells
- _discoveries_sections: produces sections without crashing on empty data
- quiz_stats tracking: bumps the right counter on _on_quiz_answer

The Game class is heavy (lots of pygame init), so we shim a minimal stand-in
with the attributes the helpers actually touch.
"""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeGame:
    """Minimal stand-in providing the attributes the Kit helpers read."""

    # Pull the unbound methods off the real Game class so they get the real
    # logic without needing pygame init.
    @staticmethod
    def _make(player, ground_items=None):
        from game_menus import GameMenusMixin  # type: ignore[attr-defined]
        # Import lazily so failures show on the right test
        return _ResolvedFake(player, ground_items or [])


class _ResolvedFake:
    def __init__(self, player, ground_items):
        self.player = player
        self.ground_items = ground_items
        self._kit_tab = 0
        self._kit_scroll = 0

    # Pull the methods straight off the real mixin via the Game class.
    def __getattr__(self, name):
        if name.startswith('_kit_') or name in (
            '_open_kit_panel', '_open_discoveries',
            '_KIT_TABS',
        ):
            # Bind the method off main.Game (which mixes in game_menus)
            import main
            method = getattr(main.Game, name, None)
            if method is None:
                raise AttributeError(name)
            if callable(method):
                return method.__get__(self, type(self))
            return method
        raise AttributeError(name)


_BASE_DEFN = {'symbol': '/', 'color': [255, 255, 255]}


def _defn(**kw):
    """Build a minimal item-defn dict with the required base fields."""
    return {**_BASE_DEFN, **kw}


def _make_player_with_items():
    from player import Player
    from items import Weapon, Armor, Shield, Accessory, Potion, Spellbook
    p = Player()
    # Build a few items with the structured fields used by the panel
    longsword = Weapon(_defn(
        id='longsword', name='longsword', damage='1d8+2',
        material='iron', weight=3, identified=True,
    ))
    plate = Armor(_defn(
        id='plate', name='plate mail', slot='body',
        ac_bonus=5, material='iron', weight=8, identified=True,
    ))
    bigshield = Shield(_defn(
        id='kite', name='kite shield', ac_bonus=2,
        material='iron', weight=5, identified=True,
    ))
    ring = Accessory(_defn(
        id='ring_pow', name='ring of power', slot='ring',
        effects={'stat': 'STR', 'amount': 2}, identified=True,
    ))
    pot = Potion(_defn(
        id='pot_heal', name='healing potion', effect='heal',
        power='2d8', identified=True, id_level=5,
    ))
    sb = Spellbook(_defn(
        id='sb_mm', name='spellbook of missile',
        spell_id='magic_missile_spell', spell_name='Magic Missile',
        mp_cost=4, identified=True, id_level=5,
    ))
    p.weapon = longsword
    p.armor_slots[1] = plate  # body slot
    p.shield = bigshield
    p.accessory_slots[0] = ring
    p.inventory = [pot, sb]
    p.known_spells = {'magic_missile_spell': 4}
    return p


# ---------------------------------------------------------------------------
# _kit_visible_level
# ---------------------------------------------------------------------------

def test_kit_visible_level_identified_returns_5():
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    assert g._kit_visible_level(p.weapon) == 5


def test_kit_visible_level_unidentified_returns_id_level():
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    from items import Potion
    # id_level=1 IS the partial-identification fixture; do NOT call
    # `pot.identified = False` afterwards — under the 2026-05-29 property
    # rule, that setter clamps id_level back to 0 (matching the new
    # invariant: identified iff id_level >= 4).
    pot = Potion(_defn(id='pot_x', name='fizzy potion', effect='fizz',
                       id_level=1))
    # known_item_ids empty + id_level 1 -> 1
    assert g._kit_visible_level(pot) == 1


def test_kit_visible_level_known_id_boosts_to_3():
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    from items import Potion
    pot = Potion(_defn(id='pot_y', name='fizzy potion', effect='fizz',
                       id_level=0))
    # Same caveat: don't reset identified=False here. id_level=0 from
    # the defn is enough to represent unidentified.
    p.known_item_ids.add('pot_y')
    # known_item_ids match -> boost to 3
    assert g._kit_visible_level(pot) == 3


# ---------------------------------------------------------------------------
# _kit_avg_damage: dice parsing
# ---------------------------------------------------------------------------

def test_kit_avg_damage_simple_dice():
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    # 1d8+2: avg (1+8)/2 + 2 = 4.5 + 2 = 6.5
    assert g._kit_avg_damage(p.weapon) == 6.5


def test_kit_avg_damage_no_bonus():
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    from items import Weapon
    w = Weapon(_defn(id='club', name='club', damage='2d6',
                     material='wood', identified=True))
    # 2d6: avg 2 * 3.5 = 7.0
    assert g._kit_avg_damage(w) == 7.0


def test_kit_avg_damage_negative_bonus():
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    from items import Weapon
    w = Weapon(_defn(id='rusty', name='rusty knife', damage='1d4-1',
                     material='iron', identified=True))
    # 1d4-1: avg 2.5 - 1 = 1.5
    assert g._kit_avg_damage(w) == 1.5


def test_kit_avg_damage_base_damage_fallback():
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    from items import Weapon
    w = Weapon(_defn(id='hammer', name='hammer', base_damage=7,
                     material='iron', identified=True))
    assert g._kit_avg_damage(w) == 7.0


# ---------------------------------------------------------------------------
# _kit_collect_items: sources and dedup
# ---------------------------------------------------------------------------

def test_kit_collect_items_includes_equipped_and_pack():
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    p.x, p.y = 5, 5
    out = g._kit_collect_items()
    sources = [s for s, _ in out]
    assert sources.count('equip') == 4   # weapon, body armor, shield, ring
    assert sources.count('pack') == 2    # potion, spellbook
    assert sources.count('floor') == 0


def test_kit_collect_items_picks_up_floor_at_player_tile():
    from items import Weapon
    p = _make_player_with_items()
    p.x, p.y = 3, 7
    on_tile = Weapon(_defn(id='dagger', name='dagger', damage='1d4',
                           material='iron', identified=True))
    on_tile.x, on_tile.y = 3, 7
    elsewhere = Weapon(_defn(id='sword', name='sword', damage='1d8',
                             material='iron', identified=True))
    elsewhere.x, elsewhere.y = 1, 1
    g = _ResolvedFake(p, [on_tile, elsewhere])
    out = g._kit_collect_items()
    floor = [it for s, it in out if s == 'floor']
    assert len(floor) == 1
    assert floor[0].id == 'dagger'


def test_kit_collect_items_no_duplicate_equipped_in_pack():
    """Equipped items should appear only with 'equip' source, never 'pack'."""
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    out = g._kit_collect_items()
    weapon_entries = [s for s, it in out if it is p.weapon]
    assert weapon_entries == ['equip']


# ---------------------------------------------------------------------------
# _kit_filter_for_tab
# ---------------------------------------------------------------------------

def test_kit_filter_for_tab_routes_to_correct_class():
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    rows = g._kit_collect_items()
    # Weapons tab
    weapons = g._kit_filter_for_tab(rows, 0)
    assert len(weapons) == 1
    # Armor tab
    armor = g._kit_filter_for_tab(rows, 1)
    assert len(armor) == 1
    # Shields tab
    shields = g._kit_filter_for_tab(rows, 2)
    assert len(shields) == 1
    # Accessories tab
    accs = g._kit_filter_for_tab(rows, 3)
    assert len(accs) == 1
    # Consumables tab (potion + spellbook)
    cons = g._kit_filter_for_tab(rows, 4)
    assert len(cons) == 2


def test_kit_filter_for_tab_spells_returns_empty():
    """Spells tab is special-cased; filter returns empty."""
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    rows = g._kit_collect_items()
    spells = g._kit_filter_for_tab(rows, 5)
    assert spells == []


# ---------------------------------------------------------------------------
# _kit_collect_spells
# ---------------------------------------------------------------------------

def test_kit_collect_spells_reads_known_spells():
    p = _make_player_with_items()
    g = _ResolvedFake(p, [])
    out = g._kit_collect_spells()
    assert len(out) == 1
    assert out[0]['spell_id'] == 'magic_missile_spell'
    assert out[0]['name'] == 'Magic Missile'
    assert out[0]['mp_cost'] == 4


def test_kit_collect_spells_empty_player():
    from player import Player
    p = Player()
    g = _ResolvedFake(p, [])
    assert g._kit_collect_spells() == []


# ---------------------------------------------------------------------------
# Discoveries: section assembly should never crash on empty player
# ---------------------------------------------------------------------------

def test_discoveries_sections_with_empty_player():
    from player import Player
    p = Player()
    # Use the render method via Game class — pull onto a fake with the right
    # attributes the method touches.
    fake = SimpleNamespace(
        player=p,
        correct_answers=0,
        wrong_answers=0,
        karma=0,
        dungeon_level=1,
        quiz_stats={},
    )
    import main
    sections = main.Game._discoveries_sections(fake)
    # Must produce non-empty list of (title, rows) tuples
    assert len(sections) >= 5
    titles = [t for t, _ in sections]
    assert 'QUIZ PERFORMANCE' in titles
    assert 'IDENTIFICATION' in titles
    assert 'BESTIARY' in titles
    assert 'FAITH & KARMA' in titles
    assert 'JOURNEY' in titles


def test_discoveries_sections_with_quiz_stats():
    from player import Player
    p = Player()
    fake = SimpleNamespace(
        player=p,
        correct_answers=10,
        wrong_answers=4,
        karma=3,
        dungeon_level=12,
        quiz_stats={
            'math': {'correct': 6, 'wrong': 2,
                     't1c': 3, 't1w': 1, 't2c': 3, 't2w': 1,
                     't3c': 0, 't3w': 0, 't4c': 0, 't4w': 0, 't5c': 0, 't5w': 0},
            'theology': {'correct': 4, 'wrong': 2,
                         't1c': 4, 't1w': 2,
                         't2c': 0, 't2w': 0, 't3c': 0, 't3w': 0,
                         't4c': 0, 't4w': 0, 't5c': 0, 't5w': 0},
        },
    )
    import main
    sections = main.Game._discoveries_sections(fake)
    # Find quiz section
    quiz_rows = next(rows for title, rows in sections if title == 'QUIZ PERFORMANCE')
    # Total line + blank + 2 subjects = 4 rows
    assert any('Total answered:  14' in r for r in quiz_rows)
    assert any('math' in r for r in quiz_rows)
    assert any('theology' in r for r in quiz_rows)


# ---------------------------------------------------------------------------
# quiz_stats tracking: ensure it accumulates correctly
# ---------------------------------------------------------------------------

def test_quiz_stats_initializes_empty():
    """A freshly constructed Game should have an empty quiz_stats dict."""
    src = Path('src/main.py').read_text(encoding='utf-8')
    # Static check: the init line must exist
    assert 'self.quiz_stats: dict = {}' in src


def test_quiz_stats_tracked_in_on_quiz_answer():
    """The _on_quiz_answer hook must bump the per-subject + per-tier counter."""
    src = Path('src/main.py').read_text(encoding='utf-8')
    # The tracking block should use setdefault on quiz_stats with subject key
    assert "self.quiz_stats.setdefault(subj" in src
    assert "t{tier}c" in src or "f't{tier}c'" in src


# ---------------------------------------------------------------------------
# _equip_delta_str: compare candidate vs currently equipped slot
# ---------------------------------------------------------------------------

class _RenderFake(_ResolvedFake):
    """Stand-in that exposes both kit helpers AND the render helpers
    (_equip_delta_str / _fmt_delta) bound to the real Game implementation."""

    def __getattr__(self, name):
        if name in ('_equip_delta_str', '_fmt_delta'):
            import main
            method = getattr(main.Game, name)
            if callable(method):
                return method.__get__(self, type(self))
            return method
        return super().__getattr__(name)


def test_equip_delta_weapon_positive():
    from items import Weapon
    p = _make_player_with_items()
    g = _RenderFake(p, [])
    # Equipped longsword avg 6.5 (1d8+2); candidate greataxe avg 10.5 (1d12+4)
    great = Weapon(_defn(id='great', name='greataxe', damage='1d12+4',
                         material='iron', identified=True))
    d = g._equip_delta_str(great)
    assert d.startswith('Δ +')
    assert 'dmg' in d


def test_equip_delta_weapon_negative():
    from items import Weapon
    p = _make_player_with_items()
    g = _RenderFake(p, [])
    # Equipped longsword 6.5; candidate club 3.5 (1d6)
    club = Weapon(_defn(id='club', name='club', damage='1d6',
                        material='wood', identified=True))
    d = g._equip_delta_str(club)
    assert d.startswith('Δ −')
    assert 'dmg' in d


def test_equip_delta_armor_uses_correct_slot():
    from items import Armor, ARMOR_SLOTS
    p = _make_player_with_items()
    g = _RenderFake(p, [])
    # Equipped plate mail in 'body' slot (ac_bonus=5); candidate brigandine ac=3
    brig = Armor(_defn(id='brig', name='brigandine', slot='body',
                       ac_bonus=3, material='iron', identified=True))
    d = g._equip_delta_str(brig)
    assert d.startswith('Δ −')
    assert 'AC' in d
    # Armor in unfilled slot: no delta possible
    helm = Armor(_defn(id='helm', name='helm', slot='head',
                       ac_bonus=2, material='iron', identified=True))
    assert g._equip_delta_str(helm) == ''


def test_equip_delta_returns_empty_when_no_equipped():
    from items import Weapon
    from player import Player
    p = Player()
    p.weapon = None
    g = _RenderFake(p, [])
    w = Weapon(_defn(id='sword', name='sword', damage='1d8',
                     material='iron', identified=True))
    # No weapon equipped -> nothing to compare against
    assert g._equip_delta_str(w) == ''


def test_equip_delta_hidden_when_candidate_unidentified():
    from items import Weapon
    p = _make_player_with_items()
    g = _RenderFake(p, [])
    mystery = Weapon(_defn(id='??', name='strange weapon', damage='1d8',
                           material='iron', identified=False, id_level=1))
    # id_level 1 -> no stats visible -> no delta
    assert g._equip_delta_str(mystery) == ''


def test_fmt_delta_zero_says_no_change():
    from player import Player
    g = _RenderFake(Player(), [])
    out = g._fmt_delta(0, 'AC')
    assert 'no change' in out
