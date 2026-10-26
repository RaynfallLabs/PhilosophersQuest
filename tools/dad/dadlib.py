"""Shared helpers for Dad's tools (make_key, check_code, codebook).

Everything Dad keeps lives OUTSIDE the repo, in Documents\\PQ_Dad\\ (the
redeemed-codes ledger and the printed Codebooks), because the repo is public
and a Codebook lists every code. The key itself is src/_dad_key.py
(gitignored); seeker_codes reads it the same way the game does.
"""
import csv
import json
import os
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
