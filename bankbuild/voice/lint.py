"""The house-voice lint (docs/quiz/HOUSE_VOICE.md, Brandon 2026-10-24).

    py -m bankbuild.voice.lint <subject> [<subject> ...]   # bank-wide rates
    py -m bankbuild.voice.lint <subject> --show RULE [-n 20] # examples of one rule

`lint_stem(stem, subject, tier) -> (failures, warnings)`, each a list of
rule names, is what `stage check` runs on every new or changed question.
Quoted text (between quotation marks) is never linted: a stem's example
sentences, titles and famous lines keep their own words. Math is exempt;
grammar is exempt from the length band and the closer length.
"""
from __future__ import annotations

import re
import sys

EXEMPT = frozenset({'math'})
NO_BAND = frozenset({'grammar'})

# (warn below, warn above, fail above) words per tier
BANDS = {1: (25, 45, 60), 2: (30, 55, 70), 3: (40, 70, 85), 4: (40, 70, 85), 5: (40, 70, 85)}
CLOSER_WARN, CLOSER_FAIL = 20, 30

# Double quotes, curly quotes, and straight single quotes that open after a
# space or bracket and close before a space or punctuation ('Between you and
# I, the plan will fail.'), so an apostrophe (can't, Bernini's) never opens one.
_QUOTED = re.compile(r'"[^"\n]*"|“[^”\n]*”|‘[^’\n]*’'
                     r"|(?:(?<=^)|(?<=[\s(\[]))'(?=\S).+?'(?=[\s.,;:!?)\]]|$)")
_MONTHS = ('January|February|March|April|May|June|July|August|September|October|'
           'November|December')
DATE_FIRST = re.compile(
    rf"^(?:In|On|By|During|Around|From|Since|Before|After|Until|Back in|Early in|Late in|"
    rf"Sometime in|Some time in|Circa)\s+(?:about\s+|around\s+|roughly\s+)?(?:"
    rf"(?:the\s+)?(?:early|late|mid|middle|spring|summer|autumn|fall|winter|year)\b|"
    rf"(?:{_MONTHS})\b|"
    rf"\d{{1,2}}\s+(?:{_MONTHS})\b|"
    rf"\d{{3,4}}s?\b|"
    rf"the\s+(?:early\s+|late\s+|mid-?)?\d{{2,4}}s\b|"
    rf"\d{{1,2}}(?:st|nd|rd|th)\b|"
    rf"(?:AD|BC|BCE|CE)\b|"
    rf"the\s+(?:\w+\s+){{0,2}}(?:century|centuries|decade|millennium|era|age)\b)")
YOU = re.compile(r"\b(?:you|your|yours|yourself|yourselves|you're|you've|you'd|you'll)\b", re.I)
SUPPOSE_YOU = re.compile(r"\bSuppose (?:that )?you\b")
BAD_OPENING = re.compile(r"^(?:Imagine|Picture|Did you know|Here is|Here's|Let's|Let us)\b", re.I)
TICS = {
    'which_of_the_following': re.compile(r"\bwhich of the following\b", re.I),
    'here_is': re.compile(r"\bhere(?:'s| is| are) the\b", re.I),
    'line_up': re.compile(r"\bline (?:the|them|these|those|up)\b.{0,40}\bup\b|\bline up the\b", re.I),
    'asks_you_to_picture': re.compile(r"\basks? (?:you|us|the reader) to (?:picture|imagine)\b", re.I),
    'twist_catch_kicker': re.compile(r"\b(?:the catch|the twist|the kicker|plot twist)\b", re.I),
    'think_about': re.compile(r"\bthink about\b", re.I),
    'did_you_know': re.compile(r"\bdid you know\b", re.I),
    'lets': re.compile(r"\blet's\b", re.I),
    'hype': re.compile(r"\b(?:fun fact|believe it or not|surprisingly|amazingly|incredibly|"
                       r"astonishingly|mind-blowing|jaw-dropping)\b", re.I),
    'so_closer': re.compile(r"(?:^|[.!?]\s+)So (?:what|why|how|where|which|who|when)\b"),
    'imagine_picture': re.compile(r"\b(?:imagine|picture this|picture a|picture an|picture the)\b", re.I),
}
_DASH = re.compile(r"—|–| -- | - ")
# Capitals for emphasis ("ask what sort of God they worship, NOT where they
# live"): the Chronicler lets the sentence carry the stress. A fixed list of
# ordinary words, so acronyms (NASA, DNA, WHO, LED, RAG) are never caught.
_CAPS_WORDS = frozenset("""
    NOT ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN ONLY ALL BOTH EITHER NEITHER
    NONE ANY EVERY EACH SOME MORE MOST LESS LEAST FEW MANY OTHER SAME DIFFERENT OWN
    WHAT WHY HOW WHERE WHEN WHICH WHOSE WHOM THAT THIS THESE THOSE AND FOR WITH BUT
    BEFORE AFTER FIRST SECOND THIRD LAST NEXT NOW THEN STILL ALSO EVEN JUST ALREADY
    NEVER ALWAYS EVER AGAIN TRUE FALSE REAL REALLY RIGHT WRONG CORRECT CORRECTLY
    CAN CANNOT MUST WILL WOULD COULD SHOULD DID DOES DOESN'T DIDN'T WAS WERE ARE
    HAS HAD HAVE KNOW KNEW SEE SAW PROVE PROVED BECAUSE HOWEVER BETWEEN AGAINST
    INSIDE OUTSIDE ABOVE BELOW OUT INTO FROM YOU HIS HER HIM SHE THEY THEM THEIR
    NEW OLD BIG SMALL HALF DOUBLE TWICE WHOLE ENTIRE EXACTLY ACTUALLY FORWARD BACKWARD
    PEOPLE THING THINGS NOTHING EVERYTHING SOMETHING ANYTHING
""".split())
_CAPS = re.compile(r"\b[A-Z][A-Z']{2,}\b")


def strip_quoted(text: str) -> str:
    return _QUOTED.sub('""', text)


_SENTENCE_END = re.compile(r"""(?:(?<=[.!?])|(?<=[.!?]['"’”]))\s+""")


def last_sentence(text: str) -> str:
    # A sentence can end inside a quotation: "...supply money?' An economist..."
    parts = [p for p in _SENTENCE_END.split(text.strip()) if p]
    return parts[-1] if parts else text


def lint_stem(stem: str, subject: str, tier: int) -> tuple[list[str], list[str]]:
    """(failures, warnings) for one stem: lists of rule names."""
    if subject in EXEMPT:
        return [], []
    fails: list[str] = []
    warns: list[str] = []
    stem = (stem or '').strip()
    bare = strip_quoted(stem)
    n = len(stem.split())
    if subject not in NO_BAND:
        lo, hi, cap = BANDS.get(int(tier or 1), BANDS[3])
        if n > cap:
            fails.append(f'too_long({n}>{cap})')
        elif n > hi:
            warns.append(f'long({n}>{hi})')
        elif n < lo:
            warns.append(f'short({n}<{lo})')
    if DATE_FIRST.match(stem):
        fails.append('date_first')
    if BAD_OPENING.match(stem):
        fails.append('bad_opening')
    if YOU.search(bare) and not SUPPOSE_YOU.search(stem):
        fails.append('second_person')
    if '!' in bare:
        fails.append('exclamation')
    if len(_DASH.findall(bare)) >= 2:
        fails.append('dashes')
    if any(w in _CAPS_WORDS for w in _CAPS.findall(bare)):
        fails.append('caps_emphasis')
    for name, rx in TICS.items():
        if name == 'imagine_picture' and SUPPOSE_YOU.search(stem):
            continue
        if rx.search(bare):
            fails.append(name)
    if not stem.endswith('?'):
        fails.append('no_question_mark')
    if subject not in NO_BAND:
        closer = len(last_sentence(stem).split())
        if closer > CLOSER_FAIL:
            fails.append(f'closer_too_long({closer})')
        elif closer > CLOSER_WARN:
            warns.append(f'closer_long({closer})')
    return fails, warns


def _rule(name: str) -> str:
    return name.split('(')[0]


def bank_report(subject: str) -> dict:
    from bankbuild.cards.common import load_questions
    qs = load_questions(subject)
    counts: dict[str, int] = {}
    clean = 0
    for q in qs:
        f, w = lint_stem(q['question'], subject, int(q.get('tier', 1)))
        if not f:
            clean += 1
        for r in f:
            counts['F:' + _rule(r)] = counts.get('F:' + _rule(r), 0) + 1
        for r in w:
            counts['w:' + _rule(r)] = counts.get('w:' + _rule(r), 0) + 1
    return {'n': len(qs), 'clean': clean, 'counts': counts}


def main() -> None:
    args = sys.argv[1:]
    if '--show' in args:
        i = args.index('--show')
        rule = args[i + 1]
        k = int(args[args.index('-n') + 1]) if '-n' in args else 20
        from bankbuild.cards.common import load_questions
        shown = 0
        for q in load_questions(args[0]):
            f, w = lint_stem(q['question'], args[0], int(q.get('tier', 1)))
            if any(_rule(r) == rule for r in f + w):
                print(f"- T{q.get('tier')} {q['question']}")
                shown += 1
                if shown >= k:
                    break
        return
    for subject in args:
        r = bank_report(subject)
        n = r['n']
        top = sorted(r['counts'].items(), key=lambda kv: -kv[1])
        print(f"{subject:10} {n:5} questions, {r['clean'] * 100 / n:4.0f}% pass  "
              + '  '.join(f'{k}={v * 100 / n:.0f}%' for k, v in top))


if __name__ == '__main__':
    main()
