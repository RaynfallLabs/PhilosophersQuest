"""Chain-equip passive flag lookup + wiring helpers.

`chain_equip.apply_tier_bonuses` writes any `passive_*` key into
`item._chain_passives` dict on the item. This module owns:

  - lookup helpers (player_has_passive / passive_value / find_passive_item)
  - per-floor charge tracking + the consume_passive_charge helper
  - small hook functions for the named passives (apply_aura_of_awe, etc.)
  - utility scanners (sum_passive_values for stacking stat-like passives)

Use-sites query these helpers at the natural hook moment (combat take_damage,
spell cast, FOV calc, scroll read fail, etc.).
"""

from __future__ import annotations

import random


def equipped_chain_items(player):
    """Iterate every equipped chain-equip item: armor + shield + accessories."""
    for slot in getattr(player, 'armor_slots', ()) or ():
        if slot is not None:
            yield slot
    sh = getattr(player, 'shield', None)
    if sh is not None:
        yield sh
    am = getattr(player, 'amulet_slot', None)
    if am is not None:
        yield am
    for acc in getattr(player, 'accessory_slots', ()) or ():
        if acc is not None:
            yield acc


def player_has_passive(player, flag: str) -> bool:
    """True if any equipped chain-equip item exposes ``flag`` via _chain_passives."""
    if player is None:
        return False
    for it in equipped_chain_items(player):
        passives = getattr(it, '_chain_passives', None)
        if passives and flag in passives:
            return True
    return False


def passive_value(player, flag: str, default=None):
    """Return the first matching value for ``flag`` from any equipped item.

    Pass a numeric default (e.g. 0) for stat-like passives so call-sites can do
    arithmetic without None checks. For boolean flags, default=None still works
    because callers usually use player_has_passive instead.
    """
    if player is None:
        return default
    for it in equipped_chain_items(player):
        passives = getattr(it, '_chain_passives', None)
        if passives and flag in passives:
            return passives[flag]
    return default


def sum_passive_values(player, flag: str) -> float:
    """Sum the numeric value of ``flag`` across all equipped items.

    Used for stat-like layers where two pieces could in theory stack
    (e.g. mp_bonus from two cloaks — JSON currently has one of each but
    the math is robust either way). Treats True/False as +0; treats
    numeric strings as their value.
    """
    if player is None:
        return 0
    total = 0.0
    for it in equipped_chain_items(player):
        passives = getattr(it, '_chain_passives', None)
        if not passives or flag not in passives:
            continue
        v = passives[flag]
        if isinstance(v, bool):
            continue
        try:
            total += float(v)
        except (TypeError, ValueError):
            continue
    return total


def find_passive_item(player, flag: str):
    """Return the item carrying ``flag``, or None.

    Useful for once-per-floor flags so the caller can track usage on the item.
    """
    if player is None:
        return None
    for it in equipped_chain_items(player):
        passives = getattr(it, '_chain_passives', None)
        if passives and flag in passives:
            return it
    return None


# ---------------------------------------------------------------------------
# Per-floor charge bookkeeping
# ---------------------------------------------------------------------------
#
# player._chain_passive_charges: dict[str, bool] -- per-floor "did we already
#   use this passive's charge?" map. Reset on every floor change.
# player._chain_passive_once_per_run: set[str] -- run-permanent "spent" flags
#   (psychopomp_step, reassembly, second_beheading_returns, etc.).


def _ensure_charge_dict(player) -> dict:
    if not hasattr(player, '_chain_passive_charges') or \
            player._chain_passive_charges is None:
        player._chain_passive_charges = {}
    return player._chain_passive_charges


def _ensure_run_set(player) -> set:
    if not hasattr(player, '_chain_passive_once_per_run') or \
            player._chain_passive_once_per_run is None:
        player._chain_passive_once_per_run = set()
    return player._chain_passive_once_per_run


def reset_per_floor_charges(player) -> None:
    """Wipe all per-floor charge flags. Called on _change_level."""
    player._chain_passive_charges = {}


def is_charge_available(player, flag: str) -> bool:
    """Per-floor charge still available?

    Returns True only if (a) the player has the passive equipped AND
    (b) the per-floor "used" flag is not set.
    """
    if not player_has_passive(player, flag):
        return False
    charges = _ensure_charge_dict(player)
    return not charges.get(flag, False)


def consume_passive_charge(player, flag: str) -> bool:
    """For per-floor-charge passives: returns True if charge available + mark consumed.

    Idiom at call-site::

        if consume_passive_charge(player, 'free_cast_once_per_floor'):
            mp_cost = 0
    """
    if not is_charge_available(player, flag):
        return False
    charges = _ensure_charge_dict(player)
    charges[flag] = True
    return True


def is_run_spent(player, flag: str) -> bool:
    """Run-permanent "spent" flag set?"""
    return flag in _ensure_run_set(player)


def consume_run_passive(player, flag: str) -> bool:
    """Per-run one-shot: returns True if not yet spent + mark spent.

    Only returns True if the passive is equipped *and* not yet consumed.
    """
    if not player_has_passive(player, flag):
        return False
    spent = _ensure_run_set(player)
    if flag in spent:
        return False
    spent.add(flag)
    return True


# ---------------------------------------------------------------------------
# Higher-level helpers used directly at hook sites
# ---------------------------------------------------------------------------


def get_mp_bonus(player) -> int:
    """Total extra max_mp from chain-equip passives (mp_bonus + max_mp_bonus)."""
    return int(sum_passive_values(player, 'mp_bonus') +
               sum_passive_values(player, 'max_mp_bonus'))


def get_attack_chain_cap_bonus(player) -> int:
    return int(sum_passive_values(player, 'attack_chain_cap_bonus'))


def get_grammar_chain_cap_bonus(player) -> int:
    return int(sum_passive_values(player, 'grammar_chain_cap_bonus'))


def get_spellbook_chain_bonus(player) -> int:
    return int(sum_passive_values(player, 'spellbook_chain_bonus'))


def get_spell_damage_multiplier(player) -> float:
    """Multiplier on outgoing spell damage. 0.0 (passive missing) -> 1.0 caller."""
    return 1.0 + float(sum_passive_values(player, 'spell_damage_bonus'))


def get_spell_crit_chance(player) -> float:
    """% chance for a spell to crit (0..1). Stacks additively if two items have it."""
    return float(sum_passive_values(player, 'spell_crit')) / 100.0


def get_death_save_bonus(player) -> int:
    return int(sum_passive_values(player, 'death_save_bonus'))


def get_hunger_slow_factor(player) -> float:
    """Largest hunger-slow value (multiplier of extra ticks). Acts as max() not sum.

    JSON values are 0.33, 0.5, 0.66 — these represent the FRACTION of
    extra-time per drain interval. Multiple Idunn-charm tiers shouldn't
    stack into >1.0 (which would make sp drain stop entirely), so we
    take the largest value rather than summing.
    """
    if player is None:
        return 0.0
    best = 0.0
    for it in equipped_chain_items(player):
        passives = getattr(it, '_chain_passives', None)
        if not passives or 'hunger_slow' not in passives:
            continue
        v = passives['hunger_slow']
        try:
            best = max(best, float(v))
        except (TypeError, ValueError):
            continue
    return best


def get_back_attack_multiplier(player) -> float:
    """Damage-from-behind multiplier (1.0 = normal). Max wins to avoid stacking."""
    if player is None:
        return 1.0
    best = 1.0
    for it in equipped_chain_items(player):
        passives = getattr(it, '_chain_passives', None)
        if not passives or 'back_attack_weakness' not in passives:
            continue
        v = passives['back_attack_weakness']
        try:
            best = max(best, float(v))
        except (TypeError, ValueError):
            continue
    return best


def get_reflect_spell_chance(player) -> float:
    """0..1 chance to reflect an incoming spell. Stacks additively."""
    a = float(sum_passive_values(player, 'reflect_spell'))
    b = float(sum_passive_values(player, 'spell_reflect'))
    return min(1.0, (a + b) / 100.0)


def get_pacify_demon_chance(player) -> float:
    """0..1 chance to pacify a visible demon on sight. Max wins."""
    if player is None:
        return 0.0
    best = 0.0
    for it in equipped_chain_items(player):
        passives = getattr(it, '_chain_passives', None)
        if not passives or 'pacify_demon_chance' not in passives:
            continue
        v = passives['pacify_demon_chance']
        try:
            best = max(best, float(v))
        except (TypeError, ValueError):
            continue
    return best


# ---------------------------------------------------------------------------
# Named-ability roll helpers (small wrappers around rolls + state mutations)
# ---------------------------------------------------------------------------


def apply_spell_damage_passives(player, dmg: float):
    """Layer chain-equip passives onto a base spell damage value.

    Returns (dmg, crit_fired, anti_being_fired). Callers can use the booleans
    for messaging.
    """
    crit = False
    anti = False
    dmg = float(dmg) * get_spell_damage_multiplier(player)
    crit_chance = get_spell_crit_chance(player)
    if crit_chance > 0 and random.random() < crit_chance:
        dmg *= 2.0
        crit = True
    if getattr(player, '_anti_being_charged', False):
        dmg *= 2.0
        player._anti_being_charged = False
        anti = True
    return dmg, crit, anti


def roll_gorgoneion_petrify(player, attacker, *, used_flag_attr='_gorgoneion_used_this_floor'):
    """Greater Aegis: first melee striker each floor saves vs petrification.

    Returns True if the petrify was applied (caller renders message).
    Mutates ``attacker.add_effect`` with a paralyzed status as a stand-in
    for petrification (monster.py status_effects already supports it).
    """
    if not player_has_passive(player, 'gorgoneion_petrify_on_hit'):
        return False
    if getattr(player, used_flag_attr, False):
        return False
    # First strike of the floor: save vs petrify. Use a 50% base chance.
    setattr(player, used_flag_attr, True)
    if random.random() < 0.50:
        if hasattr(attacker, 'add_effect'):
            attacker.add_effect('paralyzed', 4)
        return True
    return False


def roll_mirror_of_souls(player, attacker, dmg: int):
    """Smoking Mirror: 20% chance the attacker takes their own damage.

    Returns the damage to deal back to attacker (0 if no reflect).
    """
    if not player_has_passive(player, 'mirror_of_souls'):
        return 0
    if random.random() < 0.20:
        return max(1, int(dmg))
    return 0
