"""The gold economy in one place: what a floor earns, and what things cost.

Pure arithmetic, no game state. Everything that grants or charges gold by a
rule (merchant prices, bribes, encounter costs and rewards, mystery tribute,
gold found in graves and thrones) reads from here, so the pieces stay in
proportion to each other and to what a floor actually pays.

Measured 2026-10-05 with the real floor generator (ground gold, chests opened
seven times in ten, monster drops including wanderers), 12 to 16 floors per
depth: about 235 gold on floor 1, 440 on floor 5, 1,300 on floor 15, 2,600 on
floor 25, 4,300 on floor 45, 6,500 on floor 65, 8,000 on floor 95. That is a
straight line. The price formula before this module (40 x floor^1.15) matched
it deep down and was six times too low at the top: floor-1 prices were pocket
change.
"""
from __future__ import annotations

import copy

INCOME_BASE = 150
INCOME_PER_FLOOR = 90


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


# --------------------------------------------------------------- the merchant
# Share of a floor's income, by item class: one floor buys a consumable or
# two, an accessory takes about two floors and a named unique about four.
MERCHANT_SHARE = {
    'potion': 0.15, 'food': 0.10, 'ammo': 0.10,
    'scroll': 0.50, 'wand': 0.50, 'spellbook': 0.80,
    'weapon': 0.60, 'armor': 0.60, 'shield': 0.60,
    'accessory': 1.50,
}
UNIQUE_GEAR_SHARE = 3.0


def merchant_price(item, level: int = 1) -> int:
    """Gold cost of one merchant item on floor `level`."""
    tier = getattr(item, 'quiz_tier', None) or getattr(item, 'tier', 1) or 1
    try:
        tier = max(1, min(5, int(tier)))
    except (TypeError, ValueError):
        tier = 1
    ic = getattr(item, 'item_class', 'misc')
    frac = MERCHANT_SHARE.get(ic, 0.5)
    if ic in ('weapon', 'armor', 'shield') and getattr(item, 'is_unique', False):
        frac = UNIQUE_GEAR_SHARE
    return max(5, nice(floor_income(level) * frac * (0.6 + 0.2 * tier)))


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
    if d.get('type') == 'gold':
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
        text = re.sub(rf'(?<![\d,]){old}(?=g\b| ?gold\b| ?coins?\b| ?gp\b)', str(new), text)
    return text


def price_encounter(encounter: dict) -> dict:
    """A copy of an encounter definition with its gold costs and rewards at
    today's scale, and any price quoted in an option's label or outcome
    rewritten to match. Called once, when a run's encounters are chosen, so
    the dialog, the affordability check and the payment all see one number."""
    if encounter.get('_gold_priced'):
        return encounter
    enc = copy.deepcopy(encounter)
    for opt in enc.get('options') or []:
        changed: list = []
        for key in ('cost', 'reward', 'fail_reward'):
            if isinstance(opt.get(key), dict):
                _scale_gold_dict(opt[key], changed)
        if changed:
            for key in ('label', 'outcome'):
                if isinstance(opt.get(key), str):
                    opt[key] = _requote(opt[key], changed)
    enc['_gold_priced'] = True
    return enc


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
