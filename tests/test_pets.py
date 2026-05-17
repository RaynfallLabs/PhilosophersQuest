"""Tests for the 2026-05-17 pet system revamp (Phase 1):

- Naming popup: nicknames display 'Nickname the Species'
- Evolution thresholds: stage 1 at L25, stage 2 at L55
- XP curve: level * 20
- Passive XP gain: 1 XP every 3 turns
- Kill XP: scaled by monster max_hp
- Late-pickup catch-up: pets hatched on deeper floors start with bonus XP
- Unicorn trap detection sets the right field (revealed, not detected)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ---------------------------------------------------------------------------
# Evolution thresholds
# ---------------------------------------------------------------------------

def test_stage_thresholds():
    import pet_system
    assert pet_system._EVOLVE_1 == 25
    assert pet_system._EVOLVE_2 == 55


def test_pet_stages_by_level():
    from pet_system import Pet
    p = Pet('electric')
    assert p.stage == 0
    p.level = 24
    assert p.stage == 0
    p.level = 25
    assert p.stage == 1
    p.level = 54
    assert p.stage == 1
    p.level = 55
    assert p.stage == 2
    p.level = 100
    assert p.stage == 2


# ---------------------------------------------------------------------------
# Nickname display
# ---------------------------------------------------------------------------

def test_pet_name_without_nickname():
    from pet_system import Pet
    p = Pet('electric')
    assert p.species_name == 'Zappik'
    assert p.name == 'Zappik'   # no nickname → just species


def test_pet_name_with_nickname():
    from pet_system import Pet
    p = Pet('electric')
    p.nickname = 'Pikachu'
    assert p.name == 'Pikachu the Zappik'
    p.level = 25  # evolution to stage 1
    assert p.species_name == 'Voltpaw'
    assert p.name == 'Pikachu the Voltpaw'
    p.level = 55  # evolution to stage 2
    assert p.species_name == 'Thundertail'
    assert p.name == 'Pikachu the Thundertail'


def test_default_nickname_is_empty():
    from pet_system import Pet
    p = Pet('water')
    assert p.nickname == ''


# ---------------------------------------------------------------------------
# XP curve and passive gain
# ---------------------------------------------------------------------------

def test_xp_to_next_formula():
    from pet_system import Pet
    p = Pet('plant')
    p.level = 1
    assert p._xp_to_next() == 20
    p.level = 10
    assert p._xp_to_next() == 200
    p.level = 24
    assert p._xp_to_next() == 480


def test_passive_xp_every_third_turn():
    from pet_system import Pet
    p = Pet('fire')
    start_xp = p.xp
    p.gain_xp_passive()
    p.gain_xp_passive()
    assert p.xp == start_xp, "first two passive ticks should grant no XP"
    p.gain_xp_passive()
    assert p.xp == start_xp + 1, "third passive tick should grant 1 XP"
    p.gain_xp_passive()
    p.gain_xp_passive()
    assert p.xp == start_xp + 1, "no further XP until the next 3-tick interval"
    p.gain_xp_passive()
    assert p.xp == start_xp + 2


def test_passive_xp_returns_no_messages_when_dead():
    from pet_system import Pet
    p = Pet('electric')
    p.alive = False
    for _ in range(10):
        msgs = p.gain_xp_passive()
        assert msgs == []


# ---------------------------------------------------------------------------
# Kill XP scaling
# ---------------------------------------------------------------------------

def test_kill_xp_scales_with_monster_max_hp():
    from pet_system import Pet
    p = Pet('water')
    # Use a higher starting level so xp_to_next is large enough to avoid
    # mid-test level-ups consuming the awarded XP.
    p.level = 10        # xp_to_next = 200
    start_xp = p.xp
    p.gain_xp_from_kill(10)   # F1 mob ≈ 4 XP (3 + 10//10)
    assert p.xp == start_xp + 4
    p.xp = start_xp
    p.gain_xp_from_kill(200)  # F90 mob ≈ 23 XP
    assert p.xp == start_xp + 23


def test_kill_xp_increments_counter():
    from pet_system import Pet
    p = Pet('electric')
    assert p.kills_count == 0
    p.gain_xp_from_kill(30)
    p.gain_xp_from_kill(30)
    p.gain_xp_from_kill(30)
    assert p.kills_count == 3


def test_kill_xp_levels_pet_with_repeated_kills():
    """Sanity: enough mid-floor kills push the pet across multiple levels.

    Curve: L1->2 = 20 XP, L2->3 = 40 XP, ..., total to L6 = 300 XP. Each
    60-HP kill grants 9 XP, so 40 kills = 360 XP → expect L6+.
    """
    from pet_system import Pet
    p = Pet('plant')
    for _ in range(40):
        p.gain_xp_from_kill(60)
    assert p.level >= 6, \
        f"40 mid-tier kills should reach at least L6; got L{p.level}"


# ---------------------------------------------------------------------------
# Late-pickup catch-up
# ---------------------------------------------------------------------------

def test_late_pickup_bonus_zero_at_floor_zero():
    from pet_system import Pet
    p = Pet('fire')
    p.apply_late_pickup_bonus(0)
    assert p.xp == 0
    assert p.level == 1


def test_late_pickup_bonus_scales_with_floor():
    from pet_system import Pet
    p = Pet('fire')
    p.apply_late_pickup_bonus(30)   # 30 * 50 = 1500 XP
    # 1500 XP at level*20 curve: L1→2 (20), L2→3 (40), L3→4 (60), ...
    # Sum 20+40+...+200 = 20*sum(1..10) = 1100. So L11 with 400 leftover.
    assert p.level >= 10, f"pet at floor 30 should reach at least L10; got L{p.level}"


def test_late_pickup_bonus_capped_below_stage_1():
    """A pet hatched in the deepest possible spot still has to EARN evolution."""
    from pet_system import Pet
    p = Pet('water')
    p.apply_late_pickup_bonus(99)   # capped at floor * 50 = 4950, but min(4950, 4000) = 4000
    assert p.stage == 0, "catch-up alone must not push past stage 1"
    assert p.level < 25, f"catch-up must keep pet below L25 (stage 1); got L{p.level}"


# ---------------------------------------------------------------------------
# Unicorn trap-detection bug fix
# ---------------------------------------------------------------------------

def test_unicorn_sets_revealed_not_detected():
    from pet_system import UnicornPet

    class _StubPlayer:
        x = 5
        y = 5
        hp = 50
        max_hp = 50
        status_effects: dict = {}
    class _StubDungeon:
        def __init__(self):
            self.traps = {(6, 6): {'type': 'pit', 'damage': '2d6', 'message': '!',
                                    'damage_type': 'physical', 'revealed': False}}
        def is_walkable(self, x, y):
            return True

    u = UnicornPet(5, 5)
    player = _StubPlayer()
    dungeon = _StubDungeon()
    monsters = []
    pets = [u]
    # Run several ticks so the heal/cleanse timers don't dominate output
    for _ in range(3):
        u.take_turn(player, dungeon, monsters, pets, ground_items=[])
    trap = dungeon.traps[(6, 6)]
    assert trap.get('revealed') is True, "unicorn must set revealed=True so engine sees the trap"
    assert 'detected' not in trap or trap.get('detected') is None, \
        "the buggy `detected` key should no longer be written"
