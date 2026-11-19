"""The same seed builds the same floor in every process.

The floor's builders each roll on a generator of their own, and they used to
make it with a bare ``random.Random()``, which Python seeds from the
operating system. So ``random.seed(s)`` never reached a layout: every
process walked a new floor, a floor from a bug report could not be
replayed, and a test that needed a certain layout passed or failed by luck
(the 3.5.4 release run put Old Nickel in a corner of his room). The Stray
Kids' idol was set down with the shouts' stream, seeded the same way. They
now draw their seed from the shared stream (src/random_streams.py).

A child process builds each floor under several PYTHONHASHSEED values (the
order of a set of strings changes with it), and every part of the floor
must match: the tiles, the rooms, the creatures and their health, the loot,
the traps, the fixtures, where the hero stands, and the shared stream's
state once it is all built. Building it twice in one process also catches
an order that follows memory addresses (a set of objects).
"""
import json
import os
import random
import subprocess
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

SEEDS = (5, 11)
FLOORS = (1, 2, 7, 21)
HASH_SEEDS = ('0', '3', '13')


def _fingerprint(g) -> dict:
    """Each part of the floor the hero stands on, hashed."""
    import hashlib

    def h(obj):
        return hashlib.sha1(repr(obj).encode('utf-8')).hexdigest()[:12]

    d = g.dungeon
    return {
        'tiles': h(d.tiles),
        'rooms': h([(r.x, r.y, r.width, r.height) for r in d.rooms]),
        'monsters': h([(str(getattr(m, 'id', m.name)), m.x, m.y, m.hp) for m in g.monsters]),
        'items': h([(str(getattr(i, 'id', '')), getattr(i, 'x', None), getattr(i, 'y', None))
                    for i in g.ground_items]),
        'traps': h(sorted((k, str(v)) for k, v in d.traps.items())),
        'fixtures': h(sorted((k, str(v)) for k, v in (getattr(d, 'fixtures', None) or {}).items())),
        'hero': h((g.player.x, g.player.y)),
        'shared_stream': h(random.getstate()),
    }


def _build(screen, seed: int, floor: int):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(screen, player_name='__test_seeded_floor__')
    g.state = STATE_PLAYER
    if floor != g.dungeon_level:
        g._change_level(floor, enter_from_top=True)
    return g


# The child: its own save folder (main.py opens faulthandler.log there on
# import) and log folder, no bones, then every (seed, floor) as one JSON dict.
_CHILD = r'''
import json, os, sys
root, save_dir, seeds, floors = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, os.path.join(root, 'src'))
sys.path.insert(0, os.path.join(root, 'tests'))
import paths
paths._DEV_SAVE_DIR_OVERRIDE = save_dir
import game_log
game_log._LOG_DIR = save_dir
import pygame
pygame.init()
screen = pygame.display.set_mode((1, 1))
import test_seeded_floor_is_stable as t
out = {}
for s in (int(x) for x in seeds.split(',')):
    for f in (int(x) for x in floors.split(',')):
        out[f'{s}/{f}'] = t._fingerprint(t._build(screen, s, f))
print('FINGERPRINTS ' + json.dumps(out, sort_keys=True))
'''


def _run_children(tmp_path) -> dict:
    procs = {}
    for hs in HASH_SEEDS:
        env = dict(os.environ)
        env.update(PYTHONHASHSEED=hs, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                   PQ_NO_BONES='1')
        save_dir = tmp_path / f'hash_seed_{hs}'
        save_dir.mkdir()
        procs[hs] = subprocess.Popen(
            [sys.executable, '-c', _CHILD, ROOT, str(save_dir),
             ','.join(map(str, SEEDS)), ','.join(map(str, FLOORS))],
            cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace')
    results = {}
    for hs, p in procs.items():
        out, err = p.communicate(timeout=600)
        line = next((ln for ln in out.splitlines() if ln.startswith('FINGERPRINTS ')), None)
        assert p.returncode == 0 and line, f'PYTHONHASHSEED={hs} failed:\n{err[-3000:]}'
        results[hs] = json.loads(line[len('FINGERPRINTS '):])
    return results


def test_a_seeded_floor_is_the_same_under_every_hash_seed(tmp_path):
    results = _run_children(tmp_path)
    first, base = HASH_SEEDS[0], results[HASH_SEEDS[0]]
    assert set(base) == {f'{s}/{f}' for s in SEEDS for f in FLOORS}
    differ = [f'seed/floor {key}: {part} differs (PYTHONHASHSEED={first} vs {hs})'
              for hs in HASH_SEEDS[1:] for key in sorted(base)
              for part in base[key] if results[hs][key][part] != base[key][part]]
    assert not differ, '\n'.join(differ)
    # (The seeds really make different floors.)
    assert len({base[f'{s}/2']['tiles'] for s in SEEDS}) == len(SEEDS)


def test_a_seeded_floor_is_the_same_twice_in_one_process():
    """A set of objects is ordered by memory address, which changes from
    one build to the next even in one process."""
    pygame.init()
    screen = pygame.display.set_mode((1, 1))
    for floor in (2, 21):
        a = _fingerprint(_build(screen, SEEDS[0], floor))
        b = _fingerprint(_build(screen, SEEDS[0], floor))
        assert a == b, {k: (a[k], b[k]) for k in a if a[k] != b[k]}


def test_the_floor_builders_take_their_streams_from_the_shared_one():
    """Two builds of a raw floor after the same random.seed are the same:
    no builder makes a generator seeded by the operating system."""
    import items as items_mod
    from dungeon import generate_dungeon, populate_floor, spawn_items

    def raw(level):
        items_mod.bind_unique_registry(set())        # (a new run: no unique found yet)
        random.seed(99)
        d = generate_dungeon(80, 50, level)
        mons = populate_floor(d.rooms, level, d, occupancy=0.7)
        loot = spawn_items(d.rooms, level, d)
        return (d.tiles, [(str(getattr(m, 'id', m.name)), m.x, m.y, m.hp) for m in mons],
                [(getattr(i, 'id', ''), getattr(i, 'x', None), getattr(i, 'y', None)) for i in loot])

    for level in (3, 10, 25):
        assert raw(level) == raw(level)


def test_own_stream_moves_the_shared_stream_on():
    """Each builder gets a stream of its own: two in a row differ."""
    from random_streams import own_stream
    random.seed(1)
    a, b = own_stream(), own_stream()
    assert a.random() != b.random()
    random.seed(1)
    assert own_stream().random() == random.Random(_first_draw(1)).random()


def _first_draw(seed):
    r = random.Random(seed)
    return r.getrandbits(64)
