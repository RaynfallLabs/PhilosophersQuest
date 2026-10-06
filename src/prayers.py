"""The prayers a player can choose between, and what each one grants.

Pressing the prayer key opens a short list; the player picks one, answers the
theology chain, and the prayer answers according to how far the chain went.
Pure data and arithmetic: no pygame, no game state. `game_divine` does the
kneeling, the quiz and the messages.

Adding a prayer later (the owner intends more, opened by karma) means one
entry in PRAYERS and one branch in `DivineMixin._resolve_simple_prayer`.
"""
from __future__ import annotations

MERCY = 'mercy'
GUIDE_MY_HAND = 'guide_my_hand'

# id, the words on the menu, one line of what it asks for, and the lowest
# karma at which Heaven will hear it at all (None = always offered).
PRAYERS: list[dict] = [
    {
        'id': MERCY,
        'name': "Lord, Have Mercy",
        'asks': "Strength, healing and shelter, as far as your prayer reaches.",
        'title': "PRAYER  --  LORD, HAVE MERCY",
        'karma_min': None,
    },
    {
        'id': GUIDE_MY_HAND,
        'name': "Michael, Guide My Hand",
        'asks': "Wisdom for the fight in front of you. While it lasts, "
                "the clock runs long.",
        'title': "PRAYER  --  MICHAEL, GUIDE MY HAND",
        'karma_min': None,
    },
]


def available(karma: int = 0) -> list[dict]:
    """The prayers on offer at this karma, in menu order."""
    return [p for p in PRAYERS
            if p['karma_min'] is None or karma >= p['karma_min']]


def by_id(prayer_id: str) -> dict:
    return next(p for p in PRAYERS if p['id'] == prayer_id)


# ---------------------------------------------------------------------------
# Michael, Guide My Hand
#
# The answer is wisdom, lent for a while: the combat clock is the player's
# wisdom in seconds, so this is more time to chain sums. It is sized as a
# SHARE of the wisdom the player already has (never less than the flat
# figure), because five more seconds is a great deal on floor 5 and very
# little on floor 90. A full chain doubles the clock.
#
# effective chain (theology chain, +1 at an altar) -> (share, least, turns)
# ---------------------------------------------------------------------------
GUIDE_TABLE: dict[int, tuple[float, int, int]] = {
    1: (0.30, 3, 3),
    2: (0.45, 5, 4),
    3: (0.60, 6, 5),
    4: (0.80, 8, 6),
    5: (1.00, 10, 8),
    6: (1.20, 12, 10),
}
# A burst, not a state of being: a full chain is eight of your turns. (The
# first cut ran 6 to 18 turns, which covered most of a boss fight.)
# A prayer made at or below this share of health is heard differently.
DESPERATE_HP = 0.25
DESPERATE_SHIELD_TURNS = 3
DESPERATE_EXTRA_TURNS = 2


def guide_my_hand(wis: int, effective_chain: int, karma: int = 0,
                  desperate: bool = False) -> tuple[int, int]:
    """(wisdom lent, turns it lasts) for an answered prayer. (0, 0) if the
    chain was empty."""
    if effective_chain <= 0:
        return 0, 0
    share, least, turns = GUIDE_TABLE[min(effective_chain, max(GUIDE_TABLE))]
    bonus = max(least, int(round(max(1, wis) * share)))
    # Karma lengthens or shortens the gift a little; it never removes it.
    turns = max(2, turns + max(-1, min(1, int(int(karma) / 5))))
    if desperate:
        turns += DESPERATE_EXTRA_TURNS
    return bonus, turns
