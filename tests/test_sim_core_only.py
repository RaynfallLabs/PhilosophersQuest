"""The difficulty simulator plays the base game and its core systems only
(Brandon, 2026-11-16: "I do not need every little easter egg modeled in the
simulator; caviar and tater tots, dad, etc. does NOT need to be in there;
those are for kids and friends").

An easter egg reached the simulator once through the shared kitchen: it
cooked Caviar and Tater Tots, whose song runs on real seconds the simulator
never passes, so its half damage lasted the whole run and the committed kid
won 51% instead of 1%. The song dishes are never cooked there.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
os.environ.setdefault('PQ_NO_BONES', '1')

import items  # noqa: E402
import kitchen  # noqa: E402


def test_the_simulator_never_cooks_a_song_dish():
    import difficulty_sim as ds
    run = ds.Run(ds.FloorCache(1), 'mastery', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    run.food = [items.make_item_by_id('food', 'caviar'), items.make_item_by_id('food', 'tater_tots')]
    run.pantry = []
    # The game itself would cook it: the dish is ready from these two.
    assert any(kitchen.song_of(r) for r in kitchen.ready_dishes(run._kitchen_inv()))
    assert not any(kitchen.song_of(r) for r in run._ready())
    assert not any(kitchen.song_of(r) for r in run._ready('special'))
