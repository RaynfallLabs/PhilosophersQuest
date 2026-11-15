"""The Stray Kids easter egg (src/stray_kids.py, src/game_stray_kids.py).

Every run a gold shrine to the band stands on one floor of 8-12. Walk into it
twice and the hero is on the Zombie Stage, a side floor like the Cow Level,
where the eight members wait as zombies. The fight is a dance-off (Brandon,
2026-11-14): "B-B-B-BOSS BATTLE! DANCE OFF!", practice as often as wanted,
then eight rounds of Simon Says on the Mooble's dance screen, a member
leading each. They crumble to nothing, the last leaves a signed photo, and
the photo calls the band up alive for a short show that stops the room.

Data tests for every new JSON entry, pure tests for the Simon Says rules and
the earworm, and behaviour tests on a real headless Game: the stage is a
randomized floor-8-to-12 event, so these are the proof besides Brandon's own
play. The feel of the dance-off is his play-test.
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
import pytest  # noqa: E402

import rhythm  # noqa: E402
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
DO = sk.dance_off()


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

def test_the_data_names_eight_members_each_with_his_place_and_lines():
    d = sk.data()
    assert MEMBERS == ['bang_chan', 'lee_know', 'changbin', 'hyunjin', 'han',
                       'felix', 'seungmin', 'i_n']
    assert set(d['names']) == set(MEMBERS)
    form = d['stage']['formation']
    assert len(form) == 8 and len({tuple(o) for o in form}) == 8
    for m in MEMBERS:
        assert d['observe'][m] and d['shouts'][m], m
        lead = DO['leaders'][m]
        assert lead['open'] and lead['roast'], m
    assert d['chance_per_run'] == 1.0 and (d['first_floor'], d['last_floor']) == (8, 12)
    assert len(d['stars']['ring']) == 16
    # The old combat dance is gone from the data.
    assert 'dance' not in d and 'band_id' not in d


def test_the_dance_off_numbers_are_written_in_the_data():
    """Simon Says: 4 steps, one more a round, to 11 in the eighth; a little
    faster each round; three strikes; the Mooble's judging windows."""
    assert (DO['first_steps'], DO['steps_per_round'], DO['strikes']) == (4, 1, 3)
    assert (DO['bpm_first'], DO['bpm_per_round']) == (84, 4)
    assert len(DO['choreography']) >= DO['first_steps'] + (sk.rounds() - 1) * DO['steps_per_round']
    assert set(DO['choreography']) <= set(rhythm.DIRS)
    assert DO['memory'] is True
    assert 0 < DO['pass_share'] <= 1 and DO['max_misses'] >= 1
    ann = DO['announce']
    assert ann['log'] == 'B-B-B-BOSS BATTLE! DANCE OFF!'
    assert ann['top'] == 'B-B-B-BOSS BATTLE!' and ann['main'] == 'DANCE OFF!'
    ew = DO['earworm']
    assert ew['max_damage'] >= 1 and ew['effect'] in ew['effects']
    # Every member's song carries a hindrance the earworm can name.
    for m in MEMBERS:
        atk = sk.earworm_attack(m)
        assert atk.get('quip') and atk.get('effect') in ew['effects'], (m, atk)


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


def test_the_band_is_never_rolled_as_a_runs_mini_boss_and_is_no_war_band():
    """They do not fight, so they are no war-band any more (its entry went
    with the old combat dance)."""
    import war_bands
    from level_manager import LevelManager
    for seed in range(15):
        random.seed(seed)
        planned = LevelManager()._roll_planned_mini_bosses()
        assert not any(str(v).startswith('sk_') for v in planned.values())
    assert 'stray_kids' not in war_bands.data()['bands']
    for b in war_bands.data()['bands'].values():
        for role in ('leader', 'guard'):
            assert not any(str(k).startswith('sk_') for k in b.get(role) or ())


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
    """Made-up lines only (no real lyrics), short enough to read in play,
    and none trails off in an ellipsis on screen."""
    d = sk.data()
    lines = list(d['shouts']['band']) + list(d['shouts']['songs']) + list(d['stars']['lines'])
    for m in MEMBERS:
        lines += d['shouts'][m]
        lines += DO['leaders'][m]['open'] + DO['leaders'][m]['roast']
    for line in lines:
        assert 0 < len(line) <= 90, line
        assert not line.rstrip().endswith('...'), line


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
    share = d['shouting']
    assert 0 < share['member_line_share'] + share['song_line_share'] < 1


def test_the_help_page_tells_of_both_dances():
    page = _json('data', 'ui', 'how_quizzes_work.json')
    sec = next(s for s in page['sections'] if 'Dances' in s['heading'])
    text = ' '.join(sec['paragraphs'])
    assert 'old mines' in text and 'Simon Says' in text and 'practise' in text
    assert 'three strikes' in text


def test_the_announcement_banner_is_the_kill_banners_look():
    """'B-B-B-BOSS BATTLE! DANCE OFF!' is the strike finisher's banner (the
    "<Target> Slain" a kill shows), registered with a time and type of its
    own, and the fanfare is in sound_system."""
    from effects_runtime import build_default_runtime
    from effects.strike_finisher import StrikeFinisher
    import sound_system
    rt = build_default_runtime()
    h = rt.handlers['dance_off_banner']
    assert isinstance(h, StrikeFinisher) and h.durations_ms['big'] >= 2000 and h.main_pt > 36
    rt.fire('dance_off_banner', {'main_line': 'DANCE OFF!', 'top_line': 'B-B-B-BOSS BATTLE!',
                                 'color': (255, 96, 200), 'tier': 'big'})
    assert h.active and h._main_line == 'DANCE OFF!' and h._top_line == 'B-B-B-BOSS BATTLE!'
    assert h.tier == 'big'
    # The ordinary finisher is unchanged.
    fin = rt.handlers['strike_finisher']
    rt.fire('strike_finisher', {'chain': 3, 'damage': 7, 'killed': True, 'rank_name': 'Solid',
                                'target_name': 'Goblin'})
    assert fin._main_line == 'Goblin Slain'
    import inspect
    assert "'dance_off'" in inspect.getsource(sound_system.init)


# ---------------------------------------------------------------------------
# The roll and the side floor
# ---------------------------------------------------------------------------

def test_every_run_has_the_idol_on_a_floor_from_8_to_12():
    for seed in range(40):
        random.seed(seed)
        st = sk.new_run_state()
        assert 8 <= st['floor'] <= 12
        assert not st['spawned'] and not st['touched'] and not st['photo_dropped']
        assert st['challenge'] is None and st['dancing'] is None


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


def test_the_stage_has_wings_a_door_out_and_the_band_posed_in_its_hall():
    from dungeon import STAIRS_DOWN, STAIRS_UP
    d, mons, items = sk.build_stage()
    assert items == [] and len(mons) == 8
    assert [m.kind for m in mons] == [sk.zombie_kind(m) for m in MEMBERS]
    wings, hall = d.rooms
    downs = [(x, y) for y in range(d.height) for x in range(d.width) if d.tiles[y][x] == STAIRS_DOWN]
    assert len(downs) == 1 and wings.x <= downs[0][0] < wings.x + wings.width
    assert not any(d.tiles[y][x] == STAIRS_UP for y in range(d.height) for x in range(d.width))
    for slot, m in enumerate(mons):
        assert hall.x <= m.x < hall.x + hall.width and d.is_walkable(m.x, m.y)
        assert (m.x, m.y) == sk.place_of(d, slot)
        assert m.is_allied and not getattr(m, '_band', None)
    assert len({(m.x, m.y) for m in mons}) == 8
    # Bang Chan at the point of the V, nearest the wings.
    assert min(mons, key=lambda m: m.x).member == 'bang_chan'
    assert not d.__dict__.get('sk_dance')
    fixtures = set(d.fixtures.values())
    assert {'sk_speaker', 'brazier_lit', 'carpet'} <= fixtures
    ex, ey = sk.stage_edge(d)
    assert sk.on_stage(d, ex, ey) and not sk.on_stage(d, ex - 1, ey) and d.is_walkable(ex, ey)


# ---------------------------------------------------------------------------
# The dance-off (pure)
# ---------------------------------------------------------------------------

def test_simon_says_each_round_is_the_last_and_one_step_more():
    phrases = [sk.round_phrase(i) for i in range(sk.rounds())]
    assert [len(p) for p in phrases] == [4, 5, 6, 7, 8, 9, 10, 11]
    for a, b in zip(phrases, phrases[1:]):
        assert b[:len(a)] == a and len(b) == len(a) + 1
    assert [s[0] for s in phrases[-1]] == list(range(11))          # one step a beat
    assert [s[1] for s in phrases[-1]] == DO['choreography'][:11]
    assert [sk.round_bpm(i) for i in range(sk.rounds())] == [84, 88, 92, 96, 100, 104, 108, 112]
    # Whole bars, with at least a beat of rest between the call and the turn.
    for i in range(sk.rounds()):
        n = sk.round_steps(i)
        pb = sk.phrase_beats(n)
        assert pb % 4 == 0 and pb >= n + 1, (i, n, pb)
        tl = sk.round_timeline(i)
        assert len(tl['call']) == len(tl['response']) == n
        assert tl['response_start'] - tl['call'][-1][0] >= tl['beat_ms'] * 2 - 1
        assert tl['beat_ms'] == pytest.approx(60000 / sk.round_bpm(i))


def test_the_rounds_and_the_strikes():
    assert sk.after_round(True, 3, 7) == ('next', 3)
    assert sk.after_round(True, 1, 0) == ('won', 1)
    assert sk.after_round(False, 3, 7) == ('retry', 2)
    assert sk.after_round(False, 2, 7) == ('retry', 1)
    assert sk.after_round(False, 1, 7) == ('lost', 0)
    # A whole dance-off: lose the second round twice, win the rest.
    standing, strikes, plays = 8, sk.strikes(), [True, False, False] + [True] * 7
    for won in plays:
        if won:
            standing -= 1
        outcome, strikes = sk.after_round(won, strikes, standing)
    assert (outcome, strikes, standing) == ('won', 1, 0)


def test_the_earworm_never_kills():
    for m in MEMBERS:
        for hp in (1, 2, 3, 5, 40):
            for seed in range(30):
                ew = sk.earworm(m, hp, random.Random(seed))
                assert 0 <= ew['damage'] <= DO['earworm']['max_damage']
                assert ew['damage'] < hp or ew['damage'] == 0
                assert ew['effect'] and ew['turns'] >= 1 and ew['song'] and ew['quip']
    assert all(sk.earworm(m, 1, random.Random(1))['damage'] == 0 for m in MEMBERS)
    # His own song: Han's speed rap confuses; Bang Chan's demo puts you to sleep.
    assert sk.earworm('han', 30, random.Random(1))['song'] == 'Speed-Rap Song'
    assert sk.earworm('bang_chan', 30, random.Random(1))['effect'] == 'sleeping'


def test_a_member_is_a_performer_who_takes_no_harm_and_never_strikes():
    from player import Player
    z = sk.make_zombie('felix', 5, 5, 5)
    hp = z.hp
    assert z.is_allied and z.take_damage(10 ** 6) == 0 and z.hp == hp
    z.add_effect('stunned', 5)
    z.hold('confused', 5)
    assert not z.status_effects
    p = Player()
    p.x, p.y = 6, 5
    assert z.take_turn(p, None, [z]) is False and (z.x, z.y) == (5, 5)
    assert sk.data()['observe']['felix'] in z.observe_line
    assert DO['observe_tell'] in z.observe_line


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
    assert st['challenge'] is None                             # not on the stage yet


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
    import wanderers
    wanderers.make_due(g.dungeon)
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


def test_the_stage_is_lit_so_the_whole_band_can_be_seen():
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
    assert sk.data()['observe']['felix'] in text and DO['observe_tell'] in text


# ---------------------------------------------------------------------------
# The dance-off on a real Game (the fake clock, the screen's own keys)
# ---------------------------------------------------------------------------

_ARROWS = {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'up': pygame.K_UP, 'down': pygame.K_DOWN}


def _clock(g, start=80_000):
    now = [start]
    g._mooble_clock_fn = lambda: now[0]
    return now


def _dance(g, now, presses='on_time'):
    """Space, then the whole round on the fake clock: every beat's tick and
    the keys at their times (on time, or a list of (t, dir) from the start)."""
    from game_states import STATE_MOOBLE_DANCE
    assert g.state == STATE_MOOBLE_DANCE and g._mdance['phase'] == 'ready'
    g._mooble_dance_key(pygame.K_SPACE)
    md = g._mdance
    t0, tl = md['t0'], md['tl']
    keys = rhythm.on_time(tl['response']) if presses == 'on_time' else list(presses)
    events = sorted([(t, 'key', d) for t, d in keys]
                    + [(k * tl['beat_ms'], 'tick', None) for k in range(tl['beats'] + 2)])
    for t, kind, d in events:
        now[0] = t0 + int(round(t))
        if kind == 'tick':
            g._mooble_dance_tick()
        elif md['phase'] == 'play':
            g._mooble_dance_key(_ARROWS[d])
    now[0] = t0 + int(g._mooble_end_ms()) + 5
    g._mooble_dance_tick()
    assert md['phase'] == 'result'
    return md


def _to_the_card(g):
    """On the stage: the hero steps onto it, the band sees him, and the
    dance-off's card opens once the banner is over."""
    from game_states import STATE_MOOBLE_DANCE
    g.player.x, g.player.y = sk.stage_edge(g.dungeon)
    g._refresh_fov()
    g._advance_turn()
    assert g._stray_kids['challenge'] == 'pending'
    for _ in range(400):
        g.update(1 / 30)
        if g.state == STATE_MOOBLE_DANCE:
            break
    assert g.state == STATE_MOOBLE_DANCE and g._mdance['mode'] == 'practice'
    assert g._mdance['phase'] == 'ready' and g._stray_kids['challenge'] == 'made'
    return g._mdance


def test_setting_foot_on_the_stage_brings_the_announcement_then_the_card():
    g = _game('__test_sk_announce__')
    _on_stage(g)
    g.msg_log.clear()
    g.player.x, g.player.y = sk.stage_edge(g.dungeon)
    g._refresh_fov()
    g._advance_turn()
    text = _log(g)
    st = sk.data()['stage']
    for line in (st['seen'], st['pose'], DO['announce']['log'], st['tell']):
        assert line in text, line
    banner = g.effects_runtime.handlers['dance_off_banner']
    assert banner.active and banner._main_line == 'DANCE OFF!'
    g._advance_turn()
    assert text.count(DO['announce']['log']) == _log(g).count(DO['announce']['log']) == 1
    # The card waits for the banner, then opens on its own.
    g.update(1 / 30)
    from game_states import STATE_PLAYER
    assert g.state == STATE_PLAYER
    _ = _to_the_card.__doc__
    from game_states import STATE_MOOBLE_DANCE
    for _ in range(400):
        g.update(1 / 30)
        if g.state == STATE_MOOBLE_DANCE:
            break
    md = g._mdance
    assert md['owner'] == 'stray_kids' and md['mode'] == 'practice' and md['poses']['idle'] == 'sk_zombie_bang_chan'
    assert md['memory'] and len(md['tl']['response']) == 4 and md['bpm'] == 84


def test_practise_as_often_as_wanted_and_walk_away():
    import music
    g = _game('__test_sk_practise__')
    _on_stage(g)
    _to_the_card(g)
    now = _clock(g)
    hp, turn = g.player.hp, g.turn_count
    for _ in range(3):
        md = _dance(g, now)
        assert md['won'] and md['mode'] == 'practice'
        g._mooble_dance_key(pygame.K_RETURN)               # again
        md = g._mdance
        assert md['phase'] == 'play'
        g._mooble_dance_key(pygame.K_ESCAPE)               # stop: back to the card
        assert g._mdance['phase'] == 'ready' and g._mdance['mode'] == 'practice'
    md = _dance(g, now, presses=[])
    assert not md['won']                                   # a flop costs nothing
    assert g.player.hp == hp and g.turn_count == turn and not g.player.status_effects.get('confused')
    assert len(_band(g)) == 8 and not music._held
    g._mooble_dance_key(pygame.K_ESCAPE)                   # Not Yet
    from game_states import STATE_PLAYER
    assert g.state == STATE_PLAYER and g._stray_kids['dancing'] is None


def test_esc_on_the_card_through_the_key_handler_goes_back_to_play():
    """Esc through Game.handle_event: the card closes to play, and the same
    key press never goes on to open the exit prompt (the race's merge
    dropped the return after the dance screen's Esc)."""
    from game_states import STATE_PLAYER
    g = _game('__test_sk_esc__')
    _on_stage(g)
    _to_the_card(g)
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode='', mod=0, scancode=0))
    assert g.state == STATE_PLAYER


def test_a_round_won_makes_its_leader_fall_and_the_next_leads():
    g = _game('__test_sk_round__')
    _on_stage(g)
    _to_the_card(g)
    now = _clock(g)
    g.msg_log.clear()
    g._mooble_dance_key(pygame.K_d)
    md = g._mdance
    assert md['mode'] == 'dance' and md['sk_member'] == 'bang_chan' and md['sk_strikes'] == 3
    assert md['title'] == 'THE DANCE-OFF: ROUND 1 OF 8'
    assert md['ready_head'].startswith('Zombie Bang Chan')
    md = _dance(g, now)
    assert md['won'] and md['sk_outcome'] == 'next'
    lead = [m for m in g.monsters if getattr(m, 'member', '') == 'bang_chan']
    assert not lead or not lead[0].alive
    assert [m.member for m in _band(g)][0] == 'lee_know' and len(_band(g)) == 7
    text = _log(g)
    assert 'Zombie Bang Chan crumbles into glitter and grave-dust.' in text
    assert 'is slain' not in text
    import chronicle
    assert chronicle.logged(g, 'boss:sk_zombie_bang_chan')
    g._mooble_dance_key(pygame.K_RETURN)
    md = g._mdance
    assert md['sk_member'] == 'lee_know' and len(md['tl']['response']) == 5 and md['bpm'] == 88
    assert md['sk_strikes'] == 3 and md['title'] == 'THE DANCE-OFF: ROUND 2 OF 8'
    g._mooble_dance_key(pygame.K_ESCAPE)                   # danced through now: no way out
    assert g._mdance is md and md['phase'] == 'ready'


def test_a_round_lost_brings_the_earworm_and_three_strikes_lose_the_dance_off():
    import music
    g = _game('__test_sk_lost__')
    _on_stage(g)
    _to_the_card(g)
    now = _clock(g)
    g._mooble_dance_key(pygame.K_d)
    md = _dance(g, now)                                     # Bang Chan falls
    g._mooble_dance_key(pygame.K_RETURN)
    g.player.hp = 1                                         # the earworm must never kill
    g.msg_log.clear()
    for strike in (2, 1, 0):
        md = _dance(g, now, presses=[])
        assert not md['won'] and md['sk_strikes'] == strike
        assert md['sk_outcome'] == ('retry' if strike else 'lost')
        assert md['result_head'].startswith('Zombie Lee Know')
        assert any('gets stuck in your head' in ln for ln in md['result_lines'])
        assert g.player.hp == 1 and not g.player.is_dead()
        g._mooble_dance_key(pygame.K_RETURN)
    text = _log(g)
    assert "Zombie Lee Know's Dance-Teacher Correction gets stuck in your head." in text
    assert g.player.has_effect('confused')
    from game_states import STATE_PLAYER
    assert g.state == STATE_PLAYER and not music._held
    assert DO['laugh'] in _log(g)
    # The members still standing are back in their places; the fallen stay fallen.
    assert len(_band(g)) == 7
    for m in _band(g):
        assert (m.x, m.y) == sk.place_of(g.dungeon, m._sk_slot)
    assert (g.player.x, g.player.y) == sk.stage_edge(g.dungeon)
    import chronicle
    assert chronicle.logged(g, 'stray_kids:lost')
    assert g._stray_kids['lost'] == 1 and g._stray_kids['dancing'] is None


def test_challenge_again_after_a_loss_and_win_it_all():
    g = _game('__test_sk_rematch__')
    _on_stage(g)
    _to_the_card(g)
    now = _clock(g)
    g._mooble_dance_key(pygame.K_d)
    for _ in range(3):
        _dance(g, now, presses=[])
        g._mooble_dance_key(pygame.K_RETURN)
    from game_states import STATE_PLAYER, STATE_MOOBLE_DANCE
    assert g.state == STATE_PLAYER and len(_band(g)) == 8
    # Walk into Bang Chan: the card again, with the rematch line. (Once
    # the song in his head has worn off: a confused hero walks astray.)
    g.player.status_effects.clear()
    lead = _band(g)[0]
    g.player.x, g.player.y = lead.x - 1, lead.y
    g._refresh_fov()
    g.msg_log.clear()
    g._do_move(1, 0)
    assert g.state == STATE_MOOBLE_DANCE and g._mdance['mode'] == 'practice'
    assert sk.data()['stage']['challenge_again'] in _log(g)
    assert lead.alive and lead.hp == lead.max_hp            # walking into him is no blow
    g._mooble_dance_key(pygame.K_d)
    for r in range(8):
        md = _dance(g, now)
        assert md['won'] and md['sk_round'] == r
        g._mooble_dance_key(pygame.K_RETURN)
    assert g.state == STATE_PLAYER and not _band(g)
    assert any(getattr(i, 'id', '') == sk.photo_id() for i in g.ground_items)
    st = g._stray_kids
    assert st['photo_dropped'] and st['outcome'] == 'cleared' and st['dancing'] is None
    text = _log(g)
    assert DO['won_log'] in text and sk.data()['last_falls'] in text
    import chronicle
    assert chronicle.logged(g, 'stray_kids:cleared')
    assert all(chronicle.logged(g, f'boss:{k}') for k in sk.zombie_kinds())


def test_the_dance_off_raises_the_kill_events_as_the_fight_did():
    """Achievements hang on these: every member's fall is a kill (as it was
    when they were fought), with the same monster kinds and family, and the
    last one's fall drops the photo and writes the cleared Journal line."""
    import achievements
    g = _game('__test_sk_events__')
    seen = []
    g._seeker_event = lambda event, **f: seen.append((event, f)) or []
    _on_stage(g)
    _to_the_card(g)
    now = _clock(g)
    g._mooble_dance_key(pygame.K_d)
    for _ in range(8):
        _dance(g, now)
        g._mooble_dance_key(pygame.K_RETURN)
    kills = [f for e, f in seen if e == 'kill']
    assert [f['monster'] for f in kills] == sk.zombie_kinds()
    assert all(f['family'] == 'restless_dead' for f in kills)
    assert {e for e, _f in seen} <= set(achievements.KNOWN_EVENTS)
    st = g._stray_kids
    assert st['photo_dropped'] and st['outcome'] == 'cleared'
    import chronicle
    assert chronicle.logged(g, 'stray_kids:cleared')


def test_no_blow_or_spell_touches_the_band():
    g = _game('__test_sk_no_harm__')
    _on_stage(g)
    z = _band(g)[2]
    hp = z.hp
    g._cast_spell_effect({'effect': 'polymorph_spell', 'id': 'polymorph_spell', 'name': 'Polymorph',
                          'power': '', 'tier': 3}, target=z)
    assert sk.is_zombie(z) and z.alive and z.hp == hp
    assert z.take_damage(500, 'fire') == 0 and z.alive


# ---------------------------------------------------------------------------
# Watching the show
# ---------------------------------------------------------------------------

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


def test_a_save_mid_dance_off_restarts_the_round_on_load(tmp_path, monkeypatch):
    from game_states import STATE_MOOBLE_DANCE
    name = '__test_sk_save__'
    g = _game(name)
    _on_stage(g, 10)
    _to_the_card(g)
    now = _clock(g)
    g._mooble_dance_key(pygame.K_d)
    _dance(g, now)                                           # Bang Chan falls
    g._mooble_dance_key(pygame.K_RETURN)
    _dance(g, now, presses=[])                               # a strike
    g._mooble_dance_key(pygame.K_RETURN)
    g._mooble_dance_key(pygame.K_SPACE)                      # Lee Know's round, under way
    now[0] += 4000
    g._mooble_dance_tick()
    assert g._mdance['phase'] == 'play'
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    assert g2.dungeon_level == STRAY_KIDS_STAGE
    assert g2._stray_kids['touched'] and g2._stray_kids['return_floor'] == 10
    assert g2._stray_kids['dancing'] == {'mode': 'dance', 'strikes': 2, 'first': False}
    band = _band(g2)
    assert len(band) == 7 and all(isinstance(m, sk.ZombieMember) and m.is_allied for m in band)
    g2.update(1 / 30)
    assert g2.state == STATE_MOOBLE_DANCE
    md = g2._mdance
    assert md['phase'] == 'ready' and md['mode'] == 'dance' and md['sk_member'] == 'lee_know'
    assert md['sk_strikes'] == 2 and not md['sk_first']
    now2 = _clock(g2)
    md = _dance(g2, now2)
    assert md['won'] and md['sk_outcome'] == 'next'
    g2._mooble_dance_key(pygame.K_RETURN)
    g2._mdance = None
    g2._stray_kids['dancing'] = None
    g2._leave_side_floor()
    assert g2.dungeon_level == 10


def test_a_save_on_the_stage_from_before_the_dance_off_settles_the_band(tmp_path, monkeypatch):
    """An old save has the band fighting: hostile, hurt, held, quarrelling
    as a war-band in formation, the old dance on the floor. It loads with
    every member still standing back in his place as a performer, the
    fallen still fallen, and the announcement still to come."""
    name = '__test_sk_old_stage__'
    g = _game(name)
    _on_stage(g, 9)
    band = _band(g)
    _kill(g, band[0])
    for m in band[1:]:
        m.is_allied = False
        m.hp = max(1, m.max_hp // 3)
        m.__dict__['status_effects'] = {'confused': 4}
        m._band, m._band_role, m._band_leader = 'stray_kids@stage', 'guard', band[0]
        m.quarrelsome = True
        m.x, m.y = m.x - 6, m.y
    g.dungeon.sk_dance = {'anchor': [40, 25], 'beat': 17, 'shape': 2, 'aware': True, 'facing': [-1, 0]}
    for k in ('challenge', 'dancing'):
        g._stray_kids.pop(k, None)
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    band2 = _band(g2)
    assert len(band2) == 7 and 'sk_dance' not in g2.dungeon.__dict__
    for m in band2:
        assert m.is_allied and m.hp == m.max_hp and not m.status_effects
        assert not getattr(m, '_band', None) and not m.quarrelsome
        assert (m.x, m.y) == sk.place_of(g2.dungeon, m._sk_slot)
    assert g2._stray_kids.get('challenge') is None
    g2.player.x, g2.player.y = sk.stage_edge(g2.dungeon)
    g2._refresh_fov()
    g2._advance_turn()
    assert g2._stray_kids['challenge'] == 'pending'


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


def test_qa_shift_k_on_the_stage_opens_the_dance_off_at_once():
    from game_states import STATE_MOOBLE_DANCE
    g = _game('__test_sk_qa_stage__')
    _on_stage(g)
    g.player.qa_tools = True
    g._qa_stray_kids()
    assert g.state == STATE_MOOBLE_DANCE and g._mdance['owner'] == 'stray_kids'
    assert g._mdance['mode'] == 'practice'


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
