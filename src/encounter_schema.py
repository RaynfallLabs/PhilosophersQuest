"""Encounter schema: loader normalisation and the runtime rules every
encounter screen shares (DEEDS_KARMA_DESIGN.md section 4).

Pure module. ``normalise`` is called by both loaders (``npc_encounters`` and
``flavor_encounters``, which loads ``data/flavor_encounters.json``). Its defaults leave existing
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
        out = [b for b in (opt.get('pass'), opt.get('fail')) if isinstance(b, dict)]
        # A fail that reads by how many rounds were won (senet): each is an
        # outcome too.
        out += [b for _k, b in sorted((opt.get('fail_by_correct') or {}).items())
                if isinstance(b, dict)]
        return out
    return [opt]


MAX_FIGHT_COUNT = 8      # one entry's count; a crowd bigger than this is a level


def fight_entries(spec) -> list:
    """An outcome's ``fight`` as ``[(monster_id, count), ...]``.

    Accepts a monster id string, ``{"monster_id": id, "count": n}`` (count
    defaults to 1) or a list of either, so a group fight is data:
    ``[{"monster_id": "neferkaptah_risen"}, {"monster_id": "mummy", "count": 6}]``.
    Malformed entries are skipped (the validator reports them)."""
    items = spec if isinstance(spec, list) else [spec]
    out = []
    for e in items:
        if isinstance(e, str) and e:
            out.append((e, 1))
        elif isinstance(e, dict) and isinstance(e.get('monster_id'), str) and e['monster_id']:
            try:
                n = int(e.get('count', 1))
            except (TypeError, ValueError):
                n = 1
            out.append((e['monster_id'], max(1, min(MAX_FIGHT_COUNT, n))))
    return out


_FATES = ('lost', 'spared', 'saved')


def _line_holds(line: dict, person, ctx: dict) -> bool:
    if 'status' in line:
        want = line['status'] if isinstance(line['status'], (list, tuple)) else [line['status']]
        if person is None or person.get('status') not in want:
            return False
    if 'deserving' in line:
        if person is None or person.get('deserving') is not line['deserving']:
            return False
    if line.get('when') is not None:
        return deeds.check(line['when'], ctx)
    return person is not None


def _line_is_fate(line: dict) -> bool:
    st = line.get('status')
    sts = st if isinstance(st, (list, tuple)) else [st]
    if any(s in _FATES for s in sts if s):
        return True
    when = line.get('when') or {}
    pats = list(when.get('deeds_any') or ()) + list(when.get('deeds_all') or ())
    return any(str(p).split('.', 1)[0] in _FATES for p in pats)


def people_lines(table: dict, ctx: dict, max_lines=None) -> list:
    """The lines told about the people the hero met (The Gate, C18): for
    each person, the first line of ``table['lines']`` that holds; fates
    (lost, spared, saved) first, then the most recent; at most ``max``.
    Pure: reads ``ctx['reg']`` (deeds['people'] and the log) and nothing
    else, and changes nothing."""
    reg = ctx.get('reg') or deeds.new_register()
    people = reg.get('people') or {}
    order = {pid: i for i, pid in enumerate(people)}
    last_seq = {}
    for d in reg.get('log', ()):
        parts = str(d.get('id', '')).split('.')
        if len(parts) >= 2:
            last_seq[parts[1]] = max(last_seq.get(parts[1], 0), int(d.get('seq') or 0))
    chosen = {}
    for line in (table or {}).get('lines') or ():
        pid = line.get('person')
        if not pid or pid in chosen or not line.get('line'):
            continue
        if _line_holds(line, people.get(pid), ctx):
            chosen[pid] = line
    def recency(pid):
        return (last_seq.get(pid, 0), order.get(pid, -1))
    ranked = sorted(chosen, key=lambda pid: (0 if _line_is_fate(chosen[pid]) else 1,
                                              tuple(-x for x in recency(pid))))
    n = int(max_lines if max_lines is not None else (table or {}).get('max', 6))
    return [chosen[pid]['line'] for pid in ranked[:max(0, n)]]


def max_karma(opt: dict) -> int:
    """An option's karma, as the max over its pass and fail branches (P10)."""
    vals = [int(b.get('karma', 0) or 0) for b in option_branches(opt)]
    return max(vals) if vals else 0
