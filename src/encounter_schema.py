"""Encounter schema: loader normalisation and the runtime rules every
encounter screen shares (DEEDS_KARMA_DESIGN.md section 4).

Pure module. ``normalise`` is called by both loaders (``npc_encounters`` and
``flavor_encounters``, which covers the hardcoded ``FLAVOR_ENCOUNTERS`` list
as well as ``data/flavor_encounters.json``). Its defaults leave existing
content behaving exactly as before: every new field is absent, meaning off.

One option is one outcome. An option without ``quiz`` is its own outcome
object; an option with ``quiz`` has ``pass`` and ``fail`` outcome objects.

The full validator (karma rules P5-P12, stakes table, references, lint)
lives in ``tools/encounters/validate.py``.
"""
from __future__ import annotations

import deeds

ROLES = ('anchor', 'story')
STAKES = ('light', 'medium', 'high')
QUIZ_MODES = ('threshold', 'chain', 'escalator_threshold', 'escalator_chain')
MAX_VISIBLE = 4

# Anchor blocks (npc_encounters._BLOCKS): block -> (first floor, last floor).
_BLOCK_FLOORS = {1: (3, 9), 2: (11, 19), 3: (21, 29), 4: (31, 39), 5: (41, 49),
                 6: (51, 59), 7: (61, 69), 8: (71, 79), 9: (81, 89), 10: (91, 98)}


def normalise(enc: dict, *, source: str) -> dict:
    """Apply the schema defaults to one encounter, in place, and return it.

    ``source`` is ``'npc'`` (data/npc_encounters.json: the block anchors) or
    ``'flavor'`` (the flavor list). Only absent keys are filled.
    """
    if source not in ('npc', 'flavor'):
        raise ValueError(f'unknown encounter source: {source!r}')
    role = enc.setdefault('role', 'anchor' if source == 'npc' else 'story')
    enc.setdefault('stakes', 'medium' if role == 'anchor' else 'light')
    if 'band' not in enc:
        if 'min_level' in enc and 'max_level' in enc:
            enc['band'] = [int(enc['min_level']), int(enc['max_level'])]
        elif enc.get('block') in _BLOCK_FLOORS:
            enc['band'] = list(_BLOCK_FLOORS[enc['block']])
    if enc.get('chain_after'):
        # The old link ("place me whenever my opener is in the run, whatever
        # the hero chose there") is gone: the opener's outcome schedules the
        # follow-up instead. Old content still loads, as a follow-up nothing
        # rolls; the validator reports it as an error.
        import warnings
        warnings.warn(f"{enc.get('tag')}: 'chain_after' is retired; schedule it from "
                      "the opener's outcome", stacklevel=2)
        enc['callback_only'] = True
    return enc


def normalise_all(encs, *, source: str):
    for e in encs:
        normalise(e, source=source)
    return encs


# ---------------------------------------------------------------- options

def is_quiz(opt: dict) -> bool:
    return isinstance(opt.get('quiz'), dict)


def has_naive_sibling(enc: dict, opt: dict | None = None) -> bool:
    """Does the encounter offer a blind-help option (``naive: true``) other
    than ``opt``? Judgment only counts where the careless road was open."""
    return any(o.get('naive') and o is not opt for o in enc.get('options') or ())


def visible_options(enc: dict, ctx: dict, used=()) -> list:
    """The options shown, as ``[(raw_index, option), ...]`` in data order.

    An option whose ``requires`` fails, or whose ``forbids`` holds, is not
    shown (never greyed out). Within a ``hidden_group`` only the first
    passing option is shown. Options already used in a ``then: "options"``
    encounter are gone. At most four are shown.
    """
    used = set(used or ())
    groups_taken = set()
    out = []
    for i, opt in enumerate(enc.get('options') or ()):
        if i in used:
            continue
        if opt.get('requires') and not deeds.check(opt['requires'], ctx):
            continue
        if opt.get('forbids') and deeds.check(opt['forbids'], ctx):
            continue
        grp = opt.get('hidden_group')
        if grp is not None:
            if grp in groups_taken:
                continue
            groups_taken.add(grp)
        out.append((i, opt))
        if len(out) >= MAX_VISIBLE:
            break
    return out


def encounter_allowed(enc: dict, ctx: dict) -> bool:
    """May this encounter spawn now (its own ``requires`` / ``forbids``)?"""
    if enc.get('requires') and not deeds.check(enc['requires'], ctx):
        return False
    if enc.get('forbids') and deeds.check(enc['forbids'], ctx):
        return False
    return True


def resolve_text(enc: dict, ctx: dict) -> str:
    """The scene text: the first ``text_variants`` entry whose ``when``
    holds, else ``text``."""
    for v in enc.get('text_variants') or ():
        if deeds.check(v.get('when'), ctx):
            return v.get('text', enc.get('text', ''))
    return enc.get('text', '')


def resolve_outcome(o: dict, ctx: dict) -> str:
    for v in o.get('outcome_variants') or ():
        if deeds.check(v.get('when'), ctx):
            return v.get('outcome', o.get('outcome', ''))
    return o.get('outcome', '')


def quiz_passed(spec: dict, result) -> bool:
    """Threshold modes pass on ``result.success``; chain modes pass when the
    chain reached ``pass_at`` (default: the engine's own success)."""
    mode = spec.get('mode', 'threshold')
    if mode in ('chain', 'escalator_chain') and spec.get('pass_at') is not None:
        return int(getattr(result, 'score', 0) or 0) >= int(spec['pass_at'])
    return bool(getattr(result, 'success', False))


def option_branches(opt: dict) -> list:
    """The outcome objects an option can lead to: itself, or pass and fail."""
    if is_quiz(opt):
        return [b for b in (opt.get('pass'), opt.get('fail')) if isinstance(b, dict)]
    return [opt]


def max_karma(opt: dict) -> int:
    """An option's karma, as the max over its pass and fail branches (P10)."""
    vals = [int(b.get('karma', 0) or 0) for b in option_branches(opt)]
    return max(vals) if vals else 0
