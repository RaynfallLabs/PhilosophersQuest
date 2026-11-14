"""Winning-build plan 2026-11-13, slice 8: Fenrir's scraps, the Bloomleaf
Cloak and Old Nickel who wears it, the Emberpup who earns it, and every
multi-visit encounter showing that it is working (sections 3.7, 3.8, 3.8b).

These are late, randomized or many-visit things a play-test can reach only
with luck, so each rule is pinned here on a real headless Game.
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


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(name='__test_bloomleaf__', seed=11):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name=name)
    g.state = STATE_PLAYER
    return g


def _texts(g, n=12):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _data(name):
    with open(os.path.join(ROOT, 'data', name), encoding='utf-8') as f:
        return json.load(f)


# ===========================================================================
# 1. Fenrir's scraps: heavy, plain, and no hint outside Recall Lore (3.7)
# ===========================================================================

_HINT_WORDS = ('collect', 'custom', 'north', 'count', 'ten ', 'vidar', 'altar', 'god',
               'someone', 'sandal', 'wolf', 'fenrir', 'save', 'kept')


def _scrap():
    from dungeon import _quest_artifact
    return _quest_artifact('leather_scrap')


def test_a_scrap_weighs_five_pounds_and_all_ten_are_half_a_heros_load():
    from player import Player
    s = _scrap()
    assert s.weight == 5.0
    p = Player()
    assert p.STR == 10 and 10 * s.weight == 0.5 * p.get_carry_limit()


def test_the_scraps_lore_gives_nothing_away():
    lore = _scrap().lore.lower()
    assert 'shoe leather' in lore and 'no use to anyone' in lore and 'heavy' in lore
    for w in _HINT_WORDS:
        assert w not in lore, w


def test_picking_up_scraps_counts_nothing_and_writes_one_plain_line():
    from chronicle import text_of
    g = _game('__test_scrap_pickup__')
    for _ in range(3):
        s = _scrap()
        s.x, s.y = g.player.x, g.player.y
        g.ground_items.append(s)
        g._pickup()
    held = [i for i in g.player.inventory if getattr(i, 'id', '') == 'leather_scrap']
    assert len(held) == 3
    log = ' '.join(_texts(g, 30))
    assert 'That makes' not in log and 'Another scrap' not in log and 'make a shoe' not in log
    lines = [text_of(c) for c in g._chronicle if 'leather' in text_of(c).lower()]
    assert lines == ["Picked up a heavy scrap of shoe leather. No use to anyone."]
    for w in _HINT_WORDS:
        assert w not in lines[0].lower(), w


def test_the_recall_lore_hints_still_read_true():
    hints = [h for tier in _data('hints.json').values() for h in tier]
    scraps = [h for h in hints if 'scrap' in h.lower()]
    assert any("silent god's shoe" in h for h in scraps)
    assert any('keep counting' in h.lower() for h in scraps)
    # Nothing in them says a scrap is light.
    assert not any(w in h.lower() for h in scraps for w in ('light', 'weighs nothing', 'small'))


def test_the_drop_menu_opens_for_scraps_only_on_vidars_altar():
    from dungeon import ALTAR
    from game_states import STATE_DROP_MENU, STATE_PLAYER
    src = open(os.path.join(ROOT, 'src', 'game_input.py'), encoding='utf-8').read()
    block = src[src.index("'eye_of_graeae', 'broken_gram'"):src.index('self._open_drop_menu()')]
    assert 'leather_scrap' not in block                    # not one of the altar offerings
    g = _game('__test_scrap_altar__')
    x, y = g.player.x, g.player.y
    g.dungeon.tiles[y][x] = ALTAR
    g.player.inventory.append(_scrap())
    g.dungeon.vidar_altar_pos = (x, y)
    g._player_input(pygame.K_d)
    assert g.state == STATE_DROP_MENU
    # On any other altar a scrap is plain junk: dropped, nothing said of it.
    g.state = STATE_PLAYER
    g.dungeon.vidar_altar_pos = (x + 40, y + 40)
    called = []
    g._check_vidar_altar = lambda *a: called.append(a)
    item = next(i for i in g.player.inventory if getattr(i, 'id', '') == 'leather_scrap')
    g.karma = 3
    before = len(g.msg_log.entries)
    g._do_drop_item(item)
    assert not called and item in g.ground_items
    said = ' '.join(str(e[0]) for e in g.msg_log.entries[before:]).lower()
    assert 'shoe' not in said and 'leather lies' not in said


def test_traders_and_thieves_do_not_single_the_scrap_out():
    import theft
    import traders
    s = _scrap()
    assert traders.refusal({'buys': 'all'}, s, known=True, cursed_known=False) == 'Not for sale'
    from items import load_items
    corpse_like = next(i for i in load_items('food'))
    corpse_like.item_class = 'corpse'
    assert traders.refusal({'buys': 'all'}, corpse_like, known=True, cursed_known=False) == 'Not for sale'
    g = _game('__test_scrap_thief__')
    g.player.inventory.append(s)
    assert s not in theft.stealable(g.player)


# ===========================================================================
# 2. The Bloomleaf Cloak (3.8)
# ===========================================================================

def _cloak():
    import emberpup_encounter as bloomleaf
    return bloomleaf.make_cloak()


def test_the_cloak_is_a_light_unique_cloak_that_keeps_rust_off():
    import items
    import traders
    c = _cloak()
    assert c.name == 'Bloomleaf Cloak' and c.slot == 'cloak' and c.weight_class == 'light'
    assert c.special_properties.get('rustproof_wearer') is True
    assert c.is_unique and items.withheld(c)
    assert c.id in items.scripted_only_ids()                 # never random loot, chests or stock
    assert traders.refusal({'buys': 'all'}, c, known=True, cursed_known=False) == 'Not for sale'
    raw = _data(os.path.join('items', 'armor.json'))['bloomleaf_cloak']
    assert 'Bloomsaur' in raw['lore'] and 'rust' in raw['lore']
    assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', 'bloomleaf_cloak.png'))
    import renderer
    assert renderer._resolve_item_sprite_path('bloomleaf_cloak').endswith('bloomleaf_cloak.png')


def test_thieves_skip_the_cloak():
    import theft
    g = _game('__test_cloak_thief__')
    c = _cloak()
    g.player.inventory.append(c)
    assert c not in theft.stealable(g.player)


def _iron_sword(enchant=2):
    from items import instantiate_weapon
    return instantiate_weapon('longsword', 'iron', enchant=enchant)


def test_the_cloak_stops_a_rust_trap():
    g = _game('__test_cloak_trap__')
    sword = _iron_sword()
    g.player.weapon = sword
    g.player.armor_slots = [_cloak()]
    x, y = g.player.x, g.player.y
    g.dungeon.traps[(x, y)] = {'type': 'rust', 'message': 'A gush of water hits you!'}
    g._check_floor_trap(x, y, forced=True)
    assert sword.enchant_bonus == 2
    assert any('keeps the rust from your gear' in t for t in _texts(g))
    # Without it the same trap rusts the sword.
    g.player.armor_slots = []
    g.dungeon.traps[(x, y)] = {'type': 'rust', 'message': 'A gush of water hits you!'}
    g._check_floor_trap(x, y, forced=True)
    assert sword.enchant_bonus == 1


def test_the_cloak_stops_the_rust_monster(monkeypatch):
    from monster import Monster
    from player import Player
    mons = _data('monsters.json')
    rm = Monster({**mons['rust_monster'], 'id': 'rust_monster'}, 1, 1)
    atk = dict(mons['rust_monster']['attacks'][0], effect_chance=1.0)
    p = Player()
    sword = _iron_sword(1)
    p.weapon, p.shield, p.ranged_weapon = sword, None, None
    p.armor_slots = [_cloak()]
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    rm._apply_attack_effect(atk, p)
    assert sword.enchant_bonus == 1
    p.armor_slots = []
    rm._apply_attack_effect(atk, p)
    assert sword.enchant_bonus == 0


# ===========================================================================
# 3. Old Nickel, who wears it (3.8)
# ===========================================================================

def test_old_nickel_is_a_greedy_quest_only_kobold_who_drops_the_cloak():
    m = _data('monsters.json')['old_nickel']
    assert m['family'] == 'goblinkin' and 'kobold' in m['tags']
    assert m['is_mini_boss'] and m['quest_only'] and m['peak_weight'] == 0
    assert 'spawn_chance' not in m                                   # not in the planned pool
    assert m['treasure']['unique_drop_id'] == 'bloomleaf_cloak' and m['treasure']['item_chance'] == 0
    assert 'cloak of broad green leaves' in m['sight_sign']
    lore = m['lore'].lower()
    for w in ('stolen', 'tore', 'kicks', 'cobalt', 'nickel'):
        assert w in lore, w
    assert m['wary']['warn'] and set(m['wary']['provoked']) == {'struck', 'cornered', 'close'}
    assert _data('monster_sizes.json')['sizes']['old_nickel'] == 'small'
    assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters', 'old_nickel.png'))


def test_old_nickel_never_spawns_at_random():
    import dungeon
    for lvl in range(1, 12):
        assert 'old_nickel' not in dungeon._floor_pool(lvl)


def test_his_floor_is_drawn_from_one_to_the_pups_on_every_seed():
    import emberpup_encounter as bloomleaf
    import emberpup_encounter as ep
    seen = set()
    for s in range(400):
        random.seed(s)
        st = ep.new_run_state()
        assert 1 <= st['cloak_floor'] <= st['floor'], st
        seen.add(st['cloak_floor'])
    assert seen == set(range(1, 9))
    # A planned mini-boss's floor is skipped while another is free.
    rng = random.Random(3)
    assert all(bloomleaf.draw_floor(rng, 4, exclude={1, 2, 3}) == 4 for _ in range(50))
    assert bloomleaf.draw_floor(rng, None) is None


def test_the_draw_leaves_the_shared_random_stream_alone():
    import emberpup_encounter as ep
    random.seed(77)
    before = random.getstate()
    ep.new_run_state()
    assert random.getstate() == before


def _walk_to(g, floor):
    for lvl in range(g.dungeon_level + 1, floor + 1):
        g._change_level(lvl, enter_from_top=True)


def test_he_is_placed_on_his_floor_never_in_the_pups_room():
    import emberpup_encounter as bloomleaf
    import emberpup_encounter as ep
    checked = 0
    for seed in (2, 5, 9, 14, 21, 33):
        g = _game(f'__test_nickel_place_{seed}__', seed=seed)
        pf = g._emberpup['floor']
        g._emberpup['cloak_floor'] = pf               # the hard case: the pup's own floor
        g._emberpup['cloak_spawned'] = False
        _walk_to(g, pf)
        wear = [m for m in g.monsters if bloomleaf.is_wearer(m) and m.alive]
        pups = [m for m in g.monsters if ep.is_emberpup(m)]
        assert len(wear) == 1 and len(pups) == 1, seed
        nick, pup = wear[0], pups[0]
        rooms = g.dungeon.rooms
        assert bloomleaf._room_of(rooms, nick.x, nick.y) is not bloomleaf._room_of(rooms, pup.x, pup.y)
        assert g._needed_to_finish(nick)
        walk = g._reachable_tiles(g.player.x, g.player.y)
        assert any((nick.x + dx, nick.y + dy) in walk for dx in (-1, 0, 1) for dy in (-1, 0, 1)), seed
        checked += 1
    assert checked == 6


def test_he_waits_only_on_his_floor_and_only_once():
    import emberpup_encounter as bloomleaf
    g = _game('__test_nickel_once__', seed=4)
    g._emberpup['cloak_floor'] = 3
    counts = {}
    for lvl in (2, 3, 4):
        g._change_level(lvl, enter_from_top=True)
        counts[lvl] = sum(1 for m in g.monsters if bloomleaf.is_wearer(m))
    g._change_level(3, enter_from_top=False)
    counts['back'] = sum(1 for m in g.monsters if bloomleaf.is_wearer(m))
    assert counts == {2: 0, 3: 1, 4: 0, 'back': 1}


def _nickel_room(seed=6):
    """Old Nickel set down on a fresh floor, nothing else in it, in a room
    big enough to stand five steps off him (the first seed from `seed` that
    gives one)."""
    import emberpup_encounter as bloomleaf
    for s in range(seed, seed + 40):
        g = _game(f'__test_nickel_ai_{s}__', seed=s)
        g._change_level(2, enter_from_top=True)
        g.monsters = []
        g.pets = []
        g.dungeon.traps = {}
        g._emberpup.update({'cloak_floor': 2, 'cloak_spawned': False})
        g._maybe_spawn_cloak_wearer(2)
        nick = next(m for m in g.monsters if bloomleaf.is_wearer(m))
        if nick._wary_home and _spot(g, nick, 5) and _spot(g, nick, 4):
            return g, nick
    raise AssertionError('no room big enough in 40 seeds')


def _spot(g, nick, dist):
    import senses
    x0, y0, x1, y1 = nick._wary_home
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            if (g.dungeon.is_walkable(x, y) and max(abs(x - nick.x), abs(y - nick.y)) == dist
                    and senses.clear_view(nick.x, nick.y, x, y, g.dungeon)):
                return (x, y)
    return None


def _put_hero(g, nick, dist):
    spot = _spot(g, nick, dist)
    if spot is None:
        return False
    g.player.x, g.player.y = spot
    g._refresh_fov()
    return True


def test_he_watches_warns_once_and_keeps_his_distance_without_attacking():
    g, nick = _nickel_room()
    assert _put_hero(g, nick, 4)
    g._sees_monster = lambda m: True              # (a dark room hides him; the lines are the point)
    hp = g.player.hp
    home = nick._wary_home
    for _ in range(6):
        g._advance_turn()
        assert home[0] <= nick.x <= home[2] and home[1] <= nick.y <= home[3]
    assert g.player.hp == hp and not nick._provoked
    log = _texts(g, 30)
    assert sum('pulls his leaf cloak tight' in t for t in log) == 1
    assert any('cloak of broad green leaves' in t for t in log)         # the sign, at first sight


def test_he_fights_when_the_hero_comes_beside_him():
    import monster
    g, nick = _nickel_room()
    assert _put_hero(g, nick, 1)
    assert nick.take_turn(g.player, g.dungeon, g.monsters) is True
    assert nick._provoked and 'Too close' in nick._wary_line
    assert nick.ai_pattern == 'aggressive' and monster.the_name(nick) == 'Old Nickel'


def test_he_fights_when_struck_first_from_afar():
    g, nick = _nickel_room()
    assert _put_hero(g, nick, 4)
    nick.take_damage(3)
    assert nick.take_turn(g.player, g.dungeon, g.monsters) is False     # not beside him yet
    assert nick._provoked and 'Thief' in nick._wary_line


def test_cornered_he_turns_on_the_hero():
    g, nick = _nickel_room()
    assert _put_hero(g, nick, 2)
    nick._wary_home = (nick.x, nick.y, nick.x, nick.y)                   # nowhere left to back off
    nick.take_turn(g.player, g.dungeon, g.monsters)
    assert nick._provoked and nick._wary_line.startswith('Cornered')


def test_he_swipes_at_no_pet_until_provoked():
    from pet_system import Pet
    g, nick = _nickel_room()
    assert _put_hero(g, nick, 5)
    pet = Pet('water', nick.x + 1, nick.y)
    if not g.dungeon.is_walkable(pet.x, pet.y):
        pet.x, pet.y = nick.x - 1, nick.y
    g.pets = [pet]
    hp = pet.hp
    g._monster_swipes([pet])
    assert pet.hp == hp


def test_killing_him_costs_no_karma_notes_the_deed_and_drops_the_cloak_identified():
    import emberpup_encounter as bloomleaf
    import deeds
    g, nick = _nickel_room()
    g.karma = 2
    nick.hp = 0
    nick.alive = False
    g._on_monster_killed(nick)
    assert g.karma == 2
    assert deeds.has(g._deeds_reg(), 'slew.old_nickel')
    assert not any('cruelty' in str(t) for d in g._deeds_reg().get('deeds', []) for t in (d.get('tags') or ()))
    cloaks = [i for i in g.ground_items if bloomleaf.is_cloak(i)]
    assert len(cloaks) == 1
    c = cloaks[0]
    assert c.identified and c.id_level == 5 and c.buc_known and c.buc == 'uncursed'
    from chronicle import text_of
    assert any('Old Nickel' in text_of(e) for e in g._chronicle)


def test_a_banished_nickel_still_leaves_the_cloak():
    import emberpup_encounter as bloomleaf
    g, nick = _nickel_room()
    nick._banished = True
    nick.alive = False
    g._on_monster_killed(nick)
    assert len([i for i in g.ground_items if bloomleaf.is_cloak(i)]) == 1


def test_qa_shift_l_sets_him_down_then_gives_the_cloak():
    import emberpup_encounter as bloomleaf
    g = _game('__test_qa_l__')
    g.player.qa_tools = True
    g.monsters = [m for m in g.monsters if not bloomleaf.is_wearer(m)]
    g._qa_bloomleaf()
    assert any(bloomleaf.is_wearer(m) for m in g.monsters)
    g._qa_bloomleaf()
    assert any(bloomleaf.is_cloak(i) for i in g.player.inventory)
    g.player.qa_tools = False
    n = len(g.player.inventory)
    g._qa_bloomleaf()
    assert len(g.player.inventory) == n


# ===========================================================================
# 4. The Emberpup: only the leaf cloak, three feeds with time between (3.8b)
# ===========================================================================

def _pup_game(name='__test_pup_trust__', floor=6):
    import emberpup_encounter as ep
    g = _game(name)
    g.monsters = []
    g.dungeon.traps = {}
    g._emberpup = {'floor': floor, 'spawned': False, 'outcome': None,
                   'cloak_floor': None, 'cloak_spawned': True}
    g.dungeon_level = floor
    g._maybe_spawn_emberpup(floor)
    pup = next(m for m in g.monsters if ep.is_emberpup(m))
    pup._emberpup_met = True
    from items import load_items, Food
    foods = [f for f in load_items('food') if isinstance(f, Food) and f.id != 'magic_dungeon_carrot']
    for i in range(6):
        f = copy.copy(foods[i % len(foods)])
        f.identified = True
        f.count = 1
        g.player.inventory.append(f)
    return g, pup


def _feed(g, pup):
    g._start_emberpup_encounter(pup)
    if g._emberpup_phase == 'outcome':
        return g._emberpup_text                  # too soon: no choices at all
    g._emberpup_input(pygame.K_1)
    if g._emberpup_phase == 'select_food':
        g._emberpup_input(pygame.K_a)
    text = g._emberpup_text
    g._close_emberpup()
    return text


def test_three_feeds_each_after_the_gap_each_with_its_own_warmer_line():
    import emberpup_encounter as ep
    d = ep.data()
    assert d['visits_needed'] == 3 and 20 <= d['feed_gap_turns'] <= 30
    g, pup = _pup_game()
    said = []
    for n in range(3):
        said.append(_feed(g, pup))
        assert ep.feeds(pup) == n + 1
        g.turn_count += d['feed_gap_turns']
    names = [n for n in said]
    assert len(set(names)) == 3
    # Brandon's own first two steps: watching carefully, then lingering.
    assert 'watching you carefully' in said[0] and 'still wary, and still hurt' in said[0]
    assert 'scampers away' in said[1] and 'lingers' in said[1] and 'relax' in said[1]
    assert 'does not run' in said[2]
    # Each step shows on the choices screen too.
    assert len({ep.data()['waiting'][i] for i in range(4)}) == 4
    assert ep.waiting_text(pup) == d['waiting'][3]


def test_too_soon_he_is_still_eating_and_it_does_not_count():
    import emberpup_encounter as ep
    from game_states import STATE_PLAYER
    d = ep.data()
    g, pup = _pup_game('__test_pup_soon__')
    _feed(g, pup)
    food = len(ep.food_choices(g.player.inventory))
    fed_at = g._emberpup['fed_turn']
    g.turn_count = fed_at + d['feed_gap_turns'] - 1
    # Bumped too soon: only the too-soon line, no choices, no turn passes.
    g._start_emberpup_encounter(pup)
    assert g._emberpup_text == d['too_soon'][0] == (
        "The Emberpup, still eating the treat you provided, growls and backs away as you approach.")
    g._emberpup_input(pygame.K_RETURN)
    assert g.state == STATE_PLAYER and g.turn_count == fed_at + d['feed_gap_turns'] - 1
    assert ep.feeds(pup) == 1 and len(ep.food_choices(g.player.inventory)) == food
    # Fed too soon from his screen (straight after a feed): the same line.
    g.turn_count = fed_at + d['feed_gap_turns']
    g._start_emberpup_encounter(pup)
    g._emberpup_input(pygame.K_1)
    g._emberpup_input(pygame.K_a)
    assert ep.feeds(pup) == 2
    g._emberpup_input(pygame.K_RETURN)
    g._emberpup_input(pygame.K_1)
    # Two feeds in: still too soon, and the line shows his trust has moved.
    assert g._emberpup_text == d['too_soon'][1] and ep.feeds(pup) == 2
    assert 'does not run' in g._emberpup_text


def test_leaving_his_floor_counts_as_waiting():
    import emberpup_encounter as ep
    g, pup = _pup_game('__test_pup_away__')
    _feed(g, pup)
    g._emberpup_left(6, 7)
    assert g._emberpup['away']
    assert ep.feeds(pup) == 1
    _feed(g, pup)
    assert ep.feeds(pup) == 2 and not g._emberpup['away']


def test_only_the_bloomleaf_cloak_keeps_his_rain_off():
    import emberpup_encounter as ep
    from items import load_items, Armor
    d = ep.data()
    g, pup = _pup_game('__test_pup_cloak__')
    g.player.inventory = [i for i in g.player.inventory if not isinstance(i, Armor)]
    g.player.shield = None
    g._start_emberpup_encounter(pup)
    g._emberpup_input(pygame.K_5)
    assert g._emberpup_text == d['no_shelter'] and 'A cloak of leaves would turn this rain' in d['no_shelter']
    other = copy.copy(next(a for a in load_items('armor') if a.slot == 'cloak' and a.id != 'bloomleaf_cloak'))
    g.player.inventory.append(other)
    g._emberpup_input(pygame.K_RETURN)
    g._emberpup_input(pygame.K_5)
    assert 'A cloak of leaves would turn this rain' in g._emberpup_text
    assert not getattr(pup, '_emberpup_sheltered', False) and other in g.player.inventory
    # Worn, it has to come off first.
    leaf = _cloak()
    g.player.armor_slots = [leaf]
    g._emberpup_input(pygame.K_RETURN)
    g._emberpup_input(pygame.K_5)
    assert g._emberpup_text == d['take_off'] and 'leaf cloak' in d['take_off']
    g.player.armor_slots = []
    g.player.inventory.append(leaf)
    g._emberpup_input(pygame.K_RETURN)
    g._emberpup_input(pygame.K_5)
    assert pup._emberpup_sheltered and leaf not in g.player.inventory
    assert pup._emberpup_cloak is leaf and pup.sprite_id == 'npc_abandoned_emberpup_sheltered'
    assert ep.sprite_of(pup) == 'npc_abandoned_emberpup_sheltered'
    assert d['waiting_sheltered'] in ep.waiting_text(pup)
    assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters',
                                       'npc_abandoned_emberpup_sheltered.png'))


def test_his_story_tells_of_a_hard_master_and_says_he():
    import emberpup_encounter as ep
    d = ep.data()
    story = ' '.join(d['story'])
    assert 'hard on him' in story and 'bigger' in story and 'rain' in story
    assert 'trainer' not in json.dumps(d) and 'come back for you' not in story.lower()
    # Brandon's word is "he": no line calls the pup "it".
    for k, v in d.items():
        for line in (v if isinstance(v, list) else [v] if isinstance(v, str) else []):
            if k.startswith('_') or k in ('name', 'title', 'sprite_id', 'sprite_sheltered', 'pet_species'):
                continue
            low = f" {line.lower()} "
            for bad in (' its rock', ' it trusts', ' it flinches', ' it eats', ' its tail', ' its own',
                        ' it looks', ' it is cold', ' it waits', 'see it again'):
                assert bad not in low, (k, line)


def test_save_and_load_mid_trust_keeps_his_feeds_the_gap_and_the_cloak(tmp_path, monkeypatch):
    import emberpup_encounter as ep
    import save_system
    from main import Game
    name = '__test_pup_save_trust__'
    g, pup = _pup_game(name)
    g.player_name = name
    _feed(g, pup)
    g._emberpup['cloak_floor'] = 4
    pup._emberpup_sheltered = True
    pup._emberpup_cloak = ep.make_cloak()        # the Bloomleaf Cloak: nothing else counts (WB-C03)
    pup.sprite_id = ep.sprite_of(pup)
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    save_system.settle_unfinished_actions(g)
    assert save_system.save_game(g)
    g2 = Game(_screen(), player_name=name)
    g2.load_state(save_system.load_game(name))
    pups = [m for m in g2.monsters if ep.is_emberpup(m)]
    assert len(pups) == 1
    p2 = pups[0]
    assert ep.feeds(p2) == 1 and p2._emberpup_sheltered and p2.sprite_id == 'npc_abandoned_emberpup_sheltered'
    assert g2._emberpup['cloak_floor'] == 4 and g2._emberpup['fed_once']
    g2.turn_count = g._emberpup['fed_turn'] + 1
    g2._start_emberpup_encounter(p2)
    assert g2._emberpup_text == ep.data()['too_soon'][0]     # the gap survives the reload


# ===========================================================================
# 5. He keeps the cloak, at every stage, and loses the line's water weakness
# ===========================================================================

def test_the_cloaked_pup_has_his_own_picture_at_every_stage():
    from pet_system import Pet, _SPECIES
    pet = Pet('fire')
    pet.bloomleaf = True
    for level, stage in ((1, 'emberpup'), (25, 'flamescale'), (55, 'infernodrake')):
        pet.level = level
        assert pet.sprite_id == f'{stage}_cloaked'
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters', f'{stage}_cloaked.png'))
        # the approved art is still there, untouched by name
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters', f'{stage}.png'))
    plain = Pet('fire')
    assert plain.sprite_id == 'emberpup' and not plain.bloomleaf
    assert [s['name'] for s in _SPECIES['fire']['stages']] == ['Emberpup', 'Flamescale', 'Infernodrake']


def test_the_fire_line_is_weak_to_water_but_not_the_cloaked_pup():
    from pet_system import Pet, harm_taken
    soul = Pet('fire')
    pup = Pet('fire')
    pup.bloomleaf = True
    assert soul.weak_to() == ('cold',) and pup.weak_to() == ()
    assert harm_taken(soul, 5, 'cold') == (10, True)
    assert harm_taken(pup, 5, 'cold') == (5, False)
    assert harm_taken(soul, 5, 'fire') == (5, False)
    assert Pet('water').weak_to() == ()


def test_his_evolution_and_his_card_say_he_wears_it():
    import emberpup_encounter as ep
    from pet_system import Pet
    pet = Pet('fire', level=24)
    pet.bloomleaf = True
    msgs = pet.gain_xp(pet._xp_to_next())
    assert any(ep.data()['evolved_cloaked'] in m for m in msgs)
    g = _game('__test_pup_card__')
    assert g._pet_cloak_lines(pet)[0][0] == ep.data()['pet_wears_cloak']
    assert g._pet_cloak_lines(Pet('fire')) == []


def test_adopted_he_keeps_the_cloak_through_a_save(tmp_path, monkeypatch):
    import save_system
    from main import Game
    from pet_system import Pet
    name = '__test_pup_pet_save__'
    g = _game(name)
    pet = Pet('fire', g.player.x + 1, g.player.y)
    pet.bloomleaf = True
    g.pets = [pet]
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    save_system.settle_unfinished_actions(g)
    assert save_system.save_game(g)
    g2 = Game(_screen(), player_name=name)
    g2.load_state(save_system.load_game(name))
    assert g2.pets and g2.pets[0].bloomleaf and g2.pets[0].sprite_id == 'emberpup_cloaked'


def test_an_escort_keeps_its_own_picture():
    from escort_system import Escort
    e = Escort({'id': 'lena', 'name': 'Lena', 'sprite_id': 'npc_lost_girl'}, 1, 1)
    assert e.sprite_id == 'npc_lost_girl'


# ===========================================================================
# 6. The unicorn: every step of her trust has a line (3.8b)
# ===========================================================================

def _unicorn(g):
    from monster import Monster
    u = Monster({'id': 'ethereal_unicorn', 'name': 'Ethereal Unicorn', 'symbol': 'u',
                 'color': [255, 255, 240], 'hp': 200, 'thac0': 20, 'speed': 10, 'attacks': [],
                 'ai_pattern': 'sessile', 'is_allied': True}, g.player.x + 3, g.player.y)
    u._is_unicorn = True
    u._unicorn_state = 'wary'
    u._unicorn_wait = 0
    u._unicorn_eat_turns = 0
    g.monsters = [u]
    return u


def test_the_unicorns_every_state_change_says_so():
    g = _game('__test_unicorn_lines__')
    L = g._UNICORN_LINES
    u = _unicorn(g)
    g.visible = {(u.x, u.y)}
    g._tick_unicorn()
    assert _texts(g, 1)[0] == L['first_seen']
    g._tick_unicorn()
    assert _texts(g, 1)[0] == L['watching']
    g._tick_unicorn()
    assert _texts(g, 1)[0] == L['relaxing'] and u._unicorn_state == 'relaxing'
    carrot = next(f for f in __import__('items').load_items('food') if f.id == 'magic_dungeon_carrot')
    carrot = copy.copy(carrot)
    carrot.x, carrot.y = u.x + 1, u.y
    g.ground_items.append(carrot)
    g._tick_unicorn()
    assert _texts(g, 1)[0] == L['eating'] and u._unicorn_state == 'eating'
    g._tick_unicorn()
    g._tick_unicorn()
    assert _texts(g, 1)[0] == L['trusting'] and u._unicorn_state == 'trusting'


def test_the_unicorn_says_too_soon_and_when_she_loses_sight_of_you():
    g = _game('__test_unicorn_soon__')
    L = g._UNICORN_LINES
    for state, key in (('wary', 'too_soon_wary'), ('relaxing', 'too_soon_relaxing'),
                       ('eating', 'too_soon_eating')):
        u = _unicorn(g)
        u._unicorn_state = state
        g._handle_unicorn_bump(u)
        assert key in L and L[key] in _texts(g, 3) and 'Too soon' in L[key]
        assert u._unicorn_state == 'wary'
    u = _unicorn(g)
    g.visible = {(u.x, u.y)}
    g._tick_unicorn()
    g._tick_unicorn()
    g.visible = set()
    g._tick_unicorn()
    assert _texts(g, 1)[0] == L['lost']
    g.visible = {(u.x, u.y)}
    g._tick_unicorn()
    assert _texts(g, 1)[0] == L['seen_again']


# ===========================================================================
# 7. Other multi-step encounters: an escort's floors, an oath running out
# ===========================================================================

def test_an_escort_says_how_many_floors_are_left():
    from escort_system import Escort, progress_line
    e = Escort({'id': 'lena', 'name': 'Lena', 'floors': 3}, 1, 1)
    e.floors_left = 2
    assert progress_line(e) == "Lena keeps close on the stair. Two more floors to go."
    e.floors_left = 1
    assert progress_line(e) == "Lena keeps close on the stair. One more floor to go."
    e.spec['progress'] = "{name} counts the stairs under her breath: {floors}."
    assert progress_line(e) == "Lena counts the stairs under her breath: one more floor."


def test_an_oath_running_out_is_said_in_the_log():
    import game_road
    assert game_road.RoadMixin._lapse_notice({'to': 'brother tuck'}) == "Your promise to Brother Tuck has run out."
    assert game_road.RoadMixin._lapse_notice({}) == "A promise you made has run out."
