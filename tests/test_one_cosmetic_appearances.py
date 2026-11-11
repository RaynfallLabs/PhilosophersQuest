"""One-cosmetic-per-item: every functional ring/amulet type has exactly ONE
mundane appearance per run, dealt from a shared pool; deleted variant ids
remap on load; identification stays type-keyed (2026-06-07). Since bug bash
3.3.2 the commons are ten kinds, each tiered by its level (rings.py): every
level of a kind is one type.

See proposals/design/one_cosmetic_appearances.md and
data/items/_collapse_cosmetic_accessories.py.
"""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
pygame.init()
pygame.font.init()

import random

from items import (Accessory, LEGACY_ACCESSORY_ID_REMAP, get_accessory_def,
                   load_accessory_appearances, load_items,
                   remap_legacy_accessory_id, type_class)
import main as main_mod


# ---------------------------------------------------------------------------
# Helpers — invoke the Game methods without constructing a full Game (no screen)
# ---------------------------------------------------------------------------

def _roll(rng=None):
    """Call Game._roll_appearance_map on a bare stub self."""
    stub = types.SimpleNamespace()
    return main_mod.Game._roll_appearance_map(stub, rng=rng)


def _stamp(item, amap):
    stub = types.SimpleNamespace(_appearance_map=amap)
    main_mod.Game.apply_appearance(stub, item)


def _accessories():
    return {a.id: a for a in load_items('accessory')}


# ---------------------------------------------------------------------------
# 1. Data layer: one functional type -> one entry, no name collisions
# ---------------------------------------------------------------------------

def test_no_two_nonunique_accessories_share_a_name():
    accs = load_items('accessory')
    seen = {}
    for a in accs:
        if getattr(a, 'is_unique', False):
            continue
        assert a.name not in seen, (
            f"non-unique name collision: {a.name!r} on {a.id} and {seen[a.name]}")
        seen[a.name] = a.id


def test_collapsed_cosmetic_types_are_single_entries():
    # Bug bash 3.3.2: the common rings and amulets are ten kinds (rings.py);
    # each exists once, its folded variants gone.
    accs = _accessories()
    for canon in ('ring_of_protection', 'ring_of_spell_turning', 'ring_of_regeneration',
                  'ring_of_invisibility', 'ring_of_sustenance', 'ring_of_wizardry',
                  'amulet_life_saving', 'amulet_of_wisdom', 'amulet_of_intellect',
                  'amulet_of_constitution'):
        assert canon in accs, f"missing canonical survivor {canon}"
    for gone in ('ring_searching_silver', 'ring_regen_emerald', 'ring_protection_gold',
                 'amulet_of_greater_wisdom', 'ring_of_strength', 'ring_of_searching'):
        assert gone not in accs, f"deleted variant {gone} still present"


def test_each_cosmetic_type_name_resolves_to_one_item():
    # Every kind has exactly ONE entry (the whole point of the collapse).
    import rings
    by_kind = {}
    for a in load_items('accessory'):
        if getattr(a, 'kind', ''):
            assert a.kind not in by_kind, (a.kind, a.id, by_kind[a.kind])
            by_kind[a.kind] = a.id
    assert set(by_kind) == set(rings.kinds())


# ---------------------------------------------------------------------------
# 2. A kind's tiers are levels of ONE type (bug bash 3.3.2, rings.py)
# ---------------------------------------------------------------------------

def test_a_kinds_levels_keep_distinct_power_and_names():
    import copy
    import rings
    accs = _accessories()
    lo, hi = copy.copy(accs['amulet_of_wisdom']), copy.copy(accs['amulet_of_wisdom'])
    rings.relevel(lo, 1)
    rings.relevel(hi, 9)
    assert lo.effects['amount'] == 1 and hi.effects['amount'] == 5
    assert lo.name == 'Amulet of Wisdom I' and hi.name == 'Amulet of Wisdom V'
    # One type: identifying one level knows the kind at every level.
    assert type_class(lo) == type_class(hi) == 'amulet_of_wisdom'


def test_kinds_spawn_flat_through_the_dungeon():
    # A ring found deep is the same kind, stronger: the level comes from the
    # armour bells (gear.roll_level), so a kind's own weight is flat.
    accs = _accessories()
    for a in accs.values():
        if getattr(a, 'kind', ''):
            assert list(a.floor_spawn_weight) == ['1-100'], a.id


# ---------------------------------------------------------------------------
# 3. Per-run appearance shuffle: deterministic, one look per managed type
# ---------------------------------------------------------------------------

def test_appearance_map_deals_one_look_per_managed_type():
    amap = _roll(random.Random(1234))
    accs = load_items('accessory')
    # Managed types = non-unique survivors carrying the neutral fallback look.
    managed = {type_class(a) for a in accs
               if not getattr(a, 'is_unique', False)
               and not getattr(a, 'identified', False)
               and (getattr(a, 'unidentified_name', '') or '').strip().lower()
               in ('a ring', 'an amulet')}
    assert managed, "no managed types found — migration not applied?"
    for cls in managed:
        assert cls in amap, f"managed type {cls} got no appearance"
        assert amap[cls]['name'] and amap[cls]['name'] not in ('a ring', 'an amulet')


def test_appearance_map_deterministic_given_seed():
    a1 = _roll(random.Random(42))
    a2 = _roll(random.Random(42))
    assert a1 == a2
    a3 = _roll(random.Random(99))
    # Different seed should (very likely) deal a different arrangement.
    assert a1 != a3


def test_appearances_pooled_by_slot_no_crossover():
    amap = _roll(random.Random(7))
    pool = load_accessory_appearances()
    ring_looks = {p['name'] for p in pool['ring']}
    amu_looks = {p['name'] for p in pool['amulet']}
    for cls, look in amap.items():
        if cls.startswith('ring_'):
            assert look['name'] in ring_looks, f"{cls} got non-ring look {look['name']}"
        elif cls.startswith('amulet_'):
            assert look['name'] in amu_looks, f"{cls} got non-amulet look {look['name']}"


def test_pool_has_headroom_for_managed_types():
    pool = load_accessory_appearances()
    accs = load_items('accessory')
    ring_types = {type_class(a) for a in accs
                  if a.slot == 'ring' and not getattr(a, 'is_unique', False)
                  and (getattr(a, 'unidentified_name', '') or '').strip().lower() == 'a ring'}
    amu_types = {type_class(a) for a in accs
                 if a.slot == 'amulet' and not getattr(a, 'is_unique', False)
                 and (getattr(a, 'unidentified_name', '') or '').strip().lower() == 'an amulet'}
    assert len(pool['ring']) >= len(ring_types), (
        f"ring pool {len(pool['ring'])} < {len(ring_types)} managed ring types")
    assert len(pool['amulet']) >= len(amu_types), (
        f"amulet pool {len(pool['amulet'])} < {len(amu_types)} managed amulet types")


def test_apply_appearance_stamps_name_and_color():
    amap = _roll(random.Random(5))
    accs = _accessories()
    ring = accs['ring_of_protection']
    assert ring.unidentified_name == 'A Ring'   # neutral before stamp
    _stamp(ring, amap)
    assert ring.unidentified_name != 'A Ring'
    assert isinstance(ring.color, tuple) and len(ring.color) == 3


def test_apply_appearance_noop_for_uniques():
    amap = _roll(random.Random(5))
    accs = _accessories()
    uniq = accs['ring_of_gyges']
    before = uniq.unidentified_name
    _stamp(uniq, amap)
    assert uniq.unidentified_name == before   # uniques keep their own look


def test_same_type_two_instances_get_same_look_in_one_run():
    amap = _roll(random.Random(321))
    defn = get_accessory_def('ring_of_protection')
    a = Accessory({**defn, 'id': 'ring_of_protection', 'item_class': 'accessory'})
    b = Accessory({**defn, 'id': 'ring_of_protection', 'item_class': 'accessory'})
    _stamp(a, amap)
    _stamp(b, amap)
    assert a.unidentified_name == b.unidentified_name   # ONE look per type per run


# ---------------------------------------------------------------------------
# 4. Identification stays type-keyed (know one -> know them all)
# ---------------------------------------------------------------------------

def test_identification_is_type_keyed_across_instances():
    from player import Player
    pl = Player()
    defn = get_accessory_def('ring_of_protection')
    seed = Accessory({**defn, 'id': 'ring_of_protection', 'item_class': 'accessory'})
    other = Accessory({**defn, 'id': 'ring_of_protection', 'item_class': 'accessory'})
    # Learn the class from the seed.
    pl.known_class_ids.add(type_class(seed))
    assert pl.knows_item_type(other) is True


def test_every_level_of_a_kind_is_identified_together():
    import copy
    import rings
    from player import Player
    pl = Player()
    accs = _accessories()
    lo, hi = copy.copy(accs['ring_of_protection']), copy.copy(accs['ring_of_protection'])
    rings.relevel(lo, 1)
    rings.relevel(hi, 10)
    pl.known_class_ids.add(type_class(lo))
    assert pl.knows_item_type(lo) is True and pl.knows_item_type(hi) is True


# ---------------------------------------------------------------------------
# 5. Deleted-id save remap
# ---------------------------------------------------------------------------

def test_remap_table_targets_all_exist():
    accs = _accessories()
    for old, new in LEGACY_ACCESSORY_ID_REMAP.items():
        assert new in accs, f"remap {old} -> {new}: survivor missing from accessory.json"
        assert old not in accs, f"remap source {old} should have been deleted"


def test_remap_legacy_id_resolves_to_survivor():
    assert remap_legacy_accessory_id('ring_regen_emerald') == 'ring_of_regeneration'
    assert remap_legacy_accessory_id('ring_protection_gold') == 'ring_of_protection'
    assert remap_legacy_accessory_id('amulet_wisdom_sage_ivory_locket') == 'amulet_of_wisdom'
    # A ring whose power moved to armour has no survivor (bug bash 3.3.2).
    assert remap_legacy_accessory_id('ring_searching_malachite') == 'ring_searching_malachite'
    # Surviving ids pass through unchanged.
    assert remap_legacy_accessory_id('ring_of_protection') == 'ring_of_protection'


def test_heal_accessory_id_rebuilds_a_deleted_variant():
    # Simulate an old-save item pickled under a now-deleted variant id.
    defn_old = {
        'name': 'ring of regeneration', 'symbol': '=', 'color': [60, 160, 80],
        'slot': 'ring', 'effects': {'status': 'regenerating', 'duration': -1},
        'unidentified_name': 'emerald ring', 'min_level': 1, 'quiz_tier': 2,
    }
    stale = Accessory({**defn_old, 'id': 'ring_regen_emerald', 'item_class': 'accessory'})
    stale.buc = 'blessed'
    stale.buc_known = True
    stale.id_level = 3
    main_mod.Game._heal_accessory_id(stale)
    # Re-pointed to the canonical kind, at the level of its old tier.
    assert stale.id == 'ring_of_regeneration' and stale.kind == 'regeneration'
    assert stale.name == 'Ring of Regeneration II' and stale.ench_level == 3
    assert (stale.effects or {}).get('status') == 'regenerating'
    # Per-instance progress preserved.
    assert stale.buc == 'blessed' and stale.buc_known is True and stale.id_level == 3


def test_heal_accessory_id_renamed_stat_tier_keeps_power():
    defn_old = {
        'name': 'amulet of greater wisdom', 'symbol': '"', 'color': [80, 90, 110],
        'slot': 'amulet', 'effects': {'stat': 'WIS', 'amount': 3},
        'unidentified_name': 'ivory locket', 'min_level': 25, 'quiz_tier': 3,
    }
    stale = Accessory({**defn_old, 'id': 'amulet_wisdom_sage_ivory_locket',
                       'item_class': 'accessory'})
    main_mod.Game._heal_accessory_id(stale)
    assert stale.id == 'amulet_of_wisdom'
    assert stale.name == 'Amulet of Wisdom III'
    assert stale.effects['amount'] == 3        # +3 power preserved


def test_heal_accessory_id_noop_for_current_ids():
    accs = _accessories()
    cur = accs['ring_of_protection']
    before_id = cur.id
    main_mod.Game._heal_accessory_id(cur)
    assert cur.id == before_id   # already canonical, untouched
