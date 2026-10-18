"""Callbacks, delayed rewards, the oath lifecycle and the Cow Level skip
(DEEDS_KARMA_DESIGN 4.7, 4.8, 3.4, 6.3, tests 8.5), on a real headless Game.

The shipped chains (Androcles' lion, Saint Cuthbert's Gospel, the courier and
the Watch Post) are driven through the real encounter screens; the rest uses
fixture outcomes. These are 10 to 30 floors deep, so they are proven here,
not by play-test.
"""
import copy
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import pygame  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=21):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name='__test_callbacks__')
    g.state = STATE_PLAYER
    # A plain run: no random encounters in the way of the ones under test.
    g._npc_encounter_levels = {}
    g._flavor_encounter_levels = {}
    return g


def _def(tag):
    import economy
    import flavor_encounters
    import npc_encounters
    for e in list(flavor_encounters.FLAVOR_ENCOUNTERS) + list(npc_encounters.ENCOUNTERS):
        if e['tag'] == tag:
            return economy.price_encounter(copy.deepcopy(e))
    raise KeyError(tag)


def _go(g, floor, via='stairs'):
    g._change_level(floor, enter_from_top=floor >= g.dungeon_level, via=via)
    g.monsters[:] = [m for m in g.monsters
                     if getattr(m, '_flavor_encounter_tag', None) or getattr(m, '_npc_encounter_tag', None)]
    g.dungeon.traps = {}


def _npc(g, tag):
    return next((m for m in g.monsters if m.alive and tag in (
        getattr(m, '_flavor_encounter_tag', None), getattr(m, '_npc_encounter_tag', None))), None)


def _meet(g, floor, tag, flavor=True):
    """Put the encounter on ``floor`` as the run plan would and arrive."""
    (g._flavor_encounter_levels if flavor else g._npc_encounter_levels)[floor] = _def(tag)
    _go(g, floor)
    npc = _npc(g, tag)
    assert npc is not None, tag
    return npc


def _choose(g, npc, key):
    from game_states import STATE_PLAYER
    if getattr(npc, '_flavor_encounter_tag', None):
        assert g._start_flavor_encounter(npc)
    else:
        assert g._start_npc_encounter(npc)
    g._npc_encounter_input(pygame.K_RETURN)
    g._npc_encounter_input(key)
    if g._npc_encounter_phase == 'select_item':
        g._npc_encounter_input(pygame.K_a)
    assert g._npc_encounter_phase == 'outcome', g._npc_encounter_phase
    g._npc_encounter_input(pygame.K_RETURN)
    assert g.state == STATE_PLAYER


def _pending(g, kind='encounter'):
    """The callbacks the test made. The Gate's run-start callback (floors
    94-98, karma_rules.json run_start_schedule) is pending in every run."""
    return [p for p in g._deeds['pending'] if p['kind'] == kind
            and p.get('source') != 'engine:run_start']


def _has(g, item_id):
    return any(getattr(i, 'id', '') == item_id for i in g.player.inventory)


# ---------------------------------------------------------------- the chains

def test_the_lion_comes_back_only_after_the_thorn_was_drawn():
    g = _game()
    g.player.hp = g.player.max_hp = 200
    lion = _meet(g, 10, 'flv_limping_lion')
    _choose(g, lion, pygame.K_1)                         # draw the thorn
    assert _has(g, 'lions_thorn')
    (cb,) = _pending(g)
    assert cb['spec']['encounter'] == 'flv_lion_remembers'
    assert 20 < cb['target'] <= 30 and cb['target'] not in (20, 40)
    _go(g, cb['target'])
    great = _npc(g, 'flv_lion_remembers')
    assert great is not None and _pending(g) == []
    _choose(g, great, pygame.K_2)                        # stand very still
    assert _has(g, 'lions_thorn')
    # Backing away instead schedules nothing (the chain used to be placed
    # whatever the hero chose).
    g2 = _game(seed=22)
    lion2 = _meet(g2, 10, 'flv_limping_lion')
    _choose(g2, lion2, pygame.K_3)
    assert _pending(g2) == []
    for f in range(20, 35):
        assert (g2._flavor_encounter_levels.get(f) or {}).get('tag') != 'flv_lion_remembers'


def test_the_watch_post_spawns_only_with_the_couriers_oath_open():
    import deeds
    g = _game()
    courier = _meet(g, 33, 'dying_messenger', flavor=False)
    karma = g.karma
    _choose(g, courier, pygame.K_1)                      # swear to carry it
    assert g.karma == karma                              # a promise pays only when kept
    assert deeds.oath_status(g._deeds, 'edric_dispatch') == 'open'
    (cb,) = _pending(g)
    assert 37 <= cb['target'] <= 47 and cb['target'] != 40
    _go(g, cb['target'])
    post = _npc(g, 'flv_watch_post')
    assert post is not None
    k = g.karma
    _choose(g, post, pygame.K_1)                         # hand it over
    assert deeds.oath_status(g._deeds, 'edric_dispatch') == 'kept'
    assert deeds.count(g._deeds, tag='virtue:kept') == 1
    assert g.karma == k + 1                              # the point, at the keep
    # An oath no longer open at arrival: no Watch Post, and the thread is lost.
    g2 = _game(seed=23)
    c2 = _meet(g2, 33, 'dying_messenger', flavor=False)
    _choose(g2, c2, pygame.K_1)
    (cb2,) = _pending(g2)
    floor, _d, block, _t = g2._deed_where()
    deeds.release_oath(g2._deeds, 'edric_dispatch', floor=floor, block=block)
    _go(g2, cb2['target'])
    assert _npc(g2, 'flv_watch_post') is None
    assert deeds.has(g2._deeds, 'flag.thread_lost.flv_watch_post')
    # Refusing the courier schedules no Watch Post at all.
    g3 = _game(seed=24)
    c3 = _meet(g3, 33, 'dying_messenger', flavor=False)
    _choose(g3, c3, pygame.K_3)
    assert _pending(g3) == []


def _choose_then_leave(g, npc, key):
    """An option that returns to the list ('then: options'): pick it, read
    the outcome, then leave with Esc (the choice already resolved it)."""
    from game_states import STATE_PLAYER
    assert g._start_flavor_encounter(npc)
    g._npc_encounter_input(pygame.K_RETURN)
    g._npc_encounter_input(key)
    assert g._npc_encounter_phase == 'outcome', g._npc_encounter_phase
    g._npc_encounter_input(pygame.K_RETURN)
    assert g._npc_encounter_phase == 'options'
    g._npc_encounter_input(pygame.K_ESCAPE)
    assert g.state == STATE_PLAYER


def test_the_gospel_chain_keeps_or_breaks_the_oath():
    import deeds
    g = _game()
    bearer = _meet(g, 42, 'flv_coffin_bearer')
    _choose(g, bearer, pygame.K_1)
    assert deeds.oath_status(g._deeds, 'cuthbert_gospel') == 'open'
    cbs = {p['spec']['encounter']: p['target'] for p in _pending(g)}
    assert set(cbs) == {'flv_relic_broker', 'flv_cuthbert_chapel'}
    assert 44 <= cbs['flv_relic_broker'] <= 50 and 49 <= cbs['flv_cuthbert_chapel'] <= 56
    karma = g.karma
    for tag, f in sorted(cbs.items(), key=lambda kv: kv[1]):
        _go(g, f)
        if tag == 'flv_relic_broker':
            _choose(g, _npc(g, tag), pygame.K_2)         # "the book is promised"
        else:
            _choose_then_leave(g, _npc(g, tag), pygame.K_1)   # lay it on the desk
    assert deeds.oath_status(g._deeds, 'cuthbert_gospel') == 'kept'
    assert g.karma == karma + 1                          # exactly one point, at the keep
    g2 = _game(seed=25)
    b2 = _meet(g2, 42, 'flv_coffin_bearer')
    _choose(g2, b2, pygame.K_1)
    broker_at = next(p['target'] for p in _pending(g2)
                     if p['spec']['encounter'] == 'flv_relic_broker')
    k2 = g2.karma
    _go(g2, broker_at)
    _choose(g2, _npc(g2, 'flv_relic_broker'), pygame.K_1)   # sell it
    assert deeds.oath_status(g2._deeds, 'cuthbert_gospel') == 'broken'
    assert deeds.count(g2._deeds, tag='vice:betray') == 1
    assert g2.karma == k2 - 1                            # exactly one point lost


def test_aldrics_altar_keeps_the_oath_and_pays_its_point_there():
    import deeds
    from dungeon import ALTAR
    g = _game()
    knight = _meet(g, 12, 'sir_aldric', flavor=False)
    k0 = g.karma
    _choose(g, knight, pygame.K_1)
    assert g.karma == k0                                 # taking the stone is a promise, 0
    oath = g._deeds['oaths']['aldric_lodestone']
    assert oath['status'] == 'open' and oath['made_block'] == 2
    assert g._deeds['threads']['aldric_candle']['status'] == 'open'
    # Down to block 3, then back up to an altar on floor 15.
    _go(g, 22)
    _go(g, 15)
    g.dungeon.tiles[g.player.y][g.player.x] = ALTAR
    stone = next(i for i in g.player.inventory if i.id == 'cursed_lodestone')
    g._do_drop_item(stone)
    assert deeds.oath_status(g._deeds, 'aldric_lodestone') == 'kept'
    assert g.karma == k0 + 1                             # the keep pays the point
    led = [e for e in g._deeds['karma']['ledger'] if e['kind'] == 'oath']
    assert led and led[-1]['block'] == 3 and led[-1]['applied'] == 1
    assert g._deeds['threads']['aldric_candle']['status'] == 'closed'


# ---------------------------------------------------------------- fixtures

def _outcome(g, o, tag='fx_source'):
    g._npc_encounter_active = {'tag': tag, 'name': 'Fixture'}
    g._apply_outcome_deeds(o, tag)
    g._npc_encounter_active = None


FX_FOLLOW = {'tag': 'fx_follow', 'name': 'Old Friend', 'symbol': '@', 'color': [1, 2, 3],
             'sprite_id': 'npc_traveler', 'min_level': 1, 'max_level': 99, 'role': 'story',
             'stakes': 'light', 'band': [1, 99], 'callback_only': True,
             'person': {'id': 'friend', 'name': 'old friend'},
             'text': 'An old friend.', 'options': [{'label': 'Wave', 'outcome': 'You wave.'}]}


def _with_fixture(monkey_list):
    import flavor_encounters
    flavor_encounters.FLAVOR_ENCOUNTERS.append(copy.deepcopy(FX_FOLLOW))
    monkey_list.append(lambda: flavor_encounters.FLAVOR_ENCOUNTERS.pop())


def test_a_delayed_reward_arrives_on_its_floor_once():
    g = _game()
    _go(g, 3)
    _outcome(g, {'delayed': [{'after_floors': [2, 3], 'reward': {'type': 'effect', 'effect': 'blessed',
                                                               'duration': 40},
                              'text': 'A sack waits at the foot of the stair.',
                              'chronicle': 'Someone left me bread. I kept the drawing.'}]})
    (p,) = _pending(g, 'reward')
    assert 5 <= p['target'] <= 6
    _go(g, p['target'] - 1)
    assert not g.player.has_effect('blessed') and _pending(g, 'reward')
    _go(g, p['target'])
    assert g.player.has_effect('blessed') and _pending(g, 'reward') == []
    assert any(e['kind'] == 'consequence' and 'bread' in e['text'] for e in g._chronicle)
    g.player.status_effects.pop('blessed', None)
    _go(g, p['target'] - 1)
    _go(g, p['target'] + 1)
    assert not g.player.has_effect('blessed')            # once


def test_a_missed_callback_is_carried_or_dropped():
    import deeds
    undo = []
    _with_fixture(undo)
    try:
        g = _game()
        _go(g, 3)
        _outcome(g, {'schedule': [{'encounter': 'fx_follow', 'after_floors': [2, 2],
                                   'thread': 'friend'}],
                     'thread': {'id': 'friend', 'hint': 'A friend is somewhere below.'}})
        (cb,) = _pending(g)
        assert cb['target'] == 5
        _go(g, 7, via='warp')                            # past it, within latest + 3
        assert _npc(g, 'fx_follow') is not None and _pending(g) == []
        g2 = _game(seed=31)
        _go(g2, 3)
        _outcome(g2, {'schedule': [{'encounter': 'fx_follow', 'after_floors': [2, 2],
                                    'if_missed': 'drop', 'thread': 'friend'}],
                      'thread': {'id': 'friend', 'hint': 'A friend is somewhere below.'}})
        _go(g2, 7, via='warp')
        assert _npc(g2, 'fx_follow') is None and _pending(g2) == []
        assert deeds.has(g2._deeds, 'flag.thread_lost.fx_follow')
        assert g2._deeds['threads']['friend']['status'] == 'closed'
        assert any('never did find out' in e['text'] for e in g2._chronicle)
        g3 = _game(seed=32)
        _go(g3, 3)
        _outcome(g3, {'schedule': [{'encounter': 'fx_follow', 'after_floors': [2, 2]}]})
        _go(g3, 12, via='warp')                          # too far past: dropped
        assert _npc(g3, 'fx_follow') is None and _pending(g3) == []
    finally:
        for u in undo:
            u()


def test_an_oath_past_its_due_floor_lapses_for_no_karma():
    import deeds
    g = _game()
    _go(g, 4)
    _outcome(g, {'oath': {'id': 'fx_vow', 'to': 'Brother Tuck', 'what': 'Light a candle.',
                          'due_floors': [1, 1]}})
    assert g._deeds['oaths']['fx_vow']['due_floor'] == 5
    k = g.karma
    _go(g, 5)
    assert deeds.oath_status(g._deeds, 'fx_vow') == 'open'
    _go(g, 6)
    assert deeds.oath_status(g._deeds, 'fx_vow') == 'lapsed'
    assert deeds.count(g._deeds, tag='vice:lapsed') == 1 and g.karma == k
    assert any(e['kind'] == 'oath' and 'Brother Tuck' in e['text'] for e in g._chronicle)


def test_a_cow_level_trip_lapses_nothing_delivers_nothing_and_binds_nothing():
    from boss_levels import COW_LEVEL
    import deeds
    undo = []
    _with_fixture(undo)
    try:
        g = _game()
        _go(g, 31)
        _outcome(g, {'oath': {'id': 'fx_vow', 'to': 'Tuck', 'what': 'x', 'due_floors': [1, 1]},
                     'schedule': [{'encounter': 'fx_follow', 'after_floors': [3, 3]}],
                     'delayed': [{'after_floors': [1, 1], 'reward': {'type': 'effect', 'effect': 'blessed',
                                                                   'duration': 20}}]})
        before = copy.deepcopy(g._deeds['pending'])
        calls = []
        real = g._road_arrive
        g._road_arrive = lambda lvl: (calls.append(lvl), real(lvl))
        g._cow_return_level = 31
        g._change_level(COW_LEVEL, enter_from_top=True, via='cow')
        assert COW_LEVEL not in calls
        assert g.player.deepest_floor_reached == 31
        assert deeds.oath_status(g._deeds, 'fx_vow') == 'open'
        assert g._deeds['pending'] == before
        assert not g.player.has_effect('blessed')
        assert COW_LEVEL not in g._flavor_encounter_levels
        g._change_level(31, enter_from_top=False, via='cow')
        assert g._deeds['pending'] == before and deeds.oath_status(g._deeds, 'fx_vow') == 'open'
    finally:
        for u in undo:
            u()


def test_a_callback_npc_in_a_cut_off_pocket_is_brought_within_reach():
    from dungeon import WALL
    undo = []
    _with_fixture(undo)
    try:
        g = _game()
        _go(g, 3)
        _outcome(g, {'schedule': [{'encounter': 'fx_follow', 'after_floors': [1, 1]}]})
        _go(g, 4)
        npc = _npc(g, 'fx_follow')
        assert npc is not None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    g.dungeon.tiles[npc.y + dy][npc.x + dx] = WALL
        assert (npc.x, npc.y) not in g._reachable_tiles(g.player.x, g.player.y)
        g._settle_monsters()
        assert (npc.x, npc.y) in g._reachable_tiles(g.player.x, g.player.y)
    finally:
        for u in undo:
            u()


def test_the_road_when_enabled_binds_anchors_at_start_and_light_slots_on_arrival(monkeypatch):
    import karma
    import road
    rules = dict(karma.rules())
    rules['road_enabled'] = True
    monkeypatch.setattr(karma, '_RULES', rules)
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(41)
    g = Game(_screen(), player_name='__test_callbacks__')
    g.state = STATE_PLAYER
    st = g._road
    assert st['enabled'] and len(st['slots']) == 45
    anchors = {f for f, s in st['slots'].items() if s['role'] == 'anchor'}
    assert set(g._npc_encounter_levels) == anchors
    for f, enc in g._npc_encounter_levels.items():
        assert enc['block'] == road.band_of(f)
    lights = sorted(f for f, s in st['slots'].items() if s['role'] == 'light')
    target = lights[0]
    assert target not in g._flavor_encounter_levels      # late binding
    _go(g, target)
    bound = st['slots'][target]['bound']
    if bound:
        assert g._flavor_encounter_levels[target]['tag'] == bound
        assert _npc(g, bound) is not None
    assert len(st['used_tags']) == len(set(st['used_tags']))
