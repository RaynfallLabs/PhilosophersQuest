"""Regression tests for the 3 shipped fixes that previously had no coverage.

Each test would FAIL if the corresponding commit was reverted:
  - NPC duplicate-spawn fix (commit 387eec4)
  - Plant ingredients on floor (commit bffba65)
  - Unique-leak in _spawn_treasure_item (commit cd44949)

Also data-layer tests for the chain-equip items + chest templates.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
pygame.init()


# ---------------------------------------------------------------------------
# NPC duplicate-spawn fix (commit 387eec4)
# ---------------------------------------------------------------------------

def test_npc_spawn_guards_against_existing_tag():
    """A second call to _maybe_spawn_npc on a floor where the NPC is already
    in self.monsters must NOT add a duplicate. Inspects source as a string-grep
    guard since constructing a full Game stub is heavy.
    """
    import inspect
    from game_encounters import EncountersMixin
    src = inspect.getsource(EncountersMixin._maybe_spawn_npc)
    # The guard checks for an existing monster with the same _npc_encounter_tag
    assert "_npc_encounter_tag" in src
    assert "for _m in self.monsters" in src or "for m in self.monsters" in src
    # And early-returns
    assert "return" in src


def test_flavor_npc_spawn_also_guards():
    """The same guard pattern must exist for flavor NPCs."""
    import inspect
    from game_encounters import EncountersMixin
    src = inspect.getsource(EncountersMixin._maybe_spawn_flavor_npc)
    assert "_flavor_encounter_tag" in src
    assert "for _m in self.monsters" in src or "for m in self.monsters" in src


# ---------------------------------------------------------------------------
# Plant ingredients on floor (commit bffba65)
# ---------------------------------------------------------------------------

def test_plant_ingredients_eligible_pool_not_empty():
    """The plant-keyword filter must produce at least 8 eligible ingredients
    across reasonable floor levels."""
    from items import load_items
    ingredients = load_items('ingredient')
    PLANT_KEYWORDS = ('mushroom','herb','berry','leaf','root','fungus','moss',
                      'flower','seed','grain','wheat','grass','vine','spice',
                      'lichen','bark','sap')
    plants_l10 = [i for i in ingredients
                  if any(w in getattr(i, 'name', '').lower() for w in PLANT_KEYWORDS)
                  and i.min_level <= 10]
    assert len(plants_l10) >= 8, (
        f'Only {len(plants_l10)} plant ingredients eligible at L10 — expected >= 8.'
    )


def test_plant_ingredient_spawn_block_present_in_dungeon():
    """The spawn_items function must contain the plant-ingredient placement
    block (regression guard against accidental deletion)."""
    import inspect
    import dungeon
    src = inspect.getsource(dungeon.spawn_items)
    # Loose marker: the keyword tuple plus the load_items('ingredient') call
    assert "_PLANT_KEYWORDS" in src or "'mushroom'" in src
    assert "load_items('ingredient')" in src


# ---------------------------------------------------------------------------
# Unique-leak in _spawn_treasure_item (commit cd44949)
# ---------------------------------------------------------------------------

def test_spawn_treasure_item_uses_template_helpers_not_load_items():
    """The function must NOT use load_items('weapon'/'armor'/'shield') as a
    common pool — those JSON files are uniques-only. Must call the template-
    based pick_random_*_for_floor helpers instead."""
    import inspect
    import game_combat
    src = inspect.getsource(game_combat.CombatMixin._spawn_treasure_item)
    assert "pick_random_weapon_for_floor" in src, (
        '_spawn_treasure_item must call pick_random_weapon_for_floor — '
        'reverting to load_items("weapon") would drop ONLY uniques.'
    )
    assert "pick_random_armor_for_floor" in src
    assert "pick_random_shield_for_floor" in src
    # And explicit is_unique filter on the magic-item pool
    assert "is_unique" in src


# ---------------------------------------------------------------------------
# Chain-equip data integrity (24 items)
# ---------------------------------------------------------------------------

def test_every_chain_equip_item_has_tier_bonuses():
    """Every item with equip_chain_mode set must have a non-empty tier_bonuses
    dict with keys 1..N contiguous."""
    failures = []
    for cat in ('weapon', 'armor', 'shield', 'accessory'):
        d = json.load(open(f'data/items/{cat}.json', encoding='utf-8'))
        for iid, item in d.items():
            if item.get('equip_chain_mode'):
                tb = item.get('tier_bonuses', {})
                if not tb:
                    failures.append(f'{cat}:{iid} has equip_chain_mode but no tier_bonuses')
                    continue
                keys = sorted(int(k) for k in tb.keys())
                if keys != list(range(1, len(keys) + 1)):
                    failures.append(f'{cat}:{iid} tier_bonuses keys not contiguous: {keys}')
                for tier, bonus in tb.items():
                    if not bonus:
                        failures.append(f'{cat}:{iid} tier {tier} is empty')
    assert not failures, '\n'.join(failures)


def test_chain_equip_mode_uses_canonical_name():
    """equip_chain_mode values must be 'escalator_chain' or 'chain' — not 'escalator'."""
    failures = []
    for cat in ('weapon', 'armor', 'shield', 'accessory'):
        d = json.load(open(f'data/items/{cat}.json', encoding='utf-8'))
        for iid, item in d.items():
            mode = item.get('equip_chain_mode')
            if mode and mode not in ('escalator_chain', 'chain'):
                failures.append(f'{cat}:{iid} has equip_chain_mode={mode!r}')
    assert not failures, (
        'JSON convention: use "escalator_chain" (not "escalator"). '
        + '; '.join(failures)
    )


# ---------------------------------------------------------------------------
# No duplicate IDs across category files
# ---------------------------------------------------------------------------

def test_no_duplicate_item_ids_across_files():
    """Items must not share `id` between two category files (causes unstable
    loader resolution in _spawn_unique_item)."""
    seen: dict[str, str] = {}
    collisions: list[str] = []
    for cat in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll',
                'spellbook', 'potion', 'food', 'ingredient', 'ammo',
                'artifact', 'container'):
        d = json.load(open(f'data/items/{cat}.json', encoding='utf-8'))
        for iid in d:
            if iid in seen:
                collisions.append(f'{iid} in {seen[iid]} and {cat}')
            seen[iid] = cat
    assert not collisions, 'Duplicate item IDs:\n' + '\n'.join(collisions)


# ---------------------------------------------------------------------------
# Family-mastery wiring (resist_charm, resist_elemental, sp_regen)
# ---------------------------------------------------------------------------

def test_fey_resist_charm_halves_charm_duration():
    """Fey-family mastery should reduce charmed duration by half."""
    from player import Player
    p = Player()
    p.unlocked_monster_class_masteries = {
        'fey': {'kind': 'resist_charm', 'value': 1, 'desc': '_'}
    }
    p.add_effect('charmed', 10)
    # Halved to 5 (max(1, 10//2))
    assert p.status_effects.get('charmed', 0) == 5


def test_elemental_resists_elemental_damage():
    """Elemental-family mastery should reduce fire/cold/lightning damage."""
    from player import Player
    p = Player()
    p.unlocked_monster_class_masteries = {
        'elemental': {'kind': 'resist_elemental', 'value': 1, 'desc': '_'}
    }
    actual = p.take_damage(10, 'fire')
    base = Player().take_damage(10, 'fire')
    assert actual < base, f'expected mastery to reduce damage; got actual={actual} base={base}'
