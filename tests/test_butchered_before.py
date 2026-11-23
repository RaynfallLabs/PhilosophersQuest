"""Butchered Before (src/butchered.py; Brandon, 2026-11-17): "once you have
IDENTIFIED AND SUCCESSFULLY HARVESTED a specific monster ONCE, you can
automatically harvest any others".

A right answer that gains a part remembers the kind (Player.butchered_kinds,
saved); a later harvest of the same kind, once the hero has studied the kind
himself (family_lore.studied: "Only if studied"), asks no question and yields
what a right answer yields. Unidentified, a different kind, or after a wrong
answer, the question is asked.

The pure rules are tested on food_system.harvest_corpse with a fake quiz;
the H key on a headless Game. Whether it feels right in play is Brandon's
play-test (CLAUDE.md play-test rule).
"""
import json
import os
import pickle
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import butchered  # noqa: E402
import food_system  # noqa: E402
from items import Corpse  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


class Quiz:
    """start_quiz answers at once, right or wrong, and counts the quizzes."""

    def __init__(self, right=True):
        self.right = right
        self.started = 0

    def start_quiz(self, **kw):
        self.started += 1
        right = self.right

        class R:
            success = right
        kw['callback'](R())


def _corpse(kind='giant_rat', x=0, y=0):
    return Corpse(MONS[kind]['name'], kind, x, y, harvest_tier=1,
                  monster_def={'tags': MONS[kind].get('tags', []),
                               'peak_floor': MONS[kind].get('peak_floor', 1)})


def _player():
    from player import Player
    return Player()


def _identify(p, kind):
    """A correct corpse study of the kind (studied: its page opens)."""
    import family_lore
    family_lore.record_study(p, kind)


def _harvest(p, corpse, quiz):
    out = {}
    free = food_system.harvest_corpse(p, corpse, quiz,
                                      lambda ings, msg: out.update(ings=ings, msg=msg))
    return free, out


# ---------------------------------------------------------------- the rule

def test_the_first_harvest_asks_its_question():
    p = _player()
    _identify(p, 'giant_rat')
    q = Quiz()
    free, out = _harvest(p, _corpse(), q)
    assert q.started == 1 and free is False
    assert [i.id for i in out['ings']] == ['giant_rat_prime']


def test_a_success_on_an_identified_kind_makes_the_next_one_free():
    p = _player()
    _identify(p, 'giant_rat')
    _harvest(p, _corpse(), Quiz())
    assert 'giant_rat' in p.butchered_kinds
    q = Quiz(right=False)                   # a quiz would fail: none is asked
    free, out = _harvest(p, _corpse(), q)
    assert free is True and q.started == 0
    assert [i.id for i in out['ings']] == ['giant_rat_prime']        # the normal part
    assert out['msg'].startswith('You harvest the')


def test_the_free_harvest_is_the_right_answers_harvest():
    """The same parts and line as a right answer, the family's extra portion
    included (family_edges.harvest_bonus)."""
    p = _player()
    _identify(p, 'giant_rat')
    asked = _harvest(p, _corpse(), Quiz())[1]
    free = _harvest(p, _corpse(), Quiz())[1]
    assert [i.id for i in free['ings']] == [i.id for i in asked['ings']]
    assert free['msg'] == asked['msg']
    assert all(getattr(i, 'source_monster', '') == 'giant_rat' for i in free['ings'])


def test_an_unidentified_kind_still_asks_after_a_success():
    p = _player()
    _harvest(p, _corpse(), Quiz())
    assert 'giant_rat' in p.butchered_kinds         # recorded regardless
    assert not butchered.identified(p, 'giant_rat')
    q = Quiz()
    free, _out = _harvest(p, _corpse(), q)
    assert free is False and q.started == 1


def test_a_success_counts_from_the_moment_the_kind_is_identified():
    p = _player()
    _harvest(p, _corpse(), Quiz())                  # before it is identified
    _identify(p, 'giant_rat')
    q = Quiz()
    free, out = _harvest(p, _corpse(), q)
    assert free is True and q.started == 0 and out['ings']


def test_a_page_opened_by_the_book_of_thoth_is_not_studied():
    """Brandon, 2026-11-17: "Only if studied". A page opened another way
    (the Book of Thoth, Omnisight, the family's tier) is not a study."""
    p = _player()
    p.lore_known_monster_ids = {'giant_rat'}
    _harvest(p, _corpse(), Quiz())
    assert not butchered.is_free(p, _corpse())
    _identify(p, 'giant_rat')
    assert butchered.is_free(p, _corpse())


def test_a_different_kind_still_asks():
    p = _player()
    _identify(p, 'giant_rat')
    _identify(p, 'goblin')
    _harvest(p, _corpse('giant_rat'), Quiz())
    q = Quiz()
    free, _out = _harvest(p, _corpse('goblin'), q)
    assert free is False and q.started == 1


def test_a_wrong_answer_records_nothing():
    p = _player()
    _identify(p, 'giant_rat')
    free, out = _harvest(p, _corpse(), Quiz(right=False))
    assert out['ings'] == [] and 'giant_rat' not in p.butchered_kinds
    q = Quiz()
    _harvest(p, _corpse(), q)
    assert q.started == 1


def test_the_message_names_the_creature():
    # (Without the hero: the words. With him, said once a kind: test_said_once.py.)
    c = _corpse('giant_rat')
    assert butchered.fires_line(c) == "You know how to butcher a Giant Rat. No question needed."
    assert butchered.fires_line(_corpse('orc_scout' if 'orc_scout' in MONS else 'goblin')).startswith(
        ("You know how to butcher an ", "You know how to butcher a "))


def test_the_card_line_shows_only_for_a_free_kind():
    p = _player()
    assert butchered.card_line(p, 'giant_rat') == ''
    _identify(p, 'giant_rat')
    butchered.learn(p, 'giant_rat')
    assert butchered.card_line(p, 'giant_rat') == butchered.CARD_LINE == "Butchered before: no question"


# ---------------------------------------------------------------- saves

def test_the_set_survives_a_save():
    p = _player()
    butchered.learn(p, 'giant_rat')
    q = pickle.loads(pickle.dumps(p))
    assert q.butchered_kinds == {'giant_rat'}


def test_an_old_save_loads_with_an_empty_set():
    from player import Player
    p = _player()
    butchered.learn(p, 'giant_rat')
    state = p.__getstate__()
    state.pop('butchered_kinds', None)
    q = Player.__new__(Player)
    q.__setstate__(state)
    assert q.butchered_kinds == set()


def test_a_whole_game_save_keeps_it(monkeypatch, tmp_path):
    """Through the real save system (save_game, load_game, load_state)."""
    import save_system
    from main import Game
    g = _game(monkeypatch, tmp_path)
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    butchered.learn(g.player, 'giant_rat')
    save_system.settle_unfinished_actions(g)
    assert save_system.save_game(g)
    g2 = Game(pygame.display.get_surface(), player_name='__test_butchered__')
    g2.load_state(save_system.load_game('__test_butchered__'))
    assert g2.player.butchered_kinds == {'giant_rat'}


# ---------------------------------------------------------------- the H key

def _game(monkeypatch, tmp_path):
    import bones
    import layout
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(11)
    screen = pygame.display.set_mode((1280, 720))
    layout.update(1280, 720)
    g = Game(screen, player_name='__test_butchered__')
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


@pytest.fixture
def game(monkeypatch, tmp_path):
    return _game(monkeypatch, tmp_path)


def _said(g, n=12):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def test_h_asks_then_harvests_free(game, monkeypatch):
    from game_states import STATE_PLAYER, STATE_QUIZ
    g = game
    p = g.player
    _identify(p, 'giant_rat')
    events = []
    real_event = g._seeker_event

    def spy(event, **fields):
        events.append((event, fields))
        return real_event(event, **fields)
    monkeypatch.setattr(g, '_seeker_event', spy)
    started = []
    states = []

    def start_quiz(**kw):
        started.append(kw['subject'])
        states.append(g.state)

        class R:
            success = True
        kw['callback'](R())
    monkeypatch.setattr(g.quiz_engine, 'start_quiz', start_quiz)

    g.ground_items.append(_corpse('giant_rat', p.x, p.y))
    g._harvest()
    assert started == ['animal'] and states == [STATE_QUIZ]
    assert 'giant_rat' in p.butchered_kinds
    assert ('harvest', {'monster': 'giant_rat', 'free': False}) in events

    before = sum(1 for i in p.inventory if getattr(i, 'id', '') == 'giant_rat_prime'
                 for _ in range(int(getattr(i, 'count', 1) or 1)))
    turn = g.turn_count
    events.clear()
    corpse = _corpse('giant_rat', p.x, p.y)
    g.ground_items.append(corpse)
    g._harvest()
    assert started == ['animal']                    # no second quiz
    assert g.state == STATE_PLAYER
    assert corpse not in g.ground_items             # the corpse used up
    assert g.turn_count == turn + 1                 # the turn spent
    after = sum(1 for i in p.inventory if getattr(i, 'id', '') == 'giant_rat_prime'
                for _ in range(int(getattr(i, 'count', 1) or 1)))
    assert after == before + 1
    said = _said(g)
    assert "You know how to butcher a Giant Rat. No question needed." in said
    assert any(s.startswith('You harvest the') for s in said)
    assert ('harvest', {'monster': 'giant_rat', 'free': True}) in events
    assert not [e for e, _f in events if e == 'quiz_answer']
    # The next free harvest of the kind says nothing of it (said_once.py,
    # 2026-11-22: "just noise. The player gets it"): only what was harvested.
    n = len(g.msg_log.entries)
    g.ground_items.append(_corpse('giant_rat', p.x, p.y))
    g._harvest()
    assert started == ['animal']
    new = [str(e[0]) for e in g.msg_log.entries[n:]]
    assert not any('know how to butcher' in s for s in new), new
    assert any(s.startswith('You harvest the') for s in new), new


def test_a_free_harvest_counts_as_a_harvest_but_no_answer():
    """The Seeker's harvests counter counts it; no answer counter can, as no
    quiz_answer is sent (and the harvest event's `free` field is known)."""
    import achievements
    assert 'free' in achievements.KNOWN_EVENTS['harvest']
    data = json.load(open(os.path.join(ROOT, 'data', 'achievements.json'), encoding='utf-8'))
    spec = data['counters']['harvests']
    assert spec['on'] == 'harvest' and 'where' not in spec
    for name, c in data['counters'].items():
        if c.get('on') == 'quiz_answer':
            continue
        assert c.get('on') != 'harvest' or name == 'harvests', name


def test_the_corpse_card_and_the_bestiary_say_it(game):
    g = game
    p = g.player
    corpse = _corpse('giant_rat', p.x, p.y)
    texts = [str(t[0]) for t in g._lore_corpse_lines(corpse, 0)[1]]
    assert butchered.CARD_LINE not in texts
    _identify(p, 'giant_rat')
    butchered.learn(p, 'giant_rat')
    texts = [str(t[0]) for t in g._lore_corpse_lines(corpse, 5)[1]]
    assert butchered.CARD_LINE in texts
    entry = {**MONS['giant_rat'], '_id': 'giant_rat', '_known': True}
    lines = [str(t[0]) for t in g._encyclopedia_article_lines('bestiary', entry)]
    assert butchered.CARD_LINE in lines


def test_a_person_is_still_searched(game):
    """People are searched, never harvested: no question, nothing recorded."""
    import kitchen
    g = game
    p = g.player
    person = next(k for k in sorted(kitchen.harvest_map().get('people', ())) if k in MONS)
    g.ground_items.append(_corpse(person, p.x, p.y))
    g._harvest()
    assert person not in p.butchered_kinds
    assert any(s.startswith('You search the') for s in _said(g))


# ---------------------------------------------------------------- help, hint, sim

def test_the_help_page_says_it():
    data = json.load(open(os.path.join(ROOT, 'data', 'ui', 'how_quizzes_work.json'), encoding='utf-8'))
    text = ' '.join(p for s in data['sections'] for p in s.get('paragraphs', ()))
    assert 'harvested with no question' in text


def test_a_tier_1_hint_points_at_cook_ding():
    hints = json.load(open(os.path.join(ROOT, 'data', 'hints.json'), encoding='utf-8'))
    assert any('Cook Ding' in h for h in hints['1'])


def test_the_simulator_harvests_a_known_kind_free(monkeypatch):
    import difficulty_sim as ds
    run = ds.Run(ds.FloorCache(1), 'mastery', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    _identify(run.p, 'giant_rat')
    butchered.learn(run.p, 'giant_rat')
    asked = []
    monkeypatch.setattr(run.quiz, 'one_question', lambda tier: asked.append(tier) or False)
    run.cooks_left, run.hunt_left, run.corpses_used = 2, 0, 0
    run.fs = {}                                     # the floor's stats (set per floor)
    run.corpses = ['giant_rat', 'goblin']
    n = len(run.pantry)
    run._harvest_all()
    assert asked == [ds.band_tier(run.floor)]       # only the goblin asked
    assert len(run.pantry) == n + 1
    assert run.fs.get('free_harvests') == 1
