"""Quirk and power text + the 2026-10-04 quirk pass.

Every quirk must have a locked-state hint and an unlocked-state
description; hints must not give the exact condition away; the tables in
quirk_system.py must stay in step with each other.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import re
import sys
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

import quirk_system as qs  # noqa: E402
from quirk_text import QUIRK_DESC, QUIRK_HINT  # noqa: E402


def test_every_quirk_has_every_piece_of_text():
    ids = set(qs._QUIRK_NAMES)
    for table, label in ((qs._QUIRK_PROGRESS, 'progress'),
                         (qs._QUIRK_TRIGGER, 'trigger'),
                         (qs._QUIRK_FLAVOR, 'flavor'),
                         (qs._QUIRK_EFFECTS, 'effect'),
                         (QUIRK_HINT, 'hint'), (QUIRK_DESC, 'description')):
        assert set(table) == ids, (label, sorted(ids ^ set(table)))
    assert len(ids) == 112


def test_hints_do_not_give_the_condition_away():
    """A hint may not contain a digit (the threshold) and may not repeat a
    long phrase of the exact trigger text."""
    for qid, hint in QUIRK_HINT.items():
        assert 25 <= len(hint) <= 170, (qid, len(hint))
        assert not re.search(r'\d', hint), f"{qid}: hint contains a number"
        trigger = qs._QUIRK_TRIGGER[qid].lower()
        words = hint.lower().split()
        for i in range(len(words) - 3):
            assert ' '.join(words[i:i + 4]) not in trigger, \
                f"{qid}: hint repeats the trigger text"


def test_descriptions_explain_the_reward():
    for qid, desc in QUIRK_DESC.items():
        assert len(desc) >= 60, (qid, desc)
        assert desc.rstrip().endswith('.'), qid
    for pid, pdef in qs._ACTIVE_POWER_DEFS.items():
        desc = QUIRK_DESC[pid]
        assert desc.startswith('Power, '), pid
        if pdef['uses']:
            want = '1 use ' if pdef['uses'] == 1 else f"{pdef['uses']} uses "
            assert want in desc, (pid, pdef['uses'])
        else:
            assert f"every {pdef['cooldown']} turns" in desc, pid
        assert qs._QUIRK_EFFECTS[pid].startswith('Power, '), pid


def test_trigger_text_states_the_real_threshold():
    """The 'how it unlocked' line must quote the number the code uses."""
    for qid, (_key, threshold, _is_set) in qs._QUIRK_PROGRESS.items():
        if threshold <= 0:
            continue
        shown = qs._QUIRK_TRIGGER[qid].replace(',', '')
        assert str(threshold) in shown, (qid, threshold, qs._QUIRK_TRIGGER[qid])


def _system():
    from player import Player
    pl = Player()
    msgs = []
    game = SimpleNamespace(player=pl, turn_count=0, dungeon_level=1,
                           monsters=[], correct_answers=0,
                           add_message=lambda *a, **k: msgs.append(a))
    return qs.QuirkSystem(game), pl


def test_zeus_bolt_counts_each_time_haste_begins():
    system, pl = _system()
    for _ in range(15):
        pl.status_effects['hasted'] = 3
        system.on_turn()
        pl.status_effects.pop('hasted')
        system.on_turn()
    assert system.is_unlocked('zeus_bolt')


def test_gorgon_ward_counts_surviving_petrification():
    system, pl = _system()
    for _ in range(3):
        pl.status_effects['petrifying'] = 4
        system.on_turn()
        pl.status_effects.pop('petrifying')
        system.on_turn()
    assert system.is_unlocked('gorgon_ward')


def test_pythagoras_needs_three_four_five_in_order():
    system, _pl = _system()
    args = dict(correct_count=0, wrong_count=0, success=True,
                while_blinded=False, while_confused=False,
                while_hallucinating=False)
    for score in (3, 5, 4):
        system.on_quiz_complete('chain', 'math', score, **args)
    assert not system.is_unlocked('pythagoras')
    for score in (3, 4, 5):
        system.on_quiz_complete('chain', 'math', score, **args)
    assert system.is_unlocked('pythagoras')


def test_daedalus_streak_resets_on_a_failed_lock():
    system, _pl = _system()
    for _ in range(11):
        system.on_lockpick_success()
    system.on_lockpick_fail('chest', 3)
    system.on_lockpick_success()
    assert not system.is_unlocked('daedalus')
    for _ in range(11):
        system.on_lockpick_success()
    assert system.is_unlocked('daedalus')


def test_hercules_counts_distinct_named_foes_only():
    system, pl = _system()
    named = sorted(qs._named_foe_kinds())
    assert len(named) >= 12
    kill = dict(chain_score=3, ranged=False, unarmed=False,
                hp_pct_before=1.0, is_feared=False)
    for _ in range(20):
        system.on_kill(named[0], **kill)       # the same boss, repeatedly
    system.on_kill('giant_rat', **kill)
    assert not system.is_unlocked('hercules')
    base = pl.STR
    for kind in named[:12]:
        system.on_kill(kind, **kill)
    assert system.is_unlocked('hercules') and pl.STR >= base + 2


def test_subject_mastery_quirks_unlock():
    system, pl = _system()
    need = {s: n for s, _q, _n, n, _st in qs._SUBJECT_MASTERIES}
    kw = dict(correct=True, chain=1, while_blinded=False, while_confused=False,
              while_hallucinating=False, while_feared=False,
              wrong_this_session=0, score_this_session=1)
    for subject, qid, _name, n, _stat in qs._SUBJECT_MASTERIES:
        for _ in range(need[subject] - 1):
            system.on_quiz_answer(subject, **kw)
        assert not system.is_unlocked(qid), qid
        system.on_quiz_answer(subject, **kw)
        assert system.is_unlocked(qid), qid


def test_wanderlust_and_musashi_rewards_are_read():
    main_src = (_ROOT / 'src' / 'main.py').read_text(encoding='utf-8')
    assert "quirk_progress.get('wanderlust_active')" in main_src
    combat_src = (_ROOT / 'src' / 'combat.py').read_text(encoding='utf-8')
    block = combat_src[combat_src.index('# Musashi quirk'):][:600]
    assert 'mult *= 2.0' in block and 'multipliers is not None' not in block
