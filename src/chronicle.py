"""The hero's chronicle as structured entries (DEEDS_KARMA_DESIGN.md section 7.3).

Pure module. ``Game._chronicle`` is a list of entries::

    {"seq", "floor", "turn", "kind", "text", "person", "deed", "cause",
     "thread", "once"}

Every call site writes through ``Game._chron(kind, text, ...)``; the old
``Game._log_chronicle(text)`` stays as a shim (kind ``discovery``).

Phase 4 (section 7.5) adds the views the Journal and the end-of-run "Your
Story" page draw from, all pure functions over the register and the entry
list: :func:`oath_sections`, :func:`deed_rows`, :func:`people_rows`,
:func:`timeline_groups`, :func:`your_story` and :func:`roads_not_taken`
(computed from THIS run only: Brandon's decision 4). And :func:`lint`, the
voice rules every chronicle line must pass (section 7.2,
``tests/test_chronicle_voice.py``).
"""
from __future__ import annotations

import re

import deeds

KINDS = frozenset({
    'oath', 'deed', 'consequence', 'person', 'notice', 'loss', 'soul', 'boss',
    'milestone', 'discovery', 'legacy',
})

_LEGACY_FLOOR = re.compile(r' \(L(\d+)\)$')


def make_entry(*, seq: int, floor, turn: int, kind: str, text: str, person=None,
               deed=None, cause=None, thread=None, once=None, source=None) -> dict:
    if kind not in KINDS:
        raise ValueError(f'unknown chronicle kind: {kind!r}')
    e = {'seq': seq, 'floor': floor, 'turn': turn, 'kind': kind, 'text': str(text),
         'person': person, 'deed': deed, 'cause': cause, 'thread': thread,
         'once': once}
    if source is not None:
        e['source'] = source          # the encounter tag a deed or consequence came from
    return e


def in_sentence(name) -> str:
    """A named thing as it reads mid-sentence in a Journal line (JNL-13):
    "The Bull's Horn" -> "the Bull's Horn", "A Cat's Footfall" -> "a Cat's
    Footfall", "Chapel of the Grail" -> "the Chapel of the Grail". A name
    that opens with a possessive ("Pandora's Coffer") is left as it is."""
    name = str(name or '').strip()
    if not name:
        return name
    first, _sp, rest = name.partition(' ')
    if first in ('The', 'A', 'An') and rest:
        return f"{first.lower()} {rest}"
    if first.lower() in ('the', 'a', 'an') or first.endswith(("'s", "s'")):
        return name
    return f"the {name}"


def chron(game, kind: str, text: str, *, person=None, deed=None, cause=None,
          thread=None, once=None, source=None):
    """Append an entry to ``game._chronicle`` and return it. With ``once``,
    nothing is written if that key was already logged this run (the key is
    kept in ``game._deeds['flags']``)."""
    reg = deeds.ensure_register(game)
    if once is not None and once in reg['flags']:
        return None
    seq = deeds.next_seq(reg)
    if once is not None:
        reg['flags'][once] = seq
    entry = make_entry(seq=seq, floor=getattr(game, 'dungeon_level', None),
                       turn=int(getattr(game, 'turn_count', 0) or 0), kind=kind,
                       text=text, person=person, deed=deed, cause=cause,
                       thread=thread, once=once, source=source)
    log = getattr(game, '_chronicle', None)
    if not isinstance(log, list):
        log = []
        try:
            game._chronicle = log
        except Exception:
            pass
    log.append(entry)
    return entry


def once_count(game, prefix: str) -> int:
    """How many ``once`` keys starting with ``prefix`` were logged this run
    (the first three spells learned, say)."""
    reg = deeds.ensure_register(game)
    return sum(1 for k in reg['flags'] if str(k).startswith(prefix))


def text_of(entry) -> str:
    if isinstance(entry, dict):
        return str(entry.get('text', ''))
    return str(entry)


def display_text(entry) -> str:
    """The line in the old flat form, ``"text (L#)"`` (old saves held it;
    the Journal shows the floor in its own column or header instead)."""
    if not isinstance(entry, dict):
        return str(entry)
    floor = entry.get('floor')
    text = str(entry.get('text', ''))
    return f'{text} (L{floor})' if floor is not None else text


def migrate(saved) -> list:
    """A loaded chronicle as entries. Old saves hold plain strings ending in
    ``" (L#)"``: each becomes a ``legacy`` entry with its floor parsed and the
    suffix stripped, so it still displays exactly as before."""
    out = []
    for e in saved or ():
        if isinstance(e, dict):
            out.append(e)
            continue
        s = str(e)
        m = _LEGACY_FLOOR.search(s)
        floor = int(m.group(1)) if m else None
        text = s[:m.start()] if m else s
        out.append(make_entry(seq=0, floor=floor, turn=0, kind='legacy', text=text))
    return out


# ---------------------------------------------------------------- the voice lint

STAT_NAMES = ('STR', 'DEX', 'CON', 'INT', 'WIS', 'PER')

# Proper nouns that happen to hold a digit (a street number is a name, not a
# statistic). Kept tiny on purpose.
DIGIT_NAMES = ('221B',)

# A floor count written out in words is still a floor number ("sixty floors
# off", "the ninety-second floor"); "a few floors down" is not (CON-20).
_NUM_WORD = (r'(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|'
             r'thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|'
             r'thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)')
_ORD_WORD = (r'(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|'
             r'eleventh|twelfth|\w+teenth|\w+ieth|hundredth)')
_FLOOR_COUNT = (rf'{_NUM_WORD}(?:[- ]{_NUM_WORD})*\s+floors?|'
                rf'(?:{_NUM_WORD}-)?{_ORD_WORD}\s+floor')

_GAME_TERMS = re.compile(
    r'\b(karma|quiz|quizzes|tier|tiers|HP|MP|SP|XP|AC|per turn|every turn|'
    r'auto-?pass(es)?|milestone|unlocked|identifies|' + _FLOOR_COUNT + r')\b', re.I)


def lint(text) -> list:
    """What is wrong with a chronicle line by the section 7.2 voice rules
    (empty when it passes). ``{placeholders}`` are checked as plain words."""
    line = str(text or '')
    bare = line
    for name in DIGIT_NAMES:
        bare = bare.replace(name, 'X')
    bad = []
    if re.search(r'\bL\d+', line) or re.search(r'\b(Level|Floor|Depth) \d+', line, re.I):
        bad.append('floor number')
    if re.search(r'\d', bare):
        bad.append('number')
    if '!' in re.sub(r'"[^"]*"', '', line):
        bad.append('exclamation')
    if re.search(r'\+\d', line):
        bad.append('+N')
    if any(re.search(rf'\b{s}\b', line) for s in STAT_NAMES):
        bad.append('stat name')
    if _GAME_TERMS.search(line):
        bad.append('game term')
    if '...' in line or '…' in line:
        bad.append('ellipsis')
    if re.search(r'(?<!-)--(?!-)', line):
        bad.append('ASCII dash')
    if len(line) > 220:
        bad.append('too long')
    if not line.strip():
        bad.append('empty')
    return bad


# ---------------------------------------------------------------- number words

_ONES = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
         'nine', 'ten', 'eleven', 'twelve')


def number_word(n: int) -> str:
    """``3`` -> ``"three"`` (the journal never prints digits); past twelve,
    ``"many"``."""
    n = int(n)
    return _ONES[n] if 0 <= n < len(_ONES) else 'many'


# ---------------------------------------------------------------- the Journal

def entries_of(game) -> list:
    """The chronicle as entries, whatever an old object holds."""
    return migrate(getattr(game, '_chronicle', None) or [])


def _label(floor, label_fn) -> str:
    if floor is None:
        return ''
    if label_fn is not None:
        return label_fn(floor)
    return f'Floor {floor}'


VERDICTS = (('kept', 'Kept'), ('broken', 'Broken'), ('lapsed', 'Let Go'),
            ('released', 'Released'))


def oath_text(oath: dict) -> str:
    """``"To Sir Aldric: carry his lodestone to an altar."``"""
    from naming import proper_name
    to = str(oath.get('to') or '').strip()
    # A name is capitalised ("Sir Aldric"); a description is left as
    # written ("a dying courier", not "A Dying Courier").
    if to.split(' ', 1)[0] not in ('a', 'an', 'the'):
        to = proper_name(to)
    what = str(oath.get('what') or oath.get('id') or '').strip()
    if what and what[0].isupper() and not what[:2].isupper():
        what = what[0].lower() + what[1:]
    if not to:
        return what[:1].upper() + what[1:]
    return f'To {to}: {what}'


def oath_sections(reg: dict) -> dict:
    """The Oaths tab: ``{"open": [oath], "resolved": [(verdict, oath)],
    "unfinished": [hint]}``. Open oaths in the order sworn; resolved ones
    grouped Kept, Broken, Let Go, Released; then every open thread's hint."""
    oaths = sorted((reg or {}).get('oaths', {}).values(),
                   key=lambda o: int(o.get('made_seq') or 0))
    open_ = [o for o in oaths if o.get('status') == 'open']
    resolved = []
    for status, word in VERDICTS:
        resolved += [(word, o) for o in oaths if o.get('status') == status]
    threads = sorted((reg or {}).get('threads', {}).values(),
                     key=lambda t: int(t.get('opened_floor') or 0))
    unfinished = [t['hint'] for t in threads
                  if t.get('status') == 'open' and t.get('hint')]
    return {'open': open_, 'resolved': resolved, 'unfinished': unfinished}


DEED_KINDS = ('deed', 'consequence', 'loss', 'notice')


def deed_rows(entries) -> list:
    """The Deeds tab: ``[(entry, depth)]`` of deed, consequence, loss and
    notice entries in order, each consequence placed (depth 1) under its
    cause: the entry whose ``seq`` is the cause, else the latest deed from
    the same encounter (``source``) written before it."""
    rows = [e for e in entries if isinstance(e, dict) and e.get('kind') in DEED_KINDS]
    by_seq = {e.get('seq'): e for e in rows if e.get('seq')}
    parent_of = {}
    for i, e in enumerate(rows):
        if e.get('kind') != 'consequence':
            continue
        p = by_seq.get(e.get('cause')) if e.get('cause') is not None else None
        if (p is None or p is e) and e.get('source'):
            p = next((c for c in reversed(rows[:i])
                      if c.get('kind') != 'consequence' and c.get('source') == e['source']),
                     None)
        if p is not None and p is not e and p.get('kind') != 'consequence':
            parent_of[id(e)] = p
    children = {}
    for e in rows:
        p = parent_of.get(id(e))
        if p is not None:
            children.setdefault(id(p), []).append(e)
    out = []
    for e in rows:
        if id(e) in parent_of:
            continue
        out.append((e, 0))
        out += [(c, 1) for c in children.get(id(e), ())]
    return out


_PERSON_WORDS = {
    'saved': 'Saved', 'lost': 'Lost', 'unmasked': 'Unmasked',
    'aided': 'Helped', 'wronged': 'Wronged', 'spared': 'Spared', 'gone': 'Gone',
    'met': 'Met',
}


def person_status_words(p: dict) -> str:
    """How a person stands, in words (never a number)."""
    status = p.get('status') or 'met'
    if status in ('unmasked', 'lost', 'saved', 'gone'):
        return _PERSON_WORDS[status]
    if p.get('owes'):
        return 'Owes You'
    if p.get('owed'):
        return 'You Owe a Debt'
    return _PERSON_WORDS.get(status, str(status).replace('_', ' ').title())


def _shown_name(p: dict) -> str:
    """The person's name once the hero has heard it, else the scene's title
    for them ("Courteous Giant", not "Utgarda-Loki": JNL-04)."""
    if p.get('known', True) is False and p.get('title'):
        return p['title']
    return p.get('name') or p.get('id') or ''


def people_rows(reg: dict, label_fn=None) -> list:
    """The People tab: one dict per person met, in the order first met:
    ``{"name", "where", "status", "last"}``."""
    from naming import proper_name
    people = list((reg or {}).get('people', {}).values())     # dicts keep insertion order
    return [{'name': proper_name(str(_shown_name(p))),
             'where': _label(p.get('first_floor'), label_fn) if p.get('first_floor') else '',
             'status': person_status_words(p),
             'last': str(p.get('last_line') or '')}
            for p in people]


def timeline_groups(entries, label_fn=None) -> list:
    """The Timeline tab: ``[(floor label, [entries])]``, a new header each
    time the floor changes (a walk back upstairs gets its own header)."""
    groups = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        lab = _label(e.get('floor'), label_fn) or 'Before the Descent'
        if groups and groups[-1][0] == lab:
            groups[-1][1].append(e)
        else:
            groups.append((lab, [e]))
    return groups


# ---------------------------------------------------------------- roads

def record_choice(reg: dict, enc: dict, index) -> None:
    """At an encounter's commit point: remember which option was taken and
    the road hint of every option it offered, so the end screen can show
    the roads NOT taken this run (Brandon's decision 4: nothing is kept
    across runs). Hidden options count too: the encounter has been met."""
    tag = str((enc or {}).get('tag') or '')
    if not tag:
        return
    chosen = reg.setdefault('chosen', {})
    picked = chosen.setdefault(tag, [])
    if index is not None and index not in picked:
        picked.append(index)
    roads = reg.setdefault('roads', {})
    if tag not in roads:
        seen = []
        for i, opt in enumerate((enc or {}).get('options') or ()):
            road = opt.get('road') if isinstance(opt, dict) else None
            if isinstance(road, dict) and road.get('hint'):
                seen.append({'index': i, 'id': str(road.get('id') or f'{tag}.{i}'),
                             'hint': str(road['hint'])})
        roads[tag] = {'order': len(roads), 'options': seen}


def roads_not_taken(reg: dict, limit: int = 4) -> list:
    """Up to ``limit`` hints from the options the hero did not take in the
    encounters met this run: the latest encounters first, one road from each
    before a second from any, never a road whose id the hero took."""
    reg = reg or {}
    chosen = reg.get('chosen') or {}
    roads = reg.get('roads') or {}
    taken_ids = set()
    for tag, info in roads.items():
        for r in info.get('options', ()):
            if r['index'] in chosen.get(tag, ()):
                taken_ids.add(r['id'])
    per_enc = []
    for tag, info in sorted(roads.items(), key=lambda kv: -int(kv[1].get('order') or 0)):
        left = [r for r in info.get('options', ())
                if r['index'] not in chosen.get(tag, ()) and r['id'] not in taken_ids]
        if left:
            per_enc.append(left)
    out, seen = [], set()
    depth = 0
    while len(out) < limit and any(len(lst) > depth for lst in per_enc):
        for lst in per_enc:
            if depth < len(lst) and len(out) < limit and lst[depth]['hint'] not in seen:
                seen.add(lst[depth]['hint'])
                out.append(lst[depth]['hint'])
        depth += 1
    return out


# ---------------------------------------------------------------- Your Story

def oath_summary(reg: dict) -> str:
    """The promises, in words: "I swore four promises: I kept two, broke one
    and let one go." (No numbers on screen.)"""
    oaths = list((reg or {}).get('oaths', {}).values())
    if not oaths:
        return "I made no promises down here, which kept things simple."
    n = {s: sum(1 for o in oaths if o.get('status') == s)
         for s in ('open', 'kept', 'broken', 'lapsed', 'released')}
    parts = []
    if n['kept']:
        parts.append(f"kept {number_word(n['kept'])}")
    if n['broken']:
        parts.append(f"broke {number_word(n['broken'])}")
    let_go = n['lapsed'] + n['released']
    if let_go:
        parts.append(f"let {number_word(let_go)} go")
    total = len(oaths)
    noun = 'promise' if total == 1 else 'promises'
    if not parts:
        return (f"I swore {number_word(total)} {noun} and was still carrying "
                f"{'it' if total == 1 else 'them'} at the end.")
    body = parts[0] if len(parts) == 1 else ', '.join(parts[:-1]) + ' and ' + parts[-1]
    if total == 1:
        line = f"I swore one promise, and I {body.split(' ')[0]} it." if not let_go \
            else "I swore one promise, and I let it go."
    else:
        line = f"I swore {number_word(total)} {noun}: I {body}."
    if n['open']:
        rest = 'one' if n['open'] == 1 else number_word(n['open'])
        line += f" I was still carrying {rest} at the end."
    return line


HIGHLIGHT_KINDS = ('soul', 'notice', 'consequence')
_FALLBACK_KINDS = ('boss', 'loss', 'deed', 'oath', 'person', 'discovery', 'milestone',
                   'legacy')   # a pre-Journal save's lines, last (JNL-10)


def highlights(entries, limit: int = 3) -> list:
    """Up to three lines worth retelling: the latest ``soul``, ``notice`` and
    ``consequence`` entries, topped up with the latest boss, loss and deed
    lines when the run had fewer. In the order they happened."""
    entries = [e for e in entries if isinstance(e, dict) and e.get('text')]
    picked = []
    for kind in HIGHLIGHT_KINDS:
        e = next((x for x in reversed(entries) if x.get('kind') == kind), None)
        if e is not None:
            picked.append(e)
    for kind in _FALLBACK_KINDS:
        if len(picked) >= limit:
            break
        e = next((x for x in reversed(entries)
                  if x.get('kind') == kind and not any(x is p for p in picked)), None)
        if e is not None:
            picked.append(e)
    picked = picked[:limit]
    order = {id(e): i for i, e in enumerate(entries)}
    return sorted(picked, key=lambda e: order.get(id(e), 0))


def your_story(reg: dict, entries, limit_roads: int = 4) -> dict:
    """Everything the "Your Story" page shows: ``{"oaths": sentence,
    "highlights": [entry], "roads": [hint]}``."""
    return {'oaths': oath_summary(reg),
            'highlights': highlights(entries),
            'roads': roads_not_taken(reg, limit_roads)}
