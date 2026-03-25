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


def fmt_id(raw: str) -> str:
    """Convert a snake_case identifier to a display string: 'wild_swing' -> 'wild swing'."""
    return raw.replace('_', ' ')


def a_or_an(name: str) -> str:
    """Return 'a Name' or 'an Name' based on the first letter. Handles proper nouns."""
    if not name:
        return name
    first = name.lstrip('{').lstrip()  # skip BUC tags like {blessed}
    article = 'an' if first[0:1].lower() in 'aeiou' else 'a'
    return f"{article} {name}"


def save_dir() -> str:
    """Writable directory for save files.

    Frozen  -> %APPDATA%\\PhilosophersQuest\\
    Dev     -> project root (same behaviour as before)
    """
    if getattr(sys, 'frozen', False):
        base = os.path.join(
            os.environ.get('APPDATA', os.path.expanduser('~')),
            'PhilosophersQuest'
        )
    else:
        base = _root()
    os.makedirs(base, exist_ok=True)
    return base
