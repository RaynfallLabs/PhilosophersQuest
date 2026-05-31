"""Engine wave 3 (2026-05-30): wire the rest of the audit-deferred flags.

22 previously-deferred mechanics now have consumers. Tests confirm each
field LOADS onto Weapon and the consumer call sites EXIST.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from items import Weapon


def _w(**kw):
    defn = {
        'id': 't', 'name': 't', 'symbol': '(',
        'color': [255, 255, 255], 'weight': 1.0,
        'item_class': 'weapon', 'class': 'sword',
        'base_damage': 5, 'damage_types': ['slash'],
    }
    defn.update(kw)
    return Weapon(defn)


# ---------------------------------------------------------------------------
# Field loading
# ---------------------------------------------------------------------------

def test_loads_weapon_immune_to_enchant_loss():
    assert _w(weapon_immune_to_enchant_loss=True).weapon_immune_to_enchant_loss is True
    assert _w().weapon_immune_to_enchant_loss is False


def test_loads_wielder_status_immunity():
    assert _w(wielder_status_immunity=['fire', 'cold']).wielder_status_immunity == ['fire', 'cold']
    assert _w().wielder_status_immunity == []


def test_loads_stealth_damage_bonus():
    assert _w(stealth_damage_bonus=0.5).stealth_damage_bonus == 0.5
    assert _w().stealth_damage_bonus == 0.0


def test_loads_cannot_miss_before_player_takes_damage():
    assert _w(cannot_miss_before_player_takes_damage=True).cannot_miss_before_hurt is True
    assert _w().cannot_miss_before_hurt is False


def test_loads_damage_double_vs_resistant_at_max():
    assert _w(damage_double_vs_resistant_at_max=True).damage_double_vs_resistant_at_max is True


def test_loads_apply_heal_block_chance():
    assert _w(apply_heal_block_chance=0.3).apply_heal_block_chance == 0.3


def test_loads_one_shot_chain_save_per_floor():
    assert _w(one_shot_chain_save_per_floor=True).one_shot_chain_save_per_floor is True


def test_loads_damoclean_counter_auto_kill():
    w = _w(damoclean_counter_auto_kill=True)
    assert w.damoclean_counter_threshold > 0  # default 10
    assert w._damoclean_consecutive == 0


def test_loads_floor_start_reveal_chance():
    assert _w(floor_start_reveal_chance=0.5).floor_start_reveal_chance == 0.5


def test_loads_surrounded_proc_bonus():
    assert _w(surrounded_proc_bonus=True).surrounded_proc_bonus is True


def test_loads_chain_no_reset_on_tag():
    assert _w(chain_no_reset_on_tag=['humanoid']).chain_no_reset_on_tag == ['humanoid']


def test_loads_skip_chain_warmup_vs_tag():
    assert _w(skip_chain_warmup_vs_tag=['aberration']).skip_chain_warmup_vs_tag == ['aberration']


def test_loads_equipped_light_aura():
    assert _w(equipped_light_aura=3).equipped_light_aura == 3


def test_loads_kill_count_karma_adjust():
    assert _w(kill_count_karma_adjust=100).kill_count_karma_adjust == 100


def test_loads_combat_start_aoe_confuse_chance():
    assert _w(combat_start_aoe_confuse_chance=0.5).combat_start_aoe_confuse_chance == 0.5


def test_loads_extra_action_after_kill():
    assert _w(extra_action_after_kill=True).extra_action_after_kill is True


def test_loads_adjacent_pet_damage_bonus():
    assert _w(adjacent_pet_damage_bonus=0.25).adjacent_pet_damage_bonus == 0.25


def test_loads_equipped_ally_aura_buff_str():
    assert _w(equipped_ally_aura_buff_str=1).equipped_ally_aura_buff_str == 1


def test_loads_reveal_tag_on_chain_5_kill():
    assert _w(reveal_tag_on_chain_5_kill=['beast']).reveal_tag_on_chain_5_kill == ['beast']


def test_loads_chain_bonus_on_low_hp_window():
    assert _w(chain_bonus_on_low_hp_window=1).chain_bonus_on_low_hp_window == 1


# ---------------------------------------------------------------------------
# Consumer code present
# ---------------------------------------------------------------------------

def test_combat_wires_cannot_miss_before_hurt():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'cannot_miss_before_hurt' in src
    assert '_combat_player_taken_damage' in src


def test_combat_wires_one_shot_chain_save():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'one_shot_chain_save_per_floor' in src
    assert '_hrunting_save_used' in src


def test_combat_wires_skofnung_low_hp_window():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'chain_bonus_on_low_hp_window' in src
    assert '_skofnung_low_hp_pending' in src


def test_combat_wires_skip_chain_warmup_vs_tag():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'skip_chain_warmup_vs_tag' in src


def test_combat_wires_damage_double_vs_resistant_at_max():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'damage_double_vs_resistant_at_max' in src


def test_combat_wires_stealth_damage_bonus():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'stealth_damage_bonus' in src
    assert "'invisible'" in src


def test_combat_wires_surrounded_proc_bonus():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'surrounded_proc_bonus' in src
    assert '_kusanagi_force_crit' in src


def test_combat_wires_adjacent_pet_damage_bonus():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'adjacent_pet_damage_bonus' in src


def test_combat_wires_apply_heal_block():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'apply_heal_block_chance' in src
    assert "'heal_blocked'" in src


def test_combat_wires_damoclean_counter():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'damoclean_counter_threshold' in src
    assert '_damoclean_consecutive' in src


def test_combat_wires_kill_count_karma():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'kill_count_karma_adjust' in src
    assert '_karma_kill_tally' in src


def test_combat_wires_chain_no_reset_on_tag():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'chain_no_reset_on_tag' in src
    assert '_chain_carry' in src


def test_combat_wires_reveal_tag_on_chain_5_kill():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'reveal_tag_on_chain_5_kill' in src
    assert '_revealed_tag_ids' in src


def test_combat_wires_chain_carry_consumption():
    """Chain start in player_attack must consume _chain_carry."""
    import combat
    src = inspect.getsource(combat.player_attack)
    assert '_chain_carry = 0' in src or 'player._chain_carry = 0' in src


def test_player_take_damage_wires_combat_tracker():
    """take_damage flips _combat_player_taken_damage to True on actual harm."""
    from player import Player
    src = inspect.getsource(Player.take_damage)
    assert '_combat_player_taken_damage' in src


def test_player_take_damage_wires_skofnung_pending():
    from player import Player
    src = inspect.getsource(Player.take_damage)
    assert '_skofnung_low_hp_pending' in src


def test_player_restore_hp_honors_heal_blocked():
    from player import Player
    src = inspect.getsource(Player.restore_hp)
    assert "'heal_blocked'" in src or 'heal_blocked' in src


def test_player_sight_radius_includes_equipped_light_aura():
    from player import Player
    src = inspect.getsource(Player.get_sight_radius)
    assert 'equipped_light_aura' in src


def test_player_wielder_status_immunity_blocks():
    from player import Player
    src = inspect.getsource(Player.take_damage)
    assert 'wielder_status_immunity' in src


def test_game_combat_sets_combat_refs():
    """game_combat._start_combat must set _combat_monsters_ref,
    _combat_pets_ref, _combat_game_ref for combat-side consumers."""
    from game_combat import CombatMixin
    src = inspect.getsource(CombatMixin._start_combat)
    assert '_combat_monsters_ref' in src
    assert '_combat_pets_ref' in src
    assert '_combat_game_ref' in src


def test_game_combat_wires_joyeuse_dazzle():
    """Combat-start AOE confuse for Joyeuse."""
    from game_combat import CombatMixin
    src = inspect.getsource(CombatMixin._start_combat)
    assert 'combat_start_aoe_confuse_chance' in src


def test_game_combat_wires_zireael_extra_action():
    """_on_monster_killed grants the extra action after kill flag."""
    from game_combat import CombatMixin
    src = inspect.getsource(CombatMixin._on_monster_killed)
    assert 'extra_action_after_kill' in src
    assert '_zireael_used_this_turn' in src


def test_game_combat_wires_ally_aura_buff():
    from game_combat import CombatMixin
    src = inspect.getsource(CombatMixin._on_monster_killed)
    assert 'equipped_ally_aura_buff_str' in src


def test_main_wires_hrunting_per_floor_reset():
    from main import Game
    src = inspect.getsource(Game._change_level)
    assert '_hrunting_save_used' in src


def test_main_wires_floor_start_reveal():
    from main import Game
    src = inspect.getsource(Game._change_level)
    assert 'floor_start_reveal_chance' in src


def test_main_wires_advance_turn_resets():
    """Turn-advance resets the Zireael per-turn flag and decays reveal timer."""
    from main import Game
    src = inspect.getsource(Game._advance_turn)
    assert '_zireael_used_this_turn' in src
    assert '_revealed_tag_turns_left' in src


def test_game_magic_blocks_enchant_loss_for_chrysaor():
    """Cursed scroll of enchant_weapon must skip negative delta on
    weapon_immune_to_enchant_loss weapons."""
    import game_magic
    src = inspect.getsource(game_magic.MagicMixin._apply_scroll_effect)
    assert 'weapon_immune_to_enchant_loss' in src


def test_heal_blocked_status_registered():
    """The new heal_blocked status must be in DEBUFFS and EFFECT_INFO."""
    from status_effects import DEBUFFS, EFFECT_INFO
    assert 'heal_blocked' in DEBUFFS
    assert 'heal_blocked' in EFFECT_INFO


# ---------------------------------------------------------------------------
# Integration smoke
# ---------------------------------------------------------------------------

def test_restore_hp_returns_zero_when_heal_blocked():
    from player import Player
    p = Player()
    p.max_hp = 100
    p.hp = 50
    p.status_effects['heal_blocked'] = 5
    n = p.restore_hp(20)
    assert n == 0
    assert p.hp == 50
    # Without heal_blocked
    del p.status_effects['heal_blocked']
    n = p.restore_hp(20)
    assert n == 20
    assert p.hp == 70


def test_sight_radius_extends_with_torch():
    from player import Player
    p = Player()
    base = p.get_sight_radius()
    p.weapon = _w(equipped_light_aura=3)
    assert p.get_sight_radius() == base + 3


def test_fire_immunity_via_wielder_status_immunity_generalized():
    """wielder_status_immunity ['fire'] should block fire damage even
    without the legacy wielder_fire_immunity flag."""
    from player import Player
    p = Player()
    p.weapon = _w(wielder_status_immunity=['fire'])
    actual = p.take_damage(50, 'fire')
    assert actual == 0
    # Physical damage still applies
    actual = p.take_damage(5, 'physical')
    assert actual > 0
