"""Flat-armor proc registry + per-floor charge tracking.

Parallel to `chain_passives.py`. That module handles tier-bonus-derived
named passives stored in ``item._chain_passives``. THIS module handles
plain item attributes set at JSON load time (one bool/dict per item).

Most legendary armors in the AB/CD/EF audit needed a single signature
proc field added — and a single hook site that reads it. The helpers
here let those hook sites stay tidy (a single ``player_has_armor_proc``
call instead of an inline loop over armor_slots).

Conventions
-----------
- All flags are flat item attributes (``arm.unskinnable``, etc.).
- Per-floor charges are stored on the player as ``_armor_proc_charges``
  (dict[str, bool]). Reset in main.py:_change_level.
- Per-run one-shots use ``_armor_proc_run_spent`` (set[str]).
"""

from __future__ import annotations


def iter_armor_pieces(player):
    """Iterate every equipped armor piece (body/cloak/head/feet/legs/arms/hands/shirt).

    Does NOT include shield, accessories, or weapon. Use the chain_passives
    helpers for cross-slot iteration.
    """
    for slot in getattr(player, 'armor_slots', ()) or ():
        if slot is not None:
            yield slot


def player_has_armor_proc(player, attr: str) -> bool:
    """True if any equipped armor piece has ``getattr(piece, attr)`` truthy."""
    if player is None:
        return False
    for piece in iter_armor_pieces(player):
        if getattr(piece, attr, False):
            return True
    return False


def find_armor_with_proc(player, attr: str):
    """Return the first equipped armor piece with ``attr`` truthy, or None."""
    if player is None:
        return None
    for piece in iter_armor_pieces(player):
        if getattr(piece, attr, False):
            return piece
    return None


def proc_value(player, attr: str, default=None):
    """Return ``getattr(piece, attr)`` from the first piece that has it."""
    if player is None:
        return default
    for piece in iter_armor_pieces(player):
        v = getattr(piece, attr, None)
        if v:
            return v
    return default


# ---------------------------------------------------------------------------
# Per-floor charge bookkeeping
# ---------------------------------------------------------------------------


def _ensure_charge_dict(player) -> dict:
    if not hasattr(player, '_armor_proc_charges') or \
            player._armor_proc_charges is None:
        player._armor_proc_charges = {}
    return player._armor_proc_charges


def _ensure_run_set(player) -> set:
    if not hasattr(player, '_armor_proc_run_spent') or \
            player._armor_proc_run_spent is None:
        player._armor_proc_run_spent = set()
    return player._armor_proc_run_spent


def reset_per_floor_charges(player) -> None:
    """Wipe all per-floor armor-proc charge flags. Called on _change_level."""
    player._armor_proc_charges = {}


def is_charge_available(player, flag: str) -> bool:
    """Per-floor charge still available for ``flag``?

    Returns True if the player has the matching armor proc equipped AND
    the per-floor "used" flag is not set.
    """
    if not player_has_armor_proc(player, flag):
        return False
    charges = _ensure_charge_dict(player)
    return not charges.get(flag, False)


def consume_floor_charge(player, flag: str) -> bool:
    """Per-floor one-shot: returns True if not yet used + marks consumed.

    Idiom at call site::

        from armor_procs import consume_floor_charge
        if consume_floor_charge(player, 'dodge_first_arrow_per_floor'):
            return None  # arrow misses
    """
    if not is_charge_available(player, flag):
        return False
    charges = _ensure_charge_dict(player)
    charges[flag] = True
    return True


def is_run_spent(player, flag: str) -> bool:
    """Run-permanent ``flag`` already spent?"""
    return flag in _ensure_run_set(player)


def consume_run_charge(player, flag: str) -> bool:
    """Per-run one-shot: True if armor present + not yet spent + marks spent."""
    if not player_has_armor_proc(player, flag):
        return False
    spent = _ensure_run_set(player)
    if flag in spent:
        return False
    spent.add(flag)
    return True
