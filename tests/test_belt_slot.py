"""Tests for the new `belt` accessory slot.

Spec (user direction 2026-05-29):
- 5 items convert from ring/amulet to belt:
    Megingjörð, Girdle of Hippolyta (renamed from Amulet of Hippolyta),
    Ariadne's Thread, Rope of Izanagi, Anansi's Thread
- Belt slot mirrors the amulet slot: single equipped item, swaps in
  on equip of a new belt
- Engine touch points: Player.belt_slot, equipped_accessories iterator,
  _apply_equip handler, get_equipped_items dict, character sheet,
  equip menu, uncurse-prayer scan
- Save back-compat: defensive getattr() at every read site so old
  pickled players without belt_slot don't crash
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# Data: 5 items have slot=belt; Hippolyta renamed
# ---------------------------------------------------------------------------

_BELT_ITEM_IDS = {
    'megingjord',
    'amulet_of_hippolyta',
    'ariadnes_thread',
    'rope_of_izanagi',
    'anansis_thread',
}


def test_five_items_have_belt_slot():
    d = json.loads((ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    actual = {k for k, v in d.items()
              if isinstance(v, dict) and v.get('slot') == 'belt'}
    assert actual == _BELT_ITEM_IDS, (
        f"expected belt items {_BELT_ITEM_IDS}; got {actual}"
    )


def test_hippolyta_renamed_to_girdle():
    d = json.loads((ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    assert d['amulet_of_hippolyta']['name'] == 'Girdle of Hippolyta'


def test_no_unique_left_with_ambiguous_belt_lore():
    """Sanity: every item whose lore explicitly calls it a 'belt' or
    'girdle' should ALSO be slot=belt (or have a deliberate exception
    like Ring of Sir Gawain, where the item is a ring inspired by the
    girdle, not the girdle itself)."""
    d = json.loads((ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    # Items we DELIBERATELY keep off the belt list despite belt/girdle
    # appearing in their lore (lore is contextual, not descriptive of
    # the item itself)
    _EXCEPTIONS = {'ring_of_gawain'}
    bad = []
    for k, v in d.items():
        if not isinstance(v, dict) or not v.get('is_unique'):
            continue
        if k in _EXCEPTIONS or k in _BELT_ITEM_IDS:
            continue
        lore = (v.get('lore') or '').lower()
        if ' belt ' in lore or ' girdle ' in lore:
            bad.append(f'{k}: {lore[:80]}')
    assert not bad, (
        "Items with 'belt' or 'girdle' in lore that AREN'T slot=belt "
        "and AREN'T in the exception list:\n" + "\n".join(bad[:5])
    )


# ---------------------------------------------------------------------------
# Engine: belt_slot exists and is iterable through equipped_accessories
# ---------------------------------------------------------------------------

def test_player_has_belt_slot_field():
    from player import Player
    p = Player()
    assert hasattr(p, 'belt_slot')
    assert p.belt_slot is None


def test_equipped_accessories_includes_belt():
    """Once a belt is set, it must appear in `equipped_accessories`
    alongside the amulet — every passive/scan that iterates
    `equipped_accessories` will then see the belt's effects."""
    from player import Player

    class _StubBeltItem:
        slot = 'belt'
        id = 'megingjord'
        name = 'Megingjörð'
        cursed = False
        buc = 'uncursed'
        effects: dict = {}

    p = Player()
    p.belt_slot = _StubBeltItem()
    accs = p.equipped_accessories
    assert any(getattr(a, 'id', None) == 'megingjord' for a in accs)


def test_old_save_without_belt_slot_does_not_crash():
    """Save back-compat: a Player loaded from an old pickle won't have
    `belt_slot` as an attribute. The defensive getattr() in
    equipped_accessories must handle it."""
    from player import Player
    p = Player()
    # Simulate old save: delete the attribute that didn't exist before
    if hasattr(p, 'belt_slot'):
        del p.belt_slot
    # Should not raise
    assert p.equipped_accessories == p.equipped_accessories  # idempotent
    # get_equipped_items also reads it
    eq = p.get_equipped_items()
    assert eq['belt'] is None


# ---------------------------------------------------------------------------
# UI source-regression: belt is wired into the character sheet, equip
# menu, and uncurse scan. Tests assert the right code paths exist.
# ---------------------------------------------------------------------------

def test_character_sheet_lists_belt_slot():
    """game_render.py:_draw_character_sheet_screen iterates a list
    `slot_items` that must include ('Belt', p.belt_slot)."""
    import inspect
    import game_render
    src = inspect.getsource(game_render.RenderMixin)
    assert "('Belt'," in src, (
        "Character sheet must include a ('Belt', ...) row alongside "
        "the Amulet/Ring rows"
    )


def test_equip_menu_lists_belt_slot():
    """game_menus equip menu must enumerate belt_slot."""
    import inspect
    import game_menus
    src = inspect.getsource(game_menus.MenuMixin)
    assert "belt_slot" in src, (
        "Equip menu must include belt_slot in equip_menu_equipped"
    )


def test_uncurse_scan_includes_belt():
    """The Confiteor (uncurse) prayer must scan the belt slot for
    cursed gear too, otherwise a cursed belt would be un-removable."""
    import inspect
    import game_divine
    src = inspect.getsource(game_divine)
    # The scan code references belt_slot at the same level as amulet_slot
    assert "belt_slot" in src, (
        "uncurse scan in game_divine.py must inspect belt_slot for "
        "cursed gear (mirror of amulet_slot handling)"
    )
