"""Philosophy tier mastery (Brandon 2026-10-24).

Answer every philosophy question of a tier correctly in ONE run and the
tier's trait unlocks: +1 WIS at once (outside the trait allowance), and every
item whose identify question is of that tier is identified the moment it
reaches the pack. The traits list shows the progress as "N of M".
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import philosophy_mastery as pm  # noqa: E402
import quirk_system as qs  # noqa: E402
from quiz_engine import QuizEngine  # noqa: E402


# -- data -----------------------------------------------------------------------------

def test_five_tiers_each_with_every_piece_of_text():
    data = json.loads((ROOT / 'data' / 'philosophy_mastery.json').read_text(encoding='utf-8'))
    assert data['subject'] == 'philosophy' and data['wis'] == 1
    tiers = pm.tiers()
    assert [t['tier'] for t in tiers] == [1, 2, 3, 4, 5]
    assert pm.trait_ids() == [f'philosophy_tier_{n}' for n in range(1, 6)]
    for t in tiers:
        for key in ('name', 'trigger', 'effect', 'hint', 'description', 'flavor', 'journal'):
            assert t.get(key), (t['id'], key)
        assert f"tier-{t['tier']}" in t['trigger']
    # They head the traits list, and the text module has them too.
    assert qs._QUIRK_ORDER[:5] == pm.trait_ids()
    from quirk_text import QUIRK_DESC
    assert all(QUIRK_DESC[q].startswith('Wisdom +1.') for q in pm.trait_ids())


# -- the quiz engine's count ---------------------------------------------------------

def test_tier_progress_counts_right_answers_still_in_the_bank():
    e = QuizEngine()
    stems = sorted(e._tier_stems('philosophy', 1))
    assert e.tier_progress('philosophy', 1) == (0, len(stems))
    e._retired[('philosophy', 1)] = set(stems[:10]) | {'a stem a bank update removed'}
    assert e.tier_progress('philosophy', 1) == (10, len(stems))


def test_a_stale_retired_stem_cannot_master_a_tier():
    e = QuizEngine()
    stems = sorted(e._tier_stems('philosophy', 1))
    e._retired[('philosophy', 1)] = set(stems[:-2]) | {'gone one', 'gone two'}
    e.subject, e.tier = 'philosophy', 1
    e.current_question = {'question': stems[-2]}
    e._record_correct_for_mastery()
    assert not e.is_mastered('philosophy', 1)          # one real question is still unanswered
    e.current_question = {'question': stems[-1]}
    e._record_correct_for_mastery()
    assert e.is_mastered('philosophy', 1)


# -- in the game ----------------------------------------------------------------------

def _game(monkeypatch, tmp_path):
    import pygame
    import save_system
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    pygame.init()
    from main import Game
    return Game(pygame.display.set_mode((1280, 720)), player_name='mastery')


def _answer_the_last_tier_question(g, tier):
    """Every question of the tier but one already right; answer the last."""
    qe = g.quiz_engine
    stems = sorted(qe._tier_stems('philosophy', tier))
    qe._retired[('philosophy', tier)] = set(stems[:-1])
    qe.subject, qe.tier = 'philosophy', tier
    qe.current_question = {'question': stems[-1], 'answer': 'x'}
    qe._record_correct_for_mastery()
    g._on_quiz_answer(True)


def test_the_last_question_awards_the_trait_wisdom_and_names_the_pack(monkeypatch, tmp_path):
    from items import make_item_by_id
    g = _game(monkeypatch, tmp_path)
    p = g.player
    heal = make_item_by_id('potion', 'potion_of_stamina')        # identify tier 1
    sick = make_item_by_id('potion', 'potion_of_sickness')       # identify tier 2
    p.inventory += [heal, sick]
    # No trait allowance left: the Wisdom still lands now.
    p.quirk_stat_gained = 999
    wis = p.WIS
    qsys = g.quirk_system
    assert qsys.progress_count('philosophy_tier_1')[0] == 0
    _answer_the_last_tier_question(g, 1)
    assert 'philosophy_tier_1' in p.unlocked_quirks
    assert p.WIS == wis + 1
    assert not getattr(p, 'quirk_stat_owed', None)
    assert not g._needs_identify(heal)                           # tier 1: named
    assert g._needs_identify(sick)                               # tier 2: not yet
    done, need = qsys.progress_count('philosophy_tier_1')
    assert done == need and qsys.get_quirk_progress('philosophy_tier_1') == 1.0
    said = ' '.join(text for text, _kind in g.msg_log.entries[-12:])
    assert 'TIER 1 PHILOSOPHY CLEARED' in said and 'Gadfly of the Agora' in said
    assert 'potion of stamina' in said.lower()
    # Once only.
    g._philosophy_mastery_check()
    assert p.WIS == wis + 1


def test_a_picked_up_item_of_a_mastered_tier_names_itself(monkeypatch, tmp_path):
    from items import make_item_by_id
    g = _game(monkeypatch, tmp_path)
    p = g.player
    p.unlocked_quirks.add('philosophy_tier_1')
    heal = make_item_by_id('potion', 'potion_of_stamina')
    sick = make_item_by_id('potion', 'potion_of_sickness')
    for it in (heal, sick):
        it.x, it.y = p.x, p.y
        g.ground_items.append(it)
    g._pickup(target=heal)
    g._pickup(target=sick)
    assert not g._needs_identify(heal)
    assert g._needs_identify(sick)


def test_anything_reaching_the_pack_another_way_is_named_next_turn(monkeypatch, tmp_path):
    from items import make_item_by_id
    g = _game(monkeypatch, tmp_path)
    p = g.player
    p.unlocked_quirks.add('philosophy_tier_2')
    wand = make_item_by_id('wand', 'wand_of_striking')            # identify tier 2
    p.inventory.append(wand)                                     # a gift, a chest, a theft returned
    g._advance_turn()
    assert not g._needs_identify(wand)


def test_the_ring_of_pythia_lowers_the_tier_mastery_reads():
    from items import make_item_by_id

    class _Hero:
        unlocked_quirks = {'philosophy_tier_1'}

        def __init__(self, reduce):
            self._r = reduce

        def get_identify_tier_reduction(self):
            return self._r
    sick = make_item_by_id('potion', 'potion_of_sickness')       # tier 2
    assert not pm.covers(sick, _Hero(0))
    assert pm.identify_tier(sick, _Hero(1)) == 1 and pm.covers(sick, _Hero(1))


def test_a_wrong_answer_does_not_count():
    e = QuizEngine()
    before = e.tier_progress('philosophy', 1)
    e.start_quiz('threshold', 'philosophy', 1, callback=lambda r: None, threshold=1, total_qs=1)
    e.answer('certainly not the answer')
    assert e.tier_progress('philosophy', 1) == before
