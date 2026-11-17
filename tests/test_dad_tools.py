"""Dad's tools (tools/dad/): check a code, keep the redeemed ledger, print a
Codebook; and the release step that writes the key from the CI secret."""
import os
import sys
from pathlib import Path

import pytest

import seeker_codes as sc

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools' / 'dad'))
sys.path.insert(0, str(ROOT / 'tools' / 'release'))

import check_code  # noqa: E402
import codebook  # noqa: E402
import dadlib  # noqa: E402
import make_key  # noqa: E402
import write_dad_key  # noqa: E402


@pytest.fixture(autouse=True)
def _env(tmp_path):
    saved = sc._KEYS_OVERRIDE, dadlib._DAD_DIR_OVERRIDE
    sc._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}
    dadlib._DAD_DIR_OVERRIDE = str(tmp_path / 'PQ_Dad')
    yield tmp_path
    sc._KEYS_OVERRIDE, dadlib._DAD_DIR_OVERRIDE = saved


def test_check_code_real_fake_and_redeemed():
    code = sc.make_code('duck_hatched', 'DOOM', 'Robyn')
    first = check_code.check('Robyn', code)
    assert first.startswith('REAL CODE: Robyn, "The Duck of Doom"') and 'Recorded' in first
    again = check_code.check('robyn', code.lower())
    assert 'Already redeemed on' in again
    assert check_code.check('Corwin', code).startswith('NOT A REAL CODE')
    assert check_code.check('Robyn', 'DOOM-0000-0000').startswith('NOT A REAL CODE')
    assert 'DEV code' in check_code.check('Robyn', 'DEV-' + code)


def test_no_record_leaves_the_ledger_alone():
    code = sc.make_code('questions_100', 'HUNDRED', 'Robyn')
    assert 'not recorded' in check_code.check('Robyn', code, record_it=False)
    assert dadlib.ledger() == []


def test_for_a_kid_checks_with_the_seeker_name_and_records_under_the_kid():
    code = sc.make_code('duck_hatched', 'DOOM', 'Xyz')
    assert check_code.check('Corwin', code) == 'NOT A REAL CODE for Corwin.'      # his own name: no
    first = check_code.check('Xyz', code, kid='Corwin')
    assert first.startswith('REAL CODE: Xyz, "The Duck of Doom"')
    assert first.endswith('First time you have seen this code. Recorded for Corwin.')
    assert [(r['seeker'], r['achievement']) for r in dadlib.ledger()] == [('Corwin', 'duck_hatched')]
    assert dadlib.ledger()[0]['code'] == dadlib.code_key(code)
    assert 'Already redeemed for Corwin on' in check_code.check('xyz', code.lower(), kid='corwin')
    assert len(dadlib.ledger()) == 1


def test_a_code_used_for_another_kid_is_flagged_on_the_command_line():
    code = sc.make_code('duck_hatched', 'DOOM', 'Robyn')
    check_code.check('Robyn', code)
    line = check_code.check('Robyn', code, kid='Corwin')
    today = dadlib.ledger()[0]['date']
    assert f'This code was already used for Robyn on {dadlib.nice_date(today)}.' in line
    assert '--allow-duplicate' in line and len(dadlib.ledger()) == 1
    assert check_code.verify('Robyn', code, kid='Corwin')['status'] == 'duplicate'
    yes = check_code.check('Robyn', code, kid='Corwin', allow_duplicate=True)
    assert yes.endswith('Recorded for Corwin.')
    assert [r['seeker'] for r in dadlib.ledger()] == ['Robyn', 'Corwin']


def test_the_command_line_reads_for_and_its_flags(capsys):
    code = sc.make_code('duck_hatched', 'DOOM', 'Xyz')
    opts, args = check_code._options(['--for', 'Corwin', 'Xyz', code])
    assert opts == {'record_it': True, 'allow_duplicate': False, 'kid': 'Corwin'} and args == ['Xyz', code]
    opts, args = check_code._options(['--for=Fianna', '--no-record', '--allow-duplicate', 'Xyz', code])
    assert opts == {'record_it': False, 'allow_duplicate': True, 'kid': 'Fianna'}
    check_code.main(['--for', 'Corwin', 'Xyz', code])
    assert capsys.readouterr().out.strip().endswith('Recorded for Corwin.')
    check_code.main(['Robyn', sc.make_code('questions_100', 'HUNDRED', 'Robyn')])      # as before
    assert capsys.readouterr().out.strip().endswith('First time you have seen this code. Recorded.')
    assert [r['seeker'] for r in dadlib.ledger()] == ['Corwin', 'Robyn']


def test_the_ledger_finds_a_code_however_it_was_typed():
    code = sc.make_code('boss_medusa', 'GORGON', 'Robyn')
    assert 'Recorded' in check_code.check('Robyn', code.lower().replace('-', ' '))
    assert dadlib.ledger()[0]['code'] == code                      # written tidily
    for typed in (code, code.lower(), code.replace('-', ''), code.replace('0', 'O').replace('1', 'I')):
        assert [r['seeker'] for r in dadlib.find_code(typed)] == ['Robyn'], typed
    assert dadlib.find_code('GORGON-0000-0000') == [] and dadlib.find_code('') == []


def test_codebook_lists_every_achievement_with_a_real_code():
    page = codebook.build('Robyn')
    for a in dadlib.achievements():
        assert sc.make_code(a['id'], a['code_word'], 'Robyn') in page
    path = codebook.write('Robyn')
    assert os.path.exists(path) and str(dadlib.dad_dir()) in path


def test_make_key_round_trip_and_secret(tmp_path):
    keyfile = str(tmp_path / '_dad_key.py')
    make_key.write_keys('pq2', {'pq1': 'aa' * 32, 'pq2': 'bb' * 32}, keyfile)
    cur, keys = make_key.read_keys(keyfile)
    assert cur == 'pq2' and keys['pq1'] == 'aa' * 32
    secret = make_key.secret_value(cur, keys)
    assert secret.endswith('pq2:' + 'bb' * 32)
    assert write_dad_key.parse(secret) == ('pq2', {'pq1': 'aa' * 32, 'pq2': 'bb' * 32})


def test_release_refuses_a_missing_or_bad_secret(monkeypatch):
    for bad in ('', 'pq1:nothex', 'just-text'):
        monkeypatch.setenv('PQ_DAD_KEY', bad)
        monkeypatch.setattr(write_dad_key, 'OUT', os.devnull)
        assert write_dad_key.main() == 1
