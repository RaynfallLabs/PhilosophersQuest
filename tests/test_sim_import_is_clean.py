"""Importing the simulator patches nothing in the game (2026-11-16).

tools/balance/difficulty_sim.py used to swap items.load_items for a cache of
shared item objects, and stub out the bones, the moment it was imported. A
test that imported it for one check handed every later test in its process
those shared objects. The capture harness then stacked onto them, so in the
serial run before 3.5.3 the iron arrows doubled scene after scene, and the UI
gates read "Carrying 555328316629214848 / 100" while the altar could not give
a hero his change. The patches now go on only when the simulator runs
(install_caches: run_cell, the command line, carry_sim, loot_census)."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_importing_the_simulator_patches_nothing():
    code = ("import sys; sys.path[:0] = ['src', 'tools/balance']; import items, level_manager; "
            "real = items.load_items; bones = level_manager.LevelManager._maybe_spawn_bones; "
            "import difficulty_sim as ds; "
            "assert items.load_items is real and not ds._CACHES_ON; "
            "assert level_manager.LevelManager._maybe_spawn_bones is bones; "
            "ds.install_caches(); assert items.load_items is not real; print('ok')")
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    out = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0 and 'ok' in out.stdout, out.stderr[-2000:]


def test_two_loads_never_share_an_item():
    """The game's own loader hands out new objects every call, so a stack
    added to one pack can never grow another."""
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import items
    a, b = items.load_items('ammo'), items.load_items('ammo')
    assert a[0] is not b[0]
    a[0].count += 5
    assert b[0].count != a[0].count
