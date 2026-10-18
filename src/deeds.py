"""The deeds register: what the hero has done this run (DEEDS_KARMA_DESIGN.md
section 2).

Pure module: no pygame and no Game import, so every rule here is unit-tested
on plain dicts. The register is a plain dict (``Game._deeds``) so it pickles
safely across code changes, and unknown keys are never dropped.

Nothing here is shown to the player as a list or a number. Deeds surface only
through NPC lines (``text_variants``) and the chronicle.

Shape (version 1)::

    {"v": 1, "seq": 0, "log": [Deed], "oaths": {id: Oath},
     "people": {id: Person}, "threads": {id: Thread}, "pending": [Pending],
     "flags": {once_key: seq},
     "karma": {"slots": {block: source}, "constancy": [rule_id],
               "patterns_neg": [rule_id], "ledger": [entry]},
     "used_options": {encounter_tag: [option_index]}}

Blocks are keyed by int in memory. ``karma_block`` always takes
``deepest_floor_reached``, which never counts the Cow Level and never falls,
so walking back upstairs can never reopen an old block.
"""
from __future__ import annotations

import re

CURRENT_VERSION = 1

# The closed set of first segments (section 2.5).
DOMAINS = frozenset({
    'met', 'aid', 'forgo', 'wrong', 'oath', 'kept', 'broke', 'lapsed', 'released',
    'noticed', 'saved', 'lost', 'spared', 'slew', 'told', 'owe', 'flag',
})

_ID_RE = re.compile(r'^[a-z]+(\.[a-z0-9_]+){1,3}$')

OATH_STATUSES = ('open', 'kept', 'kept_late', 'broken', 'lapsed', 'released')
# How an open oath ends when its due floor passes: 'silent' lapses it on
# arrival (0 karma, vice:lapsed); 'callback' leaves it open, because a
# scheduled callback (the dead coming for the Book of Thoth) or a late
# keep resolves it instead.
LAPSE_MODES = ('silent', 'callback')
PERSON_STATUSES = ('met', 'aided', 'saved', 'lost', 'wronged', 'unmasked', 'spared')

# Condition keys check() understands (section 4.3). The validator rejects any
# other key so a typo cannot silently make a condition always true.
CONDITION_KEYS = frozenset({
    'deeds_all', 'deeds_any', 'deeds_none', 'oath_status', 'karma_min', 'karma_max',
    'stat_min', 'items_any', 'items_none', 'tags_count_min', 'floor_min', 'floor_max',
    'any',
})


def karma_block(floor: int) -> int:
    """The 10-floor stretch a floor belongs to: 1 for floors 1-10, 10 for 91+."""
    try:
        f = int(floor)
    except (TypeError, ValueError):
        f = 1
    return min(10, max(1, (f - 1) // 10 + 1))


def valid_id(deed_id) -> bool:
    """Does ``deed_id`` follow the grammar and start with a known domain?"""
    return (isinstance(deed_id, str) and bool(_ID_RE.match(deed_id))
            and deed_id.split('.', 1)[0] in DOMAINS)


def slug(text) -> str:
    """A string made safe for one id segment (lowercase, [a-z0-9_])."""
    s = re.sub(r'[^a-z0-9_]+', '_', str(text or '').lower()).strip('_')
    return s or 'x'


def new_register() -> dict:
    return {
        'v': CURRENT_VERSION,
        'seq': 0,
        'log': [],
        'oaths': {},
        'people': {},
        'threads': {},
        'pending': [],
        'flags': {},
        'karma': {'slots': {}, 'constancy': [], 'patterns_neg': [], 'ledger': []},
        'used_options': {},
    }


def ensure_shape(reg: dict) -> dict:
    """Fill any missing top-level keys in place (never drops unknown ones)."""
    base = new_register()
    for k, v in base.items():
        if k not in reg:
            reg[k] = v
    karma = reg['karma']
    if not isinstance(karma, dict):
        karma = reg['karma'] = dict(base['karma'])
    for k, v in base['karma'].items():
        karma.setdefault(k, v)
    return reg


def ensure_register(game) -> dict:
    """``game._deeds``, created if missing (duck-typed: any object will do,
    so tests can pass a SimpleNamespace)."""
    reg = getattr(game, '_deeds', None)
    if not isinstance(reg, dict):
        reg = new_register()
        try:
            game._deeds = reg
        except Exception:
            pass
    return ensure_shape(reg)


def next_seq(reg: dict) -> int:
    reg['seq'] = int(reg.get('seq', 0)) + 1
    return reg['seq']


def where(game):
    """(floor, deepest, block, turn) for ``game`` (duck-typed). ``deepest`` is
    ``player.deepest_floor_reached``, which never counts the Cow Level; the
    block is always the deepest floor's."""
    try:
        floor = int(getattr(game, 'dungeon_level', 1) or 1)
    except (TypeError, ValueError):
        floor = 1
    player = getattr(game, 'player', None)
    try:
        deepest = int(getattr(player, 'deepest_floor_reached', 0) or 0)
    except (TypeError, ValueError):
        deepest = 0
    if not deepest:
        deepest = floor if 1 <= floor <= 100 else 1
    try:
        turn = int(getattr(game, 'turn_count', 0) or 0)
    except (TypeError, ValueError):
        turn = 0
    return floor, deepest, karma_block(deepest), turn


def note(game, deed_id: str, *, source: str, tags=(), payload=None,
         unique: bool = False):
    """Record a deed on ``game``'s register from engine code (the Emberpup,
    the Black Knight, the Ring of Gyges). Never raises: a deed is a record,
    not a reason to crash a turn."""
    try:
        reg = ensure_register(game)
        floor, deepest, block, turn = where(game)
        return record(reg, deed_id, floor=floor, block=block, turn=turn, source=source,
                      tags=tags, payload=payload, unique=unique, deepest=deepest)
    except Exception:
        return None


# ---------------------------------------------------------------- recording

def record(reg: dict, deed_id: str, *, floor: int, block: int, turn: int = 0,
           source: str = '', tags=(), payload=None, ttl_floors=None,
           unique: bool = False, engine: bool = False, deepest: int | None = None):
    """Append a deed and return it (or the existing one when ``unique``).

    Raises ValueError for a malformed id, or for a ``virtue:*`` tag unless the
    engine is writing it (``engine=True``): virtue tags feed the constancy
    rules and must never be placed by hand in data.
    """
    if not valid_id(deed_id):
        raise ValueError(f'bad deed id: {deed_id!r}')
    tags = [str(t) for t in (tags or ())]
    if not engine and any(t.startswith('virtue:') for t in tags):
        raise ValueError(f'virtue tags are engine-only: {deed_id!r} {tags}')
    if unique:
        found = last(reg, deed_id)
        if found is not None:
            return found
    base = deepest if deepest is not None else floor
    deed = {
        'id': deed_id,
        'seq': next_seq(reg),
        'floor': floor, 'turn': turn, 'block': block,
        'source': source,
        'tags': tags,
        'payload': dict(payload) if isinstance(payload, dict) else payload,
        'expires_floor': (int(base) + int(ttl_floors)) if ttl_floors is not None else None,
    }
    reg['log'].append(deed)
    return deed


def _matches(deed_id: str, pattern: str | None) -> bool:
    if pattern is None:
        return True
    if pattern.endswith('.*'):
        return deed_id.startswith(pattern[:-1])
    if pattern.endswith('.'):
        return deed_id.startswith(pattern)
    return deed_id == pattern


def _live(deed: dict, deepest: int | None) -> bool:
    exp = deed.get('expires_floor')
    return deepest is None or exp is None or int(deepest) <= int(exp)


def query(reg: dict, pattern: str | None = None, *, tag: str | None = None,
          since_floor: int | None = None, deepest: int | None = None) -> list:
    out = []
    for d in reg.get('log', ()):
        if not _matches(d.get('id', ''), pattern):
            continue
        if tag is not None and tag not in (d.get('tags') or ()):
            continue
        if since_floor is not None and int(d.get('floor') or 0) < since_floor:
            continue
        if not _live(d, deepest):
            continue
        out.append(d)
    return out


def has(reg: dict, pattern: str, *, deepest: int | None = None) -> bool:
    return bool(query(reg, pattern, deepest=deepest))


def count(reg: dict, pattern: str | None = None, *, tag: str | None = None,
          since_floor: int | None = None, deepest: int | None = None) -> int:
    return len(query(reg, pattern, tag=tag, since_floor=since_floor, deepest=deepest))


def first(reg: dict, pattern: str):
    found = query(reg, pattern)
    return found[0] if found else None


def last(reg: dict, pattern: str):
    found = query(reg, pattern)
    return found[-1] if found else None


def floors_since(reg: dict, pattern: str, deepest: int):
    d = last(reg, pattern)
    if d is None:
        return None
    return int(deepest) - int(d.get('floor') or 0)


def payload(reg: dict, deed_id: str, key: str, default=None):
    d = last(reg, deed_id)
    if d is None or not isinstance(d.get('payload'), dict):
        return default
    return d['payload'].get(key, default)


def blocks_with(reg: dict, *, tag: str) -> set:
    return {int(d.get('block') or 0) for d in query(reg, tag=tag)}


# ---------------------------------------------------------------- oaths

def swear(reg: dict, oath_id: str, *, to: str, what: str, item_id=None,
          due_floor=None, floor: int, block: int, turn: int = 0, source: str = '',
          lapse_mode: str = 'silent'):
    """Create an open oath and record ``oath.<id>``. A second swear of the
    same id while it is open does nothing and returns the open oath."""
    cur = reg['oaths'].get(oath_id)
    if cur is not None and cur.get('status') == 'open':
        return cur
    deed = record(reg, f'oath.{oath_id}', floor=floor, block=block, turn=turn, source=source)
    oath = {
        'id': oath_id, 'to': to, 'what': what, 'item_id': item_id,
        'made_floor': floor, 'made_block': block, 'made_seq': deed['seq'],
        'due_floor': due_floor, 'status': 'open', 'resolved_floor': None,
        'source': source, 'lapse_mode': lapse_mode if lapse_mode in LAPSE_MODES else 'silent',
    }
    reg['oaths'][oath_id] = oath
    return oath


def oath_status(reg: dict, oath_id: str):
    o = reg.get('oaths', {}).get(oath_id)
    return o.get('status') if o else None


def _resolve_oath(reg, oath_id, status, deed_prefix, tags, *, floor, block, turn):
    o = reg.get('oaths', {}).get(oath_id)
    if not o or o.get('status') != 'open':
        return False
    o['status'] = status
    o['resolved_floor'] = floor
    record(reg, f'{deed_prefix}.{oath_id}', floor=floor, block=block, turn=turn,
           source=o.get('source', ''), tags=tags, engine=True)
    return True


def keep_oath(reg, oath_id, *, floor, block, turn=0) -> bool:
    return _resolve_oath(reg, oath_id, 'kept', 'kept', ['virtue:kept'],
                         floor=floor, block=block, turn=turn)


def keep_oath_late(reg, oath_id, *, floor, block, turn=0) -> bool:
    """Kept, but after the due floor: status ``kept_late``, deed
    ``kept.<id>`` with payload ``{"late": True}`` and NO virtue tag, so it
    is 0 karma and counts toward neither 'faithful' nor against it."""
    o = reg.get('oaths', {}).get(oath_id)
    if not o or o.get('status') != 'open':
        return False
    o['status'] = 'kept_late'
    o['resolved_floor'] = floor
    record(reg, f'kept.{oath_id}', floor=floor, block=block, turn=turn,
           source=o.get('source', ''), payload={'late': True}, engine=True)
    return True


def is_overdue(oath: dict, deepest: int) -> bool:
    """Past its due floor (the deepest floor reached is beyond it)."""
    due = (oath or {}).get('due_floor')
    return due is not None and int(deepest) > int(due)


def break_oath(reg, oath_id, *, floor, block, turn=0) -> bool:
    return _resolve_oath(reg, oath_id, 'broken', 'broke', ['vice:betray'],
                         floor=floor, block=block, turn=turn)


def lapse_oath(reg, oath_id, *, floor, block, turn=0) -> bool:
    return _resolve_oath(reg, oath_id, 'lapsed', 'lapsed', ['vice:lapsed'],
                         floor=floor, block=block, turn=turn)


def release_oath(reg, oath_id, *, floor, block, turn=0) -> bool:
    return _resolve_oath(reg, oath_id, 'released', 'released', [],
                         floor=floor, block=block, turn=turn)


def open_oaths(reg) -> list:
    return [o for o in reg.get('oaths', {}).values() if o.get('status') == 'open']


# ---------------------------------------------------------------- people

def set_person(reg: dict, person_id: str, *, name: str = '', status=None, owes=None,
               owed=None, last_line=None, deserving=None, floor: int = 0):
    p = reg['people'].get(person_id)
    if p is None:
        p = reg['people'][person_id] = {
            'id': person_id, 'name': name or person_id, 'first_floor': floor,
            'status': 'met', 'owes': False, 'owed': False, 'last_line': '',
            'deserving': None,
        }
    if name:
        p['name'] = name
    if status is not None:
        p['status'] = status
    if owes is not None:
        p['owes'] = bool(owes)
    if owed is not None:
        p['owed'] = bool(owed)
    if last_line is not None:
        p['last_line'] = last_line
    if deserving is not None:
        p['deserving'] = deserving
    return p


meet = set_person


# ---------------------------------------------------------------- threads

def open_thread(reg: dict, thread_id: str, *, hint: str = '', floor: int = 0):
    t = reg['threads'].get(thread_id)
    if t is None or t.get('status') != 'open':
        t = reg['threads'][thread_id] = {
            'id': thread_id, 'hint': hint, 'opened_floor': floor,
            'status': 'open', 'closed_line': None,
        }
    return t


def close_thread(reg: dict, thread_id: str, *, line=None) -> bool:
    t = reg['threads'].get(thread_id)
    if not t or t.get('status') != 'open':
        return False
    t['status'] = 'closed'
    t['closed_line'] = line
    return True


# ---------------------------------------------------------------- pending

def schedule(reg: dict, pending: dict) -> dict:
    p = dict(pending)
    p.setdefault('id', f"{p.get('kind', 'pending')}:{next_seq(reg)}")
    reg['pending'].append(p)
    return p


def due_on_arrival(reg: dict, deepest: int) -> list:
    """Pending entries whose target floor has been reached (``target <= deepest``)."""
    return [p for p in reg.get('pending', ())
            if p.get('target') is not None and int(p['target']) <= int(deepest)]


def pop(reg: dict, pending_id: str):
    for i, p in enumerate(reg.get('pending', ())):
        if p.get('id') == pending_id:
            return reg['pending'].pop(i)
    return None


# ---------------------------------------------------------------- conditions

def check(cond, ctx: dict) -> bool:
    """Evaluate a condition object (section 4.3). Every key is ANDed; ``any``
    is a list of sub-conditions of which one must hold. An empty or missing
    condition is true.

    ``ctx = {"reg", "karma", "stats": {"WIS": 12, ...}, "floor", "deepest",
    "items": set(ids)}``.
    """
    if not cond:
        return True
    reg = ctx.get('reg') or new_register()
    deepest = ctx.get('deepest')
    for key, val in cond.items():
        if key == 'deeds_all':
            if not all(has(reg, p, deepest=deepest) for p in val):
                return False
        elif key == 'deeds_any':
            if not any(has(reg, p, deepest=deepest) for p in val):
                return False
        elif key == 'deeds_none':
            if any(has(reg, p, deepest=deepest) for p in val):
                return False
        elif key == 'oath_status':
            for oid, want in val.items():
                wants = want if isinstance(want, (list, tuple)) else [want]
                if oath_status(reg, oid) not in wants:
                    return False
        elif key == 'karma_min':
            if int(ctx.get('karma', 0)) < int(val):
                return False
        elif key == 'karma_max':
            if int(ctx.get('karma', 0)) > int(val):
                return False
        elif key == 'stat_min':
            stats = ctx.get('stats') or {}
            for st, n in val.items():
                if int(stats.get(st, 0)) < int(n):
                    return False
        elif key == 'items_any':
            items = ctx.get('items') or set()
            if not any(i in items for i in val):
                return False
        elif key == 'items_none':
            items = ctx.get('items') or set()
            if any(i in items for i in val):
                return False
        elif key == 'tags_count_min':
            for tag, n in val.items():
                if count(reg, tag=tag, deepest=deepest) < int(n):
                    return False
        elif key == 'floor_min':
            if int(ctx.get('floor', 0)) < int(val):
                return False
        elif key == 'floor_max':
            if int(ctx.get('floor', 0)) > int(val):
                return False
        elif key == 'any':
            if not any(check(sub, ctx) for sub in val):
                return False
        else:
            raise ValueError(f'unknown condition key: {key!r}')
    return True


# ---------------------------------------------------------------- migration

# Ordered migrations from version N to N+1. Empty while v1 is the only one.
_MIGRATIONS: dict = {}


def migrate(saved, legacy: dict | None = None) -> dict:
    """The register for a loaded save (section 2.7).

    ``saved`` is ``state.get('_deeds')``. ``None`` means a save from before
    the register existed: build an empty one and backfill what the old state
    can tell us (who was met, and which karma blocks are already spent). No
    attempt is made to reconstruct choices.
    """
    if isinstance(saved, dict):
        reg = saved
        v = int(reg.get('v', 1) or 1)
        while v < CURRENT_VERSION and v in _MIGRATIONS:
            reg = _MIGRATIONS[v](reg)
            v += 1
        reg['v'] = max(v, int(reg.get('v', 1) or 1))
        ensure_shape(reg)
        # Pickled int keys stay ints; a JSON round trip would make them str.
        slots = reg['karma']['slots']
        for k in list(slots):
            if isinstance(k, str) and k.isdigit():
                slots[int(k)] = slots.pop(k)
        return reg

    reg = new_register()
    state = legacy or {}
    npc_levels = state.get('_npc_encounter_levels') or {}
    flv_levels = state.get('_flavor_encounter_levels') or {}

    def _floor_of(tag, levels):
        for lvl, enc in levels.items():
            if isinstance(enc, dict) and enc.get('tag') == tag:
                try:
                    return int(lvl)
                except (TypeError, ValueError):
                    return 0
        return 0

    for attr, levels in (('_encountered_npcs', npc_levels),
                         ('_encountered_flavor_npcs', flv_levels)):
        for tag in sorted(state.get(attr) or ()):
            deed_id = f'met.{slug(tag)}'
            fl = _floor_of(tag, levels)
            record(reg, deed_id, floor=fl, block=karma_block(fl or 1), turn=0,
                   source='legacy', unique=True)

    player = state.get('player')
    try:
        deepest = int(getattr(player, 'deepest_floor_reached', 0) or 0)
    except (TypeError, ValueError):
        deepest = 0
    if not deepest:
        try:
            deepest = int(state.get('dungeon_level', 1) or 1)
        except (TypeError, ValueError):
            deepest = 1
        if deepest > 100:                     # the Cow Level never counts
            deepest = 1
    cur = karma_block(deepest)
    slots = reg['karma']['slots']
    for b in range(1, cur):
        slots[b] = 'legacy'
    met = set(state.get('_encountered_npcs') or ())
    for lvl, enc in npc_levels.items():
        try:
            lv = int(lvl)
        except (TypeError, ValueError):
            continue
        if karma_block(lv) == cur and isinstance(enc, dict) and enc.get('tag') in met:
            slots[cur] = 'legacy'
    return reg
