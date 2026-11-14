"""The Stray Kids easter egg (src/stray_kids.py, src/game_stray_kids.py).

Every run a gold shrine to the band stands on one floor of 8-12. Walk into it
twice and the hero is on the Zombie Stage, a side floor like the Cow Level,
where the eight members dance as zombies in formation; they crumble to
nothing, the last leaves a signed photo, and the photo calls the band up
alive for a short show that stops the room.

Data tests for every new JSON entry, pure tests for the dance, and behaviour
tests on a real headless Game: the stage is a randomized floor-8-to-12 event,
so these are the proof besides Brandon's own play.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

import stray_kids as sk  # noqa: E402
from boss_levels import STRAY_KIDS_STAGE, COW_LEVEL, is_side_floor  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _json(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return json.load(f)


MONS = _json('data', 'monsters.json')
MEMBERS = sk.members()


def _game(name='__test_stray_kids__', seed=11):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name=name)
    g.state = STATE_PLAYER
    return g


def _idol_floor(g, floor=9):
    """Go down to the idol's floor the ordinary way: the game sets it down."""
    g._stray_kids = dict(sk.new_run_state(), floor=floor)
    g._change_level(floor, enter_from_top=True)
    pos = [p for p, f in (g.dungeon.__dict__.get('fixtures') or {}).items() if f == sk.idol_id()]
    assert len(pos) == 1
    return pos[0]


def _beside(g, pos):
    """Stand the hero next to (x, y) and return the step that walks into it."""
    x, y = pos
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        hx, hy = x - dx, y - dy
        if g.dungeon.is_walkable(hx, hy) and not any((m.x, m.y) == (hx, hy) for m in g.monsters):
            g.player.x, g.player.y = hx, hy
            g._refresh_fov()
            return dx, dy
    raise AssertionError('no tile beside it')


def _on_stage(g, floor=9):
    pos = _idol_floor(g, floor)
    dx, dy = _beside(g, pos)
    g.pets = []
    g._do_move(dx, dy)
    g._do_move(dx, dy)
    assert g.dungeon_level == STRAY_KIDS_STAGE
    return pos


def _log(g):
    return ' '.join(str(e[0]) for e in g.msg_log.entries)


def _band(g):
    return sk.the_band(g.monsters)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def test_the_data_names_eight_members_and_every_shape_has_eight_places():
    d = sk.data()
    assert MEMBERS == ['bang_chan', 'lee_know', 'changbin', 'hyunjin', 'han',
                       'felix', 'seungmin', 'i_n']
    assert set(d['names']) == set(MEMBERS)
    for name in d['dance']['shape_order']:
        assert len(d['dance']['shapes'][name]) == 8, name
        assert d['dance']['shape_lines'][name]
        assert len({tuple(o) for o in d['dance']['shapes'][name]}) == 8, name
    for m in MEMBERS:
        assert d['observe'][m] and d['shouts'][m], m
    assert d['chance_per_run'] == 1.0 and (d['first_floor'], d['last_floor']) == (8, 12)
    assert len(d['stars']['ring']) == 16


def test_every_member_is_a_low_danger_band_member_that_never_spawns_on_his_own():
    from dungeon import _build_spawn_pool
    for m in MEMBERS:
        kind = sk.zombie_kind(m)
        e = MONS[kind]
        assert e['name'] == f"Zombie {sk.member_name(m)}"
        assert e['family'] == 'restless_dead' and 'undead' in e['tags']
        assert e['peak_weight'] == 0 and e['frequency'] == 0 and e['spawn_chance'] == 0
        # The band is the mini-boss; each member is weak on his own (no
        # mini-boss gold or health rules), a proper name all the same.
        assert not e.get('is_mini_boss') and e['proper_noun']
        assert e['treasure']['purse'] == 'kept'
        assert e['harvest_tier'] == 0
        assert e['treasure']['gold'] == [0, 0] and e['treasure']['item_chance'] == 0
        assert e['lore'] and e['kill_chronicle'] and e['thac0'] >= 15
        for a in e['attacks']:
            assert a.get('quip'), (kind, a['name'])
            assert 'gaze' not in a['name'].lower()     # gaze has its own rules
            # LORE, NOT FLOOR: real small numbers, no more than a d4 and one
            lo, _, hi = a['damage'].partition('d')
            assert int(lo) == 1 and int(hi.split('+')[0]) <= 4, (kind, a['damage'])
    for level in (8, 10, 12, 50):
        pool = _build_spawn_pool(level)
        assert not any(k.startswith('sk_zombie_') for k in pool), level


def test_the_band_is_never_rolled_as_a_runs_mini_boss():
    from level_manager import LevelManager
    for seed in range(15):
        random.seed(seed)
        planned = LevelManager()._roll_planned_mini_bosses()
        assert not any(str(v).startswith('sk_') for v in planned.values())


def test_the_war_band_entry_is_led_by_bang_chan_and_never_set_down_by_chance():
    import war_bands
    from dungeon import _floor_pool
    b = war_bands.data()['bands']['stray_kids']
    assert b['leader'] == ['sk_zombie_bang_chan']
    assert sorted(b['guard']) == sorted(sk.zombie_kind(m) for m in MEMBERS[1:])
    assert b['morale'] == 'quarrel'
    for level in range(8, 13):
        pool = _floor_pool(level)
        for seed in range(30):
            got = war_bands.pick_band(level, pool, random.Random(seed))
            assert not got or got[0] != 'stray_kids'


def test_the_idol_and_speaker_fixtures_and_their_art():
    fx = _json('data', 'fixtures.json')['fixtures']
    idol = fx['sk_idol']
    assert idol['blocks'] and idol['layer'] == 'stand' and idol['spent_look']
    # Plainly Stray Kids to a fan (SKZ, STAY, eight little dancers), never the
    # roll call of names, and it asks to be touched (Brandon, 2026-11-13).
    for word in ('SKZ', 'STAY', 'eight', 'touched'):
        assert word in idol['look'], word
    for m in MEMBERS:
        assert sk.member_name(m) not in idol['look'], m
    assert sk.data()['idol']['call'] and 'again' in sk.data()['idol']['first_bump']
    assert fx['sk_speaker']['blocks']
    for fid in ('sk_idol', 'sk_speaker'):
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'env', 'fixtures', fid + '.png')), fid


def test_every_member_has_his_own_sprite_alive_and_dead():
    for m in MEMBERS:
        for kind in (sk.zombie_kind(m), sk.star_kind(m)):
            assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters', kind + '.png')), kind


def test_the_photo_is_a_known_keepsake_scroll_with_its_own_art():
    import altar
    import renderer
    e = _json('data', 'items', 'scroll.json')[sk.photo_id()]
    assert e['effect'] == 'summon_stray_kids' and e['identified'] and e['single_copy']
    assert e['min_level'] >= 9999 and e['peak_weight'] == 0
    assert e['name'] == 'Autographed Stray Kids Photo' == e['unidentified_name']
    assert 'summon_stray_kids' in altar.SCROLL_EFFECTS_BLESSING_IGNORES
    path = renderer._resolve_item_sprite_path(sk.photo_id())
    assert path and os.path.basename(path) == sk.photo_id() + '.png'


def test_the_data_ships_with_the_game():
    with open(os.path.join(ROOT, 'PhilosophersQuest.spec'), encoding='utf-8') as f:
        assert "'data/stray_kids.json'" in f.read()


def test_no_line_is_longer_than_a_shout():
    """Made-up lines only (no real lyrics), short enough to read in play."""
    d = sk.data()
    lines = list(d['shouts']['band']) + list(d['shouts']['songs']) + list(d['stars']['lines'])
    for m in MEMBERS:
        lines += d['shouts'][m]
    for line in lines:
        assert 0 < len(line) <= 90, line


# ---------------------------------------------------------------------------
# The roll and the side floor
# ---------------------------------------------------------------------------

def test_the_band_riffs_on_their_songs_by_title():
    """Riffs on the songs' titles and concepts (never their words): each
    names its song in quotes, and they are a good share of what is shouted."""
    import re
    d = sk.data()
    songs = d['shouts']['songs']
    assert len(songs) >= 12
    for line in songs:
        assert re.match(r'^"[^"]+"', line), line
    titles = {re.match(r'^"([^"]+)"', line).group(1) for line in songs}
    assert {'Case 143', 'Christmas EveL', "God's Menu", 'Thunderous', 'Maniac'} <= titles
    share = d['dance']
    assert 0 < share['member_line_share'] + share['song_line_share'] < 1


def test_every_run_has_the_idol_on_a_floor_from_8_to_12():
    for seed in range(40):
        random.seed(seed)
        st = sk.new_run_state()
        assert 8 <= st['floor'] <= 12
        assert not st['spawned'] and not st['touched'] and not st['photo_dropped']


def test_the_roll_leaves_the_shared_random_stream_alone():
    random.seed(5)
    a = random.random()
    random.seed(5)
    sk.roll_for_new_run()
    assert random.random() == a


def test_the_stage_is_a_side_floor_with_a_name():
    from ui import floor_label
    assert is_side_floor(STRAY_KIDS_STAGE) and is_side_floor(COW_LEVEL)
    assert not any(is_side_floor(f) for f in range(1, 101))
    assert floor_label(STRAY_KIDS_STAGE) == 'Zombie Stage'
    assert floor_label(COW_LEVEL) == 'Moo Moo Farm' and floor_label(9) == 'Floor 9'


def test_the_stage_has_wings_a_door_out_and_the_band_in_its_hall():
    from dungeon import STAIRS_DOWN, STAIRS_UP
    d, mons, items = sk.build_stage()
    assert items == [] and len(mons) == 8
    assert [m.kind for m in mons] == [sk.zombie_kind(m) for m in MEMBERS]
    wings, hall = d.rooms
    downs = [(x, y) for y in range(d.height) for x in range(d.width) if d.tiles[y][x] == STAIRS_DOWN]
    assert len(downs) == 1 and wings.x <= downs[0][0] < wings.x + wings.width
    assert not any(d.tiles[y][x] == STAIRS_UP for y in range(d.height) for x in range(d.width))
    for m in mons:
        assert hall.x <= m.x < hall.x + hall.width and d.is_walkable(m.x, m.y)
    assert len({(m.x, m.y) for m in mons}) == 8
    lead = [m for m in mons if m._band_role == 'leader']
    assert len(lead) == 1 and lead[0].kind == 'sk_zombie_bang_chan'
    assert all(m._band_leader is lead[0] for m in mons if m is not lead[0])
    assert sk.dance_of(d)['aware'] is False
    fixtures = set(d.fixtures.values())
    assert {'sk_speaker', 'brazier_lit', 'carpet'} <= fixtures


# ---------------------------------------------------------------------------
# The dance (pure)
# ---------------------------------------------------------------------------

def test_a_shape_turns_to_face_the_hero():
    front = (0, 1)
    assert sk.turn(front, (0, 1)) == (0, 1)
    assert sk.turn(front, (0, -1)) == (0, -1)
    assert sk.turn(front, (1, 0)) == (1, 0)
    assert sk.turn(front, (-1, 0)) == (-1, 0)
    assert sk.facing(10, 10, 3, 11) == (-1, 0)
    assert sk.facing(10, 10, 11, 20) == (0, 1)


def _hall_dungeon():
    from dungeon import Dungeon, Room, WALL, FLOOR
    w, h = 40, 20
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            tiles[y][x] = FLOOR
    return Dungeon(tiles, [Room(0, 0, w, h)], w, h, STRAY_KIDS_STAGE)


class _Hero:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.status_effects = {}

    def has_effect(self, e):
        return False


def _dancing_band(d, home=(30, 10)):
    d.sk_dance = sk.new_dance(home)
    band = []
    for slot, m in enumerate(MEMBERS):
        x, y = sk.place_of(d.sk_dance, slot)
        z = sk.make_zombie(m, x, y, slot)
        sk._join_band(z, band[0] if band else None)
        band.append(z)
    return band


def test_the_band_rehearses_in_place_until_one_of_them_sees_the_hero():
    d = _hall_dungeon()
    band = _dancing_band(d)
    hero = _Hero(3, 10)
    home = list(d.sk_dance['anchor'])
    for _ in range(6):
        sk.advance(d, band, (hero.x, hero.y), lambda m: False)
        for m in band:
            assert m.take_turn(hero, d, band) is False
    assert d.sk_dance['anchor'] == home and not d.sk_dance['aware']
    ev = sk.advance(d, band, (hero.x, hero.y), lambda m: True)
    assert ('seen',) in ev and d.sk_dance['aware']


def test_the_shape_changes_every_four_beats_and_the_anchor_stops_short():
    d = _hall_dungeon()
    band = _dancing_band(d)
    hero = (5, 10)
    shapes = []
    for _ in range(40):
        for ev in sk.advance(d, band, hero, lambda m: True):
            if ev[0] == 'shape':
                shapes.append(ev[1])
    assert shapes[:5] == ['two_rows', 'diamond', 'column', 'line', 'v']
    ax, ay = d.sk_dance['anchor']
    assert max(abs(ax - hero[0]), abs(ay - hero[1])) == sk.data()['dance']['keep_off']


def test_the_band_closes_in_formation_and_strikes_only_on_the_downbeat():
    d = _hall_dungeon()
    band = _dancing_band(d)
    hero = _Hero(8, 10)
    for b in band:
        b.status_effects = {}
    strikes = {True: 0, False: 0}
    for _ in range(40):
        sk.advance(d, band, (hero.x, hero.y), lambda m: True)
        on_beat = sk.strike_beat(d.sk_dance)
        for m in band:
            if m.member == 'lee_know':
                continue                    # his cat (tested on its own)
            if m.take_turn(hero, d, band):
                strikes[on_beat] += 1
    assert strikes[True] > 0 and strikes[False] == 0
    near = [m for m in band if max(abs(m.x - hero.x), abs(m.y - hero.y)) <= 3]
    assert len(near) >= 4
    assert len({(m.x, m.y) for m in band}) == 8      # never two on one tile


def test_a_member_out_of_the_dance_acts_like_any_monster():
    d = _hall_dungeon()
    band = _dancing_band(d)
    z = band[3]
    called = []
    import monster as monster_mod
    orig = monster_mod.Monster.take_turn

    def spy(self, *a, **k):
        called.append(self)
        return False
    monster_mod.Monster.take_turn = spy
    try:
        z.status_effects['confused'] = 5
        z.take_turn(_Hero(3, 10), d, band)
        z.status_effects = {'sleeping': 5}
        z.take_turn(_Hero(3, 10), d, band)
    finally:
        monster_mod.Monster.take_turn = orig
    assert called == [z, z]


def test_lee_know_would_rather_pet_his_cat(monkeypatch):
    d = _hall_dungeon()
    band = _dancing_band(d)
    lk = next(m for m in band if m.member == 'lee_know')
    d.sk_dance['aware'] = True
    d.sk_dance['beat'] = 2
    hero = _Hero(lk.x - 1, lk.y)
    monkeypatch.setitem(sk.data()['distracted']['lee_know'], 'chance', 1.0)
    assert lk.take_turn(hero, d, band) is False
    assert lk._sk_events and 'cat' in lk._sk_events[0]
    monkeypatch.setitem(sk.data()['distracted']['lee_know'], 'chance', 0.0)
    assert lk.take_turn(hero, d, band) is True


def test_seungmin_pitches_from_across_the_stage():
    d = _hall_dungeon()
    band = _dancing_band(d)
    s = next(m for m in band if m.member == 'seungmin')
    d.sk_dance['aware'] = True
    d.sk_dance['beat'] = 2
    hero = _Hero(s.x - 4, s.y)
    others = [s]
    assert s.take_turn(hero, d, others) is True
    felix = next(m for m in band if m.member == 'felix')
    assert felix.take_turn(_Hero(felix.x - 4, felix.y), d, [felix]) is False


def test_a_blow_that_lands_brings_its_quip():
    from player import Player
    z = sk.make_zombie('felix', 5, 5, 5)
    p = Player()
    p.x, p.y = 6, 5
    atk = z.attacks[0]
    random.seed(1)
    for _ in range(50):
        dmg, msg = z._resolve_blow(atk, p)
        if dmg > 0:
            assert msg.endswith(atk['quip'])
            break
    else:
        raise AssertionError('never landed')


def test_observe_says_his_own_line_and_the_beat():
    z = sk.make_zombie('lee_know', 5, 5, 1)
    assert sk.data()['observe']['lee_know'] in z.observe_line
    assert sk.data()['dance']['beat_tell'] in z.observe_line


def test_a_star_is_a_harmless_unharmed_ally_who_dances_round_the_hero():
    d = _hall_dungeon()
    s = sk.StarDancer('felix', 10, 10, slot=5)
    assert s.is_allied and sk.is_star(s) and s.name == 'Felix' and s.kind == 'sk_star_felix'
    assert s.take_damage(10 ** 6) == 0
    s.add_effect('stunned', 5)
    assert not s.status_effects
    hero = _Hero(12, 10)
    for _ in range(10):
        assert s.take_turn(hero, d, [s]) is False
    assert max(abs(s.x - hero.x), abs(s.y - hero.y)) <= 2


def test_watchers_are_the_ordinary_monsters_near_the_show():
    from monster import Monster
    d = _hall_dungeon()
    star = sk.StarDancer('han', 10, 10, slot=4)

    def mon(kind, x, y):
        return Monster({**MONS[kind], 'id': kind}, x, y)
    near = mon('goblin', 13, 10)
    far = mon('goblin', 30, 10)
    boss = mon('lamia', 12, 11)
    golem = mon('clay_golem', 11, 12)
    blind = mon('goblin', 9, 9)
    blind.status_effects['blinded'] = 3
    swarm = mon('scarab_swarm', 11, 9)                  # cannot be stunned (round 3)
    assert swarm.resists_control('stunned')
    got = sk.watchers([star, near, far, boss, golem, blind, swarm], [star], d)
    assert got == [near]
    assert set(sk.near_show([star, near, far, boss, golem, blind, swarm], [star], d)) == {
        near, boss, golem, swarm}


def test_the_watch_line_is_said_only_of_what_the_show_held():
    """Round 3: the watch line played for a stun-immune creature, and the
    hold was added again every turn of the show (12 turns stunned by a
    6-turn show)."""
    from monster import Monster
    g = _game('__test_sk_watch__')
    _open_floor(g)
    gob = Monster({**MONS['goblin'], 'id': 'goblin'}, 13, 10)
    swarm = Monster({**MONS['scarab_swarm'], 'id': 'scarab_swarm'}, 12, 12)
    boss = Monster({**MONS['lamia'], 'id': 'lamia'}, 10, 14)
    for m in (gob, swarm, boss):
        m._aware = True
    g.monsters.extend([gob, swarm, boss])
    g._refresh_fov()
    _read_photo(g)
    log = _log(g)
    assert 'The Goblin stops to watch the show.' in log
    assert 'Scarab Swarm stops to watch' not in log and not swarm.has_effect('stunned')
    assert 'The Scarab Swarm pays the show no mind.' in log
    assert 'Lamia has seen better shows, and does not stop.' in log
    watch = int(sk.data()['stars']['watch_turns'])
    for _ in range(3):
        gob.x, gob.y = 13, 10
        g._advance_turn()
        assert gob.status_effects.get('stunned', 0) <= watch
    assert log.count('pays the show no mind') == 1


def test_leaving_the_floor_ends_the_show_with_its_bow():
    g = _game('__test_sk_leave__')
    _open_floor(g)
    _read_photo(g)
    assert [m for m in g.monsters if sk.is_star(m)]
    here = g.dungeon_level
    g.msg_log.clear()
    g._change_level(here + 1, enter_from_top=True)
    assert sk.data()['stars']['bow'] in _log(g)
    assert not [m for m in g.monsters if sk.is_star(m)]
    g._change_level(here, enter_from_top=False)
    assert not [m for m in g.monsters if sk.is_star(m)]       # a revisit finds no show


# ---------------------------------------------------------------------------
# The game: the idol, the trip, the deaths, the photo
# ---------------------------------------------------------------------------

def test_the_idol_stands_only_on_its_floor_where_the_hero_can_reach_it():
    import decor
    g = _game('__test_sk_idol__')
    g._stray_kids = dict(sk.new_run_state(), floor=10)
    g._change_level(9, enter_from_top=True)
    assert sk.idol_id() not in (g.dungeon.__dict__.get('fixtures') or {}).values()
    g._change_level(10, enter_from_top=True)
    pos = [p for p, f in g.dungeon.fixtures.items() if f == sk.idol_id()]
    assert len(pos) == 1 and g._stray_kids['spawned']
    assert pos[0] in g.dungeon.fixture_blocks
    reach = decor._walk_set(g.dungeon)
    x, y = pos[0]
    assert any((x + dx, y + dy) in reach for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def test_the_idol_finds_a_reachable_spot_on_every_floor_it_can_stand_on():
    """It happens every run, so a floor whose walls are all dressed must
    still take it, and never where it cuts the floor in two."""
    import decor
    from dungeon import generate_dungeon
    for level in range(8, 13):
        for seed in range(6):
            random.seed(level * 100 + seed)
            d = generate_dungeon(80, 50, level)
            before = decor._reachable_count(d)
            pos = decor.place_event_stand(d, sk.idol_id(), (), (), random.Random(seed))
            assert pos is not None, (level, seed)
            assert decor._reachable_count(d) == before - 1, (level, seed)


def test_one_bump_says_what_it_is_the_second_touches_it():
    g = _game('__test_sk_touch__')
    pos = _idol_floor(g, 9)
    dx, dy = _beside(g, pos)
    deepest = g.player.deepest_floor_reached
    g.msg_log.clear()
    g._do_move(dx, dy)
    assert g.dungeon_level == 9
    assert sk.data()['idol']['first_bump'] in _log(g)
    import decor
    assert decor.fixture_def(sk.idol_id())['look'] not in _log(g)   # Observe says what it is
    g._do_move(dx, dy)
    assert g.dungeon_level == STRAY_KIDS_STAGE
    st = g._stray_kids
    assert st['touched'] and st['return_floor'] == 9
    assert g.player.deepest_floor_reached == deepest          # a side trip, not depth
    assert set(sk.zombie_kinds()) <= g.player.lore_known_monster_ids
    import family_lore
    assert family_lore.knowledge(g.player, 'sk_zombie_felix') == family_lore.KNOWN
    wings = g.dungeon.rooms[0]
    assert wings.x <= g.player.x < wings.x + wings.width
    assert len(_band(g)) == 8


def test_the_idol_calls_the_hero_over_once_when_he_first_sees_it():
    g = _game('__test_sk_call__')
    pos = _idol_floor(g, 9)
    call = sk.data()['idol']['call']
    g.visible = set()
    g._stray_kids_tick()
    assert call not in _log(g) and not g._stray_kids['called']
    _beside(g, pos)
    g._stray_kids_tick()
    g._stray_kids_tick()
    assert _log(g).count(call) == 1 and g._stray_kids['called']
    assert tuple(g._stray_kids['pos']) == tuple(pos)
    g.target_cursor_x, g.target_cursor_y = pos
    g._confirm_observe()
    import decor
    assert decor.fixture_def(sk.idol_id())['look'] in _log(g)


def test_the_stage_door_takes_the_hero_back_and_the_idol_is_spent():
    g = _game('__test_sk_door__')
    pos = _on_stage(g, 9)
    from dungeon import STAIRS_DOWN
    door = next((x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)
                if g.dungeon.tiles[y][x] == STAIRS_DOWN)
    g.player.x, g.player.y = door
    g._descend_stairs()
    assert g.dungeon_level == 9 and g._stray_kids['outcome'] == 'left'
    assert g.dungeon.fixture_state.get(pos) == 'spent'
    dx, dy = _beside(g, pos)
    g._do_move(dx, dy)
    g._do_move(dx, dy)
    assert g.dungeon_level == 9                      # one trip a run


def test_a_potion_of_gain_level_or_any_side_exit_leaves_for_the_idols_floor():
    g = _game('__test_sk_leave__')
    _on_stage(g, 11)
    assert g._side_floor_return_level() == 11
    g._leave_side_floor()
    assert g.dungeon_level == 11


def test_nothing_wanders_onto_the_stage():
    g = _game('__test_sk_wander__')
    _on_stage(g)
    before = len(g.monsters)
    from floor_curve import wander_interval
    g.turn_count = wander_interval(g.dungeon_level) * 3
    for y in range(g.dungeon.height):
        for x in range(g.dungeon.width):
            g.dungeon.explored.add((x, y))
    g.visible = set()
    g._maybe_wander_spawn()
    assert len(g.monsters) == before


def _kill(g, m):
    m.hp = 0
    m.alive = False
    g._on_monster_killed(m)


def test_they_crumble_to_nothing_and_the_last_leaves_the_photo():
    from items import Corpse
    g = _game('__test_sk_photo__')
    _on_stage(g)
    band = _band(g)
    for m in band[:-1]:
        _kill(g, m)
        assert not any(i.id == sk.photo_id() for i in g.ground_items)
    last = band[-1]
    _kill(g, last)
    assert not any(isinstance(i, Corpse) for i in g.ground_items)
    photos = [i for i in g.ground_items if i.id == sk.photo_id()]
    assert len(photos) == 1 and (photos[0].x, photos[0].y) == (last.x, last.y)
    assert photos[0].identified
    st = g._stray_kids
    assert st['photo_dropped'] and st['outcome'] == 'cleared'
    text = _log(g)
    assert 'glitter and grave-dust' in text


def test_when_bang_chan_falls_the_rest_lose_the_count():
    g = _game('__test_sk_leader__')
    _on_stage(g)
    lead = next(m for m in _band(g) if m.member == 'bang_chan')
    _kill(g, lead)
    rest = _band(g)
    assert len(rest) == 7
    assert all(m.quarrelsome and m.has_effect('confused') for m in rest)


def test_the_dance_runs_on_the_real_stage_and_the_band_shouts():
    g = _game('__test_sk_dance__')
    _on_stage(g)
    hall = g.dungeon.rooms[1]
    g.player.x, g.player.y = hall.x + 3, 25
    g._refresh_fov()
    g._sk_rng = random.Random(3)
    for _ in range(30):
        g._advance_turn()
        if g.player.is_dead():
            break
    dance = sk.dance_of(g.dungeon)
    assert dance['aware'] and dance['beat'] >= 30
    text = _log(g)
    assert sk.data()['stage']['seen'] in text
    assert any(f'Zombie {sk.member_name(m)}' in text for m in MEMBERS)
    # told as one band, once, not eight first-sight tells
    assert text.count(sk.data()['stage']['tell']) == 1
    assert 'hurt it most' not in text


def test_the_stage_is_lit_so_the_whole_dance_can_be_seen():
    g = _game('__test_sk_lit__')
    _on_stage(g)
    hall = g.dungeon.rooms[1]
    g.player.x, g.player.y = hall.x + 1, 25
    g._refresh_fov()
    far = (hall.x + hall.width - 2, 25)
    assert far[0] - g.player.x > g.player.get_sight_radius() + 5
    assert far in g.visible and far in g.dungeon.explored
    g.player.status_effects['blinded'] = 5
    g._refresh_fov()
    assert far not in g.visible


def test_observe_on_a_member_says_his_line():
    g = _game('__test_sk_observe__')
    _on_stage(g)
    hall = g.dungeon.rooms[1]
    z = next(m for m in _band(g) if m.member == 'felix')
    g.player.x, g.player.y = max(hall.x, z.x - 3), z.y
    g._refresh_fov()
    assert (z.x, z.y) in g.visible
    g.target_cursor_x, g.target_cursor_y = z.x, z.y
    g._confirm_observe()
    text = _log(g)
    assert sk.data()['observe']['felix'] in text


def _read_photo(g):
    from items import load_items, copy_at
    tpl = next(s for s in load_items('scroll') if s.id == sk.photo_id())
    photo = copy_at(tpl, g.player.x, g.player.y)
    g._apply_scroll_effect(photo)


def _open_floor(g):
    """The hero alone on an open floor (a hall), so the show's numbers are
    the only thing under test."""
    g.dungeon = _hall_dungeon()
    g.dungeon_level = 9
    g.monsters[:] = []
    g.ground_items[:] = []
    g.pets = []
    g.player.x, g.player.y = 10, 10
    g._refresh_fov()


def test_the_photo_puts_on_a_show_that_stops_the_room_then_bows_out():
    from monster import Monster
    g = _game('__test_sk_show__')
    _open_floor(g)
    gob = Monster({**MONS['goblin'], 'id': 'goblin'}, 13, 10)
    boss = Monster({**MONS['lamia'], 'id': 'lamia'}, 10, 15)
    g.monsters.extend([gob, boss])
    g._refresh_fov()
    _read_photo(g)
    stars = [m for m in g.monsters if sk.is_star(m)]
    assert len(stars) == 8 and all(s.is_allied for s in stars)
    assert len({(s.x, s.y) for s in stars}) == 8
    assert gob.has_effect('stunned') and not boss.has_effect('stunned')
    assert 'stops to watch the show' in _log(g)
    turns = sk.data()['stars']['dance_turns']
    for _ in range(turns):
        assert [m for m in g.monsters if sk.is_star(m)]
        gob.x, gob.y = 13, 10                   # (held where he watches)
        g._advance_turn()
    assert not [m for m in g.monsters if sk.is_star(m)]
    assert all(s.hp == s.max_hp for s in stars)
    assert sk.data()['stars']['bow'] in _log(g)


def test_walking_into_a_dancer_swaps_places():
    g = _game('__test_sk_swap__')
    _open_floor(g)
    _read_photo(g)
    s = next(m for m in g.monsters if sk.is_star(m))
    g.player.x, g.player.y = s.x + 1, s.y
    if not g.dungeon.is_walkable(g.player.x, g.player.y):
        g.player.x, g.player.y = s.x - 1, s.y
    g._refresh_fov()
    me, there = (g.player.x, g.player.y), (s.x, s.y)
    g._do_move(there[0] - me[0], there[1] - me[1])
    assert (g.player.x, g.player.y) == there
    # he took the hero's tile, then danced on a step (his turn came after)
    assert max(abs(s.x - me[0]), abs(s.y - me[1])) <= 1 and s.hp == s.max_hp
    assert 'You slip past' in _log(g)


def test_the_photo_can_be_carried_but_never_sold_or_stolen():
    import theft
    import traders
    g = _game('__test_sk_keepsake__')
    photo = g._stray_kids_photo(g.player.x, g.player.y)
    g.ground_items.append(photo)
    g._pickup(target=photo)
    assert photo in g.player.inventory
    assert photo not in theft.stealable(g.player)
    why = traders.refusal({'buys': 'all', 'pronoun': 'he'}, photo, known=True,
                          cursed_known=False, quest_ids=g._QUEST_PIECE_IDS)
    assert why == 'Not for sale'
    g._do_drop_item(photo)
    assert photo not in g.player.inventory and photo in g.ground_items


def test_reading_the_photo_is_one_grammar_question_and_a_bad_read_keeps_it():
    g = _game('__test_sk_read__')
    photo = g._stray_kids_photo(g.player.x, g.player.y)
    g.player.inventory.append(photo)
    started = {}

    def fake_start(**kw):
        started.update(kw)
    g.quiz_engine.start_quiz = fake_start
    g._read_scroll(photo)
    assert started['subject'] == 'grammar' and started['threshold'] == 1

    class R:
        success = False
    started['callback'](R())
    assert photo in g.player.inventory                       # single_copy: it survives
    R.success = True
    g._read_scroll(photo)
    started['callback'](R())
    assert photo not in g.player.inventory
    assert [m for m in g.monsters if sk.is_star(m)]


# ---------------------------------------------------------------------------
# Save and load, QA
# ---------------------------------------------------------------------------

def _roundtrip(g, name, tmp_path, monkeypatch):
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    save_system.settle_unfinished_actions(g)
    assert save_system.save_game(g)
    state = save_system.load_game(name)
    g2 = Game(_screen(), player_name=name)
    g2.load_state(state)
    g2.state = STATE_PLAYER
    return g2


def test_save_and_load_on_the_stage_mid_dance(tmp_path, monkeypatch):
    name = '__test_sk_save__'
    g = _game(name)
    _on_stage(g, 10)
    for _ in range(3):
        g._advance_turn()
    beat = sk.dance_of(g.dungeon)['beat']
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    assert g2.dungeon_level == STRAY_KIDS_STAGE
    assert g2._stray_kids['touched'] and g2._stray_kids['return_floor'] == 10
    band = _band(g2)
    assert len(band) == 8 and all(isinstance(m, sk.ZombieMember) for m in band)
    assert sk.dance_of(g2.dungeon)['beat'] == beat
    g2._leave_side_floor()
    assert g2.dungeon_level == 10


def test_a_save_from_before_the_egg_has_no_idol(tmp_path, monkeypatch):
    name = '__test_sk_old_save__'
    g = _game(name)
    del g._stray_kids
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    assert g2._stray_kids['floor'] is None and not g2._stray_kids['spawned']


def test_qa_shift_k_sets_the_idol_down_then_hands_over_the_photo():
    g = _game('__test_sk_qa__')
    g.player.qa_tools = True
    g._qa_stray_kids()
    beside = [p for p, f in g.dungeon.fixtures.items() if f == sk.idol_id()]
    assert len(beside) == 1
    x, y = beside[0]
    assert max(abs(x - g.player.x), abs(y - g.player.y)) == 1
    assert g._stray_kids['floor'] == g.dungeon_level and not g._stray_kids['touched']
    g._qa_stray_kids()
    assert any(i.id == sk.photo_id() for i in g.player.inventory)
    g.player.qa_tools = False
    n = len(g.player.inventory)
    g._qa_stray_kids()
    assert len(g.player.inventory) == n


def test_dying_on_the_stage_leaves_no_bones(monkeypatch):
    import bones
    g = _game('__test_sk_bones__')
    _on_stage(g)
    called = []
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: called.append(a))
    import save_system
    monkeypatch.setattr(save_system, 'delete_save', lambda *a, **k: None)
    g.defeat_reason = 'died'
    g._on_game_over()
    assert called == []
