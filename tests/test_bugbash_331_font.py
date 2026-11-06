"""Bug bash 3.3.1: body text on a system without Consolas (Mac, Linux).

Body text is laid out for Consolas. Without it the game fell back to Courier
New / DejaVu Sans Mono, about 9% wider, and text was cut off. The bundled
Inconsolata (OFL) is used instead wherever Consolas is missing.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import pygame  # noqa: E402

import fantasy_ui  # noqa: E402

SAMPLE = "The quick brown fox jumps over the lazy dog. 0123456789 (+1 INT)"


def setup_module(_m):
    pygame.font.init()


def test_bundled_mono_font_and_licence_ship():
    fonts = ROOT / 'assets' / 'fonts'
    assert (fonts / fantasy_ui._MONO_FILE).is_file()
    assert (fonts / 'OFL-Inconsolata.txt').is_file()


def test_without_consolas_body_text_uses_the_bundled_font(monkeypatch):
    monkeypatch.setattr(fantasy_ui, '_consolas_found', False)
    bundled = pygame.font.Font(str(ROOT / 'assets' / 'fonts' / fantasy_ui._MONO_FILE), 16)
    for role in ('body', 'small', 'mono'):
        f = fantasy_ui._make_font(role, 16, False)
        assert f.size(SAMPLE) == bundled.size(SAMPLE), role
    assert fantasy_ui._make_font('body', 16, True).bold


def test_fallback_is_no_wider_than_consolas(monkeypatch):
    if not pygame.font.match_font('consolas'):
        return      # nothing to compare against on this machine
    consolas = pygame.font.SysFont('consolas', 16)
    monkeypatch.setattr(fantasy_ui, '_consolas_found', False)
    fallback = fantasy_ui._make_font('body', 16, False)
    assert fallback.size(SAMPLE)[0] <= consolas.size(SAMPLE)[0]


def test_with_consolas_nothing_changes(monkeypatch):
    if not pygame.font.match_font('consolas'):
        return
    monkeypatch.setattr(fantasy_ui, '_consolas_found', True)
    f = fantasy_ui._make_font('body', 16, False)
    assert f.size(SAMPLE) == pygame.font.SysFont(fantasy_ui._MONO_FAMILIES, 16).size(SAMPLE)
