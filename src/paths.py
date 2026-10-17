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
    """Return 'a Name' or 'an Name' based on the first letter. Handles proper nouns."""
    if not name:
        return name
    first = name.lstrip('{').lstrip()  # skip BUC tags like {blessed}
    article = 'an' if first[0:1].lower() in 'aeiou' else 'a'
    return f"{article} {name}"


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
