"""Bug bash 5 (2026-10-17): monsters, theft and the invisible/disguised name seam.

Covers MON-01..MON-09, MON-11, CODE-02/03/10, JNL-03, PET-03/04 and
INT-02..INT-07, INT-10. Behaviour tests on a real headless Game: these are
deep, randomized spawns (thieves, mimics, the Hellmouth, invisible creatures)
that cannot be reached on demand in a play-test.

Brandon's rulings these pin:
* MON-05 / PET-04, option (b): ANY blow on an unaware disguised mimic or
  ambusher springs it (hero, pet, escort swipe, wand, spell, pull), with the
  usual reveal line. Pets do not hunt an unaware lurker.
* MON-07: clairvoyance keeps showing invisible creatures; the text says so.
"""
import copy
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()
_SCREEN = None

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)

INVISIBLE = 'huldufolk_raider'
AMBUSHER = next(k for k, v in sorted(MONS.items())
                if v.get('ai_pattern') == 'ambush' and not v.get('invisible')
                and not v.get('is_boss') and not v.get('is_mini_boss'))


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=7):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name='__test_bugbash5_hidden__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _open_spot(g, half=4):
    from dungeon import FLOOR
    for y in range(half + 1, g.dungeon.height - half - 1):
        for x in range(half + 1, g.dungeon.width - half - 1):
            if all(g.dungeon.is_walkable(x + i, y + j)
                   for i in range(-half, half + 1) for j in range(-half, half + 1)):
                return x, y
    x = min(max(g.player.x, half + 1), g.dungeon.width - half - 2)
    y = min(max(g.player.y, half + 1), g.dungeon.height - half - 2)
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    return x, y


def _monster(mid, x=0, y=0):
    from monster import Monster
    return Monster({**MONS[mid], 'id': mid}, x, y)


def _scene(mid, dx=1, dy=0, seed=7):
    g = _game(seed)
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    m = _monster(mid, x + dx, y + dy)
    g.monsters = [m]
    g._refresh_fov()
    g.visible |= {(x + i, y + j) for i in range(-4, 5) for j in range(-4, 5)}
    g._sync_unseen()
    return g, m


def _messages(g, n=30):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _wand(effect=None, wid=None):
    from items import load_items
    w = next(w for w in load_items('wand')
             if (wid and w.id == wid) or (not wid and w.effect == effect))
    w = copy.copy(w)
    w.charges = 99
    return w


def _zap(g, wand, target):
    g._wand_override_target = target
    try:
        g._apply_wand_effect(wand)
    finally:
        g._wand_override_target = None


# --- Theft: what can be stolen (MON-01, INT-07) ---------------------------

def test_thieves_never_take_quest_pieces_uniques_keys_or_the_lockpick():
    import theft
    from items import make_item_by_id, Item, load_items
    from mystery_system import MysteryKeyItem
    g, _m = _scene('ethereal_filcher')
    shard = Item({'id': 'philosophers_shard', 'name': "Philosopher's Shard", 'symbol': '*', 'color': [200, 200, 200]})
    lockpick = Item({'id': 'master_lockpick', 'name': 'Master Lockpick', 'symbol': '(', 'color': [200, 200, 200]})
    excalibur = make_item_by_id('weapon', 'excalibur')
    lake = Item({'id': 'scroll_lake_of_fire', 'name': 'Scroll of the Lake of Fire', 'symbol': '?', 'color': [200, 200, 200]})
    key = MysteryKeyItem('test_mystery', 'Bronze Key', 'k', (200, 200, 0), 1.0)
    bread = next(i for i in load_items('food') if not getattr(i, 'is_unique', False))
    g.player.inventory = [shard, lockpick, excalibur, lake, key, bread]
    took = theft.stealable(g.player)
    assert took == [bread]
    # Every named unique and artifact template is safe as well.
    for cls in ('weapon', 'artifact', 'accessory', 'armor', 'shield'):
        for tpl in load_items(cls):
            if getattr(tpl, 'is_unique', False):
                g.player.inventory = [tpl]
                assert theft.stealable(g.player) == [], tpl.id


def test_npc_payment_and_theft_share_one_withheld_rule():
    import npc_encounters
    from items import Item, withheld, WITHHELD_IDS
    for iid in WITHHELD_IDS:
        it = Item({'id': iid, 'name': iid, 'symbol': '*', 'color': [200, 200, 200]})
        assert withheld(it) and not npc_encounters.offerable(it)
    assert 'philosophers_shard' in WITHHELD_IDS and 'master_lockpick' in WITHHELD_IDS


# --- Theft: the loot always comes back (MON-02, CODE-03, INT-06, CODE-10) --

def _rob(g, thief, amount=200):
    thief.stolen_gold = amount
    g.player_gold = 1000 - amount


def test_polymorph_spell_keeps_the_thiefs_haul_and_the_new_body_is_aware():
    import spells
    g, m = _scene('bandit_thief', dx=2)
    _rob(g, m, 170)
    spell = next(v for v in spells.LEARNABLE_SPELLS.values() if v.get('effect') == 'polymorph_spell')
    random.seed(3)
    for _ in range(20):                         # every new shape, mimics and stair-posers included
        g.monsters = [m]
        g._apply_spell_effect(spell, m)
        new = g.monsters[0]
        assert new is not m
        assert new.stolen_gold == 170
        assert new._aware is True
        import unseen
        assert unseen.disguise(new) is None
        m = new


def test_a_banished_thief_drops_the_gold_at_once():
    import spells
    from items import GoldPile
    g, m = _scene('leprechaun', dx=2)
    _rob(g, m, 195)
    spell = next(v for v in spells.LEARNABLE_SPELLS.values() if v.get('effect') == 'banishment')
    g._apply_spell_effect(spell, m)
    assert not m.alive
    assert m.stolen_gold == 0
    piles = [i for i in g.ground_items if isinstance(i, GoldPile) and (i.x, i.y) == (m.x, m.y)
             and getattr(i, '_dropped_by_player', False)]
    assert sum(p.amount for p in piles) == 195


def test_gold_won_back_from_a_thief_is_not_doubled_by_a_gold_ring():
    import theft
    from items import GoldPile
    g, m = _scene('bandit_thief', dx=2)
    _rob(g, m, 400)
    theft.give_back(g, m)
    pile = next(i for i in g.ground_items if isinstance(i, GoldPile) and (i.x, i.y) == (m.x, m.y))
    assert pile.amount == 400
    assert getattr(pile, '_dropped_by_player', False) is True


def test_a_seeded_rng_makes_the_leprechauns_landing_repeatable():
    import theft
    g, m = _scene('leprechaun', dx=1)
    start = (m.x, m.y)
    spots = []
    for n in range(2):
        m.x, m.y = start
        m.stolen_gold = 0
        g.player_gold = 1000
        random.seed(999 + n)                     # the global stream differs ...
        theft.steal(g, m, 'gold', rng=random.Random(5))
        spots.append((m.x, m.y))
    assert spots[0] == spots[1] != start         # ... the seeded landing does not


# --- Names of what the hero cannot see (MON-04, CODE-02, PET-03, JNL-03) ---

def test_the_name_hides_a_disguise_and_an_unsprung_ambusher():
    from monster import the_name
    hm = _monster('hellmouth')
    assert the_name(hm) == 'The staircase leading down'
    assert the_name(_monster('lurking_horror'), lower=True) == 'the iron chest'
    amb = _monster(AMBUSHER)
    assert the_name(amb) == 'Something'
    amb._aware = True
    assert the_name(amb).endswith(MONS[AMBUSHER]['name'])


def test_pet_lines_never_name_an_unseen_creature():
    from pet_system import Pet
    g, m = _scene(INVISIBLE, dx=2)
    assert m._unseen
    pet = Pet('electric', g.player.x + 1, g.player.y)
    pet.hp = 1
    g.pets = [pet]
    random.seed(1)
    g._do_pet_turns()
    text = ' | '.join(_messages(g))
    assert MONS[INVISIBLE]['name'] not in text
    assert 'something unseen' in text           # it attacks / is slain by "something unseen"


def test_confused_attacker_and_thrown_potion_use_the_hidden_name():
    from monster import the_name
    g, m = _scene(INVISIBLE, dx=2)
    assert g._confused_name(m) == 'Something unseen'
    rat = _monster('giant_rat') if 'giant_rat' in MONS else _monster(AMBUSHER)
    rat._aware = True
    assert g._confused_name(rat).startswith('The confused ')
    assert the_name(m, lower=True) == 'something unseen'


# --- Any blow springs a lurker (MON-03, MON-05, PET-04) ------------------

def test_a_wand_aimed_at_the_hellmouth_springs_it_with_a_reveal_line():
    import false_stairs
    g, m = _scene('hellmouth', dx=3)
    assert false_stairs.poses_as_stairs(m)
    _zap(g, _wand(wid='wand_of_absolute_zero'), m)
    assert m._aware and m.ai_pattern == 'aggressive'
    assert not false_stairs.poses_as_stairs(m)
    text = ' | '.join(_messages(g))
    assert 'The staircase leading down springs to life' in text


def test_any_damage_springs_a_disguised_mimic_and_it_then_fights():
    g, m = _scene('lurking_horror', dx=1)
    m.take_damage(5)
    assert m._aware and m.ai_pattern == 'aggressive'
    g._advance_turn()
    assert any('iron chest springs to life' in t for t in _messages(g))


def test_a_struck_ambusher_springs_from_hiding():
    g, m = _scene(AMBUSHER, dx=3)
    m.take_damage(1)
    assert m._aware
    g._say_springs()
    assert any('springs from hiding' in t for t in _messages(g))


def test_pets_do_not_hunt_an_unaware_lurker_but_one_that_bites_springs():
    from pet_system import Pet
    g, m = _scene('lurking_horror', dx=3)
    pet = Pet('electric', g.player.x + 2, g.player.y)    # right beside the "chest"
    pet.hp = pet.max_hp = 10 ** 6
    assert pet.take_turn(g.player, g.dungeon, g.monsters, [pet], g.ground_items) is None
    g.pets = [pet]
    g._monster_swipes(g.pets)
    assert m._aware and m.ai_pattern == 'aggressive'
    assert any('iron chest springs to life' in t for t in _messages(g))
    # Sprung, it is fair game.
    res = pet.take_turn(g.player, g.dungeon, g.monsters, [pet], g.ground_items)
    assert res and res[0] == 'attack' and res[1] is m


def test_a_pets_pull_springs_a_disguised_mimic():
    from pet_system import Pet
    g, m = _scene('lurking_horror', dx=4)
    pet = Pet('electric', g.player.x + 1, g.player.y)
    g.pets = [pet]
    g._pull_foes_to_pet(pet, 4)
    assert m._aware


# --- Fear on the fearless (MON-06) -----------------------------------------

def test_fear_never_turns_a_galla_cowardly():
    import spells
    g, m = _scene('galla_demon', dx=3)
    m._aware = True
    ai = m.ai_pattern
    _zap(g, _wand(wid='wand_of_fear'), m)
    assert m.ai_pattern == ai and not m.has_effect('feared')
    assert 'knows no fear' in _messages(g, 1)[-1]
    spell = next(v for v in spells.LEARNABLE_SPELLS.values() if v.get('effect') == 'fear_monster_spell')
    g._apply_spell_effect(spell, m)
    assert m.ai_pattern == ai


# --- The Hellmouth's tells (MON-08, MON-09, INT-10) ------------------------

def test_look_says_the_same_of_the_hellmouth_as_of_a_real_stair():
    from dungeon import STAIRS_DOWN
    g, m = _scene('hellmouth', dx=3)
    g.target_cursor_x, g.target_cursor_y = m.x, m.y
    random.seed(0)
    g._confirm_observe()
    hm_text = _messages(g, 3)
    sx, sy = g.player.x - 2, g.player.y
    g.dungeon.tiles[sy][sx] = STAIRS_DOWN
    g.target_cursor_x, g.target_cursor_y = sx, sy
    g._confirm_observe()
    assert 'Stairs leading down.' in hm_text
    assert _messages(g, 1)[-1] == 'Stairs leading down.'
    assert not any('staircase' in t for t in hm_text)


def test_teleport_never_moves_the_black_knight():
    import spells
    from black_knight import BlackKnight
    g, _m = _scene('giant_rat' if 'giant_rat' in MONS else AMBUSHER, dx=3)
    bk = BlackKnight({**MONS['black_knight'], 'id': 'black_knight'}, g.player.x + 2, g.player.y)
    g.monsters = [bk]
    _zap(g, _wand(effect='teleport_monster'), bk)
    assert (bk.x, bk.y) == (g.player.x + 2, g.player.y)
    assert not any('vanishes' in t for t in _messages(g, 3))
    spell = next(v for v in spells.LEARNABLE_SPELLS.values() if v.get('effect') == 'teleport_away_spell')
    g._apply_spell_effect(spell, None)
    assert (bk.x, bk.y) == (g.player.x + 2, g.player.y)


def test_the_false_stair_is_remembered_like_the_real_one():
    g, m = _scene('hellmouth', dx=3)
    calls = []
    real = g.renderer.screen.blit

    g.dungeon.explored.add((m.x, m.y))
    g.visible.discard((m.x, m.y))

    class _Spy:
        def __init__(self, surf):
            self.surf = surf

        def blit(self, *a, **k):
            calls.append(a[1] if len(a) > 1 else None)
            return real(*a, **k)

        def __getattr__(self, n):
            return getattr(self.surf, n)

    g.renderer.screen = _Spy(g.renderer.screen)
    try:
        g.renderer.draw_disguise(m.x, m.y, None, g.visible, tile='stairs_down',
                                 explored=g.dungeon.explored)
    finally:
        g.renderer.screen = g.renderer.screen.surf
    assert len(calls) == 2                       # the stair, then the memory dim
    calls.clear()
    g.renderer.draw_disguise(m.x, m.y, None, g.visible, tile='stairs_down', explored=set())
    assert calls == []


# --- Danger sense, hero powers, area counts (MON-11, INT-02, INT-03) -------

def test_danger_sense_counts_an_invisible_creature_in_view():
    g, m = _scene(INVISIBLE, dx=2)
    assert (m.x, m.y) in g.visible and m._unseen
    g.player.add_effect('warning', 10)
    g._do_warning()
    assert any('danger sense tingles' in t for t in _messages(g, 2))


def test_hero_powers_neither_target_nor_name_an_unseen_creature():
    import hero_specials
    g, m = _scene(INVISIBLE, dx=2)
    hp = m.hp
    hero_specials._eff_damage_single(g, None, {'dice': '2d6', 'range': 6}, 1)
    hero_specials._eff_paralyze_target(g, None, {'paralyze': 3, 'slow_too': 0}, 1)
    assert m.hp == hp
    assert not any(MONS[INVISIBLE]['name'] in t for t in _messages(g))


def test_area_wand_counts_only_what_the_hero_sees():
    g, m = _scene(INVISIBLE, dx=2)
    w = _wand(effect='sleep_monster')
    w.effect = 'mass_sleep'
    _zap(g, w, None)
    assert '(0 affected' in _messages(g, 1)[-1]


# --- The Green Girdle turns ONE blow (INT-04) -------------------------------

def test_the_green_girdle_turns_the_knights_return_blow_once():
    import items
    g, _m = _scene('green_knight', dx=1)
    gk = g.monsters[0]
    gk._has_revived = True
    gird = next(i for i in items.load_items('armor') if i.id == 'green_girdle')
    g.player.armor_slots[4] = gird
    g.player.hp = -50
    assert g._green_girdle_spares(gk) and g.player.hp == 1
    g.player.hp = -50
    assert not g._green_girdle_spares(gk)


# --- MON-07: clairvoyance says it shows the invisible ---------------------

def test_clairvoyance_text_says_it_shows_invisible_creatures():
    from status_effects import EFFECT_INFO
    assert 'invisible' in EFFECT_INFO['clairvoyant'][2].lower()
    with open(os.path.join(ROOT, 'data', 'items', 'accessory.json'), encoding='utf-8') as f:
        acc = json.load(f)
    for iid in ('ring_clairvoy', 'amulet_clairvoyant'):
        assert acc[iid]['effects']['status'] == 'clairvoyant'
        assert 'see' in acc[iid]['lore'] or 'invisible' in acc[iid]['lore']
        assert 'invisible' in acc[iid]['lore'] or 'no eye can see' in acc[iid]['lore']
    import game_render
    lines = game_render._monster_traits(MONS[INVISIBLE]) if hasattr(game_render, '_monster_traits') else None
    if lines is not None:
        assert any('clairvoyance' in t for t in lines)



def test_a_summoned_invisible_minion_is_not_named():
    g, s = _scene('endor_medium', dx=2)
    s._aware = True
    s.summon_kind = INVISIBLE
    g._spawn_summoner_minion(s)
    text = ' | '.join(_messages(g))
    assert 'summons something unseen' in text
    assert MONS[INVISIBLE]['name'] not in text


def test_an_atreus_scion_drawn_from_an_ambusher_is_announced_aware(monkeypatch):
    import main
    from monster import the_name
    g, _m = _scene(AMBUSHER, dx=4)
    g.monsters = []
    monkeypatch.setattr(main, 'spawn_monsters', lambda *a, **k: [_monster(AMBUSHER)])
    g._spawn_house_of_atreus(g.dungeon_level)
    m = g.monsters[-1]
    assert m._aware and the_name(m) == m.name
