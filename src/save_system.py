"""
Single-slot save/load system using pickle.
Permadeath: death deletes the save file.
"""
import os
import pickle

SAVE_PATH = os.path.join(os.path.dirname(__file__), '..', 'save.pkl')


def save_exists() -> bool:
    return os.path.exists(SAVE_PATH)


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
        with open(SAVE_PATH, 'wb') as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
        return True
    except Exception as e:
        print(f"[Save] Failed: {e}")
        return False


def load_game():
    """Load saved state dict, or None on failure."""
    try:
        with open(SAVE_PATH, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"[Load] Failed: {e}")
        return None


def delete_save():
    """Delete save file (called on death for permadeath)."""
    try:
        if os.path.exists(SAVE_PATH):
            os.remove(SAVE_PATH)
    except Exception:
        pass
