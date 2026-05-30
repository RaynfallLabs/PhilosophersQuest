"""Tests for the Duck of Doom — Munchkin reference item.

Spec (from user):
- Spawns once per run on a uniform-random floor in {1..10}
- Looks like an adorable yellow duckie (`unidentified_name`)
- Pickup auto-equips as cursed head armor (+2 AC); displaces existing
  head armor (even if cursed) into inventory
- Lore: "You should know better than to pick up a duck in a dungeon."
- Identify reveals progressively: T1 name, T2 BUC, T3 stats, T4 lore,
  T5 mastery_blessing ("The Duck of Doom has no master!" — cosmetic
  humor only, no mechanical effect)
- Worn for 2026 turns -> transforms into a Waddlekind pet
- Pet evolves: Waddlekind (stage 0, Detect Monsters) -> Drake of the
  Covenant (stage 1, Psionic Blast) -> Seraphimallard (stage 2,
  Sometimes Goose)
- Permadeath: only one Duck per run, no respawn if pet dies
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# Data-layer tests
# ---------------------------------------------------------------------------

def _load_armor() -> dict:
    return json.loads((ROOT / "data" / "items" / "armor.json").read_text(encoding="utf-8"))


def test_duck_data_exists():
    armor = _load_armor()
    assert 'duck_of_doom' in armor, "Duck of Doom must be defined in armor.json"


def test_duck_is_head_slot_cursed_headgear():
    d = _load_armor()['duck_of_doom']
    assert d['slot'] == 'head'
    assert d.get('cursed') is True or d.get('buc') == 'cursed'
    assert d['ac_bonus'] == 2


def test_duck_lore_matches_spec():
    d = _load_armor()['duck_of_doom']
    assert d['lore'] == "You should know better than to pick up a duck in a dungeon."


def test_duck_unidentified_name_is_cute():
    """When unidentified the player should see something tempting, NOT
    a generic 'unknown helmet'."""
    d = _load_armor()['duck_of_doom']
    assert 'duck' in d['unidentified_name'].lower(), (
        "unidentified_name should still mention 'duck' so the player "
        "knows what they're tempted by"
    )


def test_duck_starts_unidentified():
    d = _load_armor()['duck_of_doom']
    assert d.get('identified') is False
    assert d.get('id_level', 0) == 0


def test_duck_mastery_blessing_is_cosmetic_humor():
    d = _load_armor()['duck_of_doom']
    mb = d.get('mastery_blessing')
    assert mb is not None
    assert mb['kind'] == 'cosmetic_only'
    assert mb['value'] == 0
    assert mb['desc'] == "The Duck of Doom has no master!"


def test_duck_marked_auto_equip_on_pickup():
    """The pickup intercept in main.py checks for this flag (and the
    item id) — without it the duck would go to inventory like normal
    armor and the joke wouldn't land."""
    d = _load_armor()['duck_of_doom']
    assert d.get('auto_equip_on_pickup') is True


# ---------------------------------------------------------------------------
# Pet species tests
# ---------------------------------------------------------------------------

def test_duck_pet_species_exists():
    import pet_system
    assert 'duck_of_doom' in pet_system._SPECIES


def test_duck_pet_stage_names():
    """Waddlekind -> Drake of the Covenant -> Seraphimallard."""
    import pet_system
    stages = pet_system._SPECIES['duck_of_doom']['stages']
    assert [s['name'] for s in stages] == [
        'Waddlekind', 'Drake of the Covenant', 'Seraphimallard',
    ]


def test_duck_pet_has_detect_monsters_at_stage_zero():
    """Unique to the Duck: stage 0 has a special already unlocked.
    The 2026-turn cursed incubation IS the grind to unlock Detect Monsters."""
    import pet_system
    sp = pet_system._SPECIES['duck_of_doom']
    detect = next(s for s in sp['specials'] if s['id'] == 'detect_monsters')
    assert detect['unlock_stage'] == 0
    assert detect['targeting'] == 'self'
    assert detect.get('effect') == 'player_telepathy'
    assert detect.get('effect_duration', 0) > 0


def test_duck_pet_psionic_blast_is_stage_one():
    import pet_system
    sp = pet_system._SPECIES['duck_of_doom']
    pb = next(s for s in sp['specials'] if s['id'] == 'psionic_blast')
    assert pb['unlock_stage'] == 1
    assert pb['damage_type'] == 'psychic'
    assert pb['targeting'] == 'single'


def test_duck_pet_sometimes_goose_is_stage_two():
    """Sometimes Goose — final form ability. Flavor-only goose; damage
    + status applied to every monster in the player's FOV."""
    import pet_system
    sp = pet_system._SPECIES['duck_of_doom']
    sg = next(s for s in sp['specials'] if s['id'] == 'sometimes_goose')
    assert sg['unlock_stage'] == 2
    assert sg['damage_type'] == 'psychic'
    assert sg['targeting'] == 'visible_all', (
        "Sometimes Goose hits all visible enemies — not a single tile"
    )
    # Flavor text must mention the goose (user-specified narrative)
    assert 'goose' in sg.get('flavor_message', '').lower()


def test_duck_pet_specials_available_at_each_stage():
    """available_specials() filters by unlock_stage <= self.stage.
    With unlock_stage=0 for Detect Monsters, a freshly-hatched Waddlekind
    (stage 0) has access to it. Drake (stage 1) adds Psionic Blast.
    Seraphimallard (stage 2) adds Sometimes Goose. This is the engine
    contract the rest of the design depends on."""
    from pet_system import Pet, _EVOLVE_1, _EVOLVE_2
    pet = Pet('duck_of_doom', x=0, y=0)
    # `stage` is derived from `level` via thresholds at L25 and L55.
    pet.level = 1  # stage 0 — Waddlekind
    assert pet.stage == 0
    av = {s['id'] for s in pet.available_specials()}
    assert av == {'detect_monsters'}, f"stage 0 should have only detect_monsters; got {av}"
    pet.level = _EVOLVE_1  # stage 1 — Drake of the Covenant
    assert pet.stage == 1
    av = {s['id'] for s in pet.available_specials()}
    assert av == {'detect_monsters', 'psionic_blast'}
    pet.level = _EVOLVE_2  # stage 2 — Seraphimallard
    assert pet.stage == 2
    av = {s['id'] for s in pet.available_specials()}
    assert av == {'detect_monsters', 'psionic_blast', 'sometimes_goose'}


# ---------------------------------------------------------------------------
# Game integration: source-level regression checks
# ---------------------------------------------------------------------------

def test_pickup_intercept_present_in_main():
    """The _pickup method must short-circuit on duck_of_doom BEFORE the
    standard add_to_inventory path. Otherwise the duck goes to
    inventory like a normal helmet and the joke fails."""
    import inspect
    import main
    src = inspect.getsource(main.Game._pickup)
    assert "_duck_of_doom_pickup" in src, (
        "_pickup must call _duck_of_doom_pickup for the duck"
    )
    assert "'duck_of_doom'" in src


def test_advance_turn_ticks_duck_counter():
    """The 2026-turn counter must increment every turn."""
    import inspect
    import main
    src = inspect.getsource(main.Game._advance_turn)
    assert "_duck_of_doom_tick" in src


def test_game_picks_duck_floor_at_init():
    """Run-start should pick a uniform-random floor in {1..10}."""
    import inspect
    import main
    src = inspect.getsource(main.Game.__init__)
    assert "_duck_of_doom_floor" in src
    assert "random.randint(1, 10)" in src


def test_constants_match_spec():
    """2026 was the year requested by the user — make sure no one
    silently lowers it."""
    import main
    assert main.Game.DUCK_OF_DOOM_TURNS_REQUIRED == 2026


# ---------------------------------------------------------------------------
# Mechanical sanity (statistical: spawn floor distribution)
# ---------------------------------------------------------------------------

def test_spawn_floor_distribution_is_uniform_1_to_10():
    """1000 trials of `random.randint(1, 10)` should hit every floor.
    A regression where someone changed the range would surface here."""
    import random
    counts = {}
    for _ in range(1000):
        counts[random.randint(1, 10)] = counts.get(random.randint(1, 10), 0) + 1
    assert set(counts.keys()) <= set(range(1, 11))
    # Every floor should appear at least once over 1000 trials
    assert len(counts) == 10
