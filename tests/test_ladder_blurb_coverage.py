"""Context-blurb gate for the ladder subjects (added by the pre-v3.0
audit, 2026-10-04).

PIPELINE section 16 calls the ladder blurb a hard gate, but nothing in the
repo enforced it: `bankbuild/bank.py` has no blurb check and only math had
a data test. This file adds:

  * coverage: every topic that has questions has a blurb (hard);
  * no new untopiced questions (ratchet: the count may only go down);
  * verbatim answer leaks (ratchet per subject: may only go down).

The ratchets record the state found by the audit. They exist so the
numbers cannot get WORSE while the content rebuild is pending; lower a
baseline whenever a subject is cleaned up. See PRE_V3_AUDIT_REPORT.md
section 4 for the plan.
"""
import json
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_Q = _ROOT / 'data' / 'questions'
_C = _ROOT / 'data' / 'question_contexts'

LADDER_SUBJECTS = ('history', 'philosophy', 'economics', 'ai', 'theology',
                   'geography', 'science', 'trivia', 'animal', 'cooking')

# Questions with no `topic` (C can show no blurb for them). Audit state.
UNTOPICED_BASELINE = {}

# Rungs whose keyed answer appears verbatim in their own blurb. Audit state,
# rounded up slightly so harmless reformatting does not trip the test.
LEAK_BASELINE = {
    'history': 95, 'philosophy': 5, 'economics': 674, 'ai': 10,
    'theology': 263, 'geography': 174, 'science': 52, 'trivia': 91,
    'animal': 110, 'cooking': 52,
}


# Teaching cards (Brandon, 2026-10-18): "The context tab SHOULD basically
# have every answer hinted at in it for the ladder." A subject joins this
# set when its first teaching cards are merged (bankbuild/cards/merge.py).
# For these subjects the leak ratchet above no longer applies; instead every
# card that carries a `teaches` map must pass the card gate, and the count of
# cards still waiting for their rewrite may only go down.
TEACHING_SUBJECTS = {'animal', 'philosophy'}

# Cards in a teaching subject that still lack `teaches` (rollout in progress).
UNTAUGHT_BASELINE = {'animal': 255, 'philosophy': 345}


def _load(subject):
    questions = json.loads((_Q / f'{subject}.json').read_text(encoding='utf-8'))
    if isinstance(questions, dict):
        questions = questions.get('questions', list(questions.values()))
    blurbs = json.loads((_C / f'{subject}.json').read_text(encoding='utf-8'))
    return questions, blurbs


def _blurb_text(entry):
    return entry.get('context_blurb', '') if isinstance(entry, dict) else str(entry)


@pytest.mark.parametrize('subject', LADDER_SUBJECTS)
def test_every_topic_with_questions_has_a_blurb(subject):
    questions, blurbs = _load(subject)
    topics = {q['topic'] for q in questions if q.get('topic')}
    missing = sorted(t for t in topics if not _blurb_text(blurbs.get(t, '')).strip())
    assert not missing, f"{subject}: {len(missing)} topics without a blurb: {missing[:8]}"


@pytest.mark.parametrize('subject', LADDER_SUBJECTS)
def test_untopiced_questions_do_not_grow(subject):
    questions, _blurbs = _load(subject)
    untopiced = sum(1 for q in questions if not q.get('topic'))
    allowed = UNTOPICED_BASELINE.get(subject, 0)
    assert untopiced <= allowed, (
        f"{subject}: {untopiced} questions have no topic (baseline {allowed}). "
        "Every ladder question needs a topic so its blurb can be shown.")


def _verbatim_leaks(subject):
    questions, blurbs = _load(subject)
    count = 0
    for q in questions:
        topic = q.get('topic')
        if not topic or topic not in blurbs:
            continue
        answer = str(q.get('answer', '')).strip().strip('.,;:!?"\'').lower()
        if len(answer) < 8 and len(answer.split()) < 2:
            continue
        blurb = _blurb_text(blurbs[topic]).lower()
        if re.search(r'(?<!\w)' + re.escape(answer) + r'(?!\w)', blurb):
            count += 1
    return count


@pytest.mark.parametrize('subject', LADDER_SUBJECTS)
def test_verbatim_answer_leaks_do_not_grow(subject):
    if subject in TEACHING_SUBJECTS:
        pytest.skip(f'{subject} cards now teach every rung (ruling 2026-10-18)')
    leaks = _verbatim_leaks(subject)
    allowed = LEAK_BASELINE[subject]
    assert leaks <= allowed, (
        f"{subject}: {leaks} rungs have their keyed answer verbatim in the "
        f"blurb (baseline {allowed}). A blurb must not reveal a rung's answer.")


# Notes written for the question author must never reach the player. The
# blurb is shown verbatim, so it may not talk about the ladder, the bank,
# the topic as a unit, or what "the kid" should learn. (About 900 blurbs
# carried such notes before the pre-v3.0 audit stripped them.)
AUTHOR_VOICE = (
    'this ladder', 'ladder passes', 'the ladder you', 'sub-strand',
    'geek-dad', 'spoiler-ok', 'stance doc', 'no verdict crowned',
    'the kid should', 'this topic', 'the topic walks', 'the questions below',
    'the project treats', "the bank's rule", 'this entry',
)


@pytest.mark.parametrize('subject', LADDER_SUBJECTS + ('math',))
def test_blurbs_carry_no_author_notes(subject):
    blurbs = json.loads((_C / f'{subject}.json').read_text(encoding='utf-8'))
    hits = []
    for topic, entry in blurbs.items():
        text = _blurb_text(entry).lower()
        hits += [(topic, phrase) for phrase in AUTHOR_VOICE if phrase in text]
    assert not hits, f"{subject}: author-facing text in player blurbs: {hits[:8]}"


# The per-question `context` (the explanation shown after an answer, in the
# review and study screens) obeys the same rule, and also may not use the
# question builder's own jargon: "distractors", "the keyed answer", "this
# rung", "the ladder", "the stem", "the bank keys ...". About 450 contexts
# carried such notes until bug bash 4 (call 4) reworded them.
CONTEXT_JARGON = (
    r'\bdistractors?\b', r'\bkeyed\b', r'\bkeys (both|only)\b', r'\brungs?\b',
    r'\bladders?\b', r'\bthe stem\b', r'\bout of the stem\b', r'\blegend-foils?\b',
    r'\bare foils\b', r'\blegend-flagged\b', r'\btopic spec\b', r'\bframing[_ ]note\b',
    r"\bthe bank (keys|keeps|takes|presents|tells|treats|reports|states|refuses|says|"
    r"marks|flags|teaches|avoids|asks|counts|holds)\b",
    r"\bbank's (stance|rule|own)\b",
)
# Real-world uses of those words (a story's ladder, a plant's stem, a bell
# that was rung). Stripped before the check. A new story use goes here.
CONTEXT_REAL_USES = (
    r"jacob's ladder", r'ladder of (love|nature|marking|law)', r'distance ladder',
    r'(rope|wire|wooden|extension|bladed|roots|homemade wire)[- ]ladders?',
    r'up the ladder', r'climbing the ladder', r'throw away the ladder',
    r'career ladder', r"industry's ladder", r'memorize the ladder', r'bells? (was )?rung',
    r'was rung', r'rung bell', r'rung the bell', r'rung in celebration', r'rungs joining',
    r'connecting rungs', r'[ag]-[tc] rung', r'ladder of one width', r'down the ladder',
    r"pliny's ladder", r"aquinas's (three-tier )?ladder", r"michelin's official ladder",
    r'same ladder a bell', r'severity ladder', r"'ladder' never", r'lowest rung',
    r'each lower rung', r'bottom rung of the cosmic', r'rung by rung', r'next rung up',
    r'the stem out of which', r'the stem dies', r'rear of the stem', r'base of the stem',
    r'off the stem', r'keyed .regulators', r'keyed to their masters', r'the ladder leading',
    r'a ladder down', r'immovable ladder', r'the ladder\b(?=[^.]*jacob)', r"the ladder;",
    r'scala naturae', r"dreamed of the ladder", r"the ladder's stone",
    r'ladder leading down', r'cuts the stem', r'stem fibers', r"world bank's own",
    r'the ladder image', r's_ladder', r'ladder-staircase', r'ladder of what we are',
)


def _context_jargon(text):
    low = text.lower()
    for real in CONTEXT_REAL_USES:
        low = re.sub(real, ' ', low)
    hits = [p for p in AUTHOR_VOICE if p in low]
    hits += [m.group(0) for p in CONTEXT_JARGON for m in [re.search(p, low)] if m]
    return hits


def test_context_jargon_check_sees_builder_notes():
    assert _context_jargon("The three distractors are real Hayek works.")
    assert _context_jargon("See the next rung for the language.")
    assert _context_jargon("The bank keys BOTH; a ladder that hides it argues.")
    assert not _context_jargon("Jacob dreamed of angels on Jacob's ladder at Bethel.")
    assert not _context_jargon("Ginger is a rhizome, an underground stem.")


@pytest.mark.parametrize('subject', sorted(p.stem for p in _Q.glob('*.json')))
def test_contexts_carry_no_author_notes(subject):
    questions = json.loads((_Q / f'{subject}.json').read_text(encoding='utf-8'))
    hits = [(i, _context_jargon(q.get('context', ''))) for i, q in enumerate(questions)]
    hits = [h for h in hits if h[1]]
    assert not hits, (f"{subject}: {len(hits)} contexts talk to the question author: "
                      f"{hits[:8]} (a real-world use belongs in CONTEXT_REAL_USES)")


# --- teaching cards (2026-10-18) -------------------------------------------

def _card_packets(subject):
    import sys
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    from bankbuild.cards.extract import packet
    from bankbuild.cards.common import ladders
    blurbs = json.loads((_C / f'{subject}.json').read_text(encoding='utf-8'))
    lad = ladders(subject)
    return blurbs, {t: packet(subject, t, qs, blurbs.get(t)) for t, qs in lad.items()}


@pytest.mark.parametrize('subject', sorted(TEACHING_SUBJECTS) or ['none'])
def test_teaching_cards_pass_the_card_gate(subject):
    if subject == 'none':
        pytest.skip('no subject has teaching cards yet')
    from bankbuild.cards.gate import check_card
    blurbs, packets = _card_packets(subject)
    bad = {}
    for topic, pkt in packets.items():
        entry = blurbs.get(topic)
        if isinstance(entry, dict) and entry.get('teaches'):
            errs = check_card(pkt, entry)
            if errs:
                bad[topic] = errs[:3]
    assert not bad, f"{subject}: {len(bad)} teaching cards fail the gate: {list(bad.items())[:5]}"


@pytest.mark.parametrize('subject', sorted(TEACHING_SUBJECTS) or ['none'])
def test_untaught_cards_do_not_grow(subject):
    if subject == 'none':
        pytest.skip('no subject has teaching cards yet')
    blurbs, packets = _card_packets(subject)
    untaught = sum(1 for t in packets
                   if not (isinstance(blurbs.get(t), dict) and blurbs[t].get('teaches')))
    allowed = UNTAUGHT_BASELINE.get(subject, 0)
    assert untaught <= allowed, (
        f"{subject}: {untaught} cards do not teach their ladder yet (baseline {allowed}); "
        "a card fell out of step with its questions (edited stem?) or a rewrite was lost.")
