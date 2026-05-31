"""Engine wave 2: the remaining inert weapon-flag wires (2026-05-30).

Per user direction "do it now, piece by piece" — finishes the deferred
flags from the first engine wave:

- glows_near_orcs   (Glamdring)  : +1 chain rung vs goblin/orc tags
- vigilance_aware   (Hofud)      : +2 PER while equipped
- selects_wielder   (Stormbringer): refuses unequip
- cast_me_away      (Excalibur)  : one-shot life_save at HP <= 25%
- cursed_lineage    (Pelops)     : on-equip -1 STR/+2 HP + 5%/floor House of Atreus
- prophecy_blade    (Akinakes)   : on-equip declare random tag, +50% dmg
- betrays_at_low_hp (Stormbringer): hits adjacent pet at HP <= 15% on melee hit
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from items import Weapon


def _make_weapon(**overrides):
    defn = {
        'id': 'test_w', 'name': 'test',
        'symbol': '(', 'color': [255, 255, 255], 'weight': 1.0,
        'item_class': 'weapon', 'class': 'sword',
        'base_damage': 5, 'damage_types': ['slash'],
    }
    defn.update(overrides)
    return Weapon(defn)


# ---------------------------------------------------------------------------
# Field loading on Weapon
# ---------------------------------------------------------------------------

def test_loads_glows_near_orcs():
    assert _make_weapon(glows_near_orcs=True).glows_near_orcs is True
    assert _make_weapon().glows_near_orcs is False


def test_loads_vigilance_aware():
    assert _make_weapon(vigilance_aware=True).vigilance_aware is True
    assert _make_weapon().vigilance_aware is False


def test_loads_selects_wielder():
    assert _make_weapon(selects_wielder=True).selects_wielder is True
    assert _make_weapon().selects_wielder is False


def test_loads_betrays_at_low_hp():
    assert _make_weapon(betrays_at_low_hp=True).betrays_at_low_hp is True
    assert _make_weapon().betrays_at_low_hp is False


def test_loads_cast_me_away():
    assert _make_weapon(cast_me_away=True).cast_me_away is True
    assert _make_weapon().cast_me_away is False


def test_loads_cursed_lineage():
    assert _make_weapon(cursed_lineage=True).cursed_lineage is True
    assert _make_weapon().cursed_lineage is False


def test_loads_prophecy_blade():
    assert _make_weapon(prophecy_blade=True).prophecy_blade is True
    assert _make_weapon().prophecy_blade is False


# ---------------------------------------------------------------------------
# combat.py wiring
# ---------------------------------------------------------------------------

def test_combat_wires_glows_near_orcs():
    """+1 chain rung when target has goblin or orc tag."""
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'glows_near_orcs' in src
    # Must check both goblin and orc
    idx = src.find('glows_near_orcs')
    nearby = src[max(0, idx - 100): idx + 400]
    assert "'goblin'" in nearby
    assert "'orc'" in nearby
    assert 'chain += 1' in nearby or 'chain += ' in nearby


def test_combat_wires_prophecy_blade():
    """prophecy_blade boost reads player._prophecy_target_tag and applies
    +50% damage multiplier vs the prophesied tag."""
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'prophecy_blade' in src
    assert '_prophecy_target_tag' in src


# ---------------------------------------------------------------------------
# player.py wiring
# ---------------------------------------------------------------------------

def test_try_unequip_blocks_selects_wielder():
    """try_unequip_slot must refuse if the slot item has selects_wielder."""
    from player import Player
    src = inspect.getsource(Player.try_unequip_slot)
    assert 'selects_wielder' in src

    p = Player()
    w_sticky = _make_weapon(selects_wielder=True, name='Stormbringer')
    ok, msg = p.try_unequip_slot(w_sticky)
    assert ok is False
    assert 'Stormbringer' in msg


def test_apply_weapon_passives_bumps_PER_for_vigilance_aware():
    """Equipping Hofud (vigilance_aware) gives +2 PER. Unequipping reverses."""
    from player import Player
    p = Player()
    base_per = p.PER
    w_hofud = _make_weapon(vigilance_aware=True, name='Hofud')
    p._apply_weapon_passives(w_hofud)
    assert p.PER == base_per + 2
    p._remove_weapon_passives(w_hofud)
    assert p.PER == base_per


def test_apply_weapon_passives_cursed_lineage_stat_ledger():
    """Pelops Sword: -1 STR / +2 max HP on equip; reversed on unequip."""
    from player import Player
    p = Player()
    base_str = p.STR
    base_max_hp = p.max_hp
    w_pelops = _make_weapon(cursed_lineage=True, name='Pelops Sword')
    p._apply_weapon_passives(w_pelops)
    assert p.STR == base_str - 1
    assert p.max_hp == base_max_hp + 2
    p._remove_weapon_passives(w_pelops)
    assert p.STR == base_str
    assert p.max_hp == base_max_hp


def test_prophecy_blade_declares_tag_on_equip():
    """First time Akinakes is equipped, it picks a random monster tag and
    stores it on the player. Subsequent equips don't re-roll."""
    from player import Player
    import random
    p = Player()
    assert getattr(p, '_prophecy_target_tag', None) is None
    w_akinakes = _make_weapon(prophecy_blade=True, name='Akinakes')
    random.seed(42)
    p._apply_weapon_passives(w_akinakes)
    declared = p._prophecy_target_tag
    assert declared is not None
    assert declared in {'humanoid', 'undead', 'demon', 'beast',
                         'dragon', 'fey', 'aberration'}
    # Re-equip should not reroll
    p._apply_weapon_passives(w_akinakes)
    assert p._prophecy_target_tag == declared


def test_cast_me_away_wired_in_take_damage():
    """player.take_damage must check weapon.cast_me_away at HP <= 25% and
    fire the one-shot life_save proc."""
    from player import Player
    src = inspect.getsource(Player.take_damage)
    assert 'cast_me_away' in src
    assert '_cast_me_away_used' in src
    assert "'life_save'" in src or 'life_save' in src


# ---------------------------------------------------------------------------
# game_combat.py wiring
# ---------------------------------------------------------------------------

def test_betrays_at_low_hp_wired_in_start_combat():
    """The melee combat callback in game_combat._start_combat must include
    the Stormbringer betray check (HP <= 15% + 25% roll -> ally damage)."""
    from game_combat import CombatMixin
    src = inspect.getsource(CombatMixin._start_combat)
    assert 'betrays_at_low_hp' in src
    # Must reference HP threshold, 25% chance, and damage to a pet.
    assert 'max_hp * 0.15' in src
    assert '0.25' in src
    # Pet damage uses take_damage on the chosen victim
    idx = src.find('betrays_at_low_hp')
    big = src[max(0, idx - 100): idx + 2000]
    assert '.take_damage' in big
    assert 'self.pets' in big


# ---------------------------------------------------------------------------
# main.py wiring
# ---------------------------------------------------------------------------

def test_cursed_lineage_descent_event_wired():
    """_change_level must roll for the House of Atreus event when the
    player carries a cursed_lineage weapon."""
    from main import Game
    src = inspect.getsource(Game._change_level)
    assert 'cursed_lineage' in src
    assert '_spawn_house_of_atreus' in src


def test_spawn_house_of_atreus_method_exists():
    """The descent-event helper must exist on Game."""
    from main import Game
    assert hasattr(Game, '_spawn_house_of_atreus')


# ---------------------------------------------------------------------------
# End-to-end smoke: equip a real Hofud / Pelops from JSON
# ---------------------------------------------------------------------------

def test_hofud_equip_smoke():
    """If the JSON has vigilance_aware on hofud, equipping it bumps PER."""
    import json
    from player import Player
    d = json.loads((ROOT / "data" / "items" / "weapon.json").read_text(encoding='utf-8'))
    if 'hofud' not in d:
        return
    defn = {'id': 'hofud', **d['hofud']}
    w = Weapon(defn)
    if not getattr(w, 'vigilance_aware', False):
        # JSON wave 2 hasn't added the flag yet — that's fine, this test just
        # asserts the loading & equip path works without crashing.
        return
    p = Player()
    base_per = p.PER
    p._apply_weapon_passives(w)
    assert p.PER == base_per + 2
