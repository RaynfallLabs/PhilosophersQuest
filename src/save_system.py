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
            'player':           game.player,
            'player_name':      game.player_name,
            'secret_build':     game.secret_build,
            'turn_count':       game.turn_count,
            'dungeon_level':    game.dungeon_level,
            'player_gold':      game.player_gold,
            'level_mgr':        game.level_mgr,
            'dungeon':          game.dungeon,
            'monsters':         game.monsters,
            'ground_items':     game.ground_items,
            'correct_answers':  game.correct_answers,
            'wrong_answers':    game.wrong_answers,
            'missed_questions':  getattr(game, 'missed_questions', []),
            'pets':             game.pets,
            'seals_broken':     game.seals_broken,
            'heavenly_host_active': getattr(game, 'heavenly_host_active', False),
            'abaddon_resist_removed_turns': getattr(game, 'abaddon_resist_removed_turns', 0),
            '_l100_altars_used': getattr(game, '_l100_altars_used', set()),
            'karma': getattr(game, 'karma', 0),
            '_npc_encounter_levels': getattr(game, '_npc_encounter_levels', {}),
            '_encountered_npcs': getattr(game, '_encountered_npcs', set()),
            '_abaddon_empowered': getattr(game, '_abaddon_empowered', False),
            '_locusts_strengthened': getattr(game, '_locusts_strengthened', False),
            '_judgment_resolved': getattr(game, '_judgment_resolved', False),
            '_npc_triggered_items': getattr(game, '_npc_triggered_items', set()),
            '_npc_trigger_item_levels': getattr(game, '_npc_trigger_item_levels', {}),
            '_npc_trigger_items_placed': getattr(game, '_npc_trigger_items_placed', set()),
            'player_title': getattr(game, 'player_title', ''),
            # Ascent / Death Pursuer state
            'death_pursues': getattr(game, 'death_pursues', False),
            'death_monster': getattr(game, 'death_monster', None),
            # Deep-lore item spawn tracking
            '_lore_levels': getattr(game, '_lore_levels', {}),
            '_lore_placed': getattr(game, '_lore_placed', set()),
            # Quirk system (full object with progress, unlocks, cooldowns)
            'quirk_system': getattr(game, 'quirk_system', None),
            # Secret cow level
            '_cow_poke_count': getattr(game, '_cow_poke_count', 0),
            '_cow_level_done': getattr(game, '_cow_level_done', False),
            '_cow_spawned': getattr(game, '_cow_spawned', False),
            '_cow_level': getattr(game, '_cow_level', 35),
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
