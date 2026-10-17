"""The deeds register (src/deeds.py, DEEDS_KARMA_DESIGN 2 and 8.1): pure
unit tests on plain dicts."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import deeds  # noqa: E402


def _rec(reg, did, floor=5, **kw):
    return deeds.record(reg, did, floor=floor, block=deeds.karma_block(floor), turn=1,
                        source='test', **kw)


def test_karma_block():
    assert [deeds.karma_block(f) for f in (1, 10, 11, 20, 21, 91, 99, 100)] == \
        [1, 1, 2, 2, 3, 10, 10, 10]
    assert deeds.karma_block(999) == 10 and deeds.karma_block(0) == 1


@pytest.mark.parametrize('did', ['met.marta', 'aid.marta', 'flag.thread_lost.lena',
                                 'oath.cuthbert_gospel', 'noticed.odin', 'flag.a.b.c'])
def test_id_grammar_accepts(did):
    assert deeds.valid_id(did)


@pytest.mark.parametrize('did', ['marta', 'Met.marta', 'met', 'met.', 'met.Marta',
                                 'bogus.marta', 'flag.a.b.c.d', 'met.mar-ta', '', None])
def test_id_grammar_rejects(did):
    assert not deeds.valid_id(did)
    if did is not None:
        with pytest.raises(ValueError):
            _rec(deeds.new_register(), did)


def test_record_and_queries():
    reg = deeds.new_register()
    _rec(reg, 'met.marta', floor=3)
    _rec(reg, 'aid.marta', floor=3, payload={'with': 'healing_potion'})
    _rec(reg, 'aid.lena', floor=7)
    _rec(reg, 'aid.marta', floor=9)          # repeats are allowed
    assert deeds.has(reg, 'met.marta') and not deeds.has(reg, 'met.lena')
    assert deeds.count(reg, 'aid.') == 3 and deeds.count(reg, 'aid.*') == 3
    assert deeds.count(reg, 'aid.marta') == 2
    assert deeds.first(reg, 'aid.')['floor'] == 3
    assert deeds.last(reg, 'aid.')['floor'] == 9
    assert deeds.floors_since(reg, 'aid.lena', 12) == 5
    assert deeds.floors_since(reg, 'saved.x', 12) is None
    assert deeds.payload(reg, 'aid.marta', 'with') is None      # from the LAST match
    assert deeds.payload(reg, 'met.marta', 'nope', 7) == 7
    assert deeds.count(reg, since_floor=7) == 2
    seqs = [d['seq'] for d in reg['log']]
    assert seqs == sorted(seqs) and len(set(seqs)) == 4


def test_expiry_and_unique():
    reg = deeds.new_register()
    _rec(reg, 'flag.carrying_lena', floor=10, ttl_floors=2)
    assert deeds.has(reg, 'flag.carrying_lena', deepest=12)
    assert not deeds.has(reg, 'flag.carrying_lena', deepest=13)
    assert deeds.has(reg, 'flag.carrying_lena')                 # no deepest: no expiry
    a = _rec(reg, 'met.odin', unique=True)
    b = _rec(reg, 'met.odin', unique=True)
    assert a is b and deeds.count(reg, 'met.odin') == 1


def test_virtue_tags_engine_only():
    reg = deeds.new_register()
    with pytest.raises(ValueError):
        _rec(reg, 'forgo.purse', tags=['virtue:forgo'])
    d = _rec(reg, 'forgo.purse', tags=['virtue:forgo'], engine=True)
    assert 'virtue:forgo' in d['tags']
    _rec(reg, 'wrong.robbed', tags=['vice:cruelty'])           # vices are fine from data
    assert deeds.blocks_with(reg, tag='virtue:forgo') == {1}


@pytest.mark.parametrize('fn,status,deed,tag', [
    (deeds.keep_oath, 'kept', 'kept.gospel', 'virtue:kept'),
    (deeds.break_oath, 'broken', 'broke.gospel', 'vice:betray'),
    (deeds.lapse_oath, 'lapsed', 'lapsed.gospel', 'vice:lapsed'),
    (deeds.release_oath, 'released', 'released.gospel', None),
])
def test_oath_lifecycle(fn, status, deed, tag):
    reg = deeds.new_register()
    o = deeds.swear(reg, 'gospel', to='Brother Cuthbert', what='Carry the Gospel down.',
                    floor=12, block=2, turn=5, source='flv_coffin_bearer')
    assert o['status'] == 'open' and o['made_block'] == 2
    assert deeds.has(reg, 'oath.gospel')
    assert [x['id'] for x in deeds.open_oaths(reg)] == ['gospel']
    assert fn(reg, 'gospel', floor=20, block=2) is True
    assert deeds.oath_status(reg, 'gospel') == status
    d = deeds.last(reg, deed)
    assert d is not None
    assert d['tags'] == ([tag] if tag else [])
    # Only from open: a second resolution of any kind is a no-op.
    for other in (deeds.keep_oath, deeds.break_oath, deeds.lapse_oath, deeds.release_oath):
        assert other(reg, 'gospel', floor=21, block=3) is False
    assert deeds.oath_status(reg, 'gospel') == status
    assert deeds.open_oaths(reg) == []
    assert deeds.keep_oath(reg, 'never_sworn', floor=1, block=1) is False


def test_people_and_threads():
    reg = deeds.new_register()
    deeds.meet(reg, 'marta', name='Marta', floor=4)
    deeds.set_person(reg, 'marta', status='saved', owed=True, last_line='She asked my name.')
    p = reg['people']['marta']
    assert (p['status'], p['owed'], p['first_floor'], p['name']) == ('saved', True, 4, 'Marta')
    deeds.open_thread(reg, 'marta_daughter', hint='A girl will come looking.', floor=4)
    assert reg['threads']['marta_daughter']['status'] == 'open'
    assert deeds.close_thread(reg, 'marta_daughter') is True
    assert deeds.close_thread(reg, 'marta_daughter') is False


def test_pending_queue():
    reg = deeds.new_register()
    a = deeds.schedule(reg, {'kind': 'reward', 'target': 9})
    b = deeds.schedule(reg, {'kind': 'encounter', 'target': 14, 'id': 'cb1'})
    assert [p['id'] for p in deeds.due_on_arrival(reg, 10)] == [a['id']]
    assert len(deeds.due_on_arrival(reg, 14)) == 2
    assert deeds.pop(reg, 'cb1') is b and deeds.pop(reg, 'cb1') is None
    assert len(reg['pending']) == 1


def test_check_condition_grammar():
    reg = deeds.new_register()
    _rec(reg, 'noticed.odin', tags=['god:odin'])
    _rec(reg, 'forgo.a', tags=['virtue:forgo'], engine=True)
    _rec(reg, 'forgo.b', tags=['virtue:forgo'], engine=True)
    deeds.swear(reg, 'aldric_lodestone', to='Sir Aldric', what='x', floor=5, block=1)
    ctx = {'reg': reg, 'karma': 3, 'stats': {'WIS': 15, 'STR': 9}, 'floor': 12,
           'deepest': 12, 'items': {'cursed_lodestone'}}
    ok = deeds.check
    assert ok(None, ctx) and ok({}, ctx)
    assert ok({'deeds_all': ['noticed.odin']}, ctx)
    assert not ok({'deeds_all': ['noticed.odin', 'met.mimir']}, ctx)
    assert ok({'deeds_any': ['met.mimir', 'noticed.']}, ctx)
    assert not ok({'deeds_none': ['noticed.odin']}, ctx)
    assert ok({'oath_status': {'aldric_lodestone': 'open'}}, ctx)
    assert ok({'oath_status': {'aldric_lodestone': ['kept', 'open']}}, ctx)
    assert not ok({'oath_status': {'aldric_lodestone': 'kept'}}, ctx)
    assert ok({'karma_min': 3, 'karma_max': 3}, ctx) and not ok({'karma_min': 4}, ctx)
    assert ok({'stat_min': {'WIS': 15}}, ctx) and not ok({'stat_min': {'STR': 10}}, ctx)
    assert ok({'items_any': ['cursed_lodestone']}, ctx)
    assert not ok({'items_none': ['cursed_lodestone']}, ctx)
    assert ok({'tags_count_min': {'virtue:forgo': 2}}, ctx)
    assert not ok({'tags_count_min': {'virtue:forgo': 3}}, ctx)
    assert ok({'floor_min': 12, 'floor_max': 12}, ctx) and not ok({'floor_max': 11}, ctx)
    assert ok({'any': [{'stat_min': {'WIS': 18}}, {'deeds_any': ['noticed.odin']}]}, ctx)
    assert not ok({'any': [{'stat_min': {'WIS': 18}}, {'karma_min': 9}]}, ctx)
    # ANDed: one failing key fails the whole condition
    assert not ok({'karma_min': 0, 'floor_min': 50}, ctx)
    with pytest.raises(ValueError):
        ok({'deed_all': ['typo']}, ctx)


def test_migrate_old_save_backfills():
    class P:
        deepest_floor_reached = 23
    state = {
        'player': P(),
        '_encountered_npcs': {'marta_ratchatcher', 'helena_cartographer'},
        '_encountered_flavor_npcs': {'flv_old_traveler'},
        '_npc_encounter_levels': {5: {'tag': 'marta_ratchatcher'},
                                  14: {'tag': 'tam_thief'},
                                  24: {'tag': 'helena_cartographer'}},
        '_flavor_encounter_levels': {3: {'tag': 'flv_old_traveler'}},
    }
    reg = deeds.migrate(None, legacy=state)
    assert reg['v'] == deeds.CURRENT_VERSION
    assert deeds.has(reg, 'met.marta_ratchatcher') and deeds.has(reg, 'met.flv_old_traveler')
    assert deeds.first(reg, 'met.marta_ratchatcher')['floor'] == 5
    assert deeds.first(reg, 'met.flv_old_traveler')['source'] == 'legacy'
    slots = reg['karma']['slots']
    # Past blocks are closed; block 3 too, because its anchor (Helena, floor 24) was met.
    assert slots == {1: 'legacy', 2: 'legacy', 3: 'legacy'}
    state['_encountered_npcs'] = {'marta_ratchatcher'}
    reg = deeds.migrate(None, legacy=state)
    assert reg['karma']['slots'] == {1: 'legacy', 2: 'legacy'}         # current block open


def test_migrate_keeps_unknown_keys_and_fills_missing():
    saved = {'v': 1, 'seq': 4, 'log': [], 'future_thing': [1, 2]}
    reg = deeds.migrate(saved)
    assert reg['future_thing'] == [1, 2] and reg['seq'] == 4
    assert 'ledger' in reg['karma'] and reg['used_options'] == {}
