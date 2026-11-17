"""Shared helpers for Dad's tools (make_key, check_code, codebook, the Code
Validator).

Everything Dad keeps lives OUTSIDE the repo, in Documents\\PQ_Dad\\ (the
redeemed-codes ledger, the kids list and the printed Codebooks), because the
repo is public and a Codebook lists every code. The key itself is
src/_dad_key.py (gitignored); seeker_codes reads it the same way the game does.

The ledger's ``seeker`` column is who the badge was given to: the Seeker name
the code was checked with, or the kid it was given to (the Code Validator,
check_code.py ``--for``). A code is made for the Seeker name the child plays
under, which need not be the kid's own name.
"""
import calendar
import csv
import json
import os
import re
import sys
import time

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import seeker_codes  # noqa: E402

KEY_FILE = os.path.join(SRC, '_dad_key.py')
LEDGER_FIELDS = ('date', 'seeker', 'code', 'achievement', 'name')

# Tests point this at a temp dir.
_DAD_DIR_OVERRIDE = None


def dad_dir() -> str:
    d = _DAD_DIR_OVERRIDE or os.path.join(os.path.expanduser('~'), 'Documents', 'PQ_Dad')
    os.makedirs(d, exist_ok=True)
    return d


def achievements(path: str | None = None) -> list[dict]:
    path = path or os.path.join(ROOT, 'data', 'achievements.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)['achievements']


def categories(path: str | None = None) -> dict:
    path = path or os.path.join(ROOT, 'data', 'achievements.json')
    with open(path, encoding='utf-8') as f:
        return {c['id']: c['name'] for c in json.load(f)['categories']}


def notes() -> dict:
    """How each achievement unlocks, in plain words (Dad's eyes only; kept
    out of data/achievements.json because that file ships with the game)."""
    try:
        with open(os.path.join(os.path.dirname(__file__), 'achievement_notes.json'),
                  encoding='utf-8') as f:
            return json.load(f).get('notes', {})
    except (OSError, ValueError):
        return {}


def ledger_path() -> str:
    return os.path.join(dad_dir(), 'redeemed.csv')


def ledger() -> list[dict]:
    try:
        with open(ledger_path(), newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def redeemed(seeker: str, achievement: str) -> dict | None:
    norm = seeker_codes.normalise_name(seeker)
    for row in ledger():
        if (seeker_codes.normalise_name(row.get('seeker', '')) == norm
                and row.get('achievement') == achievement):
            return row
    return None


def code_key(code) -> str:
    """A code as the ledger compares it: WORD-XXXX-XXXX whatever its case,
    spacing, dashes or O/I/L slips (seeker_codes.split_code); text that is
    no code at all, as typed, upper case, letters and digits only."""
    parts = seeker_codes.split_code(code)
    if parts is None:
        return re.sub(r'[^A-Z0-9]', '', str(code or '').upper())
    word, chars = parts
    return f'{word}-{chars[:4]}-{chars[4:]}'


def find_code(code) -> list[dict]:
    """Every ledger row with this exact code (compared by code_key), oldest
    first. Rows from before the ledger wrote codes tidily read the same."""
    want = code_key(code)
    if not want:
        return []
    return [row for row in ledger() if code_key(row.get('code', '')) == want]


def nice_date(stamp, short: bool = False) -> str:
    """'2026-11-17' -> '17 November 2026' ('17 Nov 2026' when ``short``; the
    text as written if it will not read)."""
    try:
        y, m, d = str(stamp)[:10].split('-')
        month = (calendar.month_abbr if short else calendar.month_name)[int(m)]
        return f"{int(d)} {month} {int(y)}"
    except (ValueError, IndexError):
        return str(stamp or '')


def record(seeker: str, code: str, aid: str, name: str):
    new = not os.path.exists(ledger_path())
    with open(ledger_path(), 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
        if new:
            w.writeheader()
        w.writerow({'date': time.strftime('%Y-%m-%d'), 'seeker': seeker, 'code': code,
                    'achievement': aid, 'name': name})


def require_real_key():
    if seeker_codes.is_dev():
        sys.exit("No key found (src/_dad_key.py). Run:  py tools/dad/make_key.py")
