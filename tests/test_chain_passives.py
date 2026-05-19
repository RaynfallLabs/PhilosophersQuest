"""Tests for chain-equip passive flag lookup + wiring.

`src/chain_passives.py` reads `item._chain_passives` (written by
`chain_equip.apply_tier_bonuses`) and exposes those flags to game code.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
pygame.init()
pygame.font.init()


def _make_armor(**overrides):
    from items import Armor
    defn = {
        'id': 'test_armor', 'name': 'test armor', 'symbol': '[',
        'color': [200, 200, 200], 'ac_bonus': 3, 'slot': 'body',
    }
    defn.update(overrides)
    return Armor(defn)


def _make_accessory(**overrides):
    from items import Accessory
    defn = {
        'id': 'test_ring', 'name': 'test ring', 'symbol': '=',
        'color': [200, 200, 200], 'slot': 'ring',
        'effects': {'stat': 'STR', 'amount': 1},
    }
    defn.update(overrides)
    return Accessory(defn)


def _make_shield(**overrides):
    from items import Shield
    defn = {
        'id': 'test_shield', 'name': 'test shield', 'symbol': ']',
        'color': [200, 200, 200], 'ac_bonus': 2, 'slot': 'shield',
    }
    defn.update(overrides)
    return Shield(defn)


def _equip_armor(player, armor):
    """Stash a fully-built armor item into the player.body slot (idx 1)."""
    from items import ARMOR_SLOTS
    idx = ARMOR_SLOTS.index(armor.slot) if armor.slot in ARMOR_SLOTS else 0
    player.armor_slots[idx] = armor


def _equip_acc(player, acc, slot=0):
    player.accessory_slots[slot] = acc


def _new_player():
    from player import Player
    return Player()


# ---------------------------------------------------------------------------
# Framework: lookup helpers
# ---------------------------------------------------------------------------

def test_player_has_passive_default_false():
    from chain_passives import player_has_passive
    p = _new_player()
    assert player_has_passive(p, 'aura_of_awe') is False


def test_player_has_passive_after_apply():
    from chain_equip import apply_tier_bonuses
    from chain_passives import player_has_passive
    p = _new_player()
    a = _make_armor(equip_chain_mode='escalator',
                    tier_bonuses={'5': {'passive_aura_of_awe': True}})
    apply_tier_bonuses(p, a, 5)
    _equip_armor(p, a)
    assert player_has_passive(p, 'aura_of_awe') is True


def test_passive_value_returns_default_if_missing():
    from chain_passives import passive_value
    p = _new_player()
    assert passive_value(p, 'mp_bonus', 0) == 0


def test_passive_value_returns_set_value():
    from chain_equip import apply_tier_bonuses
    from chain_passives import passive_value
    p = _new_player()
    a = _make_armor(equip_chain_mode='escalator',
                    tier_bonuses={'5': {'passive_spell_damage_bonus': 0.25}})
    apply_tier_bonuses(p, a, 5)
    _equip_armor(p, a)
    assert passive_value(p, 'spell_damage_bonus', 0) == 0.25


def test_find_passive_item_returns_item():
    from chain_equip import apply_tier_bonuses
    from chain_passives import find_passive_item
    p = _new_player()
    a = _make_armor(equip_chain_mode='escalator',
                    tier_bonuses={'5': {'passive_huginn_muninn': True}})
    apply_tier_bonuses(p, a, 5)
    _equip_armor(p, a)
    assert find_passive_item(p, 'huginn_muninn') is a


def test_sum_passive_values_stacks():
    from chain_equip import apply_tier_bonuses
    from chain_passives import sum_passive_values
    p = _new_player()
    a1 = _make_armor(id='a1', equip_chain_mode='escalator',
                     tier_bonuses={'5': {'passive_attack_chain_cap_bonus': 1}})
    a2 = _make_accessory(id='r1', equip_chain_mode='escalator',
                         tier_bonuses={'5': {'passive_attack_chain_cap_bonus': 1}})
    apply_tier_bonuses(p, a1, 5)
    apply_tier_bonuses(p, a2, 5)
    _equip_armor(p, a1)
    _equip_acc(p, a2)
    assert sum_passive_values(p, 'attack_chain_cap_bonus') == 2


# ---------------------------------------------------------------------------
# Per-floor charge bookkeeping
# ---------------------------------------------------------------------------


def test_consume_passive_charge_returns_false_if_no_passive():
    from chain_passives import consume_passive_charge
    p = _new_player()
    assert consume_passive_charge(p, 'free_cast_once_per_floor') is False


def test_consume_passive_charge_once_then_used():
    from chain_equip import apply_tier_bonuses
    from chain_passives import consume_passive_charge, is_charge_available
    p = _new_player()
    a = _make_armor(equip_chain_mode='escalator',
                    tier_bonuses={'5': {'passive_free_cast_once_per_floor': True}})
    apply_tier_bonuses(p, a, 5)
    _equip_armor(p, a)
    assert is_charge_available(p, 'free_cast_once_per_floor')
    assert consume_passive_charge(p, 'free_cast_once_per_floor') is True
    assert consume_passive_charge(p, 'free_cast_once_per_floor') is False
    assert not is_charge_available(p, 'free_cast_once_per_floor')


def test_reset_per_floor_charges_refreshes():
    from chain_equip import apply_tier_bonuses
    from chain_passives import (
        consume_passive_charge, reset_per_floor_charges, is_charge_available,
    )
    p = _new_player()
    a = _make_armor(equip_chain_mode='escalator',
                    tier_bonuses={'5': {'passive_huginn_muninn': True}})
    apply_tier_bonuses(p, a, 5)
    _equip_armor(p, a)
    consume_passive_charge(p, 'huginn_muninn')
    assert not is_charge_available(p, 'huginn_muninn')
    reset_per_floor_charges(p)
    assert is_charge_available(p, 'huginn_muninn')


def test_consume_run_passive_once_per_run():
    from chain_equip import apply_tier_bonuses
    from chain_passives import consume_run_passive, is_run_spent
    p = _new_player()
    a = _make_armor(equip_chain_mode='escalator',
                    tier_bonuses={'5': {'passive_psychopomp_step': True}})
    apply_tier_bonuses(p, a, 5)
    _equip_armor(p, a)
    assert consume_run_passive(p, 'psychopomp_step') is True
    assert is_run_spent(p, 'psychopomp_step')
    assert consume_run_passive(p, 'psychopomp_step') is False


# ---------------------------------------------------------------------------
# Stat-like passive wiring
# ---------------------------------------------------------------------------


def test_mp_bonus_increases_max_mp():
    """Robe of the Magus: passive_mp_bonus directly adds to max_mp on equip."""
    from chain_equip import apply_tier_bonuses, revert_tier_bonuses
    p = _new_player()
    base = p.max_mp
    a = _make_armor(equip_chain_mode='escalator',
                    tier_bonuses={'5': {'passive_mp_bonus': 25}})
    apply_tier_bonuses(p, a, 5)
    assert p.max_mp == base + 25
    revert_tier_bonuses(p, a)
    assert p.max_mp == base


def test_max_mp_bonus_alias_works():
    """Necklace of Harmonia uses 'passive_max_mp_bonus' (named differently)."""
    from chain_equip import apply_tier_bonuses, revert_tier_bonuses
    p = _new_player()
    base = p.max_mp
    a = _make_accessory(equip_chain_mode='escalator',
                        tier_bonuses={'5': {'passive_max_mp_bonus': 2}})
    apply_tier_bonuses(p, a, 5)
    assert p.max_mp == base + 2
    revert_tier_bonuses(p, a)
    assert p.max_mp == base


def test_get_mp_bonus_aggregator():
    """chain_passives.get_mp_bonus sums both mp_bonus and max_mp_bonus."""
    from chain_equip import apply_tier_bonuses
    from chain_passives import get_mp_bonus
    p = _new_player()
    a = _make_armor(id='robe', equip_chain_mode='escalator',
                    tier_bonuses={'5': {'passive_mp_bonus': 20}})
    n = _make_accessory(id='neck', equip_chain_mode='escalator',
                        tier_bonuses={'5': {'passive_max_mp_bonus': 2}})
    apply_tier_bonuses(p, a, 5)
    apply_tier_bonuses(p, n, 5)
    _equip_armor(p, a)
    _equip_acc(p, n)
    assert get_mp_bonus(p) == 22


def test_attack_chain_cap_bonus_lookup():
    from chain_equip import apply_tier_bonuses
    from chain_passives import get_attack_chain_cap_bonus
    p = _new_player()
    r = _make_accessory(equip_chain_mode='escalator',
                        tier_bonuses={'5': {'passive_attack_chain_cap_bonus': 1}})
    apply_tier_bonuses(p, r, 5)
    _equip_acc(p, r)
    assert get_attack_chain_cap_bonus(p) == 1


def test_grammar_chain_cap_bonus_lookup():
    from chain_equip import apply_tier_bonuses
    from chain_passives import get_grammar_chain_cap_bonus
    p = _new_player()
    r = _make_accessory(equip_chain_mode='escalator',
                        tier_bonuses={'5': {'passive_grammar_chain_cap_bonus': 1}})
    apply_tier_bonuses(p, r, 5)
    _equip_acc(p, r)
    assert get_grammar_chain_cap_bonus(p) == 1


def test_spellbook_chain_bonus_lookup():
    from chain_equip import apply_tier_bonuses
    from chain_passives import get_spellbook_chain_bonus
    p = _new_player()
    r = _make_accessory(equip_chain_mode='escalator',
                        tier_bonuses={'5': {'passive_spellbook_chain_bonus': 1}})
    apply_tier_bonuses(p, r, 5)
    _equip_acc(p, r)
    assert get_spellbook_chain_bonus(p) == 1


def test_spell_damage_multiplier_default_1():
    from chain_passives import get_spell_damage_multiplier
    p = _new_player()
    assert get_spell_damage_multiplier(p) == 1.0


def test_spell_damage_multiplier_with_passive():
    from chain_equip import apply_tier_bonuses
    from chain_passives import get_spell_damage_multiplier
    p = _new_player()
    a = _make_accessory(equip_chain_mode='escalator',
                        tier_bonuses={'5': {'passive_spell_damage_bonus': 0.25}})
    apply_tier_bonuses(p, a, 5)
    _equip_acc(p, a)
    assert abs(get_spell_damage_multiplier(p) - 1.25) < 1e-6


def test_spell_crit_chance():
    from chain_equip import apply_tier_bonuses
    from chain_passives import get_spell_crit_chance
    p = _new_player()
    a = _make_armor(equip_chain_mode='escalator',
                    tier_bonuses={'5': {'passive_spell_crit': 10}})
    apply_tier_bonuses(p, a, 5)
    _equip_armor(p, a)
    assert abs(get_spell_crit_chance(p) - 0.10) < 1e-6


def test_death_save_bonus_lookup():
    from chain_equip import apply_tier_bonuses
    from chain_passives import get_death_save_bonus
    p = _new_player()
    a = _make_accessory(equip_chain_mode='escalator',
                        tier_bonuses={'5': {'passive_death_save_bonus': 1}})
    apply_tier_bonuses(p, a, 5)
    _equip_acc(p, a)
    assert get_death_save_bonus(p) == 1


def test_hunger_slow_factor_max_not_sum():
    """Two Idunn charms shouldn't stack into ridiculous values — max wins."""
    from chain_equip import apply_tier_bonuses
    from chain_passives import get_hunger_slow_factor
    p = _new_player()
    a1 = _make_accessory(id='a1', equip_chain_mode='escalator',
                         tier_bonuses={'5': {'passive_hunger_slow': 0.33}})
    a2 = _make_accessory(id='a2', equip_chain_mode='escalator',
                         tier_bonuses={'5': {'passive_hunger_slow': 0.66}})
    apply_tier_bonuses(p, a1, 5)
    apply_tier_bonuses(p, a2, 5)
    _equip_acc(p, a1, 0)
    _equip_acc(p, a2, 1)
    assert get_hunger_slow_factor(p) == 0.66


def test_back_attack_multiplier_default_1():
    from chain_passives import get_back_attack_multiplier
    p = _new_player()
    assert get_back_attack_multiplier(p) == 1.0


def test_back_attack_multiplier_with_passive():
    from chain_equip import apply_tier_bonuses
    from chain_passives import get_back_attack_multiplier
    p = _new_player()
    a = _make_armor(equip_chain_mode='escalator',
                    tier_bonuses={'5': {'passive_back_attack_weakness': 1.5}})
    apply_tier_bonuses(p, a, 5)
    _equip_armor(p, a)
    assert get_back_attack_multiplier(p) == 1.5


def test_reflect_spell_chance_lookup():
    from chain_equip import apply_tier_bonuses
    from chain_passives import get_reflect_spell_chance
    p = _new_player()
    s = _make_shield(equip_chain_mode='escalator',
                     tier_bonuses={'5': {'passive_reflect_spell': 20}})
    apply_tier_bonuses(p, s, 5)
    p.shield = s
    assert abs(get_reflect_spell_chance(p) - 0.20) < 1e-6


def test_pacify_demon_chance_lookup():
    from chain_equip import apply_tier_bonuses
    from chain_passives import get_pacify_demon_chance
    p = _new_player()
    r = _make_accessory(equip_chain_mode='escalator',
                        tier_bonuses={'5': {'passive_pacify_demon_chance': 0.2}})
    apply_tier_bonuses(p, r, 5)
    _equip_acc(p, r)
    assert get_pacify_demon_chance(p) == 0.2


# ---------------------------------------------------------------------------
# Helper coverage: roll_gorgoneion_petrify and roll_mirror_of_souls
# ---------------------------------------------------------------------------


def test_roll_gorgoneion_petrify_returns_false_without_passive():
    from chain_passives import roll_gorgoneion_petrify

    class FakeMon:
        def __init__(self):
            self.status_effects = {}
        def add_effect(self, n, d):
            self.status_effects[n] = d

    p = _new_player()
    m = FakeMon()
    assert roll_gorgoneion_petrify(p, m) is False


def test_roll_gorgoneion_petrify_consumes_floor_charge():
    """After first strike, used_flag flips True regardless of outcome."""
    from chain_equip import apply_tier_bonuses
    from chain_passives import roll_gorgoneion_petrify

    class FakeMon:
        def __init__(self):
            self.status_effects = {}
        def add_effect(self, n, d):
            self.status_effects[n] = d

    p = _new_player()
    s = _make_shield(equip_chain_mode='escalator',
                     tier_bonuses={'5': {'passive_gorgoneion_petrify_on_hit': True}})
    apply_tier_bonuses(p, s, 5)
    p.shield = s
    p._gorgoneion_used_this_floor = False
    m = FakeMon()
    # call twice — second call returns False because flag is now used
    roll_gorgoneion_petrify(p, m)
    assert p._gorgoneion_used_this_floor is True
    m2 = FakeMon()
    assert roll_gorgoneion_petrify(p, m2) is False


def test_roll_mirror_of_souls_no_passive_returns_zero():
    from chain_passives import roll_mirror_of_souls

    class FakeMon: pass
    p = _new_player()
    assert roll_mirror_of_souls(p, FakeMon(), 10) == 0


def test_roll_mirror_of_souls_deterministic_with_seed(monkeypatch):
    from chain_equip import apply_tier_bonuses
    from chain_passives import roll_mirror_of_souls
    import random as _r

    class FakeMon: pass
    p = _new_player()
    s = _make_shield(equip_chain_mode='escalator',
                     tier_bonuses={'5': {'passive_mirror_of_souls': True}})
    apply_tier_bonuses(p, s, 5)
    p.shield = s
    # Force a roll < 0.20 so the reflect fires.
    monkeypatch.setattr(_r, 'random', lambda: 0.05)
    assert roll_mirror_of_souls(p, FakeMon(), 10) == 10
    # And > 0.20 should fail.
    monkeypatch.setattr(_r, 'random', lambda: 0.99)
    assert roll_mirror_of_souls(p, FakeMon(), 10) == 0
