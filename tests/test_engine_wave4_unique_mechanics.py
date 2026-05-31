"""Engine wave 4 (2026-05-30): every previously-"complex/deferred" mechanic
from the unique-weapons audit now built end-to-end.

Covers:
- Mjolnir chain_lightning_at_chain_n
- Sudarshana return_to_hand_ward
- Laevateinn boss_doom_dot_at_chain_5 + doom_dot status
- Spear of Longinus weep_heal_on_kill_scaled
- Rod of Moses chain_tier_status_table
- Zulfiqar every_hit_secondary_target
- Gandiva multi_arrow_at_chain_5
- Soul Reaver growth_on_innocent_kill
- Chandrahasa karma_disappear_proc
- Ruyi Jingu Bang chain_modulated_reach
- Curtana spare_kill_chance
- Spear of Lugh damage_bonus_vs_gaze
- Echidna's Fang random_status_from_pool
- Cadmus/Vel/Shamshir summon_after_kill_with_tag
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

def test_loads_chain_lightning():
    w = _w(chain_lightning_at_chain_n={'from_chain': 6, 'splash_pct': 0.5, 'max_targets': 1})
    assert w.chain_lightning_at_chain_n == {'from_chain': 6, 'splash_pct': 0.5, 'max_targets': 1}


def test_loads_return_to_hand_ward():
    assert _w(return_to_hand_ward=True).return_to_hand_ward is True


def test_loads_boss_doom_dot():
    assert _w(boss_doom_dot_at_chain_5={'pct_max_hp_per_turn': 0.05}).boss_doom_dot_at_chain_5 == {'pct_max_hp_per_turn': 0.05}


def test_loads_weep_heal():
    assert _w(weep_heal_on_kill_scaled=0.1).weep_heal_on_kill_scaled == 0.1


def test_loads_chain_tier_status_table():
    assert _w(chain_tier_status_table={'3': {'status': 'slowed', 'duration': 3}}).chain_tier_status_table


def test_loads_every_hit_secondary():
    assert _w(every_hit_secondary_target={'splash_pct': 0.5}).every_hit_secondary_target


def test_loads_multi_arrow_at_chain_5():
    assert _w(multi_arrow_at_chain_5={'targets': 3, 'damage_per': 0.5}).multi_arrow_at_chain_5


def test_loads_growth_on_innocent_kill():
    assert _w(growth_on_innocent_kill=True).growth_on_innocent_kill is True


def test_loads_karma_disappear_proc():
    assert _w(karma_disappear_proc=0.05).karma_disappear_proc == 0.05


def test_loads_chain_modulated_reach():
    assert _w(chain_modulated_reach={'4': 4, '7': 5}).chain_modulated_reach


def test_loads_spare_kill_chance():
    w = _w(spare_kill_chance=0.25)
    assert w.spare_kill_chance == 0.25
    assert w.spare_kill_max_hp_per_floor == 5


def test_loads_damage_bonus_vs_gaze():
    assert _w(damage_bonus_vs_gaze=2.0).damage_bonus_vs_gaze == 2.0


def test_loads_random_status_from_pool():
    assert _w(random_status_from_pool={'pool': ['poisoned'], 'chance': 0.4}).random_status_from_pool


def test_loads_summon_after_kill_with_tag():
    assert _w(summon_after_kill_with_tag={'tag': 'demon', 'duration_turns': 5}).summon_after_kill_with_tag


# ---------------------------------------------------------------------------
# Consumer code present
# ---------------------------------------------------------------------------

def test_combat_wires_chain_lightning():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'chain_lightning_at_chain_n' in src
    assert "'lightning'" in src


def test_combat_wires_every_hit_secondary():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'every_hit_secondary_target' in src


def test_combat_wires_multi_arrow():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'multi_arrow_at_chain_5' in src


def test_combat_wires_chain_tier_status_table():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'chain_tier_status_table' in src


def test_combat_wires_boss_doom_dot():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'boss_doom_dot_at_chain_5' in src
    assert 'doom_dot' in src


def test_combat_wires_weep_heal():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'weep_heal_on_kill_scaled' in src


def test_combat_wires_return_to_hand_ward():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'return_to_hand_ward' in src
    assert '_return_to_hand_active' in src


def test_combat_wires_growth_on_innocent_kill():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'growth_on_innocent_kill' in src
    assert '_next_hit_auto_crit' in src


def test_combat_wires_damage_bonus_vs_gaze():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'damage_bonus_vs_gaze' in src
    assert 'gaze_paralyze' in src


def test_combat_wires_random_status_from_pool():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'random_status_from_pool' in src


def test_combat_wires_summon_after_kill():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'summon_after_kill_with_tag' in src
    assert '_pending_summon' in src


def test_combat_wires_spare_kill():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'spare_kill_chance' in src
    assert '_spare_kill_floor_hp' in src


def test_combat_wires_chain_modulated_reach():
    import combat
    src = inspect.getsource(combat.can_melee_attack)
    assert 'chain_modulated_reach' in src


def test_monster_attack_wires_return_to_hand():
    """Monster.attack must check _return_to_hand_active and miss."""
    from monster import Monster
    src = inspect.getsource(Monster.attack)
    assert '_return_to_hand_active' in src


def test_monster_tick_wires_doom_dot():
    """Monster.tick_effects must apply doom_dot damage based on _doom_dot_pct."""
    from monster import Monster
    src = inspect.getsource(Monster.tick_effects)
    assert "'doom_dot'" in src
    assert '_doom_dot_pct' in src


def test_main_wires_karma_disappear():
    from main import Game
    src = inspect.getsource(Game._change_level)
    assert 'karma_disappear_proc' in src


def test_main_advance_turn_decays_temp_pets():
    from main import Game
    src = inspect.getsource(Game._advance_turn)
    assert '_temp_duration' in src


def test_game_combat_wires_pending_summon():
    from game_combat import CombatMixin
    src = inspect.getsource(CombatMixin._on_monster_killed)
    assert '_pending_summon' in src


def test_game_combat_wires_spared_message():
    from game_combat import CombatMixin
    src = inspect.getsource(CombatMixin._on_monster_killed)
    assert '_spared_this_attack' in src


def test_doom_dot_status_registered():
    from status_effects import EFFECT_INFO
    assert 'doom_dot' in EFFECT_INFO


# ---------------------------------------------------------------------------
# Behavior smoke
# ---------------------------------------------------------------------------

def test_chain_modulated_reach_extends_can_melee():
    """A Ruyi-style weapon with chain_modulated_reach reaches further."""
    from combat import can_melee_attack
    class _M:
        x = 0; y = 0; alive = True
    class _P:
        x = 0; y = 0
    p = _P()
    p.weapon = _w(reach=1, chain_modulated_reach={'4': 3, '7': 5})
    m = _M()
    m.x, m.y = 4, 0  # 4 tiles away
    # Without the modulator a reach-1 weapon couldn't hit 4 tiles. With it, can.
    assert can_melee_attack(p, m) is True


def test_doom_dot_ticks_max_hp_pct():
    """Monster with doom_dot 30 turns + 5% pct deals 5% max HP per tick."""
    from monster import Monster
    # Find any reasonable monster JSON to construct (use a minimal stub).
    class _Mon(Monster):
        pass
    m = _Mon.__new__(_Mon)
    m.name = 't'
    m.hp = 100; m.max_hp = 100; m.alive = True
    m.status_effects = {'doom_dot': 5}
    m._doom_dot_pct = 0.1
    m.attacks = []
    m.kind = 't'
    m.tags = []
    m.resistances = {}
    m.weaknesses = {}
    # take_damage must exist on Monster; calls hp -= ...
    m.tick_effects()
    # After tick: doom_dot dealt 10 damage (10% of 100), hp = 90
    assert m.hp == 90
    # And the duration ticked down by 1 (5 -> 4)
    assert m.status_effects.get('doom_dot') == 4
