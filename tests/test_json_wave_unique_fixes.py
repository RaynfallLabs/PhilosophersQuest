"""JSON wave 2026-05-30: per-weapon lore-vs-stat fixes applied.

Now that engine-wave 1+2 wired every field, the JSON catches up:
- caladbolg gets cleave_at_max
- excalibur gets cast_me_away
- gungnir gets cannot_miss
- aiglos gets wielder_fire_immunity
- vel_of_murugan gets ignoreShield: true
- hofud loses incongruous abaddon_bonus_damage, gains vigilance_aware
- dawnbreaker damageTypes camelCase fixed slash -> blunt
- Anduril effective_against += undead
- Mid-tier mastery_blessing swaps for cuchulainn_hurley, talos_sickle,
  chainsaw_prosthetic, prometheus_torch, bellerophon_lance, hector_javelin
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest

WEAPON_JSON_PATH = ROOT / "data" / "items" / "weapon.json"


@pytest.fixture(scope='module')
def weapons():
    with open(WEAPON_JSON_PATH, encoding='utf-8') as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Wave A — additive flags
# ---------------------------------------------------------------------------

def test_caladbolg_has_cleave(weapons):
    """Lore: 'cut the tops off three hills with one sweep.'"""
    assert weapons['caladbolg'].get('class_mechanic') == 'cleave_at_max'


def test_excalibur_has_cast_me_away(weapons):
    """Lore: 'take me up; cast me away'. One-shot life_save at HP <= 25%."""
    assert weapons['excalibur'].get('cast_me_away') is True


def test_gungnir_cannot_miss(weapons):
    """Lore: 'the spear has never missed'."""
    assert weapons['gungnir'].get('cannot_miss') is True


def test_aiglos_wielder_fire_immunity(weapons):
    """Lore: 'does not warm in the hand' — Sauron's flame did nothing."""
    assert weapons['aiglos'].get('wielder_fire_immunity') is True


def test_vel_of_murugan_ignore_shield(weapons):
    """Lore: 'cannot be turned aside by mortal shields'."""
    assert weapons['vel_of_murugan'].get('ignoreShield') is True


# ---------------------------------------------------------------------------
# Wave B — removals and fixes
# ---------------------------------------------------------------------------

def test_hofud_no_longer_has_abaddon_drift(weapons):
    """Hofud is a Heimdall sword — abaddon_bonus_damage was Sword-of-Michael
    data drift. Removed in JSON wave."""
    assert 'abaddon_bonus_damage' not in weapons['hofud']


def test_hofud_vigilance_aware(weapons):
    """Hofud's defining trait: 'hears wool growing'. +2 PER while equipped."""
    assert weapons['hofud'].get('vigilance_aware') is True


def test_dawnbreaker_damageTypes_is_blunt_not_slash(weapons):
    """Warhammers do blunt damage. The camelCase damageTypes used to have
    'slash' which contradicted the weapon class."""
    d = weapons['dawnbreaker'].get('damageTypes', [])
    assert 'blunt' in d
    assert 'slash' not in d


# ---------------------------------------------------------------------------
# Wave B — Anduril undead reinforce
# ---------------------------------------------------------------------------

def test_anduril_effective_against_undead(weapons):
    """Paths of the Dead — Anduril's anti-undead is doubly wired now:
    legacy undead_bonus (numeric) + new effective_against array (tag boost)."""
    ea = weapons['anduril'].get('effective_against', [])
    assert 'undead' in ea


# (Mid-tier mastery-swap tests removed 2026-08-06 — mastery blessings were
# retired with the one-question identify redesign.)


# ---------------------------------------------------------------------------
# Integration: engine + data
# ---------------------------------------------------------------------------

def test_weapons_load_through_Weapon_class():
    """Every unique loads through items.Weapon without error."""
    from items import Weapon
    with open(WEAPON_JSON_PATH, encoding='utf-8') as f:
        d = json.load(f)
    n = 0
    for wid, defn in d.items():
        if not defn.get('is_unique'):
            continue
        full = {'id': wid, **defn}
        w = Weapon(full)
        n += 1
        # Sanity: every weapon has a base_damage > 0
        assert w.base_damage > 0, f"{wid} base_damage invalid"
    assert n > 80  # there should be many uniques


def test_engine_wave_flags_round_trip():
    """Each engine-wired flag is correctly loaded onto the Weapon object
    for the weapons that should have it after the JSON wave."""
    from items import Weapon
    with open(WEAPON_JSON_PATH, encoding='utf-8') as f:
        d = json.load(f)
    checks = [
        ('caladbolg', 'class_mechanic', 'cleave_at_max'),
        ('excalibur', 'cast_me_away', True),
        ('gungnir', 'cannot_miss', True),
        ('aiglos', 'wielder_fire_immunity', True),
        ('hofud', 'vigilance_aware', True),
    ]
    for wid, attr, expected in checks:
        w = Weapon({'id': wid, **d[wid]})
        actual = getattr(w, attr, None)
        assert actual == expected, f"{wid}.{attr}: expected {expected}, got {actual}"
