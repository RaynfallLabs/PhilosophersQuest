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
    import sys
    if getattr(sys, 'frozen', False):
        from paths import save_dir
        return os.path.join(save_dir(), 'highscores.json')
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'highscores.json'
    )

_SCORE_FILE = _score_file_path()


def _load() -> list[dict]:
    try:
        with open(_SCORE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return []


def _save(entries: list[dict]) -> None:
    try:
        with open(_SCORE_FILE, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2)
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
