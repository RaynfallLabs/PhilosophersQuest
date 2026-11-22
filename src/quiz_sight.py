"""What a dazed, blinded or hallucinating hero SEES: display only, pure.

Brandon, 2026-11-22: "the confused quiz timer thing works GREAT". The same
bargain for three more effects (data/effects.json 'quiz'):

  double    Stunned: the question and answers are drawn twice and slide
            together over confusion's settle time.
  dark      Blinded: the answers are dark but for a pool of light the
            arrows move. Nothing to wait for.
  phantom   Hallucinating: a false answer keeps a slot of its own and fades
            with the settle time. On the map and under In Sight, creatures
            wear other kinds' faces.

The question, its answers, the answer check and the teaching card are never
touched. No pile of them is an auto-kill: the waits share one settle time,
the dark has none, and nothing cuts the clock. Nothing flashes or shakes.
"""
from __future__ import annotations

import random
import re
import zlib
from fractions import Fraction

import effect_rules

NOTHING = {'double': False, 'dark': False, 'phantom': False}
# What stands where the false answer is in the list of answers the cards
# compare with: no answer in any bank is this string.
NOT_AN_ANSWER = '\x00not an answer\x00'


def rules() -> dict:
    return effect_rules.data()['quiz']


def sight_for(player) -> dict:
    """Which of the three are on this hero's next question."""
    if player is None:
        return dict(NOTHING)
    r = rules()
    return {k: any(effect_rules.running(player, e) for e in r[k]['statuses']) for k in NOTHING}


def settles(player) -> bool:
    """Some effect on him makes a question take confusion's settle time to
    come clear."""
    return any(effect_rules.running(player, e) for e in rules()['settling'])


def wait_for(player, timed: bool) -> float:
    """The seconds each question takes to come clear for this hero: one
    settle time however many effects share it, 0.0 with none."""
    if player is None or not settles(player):
        return 0.0
    from quiz_engine import settle_seconds
    try:
        wis = int(player.effective_wis())
    except Exception:
        wis = int(getattr(player, 'WIS', 10) or 10)
    return settle_seconds(timed, wis)


# ---------------------------------------------------------------------------
# Double vision
# ---------------------------------------------------------------------------

def double_offset(share: float) -> tuple:
    """How far each image stands from the true place (UI pixels at scale 1):
    the whole offset as the question goes up, nothing once it has settled,
    sliding evenly between."""
    left = max(0.0, 1.0 - max(0.0, float(share)))
    r = rules()['double']
    return float(r['offset_x']) * left, float(r['offset_y']) * left


def ghost_places(offset: tuple, room: tuple) -> list:
    """Where the two images stand from the text's true place, no further
    than ``room`` (left, up, right, down) lets a whole glyph go. A cut digit
    is another digit, so what one side cannot take the other does."""
    gx, gy = (max(0, int(v)) for v in offset)
    left, up, right, down = (max(0, int(v)) for v in room)
    lx, uy = min(gx, left), min(gy, up)
    return [(-lx, -uy), (min(2 * gx - lx, right), min(2 * gy - uy, down))]


# ---------------------------------------------------------------------------
# The false answer
# ---------------------------------------------------------------------------

# A bare amount, whole: "12", "-3/4", "1 1/2", "2:1", "$5", "50%", ".5".
_BARE = re.compile(r'([-+]?)[$£€]?((?:\d[\d,]*)?(?:\.\d+)?)'
                   r'(?:\s+(\d+)\s*/\s*(\d+)|\s*[/:]\s*(\d+))?\s*(%?)')
_WORDS = {w: n for n, w in enumerate(
    'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen '
    'fifteen sixteen seventeen eighteen nineteen twenty'.split())}
_WORDS.update({'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80,
               'ninety': 90, 'hundred': 100, 'thousand': 1000, 'million': 10 ** 6, 'billion': 10 ** 9,
               'dozen': 12, 'half': Fraction(1, 2), 'quarter': Fraction(1, 4),
               'once': 1, 'twice': 2, 'thrice': 3})
# Words too common to make two answers the same answer.
_COMMON = frozenset(
    'that this with from they them their there were what when which will would have been into '
    'than then only each more most some such your because about'.split())
# An answer that speaks of the other answers, or of none, might well be true.
_CATCH_ALL = re.compile(r'^(?:none|nothing|nobody|neither|both|all of|any of|either of)\b'
                        r'|\bcannot be\b|\bcan not be\b|\bnot enough\b')


def _plain(text) -> str:
    return re.sub(r'[^0-9a-z]+', ' ', str(text).lower()).strip()


def _has_amount(text) -> bool:
    t = str(text)
    return any(c.isdigit() for c in t) or any(w in _WORDS for w in _plain(t).split())


def _amounts(text):
    """What a bare amount may be read as ("50%": 50 and 1/2); None for
    anything with more to it (a unit, a word, an expression)."""
    t = str(text).strip().lower().replace('\u2212', '-')
    if t in _WORDS:
        return {Fraction(_WORDS[t])}
    m = _BARE.fullmatch(t)
    if not m or not m.group(2):
        return None
    sign, whole, num, den, over, pct = m.groups()
    try:
        v = Fraction(whole.replace(',', ''))
        if num:
            v += Fraction(int(num), int(den))
        elif over:
            v /= int(over)
    except (ValueError, ZeroDivisionError):
        return None
    if sign == '-':
        v = -v
    return {v, v / 100} if pct else {v}


def same_answer(a, b) -> bool:
    """The two could be read as one answer, so one may not be the other's
    false twin. Strict on purpose, for a refusal costs only another try:
    two amounts are apart only when both are bare and differ however read
    ("3 days" and "72 hours" are never told apart here); two of words share
    no word that matters."""
    if str(a).strip().lower() == str(b).strip().lower():
        return True
    if _has_amount(a) and _has_amount(b):
        va, vb = _amounts(a), _amounts(b)
        return va is None or vb is None or bool(va & vb)
    pa, pb = _plain(a), _plain(b)
    if not pa or not pb:
        return False
    if f' {pa} ' in f' {pb} ' or f' {pb} ' in f' {pa} ':
        return True
    wa, wb = ({w[:5] for w in p.split() if len(w) >= 4 and w not in _COMMON} for p in (pa, pb))
    return bool(wa & wb)


def _dream(rng, choices: list) -> str:
    """Words that mean nothing, about as many as an answer here has: false
    to any question there is."""
    d = rules()['phantom']['dream']
    sizes = sorted(len(str(c).split()) for c in choices)
    words = [rng.choice(d['starts']) + rng.choice(d['ends'])
             for _ in range(max(1, min(5, sizes[len(sizes) // 2])))]
    words[0] = words[0].capitalize()
    return ' '.join(words)


def _shown_false(text: str, divides) -> bool:
    """A borrowed number is false for this sum: a bare amount (an expression
    might work out to the answer), and for "which divides N" no divisor."""
    got = _amounts(text)
    if got is None:
        return False
    if divides is None:
        return True
    return all(v.denominator == 1 and (v == 0 or divides % int(v) != 0) for v in got)


def phantom_for(question: dict, pool: list, seed: int, subject: str = ''):
    """``{'text', 'slot'}``: a false answer for ``question``, and one that
    can be shown false (data quiz.phantom). A sum with one value takes a
    number from another sum's wrong answers, differing from every answer
    here however read; any other question takes dream words, for another
    question's wrong answer may be true of this one. Its own dice: the
    game's never move."""
    choices = list((question or {}).get('choices') or ())
    if not choices or not pool:
        return None
    real = choices + [question.get('answer', '')]
    rng = random.Random(int(seed) ^ 0x5A17)
    cfg = rules()['phantom']
    stem = str(question.get('question', '') or '').strip()
    text = ''
    which = re.search(cfg['divisor_stem'], stem)
    if subject == 'math' and (which or any(re.search(p, stem) for p in cfg['closed_stems'])):
        divides = int(which.group(1)) if which else None
        longest = max(len(str(c)) for c in choices)
        for _ in range(int(cfg['tries'])):
            other = pool[rng.randrange(len(pool))]
            if other is question:
                continue
            wrong = [c for c in other.get('choices') or () if str(c) != str(other.get('answer', ''))]
            if not wrong:
                continue
            got = str(wrong[rng.randrange(len(wrong))])
            if len(got) > max(12, 2 * longest) or not _shown_false(got, divides):
                continue
            if any(same_answer(got, c) for c in real):
                continue
            text = got
            break
    if not text:
        text = _dream(rng, choices)
    return {'text': text, 'slot': rng.randrange(len(choices) + 1), 'touched': False}


def with_phantom(items: list, phantom, what) -> list:
    """``items`` in display order with ``what`` in the false answer's slot."""
    out = list(items)
    if phantom:
        out.insert(int(phantom['slot']), what)
    return out


def real_index(shown: int, phantom):
    """The displayed slot's place among the real answers; None for the
    false one's."""
    if not phantom:
        return shown
    at = int(phantom['slot'])
    if shown == at:
        return None
    return shown - 1 if shown > at else shown


# ---------------------------------------------------------------------------
# The pool of light
# ---------------------------------------------------------------------------

def move_light(at: int, dx: int, dy: int, n: int, skip=None) -> int:
    """The light moved over ``n`` answer cards in two columns: left and
    right by one, up and down by a row, round the ends, never resting on
    ``skip`` (a false answer that has faded)."""
    if n <= 0:
        return 0
    step = dx if dx else 2 * dy
    if not step:
        return at
    new = (at + step) % n
    if new == skip:
        new = (new + (1 if step > 0 else -1)) % n
    return new


# ---------------------------------------------------------------------------
# Wrong faces
# ---------------------------------------------------------------------------

_FACES: list | None = None


def _face_kinds() -> list:
    """The ordinary one-tile kinds a hallucination borrows from."""
    global _FACES
    if _FACES is None:
        import kind_data
        out = []
        for k, d in sorted(kind_data.defs().items()):
            if not isinstance(d, dict) or k.startswith('sk_zombie'):
                continue
            if any(d.get(f) for f in ('is_boss', 'is_mini_boss', 'quest_only', 'proper_noun', 'is_allied',
                                      'footprint')):
                continue
            # Only what the floors roll: a false face may not give a secret away.
            if float(d.get('peak_weight', 0) or 0) <= 0 or d.get('frequency', 3) == 0:
                continue
            out.append(k)
        _FACES = out
    return _FACES


def false_face(monster, turn: int):
    """``(kind, name)`` this creature seems to be to a hallucinating hero:
    another kind, the same for a few turns at a time (faces change as he
    acts, never by the clock)."""
    kinds = _face_kinds()
    if not kinds:
        return None
    n = zlib.crc32(f"{id(monster)}|{int(turn) // 4}".encode('utf-8')) % len(kinds)
    if kinds[n] == getattr(monster, 'kind', None):
        n = (n + 1) % len(kinds)
    import kind_data
    from naming import proper_name
    return kinds[n], proper_name(kind_data.defs()[kinds[n]].get('name') or kinds[n])


class Seeming:
    """A creature as a hallucinating hero reads it under In Sight: all its
    own but its kind and its name."""

    def __init__(self, monster, kind: str, name: str):
        object.__setattr__(self, '_of', monster)
        object.__setattr__(self, 'kind', kind)
        object.__setattr__(self, 'name', name)

    def __getattr__(self, attr):
        return getattr(object.__getattribute__(self, '_of'), attr)
