"""Dad's Code Validator (tools/dad/code_validator.py, tools/dad/validator_core.py):
the code entry, the check with the Seeker name typed and its record under the
kid chosen, the names remembered per kid, duplicates, the reels' outcome and
stop, the tracker, the kids list and the reward line, all without a window;
then a headless run of every screen.

Every test points the ledger at a temp dir (dadlib._DAD_DIR_OVERRIDE) and the
codes at a test key (seeker_codes._KEYS_OVERRIDE): no real key, code or
child's data is read or written.
"""
import json
import os
import random
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame  # noqa: E402
import pytest  # noqa: E402

import seeker_codes as sc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools' / 'dad'))

import check_code  # noqa: E402
import dadlib  # noqa: E402
import validator_core as core  # noqa: E402

TEST_KEY = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}


@pytest.fixture(autouse=True)
def _env(tmp_path):
    saved = sc._KEYS_OVERRIDE, dadlib._DAD_DIR_OVERRIDE, core._NOTES_PATH
    sc._KEYS_OVERRIDE = dict(TEST_KEY)
    dadlib._DAD_DIR_OVERRIDE = str(tmp_path / 'PQ_Dad')
    core._NOTES_PATH = str(tmp_path / 'no_notes.json')
    yield tmp_path
    sc._KEYS_OVERRIDE, dadlib._DAD_DIR_OVERRIDE, core._NOTES_PATH = saved


ACHS = dadlib.achievements()
WORDS = core.code_words(ACHS)
BY_ID = {a['id']: a for a in ACHS}


def code_for(aid, seeker='Fianna'):
    return sc.make_code(aid, BY_ID[aid]['code_word'], seeker)


def typed(text):
    """The keys typed one at a time, as the window feeds them."""
    raw = ''
    for ch in text:
        raw, _line = core.type_key(raw, ch, WORDS)
    return raw


def entry(text):
    return core.parse_entry(typed(text), WORDS)


# -- the code entry ------------------------------------------------------------------

def test_typing_shapes_the_code_and_upper_cases_it():
    e = entry('doomabcdefgh')
    assert e.code == 'DOOM-ABCD-EFGH' and e.complete and e.known
    assert entry('DOOM-ABCD-EFGH').code == 'DOOM-ABCD-EFGH'
    assert entry('doom abcd efgh').code == 'DOOM-ABCD-EFGH'
    # As far as typed: the word ends by itself when it is a whole code word.
    assert entry('DOO').code == 'DOO' and not entry('DOO').in_chars
    assert entry('DOOM').code == 'DOOM-' and entry('DOOM').in_chars
    assert entry('DOOMAB').code == 'DOOM-AB'


def test_the_typos_seeker_codes_forgives_are_read_as_meant():
    e = entry('DOOM-OOOO-IILL')
    assert e.chars == '00001111'
    # Never in the word: GORGON keeps its O.
    assert entry('GORGON').word == 'GORGON'


def test_a_word_another_word_begins_with_waits_for_a_dash():
    assert 'HUNDRED' in WORDS and 'HUNDREDTRIPS' in WORDS
    e = entry('HUNDRED')
    assert e.word == 'HUNDRED' and not e.in_chars and e.more_word
    assert 'dash' in core.hint(e)
    assert entry('HUNDRED-').in_chars
    assert entry('HUNDRED5').code == 'HUNDRED-5'
    assert entry('HUNDREDTX').code == 'HUNDRED-TX'        # no word goes on HUNDREDTX
    assert entry('HUNDREDT').word == 'HUNDREDT'           # HUNDREDTRIPS might
    assert entry('HUNDREDTRIPS').code == 'HUNDREDTRIPS-'


def test_keys_that_change_nothing_are_refused_with_a_reason():
    raw = typed('DOOM-ABCD')
    assert core.type_key(raw, 'u', WORDS) == (raw, "Codes never use the letter U. Is it a V?")
    assert core.type_key(raw, '-', WORDS)[0] == raw              # the slot draws that dash already
    full = typed('DOOM-ABCD-EFGH')
    assert core.type_key(full, 'X', WORDS) == (full, "That's the whole code. Press Enter to check it.")
    assert core.type_key('', '7', WORDS)[0] == ''                 # a code starts with its word
    assert core.type_key('', '!', WORDS) == ('', '')


def test_backspace_takes_back_what_showed():
    assert core.backspace(typed('DOOMAB'), WORDS) == 'DOOMA'
    assert core.parse_entry(core.backspace('HUNDRED-', WORDS), WORDS).in_chars is False
    assert core.backspace('', WORDS) == ''


def test_a_pasted_code_is_read_whatever_its_spacing():
    raw = core.entry_from_text('  doom abcd-efgh \n', WORDS)
    assert core.parse_entry(raw, WORDS).code == 'DOOM-ABCD-EFGH'


def test_a_dev_code_is_seen_as_soon_as_it_starts():
    e = entry('DEV')
    assert e.dev and not e.word
    e = entry('DEV-DOOM-ABCD-EFGH')
    assert e.dev and e.code == 'DEV-DOOM-ABCD-EFGH'
    assert not any(w.startswith('DEV') for w in WORDS)


# -- the check -----------------------------------------------------------------------------

def test_a_real_code_is_recorded_once_in_the_ledger_check_code_reads():
    aid = 'duck_hatched'
    v = core.validate('Fianna', entry(code_for(aid)))
    assert v['status'] == 'new' and v['achievement']['id'] == aid and v['recorded']
    rows = dadlib.ledger()
    assert [(r['seeker'], r['achievement']) for r in rows] == [('Fianna', aid)]
    # check_code.py sees it as redeemed; the validator says already claimed.
    assert 'Already redeemed on' in check_code.check('Fianna', code_for(aid))
    again = core.validate('fianna', entry(code_for(aid)))
    assert again['status'] == 'already' and again['row']['date'] == rows[0]['date']
    assert len(dadlib.ledger()) == 1
    title, lines = core.result_lines(again)
    assert title == "Already Claimed" and core.nice_date(rows[0]['date']) in lines[0]


def test_a_code_typed_with_forgiven_typos_still_checks():
    code = code_for('questions_100')
    word, rest = code.split('-', 1)
    slipped = word + '-' + rest.replace('0', 'O').replace('1', 'I')
    assert core.validate('Fianna', entry(slipped))['status'] == 'new'


def test_a_code_that_does_not_match_says_why_and_records_nothing():
    code = code_for('duck_hatched')
    bad = code[:-1] + ('X' if code[-1] != 'X' else 'Y')
    v = core.validate('Fianna', entry(bad))
    assert v['status'] == 'fake' and v['why'] == 'letters'
    title, lines = core.result_lines(v)
    assert title == "Not a Real Code"
    assert lines[0] == "That code isn't real for the Seeker name Fianna. Check the letters and the name."
    assert core.validate('Fianna', entry('GORGEN-ABCD-EFGH'))['why'] == 'word'
    # Another kid's code is not real for this name: no "it looks like Corwin's code" any more.
    other = core.validate('Fianna', entry(code_for('duck_hatched', 'Corwin')))
    assert other['status'] == 'fake' and other['why'] == 'letters' and 'sibling' not in other
    assert not any('Corwin' in ln for ln in core.result_lines(other)[1])
    assert dadlib.ledger() == []
    assert core.seeker_names('Fianna') == []                     # nothing remembered either


# -- the Seeker name (Brandon, 2026-11-17: "Ask for the code and the name of the Seeker used.
#    Assign the badge to the kid profile.") ----------------------------------------------------------

def test_the_code_is_checked_with_the_seeker_name_and_given_to_the_kid():
    aid = 'duck_hatched'
    v = core.validate('Corwin', entry(code_for(aid, 'Xyz')), 'Xyz')
    assert v['status'] == 'new' and v['kid'] == 'Corwin' and v['seeker'] == 'Xyz'
    rows = dadlib.ledger()
    assert [(r['seeker'], r['achievement']) for r in rows] == [('Corwin', aid)]   # under the kid
    assert dadlib.redeemed('Corwin', aid) and not dadlib.redeemed('Xyz', aid)
    assert core.tracker('Corwin')['claimed'] == 1 and core.tracker('Xyz')['claimed'] == 0
    # The name is remembered for the kid, and fills the field next time.
    assert core.seeker_names('Corwin') == ['Xyz'] and core.prefill_name('corwin') == 'Xyz'
    assert core.prefill_name('Fianna') == 'Fianna'               # nothing remembered: the kid's own name


def test_only_the_name_typed_is_tried():
    code = code_for('duck_hatched', 'Xyz')
    core.remember_seeker_name('Corwin', 'Xyz')
    v = core.validate('Corwin', entry(code), 'Corwin')           # Xyz is remembered, but not typed
    assert v['status'] == 'fake' and v['seeker'] == 'Corwin'
    assert "isn't real for the Seeker name Corwin" in core.result_lines(v)[1][0]
    assert dadlib.ledger() == []
    assert core.validate('Corwin', entry(code), 'xyz ')['status'] == 'new'   # as the game reads names
    blank = core.validate('Corwin', entry(code), '  ')
    assert blank['status'] == 'fake' and blank['why'] == 'name'
    assert core.result_lines(blank)[0] == "No Seeker Name"


def test_the_seeker_names_are_remembered_newest_first():
    for aid, name in (('duck_hatched', 'Xyz'), ('questions_100', 'Abc'), ('streak_25', 'xyz')):
        assert core.validate('Corwin', entry(code_for(aid, name)), name)['status'] == 'new'
    assert core.seeker_names('Corwin') == ['xyz', 'Abc']         # once each, the last used first
    assert core.prefill_name('Corwin') == 'xyz'
    data = json.loads(Path(core.kids_path()).read_text(encoding='utf-8'))
    assert data['kids'] == ['Fianna', 'Corwin'] and data['seeker_names'] == {'Corwin': ['xyz', 'Abc']}
    # The kids list is written without losing them, and a kid put back finds them again.
    core.save_kids(core.remove_kid(core.load_kids(), 1))
    assert core.load_kids() == ['Fianna'] and core.seeker_names('Corwin') == ['xyz', 'Abc']
    many = [f'Name{i}' for i in range(12)]
    for n in many:
        core.remember_seeker_name('Fianna', n)
    assert core.seeker_names('Fianna') == many[::-1][:core.SEEKER_NAMES_KEPT]


def test_old_kids_files_load(_env):
    path = Path(dadlib.dad_dir(), 'kids.json')
    path.write_text(json.dumps({'kids': ['Fianna', 'Corwin', 'Robyn']}), encoding='utf-8')   # before seeker_names
    assert core.load_kids() == ['Fianna', 'Corwin', 'Robyn'] and core.seeker_names('Robyn') == []
    assert core.prefill_name('Robyn') == 'Robyn'
    core.remember_seeker_name('Robyn', 'Wren')
    data = json.loads(path.read_text(encoding='utf-8'))
    assert data == {'kids': ['Fianna', 'Corwin', 'Robyn'], 'seeker_names': {'Robyn': ['Wren']}}
    path.write_text(json.dumps(['Ada', 'Bo']), encoding='utf-8')                             # a bare list
    assert core.load_kids() == ['Ada', 'Bo'] and core.seeker_names('Ada') == []
    for junk in ('{not json', json.dumps({'kids': 5, 'seeker_names': ['x']}),
                 json.dumps({'kids': ['Ada'], 'seeker_names': {'Ada': 'Wren'}})):
        path.write_text(junk, encoding='utf-8')
        assert core.load_kids() in (['Fianna', 'Corwin'], ['Ada'])
        assert core.seeker_names('Ada') == []
    core.remember_seeker_name('Ada', 'Wren')                     # a damaged table is written fresh
    assert core.seeker_names('Ada') == ['Wren']


# -- duplicates ----------------------------------------------------------------------------------------

def test_a_code_already_used_for_another_kid_is_flagged_not_recorded():
    code = code_for('duck_hatched', 'Fianna')
    assert core.validate('Fianna', entry(code))['status'] == 'new'
    first = dadlib.ledger()[0]
    # The same code for Corwin, typed any old way (case, spaces, O for 0): flagged.
    sloppy = code.lower().replace('-', ' ').replace('0', 'o')
    v = core.validate('Corwin', entry(sloppy), 'Fianna')
    assert v['status'] == 'duplicate' and v['row']['seeker'] == 'Fianna'
    title, lines = core.result_lines(v)
    assert title == "Already Used"
    assert lines[0] == f"This code was already used for Fianna on {core.nice_date(first['date'])}."
    assert "Enter: give it to Corwin anyway." in lines[-1]
    assert len(dadlib.ledger()) == 1 and core.seeker_names('Corwin') == []
    assert core.reel_outcome(v, list(BY_ID), random.Random(1)) == ['duck_hatched'] * 3
    # Dad says yes: it is Corwin's too.
    yes = core.validate('Corwin', entry(code), 'Fianna', allow_duplicate=True)
    assert yes['status'] == 'new' and yes['duplicate_of']['seeker'] == 'Fianna'
    assert [(r['seeker'], r['achievement']) for r in dadlib.ledger()] == [('Fianna', 'duck_hatched'),
                                                                         ('Corwin', 'duck_hatched')]
    # Now each holds it: the same code again is "already claimed" for either.
    for kid in ('Fianna', 'Corwin'):
        again = core.validate(kid, entry(code), 'Fianna')
        assert again['status'] == 'already' and core.result_lines(again)[0] == "Already Claimed"
    assert len(dadlib.ledger()) == 2


def test_the_same_kid_with_the_badge_from_another_name_is_already_claimed():
    core.validate('Corwin', entry(code_for('duck_hatched', 'Xyz')), 'Xyz')
    v = core.validate('Corwin', entry(code_for('duck_hatched', 'Abc')), 'Abc')    # another computer
    assert v['status'] == 'already' and v['row']['seeker'] == 'Corwin'
    assert len(dadlib.ledger()) == 1


def test_a_ledger_row_written_by_hand_still_counts_as_used():
    code = code_for('duck_hatched', 'Fianna')
    _ledger_rows([('Fianna', 'duck_hatched', '2026-11-17')])
    import csv
    rows = dadlib.ledger()
    rows[0]['code'] = code.lower().replace('-', ' ')
    with open(dadlib.ledger_path(), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=dadlib.LEDGER_FIELDS)
        w.writeheader()
        w.writerows(rows)
    assert [r['seeker'] for r in dadlib.find_code(code)] == ['Fianna']
    v = core.validate('Corwin', entry(code), 'Fianna')
    assert v['status'] == 'duplicate'
    assert core.result_lines(v)[1][0] == "This code was already used for Fianna on 17 November 2026."


def test_a_dev_code_is_explained_and_never_recorded():
    v = core.validate('Fianna', entry('DEV-' + code_for('duck_hatched')))
    assert v['status'] == 'dev'
    title, lines = core.result_lines(v)
    assert title == "A Practice Code" and 'DEV' in lines[0]
    assert dadlib.ledger() == []


def test_check_code_still_words_its_answers_the_same_way():
    code = code_for('duck_hatched', 'Robyn')
    assert check_code.check('Robyn', code, record_it=False).endswith('(not recorded).')
    assert check_code.check('Robyn', code).endswith('First time you have seen this code. Recorded.')
    assert check_code.check('Robyn', 'DEV-' + code).startswith('NOT A REAL CODE. It is a DEV code')
    assert check_code.check('Corwin', code) == 'NOT A REAL CODE for Corwin.'


def test_without_a_real_key_the_validator_knows_it():
    assert core.key_ready()
    sc._KEYS_OVERRIDE = {'label': sc.DEV_LABEL, 'keys': {sc.DEV_LABEL: sc.DEV_KEY}}
    assert not core.key_ready()
    assert any('make_key.py' in line for line in core.key_help())


# -- the reels ---------------------------------------------------------------------------------

def test_a_real_code_lands_three_of_its_badge_and_any_other_a_mismatch():
    rng = random.Random(4)
    pool = list(BY_ID)
    new = {'status': 'new', 'achievement': BY_ID['duck_hatched']}
    old = {'status': 'already', 'achievement': BY_ID['duck_hatched']}
    assert core.reel_outcome(new, pool, rng) == ['duck_hatched'] * 3
    assert core.reel_outcome(old, pool, rng) == ['duck_hatched'] * 3
    for status in ('fake', 'dev'):
        for _ in range(30):
            out = core.reel_outcome({'status': status}, pool, rng)
            assert len(set(out)) == 3


def test_the_reels_stop_on_the_outcome_from_where_they_rest():
    rng = random.Random(9)
    pool = list(BY_ID)
    strips = core.idle_strips(pool, rng)
    rest = [0, 0, 0]
    for trial in range(150):
        out = [rng.choice(pool)] * 3 if trial % 2 else rng.sample(pool, 3)
        plan = core.plan_reels(out, strips, rest)
        for k in range(3):
            # Nothing in the window moves until the lever is down...
            assert plan.on_payline(k, 0.0) == strips[k][rest[k]]
            assert plan.on_payline(k, core.LEVER_TIME) == strips[k][rest[k]]
            # ...and each reel stops on its badge, and stays there.
            assert plan.on_payline(k, plan.done_at()) == out[k]
            assert plan.on_payline(k, plan.done_at() + 5) == out[k]
            assert 8 < plan.speeds[k] < 24
        strips, rest = plan.strips, plan.targets


def test_the_reels_stop_one_at_a_time_in_about_three_seconds():
    plan = core.plan_reels(['a', 'b', 'c'], [['x'] * 12, ['y'] * 12, ['z'] * 12])
    first_still = [min(i / 100 for i in range(600) if plan.stopped(k, i / 100)) for k in range(3)]
    assert first_still == sorted(first_still) and len(set(first_still)) == 3
    assert first_still[0] > core.LEVER_TIME + 1.0
    assert 2.5 <= plan.done_at() <= 4.0


# -- the tracker ---------------------------------------------------------------------------------

def test_the_tracker_reads_the_same_ledger_as_check_code():
    check_code.check('Corwin', code_for('duck_hatched', 'Corwin'))
    core.validate('Corwin', entry(code_for('questions_100', 'Corwin')))
    core.validate('Fianna', entry(code_for('questions_100', 'Fianna')))
    tr = core.tracker('corwin')
    assert tr['total'] == len(ACHS) and tr['claimed'] == 2
    got = {e['id']: e for e in tr['entries'] if e['claimed']}
    assert set(got) == {'duck_hatched', 'questions_100'}
    assert all(e['date'] for e in got.values())
    assert sum(t for _g, t in tr['by_rarity'].values()) == len(ACHS)
    assert sum(g for g, _t in tr['by_rarity'].values()) == 2
    assert [s['id'] for s in tr['sections']] == list(dadlib.categories())
    assert sum(s['total'] for s in tr['sections']) == len(ACHS)
    assert core.tracker('Fianna')['claimed'] == 1


def _ledger_rows(rows):
    """Write the ledger by hand (seeker, achievement, date), as several
    machines' codes would leave it."""
    import csv
    with open(dadlib.ledger_path(), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=dadlib.LEDGER_FIELDS)
        w.writeheader()
        for seeker, aid, date in rows:
            w.writerow({'date': date, 'seeker': seeker, 'code': 'X', 'achievement': aid,
                        'name': BY_ID[aid]['name']})


def test_the_library_holds_every_badge_with_its_page():
    _ledger_rows([('Fianna', 'questions_100', '2026-11-01')])
    tr = core.tracker('Fianna')
    ids = [e['id'] for e in tr['entries']]
    assert sorted(ids) == sorted(BY_ID) and len(ids) == len(set(ids))
    # Grouped by category in the game's order, data order inside each.
    for sec in tr['sections']:
        assert [e['id'] for e in sec['entries']] == [a['id'] for a in ACHS if a['category'] == sec['id']]
        assert all(e['category_name'] == sec['name'] for e in sec['entries'])
    e = next(x for x in tr['entries'] if x['id'] == 'questions_100')
    assert e['claimed'] and e['hint'] == BY_ID['questions_100']['hint']
    assert e['text'] == BY_ID['questions_100']['unlocked_text']
    # A ladder knows its rungs and which are claimed.
    assert e['tier'] == 1 and len(e['ladder']) > 1
    assert e['ladder'][0] == {'id': 'questions_100', 'rarity': 'common', 'claimed': True}
    assert not any(r['claimed'] for r in e['ladder'][1:])


def test_a_badge_page_mirrors_the_seeker_gallery():
    tr = core.tracker('Fianna', rows=[{'seeker': 'Fianna', 'achievement': 'duck_hatched',
                                       'date': '2026-11-17'}])
    got = {e['id']: e for e in tr['entries']}
    page = core.detail_lines(got['duck_hatched'])
    assert page[0] == (BY_ID['duck_hatched']['name'], 'name')
    assert ('Claimed on 17 November 2026', 'claimed') in page
    assert (BY_ID['duck_hatched']['unlocked_text'], 'text') in page
    assert not any(kind == 'hint' for _t, kind in page)
    locked = core.detail_lines(got['questions_100'])
    assert ('Not claimed yet', 'locked') in locked and ('Hint', 'head') in locked
    assert (BY_ID['questions_100']['hint'], 'hint') in locked
    assert not any(kind == 'text' for _t, kind in locked)
    # A deep secret shows its name and "???" until claimed, as in the game.
    deep = [a['id'] for a in ACHS if a['hint'].strip() == '???']
    assert deep
    for aid in deep:
        page = core.detail_lines(got[aid])
        assert (BY_ID[aid]['name'], 'name') in page and ('???', 'hint') in page
        assert BY_ID[aid]['unlocked_text'] not in [t for t, _k in page]
    assert page[1] == ('Legendary  ·  Violet', 'rarity') and page[2] == ('Secrets', 'category')


def test_the_earned_list_is_newest_first_from_every_machine():
    _ledger_rows([('Fianna', 'questions_100', '2026-11-01'),
                  ('Corwin', 'duck_hatched', '2026-11-20'),
                  ('fianna', 'duck_hatched', '2026-11-17'),       # another machine, another spelling
                  ('Fianna', 'streak_25', '2026-11-17'),          # the same day, written later
                  ('Fianna', 'questions_100', '2026-11-30')])     # a second record never counts twice
    tr = core.tracker('Fianna')
    assert [(e['id'], e['date']) for e in tr['earned']] == [
        ('streak_25', '2026-11-17'), ('duck_hatched', '2026-11-17'), ('questions_100', '2026-11-01')]
    assert tr['claimed'] == 3 and all(e['claimed'] for e in tr['earned'])
    assert [e['id'] for e in core.tracker('Corwin')['earned']] == ['duck_hatched']
    assert core.tracker('Robyn')['earned'] == []


def test_the_grid_arrows_keep_the_column_across_categories():
    sections = [{'entries': [0] * 7}, {'entries': [0] * 3}, {'entries': [0] * 5}]
    rows = core.grid_rows(sections, 5)
    assert rows == [[0, 1, 2, 3, 4], [5, 6], [7, 8, 9], [10, 11, 12, 13, 14]]
    assert core.grid_move(3, 'down', rows) == 6          # to the end of a shorter row
    assert core.grid_move(6, 'down', rows) == 8
    assert core.grid_move(8, 'up', rows) == 6
    assert core.grid_move(0, 'up', rows) == 0
    assert core.grid_move(14, 'down', rows) == 14
    assert core.grid_move(4, 'right', rows) == 5 and core.grid_move(5, 'left', rows) == 4
    assert core.grid_move(14, 'right', rows) == 14 and core.grid_move(0, 'left', rows) == 0
    assert core.section_start(sections, 8, 1) == 10
    assert core.section_start(sections, 8, -1) == 0
    assert core.section_start(sections, 0, -1) == 0
    assert core.section_start(sections, 12, 1) == 10
    assert core.grid_move(0, 'down', []) == 0


def test_the_sound_choice_is_remembered_outside_the_repo(_env):
    assert core.load_settings() == {'sound': True}
    core.save_settings(sound=False)
    assert core.load_settings() == {'sound': False}
    assert Path(core.settings_path()).parent == Path(dadlib.dad_dir())
    assert str(_env) in core.settings_path()


def test_short_and_long_dates():
    assert core.nice_date('2026-11-17') == '17 November 2026'
    assert core.nice_date('2026-11-17', short=True) == '17 Nov 2026'
    assert core.nice_date('soon') == 'soon'


# -- the kids --------------------------------------------------------------------------------------

def test_the_kids_default_to_fianna_and_corwin_and_are_remembered(_env):
    assert core.load_kids() == ['Fianna', 'Corwin']
    names, i, msg = core.add_kid(core.load_kids(), '  robyn ')
    assert names == ['Fianna', 'Corwin', 'Robyn'] and i == 2 and msg == "Robyn added."
    core.save_kids(names)
    assert core.load_kids() == names
    assert Path(dadlib.dad_dir(), 'kids.json').is_file()
    assert str(_env) in core.kids_path()
    same, j, msg = core.add_kid(names, 'CORWIN')
    assert same == names and j == 1 and 'already' in msg
    assert core.add_kid(names, ' !! ')[1] == -1
    assert core.remove_kid(names, 0) == ['Corwin', 'Robyn']


# -- the reward line -------------------------------------------------------------------------------

def test_the_reward_is_dads_note_else_a_line_by_rarity(_env):
    a = BY_ID['duck_hatched']
    assert core.reward_line(a) == core.REWARD_BY_RARITY[a['rarity']]
    notes = _env / 'notes.json'
    notes.write_text(json.dumps({'notes': {}, 'rewards': {'duck_hatched': 'Ice cream!'},
                                 'rewards_by_rarity': {'common': 'A sticker.'}}), encoding='utf-8')
    core._NOTES_PATH = str(notes)
    assert core.reward_line(a) == 'Ice cream!'
    common = next(x for x in ACHS if x['rarity'] == 'common' and x['id'] != 'duck_hatched')
    assert core.reward_line(common) == 'A sticker.'
    # Dad's private file (outside the repo) wins.
    Path(dadlib.dad_dir(), 'rewards.json').write_text(json.dumps({'rewards': {'duck_hatched': 'Pizza!'}}),
                                                     encoding='utf-8')
    assert core.reward_line(a) == 'Pizza!'


def test_the_repo_notes_file_holds_no_rewards_yet():
    """Brandon decides the rewards: the shipped notes file carries none."""
    data = json.loads((ROOT / 'tools' / 'dad' / 'achievement_notes.json').read_text(encoding='utf-8'))
    assert not data.get('rewards')


# -- the window, headless ---------------------------------------------------------------------------

@pytest.fixture
def app(ui_theme_isolated):
    import code_validator
    import seeker_screen
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    a = code_validator.App(screen, sound=False, rng=random.Random(5))
    yield a
    seeker_screen.clear_cache()


def _key(app, key, uni='', mod=0):
    app.handle(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=mod, scancode=0))


def _run(app, seconds, step=1 / 30):
    for _ in range(int(seconds / step)):
        app.update(step)


def _lively(surface):
    """The frame is drawn: more than a handful of colours on it."""
    small = pygame.transform.scale(surface, (160, 100))
    return len({small.get_at((x, y))[:3] for x in range(0, 160, 4) for y in range(0, 100, 4)}) > 20


def test_every_screen_draws_headless(app):
    import code_validator as cv
    app.draw()
    assert app.state == cv.KIDS and _lively(app.screen)
    _key(app, pygame.K_RETURN)                                   # Fianna
    assert app.state == cv.CODE and app.name == 'Fianna'
    code = code_for('duck_hatched')
    for ch in code[:6]:
        _key(app, 0, ch)
    app.draw()
    for ch in code[6:]:
        _key(app, 0, ch)
    assert app.entry.complete and app.entry.code == code
    _key(app, pygame.K_RETURN)
    assert app.state == cv.SPIN
    assert dadlib.redeemed('Fianna', 'duck_hatched') is not None   # recorded as it was checked
    for t in (0.1, 0.6, 1.0, 1.4):
        _run(app, t - app.spin_t)
        app.draw()
    _run(app, 4.0)
    assert app.state == cv.PARTY
    for _ in range(3):
        _run(app, 0.5)
        app.draw()
    assert _lively(app.screen)
    _key(app, pygame.K_TAB)                                      # to the library, on the new badge
    assert app.state == cv.TRACKER
    app.draw()
    assert app.track['claimed'] == 1 and app.scroll > 0
    assert app.track['entries'][app.sel]['id'] == 'duck_hatched'
    for k in (pygame.K_RIGHT, pygame.K_DOWN, pygame.K_PAGEDOWN, pygame.K_END, pygame.K_HOME):
        _key(app, k)
        app.draw()
    assert app.sel == 0 and app.scroll == 0
    _key(app, pygame.K_l)                                        # the earned list
    assert app.view == 'list'
    app.draw()
    assert [e['id'] for e in app.track['earned']] == ['duck_hatched']
    _key(app, pygame.K_l)
    _key(app, pygame.K_RIGHTBRACKET)                             # Corwin's badges
    app.draw()
    assert app.name == 'Corwin' and app.track['claimed'] == 0
    _key(app, pygame.K_l)
    app.draw()                                                   # an empty list says so
    _key(app, pygame.K_LEFTBRACKET)
    _key(app, pygame.K_ESCAPE)
    assert app.state == cv.CODE


def test_the_result_screens_draw_and_go_back_to_the_slot(app):
    import code_validator as cv
    _key(app, pygame.K_RETURN)
    code = code_for('duck_hatched')
    cases = [(code[:-1] + ('X' if code[-1] != 'X' else 'Y'), 'fake'), ('DEV-' + code, 'dev'),
             (code_for('duck_hatched', 'Corwin'), 'fake')]
    core.validate('Fianna', entry(code))                         # so the real one is already claimed
    cases.append((code, 'already'))
    for text, status in cases:
        app.raw = ''
        for ch in text:
            _key(app, 0, ch)
        _key(app, pygame.K_RETURN)
        _run(app, 4.5)
        assert app.state == cv.RESULT and app.verdict['status'] == status
        app.draw()
        _key(app, pygame.K_SPACE)
        assert app.state == cv.CODE and app.raw == ''
    assert len(dadlib.ledger()) == 1


def _type(app, text):
    for ch in text:
        _key(app, 0, ch)


def _hit(app, action):
    """Click what the last frame drew for ``action``."""
    rect = next(r for r, a in app.hits if a == action)
    app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))


def test_the_code_screen_asks_for_the_seeker_name_and_the_code(app):
    import code_validator as cv
    _key(app, pygame.K_RIGHT)
    _key(app, pygame.K_RETURN)                                   # Corwin
    assert app.state == cv.CODE and app.name == 'Corwin'
    assert app.seeker_name == 'Corwin' and app.field == 'code'   # nothing remembered: his own name
    _key(app, pygame.K_UP)
    assert app.field == 'name'
    _key(app, pygame.K_BACKSPACE, mod=pygame.KMOD_CTRL)
    _type(app, 'Xyzm')                                          # M is a letter here too
    _key(app, pygame.K_BACKSPACE)
    assert app.seeker_name == 'Xyz' and app.entry.empty         # the keys went to the name
    app.draw()
    _hit(app, ('field', 'code'))                                 # a click moves to the code
    assert app.field == 'code'
    app.draw()
    _hit(app, ('field', 'name'))
    assert app.field == 'name'
    _key(app, pygame.K_DOWN)
    code = code_for('duck_hatched', 'Xyz')
    _type(app, code)
    assert app.entry.code == code and app.seeker_name == 'Xyz'
    app.draw()
    _key(app, pygame.K_RETURN)
    _run(app, 4.5)
    assert app.state == cv.PARTY and app.verdict['kid'] == 'Corwin'
    assert [(r['seeker'], r['achievement']) for r in dadlib.ledger()] == [('Corwin', 'duck_hatched')]
    app.draw()
    # The kid card says what he plays as, and the name is filled in for him next time.
    _key(app, pygame.K_ESCAPE)
    assert app.state == cv.KIDS and app._plays_as['corwin'] == 'Xyz'
    app.draw()
    _key(app, pygame.K_LEFT)
    _key(app, pygame.K_RETURN)                                   # Fianna: her own name
    assert app.name == 'Fianna' and app.seeker_name == 'Fianna'
    _key(app, pygame.K_ESCAPE)
    _key(app, pygame.K_RIGHT)
    _key(app, pygame.K_RETURN)
    assert app.name == 'Corwin' and app.seeker_name == 'Xyz' and app.field == 'code'


def test_a_code_needs_the_seeker_name_it_was_earned_under(app):
    import code_validator as cv
    _key(app, pygame.K_RETURN)                                   # Fianna, checked as Fianna
    code = code_for('duck_hatched', 'Wren')
    _type(app, code)
    _key(app, pygame.K_RETURN)
    _run(app, 4.5)
    assert app.state == cv.RESULT and app.verdict['status'] == 'fake'
    app.draw()
    _key(app, pygame.K_RETURN)                                   # back to fix it: the code stays
    assert app.state == cv.CODE and app.entry.code == code and 'Up' in app.line
    _key(app, pygame.K_UP)
    _key(app, pygame.K_BACKSPACE, mod=pygame.KMOD_CTRL)
    _key(app, pygame.K_RETURN)                                   # no name: refused, on the name
    assert app.state == cv.CODE and app.field == 'name' and 'Seeker name' in app.line
    _type(app, 'Wren')
    _key(app, pygame.K_RETURN)
    _run(app, 4.5)
    assert app.state == cv.PARTY and dadlib.redeemed('Fianna', 'duck_hatched')
    assert core.seeker_names('Fianna') == ['Wren']


def test_a_duplicate_lands_amber_and_is_given_only_on_enter(app):
    import code_validator as cv
    code = code_for('duck_hatched', 'Fianna')
    core.validate('Fianna', entry(code))                         # Fianna had it first
    _key(app, pygame.K_RIGHT)
    _key(app, pygame.K_RETURN)                                   # Corwin
    _key(app, pygame.K_UP)
    _key(app, pygame.K_BACKSPACE, mod=pygame.KMOD_CTRL)
    _type(app, 'Fianna')
    _key(app, pygame.K_DOWN)
    _type(app, code)
    _key(app, pygame.K_RETURN)
    _run(app, 4.5)
    assert app.state == cv.RESULT and app.verdict['status'] == 'duplicate'
    assert app._duplicate() and len(set(app.plan.outcome)) == 1
    app.draw()
    assert 'anyway' in app._result_hint()
    _key(app, pygame.K_ESCAPE)                                   # back: nothing recorded
    assert app.state == cv.CODE and app.raw == '' and len(dadlib.ledger()) == 1
    _type(app, code)
    _key(app, pygame.K_RETURN)
    _run(app, 4.5)
    assert app.verdict['status'] == 'duplicate'
    _key(app, pygame.K_RETURN)                                   # give it to Corwin anyway
    assert app.state == cv.PARTY and dadlib.redeemed('Corwin', 'duck_hatched')
    assert len(dadlib.ledger()) == 2
    _run(app, 1.0)
    app.draw()


def test_skipping_the_spin_lands_the_same_answer(app):
    import code_validator as cv
    _key(app, pygame.K_RETURN)
    for ch in code_for('questions_100'):
        _key(app, 0, ch)
    _key(app, pygame.K_RETURN)
    _run(app, 0.2)
    _key(app, pygame.K_ESCAPE)
    _run(app, 1.0)
    assert app.state == cv.PARTY
    assert [app.plan.on_payline(k, app.spin_t) for k in range(3)] == ['questions_100'] * 3


def test_kid_screen_add_remove_and_no_key(app):
    import code_validator as cv
    _key(app, pygame.K_EQUALS, '=')                              # the "+" card
    for ch in 'robyn':
        _key(app, 0, ch)
    app.draw()
    _key(app, pygame.K_RETURN)
    assert app.kids == ['Fianna', 'Corwin', 'Robyn'] and core.load_kids() == app.kids
    app.draw()
    _key(app, pygame.K_DELETE)
    app.draw()
    _key(app, pygame.K_y)
    assert app.kids == ['Fianna', 'Corwin']
    app.key_ok = False
    app.pick = 0
    _key(app, pygame.K_RETURN)
    app.draw()
    assert app.state == cv.KIDS                                   # nothing to check codes with
    _key(app, pygame.K_t)
    assert app.state == cv.TRACKER                                # the tracker still opens
    app.draw()


def test_the_sounds_are_built_and_m_mutes_except_in_a_code(ui_theme_isolated):
    import code_validator
    import seeker_screen
    pygame.init()
    a = code_validator.App(pygame.display.set_mode((1280, 800)), sound=True, rng=random.Random(2))
    try:
        if not a.fx.sounds:
            pytest.skip("no audio device here")
        for name in ('key', 'refuse', 'lever', 'ratchet', 'tick', 'reel_stop', 'nope', 'chime',
                     'achievement', 'secret', 'stamp', 'coins'):
            snd = a.fx.sounds[name]
            assert snd.get_length() <= 1.2, name             # nothing long
        assert a.fx.on
        _key(a, pygame.K_m, 'm')                             # the kid screen: M is the sound switch
        assert not a.fx.on and core.load_settings() == {'sound': False}
        _key(a, pygame.K_RETURN)
        _key(a, pygame.K_m, 'm')                             # the code: M is a letter
        assert a.entry.word == 'M' and not a.fx.on
        _key(a, pygame.K_F5)
        assert a.fx.on and core.load_settings() == {'sound': True}
        again = code_validator.Sfx(True, on=core.load_settings()['sound'])
        assert again.on
    finally:
        seeker_screen.clear_cache()


def test_a_short_code_does_not_pull_the_lever(app):
    import code_validator as cv
    _key(app, pygame.K_RETURN)
    for ch in 'DOOM-AB':
        _key(app, 0, ch)
    _key(app, pygame.K_RETURN)
    assert app.state == cv.CODE and 'whole code' in app.line
    _key(app, pygame.K_BACKSPACE)
    assert app.entry.code == 'DOOM-A'
    app.draw()


# -- code words of any length (Brandon, 2026-11-17: "it only accepts 4 letters to start but some
#    codes are HUNDRED-1234-5678"; the empty slot showed four ghost boxes spelling WORD) -----------

def test_every_code_word_types_whole_with_or_without_dashes():
    import validator_core as vc
    words = vc.code_words()
    assert min(map(len, words)) <= 3 and max(map(len, words)) >= 12       # MOO ... HUNDREDTRIPS
    rng = random.Random(3)
    for w in sorted(words):
        chars = ''.join(rng.choice(sc.ALPHABET) for _ in range(8))
        for sep in ('-', ''):
            raw = ''
            for ch in w + sep + chars[:4] + sep + chars[4:]:
                raw, _why = vc.type_key(raw, ch, words)
            raw = vc.complete_reading(raw, words) or raw      # what Enter does with a dashless code
            e = vc.parse_entry(raw, words)
            assert e.complete and e.code == f'{w}-{chars[:4]}-{chars[4:]}', (w, sep, raw, e.code)


def test_a_shorter_word_is_read_when_only_it_makes_a_whole_code():
    import validator_core as vc
    words = vc.code_words()
    assert {'TABLE', 'TABLET'} <= words                                   # TABLE with a code starting T
    assert vc.complete_reading('TABLET1G3JGM1', words) == 'TABLE-T1G3JGM1'
    assert vc.complete_reading('TABLE-T1G3JGM1', words) is None           # a dash says where the word ends
    assert vc.complete_reading('HUND', words) is None


def test_the_empty_word_says_any_length():
    src = (ROOT / 'tools' / 'dad' / 'code_validator.py').read_text(encoding='utf-8')
    assert '"ANY LENGTH"' in src and 'Word (any length)' in src
    assert "'WORD'[i]" not in src                                         # no four ghost boxes
    import validator_core as vc
    title, lines = vc.result_lines({'status': 'fake', 'seeker': 'Fianna', 'why': 'short', 'code': 'HUN'})
    assert any('any length' in ln for ln in lines)
