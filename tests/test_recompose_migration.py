"""Old saves absorb composite-item naming fixes + template rebalances on load
(2026-06-07).

Item name/AC are baked in at instantiation and pickled, so a pre-fix save still
shows 'Hide Hide Armor' (AC 1). _migrate_recompose_composite_items recomputes
name/unidentified_name (+ armor AC) from current template+material JSON, while
leaving uniques (id is not '<material>_<template>') untouched.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from items import instantiate_armor, instantiate_weapon
from main import Game


class _P:
    def __init__(self, inv):
        self.inventory = inv
        self.weapon = self.ranged_weapon = self.shield = None
        self.armor_slots = []


def _run(inv, state=None):
    g = Game.__new__(Game)
    g.player = _P(inv)
    Game._migrate_recompose_composite_items(g, state or {})


def test_stale_doubled_name_and_ac_recomposed():
    a = instantiate_armor('hide', 'hide')      # current: 'Hide Armor', AC 2
    a.name = 'Hide Hide Armor'                  # the old baked-in values
    a.unidentified_name = 'Hide Hide Armor'
    a.ac_bonus = 1
    _run([a])
    assert a.name == 'Hide Armor'
    assert a.ac_bonus == 2


def test_unique_id_without_material_prefix_is_untouched():
    a = instantiate_armor('hide', 'hide')
    a.id = 'excalibur'                          # unique id, not '<mat>_<tpl>'
    a.name = 'STALE UNIQUE NAME'
    _run([a])
    assert a.name == 'STALE UNIQUE NAME'


def test_known_unique_with_colliding_material_prefix_is_skipped():
    """A hand-authored unique whose id starts with a real material name (e.g.
    bronze_aegis, cloth_of_penelope) must NOT be recomposed -- the guard checks
    the known-unique-id set, not just the '<mat>_' startswith heuristic."""
    import json
    from pathlib import Path

    from items import get_material
    root = Path(__file__).resolve().parents[1]
    target = None
    for cat in ('armor', 'shield', 'weapon'):
        d = json.loads((root / 'data' / 'items' / f'{cat}.json').read_text(encoding='utf-8'))
        ids = d.keys() if isinstance(d, dict) else [x.get('id') for x in d]
        for uid in ids:
            if not uid or '_' not in uid:
                continue
            mat = uid.split('_')[0]
            if get_material('armor', mat) or get_material('weapons', mat):
                target = (uid, mat)
                break
        if target:
            break
    if not target:
        return        # no colliding unique in current data -> guard trivially holds
    uid, mat = target
    a = instantiate_armor('hide', 'hide')
    a.id = uid
    a.material = mat
    a.name = a.unidentified_name = 'UNIQUE_SENTINEL'
    _run([a])
    assert a.name == 'UNIQUE_SENTINEL', f'{uid} (mat {mat!r}) was wrongly recomposed'


def test_recompose_is_idempotent_on_fresh_items():
    w = instantiate_weapon('longsword', 'iron')
    armor = instantiate_armor('leather', 'leather')
    n1, n2, ac = w.name, armor.name, armor.ac_bonus
    _run([w, armor])
    assert (w.name, armor.name, armor.ac_bonus) == (n1, n2, ac)


def test_recompose_walks_equipment_and_ground():
    worn = instantiate_armor('hide', 'hide')
    worn.name = 'Hide Hide Armor'
    ground = instantiate_armor('hide', 'hide')
    ground.name = 'Hide Hide Armor'
    g = Game.__new__(Game)
    g.player = _P([])
    g.player.armor_slots = [worn]
    Game._migrate_recompose_composite_items(g, {'ground_items': [ground]})
    assert worn.name == 'Hide Armor'
    assert ground.name == 'Hide Armor'
