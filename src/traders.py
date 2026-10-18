"""The traders: who stands where, what they stock, what they pay, and how the
hero's deeds move their prices (economy refactor 2026-10-17,
ECONOMY_REFACTOR_PROPOSAL D3-D7).

Pure module: no pygame and no Game import, so every rule here is unit-tested
on plain objects. The Game side (placing a trader on arrival, the shop's
Buy / Sell / Services tabs, the services themselves) is game_traders.py.
Everything a trader is and says lives in data/traders.json.

* **The plan** (``roll_plan``): which floors hold a trader, decided once a run
  from the Road's seed (road.rng_for), never from the shared random stream,
  like the Emberpup's and the Black Knight's rolls. A gate camp (the sutler)
  stands on floors 19, 39, 59 and 79, before each gate boss, always.
* **Stock** (``build_stock``): from the trader's stock list, weighted to the
  floor like any other loot, dressed (wand charges and ammo bundles rolled),
  never cursed or enchanted, a named unique only if the run has not had it.
* **Prices**: economy.merchant_price (class share x tier x worth x markup)
  times the deeds multiplier (``price_mult``).
* **Selling** (``refusal`` and economy.sell_offer): 20-25% of his own price,
  capped by his purse; quest pieces and worn things never; an unknown thing
  sells as its unidentified class. Treasure sells near its full value to
  any trader (treasure.py).
* **The lean** (``stock_bias``): the stock leans toward kinds the hero has
  not held yet, and each trader's ``spread`` makes sure his stall offers a
  real choice across kinds (2026-10-18, Brandon: traders are where a kid
  finds or CHOOSES the things that build a character).
* **Gems and rare wares**: a few gems for the coin-to-gem exchange
  (``treasure.gem_stock``) and very rarely a ``rare_stock`` ware (the
  Draught of Mimir's Well, floor 40 and down).

``Game._traders`` is a plain dict so it pickles across code changes::

    {"v": 1, "seed": int, "floors": {floor: kind}, "spawned": [floor],
     "friends_used": [person], "told": [line key], "credits_used": int}
"""
from __future__ import annotations

import copy
import json
import random

CURRENT_VERSION = 1
SEED_KEY = 'traders'

_DATA: dict | None = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'traders.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def kind_def(kind: str) -> dict:
    return (data().get('traders') or {}).get(kind) or (data()['traders']['generalist'])


# ------------------------------------------------------------------ the plan

def _rng(seed: int, key: str) -> random.Random:
    import road
    return road.rng_for(seed, key)


def roll_plan(seed: int, *, secret_floors=(), busy_floors=()) -> dict:
    """{floor: kind} for one run. Gate camps first, then the specialists, then
    a generalist on some of the floors left. A trader prefers a floor with no
    anchor, medium or high Road slot (``busy_floors``) and never takes the
    Emberpup's or the Black Knight's floor (``secret_floors``)."""
    plan = data().get('plan') or {}
    never = {int(f) for f in plan.get('never', ())}
    secret = {int(f) for f in secret_floors if f}
    busy = {int(f) for f in busy_floors if f}
    floors: dict = {}
    for f, kind in (plan.get('gate_camps') or {}).items():
        floors[int(f)] = kind
    rng = _rng(seed, SEED_KEY)
    for spec in plan.get('specialists') or ():
        lo, hi = spec['floors']
        pool = [f for f in range(int(lo), int(hi) + 1)
                if f not in never and f not in secret and f not in floors]
        quiet = [f for f in pool if f not in busy]
        for _ in range(int(spec.get('count', 1))):
            src = [f for f in (quiet or pool) if f not in floors
                   and f - 1 not in floors and f + 1 not in floors] or \
                  [f for f in (quiet or pool) if f not in floors]
            if not src:
                break
            f = rng.choice(src)
            floors[f] = spec['kind']
            if f in quiet:
                quiet.remove(f)
    lo, hi = plan.get('generalist_floors', (2, 98))
    chance = float(plan.get('generalist_chance', 0.17))
    for f in range(int(lo), int(hi) + 1):
        if f in floors or f in never or f in secret:
            continue
        p = chance * (0.5 if f in busy else 1.0)
        if rng.random() < p:
            floors[f] = plan.get('generalist', 'generalist')
    return {'v': CURRENT_VERSION, 'seed': int(seed), 'floors': floors, 'spawned': [],
            'friends_used': [], 'told': [], 'credits_used': 0}


def ensure_plan(st) -> dict:
    """A loaded ``_traders`` dict, with any missing keys filled (string floor
    keys from an old save made ints)."""
    if not isinstance(st, dict):
        return None
    st.setdefault('v', CURRENT_VERSION)
    st.setdefault('floors', {})
    for k in list(st['floors']):
        if isinstance(k, str) and k.isdigit():
            st['floors'][int(k)] = st['floors'].pop(k)
    st.setdefault('spawned', [])
    st.setdefault('friends_used', [])
    st.setdefault('told', [])
    st.setdefault('credits_used', 0)
    return st


# ------------------------------------------------------------------ stock

def stock_size(defn: dict, level: int) -> int:
    for lo, hi, n in defn.get('stock_size') or ((1, 100, 5),):
        if int(lo) <= level <= int(hi):
            return int(n)
    return 5


def _pool(cat: str, level: int, rng, *, unique_first=False):
    from dungeon import _item_eligible_weighted
    from items import is_random_loot, load_items, unique_available
    try:
        items = [i for i in load_items(cat) if is_random_loot(i) and unique_available(i)]
    except Exception:
        return []
    if unique_first:
        uniq = [i for i in items if getattr(i, 'is_unique', False)
                and int(getattr(i, 'min_level', 1) or 1) <= level]
        if uniq:
            return uniq
    return _item_eligible_weighted(items, level, rng)


def _bias(seen) -> tuple:
    """(weight of a ware, candidates per gear pick) from data/traders.json
    ``stock_bias``: a kind the hero has already held weighs ``seen_weight``
    against 1 for one he has not (Brandon, 2026-10-18: "merchants should be
    an excellent way for kids to find or CHOOSE items they haven't yet
    encountered, helps to BUILD the character")."""
    b = data().get('stock_bias') or {}
    seen = set(seen or ())
    sw = float(b.get('seen_weight', 0.35))

    def weight(it) -> float:
        return sw if getattr(it, 'id', None) in seen else 1.0
    return weight, max(1, int(b.get('gear_candidates', 3)))


def _pick_weighted(rng, pool, weight):
    if not pool:
        return None
    ws = [weight(i) for i in pool]
    if sum(ws) <= 0:
        return rng.choice(pool)
    return rng.choices(pool, weights=ws, k=1)[0]


def _ware_class(it) -> str:
    return getattr(it, 'item_class', '') or ''


def build_stock(defn: dict, level: int, rng, seen=()) -> list:
    """The wares for one trader of ``defn`` on floor ``level``: guaranteed
    entries ('ids') first, then the random picks, deduplicated, dressed and
    cut to the stock size, with at least one ware from each of the trader's
    ``spread`` groups (a real choice across kinds, by his role: an
    accessory, a weapon or armour, a scroll or book, something to drink).

    ``seen``: the item ids the hero has already held. The random picks lean
    toward what he has not (``stock_bias``). The lean picks KINDS only:
    every ware is still sold as the hero knows it (unidentified), and its
    power is the item's own, weighted to the floor like any loot.

    After the stock: a few gems (the coin-to-gem exchange,
    ``treasure.gem_stock``) and, very rarely, a ``rare_stock`` ware."""
    from items import (load_items, make_item_by_id, pick_random_armor_for_floor,
                       pick_random_shield_for_floor, pick_random_weapon_for_floor,
                       unique_available)
    gear_pick = {'weapon': pick_random_weapon_for_floor, 'armor': pick_random_armor_for_floor,
                 'shield': pick_random_shield_for_floor}
    weight, gear_n = _bias(seen)

    def gear(kind):
        cands = []
        for _ in range(gear_n):
            try:
                g = gear_pick[kind](level, rng)
            except Exception:
                g = None
            if g is not None:
                cands.append(g)
        return _pick_weighted(rng, cands, weight)

    def from_class(cls):
        if cls in gear_pick:
            return gear(cls)
        return _pick_weighted(rng, _pool(cls, level, rng), weight)

    sure, rolled = [], []
    for entry in defn.get('stock') or ():
        n = int(entry.get('picks', 1))
        try:
            if 'ids' in entry:
                pool = [i for i in load_items(entry['cat']) if i.id in entry['ids']
                        and int(getattr(i, 'min_level', 1) or 1) <= max(level, 1) + 5]
                if pool:
                    sure.extend(_pick_weighted(rng, pool, weight) for _ in range(n))
            elif 'id' in entry:
                if rng.random() < float(entry.get('chance', 1.0)):
                    it = make_item_by_id(entry.get('cat', 'artifact'), entry['id'])
                    if it is not None and unique_available(it):
                        rolled.append(it)
            elif 'gear' in entry:
                for _ in range(n):
                    g = gear(entry['gear'])
                    if g is not None:
                        rolled.append(g)
            elif 'class' in entry:
                pool = _pool(entry['class'], level, rng, unique_first=entry.get('unique_first', False))
                if pool:
                    rolled.extend(_pick_weighted(rng, pool, weight) for _ in range(n))
        except Exception:
            from game_log import log_error
            log_error('traders.build_stock: recovered from an error')
    from dungeon import dress_spawn
    taken = set()

    def dressed(it):
        iid = getattr(it, 'id', None)
        if not iid or iid in taken or not unique_available(it):
            return None
        taken.add(iid)
        ware = copy.copy(it)
        # Wand charges and ammo bundles rolled like any loot (they came at
        # the minimum, ECONOMY_REFACTOR_PROPOSAL S3). Never cursed or
        # enchanted: a trader's goods are what they say they are.
        dress_spawn(ware, level, rng, buc=False)
        return ware

    out_sure = [w for w in (dressed(it) for it in sure) if w is not None]
    out_rolled = [w for w in (dressed(it) for it in rolled) if w is not None]
    rng.shuffle(out_rolled)
    n = max(stock_size(defn, level), len(out_sure))
    final = list(out_sure)
    # A real choice: one ware from each spread group first.
    for group in defn.get('spread') or ():
        group = set(group)
        if any(_ware_class(w) in group for w in final):
            continue
        cand = [w for w in out_rolled if _ware_class(w) in group]
        pick = _pick_weighted(rng, cand, weight) if cand else None
        if pick is None:
            for cls in sorted(group):
                try:
                    extra = from_class(cls)
                except Exception:
                    extra = None
                pick = dressed(extra) if extra is not None else None
                if pick is not None:
                    break
        if pick is not None:
            final.append(pick)
    for w in out_rolled:
        if len(final) >= n:
            break
        if w not in final:
            final.append(w)
    final += _gem_stock(defn, level, rng, taken)
    final += _rare_stock(defn, level, rng, taken)
    return final


def _gem_stock(defn: dict, level: int, rng, taken: set) -> list:
    """A few gems for sale: the coin-to-gem exchange (data/traders.json
    ``treasure.gem_stock``, by trader kind). Priced at value x the spread."""
    import treasure as _tr
    want = int(((data().get('treasure') or {}).get('gem_stock') or {}).get(defn.get('kind', ''), 0) or 0)
    out = []
    for _ in range(want * 3):
        if len(out) >= want:
            break
        g = _tr.roll(level, rng, ('gem',))
        if g is None or g.id in taken:
            continue
        taken.add(g.id)
        out.append(g)
    return out


def _rare_stock(defn: dict, level: int, rng, taken: set) -> list:
    """Very rare wares (data/traders.json ``rare_stock``): each entry has its
    own chance per trader stock, a least floor and its own price share."""
    from items import make_item_by_id
    out = []
    for entry in data().get('rare_stock') or ():
        if not isinstance(entry, dict) or level < int(entry.get('min_floor', 1)):
            continue
        kinds = entry.get('kinds')
        if kinds and defn.get('kind') not in kinds:
            continue
        if rng.random() >= float(entry.get('chance', 0.0)):
            continue
        it = make_item_by_id(entry.get('cat', 'potion'), entry['id'])
        if it is None or it.id in taken:
            continue
        taken.add(it.id)
        if entry.get('share'):
            it._trade_share = float(entry['share'])
        out.append(it)
    return out


# ------------------------------------------------------------------ deeds

def _check(cond, ctx) -> bool:
    if not cond:
        return False
    import deeds
    if isinstance(cond, str):
        cond = (data().get('rumours') or {}).get(cond)
        if not cond:
            return False
    try:
        return bool(deeds.check(cond, ctx))
    except Exception:
        return False


def friend_for(kind: str, ctx, used=()) -> dict | None:
    """The person the hero saved who comes back as this kind of trader, if
    one has (and has not come already this run)."""
    fr = kind_def(kind).get('friend')
    if not fr or fr.get('person') in set(used or ()):
        return None
    return fr if _check(fr.get('when'), ctx) else None


def price_mult(kind: str, ctx, *, friend: bool = False) -> tuple:
    """(multiplier, [(key, line)]) for this trader's prices from the hero's
    deeds: a wronged merchant (+25%, every trader), this trader's own
    reactions to rumours (charity, a con), a friend's price (-20%)."""
    g = data().get('guild') or {}
    mult, lines = 1.0, []
    if _check(g.get('wronged'), ctx):
        mult *= float(g.get('wronged_mult', 1.25))
        lines.append(('wronged', "Word's gone round the stalls about you. Prices are what they are now."))
    for r in kind_def(kind).get('reactions') or ():
        if _check(r.get('when'), ctx):
            mult *= float(r.get('mult', 1.0))
            lines.append((f"{kind}:{r.get('when')}", r.get('line', '')))
    if friend:
        mult *= 1.0 - float(g.get('friend_discount', 0.2))
    return mult, lines


def credits_owed(reg: dict, used: int) -> int:
    """Kept oaths not yet paid back with a free item (D7)."""
    import deeds
    prefix = (data().get('guild') or {}).get('credit_deed', 'kept.')
    n = sum(1 for d in deeds.query(reg) if str(d.get('id', '')).startswith(prefix))
    return max(0, n - int(used or 0))


# ------------------------------------------------------------------ selling

# Classes a fence can sell on. A thing outside these (a key, a corpse, a
# chest, the master lockpick) is never bought.
SELLABLE_CLASSES = frozenset({'weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll',
                              'spellbook', 'potion', 'food', 'ammo', 'ingredient', 'artifact',
                              'treasure'})
# The one kind of artifact a trader deals in.
SELLABLE_ARTIFACTS = frozenset({'soul_sphere'})


def is_quest_piece(item, quest_ids=()) -> bool:
    """A thing the story needs: never sold."""
    from items import scripted_only_ids
    iid = getattr(item, 'id', None)
    if iid in set(quest_ids or ()):
        return True
    if getattr(item, 'plot_locked', False) or getattr(item, 'not_pickable', False):
        return True
    ic = getattr(item, 'item_class', '')
    if ic == 'artifact' and iid not in SELLABLE_ARTIFACTS:
        return True
    try:
        if iid in scripted_only_ids() and ic != 'ingredient':
            return True
    except Exception:
        pass
    return False


def refusal(defn: dict, item, *, known: bool, cursed_known: bool, quest_ids=()) -> str | None:
    """Why this trader will not buy ``item`` (None: he will). ``known``:
    the hero knows its type; ``cursed_known``: the hero knows it is cursed."""
    if is_quest_piece(item, quest_ids):
        return "Not for sale"
    ic = getattr(item, 'item_class', '')
    if ic not in SELLABLE_CLASSES:
        return "Not for sale"
    buys = defn.get('buys', 'all')
    # Treasure is as good as coin to anyone: every trader takes it.
    if buys != 'all' and ic not in set(buys) and ic != 'treasure':
        return "He doesn't deal in that"
    if cursed_known and not defn.get('buys_cursed'):
        return "Cursed: he won't touch it"
    return None
