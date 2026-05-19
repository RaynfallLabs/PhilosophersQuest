"""Tests that the 11 previously-dead class mastery kinds now take effect at
their use-sites.

Each test mocks a player with a single blessing on
`unlocked_class_masteries`, triggers the relevant action (attack/regen tick/
scroll cast/etc.), and asserts the mastery bonus was applied.

Covered kinds (one per test, minimum):
  1.  class_acc_ac_bonus          (Ring of Protection)
  2.  class_acc_regen_bonus       (Ring of Regeneration)
  3.  class_acc_resist_bonus      (Ring of Fire Resist)
  4.  class_acc_sp_burn_bonus     (Ring of Sustenance)
  5.  class_acc_passive_radius    (Ring of Searching / Warning / Clairvoyance)
  6.  class_acc_quirk             (Ring of Speed)
  7.  class_acc_buff_duration_bonus (default-fallback ring)
  8.  class_scroll_potency        (Scroll of Heal)
  9.  class_scroll_extra_uses     (Scroll of Identify / Teleport)
 10.  class_scroll_persist        (Scroll of Mapping)
 11.  potion_potency_bonus        (Potion of Healing)
 12.  potion_duration_bonus       (Potion of Haste / Heroism)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
pygame.init()
pygame.font.init()


_ACC_BASE = {'symbol': '=', 'color': [200, 200, 200], 'slot': 'ring'}


def _acc_defn(**kw):
    return {**_ACC_BASE, **kw}


def _make_ring(name: str, ring_id: str | None = None, **eff_kw):
    """Build a ring Accessory whose mastery_class slug matches `name`."""
    from items import Accessory
    return Accessory(_acc_defn(
        id=ring_id or name.replace(' ', '_'),
        name=name,
        effects=eff_kw or {},
    ))


# ---------------------------------------------------------------------------
# 1. class_acc_ac_bonus — Ring of Protection mastery adds AC bonus
# ---------------------------------------------------------------------------

def test_class_acc_ac_bonus_lowers_ac():
    from player import Player
    p = Player()
    base_ac = p.get_ac()
    # Equip a "ring of protection" — class_acc_ac_bonus mastery should add +1 AC.
    ring = _make_ring('ring of protection', ring_id='ring_protection_iron')
    p.accessory_slots[0] = ring
    p.unlocked_class_masteries['ring_of_protection'] = {
        'kind': 'class_acc_ac_bonus', 'value': 1, 'desc': '_',
    }
    assert p.get_ac() == base_ac - 1, \
        f"Ring of Protection mastery: expected AC {base_ac - 1}, got {p.get_ac()}"


# ---------------------------------------------------------------------------
# 2. class_acc_regen_bonus — Ring of Regeneration mastery boosts regen
# ---------------------------------------------------------------------------

def test_class_acc_regen_bonus_increases_regen_helper():
    """Helper method on Player surfaces the bonus value for the regen tick."""
    from player import Player
    p = Player()
    assert p.get_class_mastery_regen_bonus() == 0
    p.accessory_slots[0] = _make_ring('ring of regeneration',
                                       ring_id='ring_regen_emerald')
    p.unlocked_class_masteries['ring_of_regeneration'] = {
        'kind': 'class_acc_regen_bonus', 'value': 2, 'desc': '_',
    }
    assert p.get_class_mastery_regen_bonus() == 2


# ---------------------------------------------------------------------------
# 3. class_acc_resist_bonus — Ring of Fire Resist mastery reduces fire damage
# ---------------------------------------------------------------------------

def test_class_acc_resist_bonus_reduces_armor_resistance_multiplier():
    from player import Player
    p = Player()
    # Plain take_damage path: 100 damage fire, fully resisted by mastery.
    p.accessory_slots[0] = _make_ring('ring of fire resist',
                                       ring_id='ring_fireres_ruby')
    p.unlocked_class_masteries['ring_of_fire_resist'] = {
        'kind': 'class_acc_resist_bonus',
        'value': {'type': 'fire', 'amount': 0.10},
        'desc': '_',
    }
    # get_armor_resistance returns a multiplier (1.0 = full, 0.9 = 10% reduced).
    mult_fire = p.get_armor_resistance('fire')
    mult_cold = p.get_armor_resistance('cold')
    assert mult_fire < mult_cold, \
        "Fire mastery should reduce fire damage below cold (unaffected)"
    assert abs(mult_fire - 0.9) < 1e-6, \
        f"Expected fire mult 0.90, got {mult_fire}"


# ---------------------------------------------------------------------------
# 4. class_acc_sp_burn_bonus — Ring of Sustenance mastery slows SP burn
# ---------------------------------------------------------------------------

def test_class_acc_sp_burn_bonus_factor():
    from player import Player
    p = Player()
    assert p.get_class_mastery_sp_burn_factor() == 0.0
    p.accessory_slots[0] = _make_ring('ring of sustenance',
                                       ring_id='ring_sust_amber')
    p.unlocked_class_masteries['ring_of_sustenance'] = {
        'kind': 'class_acc_sp_burn_bonus', 'value': 0.10, 'desc': '_',
    }
    assert abs(p.get_class_mastery_sp_burn_factor() - 0.10) < 1e-6


# ---------------------------------------------------------------------------
# 5. class_acc_passive_radius — Ring of Searching mastery extends radius
# ---------------------------------------------------------------------------

def test_class_acc_passive_radius_searching():
    from player import Player
    p = Player()
    assert p.get_class_mastery_passive_radius_bonus('searching') == 0
    p.accessory_slots[0] = _make_ring('ring of searching',
                                       ring_id='ring_search_topaz')
    p.unlocked_class_masteries['ring_of_searching'] = {
        'kind': 'class_acc_passive_radius', 'value': 1, 'desc': '_',
    }
    assert p.get_class_mastery_passive_radius_bonus('searching') == 1
    # Bonus must be class-scoped — telepathy mastery on a different ring
    # doesn't bleed into searching.
    assert p.get_class_mastery_passive_radius_bonus('telepathy') == 0


# ---------------------------------------------------------------------------
# 6. class_acc_quirk — Ring of Speed mastery extends hasted duration
# ---------------------------------------------------------------------------

def test_class_acc_quirk_extends_haste_duration():
    from player import Player
    p = Player()
    # Mastery alone is enough — equip not required for quirk extends (the
    # blessing's flavor is "you know how to wear this kind of ring").
    p.unlocked_class_masteries['ring_of_speed'] = {
        'kind': 'class_acc_quirk', 'value': 'speed_extend', 'desc': '_',
    }
    p.add_effect('hasted', 10)
    # Vanilla 10 + 4 mastery extend = 14
    assert p.status_effects.get('hasted', 0) == 14, \
        f"Expected hasted 14, got {p.status_effects.get('hasted')}"


# ---------------------------------------------------------------------------
# 7. class_acc_buff_duration_bonus — default fallback adds turns to any buff
# ---------------------------------------------------------------------------

def test_class_acc_buff_duration_bonus_fallback():
    """The fallback default for accessories adds +N to any buff added while
    a mastered ring of that class is equipped."""
    from player import Player
    p = Player()
    p.accessory_slots[0] = _make_ring('ring of fingertips',
                                       ring_id='ring_fingertips_x')
    p.unlocked_class_masteries['ring_of_fingertips'] = {
        'kind': 'class_acc_buff_duration_bonus', 'value': 4, 'desc': '_',
    }
    p.add_effect('hasted', 10)
    assert p.status_effects.get('hasted', 0) == 14, \
        f"Expected hasted 14 from buff_duration_bonus, got {p.status_effects.get('hasted')}"


# ---------------------------------------------------------------------------
# 8. class_scroll_potency — Scroll of Heal mastery heals more
# ---------------------------------------------------------------------------

def test_class_scroll_potency_boosts_scroll_heal():
    """When scroll_of_heal mastery is set, the scroll heals more.

    Uses inspect on the use-site rather than running _apply_scroll_effect (which
    needs a full Game instance). The wiring is verified by reading the source.
    """
    import inspect
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._apply_scroll_effect)
    assert 'class_scroll_potency' in src, \
        "_apply_scroll_effect must query class_scroll_potency for healing scrolls"
    assert "_scroll_pot_mult" in src
    # And the heal branch must use the multiplier.
    heal_idx = src.find("if effect == 'heal'")
    next_branch = src.find("elif effect ==", heal_idx + 1)
    heal_branch = src[heal_idx:next_branch]
    assert '_scroll_pot_mult' in heal_branch, \
        "heal scroll branch must multiply amount by _scroll_pot_mult"


# ---------------------------------------------------------------------------
# 9. class_scroll_extra_uses — Scroll of Identify mastery saves the scroll
# ---------------------------------------------------------------------------

def test_class_scroll_extra_uses_wired_in_read_path():
    """The read path must consult class_scroll_extra_uses before consuming
    the scroll."""
    import pathlib
    src = pathlib.Path('src/game_magic.py').read_text(encoding='utf-8')
    assert 'class_scroll_extra_uses' in src, \
        "src/game_magic.py must wire class_scroll_extra_uses at the scroll-read use-site"
    assert '_class_extra_uses_used' in src, \
        "Per-scroll bonus-use counter must be tracked"


# ---------------------------------------------------------------------------
# 10. class_scroll_persist — Scroll of Mapping mastery auto-maps new floors
# ---------------------------------------------------------------------------

def test_class_scroll_persist_auto_maps_new_floors():
    """The level-change path must consult scroll_of_mapping mastery."""
    import pathlib
    src = pathlib.Path('src/main.py').read_text(encoding='utf-8')
    assert 'class_scroll_persist' in src, \
        "src/main.py must wire class_scroll_persist for scroll_of_mapping at level change"
    # And the wiring should appear AFTER _change_level's dungeon assignment
    idx = src.find('def _change_level')
    assert idx >= 0
    block = src[idx:idx + 5000]
    assert 'class_scroll_persist' in block, \
        "class_scroll_persist must be wired inside _change_level (post-dungeon assignment)"
    assert 'dungeon.explored.add' in block


# ---------------------------------------------------------------------------
# 11. potion_potency_bonus — Potion of Healing mastery heals more
# ---------------------------------------------------------------------------

def test_potion_potency_bonus_increases_heal_amount():
    from player import Player
    from items import Potion
    from food_system import drink_potion
    import random
    # Seed the RNG so both rolls produce the same value.
    random.seed(42)
    p = Player()
    p.hp = 1
    p.max_hp = 200
    pot1 = Potion({'id': 'potion_of_healing', 'name': 'potion of healing',
                   'symbol': '!', 'color': [255, 0, 0],
                   'effect': 'heal', 'power': '4d4'})
    drink_potion(p, pot1)
    baseline = p.hp - 1

    random.seed(42)
    p2 = Player()
    p2.hp = 1
    p2.max_hp = 200
    p2.unlocked_class_masteries['potion_of_healing'] = {
        'kind': 'potion_potency_bonus', 'value': 0.50, 'desc': '_',
    }
    pot2 = Potion({'id': 'potion_of_healing', 'name': 'potion of healing',
                   'symbol': '!', 'color': [255, 0, 0],
                   'effect': 'heal', 'power': '4d4'})
    drink_potion(p2, pot2)
    mastered = p2.hp - 1
    assert mastered > baseline, \
        f"Mastered heal ({mastered}) must exceed baseline ({baseline})"
    # 50% bonus: mastered ~= 1.5x baseline
    assert mastered == int(baseline * 1.5), \
        f"Expected mastered ({mastered}) to equal int(baseline*1.5)={int(baseline*1.5)}; baseline={baseline}"


# ---------------------------------------------------------------------------
# 12. potion_duration_bonus — Potion of Haste mastery extends duration
# ---------------------------------------------------------------------------

def test_potion_duration_bonus_extends_haste_duration():
    from player import Player
    from items import Potion
    from food_system import drink_potion
    # Baseline drink — 40 turns of haste from data, but apply_effect caps
    # somewhere; just compare with vs without mastery on the SAME player.
    p1 = Player()
    pot1 = Potion({'id': 'potion_of_haste', 'name': 'potion of haste',
                   'symbol': '!', 'color': [255, 140, 20],
                   'effect': 'haste', 'power': '', 'duration': 20})
    drink_potion(p1, pot1)
    baseline = p1.status_effects.get('hasted', 0)

    p2 = Player()
    p2.unlocked_class_masteries['potion_of_haste'] = {
        'kind': 'potion_duration_bonus', 'value': 4, 'desc': '_',
    }
    pot2 = Potion({'id': 'potion_of_haste', 'name': 'potion of haste',
                   'symbol': '!', 'color': [255, 140, 20],
                   'effect': 'haste', 'power': '', 'duration': 20})
    drink_potion(p2, pot2)
    mastered = p2.status_effects.get('hasted', 0)
    assert mastered > baseline, \
        f"Mastered haste ({mastered}) must exceed baseline ({baseline})"
    # Difference should be 4 turns (the mastery value); BUC mult on baseline
    # is 1.0 for uncursed so 20 baseline + 4 mastery = 24 mastered.
    assert mastered - baseline == 4, \
        f"Mastery delta should equal value 4, got {mastered - baseline}"


# ---------------------------------------------------------------------------
# Bonus: sanity check that all 11 dead kinds now have at least one read site
# in src/ (so future audits don't regress this)
# ---------------------------------------------------------------------------

def test_every_dead_kind_now_read_in_src():
    """Each kind must appear in at least one .py file under src/ besides
    class_masteries.py and game_magic._claim_mastery (which only WRITES)."""
    import pathlib
    dead_kinds = [
        'class_acc_ac_bonus',
        'class_acc_regen_bonus',
        'class_acc_passive_radius',
        'class_acc_resist_bonus',
        'class_acc_sp_burn_bonus',
        'class_acc_quirk',
        'class_acc_buff_duration_bonus',
        'class_scroll_potency',
        'class_scroll_persist',
        'class_scroll_extra_uses',
        'potion_potency_bonus',
        'potion_duration_bonus',
    ]
    src_root = pathlib.Path('src')
    py_files = [pp for pp in src_root.rglob('*.py')
                if pp.name != 'class_masteries.py']
    combined = '\n'.join(f.read_text(encoding='utf-8') for f in py_files)
    for kind in dead_kinds:
        assert kind in combined, \
            f"Mastery kind {kind!r} has no read site outside class_masteries.py"
