"""Brandon's first Dungeon Alive play-test (2026-11-12).

"some of your new additions just look out of place, like a cattle skull
sitting on the ground. Now we have big empty rooms with random stuff on the
floor. I also noticed that a SHIT TON of monsters all descended on me at
once, early on the first floor... it also makes me wonder if the triggers
arent too sensitive for some of these? they all seemed to come running"

* A fight is quieter (5 tiles, not 8); a sleeper gets one chance to wake a
  turn, not one per noise; the squeaky board reaches 20 tiles, not the floor.
* The horns of consecration (painted as a bull's skull) are redrawn in code
  (tools/content/genart/horns.py: the Knossos shape) and back in the
  Labyrinth, with a fallen column drum beside them.
* Loose objects lie against a wall in one small group; only flat marks
  (scorch, cracks, ash, snow, straw) lie out in a room or in a corridor.
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))

import pytest  # noqa: E402

import decor  # noqa: E402
import senses  # noqa: E402


# ------------------------------------------------------------------ noise

def test_a_fight_carries_five_tiles_and_the_squeak_twenty():
    n = senses.data()['noise']
    assert n['melee'] == 5 and n['struck'] == 5
    assert n['squeak'] == 20
    w = senses.data()['waking']
    assert w['loud'] <= 0.4 and w['loud_far'] <= 0.15


class _CountingRng:
    def __init__(self, value):
        self.value = value
        self.calls = 0

    def random(self):
        self.calls += 1
        return self.value


def test_a_sleeper_gets_one_chance_to_wake_a_turn():
    from test_senses import Hero, make, two_rooms
    dun = two_rooms()
    hero = Hero(3, 3)
    gob = make('goblin', 5, 5)
    gob.add_effect('sleeping', 500)
    senses.emit(dun, 4, 4, 'melee')
    senses.emit(dun, 4, 4, 'struck')                 # one round of a fight: two noises
    rng = _CountingRng(0.99)                         # never low enough to wake
    assert senses.resolve_noises(dun, [gob], hero, rng=rng) == []
    assert rng.calls == 1
    assert gob.has_effect('sleeping')


def test_the_squeaky_board_no_longer_calls_the_whole_floor():
    from test_senses import make, two_rooms
    dun = two_rooms()
    near, far = make('goblin', 4, 4), make('goblin', 18, 2)     # far: some 35 tiles round
    senses.rouse_near([near, far], 3, 3, senses.noise_radius('squeak'), dun)
    assert near._goal == (3, 3)
    assert far.__dict__.get('_goal') is None


# ------------------------------------------------------------------ props

LOOSE_OBJECTS = {'bone_pile', 'rubble', 'broken_pot', 'snake_skin', 'statue_rubble',
                 'slayer_bones', 'frozen_bones', 'broken_fetter', 'roots', 'candles'}


def test_the_redrawn_horns_are_back_in_the_labyrinth():
    lab = decor.domain_by_id('labyrinth')
    assert set(lab['decor']['stand']['ids']) == {'horns_consecration', 'column_drum'}
    assert decor.boss_floors()['floors']['20']['entrance'] == 'horns_consecration'
    from PIL import Image
    pic = Image.open(os.path.join(ROOT, 'assets', 'tiles', 'env', 'fixtures', 'horns_consecration.png'))
    assert pic.size == (64, 64) and pic.mode == 'RGBA'
    # The Knossos shape: one solid base, two horns with clear air between them above it.
    a = pic.getchannel('A').load()
    ys = [y for y in range(64) if any(a[x, y] for x in range(64))]
    top, bottom = ys[0], ys[-1]
    mid_row = top + (bottom - top) // 4                         # a quarter of the way down
    runs, inside = 0, False
    for x in range(64):
        if a[x, mid_row] and not inside:
            runs += 1
        inside = bool(a[x, mid_row])
    assert runs == 2                                            # two horns, not a skull


def test_flat_marks_are_marked_and_objects_are_not():
    for fid in ('scorch_mark', 'ember_crack', 'ash_drift', 'snow_drift', 'straw', 'reeds'):
        assert decor._flat(fid), fid
    for fid in LOOSE_OBJECTS:
        assert not decor._flat(fid), fid


@pytest.fixture(scope='module')
def floors():
    import bones
    bones.load_bones = lambda *a, **k: None
    from level_manager import LevelManager
    lm = LevelManager()
    out = []
    for lvl in (1, 4, 9, 14, 25, 33, 45, 66, 85):
        random.seed(7000 + lvl)
        d, _m, _i = lm.generate(lvl)
        out.append((lvl, d))
    return out


def test_no_loose_object_lies_out_in_the_open(floors):
    from dungeon import WALL
    bad = []
    for lvl, d in floors:
        if lvl % 20 == 0:
            continue                                  # the finales dress by their own rules
        for (x, y), fid in (d.__dict__.get('fixtures') or {}).items():
            if fid not in LOOSE_OBJECTS:
                continue
            walls = sum(1 for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if d.in_bounds(x + ox, y + oy) and d.tiles[y + oy][x + ox] == WALL)
            if walls == 0:
                bad.append((lvl, (x, y), fid))
    assert not bad, bad[:8]


def test_corridors_hold_flat_marks_only(floors):
    import hazards
    for lvl, d in floors:
        inner = set()
        for r in d.rooms:
            inner |= {(x, y) for y in range(r.y, r.y + r.height) for x in range(r.x, r.x + r.width)}
        for pos, fid in (d.__dict__.get('fixtures') or {}).items():
            if pos in inner or hazards.hazard_def(fid):
                continue
            if decor.fixture_def(fid).get('layer') == 'floor':
                assert decor._flat(fid), (lvl, pos, fid)


def test_a_cluster_starts_in_a_corner_when_there_is_one():
    from test_senses import two_rooms
    d = two_rooms()
    room = d.rooms[0]
    taken = set()
    n = decor._place_cluster(d, room, {'rubble': 1}, 3, taken, random.Random(2))
    assert n == 3
    spots = sorted(taken)
    assert any(decor._wall_sides(p, room, d) >= 2 for p in spots)
    for (x, y) in spots:                               # all of it touching a wall
        assert decor._wall_sides((x, y), room, d) >= 1
