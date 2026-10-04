"""Display-name capitalisation.

Data files author most item / monster names in lowercase ("ring of magic
resist", "giant rat"). ``proper_name`` turns those into polished title
case, and ``ProperNameAttr`` applies it to the name attributes of items
and monsters, so every screen and every log line shows the same
capitalised name without each call site having to remember to fix it.

Pure string logic -- no pygame, no game imports -- so data classes can use
it without import cycles.
"""
from functools import lru_cache

# Words that stay lowercase inside a name (never at the start).
_SMALL_WORDS = frozenset({
    'a', 'an', 'the', 'of', 'and', 'or', 'nor', 'in', 'on', 'at', 'to',
    'for', 'with', 'by', 'from', 'vs',
})


def _cap_piece(piece: str) -> str:
    """Capitalise the first letter of ``piece`` if the piece is entirely
    lowercase; leave anything already carrying capitals alone ("STR+1",
    "McCoy"). Only the first letter is touched, so "john's" -> "John's"
    (``str.title`` would give "John'S")."""
    if piece != piece.lower():
        return piece
    for i, ch in enumerate(piece):
        if ch.isalpha():
            return piece[:i] + ch.upper() + piece[i + 1:]
    return piece


@lru_cache(maxsize=8192)
def _proper_name_cached(name: str) -> str:
    out = []
    for idx, word in enumerate(name.split(' ')):
        if idx > 0 and word in _SMALL_WORDS:
            out.append(word)
            continue
        out.append('-'.join(_cap_piece(p) for p in word.split('-')))
    return ' '.join(out)


def proper_name(name) -> str:
    """Return ``name`` in title case: "ring of magic resist" ->
    "Ring of Magic Resist", "ox-hide shield" -> "Ox-Hide Shield".

    Small joining words stay lowercase except at the start. Words that
    already contain capitals are left untouched, so hand-authored names
    ("Ring of the Nibelung", "Amulet of STR+1") pass through unchanged and
    the function is safe to apply more than once.
    """
    if not isinstance(name, str) or not name:
        return name
    return _proper_name_cached(name)


class ProperNameAttr:
    """Descriptor that keeps a name attribute in ``proper_name`` form.

    Used for ``Item.name`` / ``Item.unidentified_name`` / ``Monster.name``:
    every assignment is normalised on the way in, and reads normalise too,
    so objects unpickled from saves written before this existed (whose
    ``__dict__`` still holds the lowercase string) display correctly
    without a save migration. The value lives in the instance ``__dict__``
    under the same key, so pickles stay compatible in both directions.
    """

    def __init__(self, key: str):
        self.key = key

    def __get__(self, obj, owner=None):
        if obj is None:
            return self
        try:
            return proper_name(obj.__dict__[self.key])
        except KeyError:
            raise AttributeError(self.key) from None

    def __set__(self, obj, value):
        obj.__dict__[self.key] = proper_name(value)
