"""Identify v3.1 split-knowledge tests (2026-09-01).

The player carries two independent sets:
  - known_forms      (long_sword, plate_armor, ring, potion, ...)
  - known_materials  (iron, mithril, dragonscale, ...)

Once a form AND its material are both known, future items matching that
combo auto-show their true name in the inventory without a per-id-slug
identify event. BUC and enchant still need per-instance identify.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def test_new_player_has_empty_split_knowledge_sets():
    from player import Player
    p = Player()
    assert isinstance(p.known_forms, set)
    assert isinstance(p.known_materials, set)
    assert len(p.known_forms) == 0
    assert len(p.known_materials) == 0


def test_form_id_strips_material_prefix_for_weapons():
    from items import instantiate_weapon, form_id, material_id
    it = instantiate_weapon('longsword', 'iron')
    assert form_id(it) == 'longsword'
    assert material_id(it) == 'iron'


def test_form_id_strips_material_prefix_for_armor():
    from items import instantiate_armor, form_id, material_id
    # Pick any armor template + material combo that exists.
    from items import load_templates, load_materials
    tpls = load_templates('armor')
    mats = load_materials('armor')
    tid = next(iter(tpls.keys()))
    # Grab a material compatible with this template
    compat = set(tpls[tid].get('compatible_material_classes') or [])
    mid = None
    for m, defn in mats.items():
        mcls = defn.get('material_class') or defn.get('class')
        if not compat or (mcls and mcls in compat):
            mid = m
            break
    assert mid is not None
    it = instantiate_armor(tid, mid)
    assert form_id(it) == tid
    assert material_id(it) == mid


def test_form_id_returns_slug_for_accessories():
    """Accessories use the name-slug as form (matches type_class)."""
    from items import Accessory, form_id, material_id
    ring = Accessory({
        'id': 'iron_ring_of_strength',
        'name': 'Ring of Strength',
        'item_class': 'accessory',
        'slot': 'ring',
        'symbol': '=',
        'color': [200, 200, 50],
        'weight': 0.1,
    })
    assert form_id(ring) == 'ring_of_strength'
    # Accessories don't carry material — material_id is None.
    assert material_id(ring) is None


def test_form_id_returns_none_for_uniques():
    from items import form_id, material_id
    class MockUnique:
        is_unique = True
        id = 'sword_of_michael'
        material = 'divine_steel'
    m = MockUnique()
    assert form_id(m) is None
    assert material_id(m) is None


def test_is_split_type_known_needs_both_form_and_material():
    from items import instantiate_weapon, is_split_type_known
    from player import Player
    p = Player()
    it = instantiate_weapon('longsword', 'iron')

    # Neither known
    assert not is_split_type_known(p, it)
    # Only form
    p.known_forms.add('longsword')
    assert not is_split_type_known(p, it)
    # Only material
    p.known_forms.discard('longsword')
    p.known_materials.add('iron')
    assert not is_split_type_known(p, it)
    # Both known -> True
    p.known_forms.add('longsword')
    assert is_split_type_known(p, it)


def test_is_split_type_known_true_for_materialless_items_with_known_form():
    """A form without material (potion, scroll) only needs form-known."""
    from items import Item, is_split_type_known
    from player import Player
    p = Player()
    potion = Item({
        'id': 'potion_of_healing',
        'name': 'Potion of Healing',
        'item_class': 'potion',
        'symbol': '!',
        'color': [200, 100, 100],
        'weight': 0.3,
    })
    p.known_forms.add('potion_of_healing')
    assert is_split_type_known(p, potion)


def test_is_split_type_known_false_for_uniques():
    """Uniques never route through split-knowledge."""
    from items import is_split_type_known
    from player import Player
    class MockUnique:
        is_unique = True
        id = 'sword_of_michael'
        material = 'divine_steel'
    p = Player()
    p.known_forms.add('sword_of_michael')  # even if somehow added
    p.known_materials.add('divine_steel')
    assert not is_split_type_known(p, MockUnique())


def test_knows_item_type_routes_through_split_knowledge():
    from items import instantiate_weapon
    from player import Player
    p = Player()
    a = instantiate_weapon('longsword', 'iron')
    b = instantiate_weapon('shortsword', 'iron')
    c = instantiate_weapon('longsword', 'steel')

    # Baseline: nothing known.
    assert not p.knows_item_type(a)

    # Identify the iron long sword directly (populate all knowledge).
    p.known_item_ids.add(a.id)
    p.known_forms.add('longsword')
    p.known_materials.add('iron')

    # a is known by id.
    assert p.knows_item_type(a)
    # b (short_sword) is NOT known — form differs.
    assert not p.knows_item_type(b)
    # c (steel long_sword) is NOT known — material differs.
    assert not p.knows_item_type(c)

    # Now learn short_sword form (e.g. from a bronze short sword identify).
    p.known_forms.add('shortsword')
    # b should now auto-know (short_sword + iron both known).
    assert p.knows_item_type(b)
    # c still unknown (steel not learned).
    assert not p.knows_item_type(c)

    # Learn steel material.
    p.known_materials.add('steel')
    # c should now auto-know (long_sword + steel both known).
    assert p.knows_item_type(c)


def test_split_knowledge_combinatorics_win():
    """Learn a handful of forms + a handful of materials -> ALL their
    compatible combinations become auto-known. That's the design win:
    N forms × M materials combos covered by N + M unlocks."""
    from items import instantiate_weapon, load_templates, load_materials
    from player import Player
    p = Player()

    p.known_forms.update(['longsword', 'shortsword', 'dagger', 'mace'])
    p.known_materials.update(['iron', 'steel', 'bronze'])

    tpls = load_templates('weapons')
    mats = load_materials('weapons')

    checked = 0
    for tid in p.known_forms:
        compat = set(tpls.get(tid, {}).get('compatible_material_classes') or [])
        for mid in p.known_materials:
            if mid not in mats:
                continue
            mcls = mats[mid].get('material_class') or mats[mid].get('class')
            if compat and mcls and mcls not in compat:
                continue
            try:
                it = instantiate_weapon(tid, mid)
            except Exception:
                continue
            assert p.knows_item_type(it), \
                f"{tid}+{mid} should auto-know when form+material both learned"
            checked += 1
    assert checked >= 4, f"expected at least a few auto-known combos, got {checked}"


def test_migration_missing_sets_treated_as_empty():
    """Old saves have no known_forms / known_materials attrs. __setstate__
    should backfill empty sets so knows_item_type doesn't AttributeError."""
    from player import Player
    p = Player()
    # Simulate old pickled state without the split-knowledge fields.
    old_state = p.__getstate__()
    old_state.pop('known_forms', None)
    old_state.pop('known_materials', None)
    p2 = Player.__new__(Player)
    p2.__setstate__(old_state)
    assert hasattr(p2, 'known_forms')
    assert hasattr(p2, 'known_materials')
    assert p2.known_forms == set()
    assert p2.known_materials == set()
