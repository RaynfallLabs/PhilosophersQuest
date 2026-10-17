"""Bug bash 2026-10-16 (F5), CQ-18: game-logic handlers that swallowed
errors silently (a boss kill, the Judgment rewards, the starting kit) now
write them to ERROR_LOG.txt; what the game does next is unchanged."""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame

pygame.init()


# ── CQ-18 ────────────────────────────────────────────────────────────────────

def _record_log_errors(monkeypatch):
    import game_log
    seen = []
    monkeypatch.setattr(game_log, 'log_error',
                        lambda msg, exc_info=True: seen.append(msg))
    return seen


def test_a_failed_boss_kill_is_logged_not_silent(monkeypatch):
    from main import Game
    import types
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_cq18a__')
    m = types.SimpleNamespace(id='abaddon', alive=False, hp=0)
    g.monsters = [m]
    seen = _record_log_errors(monkeypatch)

    def boom(_m):
        raise RuntimeError('kill handler broke')
    monkeypatch.setattr(g, '_on_monster_killed', boom)
    g._reap_unnoticed_kills()
    assert m._kill_handled is True          # behaviour unchanged
    assert any('_reap_unnoticed_kills' in s for s in seen)


def test_a_failed_judgment_reward_is_logged(monkeypatch):
    from main import Game
    import items
    import npc_encounters
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_cq18b__')
    seen = _record_log_errors(monkeypatch)
    monkeypatch.setattr(npc_encounters, 'judge_karma',
                        lambda k: ('sword_and_scales', 'You are found worthy.'))

    def broken(cat):
        raise OSError('items file unreadable')
    monkeypatch.setattr(items, 'load_items', broken)
    g._resolve_judgment()                    # still resolves, as before
    assert sum('_resolve_judgment' in s for s in seen) == 2


def test_a_failed_starting_kit_piece_is_logged(monkeypatch):
    from main import Game
    import items
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_cq18c__')
    seen = _record_log_errors(monkeypatch)

    def broken(cat):
        raise OSError('items file unreadable')
    monkeypatch.setattr(items, 'load_items', broken)
    g._give_starting_kit()
    assert any('_give_starting_kit' in s for s in seen)
