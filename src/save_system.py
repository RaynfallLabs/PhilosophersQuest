"""
Per-name save/load system using pickle.
Each player name gets its own save file (save_<name>.pkl).
Permadeath: death deletes the save file.

File layout: a short text header (MAGIC, then one JSON line naming the hero,
the run and the turn it was written on), then the pickled state. Saves from
before the header (a bare pickle) still load. Nothing here checks where a save
file came from: a save copied in by hand loads like any other (bug bash 4,
ruling 21).
"""
import hashlib
import json
import os
import re
import pickle
from paths import save_dir

MAGIC = b'PQSAVE2\n'
_MAX_STEM = 120       # characters of encoded name kept before a hash stands in


def _encode_name(name: str) -> str:
    """Name -> file-name part, one-to-one, and safe on a case-blind disk.

    Lower-case letters, digits and '-' stand for themselves; a capital is '+'
    and its lower-case letter; anything else is '_<hex code>_'. "Bob", "bob",
    "Bob!" and "bob " used to share one file (case and punctuation were all
    folded away): one hero's save overwrote the other's."""
    out = []
    for ch in name:
        if ('a' <= ch <= 'z') or ('0' <= ch <= '9') or ch == '-':
            out.append(ch)
        elif 'A' <= ch <= 'Z':
            out.append('+' + ch.lower())
        else:
            out.append(f'_{ord(ch):x}_')
    stem = ''.join(out)
    if len(stem) > _MAX_STEM:
        # Long non-Latin names would pass the file-name length limit.
        digest = hashlib.sha1(name.encode('utf-8')).hexdigest()[:16]
        stem = f'{stem[:_MAX_STEM - 17]}~{digest}'
    return stem


def _save_path(name: str) -> str:
    """Return the save file path for the given player name."""
    return os.path.join(save_dir(), f'save_{_encode_name(name)}.pkl')


def _legacy_save_path(name: str) -> str:
    """Where a save for this name lived before names were kept apart
    (case and punctuation folded to '_')."""
    safe = re.sub(r'[^\w\-]', '_', name.lower())
    return os.path.join(save_dir(), f'save_{safe}.pkl')


def _nonempty(path: str) -> bool:
    # A 0-byte file is a truncated/corrupt save (e.g. from a pre-atomic-write
    # failed dump); treat it as no save so it doesn't masquerade as loadable.
    try:
        return os.path.isfile(path) and os.path.getsize(path) > 0
    except OSError:
        return False


def read_save_header(path: str) -> dict | None:
    """The header of a save file, or None for a save from before headers
    (or a file that is not a save). Reads a few bytes, never the state."""
    try:
        with open(path, 'rb') as f:
            if f.read(len(MAGIC)) != MAGIC:
                return None
            head = json.loads(f.readline(4096).decode('utf-8'))
        return head if isinstance(head, dict) else None
    except (OSError, ValueError):
        return None


def _find_save(name: str) -> str | None:
    """The file holding this name's save, or None. A save written under the
    old name mapping (no header) is still found at its old path."""
    path = _save_path(name)
    if _nonempty(path):
        return path
    old = _legacy_save_path(name)
    if old != path and _nonempty(old) and read_save_header(old) is None:
        return old
    return None


def save_exists(name: str) -> bool:
    return _find_save(name) is not None


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


def run_is_over(game) -> bool:
    """True once the hero has died, won or fled: such a run must never be
    written back to disk (its save was deleted on purpose)."""
    if getattr(game, '_run_over', False):
        return True
    try:
        from game_states import STATE_DEAD, STATE_VICTORY
    except Exception:
        return False
    return getattr(game, 'state', None) in (STATE_DEAD, STATE_VICTORY)


def settle_unfinished_actions(game) -> None:
    """Resolve what was mid-flight before an exit save (quit or crash).

    None of these is saved, so writing the run without settling them let a
    player escape a cost or lose one:
      - a Necronomicon recital left unfinished counts as a failure, exactly
        as ESC does (quitting used to dodge the Deadites);
      - a question left unanswered is a wrong answer (the action had already
        spent its corpse, ingredients or Intercession);
      - a targeted spell still being aimed is cancelled and refunded as ESC
        does (the MP or the free cast used to be lost).
    Each step is guarded on its own: a failure in one never blocks the save.
    """
    try:
        if getattr(game, '_necro_qs', None) is not None:
            game._necro_complete()
    except Exception:
        pass
    try:
        from quiz_engine import QuizState
        qe = getattr(game, 'quiz_engine', None)
        if (qe is not None and getattr(qe, 'callback', None) is not None
                and qe.state != QuizState.COMPLETE):
            qe._end(success=False)
    except Exception:
        pass
    try:
        if getattr(game, '_pending_spell', None) is not None:
            game._refund_pending_spell()
            game._power_targeting = False
            game._pending_power = None
    except Exception:
        pass


def save_game(game) -> bool:
    """Serialize the full game state to disk. Returns True on success.

    Writes to a temp file and atomically replaces the real save, so a failed or
    partial dump (e.g. an unpicklable object sneaking into state) can never
    corrupt or destroy an existing good save."""
    path = _save_path(game.player_name)
    # One temp file per running copy of the game: two copies used to share
    # one temp name, and about a third of their saves failed.
    tmp = f'{path}.{os.getpid()}.tmp'
    if _disk_save_is_newer(game, path):
        return True                      # the newer save stays; said in-game
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
            '_l100_altars_tried': getattr(game, '_l100_altars_tried', set()),
            'karma': getattr(game, 'karma', 0),
            '_npc_encounter_levels': getattr(game, '_npc_encounter_levels', {}),
            '_encountered_npcs': getattr(game, '_encountered_npcs', set()),
            '_flavor_encounter_levels': getattr(game, '_flavor_encounter_levels', {}),
            '_encountered_flavor_npcs': getattr(game, '_encountered_flavor_npcs', set()),
            '_abaddon_empowered': getattr(game, '_abaddon_empowered', False),
            '_abaddon_empowered_applied': getattr(game, '_abaddon_empowered_applied', False),
            '_flux_given': getattr(game, '_flux_given', False),
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
            # Duck of Doom spawn state (was not saved: a reload re-rolled the
            # floor, so a run could get a second duck or none).
            '_duck_of_doom_floor': getattr(game, '_duck_of_doom_floor', None),
            '_duck_of_doom_placed': getattr(game, '_duck_of_doom_placed', False),
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
            # The abandoned Emberpup: its floor, placed yet, how it ended.
            '_emberpup': getattr(game, '_emberpup', None),
            # Chronicle & Lore Hints (Encyclopedia tabs)
            '_chronicle': getattr(game, '_chronicle', []),
            '_recalled_hints': getattr(game, '_recalled_hints', []),
            '_cooked_recipes': getattr(game, '_cooked_recipes', []),
            # Quiz deck state — preserves shuffle position so questions don't repeat on reload
            'quiz_deck_state': game.quiz_engine.get_deck_state(),
            '_run_id': run_id_of(game),
        }
        header = json.dumps({'name': game.player_name, 'run': run_id_of(game),
                             'turn': int(game.turn_count)}, ensure_ascii=True)
        with open(tmp, 'wb') as f:
            f.write(MAGIC)
            f.write(header.encode('ascii') + b'\n')
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, path)   # atomic; never touches `path` unless dump succeeded
        # A save loaded from its old-mapping file now lives at the new path:
        # retire the old file, or it would be found again (by another name).
        old = getattr(game, '_legacy_save_path', None)
        if old and os.path.normcase(os.path.abspath(old)) != os.path.normcase(os.path.abspath(path)):
            try:
                if read_save_header(old) is None and os.path.exists(old):
                    os.remove(old)
            except OSError:
                pass
        game._legacy_save_path = None
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


def run_id_of(game) -> str:
    """This run's identity, made on first use and kept in the save."""
    rid = getattr(game, '_run_id', None)
    if not rid:
        import uuid
        rid = uuid.uuid4().hex
        game._run_id = rid
    return rid


def _disk_save_is_newer(game, path: str) -> bool:
    """True when the file at `path` is a later save of this same run (another
    copy of the game, playing the same hero, wrote it further on). Writing
    now would clobber that progress with older play: the higher version wins.
    A save of a different run, or one from before headers, is not compared.
    Saves copied in by hand are not checked or refused anywhere."""
    head = read_save_header(path)
    if not head or head.get('run') != run_id_of(game):
        return False
    try:
        disk_turn = int(head.get('turn', -1))
    except (TypeError, ValueError):
        return False
    if disk_turn <= int(getattr(game, 'turn_count', 0)):
        return False
    try:
        from game_log import log_info
        log_info(f"save skipped: disk turn {disk_turn} > this copy's turn "
                 f"{getattr(game, 'turn_count', '?')} for {game.player_name!r}")
    except Exception:
        pass
    if not getattr(game, '_newer_save_warned', False):
        game._newer_save_warned = True
        try:
            game.add_message(
                f"Another copy of the game has saved {game.player_name} further on "
                f"(turn {disk_turn:,}). That save is kept: this copy will not "
                "write over it.", 'warning')
        except Exception:
            pass
    return True


def load_game(name: str):
    """Load saved state dict for the given name, or None on failure.
    Reads both layouts: header + pickle, and a bare pickle (older saves).
    A save found at its old-mapping path says so in '__loaded_from__'."""
    try:
        path = _find_save(name) or _save_path(name)
        with open(path, 'rb') as f:
            if f.read(len(MAGIC)) == MAGIC:
                f.readline()
            else:
                f.seek(0)
            state = pickle.load(f)
        if isinstance(state, dict) and path != _save_path(
                str(state.get('player_name') or name)):
            state['__loaded_from__'] = path
        return state
    except Exception as e:
        print(f"[Load] Failed: {e}")
        try:
            from game_log import log_error
            log_error(f"load_game failed for {name!r}: {e}")
        except Exception:
            pass
        return None


def set_aside_save(name: str) -> str | None:
    """Move a save that will not load out of the way, keeping it. Returns the
    new path, or None if it could not be moved.

    A save that exists but cannot be read used to be treated as "no save":
    the game started a new hero under the name and its first autosave
    overwrote the unreadable file, which might have been recoverable."""
    import time
    src = _find_save(name) or _save_path(name)
    dst = f"{src}.unreadable-{time.strftime('%Y%m%d-%H%M%S')}"
    try:
        os.replace(src, dst)
        return dst
    except OSError:
        return None


def delete_save(name: str):
    """Delete save file (called on death for permadeath). A save still at its
    old-mapping path (loaded, not yet re-saved) is the one deleted then."""
    try:
        path = _find_save(name) or _save_path(name)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
