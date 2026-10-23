"""Topic cards outside the quiz: what a card is called, what it says, and
which topics the hero has met and read.

Every quiz question belongs to a topic, and every topic has a card in
data/question_contexts/<subject>.json: the card C opens during a quiz
(teaching cards, ruling 2026-10-18). The quiz engine serves the card for the
question in hand. This module serves the places that show a card with no
quiz running: the missed-question review (C), the Encyclopedia's Lore Codex
(m) and Study Mode's By Topic.

The hero's record is two sets of "subject|topic" keys on the Player:
`topics_met` (a question from the topic was asked) and `topics_read` (its
card was opened). Saves from before 2026-10-23 have neither; both read as
empty.
"""
from __future__ import annotations

import hashlib
import json

from naming import proper_name
from paths import data_path

_SUBJECT_LABELS = {'ai': 'AI', 'animal': 'Animals'}

_cards: dict[str, dict] = {}
_questions: dict[str, list] = {}


def _load_json(*parts):
    try:
        with open(data_path(*parts), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def cards(subject: str) -> dict:
    """The subject's card file, {topic: {"context_blurb", "title", ...}}."""
    if subject not in _cards:
        data = _load_json('data', 'question_contexts', f'{subject}.json')
        _cards[subject] = data if isinstance(data, dict) else {}
    return _cards[subject]


def questions(subject: str) -> list:
    if subject not in _questions:
        data = _load_json('data', 'questions', f'{subject}.json')
        _questions[subject] = data if isinstance(data, list) else []
    return _questions[subject]


def subject_label(subject: str) -> str:
    return _SUBJECT_LABELS.get(subject, proper_name(str(subject).replace('_', ' ')))


def title(subject: str, topic: str | None) -> str:
    """The card's title; for a topic without one, its id made readable."""
    entry = cards(subject).get(topic) if topic else None
    if isinstance(entry, dict) and str(entry.get('title', '')).strip():
        return entry['title'].strip()
    return proper_name(str(topic or '').replace('-', ' ').strip()) or 'Untitled'


def card(subject: str, topic: str | None) -> str | None:
    """The card's text, or None when the topic has no card."""
    entry = cards(subject).get(topic) if topic else None
    text = entry.get('context_blurb') if isinstance(entry, dict) else entry
    return text.strip() if isinstance(text, str) and text.strip() else None


def topics(subject: str) -> list[tuple[str, str]]:
    """(topic, title) for every topic that has a card, in title order."""
    out = [(t, title(subject, t)) for t in cards(subject) if card(subject, t)]
    return sorted(out, key=lambda p: p[1].lower())


def ladder(subject: str, topic: str) -> list[dict]:
    """The topic's questions, easiest tier first (stable within a tier)."""
    qs = [q for q in questions(subject) if q.get('topic') == topic]
    return sorted(qs, key=lambda q: int(q.get('tier', 1) or 1))


def topic_for(subject: str, question_text: str) -> str | None:
    """The topic of the question with this stem. Missed questions recorded
    before the cards shipped carry no topic; this finds it."""
    stem = str(question_text or '').strip()
    for q in questions(subject):
        if str(q.get('question', '')).strip() == stem:
            return q.get('topic')
    return None


def missed_topic(entry: dict | None) -> tuple[str, str | None]:
    """(subject, topic) of a missed-question entry (Game.missed_questions)."""
    if not entry:
        return '', None
    subject = entry.get('subject', '')
    return subject, entry.get('topic') or topic_for(subject, entry.get('question', ''))


def lesson(subject: str, q: dict) -> str | None:
    """The one card sentence that teaches this question (its `teaches`
    entry), as the quiz engine's lesson_for gives it."""
    entry = cards(subject).get(q.get('topic'))
    teaches = entry.get('teaches') if isinstance(entry, dict) else None
    stem = str(q.get('question', '')).strip()
    if isinstance(teaches, dict) and stem:
        line = teaches.get(hashlib.sha1(stem.encode('utf-8')).hexdigest()[:10])
        if isinstance(line, str) and line.strip():
            return line.strip()
    return None


def _key(subject: str, topic: str) -> str:
    return f'{subject}|{topic}'


def _record(player, attr: str) -> set:
    s = getattr(player, attr, None)
    if not isinstance(s, set):
        s = set(s or ())
        try:
            setattr(player, attr, s)
        except AttributeError:
            pass
    return s


def note_met(player, subject: str, topic: str | None) -> None:
    if player is not None and subject and topic and card(subject, topic):
        _record(player, 'topics_met').add(_key(subject, topic))


def note_read(player, subject: str, topic: str | None) -> None:
    if player is not None and subject and topic and card(subject, topic):
        _record(player, 'topics_met').add(_key(subject, topic))
        _record(player, 'topics_read').add(_key(subject, topic))


def has_read(player, subject: str, topic: str) -> bool:
    return _key(subject, topic) in (getattr(player, 'topics_read', None) or ())


def codex_entries(player) -> list[dict]:
    """The Lore Codex: one entry per topic the hero has met, by subject and
    then title. Each carries `_subject`, `_topic` and `_read`."""
    out = []
    for k in getattr(player, 'topics_met', None) or ():
        subject, _, topic = str(k).partition('|')
        if not card(subject, topic):
            continue                     # a topic retired since (split, merged)
        out.append({'_id': k, 'name': title(subject, topic), '_subject': subject,
                    '_topic': topic, '_read': has_read(player, subject, topic)})
    return sorted(out, key=lambda e: (subject_label(e['_subject']).lower(), e['name'].lower()))
