"""Merlin's stone: the path to the Staff of Emrys (Brandon, 2026-11-16: yes,
other heroes can earn it on a path; myth-true, once a run, placed at run
start, earned only by what the hero does there, one path, one staff,
depth-true tier).

Malory IV.1 and IV.5: Nimue shut Merlin under a great stone, and Bagdemagus
could not lift it ("leave your labour"); the hawthorn is the Livre d'Artus's;
Geoffrey's Merlin moved the Giants' Dance by art where strength failed, so
the voice under the stone gives his staff to one who answers (SCIENCE), not
one who heaves. Never placed for Merlin himself: the staff is in his hand.

The path is early-game but placed by the Road's seed, so it is proven by
headless games through the real encounter and quiz callback (the encounter
helpers are test_horns.py's).
"""
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest  # noqa: E402

import test_horns as TH  # noqa: E402
import encounter_schema as ES  # noqa: E402
from tools.encounters import validate as V  # noqa: E402
from welcome_screen import SECRET_BUILDS  # noqa: E402

TAG = 'flv_merlins_stone'
STAFF = 'staff_of_emrys'
MERLIN = 'merlin ambrosius'
ENC = TH.FLV[TAG]


def _start_floors(g):
    return {p['spec']['encounter']: p['target'] for p in g._deeds['pending']
            if p.get('source') == 'engine:run_start'}


# ---------------------------------------------------------------- data

def test_the_path_is_placed_once_a_run_on_tier_ones_floors_never_for_merlin():
    spec = next(s for s in TH.RULES['run_start_schedule'] if s['encounter'] == TAG)
    assert spec['floors'] == [ENC['min_level'], ENC['max_level']] == [10, 16]
    assert spec['not_for_builds'] == [MERLIN]
    assert ENC['callback_only']
    # depth-true: the staff is maths tier 1, and so are the path's floors and quiz
    staff = json.load(open(os.path.join(ROOT, 'data', 'items', 'weapon.json'), encoding='utf-8'))[STAFF]
    assert staff['quiz_tier'] == 1
    assert all((f - 1) // 20 + 1 == 1 for f in spec['floors'])
    # Not in floors 1-9, where the first oaths' callbacks have narrow windows
    # (on 6-11 it starved Wat's seventh lamp in 4 runs of 60).
    assert spec['floors'][0] >= 10


def test_one_way_to_earn_it_the_myths_and_never_a_second_copy():
    rewards = [b.get('reward') for o in ENC['options'] for b in ES.option_branches(o)]
    assert [r for r in rewards if r] == [{'type': 'specific_item', 'item_type': 'weapon', 'item_id': STAFF}]
    answer = next(o for o in ENC['options'] if o.get('quiz'))
    assert answer['quiz']['subject'] == 'science' and answer['quiz']['tier'] == 1
    assert answer['requires'] == {'items_none': [STAFF]}


def test_the_path_passes_the_encounter_validator():
    issues = [i for i in V.validate_all() if TAG in str(i)]
    assert not issues, issues


def test_the_stone_has_its_painted_sprite_and_the_badge_its_art():
    assert TH._png('monsters', ENC['sprite_id']) == (64, 64)
    import pygame
    p = os.path.join(ROOT, 'assets', 'achievements', 'not_by_strength.png')
    assert pygame.image.load(p).get_size() == (128, 128)


# ---------------------------------------------------------------- placement

def test_every_seed_puts_the_stone_on_a_free_floor_of_its_band():
    g = TH._game(name='__test_merlin_seeds__')
    for seed in range(40):
        random.seed(seed)
        g._deeds['pending'] = []
        g._init_road()
        start = _start_floors(g)
        assert 10 <= start[TAG] <= 16, (seed, start[TAG])
        assert start[TAG] not in set(g._secret_floors()), seed
        assert len(set(start.values())) == len(start)           # one floor each


def test_merlin_himself_never_meets_his_own_stone():
    from main import Game
    random.seed(3)
    g = Game(TH._screen(), player_name=MERLIN, secret_build=SECRET_BUILDS[MERLIN])
    assert g.player.weapon.id == STAFF
    assert TAG not in _start_floors(g)
    assert 'flv_robin_hood_bridge' in _start_floors(g)           # the other paths still are
    # A plain hero who happens to be called Merlin gets the path.
    g2 = Game(TH._screen(), player_name='Merlin')
    assert TAG in _start_floors(g2)


# ---------------------------------------------------------------- the encounter

def _staffs(g):
    return [i for i in list(g.player.inventory) + [g.player.weapon] if getattr(i, 'id', '') == STAFF]


def test_answering_the_voice_earns_the_staff():
    g = TH._game(name='__test_merlin_pass__')
    TH._open(g, TH._meet(g, 12, TAG))
    labels = TH._labels(g)
    assert labels == ['Try to lift the stone', '"Who are you?"', "Answer the voice's questions",
                      'Leave him under his stone']
    TH._pick(g, "Answer the voice's questions", quiz=TH.PASS)
    assert 'Not by strength' in g._npc_outcome_text
    assert len(_staffs(g)) == 1
    TH._continue(g)
    import deeds
    assert deeds.has(g._deeds, 'told.merlin_staff') and deeds.has(g._deeds, 'met.merlin')
    assert any('gave me his staff' in str(e.get('text', '')) for e in g._chronicle)


def test_heaving_at_the_stone_gives_nothing_and_the_voice_says_why():
    g = TH._game(name='__test_merlin_lift__')
    TH._open(g, TH._meet(g, 12, TAG))
    TH._pick(g, 'Try to lift the stone')
    assert 'Leave your labour' in g._npc_outcome_text and 'not do it with my arms' in g._npc_outcome_text
    TH._continue(g)
    assert 'Try to lift the stone' not in TH._labels(g)          # once is enough
    assert not _staffs(g)
    TH._pick(g, '"Who are you?"')
    assert 'Merlin' in g._npc_outcome_text and 'Stonehenge' in g._npc_outcome_text
    TH._continue(g)
    assert not _staffs(g)


@pytest.mark.parametrize('how', ['fail', 'leave'])
def test_a_wrong_answer_or_walking_on_earns_no_staff(how):
    g = TH._game(name='__test_merlin_no__')
    TH._open(g, TH._meet(g, 12, TAG))
    if how == 'fail':
        TH._pick(g, "Answer the voice's questions", quiz=TH.FAIL)
        assert 'not yet' in g._npc_outcome_text
    else:
        TH._pick(g, 'Leave him under his stone')
    TH._continue(g)
    assert not _staffs(g)
    assert TAG in g._encountered_flavor_npcs                     # once a run


def test_a_hero_already_holding_the_staff_is_not_offered_another():
    from items import make_item_by_id
    g = TH._game(name='__test_merlin_second__')
    g.player.inventory.append(make_item_by_id('weapon', STAFF))
    TH._open(g, TH._meet(g, 12, TAG))
    assert "Answer the voice's questions" not in TH._labels(g)


def test_the_qa_key_reaches_the_stone():
    import game_horns
    assert game_horns.QA_PATHS[-1] == TAG
    g = TH._game(name='__test_merlin_qa__')
    g.player.qa_tools = True
    TH._go(g, 13)
    g._qa_horn_step = game_horns.QA_PATHS.index(TAG)
    g._qa_horns()
    npc = TH._npc(g, TAG)
    assert npc is not None and max(abs(npc.x - g.player.x), abs(npc.y - g.player.y)) <= 3


# ---------------------------------------------------------------- the Seeker

def test_the_staff_won_at_the_stone_is_not_by_strength(seeker):
    g = TH._game(name='__test_merlin_badge__')
    TH._open(g, TH._meet(g, 12, TAG))
    TH._pick(g, "Answer the voice's questions", quiz=TH.FAIL)
    TH._continue(g)
    assert not TH._won(g, 'not_by_strength')
    g2 = TH._game(name='__test_merlin_badge_2__')
    TH._open(g2, TH._meet(g2, 12, TAG))
    TH._pick(g2, "Answer the voice's questions", quiz=TH.PASS)
    TH._continue(g2)
    assert TH._won(g2, 'not_by_strength')


def test_the_achievement_hint_points_at_malory_not_the_mechanic():
    by = {a['id']: a for a in TH._load('data', 'achievements.json')['achievements']}
    a = by['not_by_strength']
    assert a['category'] == 'secrets' and 'Malory' in a['hint']
    low = a['hint'].lower()
    assert not any(w in low for w in a['spoiler_words'])
    for word in ('quiz', 'science', 'staff', 'answer', 'merlin'):
        assert word not in low, word


@pytest.fixture
def seeker(tmp_path):
    import seeker_codes
    import seeker_profile
    saved = seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE
    seeker_codes._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}
    seeker_profile._DIR_OVERRIDE = str(tmp_path / 'seekers')
    seeker_profile.set_active('Robyn')
    yield 'Robyn'
    seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE = saved


# ---------------------------------------------------------------- the census

def test_the_census_counts_the_path_in_tier_one():
    from tools.balance import tier_census
    assert tier_census.band(ENC['min_level']) == 1
