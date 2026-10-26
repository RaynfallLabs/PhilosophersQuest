"""Reward codes for Dad (src/seeker_codes.py): pure-function tests.

A code must be the same every time for one Seeker and one achievement,
different for a sibling, readable aloud (no I, L, O or U), forgiving of how a
child types it, and impossible to make without the key.
"""
import pytest

import seeker_codes as sc

TEST_KEY = bytes(range(32))
OTHER_KEY = bytes(range(100, 132))


@pytest.fixture(autouse=True)
def _test_key():
    saved = sc._KEYS_OVERRIDE
    sc._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': TEST_KEY}}
    yield
    sc._KEYS_OVERRIDE = saved


ACHS = [('duck_hatched', 'QUACK'), ('questions_100', 'HUNDRED'), ('gorgon', 'GORGON')]


def test_known_answer_vector():
    # Pinned: if this changes, every code a child has ever been shown changes.
    assert sc.make_code('duck_hatched', 'QUACK', 'Robyn') == 'QUACK-NYEF-YZF5'


def test_name_is_normalised():
    a = sc.make_code('duck_hatched', 'QUACK', 'Robyn')
    assert a == sc.make_code('duck_hatched', 'QUACK', ' robyn ')
    assert a == sc.make_code('duck_hatched', 'QUACK', 'ROBYN')
    assert a == sc.make_code('duck_hatched', 'quack', 'Ro-byn!')


def test_codes_differ_by_seeker_and_achievement():
    a = sc.make_code('duck_hatched', 'QUACK', 'Robyn')
    assert a != sc.make_code('duck_hatched', 'QUACK', 'Corwin')
    assert a.split('-', 1)[1] != sc.make_code('questions_100', 'QUACK', 'Robyn').split('-', 1)[1]


def test_alphabet_is_readable():
    assert not set('ILOU') & set(sc.ALPHABET)
    for who in ('Robyn', 'Corwin', 'Fianna', 'Cain', 'Fluffs', 'X'):
        for aid, word in ACHS:
            chars = sc.make_code(aid, word, who).split('-', 1)[1].replace('-', '')
            assert len(chars) == 8 and set(chars) <= set(sc.ALPHABET)


def test_check_round_trip_and_typos():
    code = sc.make_code('gorgon', 'GORGON', 'Robyn')
    assert sc.check_code(code, 'Robyn', ACHS) == ('gorgon', 'pq1')
    sloppy = code.lower().replace('-', ' ')
    assert sc.check_code(sloppy, 'robyn', ACHS) == ('gorgon', 'pq1')
    # O for 0 and I/L for 1, in the code part only (the word keeps its O).
    word, chars = sc.split_code(code)
    typo = chars.replace('0', 'O').replace('1', 'I')
    assert sc.check_code(f'{word}-{typo}', 'Robyn', ACHS) == ('gorgon', 'pq1')


def test_wrong_seeker_or_forged_code_fails():
    code = sc.make_code('duck_hatched', 'QUACK', 'Robyn')
    assert sc.check_code(code, 'Corwin', ACHS) is None
    assert sc.check_code('QUACK-0000-0000', 'Robyn', ACHS) is None
    assert sc.check_code('NOPE-' + code.split('-', 1)[1], 'Robyn', ACHS) is None
    assert sc.check_code('', 'Robyn', ACHS) is None


def test_old_keys_still_verify_after_rotation():
    old = sc.make_code('duck_hatched', 'QUACK', 'Robyn')
    sc._KEYS_OVERRIDE = {'label': 'pq2', 'keys': {'pq1': TEST_KEY, 'pq2': OTHER_KEY}}
    new = sc.make_code('duck_hatched', 'QUACK', 'Robyn')
    assert new != old
    assert sc.check_code(old, 'Robyn', ACHS) == ('duck_hatched', 'pq1')
    assert sc.check_code(new, 'Robyn', ACHS) == ('duck_hatched', 'pq2')


def test_dev_codes_are_marked_and_never_accepted():
    sc._KEYS_OVERRIDE = {'label': sc.DEV_LABEL, 'keys': {sc.DEV_LABEL: sc.DEV_KEY}}
    code = sc.make_code('duck_hatched', 'QUACK', 'Robyn')
    assert code.startswith('DEV-') and sc.is_dev()
    assert sc.check_code(code, 'Robyn', ACHS) is None
    assert sc.check_code(code[4:], 'Robyn', ACHS) is None          # dev key is never trusted
    assert sc.check_code(code[4:], 'Robyn', ACHS, keys={'pq1': TEST_KEY}) is None


def test_seal():
    s = sc.seal(b'payload')
    assert sc.seal_ok(b'payload', 'pq1', s)
    assert not sc.seal_ok(b'payload!', 'pq1', s)
    assert not sc.seal_ok(b'payload', 'pq9', s)
    # A real build never trusts a seal made with the public dev key.
    dev = sc.seal(b'payload', 'pq1')
    sc._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': TEST_KEY, sc.DEV_LABEL: sc.DEV_KEY}}
    assert not sc.seal_ok(b'payload', sc.DEV_LABEL, dev)


def test_key_file_is_gitignored():
    from pathlib import Path
    gi = (Path(__file__).resolve().parent.parent / '.gitignore').read_text(encoding='utf-8')
    assert 'src/_dad_key.py' in gi
