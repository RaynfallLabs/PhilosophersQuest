"""No singular they in game content (Brandon, 2026-10-18).

"they/them" is ONLY ever plural. An individual is always he, she or it, in
every story, encounter, quiz question, context blurb, journal line, hint,
item lore and UI string.

Most singular they cannot be told from a plural by a regex, so the bank-wide
sweep (2026-10-18) was done by reading every candidate. This test is the
mechanical floor that keeps the obvious shapes out for good:

* "themself", "they is", "they was / has / does";
* "he or she", "the hero" or "the player" followed, in the same sentence, by
  they / their / themselves;
* a singular subject (someone, anyone, whoever, everyone, nobody, each X,
  every X) followed in the same clause by their / themselves / theirs, with
  no plural-looking word in between.

"them" (and "they" after anyone / every X) is left out of the last two
shapes on purpose: measured on this text it was wrong over 90% of the time,
because it nearly always points back to a plural thing ("anyone could read
them", "the player rotated them", "every book they could find").

It scans every JSON file under data/ (the pruned-question archive excepted)
and every non-docstring string literal under src/. A hit that is a proven
plural (or a real quotation) goes in ALLOW below with its reason.
"""
from __future__ import annotations

import io
import json
import re
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
SRC = ROOT / 'src'

_TIME = (r"(?:year|day|night|morning|evening|week|month|season|spring|summer|autumn|winter|time|"
         r"hour|minute|second|century|decade|generation|dawn|dusk|harvest|turn|round|floor|step|upkeep|"
         r"few|january|february|march|april|may|june|july|august|september|october|november|december)")
_STOPS = r"[^.!?;:\"“”—()]"

TELLS = {
    'themself': re.compile(r"\bthemself\b", re.I),
    'they + singular verb': re.compile(r"\bthey (?:is|was|has|does)\b", re.I),
}
HERO = re.compile(r"\b(?:he or she|the hero|the player)\b(?!['’]s\b)(?P<gap>" + _STOPS + r"{0,40}?)"
                  r"\b(?:they|their|themselves|theirs)\b", re.I)
INDEFINITE = re.compile(
    r"\b(?:someone|somebody|anyone|anybody|whoever|everyone|everybody|no one|nobody"
    r"|(?<!s )(?<!they )(?<!we )(?<!who )(?<!which )(?<!that )(?<!have )(?<!had )(?<!are )(?<!were )"
    r"each (?!other\b|of\b|one\b|and\b|with\b|in\b|" + _TIME + r"s?\b)(?![a-z]+s\b)[a-z]+"
    r"|every (?!" + _TIME + r"s?\b|one\b|single\b|other\b|bit\b|kind\b|part\b|piece\b|which\b|last\b)"
    r"(?![a-z]+s\b)[a-z]+)\b"
    r"(?P<gap>" + _STOPS + r"{1,40}?)\b(?:their|themselves|theirs)\b", re.I)
_PLURAL_WORDS = {'and', 'or', 'both', 'people', 'men', 'women', 'children', 'them', 'they', 'their'}
_DETERMINERS = {'the', 'these', 'those', 'many', 'all', 'some', 'few', 'two', 'three', 'four', 'his', 'her',
                'its', 'our', 'your', 'of', 'my', 'several', 'other', 'such', 'no', 'whose'}


def _has_plural(gap: str, conjunctions: bool = True) -> bool:
    """A plural-looking word in the gap: a plural word, or 'the/his/two... Xs'."""
    words = [w.lower() for w in re.findall(r"[A-Za-z']+", gap)]
    for i, w in enumerate(words):
        if w in _PLURAL_WORDS and (conjunctions or w not in ('and', 'or')):
            return True
        if (i > 0 and words[i - 1] in _DETERMINERS and len(w) > 2 and w.endswith('s')
                and not w.endswith(('ss', 'us', "'s"))):
            return True
    return False


def find_singular_they(text: str) -> list[tuple[str, int, int]]:
    """(shape, start, end) for every mechanically detectable singular they."""
    out = []
    for name, rx in TELLS.items():
        out += [(name, m.start(), m.end()) for m in rx.finditer(text)]
    out += [('the hero/player ... they', m.start(), m.end()) for m in HERO.finditer(text)
            if not _has_plural(m.group('gap'), conjunctions=False)]
    for m in INDEFINITE.finditer(text):
        gap = m.group('gap')
        if not re.search(r"[A-Za-z]", gap):
            continue            # "every book they could find": a relative clause on a plural
        if _has_plural(gap):
            continue            # a plural sits between subject and pronoun
        out.append(('singular subject ... their', m.start(), m.end()))
    return out


# (file relative to the repo root, a substring of the offending string) -> reason.
# Only proven plurals and real quotations belong here.
_Q = 'data/questions/'
_C = 'data/question_contexts/'
ALLOW: dict[tuple[str, str], str] = {
    ('data/hints.json', 'They live in the hero, and wait in a small menu until they are called.'):
        "they = 'some powers'",
    ('data/items/shield.json', 'every act of their'): "their = 'the dead'",
    ('data/monsters.json', 'anyone who enters their'): 'their = the dead soldiers of the line',
    ('data/monsters.json', 'everyone but themselves'): 'themselves = the tengu',
    (_C + 'animal.json', 'anyone who gets too close to their'): 'their = the birds',
    (_C + 'animal.json', 'every feature of their'): 'their = numbats / capybaras',
    (_C + 'cooking.json', 'each region, families have their'): 'their = families',
    (_C + 'history.json', 'every public building across their'): 'their = the Romans',
    (_C + 'philosophy.json', 'each ran with the method in their'): 'their = Heidegger, Sartre and Beauvoir',
    (_C + 'history.json', 'each representing a specific consonant sound of their'): 'their = the people who made the script',
    (_C + 'history.json', 'each town, craftsmen organized themselves'): 'themselves = craftsmen',
    (_C + 'science.json', 'Nobody has proven that their'): 'their = the Navier-Stokes equations',
    (_Q + 'ai.json', 'every image including ones outside their'): 'their = image-recognition systems',
    (_Q + 'ai.json', 'every summary on their'): 'their = Notion, Otter and Google',
    (_Q + 'animal.json', 'each editing site to do their'): 'their = the editing enzymes',
    (_Q + 'animal.json', 'every new tunnel by themselves'): 'themselves = the animals (plural answer choices)',
    (_Q + 'animal.json', 'no one knew what narwhals actually did with their'): 'their = narwhals',
    (_Q + 'cooking.json', 'anyone from taking the plant out of their'): 'their = the Spanish rulers',
    (_Q + 'economics.json', 'Someone whose occupational output is ideas themselves'): 'themselves = ideas',
    (_Q + 'economics.json', 'each wrote memoirs defending their'): 'their = Paulson and Bernanke',
    (_Q + 'economics.json', 'every drug on their'): 'their = markets',
    (_Q + 'economics.json', 'every large US company through their'): 'their = the three investment firms',
    (_Q + 'economics.json', 'whoever was handy to fill their'): 'their = the local police',
    (_Q + 'geography.json', 'each island, because one calling card of theirs'): 'theirs = the Lapita',
    (_Q + 'geography.json', 'every note, yet together their'): 'their = the two players (polos and sangsih)',
    (_Q + 'history.json', 'anyone outside hear their'): 'their = the delegates',
    (_Q + 'history.json', 'each crew planted an American flag beside their'): 'their = the crew, a plural group of astronauts',
    (_Q + 'history.json', 'each food, one part of their'): 'their = the finches',
    (_Q + 'history.json', 'every Soviet refugee in their'): 'their = Britain and America',
    (_Q + 'history.json', 'every author the American founders quoted in their'): 'their = the founders',
    (_Q + 'history.json', 'every book in the world for their'): "their = Alexandria's rulers",
    (_Q + 'history.json', 'every one of their countenances'): "their = the chained people (Equiano's own words)",
    (_Q + 'history.json', 'every detail of the two-day event themselves'): 'themselves = the organizers',
    (_Q + 'philosophy.json', 'Every choice is fully theirs'): 'theirs = people',
    (_Q + 'philosophy.json', 'anyone thinks good to doubt their'): "their = 'things outside of us' (Kant, quoted)",
    (_Q + 'philosophy.json', 'each fail on their'): 'their = the two giveaways',
    (_Q + 'philosophy.json', 'each keep to their'): 'their = reason, drive and appetite',
    (_Q + 'philosophy.json', 'each studied the claim on their'): 'their = many people',
    (_Q + 'philosophy.json', 'every metal object off their'): 'their = the believers',
    (_Q + 'philosophy.json', 'everyone, resist evidence that violates their'): 'their = scientists',
    (_Q + 'philosophy.json', 'no one truly needs diamonds, their'): 'their = diamonds',
    (_Q + 'philosophy.json', 'no one would choose for their'): "their = the goods (Plato, Republic 357c, quoted)",
    (_Q + 'philosophy.json', 'nobody by themselves'): 'themselves = the two observations',
    (_Q + 'philosophy.json', 'someone else must apply their'): 'their = the lawmakers',
    (_Q + 'science.json', 'anyone found their'): 'their = the empty squares',
    (_Q + 'science.json', 'each carry fewer nuclear charges than their'): 'their = tellurium and cobalt',
    (_Q + 'science.json', 'each set against their'): 'their = the sixty adults',
    (_Q + 'science.json', 'every flex tugs their'): 'their = the lopsided molecules',
    (_Q + 'science.json', 'every stage of their'): 'their = B cells',
    (_Q + 'theology.json', 'no one could have moved their'): 'their = Odysseus and Penelope',
    (_Q + 'trivia.json', 'each city-state are powerful defilers themselves'): 'themselves = the Sorcerer-Kings',
    (_Q + 'trivia.json', 'every magazine cover called their'): 'their = fans and magazine covers',
}

def _json_strings():
    for fp in sorted(DATA.rglob('*.json')):
        if '_pruned' in fp.parts:
            continue
        rel = fp.relative_to(ROOT).as_posix()
        stack = [json.loads(fp.read_text(encoding='utf-8'))]
        while stack:
            o = stack.pop()
            if isinstance(o, dict):
                stack.extend(o.values())
            elif isinstance(o, list):
                stack.extend(o)
            elif isinstance(o, str):
                yield rel, o


def _src_strings():
    fstring_middle = getattr(tokenize, 'FSTRING_MIDDLE', None)
    for fp in sorted(SRC.rglob('*.py')):
        rel = fp.relative_to(ROOT).as_posix()
        toks = tokenize.generate_tokens(io.StringIO(fp.read_text(encoding='utf-8')).readline)
        prev = None
        for t in toks:
            if t.type in (tokenize.COMMENT, tokenize.NL):
                continue
            is_str = t.type == tokenize.STRING or (fstring_middle is not None and t.type == fstring_middle)
            if is_str:
                docstring = (t.type == tokenize.STRING
                             and (prev is None or prev.type in (tokenize.NEWLINE, tokenize.INDENT,
                                                                 tokenize.DEDENT))
                             and t.string.lstrip('rRbBuUfF')[:3] in ('"""', "'''"))
                if not docstring:
                    yield rel, t.string
            prev = t


def _all_strings():
    return list(_json_strings()) + list(_src_strings())


def _allowed(rel: str, text: str) -> bool:
    return any(rel == f and sub in text for (f, sub) in ALLOW)


def test_no_mechanical_singular_they():
    hits = []
    for rel, text in _all_strings():
        if _allowed(rel, text):
            continue
        for name, s, e in find_singular_they(text):
            hits.append(f"{rel}: [{name}] ...{text[max(0, s - 60):e + 40]}...")
    assert not hits, ("Singular they found (use he, she or it; rephrase generic "
                      "'the player / anyone' sentences):\n" + "\n".join(hits[:80])
                      + (f"\n... and {len(hits) - 80} more" if len(hits) > 80 else ''))


def test_allow_lists_have_no_stale_entries():
    """Every allow-list entry must still match a string that the patterns flag."""
    flagged: dict[str, list[str]] = {}
    for rel, text in _all_strings():
        if find_singular_they(text):
            flagged.setdefault(rel, []).append(text)
    stale = [k for k in ALLOW if not any(k[1] in t for t in flagged.get(k[0], []))]
    assert not stale, f"stale allow-list entries: {stale}"


def test_every_allow_entry_has_a_reason():
    assert all(r.strip() for r in ALLOW.values())


@pytest.mark.parametrize('sentence', [
    'Doctor Finch says they is busy.',
    'The knight armed themself.',
    'Someone left their cloak here.',
    'The player drinks, and they feel better.',
    'Every traveller keeps their purse close.',
    'Each guest carries their own cup.',
    'Whoever finds it keeps it for themselves.',
])
def test_patterns_catch_known_shapes(sentence):
    assert find_singular_they(sentence)


@pytest.mark.parametrize('sentence', [
    'The villagers say they have seen a light.',
    'Doctor Finch says he is busy.',
    'The hunters burned every village they passed.',
    'Apple and Google each ship their own font.',
    'Anyone could read them.',
    'Every year the farmers bring their goats.',
    'Each of the brothers kept his own sword.',
])
def test_patterns_spare_plurals(sentence):
    assert not find_singular_they(sentence)
