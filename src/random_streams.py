"""Random streams of their own that still follow the game's seed.

The floor's builders (generate_dungeon, populate_floor, spawn_items, the
hidden chambers, the war-band, the clan, the dressing, the creatures' jobs)
each roll on a generator of their own, so one builder's rolls never shift
another's. They used to make it with a bare ``random.Random()``, which
Python seeds from the operating system: ``random.seed(s)`` never reached a
layout, so the same seed walked a new floor in every process. A floor from
a bug report could not be replayed, and a test that needed a certain
layout passed or failed by luck (the 3.5.4 release run put Old Nickel in a
corner of his room with his back to the wall).

``own_stream()`` takes the seed from the shared stream instead: one 64-bit
draw, so the shared stream moves on and the next builder gets a different
stream. In play the shared stream is seeded from the operating system, so
floors are as random as before. After ``random.seed(s)`` the same floors
come out in every process. (tests/test_seeded_floor_is_stable.py)
"""
from __future__ import annotations

import random


def own_stream() -> random.Random:
    """A generator of its own, seeded by one draw from the shared stream."""
    return random.Random(random.getrandbits(64))
