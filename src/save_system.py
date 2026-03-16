"""
Per-name save/load system using pickle.
Each player name gets its own save file (save_<name>.pkl).
Permadeath: death deletes the save file.
"""
import os
import re
import pickle
from paths import save_dir


def _save_path(name: str) -> str:
    """Return the save file path for the given player name."""
    safe = re.sub(r'[^\w\-]', '_', name.lower())
    return os.path.join(save_dir(), f'save_{safe}.pkl')


def save_exists(name: str) -> bool:
    return os.path.exists(_save_path(name))


def save_game(game) -> bool:
    """Serialize the full game state to disk. Returns True on success."""
    try:
        state = {
            'player':        game.player,
            'player_name':   game.player_name,
            'secret_build':  game.secret_build,
            'turn_count':    game.turn_count,
            'dungeon_level': game.dungeon_level,
            'player_gold':   game.player_gold,
            'level_mgr':     game.level_mgr,
            'dungeon':       game.dungeon,
            'monsters':      game.monsters,
            'ground_items':  game.ground_items,
        }
        with open(_save_path(game.player_name), 'wb') as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
        return True
    except Exception as e:
        print(f"[Save] Failed: {e}")
        return False


def load_game(name: str):
    """Load saved state dict for the given name, or None on failure."""
    try:
        with open(_save_path(name), 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"[Load] Failed: {e}")
        return None


def delete_save(name: str):
    """Delete save file (called on death for permadeath)."""
    try:
        path = _save_path(name)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
