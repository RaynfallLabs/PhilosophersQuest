"""Dad's Code Validator, everything but the window (code_validator.py draws
it). No pygame here, so the tests drive every rule directly.

* The kids: the profiles Dad gives badges to, kept in
  Documents\\PQ_Dad\\kids.json (outside the repo: it is the children's data),
  with the Seeker names each kid's codes were earned under, newest first
  (``seeker_names``: the kids play on more than one machine, under names
  that need not be their own).
* The code entry: the Seeker name the code was earned under (the name on
  the kid's Seeker page in the game), and the keys Dad typed, shaped into
  WORD-XXXX-XXXX as he types, forgiving the slips seeker_codes forgives (O
  for 0, I or L for 1).
* The check: check_code.verify with that Seeker name, the same check, ledger
  and record as check_code.py. A real code is given to the kid chosen
  (recorded under the kid's name) and its Seeker name remembered for that
  kid. A code already in the ledger for another kid is flagged, and given
  only if Dad says so. Plus a kind word on why a code did not match.
* The reels: which badges land on the payline (decided BEFORE they spin, by
  the real check) and where each reel is at any moment, so each one stops
  exactly there.
* The tracker: every achievement for one kid, claimed or not, read from the
  same ledger check_code.py writes, so the two tools always agree.
* The reward line under a claimed badge.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_code  # noqa: E402
import dadlib  # noqa: E402
from dadlib import seeker_codes  # noqa: E402

import naming  # noqa: E402  (src/, put on the path by dadlib)
import seeker_profile  # noqa: E402

RARITIES = ('common', 'rare', 'epic', 'legendary')
RARITY_NAMES = {'common': 'Common', 'rare': 'Rare', 'epic': 'Epic', 'legendary': 'Legendary'}
FRAME_NAMES = {r: f.title() for r, f in check_code.RARITY.items()}     # Bronze, Silver...


def normalise(name) -> str:
    return seeker_codes.normalise_name(name)


nice_date = dadlib.nice_date        # '2026-11-17' -> '17 November 2026'


# -- the kids -------------------------------------------------------------------

DEFAULT_KIDS = ('Fianna', 'Corwin')
SEEKER_NAMES_KEPT = 8               # Seeker names remembered for one kid


def kids_path() -> str:
    return os.path.join(dadlib.dad_dir(), 'kids.json')


def _dedupe(names) -> list[str]:
    out, seen = [], set()
    for n in names:
        if n and normalise(n) not in seen:
            seen.add(normalise(n))
            out.append(n)
    return out


def _read_kids_file() -> dict:
    """kids.json as {'kids': [...], 'seeker_names': {kid: [...]}}. A file
    from before the Seeker names (``{"kids": [...]}``, or a bare list of
    names) reads with none; a missing or damaged file reads as empty."""
    try:
        with open(kids_path(), encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    if isinstance(data, list):
        return {'kids': data}
    return data if isinstance(data, dict) else {}


def _write_kids_file(data: dict) -> None:
    path = kids_path()
    with open(path + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1)
    os.replace(path + '.tmp', path)


def load_kids() -> list[str]:
    """The names on the picker: kids.json, else Fianna and Corwin."""
    names = _read_kids_file().get('kids')
    try:
        out = _dedupe(seeker_profile.clean_name(n) for n in names if isinstance(n, str))
        if out:
            return out
    except TypeError:
        pass
    return list(DEFAULT_KIDS)


def save_kids(names) -> None:
    """The kids list, written; the Seeker names remembered stay as they were
    (a kid taken off the list and put back finds them again)."""
    data = _read_kids_file()
    data['kids'] = list(names)
    _write_kids_file(data)


def seeker_names(kid) -> list[str]:
    """The Seeker names this kid's codes were earned under, newest first."""
    table = _read_kids_file().get('seeker_names')
    if not isinstance(table, dict):
        return []
    norm = normalise(kid)
    for k, names in table.items():
        if normalise(k) == norm and isinstance(names, list):
            return _dedupe(seeker_profile.clean_name(n) for n in names if isinstance(n, str))
    return []


def prefill_name(kid) -> str:
    """The Seeker name the code screen starts with for this kid: the last one
    a code of his or hers was earned under, else the kid's own name."""
    names = seeker_names(kid)
    return names[0] if names else str(kid or '')


def remember_seeker_name(kid, name) -> list[str]:
    """Put ``name`` first in this kid's Seeker names (once, whatever its
    case) and write kids.json. Returns the kid's names, newest first."""
    name = seeker_profile.clean_name(name)
    if name is None or not normalise(kid):
        return seeker_names(kid)
    data = _read_kids_file()
    if not isinstance(data.get('kids'), list):
        data['kids'] = load_kids()
    table = data.get('seeker_names')
    table = dict(table) if isinstance(table, dict) else {}
    norm = normalise(kid)
    old = next((k for k in table if normalise(k) == norm), None)
    before = table.pop(old, []) if old is not None else []
    before = [n for n in before if isinstance(n, str)] if isinstance(before, list) else []
    names = _dedupe([name] + before)[:SEEKER_NAMES_KEPT]
    table[old if old is not None else str(kid)] = names
    data['seeker_names'] = table
    _write_kids_file(data)
    return names


def add_kid(names, typed) -> tuple[list[str], int, str]:
    """(the list, the index of the name typed, a line to show). A name already
    there (in any case) is chosen, not added twice; a name with no letter or
    number in it leaves the list alone, at index -1."""
    name = seeker_profile.clean_name(typed)
    if name is None:
        return list(names), -1, "Type a name with at least one letter in it."
    name = naming.proper_name(name)
    for i, n in enumerate(names):
        if normalise(n) == normalise(name):
            return list(names), i, f"{n} is already on the list."
    return list(names) + [name], len(names), f"{name} added."


def remove_kid(names, index) -> list[str]:
    """The list without ``names[index]``. The ledger is never touched: a name
    put back later finds every code it claimed."""
    return [n for i, n in enumerate(names) if i != index]


# -- the code entry -------------------------------------------------------------

CHARS = seeker_codes.CODE_CHARS          # the 8 characters after the word
WORD_MAX = 16
_TYPO = seeker_codes._TYPO               # O -> 0, I -> 1, L -> 1 (in the code part only)
DEV = 'DEV'


def code_words(achs=None) -> set[str]:
    achs = dadlib.achievements() if achs is None else achs
    return {str(a['code_word']).upper() for a in achs}


@dataclass(frozen=True)
class Entry:
    """A code as typed so far."""
    dev: bool = False          # it began DEV: a code from a copy built without the key
    word: str = ''
    chars: str = ''            # the code part, typos already read as meant
    in_chars: bool = False     # the word is done: typing now fills the code boxes
    known: bool = False        # the word is some achievement's code word
    possible: bool = True      # the word is a code word, or the start of one
    more_word: bool = False    # a whole code word that a longer one begins with (HUNDRED)

    @property
    def complete(self) -> bool:
        return bool(self.word) and len(self.chars) == CHARS

    @property
    def empty(self) -> bool:
        return not (self.dev or self.word or self.chars)

    @property
    def code(self) -> str:
        """The code as check_code reads it: WORD-XXXX-XXXX (DEV- in front of a DEV code)."""
        out = self.word
        if self.in_chars or self.chars:
            out += '-' + self.chars[:4]
        if len(self.chars) > 4:
            out += '-' + self.chars[4:]
        return (DEV + '-' + out) if self.dev else out


def clean_raw(raw) -> str:
    """Upper case, a space or dot read as a dash, nothing but A-Z, 0-9 and
    single dashes, no dash in front."""
    s = re.sub(r'[\s_.]', '-', str(raw or '').upper())
    s = re.sub(r'[^A-Z0-9-]', '', s)
    return re.sub(r'-+', '-', s).lstrip('-')


def _extends(head: str, words) -> bool:
    return any(w.startswith(head) and w != head for w in words)


def _split(head: str, words, ended: bool) -> tuple[str, str, bool]:
    """(word, code characters, the word is done) from what came before any
    dash. ``ended``: a dash came after it, so the word is over."""
    if not head:
        return '', '', False
    if head.isalpha():
        if head in words and (ended or not _extends(head, words)):
            return head, '', True
        if not ended and _extends(head, words):
            return head, '', False                     # still typing a word
    best = max((w for w in words if head.startswith(w) and len(w) < len(head)), key=len, default='')
    if best:
        return best, head[len(best):], True
    digit = next((i for i, c in enumerate(head) if c.isdigit()), None)
    if digit is not None:
        return head[:digit], head[digit:], True
    return head[:WORD_MAX], '', ended


def parse_entry(raw, words) -> Entry:
    """The Entry for the keys typed so far (``raw``). The dashes are drawn by
    the slot, not typed: the word ends by itself when it is a whole code word
    no longer one begins with, or at a dash, a digit, or the first letter no
    code word goes on with."""
    s = clean_raw(raw)
    dev = False
    if s.replace('-', '').startswith(DEV):
        dev, n, i = True, 0, 0
        while n < len(DEV):
            n += s[i] != '-'
            i += 1
        s = s[i:].lstrip('-')
    if '-' in s:
        head, tail = s.split('-', 1)
        word, chars, _done = _split(head, words, True)
        chars += tail.replace('-', '')
        in_chars = bool(word)
    else:
        word, chars, in_chars = _split(s, words, False)
    chars = ''.join(_TYPO.get(c, c) for c in chars)
    chars = ''.join(c for c in chars if c in seeker_codes.ALPHABET)[:CHARS]
    known = word in words
    return Entry(dev=dev, word=word, chars=chars, in_chars=in_chars, known=known,
                 possible=known or _extends(word, words) or not word,
                 more_word=known and not in_chars and _extends(word, words))


def complete_reading(raw, words) -> str | None:
    """Keys typed with no dash that read as a whole code only with a
    shorter code word: TABLE with a code starting T reads, letter by letter,
    as the longer word TABLET and seven characters. Returns the keys as that
    whole code (WORD-XXXXXXXX), or None when there is no such reading."""
    s = clean_raw(raw)
    if '-' in s or s.startswith(DEV):
        return None
    for w in sorted(words, key=len, reverse=True):
        rest = s[len(w):]
        if s.startswith(w) and len(rest) == CHARS:
            chars = ''.join(_TYPO.get(c, c) for c in rest)
            if all(c in seeker_codes.ALPHABET for c in chars):
                return f'{w}-{chars}'
    return None


def type_key(raw: str, ch: str, words) -> tuple[str, str]:
    """(the keys typed, a line to show) after Dad types ``ch``. A key that
    would change nothing on the slot (a ninth code character, a U, a dash
    where one is already drawn) is refused with a word on why."""
    ch = str(ch or '')[:1]
    if not ch or not (ch.isalnum() or ch in '- _.') or not ch.isascii():
        return raw, ''
    before = parse_entry(raw, words)
    if before.complete:
        return raw, "That's the whole code. Press Enter to check it."
    if ch.isdigit() and not before.word and not before.chars:
        return raw, "A code starts with its word, in letters: like DOOM-XXXX-XXXX."
    new = raw + ch
    after = parse_entry(new, words)
    if after == before:
        up = ch.upper()
        if up == 'U' and before.in_chars:
            return raw, "Codes never use the letter U. Is it a V?"
        if ch in '- _.':
            return raw, ''
        if not before.in_chars and len(before.word) >= WORD_MAX:
            return raw, "That word is longer than any code word."
        return raw, ''
    return new, hint(after)


def hint(e: Entry) -> str:
    """The line under the slot while Dad types."""
    if e.dev:
        return "This code starts with DEV. Finish typing it and press Enter."
    if e.complete:
        return "Press Enter to check it!"
    if e.word and not e.in_chars:
        if e.more_word:
            return f"Is the word {e.word}? Type a dash to go on to the code."
        if not e.possible:
            return f"No code starts with {e.word}. Check the word, or type a dash to go on."
    return ''


def backspace(raw: str, words) -> str:
    """The keys typed, less the last one that showed (a dash the slot drew
    anyway goes with it)."""
    raw = clean_raw(raw)
    before = parse_entry(raw, words)
    while raw:
        raw = raw[:-1]
        if parse_entry(raw, words) != before:
            break
    return raw


def entry_from_text(text, words) -> str:
    """The keys for a pasted code (any spacing or case)."""
    raw = ''
    for ch in clean_raw(text):
        raw, _ = type_key(raw, ch, words)
    return raw


# -- the check ------------------------------------------------------------------

def clean_seeker_name(text) -> str:
    """The Seeker name as typed, tidied as the game tidies it (spaces
    collapsed, at most seeker_profile.NAME_MAX characters); '' if it has no
    letter or digit in it."""
    return seeker_profile.clean_name(text) or ''


def validate(kid: str, entry: Entry, seeker: str | None = None, *, data_path=None,
             record_it=True, allow_duplicate=False) -> dict:
    """check_code.verify on the code typed, checked with the Seeker name it
    was earned under (``seeker``; the kid's own name when not given) and
    given to ``kid``. A real code seen for the first time is recorded in the
    ledger under the kid then and there, and its Seeker name remembered for
    the kid. A code that did not match gets a kind word: 'why' is 'short'
    (letters missing), 'word' (no code word is spelled so) or 'letters' (the
    word is right, the rest or the name is not) or 'name' (no Seeker name)."""
    seeker = clean_seeker_name(kid if seeker is None else seeker)
    if not seeker and not entry.dev:
        return {'status': 'fake', 'why': 'name', 'seeker': '', 'kid': kid, 'code': entry.code}
    v = check_code.verify(seeker, entry.code, kid=kid, record_it=record_it, data_path=data_path,
                          allow_duplicate=allow_duplicate)
    v['code'] = entry.code
    if v['status'] == 'new' and v.get('recorded'):
        remember_seeker_name(kid, seeker)
    if v['status'] != 'fake':
        return v
    if not entry.complete:
        v['why'] = 'short'
    elif not entry.known:
        v['why'] = 'word'
    else:
        v['why'] = 'letters'
    return v


def result_lines(v: dict) -> tuple[str, list[str]]:
    """(the title, the lines) of the card for a code that is not a new claim."""
    who = v.get('kid') or v.get('seeker', '')
    if v['status'] == 'already':
        a = v['achievement']
        return ("Already Claimed",
                [f"{who} claimed {a['name']} on {nice_date(v['row'].get('date'))}.",
                 "This reward was given already, so nothing new was written down."])
    if v['status'] == 'duplicate':
        row = v['row']
        return ("Already Used",
                [f"This code was already used for {row.get('seeker', '')} on {nice_date(row.get('date'))}.",
                 "Nothing new was written down.",
                 f"Enter: give it to {who} anyway.   Esc: back."])
    if v['status'] == 'dev':
        return ("A Practice Code",
                ["Codes that start with DEV come from a copy of the game made without Dad's key, "
                 "so they can't be checked. Nothing is wrong with the badge!",
                 "Open the Seeker Profile (F4 on the title screen) in the installed game: "
                 "it shows the real code for every badge already won."])
    why = v.get('why')
    if why == 'name':
        return "No Seeker Name", ["Type the Seeker name the code was earned under: the name on the kid's "
                                  "Seeker page (F4 on the game's title screen)."]
    lines = [f"That code isn't real for the Seeker name {v.get('seeker', '')}. "
             "Check the letters and the name."]
    if why == 'word':
        word = v.get('code', '').split('-')[0]
        lines.append(f"No achievement's code starts with {word}: check the word first.")
    elif why == 'short':
        lines.append("A code is its word, any length (DOOM, QUACK, HUNDRED...), then eight "
                     "letters and numbers: WORD-XXXX-XXXX.")
    else:
        lines.append("The word is right: check the eight letters and numbers after it, and the Seeker "
                     "name (it is on the kid's Seeker page, F4 on the game's title screen).")
    return "Not a Real Code", lines


# -- the reels --------------------------------------------------------------------

REELS = 3
STRIP = 12                  # badges on each reel
LEVER_TIME = 0.45           # the handle comes down before the reels go
SPIN_UP = 0.30              # seconds to full speed
SPEED = 15.0                # badges a second at full speed
SETTLE = 0.60               # the slow-down into each stop
STOPS = (1.45, 2.15, 2.95)  # each reel's stop, in seconds after the lever
HOLD = 0.75                 # the stopped reels are shown this long before the result
_C1 = 1.2                   # the overshoot of the stop's little bounce
_EASE_START = _C1 + 3       # the ease's slope at its start (its speed matches the spin)


def reel_outcome(verdict: dict, pool, rng) -> list[str]:
    """The three badges (achievement ids) on the payline when the reels stop,
    decided by the real check before they spin: three of the code's own
    badge for a real code (new, claimed before, or used for another kid),
    three different ones for any other."""
    if verdict.get('status') in ('new', 'already', 'duplicate'):
        return [verdict['achievement']['id']] * REELS
    return rng.sample(sorted(set(pool)), REELS)


def _ease(u: float) -> float:
    """Ease out with a little overshoot (it lands, rocks past, settles back)."""
    u -= 1.0
    return 1.0 + (_C1 + 1) * u ** 3 + _C1 * u ** 2


def _span(stop: float) -> float:
    """Seconds of full speed a reel's whole run is worth (its distance / speed)."""
    return SPIN_UP / 2 + (stop - SETTLE - SPIN_UP) + SETTLE / _EASE_START


def _motion(t: float, stop: float, speed: float = SPEED) -> float:
    """Badges travelled ``t`` seconds after the lever, by a reel that runs at
    ``speed`` and stops at ``stop``: up to speed, on, then a slow-down that
    lands with a little bounce. The slow-down starts at the spin's own speed."""
    if t <= 0:
        return 0.0
    t = min(t, stop)
    ts = stop - SETTLE

    def cruise(x):
        if x < SPIN_UP:
            return speed * x * x / (2 * SPIN_UP)
        return speed * SPIN_UP / 2 + speed * (x - SPIN_UP)

    if t <= ts:
        return cruise(t)
    return cruise(ts) + speed * SETTLE / _EASE_START * _ease((t - ts) / SETTLE)


def idle_strips(pool, rng, strip_len: int = STRIP) -> list[list[str]]:
    """Each reel's badges as the machine first stands (shown at position 0)."""
    pool = sorted(set(pool))
    return [rng.sample(pool, strip_len) if len(pool) >= strip_len else
            [rng.choice(pool) for _ in range(strip_len)] for _k in range(REELS)]


@dataclass
class ReelPlan:
    outcome: list            # the badge each reel stops on
    strips: list             # each reel's badges, top to bottom
    start: list              # each reel's resting position before the lever (whole badges)
    speeds: list             # each reel's full speed, badges a second
    targets: list            # where each reel stops (the outcome's place on its strip)

    def position(self, k: int, t: float) -> float:
        """Reel ``k``'s position ``t`` seconds after Enter: the badge at
        strips[k][round(position) % len] is on the payline."""
        return self.start[k] + _motion(t - LEVER_TIME, STOPS[k], self.speeds[k])

    def on_payline(self, k: int, t: float) -> str:
        n = len(self.strips[k])
        return self.strips[k][int(math.floor(self.position(k, t) + 0.5)) % n]

    def stopped(self, k: int, t: float) -> bool:
        return t >= LEVER_TIME + STOPS[k]

    @staticmethod
    def done_at() -> float:
        return LEVER_TIME + STOPS[-1]


def plan_reels(outcome, strips, rest=None) -> ReelPlan:
    """The spin onto ``outcome``. Each reel starts where it rests (``rest``,
    whole badges; 0 at first) on its own strip; its outcome badge is put on
    the strip out of sight, a whole number of badges ahead, and its speed
    set (near SPEED) so it stops with that badge on the payline. Nothing in
    the window changes when the lever is pulled."""
    rest = list(rest or [0] * len(outcome))
    new_strips, speeds, targets = [], [], []
    for k, want in enumerate(outcome):
        strip = list(strips[k])
        n = len(strip)
        s0 = int(rest[k]) % n
        span = _span(STOPS[k])
        base = round(SPEED * span)
        for j in sorted(range(-(n // 2), n // 2 + 1), key=abs):
            at = (s0 + base + j) % n
            if min((at - s0) % n, (s0 - at) % n) > 2:       # out of sight at the start
                break
        strip[at] = want
        new_strips.append(strip)
        speeds.append((base + j) / span)
        targets.append(at)
    return ReelPlan(list(outcome), new_strips, [float(int(r) % len(s)) for r, s in zip(rest, strips)],
                    speeds, targets)


# -- the tracker --------------------------------------------------------------------

def claims(seeker: str, rows=None) -> dict:
    """{achievement id: its ledger row} for one kid: the first row for each,
    as dadlib.redeemed reads it."""
    norm = normalise(seeker)
    out: dict = {}
    for row in (dadlib.ledger() if rows is None else rows):
        aid = row.get('achievement')
        if aid and aid not in out and normalise(row.get('seeker', '')) == norm:
            out[aid] = row
    return out


def tracker(seeker: str, *, data_path=None, rows=None) -> dict:
    """The kid's badge library: every achievement in data/achievements.json,
    by category in the game's order (as the Seeker gallery groups them), each
    claimed (with its date) or not, whichever machine the code came from;
    and the counts, claimed of total, overall and by rarity. Each entry
    carries what its detail shows (``detail_lines``) and, for a ladder, its
    rungs."""
    achs = dadlib.achievements(data_path)
    cats = dadlib.categories(data_path)
    rows = dadlib.ledger() if rows is None else rows
    got = claims(seeker, rows)
    order = list(cats) + sorted({a['category'] for a in achs} - set(cats))
    ladders: dict = {}
    for a in achs:
        if a.get('ladder'):
            ladders.setdefault(a['ladder'], []).append(a)
    sections, entries = [], []
    by_rarity = {r: [0, 0] for r in RARITIES}
    for cid in order:
        sec = []
        for a in achs:
            if a['category'] != cid:
                continue
            row = got.get(a['id'])
            e = {'id': a['id'], 'name': a['name'], 'rarity': a['rarity'], 'art': a['art'],
                 'category': cid, 'category_name': cats.get(cid, cid.title()),
                 'claimed': row is not None, 'date': (row or {}).get('date', ''),
                 'hint': a.get('hint', ''), 'text': a.get('unlocked_text', ''),
                 'tier': None, 'ladder': None}
            if a.get('ladder'):
                rungs = sorted(ladders[a['ladder']], key=lambda x: int(x.get('tier', 1)))
                e['tier'] = int(a.get('tier', 1))
                e['ladder'] = [{'id': x['id'], 'rarity': x['rarity'], 'claimed': x['id'] in got}
                               for x in rungs]
            sec.append(e)
            tally = by_rarity.setdefault(a['rarity'], [0, 0])
            tally[1] += 1
            tally[0] += e['claimed']
        if sec:
            sections.append({'id': cid, 'name': cats.get(cid, cid.title()), 'entries': sec,
                             'claimed': sum(e['claimed'] for e in sec), 'total': len(sec)})
            entries += sec
    return {'seeker': seeker, 'sections': sections, 'entries': entries,
            'earned': earned(entries, rows, seeker),
            'by_rarity': {r: tuple(v) for r, v in by_rarity.items()},
            'claimed': sum(e['claimed'] for e in entries), 'total': len(entries)}


def earned(entries, rows, seeker) -> list[dict]:
    """The claimed entries, newest first: by the date claimed, and on one day
    by the order they were written in the ledger (the last written first)."""
    norm = normalise(seeker)
    order = {}
    for i, row in enumerate(rows):
        if normalise(row.get('seeker', '')) == norm and row.get('achievement') not in order:
            order[row.get('achievement')] = i
    mine = [e for e in entries if e['claimed']]
    return sorted(mine, key=lambda e: (str(e['date']), order.get(e['id'], -1)), reverse=True)


def detail_lines(e: dict) -> list[tuple[str, str]]:
    """What a badge's detail says, as (text, kind) in order, mirroring the
    Seeker gallery's badge page: the name; rarity and frame; category; when
    it was claimed; then its unlocked text once claimed, or its hint until
    then (a deep secret's hint is "???", as in the game)."""
    out = [(e['name'], 'name'),
           (f"{RARITY_NAMES.get(e['rarity'], '')}  ·  {FRAME_NAMES.get(e['rarity'], '')} Frame", 'rarity'),
           (e.get('category_name', ''), 'category')]
    if e['claimed']:
        out.append((f"Claimed on {nice_date(e['date'])}", 'claimed'))
        out.append((e.get('text', ''), 'text'))
    else:
        out.append(("Not claimed yet", 'locked'))
        out.append(("Hint", 'head'))
        out.append((e.get('hint', '') or '???', 'hint'))
    return out


def grid_rows(sections, cols: int) -> list[list[int]]:
    """The library grid's rows, as indexes into the flat entry list: each
    category starts a row of its own, ``cols`` badges a row."""
    rows, base = [], 0
    for sec in sections:
        n = len(sec['entries'])
        for start in range(0, n, max(1, cols)):
            rows.append(list(range(base + start, base + min(n, start + cols))))
        base += n
    return rows


def grid_move(sel: int, step: str, rows) -> int:
    """The badge picked after one arrow: 'left' and 'right' run on through
    the whole library; 'up' and 'down' keep the column (to the end of a
    shorter row)."""
    total = sum(len(r) for r in rows)
    if not total:
        return 0
    sel = max(0, min(sel, total - 1))
    if step == 'left':
        return max(0, sel - 1)
    if step == 'right':
        return min(total - 1, sel + 1)
    ri = next(i for i, r in enumerate(rows) if sel in r)
    col = rows[ri].index(sel)
    to = ri + (-1 if step == 'up' else 1)
    if not 0 <= to < len(rows):
        return sel
    return rows[to][min(col, len(rows[to]) - 1)]


def section_start(sections, sel: int, step: int) -> int:
    """The first badge of the category before (``step`` -1) or after (+1)
    the one ``sel`` is in."""
    starts, base = [], 0
    for sec in sections:
        starts.append(base)
        base += len(sec['entries'])
    if not starts:
        return 0
    cur = max(i for i, s in enumerate(starts) if s <= max(0, sel))
    return starts[max(0, min(len(starts) - 1, cur + step))]


# -- Dad's settings ---------------------------------------------------------------------

def settings_path() -> str:
    return os.path.join(dadlib.dad_dir(), 'validator.json')


def load_settings() -> dict:
    """{'sound': bool}: the validator's own (the game's settings are never read)."""
    out = {'sound': True}
    try:
        with open(settings_path(), encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get('sound'), bool):
            out['sound'] = data['sound']
    except (OSError, ValueError):
        pass
    return out


def save_settings(**changes) -> dict:
    data = load_settings()
    data.update(changes)
    path = settings_path()
    try:
        with open(path + '.tmp', 'w', encoding='utf-8') as f:
            json.dump(data, f)
        os.replace(path + '.tmp', path)
    except OSError:
        pass
    return data


# -- the reward ----------------------------------------------------------------------

REWARD_BY_RARITY = {
    'common': "A bronze badge! A small reward, Dad's choice.",
    'rare': "A silver badge! A good reward, Dad's choice.",
    'epic': "A gold badge! A big reward, Dad's choice.",
    'legendary': "A violet badge! A legendary reward, Dad's choice.",
}

# Tests point this at a file of their own (None: tools/dad/achievement_notes.json).
_NOTES_PATH: str | None = None


def _reward_tables() -> tuple[dict, dict]:
    """({achievement id: reward}, {rarity: reward}) from the 'rewards' and
    'rewards_by_rarity' keys of achievement_notes.json, and the same keys in
    Documents\\PQ_Dad\\rewards.json (outside the repo), which wins."""
    by_id, by_rarity = {}, {}
    paths = [_NOTES_PATH or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         'achievement_notes.json'),
             os.path.join(dadlib.dad_dir(), 'rewards.json')]
    for path in paths:
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            by_id.update({k: v for k, v in dict(data.get('rewards') or {}).items() if isinstance(v, str)})
            by_rarity.update({k: v for k, v in dict(data.get('rewards_by_rarity') or {}).items()
                              if isinstance(v, str)})
    return by_id, by_rarity


def reward_line(achievement: dict) -> str:
    """The reward for this badge: its own note if Dad wrote one, else the
    line for its rarity."""
    by_id, by_rarity = _reward_tables()
    if by_id.get(achievement['id'], '').strip():
        return by_id[achievement['id']].strip()
    r = achievement.get('rarity', 'common')
    return (by_rarity.get(r) or REWARD_BY_RARITY.get(r) or REWARD_BY_RARITY['common']).strip()


# -- the key ---------------------------------------------------------------------------

def key_ready() -> bool:
    """True when Dad's real key is installed (dadlib.require_real_key passes)."""
    try:
        dadlib.require_real_key()
    except SystemExit:
        return False
    return True


def key_help() -> list[str]:
    return ["No reward key is installed on this computer, so codes can't be checked yet.",
            "If you have a saved copy of _dad_key.py, put it back in this folder:",
            os.path.dirname(dadlib.KEY_FILE),
            "First time ever? Make one with:  py tools/dad/make_key.py   (the tracker works without it)"]
