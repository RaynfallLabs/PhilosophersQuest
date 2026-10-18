"""Wiring audit of the Soul Spheres, coin weight, treasure and the Draught of
Mimir's Well (2026-10-18, Brandon: "make sure all of this is fully wired to
EVERY system").

Each test pins one seam the audit found broken and fixed. They drive a real
headless Game (or the real generator), not the source text:

* a rolled floor sphere whose room was already full vanished (maze floors);
* a swamp room flooded tiles that loot already lay on (a sphere in the water);
* a prayer's blessing named an unidentified item by its TRUE name, and spent
  itself on treasure or a sphere, which take no blessing;
* treasure (known by sight, never cursed) could be blessed, cursed, or
  "forgotten" by a cursed Scroll of Identify and then offered for identifying;
* an altar took a gem worth far more than its tribute, with no change, and
  the card never said so;
* the pets doc quoted the bound sphere's lore with a singular "them".
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import items  # noqa: E402
import pet_system  # noqa: E402,F401  (monkeypatched through sys.modules)
import treasure  # noqa: E402

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__test_wiring_audit__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _texts(g, n=8):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


# ---------------------------------------------------------------- spawning

def test_a_rolled_floor_sphere_goes_to_another_room_when_its_own_is_full(monkeypatch):
    """The floor's sphere roll picks a room; when no floor tile in it is free
    the sphere goes to the next room, never silently lost."""
    from dungeon import FLOOR, WATER, generate_dungeon, spawn_items
    random.seed(3)
    d = generate_dungeon(80, 50, 5)
    rooms = sorted(d.rooms, key=lambda r: r.width * r.height, reverse=True)
    roomy, full = rooms[0], rooms[1]
    for x, y in full.inner_tiles():                 # nothing can be laid here
        if d.tiles[y][x] == FLOOR:
            d.tiles[y][x] = WATER
    monkeypatch.setattr(sys.modules['pet_system'], 'sphere_for_floor',
                        lambda level, rng: 'soul_sphere')
    # rooms[1:] is just the full room, so the roll can only pick it.
    got = spawn_items([roomy, full], 5, d, structures=False)
    spheres = [i for i in got if getattr(i, 'id', '') == 'soul_sphere']
    assert len(spheres) == 1
    s = spheres[0]
    assert (s.x, s.y) in set(roomy.inner_tiles()) and d.is_walkable(s.x, s.y)


def test_a_swamp_never_floods_a_tile_that_loot_lies_on(monkeypatch):
    import dungeon
    from dungeon import FLOOR, WATER, _flood_swamp, generate_dungeon

    class _AlwaysFlood(random.Random):
        def random(self):
            return 0.0

    random.seed(5)
    d = generate_dungeon(80, 50, 21)
    room = max(d.rooms, key=lambda r: r.width * r.height)
    floor = [(x, y) for x, y in room.inner_tiles() if d.tiles[y][x] == FLOOR]
    assert len(floor) >= 6
    lying = []
    for x, y in floor[::2]:                        # loot on every other tile
        s = items.make_item_by_id('artifact', 'soul_sphere')
        s.x, s.y = x, y
        lying.append(s)
    # No stairs found: the flood is never undone for cutting them off, so
    # what stays dry stays dry because something lies on it.
    monkeypatch.setattr(dungeon, '_find_stair_tiles', lambda *a: (None, None))
    _flood_swamp(d, room, lying, _AlwaysFlood(1))
    assert all(d.tiles[s.y][s.x] == FLOOR for s in lying)
    assert all(d.tiles[y][x] == WATER for x, y in floor[1::2])   # the bare tiles flood


# ---------------------------------------------------------------- the prayer's blessing

def test_a_prayers_blessing_names_an_item_as_the_hero_knows_it():
    g = _game()
    p = g.player
    potion = next(i for i in items.load_items('potion') if i.id == 'potion_of_extra_healing')
    import copy
    potion = copy.copy(potion)
    potion.id_level = 0
    p.known_item_ids.discard(potion.id)
    p.inventory = [potion]
    shown = g._bare_name(potion)
    assert potion.name not in shown               # the hero does not know it
    g.karma = 0
    g.msg_log.entries.clear()
    g._resolve_simple_prayer(4, at_altar=False)
    log = ' '.join(_texts(g, 20))
    assert potion.buc == 'blessed'
    assert f"suffuses the {shown}" in log
    assert potion.name not in log


def test_a_prayers_blessing_is_never_spent_on_treasure_or_a_sphere():
    g = _game()
    p = g.player
    ruby = treasure.make('treasure_burmese_ruby')
    sphere = items.make_item_by_id('artifact', 'master_hearth_sphere')
    p.known_item_ids.discard(sphere.id)
    p.inventory = [ruby, sphere]
    g.karma = 0
    g.msg_log.entries.clear()
    g._resolve_simple_prayer(4, at_altar=False)
    assert ruby.buc == 'uncursed' and sphere.buc == 'uncursed'
    log = ' '.join(_texts(g, 20))
    assert 'Nothing you carry can take another blessing.' in log
    assert 'Master Hearth Sphere' not in log


# ---------------------------------------------------------------- treasure has no BUC and no identity to lose

def test_treasure_cannot_be_cursed_blessed_or_unidentified_by_anything():
    ruby = treasure.make('treasure_burmese_ruby')
    ruby.buc = 'cursed'
    ruby.buc_known = False
    ruby.id_level = 0
    assert ruby.buc == 'uncursed' and ruby.buc_known and ruby.id_level == 5
    assert ruby.identified and not ruby.cursed and ruby.can_be_cursed is False
    ruby.buc = 'blessed'
    assert ruby.buc == 'uncursed'
    g = _game()
    assert g._display_name(ruby) == 'Burmese Ruby'


def test_a_cursed_identify_scroll_never_forgets_treasure():
    g = _game()
    p = g.player
    ruby = treasure.make('treasure_burmese_ruby')
    p.inventory = [ruby]
    g._scroll_identify_amnesia()
    assert ruby.id_level == 5
    assert "words dissolve into nonsense" in ' '.join(_texts(g, 3))
    # Still nothing to identify on the Kit or the sheet.
    assert {a['id'] for a in g._item_actions(ruby, 'pack')} == {'drop', 'lore'}


def test_old_pickled_treasure_reads_its_fixed_identity():
    """A Treasure pickled with the plain fields (today's dev saves) still
    reads uncursed and identified: the class properties win."""
    import pickle
    ruby = treasure.make('treasure_burmese_ruby')
    ruby.__dict__.update({'buc': 'cursed', 'id_level': 0, 'buc_known': False})
    back = pickle.loads(pickle.dumps(ruby))
    assert back.buc == 'uncursed' and back.id_level == 5 and back.buc_known


# ---------------------------------------------------------------- an altar's tribute

def test_the_altar_card_says_what_treasure_the_tribute_would_take():
    import economy
    from mystery_system import MYSTERIES
    g = _game()
    p = g.player
    cost = economy.written_gold(MYSTERIES['oracle']['gold_cost'])
    g.player_gold = cost                           # coin covers it: nothing said
    assert g._tribute_plan_line(cost) == ''
    g.player_gold = 20
    p.inventory.append(treasure.make('treasure_burmese_ruby'))
    line = g._tribute_plan_line(cost)
    assert 'Burmese Ruby' in line and 'no change' in line
    # Nothing to pay with at all: the altar refuses before the card (no line).
    p.inventory = [i for i in p.inventory if not treasure.is_treasure(i)]
    assert g._tribute_plan_line(cost) == ''


def test_the_altar_takes_exactly_what_its_card_said():
    import economy
    from game_states import STATE_MYSTERY_APPROACH
    from mystery_system import MYSTERIES, MysteryAltar
    g = _game()
    p = g.player
    cost = economy.written_gold(MYSTERIES['oracle']['gold_cost'])
    g.player_gold = 20
    ruby = treasure.make('treasure_burmese_ruby')
    p.inventory.append(ruby)
    altar = MysteryAltar('oracle', p.x, p.y)
    g.ground_items.append(altar)
    g._start_mystery(altar)
    assert g.state == STATE_MYSTERY_APPROACH
    said = g._tribute_plan_line(cost)
    g._begin_mystery_challenge()
    assert ruby not in p.inventory and g.player_gold == 20
    assert any('You offer a Burmese Ruby as tribute.' in t for t in _texts(g, 6)), said


# ---------------------------------------------------------------- QA paths

def test_the_qa_treasure_sampler_brings_its_trader_even_in_a_corridor():
    """'$' on the QA hero: the trader with the draught stands beside him
    however cramped the start (with fewer than eighteen free tiles within
    five, the trader, placed last, was left out)."""
    from dungeon import FLOOR, WALL
    from game_states import STATE_PLAYER
    from mystery_system import MerchantNPC
    import pygame as _pg
    g = _game()
    p = g.player
    p.qa_tools = True
    g.ground_items = [i for i in g.ground_items if not isinstance(i, MerchantNPC)
                      and max(abs(i.x - p.x), abs(i.y - p.y)) > 10]
    for dy in range(-5, 6):                       # a corridor: four open tiles
        for dx in range(-5, 6):
            x, y = p.x + dx, p.y + dy
            if g.dungeon.in_bounds(x, y):
                g.dungeon.tiles[y][x] = FLOOR if (dx == 0 or dy == 0) and abs(dx + dy) <= 1 else WALL
    g.state = STATE_PLAYER
    g.handle_event(_pg.event.Event(_pg.KEYDOWN, key=_pg.K_4, unicode='$', mod=_pg.KMOD_SHIFT,
                                   scancode=0))
    traders = [i for i in g.ground_items if isinstance(i, MerchantNPC)]
    assert len(traders) == 1
    m = traders[0]
    assert max(abs(m.x - p.x), abs(m.y - p.y)) == 1
    assert any(w.id == 'draught_of_mimir' for w in m.stock)
    assert any(isinstance(i, items.GoldPile) and i.amount == 20000 for i in g.ground_items)
    # A second press does not stack a second trader beside him.
    g.handle_event(_pg.event.Event(_pg.KEYDOWN, key=_pg.K_4, unicode='$', mod=_pg.KMOD_SHIFT,
                                   scancode=0))
    assert len([i for i in g.ground_items if isinstance(i, MerchantNPC)]) == 1


# ---------------------------------------------------------------- text

def test_the_pets_doc_quotes_the_bound_spheres_lore_as_the_game_writes_it():
    src = open(os.path.join(ROOT, 'src', 'game_menus.py'), encoding='utf-8').read()
    assert 'Hurl it to summon it back to your side.' in src
    doc = open(os.path.join(ROOT, 'docs', 'systems', 'pets.md'), encoding='utf-8').read()
    assert 'summon them back' not in doc
    assert 'Hurl it to summon it back to your side.' in doc
