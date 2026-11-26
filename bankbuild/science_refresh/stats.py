"""Information-only measures for the refresh (never gates; Brandon, 2026-11-25).

Words per stem, Flesch-Kincaid reading grade, and the share of stems that open
on a named person, a year or a place (the 11-16 audit's "story share").
"""
from __future__ import annotations

import re
import statistics

_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
_SENT = re.compile(r'[.!?]+(?=\s|$)')


def syllables(word: str) -> int:
    w = word.lower().strip("'")
    if len(w) <= 3:
        return 1
    w = re.sub(r'(?:[^laeiouy]es|ed|[^laeiouy]e)$', '', w)
    w = re.sub(r'^y', '', w)
    return max(1, len(re.findall(r'[aeiouy]{1,2}', w)))


def fk_grade(text: str) -> float:
    ws = _WORD.findall(text or '')
    if not ws:
        return 0.0
    sents = max(1, len(_SENT.findall(text)))
    syl = sum(syllables(w) for w in ws)
    return 0.39 * len(ws) / sents + 11.8 * syl / len(ws) - 15.59


_STORY = re.compile(r"^(?:In |On |By |During )?(?:\d{3,4}\b|[A-Z][a-z]+ [A-Z][a-z]+|[A-Z][a-z]+'s )")


def opens_on_story(stem: str) -> bool:
    """A rough read of the audit's measure: a name, a year or a place first."""
    first = (stem or '').split('.')[0]
    return bool(_STORY.match(stem or '')) or bool(re.match(r'^[A-Z][a-z]+ (?:[A-Z]\.|von|de|van) ', first))


def summarise(qs: list[dict]) -> dict:
    if not qs:
        return {'n': 0}
    words = [len(q['question'].split()) for q in qs]
    grades = [fk_grade(q['question']) for q in qs]
    ans = [len(q['answer'].split()) for q in qs]
    return {'n': len(qs),
            'stem_words_median': statistics.median(words),
            'stem_words_range': (min(words), max(words)),
            'reading_grade_median': round(statistics.median(grades), 1),
            'answer_words_median': statistics.median(ans),
            'story_share': round(100 * sum(opens_on_story(q['question']) for q in qs) / len(qs))}
