"""Coin weight and treasure (Brandon's decision D2, 2026-10-18).

    "I think that's a very real lesson about cash and metals; they have value
    but are hard to move. ... make sure it's a realistic weight for coins.
    Let's say 1 gp is 1/10th an oz? ... Gems or TREASURE ... could be great
    way to capture wealth."

* **Coins weigh something.** One gold piece is a tenth of an ounce, so 160
  make a pound (``COINS_PER_LB``). The purse counts toward the carry limit
  like any item (Player.get_current_weight): 16,000 gold is a full pack at
  Strength 10. A pile is picked up only as far as the hero can carry; coin
  paid that will not fit is set down at the hero's feet, or (from a person
  paying a debt) made up in gems.
* **Treasure** (data/items/treasure.json; items.Treasure): gems, jewellery and
  art objects, with real weights and lore-fixed values (LORE NOT FLOOR: a
  ruby is worth what a ruby is worth on any floor; deep floors simply hold
  the dearer kinds, by spawn weight like any loot). A gem is a small fortune
  that weighs nothing; a gold idol is a big one that weighs ten pounds; a
  silver candelabra is worth less than its own weight in gold coin.
* **Known by sight, valued by a trader.** Treasure needs no identify
  question and looks the same before and after. Until a trader values a
  kind, the hero knows only its rough worth ("hundreds of gold"); after, its
  exact value (``Player.appraised_treasure``, a set of kind ids, like the
  known item types). A trader values every piece in the pack when the shop
  opens.
* **Traders deal in it** (data/traders.json ``treasure``): they buy treasure
  at ``buy_rate`` of its value, sell a few gems at ``sell_markup`` (the coin-
  to-gem exchange), and take treasure as payment at ``buy_rate`` when the
  coin runs short, giving change from their purse. No haggling over gems and
  no friend's discount on them, so no buy-and-sell loop.
* **People take it too.** A gold cost in an encounter is paid in coin first
  and the rest in treasure at the same rate, with change in coin.
* **It is the score.** What treasure the hero carries when the run ends is
  added to the score (``SCORE_PER_GOLD``).

Pure module: no pygame and no Game import.
"""
from __future__ import annotations

import copy
import json
import math

COINS_PER_LB = 160                # 1 gold piece = 0.1 oz; 16 oz to the pound
SCORE_PER_GOLD = 1.0              # score points per gold of treasure carried out

# ---- where treasure lies, by lore (which KINDS each place holds; what is
# found is then weighted to the floor like any loot, each kind's own bell).
# A chest holds it through its own loot table ("treasure" in
# data/chest_templates.json); a creature through ``treasure.treasure_chance``
# in data/monsters.json (tools/balance/gold_by_lore.py writes it by purse
# kind: a dragon's hoard, a vampire's old money, a thief's takings).
# Counts measured with tools/balance/gold_sim.py and weight_model.py
# (2026-10-18): treasure is about a tenth of what a shallow floor pays and
# about half of what a deep one pays (deep pieces are dear: a diamond is a
# floor's income), so a deep reward is gems more than coin.
GRAVE_KINDS = ('jewellery', 'coins')     # what the dead were buried wearing
THRONE_GEM_CHANCE = 0.5                  # a loose stone in a throne's armrest
TREASURY_PIECES = (0, 1)                 # a treasury room: its plate and gems
VAULT_PIECES = (1, 1)                    # a closed vault
LAIR_CHANCE = 0.1                        # a den or barracks: loot of the dead
BOSS_HOARD_PIECES = {60: 3, 80: 2, 40: 1, 20: 1}   # gate-boss floors (Fafnir's is the greatest)

# What the hero knows of an unvalued kind: its order of magnitude, the way
# anyone knows a ruby is worth thousands and a garnet is not. (A range built
# from the true value would give the value away.) (upper bound, words).
VALUE_BANDS = ((100, 10, 'tens of gold'),
               (1000, 100, 'hundreds of gold'),
               (10000, 1000, 'thousands of gold'),
               (math.inf, 10000, 'a fortune'))

_KINDS: dict | None = None


# ------------------------------------------------------------------ coin

def coin_weight(coins) -> float:
    """Pounds of ``coins`` gold pieces."""
    try:
        return max(0, int(coins or 0)) / float(COINS_PER_LB)
    except (TypeError, ValueError):
        return 0.0


def coins_in(pounds: float) -> int:
    """How many gold pieces fit in ``pounds`` of spare carrying."""
    return max(0, int(math.floor(max(0.0, float(pounds)) * COINS_PER_LB + 1e-6)))


def weight_text(coins) -> str:
    """'7.5 lb' for a purse: one decimal under 10 lb, whole pounds above."""
    w = coin_weight(coins)
    if w < 10:
        return f"{w:.1f} lb"
    return f"{w:.0f} lb"


# ------------------------------------------------------------------ the kinds

def kinds() -> dict:
    """{kind id: data entry}, data/items/treasure.json, loaded once."""
    global _KINDS
    if _KINDS is None:
        from paths import data_path
        try:
            with open(data_path('data', 'items', 'treasure.json'), encoding='utf-8') as f:
                _KINDS = {k: v for k, v in json.load(f).items() if isinstance(v, dict)}
        except (OSError, ValueError):
            _KINDS = {}
    return _KINDS


def templates() -> list:
    """One Treasure instance per kind (fresh list; copy before placing)."""
    from items import load_items
    try:
        return load_items('treasure')
    except (OSError, KeyError, ValueError):
        return []


def make(kind_id: str, x: int = 0, y: int = 0, count: int = 1):
    from items import make_item_by_id
    it = make_item_by_id('treasure', kind_id)
    if it is not None:
        it.x, it.y, it.count = x, y, max(1, int(count))
    return it


def is_treasure(item) -> bool:
    return getattr(item, 'item_class', '') == 'treasure'


def unit_value(item) -> int:
    """True value of one piece (data). Never shown before it is valued."""
    if not is_treasure(item):
        return 0
    v = getattr(item, 'value', None)
    if v is None:
        v = (kinds().get(getattr(item, 'id', '')) or {}).get('value', 0)
    return max(0, int(v or 0))


def total_value(item) -> int:
    return unit_value(item) * max(1, int(getattr(item, 'count', 1) or 1))


def carried(player) -> list:
    return [i for i in (getattr(player, 'inventory', None) or ()) if is_treasure(i)]


def carried_value(player) -> int:
    """True value of every piece in the pack: the score's treasure."""
    return sum(total_value(i) for i in carried(player))


def score_points(player) -> int:
    return int(carried_value(player) * SCORE_PER_GOLD)


# ------------------------------------------------------------------ knowing

def appraised(player) -> set:
    s = getattr(player, 'appraised_treasure', None)
    if s is None:
        s = set()
        try:
            player.appraised_treasure = s
        except AttributeError:
            pass
    return s


def is_valued(player, item) -> bool:
    return getattr(item, 'id', None) in appraised(player)


def appraise(player, item) -> bool:
    """Mark this kind valued. True when it was not before."""
    s = appraised(player)
    iid = getattr(item, 'id', None)
    if not iid or iid in s:
        return False
    s.add(iid)
    return True


def band(value: int) -> tuple:
    for hi, low, words in VALUE_BANDS:
        if value < hi:
            return low, words
    return VALUE_BANDS[-1][1], VALUE_BANDS[-1][2]


def known_unit_value(player, item) -> int:
    """What the hero can COUNT on one piece being worth: its value once a
    trader has valued the kind, else the low end of its band. Used for
    what he can afford, never as a figure on screen for an unvalued kind."""
    v = unit_value(item)
    if is_valued(player, item):
        return v
    return band(v)[0]


def value_text(player, item) -> str:
    """'Valued at 2,500 gold' or 'Worth thousands of gold (not yet valued)'."""
    v = unit_value(item)
    n = max(1, int(getattr(item, 'count', 1) or 1))
    if is_valued(player, item):
        each = ' each' if n > 1 else ''
        return f"Valued at {v:,} gold{each}"
    return f"Worth {band(v)[1]} (not yet valued)"


def kind_label(item) -> str:
    return {'gem': 'Gem', 'jewellery': 'Jewellery', 'coins': 'Old Coins',
            'art': 'Art Object'}.get(getattr(item, 'kind', ''), 'Treasure')


def wealth(player, coins: int) -> int:
    """Coin plus what the hero can count on his treasure being worth."""
    return max(0, int(coins or 0)) + sum(
        known_unit_value(player, i) * max(1, int(getattr(i, 'count', 1) or 1))
        for i in carried(player))


# ------------------------------------------------------------------ trading

def rates() -> dict:
    """data/traders.json ``treasure``: buy_rate, sell_markup, gem stock."""
    try:
        import traders
        return traders.data().get('treasure') or {}
    except Exception:
        return {}


def buy_rate() -> float:
    return float(rates().get('buy_rate', 0.9))


def sell_markup() -> float:
    return float(rates().get('sell_markup', 1.1))


def credit(item, rate: float | None = None) -> int:
    """What one piece pays toward a price, or is sold for: its value x rate."""
    r = buy_rate() if rate is None else float(rate)
    return int(unit_value(item) * r)


def shop_price(item) -> int:
    """A trader's price for one piece of treasure he sells (a gem): its
    value x the exchange markup. Never haggled, never discounted."""
    return int(math.ceil(round(unit_value(item) * sell_markup(), 6)))


def plan_payment(price: int, coins: int, stacks, *, cap_states: int = 40000) -> dict | None:
    """How to pay ``price`` with ``coins`` and treasure.

    ``stacks``: [(item, unit_credit, count)]. Coin goes first; if it falls
    short, the fewest-gold set of pieces that, with the coin, covers the
    price (the least treasure given up; the most coin spent, which is the
    heavy part). Returns {'coin', 'take': [(item, n)], 'credit', 'change'}
    or None when everything together is not enough.
    """
    price = max(0, int(price))
    coins = max(0, int(coins or 0))
    if coins >= price:
        return {'coin': price, 'take': [], 'credit': 0, 'change': 0}
    target = price - coins
    units = [(it, int(c), int(n)) for it, c, n in stacks if int(c) > 0 and int(n) > 0]
    total = sum(c * n for _, c, n in units)
    if total < target:
        return None
    # Smallest reachable treasure sum >= target (bounded knapsack over sums).
    best = None
    sums = {0: ()}
    for idx, (_it, c, n) in enumerate(units):
        new = dict(sums)
        for s, picks in sums.items():
            for k in range(1, n + 1):
                t = s + c * k
                if t >= target:
                    if best is None or t < best[0]:
                        best = (t, picks + ((idx, k),))
                    break
                if t not in new:
                    new[t] = picks + ((idx, k),)
        sums = new
        if len(sums) > cap_states:
            break
    if best is None:
        # Too many combinations: greedy, dearest first, then drop what is spare.
        chosen, got = [], 0
        for idx, (_it, c, n) in sorted(enumerate(units), key=lambda e: -e[1][1]):
            k = 0
            while k < n and got < target:
                k += 1
                got += c
            if k:
                chosen.append((idx, k))
        best = (got, tuple(chosen))
    t, picks = best
    take = [(units[idx][0], k) for idx, k in picks]
    coin = max(0, price - t)
    return {'coin': coin, 'take': take, 'credit': t, 'change': max(0, t - price)}


# ------------------------------------------------------------------ finding

def pool(level: int, rng, kinds_allowed=None) -> list:
    """Treasure kinds weighted to the floor like any other loot
    (dungeon._item_eligible_weighted: each kind's own spawn bell)."""
    from dungeon import _item_eligible_weighted
    t = templates()
    if kinds_allowed:
        t = [i for i in t if getattr(i, 'kind', '') in set(kinds_allowed)]
    if not t:
        return []
    return _item_eligible_weighted(t, max(1, int(level)), rng)


def roll(level: int, rng, kinds_allowed=None, x: int = 0, y: int = 0):
    """One piece of treasure for floor ``level`` (None if nothing fits)."""
    p = pool(level, rng, kinds_allowed)
    if not p:
        return None
    it = copy.copy(rng.choice(p))
    it.x, it.y, it.count = x, y, 1
    return it


def private_rng(rng, level: int, salt: int):
    """A generator of its own for treasure, keyed on the floor generator's
    state (like the room coin piles): placing treasure moves no layout and no
    roll that comes after it."""
    import random as _random
    try:
        key = tuple(rng.getstate()[1][:8])
    except Exception:
        key = (0,)
    return _random.Random(hash((key, int(level), int(salt))))


def place(ground_items: list, tiles, level: int, rng, pieces: int, kinds_allowed=None) -> int:
    """Lay ``pieces`` of treasure for floor ``level`` on free ``tiles`` (one
    a tile). Returns their total value (a hoard's coin shrinks by it:
    ``coin_after_treasure``)."""
    free = [t for t in tiles if not any(getattr(i, 'x', -1) == t[0] and getattr(i, 'y', -1) == t[1]
                                        for i in ground_items)]
    total = 0
    for _ in range(max(0, int(pieces))):
        if not free:
            break
        x, y = free.pop(rng.randrange(len(free)))
        it = roll(level, rng, kinds_allowed, x, y)
        if it is None:
            continue
        ground_items.append(it)
        total += total_value(it)
    return total


# A hoard holds what it held; deep, more of it is gems and plate. The coin
# beside the treasure shrinks by the treasure's worth, never below this share
# of what it was (Brandon's D2: "deep rewards shift toward gems and treasure
# instead of huge coin piles").
HOARD_COIN_FLOOR = 0.25


def coin_after_treasure(coin: int, treasure_value: int) -> int:
    coin = max(0, int(coin))
    return max(int(coin * HOARD_COIN_FLOOR), coin - max(0, int(treasure_value)))


def gems_for(amount: int, level: int) -> tuple:
    """Gems worth no more than ``amount`` in total, the dearest kinds found
    by this floor first: how a person who owes the hero more coin than he
    can carry pays the rest. Returns ([gem items], gold left over)."""
    amount = max(0, int(amount))
    gems = sorted((g for g in templates() if getattr(g, 'kind', '') == 'gem'
                   and int(getattr(g, 'min_level', 1) or 1) <= max(1, int(level))),
                  key=lambda g: -unit_value(g))
    out = []
    for g in gems:
        v = unit_value(g)
        if v <= 0 or amount < v:
            continue
        n = amount // v
        amount -= n * v
        piece = copy.copy(g)
        piece.count = int(n)
        out.append(piece)
    return out, amount
