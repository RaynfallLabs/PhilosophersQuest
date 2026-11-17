"""One disguise per kind (round 3, 2026-11-14).

Known by Hand (src/known_by_hand.py) keys on the KIND (the item id: the
material + template for common gear). Before identification, 76 armour
names were shared by two kinds: linen and rawhide both trimmed to "Rough",
so a "Rough Cloak" was either, and its BY HAND mark (or an equip with no
quiz) told the two apart. Brandon: "a linen and hide plate are not both
'rough' but 'rough cloth' and 'rough hide'". An unidentified name may show
the material's class; it must belong to exactly one kind.

Data-layer tests: every kind any spawn path can make, against every other.
"""
import json
import os
import random
import sys
from collections import defaultdict

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import items  # noqa: E402
import known_by_hand as kbh  # noqa: E402
from naming import proper_name  # noqa: E402


def _accepts(tpl, mat, shield=False):
    """The spawn rule (items._template_then_material, smithing._accepts):
    the template takes the material's class; a shield, a material that
    applies to shields."""
    acc = set(tpl.get('compatible_material_classes') or ())
    cls = set(str(mat.get('material_class', '')).split(','))
    if acc and not acc & cls:
        return False
    if shield:
        applies = mat.get('applies_to')
        if applies and 'shield' not in applies:
            return False
    return True


def _common_kinds():
    """Every common armour piece and shield a find, a chest, a trader, a
    smith's order or a drop can make: one instance per kind."""
    out = {}
    mats = items.load_materials('armor')
    for tid, tpl in items.load_templates('armor').items():
        for mid, mat in mats.items():
            if _accepts(tpl, mat):
                it = items.instantiate_armor(tid, mid)
                out[it.id] = it
    for tid, tpl in items.load_templates('shields').items():
        for mid, mat in mats.items():
            if _accepts(tpl, mat, shield=True):
                it = items.instantiate_shield(tid, mid)
                out[it.id] = it
    # Fixed specs: the starting kits (welcome_screen) and a drop made to a
    # spec ("armor:cloak:hide:elementward:2").
    from welcome_screen import SECRET_BUILDS
    for b in SECRET_BUILDS.values():
        sh, ar = b.get('_start_shield'), b.get('_start_armor')
        if isinstance(sh, tuple):
            it = items.instantiate_shield(sh[0], sh[1])
            out[it.id] = it
        if isinstance(ar, tuple):
            it = items.instantiate_armor(ar[0], ar[1])
            out[it.id] = it
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    for m in mons.values():
        spec = str((m or {}).get('unique_drop_id', '') if isinstance(m, dict) else '')
        if spec.startswith('armor:'):
            it = items.made_drop(spec)
            if it is not None:
                out[it.id] = it
    return out


def _named_kinds(rng):
    """Every named or data-defined wearable that asks a quiz, the rings and
    amulets wearing this run's dealt looks (Game._roll_appearance_map)."""
    from main import Game
    amap = Game._roll_appearance_map(object(), rng)
    out = {}
    for cat in ('armor', 'shield', 'accessory'):
        for it in items.load_items(cat):
            look = amap.get(items.type_class(it)) if cat == 'accessory' else None
            if look and not getattr(it, 'is_unique', False):
                it.unidentified_name = look['name']
            out.setdefault(it.id, it)
    return out


def _disguise(it):
    if getattr(it, 'identified', False):
        return None                    # known from the start: no disguise to share
    return proper_name(str(it.unidentified_name or '')).strip().lower()


def test_no_two_kinds_share_a_disguise():
    """Known by Hand tells kinds apart, so a disguise names one kind."""
    for seed in (1, 2, 3, 11, 29):
        kinds = dict(_common_kinds())
        for iid, it in _named_kinds(random.Random(seed)).items():
            kinds.setdefault(iid, it)
        by_name = defaultdict(set)
        for iid, it in kinds.items():
            if not kbh.asks_quiz(it):
                continue
            name = _disguise(it)
            if name:
                by_name[name].add(iid)
        shared = {n: sorted(k) for n, k in by_name.items() if len(k) > 1}
        assert not shared, (seed, shared)


def test_linen_and_rawhide_are_rough_cloth_and_rough_hide():
    for tid, cloth, hide in (('cloak', 'Rough Cloth Cloak', 'Rough Hide Cloak'),
                             ('leather_boots', 'Rough Cloth Boots', 'Rough Hide Boots'),
                             ('padded', 'Rough Cloth Padded Coat', 'Rough Hide Padded Coat'),
                             ('padded_shirt', 'Rough Cloth Shirt', 'Rough Hide Shirt'),
                             ('cloth_leggings', 'Rough Cloth Breeches', 'Rough Hide Breeches')):
        assert items.instantiate_armor(tid, 'linen').unidentified_name == cloth
        assert items.instantiate_armor(tid, 'rawhide').unidentified_name == hide
    # A template that is itself a hide word does not say it twice.
    assert items.instantiate_armor('hide', 'rawhide').unidentified_name == 'Rough Hide Armor'
    assert items.instantiate_armor('leather', 'rawhide').unidentified_name == 'Rough Hide Jerkin'


def test_a_disguise_names_the_class_and_never_the_material():
    for mid in ('linen', 'rawhide'):
        mat = items.get_material('armor', mid)
        assert mat.get('disguise'), mid
        for tid in ('cloak', 'leather_cap', 'leather_gloves'):
            name = items.instantiate_armor(tid, mid).unidentified_name
            assert mid not in name.lower(), name


def test_every_common_disguise_is_short_and_title_case():
    # Six words is the longest there is ("Dull Red-Grey Metal Full Plate
    # Armor"); a disguise made to tell two kinds apart is no longer.
    for iid, it in _common_kinds().items():
        name = str(it.unidentified_name)
        assert name == proper_name(name), (iid, name)
        assert len(name.split()) <= 6 and len(name) <= 44, (iid, name)
    for mid in ('linen', 'rawhide'):
        for iid, it in _common_kinds().items():
            if iid.startswith(mid + '_'):
                assert len(str(it.unidentified_name).split()) <= 5, iid
        assert not name.lower().startswith(('a ', 'an ', 'the ')), (iid, name)


def test_an_old_saves_rough_cloak_takes_its_new_disguise_on_load(monkeypatch, tmp_path):
    """A save's linen cloak was a "Rough Cloak"; loading recomposes it from
    today's data (Game._migrate_recompose_composite_items)."""
    import pygame
    import bones
    import save_system
    from main import Game
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    pygame.init()
    g = Game(pygame.display.set_mode((1, 1)), player_name='__disguises__', secret_build=None)
    cloak = items.instantiate_armor('cloak', 'linen')
    cloak.unidentified_name = 'Rough Cloak'
    hide = items.instantiate_armor('cloak', 'rawhide')
    hide.unidentified_name = 'Rough Cloak'
    shelf = items.instantiate_armor('leather_boots', 'linen')
    shelf.unidentified_name = 'Rough Boots'

    class _Stall:                       # a trader on the floor, his stock on the shelf
        stock = [shelf]
    g.player.inventory.append(cloak)
    hide.x, hide.y = g.player.x, g.player.y
    g._migrate_recompose_composite_items({'ground_items': [hide, _Stall()], 'level_mgr': None})
    assert cloak.unidentified_name == 'Rough Cloth Cloak'
    assert hide.unidentified_name == 'Rough Hide Cloak'
    assert shelf.unidentified_name == 'Rough Cloth Boots'
