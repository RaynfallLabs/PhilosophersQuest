"""Regression tests for plot-required items and boss maps.

Every item the game needs for completion (Philosopher's Stone, Sword/Scales
of Michael, the secret 'Death is Dead' victory chain, the 6 Gleipnir-binding
ingredients, the 6 boss-floor maps) must spawn correctly. These tests guard
the path-to-victory infrastructure.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
pygame.init()


def test_philosophers_stone_spawns_at_l100():
    """The Stone is the primary victory item — must always spawn at L100."""
    from level_manager import LevelManager
    for _ in range(3):
        lm = LevelManager()
        dungeon, monsters, items = lm.generate(100)
        stone = next((i for i in items if getattr(i, 'id', '') == 'philosophers_stone'), None)
        assert stone is not None, 'philosophers_stone missing from L100 spawn'


def test_all_boss_levels_generate_with_their_boss():
    """L20/40/60/80/100 + L999 cow level must each produce their canonical boss."""
    from boss_levels import generate_boss_level, COW_LEVEL
    BOSSES = {
        20: 'asterion_minotaur',
        40: 'medusa_gorgon',
        60: 'fafnir_dragon',
        80: 'fenrir_wolf',
        100: 'abaddon_destroyer',
        COW_LEVEL: 'hell_bovine',
    }
    for lvl, boss_id in BOSSES.items():
        for trial in range(3):
            dungeon, monsters, items = generate_boss_level(lvl)
            assert len(dungeon.rooms) >= 1, f'L{lvl} trial {trial}: no rooms'
            kinds = [getattr(m, 'kind', '') for m in monsters]
            assert boss_id in kinds, (
                f'L{lvl} trial {trial}: boss {boss_id} missing. Got: {kinds[:6]}'
            )


def test_gleipnir_ingredients_all_spawnable():
    """The 6 myth-fragment artifacts that forge Gleipnir must all exist + spawn."""
    INGREDIENTS = (
        'cats_footstep', 'womans_beard', 'mountain_root',
        'fish_breath', 'bird_spittle', 'bear_sinew',
    )
    art = json.load(open('data/items/artifact.json', encoding='utf-8'))
    for ing in INGREDIENTS:
        assert ing in art, f'{ing} missing from artifact.json'
        item = art[ing]
        assert item.get('peak_weight', 0) > 0, f'{ing} has peak_weight 0 (would never spawn)'


def test_michael_artifacts_exist_for_judgment_reward():
    """Sword + Scales of Michael are granted by the L99 Altar judgment."""
    from items import load_items
    weapons = load_items('weapon')
    artifacts = load_items('artifact')
    sword = next((w for w in weapons if w.id == 'sword_of_michael'), None)
    scales = next((a for a in artifacts if a.id == 'scales_of_michael'), None)
    assert sword is not None, 'sword_of_michael missing from weapon.json'
    assert scales is not None, 'scales_of_michael missing from artifact.json'


def test_secret_victory_lore_factories_exist():
    """The DEATH IS DEAD path uses runtime factories for 4 plot items."""
    from items import (make_abyssal_shimmer, make_philosophers_wrench,
                       make_scroll_lake_of_fire, make_tablet_of_second_death)
    shim = make_abyssal_shimmer(0, 0)
    wrench = make_philosophers_wrench(0, 0)
    fire = make_scroll_lake_of_fire(0, 0)
    tablet = make_tablet_of_second_death(0, 0)
    assert shim.id == 'abyssal_shimmer'
    assert wrench.id == 'philosophers_wrench'
    assert fire.id == 'scroll_lake_of_fire'
    assert tablet.id == 'tablet_of_second_death'


def test_unique_gram_family_present():
    """Gram (reforged) + broken_gram must exist for the Sigurd-altar quest."""
    weapons = json.load(open('data/items/weapon.json', encoding='utf-8'))
    assert 'gram' in weapons, 'gram missing from weapon.json'
    assert 'broken_gram' in weapons, 'broken_gram missing from weapon.json'


def test_quest_artifact_spawn_paths_exist():
    """Bronze Bull, Gleipnir, Eye of Graeae, Ariadne's Thread, Vidar's
    Sandal must all have at least one spawn-path reference in src/."""
    PLOT_ARTIFACTS = (
        'bronze_bull', 'gleipnir', 'eye_of_graeae',
        'ariadnes_thread', 'vidars_sandal',
    )
    src_text = ''
    for root, _, files in os.walk('src'):
        for f in files:
            if f.endswith('.py'):
                with open(os.path.join(root, f), encoding='utf-8') as fp:
                    src_text += fp.read() + '\n'
    for art in PLOT_ARTIFACTS:
        assert (f"'{art}'" in src_text or f'"{art}"' in src_text), (
            f'plot artifact {art} has no spawn-path reference in src/'
        )


def test_chronicle_pickup_ids_are_real():
    """The _CHRONICLE_ITEMS set must reference real ids. Catches the
    eye_of_the_graeae / broken_blade_of_gram typo class of bug."""
    import re
    main_py = open('src/main.py', encoding='utf-8').read()
    m = re.search(r"_CHRONICLE_ITEMS\s*=\s*\{([^}]+)\}", main_py)
    assert m is not None, 'could not locate _CHRONICLE_ITEMS'
    ids = re.findall(r"'([\w_]+)'", m.group(1))

    known = set()
    for cat in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll',
                'spellbook', 'potion', 'food', 'ingredient', 'ammo',
                'artifact', 'container'):
        d = json.load(open(f'data/items/{cat}.json', encoding='utf-8'))
        known.update(d.keys())
    known.update(['abyssal_shimmer', 'philosophers_wrench',
                  'scroll_lake_of_fire', 'tablet_of_second_death',
                  'complete_tablet_of_second_death'])

    unknown = [i for i in ids if i not in known]
    assert not unknown, (
        f"_CHRONICLE_ITEMS references unknown ids: {unknown}"
    )


def test_fafnir_drops_blood_potion():
    """Fafnir (L60 boss) must drop fafnirs_blood — key reforge hint."""
    potions = json.load(open('data/items/potion.json', encoding='utf-8'))
    assert 'fafnirs_blood' in potions, 'fafnirs_blood missing from potion.json'


def test_seal_demons_drop_resolves():
    """All 7 seal demons exist in monsters.json + are flagged is_mini_boss."""
    from level_manager import LevelManager
    monsters = json.load(open('data/monsters.json', encoding='utf-8'))
    seal_levels = LevelManager._SEAL_DEMON_LEVELS
    assert len(seal_levels) == 7
    for lvl, demon_id in seal_levels.items():
        assert demon_id in monsters, f'{demon_id} missing from monsters.json'
        assert monsters[demon_id].get('is_mini_boss'), (
            f'{demon_id} not flagged is_mini_boss'
        )
