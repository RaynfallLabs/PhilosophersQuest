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
    # A 0-byte file is a truncated/corrupt save (e.g. from a pre-atomic-write
    # failed dump); treat it as no save so it doesn't masquerade as loadable.
    path = _save_path(name)
    return os.path.exists(path) and os.path.getsize(path) > 0


def _find_unpicklable(obj, path='state', _seen=None, _out=None, _depth=0):
    """Best-effort localizer: return [(path, typename), ...] for the objects
    pickle can't serialize, descending only into subtrees that fail. Used only
    when a save fails, to print the exact attribute (e.g. a stray pygame
    Surface) instead of a vague 'cannot pickle' message. Honors __getstate__ so
    it matches what pickle actually walks."""
    if _out is None:
        _out = []
    if _seen is None:
        _seen = set()
    if len(_out) >= 8 or _depth > 18:
        return _out
    try:
        pickle.dumps(obj)
        return _out                      # this subtree is clean
    except Exception:
        pass
    oid = id(obj)
    if oid in _seen:
        return _out
    _seen.add(oid)
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            _find_unpicklable(v, f"{path}[{k!r}]", _seen, _out, _depth + 1)
        return _out
    if isinstance(obj, (list, tuple, set, frozenset)):
        for i, v in enumerate(list(obj)):
            _find_unpicklable(v, f"{path}[{i}]", _seen, _out, _depth + 1)
        return _out
    st = None
    gs = getattr(obj, '__getstate__', None)
    if callable(gs):
        try:
            st = gs()
        except Exception:
            st = None
    if st is None:
        st = getattr(obj, '__dict__', None)
    if isinstance(st, dict):
        before = len(_out)
        for k, v in list(st.items()):
            _find_unpicklable(v, f"{path}.{k}", _seen, _out, _depth + 1)
        if len(_out) == before:          # no child pinned it; blame this object
            _out.append((path, type(obj).__name__))
        return _out
    _out.append((path, type(obj).__name__))
    return _out


def save_game(game) -> bool:
    """Serialize the full game state to disk. Returns True on success.

    Writes to a temp file and atomically replaces the real save, so a failed or
    partial dump (e.g. an unpicklable object sneaking into state) can never
    corrupt or destroy an existing good save."""
    path = _save_path(game.player_name)
    tmp = path + '.tmp'
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
            'quiz_stats':        getattr(game, 'quiz_stats', {}),
            'pets':             game.pets,
            'seals_broken':     game.seals_broken,
            'heavenly_host_active': getattr(game, 'heavenly_host_active', False),
            'abaddon_resist_removed_turns': getattr(game, 'abaddon_resist_removed_turns', 0),
            '_l100_altars_used': getattr(game, '_l100_altars_used', set()),
            'karma': getattr(game, 'karma', 0),
            '_npc_encounter_levels': getattr(game, '_npc_encounter_levels', {}),
            '_encountered_npcs': getattr(game, '_encountered_npcs', set()),
            '_flavor_encounter_levels': getattr(game, '_flavor_encounter_levels', {}),
            '_encountered_flavor_npcs': getattr(game, '_encountered_flavor_npcs', set()),
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
            '_secret_victory': getattr(game, '_secret_victory', False),
            # Deep-lore item spawn tracking
            '_lore_levels': getattr(game, '_lore_levels', {}),
            '_lore_placed': getattr(game, '_lore_placed', set()),
            # One-cosmetic-per-item: per-run accessory appearance map (one look
            # per collapsed ring/amulet type). Backward-compatible: old saves
            # return {} and load_state rolls a fresh one.
            '_appearance_map': getattr(game, '_appearance_map', {}),
            # Quirk system (full object with progress, unlocks, cooldowns)
            'quirk_system': getattr(game, 'quirk_system', None),
            # Secret cow level
            '_cow_poke_count': getattr(game, '_cow_poke_count', 0),
            '_cow_level_done': getattr(game, '_cow_level_done', False),
            '_cow_spawned': getattr(game, '_cow_spawned', False),
            '_cow_level': getattr(game, '_cow_level', 35),
            # Cow-level return floor — without this, reloading on the cow
            # level then taking the exit portal warps to floor 0.
            '_cow_return_level': getattr(game, '_cow_return_level', 0),
            # Per-floor charge state (one-shot artifact / passive flags)
            # — must be saved so reload doesn't refresh them.
            '_first_hit_used':   getattr(game, '_first_hit_used', False),
            '_death_save_used':  getattr(game, '_death_save_used', False),
            '_tarnhelm_used':    getattr(game, '_tarnhelm_used', False),
            '_quiz_reroll_used': getattr(game, '_quiz_reroll_used', False),
            # Chronicle dedup guards
            '_chronicle_abaddon_start': getattr(game, '_chronicle_abaddon_start', False),
            # Magic carrot (L1-19) + ethereal unicorn (L21-39) one-shot spawns.
            # Without these, reload re-randomizes the target floor and can
            # spawn a SECOND carrot/unicorn within the same run.
            '_magic_carrot_spawned': getattr(game, '_magic_carrot_spawned', False),
            '_magic_carrot_target_level': getattr(game, '_magic_carrot_target_level', None),
            '_unicorn_spawned': getattr(game, '_unicorn_spawned', False),
            '_unicorn_target_level': getattr(game, '_unicorn_target_level', None),
            # Chronicle & Lore Hints (Encyclopedia tabs)
            '_chronicle': getattr(game, '_chronicle', []),
            '_recalled_hints': getattr(game, '_recalled_hints', []),
            '_cooked_recipes': getattr(game, '_cooked_recipes', []),
            # Quiz deck state — preserves shuffle position so questions don't repeat on reload
            'quiz_deck_state': game.quiz_engine.get_deck_state(),
        }
        with open(tmp, 'wb') as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, path)   # atomic; never touches `path` unless dump succeeded
        return True
    except Exception as e:
        print(f"[Save] Failed: {e}")
        # Pinpoint the exact attribute path of the unpicklable object(s).
        culprits = []
        try:
            culprits = list(_find_unpicklable(state))
            for p, tn in culprits:
                print(f"[Save]   unpicklable at {p}  ({tn})")
        except Exception:
            pass
        # Record to the verbose error log (print() goes nowhere in the bundle).
        try:
            from game_log import log_error
            detail = ''.join(f"\n    unpicklable at {p}  ({tn})" for p, tn in culprits)
            log_error(f"save_game failed for player "
                      f"{getattr(game, 'player_name', '?')!r}: {e}{detail}")
        except Exception:
            pass
        # Leave the existing save intact; discard only the throwaway temp.
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False


def load_game(name: str):
    """Load saved state dict for the given name, or None on failure."""
    try:
        with open(_save_path(name), 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"[Load] Failed: {e}")
        try:
            from game_log import log_error
            log_error(f"load_game failed for {name!r}: {e}")
        except Exception:
            pass
        return None


def delete_save(name: str):
    """Delete save file (called on death for permadeath)."""
    try:
        path = _save_path(name)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
