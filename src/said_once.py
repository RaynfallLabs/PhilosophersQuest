"""Said Once: a line that tells the hero a known thing spares him a question
is said the first time it does so for that kind, then never again this run.

Brandon (2026-11-22): "Repetitive messages like 'You know how to butcher..
X. No question needed' is just noise. The player gets it." One rule for
every such line:

  * Butchered Before (butchered.py): the first free harvest of each kind.
  * Known by Hand (known_by_hand.py): the first time each kind of gear goes
    on with no quiz, a chain-equip legend's too.

The corpse card, the Bestiary page and the equip menus show the mark
(Butchered Before, Known by Hand) every time; only the log goes quiet.

The hero remembers what was said for this run (Player.said_once, a set of
'topic:kind' strings, saved; an old save starts with none, so a kind may be
told once more). Pure rules over the player's store; no pygame.
"""
from __future__ import annotations


def _store(player) -> set:
    s = player.__dict__.get('said_once')
    if not isinstance(s, set):
        s = set(s or ())
        player.__dict__['said_once'] = s
    return s


def said(player, topic: str, key: str) -> bool:
    """Has this line been said for this kind already?"""
    if player is None or not key:
        return False
    return f'{topic}:{key}' in _store(player)


def first(player, topic: str, key: str) -> bool:
    """True the first time ``topic`` is asked for kind ``key`` (it is then
    remembered); False after. No hero (a harness) or no kind: always True."""
    if player is None or not key:
        return True
    store = _store(player)
    tag = f'{topic}:{key}'
    if tag in store:
        return False
    store.add(tag)
    return True


def line(player, topic: str, key: str, text: str) -> str:
    """``text`` the first time for this kind, '' after."""
    return text if text and first(player, topic, key) else ''
