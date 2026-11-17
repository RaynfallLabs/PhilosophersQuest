"""Bug bash on the winning build (2026-11-13), area C: the world, encounters
and maths (slices 6, 8 and 9, and the Stray Kids easter egg).

Each test names its finding (WB-C01 ...). The rules are deep, randomized or
need an old save, so a play-test cannot reach them on demand: these are the
proof, on a real headless Game where the game is involved.
"""
import copy
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(name='__test_wb_c__', seed=11):
    import items
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.state = STATE_PLAYER
    return g


def _texts(g, n=12):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


# ===========================================================================
# WB-C01: an altar's points count against food's cap, both ways round
# ===========================================================================

def test_wb_c01_cooking_counts_what_an_altar_gave():
    """rededication.py: "points an altar gives count against the same cap as
    points a meal gives". The altar read the kitchen's ledger, but the
    kitchen never read the altar's: two points rededicated into Strength
    first, then cooked to the cap, put Strength two past what food could
    teach it."""
    import rededication as R
    from player import Player
    p = Player()
    p.deepest_floor_reached = 4
    cap = p.cooking_stat_softcap('STR')
    p.stats_at_start = {s: getattr(p, s) for s in R.STATS}
    p.apply_stat_bonus('DEX', 3)
    p.cooking_stat_gained['DEX'] = 3              # three cooked points to give back
    n = R.points_to_move(p, 'DEX', 'STR', 5)
    assert n == 2
    R.move(p, 'DEX', 'STR', n)
    for _ in range(40):                           # forty floors' worth of Strength meals
        p._cook_stat_gain_this_floor = 0
        p.feed_cut_stat('STR', 1)                 # dishes of the altar's band (tier 1)
    assert R.taught(p, 'STR') == cap
    assert p.STR == 10 + cap
    assert p.cut_stat_block('STR', 1) == 'tier'   # the meal card says so too
    assert p.apply_cooking_stat_bonus('STR', 2) == 0      # a rare food's own bonus as well
    # A point given back never frees the kitchen's room (its own ledger).
    assert R.taught(p, 'DEX') == 3


# ===========================================================================
# WB-C02: what a worn legend lends is not the hero's to give back
# ===========================================================================

def test_wb_c02_a_chain_items_tier_points_are_lent_not_his_own():
    """rededication.lent counted rings, carried keepsakes, draughts and
    Gawain's surge, but not a chain-attuned legend's tier bonuses (the
    Necklace of Harmonia's Wisdom), Hofud's +2 Perception or the point of
    Strength the Pelops sword takes: the hero could give back a lent point
    and end below where he began once the piece came off."""
    import chain_equip
    import rededication as R
    from items import make_item_by_id
    from player import Player
    p = Player()
    p.stats_at_start = {s: getattr(p, s) for s in R.STATS}
    neck = make_item_by_id('accessory', 'necklace_of_harmonia')
    p.amulet_slot = neck
    p.sync_worn_stats()                           # its own +4 Wisdom, -2 Constitution (the worn ledger)
    chain_equip.apply_tier_bonuses(p, neck, 1)    # attuned: +2 Wisdom, -1 Constitution
    assert p.WIS == 16 and p.CON == 7
    assert R.give_room(p, 'WIS') == 0
    assert R.own_value(p, 'WIS') == 10 and R.own_value(p, 'CON') == 10
    hofud = make_item_by_id('weapon', 'hofud')
    p.weapon = hofud
    p._apply_weapon_passives(hofud)               # +2 Perception while wielded
    assert p.PER == 12 and R.give_room(p, 'PER') == 0
    pelops = make_item_by_id('weapon', 'pelops_sword')
    p._remove_weapon_passives(hofud)
    p.weapon = pelops
    p._apply_weapon_passives(pelops)              # takes a point of Strength
    assert p.STR == 9 and R.own_value(p, 'STR') == 10
    # And so nothing can move at an altar.
    assert not R.possible(p)


# ===========================================================================
# WB-C03: an old save's rain cover is not the Bloomleaf Cloak
# ===========================================================================

def _pup_game(name, floor=6):
    import emberpup_encounter as ep
    from items import load_items, Food
    g = _game(name)
    g.monsters = []
    g.dungeon.traps = {}
    g._emberpup = {'floor': floor, 'spawned': False, 'outcome': None,
                   'cloak_floor': None, 'cloak_spawned': True}
    g.dungeon_level = floor
    g._maybe_spawn_emberpup(floor)
    pup = next(m for m in g.monsters if ep.is_emberpup(m))
    pup._emberpup_met = True
    foods = [f for f in load_items('food') if isinstance(f, Food) and f.id != 'magic_dungeon_carrot']
    for i in range(4):
        f = copy.copy(foods[i % len(foods)])
        f.identified = True
        f.count = 1
        g.player.inventory.append(f)
    return g, pup


def test_wb_c03_an_old_saves_rain_cover_is_not_the_leaf_cloak():
    """A Dungeon Alive save (2026-11-12) let any cloak or shield shelter the
    pup and kept no record of which. Read by the new rules, that pup was
    "sheltered": he adopted as the cloaked Emberpup (the leaf-cloak art at
    every stage, no weakness to water, the leaf-cloak lines) though the hero
    never gave him the Bloomleaf Cloak, and the leaf cloak could no longer
    be given ("Your leaf cloak is still over his rock")."""
    import emberpup_encounter as ep
    from game_states import STATE_EMBERPUP, STATE_QUIZ
    d = ep.data()
    g, pup = _pup_game('__test_wb_c03__')
    # The old save: fed on his visits, a plain cloak left over his rock.
    pup._emberpup_feeds = 3
    pup._emberpup_fed = True
    pup._emberpup_sheltered = True
    g._emberpup.update({'fed_once': True, 'fed_turn': 0, 'away': True})
    g.turn_count = 500
    assert ep.sprite_of(pup) == d['sprite_id']
    assert d['waiting_sheltered'] not in ep.waiting_text(pup)
    assert not g._cloak_in_play()
    g._start_emberpup_encounter(pup)
    g._emberpup_input(pygame.K_4)                 # "I choose you!"
    assert g.state == STATE_EMBERPUP and g._emberpup_text == d['refused_cold']
    # The leaf cloak can still be given, and then he is the cloaked pup.
    g._emberpup_input(pygame.K_RETURN)
    leaf = ep.make_cloak()
    g.player.inventory.append(leaf)
    g._emberpup_input(pygame.K_5)
    assert pup._emberpup_cloak is leaf and leaf not in g.player.inventory
    assert ep.sprite_of(pup) == d['sprite_sheltered']
    g._emberpup_input(pygame.K_RETURN)
    g._emberpup_input(pygame.K_4)
    assert g.state == STATE_QUIZ


def test_wb_c03_only_the_leaf_cloak_makes_the_cloaked_pet():
    import emberpup_encounter as ep
    g, pup = _pup_game('__test_wb_c03_adopt__')
    pup._emberpup_sheltered = True                # an old save's cover
    g._emberpup_npc = pup
    g._emberpup_adopt(pup)
    assert g.pets and not g.pets[-1].bloomleaf and g.pets[-1].sprite_id == 'emberpup'
    g2, pup2 = _pup_game('__test_wb_c03_adopt2__')
    pup2._emberpup_sheltered = True
    pup2._emberpup_cloak = ep.make_cloak()
    g2._emberpup_npc = pup2
    g2._emberpup_adopt(pup2)
    assert g2.pets[-1].bloomleaf and g2.pets[-1].sprite_id == 'emberpup_cloaked'


# ===========================================================================
# WB-C04: the new services speak of the trader as he, she or it
# ===========================================================================

def _shop(g, kind, level=50):
    import random as _r
    from mystery_system import build_trader
    m = build_trader(kind, level, _r.Random(3))
    m.x, m.y = g.player.x + 1, g.player.y
    g.ground_items.append(m)
    g.dungeon_level = level
    g._trader_open(m)
    return m


def _service_text(g) -> str:
    from game_traders import TAB_SERVICES
    g._shop_tab = TAB_SERVICES
    menu = g._trader_menu()
    out = []
    for e in menu['entries']:
        for d in e.get('details') or ():
            if isinstance(d, tuple):
                out.append(str(d[0]))
    return ' '.join(out)


def test_wb_c04_the_new_services_use_the_traders_own_pronouns():
    """The trade-in and special-order descriptions said "from him... his
    price... his next stall" for every trader, and three "why" lines said
    "him" and "his": Mother Wort, Old Mags and Brunhild are "she" and Vesper
    is "it" (data/traders.json "pronoun")."""
    import re
    g = _game('__test_wb_c04__')
    plan = g._trader_plan()
    plan['floors'] = {50: 'dwarf_armourer'}       # her last stall
    g.player.weapon = None
    g.player.armor_slots = [None] * len(g.player.armor_slots)
    for kind in ('dwarf_armourer', 'apothecary', 'abyssal', 'sutler'):
        m = _shop(g, kind)
        said = _service_text(g)
        assert not re.search(r'\b(him|his|he)\b', said, re.I), (kind, said)
        if kind == 'dwarf_armourer':
            assert "This is her last stall" in said
            assert "for her to line" in said
        g.ground_items.remove(m)
    # A he says he.
    plan['floors'] = {50: 'armourer'}
    _shop(g, 'armourer')
    assert 'This is his last stall' in _service_text(g)


# ===========================================================================
# WB-C05: Old Nickel watches with eyes, not by knowing
# ===========================================================================

def _nickel(seed=6):
    import emberpup_encounter as bloomleaf
    import senses
    for s in range(seed, seed + 40):
        g = _game(f'__test_wb_c05_{s}__', seed=s)
        g._change_level(2, enter_from_top=True)
        g.monsters = []
        g.pets = []
        g.dungeon.traps = {}
        g._emberpup.update({'cloak_floor': 2, 'cloak_spawned': False})
        g._maybe_spawn_cloak_wearer(2)
        nick = next(m for m in g.monsters if bloomleaf.is_wearer(m))
        home = nick._wary_home
        if not home:
            continue
        for x in range(home[0], home[2] + 1):
            for y in range(home[1], home[3] + 1):
                if (g.dungeon.is_walkable(x, y) and max(abs(x - nick.x), abs(y - nick.y)) == 3
                        and senses.clear_view(nick.x, nick.y, x, y, g.dungeon)):
                    g.player.x, g.player.y = x, y
                    g._refresh_fov()
                    return g, nick
    raise AssertionError('no room big enough in 40 seeds')


def test_wb_c05_old_nickel_does_not_see_an_invisible_hero():
    """Monster._wary_turn tested a bare line of sight, so Old Nickel saw an
    invisible hero (and one in the Boots of Elvenkind at twice their reach):
    he warned him and backed away. Every other creature notices through
    senses.sees (Dungeon Alive ruling: no omniscient monsters). The stalker
    he became (Monster._stalker_turn, 2026-11-17) watches the same way."""
    g, nick = _nickel()
    at = (nick.x, nick.y)
    g.player.add_effect('invisible', 50)
    nick.take_turn(g.player, g.dungeon, g.monsters)
    assert not nick._aware and not nick._provoked and (nick.x, nick.y) == at
    # Seen, he knows him and keeps his distance.
    g.player.status_effects.pop('invisible', None)
    nick.take_turn(g.player, g.dungeon, g.monsters)
    assert nick._aware and nick._tracking and not nick._provoked


# ===========================================================================
# WB-C06: the band shrugs off polymorph, so the photo is never lost
# ===========================================================================

def test_wb_c06_a_band_member_resists_polymorph():
    """A wand or spell of polymorph turned a zombie band member into some
    ordinary creature: out of the band for good, and if he was the last one
    standing, the stage was "cleared" with no photo, ever (the photo drops
    only from the last member's death). The Black Knight and the mini-bosses
    already shrug it off."""
    import stray_kids as sk
    from items import load_items
    g = _game('__test_wb_c06__')
    g.monsters = []
    x, y = g.player.x + 2, g.player.y
    m = sk.make_zombie('felix', x, y, 5)
    g.monsters.append(m)
    wand = copy.copy(next(w for w in load_items('wand') if w.id == 'wand_of_polymorph'))
    g._wand_override_target = m
    random.seed(3)
    g._apply_wand_effect(wand)
    assert g.monsters[0] is m and sk.is_zombie(g.monsters[0])
    assert any('resists' in t for t in _texts(g, 4))
    # The spell's path too.
    g._cast_spell_effect({'effect': 'polymorph_spell', 'id': 'polymorph_spell', 'name': 'Polymorph',
                          'power': '', 'tier': 3}, target=m)
    assert g.monsters[0] is m and sk.is_zombie(g.monsters[0])
    # The last to fall still leaves the photo.
    m.hp = 0
    m.alive = False
    g._on_monster_killed(m)
    assert any(getattr(i, 'id', '') == sk.photo_id() for i in g.ground_items)


# ===========================================================================
# WB-C07: Old Nickel and the Road's people keep apart
# ===========================================================================

def _npc(g, x, y, tag='_wb_c07'):
    from monster import Monster
    m = Monster({'id': 'npc_traveler', 'name': 'A Traveller', 'symbol': '@', 'color': [1, 1, 1],
                 'hp': 1, 'thac0': 20, 'speed': 0, 'attacks': [], 'ai_pattern': 'sessile',
                 'resistances': [], 'weaknesses': [], 'min_level': 1, 'is_allied': True,
                 'harvest_tier': 0, 'harvest_threshold': 99, 'ingredient_id': None}, x, y)
    m._flavor_encounter_tag = tag
    g.monsters.append(m)
    return m


def test_wb_c07_old_nickel_never_takes_a_room_with_a_road_encounter():
    """Slice 11 kept Old Nickel out of a stall's room (the hero would have
    to corner him, and fight, just to trade), but not out of a room where a
    Road anchor or a story NPC stands: about one run in thirty set them in
    one room, and talking to the NPC meant cornering him."""
    import emberpup_encounter as ep
    for seed in (3, 8, 15):
        g = _game(f'__test_wb_c07_{seed}__', seed=seed)
        g._change_level(2, enter_from_top=True)
        # (The floor's own Road people, whose floors the Road's seed decides,
        # are taken off: these are placed by hand.)
        g.monsters = [m for m in g.monsters if not ep.is_wearer(m) and not ep._is_road_person(m)]
        # Nor a war-band's camp (bug bash 3.5.1): the one room left free
        # here could be the camp, which he never takes either.
        g.dungeon.band = None
        rooms = g.dungeon.rooms
        here = ep._room_of(rooms, g.player.x, g.player.y)
        free = [r for r in rooms[1:] if r is not here]
        assert len(free) >= 2
        far = [r for r in free if any(g.dungeon.is_walkable(*t) and max(abs(t[0] - g.player.x),
                                                                       abs(t[1] - g.player.y)) > 2
                                      for t in r.inner_tiles())]
        keep = far[-1]
        free = [r for r in free if r is not keep] + [keep]
        for r in free[:-1]:
            t = next((t for t in r.inner_tiles() if g.dungeon.is_walkable(*t)), None)
            if t is not None:
                _npc(g, *t, tag=f'_wb_c07_{id(r)}')
        g._emberpup.update({'cloak_floor': 2, 'cloak_spawned': False})
        g._maybe_spawn_cloak_wearer(2)
        nick = next(m for m in g.monsters if ep.is_wearer(m))
        assert ep._room_of(rooms, nick.x, nick.y) is keep, seed


def test_wb_c07_a_road_npc_is_never_set_down_in_his_room():
    import emberpup_encounter as ep
    g = _game('__test_wb_c07_npc__', seed=5)
    g._change_level(2, enter_from_top=True)
    g.monsters = []
    g._emberpup.update({'cloak_floor': 2, 'cloak_spawned': False})
    g._maybe_spawn_cloak_wearer(2)
    nick = next(m for m in g.monsters if ep.is_wearer(m))
    home = nick._wary_home
    assert home
    enc = {'tag': '_wb_c07_road', 'name': 'A Traveller', 'symbol': '@', 'color': [1, 1, 1]}
    for i in range(12):
        npc = g._spawn_encounter_npc(dict(enc, tag=f'_wb_c07_road_{i}'), '_flavor_encounter_tag', 2)
        assert npc is not None
        assert not (home[0] <= npc.x <= home[2] and home[1] <= npc.y <= home[3]), i


# ===========================================================================
# WB-C08: Old Nickel's warning is never spent where it cannot be seen
# ===========================================================================

def test_wb_c08_a_warning_given_in_the_dark_is_given_again():
    """He warns once ("Mine. All of it. Go away, big one."), the line that
    tells the hero he is not hostile. He sees farther than the hero does in a
    dark room, so the warning was often given while the hero could not see
    him: the line was dropped and the warning spent for good. His first-sight
    line (data/old_nickel.json 'sight', 2026-11-17) waits the same way."""
    import old_nickel
    g, nick = _nickel()

    def sight(log):
        return [t for t in log if t.startswith('Old Nickel: "')
                and t[len('Old Nickel: "'):-1] in old_nickel.lines('sight')]
    g._sees_monster = lambda m: False             # a dark room: he is not seen
    for _ in range(3):
        g._advance_turn()
    assert not sight(_texts(g, 40))
    g._sees_monster = lambda m: True              # now he is
    for _ in range(4):
        g._advance_turn()
    assert len(sight(_texts(g, 40))) == 1
    assert not nick._provoked


# ===========================================================================
# WB-C09: an unmarked counter does not name itself by standing first
# ===========================================================================

def test_wb_c09_an_unmarked_counter_is_not_always_first_on_the_shelf():
    """domain_counters: "a consumable counter (a wand, a potion, a book) goes
    on the shelf unmarked, and the line names only what to look for". But
    the counters were racked first, every stall: "You'll want something
    holy" and an unknown wand at the top of the list named the Wand of
    Sunburst; Grindle's first wand was always the fire wand. A kid learned
    the look of a wand without the philosophy question."""
    import items
    from mystery_system import build_trader
    firsts, seen = [], 0
    for kind, lvl in (('apothecary', 30), ('generalist', 25), ('bookseller', 30),
                      ('abyssal', 70), ('sutler', 39), ('apothecary', 12)):
        for seed in range(6):
            items.bind_unique_registry(set())
            m = build_trader(kind, lvl, random.Random(seed))
            info = m.counter or {}
            if info.get('marked', True):
                continue
            seen += 1
            counters = [it for it in m.stock if getattr(it, '_shelf_counter', False)]
            assert not counters                     # the build's own flag never stays on a ware
            firsts.append(getattr(m.stock[0], 'item_class', '') in ('wand', 'potion', 'spellbook', 'flask')
                          and getattr(m.stock[0], '_counter', None) is None)
            # The wares themselves are all still there.
            assert len({id(it) for it in m.stock}) == len(m.stock)
    assert seen >= 20
    # Not first on every shelf any more (it is somewhere on the shelf).
    assert sum(firsts) < seen * 0.7, (sum(firsts), seen)
