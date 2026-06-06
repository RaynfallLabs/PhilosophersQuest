"""Dungeon monster-distribution regression tests (2026-06-06 per-room pass).

Before the fix, whole-floor population threw a small global count at the rooms
and let each monster pick a room at random -> ~31% room coverage (measured over
400 seeds), most rooms empty, the rest lumped ("all the monsters are in one
corner"). populate_floor() now rolls EVERY room for occupancy, spreading a
baseline across the level; packs/dens still cluster intentionally on top. These
tests lock in the spread, and that the count-based spawn_monsters() STILL lumps
(the zoo/den/lair callers depend on that).
"""
from dungeon import generate_dungeon, populate_floor, spawn_monsters


def _room_of(mx, my, rooms):
    """Index of the room whose inner area contains (mx, my), or None."""
    for i, r in enumerate(rooms):
        if r.x < mx < r.x + r.width - 1 and r.y < my < r.y + r.height - 1:
            return i
    return None


def _avg_room_coverage(level, seeds):
    """Mean fraction of spawnable rooms (excluding the start room) that hold at
    least one monster, over `seeds` freshly generated BSP floors."""
    covs = []
    for _ in range(seeds):
        d = generate_dungeon(80, 50, level)
        spawn_rooms = d.rooms[1:]
        if len(spawn_rooms) < 4:
            continue  # skip degenerate / maze-ish floors; measure real BSP ones
        density = min(0.50 + level / 130, 0.95)
        monsters = populate_floor(d.rooms, level, d, occupancy=density)
        occupied = set()
        for m in monsters:
            ri = _room_of(m.x, m.y, d.rooms)
            if ri:                       # ri != 0 and not None
                occupied.add(ri)
        covs.append(len(occupied) / len(spawn_rooms))
    assert covs, 'no qualifying floors generated'
    return sum(covs) / len(covs)


def test_populate_floor_spreads_across_rooms_shallow():
    # Old algorithm measured ~0.31 average coverage. Shallow density ~0.54 here.
    avg = _avg_room_coverage(5, seeds=40)
    assert avg >= 0.45, f'shallow room coverage too low: {avg:.2f} (old bug was ~0.31)'


def test_populate_floor_spreads_across_rooms_deep():
    # Deep density ~0.78; assert well above the old ~0.31.
    avg = _avg_room_coverage(37, seeds=30)
    assert avg >= 0.62, f'deep room coverage too low: {avg:.2f}'


def test_populate_floor_never_returns_empty():
    for _ in range(40):
        d = generate_dungeon(80, 50, 3)
        monsters = populate_floor(d.rooms, 3, d, occupancy=0.5)
        assert monsters, 'populate_floor returned a completely empty floor'


def test_spawn_monsters_still_lumps_for_targeted_clusters():
    """The zoo/graveyard/den/lair callers pass a single room (the den/lair ones
    pass it twice, since rooms[1:] skips the first) and rely on spawn_monsters
    concentrating monsters there. Confirm the intentional cluster still works."""
    d = generate_dungeon(80, 50, 10)
    target_room = d.rooms[1]
    extras = spawn_monsters([target_room, target_room], 10, d,
                            min_count=3, max_count=5)
    assert extras, 'spawn_monsters produced no monsters for a targeted room'
    inner = set(target_room.inner_tiles())
    assert all((m.x, m.y) in inner for m in extras), \
        'targeted-cluster monsters escaped their room'
