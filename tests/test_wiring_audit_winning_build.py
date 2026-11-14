"""The independent wiring audit of the winning build (slice 11, 2026-11-13).

The slices were built in parallel worktrees; these pin the seams where two of
them meet, found by the audit:

* Kit Sense (slice 3) reads what the hero put on his own weapon (a smith's
  silvering or cold-iron inlay, slice 6; a coating, slice 5) even while the
  weapon itself is unidentified.
* A trader's stall (slice 6) never stands in Old Nickel's room (slice 8), and
  Old Nickel is never set down in a room that already holds a stall.
* The stall counters name only things that exist: item ids by class, and the
  shield templates (slice 5's mirror shield).
* The help screen lists every Shift key the map answers, drawn whole at the
  smallest window, and the in-game key names match the handlers.
* Old-rule text the sweep missed stays gone.

Logic tests on the real data and a headless Game. Whether any of it feels
right is Brandon's play-test: Claude cannot drive Pygame.
"""
import json
import os
import random
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import items  # noqa: E402
from items import instantiate_weapon, make_item_by_id  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402


def _load(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return json.load(f)


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


MONS = _load('data', 'monsters.json')


def _mon(kind):
    return Monster({**MONS[kind], 'id': kind}, 0, 0)


def _screen(size=(1600, 900)):
    return pygame.display.set_mode(size)


def _game(name, seed=7):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.state = STATE_PLAYER
    return g


# ===========================================================================
# Kit Sense x the smith's work x coatings
# ===========================================================================

def test_kit_sense_counts_the_silver_a_smith_worked_into_an_unknown_weapon():
    import kit_sense
    import smithing
    p = Player()
    wolf = _mon('werewolf')                    # weak to silver, resists blunt
    mace = instantiate_weapon('mace', 'iron')
    p.weapon = mace
    assert not kit_sense.knows_weapon(p, mace)  # an unidentified iron mace
    assert kit_sense.known_mult(p, mace, wolf) == 0.5
    assert smithing.inlay(mace, 'silver')
    # He paid the smith and watched the silver go in: blunt x0.5, silver x2.
    assert kit_sense.known_mult(p, mace, wolf) == 1.0
    # Still nothing he cannot know: an unknown weapon's own metal stays hidden.
    plain = instantiate_weapon('mace', 'silver')
    assert not kit_sense.knows_weapon(p, plain)
    assert kit_sense.known_mult(p, plain, wolf) == 0.5


def test_kit_sense_counts_the_coating_he_worked_into_an_unknown_weapon():
    import coatings
    import kit_sense
    p = Player()
    wolf = _mon('werewolf')
    mace = instantiate_weapon('mace', 'iron')
    p.weapon = mace
    dust = make_item_by_id('flask', 'silver_dust')
    assert coatings.apply(p, dust)
    assert kit_sense.known_mult(p, mace, wolf) == 1.0
    # A known silver mace in the pack is then no better than the hand.
    other = instantiate_weapon('mace', 'silver')
    p.known_item_ids.add(other.id)
    other.identified = True
    p.inventory = [other]
    got = kit_sense.advise(p, wolf)
    assert got is None or got[0].item is not other, got


# ===========================================================================
# Old Nickel's room and the traders' stalls
# ===========================================================================

def _nickel(g, room):
    import emberpup_encounter as ee
    m = Monster(ee.wearer_defn(), *next(iter(room.inner_tiles())))
    m._wary_home = ee.home_of(room)
    g.monsters.append(m)
    return m


def test_a_stall_never_stands_in_old_nickels_room():
    g = _game('__test_audit_stall__')
    g.monsters = []
    rooms = g.dungeon.rooms
    assert len(rooms) >= 3
    home = rooms[1]                    # the room _trader_spot tries first
    _nickel(g, home)
    h = g.monsters[0]._wary_home
    for s in range(25):
        spot = g._trader_spot(random.Random(s))
        assert spot is not None
        assert not (h[0] <= spot[0] <= h[2] and h[1] <= spot[1] <= h[3]), (s, spot, h)


def test_old_nickel_is_never_set_down_in_a_room_with_a_stall():
    import emberpup_encounter as ee
    from mystery_system import MerchantNPC
    g = _game('__test_audit_nickel_stall__', seed=3)
    rooms = g.dungeon.rooms
    here = ee._room_of(rooms, g.player.x, g.player.y)
    cands = [r for r in rooms if r is not here and r is not rooms[0]]
    assert len(cands) >= 3
    base_items = list(g.ground_items)
    # Every room but one holds a stall, for each choice of the one: he must
    # land in the one left every time.
    for keep in cands:
        g.monsters = [m for m in g.monsters if not ee.is_wearer(m)]
        g.ground_items = list(base_items)
        for r in cands:
            if r is not keep:
                x, y = next(iter(r.inner_tiles()))
                g.ground_items.append(MerchantNPC(x, y, [], []))
        st = g._emberpup_state()
        st['cloak_floor'] = g.dungeon_level
        st['cloak_spawned'] = False
        g._maybe_spawn_cloak_wearer(g.dungeon_level)
        nick = [m for m in g.monsters if ee.is_wearer(m)]
        assert len(nick) == 1
        assert ee._room_of(rooms, nick[0].x, nick[0].y) is keep


# ===========================================================================
# The stall counters name real things
# ===========================================================================

def test_every_stall_counter_names_an_item_or_template_that_exists():
    import traders
    from items import load_items, load_templates
    ids = {}

    def ids_of(cls):
        if cls not in ids:
            ids[cls] = {getattr(i, 'id', None) for i in load_items(cls)}
        return ids[cls]
    c = traders.data()['counters']
    for side in ('weak', 'guard'):
        for key, need in c[side].items():
            for o in need['offers']:
                for iid in o.get('ids') or ():
                    assert iid in ids_of(o['class']), (key, o)
                if o.get('template'):
                    kind = {'shield': 'shields', 'armor': 'armor', 'weapon': 'weapons'}[o['gear']]
                    assert o['template'] in load_templates(kind), (key, o)
    # Each trader's shelf rows that name a kind (data/traders.json stock:
    # Mother Wort's earplugs, the sutler's cold-iron charm, ...).
    named = 0
    for kind, d in traders.data()['traders'].items():
        for row in d.get('stock') or ():
            for iid in ([row['id']] if row.get('id') else []) + list(row.get('ids') or ()):
                assert iid in ids_of(row['cat']), (kind, row)
                named += 1
    assert named


# ===========================================================================
# Help and keys
# ===========================================================================

def _map_shift_letters():
    """The capital letters the map answers outside the QA build
    (game_input.handle_event, STATE_PLAYER: the key's character as
    _command_char reads it, ``uni``, since the Caps Lock fix of bug bash
    WB-A01)."""
    src = _read('src', 'game_input.py')
    out = set()
    for line in src.splitlines():
        m = re.search(r"(?:event\.unicode|\buni) == '([A-Z])'", line)
        if m and 'qa_tools' not in line:
            out.add(m.group(1))
    return out


def test_the_help_screen_lists_every_shift_key_the_map_answers():
    letters = _map_shift_letters()
    assert {'P', 'E', 'S', 'C'} <= letters, letters
    help_src = _read('src', 'game_render.py')
    body = help_src[help_src.index('def _draw_help_screen'):help_src.index('def _how_quizzes_page')]
    for ch in letters:
        assert f'("Shift+{ch}",' in body, ch


def test_the_new_keys_are_drawn_whole_at_the_smallest_window():
    # With the painted kit the game ships (assets/ui), every row is fitted
    # whole or the assert fires; the shipped look is the one that counts.
    import ui_theme
    from main import Game
    saved = ui_theme.save_state()
    try:
        ui_theme.load()
        g = Game(_screen((1280, 720)), player_name='__test_audit_help__')
        drawn = []
        real_fit = g._fit_line

        def fit(text, *a, **k):
            font, shown = real_fit(text, *a, **k)
            assert shown == text, f'help row cut at 1280x720: {shown!r}'
            drawn.append(text)
            return font, shown
        g._fit_line = fit
        g._draw_help_screen()
    finally:
        ui_theme.restore_state(saved)
    for row in ('Loadouts', 'Press / Guard', 'Coat weapon', 'Swap weapons',
                'Kit: compare, equip, drop', 'Pet menu', 'Cancel / close'):
        assert row in drawn, row


def test_the_swap_key_is_named_s_wherever_the_game_names_it():
    # The plan said X; slice 1 made it S (X is Examine). Nothing may still say X.
    for rel in ('src/game_dressing.py', 'src/item_actions.py', 'src/game_render.py',
                'docs/systems/ui.md', 'docs/systems/armour.md', 'data/hints.json'):
        text = _read(*rel.split('/'))
        assert not re.search(r"\bX (swaps|to swap)\b", text), rel


# ===========================================================================
# Old-rule text
# ===========================================================================

def test_the_weapon_doc_no_longer_says_a_bane_is_half_again():
    doc = _read('docs', 'systems', 'weapons_and_materials.md')
    assert 'weapon deals 1.5x to monsters' not in doc
    assert '+1.5× via per-weapon anti-tag' not in doc
    assert 'dtype_mult       = 1.5' not in doc
