"""Old Nickel, the murderer of sleepers (Brandon, 2026-11-17).

"Old Nickel is not nearly mean enough... we need to make it clear he will
murder people in their sleep for their things, more lines of dialogue." Then
his rules for the kobold's AI (ai_pattern stalker_coward,
Monster._stalker_turn):

1. He only attacks when the hero is right next to him.
2. When the hero moves toward him or around him in view, he says one of his
   lines: the pool without repeats until it runs out, then a short recurring
   set egging the hero on to rest; paced, not every step.
3. When the hero rests (the wait key), or is asleep, paralysed, confused or
   stunned, he darts in at double speed and attacks.
4. When the hero moves away, he follows, about 3 tiles off.
5. When the hero moves toward him, he backs away, until he cannot; then he
   attacks once the hero is next to him.

And: "his lines should be more like Gollum" (an homage, never Tolkien's
words). Floors 1-8, randomized: these are logic tests on a real headless
Game, in an arena carved into its floor.
"""
import json
import os
import random
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()
_SCREEN = None

PREY = ('sleeping', 'paralyzed', 'confused', 'stunned')
BRANDONS_LINE = "Yessss... eyes tired, yes? Rest, rest, Nickel will guard you."


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _data(name):
    with open(os.path.join(ROOT, 'data', name), encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def _quiet_turn():
    """senses.TURN is the game's word on this turn: each test starts with a
    hero who neither rested nor moved, and leaves it so."""
    import senses
    senses.begin_turn(moved=False, guilty=False, floor=0, rested=False)
    yield
    senses.begin_turn(moved=False, guilty=False, floor=0, rested=False)


def _game(name='__test_old_nickel__', seed=11):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name=name)
    g.state = STATE_PLAYER
    return g


# The arena: an open room carved into the floor, walls all round.
X0, Y0, W, H = 3, 3, 13, 9
X1, Y1 = X0 + W - 1, Y0 + H - 1
MID = (X0 + 6, Y0 + 4)


def _arena(g):
    from dungeon import FLOOR, WALL
    d = g.dungeon
    for y in range(Y0 - 1, Y1 + 2):
        for x in range(X0 - 1, X1 + 2):
            edge = x in (X0 - 1, X1 + 1) or y in (Y0 - 1, Y1 + 1)
            d.tiles[y][x] = WALL if edge else FLOOR
    box = {(x, y) for x in range(X0 - 1, X1 + 2) for y in range(Y0 - 1, Y1 + 2)}
    d.fixture_blocks = frozenset(t for t in d.fixture_blocks if t not in box)
    d.fixture_opaque = frozenset(t for t in d.fixture_opaque if t not in box)
    d.traps = {}
    g.monsters = []
    g.pets = []
    g.ground_items = [i for i in g.ground_items if (i.x, i.y) not in box]
    return (X0, Y0, X1, Y1)


def _nickel(g, at=MID):
    import emberpup_encounter as ep
    from monster import Monster
    m = Monster(ep.wearer_defn(), *at)
    m._wary_home = (X0, Y0, X1, Y1)
    m._hoard = tuple(at)
    g.monsters.append(m)
    return m


def _hero(g, x, y):
    g.player.x, g.player.y = x, y
    g._refresh_fov()


def _dist(m, p):
    return max(abs(m.x - p.x), abs(m.y - p.y))


def _turn(g, m):
    return m.take_turn(g.player, g.dungeon, g.monsters)


def _texts(g, n=40):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _setup(seed=11, at=MID):
    g = _game(f'__test_old_nickel_{seed}__', seed=seed)
    _arena(g)
    return g, _nickel(g, at)


# ===========================================================================
# His data: the AI's numbers and his lines
# ===========================================================================

def test_he_is_a_stalking_coward_in_the_data():
    m = _data('monsters.json')['old_nickel']
    assert m['ai_pattern'] == 'stalker_coward' and 'wary' not in m
    s = m['stalker']
    assert s['keep'] == 3 and s['dash_steps'] == 2
    assert set(s['prey_on']) == {'resting', 'sleeping', 'paralyzed', 'confused', 'stunned'}
    assert s['lose_after'] > 0 and s['hears_prey'] > 0
    for atk in m['attacks']:                       # a sleeper's blow, the mara's tool
        assert atk['bonus_vs'] == {'sleeping': 1.5, 'paralyzed': 1.5}
    lore = m['lore']
    assert 'killed more sleeping miners than the damp has' in lore
    assert 'never woke' in lore and 'counts the dead' in lore


def test_his_line_pools_load_and_every_moment_has_lines():
    import old_nickel
    for moment in ('sight', 'taunt', 'iron', 'cloak', 'recurring', 'dash_unseen',
                   'prey_strike', 'cornered', 'struck', 'strike', 'hurt', 'death'):
        assert old_nickel.lines(moment), moment
    groups = old_nickel.data()['dash_groups']
    for state in _data('monsters.json')['old_nickel']['stalker']['prey_on']:
        assert old_nickel.lines('dash', groups[state]), state
    assert len(old_nickel.taunt_pool(iron=True)) >= 15
    assert 1 <= len(old_nickel.lines('recurring')) <= 3
    assert BRANDONS_LINE in old_nickel.lines('recurring')


def _all_lines():
    import old_nickel
    out = []
    for v in old_nickel.data()['lines'].values():
        if isinstance(v, dict):
            for pool in v.values():
                out += pool
        else:
            out += v
    return out


def test_his_lines_are_his_own_words_plain_and_short():
    """Gollum's register as an homage: hissing, Nickel talking of himself,
    never Tolkien's own words. One line a message, his name capitalised,
    short enough to float over him."""
    lines = _all_lines()
    assert len(lines) == len(set(lines)), 'a line appears twice'
    low = ' '.join(lines).lower()
    for banned in ('precious', 'tricksy', 'hobbit', 'gollum', 'baggins', 'smeagol', 'sméagol'):
        assert banned not in low, banned
    assert 'yesss' in low and 'shiny' in low
    for t in lines:
        assert '\n' not in t and '"' not in t, t
        assert len(t) <= 80, (len(t), t)
        assert not re.search(r'\bnickel\b', t), t          # always "Nickel"
        assert not re.search(r'\b(blood|guts|gore)\b', t) or 'own blood' in t, t
    unseen = ' '.join(_data('old_nickel.json')['lines']['dash_unseen'])
    assert 'Nickel' not in unseen                        # the dark never names him


def test_the_tell_warns_of_him_first():
    import emberpup_encounter as ep
    import tells
    from monster import Monster
    m = Monster(ep.wearer_defn(), 0, 0)
    assert tells.abilities(m)[0] == 'stalker'
    sign, does, counter = tells.parts(m, 'stalker')
    assert 'out of reach' in sign and 'rest' in does and 'corner' in counter


# ===========================================================================
# Rule 1 and 5: he backs off, and strikes only cornered, beside the hero
# ===========================================================================

def test_he_holds_his_distance_from_a_hero_who_stands_still():
    g, m = _setup()
    for dx in (3, 4):
        m.x, m.y = MID
        _hero(g, MID[0] - dx, MID[1])
        hp = g.player.hp
        assert _turn(g, m) is False
        assert (m.x, m.y) == MID and g.player.hp == hp
        assert m._aware and m._tracking


def test_he_backs_away_from_a_hero_who_comes_at_him():
    g, m = _setup()
    _hero(g, MID[0] - 2, MID[1])
    assert _turn(g, m) is False
    assert _dist(m, g.player) == 3 and m._stalk_event == 'backs'
    # Beside him with room behind: he backs off, he does not strike.
    m.x, m.y = MID
    _hero(g, MID[0] - 1, MID[1])
    assert _turn(g, m) is False
    assert _dist(m, g.player) == 2 and not m._provoked


@pytest.mark.parametrize('corner,hero', [
    ((X0, Y0), (X0 + 1, Y0 + 1)),            # a corner
    ((X0, Y0), (X0 + 1, Y0)),
    ((X0 + 6, Y0), (X0 + 6, Y0 + 1)),        # his back to a wall
])
def test_cornered_beside_the_hero_he_strikes(corner, hero):
    g, m = _setup(at=corner)
    _hero(g, *hero)
    assert _turn(g, m) is True
    assert m._stalk_event == 'cornered' and m._provoked and (m.x, m.y) == corner


def test_cornered_two_tiles_off_he_waits_and_does_not_strike():
    g, m = _setup(at=(X0, Y0))
    _hero(g, X0 + 2, Y0 + 2)
    assert _turn(g, m) is False and (m.x, m.y) == (X0, Y0)


def test_he_never_attacks_from_two_tiles_or_more_unless_the_hero_rests():
    """Every hero tile two or more off, Nickel in the middle, by a wall and
    in a corner: never a blow."""
    for at in (MID, (X0, Y0), (X0 + 6, Y0), (X1, Y1)):
        g, m = _setup(at=at)
        for hx in range(X0, X1 + 1):
            for hy in range(Y0, Y1 + 1):
                if max(abs(hx - at[0]), abs(hy - at[1])) < 2:
                    continue
                m.x, m.y = at
                m._path = None
                _hero(g, hx, hy)
                assert _turn(g, m) is False, (at, hx, hy)
                assert max(abs(m.x - hx), abs(m.y - hy)) >= 2, (at, hx, hy)


def test_walking_at_him_across_his_room_never_draws_a_blow_until_he_is_cornered():
    """The game's own turns: the hero walks straight at him. He backs off
    toward his hoard until the wall stops him, and only then strikes."""
    g, m = _setup(at=(X0 + 6, Y0 + 4))
    g._sees_monster = lambda mo: True
    _hero(g, X0 + 2, Y0 + 4)
    hp = g.player.hp
    blows_before_cornered = 0
    for _ in range(30):
        step = (1 if m.x > g.player.x else -1 if m.x < g.player.x else 0,
                1 if m.y > g.player.y else -1 if m.y < g.player.y else 0)
        nx, ny = g.player.x + step[0], g.player.y + step[1]
        if (nx, ny) != (m.x, m.y) and g.dungeon.is_walkable(nx, ny):
            _hero(g, nx, ny)
        g._advance_turn()
        if m._stalk_event == 'cornered':
            break
        if g.player.hp < hp:
            blows_before_cornered += 1
    assert blows_before_cornered == 0
    assert m._stalk_event == 'cornered'


# ===========================================================================
# Rule 3: a hero at rest or helpless, he darts in at double speed
# ===========================================================================

def test_a_resting_hero_he_darts_in_on_at_double_speed_and_strikes():
    import senses
    g, m = _setup()
    _hero(g, MID[0] - 3, MID[1])
    senses.TURN.rested = True
    assert _turn(g, m) is True                     # three off: two steps, and the blow
    assert _dist(m, g.player) == 1 and m._stalk_event == 'prey' and m._stalk_prey == 'resting'
    # From farther, two steps in one turn.
    g, m = _setup(at=(X1, MID[1]))
    _hero(g, X1 - 7, MID[1])
    senses.TURN.rested = True
    assert _turn(g, m) is False
    assert max(abs(m.x - X1), abs(m.y - MID[1])) == 2      # two steps in one turn
    assert _dist(m, g.player) == 5 and m._stalk_event == 'dash'


def test_he_hears_a_sleeper_he_cannot_see_only_close_by():
    import senses
    g, m = _setup(at=(X1, MID[1]))
    g.player.status_effects['invisible'] = 50       # not seen
    _hero(g, X1 - 5, MID[1])
    senses.TURN.rested = True
    _turn(g, m)
    assert m._stalk_event == 'dash'                  # five off: he hears the breath
    g, m = _setup(at=(X1, MID[1]))
    g.player.status_effects['invisible'] = 50
    _hero(g, X1 - 10, MID[1])
    senses.TURN.rested = True
    _turn(g, m)
    assert m._stalk_event != 'dash' and (m.x, m.y) == (X1, MID[1])


@pytest.mark.parametrize('status', PREY)
def test_a_helpless_hero_he_darts_in_on_and_strikes(status):
    g, m = _setup()
    _hero(g, MID[0] - 3, MID[1])
    g.player.status_effects[status] = 5
    assert _turn(g, m) is True
    assert _dist(m, g.player) == 1 and m._stalk_prey == status
    # Still held: he keeps at him.
    assert _turn(g, m) is True
    # Once it ends, he backs off again (he has room).
    g.player.status_effects.pop(status)
    assert _turn(g, m) is False
    assert _dist(m, g.player) == 2 and m._stalk_event == 'backs'


def test_a_blow_on_a_sleeper_lands_harder():
    import emberpup_encounter as ep
    from monster import Monster
    from player import Player
    m = Monster(ep.wearer_defn(), 1, 0)
    atk = dict(m.attacks[0], damage='1d2+3')
    hits = {}
    for asleep in (False, True):
        p = Player()
        p.x, p.y = 0, 0
        p.hp = p.max_hp = 500
        if asleep:
            p.status_effects['sleeping'] = 5
        random.seed(4)
        dmg = 0
        for _ in range(60):
            got, _msg = m._resolve_blow(atk, p)
            dmg = max(dmg, got)
            p.status_effects['sleeping'] = 5 if asleep else 0
        hits[asleep] = dmg
    assert hits[True] > hits[False]


def test_the_wait_key_is_a_rest_he_darts_in_on():
    g, m = _setup()
    _hero(g, MID[0] - 3, MID[1])
    g._player_input(pygame.K_PERIOD)
    assert _dist(m, g.player) == 1 and m._provoked
    assert m._stalk_prey == 'resting'
    # A turn the hero does not rest, he backs off from him.
    g._advance_turn()
    assert _dist(m, g.player) == 2


# ===========================================================================
# Rule 4: he follows a hero who walks away; out of sight, home to his hoard
# ===========================================================================

def test_he_follows_a_hero_who_walks_away_about_three_tiles_off():
    g, m = _setup(at=(X1, MID[1]))
    _hero(g, X1 - 3, MID[1])
    dists = []
    for _ in range(7):
        _hero(g, g.player.x - 1, g.player.y)
        _turn(g, m)
        dists.append(_dist(m, g.player))
    assert all(3 <= d <= 4 for d in dists), dists
    assert m.x < X1 - 3                              # he came after him


def test_out_of_sight_long_enough_he_goes_back_to_his_hoard():
    g, m = _setup(at=(X1, MID[1]))
    _hero(g, X1 - 7, MID[1])
    for _ in range(3):
        _turn(g, m)                                  # he follows
    assert (m.x, m.y) != (X1, MID[1])
    g.player.status_effects['invisible'] = 99        # he loses him
    lose = int(m.stalker['lose_after'])
    for _ in range(lose + 20):
        _turn(g, m)
    assert (m.x, m.y) == (X1, MID[1]) and not m._tracking


def test_back_on_his_floor_the_hero_finds_him_by_his_hoard():
    g, m = _setup(at=(X1, MID[1]))
    m.x, m.y = X0 + 4, MID[1]
    m._stalk_seen_at = (X0, MID[1])
    _hero(g, X0, Y0)
    g._maybe_spawn_cloak_wearer(g.dungeon_level)
    assert (m.x, m.y) == (X1, MID[1]) and m._stalk_seen_at is None


# ===========================================================================
# Rule 2: his lines as the hero moves, paced, then the recurring set
# ===========================================================================

def test_the_pool_is_said_without_repeats_then_the_recurring_lines_come_round():
    import emberpup_encounter as ep
    import old_nickel
    from monster import Monster
    m = Monster(ep.wearer_defn(), 0, 0)
    rng = random.Random(5)
    pool = old_nickel.taunt_pool(iron=True)
    said = [old_nickel.taunt(m, rng, iron=True) for _ in pool]
    assert sorted(said) == sorted(pool)
    rec = old_nickel.lines('recurring')
    after = [old_nickel.taunt(m, rng, iron=True) for _ in range(2 * len(rec))]
    assert after == rec + rec


def test_no_iron_no_iron_lines():
    import emberpup_encounter as ep
    import old_nickel
    from monster import Monster
    m = Monster(ep.wearer_defn(), 0, 0)
    rng = random.Random(2)
    said = [old_nickel.taunt(m, rng, iron=False) for _ in old_nickel.taunt_pool(False)]
    assert not set(said) & set(old_nickel.lines('iron'))


def test_the_trigger_is_the_hero_coming_at_him_or_round_him():
    import old_nickel
    at = (10, 10)
    assert old_nickel.came_on((5, 10), (6, 10), at)          # toward
    assert old_nickel.came_on((6, 8), (7, 7), at)            # round him, same distance
    assert not old_nickel.came_on((6, 10), (5, 10), at)      # away: he follows
    assert not old_nickel.came_on((6, 10), (6, 10), at)      # no step
    assert not old_nickel.came_on(None, (6, 10), at)


def test_his_lines_are_paced_and_fall_back_to_the_recurring_set():
    """The game's side: one line on first sight (and the Journal's), then a
    line as the hero comes round him, never two within line_gap turns; the
    whole pool once, then the recurring set."""
    import old_nickel
    from chronicle import text_of
    g, m = _setup()
    g._sees_monster = lambda mo: True
    gap = int(old_nickel.data()['line_gap'])
    ring = [(MID[0] + dx, MID[1] + dy) for dx, dy in
            ((-3, 0), (-3, -1), (-3, -2), (-2, -3), (-1, -3), (0, -3), (1, -3), (2, -3),
             (3, -2), (3, -1), (3, 0), (3, 1), (3, 2), (2, 3), (1, 3), (0, 3), (-1, 3),
             (-2, 3), (-3, 2), (-3, 1))]
    spoken = []
    for t in range(400):
        g.turn_count = t
        _hero(g, *ring[t % len(ring)])
        before = len(g.msg_log.entries)
        g._old_nickel_turn(m, (m.x, m.y), False)
        for e in g.msg_log.entries[before:]:
            text = str(e[0])
            if text.startswith('Old Nickel: "'):
                spoken.append((t, text[len('Old Nickel: "'):-1]))
    assert spoken[0][1] in old_nickel.lines('sight')
    assert any(old_nickel.seen_chronicle() == text_of(c) for c in g._chronicle)
    turns = [t for t, _ in spoken[1:]]
    assert all(b - a >= gap for a, b in zip(turns, turns[1:])), turns
    lines = [s for _, s in spoken[1:]]
    pool = old_nickel.taunt_pool(old_nickel.carries_iron(g.player))
    assert sorted(lines[:len(pool)]) == sorted(pool)
    rec = old_nickel.lines('recurring')
    assert lines[len(pool):len(pool) + 2 * len(rec)] == rec + rec


def test_his_first_sight_line_waits_until_he_is_seen():
    import old_nickel
    g, m = _setup()
    g._sees_monster = lambda mo: False
    for t in range(3):
        g.turn_count = t
        g._old_nickel_turn(m, (m.x, m.y), False)
    assert not any(t.startswith('Old Nickel:') for t in _texts(g))
    g._sees_monster = lambda mo: True
    g._old_nickel_turn(m, (m.x, m.y), False)
    said = [t for t in _texts(g) if t.startswith('Old Nickel:')]
    assert len(said) == 1 and said[0][len('Old Nickel: "'):-1] in old_nickel.lines('sight')
    assert g._bk_speech and g._bk_speech['knight'] is m      # floating over him


def test_the_dark_never_names_him_as_he_darts_in():
    import old_nickel
    g, m = _setup()
    g._sees_monster = lambda mo: False
    m._stalk_event, m._stalk_prey = 'dash', 'resting'
    g._old_nickel_turn(m, (m.x, m.y), False)
    g._old_nickel_turn(m, (m.x, m.y), False)              # once a dash
    told = [t for t in _texts(g) if t in old_nickel.lines('dash_unseen')]
    assert len(told) == 1 and 'Nickel' not in told[0]


def test_his_dash_strike_cornered_struck_hurt_and_death_lines():
    import old_nickel
    g, m = _setup()
    g._sees_monster = lambda mo: True
    old_nickel.voice(m)['sight'] = True
    g.turn_count = 100
    m._stalk_event, m._stalk_prey = 'dash', 'paralyzed'
    g._old_nickel_turn(m, (m.x, m.y), False)
    assert any(t.endswith(old_nickel.lines('dash', 'held')[0] + '"') for t in _texts(g))
    m._stalk_event = 'prey'
    g._old_nickel_blow(m, 3)
    assert any(t[len('Old Nickel: "'):-1] in old_nickel.lines('prey_strike') for t in _texts(g, 3))
    g.turn_count = 110
    m._stalk_event = 'cornered'
    g._old_nickel_turn(m, (m.x, m.y), True)
    assert _texts(g, 1)[0][len('Old Nickel: "'):-1] in old_nickel.lines('cornered')
    g.turn_count = 120
    m._stalk_event = ''
    m._struck = True
    g._old_nickel_turn(m, (m.x, m.y), False)
    assert _texts(g, 1)[0][len('Old Nickel: "'):-1] in old_nickel.lines('struck')
    m.hp = int(m.max_hp * 0.4)
    g.turn_count = 130
    g._old_nickel_turn(m, (m.x, m.y), False)
    assert _texts(g, 1)[0][len('Old Nickel: "'):-1] in old_nickel.lines('hurt')
    g.turn_count = 131
    n = len(g.msg_log.entries)
    g._old_nickel_turn(m, (m.x, m.y), False)                 # once a share
    assert len(g.msg_log.entries) == n
    g.visible = {(m.x, m.y)}
    m.hp, m.alive = 0, False
    g._on_monster_killed(m)
    assert any(t[len('Old Nickel: "'):-1] in old_nickel.lines('death') for t in _texts(g, 12))


def test_a_nickel_saved_before_he_stalked_becomes_a_stalker():
    import emberpup_encounter as ep
    from monster import Monster
    g, _m = _setup()
    old = dict(ep.wearer_defn())
    old.pop('stalker')
    old['ai_pattern'] = 'aggressive'
    old['wary'] = {'radius': 5, 'keep': 3, 'warn': 'Mine.', 'provoked': {}}
    old['attacks'] = [{k: v for k, v in a.items() if k != 'bonus_vs'} for a in old['attacks']]
    m = Monster(old, MID[0], MID[1])
    m.wary = old['wary']                    # as a pickle from before kept it
    g.monsters = [m]
    g._old_nickel_refresh()
    assert m.ai_pattern == 'stalker_coward' and m.stalker and 'wary' not in m.__dict__
    assert all('bonus_vs' in a for a in m.attacks) and m._hoard_tile()


def test_observe_says_he_is_following():
    import senses
    g, m = _setup()
    _hero(g, MID[0] - 3, MID[1])
    _turn(g, m)
    assert senses.status_line(m) == 'He is following you, just out of reach.'
