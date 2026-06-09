"""Back-compat: old saves must absorb this session's data changes on load
without breaking (2026-06-07).

Verified end-to-end by headless-loading the real saves through Game.load_state;
these two unit tests pin the migration invariants that are easy to break later:
  1. a pre-overhaul 'Assorted Monster Parts' Ingredient is reconciled to the
     eatable 'Assorted Monster Jerky' (the cooking overhaul renamed it + added
     edible_safe/raw_sp; old pickled instances missed both).
  2. the one-cosmetic accessory remap maps every removed variant id to a
     SURVIVING id (else an old save's ring would become a dead item on load).
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import json
from pathlib import Path

_ACC = Path(__file__).resolve().parents[1] / 'data' / 'items' / 'accessory.json'


def test_legacy_assorted_parts_reconciled_to_jerky():
    from food_system import load_ingredient_for
    from main import Game
    stale = load_ingredient_for('assorted_monster_parts')
    stale.name = 'Assorted Monster Parts'   # pre-overhaul pickled state
    stale.edible_safe = False
    stale.raw_sp = None

    class _M:
        pass
    g = _M(); g.player = _M(); g.player.inventory = [stale]
    Game._migrate_legacy_ingredients(g, {})

    assert stale.name == 'Assorted Monster Jerky'
    assert stale.edible_safe is True
    assert stale.raw_sp == 25


def test_legacy_unknown_ingredient_id_swapped_not_crashed():
    # A truly-removed ingredient id (pre-2026-05-31 redesign) must be swapped for
    # assorted parts, not left as a dead item.
    from food_system import load_ingredient_for
    from main import Game
    dead = load_ingredient_for('assorted_monster_parts')
    dead.id = 'orc_meat_legacy_gone'          # an id no longer in the bank

    class _M:
        pass
    g = _M(); g.player = _M(); g.player.inventory = [dead]
    Game._migrate_legacy_ingredients(g, {})
    assert g.player.inventory[0].id == 'assorted_monster_parts'


def test_accessory_remap_targets_all_valid_and_non_noop():
    from items import LEGACY_ACCESSORY_ID_REMAP
    valid = set(json.loads(_ACC.read_text(encoding='utf-8')).keys())
    bad = {o: n for o, n in LEGACY_ACCESSORY_ID_REMAP.items() if n not in valid}
    assert not bad, f"remap maps to non-existent ids (dead items on load): {bad}"
    noop = [k for k in LEGACY_ACCESSORY_ID_REMAP if k in valid]
    assert not noop, f"remap keys still exist in accessory.json (contradiction): {noop}"
    assert len(LEGACY_ACCESSORY_ID_REMAP) >= 70   # the cosmetic-collapse set


def test_class_accessors_safe_on_a_pre_class_player():
    # An old save's player has no class_* attrs; class_system must read them as
    # empty defaults, never AttributeError.
    import class_system as cs
    from player import Player
    p = Player()
    assert cs.class_path(p) == []
    assert cs.proficiency(p, 'healing_received_pct') == 0
    assert cs.weapon_flat_bonus(p, None) == 0
    assert cs.save_bonus(p, 'body') == 0
    assert cs.offered_choices(p)            # Fighter always offered, no crash
