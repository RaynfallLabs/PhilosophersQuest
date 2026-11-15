"""Bug bash 3.5.1, hunter C: the world and the newest changes (the floor's
clock, the bigger starting population and its small war-bands, mini-boss
tuning, hit lines and the strike preview, the round-3 rule fixes).

Each test failed before its fix."""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, HERE)

import war_bands  # noqa: E402


def _texts(g):
    return [t for t, _ in g.msg_log.entries]


# ------------------------------------------------------- the known roster

def test_one_of_a_role_is_named_in_the_singular():
    """Every gang of footpads has one archer, and a hero who knew the
    captain's kind heard "A leader, two fighters and one archers"."""
    text = war_bands.roster_text({'counts': {'guard': 2, 'shooter': 1, 'caster': 1, 'healer': 0}})
    assert text == 'A leader, two fighters, one archer and one caster'
    line = war_bands.arrival_line({'id': 'footpads', 'counts': {'guard': 1, 'shooter': 1}}, True)
    assert 'one fighter and one archer.' in line, line
    assert 'one archers' not in line and 'one fighters' not in line
    # More than one stays plural.
    assert war_bands.roster_text({'counts': {'guard': 3}}) == 'A leader and three fighters'


# ------------------------------------------------ floor 1's arrival lines

def _game_with(seed_from, want):
    from test_bug_bash_5_encounters import _game
    for seed in range(seed_from, seed_from + 60):
        g = _game(seed)
        if want(g):
            return g
    raise AssertionError('no floor 1 found for the test')


def test_floor_ones_war_band_is_heard_at_the_start():
    """Since 3.5.1 floor 1 holds a war-band on more than half its maps, but
    only _change_level said the band's line: floor 1's was never said at
    the start, and was first heard on coming back up from floor 2."""
    g = _game_with(1, lambda g: isinstance(getattr(g.dungeon, 'band', None), dict))
    band = g.dungeon.band
    assert band['said']
    line = war_bands.data()['bands'][band['id']]['line']
    known = war_bands.data()['bands'][band['id']]['known_line'].split('{roster}')[0]
    assert any(t == line or t.startswith(known) for t in _texts(g)), _texts(g)


def test_floor_ones_atmosphere_is_said_at_the_start_and_only_once():
    """A den's snoring or a vault's coins on floor 1 were never said at the
    start, and were said on the first return to floor 1."""
    g = _game_with(1, lambda g: bool(getattr(g.dungeon, 'atmosphere_messages', None)))
    atmo = list(g.dungeon.atmosphere_messages)
    texts = _texts(g)
    for a in atmo:
        assert texts.count(a) == 1, (a, texts)
    assert g.dungeon._atmosphere_said
    g._say_atmosphere()
    assert _texts(g).count(atmo[0]) == 1
