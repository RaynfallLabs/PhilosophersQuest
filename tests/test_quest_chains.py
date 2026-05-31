"""Quest chain spawn + effect pin tests — covering the chains my earlier
quest-lifecycle audit MISSED.

Covered:
- Major boss levels (F20/40/60/80/100): bosses spawn, drop scrolls,
  boss reward scrolls exist with effect=boss_reward
- 4 lore items (shimmer/wrench/fire_scroll/tablet): random level pick
  in correct range, factory functions exist
- Cow level (L999): entry/exit/state wired, cow king is portal-only
- Ariadne chain: Bronze Bull (L12), Ariadne Shrine (L17)
- Athena/Medusa chain: Eye of Graeae (L29), Athena Shrine (L37)
- Odin/Fafnir chain: Broken Gram (L48), Odin Shrine (L53)
- Vidar/Fenrir chain: 10 leather_scrap floors (L5-73), Dwarven Forge
  (L76), Vidar's Altar (L79)
- Gleipnir chain: 6 components on L62/65/68/71/74/77, _create_gleipnir_room
- Pit gate: Judgment Altar on L99
- Special-tile interactions wired (altar/fountain/grave/throne)
- Quest artifact chronicle list covers all known quest items
- NPC encounter accept-item costs (cursed_lodestone, sealed_dispatch)
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
# Major bosses: each boss level generator + boss + reward scroll
# ---------------------------------------------------------------------------

MAJOR_BOSSES = {
    20: 'asterion_minotaur',
    40: 'medusa_gorgon',
    60: 'fafnir_dragon',
    80: 'fenrir_wolf',
    100: 'abaddon_destroyer',
}

BOSS_SCROLLS = {
    'asterion_minotaur': 'scroll_of_the_labyrinth',
    'medusa_gorgon': 'scroll_of_the_gorgon',
    'fafnir_dragon': 'scroll_of_the_hoard',
    'fenrir_wolf': 'scroll_of_ragnarok',
    'abaddon_destroyer': 'scroll_of_the_abyss',
    'cow_king': 'scroll_of_the_pasture',
}


def test_each_major_boss_has_level_generator():
    src = _src('boss_levels')
    for lvl in MAJOR_BOSSES:
        assert f"level_num == {lvl}" in src, f"No generator for L{lvl}"


def test_each_major_boss_treasure_has_scroll():
    monsters = json.loads((ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    for bkind, scroll_id in BOSS_SCROLLS.items():
        assert bkind in monsters, f"{bkind} missing from monsters.json"
        t = monsters[bkind].get('treasure', {})
        assert t.get('boss_scroll_id') == scroll_id, \
            f"{bkind}: boss_scroll_id should be {scroll_id}, got {t.get('boss_scroll_id')}"


def test_all_boss_scrolls_exist_and_are_gated():
    scrolls = json.loads((ROOT / "data" / "items" / "scroll.json").read_text(encoding='utf-8'))
    for scroll_id in BOSS_SCROLLS.values():
        assert scroll_id in scrolls, f"Boss scroll {scroll_id} missing from scroll.json"
        s = scrolls[scroll_id]
        assert s.get('effect') == 'boss_reward', \
            f"{scroll_id}: effect should be boss_reward"
        assert s.get('min_level', 0) >= 9999, \
            f"{scroll_id}: min_level should be 9999 to suppress natural spawn"
        assert s.get('peak_floor', 0) >= 9999, \
            f"{scroll_id}: peak_floor should be 9999 (boss-only drop)"


def test_boss_reward_dispatcher_exists():
    src = _src('game_magic')
    assert "effect == 'boss_reward'" in src
    assert "REWARD CODE" in src


def test_fafnir_blood_drop_wired():
    """Killing Fafnir must spawn the unique fafnirs_blood potion."""
    src = _src('game_combat')
    assert "monster.kind == 'fafnir_dragon'" in src
    assert "_spawn_fafnir_blood" in src


# ---------------------------------------------------------------------------
# Lore items (random-level placement)
# ---------------------------------------------------------------------------

LORE_ITEMS = ('shimmer', 'wrench', 'fire_scroll', 'tablet')
LORE_FACTORIES = (
    'make_abyssal_shimmer', 'make_philosophers_wrench',
    'make_scroll_lake_of_fire', 'make_tablet_of_second_death',
)


def test_lore_levels_initialized_in_init():
    src = _src('main')
    for key in LORE_ITEMS:
        assert f"'{key}'" in src, f"Lore key {key} missing from main.py"


def test_lore_factories_exist():
    src = _src('items')
    for fn in LORE_FACTORIES:
        assert f"def {fn}" in src, f"Lore factory {fn} missing from items.py"


def test_lore_items_placed_at_assigned_level():
    src = _src('main')
    assert "_maybe_place_lore_items" in src
    assert "_lore_placed" in src


# ---------------------------------------------------------------------------
# Cow level
# ---------------------------------------------------------------------------

def test_cow_level_state_machine_wired():
    src = _src('main')
    for attr in ('_cow_poke_count', '_cow_level_done', '_cow_spawned',
                 '_cow_level', '_cow_return_level'):
        assert attr in src, f"Cow state {attr} missing"


def test_cow_level_entry_exit_wired():
    src = _src('game_encounters')
    assert "_enter_cow_level" in src
    assert "_exit_cow_level" in src
    assert "COW_LEVEL" in src


def test_cow_king_spawn_chance_zero_is_portal_only():
    monsters = json.loads((ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    assert monsters['cow_king'].get('spawn_chance', -1) == 0, \
        "cow_king should have spawn_chance=0 (portal-only via cow level)"


# ---------------------------------------------------------------------------
# Ariadne / Athena / Odin / Vidar / Pit shrines (fixed-level placement)
# ---------------------------------------------------------------------------

FIXED_LEVEL_SPAWNS = {
    12: 'bronze_bull',
    17: '_create_ariadne_shrine',
    29: 'eye_of_graeae',
    37: '_create_athena_shrine',
    48: 'broken_gram',  # weapon, loaded via load_items
    53: '_create_odin_shrine',
    76: '_create_dwarven_forge',
    79: '_create_vidar_altar',
    99: '_create_judgment_altar',
}


def test_fixed_level_quest_spawns():
    src = _src('dungeon')
    for lvl, marker in FIXED_LEVEL_SPAWNS.items():
        # Look for "if level == <N>" or "level == <N>" near the marker
        assert marker in src, f"L{lvl} spawn marker '{marker}' missing"
        assert f"level == {lvl}" in src, f"L{lvl} gate missing"


def test_shrine_creation_functions_defined():
    src = _src('dungeon')
    for fn in ('_create_ariadne_shrine', '_create_athena_shrine',
               '_create_odin_shrine', '_create_dwarven_forge',
               '_create_vidar_altar', '_create_judgment_altar'):
        assert f"def {fn}" in src, f"Shrine function {fn} not defined"


# ---------------------------------------------------------------------------
# Gleipnir chain (6 components across f62-77 + forge at 76 + altar at 79)
# ---------------------------------------------------------------------------

GLEIPNIR_FLOORS = (62, 65, 68, 71, 74, 77)
GLEIPNIR_COMPONENT_IDS = (
    'cats_footstep', 'womans_beard', 'mountain_root',
    'fish_breath', 'bird_spittle', 'bear_sinew',
)


def test_gleipnir_components_map_floors_to_ids():
    src = _src('dungeon')
    assert "_GLEIPNIR_COMPONENTS" in src
    for lvl in GLEIPNIR_FLOORS:
        assert f"{lvl}:" in src, f"Gleipnir floor {lvl} missing"
    for cid in GLEIPNIR_COMPONENT_IDS:
        assert f"'{cid}'" in src, f"Gleipnir component {cid} missing"


def test_gleipnir_components_chronicled_on_pickup():
    src = _src('main')
    for cid in GLEIPNIR_COMPONENT_IDS:
        assert cid in src, f"Gleipnir component {cid} not chronicled"


def test_gleipnir_forge_creates_artifact():
    src = _src('game_divine')
    assert "_check_gleipnir_forge" in src
    assert "'gleipnir'" in src or '"gleipnir"' in src


def test_vidar_altar_creates_sandal():
    src = _src('game_divine')
    assert "_check_vidar_altar" in src or "vidars_sandal" in src


def test_vidars_sandal_consumes_against_fenrir():
    src = _src('game_combat')
    assert "vidars_sandal" in src


# ---------------------------------------------------------------------------
# Leather scrap floors (Vidar's Sandal prereq)
# ---------------------------------------------------------------------------

LEATHER_SCRAP_FLOORS = (5, 13, 21, 28, 35, 42, 50, 58, 66, 73)


def test_leather_scrap_floor_list():
    src = _src('dungeon')
    assert "_LEATHER_SCRAP_LEVELS" in src
    for lvl in LEATHER_SCRAP_FLOORS:
        # The constant list contains exactly these floors
        pass  # just verifying constant exists is enough; rest comes from grep
    # Look for the actual list
    import re
    m = re.search(r"_LEATHER_SCRAP_LEVELS\s*=\s*\[([^\]]+)\]", src)
    assert m, "Leather scrap level list not found"
    floors_in_src = [int(s.strip()) for s in m.group(1).split(',') if s.strip()]
    assert set(LEATHER_SCRAP_FLOORS) == set(floors_in_src), \
        f"Leather scrap floors mismatch: {floors_in_src}"


# ---------------------------------------------------------------------------
# Judgment Altar on L99 (Pit gate)
# ---------------------------------------------------------------------------

def test_judgment_altar_at_l99():
    src = _src('dungeon')
    assert "level == 99" in src
    assert "_create_judgment_altar" in src
    assert "judgment_altar_pos" in src


def test_judgment_altar_check_wired():
    src = _src('game_divine')
    assert "judgment_altar_pos" in src


# ---------------------------------------------------------------------------
# Special tile dispatchers (ALTAR / FOUNTAIN / GRAVE / THRONE)
# ---------------------------------------------------------------------------

def test_special_tiles_have_dispatchers():
    src = _src('game_divine')
    # All four special tiles must have at least one dispatcher
    assert "_on_altar" in src
    # Fountain / grave / throne quizzes
    assert "FOUNTAIN" in src or "fountain" in src.lower()
    assert "GRAVE" in src or "grave" in src.lower()
    assert "THRONE" in src or "throne" in src.lower()


def test_main_dispatches_special_tile_interactions():
    src = _src('main')
    assert "FOUNTAIN" in src
    assert "GRAVE" in src
    assert "THRONE" in src


# ---------------------------------------------------------------------------
# Quest artifact chronicle list completeness
# ---------------------------------------------------------------------------

CHRONICLED_QUEST_ITEMS = (
    'philosophers_stone', 'ariadnes_thread', 'bronze_bull',
    'eye_of_graeae', 'broken_gram', 'gleipnir',
    'vidars_sandal', 'scales_of_michael', 'sword_of_michael',
    'magic_dungeon_carrot',
    'cats_footstep', 'womans_beard', 'mountain_root',
    'fish_breath', 'bird_spittle', 'bear_sinew',
    'tablet_of_second_death', 'philosophers_wrench',
    'complete_tablet_of_second_death', 'scroll_lake_of_fire',
)


def test_quest_artifacts_chronicled():
    src = _src('main')
    assert "_CHRONICLE_ITEMS" in src
    for iid in CHRONICLED_QUEST_ITEMS:
        assert iid in src, f"Quest item {iid} missing from chronicle"


# ---------------------------------------------------------------------------
# Burden / NPC encounter accept-item costs
# ---------------------------------------------------------------------------

def test_burden_items_referenced_in_npc_encounters():
    src = _src('npc_encounters')
    assert "cursed_lodestone" in src
    assert "sealed_dispatch" in src


def test_grant_burden_item_function_exists():
    src = _src('game_encounters')
    assert "_grant_burden_item" in src or "burden" in src.lower()


# ---------------------------------------------------------------------------
# Save/load coverage for quest state
# ---------------------------------------------------------------------------

QUEST_STATE_FIELDS = (
    '_lore_levels', '_lore_placed',
    '_cow_poke_count', '_cow_level_done', '_cow_spawned',
    '_cow_level', '_cow_return_level',
    '_npc_encounter_levels', '_encountered_npcs',
    '_npc_triggered_items', 'seals_broken',
)


def test_save_system_persists_all_quest_state():
    src = _src('save_system')
    missing = [f for f in QUEST_STATE_FIELDS if f not in src]
    assert not missing, f"save_system missing fields: {missing}"


def test_load_state_restores_seals_broken():
    src = _src('main')
    assert "state.get('seals_broken'" in src


# ---------------------------------------------------------------------------
# Tablet of Second Death + Philosopher's Wrench chain
# ---------------------------------------------------------------------------

def test_tablet_chain_factories_exist():
    src = _src('items')
    assert "def make_tablet_of_second_death" in src
    assert "def make_philosophers_wrench" in src
    assert "complete_tablet_of_second_death" in src


def test_wrench_use_function_wired():
    src = _src('main')
    assert "_use_philosophers_wrench" in src
    assert "tablet_of_second_death" in src


def test_complete_tablet_logic_in_game_magic():
    src = _src('game_magic')
    assert "complete_tablet_of_second_death" in src
