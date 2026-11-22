"""Confusion on the quiz: the words swim, then settle (Brandon, 2026-11-19:
"maybe scramble letters and numbers? ... make it almost impossible to hit, so
we need to be careful it's not an auto kill").

* The pure functions (the confusion section of src/quiz_engine.py): inside
  words of four letters or more the inner letters are shuffled (first and
  last kept), numbers' digits
  are shuffled (sign, point and commas in place), punctuation, maths signs and
  short words stay; deterministic per seed; settled one word at a time and
  true at the settle time; the numbers in data/confusion.json.
* The engine stamps each question (QuizEngine._stamp_scramble) and counts
  its seconds; the quiz screen draws the scrambled text while confused, true
  text otherwise and in the result, and shows the Confused chip.
* No double penalty: confusion's x0.55 clock cut is gone.
* Not an auto-kill: a confusion is not refreshed while it runs, and the hero
  is Clear-Headed for three turns after it ends or is cured.
* The simulator models the settle wait instead of the cut.

Display only, so a play-test is the real proof (floors 1-10: allips,
boggarts, goblin shamans); these pin the rules.
"""
import os
import pickle
import random
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PQ_NO_BONES', '1')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import quiz_engine as qs  # noqa: E402  (its confusion section)
import status_effects as se  # noqa: E402

pygame.init()

_WORDS = re.compile(r'[0-9]+(?:[.,][0-9]+)*|[^\W\d_]+')


def _tokens(text):
    return [m.group(0) for m in _WORDS.finditer(text)]


# ---------------------------------------------------------------------------
# The pure module
# ---------------------------------------------------------------------------

_TEXT = ("Which philosopher said the unexamined life is not worth living? "
         "Socrates, in 399 BC -- or was it -3.75 + 1,024 = 12, or x = 7?")


def test_words_keep_first_and_last_and_shuffle_only_the_inside():
    out = qs.scramble(_TEXT, seed=11, share=0.0)
    assert len(out) == len(_TEXT)
    for true, drawn in zip(_tokens(_TEXT), _tokens(out)):
        if true[0].isdigit():
            continue
        assert drawn[0] == true[0] and drawn[-1] == true[-1]
        assert sorted(drawn) == sorted(true)              # a permutation
        if len(true) < 4:
            assert drawn == true                          # short words stay
    # Every word that can swim does, at share 0.
    swimming = [t for t in _tokens(_TEXT) if qs.swims(t)]
    moved = [d for t, d in zip(_tokens(_TEXT), _tokens(out)) if qs.swims(t) and d != t]
    assert len(moved) == len(swimming) > 5


def test_numbers_shuffle_their_digits_and_keep_sign_point_and_commas():
    for true, seed in (("-3.75", 1), ("1,024", 2), ("399", 3), ("12", 4), ("7", 5), ("11", 6)):
        out = qs.scramble(true, seed=seed, share=0.0)
        assert len(out) == len(true)
        for i, ch in enumerate(true):
            if not ch.isdigit():
                assert out[i] == ch                       # '-', '.', ',' stay put
        assert sorted(c for c in out if c.isdigit()) == sorted(c for c in true if c.isdigit())
        digits = [c for c in true if c.isdigit()]
        if len(digits) >= 2 and len(set(digits)) > 1:
            assert out != true
        else:
            assert out == true                            # one digit, or all one digit


def test_punctuation_spaces_and_maths_signs_never_move():
    text = "What is (12 + 34) x 56 / 78 - 90 = ? Explain, briefly: why!"
    for seed in range(20):
        out = qs.scramble(text, seed=seed, share=0.0)
        assert len(out) == len(text)
        for a, b in zip(text, out):
            if not a.isalnum():
                assert a == b


def test_the_same_seed_draws_the_same_scramble_and_another_seed_another():
    a = qs.scramble(_TEXT, seed=99, share=0.3)
    assert qs.scramble(_TEXT, seed=99, share=0.3) == a
    others = {qs.scramble(_TEXT, seed=s, share=0.0) for s in range(10)}
    assert len(others) > 1


def test_words_settle_one_at_a_time_and_read_true_at_the_settle_time():
    blocks = [[_TEXT[:60], _TEXT[60:]], ['The Nile'], ['Mississippi'], ['Danube'], ['Amazon']]
    seed = 5
    n = sum(1 for b in blocks for line in b for t in _tokens(line) if qs.swims(t))
    prev_swimming = None
    for k in range(0, 41):
        share = k / 40
        runs = qs.scramble_runs(blocks, seed, share)
        count =sum(1 for b in runs for line in b for t, s in line if s for _ in _tokens(t))
        assert count == n - qs.settled_count(n, share)
        if prev_swimming is not None:
            assert count <= prev_swimming                 # settling only goes one way
        prev_swimming = count
    assert qs.scramble_lines(blocks, seed, 1.0) == blocks  # true at the settle time
    assert qs.scramble_lines(blocks, seed, 1.5) == blocks
    # A settled word stays settled: what is true at 0.5 is true at 0.75.
    half = qs.scramble_lines(blocks, seed, 0.5)
    later = qs.scramble_lines(blocks, seed, 0.75)
    for b_true, b_half, b_late in zip(blocks, half, later):
        for t, h, lt in zip(b_true, b_half, b_late):
            for tw, hw, lw in zip(_tokens(t), _tokens(h), _tokens(lt)):
                if hw == tw:
                    assert lw == tw


def test_runs_join_to_lines_of_the_true_length():
    blocks = [['Double 36?'], ['67'], ['144'], ['36'], ['72']]
    runs = qs.scramble_runs(blocks, 3, 0.0)
    for b_true, b_runs in zip(blocks, runs):
        for line, line_runs in zip(b_true, b_runs):
            assert len(''.join(t for t, _s in line_runs)) == len(line)
            assert any(s for _t, s in line_runs)          # every block here can swim


def test_settle_times_come_from_the_data():
    import json
    with open(os.path.join(ROOT, 'data', 'confusion.json'), encoding='utf-8') as f:
        rules = json.load(f)['scramble']
    assert rules['timed_seconds'] == 1.6 and rules['untimed_seconds'] == 2.5
    assert qs.settle_seconds(True, 10) == 1.6
    assert qs.settle_seconds(False, 10) == 2.5
    assert qs.settle_seconds(True, 14) == pytest.approx(1.4)
    assert qs.settle_seconds(False, 20) == pytest.approx(2.0)
    assert qs.settle_seconds(True, 40) == 0.8            # never under the floor
    assert qs.settle_seconds(False, 6) == 2.5            # nothing added under 10


def test_no_settle_for_a_hero_who_is_not_confused():
    from player import Player
    p = Player()
    assert qs.settle_for(p, True) == 0.0
    assert qs.settle_for(None, True) == 0.0
    p.status_effects['confused'] = 4
    p.WIS = 12
    assert qs.settle_for(p, True) == pytest.approx(1.5)
    assert qs.settle_for(p, False) == pytest.approx(2.4)


# ---------------------------------------------------------------------------
# The engine
# ---------------------------------------------------------------------------

_SUM = {'tier': 1, 'question': 'Double 36?', 'answer': '72',
        'choices': ['67', '144', '36', '72'], 'topic': 'doubling'}
_SUM2 = {'tier': 1, 'question': 'What is 48 + 25?', 'answer': '73',
         'choices': ['73', '63', '83', '72'], 'topic': 'addition'}
_GEO = {'tier': 1, 'question': 'Which great river flows north through Egypt to the sea?',
        'answer': 'The Nile', 'choices': ['The Nile', 'Mississippi', 'Danube', 'Amazon'],
        'topic': 'rivers'}
_GEO2 = {'tier': 1, 'question': 'Which mountain range runs along the spine of Italy?',
         'answer': 'Apennines', 'choices': ['Apennines', 'Pyrenees', 'Carpathians', 'Urals'],
         'topic': 'mountains'}


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    import quiz_engine
    import save_system
    import bones
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setattr(save_system, '_save_path',
                        lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    yield


def _stage(qe, subject, questions, tier=1):
    qe._decks[(subject, tier)] = [dict(q) for q in questions]
    qe._deck_idx[(subject, tier)] = 0
    qe._last_q[(subject, tier)] = None


def _engine(settle=1.6):
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe.scramble_hook = lambda timed: settle
    return qe


@pytest.mark.parametrize('mode,timed', [
    ('threshold', False), ('chain', True), ('escalator_threshold', False),
    ('escalator_chain', False)])
def test_every_quiz_mode_stamps_its_questions(mode, timed):
    from quiz_engine import QuizState
    qe = _engine(1.6 if timed else 2.5)
    for t in range(1, 6):
        _stage(qe, 'math', [_SUM, _SUM2], tier=t)
    qe.start_quiz(mode=mode, subject='math', tier=1, callback=lambda r: None,
                  threshold=2, total_qs=3, timed=timed)
    assert qe.state == QuizState.ASKING
    assert qe.confused_quiz()
    assert qe.scramble_settle == (1.6 if timed else 2.5)
    seed, share = qe.scramble_view()
    assert share == 0.0
    first_seed = seed
    qe.update(0.5)
    assert qe.scramble_view()[1] == pytest.approx(0.5 / qe.scramble_settle)
    # The next question scrambles afresh: a new seed, its seconds from 0.
    assert qe.answer(qe.current_question['answer'])
    assert qe.scramble_view() is None                    # the result is drawn true
    for _ in range(30):
        if qe.state != QuizState.RESULT:
            break
        qe.update(0.1)
    assert qe.state == QuizState.ASKING
    assert qe.q_elapsed == pytest.approx(0.0)
    assert qe.scramble_view()[0] != first_seed
    # Settled at its settle time; the Confused line stays up.
    qe.update(qe.scramble_settle)
    assert qe.scramble_view() is None
    assert qe.confused_quiz()


def test_no_hook_or_no_confusion_means_true_text():
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    _stage(qe, 'math', [_SUM])
    qe.start_quiz(mode='chain', subject='math', tier=1, callback=lambda r: None, timed=True)
    assert qe.scramble_view() is None and not qe.confused_quiz()
    qe2 = _engine(0.0)
    _stage(qe2, 'math', [_SUM])
    qe2.start_quiz(mode='chain', subject='math', tier=1, callback=lambda r: None, timed=True)
    assert qe2.scramble_view() is None and not qe2.confused_quiz()


def test_the_card_stopping_the_clock_stops_the_settling_too():
    qe = _engine(1.6)
    _stage(qe, 'math', [_SUM])
    qe.start_quiz(mode='chain', subject='math', tier=1, callback=lambda r: None, timed=True)
    qe.update(0.4)
    assert qe.pause_timer()
    qe.update(5.0)
    assert qe.q_elapsed == pytest.approx(0.4)
    qe.resume_timer()
    qe.update(0.4)
    assert qe.q_elapsed == pytest.approx(0.8)


def test_a_question_put_up_outside_the_deck_is_never_scrambled():
    """The Necronomicon sets its own questions on the engine: never stamped."""
    qe = _engine(2.5)
    _stage(qe, 'grammar', [_GEO])
    qe.start_quiz(mode='threshold', subject='grammar', tier=1, callback=lambda r: None,
                  threshold=1, total_qs=1)
    assert qe.confused_quiz()
    qe.current_question = {'question': 'Klaatu Barada...?', 'answer': 'Nikto',
                           'choices': ['Necktie', 'Nickel', 'Nikon']}
    assert not qe.confused_quiz() and qe.scramble_view() is None


# ---------------------------------------------------------------------------
# The real game: the hook, the screen, the chip
# ---------------------------------------------------------------------------

def _game(name='__test_quiz_scramble__'):
    import layout
    from main import Game
    size = (1600, 900)
    screen = pygame.display.set_mode(size)
    layout.update(*size)
    random.seed(7)
    g = Game(screen, player_name=name)
    g.on_resize(*size)
    g._resize_grace = 0
    return g


def _spy_cards(monkeypatch):
    import fantasy_ui
    cards = []
    real = fantasy_ui.draw_choice_button

    def spy(surface, rect, **kw):
        text = kw.get('text')
        cards.append((' '.join(text) if isinstance(text, list) else str(text), kw.get('swim')))
        return real(surface, rect, **kw)

    monkeypatch.setattr(fantasy_ui, 'draw_choice_button', spy)
    return cards


def _spy_question(monkeypatch):
    import fantasy_ui
    drawn = []
    real = fantasy_ui.blit_runs

    def spy(surf, font, runs, pos, color, swim):
        drawn.append(''.join(t for t, _s in runs))
        return real(surf, font, runs, pos, color, swim)

    monkeypatch.setattr(fantasy_ui, 'blit_runs', spy)
    return drawn


def _start_geo(g, questions=(_GEO,)):
    from game_states import STATE_QUIZ
    qe = g.quiz_engine
    _stage(qe, 'geography', list(questions))
    qe.start_quiz(mode='threshold', subject='geography', tier=1, callback=lambda r: None,
                  threshold=1, total_qs=1)
    g.state = STATE_QUIZ
    g.quiz_title = 'PUT ON IRON HELM  --  GEOGRAPHY'
    return qe


def test_the_game_asks_the_hero_whether_he_is_confused():
    g = _game()
    g.player.status_effects.pop('confused', None)
    qe = _start_geo(g)
    assert qe.scramble_settle == 0.0
    g.player.status_effects['confused'] = 4
    qe = _start_geo(g)
    assert qe.scramble_settle == qs.settle_seconds(False, g.player.effective_wis())


def test_the_quiz_screen_draws_the_words_swimming_then_true(monkeypatch):
    g = _game()
    g.player.status_effects['confused'] = 4
    qe = _start_geo(g)
    cards = _spy_cards(monkeypatch)
    lines = _spy_question(monkeypatch)
    g._draw_quiz()
    assert len(cards) == 4
    true_cards = set(_GEO['choices'])
    drawn = [c[0] for c in cards]
    assert all(c[1] is not None for c in cards)           # each card drawn as runs
    assert any(d not in true_cards for d in drawn)         # some answer swims
    for d in drawn:                                        # ...as its own letters
        assert any(sorted(d) == sorted(t) for t in true_cards)
    # The question's lines come first (the cards' own lines follow them).
    q_lines = lines[:len(g._quiz_layout(qe)['q_lines'])]
    assert q_lines and ' '.join(q_lines) != _GEO['question']
    assert sorted(''.join(q_lines).replace(' ', '')) == sorted(_GEO['question'].replace(' ', ''))
    assert [len(x) for x in q_lines] == [len(x) for x in g._quiz_layout(qe)['q_lines']]
    # Settled: the true text, drawn plainly.
    cards.clear()
    lines.clear()
    qe.update(qe.scramble_settle + 0.01)
    g._draw_quiz()
    assert sorted(c[0] for c in cards) == sorted(true_cards)
    assert all(c[1] is None for c in cards)
    assert lines == []
    # And the answer is checked against the bank, never the screen.
    assert qe.answer('The Nile')


def test_not_confused_the_screen_draws_true_text(monkeypatch):
    g = _game()
    g.player.status_effects.pop('confused', None)
    _start_geo(g)
    cards = _spy_cards(monkeypatch)
    lines = _spy_question(monkeypatch)
    chips = []
    monkeypatch.setattr(type(g), '_draw_quiz_confused_chip',
                        lambda self, *a, **k: chips.append(a) or pygame.Rect(0, 0, 1, 1))
    g._draw_quiz()
    assert sorted(c[0] for c in cards) == sorted(_GEO['choices'])
    assert all(c[1] is None for c in cards)
    assert lines == [] and chips == []


def test_the_confused_chip_shows_on_the_quiz_and_stays_after_the_words_settle(monkeypatch):
    g = _game()
    g.player.status_effects['confused'] = 4
    qe = _start_geo(g)
    chips = []
    real = type(g)._draw_quiz_confused_chip

    def spy(self, *a, **k):
        rect = real(self, *a, **k)
        chips.append(rect)
        return rect

    monkeypatch.setattr(type(g), '_draw_quiz_confused_chip', spy)
    g._draw_quiz()
    assert len(chips) == 1
    L = g._quiz_layout(qe)
    chip = chips[0]
    # In the timer row, inside the panel, clear of the question.
    assert L['panel_rect'].contains(chip)
    assert chip.bottom <= L['question_rect'].y
    assert chip.y >= L['header_rect'].bottom
    qe.update(qe.scramble_settle + 0.1)
    g._draw_quiz()
    assert len(chips) == 2
    f, label, _w = g._quiz_confused_label(2000, timed=False)
    assert label == qs.confused_chip_text() == 'Confused: the words swim, then settle'
    f, label, _w = g._quiz_confused_label(200, timed=True)
    assert label == 'Confused'                          # a narrow timed row


def test_a_timed_chain_scrambles_its_sums(monkeypatch):
    from game_states import STATE_QUIZ
    g = _game()
    g.player.status_effects['confused'] = 4
    qe = g.quiz_engine
    _stage(qe, 'math', [_SUM])
    qe.start_quiz(mode='chain', subject='math', tier=1, callback=lambda r: None, timed=True,
                  base_seconds=g.player.get_quiz_timer('math'),
                  timer_modifier=g.player.get_quiz_timer_modifier())
    g.state = STATE_QUIZ
    g.quiz_title = 'MELEE ATTACK  --  MATH'
    assert qe.scramble_settle == qs.settle_seconds(True, g.player.effective_wis())
    cards = _spy_cards(monkeypatch)
    lines = _spy_question(monkeypatch)
    g._draw_quiz()
    # Every word and number here can swim, and at first every one does: "36"
    # has one other order, and the card "36" reads "63" as well.
    assert lines[0] != 'Double 36?' and '63' in lines[0]      # the sum, drawn first
    assert lines[0][0] == 'D' and lines[0].endswith('e 63?')
    assert sorted(c[0] for c in cards) != sorted(_SUM['choices'])
    assert '63' in {c[0] for c in cards}


# ---------------------------------------------------------------------------
# No double penalty
# ---------------------------------------------------------------------------

def test_confusion_no_longer_cuts_the_clock():
    import inspect
    from player import Player
    p = Player()
    plain = (p.get_quiz_timer_modifier(), p.combat_clock())
    p.status_effects['confused'] = 5
    assert (p.get_quiz_timer_modifier(), p.combat_clock()) == plain
    assert p.get_quiz_timer_modifier() == 1.0
    src = inspect.getsource(Player.get_quiz_timer_modifier)
    assert '0.55' not in src and "has_effect('confused')" not in src
    # Since 2026-11-22 no debuff cuts it: theirs show on the quiz (quiz_sight.py).
    for e in ('blinded', 'stunned', 'hallucinating'):
        p.status_effects[e] = 5
    assert (p.get_quiz_timer_modifier(), p.combat_clock()) == plain


# ---------------------------------------------------------------------------
# Not an auto-kill: Clear-Headed after every bout
# ---------------------------------------------------------------------------

def _p():
    from player import Player
    return Player()


def test_a_running_confusion_is_not_refreshed():
    p = _p()
    assert se.apply_effect(p, 'confused', 3) is True
    se.tick_all(p)
    assert p.status_effects['confused'] == 2
    assert se.apply_effect(p, 'confused', 6) is False
    assert p.status_effects['confused'] == 2


def test_clear_headed_for_three_turns_after_confusion_ends():
    p = _p()
    se.apply_effect(p, 'confused', 1)
    msgs = se.tick_all(p)
    assert p.status_effects.get('confused', 0) == 0
    assert p.status_effects.get('confuse_immune') == se.CLEAR_HEADED_TURNS == 3
    assert any('Clear-Headed' in m for m, _t in msgs)
    assert se.EFFECT_INFO['confuse_immune'][0] == 'Clear-Headed'
    assert se.apply_effect(p, 'confused', 6) is False
    for _ in range(se.CLEAR_HEADED_TURNS):
        assert se.apply_effect(p, 'confused', 6) is False
        se.tick_all(p)
    assert p.status_effects.get('confuse_immune', 0) == 0
    assert se.apply_effect(p, 'confused', 6) is True


def test_a_cure_is_followed_by_clear_headed_too():
    # Cured, then a monster tries again before the turn ends.
    p = _p()
    se.apply_effect(p, 'confused', 5)
    p.status_effects.pop('confused')                    # a potion, a prayer, a trader
    assert se.apply_effect(p, 'confused', 5) is False
    assert p.status_effects.get('confuse_immune') == 3
    # Cured, and the turn ends first.
    p = _p()
    se.apply_effect(p, 'confused', 5)
    del p.status_effects['confused']
    se.tick_all(p)
    assert p.status_effects.get('confuse_immune') == 3
    assert se.apply_effect(p, 'confused', 5) is False


def test_the_save_still_halves_and_the_old_safeguards_still_stand():
    p = _p()
    applied, _msg = se.apply_debuff_with_save(p, 'confused', 6, dc=-100)   # always saves
    assert applied and p.status_effects['confused'] == 3
    p = _p()
    se.apply_effect(p, 'confused', 20)
    assert p.status_effects['confused'] == se.CONTROL_CAP['confused'] == 6
    for guard in ('magic_resist', 'confuse_immune'):
        p = _p()
        p.status_effects[guard] = 10
        assert se.apply_effect(p, 'confused', 4) is False


def test_a_confuser_every_turn_never_keeps_the_hero_scrambled_back_to_back():
    p = _p()
    streak = longest = 0
    clear_runs = []
    clear = 0
    for _ in range(120):
        se.apply_debuff_with_save(p, 'confused', 6, dc=100)   # never saves
        if p.status_effects.get('confused', 0) > 0:
            streak += 1
            longest = max(longest, streak)
            if clear:
                clear_runs.append(clear)
            clear = 0
        else:
            streak = 0
            clear += 1
        se.tick_all(p)
    assert longest <= se.CONTROL_CAP['confused']
    assert clear_runs and min(clear_runs) >= se.CLEAR_HEADED_TURNS


def test_a_trophys_permanent_clear_head_is_left_alone():
    p = _p()
    p.status_effects['confuse_immune'] = -1
    assert se.apply_effect(p, 'confused', 4) is False
    se.tick_all(p)
    assert p.status_effects['confuse_immune'] == -1


def test_an_old_pickled_hero_mid_confusion_still_recovers():
    p = _p()
    p.status_effects['confused'] = 2                    # written before the bouts were kept
    p.__dict__.pop('_soft_bouts', None)
    p2 = pickle.loads(pickle.dumps(p))
    assert qs.settle_for(p2, True) > 0
    se.tick_all(p2)
    del p2.status_effects['confused']                   # cured on the next turn
    se.tick_all(p2)
    assert p2.status_effects.get('confuse_immune', 0) > 0


def test_a_save_mid_confusion_loads_confused_and_scrambles(tmp_path, monkeypatch):
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    name = '__test_quiz_scramble_save__'
    g = _game(name)
    g.state = STATE_PLAYER
    se.apply_effect(g.player, 'confused', 4)
    g.player.__dict__.pop('_soft_bouts', None)          # as an older save has it
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    save_system.settle_unfinished_actions(g)
    assert save_system.save_game(g)
    state = save_system.load_game(name)
    g2 = Game(pygame.display.get_surface(), player_name=name)
    g2.load_state(state)
    g2.state = STATE_PLAYER
    assert g2.player.status_effects.get('confused') == 4
    qe = _start_geo(g2)
    assert qe.scramble_view() is not None
    for _ in range(4):
        g2.player.tick_effects()
    assert g2.player.status_effects.get('confused', 0) == 0
    assert g2.player.status_effects.get('confuse_immune') == 3


# ---------------------------------------------------------------------------
# Study Mode and the cards never scramble
# ---------------------------------------------------------------------------

def test_study_mode_and_the_topic_cards_never_scramble():
    for name in ('study_mode.py', 'topic_cards.py'):
        with open(os.path.join(ROOT, 'src', name), encoding='utf-8') as f:
            src = f.read()
        assert 'scramble' not in src, name
    # The context card reads the bank's card text, never the screen form.
    with open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8') as f:
        render = f.read()
    modal = render[render.index('def _draw_quiz_context_modal'):]
    modal = modal[:modal.index('\n    def ', 10)]
    assert 'scramble' not in modal


# ---------------------------------------------------------------------------
# The simulator
# ---------------------------------------------------------------------------

def test_the_simulator_waits_for_the_words_to_settle():
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
    import difficulty_sim as ds
    qm = ds.QuizModel(1.0, 1.0, 'greedy', ds.parse_knobs(''))
    # A settle as long as the clock leaves no time to answer.
    chain, asked, _right = qm.sample_chain(1, 5.0, None, settle=5.0)
    assert chain == 0 and asked == 1
    # start_quiz reads the hero's confusion, as the game's engine does.
    seen = []
    real = qm.sample_chain

    def spy(*a, **k):
        seen.append(k.get('settle'))
        return real(*a, **k)

    qm.sample_chain = spy
    p = _p()
    qm.player = p
    qm.start_quiz(tier=1, callback=lambda r: None, base_seconds=10)
    p.status_effects['confused'] = 4
    qm.start_quiz(tier=1, callback=lambda r: None, base_seconds=10)
    assert seen == [0.0, qs.settle_seconds(True, p.effective_wis())]
    # And the Run wires its hero in, so a fork keeps its own.
    run = ds.Run(ds.FloorCache(1), 'mastery', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    assert run.quiz.player is run.p
    twin = run.fork()
    assert twin.quiz.player is twin.p
