"""Butchered Before: a creature the hero has identified and harvested once is
harvested again with no question (Brandon, 2026-11-17: "once you have
IDENTIFIED AND SUCCESSFULLY HARVESTED a specific monster ONCE, you can
automatically harvest any others").

Known by Hand's pattern (known_by_hand.py), at the butcher's table:

  * The kind is the corpse's monster id ("giant_rat"). A different kind asks
    its own question, kin or not: every goblin gives Goblin Gristle, but a
    goblin archer is a kind of its own.
  * A right answer that gains a part is remembered for this run
    (Player.butchered_kinds, saved; an old save starts with none), whether
    the kind is identified yet or not. A wrong answer remembers nothing.
  * The free harvest needs both at the moment of the harvest: the kind
    butchered before AND identified, its full Bestiary page open
    (family_lore.has_page, the game's one rule for an identified kind:
    studied by a corpse study or the Wand of Probing, its page opened by the
    Book of Thoth, a Scroll of Omnisight or a gate boss's quest, or its
    family known at tier 1 or more). A success recorded before the kind was
    identified counts from the moment it is.
  * A free harvest is the right answer's harvest (food_system.harvest_corpse):
    the same part at the same tier, the family's extra portion, the corpse
    used up and the turn spent. No quiz is started, so no answer is counted
    (the Seeker's quiz counters, the streak, the quirks that count answers);
    it is still a harvest (the Seeker's harvest count, the quirks that count
    kinds harvested).
  * A person is searched, never harvested (food_system.search_corpse), and
    never comes here.

One set of kinds, never a number changed (docs/systems/README.md).
Pure rules over the player's store; no pygame, no game state.
"""
from __future__ import annotations

MARK = "Butchered Before"
CARD_LINE = "Butchered before: no question"


def kind_key(obj) -> str:
    """The kind a corpse (or a monster, or a kind id) is for the butcher: its
    monster id ('' for none)."""
    if isinstance(obj, str):
        return obj
    return str(getattr(obj, 'monster_id', None) or getattr(obj, 'kind', None) or '')


def _store(player) -> set:
    s = player.__dict__.get('butchered_kinds')
    if not isinstance(s, set):
        s = set(s or ())
        player.__dict__['butchered_kinds'] = s
    return s


def butchered(player, obj) -> bool:
    """Has the hero harvested this kind right before (identified or not)?"""
    if player is None:
        return False
    key = kind_key(obj)
    return bool(key) and key in _store(player)


def identified(player, obj) -> bool:
    """Is this kind identified: its full Bestiary page open
    (family_lore.has_page)?"""
    key = kind_key(obj)
    if player is None or not key:
        return False
    import family_lore
    try:
        return bool(family_lore.has_page(player, key))
    except (OSError, ValueError):
        return False


def is_free(player, obj) -> bool:
    """Does harvesting this kind skip the question now? Butchered before and
    identified, both."""
    return butchered(player, obj) and identified(player, obj)


def learn(player, obj) -> bool:
    """A right answer gained a part of this kind: remember it. True when it
    is newly remembered."""
    if player is None:
        return False
    key = kind_key(obj)
    if not key:
        return False
    store = _store(player)
    if key in store:
        return False
    store.add(key)
    return True


def fires_line(corpse) -> str:
    """What the log says as a known kind is harvested with no question: "You
    know how to butcher a Giant Rat. No question needed." (monster.a_name of
    the creature the corpse was: "an Orc Scout", "Fenrir")."""
    from monster import a_name, kind_of_corpse
    return f"You know how to butcher {a_name(kind_of_corpse(corpse))}. No question needed."


def card_line(player, obj) -> str:
    """The corpse card's and the Bestiary page's line for a kind harvested
    with no question now, else ''."""
    return CARD_LINE if is_free(player, obj) else ''
