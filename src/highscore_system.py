"""
highscore_system.py -- Persistent high score table for Philosopher's Quest.

Stores up to MAX_ENTRIES runs in a JSON file next to the src/ directory.
Each entry: {name, score, grade, level, kills, turns, date, victory}
"""
from __future__ import annotations

import json
import os
from datetime import datetime

MAX_ENTRIES = 100

def _score_file_path() -> str:
    # save_dir() is the project root in dev (where this file always lived)
    # and the per-user data dir when frozen.
    from paths import save_dir
    return os.path.join(save_dir(), 'highscores.json')

_SCORE_FILE = _score_file_path()


def _load() -> list[dict]:
    try:
        with open(_SCORE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            # Only rows that are a real entry: the table, the welcome screen
            # and the death screen all trust every field, and one bad row
            # stopped the game from opening.
            good = []
            for e in data:
                if isinstance(e, dict) and isinstance(e.get('score'), (int, float)) \
                        and not isinstance(e.get('score'), bool):
                    e.setdefault('name', '?')
                    for k in ('level', 'kills', 'turns'):
                        if not isinstance(e.get(k), (int, float)):
                            e[k] = 0
                    e.setdefault('grade', '')
                    e.setdefault('victory', False)
                    e.setdefault('date', '')
                    e['name'] = str(e['name'])
                    good.append(e)
            return good
    except (OSError, ValueError):
        # ValueError covers a malformed table AND bytes that are not UTF-8
        # (UnicodeDecodeError): either used to escape and break the end
        # screen on every frame.
        pass
    return []


def _save(entries: list[dict]) -> None:
    # Written beside the table and swapped in, so a kill mid-write cannot
    # leave half a file (which read as "no scores").
    try:
        tmp = _SCORE_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2)
        os.replace(tmp, _SCORE_FILE)
    except OSError:
        pass


def add_score(
    name: str,
    score: int,
    grade: str,
    level: int,
    kills: int,
    turns: int,
    victory: bool,
) -> int:
    """
    Insert a new score entry, keep top MAX_ENTRIES by score.
    Returns the rank (1-based) of the new entry, or 0 if it didn't make the table.
    """
    entries = _load()
    entry = {
        'name':    name,
        'score':   score,
        'grade':   grade,
        'level':   level,
        'kills':   kills,
        'turns':   turns,
        'victory': victory,
        'date':    datetime.now().strftime('%Y-%m-%d'),
    }
    entries.append(entry)
    entries.sort(key=lambda e: e.get('score', 0), reverse=True)
    entries = entries[:MAX_ENTRIES]
    _save(entries)
    # Find rank of this entry (by score value -- may not be unique)
    for i, e in enumerate(entries):
        if e is entry or (e['score'] == score and e['name'] == name and e['date'] == entry['date']):
            return i + 1
    return 0


def get_scores() -> list[dict]:
    """Return the current top-score list (sorted descending by score)."""
    return _load()


def get_top(n: int = 5) -> list[dict]:
    """Return top N entries."""
    return _load()[:n]
