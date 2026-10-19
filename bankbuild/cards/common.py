"""Shared helpers for the teaching context-card rollout (2026-10-18).

Ruling (Brandon, 2026-10-18): the C-key context card TEACHES every rung of
its ladder, so a kid willing to read can learn instead of guessing. See
NEXT_STEPS_REVIEW_2026_10_18.md section 1 and bankbuild/PIPELINE.md §16.

Working files live in `_cards/<subject>/` (scratch, untracked):
  bNNN_in.json     author packet: topics with full questions + contexts
  bNNN_cards.json  author output: {topic: {"context_blurb", "teaches"}}
  bNNN_judge_in.json  judge packet: cards + stems + shuffled choices, no keys
  bNNN_judge.json  judge output: {topic: {hash: {"pick", "quote"}}}
  bNNN_score.json  scored result per topic (pass / failing hashes)
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QDIR = ROOT / 'data' / 'questions'
CDIR = ROOT / 'data' / 'question_contexts'
WORK = ROOT / '_cards'

SOURCE_RE = re.compile(r'\s*Source:.*$', re.IGNORECASE | re.DOTALL)


def stem_hash(stem: str) -> str:
    """First 10 hex chars of SHA-1 of the stem text (the `teaches` key)."""
    return hashlib.sha1(stem.strip().encode('utf-8')).hexdigest()[:10]


def load_questions(subject: str) -> list[dict]:
    data = json.loads((QDIR / f'{subject}.json').read_text(encoding='utf-8'))
    if isinstance(data, dict):
        data = data.get('questions', list(data.values()))
    return data


def load_cards(subject: str) -> dict:
    p = CDIR / f'{subject}.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def ladders(subject: str) -> dict[str, list[dict]]:
    """topic -> questions, in tier order (stable within a tier)."""
    out: dict[str, list[dict]] = {}
    for q in load_questions(subject):
        t = q.get('topic')
        if t:
            out.setdefault(t, []).append(q)
    for t in out:
        out[t].sort(key=lambda q: int(q.get('tier', 1)))
    return out


def norm(text: str) -> str:
    text = text.lower().replace('’', "'").replace('‘', "'")
    text = re.sub(r'[—–\-]', ' ', text)
    text = re.sub(r"[^a-z0-9' ]+", ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def words(text: str) -> list[str]:
    return norm(text).split()


def target_words(n_questions: int) -> tuple[int, int, int]:
    """(minimum, target, hard cap) word counts for a card of n questions."""
    target = 60 + 40 * n_questions
    lo = max(150, min(560, int(round(0.75 * target))))
    return lo, max(150, target), 750


def strip_source(context: str) -> str:
    return SOURCE_RE.sub('', context or '').strip()


def shuffled_choices(q: dict) -> list[str]:
    """Deterministic shuffle so the judge never sees the key in slot one."""
    ch = list(q.get('choices') or [])
    random.Random(stem_hash(q['question'])).shuffle(ch)
    return ch


def batch_path(subject: str, batch: int, kind: str) -> Path:
    return WORK / subject / f'b{batch:03d}_{kind}.json'


def read_json(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding='utf-8')
