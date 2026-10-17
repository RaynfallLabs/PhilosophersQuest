"""Bug bash 2026-10-16 (F5), CQ-17: proven-dead helpers removed."""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── CQ-17 ────────────────────────────────────────────────────────────────────

def test_proven_dead_helpers_stay_deleted():
    """Removed 2026-10-16 after a whole-repo search found no caller (src,
    tests, tools, data, the spec). Two were misleading as well:
    manhattan_distance claimed to be used 'wherever' that sum was written,
    and can_footprint_fit took an ignore_monster argument it never read."""
    import importlib
    gone = {
        'armor_procs': ['find_armor_with_proc'],
        'fantasy_ui': ['subject_icon'],
        'geom': ['manhattan_distance', 'can_footprint_fit'],
        'paths': ['fmt_id'],
        'sound_system': ['is_on'],
    }
    for mod, names in gone.items():
        m = importlib.import_module(mod)
        for n in names:
            assert not hasattr(m, n), f'{mod}.{n}'
    from level_manager import LevelManager
    from pet_system import SketchedPet
    from quiz_engine import QuizEngine
    assert not hasattr(LevelManager, 'has_visited')
    assert not hasattr(SketchedPet, '_calc_dice_avg')
    assert not hasattr(QuizEngine, 'reload_context_blurbs')
