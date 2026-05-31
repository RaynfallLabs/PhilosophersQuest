"""Engine wave 6 (2026-05-30): the remaining lore mechanics from the
2026-05-30 armor/accessory audits, now wired all the way through.

Built-out systems in this wave:
- Rest-site mechanics (altar tile): phalanx_recovery, peace_at_the_forge,
  disguise_at_camp.
- Charge-on-accessory infrastructure (use_charged / charges / max_charges)
  exposed in the power menu: Lyre of Orpheus, Hand of Glory.
- Rotating-subject chain bonus (Torque of Lugh, Hamsa Hand) — picks one
  subject per floor and grants +3s on its quizzes.
- Activated dash + bribe via the power menu: Seven-League Step (boots),
  Gilgamesh's Bribe (helm).
- Small per-item procs: atlantean_resonance, royal_burial, amazon_charge,
  purity, dragonslayer monster_tag_chain_bonus, ring_of_pythia identify
  timer, ring_of_eluned auto-invis, ring_of_hypatia shielded burst,
  ring_of_gyges karma penalty.
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from items import Accessory


def _acc(**kw):
    defn = {
        'id': 'a', 'name': 'a', 'symbol': '=',
        'color': [255, 255, 255], 'weight': 0.5,
        'item_class': 'accessory', 'slot': 'ring',
    }
    defn.update(kw)
    return Accessory(defn)


# ---------------------------------------------------------------------------
# New Accessory fields load
# ---------------------------------------------------------------------------

def test_loads_use_charged():
    a = _acc(use_charged=True, charges=3, max_charges=3)
    assert a.use_charged is True
    assert a.charges == 3
    assert a.max_charges == 3


def test_loads_identify_timer_bonus():
    assert _acc(identify_timer_bonus=2).identify_timer_bonus == 2


def test_loads_auto_invisible_at_low_hp():
    assert _acc(auto_invisible_at_low_hp=True).auto_invisible_at_low_hp is True


def test_loads_protected_when_surrounded():
    assert _acc(protected_when_surrounded=True).protected_when_surrounded is True


def test_loads_gyges_invisible_attack_karma():
    assert _acc(gyges_invisible_attack_karma=True).gyges_invisible_attack_karma is True


def test_loads_monster_tag_chain_bonus():
    a = _acc(monster_tag_chain_bonus={"dragon": 1})
    assert a.monster_tag_chain_bonus == {"dragon": 1}


def test_loads_rotating_subject_chain_cap():
    pool = ["math", "geography"]
    a = _acc(rotating_subject_chain_cap=pool)
    assert a.rotating_subject_chain_cap == pool


# ---------------------------------------------------------------------------
# Hook-site wiring (source-presence)
# ---------------------------------------------------------------------------

def _src(*modules):
    out = []
    for m in modules:
        out.append((ROOT / "src" / f"{m}.py").read_text(encoding='utf-8'))
    return "\n".join(out)


def test_main_wires_rest_site_mechanics():
    s = _src('main')
    assert 'phalanx_recovery' in s
    assert 'peace_at_the_forge' in s
    assert 'disguise_at_camp' in s


def test_main_wires_rotating_subject():
    s = _src('main')
    assert 'rotating_subject_chain_cap' in s
    assert '_rotating_chain_subject' in s


def test_main_wires_atlantean_resonance():
    s = _src('main')
    assert 'atlantean_resonance' in s


def test_main_wires_eluned_and_hypatia():
    s = _src('main')
    assert 'auto_invisible_at_low_hp' in s
    assert 'protected_when_surrounded' in s


def test_main_wires_amazon_charge_counter():
    s = _src('main')
    assert 'amazon_charge' in s
    assert '_straight_line_steps' in s


def test_combat_wires_amazon_charge_damage():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'amazon_charge' in src
    assert '_amazon_charge_armed' in src


def test_combat_wires_dragonslayer_tag_bonus():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'monster_tag_chain_bonus' in src


def test_combat_wires_gyges_karma():
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'gyges_invisible_attack_karma' in src


def test_game_menus_wires_seven_league_step():
    import game_menus
    assert hasattr(game_menus.MenuMixin, '_activate_seven_league_step')


def test_game_menus_wires_gold_offering():
    import game_menus
    assert hasattr(game_menus.MenuMixin, '_activate_gold_offering')


def test_game_menus_wires_accessory_charges():
    import game_menus
    assert hasattr(game_menus.MenuMixin, '_activate_accessory_charge')


def test_player_get_quiz_extra_seconds_wires_pythia():
    from player import Player
    src = inspect.getsource(Player.get_quiz_extra_seconds)
    assert 'identify_timer_bonus' in src
    assert 'philosophy' in src


def test_player_get_quiz_extra_seconds_wires_rotating():
    from player import Player
    src = inspect.getsource(Player.get_quiz_extra_seconds)
    assert '_rotating_chain_subject' in src


def test_bones_wires_royal_burial():
    s = _src('bones')
    assert 'royal_burial' in s
    assert 'preserved' in s


def test_player_apply_equip_wires_purity():
    from player import Player
    src = inspect.getsource(Player._apply_equip)
    assert 'purity' in src


# ---------------------------------------------------------------------------
# JSON-side: items carry the new flags
# ---------------------------------------------------------------------------

ACCESSORY = json.loads((ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
ARMOR = json.loads((ROOT / "data" / "items" / "armor.json").read_text(encoding='utf-8'))


def test_lyre_of_orpheus_has_charges():
    l = ACCESSORY['lyre_of_orpheus']
    assert l['use_charged'] is True
    assert l['charges'] == 3
    assert l['max_charges'] == 3


def test_hand_of_glory_has_charges():
    h = ACCESSORY['hand_of_glory']
    assert h['use_charged'] is True
    assert h['charges'] == 3
    assert h['max_charges'] == 3


def test_torque_of_lugh_has_rotating_pool():
    """Per the bug-bash balance audit (agent a4dd), the original 10-subject
    rotation was too broad — the subject filter never bit. Trimmed to 6."""
    t = ACCESSORY['torque_of_lugh']
    assert len(t['rotating_subject_chain_cap']) == 6


def test_hamsa_hand_has_three_faiths():
    h = ACCESSORY['hamsa_hand']
    assert set(h['rotating_subject_chain_cap']) == {'theology', 'history', 'grammar'}


def test_orichalcum_has_atlantean_resonance():
    assert ARMOR['orichalcum_breastplate']['atlantean_resonance'] == 30


def test_ring_of_pythia_has_identify_timer():
    assert ACCESSORY['ring_of_pythia']['identify_timer_bonus'] == 2


def test_ring_of_eluned_has_auto_invis():
    assert ACCESSORY['ring_of_eluned']['auto_invisible_at_low_hp'] is True


def test_ring_of_hypatia_has_protected():
    assert ACCESSORY['ring_of_hypatia']['protected_when_surrounded'] is True


def test_ring_of_gyges_has_karma_flag():
    assert ACCESSORY['ring_of_gyges']['gyges_invisible_attack_karma'] is True


def test_dragonslayer_ring_has_dragon_bonus():
    d = ACCESSORY['dragonslayer_ring']
    assert d['monster_tag_chain_bonus'].get('dragon', 0) >= 1


# ---------------------------------------------------------------------------
# Behavior smoke
# ---------------------------------------------------------------------------


def test_purity_uncurses_equipped_item_on_equip():
    """Galahad helm uncurses an item at the moment of equip."""
    from items import Armor
    from player import Player

    # Real Player; install Galahad-like helm in slot 0.
    p = Player()
    p.armor_slots[0] = Armor({
        'id': 'galahad_test', 'name': 'galahad helm',
        'symbol': '[', 'color': [255, 255, 255], 'weight': 1.0,
        'item_class': 'armor', 'slot': 'head', 'ac_bonus': 2, 'tier': 4,
        'purity': True,
    })

    target = Armor({
        'id': 'plate_test', 'name': 'cursed plate',
        'symbol': '[', 'color': [255, 255, 255], 'weight': 1.0,
        'item_class': 'armor', 'slot': 'body', 'ac_bonus': 3, 'tier': 1,
    })
    target.buc = 'cursed'
    p._apply_equip(target)
    assert target.buc == 'uncursed'


def test_charges_decrement_smoke():
    """Direct decrement of charges still works (manual decrement path)."""
    a = _acc(use_charged=True, charges=3, max_charges=3)
    a.charges -= 1
    assert a.charges == 2
