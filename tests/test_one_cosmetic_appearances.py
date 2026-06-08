"""One-cosmetic-per-item: every functional ring/amulet type has exactly ONE
mundane appearance per run, dealt from a shared pool; tiered stat rings keep
distinct power under disambiguated names; deleted variant ids remap on load;
identification stays type-keyed (2026-06-07).

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
                   remap_legacy_accessory_id)
from class_masteries import CLASS_MASTERY_BLESSINGS, get_mastery_class
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
    accs = _accessories()
    # Each canonical cosmetic survivor exists exactly once; its old variants gone.
    for canon in ('ring_of_searching', 'ring_of_warning', 'ring_of_telepathy',
                  'ring_of_regeneration', 'ring_of_fire_resist', 'ring_of_cold_resist',
                  'amulet_of_searching', 'amulet_of_warning', 'amulet_of_telepathy'):
        assert canon in accs, f"missing canonical survivor {canon}"
    for gone in ('ring_searching_silver', 'ring_searching_malachite', 'ring_warning_oak',
                 'amulet_searching_bone'):
        assert gone not in accs, f"deleted variant {gone} still present"


def test_each_cosmetic_type_name_resolves_to_one_item():
    # Every canonical cosmetic display name must map to exactly ONE entry (the
    # whole point of the collapse). Grouping by the literal "ring/amulet of X"
    # name, not by status, so named amulets carrying a regen side-effect
    # (Ouroboros, Ankh of Ra) don't count as variants of the plain type.
    accs = load_items('accessory')
    from collections import defaultdict
    cosmetic_names = {
        'ring of warning', 'ring of searching', 'ring of telepathy',
        'ring of regeneration', 'ring of fire resist', 'ring of cold resist',
        'ring of shock resist', 'ring of poison resist', 'ring of sleep resist',
        'amulet of warning', 'amulet of searching', 'amulet of telepathy',
    }
    by_name = defaultdict(list)
    for a in accs:
        if a.name in cosmetic_names:
            by_name[a.name].append(a.id)
    for name, ids in by_name.items():
        assert len(ids) == 1, f"cosmetic type {name!r} has multiple definitions: {ids}"
    # And all expected types are present.
    assert set(by_name) == cosmetic_names


# ---------------------------------------------------------------------------
# 2. Tiered stat rings keep DISTINCT power under disambiguated names
# ---------------------------------------------------------------------------

def test_strength_ring_tiers_distinct_power_and_names():
    accs = _accessories()
    base = accs['ring_of_strength']
    greater = accs['ring_of_greater_strength']
    master = accs['ring_of_master_strength']
    assert base.effects['amount'] == 1
    assert greater.effects['amount'] == 2
    assert master.effects['amount'] == 3
    # Honest, distinct display names
    assert base.name == 'ring of strength'
    assert greater.name == 'ring of greater strength'
    assert master.name == 'ring of master strength'
    # And distinct mastery classes (each tier is its own type now)
    assert len({get_mastery_class(base), get_mastery_class(greater),
                get_mastery_class(master)}) == 3


def test_all_six_stat_rings_have_three_distinct_tiers():
    accs = _accessories()
    for stat, word in (('strength', 'strength'), ('constitution', 'constitution'),
                       ('dexterity', 'dexterity'), ('intellect', 'intellect'),
                       ('wisdom', 'wisdom'), ('perception', 'perception')):
        amounts = []
        for tier_id in (f'ring_of_{word}', f'ring_of_greater_{word}', f'ring_of_master_{word}'):
            assert tier_id in accs, f"missing tier {tier_id}"
            amounts.append(accs[tier_id].effects['amount'])
        assert amounts == [1, 2, 3], f"{stat} tiers not 1/2/3: {amounts}"


def test_amulet_stat_tiers_are_plus2_and_plus3():
    accs = _accessories()
    for word in ('strength', 'constitution', 'dexterity', 'intellect', 'wisdom', 'perception'):
        base = accs[f'amulet_of_{word}']
        greater = accs[f'amulet_of_greater_{word}']
        assert base.effects['amount'] == 2
        assert greater.effects['amount'] == 3


def test_tiered_bell_curve_weights_preserved():
    # The deep tiers must keep their late-floor bell (1 at floor 1-20, climbing).
    accs = _accessories()
    master = accs['ring_of_master_strength']
    fsw = master.floor_spawn_weight
    assert fsw.get('1-20') == 1 and fsw.get('21-40') == 20, fsw
    # Base tier-1 ring keeps its early bell (20 tapering to 10).
    base = accs['ring_of_strength']
    bfsw = base.floor_spawn_weight
    assert bfsw.get('1-20') == 20 and bfsw.get('81-100') == 10, bfsw


def test_every_renamed_stat_tier_has_a_mastery_blessing():
    # After the rename, each of the 6-stat x {base/greater[/master]} tier slugs
    # I created must have a class-mastery entry so the pat-on-the-back bonus
    # still fires. (Bespoke distinct-named rings like "ring of giant strength"
    # never had a class blessing and are intentionally out of scope.)
    expected = []
    for word in ('strength', 'constitution', 'dexterity', 'intellect', 'wisdom', 'perception'):
        expected += [f'ring_of_{word}', f'ring_of_greater_{word}', f'ring_of_master_{word}',
                     f'amulet_of_{word}', f'amulet_of_greater_{word}']
    for slug in expected:
        assert slug in CLASS_MASTERY_BLESSINGS, f"renamed tier slug {slug!r} has no mastery blessing"


# ---------------------------------------------------------------------------
# 3. Per-run appearance shuffle: deterministic, one look per managed type
# ---------------------------------------------------------------------------

def test_appearance_map_deals_one_look_per_managed_type():
    amap = _roll(random.Random(1234))
    accs = load_items('accessory')
    # Managed types = non-unique survivors carrying the neutral fallback look.
    managed = {get_mastery_class(a) for a in accs
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
    ring_types = {get_mastery_class(a) for a in accs
                  if a.slot == 'ring' and not getattr(a, 'is_unique', False)
                  and (getattr(a, 'unidentified_name', '') or '').strip().lower() == 'a ring'}
    amu_types = {get_mastery_class(a) for a in accs
                 if a.slot == 'amulet' and not getattr(a, 'is_unique', False)
                 and (getattr(a, 'unidentified_name', '') or '').strip().lower() == 'an amulet'}
    assert len(pool['ring']) >= len(ring_types), (
        f"ring pool {len(pool['ring'])} < {len(ring_types)} managed ring types")
    assert len(pool['amulet']) >= len(amu_types), (
        f"amulet pool {len(pool['amulet'])} < {len(amu_types)} managed amulet types")


def test_apply_appearance_stamps_name_and_color():
    amap = _roll(random.Random(5))
    accs = _accessories()
    ring = accs['ring_of_searching']
    assert ring.unidentified_name == 'a ring'   # neutral before stamp
    _stamp(ring, amap)
    assert ring.unidentified_name != 'a ring'
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
    defn = get_accessory_def('ring_of_searching')
    a = Accessory({**defn, 'id': 'ring_of_searching', 'item_class': 'accessory'})
    b = Accessory({**defn, 'id': 'ring_of_searching', 'item_class': 'accessory'})
    _stamp(a, amap)
    _stamp(b, amap)
    assert a.unidentified_name == b.unidentified_name   # ONE look per type per run


# ---------------------------------------------------------------------------
# 4. Identification stays type-keyed (know one -> know them all)
# ---------------------------------------------------------------------------

def test_identification_is_type_keyed_across_instances():
    from player import Player
    pl = Player()
    defn = get_accessory_def('ring_of_searching')
    seed = Accessory({**defn, 'id': 'ring_of_searching', 'item_class': 'accessory'})
    other = Accessory({**defn, 'id': 'ring_of_searching', 'item_class': 'accessory'})
    # Learn the class from the seed.
    pl.known_class_ids.add(get_mastery_class(seed))
    assert pl.knows_item_type(other) is True


def test_distinct_tiers_are_separately_identified():
    from player import Player
    pl = Player()
    accs = _accessories()
    base = accs['ring_of_strength']
    master = accs['ring_of_master_strength']
    pl.known_class_ids.add(get_mastery_class(base))
    # Knowing +1 must NOT reveal the +3 tier — they are honest, distinct types.
    assert pl.knows_item_type(base) is True
    assert pl.knows_item_type(master) is False


# ---------------------------------------------------------------------------
# 5. Deleted-id save remap
# ---------------------------------------------------------------------------

def test_remap_table_targets_all_exist():
    accs = _accessories()
    for old, new in LEGACY_ACCESSORY_ID_REMAP.items():
        assert new in accs, f"remap {old} -> {new}: survivor missing from accessory.json"
        assert old not in accs, f"remap source {old} should have been deleted"


def test_remap_legacy_id_resolves_to_survivor():
    assert remap_legacy_accessory_id('ring_searching_malachite') == 'ring_of_searching'
    assert remap_legacy_accessory_id('ring_strength_mithril') == 'ring_of_master_strength'
    assert remap_legacy_accessory_id('amulet_strength_iron_medallion') == 'amulet_of_strength'
    # Surviving ids pass through unchanged.
    assert remap_legacy_accessory_id('ring_of_searching') == 'ring_of_searching'


def test_heal_accessory_id_rebuilds_a_deleted_variant():
    # Simulate an old-save item pickled under a now-deleted variant id.
    defn_old = {
        'name': 'ring of searching', 'symbol': '=', 'color': [60, 160, 80],
        'slot': 'ring', 'effects': {'status': 'searching', 'duration': -1},
        'unidentified_name': 'malachite ring', 'min_level': 1, 'quiz_tier': 1,
    }
    stale = Accessory({**defn_old, 'id': 'ring_searching_malachite', 'item_class': 'accessory'})
    stale.buc = 'blessed'
    stale.buc_known = True
    stale.id_level = 3
    main_mod.Game._heal_accessory_id(stale)
    # Re-pointed to the canonical id + canonical mechanical fields.
    assert stale.id == 'ring_of_searching'
    assert stale.name == 'ring of searching'
    assert (stale.effects or {}).get('status') == 'searching'
    # Per-instance progress preserved.
    assert stale.buc == 'blessed' and stale.buc_known is True and stale.id_level == 3


def test_heal_accessory_id_renamed_stat_tier_keeps_power():
    defn_old = {
        'name': 'ring of strength', 'symbol': '=', 'color': [80, 90, 110],
        'slot': 'ring', 'effects': {'stat': 'STR', 'amount': 3},
        'unidentified_name': 'adamantine ring', 'min_level': 25, 'quiz_tier': 3,
    }
    stale = Accessory({**defn_old, 'id': 'ring_strength_adamantine', 'item_class': 'accessory'})
    main_mod.Game._heal_accessory_id(stale)
    assert stale.id == 'ring_of_master_strength'
    assert stale.name == 'ring of master strength'
    assert stale.effects['amount'] == 3        # +3 power preserved


def test_heal_accessory_id_noop_for_current_ids():
    accs = _accessories()
    cur = accs['ring_of_searching']
    before_id = cur.id
    main_mod.Game._heal_accessory_id(cur)
    assert cur.id == before_id   # already canonical, untouched
