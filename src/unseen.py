"""What the hero can and cannot see of a monster standing on a tile he CAN see.

The field of view says which tiles are in sight. Three kinds of creature can
stand on one of those tiles and still not be seen:

* an ambusher that has not sprung (`ai_pattern` 'ambush': piercers, lurkers,
  cloakers), which is not drawn at all until it is aware of the hero;
* a mimic-AI creature still posing as something else (`ai_pattern` 'mimic':
  the Lurking Horror poses as a chest, the Gilded Mimic as a spilled hoard),
  which is drawn as the thing it imitates (its `disguise` in monsters.json);
* an INVISIBLE creature (`invisible: true` in monsters.json), which nobody
  sees unless he has a way to see the unseen: see invisible (cooked meals,
  the beholder's and cyclops's prime cuts), true sight, telepathy, or the
  clairvoyance the Detect Monsters spell lends.

An invisible creature that is not seen still moves and fights as usual. Its
blows are reported as "Something unseen ..." (`Monster._unseen`, kept by
`Game._sync_unseen`), it is left out of the sidebar, look and target lists,
and walking into it does not attack: the hero feels something there
(`Monster._felt_at`), and the next blow at that tile is a real attack.

Every place that asks "can the hero see this monster?" asks here, so the
rules live in one file.
"""
from geom import monster_at_tile

# Effects that let the hero see an invisible creature.
REVEAL_EFFECTS = ('see_invisible', 'truesight', 'telepathy', 'clairvoyant')

# A seen invisible creature is drawn in its own art with this multiply tint:
# a cold pale blue, see-through, so the player knows it is normally unseen.
SEE_INVISIBLE_TINT = (160, 195, 255, 135)

# The faint shimmer left on a tile where the hero has felt something unseen.
FELT_SHIMMER = (200, 215, 255)


def sees_invisible(player) -> bool:
    """True when the hero has any way to see invisible creatures."""
    has = getattr(player, 'has_effect', None)
    if has is None:
        return False
    return any(has(e) for e in REVEAL_EFFECTS)


def is_invisible(m) -> bool:
    """The creature itself is invisible by nature (whoever is looking)."""
    return bool(getattr(m, 'invisible', False))


def unseen(m, player) -> bool:
    """An invisible creature the hero has no way to see."""
    return is_invisible(m) and not sees_invisible(player)


def lurking(m) -> bool:
    """An ambusher that has not sprung, or a mimic still in its disguise."""
    if getattr(m, '_aware', False):
        return False
    return getattr(m, 'ai_pattern', '') in ('ambush', 'mimic')


def disguise(m):
    """The thing an un-sprung mimic-AI creature is drawn as, or None.

    A dict {'item': <item sprite id>, 'name': <what the hero sees>} from the
    creature's `disguise` field in monsters.json, or {'tile': <map feature
    sprite, e.g. 'stairs_down'>, 'name': ...} for one posing as part of the
    map (the Hellmouth: src/false_stairs.py seats it)."""
    if getattr(m, 'ai_pattern', '') != 'mimic' or getattr(m, '_aware', False):
        return None
    d = getattr(m, 'disguise', None)
    return d if isinstance(d, dict) and (d.get('item') or d.get('tile')) else None


def concealed(m, player) -> bool:
    """The hero cannot see this creature even when its tile is in sight."""
    return lurking(m) or unseen(m, player)


def seen(m, visible, player) -> bool:
    """The hero can see this creature: alive, on a tile in sight (any tile of
    a big creature's footprint), and not concealed."""
    if not getattr(m, 'alive', False) or visible is None:
        return False
    fw, fh = getattr(m, 'footprint', (1, 1)) or (1, 1)
    in_sight = any((m.x + dx, m.y + dy) in visible
                   for dx in range(int(fw)) for dy in range(int(fh)))
    return in_sight and not concealed(m, player)


def seen_monster_at(monsters, x, y, player):
    """The creature on (x, y) if the hero can see it there, else None."""
    m = monster_at_tile(monsters, x, y)
    if m is None or concealed(m, player):
        return None
    return m
