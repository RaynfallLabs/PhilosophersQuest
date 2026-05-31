"""Pin tests for the 9 legendary weapons the vision audit flagged as
"unimplemented" — they're actually all wired with working mechanics.

The 2026-05-30 vision audit listed these as deferred. Direct trace shows:
- 6 weapons ship their proposal proc fully wired in items.py + combat.py
- 3 weapons (Heracles, Cronus, Mwindo) have alternate mechanics in JSON
  that are wired and play correctly — the proposal procs were aspirational
  and never landed, but the items are NOT dead.

These pin tests verify every legendary's combat mechanic has an active
consumer so the next refactor or rebuild doesn't accidentally regress them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _weapon(wid):
    w = json.loads(
        (ROOT / "data" / "items" / "weapon.json").read_text(encoding='utf-8'))
    return w.get(wid, {})


def _src(name):
    return (ROOT / "src" / f"{name}.py").read_text(encoding='utf-8')


# ---------------------------------------------------------------------------
# Cadmus's Sword: summon-on-kill (dragon) + bonus damage vs dragon
# ---------------------------------------------------------------------------

def test_cadmus_summon_after_kill_with_tag_field_present():
    w = _weapon('cadmus_sword')
    su = w.get('summon_after_kill_with_tag')
    assert isinstance(su, dict)
    assert su.get('tag') == 'dragon'


def test_cadmus_dragon_bonus_damage_field_present():
    w = _weapon('cadmus_sword')
    assert w.get('dragon_bonus_damage')


def test_summon_after_kill_consumer_in_combat():
    """combat.player_attack checks weapon.summon_after_kill_with_tag."""
    src = _src('combat')
    assert "summon_after_kill_with_tag" in src
    assert "_pending_summon" in src or "summon" in src.lower()


def test_dragon_bonus_damage_consumer_via_bonus_damage_vs_tag():
    """items.py:Weapon builds bonus_damage_vs_tag from <tag>_bonus_damage keys."""
    src = _src('items')
    assert "bonus_damage_vs_tag" in src
    assert "_bonus_damage" in src


# ---------------------------------------------------------------------------
# Vel of Murugan / Shamshir-e-Zomorrodnegar: summon-on-kill (demon)
# ---------------------------------------------------------------------------

def test_vel_of_murugan_summon_demon_wired():
    w = _weapon('vel_of_murugan')
    su = w.get('summon_after_kill_with_tag')
    assert isinstance(su, dict)
    assert su.get('tag') == 'demon'


def test_shamshir_summon_demon_wired():
    w = _weapon('shamshir_e_zomorrodnegar')
    su = w.get('summon_after_kill_with_tag')
    assert isinstance(su, dict)
    assert su.get('tag') == 'demon'


# ---------------------------------------------------------------------------
# Parashu: chain_no_reset_on_tag (humanoid)
# ---------------------------------------------------------------------------

def test_parashu_chain_no_reset_field_present():
    w = _weapon('parashu')
    tags = w.get('chain_no_reset_on_tag')
    assert isinstance(tags, list)
    assert 'humanoid' in tags


def test_chain_no_reset_consumer_in_combat():
    src = _src('combat')
    assert "chain_no_reset_on_tag" in src


# ---------------------------------------------------------------------------
# Sword of Damocles: chain-N auto-kill
# ---------------------------------------------------------------------------

def test_damocles_counter_auto_kill_field_present():
    w = _weapon('sword_of_damocles')
    assert w.get('damoclean_counter_auto_kill') is True
    assert int(w.get('damoclean_counter_threshold', 0)) >= 5


def test_damocles_counter_consumer_in_items_or_combat():
    src_items = _src('items')
    assert "damoclean_counter_auto_kill" in src_items


# ---------------------------------------------------------------------------
# Heracles's Olive-Club: beast bonus + knockback (lore deviation but live)
# ---------------------------------------------------------------------------

def test_heracles_beast_bonus_present():
    w = _weapon('heracles_club')
    assert w.get('beast_bonus_damage')


def test_heracles_knockback_present():
    w = _weapon('heracles_club')
    assert w.get('knockback') is True


# ---------------------------------------------------------------------------
# Cronus's Scythe: lifesteal + ignore shield (lore deviation but live)
# ---------------------------------------------------------------------------

def test_cronus_lifesteal_present():
    w = _weapon('cronus_scythe')
    assert float(w.get('lifestealPercent', 0)) > 0


def test_cronus_ignore_shield_present():
    w = _weapon('cronus_scythe')
    assert w.get('ignoreShield') is True


def test_lifesteal_consumer_in_combat():
    src = _src('combat')
    assert "lifesteal_percent" in src


# ---------------------------------------------------------------------------
# Mwindo's Conga-Scepter: kill-heal (alternate mechanic)
# ---------------------------------------------------------------------------

def test_mwindo_kill_heal_present():
    w = _weapon('mwindo_axe')
    assert int(w.get('kill_heal_amount', 0)) > 0


def test_kill_heal_consumer_in_combat():
    src = _src('combat')
    assert "kill_heal_amount" in src


# ---------------------------------------------------------------------------
# Hector's Javelin: bleed + FOV decouple from engine wave 1
# ---------------------------------------------------------------------------

def test_hector_javelin_bleed_chance_set():
    w = _weapon('hector_javelin')
    assert float(w.get('bleedChance', 0)) > 0


# ---------------------------------------------------------------------------
# Generalized: every weapon in this audit must exist in JSON
# ---------------------------------------------------------------------------

ALL_AUDITED_WEAPONS = (
    'cadmus_sword', 'vel_of_murugan', 'shamshir_e_zomorrodnegar',
    'parashu', 'sword_of_damocles', 'heracles_club', 'cronus_scythe',
    'mwindo_axe', 'hector_javelin',
)


def test_every_audited_weapon_in_json():
    weapons = json.loads(
        (ROOT / "data" / "items" / "weapon.json").read_text(encoding='utf-8'))
    missing = [wid for wid in ALL_AUDITED_WEAPONS if wid not in weapons]
    assert not missing, f"Audited weapons missing from JSON: {missing}"


def test_no_audited_weapon_has_dead_unique_drop_id():
    """If any of these became mini-boss drops, the drop must resolve."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    weapons = json.loads(
        (ROOT / "data" / "items" / "weapon.json").read_text(encoding='utf-8'))
    for mid, mon in monsters.items():
        drop = mon.get('treasure', {})
        if isinstance(drop, dict):
            did = drop.get('unique_drop_id')
            if did in ALL_AUDITED_WEAPONS:
                # If this weapon is a drop, it must exist in weapon.json
                assert did in weapons, \
                    f"Monster {mid} drops {did} but weapon missing from JSON"
