"""The Road: where the run's encounters stand (DEEDS_KARMA_DESIGN.md section 5,
with Brandon's decisions in section 11).

Pure module: no pygame and no Game import. Everything here is decided by
``road_seed`` and the play history passed in; nothing draws on the shared
``random`` stream, so seeded dungeons are unchanged.

* **Slots** (5.1): the even floors 2..98 minus the boss floors 20, 40, 60, 80,
  jittered by one floor either way. 45 slots, gaps of at most 3 floors
  (including around the boss floors), the first on floor 2 or 3. Floors 1,
  99, 100 and the Cow Level (999) are never slots.
* **Roles** (5.2): each 10-floor band gets one anchor slot (inside the old
  anchor block range, so anchor placement is unchanged), one medium slot,
  one high slot in bands 2, 4, 6, 8 and 10 (on floor 15 or deeper in band 2),
  a second medium slot in the odd bands 1, 3, 5, 7 and 9 (Brandon: every
  block offers two or three real chances; ENCOUNTER_STORIES_DRAFT Part I),
  and the rest light. The Emberpup's floor and the Black Knight's floor never
  hold a medium or high slot (5.5).
* **Binding** (5.3): anchors bind at run start (their trigger items are laid
  1-3 floors earlier), with a non-triggered fallback for a triggered anchor;
  every other slot binds late, on first arrival, from the encounters whose
  ``requires`` hold then. No cross-run memory (decision 4): no repeat
  down-weighting.
* **Targets** for callbacks and delayed rewards (4.7, 4.8).

``Game._road`` is a plain dict (``new_state``) so it pickles across code
changes::

    {"v": 1, "enabled": bool, "seed": int,
     "slots": {floor: {"role", "stakes", "bound": tag|None, "fallback": tag|None}},
     "used_tags": [tag, ...]}
"""
from __future__ import annotations

import random
import zlib

import deeds
from boss_levels import COW_LEVEL

CURRENT_VERSION = 1

BOSS_FLOORS = frozenset({20, 40, 60, 80})
NEVER_SLOTS = frozenset({1, 99, 100, 999}) | BOSS_FLOORS
MAX_GAP = 3

# Seed constants (the Emberpup uses 0x0E3BE6 and the Black Knight 0xB1AC4 on
# the same 64-bit draw; only the XOR differs).
SEED_XOR = 0x20AD
JITTER_XOR = 0x5A0D
ROLE_XOR = 0x7E1E

# Anchor block ranges (npc_encounters._BLOCKS), by band.
ANCHOR_RANGE = {1: (3, 9), 2: (11, 19), 3: (21, 29), 4: (31, 39), 5: (41, 49),
                6: (51, 59), 7: (61, 69), 8: (71, 79), 9: (81, 89), 10: (91, 98)}
HIGH_BANDS = frozenset({2, 4, 6, 8, 10})
# Bands with no high slot get a second medium slot instead.
SECOND_MEDIUM_BANDS = frozenset({1, 3, 5, 7, 9})
STAKES_ORDER = ('light', 'medium', 'high')


# A band is a karma block: one 10-floor stretch (CODE-08: one definition).
band_of = deeds.karma_block


def rng_for(seed: int, key: str) -> random.Random:
    """A private generator for one decision, keyed by name."""
    return random.Random((int(seed) ^ zlib.crc32(key.encode('utf-8'))) & 0xFFFFFFFFFFFFFFFF)


def roll_seed() -> int:
    """The run's road seed, drawn like the Emberpup's and the Black Knight's:
    one 64-bit draw from the shared stream with its state restored, so the
    stream is untouched and a seeded game is repeatable."""
    saved = random.getstate()
    try:
        seed = random.getrandbits(64)
    finally:
        random.setstate(saved)
    return seed ^ SEED_XOR


def fresh_seed() -> int:
    """A seed for an old save that has none (never touches the shared stream)."""
    return random.SystemRandom().getrandbits(64)


# ---------------------------------------------------------------- slots

def base_floors() -> list:
    return [f for f in range(2, 99, 2) if f not in BOSS_FLOORS]


def _allowed(f: int) -> bool:
    return 1 < f < 99 and f not in NEVER_SLOTS


def _candidates(b: int) -> list:
    """Jitter candidates for base floor ``b``, plus the boss-neighbourhood
    nudge (the floor before a boss may sit on boss-1, the one after on boss+1)."""
    out = [b - 1, b, b + 1]
    if b + 2 in BOSS_FLOORS:
        out.append(b + 1)
    if b - 2 in BOSS_FLOORS:
        out.append(b - 1)
    return [c for c in dict.fromkeys(out) if _allowed(c)]


def build_slots(seed: int) -> list:
    """The 45 slot floors in order (5.1)."""
    rng = random.Random(int(seed) ^ JITTER_XOR)
    bases = base_floors()
    slots = []
    prev = 0
    for i, b in enumerate(bases):
        nxt = bases[i + 1] if i + 1 < len(bases) else None

        def ok(c, prev=prev, nxt=nxt):
            if not _allowed(c) or c <= prev or c - prev > MAX_GAP:
                return False
            if nxt is None:
                return True
            return any(n > c and n - c <= MAX_GAP for n in _candidates(nxt))

        offs = [-1, 0, 1]
        rng.shuffle(offs)
        pick = next((b + o for o in offs if ok(b + o)), None)
        if pick is None:
            pick = next((c for c in _candidates(b) if ok(c)), None)
        if pick is None:              # cannot happen for the fixed boss set
            pick = b if _allowed(b) and b > prev else prev + 1
        slots.append(pick)
        prev = pick
    return slots


def assign_roles(seed: int, slots, *, secret_floors=()) -> dict:
    """{floor: {'role', 'stakes'}} for the slot floors (5.2, 5.5)."""
    rng = random.Random(int(seed) ^ ROLE_XOR)
    secret = {int(f) for f in secret_floors if f}
    out = {f: {'role': 'light', 'stakes': 'light'} for f in slots}
    for band in range(1, 11):
        mine = [f for f in slots if band_of(f) == band]
        free = list(mine)

        def take(pool):
            prefer = [f for f in pool if f not in secret] or pool
            if not prefer:
                return None
            f = rng.choice(prefer)
            free.remove(f)
            return f

        if band in HIGH_BANDS:
            pool = [f for f in free if band != 2 or f >= 15]
            f = take(pool)
            if f is not None:
                out[f] = {'role': 'high', 'stakes': 'high'}
        lo, hi = ANCHOR_RANGE[band]
        # The anchor is never refused a floor for a secret: it is placed as
        # before; only medium and high make way.
        pool = [f for f in free if lo <= f <= hi]
        if pool:
            f = rng.choice(pool)
            free.remove(f)
            out[f] = {'role': 'anchor', 'stakes': 'medium'}
        for _n in range(2 if band in SECOND_MEDIUM_BANDS else 1):
            f = take(list(free))
            if f is not None:
                out[f] = {'role': 'medium', 'stakes': 'medium'}
    # Demote whatever could not move off a secret floor.
    for f in secret:
        if f in out and out[f]['role'] in ('medium', 'high'):
            out[f] = {'role': 'light', 'stakes': 'light'}
    return out


def new_state(seed: int, *, enabled: bool, secret_floors=()) -> dict:
    st = {'v': CURRENT_VERSION, 'enabled': bool(enabled), 'seed': int(seed),
          'slots': {}, 'used_tags': []}
    if enabled:
        slots = build_slots(seed)
        for f, r in assign_roles(seed, slots, secret_floors=secret_floors).items():
            st['slots'][f] = {'role': r['role'], 'stakes': r['stakes'],
                              'bound': None, 'fallback': None}
    return st


def ensure_state(st, *, legacy: bool = True) -> dict:
    """A loaded ``_road`` (None for a save from before the Road): an old save
    gets a disabled Road with a fresh seed and keeps its legacy dicts."""
    if not isinstance(st, dict):
        return new_state(fresh_seed(), enabled=False)
    st.setdefault('v', CURRENT_VERSION)
    st.setdefault('enabled', False)
    if 'seed' not in st:
        st['seed'] = fresh_seed()
    st.setdefault('slots', {})
    st.setdefault('used_tags', [])
    for k in list(st['slots']):
        if isinstance(k, str) and k.isdigit():
            st['slots'][int(k)] = st['slots'].pop(k)
    return st


def busy_floors(st: dict) -> set:
    """Floors holding an anchor, medium or high slot: callbacks never land
    there."""
    return {f for f, s in (st.get('slots') or {}).items()
            if s.get('role') in ('anchor', 'medium', 'high')}


# ---------------------------------------------------------------- binding

def bind_anchors(st: dict, encounters, *, blocks=None) -> dict:
    """Bind every anchor slot at run start. Returns {floor: encounter} for
    the anchors (the ``_npc_encounter_levels`` view) and records each tag and
    any fallback in the state. ``encounters`` are the anchor definitions
    (``npc_encounters.ENCOUNTERS``)."""
    out = {}
    for f in sorted(st['slots']):
        s = st['slots'][f]
        if s['role'] != 'anchor':
            continue
        band = band_of(f)
        rng = rng_for(st['seed'], f'anchor:{f}')
        cands = [e for e in encounters if e.get('block') == band and not e.get('trigger_item')
                 and e['tag'] not in st['used_tags']]
        trig = [e for e in encounters if e.get('block') == band and e.get('trigger_item')
                and e['tag'] not in st['used_tags']]
        pool = list(cands)
        if trig:
            pool.append(rng.choice(trig))           # up to one triggered, as before
        if not pool:
            continue
        enc = rng.choice(pool)
        s['bound'] = enc['tag']
        st['used_tags'].append(enc['tag'])
        out[f] = enc
        if enc.get('trigger_item'):
            alts = [e for e in cands if e['tag'] != enc['tag']]
            if enc.get('fallback_anchor'):
                alts = [e for e in encounters if e['tag'] == enc['fallback_anchor']] or alts
            if alts:
                fb = rng.choice(alts)
                s['fallback'] = fb['tag']
                st['used_tags'].append(fb['tag'])
    return out


def eligible(enc: dict, stakes: str, floor: int, used) -> bool:
    if enc.get('callback_only') or enc.get('tag') in used:
        return False
    if enc.get('role') != 'story' and not enc.get('road_ok'):
        return False
    if enc.get('stakes', 'light') != stakes:
        return False
    band = enc.get('band') or [enc.get('min_level', 1), enc.get('max_level', 100)]
    return int(band[0]) <= int(floor) <= int(band[1])


def bind_slot(st: dict, floor: int, pool, allowed=lambda e: True):
    """Late-bind the slot on ``floor`` (first arrival). ``pool`` is every
    story encounter; ``allowed(enc)`` checks its requires / forbids against
    the hero's deeds now. An empty pool falls back to a lighter stake, then
    leaves the slot empty. Returns the encounter or None."""
    s = (st.get('slots') or {}).get(floor)
    if not s or s.get('role') == 'anchor' or s.get('bound'):
        return None
    used = set(st.get('used_tags') or ())
    rng = rng_for(st['seed'], f'bind:{floor}')
    i = STAKES_ORDER.index(s.get('stakes', 'light'))
    for stakes in reversed(STAKES_ORDER[:i + 1]):
        cands = [e for e in pool if eligible(e, stakes, floor, used) and allowed(e)]
        if cands:
            cands.sort(key=lambda e: e['tag'])
            enc = rng.choice(cands)
            s['bound'] = enc['tag']
            st['used_tags'].append(enc['tag'])
            return enc
    return None


# ---------------------------------------------------------------- targets

def pick_target(seed: int, key: str, earliest: int, latest: int, *, deepest: int,
                blocked=(), allow_boss: bool = False, band=None):
    """A floor in [earliest, latest] for a callback or a delayed reward
    (4.7, 4.8): deeper than ``deepest``, never 99, 100 or the Cow Level,
    never a boss floor unless ``allow_boss``, never in ``blocked``. When the
    target encounter has a ``band`` and it overlaps the range, the pick stays
    inside it (so a chain keeps the floors its content was written for).
    None when no floor qualifies."""
    lo, hi = int(earliest), int(latest)
    floors = [f for f in range(max(lo, int(deepest) + 1), hi + 1)
              if 1 < f < 99 and f != COW_LEVEL
              and (allow_boss or f not in BOSS_FLOORS) and f not in set(blocked)]
    if band:
        inside = [f for f in floors if int(band[0]) <= f <= int(band[1])]
        if inside:
            floors = inside
    if not floors:
        return None
    return rng_for(seed, key).choice(floors)
