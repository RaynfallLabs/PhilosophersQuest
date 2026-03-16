"""
Centralised path resolution — works both during development and when
frozen by PyInstaller into a standalone Windows executable.

Usage:
    from paths import data_path, save_dir

    monsters = data_path('data', 'monsters.json')
    save     = os.path.join(save_dir(), 'save_alice.pkl')
"""
import os
import sys


def _root() -> str:
    """Return the project root — sys._MEIPASS when frozen, otherwise src/.."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS          # PyInstaller extracts everything here
    return os.path.join(os.path.dirname(__file__), '..')


def data_path(*parts: str) -> str:
    """Absolute path to a read-only game asset / data file."""
    return os.path.normpath(os.path.join(_root(), *parts))


def save_dir() -> str:
    """Writable directory for save files.

    Frozen  → %APPDATA%\\PhilosophersQuest\\
    Dev     → project root (same behaviour as before)
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
