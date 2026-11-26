"""Shared paths and loaders for the science refresh (2026-11-25).

The refresh replaces the science bank with 1,000 questions, exactly 200 a
tier, built in one-tier UNITS drawn from a grade-by-grade curriculum map
(T1 = 5th grade ... T5 = 9th grade). Working state lives here, one folder
per unit, so the build resumes after a usage wall:

    bankbuild/science_refresh/
        config.json            the refresh's subject rules (tiers = grades)
        curriculum_map.json    the grade-by-grade map; every unit names a line
        units.json             the unit list (id, title, tier, strand, lines, scope)
        units/<id>/facts.md    the sourced fact sheet
        units/<id>/draft.json  the author's questions
        units/<id>/gates.json  the mechanical gates' findings
        units/<id>/judge.json  the adversarial judge's verdicts
        units/<id>/factcheck.json  the web fact-check's verdicts
        units/<id>/final.json  the questions after the one revision and drops
        units/<id>/card.json   the teaching card, once it passed gate + coverage
        units/<id>/state.json  which steps are done
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
UNITS_DIR = HERE / 'units'
SUBJECT = 'science'
TIER_GRADE = {1: 5, 2: 6, 3: 7, 4: 8, 5: 9}
STRANDS = ('physical', 'life', 'earth', 'method')
STRAND_LETTER = {'physical': 'P', 'life': 'L', 'earth': 'E', 'method': 'M'}

# The order a unit moves through (plan section 4). `state.json` records each.
STEPS = ('researched', 'authored', 'gated', 'judged', 'factchecked', 'revised',
         'rechecked', 'carded', 'covered')


def read_json(p: Path, default=None):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except FileNotFoundError:
        return default


def write_json(p: Path, obj) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def load_units() -> list[dict]:
    data = read_json(HERE / 'units.json', {'units': []})
    return data['units'] if isinstance(data, dict) else data


def unit_by_id(uid: str) -> dict | None:
    return next((u for u in load_units() if u['id'] == uid), None)


def map_lines() -> dict[str, dict]:
    """line id -> line (with its grade), from curriculum_map.json."""
    cmap = read_json(HERE / 'curriculum_map.json', {'grades': {}})
    out = {}
    for grade, g in (cmap.get('grades') or {}).items():
        for line in g.get('lines', []):
            out[line['id']] = dict(line, grade=int(grade))
    return out


def unit_questions(uid: str, prefer: tuple[str, ...] = ('final', 'draft')) -> tuple[str, list[dict]]:
    """(which file, questions) for a unit: its final questions if it has them."""
    for kind in prefer:
        data = read_json(UNITS_DIR / uid / f'{kind}.json')
        if data:
            qs = data['questions'] if isinstance(data, dict) else data
            return kind, qs
    return '', []


def state(uid: str) -> dict:
    return read_json(UNITS_DIR / uid / 'state.json', {}) or {}


def mark(uid: str, step: str, **info) -> None:
    st = state(uid)
    st[step] = info or True
    write_json(UNITS_DIR / uid / 'state.json', st)
