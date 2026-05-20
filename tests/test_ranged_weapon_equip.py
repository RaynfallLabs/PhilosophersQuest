"""Regression: every ranged weapon class equips to the ranged_weapon slot.

Established 2026-05-20 after a generated longbow was discovered to equip to
the melee `weapon` slot during playtest. Root cause: bow/crossbow templates
under `data/templates/weapons/` were missing `requires_ammo`, and the equip
router at player.py:_apply_equip routes by `requires_ammo is not None`.
Also `atalanta_bow` unique had requiresAmmo explicitly null.

These tests fail loudly if anyone re-introduces the bug by editing a bow
template or a unique bow without the right ammo field.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

REPO = os.path.join(os.path.dirname(__file__), '..')
TEMPLATES_DIR = os.path.join(REPO, 'data', 'templates', 'weapons')
UNIQUES_FILE = os.path.join(REPO, 'data', 'items', 'weapon.json')

# Templates that must declare ammo type
RANGED_TEMPLATES = {
    'shortbow':       'arrow',
    'longbow':        'arrow',
    'composite_bow':  'arrow',
    'light_crossbow': 'bolt',
    'heavy_crossbow': 'bolt',
    'sling':          'stone',
}

# Templates whose ammo is unlimited (no inventory item needed)
INFINITE_AMMO_TEMPLATES = {'sling'}


def test_ranged_templates_declare_ammo():
    for tpl, expected in RANGED_TEMPLATES.items():
        with open(os.path.join(TEMPLATES_DIR, f'{tpl}.json'), encoding='utf-8') as f:
            data = json.load(f)
        assert data.get('requires_ammo') == expected, (
            f"template {tpl!r} must declare requires_ammo={expected!r} "
            f"(got {data.get('requires_ammo')!r}). Without this, generated "
            f"common bows/crossbows equip to the melee slot — see playtest "
            f"bug 2026-05-20."
        )


def test_unique_bows_declare_ammo():
    """Unique items in weapon.json with weapon_class 'bow'/'crossbow' must
    declare requiresAmmo (camelCase per the uniques file convention)."""
    with open(UNIQUES_FILE, encoding='utf-8') as f:
        uniques = json.load(f)
    ranged_classes = {'bow', 'crossbow'}
    failures = []
    for uid, u in uniques.items():
        wcls = u.get('weapon_class', u.get('class', ''))
        if wcls in ranged_classes:
            ammo = u.get('requiresAmmo') or u.get('requires_ammo')
            if not ammo:
                failures.append((uid, wcls, u.get('requiresAmmo')))
    assert not failures, (
        f"{len(failures)} unique ranged weapons missing requiresAmmo. "
        f"First 5: {failures[:5]}. Set 'requiresAmmo' to 'arrow'/'bolt' "
        f"so they equip to the ranged slot, not the melee slot."
    )


def test_generated_bow_routes_to_ranged_slot():
    """End-to-end: factory a longbow, instantiate Player, equip it, confirm
    it landed in self.ranged_weapon and NOT self.weapon."""
    from player import Player
    from items import instantiate_weapon

    # Build an oak longbow directly via the same factory the dungeon uses
    w = instantiate_weapon('longbow', 'oak')
    assert w.requires_ammo == 'arrow', (
        f"longbow factory produced requires_ammo={w.requires_ammo!r}, "
        f"expected 'arrow'"
    )

    p = Player()
    p._apply_equip(w)
    assert p.ranged_weapon is w, (
        f"longbow should equip to ranged_weapon slot. "
        f"weapon={p.weapon!r}, ranged_weapon={p.ranged_weapon!r}"
    )
    assert p.weapon is not w, "longbow should NOT equip to the melee weapon slot"


def test_sling_is_ranged_with_infinite_ammo():
    """Sling: stones are 'free' (in-fiction always available), so the engine
    treats sling as ranged with infinite_ammo=True. Generated slings must
    declare both fields so they route to ranged slot AND can fire without
    inventory ammo."""
    from items import instantiate_weapon
    w = instantiate_weapon('sling', 'leather_strap') if False else None
    # Try compatible materials from sling template
    for mat in ('leather', 'rare_wood', 'exotic_organic', 'oak'):
        try:
            w = instantiate_weapon('sling', mat)
            break
        except ValueError:
            continue
    assert w is not None, "could not factory a sling — no compatible material"
    assert w.requires_ammo == 'stone', \
        f"sling requires_ammo must be 'stone', got {w.requires_ammo!r}"
    assert w.infinite_ammo is True, \
        f"sling must have infinite_ammo=True (stones are free); got {w.infinite_ammo!r}"


def test_ranged_templates_have_meaningful_reach():
    """Established 2026-05-20: every ranged template must declare reach > 1.
    Default reach=1 makes a bow no better than a sword. The unique reach is
    each weapon's identity — sling 4 (short), shortbow 6, composite_bow 7,
    light_crossbow 7, heavy_crossbow 9, longbow 10.
    """
    expected_min = {
        'sling':          4,
        'shortbow':       6,
        'composite_bow':  7,
        'light_crossbow': 7,
        'heavy_crossbow': 9,
        'longbow':       10,
    }
    failures = []
    for tpl, minimum in expected_min.items():
        with open(os.path.join(TEMPLATES_DIR, f'{tpl}.json'), encoding='utf-8') as f:
            d = json.load(f)
        actual = d.get('reach', 1)
        if actual < minimum:
            failures.append((tpl, actual, minimum))
    assert not failures, (
        f'Ranged templates with reach below floor: {failures}. '
        f'A bow with reach 1 is just a melee weapon.'
    )


def test_atalanta_bow_has_proper_reach():
    """Atalanta's bow is peak_floor 30 — a reach=1 bug made it useless.
    Must be at least 8 (matches longbow basis)."""
    with open(UNIQUES_FILE, encoding='utf-8') as f:
        uniques = json.load(f)
    reach = uniques['atalanta_bow'].get('reach', 1)
    assert reach >= 8, (
        f'atalanta_bow has reach={reach}, must be >= 8 (longbow basis). '
        f'A peak_floor=30 bow with reach=1 is meaningless.'
    )


def test_archer_monsters_drop_ammo():
    """All 8 designated archer monsters must declare treasure.ammo_drop so
    players can sustain a ranged build by harvesting kills."""
    import os
    mpath = os.path.join(REPO, 'data', 'monsters.json')
    with open(mpath, encoding='utf-8') as f:
        monsters = json.load(f)
    archers = ['skeletal_archer', 'bone_archer', 'bandit_archer',
               'gnoll_archer', 'orc_archer', 'goblin_sniper',
               'drow_warrior', 'shadow_archer']
    failures = []
    for a in archers:
        drop = monsters[a].get('treasure', {}).get('ammo_drop')
        if not drop:
            failures.append(a)
            continue
        for required in ('ammo_id', 'count_range', 'chance'):
            if required not in drop:
                failures.append((a, 'missing field', required))
    assert not failures, (
        f'Archers without ammo_drop block: {failures}. '
        f'Without this, ranged builds run dry by floor 3-4.'
    )


def test_drop_treasure_honors_ammo_drop():
    """End-to-end: kill a bandit_archer, confirm an iron_arrow stack lands
    on the ground. With chance 0.65 we seed RNG so the drop is deterministic."""
    import random
    from unittest.mock import MagicMock
    from game_combat import CombatMixin

    # Build a minimal Game stub. _drop_treasure only touches ground_items,
    # add_message, and the spawn helpers — we stub the rest.
    g = MagicMock(spec=CombatMixin)
    g.ground_items = []
    g.add_message = MagicMock()
    # Re-bind unbound methods so they execute against our stub
    g._drop_treasure = CombatMixin._drop_treasure.__get__(g, CombatMixin)
    g._spawn_archer_ammo = CombatMixin._spawn_archer_ammo.__get__(g, CombatMixin)

    monster = MagicMock()
    monster.x, monster.y = 5, 5
    monster.name = 'bandit archer'
    monster.treasure = {
        'gold': [0, 0],
        'item_chance': 0.0,
        'ammo_drop': {
            'ammo_id': 'iron_arrow',
            'count_range': [5, 5],
            'chance': 1.0,  # force drop for determinism
        }
    }

    random.seed(42)
    g._drop_treasure(monster)
    # Confirm one item landed on the ground with the right id + count
    assert len(g.ground_items) == 1, f'expected 1 dropped ammo stack, got {len(g.ground_items)}'
    dropped = g.ground_items[0]
    assert dropped.id == 'iron_arrow'
    assert dropped.count == 5
    assert (dropped.x, dropped.y) == (5, 5)


def test_can_ranged_attack_skips_ammo_check_for_infinite_ammo():
    """combat.can_ranged_attack must respect infinite_ammo. A sling with
    no stones in inventory must still be able to fire — the in-game story
    is that stones are everywhere on a dungeon floor."""
    from items import instantiate_weapon
    from combat import can_ranged_attack
    from player import Player

    # Get a sling
    for mat in ('leather', 'rare_wood', 'exotic_organic', 'oak'):
        try:
            w = instantiate_weapon('sling', mat)
            break
        except ValueError:
            continue

    p = Player()
    p.PER = 14  # extend reach slightly
    p._apply_equip(w)
    assert p.ranged_weapon is w

    # Stub a target within reach. Sling has reach=1 from template default,
    # PER 14 adds (14-10)//3 = 1 -> total reach 2. Place target at distance 2.
    class StubMonster:
        x, y = 2, 0
        alive = True
    class StubDungeon:
        def is_walkable(self, x, y): return True
        width = 20
        height = 20
        tiles = [[1] * 20 for _ in range(20)]

    p.x, p.y = 0, 0
    # Empty inventory — no stones at all
    assert p.inventory == []
    # Should still succeed because sling has infinite_ammo
    ok = can_ranged_attack(p, StubMonster(), StubDungeon())
    assert ok, "sling with infinite_ammo must fire without inventory stones"
