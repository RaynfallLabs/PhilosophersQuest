# Recursive shadowcasting FOV
# Based on: http://www.roguebasin.com/index.php?title=FOV_using_recursive_shadowcasting

# (xx, xy, yx, yy) transform matrices — one per octant
_OCTANTS = [
    ( 1,  0,  0,  1),
    ( 0,  1,  1,  0),
    ( 0, -1,  1,  0),
    (-1,  0,  0,  1),
    (-1,  0,  0, -1),
    ( 0, -1, -1,  0),
    ( 0,  1, -1,  0),
    ( 1,  0,  0, -1),
]


def calculate_fov(dungeon, px: int, py: int, radius: int) -> set:
    """Return the set of (x, y) tiles visible from (px, py) within radius."""
    visible = {(px, py)}
    for xx, xy, yx, yy in _OCTANTS:
        _cast_light(dungeon, visible, px, py, 1, 1.0, 0.0, radius, xx, xy, yx, yy)
    return visible


def _cast_light(dungeon, visible, cx, cy, row, start, end, radius, xx, xy, yx, yy):
    if start < end:
        return

    radius_sq = radius * radius
    new_start = 0.0

    for j in range(row, radius + 1):
        dx, dy = -j - 1, -j
        blocked = False

        while dx <= 0:
            dx += 1
            wx = cx + dx * xx + dy * xy
            wy = cy + dx * yx + dy * yy

            l_slope = (dx - 0.5) / (dy + 0.5)
            r_slope = (dx + 0.5) / (dy - 0.5)

            if start < r_slope:
                continue
            if end > l_slope:
                break

            if dx * dx + dy * dy < radius_sq and dungeon.in_bounds(wx, wy):
                visible.add((wx, wy))

            if blocked:
                if dungeon.is_opaque(wx, wy):
                    new_start = r_slope
                    continue
                else:
                    blocked = False
                    start = new_start
            else:
                if dungeon.is_opaque(wx, wy) and j < radius:
                    blocked = True
                    _cast_light(dungeon, visible, cx, cy, j + 1, start, l_slope,
                                radius, xx, xy, yx, yy)
                    new_start = r_slope

        if blocked:
            break
