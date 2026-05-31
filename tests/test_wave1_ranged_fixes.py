"""Wave 1 ranged-weapon fixes (2026-05-30):

A — composite_bow's str_bonus_range_7 mechanic is wired in combat.py
B — hector_javelin is now one-handed (so the existing throw system accepts it)
C — Ranged targeting decoupled from FOV: shoot into darkness, projectile traces
    and hits first obstacle (monster OR wall) along Bresenham path
D — PER -> small ranged damage scaling (+max(0, (PER-10)//3) when ammo present)
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# A — composite_bow STR mechanic
# ---------------------------------------------------------------------------

def test_str_bonus_range_7_wired_in_player_attack():
    """combat.player_attack must include the str_bonus_range_7 handler.
    Previously the composite_bow template declared this mechanic but no
    code referenced it — composite bows behaved identically to longbows."""
    import combat
    src = inspect.getsource(combat.player_attack)
    assert 'str_bonus_range_7' in src, (
        "composite_bow's str_bonus_range_7 mechanic must be wired in "
        "combat.player_attack (Wave 1 A, 2026-05-30)"
    )
    # The handler must reference player.STR for the scaling and ammo to
    # gate it to ranged shots only.
    assert 'player.STR' in src
    # The math: every STR point above 10 adds 5% multiplier
    assert '0.05' in src


# ---------------------------------------------------------------------------
# B — hector_javelin one-handed (so the throw system accepts it)
# ---------------------------------------------------------------------------

def test_hector_javelin_is_one_handed():
    """Hector's Javelin should be one-handed — the existing throw system
    rejects two-handed weapons. Per weapons.md design (Iliad spear-throwing
    duel) and historical accuracy (Roman/Greek javelins were 1H)."""
    p = ROOT / "data" / "items" / "weapon.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    hj = d['hector_javelin']
    assert hj['two_handed'] is False, "hector_javelin must be 1H to be throwable"
    assert hj['twoHanded'] is False, "twoHanded must mirror two_handed=false"
    assert hj['weapon_class'] == 'spear', "spear class is in _THROWABLE_CLASSES"
    assert hj['weight'] <= 5.0, "weight must be <= 5.0 for _is_throwable_weapon"


def test_hector_javelin_passes_is_throwable_check():
    """Wire-up check: the existing _is_throwable_weapon staticmethod must
    return True for hector_javelin now that it's 1H."""
    from items import Weapon
    p = ROOT / "data" / "items" / "weapon.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    defn = {'id': 'hector_javelin', **d['hector_javelin']}
    w = Weapon(defn)
    from game_combat import CombatMixin
    assert CombatMixin._is_throwable_weapon(w), (
        "hector_javelin must pass _is_throwable_weapon now that it's 1H"
    )


# ---------------------------------------------------------------------------
# C — FOV decoupled from ranged targeting
# ---------------------------------------------------------------------------

def test_can_ranged_attack_does_not_require_line_of_sight():
    """combat.can_ranged_attack no longer calls _line_of_sight — the
    projectile path is resolved at fire time instead, so the player can
    target unseen monsters in corridors."""
    import combat
    src = inspect.getsource(combat.can_ranged_attack)
    assert '_line_of_sight' not in src, (
        "can_ranged_attack must NOT require line of sight after Wave 1 "
        "(2026-05-30) — path resolution moved to _confirm_ranged_target"
    )


def test_open_targeting_drops_visibility_filter():
    """The ranged-targeting menu must include monsters outside FOV (within
    reach). _open_targeting used to filter by self.visible; now it only
    filters by can_ranged_attack (which is reach + ammo)."""
    from game_combat import CombatMixin
    src = inspect.getsource(CombatMixin._open_targeting)
    # The OLD filter was `(m.x, m.y) in self.visible` joined with the
    # can_ranged_attack call. The new code only filters by can_ranged_attack.
    # Find the candidate-build expression and confirm visibility is gone.
    # We tolerate it being mentioned in a COMMENT explaining the change.
    code_lines = [
        line for line in src.splitlines()
        if 'self.visible' in line and not line.lstrip().startswith('#')
    ]
    assert not code_lines, (
        f"_open_targeting must drop the visibility filter (Wave 1 C). "
        f"Code lines still referencing self.visible: {code_lines}"
    )


def test_confirm_ranged_target_traces_projectile():
    """_confirm_ranged_target must trace projectile path and dispatch to
    either _fire_ranged (monster hit) or _consume_ranged_ammo_for_miss
    (wall hit or empty path)."""
    from game_combat import CombatMixin
    src = inspect.getsource(CombatMixin._confirm_ranged_target)
    assert '_trace_projectile_obstacle' in src, (
        "_confirm_ranged_target must call _trace_projectile_obstacle to "
        "resolve where the shot actually lands"
    )
    assert '_consume_ranged_ammo_for_miss' in src, (
        "non-monster outcomes must consume ammo via _consume_ranged_ammo_for_miss"
    )


def test_trace_projectile_obstacle_exists():
    """The helper that resolves the projectile's first obstacle (monster
    or wall) must exist on CombatMixin."""
    from game_combat import CombatMixin
    assert hasattr(CombatMixin, '_trace_projectile_obstacle')
    sig = inspect.signature(CombatMixin._trace_projectile_obstacle)
    # (self, x0, y0, x1, y1)
    assert list(sig.parameters)[1:] == ['x0', 'y0', 'x1', 'y1']


def test_consume_ranged_ammo_for_miss_exists():
    """Wall-hit and empty-path outcomes go through this helper, which
    decrements ammo and prints an appropriate message."""
    from game_combat import CombatMixin
    assert hasattr(CombatMixin, '_consume_ranged_ammo_for_miss')


# ---------------------------------------------------------------------------
# D — PER -> ranged damage
# ---------------------------------------------------------------------------

def test_per_scales_ranged_damage():
    """combat.player_attack must add a small PER-based bonus to base damage
    when ammo is present (= ranged shot). Per user 2026-05-30, PER had
    ZERO damage hook before; now +1 per 3 PER points above 10."""
    import combat
    src = inspect.getsource(combat.player_attack)
    # The signature line should mention PER somewhere in the ammo branch.
    # Look for `player.PER` and `ammo` co-located within the function.
    assert 'player.PER' in src, "player.PER must be referenced for the scaling"
    assert '(player.PER - 10) // 3' in src or '(player.PER-10) // 3' in src \
        or '(player.PER - 10)//3' in src, \
        "expected the +max(0, (PER-10)//3) formula"
