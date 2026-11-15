"""Bug bash 3.5.1, hunter B: the quest pets, the dance-offs, riding, the race
and the soundtrack (all new in 3.5.0, none of it play-tested yet).

Each test pins one bug a player would have met, on a real headless Game
driven through the same keys and frames the game loop uses (the dance's
clock is a fake one, as in tests/test_mooble.py). The rhythm's feel and the
race's pace stay Brandon's play-test.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import mooble_encounter as mo  # noqa: E402
import test_mooble as TM  # noqa: E402

pygame.init()


# ---------------------------------------------------------------------------
# The Mooble's dance
# ---------------------------------------------------------------------------

def test_a_flopped_dance_of_the_dark_holds_them_for_1_turn_not_1_turns():
    """B-01. The Dance of the Dark's result card said "stand staring for 1
    turns" after a flop (the Flop band holds them 1 turn)."""
    bands = {b['name']: b for b in mo.special_spec()['bands']}
    flop = mo.special_result_line(bands['flop'])
    assert 'for 1 turn,' in flop and '1 turns' not in flop, flop
    assert 'for 3 turns,' in mo.special_result_line(bands['great'])
    # Danced through the menu with real keys (no step hit: a flop), the
    # result card draws that line.
    from pet_system import Pet
    g = TM._game('__test_351b_flop__')
    TM._hall(g)
    pet = Pet('mooble', 11, 10, level=20)
    g.pets = [pet]
    now = TM._clock(g)
    md = TM._special_through_the_menu(g, now, lambda resp: [])
    assert md['band']['name'] == 'flop'
    drawn = []
    real_wrap = g._ui_wrap_text

    def wrap(text, *a, **k):
        drawn.append(str(text))
        return real_wrap(text, *a, **k)
    g._ui_wrap_text = wrap
    g.screen = pygame.Surface((1600, 900))
    g._draw_mooble_dance()
    assert any('for 1 turn,' in t for t in drawn), drawn
    assert not any('1 turns' in t for t in drawn)


def test_the_count_in_starts_after_the_soundtrack_steps_aside(monkeypatch):
    """B-02. Holding the soundtrack waits for the sound effects still playing
    (music._effects_done, up to a second), and the dance's clock started
    before that wait: Enter to practise again during the result's fanfare
    lost the first beats of the count-in ("5, 6") to the wait."""
    import music
    g = TM._game('__test_351b_count_in__')
    TM._fed(g)
    now = TM._clock(g)

    def slow_hold():
        now[0] += 700                     # the result's fanfare still ringing
    monkeypatch.setattr(music, 'hold', slow_hold)
    monkeypatch.setattr(music, 'release', lambda: None)
    TM._key(g, pygame.K_1)
    before = now[0]
    g._mooble_dance_key(pygame.K_SPACE)
    md = g._mdance
    assert now[0] == before + 700
    assert md['t0'] == now[0]             # the clock starts once the music is quiet
    import game_mooble_dance as gmd
    played = []
    monkeypatch.setattr(gmd, '_play', lambda name: played.append(name))
    g._mooble_dance_tick()
    assert played == ['dance_bar']        # the count-in's first beat, "5", sounds


def test_opening_the_practice_card_and_backing_out_is_not_practising():
    """B-03. Choosing Practise and pressing Esc on its card, without dancing
    a step, counted as practising before the dance-off: that dance-off won
    no step toward Terpsichore's Step ("won with no practice round first")
    and the Seeker's dance_off event said practised."""
    g = TM._game('__test_351b_practised__')
    m = TM._fed(g)
    now = TM._clock(g)
    TM._key(g, pygame.K_1)                       # the practice card
    g._mooble_dance_key(pygame.K_ESCAPE)         # not now
    assert not g._mooble.get('practised')
    TM._win_dance_off(g, now)
    assert g.player.quirk_progress.get('terpsichore_cold_wins') == 1
    TM._key(g, pygame.K_RETURN)
    # A practice round really danced still counts.
    TM._wait(g)
    g._start_mooble_encounter(m)
    TM._key(g, pygame.K_1)
    TM._dance_through(g, now)
    assert g._mooble.get('practised') is True
    g._mooble_dance_key(pygame.K_d)
    TM._dance_through(g, now)
    g._mooble_dance_key(pygame.K_RETURN)
    assert mo.dances(m) == 2
    assert g.player.quirk_progress.get('terpsichore_cold_wins') == 1
