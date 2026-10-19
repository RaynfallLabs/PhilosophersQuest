"""Thieves that really steal (an attack with `steal` in monsters.json).

    {"name": "Cut Purse", "damage": "1d4+1", "type": "slash",
     "steal": "gold", "steal_chance": 0.7}
    "after_theft": "flee" | "teleport"          (on the monster; default flee)

* `steal`: "gold" takes a share of the hero's purse (economy.THEFT_PURSE_SHARE),
  "item" takes one unworn thing from the pack (a piece of treasure catches a
  thief's eye most of all), "any" takes gold or an item. What is taken leaves
  the hero lighter (coins weigh, treasure.py); a monster has no carry limit.
* A blow with `steal` that lands rolls `steal_chance` (default 1.0); the
  monster notes the wish (`_wants_steal`) and the game carries it out here
  right after the blow, because gold belongs to the Game, not the Player.
* A thief takes one haul. Carrying it, it runs (Monster.take_turn: it flees
  the hero and fights only when cornered). With `after_theft: teleport` it
  first vanishes to a far part of the same floor (the leprechaun's trick).
  It never leaves the floor with the loot.
* Whatever it carries falls on its tile when it dies, by any death (the
  game's one kill handler calls `give_back`), so the hero can always win
  it back by running it down.

Never stolen: anything worn or wielded, containers, mystery keys,
scripted quest and story pieces (items.scripted_only_ids: the Philosopher's
Stone, seals, the Thread and the like), and whatever no NPC may take either
(items.withheld: the Philosopher's Shard, named uniques, one-of-a-kind
things). A thief would otherwise be able to end a run.
"""
from __future__ import annotations

import random

TELEPORT_MIN_DISTANCE = 12      # a teleporting thief lands at least this far away
# Magical and bright things draw a thief's eye three times as often.
# Treasure most of all: a gem is the perfect thing to steal, small and dear.
BRIGHT_KINDS = ('Wand', 'Ring', 'Amulet', 'Accessory', 'Scroll', 'Potion', 'Artifact', 'Spellbook',
                'Treasure')
BRIGHT_WEIGHT = 3.0


def carried(monster) -> list:
    """The items this monster has stolen (never None)."""
    items = monster.__dict__.get('stolen_items')
    if items is None:
        items = []
        monster.__dict__['stolen_items'] = items
    return items


def has_loot(monster) -> bool:
    return bool(int(getattr(monster, 'stolen_gold', 0) or 0) or monster.__dict__.get('stolen_items'))


def stealable(player) -> list:
    """Pack items a thief can take."""
    from items import Container, scripted_only_ids, withheld
    from mystery_system import MysteryKeyItem
    worn = {id(i) for i in player.worn_items()}
    locked = scripted_only_ids()
    out = []
    for it in getattr(player, 'inventory', None) or ():
        if id(it) in worn or isinstance(it, (Container, MysteryKeyItem)):
            continue
        if getattr(it, 'id', '') in locked or getattr(it, 'bound_to_wielder', False):
            continue
        # Quest pieces, named uniques and one-of-a-kind things: the same rule
        # that keeps an NPC from taking them as payment (MON-01).
        if withheld(it):
            continue
        out.append(it)
    return out


def _pick_item(rng, items):
    weights = [BRIGHT_WEIGHT if any(k in type(it).__name__ for k in BRIGHT_KINDS) else 1.0
               for it in items]
    return rng.choices(items, weights=weights, k=1)[0]


def _teleport_away(game, m, rng=random) -> bool:
    """Set the thief down on a far, walkable, free tile the hero can reach."""
    from geom import all_occupied_tiles
    d = game.dungeon
    p = game.player
    taken = all_occupied_tiles(game.monsters, exclude=m)
    try:
        taken |= game._occupants()
    except Exception:
        taken.add((p.x, p.y))
    try:
        from dungeon import _reach_from_stairs
        reach = _reach_from_stairs(d)
    except Exception:
        reach = None
    spots = [(x, y) for y in range(d.height) for x in range(d.width)
             if d.is_walkable(x, y) and (x, y) not in taken
             and (not reach or (x, y) in reach)
             and max(abs(x - p.x), abs(y - p.y)) >= TELEPORT_MIN_DISTANCE]
    if not spots:
        return False
    m.x, m.y = rng.choice(spots)
    m._aware = True
    return True


def steal(game, m, kind: str, rng=random) -> str:
    """The thief `m` takes what `kind` allows. Returns the message ('' when
    there was nothing to take or it already carries a haul)."""
    from monster import the_name
    if has_loot(m) or not getattr(m, 'alive', False):
        return ''
    player = game.player
    # A hero who reads this family's hands (Mortal Foes' Read Their Hands,
    # src/family_edges.py) is never robbed by it: its trigger line says so.
    try:
        import family_edges
        if family_edges.theft_immune(player, m):
            return ''
    except ImportError:
        pass
    purse = int(getattr(game, 'player_gold', 0) or 0)
    items = stealable(player)
    if kind == 'any':
        kind = 'gold' if purse > 0 and (not items or rng.random() < 0.5) else 'item'
    who = the_name(m)
    if kind == 'gold':
        from economy import theft_take
        amount = theft_take(rng, purse)
        if amount <= 0:
            return ''
        game.player_gold = purse - amount
        m.stolen_gold = int(getattr(m, 'stolen_gold', 0) or 0) + amount
        msg = f"{who} cuts your purse and makes off with {amount:,} gold!"
    else:
        if not items:
            return ''
        it = _pick_item(rng, items)
        taken = player.drop_stack(it, 1)
        if taken is None:
            return ''
        carried(m).append(taken)
        try:
            name = game._display_name(taken)
        except Exception:
            name = getattr(taken, 'name', 'something')
        msg = f"{who} snatches your {name} and runs!"
    m._aware = True
    m._flee_timer = 0
    if getattr(m, 'after_theft', 'flee') == 'teleport' and _teleport_away(game, m, rng):
        msg += f" In a blink {the_name(m, lower=True)} is gone, somewhere else on this floor."
    return msg


def give_back(game, m) -> list[str]:
    """Drop everything a dead thief was carrying on its tile. Returns the
    messages."""
    msgs = []
    gold = int(getattr(m, 'stolen_gold', 0) or 0)
    items = list(m.__dict__.get('stolen_items') or ())
    if not gold and not items:
        return msgs
    from items import add_gold_to_tile
    if gold:
        # The hero's own gold coming back, not a find: a gold ring
        # (Draupnir) must not double it (ECONOMY_REFACTOR_PROPOSAL S2).
        add_gold_to_tile(game.ground_items, gold, m.x, m.y, found=False)
        m.stolen_gold = 0
        msgs.append(f"Your stolen {gold:,} gold spills out where it fell.")
    for it in items:
        it.x, it.y = m.x, m.y
        game.ground_items.append(it)
        try:
            name = game._display_name(it)
        except Exception:
            name = getattr(it, 'name', 'something')
        msgs.append(f"Your stolen {name} falls to the ground.")
    m.__dict__['stolen_items'] = []
    return msgs
