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
