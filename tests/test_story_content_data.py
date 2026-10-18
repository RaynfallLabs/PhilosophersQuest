"""Data tests for the story items, monsters and effects (ENCOUNTER_STORIES_DRAFT
J3): each exists with lore, is encounter-only (never in a random pool), has
lore-first numbers that sit in its band (LORE NOT FLOOR: fixed base data,
nothing scaled at runtime), and has its own 64 px picture."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

MONSTERS = {   # id -> (band low, band high) where its stories happen
    'neferkaptah_risen': (54, 83), 'azarael': (81, 89), 'locust_cultist': (80, 98),
    'locust_herald': (80, 98), 'villager_mob': (31, 65), 'palace_guard': (31, 56),
    'morrow': (24, 34),
}
ITEMS = {
    'brennans_sword': 'weapon', 'azaraels_brand': 'accessory', 'locust_charm': 'accessory',
    'brass_wardens_cog': 'accessory', 'black_string_bracelet': 'accessory',
    'wats_oil_flask': 'artifact', 'olifant': 'artifact', 'raphaels_gall': 'artifact',
    'green_girdle': 'armor',
}
NPC_FIGURES = ('npc_neferkaptah', 'npc_ahwere')


def _load(rel):
    with open(os.path.join(ROOT, *rel.split('/')), encoding='utf-8') as f:
        return json.load(f)


def _avg_hp(dice: str) -> float:
    n, rest = dice.split('d')
    sides, _, plus = rest.partition('+')
    return int(n) * (int(sides) + 1) / 2 + int(plus or 0)


@pytest.mark.parametrize('mid', sorted(MONSTERS))
def test_story_monster_data(mid):
    m = _load('data/monsters.json')[mid]
    assert m['lore'] and len(m['lore']) > 120
    assert m['frequency'] == 0 and m['peak_weight'] == 0.0 and m.get('quest_only')
    lo, hi = MONSTERS[mid]
    assert lo - 2 <= m['peak_floor'] <= hi
    assert m['attacks'] and all('damage' in a for a in m['attacks'])
    from monster import Monster
    from game_magic import _monster_defn
    mon = Monster(_monster_defn(mid), 0, 0)
    assert mon.max_hp >= 1


def test_story_monster_strength_follows_the_lore():
    m = _load('data/monsters.json')
    hp = {k: _avg_hp(m[k]['hp']) for k in MONSTERS}
    # The fallen Power outlasts the cult soldier, who outlasts the herald.
    assert hp['azarael'] > hp['locust_cultist'] > hp['locust_herald']
    # A palace guard is trained; a villager with a pitchfork is not.
    assert hp['palace_guard'] > hp['villager_mob']
    # The risen prince leads mummies and is far beyond one.
    assert hp['neferkaptah_risen'] > 20 * _avg_hp(m['mummy']['hp'])
    for k in ('neferkaptah_risen', 'azarael', 'morrow'):
        assert m[k].get('proper_noun')


@pytest.mark.parametrize('iid', sorted(ITEMS))
def test_story_item_data(iid):
    from items import make_item_by_id, scripted_only_ids
    it = make_item_by_id(ITEMS[iid], iid)
    assert it is not None and it.lore and len(it.lore) > 120
    assert iid in scripted_only_ids()                     # never in a random pool


def test_story_item_numbers():
    from items import make_item_by_id
    sword = make_item_by_id('weapon', 'brennans_sword')
    w = _load('data/items/weapon.json')
    # A plain good knightly sword: below the legendary blades of its band.
    assert w['brennans_sword']['mathTier'] == 4
    assert w['brennans_sword']['baseDamage'] < w['joyeuse']['baseDamage'] < w['durendal']['baseDamage']
    assert sword is not None
    cog = make_item_by_id('accessory', 'brass_wardens_cog')
    bracelet = make_item_by_id('accessory', 'black_string_bracelet')
    brand = make_item_by_id('accessory', 'azaraels_brand')
    charm = make_item_by_id('accessory', 'locust_charm')
    assert (cog.quiz_timer_bonus, bracelet.quiz_timer_bonus) == (2, 3)
    assert bracelet.bound_to_wielder and brand.bound_to_wielder and not cog.bound_to_wielder
    assert charm.calms_locusts
    assert make_item_by_id('artifact', 'raphaels_gall').cures_blindness_once


def test_story_effects_are_registered():
    from status_effects import EFFECT_INFO, BUFFS, DEBUFFS, _EXPIRE_MSGS
    for eff in ('porter', 'light', 'sickly', 'brilliance'):
        assert eff in EFFECT_INFO and eff in _EXPIRE_MSGS
    assert {'porter', 'light'} <= BUFFS and 'sickly' in DEBUFFS


def test_quest_pieces_include_the_promised_things():
    from main import Game
    assert {'book_of_thoth', 'brennans_sword', 'wats_oil_flask', 'olifant'} <= Game._QUEST_PIECE_IDS


@pytest.mark.parametrize('mid', sorted(MONSTERS) + list(NPC_FIGURES))
def test_story_monster_art_present(mid):
    path = os.path.join(ROOT, 'assets', 'tiles', 'monsters', mid + '.png')
    assert os.path.isfile(path)
    import pygame
    assert pygame.image.load(path).get_size() == (64, 64)


@pytest.mark.parametrize('iid', sorted(ITEMS))
def test_story_item_art_present(iid):
    from renderer import _resolve_item_sprite_path
    path = _resolve_item_sprite_path(iid)
    assert path is not None and os.path.normcase(os.path.abspath(path)) == os.path.normcase(
        os.path.join(ROOT, 'assets', 'tiles', 'items', iid + '.png'))
