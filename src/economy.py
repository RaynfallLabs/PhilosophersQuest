"""The gold economy in one place: what a floor earns, and what things cost.

Pure arithmetic, no game state. Everything that grants or charges gold by a
rule (trader prices and offers, services, bribes, encounter costs and
rewards, mystery tribute, chests, coin piles, graves and thrones) reads from
here, so the pieces stay in proportion to each other and to what a floor
actually pays.

The income line (economy refactor, 2026-10-17). Gold is by lore, not by
kill (ECONOMY_REFACTOR_PROPOSAL D1): beasts, oozes, constructs and spirits
carry no coin (tools/balance/gold_by_lore.py wrote what each creature
carries into data/monsters.json), and the coin lies in room coin piles,
lairs, hoards and chests priced from this line. Measured with
tools/balance/gold_sim.py (40 runs, 'prepared' at 90%) the generator pays
about 375 gold a floor on floors 1-5, 725 on 6-10, 1,480 on 11-19, 2,100 on
21-29, 3,500 on 41-49, 5,500 on 61-69 and 8,400 on 90-99: the same as before
on floors 1-10 and about 60% of before from floor 20 down (where it had run
to 1.35-1.55 times the old line, 150 + 90 x floor). The line below sits
within about 15% of every band.
"""
from __future__ import annotations

import copy

INCOME_BASE = 130
INCOME_PER_FLOOR = 76


def floor_income(level: int) -> float:
    """Gold an ordinary floor pays a player who explores it."""
    return float(INCOME_BASE + INCOME_PER_FLOOR * max(1, min(100, int(level or 1))))


def nice(amount: float) -> int:
    """Round to a number a shopkeeper would say: fives, then tens, then fifties."""
    amount = max(0.0, float(amount))
    step = 5 if amount < 200 else 10 if amount < 1000 else 50
    return int(max(step if amount > 0 else 0, round(amount / step) * step))


def share(level: int, fraction: float) -> int:
    """`fraction` of one floor's income on `level`, as a round figure."""
    return nice(floor_income(level) * fraction)


# --------------------------------------------------------------- the traders
# Share of a floor's income, by item class: one floor buys a consumable or
# two, an accessory takes about two floors and a named unique about four.
MERCHANT_SHARE = {
    'potion': 0.15, 'food': 0.10, 'ammo': 0.10,
    'scroll': 0.50, 'wand': 0.50, 'spellbook': 0.80,
    'weapon': 0.60, 'armor': 0.60, 'shield': 0.60,
    'accessory': 1.50,
}
UNIQUE_GEAR_SHARE = 3.0
# A named ring or amulet (Jade Cicada, Brisingamen) cost what a plain ring
# did: 1.5-2.4 floors of income (ECONOMY_REFACTOR_PROPOSAL S4). It takes the
# premium named gear already had.
UNIQUE_ACCESSORY_SHARE = 3.0
# What the hero is offered for a thing whose type he does not know: its
# class at a middling tier, worth 1. Never its true worth (that would name it).
UNKNOWN_TIER = 2

_WORTH = None


def worth_table() -> dict:
    """data/item_worth.json, loaded once."""
    global _WORTH
    if _WORTH is None:
        import json
        from paths import data_path
        try:
            with open(data_path('data', 'item_worth.json'), encoding='utf-8') as f:
                _WORTH = json.load(f)
        except (OSError, ValueError):
            _WORTH = {}
    return _WORTH


def _worth_value(v, table) -> float:
    if v == 'junk':
        return float(table.get('junk', 0.1))
    try:
        return float(v)
    except (TypeError, ValueError):
        return 1.0


def item_worth(item) -> float:
    """What this kind of thing is worth against others of its class: Full
    Healing 3, Healing 1, Sickness junk (data/item_worth.json)."""
    t = worth_table()
    iid = getattr(item, 'id', '') or ''
    by_id = t.get('by_id') or {}
    if iid in by_id:
        return _worth_value(by_id[iid], t)
    spell = getattr(item, 'spell_id', None)
    if spell and spell in (t.get('by_spell') or {}):
        return _worth_value(t['by_spell'][spell], t)
    ic = getattr(item, 'item_class', '')
    eff = getattr(item, 'effect', None)
    by_eff = (t.get('by_effect') or {}).get(ic) or {}
    if isinstance(eff, str) and eff in by_eff:
        return _worth_value(by_eff[eff], t)
    return 1.0


def _item_tier(item) -> int:
    tier = getattr(item, 'quiz_tier', None) or getattr(item, 'tier', 1) or 1
    try:
        return max(1, min(5, int(tier)))
    except (TypeError, ValueError):
        return 1


def class_share(item) -> float:
    """The class's share of a floor's income for this item (before worth)."""
    iid = getattr(item, 'id', '') or ''
    # A rare ware priced by its own stock entry (data/traders.json
    # rare_stock "share": the Draught of Mimir's Well).
    own = getattr(item, '_trade_share', None)
    if own:
        return float(own)
    by_share = worth_table().get('share_by_id') or {}
    if iid in by_share:
        return float(by_share[iid])
    ic = getattr(item, 'item_class', 'misc')
    frac = MERCHANT_SHARE.get(ic, 0.5)
    if getattr(item, 'is_unique', False):
        if ic in ('weapon', 'armor', 'shield'):
            frac = UNIQUE_GEAR_SHARE
        elif ic == 'accessory':
            frac = UNIQUE_ACCESSORY_SHARE
    return frac


def merchant_price(item, level: int = 1, markup: float = 1.0) -> int:
    """Gold cost of one trader's item on floor `level`: its class share of
    the floor's income, by tier, times what it is worth (data/item_worth.json),
    times the trader's own markup (an abyssal dealer's 1.5)."""
    if getattr(item, 'item_class', '') == 'treasure':
        # Treasure keeps its own worth on every floor (LORE NOT FLOOR): a
        # trader sells a gem at its value x the exchange spread
        # (treasure.shop_price), whatever his markup.
        import treasure
        return treasure.shop_price(item)
    frac = class_share(item) * (0.6 + 0.2 * _item_tier(item)) * item_worth(item)
    return max(5, nice(floor_income(level) * frac * float(markup or 1.0)))


def unknown_price(item, level: int = 1, markup: float = 1.0) -> int:
    """The price of a thing as its unidentified class: what a trader can
    offer for it when the hero cannot say what it is. It never depends on
    what the thing really is (its worth, its tier, whether it is unique)."""
    ic = getattr(item, 'item_class', 'misc')
    if ic == 'treasure':
        return merchant_price(item, level, markup)     # treasure is always known
    frac = MERCHANT_SHARE.get(ic, 0.5) * (0.6 + 0.2 * UNKNOWN_TIER)
    return max(5, nice(floor_income(level) * frac * float(markup or 1.0)))


# --------------------------------------------------------------- selling
# A trader pays a share of HIS OWN price (ECONOMY_REFACTOR_PROPOSAL D5): 20%
# for a thing the hero cannot fully vouch for, 25% for one identified to the
# last detail. Capped by what is left in his purse.
SELL_RATE_UNKNOWN = 0.20
SELL_RATE_IDENTIFIED = 0.25
# No buy/sell loop: a thing bought from any trader never sells for more than
# this share of what was paid for it. Haggling takes at most 50% off and a
# friend's price 20% more, so the least ever paid is 40% of a list price; a
# resale is capped at half of what was paid: always a loss, on any floor, to
# any trader, whatever his markup.
RESALE_CAP_OF_PAID = 0.5
# A trader's buying purse, in floors of income (data/traders.json may set its own).
TRADER_PURSE_SHARE = 1.5


def sell_offer(item, level: int, *, known: bool, identified: bool,
               markup: float = 1.0, purse: int | None = None) -> int:
    """What a trader offers for ``item`` on floor ``level``.

    known: the hero knows the item's type (it is named). An unknown thing is
    priced as its unidentified class, so the offer never tells the hero what
    it is. identified: this copy is identified to the last detail.
    """
    if getattr(item, 'item_class', '') == 'treasure':
        # Treasure sells near its full value (treasure.buy_rate), every
        # trader takes it, and there is no resale cap: he sells a gem at
        # value x 1.1 and buys at x 0.9, so no loop is possible.
        import treasure
        offer = treasure.credit(item)
        if purse is not None:
            offer = min(offer, max(0, int(purse)))
        return max(0, int(offer))
    his = merchant_price(item, level, markup) if known else unknown_price(item, level, markup)
    rate = SELL_RATE_IDENTIFIED if (known and identified) else SELL_RATE_UNKNOWN
    offer = his * rate
    paid = getattr(item, '_bought_for', None)
    cap = None if paid is None else int(float(paid) * RESALE_CAP_OF_PAID)
    offer = nice(offer) if offer >= 5 else int(offer)
    if cap is not None:
        offer = min(offer, cap)
    if purse is not None:
        offer = min(offer, max(0, int(purse)))
    return max(0, int(offer))


# --------------------------------------------------------------- services
# People who sell a second chance, never the answer (D3). Prices are shares
# of the floor's income; the dearest also take a share of the purse when
# that is more (D6: they bite at every depth).
SERVICE_SHARE = {
    'repair':      0.15,     # per point of enchantment rust, acid or fire took
    'sharpen':     0.60,     # +1 to the wielded weapon, at most +2 from smiths
    'reinforce':   0.60,     # +1 to the body armour, at most +2 from smiths
    'cut_curse':   0.30,     # a cursed worn thing cut off, and destroyed
    'cure':        0.25,     # poison, disease, sickness, blindness, confusion
    'restore':     0.80,     # every point a drain or disease took, back
    'heal':        0.30,     # wounds bound: back to full health
    'id_retry':    0.30,     # identify with a scribe at your elbow: no backlash
    'map':         0.30,     # the floor's layout
    'porter':      0.50,     # a porter for PORTER_FLOORS floors
}
SERVICE_PURSE_PCT = {
    'restore': 10,
    'cut_curse': 5,
}
SMITH_ENCHANT_CAP = 2
PORTER_FLOORS = 3


def service_price(service: str, level: int, *, purse: int = 0, points: int = 1,
                  markup: float = 1.0) -> int:
    """What a service costs on floor ``level`` (``points`` for repair)."""
    frac = SERVICE_SHARE.get(service, 0.3) * max(1, int(points or 1))
    price = floor_income(level) * frac * float(markup or 1.0)
    pct = SERVICE_PURSE_PCT.get(service)
    if pct:
        price = max(price, max(0, int(purse or 0)) * pct / 100.0)
    return max(5, nice(price))


# --------------------------------------------------------- deep temptations
# A gold figure that should bite at every depth (D6): ``purse_pct`` on a gold
# reward means "this written amount, or that share of what the hero carries,
# whichever is more". "Vell offers you a quarter of what you carry."
def purse_scaled(amount: float, purse: int, pct) -> int:
    try:
        pct = float(pct or 0)
    except (TypeError, ValueError):
        pct = 0.0
    if pct <= 0:
        return int(amount or 0)
    return max(int(amount or 0), nice(max(0, int(purse or 0)) * pct / 100.0))


# Forgoing gold on principle counts as a sacrifice only when the gold was a
# real one: at least this share of the purse at the time (D6; Brandon's karma
# rule, "forgoing a benefit only counts if the benefit was real").
FORGO_MIN_PURSE_SHARE = 0.10


def forgo_is_real(forgone_gold: float, purse: int) -> bool:
    purse = max(0, int(purse or 0))
    if purse <= 0:
        return True
    return float(forgone_gold or 0) >= FORGO_MIN_PURSE_SHARE * purse


# ------------------------------------------------------- encounters, mysteries
# The gold figures written into encounter and mystery data (20 to 450) were
# about 3% of a floor's income at every depth: a paid choice cost nothing and
# a gold reward bought nothing. They already rise with depth in step with
# income, so one multiplier puts all of them at a sixth to a third of a floor.
WRITTEN_GOLD_MULT = 6


def written_gold(amount: float) -> int:
    """A gold figure from encounter or mystery data, at today's scale."""
    return nice(float(amount) * WRITTEN_GOLD_MULT) if amount else 0


def _scale_gold_dict(d: dict, changed: list) -> None:
    if d.get('type') == 'gold' and not d.get('share') and not d.get('service'):
        for key in ('amount', 'min', 'max'):
            if isinstance(d.get(key), (int, float)):
                old = d[key]
                d[key] = written_gold(old)
                changed.append((int(old), d[key]))
    for sub in d.get('rewards') or []:          # 'multi' rewards
        if isinstance(sub, dict):
            _scale_gold_dict(sub, changed)


def _requote(text: str, changed: list) -> str:
    """Rewrite a quoted price in an option's own words: "(30g)" or "50 gold"."""
    import re
    for old, new in changed:
        text = re.sub(rf'(?<![\d,]){old}(?=g\b| ?gold\b| ?coins?\b| ?gp\b)',
                      f'{new:,}' if isinstance(new, int) else str(new), text)
    return text


def share_price(share_class: str, level: int, markup: float = 1.0) -> int:
    """A vendor's price for one thing of a class, at the trader's rate for
    a thing of that class whose kind is not known yet (a random potion from
    a pedlar's bag): the price a trader would ask on this floor, times the
    vendor's own markup (``1.5`` an abyssal dealer, ``0.7`` a desperate one)."""
    frac = MERCHANT_SHARE.get(share_class, 0.5) * (0.6 + 0.2 * UNKNOWN_TIER)
    return max(5, nice(floor_income(level) * frac * float(markup or 1.0)))


def _price_shares(enc: dict, level) -> None:
    """Resolve every ``{"type": "gold", "share": "potion", "markup": 1.5}``
    cost (ECONOMY_REFACTOR_PROPOSAL S5): the ~20 plain vendor options were
    their written gold x 6, never checked against the trader (270 gold for a
    15% heal on floor 1, nine times the trader's potion). They now sit at
    the trader's price on the floor where the encounter stands."""
    lvl = level or enc.get('min_level') or (enc.get('floors') or [1])[0] or 1
    for opt in enc.get('options') or []:
        cost = opt.get('cost')
        if isinstance(cost, dict) and cost.get('type') == 'gold' and cost.get('service'):
            # A vendor's service (D3): priced like a trader's.
            cost['amount'] = service_price(cost['service'], int(lvl),
                                           points=int(cost.get('points', 1) or 1),
                                           markup=cost.get('markup', 1.0))
        elif isinstance(cost, dict) and cost.get('type') == 'gold' and cost.get('share'):
            cost['amount'] = share_price(cost['share'], int(lvl), cost.get('markup', 1.0))


def price_encounter(encounter: dict, level: int | None = None) -> dict:
    """A copy of an encounter definition with its gold costs and rewards at
    today's scale, and any price quoted in an option's label or outcome
    rewritten to match. Called once, when a run's encounters are chosen, so
    the dialog, the affordability check and the payment all see one number.
    ``level`` is the floor it stands on (a vendor's share-priced goods)."""
    if encounter.get('_gold_priced'):
        return encounter
    enc = copy.deepcopy(encounter)
    _price_shares(enc, level)
    for opt in enc.get('options') or []:
        _price_outcome(opt)
        # A choice that costs gold says so. Several did not ("Ask about
        # treasure", 350 gold, shown only as a missing purse afterwards).
        cost = opt.get('cost')
        if isinstance(cost, dict) and cost.get('type') == 'gold':
            amount = cost.get('amount', cost.get('max', cost.get('min')))
            label = opt.get('label')
            if (isinstance(amount, (int, float)) and amount > 0 and isinstance(label, str)
                    and str(int(amount)) not in label and f'{int(amount):,}' not in label):
                opt['label'] = f"{label.rstrip()} ({int(amount):,} Gold)"
    # Escort specs shared through '$ref' (DEEDS_KARMA_DESIGN 4.9).
    for spec in (enc.get('escorts') or {}).values():
        if isinstance(spec, dict):
            _price_escort(spec)
    enc['_gold_priced'] = True
    return enc


def _price_outcome(o: dict) -> None:
    """Scale the gold in one option or outcome object, its quoted prices, and
    every outcome nested in it: a quiz option's ``pass`` / ``fail``, its
    ``delayed`` rewards, and an inline ``escort``'s arrival and failure."""
    changed: list = []
    for key in ('cost', 'reward', 'fail_reward'):
        if isinstance(o.get(key), dict):
            _scale_gold_dict(o[key], changed)
    for d in o.get('delayed') or []:
        if isinstance(d, dict) and isinstance(d.get('reward'), dict):
            _scale_gold_dict(d['reward'], changed)
    if changed:
        for key in ('label', 'outcome'):
            if isinstance(o.get(key), str):
                o[key] = _requote(o[key], changed)
    for key in ('pass', 'fail'):
        if isinstance(o.get(key), dict):
            _price_outcome(o[key])
    if isinstance(o.get('escort'), dict):
        _price_escort(o['escort'])


def _price_escort(spec: dict) -> None:
    for key in ('on_arrive', 'on_fail'):
        if isinstance(spec.get(key), dict):
            _price_outcome(spec[key])


# ------------------------------------------------- coins lying in the dungeon
# Gold by lore (D1): coins lie where people lost them, not inside wolves.
COIN_PILE_CHANCE = 0.25            # an ordinary room (not the first) holds a pile
COIN_PILE_SHARE = (0.015, 0.04)    # a dropped purse, a dead man's pay
LAIR_GOLD_SHARE = (0.08, 0.20)     # a monster den's or a barracks' heap


# ------------------------------------------------------------- smaller amounts
BRIBE_SHARE = (0.05, 0.15)        # a bribe: this much of the floor's income
BRIBE_TURNS = 3                   # how long the bribed monster stands aside
GRAVE_SMALL_SHARE = (0.02, 0.08)  # a few coins buried with the dead
GRAVE_RICH_SHARE = (0.08, 0.25)   # a rich burial
THRONE_SHARE = (0.04, 0.15)       # wedged in the cushions
SCRAP_SHARE = 0.01                # a spare lockpick sold for scrap


def roll_share(rng, level: int, bounds: tuple) -> int:
    """A random round figure between two shares of the floor's income."""
    lo, hi = bounds
    return max(5, nice(floor_income(level) * rng.uniform(lo, hi)))


# ------------------------------------------------- a share of the purse, paid
# A choice that costs "N% of your purse" (DEEDS_KARMA_DESIGN 4.13) was free
# with an empty purse, and the purse could be emptied by dropping the gold
# first (ECONOMY_REFACTOR_PROPOSAL S1). A share the hero CHOOSES to pay now
# has a floor: N% of two floors' income. Losses that land on the hero (a
# thief, a delayed consequence) stay a plain share of what is there.
PCT_COST_FLOOR_INCOMES = 2.0


def pct_cost(purse: int, pct: float, level: int) -> int:
    """What a chosen ``gold_pct`` cost of ``pct`` takes from ``purse`` on
    floor ``level``: ``pct``% of the purse, never less than ``pct``% of
    ``PCT_COST_FLOOR_INCOMES`` floors' income."""
    try:
        pct = float(pct)
    except (TypeError, ValueError):
        pct = 0.0
    if pct <= 0:
        return 0
    purse = max(0, int(purse or 0))
    least = nice(floor_income(level) * PCT_COST_FLOOR_INCOMES * pct / 100.0)
    return max(least, int(purse * pct / 100.0))


# ------------------------------------------------------------------ theft
# A thief (src/theft.py) cuts away this share of the purse the hero carries.
# A share of the purse, not a written amount: it means the same on floor 3
# and on floor 70, and the hero gets all of it back by killing the thief.
THEFT_PURSE_SHARE = (0.15, 0.30)


def theft_take(rng, purse: int) -> int:
    """How much of a purse of `purse` gold a thief gets away with."""
    purse = int(purse or 0)
    if purse <= 0:
        return 0
    lo, hi = THEFT_PURSE_SHARE
    return max(1, min(purse, int(round(purse * rng.uniform(lo, hi)))))
