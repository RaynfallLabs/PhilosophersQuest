"""The Stray Kids easter egg, the whole way through, as a player would
(round 3, Brandon: "a minor easter egg, just make sure it all works"; the
dance-off, 2026-11-14: "B-B-B-BOSS BATTLE! DANCE OFF!").

One run on a real headless Game, every step a key through the game's own
handler (the driver of tests/test_bugbash_wb_e.py), the dance on a fake clock
with each arrow pressed at its time:

1. the idol stands on its floor (8 to 12), set down by the game;
2. it calls the hero over; walking into it twice takes him to the Zombie
   Stage;
3. he walks out of the wings onto the stage: the band strikes a pose and
   "B-B-B-BOSS BATTLE! DANCE OFF!" fills the map; once the banner is over
   the dance-off's card opens;
4. he practises twice, free;
5. the dance-off: he loses the first round on purpose (the roast, the
   earworm, a strike), then wins all eight rounds on time, one member
   falling to each; the last leaves the photo;
6. he picks it up and takes the stage door back: the idol is spent, and
   stays spent;
7. he reads the photo: an ordinary monster stops to watch, a named foe and
   a swarm that cannot be stunned do not, each with its own line;
8. he saves and loads mid-show, and the show goes on and bows out;
9. a second show (the QA photo), and he leaves the floor mid-show: it ends
   with its bow there, and coming back finds no show.

The feel of it (the tempo, the memory, the strikes) is Brandon's play-test.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

from test_bugbash_wb_e import (  # noqa: E402,F401  (make_game is a fixture)
    make_game, no_errors, open_floor, path_step, pick, place_monster, reload, warp)

_ARROWS = {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'up': pygame.K_UP, 'down': pygame.K_DOWN}


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


def fake_clock(g, start=60_000):
    """The dance screen's clock, set by hand (``_mooble_clock_fn``)."""
    now = [start]
    g._mooble_clock_fn = lambda: now[0]
    return now


def dance_round(h, now, presses='on_time'):
    """Space, then a whole phrase as the game loop runs it: a frame on every
    beat and each arrow a real key event at its time on the clock (every
    step on time, a list of (t, dir) from the start, or none). The screen
    is drawn at the start and the end."""
    import rhythm
    g = h.g
    h.key(pygame.K_SPACE)
    md = g._mdance
    assert md['phase'] == 'play'
    t0, tl = md['t0'], md['tl']
    keys = rhythm.on_time(tl['response']) if presses == 'on_time' else list(presses)
    events = sorted([(t, 'key', d) for t, d in keys]
                    + [(k * tl['beat_ms'], 'tick', None) for k in range(1, tl['beats'] + 2)])
    for t, kind, d in events:
        now[0] = t0 + int(round(t))
        if kind == 'tick':
            g.update(1 / 30)
        elif md['phase'] == 'play':
            g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=_ARROWS[d], unicode='',
                                              mod=0, scancode=0))
    now[0] = t0 + int(g._mooble_end_ms()) + 5
    h.frame()
    assert md['phase'] == 'result'
    return md


def to_the_stage(h):
    """From the wings, walk onto the stage (real steps) until the band sees
    him; then the frames of play until the dance-off's card opens. Returns
    every line said on the way."""
    import stray_kids
    from game_states import STATE_MOOBLE_DANCE
    g = h.g
    ex, ey = stray_kids.stage_edge(g.dungeon)
    heard = []
    for _ in range(60):
        if g._stray_kids_state().get('challenge'):
            break
        # (to a tile beside the one past the edge: the edge itself, first)
        if not path_step(h, ex + 1, ey):
            h.move(1, 0)
        heard += h.said()
    assert g._stray_kids_state()['challenge'] == 'pending'
    assert g.effects_runtime.handlers['dance_off_banner'].active
    for _ in range(300):
        h.frame()
        if g.state == STATE_MOOBLE_DANCE:
            break
    heard += h.said()
    assert g.state == STATE_MOOBLE_DANCE and g._mdance['owner'] == 'stray_kids'
    return heard


def win_the_dance_off(h, now, lose_first=0):
    """D from the card, then every round: ``lose_first`` rounds lost (no
    keys), the rest danced on time, Enter after each. The lines said."""
    import stray_kids
    g = h.g
    heard = []
    h.key(pygame.K_d)
    for _ in range(lose_first):
        md = dance_round(h, now, presses=[])
        assert not md['won']
        h.key(pygame.K_RETURN)
        heard += h.said()
    while stray_kids.the_band(g.monsters):
        md = dance_round(h, now)
        assert md['won'], md['result']
        h.key(pygame.K_RETURN)
        heard += h.said()
    return heard


def _walk_beside(h, x, y):
    """Walk to a tile beside (x, y), square on (the bump is a straight step).

    No nearer in eight steps counts as stuck too: a wanderer that keeps
    stepping into the way (a Sluagh on the idol's floor) sent the walk round
    and round the map for 300 steps, about one run in a hundred (round 3 F)."""
    g = h.g
    stuck = 0
    best, since = None, 0
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
        dist = abs(x - p.x) + abs(y - p.y)
        if best is None or dist < best:
            best, since = dist, 0
        else:
            since += 1
        if not moved or stuck >= 3 or since >= 8:
            best, since = None, 0
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
    from game_states import STATE_MOOBLE_DANCE, STATE_PLAYER
    g, h = make_game(build='titivillus', name='Titivillus')
    st = g._stray_kids_state()
    floor = st['floor']
    assert 8 <= floor <= 12                           # every run, on one floor of 8-12
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
    h.wait()                                          # (a turn with it in plain view: the walk
    heard = ' '.join(h.said())                        #  may have been cut short by a set-down)
    assert stray_kids.data()['idol']['call'] in heard and st['called']
    h.move(*step)
    assert any('walk into it again' in t for t in h.said())
    h.move(*step)
    assert g.dungeon_level == STRAY_KIDS_STAGE
    said = h.said()
    # (each line is looked for, not its place: a spell wearing off in the
    # same turn is said in among them)
    assert 'The stage door is the way out (> on it).' in said
    assert any('Five, six, seven, EIGHT' in t for t in said)
    assert len(stray_kids.the_band(g.monsters)) == 8
    assert not g._stray_kids_state().get('challenge')           # not on the stage yet
    # 3. Onto the stage: the pose, the announcement, then the card.
    heard = to_the_stage(h)
    do = stray_kids.dance_off()
    assert stray_kids.data()['stage']['pose'] in heard
    assert do['announce']['log'] in heard
    md = g._mdance
    assert md['mode'] == 'practice' and md['phase'] == 'ready'
    assert md['poses']['idle'] == 'sk_zombie_bang_chan'
    # 4. Practise twice: free, no turn, nothing lost.
    now = fake_clock(g)
    turn, hp = g.turn_count, p.hp
    for _ in range(2):
        md = dance_round(h, now)
        assert md['won'] and md['mode'] == 'practice' and md['phase'] == 'result'
        h.key(pygame.K_ESCAPE)                        # Not Yet
        assert g.state == STATE_PLAYER
        lead = stray_kids.the_band(g.monsters)[0]
        _walk_beside(h, lead.x, lead.y)               # and walk back into the band
        dx, dy = lead.x - g.player.x, lead.y - g.player.y
        h.move(dx, dy)
        assert g.state == STATE_MOOBLE_DANCE and g._mdance['mode'] == 'practice'
        assert lead.alive and lead.hp == lead.max_hp  # walking into him is never a blow
    assert len(stray_kids.the_band(g.monsters)) == 8
    turn_after_practice = g.turn_count
    assert p.hp == hp
    # 5. The dance-off: the first round lost on purpose, then all eight won.
    p.hp = p.max_hp
    heard = win_the_dance_off(h, now, lose_first=1)
    said = ' '.join(heard)
    assert 'Zombie Bang Chan: "' in said                          # his roast
    assert "Zombie Bang Chan's Four A.M. Demo Song gets stuck in your head." in said
    assert not p.is_dead() and p.hp >= 1
    assert not stray_kids.the_band(g.monsters)
    assert g.state == STATE_PLAYER and g.turn_count > turn_after_practice >= turn
    for m in stray_kids.members():
        assert f"Zombie {stray_kids.member_name(m)} crumbles into glitter and grave-dust." in said, m
    assert 'is slain' not in said
    assert 'An Autographed Stray Kids Photo lies where the band last stood.' in said
    assert do['won_log'] in said
    assert '""' not in said
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
    # 6. The stage door, back to the idol's floor; the idol is spent.
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
    assert stray_kids.data()['stage']['leave_cleared'] in h.said()
    assert g._stray_kids_state()['outcome'] == 'cleared'
    g.monsters = [m for m in g.monsters if getattr(m, 'is_allied', False)]
    step = _walk_beside(h, ix, iy)
    h.said()
    h.move(*step)
    assert stray_kids.data()['idol']['spent_bump'] in h.said()
    h.move(*step)                                     # and again: still spent, no trip
    assert stray_kids.data()['idol']['spent_bump'] in h.said()
    assert g.dungeon_level == floor
    # 7. The photo: a goblin stops to watch; a named foe and a swarm do not.
    for e in list(p.status_effects):                  # (the earworm has worn off by now)
        p.status_effects.pop(e, None)
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
    # 8. Save and load mid-show: the show goes on, and bows out.
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
    # 9. A second show (the QA photo), and he leaves the floor mid-show.
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


def test_a_lost_dance_off_then_challenge_again_and_win(make_game):  # noqa: F811  (the fixture)
    """Three strikes and the band laughs him off the stage: the members
    still standing back in their places, the fallen still fallen, the hero
    at the edge of the stage, shaken (the earworm) but never killed, even at
    one hit point. He practises again, walks into the band, and wins."""
    import stray_kids
    from game_states import STATE_PLAYER, STATE_MOOBLE_DANCE
    g, h = make_game(build='titivillus', name='Titivillus')
    warp(h, 9)
    g = h.g
    g.monsters = [m for m in g.monsters if getattr(m, 'is_allied', False)]
    g.pets = []
    g._enter_stray_kids_stage()
    h.said()
    to_the_stage(h)
    now = fake_clock(g)
    h.key(pygame.K_d)
    md = dance_round(h, now)                          # Bang Chan falls
    assert md['won']
    h.key(pygame.K_RETURN)
    g.player.hp = 1
    for _ in range(3):
        md = dance_round(h, now, presses=[])
        assert not md['won'] and g.player.hp == 1 and not g.player.is_dead()
        h.key(pygame.K_RETURN)
    said = ' '.join(h.said())
    assert g.state == STATE_PLAYER
    assert stray_kids.dance_off()['laugh'] in said
    band = stray_kids.the_band(g.monsters)
    assert len(band) == 7 and band[0].member == 'lee_know'
    assert all((m.x, m.y) == stray_kids.place_of(g.dungeon, m._sk_slot) for m in band)
    assert (g.player.x, g.player.y) == stray_kids.stage_edge(g.dungeon)
    assert g.player.status_effects                    # shaken: his song is still in his head
    # Challenge again: walk into the band, practise once, then win. (Once
    # the song in his head has worn off: a confused hero walks astray.)
    g.player.status_effects.clear()
    g.player.hp = g.player.max_hp
    lead = band[0]
    _walk_beside(h, lead.x, lead.y)
    h.move(lead.x - g.player.x, lead.y - g.player.y)
    assert g.state == STATE_MOOBLE_DANCE and g._mdance['mode'] == 'practice'
    assert stray_kids.data()['stage']['challenge_again'] in h.said()
    md = dance_round(h, now)
    assert md['won'] and len(md['tl']['response']) == 5      # Lee Know's round: five steps
    win_the_dance_off(h, now)
    assert not stray_kids.the_band(g.monsters) and g.state == STATE_PLAYER
    assert any(getattr(i, 'id', '') == stray_kids.photo_id() for i in g.ground_items)
    no_errors(h)
