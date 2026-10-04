"""Regression tests for bugs found in the pre-v3.0 audit (2026-10-04).

Each test names the audit id from PRE_V3_AUDIT_REPORT.md.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

from quiz_engine import QuizEngine, QuizState  # noqa: E402


def _q(tier, text, answer='right'):
    return {'tier': tier, 'question': text, 'answer': answer,
            'choices': [answer, 'w1', 'w2', 'w3']}


def _engine(n=8):
    eng = QuizEngine()
    eng._cache['math'] = [_q(1, f'Q{i}') for i in range(n)]
    return eng


# ---- B2: a finished quiz must not finish twice ----------------------------

def test_b2_end_fires_callback_once():
    eng = _engine()
    calls = []
    eng.start_quiz('threshold', 'math', tier=1, callback=calls.append,
                   threshold=1)
    eng._end(success=False)
    eng._end(success=False)          # stray second end (e.g. ESC)
    assert len(calls) == 1
    assert eng.callback is None


# ---- B7: Tablet reroll flag is one-shot -----------------------------------

def test_b7_reroll_flag_applies_to_one_quiz_only():
    eng = _engine()
    eng._reroll_flag = True
    eng.start_quiz('chain', 'math', tier=1, callback=lambda r: None)
    assert eng.reroll_available is True
    eng._end(success=True)
    eng.start_quiz('threshold', 'math', tier=1, callback=lambda r: None,
                   threshold=1)
    assert eng.reroll_available is False, \
        "a combat reroll must not leak into the next quiz"


def test_b7_reroll_does_not_grant_a_free_chain():
    eng = _engine()
    eng._reroll_flag = True
    eng.start_quiz('chain', 'math', tier=1, callback=lambda r: None)
    eng.answer('w1')                  # wrong first answer
    eng.result_timer = 0
    eng._advance()
    assert eng.reroll_was_used is True
    assert eng.chain == 0


# ---- B19: scroll offset resets per question --------------------------------

def test_b19_scroll_offset_resets_on_next_question():
    eng = _engine()
    eng.start_quiz('chain', 'math', tier=1, callback=lambda r: None)
    eng._quiz_scroll_offset = 96
    eng._next_question()
    assert eng._quiz_scroll_offset == 0


# ---- B13: tick_all must not resurrect an effect removed mid-tick -----------

def test_b13_poison_damage_wakes_sleeper_for_good():
    from player import Player
    from status_effects import tick_all
    p = Player()
    p.hp = p.max_hp = 50
    p.status_effects.clear()
    p.status_effects['poisoned'] = 5
    p.status_effects['sleeping'] = 4
    tick_all(p)
    assert 'sleeping' not in p.status_effects


# ---- B15: no duplicate keys in the expire-message table --------------------

def test_b15_no_duplicate_expire_messages():
    src = (_ROOT / 'src' / 'status_effects.py').read_text(encoding='utf-8')
    start = src.index('_EXPIRE_MSGS')
    block = src[start:src.index('\n}\n', start)]
    keys = [line.split("'")[1] for line in block.splitlines()
            if line.strip().startswith("'")]
    dupes = {k for k in keys if keys.count(k) > 1}
    assert not dupes, dupes


# ---- B16: joiners inside hyphenated names stay lowercase -------------------

def test_b16_hyphenated_small_words():
    from naming import proper_name
    assert proper_name("will-o'-the-wisp") == "Will-o'-the-Wisp"
    assert proper_name('ox-hide shield') == 'Ox-Hide Shield'


# ---- W1: every rage bonus in the data can be rolled ------------------------

def test_w1_rage_damage_bonus_never_crashes():
    from monster import Monster
    defs = json.loads((_ROOT / 'data' / 'monsters.json').read_text(encoding='utf-8'))
    checked = 0
    for mid, d in defs.items():
        if not isinstance(d, dict) or not d.get('rage_damage_bonus'):
            continue
        d = dict(d)
        d.setdefault('id', mid)
        m = Monster(d, 0, 0)
        assert isinstance(m._roll_rage_bonus(), int), mid
        checked += 1
    assert checked >= 1


# ---- W12: merchant placement tests FLOOR, not a magic number ---------------

def test_w12_merchant_uses_floor_constant():
    src = (_ROOT / 'src' / 'mystery_system.py').read_text(encoding='utf-8')
    assert '== 3  # FLOOR' not in src
    from dungeon import FLOOR, STAIRS_DOWN
    assert FLOOR != STAIRS_DOWN


# ---- W5: Vidar's Sandal template is where the altar looks for it -----------

def test_w5_vidars_sandal_is_an_artifact():
    from items import load_items
    assert any(a.id == 'vidars_sandal' for a in load_items('artifact'))
    src = (_ROOT / 'src' / 'game_divine.py').read_text(encoding='utf-8')
    block = src[src.index('def _check_vidar_altar'):]
    block = block[:block.index('\n    def ', 10)]
    assert "load_items('artifact')" in block
    assert block.index('sandal_t =') < block.index('self.ground_items.remove(scrap)')


# ---- B3: a cursed wielded weapon must not eat the new weapon ---------------

def test_b3_equip_checks_current_weapon_before_removing_new_one():
    src = (_ROOT / 'src' / 'main.py').read_text(encoding='utf-8')
    block = src[src.index('    def _equip_item(self, item):'):]
    block = block[:block.index('elif isinstance(item, Shield)')]
    assert block.index('try_unequip_slot(_current)') < \
        block.index('self.player.remove_from_inventory(item)')
