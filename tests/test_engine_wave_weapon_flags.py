"""Engine wave 2026-05-30: previously-inert Weapon JSON flags now wired.

Per the unique-weapons audit (proposals/legendary_uniques/weapons.md vs
data/items/weapon.json), ~30 weapons had lore-promised mechanics that were
declared in JSON but had no consumer in src/. This commit wakes them up.

Tests check:
1. New fields are loaded on Weapon
2. Consumer code exists in combat.player_attack / player.take_damage
3. Backward compatibility — existing wired flags still work
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from items import Weapon


def _make_weapon(**overrides):
    """Build a minimal weapon defn for testing flag loading."""
    defn = {
        'id': 'test_weapon', 'name': 'test weapon',
        'symbol': '(', 'color': [255, 255, 255], 'weight': 1.0,
        'item_class': 'weapon', 'class': 'sword',
        'base_damage': 5, 'damage_types': ['slash'],
    }
    defn.update(overrides)
    return Weapon(defn)


# ---------------------------------------------------------------------------
# Field loading
# ---------------------------------------------------------------------------

def test_weapon_loads_effects_block():
    """effects: {status, effect_chance, effect_duration} now on Weapon
    (was only on Accessory before)."""
    w = _make_weapon(effects={
        'status': 'burning', 'effect_chance': 0.4, 'effect_duration': 5
    })
    assert w.effects == {'status': 'burning', 'effect_chance': 0.4, 'effect_duration': 5}

    # Default: empty dict
    w2 = _make_weapon()
    assert w2.effects == {}


def test_weapon_loads_effective_against_array():
    """Weapon-side effective_against array (lore-tagged anti-X)."""
    w = _make_weapon(effective_against=['demon', 'undead'])
    assert w.effective_against == ['demon', 'undead']

    w2 = _make_weapon()
    assert w2.effective_against == []


def test_weapon_loads_per_tag_bonus_damage_dice():
    """{dragon|beast|undead|goblin|demon|fey|giant|troll}_bonus_damage
    aggregate into a single dict at load time."""
    w = _make_weapon(
        dragon_bonus_damage='1d8',
        undead_bonus_damage='1d6',
        goblin_bonus_damage='1d4',
    )
    assert w.bonus_damage_vs_tag == {
        'dragon': '1d8', 'undead': '1d6', 'goblin': '1d4'
    }

    w2 = _make_weapon()
    assert w2.bonus_damage_vs_tag == {}


def test_weapon_loads_undead_multiplier_legacy_flag():
    """Anduril's legacy undead_bonus numeric multiplier."""
    w = _make_weapon(undead_bonus=2.5)
    assert w.undead_multiplier == 2.5

    w2 = _make_weapon()
    assert w2.undead_multiplier == 1.0


def test_weapon_loads_freeze_chance():
    """Aiglos's freeze proc chance."""
    w = _make_weapon(freeze_chance=0.25)
    assert w.freeze_chance == 0.25
    # camelCase variant accepted
    w2 = _make_weapon(freezeChance=0.4)
    assert w2.freeze_chance == 0.4


def test_weapon_loads_first_blood_bonus():
    """Atalanta's first-blood flag."""
    w = _make_weapon(first_blood_bonus=True)
    assert w.first_blood_bonus is True
    w2 = _make_weapon()
    assert w2.first_blood_bonus is False


def test_weapon_loads_cannot_miss():
    """Gungnir's never-miss flag."""
    w = _make_weapon(cannot_miss=True)
    assert w.cannot_miss is True
    w2 = _make_weapon()
    assert w2.cannot_miss is False


def test_weapon_loads_wielder_fire_immunity():
    """Aiglos's fire-immunity-while-equipped flag."""
    w = _make_weapon(wielder_fire_immunity=True)
    assert w.wielder_fire_immunity is True
    w2 = _make_weapon()
    assert w2.wielder_fire_immunity is False


# ---------------------------------------------------------------------------
# Consumer code exists (source-regression)
# ---------------------------------------------------------------------------

def test_combat_wires_cannot_miss():
    """combat.player_attack must promote chain 0 to 1 when weapon has
    cannot_miss flag (same shape as the existing guaranteed_hit handler)."""
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'cannot_miss' in src
    # Must reference the promotion (chain = 1)
    # Just check the pattern is present near the cannot_miss line
    cannot_miss_idx = src.find('cannot_miss')
    nearby = src[max(0, cannot_miss_idx - 200): cannot_miss_idx + 200]
    assert 'chain' in nearby and ('= 1' in nearby or '=1' in nearby)


def test_combat_wires_weapon_effective_against():
    """combat.player_attack must apply weapon-side effective_against array
    as a damage multiplier (not just material-side)."""
    import combat
    src = inspect.getsource(combat.player_attack)
    assert "getattr(weapon, 'effective_against'" in src \
        or 'weapon.effective_against' in src


def test_combat_wires_bonus_damage_vs_tag():
    """combat.player_attack must roll bonus_damage_vs_tag dice and add to
    damage when target matches the tag."""
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'bonus_damage_vs_tag' in src
    # Must use _tag_match
    assert '_tag_match' in src


def test_combat_wires_first_blood_bonus():
    """combat.player_attack must apply +50% damage on chain 1 vs full-HP
    target when first_blood_bonus is set."""
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'first_blood_bonus' in src
    # Must check chain == 1 AND monster.hp >= monster.max_hp (Atalanta logic)
    fbb_idx = src.find('first_blood_bonus')
    nearby = src[max(0, fbb_idx - 100): fbb_idx + 400]
    assert 'chain == 1' in nearby
    assert 'max_hp' in nearby


def test_combat_wires_freeze_proc():
    """combat.player_attack must add a freeze proc when weapon.freeze_chance > 0."""
    import combat
    src = inspect.getsource(combat.player_attack)
    assert "freeze_chance" in src
    # Must apply 'frozen' status
    assert "'frozen'" in src


def test_combat_wires_effects_block():
    """combat.player_attack must read weapon.effects and roll effect_chance
    to apply effect_duration of the status."""
    import combat
    src = inspect.getsource(combat.player_attack)
    # The block uses _wfx variables — check key references
    assert "getattr(weapon, 'effects'" in src
    assert 'effect_chance' in src
    assert 'effect_duration' in src


def test_player_wires_wielder_fire_immunity():
    """player.take_damage must block fire when wielded weapon has
    wielder_fire_immunity (Aiglos)."""
    from player import Player
    src = inspect.getsource(Player.take_damage)
    assert 'wielder_fire_immunity' in src


# ---------------------------------------------------------------------------
# End-to-end smoke: Atalanta loads cleanly with new fields
# ---------------------------------------------------------------------------

def test_atalanta_bow_first_blood_bonus_loads():
    """Smoke test: load Atalanta's Bow from JSON and verify the
    first_blood_bonus flag actually populates."""
    import json
    p = ROOT / "data" / "items" / "weapon.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    if 'atalanta_bow' not in d:
        return  # weapon not present, skip
    defn = {'id': 'atalanta_bow', **d['atalanta_bow']}
    w = Weapon(defn)
    # The JSON has first_blood_bonus: true per the audit. After the engine
    # wave loads it onto Weapon, this assertion passes (it would have
    # silently been ignored before).
    assert w.first_blood_bonus is True, (
        "atalanta_bow.json declares first_blood_bonus — after the engine "
        "wave (2026-05-30) the field must load onto the Weapon instance"
    )


def test_gungnir_cannot_miss_loads():
    """Smoke test: gungnir defines cannot_miss in its mastery proposal but
    weapons.md says the flag should be on the weapon. If JSON has it,
    confirm it loads."""
    import json
    p = ROOT / "data" / "items" / "weapon.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    if 'gungnir' not in d:
        return
    defn = {'id': 'gungnir', **d['gungnir']}
    w = Weapon(defn)
    # JSON may or may not have cannot_miss yet — the wave-2 JSON pass adds it.
    # This test just confirms the field LOADS without crashing.
    assert hasattr(w, 'cannot_miss')
    assert isinstance(w.cannot_miss, bool)
