"""Bug bash 3.5.1, hunter F: the Seeker's achievements and the traits, and
the round-3 rules of the kit and the pack.

Each test is a fault a player could meet, driven where it can be through the
game's own paths, and fails on 3.5.0.
"""
import json
import os
import random
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tests'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import seeker_codes  # noqa: E402
import seeker_profile  # noqa: E402

SRC = ROOT / 'src'
MONS = json.loads((ROOT / 'data' / 'monsters.json').read_text(encoding='utf-8'))
NAME = '__bugbash_351_f__'


def _unbind_listeners():
    """A Game with a Seeker binds module-level listeners: put them back."""
    import counters
    import deeds
    import monster
    import pet_system
    import topic_cards
    counters.ON_COUNTER = None
    deeds.ON_RECORD = None
    monster.DAMAGE_OBSERVER = None
    pet_system.ON_GROWTH = None
    topic_cards.ON_READ = None


@pytest.fixture
def seeker(tmp_path):
    saved = seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE
    seeker_codes._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}
    seeker_profile._DIR_OVERRIDE = str(tmp_path / 'seekers')
    seeker_profile.set_active('Robyn')
    yield 'Robyn'
    seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE = saved
    _unbind_listeners()


@pytest.fixture
def no_seeker(tmp_path):
    saved = seeker_profile._DIR_OVERRIDE
    seeker_profile._DIR_OVERRIDE = str(tmp_path / 'none')
    yield
    seeker_profile._DIR_OVERRIDE = saved
    _unbind_listeners()


def _game(name=NAME):
    from main import Game
    from game_states import STATE_PLAYER
    import items
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name=name)
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _answer_quiz(g, right=True, limit=20):
    """Answer the open quiz through its number keys until it closes."""
    from game_states import STATE_QUIZ
    from quiz_engine import QuizState
    qe = g.quiz_engine
    for _ in range(limit):
        if g.state != STATE_QUIZ:
            return
        if qe.state != QuizState.ASKING or qe.celebrating:
            if qe.state == QuizState.RESULT and getattr(qe, '_result_hold', False):
                qe._result_hold_until = 0.0
                g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN,
                                                  unicode='\r', mod=0, scancode=0))
            g.update(0.2)
            continue
        q = qe.current_question
        choices = q.get('choices', [])
        want = str(q['answer']).strip()
        order = qe.confused_order if (qe.confused_order and
                                      len(qe.confused_order) == len(choices)) else \
            list(range(len(choices)))
        shown = [choices[i] for i in order]
        pos = next(i for i, c in enumerate(shown) if (str(c).strip() == want) == right)
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=getattr(pygame, f'K_{pos + 1}'),
                                          unicode=str(pos + 1), mod=0, scancode=0))
        for _ in range(3):
            g.update(0.2)
    raise AssertionError('the quiz never closed')


# ---------------------------------------------------------------------------
# 1. What a fall earns never showed its card
# ---------------------------------------------------------------------------

def test_what_a_fall_earns_waits_for_the_title_screen(seeker):
    """main() hands the title screen the achievements won as the run ended
    (its comment: "the death and victory screens are no place for them, so
    the title shows their cards"). It read Game._seeker_pending, which every
    frame empties into the popup queue, and that queue opens nothing over the
    death screen: The First Fall and Forgot to Eat were never shown."""
    from game_states import STATE_DEAD
    g = _game()
    g._popup_queue_list().clear()
    g._seeker_pending.clear()
    g.defeat_reason = 'starved'
    g._seeker_run_end(False)              # what _on_game_over tells the Seeker
    g.state = STATE_DEAD
    for _ in range(4):
        g.update(0.5)                     # the death screen's frames
    assert g.state == STATE_DEAD          # nothing opened over it
    assert not g._seeker_pending          # (the frames moved them on)
    carried = g._seeker_unshown()
    assert 'fall_1' in carried and 'forgot_to_eat' in carried
    # ... and the title screen takes them as its unlock cards.
    from welcome_screen import WelcomeScreen
    w = WelcomeScreen(pygame.display.set_mode((1, 1)), 'test')
    w._seeker_won(carried)
    assert {'fall_1', 'forgot_to_eat'} <= {c['id'] for c in w._seeker_cards}


def test_main_carries_the_unshown_achievements_not_only_the_pending():
    text = (SRC / 'main.py').read_text(encoding='utf-8')
    block = text[text.index('Achievements won as the run ended wait for the title screen'):]
    block = block[:block.index('if game.state in (STATE_DEAD, STATE_VICTORY)')]
    assert '_seeker_unshown()' in block


def test_the_stone_home_shows_its_badge_after_the_ending_and_is_not_carried_twice(seeker):
    """Leaving with the Stone opens the ending's own popup at once; closing
    it opens the queued achievements, so none is left for the title."""
    from game_states import STATE_STORY_POPUP, STATE_VICTORY
    g = _game()
    g._popup_queue_list().clear()
    g._seeker_pending.clear()
    g._seeker_run_end(True)
    g._show_story_popup('exit_with_stone', STATE_VICTORY)
    g.update(0.5)
    assert g.state == STATE_STORY_POPUP and not g.popup_data.get('achievements')
    g._close_story_popup()
    assert g.state == STATE_STORY_POPUP
    assert 'stone_home' in [a['id'] for a in g.popup_data['achievements']]
    while g.state == STATE_STORY_POPUP:
        g._close_story_popup()
    assert g.state == STATE_VICTORY
    assert g._seeker_unshown() == []


def test_with_no_seeker_nothing_is_carried(no_seeker):
    g = _game()
    assert g._seeker is None
    assert g._seeker_unshown() == []


# ---------------------------------------------------------------------------
# 2. Proteus' Many Shapes never came for a ring
# ---------------------------------------------------------------------------

def test_a_ring_that_is_the_25th_kind_known_by_hand_earns_proteus(no_seeker):
    """The trait counts the kinds Known by Hand when gear goes on, but a ring
    or an amulet put on never told the traits: a ring that was the 25th kind
    left the trait locked (its bar full) until the next armour or weapon."""
    import known_by_hand as kbh
    from items import make_item_by_id
    g = _game()
    pl = g.player
    pl.known_by_hand = {f'old_kind_{i}' for i in range(24)}
    ring = make_item_by_id('accessory', 'ring_of_protection')
    assert ring is not None and not kbh.knows(pl, ring)
    pl.inventory.append(ring)
    g._equip_accessory(ring)
    _answer_quiz(g, right=True)
    assert any(r is ring for r in pl.accessory_slots)
    assert len(pl.known_by_hand) == 25
    assert g.quirk_system.is_unlocked('proteus')


# ---------------------------------------------------------------------------
# 3. Opening the practice screen counted as practising
# ---------------------------------------------------------------------------

def test_leaving_the_practice_screen_before_dancing_is_not_practising(seeker):
    """Terpsichore's Step and the Seeker's dance_off event ask whether a
    practice round was DANCED before the dance-off (achievements.py). The
    flag was set as the practice screen opened, so a hero who opened it and
    stepped back with Esc lost his cold win."""
    import test_mooble as TM
    from game_states import STATE_MOOBLE, STATE_MOOBLE_DANCE
    g = TM._game(name=NAME)
    TM._fed(g)
    now = TM._clock(g)
    TM._key(g, pygame.K_1)                       # Practise ...
    assert g.state == STATE_MOOBLE_DANCE and g._mdance['mode'] == 'practice'
    g._mooble_dance_key(pygame.K_ESCAPE)         # ... and straight back out
    assert g.state == STATE_MOOBLE
    TM._win_dance_off(g, now)
    assert g.player.quirk_progress.get('terpsichore_cold_wins') == 1
    _unbind_listeners()


def test_a_practice_round_danced_still_counts(seeker):
    import test_mooble as TM
    g = TM._game(name=NAME)
    TM._fed(g)
    now = TM._clock(g)
    TM._key(g, pygame.K_1)
    TM._dance_through(g, now)                    # a practice round, danced
    g._mooble_dance_key(pygame.K_ESCAPE)
    TM._win_dance_off(g, now)
    assert not g.player.quirk_progress.get('terpsichore_cold_wins')


# ---------------------------------------------------------------------------
# 4. A locked badge's bar read "1 of 1"
# ---------------------------------------------------------------------------

def test_a_badge_of_a_counter_and_an_event_is_never_full_while_locked(seeker):
    """In the Polished Shield, Medusa's gaze turned by a mirror is half of
    it; killing her is the other half. The Encyclopedia's line read
    "Progress: 1 of 1" on the locked badge once the gaze was turned."""
    import counters
    g = _game()
    s = g._seeker
    assert s.book.progress('polished_shield', s.profile, s.run) == (0, 2)
    medusa = __import__('monster').Monster(dict(MONS['medusa_gorgon'], id='medusa_gorgon'), 0, 0)
    counters.fired(counters.GAZE, medusa)
    assert not s.profile.is_unlocked('polished_shield')
    assert s.book.progress('polished_shield', s.profile, s.run) == (1, 2)
    # Polymath (counters only) still sums its parts.
    have, need = s.book.progress('polymath', s.profile, s.run)
    assert need == 10 * 100 + 2 * 25
