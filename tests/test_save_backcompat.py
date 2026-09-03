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


def test_v265_legacy_assorted_parts_dropped():
    """v2.6.5: assorted_monster_parts was deleted. Old saves carrying an
    'Assorted Monster Parts' Ingredient have it removed from inventory on
    load (nothing valid to swap to)."""
    from food_system import load_ingredient_for
    from items import Ingredient
    from main import Game

    # Simulate a pre-v2.6.5 pickled ingredient by faking the id.
    # Take any current ingredient and give it the deleted id.
    stale = load_ingredient_for('giant_rat_prime')
    stale.id = 'assorted_monster_parts'
    stale.name = 'Assorted Monster Parts'

    class _M:
        pass
    g = _M(); g.player = _M(); g.player.inventory = [stale]
    Game._migrate_legacy_ingredients(g, {})

    # Dropped from inventory (no replacement possible).
    remaining_ings = [i for i in g.player.inventory if isinstance(i, Ingredient)]
    assert remaining_ings == [], "assorted_monster_parts should be dropped on v2.6.5 load"


def test_v265_legacy_family_cut_dropped():
    """Same story for family_* cuts."""
    from food_system import load_ingredient_for
    from items import Ingredient
    from main import Game

    stale = load_ingredient_for('goblin_prime')
    stale.id = 'family_humanoid'

    class _M:
        pass
    g = _M(); g.player = _M(); g.player.inventory = [stale]
    Game._migrate_legacy_ingredients(g, {})
    assert [i for i in g.player.inventory if isinstance(i, Ingredient)] == []


def test_legacy_unknown_ingredient_id_dropped():
    """Truly-removed ingredients (pre-any-current-schema) are dropped, not
    left as dead items."""
    from food_system import load_ingredient_for
    from items import Ingredient
    from main import Game

    stale = load_ingredient_for('goblin_prime')
    stale.id = 'orc_meat_legacy_gone'
    class _M:
        pass
    g = _M(); g.player = _M(); g.player.inventory = [stale]
    Game._migrate_legacy_ingredients(g, {})
    assert [i for i in g.player.inventory if isinstance(i, Ingredient)] == []


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
