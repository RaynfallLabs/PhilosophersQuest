"""BUC + binary-potion-mastery effects (2026-06-07).

User found dead text: blessed accessories/wands "did nothing", and the
"20% more potent" potion mastery did nothing for binary potions like
teleportation (there is no magnitude to scale). Cursed had the mirror gap:
cursed gear was sticky (welded on) but carried no stat penalty.

Fixes, all symmetric blessed<->cursed:
  * get_ac: blessed +1 / cursed -1 AC per worn armor, shield AND accessory.
  * wands:  blessed +1 / cursed -1 max charge (floor 1).
  * binary potions (teleport/cures/gain-level): mastery/blessed grant a
    PRESERVE chance (dose not used up); cursed grants a FIZZLE chance (magic
    fails outright). Default mastery for those classes is 'potion_preserve'.
  * full_heal: blessed/mastered also scours away debuffs.
"""
import pytest

from items import Armor, Accessory, Wand, Potion
from player import Player
from class_masteries import default_blessing_for_class
from food_system import drink_potion
from status_effects import DEBUFFS

_BASE = {'symbol': '!', 'color': [200, 50, 50]}


def _armor(buc):
    return Armor({**_BASE, 'id': 't_armor', 'name': 'Test Plate', 'slot': 'body',
                  'ac_bonus': 3, 'buc': buc})


def _acc(buc):
    return Accessory({**_BASE, 'id': 't_ring', 'name': 'Test Ring', 'slot': 'ring', 'buc': buc})


def _wand(buc):
    return Wand({**_BASE, 'id': 'wand_t', 'name': 'Test Wand',
                 'charges_min': 3, 'charges_max': 3, 'max_charges': 3, 'buc': buc})


def _potion(effect, buc='uncursed'):
    return Potion({**_BASE, 'id': f'potion_{effect}', 'name': 'Test Potion',
                   'effect': effect, 'buc': buc})


# --- AC: armor + shield + accessory, blessed lowers / cursed raises ---------

def test_blessed_armor_lowers_ac_cursed_raises():
    pl = Player()
    pl.armor_slots[0] = _armor('uncursed'); ac_u = pl.get_ac()
    pl.armor_slots[0] = _armor('blessed');  ac_b = pl.get_ac()
    pl.armor_slots[0] = _armor('cursed');   ac_c = pl.get_ac()
    assert ac_b == ac_u - 1        # lower AC is better
    assert ac_c == ac_u + 1        # cursed armor is now a real penalty


def test_blessed_accessory_does_something_cursed_too():
    # The exact complaint: a blessed accessory used to do nothing.
    pl = Player()
    pl.accessory_slots[0] = _acc('uncursed'); ac_u = pl.get_ac()
    pl.accessory_slots[0] = _acc('blessed');  ac_b = pl.get_ac()
    pl.accessory_slots[0] = _acc('cursed');   ac_c = pl.get_ac()
    assert ac_b == ac_u - 1
    assert ac_c == ac_u + 1


# --- Wands: blessed +1 / cursed -1 charge -----------------------------------

def test_wand_buc_shifts_charges():
    assert _wand('uncursed').max_charges == 3
    assert _wand('blessed').max_charges == 4
    assert _wand('cursed').max_charges == 2
    # The roll bounds shift too, so the placement re-roll respects BUC.
    b = _wand('blessed')
    assert b.charges == 4 and b.charges_min == 4 and b.charges_max == 4
    c = _wand('cursed')
    assert c.charges == 2 and c.charges_min == 2 and c.charges_max == 2


def test_cursed_wand_charges_never_below_one():
    w = Wand({**_BASE, 'id': 'wand_min', 'name': 'Spent Wand',
              'charges_min': 1, 'charges_max': 1, 'max_charges': 1, 'buc': 'cursed'})
    assert w.max_charges == 1 and w.charges == 1   # floor, not 0/-?


# --- Potion mastery is effect-aware -----------------------------------------

def test_binary_potion_mastery_is_preserve_not_dead_potency():
    for eff in ('teleport', 'cure_poison', 'cure_disease', 'cure_all',
                'restore_str', 'gain_level'):
        m = default_blessing_for_class(f'potion_{eff}', _potion(eff))
        assert m['kind'] == 'potion_preserve', eff


def test_quantitative_potion_mastery_stays_potency():
    for eff in ('heal', 'extra_heal', 'restore_sp'):
        m = default_blessing_for_class(f'potion_{eff}', _potion(eff))
        assert m['kind'] == 'potion_potency_bonus', eff


# --- full_heal cleanse ------------------------------------------------------

def test_blessed_full_heal_cleanses_debuffs():
    pl = Player()
    # Use a CONCRETE non-heal-blocking debuff. DEBUFFS is a frozenset, so
    # next(iter(...)) varied by PYTHONHASHSEED and could pick 'heal_blocked',
    # which makes restore_hp a no-op -> the "fully healed" assert flaked.
    deb = 'confused'
    assert deb in DEBUFFS and deb != 'heal_blocked'
    pl.status_effects[deb] = 5
    pl.hp = 1
    drink_potion(pl, _potion('full_heal', 'blessed'))
    assert deb not in pl.status_effects   # cleansed
    assert pl.hp == pl.max_hp             # and fully healed


def test_uncursed_full_heal_leaves_debuffs():
    pl = Player()
    deb = 'weakened'                          # concrete, deterministic
    assert deb in DEBUFFS
    pl.status_effects[deb] = 5
    pl.hp = 1
    drink_potion(pl, _potion('full_heal', 'uncursed'))
    assert pl.status_effects.get(deb) == 5   # no free cleanse without bless/mastery


def test_blessed_full_heal_overcomes_heal_block():
    # heal_blocked makes restore_hp a no-op, so the cleanse MUST run before the
    # heal. A blessed full-heal should cure heal_blocked AND restore to full.
    pl = Player()
    assert 'heal_blocked' in DEBUFFS
    pl.status_effects['heal_blocked'] = 5
    pl.hp = 1
    drink_potion(pl, _potion('full_heal', 'blessed'))
    assert 'heal_blocked' not in pl.status_effects   # cleansed first...
    assert pl.hp == pl.max_hp                         # ...so the heal lands


# --- Binary preserve / fizzle wiring (force the dice) -----------------------

def test_mastered_teleport_can_preserve(monkeypatch):
    import dice
    monkeypatch.setattr(dice, 'roll', lambda *a, **k: 1)   # every roll = 1
    pl = Player()
    pot = _potion('teleport', 'uncursed')
    pl.unlocked_class_masteries[pot.id] = {'kind': 'potion_preserve', 'value': 0.25}
    msgs = drink_potion(pl, pot)
    assert '_teleport' in msgs       # the effect still fired
    assert '_preserve' in msgs       # ...and the dose lingered (caller re-adds it)


def test_cursed_teleport_can_fizzle(monkeypatch):
    import dice
    monkeypatch.setattr(dice, 'roll', lambda *a, **k: 1)   # 1d4 == 1 -> fizzle
    pl = Player()
    msgs = drink_potion(pl, _potion('teleport', 'cursed'))
    assert '_teleport' not in msgs   # magic failed outright
    assert any('curdles' in m for m in msgs)


def test_uncursed_teleport_is_plain():
    pl = Player()
    msgs = drink_potion(pl, _potion('teleport', 'uncursed'))
    assert '_teleport' in msgs
    assert '_preserve' not in msgs   # no mastery, not blessed -> consumed normally


# --- Preserve re-add must not duplicate a stack (the quaff-caller contract) ---
# remove_from_inventory only DECREMENTS a stack (object stays held), so the
# caller bumps count back; a singleton is removed, so the caller re-adds it.
# Calling add_to_inventory on a still-held stack would alias it twice.

def test_preserve_stack_bumps_count_no_alias():
    pl = Player()
    pot = _potion('teleport'); pot.count = 3
    pl.add_to_inventory(pot)
    pl.remove_from_inventory(pot)                 # quaff one -> count 2, still held
    if pot in pl.inventory:                       # mirror game_menus preserve logic
        pot.count = getattr(pot, 'count', 1) + 1
    else:
        pl.add_to_inventory(pot)
    held = [i for i in pl.inventory if i.id == pot.id]
    assert len(held) == 1            # NOT aliased twice in the list
    assert held[0].count == 3        # consume undone


def test_preserve_singleton_is_readded():
    pl = Player()
    pot = _potion('teleport'); pot.count = 1
    pl.add_to_inventory(pot)
    pl.remove_from_inventory(pot)                 # singleton removed
    assert pot not in pl.inventory
    if pot in pl.inventory:
        pot.count = getattr(pot, 'count', 1) + 1
    else:
        pl.add_to_inventory(pot)
    held = [i for i in pl.inventory if i.id == pot.id]
    assert len(held) == 1 and held[0].count == 1
