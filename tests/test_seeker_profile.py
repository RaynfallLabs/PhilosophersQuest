"""The Seeker profile (src/seeker_profile.py): persistence that outlives every
run and every version. Atomic writes, the backup, damaged and edited files
(kept, never deleted), newer schemas (read-only), and two copies of the game
writing without losing each other's progress.
"""
import json
import os

import pytest

import seeker_codes as sc
import seeker_profile as sp


@pytest.fixture(autouse=True)
def _isolated(tmp_path):
    saved_keys, saved_dir = sc._KEYS_OVERRIDE, sp._DIR_OVERRIDE
    sc._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}
    sp._DIR_OVERRIDE = str(tmp_path)
    yield tmp_path
    sc._KEYS_OVERRIDE, sp._DIR_OVERRIDE = saved_keys, saved_dir


def _files(tmp_path):
    return sorted(os.listdir(tmp_path))


def test_round_trip():
    p = sp.load('Robyn')
    p.add('questions_answered', 5)
    p.raise_best('biggest_blow', 120)
    assert p.include('secret_builds', 'fianna')
    assert not p.include('secret_builds', 'fianna')
    p.set_live('right_streak', 7)
    assert p.unlock('questions_100', hero='Fianna')
    assert not p.unlock('questions_100')
    assert p.flush()
    q = sp.load('robyn')                      # same Seeker, any case
    assert q.stat('questions_answered') == 5 and q.best('biggest_blow') == 120
    assert q.members('secret_builds') == {'fianna'} and q.live('right_streak') == 7
    assert q.is_unlocked('questions_100')
    assert q.unlocked()['questions_100']['hero'] == 'Fianna'


def test_counters_never_go_down():
    p = sp.load('Robyn')
    p.add('kills', 3)
    p.add('kills', -10)
    p.raise_best('blow', 50)
    p.raise_best('blow', 10)
    assert p.stat('kills') == 3 and p.best('blow') == 50


def test_unknown_keys_survive():
    p = sp.load('Robyn')
    p.add('kills', 1)
    p.flush()
    path = sp.profile_path('Robyn')
    doc = json.load(open(path, encoding='utf-8'))
    doc['from_the_future'] = {'x': 1}
    sp.write(path, doc)
    q = sp.load('Robyn')
    q.add('kills', 1)
    q.flush()
    assert json.load(open(path, encoding='utf-8'))['from_the_future'] == {'x': 1}


def test_two_copies_merge(tmp_path):
    a = sp.load('Robyn')
    b = sp.load('Robyn')
    a.add('kills', 10)
    a.include('endings', 'died')
    a.unlock('first_fall')
    a.flush()
    b.add('kills', 4)
    b.include('endings', 'starved')
    b.unlock('forgot_to_eat')
    b.flush()
    c = sp.load('Robyn')
    assert c.stat('kills') == 14
    assert c.members('endings') == {'died', 'starved'}
    assert c.is_unlocked('first_fall') and c.is_unlocked('forgot_to_eat')


def test_backup_is_kept_and_restores_a_damaged_file(tmp_path):
    p = sp.load('Robyn')
    p.add('kills', 1)
    p.flush()
    p.add('kills', 1)
    p.flush()                                 # the first write is now the .bak
    path = sp.profile_path('Robyn')
    assert os.path.exists(path + '.bak')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('{not json')
    q = sp.load('Robyn')
    assert q.stat('kills') == 1               # the backup
    assert q.notice and 'backup' in q.notice
    assert not q.edited_found
    assert any('.unreadable-' in f for f in _files(tmp_path))   # kept, not deleted


def test_edited_file_is_set_aside_silently():
    p = sp.load('Robyn')
    p.add('kills', 1)
    p.flush()
    p.add('kills', 1)
    p.flush()
    path = sp.profile_path('Robyn')
    doc = json.load(open(path, encoding='utf-8'))
    doc['unlocked']['stone_home'] = {'at': 'x', 'version': 'x', 'hero': 'x'}
    json.dump(doc, open(path, 'w', encoding='utf-8'))      # seal now wrong
    q = sp.load('Robyn')
    assert not q.is_unlocked('stone_home')
    assert q.edited_found
    assert q.notice is None                    # the secret: no word about it
    assert any('.edited-' in f for f in os.listdir(os.path.dirname(path)))


def test_edit_while_running_is_caught_on_flush():
    p = sp.load('Robyn')
    p.add('kills', 2)
    p.flush()
    path = sp.profile_path('Robyn')
    doc = json.load(open(path, encoding='utf-8'))
    doc['stats']['kills'] = 99999
    json.dump(doc, open(path, 'w', encoding='utf-8'))
    p.add('kills', 1)
    assert p.flush()
    assert p.edited_found
    assert sp.load('Robyn').stat('kills') == 3


def test_newer_schema_is_read_only():
    p = sp.load('Robyn')
    p.add('kills', 1)
    p.flush()
    path = sp.profile_path('Robyn')
    doc = json.load(open(path, encoding='utf-8'))
    doc['schema'] = sp.SCHEMA + 1
    sp.write(path, doc)
    before = open(path, encoding='utf-8').read()
    q = sp.load('Robyn')
    assert q.readonly and q.notice and 'newer version' in q.notice
    q.add('kills', 5)
    assert not q.flush()
    assert open(path, encoding='utf-8').read() == before


def test_missing_file_falls_back_to_backup():
    p = sp.load('Robyn')
    p.add('kills', 1)
    p.flush()
    p.add('kills', 1)
    p.flush()
    os.remove(sp.profile_path('Robyn'))
    assert sp.load('Robyn').stat('kills') == 1


def test_failed_write_leaves_old_file(monkeypatch):
    p = sp.load('Robyn')
    p.add('kills', 1)
    p.flush()
    path = sp.profile_path('Robyn')
    before = open(path, encoding='utf-8').read()

    def boom(*a, **k):
        raise OSError('disk full')
    monkeypatch.setattr(sp.os, 'replace', boom)
    p.add('kills', 1)
    assert not p.flush()
    monkeypatch.undo()
    assert open(path, encoding='utf-8').read() == before
    assert not [f for f in os.listdir(os.path.dirname(path)) if f.endswith('.tmp')]


def test_index_active_seeker_and_names(tmp_path):
    assert sp.active_name() is None
    assert sp.set_active('  Robyn  ') == 'Robyn'
    assert sp.active_name() == 'Robyn'
    sp.set_active('Corwin')
    sp.set_active('robyn')
    assert sp.active_name() == 'robyn'
    assert [n.casefold() for n in sp.all_names()] == ['corwin', 'robyn']
    os.remove(os.path.join(tmp_path, 'index.json'))
    assert [n.casefold() for n in sp.all_names()] == ['corwin', 'robyn']   # rebuilt from files


def test_clean_name():
    assert sp.clean_name('   ') is None
    assert sp.clean_name('!!!') is None
    assert sp.clean_name('  Ro   byn ') == 'Ro byn'
    assert len(sp.clean_name('x' * 100)) == sp.NAME_MAX
