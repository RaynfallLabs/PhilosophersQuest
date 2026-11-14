"""The Stray Kids easter egg, the whole way through, as a player would
(round 3, Brandon: "a minor easter egg, just make sure it all works").

One run on a real headless Game, every step a key through the game's own
handler (the driver of tests/test_bugbash_wb_e.py):

1. the idol stands on its floor (8 to 12), set down by the game;
2. it calls the hero over; walking into it twice takes him to the Zombie
   Stage;
3. the band dances in formation and roasts him;
4. he fights the band to the last, and the last leaves the photo;
5. he takes the stage door back: the idol is spent, and stays spent;
6. he reads the photo: an ordinary monster stops to watch, a named foe and
   a swarm that cannot be stunned do not, each with its own line;
7. he saves and loads mid-show, and the show goes on and bows out;
8. a second show (the QA photo), and he leaves the floor mid-show: it ends
   with its bow there, and coming back finds no show.

The feel of it is Brandon's play-test.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

from test_bugbash_wb_e import (  # noqa: E402,F401  (make_game is a fixture)
    blow, make_game, no_errors, open_floor, path_step, pick, place_monster, reload, warp)


def _star_count(g):
    import stray_kids
    return sum(1 for m in g.monsters if stray_kids.is_star(m))


def _read_photo(h):
    import stray_kids
    g = h.g
    h.key('r')
    photo = next(i for i in g.scroll_menu_items if getattr(i, 'id', '') == stray_kids.photo_id())
    pick(h, photo, g._get_scroll_tab_items)
    h.quiz(3)
    return h.said()


def _walk_beside(h, x, y):
    """Walk to a tile beside (x, y), square on (the bump is a straight step)."""
    g = h.g
    stuck = 0
    for _ in range(300):
        p = g.player
        if abs(x - p.x) + abs(y - p.y) == 1:
            return (x - p.x, y - p.y)
        was = (p.x, p.y)
        moved = path_step(h, x, y)
        while g.state != 'player':                # (a prompt the way crossed: a fountain...)
            h.key(pygame.K_ESCAPE)
            if g.state != 'player':
                h.key(pygame.K_RETURN)
        stuck = stuck + 1 if (p.x, p.y) == was else 0
        if not moved or stuck >= 3:
            # The walk is not what is under test: set him beside it.
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if g.dungeon.is_walkable(x + dx, y + dy):
                    p.x, p.y = x + dx, y + dy
                    break
            else:
                open_floor(g, x + 1, y, 0)
                p.x, p.y = x + 1, y
            g._refresh_fov()
    raise AssertionError('never got there')


def _set_near(g, x, y, lo=3, hi=6):
    """Set the hero a short walk from (x, y): a tile from which a path of
    ``lo`` to ``hi`` steps reaches the tile beside it (the floor's long walk
    is not what is under test; the last steps are keys)."""
    from collections import deque
    d = g.dungeon
    start = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
             if d.is_walkable(x + dx, y + dy)]
    dist = {t: 0 for t in start}
    q = deque(start)
    while q:
        cur = q.popleft()
        if lo <= dist[cur] <= hi:
            g.player.x, g.player.y = cur
            g._refresh_fov()
            return
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt not in dist and d.is_walkable(*nxt):
                dist[nxt] = dist[cur] + 1
                q.append(nxt)
    g.player.x, g.player.y = start[0]
    g._refresh_fov()


def _spot(g, avoid=()):
    """A walkable, free tile in plain sight of the hero, two or three out."""
    import decor
    p = g.player
    taken = {(m.x, m.y) for m in g.monsters} | set(avoid)
    for r in (2, 3, 1):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                t = (p.x + dx, p.y + dy)
                if (t in g.visible and g.dungeon.is_walkable(*t) and t not in taken
                        and not decor.fixture_at(g.dungeon, *t)):
                    return dx, dy
    raise AssertionError('no room for a watcher')


def test_the_stray_kids_from_the_idol_to_the_last_bow(make_game):  # noqa: F811  (the fixture)
    import decor
    import stray_kids
    from boss_levels import STRAY_KIDS_STAGE
    g, h = make_game(build='titivillus', name='Titivillus')
    st = g._stray_kids_state()
    floor = st['floor']
    assert 8 <= floor <= 12                           # every run, on one floor of 8-12
    h.shift('I')                                      # (the QA build's sturdy hero)
    import random
    g._sk_rng = random.Random(3)                      # (where the idol stands: one place)
    warp(h, floor)
    g = h.g
    p = g.player
    g.monsters = [m for m in g.monsters if getattr(m, 'is_allied', False)]
    g.pets = []
    # 1. The game set the idol down on its floor.
    st = g._stray_kids_state()
    assert st['spawned'] and st['pos']
    ix, iy = st['pos']
    assert decor.fixture_at(g.dungeon, ix, iy) == stray_kids.idol_id()
    # 2. It calls him over the first time he sees it, then two bumps.
    _set_near(g, ix, iy)
    step = _walk_beside(h, ix, iy)
    heard = ' '.join(h.said())
    assert stray_kids.data()['idol']['call'] in heard and st['called']
    h.move(*step)
    assert 'walk into it again' in h.said()[-1]
    h.move(*step)
    assert g.dungeon_level == STRAY_KIDS_STAGE
    said = h.said()
    assert said[-1] == 'The stage door is the way out (> on it).'
    assert any('Five, six, seven, EIGHT' in t for t in said)
    # 3. The dance: they see him, close in formation, and roast him.
    band = stray_kids.the_band(g.monsters)
    assert len(band) == 8
    heard = []
    for _ in range(80):
        lead = stray_kids.the_band(g.monsters)[0]
        if stray_kids.dance_of(g.dungeon).get('aware') or not path_step(h, lead.x, lead.y):
            h.wait()                                  # (out of the wings, onto the stage)
        heard += h.said()
        if stray_kids.dance_of(g.dungeon).get('aware') and any(': "' in t for t in heard):
            break
    dance = stray_kids.dance_of(g.dungeon)
    assert dance['aware'] and stray_kids.data()['stage']['seen'] in heard
    assert any(t.startswith('Zombie ') and ': "' in t for t in heard), heard[-10:]
    # In formation: within a few beats (nearly) every member stands at, or
    # a step from, his place in the shape (they walk to a new one each
    # time it changes).
    hall = g.dungeon.rooms[1]
    cx, cy = hall.x + 3, hall.y + hall.height // 2
    for _ in range(60):                               # into the hall, where the shape has room
        if p.x >= hall.x + 2:
            break
        p.hp = p.max_hp
        if not path_step(h, cx, cy):
            h.wait()
        heard += h.said()
    best = 0
    for _ in range(16):
        band = stray_kids.the_band(g.monsters)
        near = sum(1 for m in band
                   if max(abs(m.x - stray_kids.place_of(dance, m._sk_slot)[0]),
                          abs(m.y - stray_kids.place_of(dance, m._sk_slot)[1])) <= 1)
        best = max(best, near)
        if best >= 6:
            break
        p.hp = p.max_hp
        h.wait()
        heard += h.said()
    # (in the narrow way from the wings the shape has no room, and the band
    # bunches as one: still a group round its anchor)
    ax, ay = dance['anchor']
    assert all(max(abs(m.x - ax), abs(m.y - ay)) <= 6 for m in band), (dance['anchor'], band)
    assert best >= 4, [(m.name, (m.x, m.y), stray_kids.place_of(dance, m._sk_slot)) for m in band]
    # 4. The fight, to the last of them, and the photo. (Their health is
    # cut to a blow each: the scene; every blow is still the hero's keys.)
    for m in stray_kids.the_band(g.monsters):
        m.hp = 1
    for _ in range(600):
        band = stray_kids.the_band(g.monsters)
        if not band:
            break
        while g.state not in ('player',) and not h.in_quiz():
            h.key(pygame.K_RETURN)
        p.hp = p.max_hp                                # (the stage is not the test here)
        tgt = min(band, key=lambda m: abs(m.x - p.x) + abs(m.y - p.y))
        if abs(tgt.x - p.x) + abs(tgt.y - p.y) == 1:
            heard += blow(h, tgt, 3)
        elif not path_step(h, tgt.x, tgt.y):
            h.wait()
        heard += h.said()
    assert not stray_kids.the_band(g.monsters)
    said = ' '.join(heard)
    assert 'crumbles into glitter and grave-dust. Nothing is left of him.' in said
    assert 'An Autographed Stray Kids Photo lies where the band last stood.' in said
    assert '""' not in said and ' its ' not in ' '.join(t for t in heard if t.startswith('Zombie '))
    photo = next(i for i in g.ground_items if getattr(i, 'id', '') == stray_kids.photo_id())
    for _ in range(100):
        if (p.x, p.y) == (photo.x, photo.y):
            break
        if abs(photo.x - p.x) + abs(photo.y - p.y) == 1:
            h.move(photo.x - p.x, photo.y - p.y)
        elif not path_step(h, photo.x, photo.y):
            p.x, p.y = photo.x, photo.y
            g._refresh_fov()
    h.key('g')
    assert any(getattr(i, 'id', '') == stray_kids.photo_id() for i in p.inventory)
    # 5. The stage door, back to the idol's floor; the idol is spent.
    from dungeon import STAIRS_DOWN
    d = g.dungeon
    door = next((x, y) for y in range(d.height) for x in range(d.width) if d.tiles[y][x] == STAIRS_DOWN)
    p.x, p.y = door
    g._refresh_fov()
    h.said()
    h.key(pygame.K_PERIOD, '>')
    g = h.g
    p = g.player
    assert g.dungeon_level == floor
    assert h.said()[0] == stray_kids.data()['stage']['leave_cleared']
    assert g._stray_kids_state()['outcome'] == 'cleared'
    g.monsters = [m for m in g.monsters if getattr(m, 'is_allied', False)]
    step = _walk_beside(h, ix, iy)
    h.said()
    h.move(*step)
    assert h.said()[-1] == stray_kids.data()['idol']['spent_bump']
    h.move(*step)                                     # and again: still spent, no trip
    assert h.said()[-1] == stray_kids.data()['idol']['spent_bump']
    assert g.dungeon_level == floor
    # 6. The photo: a goblin stops to watch; a named foe and a swarm do not.
    open_floor(g, p.x, p.y, 3)
    g.monsters = [m for m in g.monsters if getattr(m, 'is_allied', False)]
    gob = place_monster(g, 'goblin', *_spot(g))
    g._refresh_fov()
    boss = place_monster(g, 'lamia', *_spot(g))
    g._refresh_fov()
    swarm = place_monster(g, 'scarab_swarm', *_spot(g))
    for m in (gob, boss, swarm):
        m._aware = True
    g._refresh_fov()
    said = _read_photo(h)
    assert _star_count(g) == 8
    assert 'The Goblin stops to watch the show.' in said, said
    assert gob.has_effect('stunned')
    assert 'Lamia has seen better shows, and does not stop.' in said, said
    assert 'The Scarab Swarm pays the show no mind.' in said, said
    assert not boss.has_effect('stunned') and not swarm.has_effect('stunned')
    assert not any('Lamia stops to watch' in t or 'Swarm stops to watch' in t for t in said)
    # 7. Save and load mid-show: the show goes on, and bows out.
    for m in (boss, swarm):
        m.alive = False                                 # (they would fight him; not the test)
    g.monsters = [m for m in g.monsters if m.alive]
    h.wait()
    left = _star_count(g)
    assert left == 8
    g = reload(h)
    assert _star_count(g) == 8
    for _ in range(int(stray_kids.data()['stars']['dance_turns']) + 2):
        h.wait()
    said = h.said()
    assert _star_count(g) == 0
    assert stray_kids.data()['stars']['bow'] in said
    # 8. A second show (the QA photo), and he leaves the floor mid-show.
    h.shift('K')
    assert any(getattr(i, 'id', '') == stray_kids.photo_id() for i in g.player.inventory)
    h.said()
    _read_photo(h)
    assert _star_count(g) == 8
    warp(h, floor + 1)
    g = h.g
    assert g.dungeon_level == floor + 1 and _star_count(g) == 0
    assert stray_kids.data()['stars']['bow'] in h.said()   # the show ends with its bow
    warp(h, floor)
    g = h.g
    assert g.dungeon_level == floor and _star_count(g) == 0     # no show runs on
    assert not any(getattr(m, '_sk_watching', False) for m in g.monsters)
    no_errors(h)
