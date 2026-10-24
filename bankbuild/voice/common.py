"""Shared helpers for the house-voice pass (Brandon 2026-10-24).

Every ladder is read once: its same-fact twins are MERGED from the
questions it already has (no new facts), and every stem is told in the
house voice (docs/quiz/HOUSE_VOICE.md, the Chronicler). Keys never change.
The cards stay; their `teaches` entries follow the new stems.

Working files live in `_voice/<subject>/` (scratch, untracked):
  bNNN_in.json        writer packet: ladders with card, questions, lint, twins
  bNNN_changes.json   writer output, in bankbuild/cards/stage.py's format
  bNNN_notes.json     writer notes: merges, unchanged stems, not-twins, errors
  bNNN_judge_in.json  judge packet: card, new stems, shuffled choices, old stems
  bNNN_judge.json     judge output
  bNNN_score.json     scored result per topic (cumulative across rounds)
  status.json         topics done, batches and their state
"""
from __future__ import annotations

import json
from pathlib import Path

from bankbuild.cards.common import ROOT, read_json, stem_hash, write_json

WORK = ROOT / '_voice'
TWINS = ROOT / 'data' / 'question_twins.json'
SUBJECTS = ROOT / 'bankbuild' / 'subjects'

# The order the banks go through the pass (how often each is asked in play).
ORDER = ('philosophy', 'animal', 'geography', 'cooking', 'history', 'economics',
         'science', 'theology', 'trivia', 'ai', 'grammar')


def bpath(subject: str, batch: int, kind: str) -> Path:
    return WORK / subject / f'b{batch:03d}_{kind}.json'


def twin_groups(subject: str) -> list[list[str]]:
    """The subject's same-fact twin groups (lists of stem hashes)."""
    if not TWINS.exists():
        return []
    data = json.loads(TWINS.read_text(encoding='utf-8'))
    return [[h for h, _tier in g] for g in data.get('groups', {}).get(subject, [])]


def gid(group: list[str]) -> str:
    """A stable name for a twin group: its smallest hash."""
    return 'tw-' + min(group)


def status(subject: str) -> dict:
    p = WORK / subject / 'status.json'
    st = read_json(p) if p.exists() else {}
    st.setdefault('done', [])
    st.setdefault('batches', {})
    return st


def save_status(subject: str, st: dict) -> None:
    write_json(WORK / subject / 'status.json', st)


def subject_config(subject: str) -> dict:
    """voice_rule, tier_note and framing from bankbuild/subjects/<subject>.json;
    for a subject without one (ai, trivia), a pointer to its subject doc."""
    p = SUBJECTS / f'{subject}.json'
    if p.exists():
        d = json.loads(p.read_text(encoding='utf-8'))
        return {k: d.get(k, '') for k in ('voice_rule', 'tier_note', 'framing')}
    return {'voice_rule': f'See docs/quiz/subjects/{subject}.md and '
                          f'docs/quiz/{subject}_strategies.md.',
            'tier_note': f'See docs/quiz/subjects/{subject}.md.', 'framing': ''}


def load_changes(subject: str, batch: int) -> dict:
    p = bpath(subject, batch, 'changes')
    return read_json(p) if p.exists() else {}


def load_notes(subject: str, batch: int) -> dict:
    p = bpath(subject, batch, 'notes')
    n = read_json(p) if p.exists() else {}
    for k in ('merges', 'unchanged', 'not_twins', 'question_errors'):
        n.setdefault(k, [])
    return n


__all__ = ['WORK', 'TWINS', 'ORDER', 'bpath', 'twin_groups', 'gid', 'status', 'save_status',
           'subject_config', 'load_changes', 'load_notes', 'read_json', 'write_json', 'stem_hash']
