"""Old Nickel, the false friend who murders sleepers (Brandon, 2026-11-17).

"Old Nickel is not nearly mean enough... we need to make it clear he will
murder people in their sleep for their things, more lines of dialogue."
Then his rules for the kobold's AI (ai_pattern stalker_coward,
Monster._stalker_turn), the statuses he preys on, "more like Gollum", and:
"he initially approaches the player and tells him he'll protect him and
watch his back... urges the player to go to sleep or rest... stays within
two squares and can launch his sneak attack... then declares his evil
intent when the player finally rests... sneak attack should do significant
damage over a normal attack as well."

The FRIEND, from first sight: he comes up to the hero, keeps two tiles off
(a step back when the hero comes beside him), never strikes, and talks like
a helper, muttering about shinies under his breath.

He helps, when it is safe: one stab at a wounded monster busy with the
hero, then back to his two tiles, with a helper line.

The REVEAL, for good, sudden and vicious: the hero rests (the wait key), or
is asleep, paralysed, confused or stunned near him. He darts in still
smiling, and the moment he reaches him he shouts the act away and strikes:
the sneak attack, three times as hard, no cap ("We're not running a charity
here"). Or the hero strikes him first: "So the big one is clever."

REVEALED, his five rules:
1. He only attacks when the hero is right next to him (and he is cornered).
2. When the hero moves toward him or around him in view, a line: the pool
   without repeats, then a short recurring set; paced.
3. A hero at rest or helpless he darts in on at double speed and attacks.
4. When the hero moves away, he follows, about 3 tiles off.
5. When the hero moves toward him, he backs away until he cannot.

Floors 1-8, randomized: logic tests on a real headless Game, in an arena
carved into its floor.
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
SAY = 'Old Nickel: "'
ASIDE = 'Old Nickel, under his breath: "'


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


def _nickel(g, at=MID, revealed=False):
    import emberpup_encounter as ep
    from monster import Monster
    m = Monster(ep.wearer_defn(), *at)
    m._wary_home = (X0, Y0, X1, Y1)
    m._hoard = tuple(at)
    m._revealed = revealed
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


def _setup(seed=11, at=MID, revealed=True):
    """A game, the arena, and Nickel in it: the act already dropped unless
    `revealed` is False (the friend)."""
    g = _game(f'__test_old_nickel_{seed}__', seed=seed)
    _arena(g)
    return g, _nickel(g, at, revealed)


def _said(text, prefix=SAY):
    return text[len(prefix):-1] if text.startswith(prefix) else None


# ===========================================================================
# His data: the AI's numbers and his lines
# ===========================================================================

def test_he_is_a_false_friend_and_a_stalking_coward_in_the_data():
    m = _data('monsters.json')['old_nickel']
    assert m['ai_pattern'] == 'stalker_coward' and 'wary' not in m
    s = m['stalker']
    assert s['friend_keep'] == 2 and s['keep'] == 3 and s['dash_steps'] == 2
    assert s['sneak_mult'] == 3.0 and 'sneak_cap' not in s
    assert s['help_below'] == 0.5 and s['help_gap'] >= 2
    assert set(s['prey_on']) == {'resting', 'sleeping', 'paralyzed', 'confused', 'stunned'}
    assert s['lose_after'] > 0 and s['hears_prey'] > 0
    for atk in m['attacks']:                       # a sleeper's blow, the mara's tool
        assert atk['bonus_vs'] == {'sleeping': 1.5, 'paralyzed': 1.5}
    lore = m['lore']
    assert 'killed more sleeping miners than the damp has' in lore
    assert 'never woke' in lore and 'counts the dead' in lore
    assert 'offers to watch their backs' in lore
    assert 'smiles up at you' in m['sight_sign']


def test_his_line_pools_load_and_every_moment_has_lines():
    import old_nickel
    for moment in ('sight', 'offer', 'aside', 'aside_iron', 'friend_recurring',
                   'reveal', 'reveal_struck', 'helper',
                   'taunt', 'iron', 'cloak', 'recurring', 'dash_unseen',
                   'prey_strike', 'cornered', 'struck', 'strike', 'hurt', 'death'):
        assert old_nickel.lines(moment), moment
    groups = old_nickel.data()['dash_groups']
    for state in _data('monsters.json')['old_nickel']['stalker']['prey_on']:
        assert old_nickel.lines('dash', groups[state]), state
    assert 3 <= len(old_nickel.lines('reveal')) <= 5
    assert "So the big one is clever. Clever ones bleed too." in old_nickel.lines('reveal_struck')
    assert len(old_nickel.taunt_pool(iron=True, friendly=True)) >= 10
    assert len(old_nickel.taunt_pool(iron=True)) >= 15
    for friendly in (True, False):
        assert 1 <= len(old_nickel.recurring(friendly)) <= 3
    assert BRANDONS_LINE in old_nickel.recurring(friendly=True)


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
    short enough to float over him (the bubble wraps a long one)."""
    lines = _all_lines()
    assert len(lines) == len(set(lines)), 'a line appears twice'
    low = ' '.join(lines).lower()
    for banned in ('precious', 'tricksy', 'hobbit', 'gollum', 'baggins', 'smeagol', 'sméagol'):
        assert banned not in low, banned
    assert 'yesss' in low and 'shiny' in low
    for t in lines:
        assert '\n' not in t and '"' not in t, t
        assert len(t) <= 110, (len(t), t)
        assert not re.search(r'\bnickel\b', t), t          # always "Nickel"
        assert not re.search(r'\b(guts|gore)\b', t), t
    unseen = ' '.join(_data('old_nickel.json')['lines']['dash_unseen'])
    assert 'Nickel' not in unseen                        # the dark never names him


def test_the_friend_never_says_what_he_is_out_loud():
    """The murders show only after the reveal. The friend's own words are
    offers and urgings (a few double-edged); his asides are muttered."""
    import old_nickel
    spoken = (old_nickel.lines('sight') + old_nickel.lines('offer')
              + old_nickel.lines('friend_recurring'))
    for t in spoken:
        low = t.lower()
        for word in ('bones', 'kill', 'dead', 'blood', 'pile', 'bleed', 'nickel waits'):
            assert word not in low, (word, t)
    low = ' '.join(spoken).lower()
    assert 'watch your back' in low and 'guards you' in low and 'safe places to sleep' in low
    assert 'rest, rest, nickel keeps watch' in low
    assert any('Shiny' in t and 'good helper' in t for t in old_nickel.lines('aside'))
    reveal = ' '.join(old_nickel.lines('reveal')).lower()
    assert 'bones' in reveal and 'friend' in reveal


def test_the_tell_fits_both_faces():
    import emberpup_encounter as ep
    import tells
    from monster import Monster
    m = Monster(ep.wearer_defn(), 0, 0)
    assert tells.abilities(m)[0] == 'stalker'
    sign, does, counter = tells.parts(m, 'stalker')
    assert sign == 'Old Nickel follows you, smiling, offering to keep watch.'
    assert 'no friend' in does and 'rest' in does
    m._revealed = True
    sign, does, counter = tells.parts(m, 'stalker')
    assert 'out of reach' in sign and 'rest' in does and 'corner' in counter


# ===========================================================================
# The friend: he comes up to the hero, keeps two tiles off, never strikes
# ===========================================================================

def test_the_friend_comes_up_to_the_hero_and_stays_two_tiles_off():
    g, m = _setup(at=(X1, MID[1]), revealed=False)
    _hero(g, X1 - 7, MID[1])
    hp = g.player.hp
    for _ in range(8):
        assert _turn(g, m) is False
    assert _dist(m, g.player) == 2 and g.player.hp == hp and not m._revealed
    # The hero walks off: he keeps up, at two.
    for _ in range(4):
        _hero(g, g.player.x - 1, g.player.y)
        _turn(g, m)
        assert _dist(m, g.player) == 2


def test_the_friend_gives_a_little_ground_and_never_strikes():
    g, m = _setup(revealed=False)
    _hero(g, MID[0] - 1, MID[1])
    assert _turn(g, m) is False
    assert _dist(m, g.player) == 2 and m._stalk_event == 'backs'
    # Cornered with the hero beside him, the friend still does not strike.
    g, m = _setup(at=(X0, Y0), revealed=False)
    _hero(g, X0 + 1, Y0 + 1)
    for _ in range(5):
        assert _turn(g, m) is False
    assert not m._revealed and not m._provoked


def test_the_friend_never_attacks_an_awake_hero_anywhere():
    for at in (MID, (X0, Y0), (X0 + 6, Y0)):
        g, m = _setup(at=at, revealed=False)
        for hx in range(X0, X1 + 1, 2):
            for hy in range(Y0, Y1 + 1, 2):
                if (hx, hy) == at:
                    continue
                m.x, m.y = at
                m._path = None
                _hero(g, hx, hy)
                assert _turn(g, m) is False, (at, hx, hy)
        assert not m._revealed


# ===========================================================================
# The reveal: rest near him (or strike him) and the act drops, for good
# ===========================================================================

def test_a_rest_drops_the_act_and_brings_the_sneak_attack():
    import senses
    g, m = _setup(revealed=False)
    _hero(g, MID[0] - 2, MID[1])
    senses.TURN.rested = True
    assert _turn(g, m) is True                         # one step in, and the blow
    assert m._revealed and m._stalk_reveal == 'prey' and m._sneak_ready
    assert _dist(m, g.player) == 1 and m._stalk_prey == 'resting'


@pytest.mark.parametrize('status', PREY)
def test_each_helpless_state_drops_the_act(status):
    g, m = _setup(revealed=False)
    _hero(g, MID[0] - 2, MID[1])
    g.player.status_effects[status] = 5
    assert _turn(g, m) is True
    assert m._revealed and m._stalk_reveal == 'prey' and m._stalk_prey == status
    assert m._sneak_ready


def test_the_sneak_attack_hits_three_times_as_hard_and_never_misses():
    import emberpup_encounter as ep
    from monster import Monster
    from player import Player
    m = Monster(ep.wearer_defn(), 1, 0)
    lo, hi = 2, 4                                     # his spear, 1d3+1
    for seed in range(40):
        random.seed(seed)
        p = Player()
        p.x, p.y = 0, 0
        p.hp = p.max_hp = 500
        m._sneak_ready = True
        dmg, msg = m.attack(p)                         # the sneak comes with the spear
        assert 3 * lo <= dmg <= 3 * hi, (seed, dmg, msg)
        assert "you never saw it coming" in msg
        assert not m._sneak_ready
    # The next blow is an ordinary one.
    random.seed(1)
    p = Player()
    p.hp = p.max_hp = 500
    p.x, p.y = 0, 0
    got = [m.attack(p)[0] for _ in range(40)]
    assert max(got) <= hi


def test_the_sneak_attack_can_kill():
    """No cap (Brandon: "We're not running a charity here. Game is too easy
    as it is."): three times the blow, whatever the hero has left."""
    import emberpup_encounter as ep
    from monster import Monster
    from player import Player
    m = Monster(ep.wearer_defn(), 1, 0)
    assert m.sneak_blow(4) == 12 and m.sneak_blow(2) == 6
    assert 'sneak_cap' not in m.stalker
    deaths = 0
    for seed in range(40):
        random.seed(seed)
        p = Player()
        p.x, p.y = 0, 0
        p.max_hp = p.hp = 8
        m._sneak_ready = True
        dmg, _msg = m.attack(p)
        assert 6 <= dmg <= 12, (seed, dmg)
        deaths += p.hp <= 0
    assert deaths > 0                                  # a full-health hero of 8 can die


def test_the_betrayal_is_sudden_a_shout_and_the_blow_together():
    """The friend closes on a resting hero still smiling; the act drops only
    the moment he reaches him, with a shout, and the blow lands then."""
    import old_nickel
    import senses
    g, m = _setup(at=(X1, MID[1]), revealed=False)
    _hero(g, X1 - 5, MID[1])
    senses.TURN.rested = True
    assert _turn(g, m) is False                        # two steps in, not there yet
    assert not m._revealed and m._stalk_event == 'creep' and _dist(m, g.player) == 3
    assert _turn(g, m) is True                         # there: the act drops, he strikes
    assert m._revealed and m._stalk_reveal == 'prey' and m._sneak_ready
    for t in old_nickel.lines('reveal'):
        assert '!' in t and len(t) <= 80, t           # shouted, short
    assert any('bones' in t and 'old Nickel was a friend' in t for t in old_nickel.lines('reveal'))


def test_the_reveal_is_said_in_the_danger_colour_and_his_bubble():
    import old_nickel
    import senses
    g, m = _setup(revealed=False)
    g._sees_monster = lambda mo: True
    old_nickel.voice(m)['sight'] = True
    _hero(g, MID[0] - 2, MID[1])
    senses.TURN.rested = True
    _turn(g, m)
    g._old_nickel_turn(m, (m.x, m.y), True)
    text, kind = g.msg_log.entries[-1][0], g.msg_log.entries[-1][1]
    assert _said(str(text)) in old_nickel.lines('reveal') and kind == 'danger'
    assert g._bk_speech['knight'] is m and g._bk_speech['text'] in old_nickel.lines('reveal')


# ===========================================================================
# The friend helps, when it is safe: one stab at a wounded monster
# ===========================================================================

def _goblin(g, x, y, share=0.4, aware=True):
    from monster import Monster
    gob = Monster(dict(_data('monsters.json')['goblin'], id='goblin'), x, y)
    gob.max_hp = max(gob.max_hp, 20)
    gob.hp = max(1, int(gob.max_hp * share))
    gob._aware = aware
    g.monsters.append(gob)
    return gob


def test_the_friend_stabs_a_wounded_monster_busy_with_the_hero():
    import old_nickel
    g, m = _setup(at=(MID[0] + 2, MID[1]), revealed=False)
    g._sees_monster = lambda mo: True
    old_nickel.voice(m)['sight'] = True
    _hero(g, MID[0] - 1, MID[1])
    gob = _goblin(g, MID[0], MID[1])                  # beside the hero, at 40%
    hp, hero_hp = gob.hp, g.player.hp
    assert _turn(g, m) is False                        # never a blow on the hero
    assert gob.hp < hp and g.player.hp == hero_hp and m._stalk_event == 'help'
    assert not m._revealed
    g._old_nickel_turn(m, (m.x, m.y), False)
    log = _texts(g, 4)
    assert any('Old Nickel darts in and stabs the Goblin for' in t for t in log), log
    assert any(_said(t) in old_nickel.lines('helper') for t in log), log
    # Once, then back: no second stab within help_gap turns.
    hp = gob.hp
    for _ in range(int(m.stalker['help_gap']) - 1):
        _turn(g, m)
        assert gob.hp == hp
    assert _dist(m, g.player) == 2


def test_the_friend_never_stabs_a_healthy_monster():
    for share in (1.0, 0.75, 0.55):
        g, m = _setup(at=(MID[0] + 2, MID[1]), revealed=False)
        _hero(g, MID[0] - 1, MID[1])
        gob = _goblin(g, MID[0], MID[1], share=share)
        hp = gob.hp
        for _ in range(6):
            _turn(g, m)
        assert gob.hp == hp and m._stalk_event != 'help', share


def test_the_friend_never_stabs_one_free_to_hit_him_back():
    """Wounded, but beside him and not busy with the hero (nor held): no."""
    g, m = _setup(at=(MID[0] + 3, MID[1]), revealed=False)
    _hero(g, MID[0] - 2, MID[1])
    gob = _goblin(g, MID[0] + 4, MID[1])               # beside Nickel, two from no one
    hp = gob.hp
    for _ in range(6):
        _turn(g, m)
        assert gob.hp == hp
    # Held fast, it is safe again.
    gob.status_effects['paralyzed'] = 5
    m._help_wait = 0
    m.x, m.y = MID[0] + 3, MID[1]
    _turn(g, m)
    assert gob.hp < hp


def test_the_friend_never_stabs_a_monster_not_in_the_fight():
    g, m = _setup(at=(MID[0] + 2, MID[1]), revealed=False)
    _hero(g, MID[0] - 1, MID[1])
    gob = _goblin(g, MID[0], MID[1], aware=False)
    hp = gob.hp
    _turn(g, m)
    assert gob.hp == hp


def test_revealed_he_helps_no_one():
    g, m = _setup(at=(MID[0] + 3, MID[1]), revealed=True)
    _hero(g, MID[0] - 1, MID[1])
    gob = _goblin(g, MID[0], MID[1])
    hp = gob.hp
    for _ in range(6):
        _turn(g, m)
    assert gob.hp == hp


def test_a_helper_stab_that_kills_is_a_kill():
    g, m = _setup(at=(MID[0] + 2, MID[1]), revealed=False)
    g._sees_monster = lambda mo: True
    import old_nickel
    old_nickel.voice(m)['sight'] = True
    _hero(g, MID[0] - 1, MID[1])
    gob = _goblin(g, MID[0], MID[1])
    gob.hp = 1
    _turn(g, m)
    assert not gob.alive
    g._old_nickel_turn(m, (m.x, m.y), False)
    assert gob._kill_handled                        # the game counted the kill


def test_the_wait_key_drops_the_act_in_the_game():
    from chronicle import text_of
    import old_nickel
    g, m = _setup(revealed=False)
    g._sees_monster = lambda mo: True
    _hero(g, MID[0] - 2, MID[1])
    g._advance_turn()                                  # first sight: the friend
    assert not m._revealed
    hp = g.player.hp
    g._player_input(pygame.K_PERIOD)                   # the hero rests
    assert m._revealed and _dist(m, g.player) == 1
    log = _texts(g, 12)
    assert any(_said(t) in old_nickel.lines('reveal') for t in log), log
    assert any("you never saw it coming" in t for t in log), log
    assert g.player.hp < hp
    assert any(old_nickel.chronicle('prey') == text_of(c) for c in g._chronicle)


def test_struck_as_a_friend_the_act_drops_with_no_sneak_attack():
    import old_nickel
    g, m = _setup(revealed=False)
    g._sees_monster = lambda mo: True
    _hero(g, MID[0] - 2, MID[1])
    old_nickel.voice(m)['sight'] = True
    m.take_damage(3)
    _turn(g, m)
    assert m._revealed and m._stalk_reveal == 'struck' and not m._sneak_ready
    g._old_nickel_turn(m, (m.x, m.y), False)
    assert _said(_texts(g, 1)[0]) in old_nickel.lines('reveal_struck')
    # And no 'struck' line after it: the reveal was that.
    g.turn_count += 10
    n = len(g.msg_log.entries)
    g._old_nickel_turn(m, (m.x, m.y), False)
    assert not any(_said(str(e[0])) in old_nickel.lines('struck')
                   for e in g.msg_log.entries[n:])


def test_the_act_never_comes_back():
    import senses
    g, m = _setup(revealed=False)
    _hero(g, MID[0] - 2, MID[1])
    senses.TURN.rested = True
    _turn(g, m)
    assert m._revealed
    senses.TURN.rested = False
    for _ in range(30):                                # long out of sight
        g.player.status_effects['invisible'] = 99
        _turn(g, m)
    g._maybe_spawn_cloak_wearer(g.dungeon_level)       # the hero comes back
    g.player.status_effects.pop('invisible', None)
    _hero(g, MID[0] - 2, MID[1])
    m._stalk_reveal = ''
    _turn(g, m)
    assert m._revealed and m._stalk_reveal == ''
    assert _dist(m, g.player) >= 3                     # the stalker keeps three, not two


# ===========================================================================
# Revealed, rules 1 and 5: he backs off, and strikes only cornered
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


@pytest.mark.parametrize('revealed', (False, True))
def test_he_never_attacks_from_two_tiles_or_more_unless_the_hero_rests(revealed):
    """Every hero tile two or more off, Nickel in the middle, by a wall and
    in a corner, the friend and the stalker: never a blow."""
    for at in (MID, (X0, Y0), (X0 + 6, Y0), (X1, Y1)):
        g, m = _setup(at=at, revealed=revealed)
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
# Revealed, rule 3: a hero at rest or helpless, he darts in at double speed
# ===========================================================================

def test_a_resting_hero_he_darts_in_on_at_double_speed_and_strikes():
    import senses
    g, m = _setup()
    _hero(g, MID[0] - 3, MID[1])
    senses.TURN.rested = True
    assert _turn(g, m) is True                     # three off: two steps, and the blow
    assert _dist(m, g.player) == 1 and m._stalk_event == 'prey' and m._stalk_prey == 'resting'
    assert not m._sneak_ready                      # the sneak was the friend's, once
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


def test_a_later_blow_on_a_sleeper_lands_half_as_hard_again():
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
    assert hits[True] > hits[False] and hits[True] <= int(round(5 * 1.5))


# ===========================================================================
# Revealed, rule 4: he follows a hero who walks away; out of sight, home
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


@pytest.mark.parametrize('revealed', (False, True))
def test_out_of_sight_long_enough_he_goes_back_to_his_hoard(revealed):
    g, m = _setup(at=(X1, MID[1]), revealed=revealed)
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

@pytest.mark.parametrize('friendly', (True, False))
def test_the_pool_is_said_without_repeats_then_the_recurring_lines_come_round(friendly):
    import emberpup_encounter as ep
    import old_nickel
    from monster import Monster
    m = Monster(ep.wearer_defn(), 0, 0)
    rng = random.Random(5)
    pool = old_nickel.taunt_pool(iron=True, friendly=friendly)
    said = [old_nickel.taunt(m, rng, iron=True, friendly=friendly) for _ in pool]
    assert sorted(said) == sorted(pool)
    rec = old_nickel.recurring(friendly)
    after = [old_nickel.taunt(m, rng, iron=True, friendly=friendly) for _ in range(2 * len(rec))]
    assert after == rec + rec


def test_no_iron_no_iron_lines():
    import emberpup_encounter as ep
    import old_nickel
    from monster import Monster
    for friendly, iron_pool in ((True, 'aside_iron'), (False, 'iron')):
        m = Monster(ep.wearer_defn(), 0, 0)
        rng = random.Random(2)
        said = [old_nickel.taunt(m, rng, iron=False, friendly=friendly)
                for _ in old_nickel.taunt_pool(False, friendly)]
        assert not set(said) & set(old_nickel.lines(iron_pool))


def test_the_trigger_is_the_hero_coming_at_him_or_round_him():
    import old_nickel
    at = (10, 10)
    assert old_nickel.came_on((5, 10), (6, 10), at)          # toward
    assert old_nickel.came_on((6, 8), (7, 7), at)            # round him, same distance
    assert not old_nickel.came_on((6, 10), (5, 10), at)      # away: he follows
    assert not old_nickel.came_on((6, 10), (6, 10), at)      # no step
    assert not old_nickel.came_on(None, (6, 10), at)


_RING = [(dx, dy) for dx, dy in
         ((-3, 0), (-3, -1), (-3, -2), (-2, -3), (-1, -3), (0, -3), (1, -3), (2, -3),
          (3, -2), (3, -1), (3, 0), (3, 1), (3, 2), (2, 3), (1, 3), (0, 3), (-1, 3),
          (-2, 3), (-3, 2), (-3, 1))]


def _walk_round(g, m, turns=400):
    spoken = []
    for t in range(turns):
        g.turn_count = t
        dx, dy = _RING[t % len(_RING)]
        _hero(g, MID[0] + dx, MID[1] + dy)
        before = len(g.msg_log.entries)
        g._old_nickel_turn(m, (m.x, m.y), False)
        for e in g.msg_log.entries[before:]:
            text = str(e[0])
            for prefix in (SAY, ASIDE):
                if text.startswith(prefix):
                    spoken.append((t, _said(text, prefix), prefix == ASIDE))
    return spoken


def test_the_friends_lines_are_paced_muttered_and_fall_back_to_urging_rest():
    """One offer on first sight (and the Journal's line), then a line as the
    hero comes round him, never two within line_gap turns; his offers and
    asides once (the asides under his breath), then the rest urgings."""
    import old_nickel
    from chronicle import text_of
    g, m = _setup(revealed=False)
    g._sees_monster = lambda mo: True
    gap = int(old_nickel.data()['line_gap'])
    spoken = _walk_round(g, m)
    assert spoken[0][1] in old_nickel.lines('sight')
    assert any(old_nickel.chronicle('seen') == text_of(c) for c in g._chronicle)
    turns = [t for t, _, _ in spoken[1:]]
    assert all(b - a >= gap for a, b in zip(turns, turns[1:])), turns
    lines = [s for _, s, _ in spoken[1:]]
    pool = old_nickel.taunt_pool(old_nickel.carries_iron(g.player), friendly=True)
    assert sorted(lines[:len(pool)]) == sorted(pool)
    for _, s, aside in spoken[1:]:
        assert aside == old_nickel.is_aside(s), s
    rec = old_nickel.recurring(friendly=True)
    assert lines[len(pool):len(pool) + 2 * len(rec)] == rec + rec
    assert not m._revealed


def test_revealed_his_lines_are_the_killers_own():
    import old_nickel
    g, m = _setup()
    g._sees_monster = lambda mo: True
    old_nickel.voice(m)['sight'] = True
    spoken = _walk_round(g, m)
    lines = [s for _, s, _ in spoken]
    pool = old_nickel.taunt_pool(old_nickel.carries_iron(g.player))
    assert sorted(lines[:len(pool)]) == sorted(pool)
    rec = old_nickel.recurring()
    assert lines[len(pool):len(pool) + 2 * len(rec)] == rec + rec
    assert not any(aside for _, _, aside in spoken)


def test_his_first_sight_line_waits_until_he_is_seen():
    import old_nickel
    g, m = _setup(revealed=False)
    g._sees_monster = lambda mo: False
    for t in range(3):
        g.turn_count = t
        g._old_nickel_turn(m, (m.x, m.y), False)
    assert not any(t.startswith('Old Nickel') for t in _texts(g))
    g._sees_monster = lambda mo: True
    g._old_nickel_turn(m, (m.x, m.y), False)
    said = [t for t in _texts(g) if t.startswith('Old Nickel')]
    assert len(said) == 1 and _said(said[0]) in old_nickel.lines('sight')
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
    assert any(_said(t) in old_nickel.lines('prey_strike') for t in _texts(g, 3))
    g.turn_count = 110
    m._stalk_event = 'cornered'
    g._old_nickel_turn(m, (m.x, m.y), True)
    assert _said(_texts(g, 1)[0]) in old_nickel.lines('cornered')
    g.turn_count = 120
    m._stalk_event = ''
    m._struck = True
    g._old_nickel_turn(m, (m.x, m.y), False)
    assert _said(_texts(g, 1)[0]) in old_nickel.lines('struck')
    m.hp = int(m.max_hp * 0.4)
    g.turn_count = 130
    g._old_nickel_turn(m, (m.x, m.y), False)
    assert _said(_texts(g, 1)[0]) in old_nickel.lines('hurt')
    g.turn_count = 131
    n = len(g.msg_log.entries)
    g._old_nickel_turn(m, (m.x, m.y), False)                 # once a share
    assert len(g.msg_log.entries) == n
    g.visible = {(m.x, m.y)}
    m.hp, m.alive = 0, False
    g._on_monster_killed(m)
    assert any(_said(t) in old_nickel.lines('death') for t in _texts(g, 12))


def test_the_sneak_attack_has_no_line_after_it():
    g, m = _setup()
    g._sees_monster = lambda mo: True
    m._stalk_event, m._stalk_prey = 'prey', 'resting'
    m._last_sneak = True
    n = len(g.msg_log.entries)
    g._old_nickel_blow(m, 9)
    assert len(g.msg_log.entries) == n


def test_a_nickel_saved_before_he_stalked_becomes_a_stalker():
    import emberpup_encounter as ep
    from monster import Monster
    g, _m = _setup()
    old = dict(ep.wearer_defn())
    old.pop('stalker')
    old['ai_pattern'] = 'aggressive'
    old['wary'] = {'radius': 5, 'keep': 3, 'warn': 'Mine.', 'provoked': {}}
    old['attacks'] = [{k: v for k, v in a.items() if k != 'bonus_vs'} for a in old['attacks']]
    for provoked in (False, True):
        m = Monster(old, MID[0], MID[1])
        m.wary = old['wary']                    # as a pickle from before kept it
        m._provoked = provoked
        g.monsters = [m]
        g._old_nickel_refresh()
        assert m.ai_pattern == 'stalker_coward' and m.stalker and 'wary' not in m.__dict__
        assert all('bonus_vs' in a for a in m.attacks) and m._hoard_tile()
        assert m._revealed is provoked          # one already fighting has dropped the act


def test_observe_says_what_face_he_shows():
    import senses
    g, m = _setup(revealed=False)
    _hero(g, MID[0] - 3, MID[1])
    _turn(g, m)
    assert senses.status_line(m) == 'He follows you, smiling, offering to keep watch.'
    m._revealed = True
    assert senses.status_line(m) == 'He is following you, just out of reach.'
