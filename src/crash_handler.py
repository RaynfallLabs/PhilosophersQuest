"""
Crash report writer for Philosopher's Quest.

On an unhandled exception, write_crash_report() is called with the exc_info
triple and an optional live Game object.  It writes a plain-text file to the
project root (one directory above src/) named:

    crash_YYYYMMDD_HHMMSS.txt

Playtesters can send this file directly to the developer.
"""

import os
import sys
import platform
import traceback
import datetime


def _project_root() -> str:
    """Return the project root regardless of the current working directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_crash_report(exc_type, exc_value, exc_tb, game=None) -> str:
    """
    Write a crash report and return its file path.

    Parameters
    ----------
    exc_type, exc_value, exc_tb : exception triple from sys.exc_info()
    game : Game instance (optional) -- used to capture live game state
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"crash_{timestamp}.txt"
    path      = os.path.join(_project_root(), filename)

    lines = []

    lines.append("=" * 70)
    lines.append("  PHILOSOPHER'S QUEST -- CRASH REPORT")
    lines.append("=" * 70)
    lines.append(f"  Time    : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Platform: {platform.platform()}")
    lines.append(f"  Python  : {sys.version.split()[0]}")
    try:
        import pygame
        lines.append(f"  Pygame  : {pygame.version.ver}")
    except Exception:
        lines.append("  Pygame  : (not importable)")
    lines.append("")

    # ---- Traceback -------------------------------------------------------
    lines.append("-" * 70)
    lines.append("TRACEBACK")
    lines.append("-" * 70)
    lines.extend(
        traceback.format_exception(exc_type, exc_value, exc_tb)
    )

    # ---- Game state snapshot ---------------------------------------------
    lines.append("-" * 70)
    lines.append("GAME STATE")
    lines.append("-" * 70)
    if game is None:
        lines.append("  (no game object available)")
    else:
        try:
            p = game.player
            lines.append(f"  Player name  : {getattr(game, 'player_name', '?')}")
            lines.append(f"  Dungeon level: {getattr(game, 'dungeon_level', '?')}")
            lines.append(f"  Game state   : {getattr(game, 'state', '?')}")
            lines.append(f"  Turn         : {getattr(game, 'turn_count', '?')}")
            lines.append(f"  HP           : {p.hp} / {p.max_hp}")
            lines.append(f"  SP           : {p.sp} / {p.max_sp}")
            lines.append(f"  MP           : {p.mp} / {p.max_mp}")
            lines.append(f"  STR/CON/DEX  : {p.STR} / {p.CON} / {p.DEX}")
            lines.append(f"  INT/WIS/PER  : {p.INT} / {p.WIS} / {p.PER}")
            lines.append(f"  Status fx    : {list(p.status_effects.keys())}")
            lines.append(f"  Inventory    : {[i.name for i in p.inventory]}")
            lines.append(f"  Weapon       : {p.weapon.name if p.weapon else 'none'}")
            lines.append(f"  Known spells : {list(p.known_spells.keys())}")
            lines.append(f"  Quirks       : {sorted(p.unlocked_quirks)}")
        except Exception as inner:
            lines.append(f"  (error while reading game state: {inner})")

    # ---- Emergency save --------------------------------------------------
    save_ok = False
    if game is not None:
        try:
            from save_system import save_game
            save_ok = save_game(game)
        except Exception as save_err:
            lines.append("")
            lines.append(f"  EMERGENCY SAVE FAILED: {save_err}")

    if save_ok:
        lines.append("")
        lines.append("  Emergency save written -- your progress has been preserved.")
    lines.append("=" * 70)
    lines.append("  Please send this file to the developer. Thank you!")
    lines.append("=" * 70)

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception:
        # Last resort: write to cwd
        path = os.path.join(os.getcwd(), filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    return path
