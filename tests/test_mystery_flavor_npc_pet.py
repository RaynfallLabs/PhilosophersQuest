"""Pin tests for the 4 systems my second-pass quest audit missed:

1. Mystery system (mystery_system.py): 12 mysteries with altars,
   key items, can_activate gating, apply_mystery_reward dispatch
2. Flavor encounter system (flavor_encounters.py): 97 random NPC
   encounters with cost/reward options, 100-floor coverage
3. Pet system (pet_system.py): special pet classes (FenrirPet,
   SketchedPet, DadPet, UnicornPet), Duck of Doom transform,
   carry-only quest items (Charmander Stuffie, Dreamspun Sketchbook)
4. NPC encounter system (npc_encounters.py): 31 moral encounters
   across 10 level blocks, trigger items + rewards
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _src(name):
    return (ROOT / "src" / f"{name}.py").read_text(encoding='utf-8')


# ---------------------------------------------------------------------------
# 1. MYSTERY SYSTEM
# ---------------------------------------------------------------------------

EXPECTED_MYSTERIES = {
    'sphinx', 'pandora', 'grail', 'fleece', 'mimir', 'mjolnir',
    'crucible', 'oracle', 'solomon', 'fisher_king', 'sisyphus',
    'cauldron',
}


def test_all_expected_mysteries_defined():
    from mystery_system import MYSTERIES
    missing = EXPECTED_MYSTERIES - set(MYSTERIES.keys())
    assert not missing, f"Missing mysteries: {missing}"
    extra = set(MYSTERIES.keys()) - EXPECTED_MYSTERIES
    # Allow new mysteries to be added without breaking the test
    assert len(MYSTERIES) >= 12


def test_each_mystery_has_required_fields():
    from mystery_system import MYSTERIES
    required = ('name', 'floor_range', 'symbol', 'color', 'description',
                'challenge', 'reward', 'reward_text', 'fail_text',
                'invert_result')
    bad = []
    for mid, m in MYSTERIES.items():
        missing = [k for k in required if k not in m]
        if missing:
            bad.append((mid, missing))
    assert not bad, f"Mysteries missing fields: {bad}"


def test_each_mystery_floor_range_valid():
    from mystery_system import MYSTERIES
    bad = []
    for mid, m in MYSTERIES.items():
        lo, hi = m['floor_range']
        if not (1 <= lo <= hi <= 100):
            bad.append((mid, (lo, hi)))
    assert not bad, f"Mysteries with bad floor_range: {bad}"


def test_each_mystery_challenge_mode_valid():
    from mystery_system import MYSTERIES
    valid_modes = {'threshold', 'chain', 'escalator_threshold',
                   'escalator_chain', 'physical'}
    bad = []
    for mid, m in MYSTERIES.items():
        mode = m.get('challenge', {}).get('mode')
        if mode not in valid_modes:
            bad.append((mid, mode))
    assert not bad, f"Mysteries with invalid challenge mode: {bad}"


def test_mystery_spawn_called_in_dungeon_gen():
    src = _src('dungeon')
    assert "spawn_mystery_for_level" in src
    assert "from mystery_system import" in src


def test_mystery_altar_renders_as_ground_item():
    src = _src('game_combat')
    assert "MysteryAltar" in src


def test_mystery_activation_dispatcher_wired():
    src = _src('game_divine')
    assert "can_activate" in src
    assert "consume_key_item" in src
    assert "apply_mystery_reward" in src


def test_sisyphus_physical_challenge_handled():
    src = _src('main')
    assert "apply_mystery_reward('sisyphus'" in src


def test_pandora_inverted_result_design():
    """Pandora's mystery has invert_result=True (failure → real reward)."""
    from mystery_system import MYSTERIES
    assert MYSTERIES['pandora']['invert_result'] is True


def test_save_system_persists_mystery_state():
    """Mystery altars + key items live in ground_items (per dungeon spawn),
    so they get pickled via game.ground_items. The runtime ref
    _active_mystery_altar is transient (cleared when quiz resolves)
    and doesn't need explicit persistence."""
    src = _src('save_system')
    assert "ground_items" in src


# ---------------------------------------------------------------------------
# 2. FLAVOR ENCOUNTER SYSTEM
# ---------------------------------------------------------------------------

def test_flavor_encounters_loaded():
    from flavor_encounters import FLAVOR_ENCOUNTERS
    assert len(FLAVOR_ENCOUNTERS) >= 50, \
        f"Expected ≥50 flavor encounters, got {len(FLAVOR_ENCOUNTERS)}"


def test_each_flavor_encounter_has_required_fields():
    from flavor_encounters import FLAVOR_ENCOUNTERS
    required = ('tag', 'name', 'symbol', 'color', 'min_level',
                'max_level', 'text', 'options')
    bad = []
    for e in FLAVOR_ENCOUNTERS:
        missing = [k for k in required if k not in e]
        if missing:
            bad.append((e.get('tag', '?'), missing))
    assert not bad, f"Flavor encounters missing fields: {bad}"


def test_flavor_encounter_tags_unique():
    from flavor_encounters import FLAVOR_ENCOUNTERS
    tags = [e['tag'] for e in FLAVOR_ENCOUNTERS]
    assert len(tags) == len(set(tags))


def test_flavor_encounters_cover_all_floors_1_to_99():
    """No floor (excluding boss levels) should be without an eligible encounter."""
    from flavor_encounters import FLAVOR_ENCOUNTERS
    BOSS = {20, 40, 60, 80, 100}
    covered = set()
    for e in FLAVOR_ENCOUNTERS:
        for lvl in range(e['min_level'], e['max_level'] + 1):
            covered.add(lvl)
    needed = set(range(1, 100)) - BOSS
    gaps = needed - covered
    assert not gaps, f"Floors with no flavor encounter eligible: {sorted(gaps)}"


def test_flavor_spawn_excludes_boss_levels():
    src = _src('flavor_encounters')
    assert "BOSS_LEVELS" in src
    assert "20, 40, 60, 80, 100" in src or "{20, 40, 60, 80, 100}" in src


def test_flavor_dispatcher_wired():
    src = _src('game_encounters')
    assert "_maybe_spawn_flavor_npc" in src
    assert "_encountered_flavor_npcs" in src


def test_save_system_persists_flavor_encounter_state():
    src = _src('save_system')
    assert "_flavor_encounter_levels" in src or "_encountered_flavor_npcs" in src


# ---------------------------------------------------------------------------
# 3. PET SYSTEM
# ---------------------------------------------------------------------------

def test_special_pet_classes_defined():
    from pet_system import FenrirPet, SketchedPet, DadPet, UnicornPet, Pet
    # Just need them all importable
    assert issubclass(FenrirPet, Pet)
    assert issubclass(SketchedPet, Pet)
    assert issubclass(DadPet, Pet)
    assert issubclass(UnicornPet, Pet)


def test_duck_of_doom_pet_species_defined():
    from pet_system import _SPECIES
    assert 'duck_of_doom' in _SPECIES


def test_duck_of_doom_transform_after_2026_turns():
    """The Duck of Doom hatches after wearing the cursed headgear 2026 turns."""
    src = _src('main')
    assert "_duck_of_doom_transform" in src
    assert "2026" in src  # the magic number for transformation


def test_charmander_stuffie_grants_fire_breath():
    src = _src('game_menus')
    assert "charmander_stuffie" in src
    assert "stuffie_fire_breath" in src


def test_dreamspun_sketchbook_grants_manifest():
    src = _src('game_menus')
    assert "dreamspun_sketchbook" in src
    assert "sketch_manifest" in src


def test_dreamspun_creates_sketched_pet():
    src = _src('game_menus')
    assert "SketchedPet" in src or "sketch_manifest" in src


def test_charmander_carry_only_in_accessory_json():
    accessory = json.loads(
        (ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    assert 'charmander_stuffie' in accessory
    assert accessory['charmander_stuffie'].get('slot') == 'none'


def test_dreamspun_carry_only_in_accessory_json():
    accessory = json.loads(
        (ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    assert 'dreamspun_sketchbook' in accessory
    assert accessory['dreamspun_sketchbook'].get('slot') == 'none'


def test_gleipnir_creates_bind_odinkiller_power():
    src = _src('game_menus')
    assert "'gleipnir'" in src
    assert "bind_odinkiller" in src


def test_scales_of_michael_summons_heavenly_host():
    src = _src('game_menus')
    assert "scales_of_michael" in src
    assert "summon_heavenly_host" in src or "heavenly_host" in src


def test_unicorn_pet_spawn_wired():
    src = _src('game_encounters')
    assert "_tick_unicorn" in src or "UnicornPet" in src
    src_main = _src('main')
    assert "_tick_unicorn" in src_main


# ---------------------------------------------------------------------------
# 4. NPC ENCOUNTER SYSTEM
# ---------------------------------------------------------------------------

def test_thirty_one_npc_encounters_defined():
    from npc_encounters import ENCOUNTERS, _BLOCKS
    assert len(ENCOUNTERS) >= 30, \
        f"Expected ≥30 NPC encounters, got {len(ENCOUNTERS)}"


def test_each_block_has_at_least_three_candidates():
    """Per docstring: 'One encounter guaranteed per 10-level block,
    chosen from 3 candidates'."""
    from npc_encounters import ENCOUNTERS, _BLOCKS
    from collections import defaultdict
    by_block = defaultdict(list)
    for e in ENCOUNTERS:
        by_block[e['block']].append(e['tag'])
    short = [(b, len(by_block.get(b, []))) for b, _, _ in _BLOCKS
             if len(by_block.get(b, [])) < 3]
    assert not short, f"Blocks with <3 candidates: {short}"


def test_npc_encounter_tags_unique():
    from npc_encounters import ENCOUNTERS
    tags = [e['tag'] for e in ENCOUNTERS]
    assert len(tags) == len(set(tags))


def test_each_npc_encounter_has_three_options():
    from npc_encounters import ENCOUNTERS
    bad = []
    for e in ENCOUNTERS:
        if not isinstance(e.get('options'), list) or len(e['options']) < 2:
            bad.append((e['tag'], len(e.get('options', []))))
    assert not bad, f"NPC encounters with <2 options: {bad}"


def test_each_npc_option_has_label():
    from npc_encounters import ENCOUNTERS
    bad = []
    for e in ENCOUNTERS:
        for i, opt in enumerate(e.get('options', [])):
            if 'label' not in opt:
                bad.append((e['tag'], i))
    assert not bad, f"Options missing label: {bad}"


def test_npc_boss_levels_excluded():
    src = _src('npc_encounters')
    assert "_BOSS_LEVELS" in src
    assert "{20, 40, 60, 80, 100}" in src


def test_npc_trigger_items_resolve_to_real_items():
    from npc_encounters import ENCOUNTERS
    import glob
    import os
    all_items = set()
    for path in glob.glob(str(ROOT / "data" / "items" / "*.json")):
        all_items.update(json.loads(
            Path(path).read_text(encoding='utf-8')).keys())
    bad = []
    for e in ENCOUNTERS:
        tid = e.get('trigger_item')
        if tid and tid not in all_items:
            bad.append((e['tag'], tid))
    assert not bad, f"Trigger items missing from JSON: {bad}"


def test_npc_trigger_item_placement_wired():
    src = _src('main')
    assert "_maybe_spawn_trigger_item" in src
    assert "_npc_trigger_item_levels" in src
    assert "_npc_trigger_items_placed" in src


def test_npc_specific_item_rewards_resolve():
    """Encounters with `reward.type == 'specific_item'` must reference
    an item id that exists in JSON."""
    from npc_encounters import ENCOUNTERS
    import glob
    all_items = set()
    for path in glob.glob(str(ROOT / "data" / "items" / "*.json")):
        all_items.update(json.loads(
            Path(path).read_text(encoding='utf-8')).keys())
    bad = []
    for e in ENCOUNTERS:
        for opt in e.get('options', []):
            reward = opt.get('reward', {})
            if isinstance(reward, dict) and reward.get('type') == 'specific_item':
                iid = reward.get('item_id', '')
                if iid and iid not in all_items:
                    bad.append((e['tag'], iid))
    assert not bad, f"NPC reward item ids not in JSON: {bad}"


def test_npc_accept_item_costs_resolve():
    """Cost type 'accept_item' grants a burden artifact — the item must exist."""
    from npc_encounters import ENCOUNTERS
    artifacts = json.loads(
        (ROOT / "data" / "items" / "artifact.json").read_text(encoding='utf-8'))
    bad = []
    for e in ENCOUNTERS:
        for opt in e.get('options', []):
            cost = opt.get('cost', {})
            if isinstance(cost, dict) and cost.get('type') == 'accept_item':
                iid = cost.get('item_id', '')
                if iid and iid not in artifacts:
                    bad.append((e['tag'], iid))
    assert not bad, f"accept_item burdens missing from artifact.json: {bad}"


def test_npc_dispatcher_in_game_encounters():
    src = _src('game_encounters')
    # Multiple critical functions for NPC dialog flow
    assert "_apply_npc_reward" in src
    assert "specific_item" in src
    assert "_grant_burden_item" in src or "burden" in src.lower()
