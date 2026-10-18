"""Encounter schema validation (DEEDS_KARMA_DESIGN 8.3; tools/encounters/validate.py).

Every encounter in data/npc_encounters.json and data/flavor_encounters.json
must pass the validator, except the known breaches in
tests/encounter_legacy_allow.json: its "pending_engine" section lists fields
whose engine support is being built in parallel and is emptied when that
work is merged. A new breach fails; so does an allowlist entry that no longer
occurs (the list may only shrink). Fixture encounters prove each rule fires.
"""
import copy
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, ROOT)

from tools.encounters import validate as V  # noqa: E402


def test_shipped_encounters_pass_with_legacy_allowlist():
    issues = V.validate_all()
    errors, _allowed, stale = V.split_by_allowlist(issues, V.load_allowlist())
    assert not errors, '\n'.join(map(str, errors))
    assert not stale, f'stale allowlist entries (remove them): {stale}'


def test_allowlist_only_names_real_encounters():
    tags = {e['tag'] for _s, e in V.load_all()}
    assert set(V.load_allowlist()) <= tags


def test_normalise_defaults_cover_both_files():
    import flavor_encounters
    import npc_encounters
    for e in npc_encounters.ENCOUNTERS:
        assert e['role'] == 'anchor' and e['stakes'] in ('medium', 'high')
        assert len(e['band']) == 2
    # Every flavor encounter is JSON now (no hardcoded list), a story
    # encounter, with band = [min_level, max_level]. Stakes are never shown (P13).
    src = open(os.path.join(ROOT, 'src', 'flavor_encounters.py'), encoding='utf-8').read()
    assert "'tag':" not in src, 'encounter data belongs in data/flavor_encounters.json'
    for e in flavor_encounters.FLAVOR_ENCOUNTERS:
        assert e['role'] == 'story' and e['stakes'] in ('light', 'medium', 'high'), e['tag']
        assert e['band'] == [e['min_level'], e['max_level']]
    # The follow-ups that keep or break an oath are medium or higher (P11).
    for tag in ('flv_relic_broker', 'flv_cuthbert_chapel', 'flv_watch_post'):
        e = next(e for e in flavor_encounters.FLAVOR_ENCOUNTERS if e['tag'] == tag)
        assert e['callback_only'] and e['stakes'] == 'medium'


def test_cli_exits_clean():
    assert V.main([]) == 0


# ------------------------------------------------------------ fixtures

BASE = {
    'tag': 'fx_priests', 'name': 'Two Prisoners', 'symbol': '@', 'color': [200, 200, 200],
    'min_level': 5, 'max_level': 9, 'role': 'story', 'stakes': 'medium', 'band': [5, 9],
    'text': 'Two men in chains. Cultists in these halls have been known to wear a '
            "captured priest's robe.",
    'options': [
        {'label': 'Question them both',
         'quiz': {'subject': 'theology', 'tier': 3, 'mode': 'threshold', 'threshold': 1,
                  'total_qs': 1},
         'deeds': ['met.chained_priests'],
         'pass': {'outcome': 'The right one finishes the prayer.', 'karma': 1,
                  'karma_kind': 'judgment', 'deeds': ['saved.anselm']},
         'fail': {'outcome': 'You cannot tell.', 'deeds': ['lost.anselm']}},
        {'label': 'Free whichever begs hardest', 'naive': True,
         'warning': "Cultists in these halls have been known to wear a captured priest's robe.",
         'cost': {'type': 'hp_pct', 'amount': 20},
         'deeds': ['lost.anselm'], 'outcome': 'The cultist thanks you with a knife.'},
        {'label': 'Walk on', 'outcome': 'You walk on.'},
    ],
}


def _codes(enc, source='flavor'):
    return {i.code for i in V.validate_all([(source, enc)])}


def _mut(fn):
    e = copy.deepcopy(BASE)
    fn(e)
    return e


def test_fixture_is_clean():
    assert _codes(BASE) == set()


@pytest.mark.parametrize('mutate,code', [
    (lambda e: e['options'][0]['pass'].pop('karma_kind'), 'karma_kind_missing'),
    (lambda e: e['options'][1].update(naive=False) or e['options'][1].pop('naive'), 'judgment'),
    (lambda e: e['options'][1].update(karma=-1, karma_kind='reckless'), 'karma_kind'),
    (lambda e: e['options'][1].update(karma=1, karma_kind='forgo'), 'naive'),
    (lambda e: (e['options'][1].pop('cost'), e['options'][1].update(deeds=['met.x'])), 'naive'),
    (lambda e: e.update(stakes='light'), 'light_karma'),
    (lambda e: e['options'][0].update(reward={'type': 'gold', 'amount': 5}), 'quiz_shape'),
    (lambda e: e['options'][2].update(cost={'type': 'gold', 'amount': 5}), 'free_exit'),
    (lambda e: e['options'].extend([{'label': 'a', 'outcome': 'a'},
                                    {'label': 'b', 'outcome': 'b'}]), 'visible'),
    (lambda e: e['options'][2].update(deeds=[{'id': 'met.x', 'tags': ['virtue:forgo']}]),
     'virtue'),
    (lambda e: e['options'][2].update(reward={'type': 'stat', 'stat': 'WIS', 'amount': 1}),
     'stat_reward'),
    (lambda e: e['options'][0]['quiz'].update(subject='astrology'), 'quiz'),
    (lambda e: e['options'][0]['quiz'].update(timed=True), 'quiz'),
    (lambda e: e['options'][0]['quiz'].update(total_qs=4, threshold=3), 'stakes'),
    (lambda e: e['options'][1].update(warning='A sentence nowhere in the scene.'), 'naive'),
    (lambda e: e['options'][2].update(chronicle='Reached L12! +2 WIS.'), 'chronicle_lint'),
    (lambda e: e['options'][2].update(road={'id': 'x.y', 'hint': 'Press 2 for karma.'}),
     'road_lint'),
    (lambda e: e['options'][2].update(requires={'deed_all': ['x']}), 'condition'),
    (lambda e: e['options'][2].update(oath_keep='never_sworn'), 'reference'),
    (lambda e: e.update(disguise={'who': 'odin', 'tells': ['one eye bright']}), 'disguise'),
    (lambda e: e.update(contested=True), 'contested'),
    (lambda e: e.update(stance='3.1'), 'stance'),
    (lambda e: e['options'][2].update(karma=1, karma_kind='oath'), 'karma_kind'),
    (lambda e: e['options'][2].update(frobnicate=1), 'unknown_key'),
])
def test_rule_fires(mutate, code):
    assert code in _codes(_mut(mutate))


def test_forgo_needs_a_richer_visible_sibling():
    def refuse(e):
        e['options'][2].update(karma=1, karma_kind='forgo', label='Refuse the ring')
    assert 'forgo' in _codes(_mut(refuse))

    def with_temptation(e):
        refuse(e)
        e['options'].insert(2, {'label': 'Take the ring', 'outcome': 'It fits.',
                                'reward': {'type': 'specific_item', 'item_type': 'accessory',
                                           'item_id': 'x'}})
        e['options'].pop(1)                   # keep within four visible
    assert 'forgo' not in _codes(_mut(with_temptation))


def test_hidden_group_counts_once_in_the_visible_bound():
    def hidden(e):
        for n in range(3):
            e['options'].append({'label': f'secret {n}', 'hidden': True, 'hidden_group': 'g',
                                 'requires': {'deeds_any': ['noticed.odin']},
                                 'outcome': 'x'})
    assert 'visible' not in _codes(_mut(hidden))


def test_reward_value_table():
    t = V._rules()['reward_value']
    assert V.reward_value({'type': 'gold', 'amount': 50}, t) == 5
    assert V.reward_value({'type': 'gold', 'min': 10, 'max': 30}, t) == 2
    assert V.reward_value({'type': 'random_potion', 'count': 2}, t) == 6
    assert V.reward_value({'type': 'multi', 'rewards': [{'type': 'stat', 'amount': 1},
                                                        {'type': 'specific_item'}]}, t) == 21


def test_opportunities_report_covers_every_block():
    rep = V.opportunities_report()
    assert set(rep) == set(range(1, 11))


# ------------------------------------------------- rules the story draft needs

def test_a_loss_is_at_most_one():
    # Brandon, 2026-10-18: "Max karma drop is -1". -2 is rejected for every
    # kind, the gravest wrongs included.
    assert 'karma_size' not in _codes(_mut(lambda e: e['options'][2].update(
        karma=-1, karma_kind='cruelty')))
    for kind in ('cruelty', 'sacrilege', 'betray', 'stance_wrong'):
        assert 'karma_size' in _codes(_mut(lambda e, k=kind: e['options'][2].update(
            karma=-2, karma_kind=k))), kind
    assert 'karma_size' in _codes(_mut(lambda e: e['options'][2].update(
        karma=-3, karma_kind='cruelty')))
    assert 'karma_size' in _codes(_mut(lambda e: e['options'][0]['pass'].update(karma=2)))


def test_a_negative_beside_an_oath_break_must_be_the_break_itself():
    # The engine charges -1 betray for the break unless the outcome already
    # pays it as betray; a cruelty beside it would make one choice cost two.
    def brk(kind):
        def f(e):
            e['options'].insert(0, {'label': 'Swear', 'outcome': 'You swear.',
                                    'oath': {'id': 'fx_oath', 'to': 'x', 'what': 'y'}})
            e['options'].pop(2)                   # keep within four visible
            e['options'][-1].update(oath_break='fx_oath', karma=-1, karma_kind=kind)
        return f
    assert 'karma_size' in _codes(_mut(brk('cruelty')))
    assert 'karma_size' not in _codes(_mut(brk('betray')))


def test_a_story_medium_quiz_may_ask_two_of_three():
    assert 'stakes' not in _codes(_mut(lambda e: e['options'][0]['quiz'].update(
        total_qs=3, threshold=2)))


def test_a_failed_examination_may_land_the_trap_it_was_checking_for():
    # A fail branch beside a naive sibling may carry the trap's loss.
    assert 'stakes' not in _codes(_mut(lambda e: e['options'][0]['fail'].update(
        cost={'type': 'hp_pct', 'amount': 10})))

    def no_trap(e):
        e['options'][1].pop('naive')
        e['options'][1].pop('warning')
        e['options'][0]['pass'].update(karma=0)
        e['options'][0]['pass'].pop('karma_kind')
        e['options'][0]['fail'].update(cost={'type': 'hp_pct', 'amount': 10})
    assert 'stakes' in _codes(_mut(no_trap))


def test_options_split_by_deed_can_cover_the_walk_away_between_them():
    def split(e):
        e['options'][2].update(requires={'deeds_all': ['met.x']})
        e['options'].append({'label': 'Walk on', 'outcome': 'You go.',
                             'forbids': {'deeds_all': ['met.x']}})
    assert 'free_exit' not in _codes(_mut(split))

    def gap(e):
        e['options'][2].update(requires={'deeds_all': ['met.x']})
    assert 'free_exit' in _codes(_mut(gap))


def test_judgment_after_a_passed_examination():
    def after(e):
        e['options'][0]['pass'].update(karma=0, deeds=['noticed.anselm_true'],
                                       then='options')
        e['options'][0]['pass'].pop('karma_kind')
        e['options'].insert(2, {'label': 'Free the true priest',
                                'requires': {'deeds_all': ['noticed.anselm_true']},
                                'outcome': 'He walks free.', 'karma': 1,
                                'karma_kind': 'judgment'})
    assert 'judgment' not in _codes(_mut(after))

    def free(e):
        e['options'].insert(2, {'label': 'Free the true priest', 'outcome': 'x',
                                'karma': 1, 'karma_kind': 'judgment'})
    assert 'judgment' in _codes(_mut(free))


def test_forgo_counts_what_each_side_costs():
    def sword(e):
        e['options'][2].update(label='Hand over the sword', karma=1, karma_kind='forgo',
                               cost={'type': 'triggered_item_id', 'item_id': 'x'})
        e['options'][1] = {'label': 'Keep it', 'outcome': 'You keep it.'}
    assert 'forgo' not in _codes(_mut(sword))


def test_a_fight_is_a_visible_cost_on_the_right_side():
    def stance(e):
        e.update(stance='1', stance_note='x')
        e['options'][2].update(side='right', karma=1, karma_kind='stance',
                               fight={'monster_id': 'ogre'})
        e['options'].append({'label': 'Say it', 'side': 'wrong', 'outcome': 'x',
                             'karma': -1, 'karma_kind': 'stance_wrong'})
        e['options'].pop(1)
    assert 'stance' not in _codes(_mut(stance))


# ------------------------------------------- owning up vs surrender (J10)

def _confession(**over):
    """A callback where the hero meets someone he wronged: the fixture's walk
    on, a quiet way out, and the confession."""
    e = copy.deepcopy(BASE)
    e['options'] = [
        {'label': 'Pay it back quietly', 'requires': {'deeds_any': ['wrong.robbed_fx']},
         'cost': {'type': 'gold_pct', 'amount': 2}, 'outcome': 'You pay.'},
        dict({'label': 'Tell him it was you, and pay it back',
              'requires': {'deeds_any': ['wrong.robbed_fx']},
              'cost': {'type': 'gold_pct', 'amount': 10}, 'outcome': 'You say it.',
              'karma': 1, 'karma_kind': 'owning'}, **over),
        {'label': 'Walk on', 'outcome': 'You walk on.'},
    ]
    return e


def test_owning_up_with_a_cost_and_the_heros_own_wrong_is_clean():
    codes = _codes(_confession())
    assert 'owning' not in codes and 'karma_kind' not in codes
    # The wrong may be the whole encounter's requires instead of the option's.
    e = _confession(requires=None)
    e['options'][1].pop('requires')
    e['requires'] = {'deeds_any': ['wrong.robbed_fx']}
    assert 'owning' not in _codes(e)
    # A fight is a visible price too.
    e = _confession(cost=None, fight={'monster_id': 'ogre'})
    e['options'][1].pop('cost')
    assert 'owning' not in _codes(e)


@pytest.mark.parametrize('over', [
    {'cost': None},                                              # owning up for free is talk
    {'requires': {'deeds_any': ['met.fx']}},                    # not the hero's wrong
    {'requires': {'deeds_any': ['wrong.robbed_fx', 'met.fx']}},  # not always the hero's wrong
    {'requires': {'deeds_any': ['wrong.']}},                     # a wrong, but which?
    {'cost': {'type': 'accept_item', 'item_id': 'elaras_silver_ring'}},  # not a burden
])
def test_owning_up_needs_a_real_cost_and_the_heros_own_wrong(over):
    e = _confession(**over)
    if over.get('cost', 1) is None:
        e['options'][1].pop('cost')
    assert 'owning' in _codes(e)


def test_taking_up_a_cursed_burden_is_a_real_cost():
    e = _confession(cost={'type': 'accept_item', 'item_id': 'cursed_lodestone'})
    assert 'owning' not in _codes(e)


def test_owning_up_is_never_paid_before_a_crooked_court():
    e = _confession()
    e['authority'] = {'who': 'a bought magistrate', 'just': False}
    assert 'owning' in _codes(e)


def _tribunal(just, **over):
    e = copy.deepcopy(BASE)
    e['authority'] = {'who': 'the witch-finder and the mob', 'just': just}
    e['options'].append(dict({'label': 'Hand yourself over to them', 'submit': True,
                              'outcome': 'You go with them.'}, **over))
    return e


def test_submitting_to_an_unjust_authority_never_pays():
    assert 'unjust' not in _codes(_tribunal(False))
    assert 'unjust' in _codes(_tribunal(False, karma=1, karma_kind='forgo'))
    # Before an honest court, owning your guilt may be rewarded where the
    # design already allows it (Lucan to the assize, +1 judgment on a pass).
    assert 'unjust' not in _codes(_tribunal(True, karma=1, karma_kind='forgo'))


def test_walking_away_or_resisting_an_unjust_authority_is_never_penalised():
    e = _tribunal(False)
    e['options'][2].update(karma=-1, karma_kind='cruelty')       # walking on, penalised
    assert 'unjust' in _codes(e)
    # Only handing someone over, a villain's choice or the wrong side may cost.
    e = _tribunal(False, karma=-1, karma_kind='betray')
    assert 'unjust' not in _codes(e)


def test_authority_shape_and_submit_need_each_other():
    e = copy.deepcopy(BASE)
    e['options'][2]['submit'] = True
    assert 'authority' in _codes(e)
    e['authority'] = {'who': 'x'}
    assert 'authority' in _codes(e)
    e['authority'] = {'who': 'the assize', 'just': True, 'why': 'A lawful court.'}
    assert 'authority' not in _codes(e)
    e['authority']['mood'] = 'grim'
    assert 'unknown_key' in _codes(e)


def test_owning_report_lists_every_confession():
    rows = V.owning_report()
    assert rows and all(cb and wrongs for _t, _l, wrongs, _b, cb in rows)


def test_pending_engine_section_is_merged_into_the_allowlist(tmp_path):
    p = tmp_path / 'allow.json'
    p.write_text('{"_doc": "x", "a": ["c1"], "pending_engine": {"_doc": "y", '
                 '"a": ["c2"], "b": ["c3"]}}', encoding='utf-8')
    assert V.load_allowlist(str(p)) == {'a': {'c1', 'c2'}, 'b': {'c3'}}
    assert V.load_pending(str(p)) == {'a': {'c2'}, 'b': {'c3'}}
