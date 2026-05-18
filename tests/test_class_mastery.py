"""Tests for the class-level mastery system on common items.

Verifies the rules established 2026-05-18:
  - Each common item has a `mastery_class` derived from name (accessories) or
    id (wands/scrolls/potions/spellbooks)
  - Mastering one item in a class applies the blessing to ALL items in the
    class (in inventory + future drops)
  - The blessing is recorded on player.unlocked_class_masteries
  - Tier-1 identification names ALL items in the class (player.known_class_ids)
  - Uniques continue to use per-id mastery (player.unlocked_masteries)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
pygame.init()
pygame.font.init()


_BASE_DEFN = {'symbol': '=', 'color': [200, 200, 200]}


def _defn(**kw):
    return {**_BASE_DEFN, **kw}


# ---------------------------------------------------------------------------
# get_mastery_class
# ---------------------------------------------------------------------------

def test_get_mastery_class_for_accessory_uses_slugified_name():
    from items import Accessory
    from class_masteries import get_mastery_class
    a = Accessory(_defn(id='ring_strength_iron', name='ring of strength',
                        slot='ring', effects={'stat': 'STR', 'amount': 1}))
    assert get_mastery_class(a) == 'ring_of_strength'


def test_get_mastery_class_groups_ring_strength_variants():
    from items import Accessory
    from class_masteries import get_mastery_class
    a = Accessory(_defn(id='ring_strength_iron', name='ring of strength',
                        slot='ring', effects={'stat': 'STR', 'amount': 1}))
    b = Accessory(_defn(id='ring_strength_adamantine', name='ring of strength',
                        slot='ring', effects={'stat': 'STR', 'amount': 3}))
    assert get_mastery_class(a) == get_mastery_class(b) == 'ring_of_strength'


def test_get_mastery_class_for_wand_uses_id():
    from items import Wand
    from class_masteries import get_mastery_class
    w = Wand(_defn(id='wand_of_healing', name='wand of healing',
                   effect='heal', power='2d4',
                   charges=3, max_charges=3))
    assert get_mastery_class(w) == 'wand_of_healing'


def test_get_mastery_class_unique_returns_id():
    """Uniques always key mastery by id, not name."""
    from items import Weapon
    from class_masteries import get_mastery_class
    w = Weapon(_defn(id='soul_reaver', name='Soul Reaver',
                     damage='2d6+3', material='adamantine',
                     is_unique=True))
    assert get_mastery_class(w) == 'soul_reaver'


def test_get_mastery_class_separates_ring_vs_amulet():
    from items import Accessory
    from class_masteries import get_mastery_class
    ring = Accessory(_defn(id='ring_strength_iron', name='ring of strength',
                           slot='ring', effects={}))
    amulet = Accessory(_defn(id='amulet_strength_iron', name='amulet of strength',
                             slot='amulet', effects={}))
    # Ring of Strength and Amulet of Strength are DIFFERENT classes
    assert get_mastery_class(ring) != get_mastery_class(amulet)
    assert get_mastery_class(ring) == 'ring_of_strength'
    assert get_mastery_class(amulet) == 'amulet_of_strength'


# ---------------------------------------------------------------------------
# CLASS_MASTERY_BLESSINGS coverage
# ---------------------------------------------------------------------------

def test_authored_blessings_have_required_keys():
    from class_masteries import CLASS_MASTERY_BLESSINGS
    assert len(CLASS_MASTERY_BLESSINGS) >= 40
    for class_id, b in CLASS_MASTERY_BLESSINGS.items():
        assert 'kind' in b, f"{class_id} missing 'kind'"
        assert 'desc' in b, f"{class_id} missing 'desc'"
        assert b.get('scope') == 'class', f"{class_id} wrong scope"


def test_authored_blessings_are_small_flavor():
    """User-defined rule: class blessings are SMALL flavor bonuses, not major."""
    from class_masteries import CLASS_MASTERY_BLESSINGS
    for class_id, b in CLASS_MASTERY_BLESSINGS.items():
        kind = b.get('kind', '')
        val = b.get('value')
        if 'stat_bonus' in kind and isinstance(val, dict):
            amt = abs(int(val.get('amount', 0)))
            assert amt <= 1, f"{class_id} stat bonus too large: {amt} (rule: small flavor)"
        if 'extra_charge' in kind:
            extra = int(val) if isinstance(val, (int, float)) else 0
            assert extra <= 2, f"{class_id} too many extra charges: {extra}"
        if 'potency_bonus' in kind:
            pct = float(val) if isinstance(val, (int, float)) else 0
            assert pct <= 0.30, f"{class_id} potency bonus too large: {pct}"


def test_default_blessing_fallback_per_type():
    from items import Accessory, Wand, Scroll, Spellbook, Potion
    from class_masteries import default_blessing_for_class
    a = Accessory(_defn(id='x', name='ring of fingertips', slot='ring', effects={}))
    assert default_blessing_for_class('ring_of_fingertips', a) is not None
    w = Wand(_defn(id='wand_x', name='wand', effect='heal', power='1d4',
                   charges=1, max_charges=1))
    assert default_blessing_for_class('wand_x', w) is not None
    s = Scroll(_defn(id='scroll_x', name='scroll', effect='heal', power='1d4'))
    assert default_blessing_for_class('scroll_x', s) is not None
    sb = Spellbook(_defn(id='sb_x', name='spellbook',
                          spell_id='magic_missile_spell', spell_name='MM',
                          mp_cost=4))
    assert default_blessing_for_class('sb_x', sb) is not None
    p = Potion(_defn(id='potion_x', name='potion', effect='heal', power='1d4'))
    assert default_blessing_for_class('potion_x', p) is not None


# ---------------------------------------------------------------------------
# Player class-mastery state
# ---------------------------------------------------------------------------

def test_player_starts_with_empty_class_mastery_state():
    from player import Player
    p = Player()
    assert hasattr(p, 'unlocked_class_masteries')
    assert hasattr(p, 'known_class_ids')
    assert p.unlocked_class_masteries == {}
    assert p.known_class_ids == set()


# ---------------------------------------------------------------------------
# Static check: identify dispatch is unified
# ---------------------------------------------------------------------------

def test_identify_item_always_routes_to_escalator():
    """_identify_item should always call _identify_unique_item — no split."""
    from pathlib import Path
    src = Path('src/game_magic.py').read_text(encoding='utf-8')
    # _identify_common_item should be gone
    assert '_identify_common_item' not in src, \
        "_identify_common_item should have been removed (unified escalator path)"
    # _identify_item should just route to _identify_unique_item
    idx = src.find('def _identify_item(self, item)')
    assert idx >= 0
    block = src[idx:idx + 600]
    assert '_identify_unique_item' in block


def test_claim_mastery_routes_commons_to_class_store():
    """_claim_mastery must check is_unique and route accordingly."""
    from pathlib import Path
    src = Path('src/game_magic.py').read_text(encoding='utf-8')
    idx = src.find('def _claim_mastery(self, item)')
    assert idx >= 0
    block = src[idx:idx + 2000]
    assert 'unlocked_class_masteries' in block
    assert 'is_unique' in block


def test_propagate_identification_handles_classes():
    from pathlib import Path
    src = Path('src/game_magic.py').read_text(encoding='utf-8')
    idx = src.find('def _propagate_identification')
    assert idx >= 0
    block = src[idx:idx + 1500]
    assert 'known_class_ids' in block
    assert 'get_mastery_class' in block
