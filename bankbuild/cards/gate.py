"""Deterministic gate for teaching context cards.

    py -m bankbuild.cards.gate <subject> <batch>          # check bNNN_cards.json
    py -m bankbuild.cards.gate <subject> <batch> --quiet  # only the summary line

A card FAILS when it:
  * is shorter than its minimum or longer than 750 words;
  * shares a run of 6 or more words with any stem in its ladder;
  * contains a whole choice string of more than 4 words (keyed or not);
  * names 3 or more of one question's choices;
  * carries "Source:", a URL, author notes, or quiz jargon;
  * says "the answer is" / "correct answer";
  * has a `teaches` map that misses a question, or whose sentence is not
    found word for word in the card.
Exit code 1 if any card fails.
"""
from __future__ import annotations

import re
import sys

from bankbuild.cards.common import batch_path, norm, read_json, words

AUTHOR_VOICE = (
    'this ladder', 'ladder passes', 'the ladder you', 'sub-strand', 'geek-dad',
    'spoiler-ok', 'stance doc', 'no verdict crowned', 'the kid should', 'this topic',
    'the topic walks', 'the questions below', 'the project treats', "the bank's rule",
    'this entry', 'this card', 'the card ',
)
JARGON = re.compile(
    r"\b(distractors?|keyed answer|this rung|each rung|this ladder|the stem|"
    r"tier [1-5]|question [1-9])\b", re.I)
GIVEAWAY = re.compile(r"\b(the (correct )?answer is|correct answer|right answer)\b", re.I)
URL = re.compile(r"(https?://|www\.|source:)", re.I)


def _ngrams(ws: list[str], n: int) -> set[tuple]:
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def _contains(hay: str, needle: str) -> bool:
    n = norm(needle)
    return bool(n) and re.search(r'(?<![a-z0-9])' + re.escape(n) + r'(?![a-z0-9])', hay) is not None


def check_card(pkt: dict, card: dict) -> list[str]:
    errs: list[str] = []
    text = (card or {}).get('context_blurb', '') or ''
    teaches = (card or {}).get('teaches', {}) or {}
    if not text.strip():
        return ['empty card']
    ws = words(text)
    lo, _target, cap = pkt['length']['min_words'], pkt['length']['target_words'], pkt['length']['max_words']
    if len(ws) < lo:
        errs.append(f'too short: {len(ws)} words (min {lo})')
    if len(ws) > cap:
        errs.append(f'too long: {len(ws)} words (max {cap})')
    hay = ' '.join(ws)
    card_6 = _ngrams(ws, 6)
    low = text.lower()
    for phrase in AUTHOR_VOICE:
        if phrase in low:
            errs.append(f'author note: "{phrase.strip()}"')
    m = JARGON.search(text)
    if m:
        errs.append(f'quiz jargon: "{m.group(0)}"')
    if GIVEAWAY.search(text):
        errs.append('says "the answer is"')
    if URL.search(text):
        errs.append('source line or URL')
    for q in pkt['questions']:
        h = q['hash']
        shared = card_6 & _ngrams(words(q['stem']), 6)
        if shared:
            errs.append(f'{h}: copies 6+ words of the stem: "{" ".join(sorted(shared)[0])}"')
        named = 0
        for ch in q['choices']:
            if len(words(ch)) > 4 and _contains(hay, ch):
                errs.append(f'{h}: contains a whole choice (>4 words): "{ch}"')
            if _contains(hay, ch):
                named += 1
        if named >= 3:
            errs.append(f'{h}: names {named} of its 4 choices')
        sent = teaches.get(h)
        if not sent or not str(sent).strip():
            errs.append(f'{h}: no teaches sentence')
        elif norm(sent) not in hay:
            errs.append(f'{h}: teaches sentence not found word for word in the card')
    extra = set(teaches) - {q['hash'] for q in pkt['questions']}
    if extra:
        errs.append(f'teaches has unknown hashes: {sorted(extra)[:3]}')
    return errs


def gate_batch(subject: str, batch: int) -> dict[str, list[str]]:
    pkt = read_json(batch_path(subject, batch, 'in'))
    cards = read_json(batch_path(subject, batch, 'cards'))
    res = {}
    for p in pkt['topics']:
        res[p['topic']] = check_card(p, cards.get(p['topic']))
    return res


def main() -> None:
    subject, batch = sys.argv[1], int(sys.argv[2])
    quiet = '--quiet' in sys.argv
    res = gate_batch(subject, batch)
    bad = {t: e for t, e in res.items() if e}
    if not quiet:
        for t, e in bad.items():
            print(f'FAIL {t}')
            for x in e:
                print(f'   - {x}')
    print(f'{subject} b{batch:03d}: {len(res) - len(bad)}/{len(res)} cards pass the gate')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
