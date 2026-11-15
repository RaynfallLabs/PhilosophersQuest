"""
Centralised path resolution -- works both during development and when
frozen by PyInstaller into a standalone Windows executable.

Usage:
    from paths import data_path, save_dir

    monsters = data_path('data', 'monsters.json')
    save     = os.path.join(save_dir(), 'save_alice.pkl')
"""
import os
import sys


def _root() -> str:
    """Return the project root -- sys._MEIPASS when frozen, otherwise src/.."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS          # PyInstaller extracts everything here
    return os.path.join(os.path.dirname(__file__), '..')


def data_path(*parts: str) -> str:
    """Absolute path to a read-only game asset / data file."""
    return os.path.normpath(os.path.join(_root(), *parts))


def a_or_an(name: str) -> str:
    """Return 'a Name' or 'an Name' based on the first letter.

    A name that brings its own article (an unknown piece's appearance, "A
    Rough Amber Pelt") gets the one it needs: "a Rough Amber Pelt", never
    "an A Rough Amber Pelt" (bug bash 3.5.1 E). A counted name ("5 Gold
    Coins"), one led by "The", and a plural thing ("Rough Cloth Gloves",
    "Boots of Hermes", never "a Rough Cloth Gloves") take none."""
    if not name:
        return name
    first = name.lstrip('{').lstrip()  # skip BUC tags like {blessed}
    low = first.lower()
    if low.startswith('the ') or first[:1].isdigit():
        return name
    for art in ('a ', 'an '):
        if low.startswith(art):
            name = first = first[len(art):].lstrip()
            break
    if _plural_thing(first):
        return name
    article = 'an' if first[0:1].lower() in 'aeiou' else 'a'
    return f"{article} {name}"


# A head noun that ends in -s and is one thing (the Aegis, a haggis, the
# Caduceus, a labrys, the Ouroboros, a pithos; a Cyclops, an akinakes).
_ONE_THING_ENDS = ('ss', 'us', 'is', 'os', 'ys', 'as')
_ONE_THING_WORDS = frozenset({'cyclops', 'akinakes'})


def _plural_thing(name: str) -> bool:
    """Is the thing named plural ("Rough Cloth Gloves", "Boots of Hermes",
    "Lamb Skewers")? Read from its head noun: the last word before any
    " of ", a stack's " x4" left off."""
    import re
    head = re.sub(r'\s+x\d+$', '', str(name)).split(' of ')[0].split()
    word = head[-1].lower() if head else ''
    return (word.endswith('s') and not word.endswith(_ONE_THING_ENDS)
            and word not in _ONE_THING_WORDS)


# Tests point this at a temp dir (tests/conftest.py) so a pytest run never
# writes saves, high scores, settings, bones or answer times into the
# developer's real dev save dir. Replaces the DEV location only; the frozen
# paths below are never overridden.
_DEV_SAVE_DIR_OVERRIDE = None


def save_dir() -> str:
    """Writable directory for save files.

    Frozen Windows -> %APPDATA%\\PhilosophersQuest\\
    Frozen Linux   -> $XDG_DATA_HOME/PhilosophersQuest/ or ~/.local/share/PhilosophersQuest/
    Frozen macOS   -> ~/Library/Application Support/PhilosophersQuest/
    Dev            -> project root (unchanged), or _DEV_SAVE_DIR_OVERRIDE
    """
    if getattr(sys, 'frozen', False):
        if sys.platform == 'win32':
            base = os.path.join(
                os.environ.get('APPDATA', os.path.expanduser('~')),
                'PhilosophersQuest',
            )
        elif sys.platform == 'darwin':
            base = os.path.join(
                os.path.expanduser('~'),
                'Library', 'Application Support', 'PhilosophersQuest',
            )
        else:  # linux / bsd / other unix
            xdg = os.environ.get('XDG_DATA_HOME') or os.path.join(
                os.path.expanduser('~'), '.local', 'share',
            )
            base = os.path.join(xdg, 'PhilosophersQuest')
    else:
        base = _DEV_SAVE_DIR_OVERRIDE or _root()
    os.makedirs(base, exist_ok=True)
    return base
