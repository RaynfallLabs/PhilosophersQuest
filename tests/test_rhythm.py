"""The Mooble's dance, scored (src/rhythm.py): pure tests, no pygame.

The rhythm game is the one action that is not a quiz (RARE_PETS_PLAN
section 2). Its FEEL (whether the windows are fair at 80, 95 and 110 beats a
minute, whether the arrows light early enough) needs Brandon's hands; these
pin the arithmetic: the timeline, on time, early, late, the wrong arrow, no
key, strays, and the pass mark from data/mooble.json.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pytest  # noqa: E402

import rhythm  # noqa: E402

with open(os.path.join(ROOT, 'data', 'mooble.json'), encoding='utf-8') as _f:
    DANCE = json.load(_f)['dance']

FOUR = [[0, 'left'], [2, 'right'], [4, 'left'], [6, 'right']]


def _tl(steps=FOUR, bpm=80):
    return rhythm.timeline(steps, bpm, DANCE['lead_beats'], DANCE['phrase_beats'])


def _judge(presses, steps=FOUR, bpm=80, now=None):
    tl = _tl(steps, bpm)
    return rhythm.judge(tl['response'], presses, good_ms=DANCE['good_ms'],
                        perfect_ms=DANCE['perfect_ms'],
                        attach_ms=rhythm.attach_window(tl['beat_ms'], DANCE['good_ms']),
                        now_ms=now)


def test_the_timeline_counts_in_then_his_call_then_your_response():
    tl = _tl()
    assert tl['beat_ms'] == pytest.approx(750.0)                 # 80 beats a minute
    assert tl['call_start'] == pytest.approx(4 * 750)              # four beats of count-in
    assert tl['response_start'] == pytest.approx(12 * 750)         # then two bars of his
    assert [d for _t, d in tl['call']] == ['left', 'right', 'left', 'right']
    assert [t for t, _d in tl['call']] == pytest.approx([3000, 4500, 6000, 7500])
    assert [t for t, _d in tl['response']] == pytest.approx([9000, 10500, 12000, 13500])
    assert tl['response_end'] == pytest.approx(20 * 750)


def test_every_step_on_time_is_perfect_and_wins():
    tl = _tl()
    res = _judge(rhythm.on_time(tl['response']))
    assert (res['hits'], res['perfects'], res['misses'], res['strays']) == (4, 4, 0, 0)
    assert rhythm.passed(res, DANCE['pass_share'], DANCE['max_misses'])


def test_within_the_windows_perfect_and_good():
    tl = _tl()
    (t0, d0), (t1, d1), (t2, d2), (t3, d3) = tl['response']
    res = _judge([(t0 - 40, d0), (t1 + 49, d1), (t2 - 120, d2), (t3 + 150, d3)])
    assert [s['grade'] for s in res['steps']] == ['perfect', 'perfect', 'good', 'good']
    assert res['steps'][2]['offset'] == pytest.approx(-120)


def test_too_early_too_late_and_the_wrong_arrow_are_misses():
    tl = _tl()
    (t0, d0), (t1, d1), (t2, d2), (t3, _d3) = tl['response']
    res = _judge([(t0 - 200, d0), (t1 + 260, d1), (t2, d2), (t3, 'up')])
    grades = [(s['grade'], s['why']) for s in res['steps']]
    assert grades == [('miss', 'early'), ('miss', 'late'), ('perfect', None), ('miss', 'wrong')]
    assert res['misses'] == 3 and res['strays'] == 0
    assert not rhythm.passed(res, DANCE['pass_share'], DANCE['max_misses'])


def test_a_step_no_key_reached_is_a_miss_once_its_window_has_passed():
    tl = _tl()
    t0 = tl['response'][0][0]
    # While the window is open the step is still pending...
    assert _judge([], now=t0 + 100)['steps'][0]['grade'] == 'pending'
    # ...and a miss once it has gone.
    assert _judge([], now=t0 + 151)['steps'][0]['grade'] == 'miss'
    res = _judge([])
    assert res['missed_steps'] == 4 and res['hits'] == 0


def test_the_first_key_decides_a_step_and_a_second_is_a_stray():
    tl = _tl()
    t0, d0 = tl['response'][0]
    res = _judge([(t0, 'up'), (t0 + 10, d0)])
    assert res['steps'][0]['grade'] == 'miss' and res['steps'][0]['why'] == 'wrong'
    assert res['strays'] == 1


def test_mashing_every_arrow_never_wins():
    tl = _tl()
    presses = [(t, d) for t, _ in tl['response'] for d in rhythm.DIRS]
    res = _judge(presses)
    assert res['strays'] >= 3 * len(tl['response']) - 1
    assert not rhythm.passed(res, DANCE['pass_share'], DANCE['max_misses'])


def test_a_key_far_from_every_step_is_a_stray_and_counts_as_a_miss():
    tl = _tl()
    stray = (tl['response'][0][0] + 750, 'left')       # beat 1: no step there
    res = _judge(rhythm.on_time(tl['response']) + [stray])
    assert res['hits'] == 4 and res['strays'] == 1 and res['misses'] == 1
    assert rhythm.passed(res, DANCE['pass_share'], DANCE['max_misses'])


def test_the_pass_mark_is_three_quarters_and_two_misses_at_most():
    assert (DANCE['pass_share'], DANCE['max_misses']) == (0.75, 2)
    assert (DANCE['good_ms'], DANCE['perfect_ms']) == (150, 50)
    assert rhythm.hits_needed(4, 0.75) == 3
    assert rhythm.hits_needed(6, 0.75) == 5
    assert rhythm.hits_needed(8, 0.75) == 6
    eight = rhythm.timeline(DANCE['visits'][2]['steps'], DANCE['visits'][2]['bpm'])['response']
    on = rhythm.on_time(eight)
    # Six of eight with two missed: a win. Five of eight: a loss.
    res = rhythm.judge(eight, on[:6], good_ms=150, perfect_ms=50)
    assert res['hits'] == 6 and res['misses'] == 2 and rhythm.passed(res)
    res = rhythm.judge(eight, on[:5], good_ms=150, perfect_ms=50)
    assert not rhythm.passed(res)
    # Every step hit but three strays: too many misses.
    res = rhythm.judge(eight, on + [(on[0][0] + 270, 'up')] * 3, good_ms=150, perfect_ms=50)
    assert res['hits'] == 8 and not rhythm.passed(res)


def test_the_three_visits_grow_longer_and_quicker():
    visits = DANCE['visits']
    assert [len(v['steps']) for v in visits] == [4, 6, 8]
    assert [v['bpm'] for v in visits] == [80, 95, 110]
    for v in visits:
        ph = rhythm.phrase(v['steps'])
        assert all(0 <= b < DANCE['phrase_beats'] for b, _d in ph)
        assert len({b for b, _d in ph}) == len(ph)            # one step a beat at most
        # The Good windows of neighbouring steps never overlap.
        bm = rhythm.beat_ms(v['bpm'])
        gaps = [(b2 - b1) * bm for (b1, _), (b2, _) in zip(ph, ph[1:])]
        assert min(gaps) > 2 * DANCE['good_ms']


def test_a_slow_frame_never_moves_a_step():
    """The schedule is the schedule: judging the same keys after a stall
    (a later 'now') changes nothing already decided."""
    tl = _tl()
    keys = rhythm.on_time(tl['response'][:2])
    early = _judge(keys, now=tl['response'][1][0] + 1)
    late = _judge(keys, now=tl['response'][1][0] + 5000)
    assert [s['grade'] for s in early['steps'][:2]] == [s['grade'] for s in late['steps'][:2]] == \
        ['perfect', 'perfect']


def test_a_bad_step_in_the_data_is_refused():
    with pytest.raises(ValueError):
        rhythm.phrase([[0, 'sideways']])


def test_a_dance_with_no_call_follows_the_count_in_at_once():
    tl = rhythm.timeline(FOUR, 90, 4, 8, call=False)
    bm = rhythm.beat_ms(90)
    assert tl['call'] == [] and not tl['has_call']
    assert tl['response_start'] == pytest.approx(4 * bm)
    assert tl['response'][0][0] == pytest.approx(4 * bm)
    assert tl['beats'] == 12 and tl['response_end'] == pytest.approx(12 * bm)


def test_score_counts_perfects_extra_and_strays_against():
    res = {'total': 4, 'perfects': 2, 'goods': 2, 'strays': 0}
    assert rhythm.score(res) == pytest.approx(1.0)
    assert rhythm.score(res, perfect_worth=1.5) == pytest.approx(1.25)
    assert rhythm.score({**res, 'strays': 2}, stray_cost=0.5) == pytest.approx(0.75)
    assert rhythm.score({'total': 4, 'perfects': 0, 'goods': 0, 'strays': 9}, stray_cost=1) == 0.0


def test_band_is_the_highest_reached_and_never_below_the_lowest():
    bands = [{'min_score': 0.6, 'name': 'b'}, {'min_score': 0.0, 'name': 'a'}, {'min_score': 1.0, 'name': 'c'}]
    assert [rhythm.band(v, bands)['name'] for v in (0.0, 0.59, 0.6, 0.99, 1.0, 9)] == \
        ['a', 'a', 'b', 'b', 'c', 'c']
    assert rhythm.band(-1, bands)['name'] == 'a'
    assert rhythm.band(1, []) == {}
