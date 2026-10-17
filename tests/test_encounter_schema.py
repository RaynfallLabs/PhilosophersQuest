"""Encounter schema validation (DEEDS_KARMA_DESIGN 8.3; tools/encounters/validate.py).

Every encounter in data/npc_encounters.json, data/flavor_encounters.json and
the hardcoded FLAVOR_ENCOUNTERS list must pass the validator, except the
known legacy breaches in tests/encounter_legacy_allow.json, which Phase 3a
must empty. A new breach fails; so does an allowlist entry that no longer
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


def test_normalise_defaults_cover_all_three_sources():
    import flavor_encounters
    import npc_encounters
    for e in npc_encounters.ENCOUNTERS:
        assert (e['role'], e['stakes']) == ('anchor', 'medium')
        assert len(e['band']) == 2
    hard = [e for e in flavor_encounters.FLAVOR_ENCOUNTERS if e['tag'] == 'flv_wandering_merchant']
    assert hard, 'the hardcoded list is covered'
    for e in flavor_encounters.FLAVOR_ENCOUNTERS:
        assert (e['role'], e['stakes']) == ('story', 'light')
        assert e['band'] == [e['min_level'], e['max_level']]


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
    (lambda e: e['options'][0]['quiz'].update(total_qs=3, threshold=2), 'stakes'),
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
