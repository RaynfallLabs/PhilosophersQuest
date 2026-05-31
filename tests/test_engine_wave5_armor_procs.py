"""Engine wave 5 (2026-05-30): flat-armor procs from the unique-armor audit.

The audit found 30+ legendary armors with proposal-only mechanics. This wave
wires the consumers at:

- monster.attack:         unskinnable, dodge_first_arrow, monkey_king_dodge
- game_combat post-hit:   webbed_strike, their_own_methods, caustic_blood,
                          story_thread, et_tu_charge mark, maid_does_not_fall
- combat.player_attack:   last_stand_bonus, cannae_encirclement dmg,
                          et_tu_charge dmg, gita_focus crit, riastrad_echo
- player.get_ac:          cannae_encirclement AC, boundary_guardian,
                          guerrilla_terrain, paradise_water
- main._advance_turn:     thors_step, weave_and_unweave, terrain caches
- main._change_level:     descent_haste, ringing_intimidation, bond_check,
                          per-floor charge reset
- main._refresh_fov:      forest_hearing, tremor_sense
- player._apply_equip:    prophets_passing (+max_mp)
- items.effective_enchant_cap: divine_smithing
- status_effects.tick_all: grendel_grip
- game_combat pet damage: wild_friend
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from items import Armor


def _armor(**kw):
    defn = {
        'id': 'a', 'name': 'a', 'symbol': '[',
        'color': [255, 255, 255], 'weight': 1.0,
        'item_class': 'armor', 'slot': 'body',
        'ac_bonus': 1, 'tier': 1,
    }
    defn.update(kw)
    return Armor(defn)


# ---------------------------------------------------------------------------
# Field loading on Armor class
# ---------------------------------------------------------------------------

def test_loads_unskinnable():
    assert _armor(unskinnable=True).unskinnable is True


def test_loads_weave_and_unweave():
    assert _armor(weave_and_unweave=True).weave_and_unweave is True


def test_loads_phalanx_recovery():
    assert _armor(phalanx_recovery=5).phalanx_recovery == 5


def test_loads_water_tile_ac_bonus():
    a = _armor(water_tile_ac_bonus=2, water_tile_regen_bonus=1)
    assert a.water_tile_ac_bonus == 2
    assert a.water_tile_regen_bonus == 1


def test_loads_prophets_passing():
    assert _armor(prophets_passing=True).prophets_passing is True


def test_loads_webbed_strike():
    assert _armor(webbed_strike=True).webbed_strike is True


def test_loads_forest_hearing():
    assert _armor(forest_hearing=6).forest_hearing == 6


def test_loads_story_thread():
    assert _armor(story_thread=True).story_thread is True


def test_loads_monkey_king_dodge():
    assert _armor(monkey_king_dodge=10).monkey_king_dodge == 10


def test_loads_grendel_grip():
    assert _armor(grendel_grip=True).grendel_grip is True


def test_loads_gold_offering():
    assert _armor(gold_offering=True).gold_offering is True


def test_loads_bond_check():
    assert _armor(bond_check=True).bond_check is True


def test_loads_bovine_fury():
    assert _armor(bovine_fury=True).bovine_fury is True


def test_loads_dodge_first_arrow():
    assert _armor(dodge_first_arrow_per_floor=True).dodge_first_arrow_per_floor is True


def test_loads_quest_humility():
    assert _armor(quest_humility=True).quest_humility is True


def test_loads_their_own_methods():
    assert _armor(their_own_methods=0.20).their_own_methods == 0.20


def test_loads_royal_burial():
    assert _armor(royal_burial=True).royal_burial is True


def test_loads_riastrad_echo():
    assert _armor(riastrad_echo=True).riastrad_echo is True


def test_loads_cannae_encirclement():
    assert _armor(cannae_encirclement=True).cannae_encirclement is True


def test_loads_last_stand_bonus():
    assert _armor(last_stand_bonus=True).last_stand_bonus is True


def test_loads_et_tu_charge():
    assert _armor(et_tu_charge=True).et_tu_charge is True


def test_loads_guerrilla_terrain():
    assert _armor(guerrilla_terrain=True).guerrilla_terrain is True


def test_loads_disguise_at_camp():
    assert _armor(disguise_at_camp=True).disguise_at_camp is True


def test_loads_boundary_guardian():
    assert _armor(boundary_guardian=True).boundary_guardian is True


def test_loads_wild_friend():
    assert _armor(wild_friend=0.2).wild_friend == 0.2


def test_loads_gita_focus():
    assert _armor(gita_focus=True).gita_focus is True


def test_loads_seven_league_step():
    assert _armor(seven_league_step=True).seven_league_step is True


def test_loads_tremor_sense():
    assert _armor(tremor_sense=3).tremor_sense == 3


def test_loads_peace_at_the_forge():
    assert _armor(peace_at_the_forge=2).peace_at_the_forge == 2


def test_loads_caustic_blood():
    assert _armor(caustic_blood=0.5).caustic_blood == 0.5


def test_loads_divine_smithing():
    assert _armor(divine_smithing=1).divine_smithing == 1


def test_loads_maid_does_not_fall():
    assert _armor(maid_does_not_fall=True).maid_does_not_fall is True


def test_loads_atlantean_resonance():
    assert _armor(atlantean_resonance=5).atlantean_resonance == 5


def test_loads_descent_haste():
    assert _armor(descent_haste=5).descent_haste == 5


def test_loads_ringing_intimidation():
    assert _armor(ringing_intimidation=3).ringing_intimidation == 3


def test_loads_purity():
    assert _armor(purity=True).purity is True


def test_loads_thors_step():
    assert _armor(thors_step=0.05).thors_step == 0.05


# ---------------------------------------------------------------------------
# Helper module exists
# ---------------------------------------------------------------------------

def test_armor_procs_module_present():
    import armor_procs
    assert hasattr(armor_procs, 'player_has_armor_proc')
    assert hasattr(armor_procs, 'proc_value')
    assert hasattr(armor_procs, 'consume_floor_charge')
    assert hasattr(armor_procs, 'consume_run_charge')
    assert hasattr(armor_procs, 'reset_per_floor_charges')


def test_armor_procs_player_has_armor_proc_truthy():
    """player_has_armor_proc finds an item with the attr set."""
    from armor_procs import player_has_armor_proc

    class _P:
        armor_slots = [None, _armor(unskinnable=True), None, None, None, None, None, None]
    assert player_has_armor_proc(_P(), 'unskinnable') is True


def test_armor_procs_player_has_armor_proc_falsy():
    from armor_procs import player_has_armor_proc

    class _P:
        armor_slots = [None] * 8
    assert player_has_armor_proc(_P(), 'unskinnable') is False


def test_armor_procs_consume_floor_charge_once_per_floor():
    from armor_procs import consume_floor_charge, reset_per_floor_charges

    class _P:
        armor_slots = [None, _armor(maid_does_not_fall=True), None, None, None, None, None, None]
    p = _P()
    assert consume_floor_charge(p, 'maid_does_not_fall') is True
    assert consume_floor_charge(p, 'maid_does_not_fall') is False
    reset_per_floor_charges(p)
    assert consume_floor_charge(p, 'maid_does_not_fall') is True


def test_armor_procs_consume_run_charge_once_per_run():
    from armor_procs import consume_run_charge

    class _P:
        armor_slots = [None, _armor(maid_does_not_fall=True), None, None, None, None, None, None]
    p = _P()
    assert consume_run_charge(p, 'maid_does_not_fall') is True
    assert consume_run_charge(p, 'maid_does_not_fall') is False


# ---------------------------------------------------------------------------
# Hook-site wiring (presence checks via getsource)
# ---------------------------------------------------------------------------

def test_monster_attack_wires_unskinnable():
    from monster import Monster
    src = inspect.getsource(Monster.attack)
    assert 'unskinnable' in src


def test_monster_attack_wires_dodge_first_arrow():
    from monster import Monster
    src = inspect.getsource(Monster.attack)
    assert 'dodge_first_arrow_per_floor' in src


def test_monster_attack_wires_monkey_king_dodge():
    from monster import Monster
    src = inspect.getsource(Monster.attack)
    assert 'monkey_king_dodge' in src


def test_combat_wires_last_stand_bonus():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'last_stand_bonus' in src


def test_combat_wires_cannae_encirclement_damage():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'cannae_encirclement' in src


def test_combat_wires_et_tu_charge_damage():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert '_et_tu_target' in src


def test_combat_wires_gita_focus():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'gita_focus' in src


def test_combat_wires_riastrad_echo():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'riastrad_echo' in src


def test_player_get_ac_wires_terrain_procs():
    from player import Player
    src = inspect.getsource(Player.get_ac)
    assert '_armor_proc_adj_enemies' in src
    assert '_armor_proc_near_door' in src
    assert '_armor_proc_in_corridor' in src
    assert '_armor_proc_on_water' in src


def test_status_effects_tick_all_wires_grendel_grip():
    import status_effects
    src = inspect.getsource(status_effects.tick_all)
    assert 'grendel_grip' in src


def test_items_effective_enchant_cap_present():
    import items
    assert hasattr(items, 'effective_enchant_cap')


def test_items_effective_enchant_cap_uses_divine_smithing():
    import items
    src = inspect.getsource(items.effective_enchant_cap)
    assert 'divine_smithing' in src


def test_player_apply_equip_wires_prophets_passing():
    from player import Player
    src = inspect.getsource(Player._apply_equip)
    assert 'prophets_passing' in src
    assert '_prophets_mp_grant' in src


# ---------------------------------------------------------------------------
# Behavior smoke
# ---------------------------------------------------------------------------

def test_unskinnable_floors_physical_dmg_to_one():
    """A monster's physical attack against an unskinnable wearer floors at 1.

    Builds a synthetic monster with a known dice attack, equips the Nemean
    pelt, and verifies the dmg variable in monster.attack is clamped.
    """
    import random
    from monster import Monster

    class _Mon(Monster):
        pass
    m = _Mon.__new__(_Mon)
    m.name = 't'
    m.hp = 50; m.max_hp = 50; m.alive = True; m.kind = 't'
    m.attacks = [{'name': 'claw', 'damage': '5d6', 'type': 'physical'}]
    m.thac0 = 5; m.is_boss = False; m.min_hit_chance = 1.0
    m.gaze_paralyze = 0; m._gaze_cooldown = 0; m.gaze_cooldown_max = 5
    m.status_effects = {}; m.tags = []
    m.rage_stacks = 0; m.rage_damage_bonus = ''
    m.can_charge = False; m._charge_ready = False; m.charge_bonus_mult = 1.5
    m._mimic_surprise = False; m.ai_pattern = 'melee'
    m._aoo_disengage_pending = False; m._force_piercing = False
    m._is_summoned = False; m._gaze_cooldown = 0
    m.x = 0; m.y = 0; m.resistances = []; m.weaknesses = []
    m.magical = False

    def _h(eff):
        return m.status_effects.get(eff, 0) > 0
    m.has_effect = _h

    class _P:
        x = 0; y = 0; max_hp = 100; hp = 100
        status_effects = {}
        armor_slots = [None, _armor(slot='body', ac_bonus=6, unskinnable=True), None, None, None, None, None, None]
        shield = None
        _facing_dx = 0; _facing_dy = 0

        def get_sight_radius(self): return 10
        def get_ac(self): return 0
        def has_effect(self, e): return False
        def take_damage(self, amt, _t='physical'):
            self.hp -= amt; return amt
        def add_effect(self, e, d): self.status_effects[e] = d
    p = _P()

    # Force a fixed roll so the to_hit + damage path is deterministic.
    random.seed(7)
    actual, msg = m.attack(p)
    # Damage should have been clamped to 1 by unskinnable.
    assert actual <= 1


def test_grendel_grip_clears_paralysis_on_tick():
    """status_effects.tick_all clears paralyzed when grendel_grip is equipped."""
    import status_effects

    class _P:
        armor_slots = [None, None, None, None, None, None, None, None]
        status_effects = {'paralyzed': 5}
        hp = 50; max_hp = 50

        def has_effect(self, e): return self.status_effects.get(e, 0) > 0
        def take_damage(self, amt, _t='physical'):
            self.hp -= amt; return amt
        def apply_stat_bonus(self, s, n): pass
    p = _P()
    # head is index 0; install Beowulf coif there
    p.armor_slots[0] = _armor(slot='head', grendel_grip=True)
    status_effects.tick_all(p)
    assert p.status_effects.get('paralyzed', 0) == 0


def test_divine_smithing_raises_enchant_cap():
    """effective_enchant_cap returns ENCHANT_CAP['weapon'] + divine_smithing."""
    from items import effective_enchant_cap, ENCHANT_CAP

    class _P:
        armor_slots = [None, _armor(slot='body', divine_smithing=1), None, None, None, None, None, None]
    base = ENCHANT_CAP['weapon']
    assert effective_enchant_cap(_P(), 'weapon') == base + 1
    # Doesn't affect armor slots
    assert effective_enchant_cap(_P(), 'body') == ENCHANT_CAP['body']
