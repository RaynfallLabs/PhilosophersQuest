"""Deterministic gate for teaching context cards.

    py -m bankbuild.cards.gate <subject> <batch>          # check bNNN_cards.json
    py -m bankbuild.cards.gate <subject> <batch> --quiet  # only the summary line

A card FAILS when it:
  * is shorter than its minimum or longer than 750 words;
  * shares a run of 6 or more words with any stem in its ladder;
  * contains a whole choice string of more than 4 words (keyed or not);
  * names 2 or more of one question's pure distractors (choices that are
    not the keyed answer of any question in the ladder);
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
GIVEAWAY = re.compile(r"\b(the (correct )?answer is|the correct answer)\b", re.I)
URL = re.compile(r"(https?://|www\.|(^|[.!?]\s+)Sources?:)")


def _singular_they(text: str) -> list:
    """The repo's own singular-they lint (tests/test_no_singular_they.py)."""
    import importlib.util
    from bankbuild.cards.common import ROOT
    global _FIND_THEY
    if '_FIND_THEY' not in globals():
        spec = importlib.util.spec_from_file_location(
            '_they_lint', ROOT / 'tests' / 'test_no_singular_they.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _FIND_THEY = mod.find_singular_they
    return _FIND_THEY(text)


def _ngrams(ws: list[str], n: int) -> set[tuple]:
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def _sentence_ngrams(text: str, n: int) -> set[tuple]:
    """n-word runs inside each sentence, so a run never spans a full stop."""
    out: set[tuple] = set()
    for part in re.split(r'(?<=[.!?])\s+|\n+', text):
        out |= _ngrams(words(part), n)
    return out


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
    n_words = len(text.split())          # length counts words as a reader does
    lo, _target, cap = pkt['length']['min_words'], pkt['length']['target_words'], pkt['length']['max_words']
    if n_words < lo:
        errs.append(f'too short: {n_words} words (min {lo})')
    if n_words > cap:
        errs.append(f'too long: {n_words} words (max {cap})')
    hay = ' '.join(ws)
    card_6 = _sentence_ngrams(text, 6)
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
    for kind, start, end in _singular_they(text):
        errs.append(f'singular they ({kind}): "...{text[max(0, start - 40):end + 10]}..." '
                    '(use he, she or it; if the referent really is plural, reword so the lint sees it)')
    keyed = {norm(q['answer']) for q in pkt['questions']}
    for q in pkt['questions']:
        h = q['hash']
        shared = sorted(card_6 & _sentence_ngrams(q['stem'], 6))
        if shared:
            runs = '; '.join('"' + ' '.join(g) + '"' for g in shared[:6])
            errs.append(f'{h}: copies 6+ words of the stem ({len(shared)} runs): {runs}')
        toured = []
        for ch in q['choices']:
            if len(ch.split()) > 4 and _contains(hay, ch):
                errs.append(f'{h}: contains a whole choice (>4 words): "{ch}"')
            elif len(words(ch)) > 6 and norm(ch) not in keyed:
                # A distractor's phrasing must not leak into the card (a
                # keyed answer sharing words with its own teaching sentence
                # is the fact, and fine in an open book).
                near = card_6 & _ngrams(words(ch), 6)
                if near:
                    errs.append(f'{h}: copies 6+ words of a choice: "{" ".join(sorted(near)[0])}"')
            if norm(ch) not in keyed and _contains(hay, ch):
                toured.append(ch)
        if len(toured) >= 2:
            errs.append(f'{h}: names {len(toured)} of its distractors: {toured}')
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
