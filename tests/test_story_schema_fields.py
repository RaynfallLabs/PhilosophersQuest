"""The validator knows every J3 field (ENCOUNTER_STORIES_DRAFT Part J3):
the story-shaped fixtures used by the engine tests validate clean, each new
rule fires on a broken copy, Silas's judgment +1 on a follow-up option that
only a pass reveals is accepted, and the karma-opportunity-per-block budget
report and the karma Monte Carlo run on fixture and on shipped data.
"""
import copy
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))

from tools.encounters import validate as V  # noqa: E402


def _story(name):
    import test_story_engine_hooks as T
    import encounter_schema
    return encounter_schema.normalise(copy.deepcopy(getattr(T, name)), source='flavor')


def _codes(enc, source='flavor', extra=()):
    encs = [(source, enc)] + list(extra)
    return {i.code for i in V.validate_all(encs) if i.tag == enc['tag']}


def _all_three():
    return [('flavor', _story(n)) for n in ('SETNE', 'DEAD', 'GATE')]


def test_story_fixtures_validate_clean():
    issues = V.validate_all(_all_three())
    assert not issues, '\n'.join(map(str, issues))


SILAS = {
    'tag': 'fx_silas', 'name': 'Forgotten Prisoner', 'symbol': '@', 'color': [150, 150, 150],
    'block': 8, 'role': 'anchor', 'stakes': 'medium', 'band': [71, 79],
    'person': {'id': 'silas', 'name': 'Silas Mordaunt'},
    'text': "A white-haired man in an ancient cell. The wall is covered in scratches. "
            "They're too long, and some have a little cross after them.",
    'options': [
        {'label': 'Feed your gold into the lock', 'naive': True,
         'forbids': {'deeds_any': ['noticed.silas_poisoner']},
         'warning': "They're too long, and some have a little cross after them.",
         'cost': {'type': 'gold_pct', 'amount': 15},
         'deeds': ['aid.silas', {'id': 'spared.silas', 'payload': {'deserving': False}}],
         'person_status': {'status': 'spared', 'deserving': False},
         'outcome': 'He presses a little flask into your hand.'},
        {'label': 'Read the scratches before you decide',
         'quiz': {'subject': 'history', 'tier': 3, 'mode': 'threshold', 'threshold': 2,
                  'total_qs': 3},
         'pass': {'outcome': 'Eleven names, eleven little crosses.', 'then': 'options',
                  'deeds': ['noticed.silas_poisoner']},
         'fail': {'outcome': 'The scratches mean nothing to you.', 'then': 'options',
                  'deeds': ['met.silas']}},
        {'label': 'Leave him to his sentence',
         'requires': {'deeds_all': ['noticed.silas_poisoner']},
         'karma': 1, 'karma_kind': 'judgment',
         'outcome': 'He begins, very neatly, to scratch your name.'},
        {'label': 'Tell him you cannot afford it',
         'forbids': {'deeds_any': ['noticed.silas_poisoner']},
         'deeds': ['met.silas'], 'outcome': '"Perhaps the next one."'},
    ],
}


def test_silas_judgment_on_a_follow_up_only_a_pass_reveals():
    assert 'judgment' not in _codes(copy.deepcopy(SILAS), source='npc')


@pytest.mark.parametrize('mutate', [
    # The revealing deed is also written by the fail branch: no longer pass-only.
    lambda e: e['options'][1]['fail']['deeds'].append('noticed.silas_poisoner'),
    # No naive sibling: the examination proves nothing.
    lambda e: e['options'].pop(0),
    # The follow-up is not gated by the pass at all.
    lambda e: e['options'][2].pop('requires'),
])
def test_silas_rule_still_rejects_an_unearned_judgment(mutate):
    e = copy.deepcopy(SILAS)
    mutate(e)
    assert 'judgment' in _codes(e, source='npc')


def _mut(name, fn):
    e = _story(name)
    fn(e)
    return e


SENET = 1          # the senet option's index in SETNE


@pytest.mark.parametrize('name,mutate,code', [
    ('DEAD', lambda e: e['options'][1]['fight'].append({'monster_id': 'no_such_monster'}), 'fight'),
    ('DEAD', lambda e: e['options'][1]['fight'][1].update(count=40), 'fight'),
    ('DEAD', lambda e: e['options'][1]['fight'][0].update(mob=1), 'unknown_key'),
    ('DEAD', lambda e: e['options'][1].update(fight=[]), 'fight'),
    ('DEAD', lambda e: [o.pop('fight', None) for o in e['options']], 'hostile'),
    ('DEAD', lambda e: e.update(callback_only=False), 'hostile'),
    ('DEAD', lambda e: e.pop('hostile'), 'free_exit'),
    ('SETNE', lambda e: e['options'][SENET]['quiz'].pop('play_all'), 'per_miss'),
    ('SETNE', lambda e: e['options'][SENET]['per_miss'].append({'text': 'x'}), 'per_miss'),
    ('SETNE', lambda e: e['options'][SENET]['per_miss'][1].update(effect={'effect': 'sunk'}),
     'per_miss'),
    ('SETNE', lambda e: e['options'][SENET]['per_miss'][0].update(splash=1), 'unknown_key'),
    ('SETNE', lambda e: e['options'][SENET]['fail_by_correct'].update({'2': {'outcome': 'x'}}),
     'quiz_shape'),
    ('SETNE', lambda e: e['options'][0].update(per_miss=[{'text': 'x'}]), 'quiz_shape'),
    ('SETNE', lambda e: e['options'][SENET]['quiz'].update(play_all='yes'), 'quiz'),
    ('SETNE', lambda e: e['options'][SENET]['quiz'].update(spin=1), 'unknown_key'),
    ('SETNE', lambda e: e['options'][SENET]['pass'].pop('schedule'), 'oath'),
    ('SETNE', lambda e: e['options'][SENET]['pass']['oath'].update(lapse_mode='never'), 'oath'),
    ('SETNE', lambda e: e['options'][SENET]['pass']['schedule'][0].update(after_oath_due='other'),
     'schedule'),
    ('SETNE', lambda e: e['options'][0]['people'].append({'id': 'Bad Id'}), 'people'),
    ('SETNE', lambda e: e['options'][0]['people'][0].update(status='drowned'), 'people'),
    ('SETNE', lambda e: e['options'][2].update(seal_door='yes'), 'field'),
    ('SETNE', lambda e: e['options'][2]['people'][0].update(last_line='x' * 300), 'field'),
    ('GATE', lambda e: e['options'][0]['people_lines'].update(table='heaven'), 'people_lines'),
    ('GATE', lambda e: e['options'][0]['people_lines'].update(max=50), 'people_lines'),
    ('GATE', lambda e: e['options'][1].update(reward={'type': 'effect', 'effect': 'glowing'}),
     'reward'),
    ('GATE', lambda e: e['options'][1].update(reward={'type': 'effect', 'effect': 'porter',
                                                      'floors': 40}), 'reward'),
    ('GATE', lambda e: e['options'][1].update(reward={'type': 'gold_pct_loss', 'amount': 90}),
     'reward'),
])
def test_new_field_rules_fire(name, mutate, code):
    e = _mut(name, mutate)
    others = [x for x in _all_three() if x[1]['tag'] != e['tag']]
    assert code in _codes(e, extra=others)


def test_karma_size_allows_no_loss_beyond_one():
    # Brandon, 2026-10-18: "Max karma drop is -1", the gravest wrongs too.
    def with_karma(k, kind):
        e = _story('GATE')
        e['stakes'] = 'medium'
        e['options'][1].update(karma=k, karma_kind=kind)
        return e
    for kind in ('cruelty', 'sacrilege', 'betray', 'stance_wrong'):
        assert 'karma_size' not in _codes(with_karma(-1, kind)), kind
        assert 'karma_size' in _codes(with_karma(-2, kind)), kind
    assert 'karma_size' in _codes(with_karma(-3, 'cruelty'))
    assert 'karma_size' in _codes(with_karma(2, 'forgo'))


def test_oath_break_with_its_own_betray_point_is_not_charged_twice():
    # Engine side is in test_story_engine_hooks; the data shape validates.
    e = _story('DEAD')
    assert 'karma_size' not in _codes(e, extra=[x for x in _all_three() if x[1]['tag'] != 'flv_dead_come_for_the_book'])


def test_naive_with_a_lifted_purse_or_a_fever_is_a_real_consequence():
    e = copy.deepcopy(SILAS)
    e['options'][0].pop('cost')
    e['options'][0]['deeds'] = ['aid.silas']
    e['options'][0].pop('person_status')
    assert 'naive' in _codes(e, source='npc')
    e['options'][0]['reward'] = {'type': 'effect', 'effect': 'sickly', 'duration': 60}
    assert 'naive' not in _codes(e, source='npc')
    e['options'][0]['reward'] = None
    e['options'][0].pop('reward')
    e['options'][0]['delayed'] = [{'after_floors': [0, 1],
                                   'reward': {'type': 'gold_pct_loss', 'amount': 10}}]
    assert 'naive' not in _codes(e, source='npc')
    assert 'delayed' not in _codes(e, source='npc')     # [0, 1] is allowed


def test_reward_value_names_the_book_as_the_greatest_prize():
    t = V._rules()['reward_value']
    book = V.reward_value({'type': 'specific_item', 'item_type': 'spellbook',
                           'item_id': 'book_of_thoth'}, t)
    other = V.reward_value({'type': 'specific_item', 'item_id': 'x'}, t)
    assert book > other == 6
    assert V.reward_value({'type': 'gold_pct_loss', 'amount': 10}, t) < 0
    assert V.reward_value({'type': 'effect', 'effect': 'porter', 'floors': 5}, t) == 5


def test_setne_forgo_has_its_temptation():
    e = _story('SETNE')
    others = [x for x in _all_three() if x[1]['tag'] != e['tag']]
    assert 'forgo' not in _codes(e, extra=others)
    e['options'][SENET]['pass'].pop('reward')
    assert 'forgo' in _codes(e, extra=others)


# ------------------------------------------------------------------ budget report

def test_opportunity_budget_on_fixtures():
    encs = [('npc', copy.deepcopy(SILAS))] + _all_three()
    med = _story('GATE')
    med.update(tag='fx_med', stakes='medium', band=[71, 80], callback_only=False)
    med['options'][1].update(karma=1, karma_kind='forgo')
    encs.append(('flavor', med))
    rep = V.opportunity_budget(encs)
    assert set(rep) == set(range(1, 11))
    assert rep[8]['anchors'] == (1, 1)                    # Silas has a +1 path
    assert rep[8]['medium'] == (1, 1, 1)                  # even band: one medium slot
    assert rep[8]['expected'] == 2.0
    # The tomb (its own roll, 45-65 without 60) has a +1 path (forgo, oath).
    assert rep[5]['showcase'] > 0 and rep[6]['showcase'] > 0 and rep[7]['showcase'] > 0
    assert abs(sum(rep[b]['showcase'] for b in rep) - 1.0) < 0.02
    assert rep[1]['expected'] == 0.0


def test_budget_cli_on_shipped_data(capsys):
    assert V.main(['--budget']) == 0
    out = capsys.readouterr().out
    assert out.count('genuine +1 chances') == 10


# ------------------------------------------------------------------ karma Monte Carlo

def test_karma_sim_runs_on_fixtures_and_shipped_data():
    from tools.balance import karma_sim
    rep = karma_sim.run(n=60, seed=2)
    assert set(rep['styles']) == set(karma_sim.STYLES)
    assert rep['oracle_max'] <= 12                        # 8.2 oracle check
    for r in rep['styles'].values():
        assert -10 <= r['p10'] <= r['p50'] <= r['p90'] <= 10
        # Each share is rounded to four places, so the four can miss 1 by 2e-4.
        assert abs(r['sword'] + r['scales'] + r['silence'] + r['below_zero'] - 1) < 5e-4
    # The simulation sets the gate itself and puts the shipped rules back.
    import karma
    assert karma.rules() is karma._RULES and karma.gate_enabled() is True
    encs = [('npc', copy.deepcopy(SILAS))] + _all_three()
    small = karma_sim.run(n=40, seed=3, encounters=encs)
    assert small['untyped_karma_options'] == 0
    # A saint reads the wall and leaves Silas to his sentence more often than
    # the villain does anything good.
    assert small['styles']['saint']['mean'] >= small['styles']['villain']['mean']


def test_karma_sim_is_deterministic():
    from tools.balance import karma_sim
    a = karma_sim.run(n=30, seed=9, styles=['saint', 'inconsistent'])
    b = karma_sim.run(n=30, seed=9, styles=['saint', 'inconsistent'])
    assert a == b
