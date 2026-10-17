"""The hero's chronicle as structured entries (DEEDS_KARMA_DESIGN.md section 7.3).

Pure module. ``Game._chronicle`` is a list of entries::

    {"seq", "floor", "turn", "kind", "text", "person", "deed", "cause",
     "thread", "once"}

``Game._log_chronicle(text)`` stays as a shim for the ~94 old call sites
(kind ``discovery``) until Phase 4 migrates them. The display is unchanged:
:func:`display_text` renders an entry exactly as the old flat string was,
``"text (L#)"``.
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
               deed=None, cause=None, thread=None, once=None) -> dict:
    if kind not in KINDS:
        raise ValueError(f'unknown chronicle kind: {kind!r}')
    return {'seq': seq, 'floor': floor, 'turn': turn, 'kind': kind, 'text': str(text),
            'person': person, 'deed': deed, 'cause': cause, 'thread': thread,
            'once': once}


def chron(game, kind: str, text: str, *, person=None, deed=None, cause=None,
          thread=None, once=None):
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
                       thread=thread, once=once)
    log = getattr(game, '_chronicle', None)
    if not isinstance(log, list):
        log = []
        try:
            game._chronicle = log
        except Exception:
            pass
    log.append(entry)
    return entry


def text_of(entry) -> str:
    if isinstance(entry, dict):
        return str(entry.get('text', ''))
    return str(entry)


def display_text(entry) -> str:
    """The line as the Chronicle tab has always shown it: ``"text (L#)"``."""
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
