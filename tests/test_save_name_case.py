"""Hotfix 3.2.1: a secret build's save is found however its name is typed.

v3.2.0 named save files case-sensitively ("Bob" and "bob" are two heroes)
but stored a secret build under its proper-case name ("fianna" -> "Fianna").
The title screen looked the save up by the raw typed text, so typing
"fianna" missed save_+fianna.pkl, started a NEW Fianna and autosaved over
the real save. Brandon hit it with Ash Ketchum on the Windows build."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

import paths  # noqa: E402
import save_system  # noqa: E402
from naming import hero_name  # noqa: E402
from welcome_screen import SECRET_BUILDS  # noqa: E402


def test_hero_name_proper_cases_secret_builds_only():
    assert hero_name('fianna', SECRET_BUILDS['fianna']) == 'Fianna'
    assert hero_name('  ash   ketchum ', SECRET_BUILDS['ash ketchum']) == 'Ash Ketchum'
    assert hero_name('ASH KETCHUM', SECRET_BUILDS['ash ketchum']) == 'Ash Ketchum'
    assert hero_name('bob', None) == 'bob'          # an ordinary name is kept as typed
    assert hero_name('Bob', None) == 'Bob'


def test_a_lower_case_secret_name_finds_its_proper_case_save(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, '_DEV_SAVE_DIR_OVERRIDE', str(tmp_path))
    real = save_system._save_path('Fianna')           # where the game saved her
    Path(real).write_bytes(b'not empty')
    assert not save_system.save_exists('fianna')     # the v3.2.0 lookup missed it
    assert save_system.save_exists(hero_name('fianna', SECRET_BUILDS['fianna']))


def test_the_title_screen_looks_saves_up_by_the_stored_name():
    src = (ROOT / 'src' / 'main.py').read_text(encoding='utf-8')
    fix = src.index('player_name = hero_name(player_name, secret_build)')
    look = src.index('if save_exists(player_name):')
    assert fix < look, 'the save must be looked up by hero_name, not the raw typed text'
    welcome = (ROOT / 'src' / 'welcome_screen.py').read_text(encoding='utf-8')
    assert 'save_exists(self.name_buf.strip())' not in welcome
