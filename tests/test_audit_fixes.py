"""Tests covering the Phase 4 audit fixes."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ---------------------------------------------------------------------------
# Fix #1: restore_hp returns int (delta), not None
# ---------------------------------------------------------------------------

def test_restore_hp_returns_actual_delta():
    from player import Player
    p = Player()
    p.hp = 10
    p.max_hp = 30
    gained = p.restore_hp(8)
    assert gained == 8
    assert p.hp == 18
    # Capped at max_hp
    gained = p.restore_hp(99)
    assert gained == 12   # 30 - 18
    assert p.hp == 30
    # Already at max
    gained = p.restore_hp(5)
    assert gained == 0


# ---------------------------------------------------------------------------
# Fix #2: floating eye respects sleep_resist + blindness
# ---------------------------------------------------------------------------

def test_floating_eye_paralysis_check_in_combat_source():
    """The start_combat code path must guard floating-eye paralysis with
    sleep_resist + blinded checks (matches monster.attack behavior)."""
    src = Path('src/game_combat.py').read_text(encoding='utf-8')
    idx = src.find("if monster.kind == 'floating_eye'")
    assert idx >= 0
    window = src[idx:idx + 800]
    assert 'sleep_resist' in window
    assert 'blinded' in window


# ---------------------------------------------------------------------------
# Fix #3: Unicorn pet is immune to adjacent-monster swipes
# ---------------------------------------------------------------------------

def test_unicorn_skipped_in_pet_swipe_loop():
    """game_combat._do_pet_turns must skip is_unicorn pets when monsters
    swipe at adjacent companions."""
    src = Path('src/game_combat.py').read_text(encoding='utf-8')
    # The pet-swipe loop body should contain a guard for is_unicorn.
    idx = src.find('Monsters attack adjacent pets')
    assert idx >= 0
    window = src[idx:idx + 2000]
    assert 'is_unicorn' in window, \
        "unicorn-immunity guard missing from monster-swipes-pet loop"


# ---------------------------------------------------------------------------
# Fix #4: cancellation / drain_magic / dispel_magic preserve player DoTs
# ---------------------------------------------------------------------------

def test_dispel_only_clears_buffs_not_dots():
    """The three mass-strip spell effects should now iterate BUFFS only,
    not blanket-clear the monster's status_effects dict."""
    src = Path('src/game_magic.py').read_text(encoding='utf-8')
    # All three effect branches should reference BUFFS, not bare clear().
    for needle in ('cancellation', 'drain_magic', 'dispel_magic'):
        idx = src.find(f"effect == '{needle}'")
        assert idx >= 0, f"effect branch '{needle}' missing"
        window = src[idx:idx + 600]
        assert 'BUFFS' in window, \
            f"{needle} branch should iterate BUFFS instead of clear()"
        # And the bare .clear() should NOT appear in the same window.
        assert 'status_effects.clear()' not in window, \
            f"{needle} branch still uses status_effects.clear()"


# ---------------------------------------------------------------------------
# Fix #5: prayer verse table cap at chain 5 (not 8)
# ---------------------------------------------------------------------------

def test_show_prayer_verse_capped_at_5():
    """v2.13.0: the simple-prayer resolver is the only caller of
    ``_show_prayer_verse`` now; the L100 fall-through and the chain>0
    success paths both clamp with ``min(chain, 5)``. The verse table
    peaks at chain 5."""
    src = Path('src/game_divine.py').read_text(encoding='utf-8')
    assert 'min(chain, 5)' in src, (
        "simple-prayer resolver must clamp the verse key to 5"
    )
    # The old 'min(..., 8)' calls should be gone.
    assert 'min(effective, 8)' not in src
    assert 'min(chain, 8)' not in src


# ---------------------------------------------------------------------------
# Fix #6: max_chain=6 removed from fountain/throne (engine caps at 5)
# ---------------------------------------------------------------------------

def test_fountain_throne_max_chain_corrected():
    src = Path('src/game_divine.py').read_text(encoding='utf-8')
    # No remaining max_chain=6 in game_divine; should all be 5.
    assert 'max_chain=6' not in src


# ---------------------------------------------------------------------------
# Fix #7: stand_ac state cleanup on status expiry
# ---------------------------------------------------------------------------

def test_stand_ac_cleanup_on_expiry():
    """Leonidas' Spartan Stand AC bonus + counter pct must reset when the
    stand_ac status expires (handled in status_effects.tick_all)."""
    src = Path('src/status_effects.py').read_text(encoding='utf-8')
    # Find the expiry branch
    idx = src.find("elif effect == 'stand_ac':")
    assert idx >= 0
    window = src[idx:idx + 300]
    assert '_stand_ac_bonus = 0' in window
    assert '_stand_counter_pct = 0' in window


# ---------------------------------------------------------------------------
# Fix #8: load_state has compat shims for Phase 3 player fields
# ---------------------------------------------------------------------------

def test_load_state_has_phase_3_shims():
    src = Path('src/main.py').read_text(encoding='utf-8')
    for field in ['hero_passives', 'hero_specials', 'hero_special_cooldowns',
                  'qa_tools', '_stand_ac_bonus', '_stand_counter_pct',
                  '_elder_blood_escape_used']:
        assert f"hasattr(self.player, '{field}')" in src, \
            f"load_state missing compat shim for {field}"


# ---------------------------------------------------------------------------
# Fix #9: spartan_stand refresh-only-if-better semantics
# ---------------------------------------------------------------------------

def test_stand_buff_refreshes_only_if_better():
    """A weaker Stand cast must NOT lower an active stronger Stand buff."""
    src = Path('src/hero_specials.py').read_text(encoding='utf-8')
    idx = src.find('def _eff_self_buff_stand')
    assert idx >= 0
    window = src[idx:idx + 1500]
    assert 'max(' in window
    # Both _stand_ac_bonus and _stand_counter_pct should be max()'d
    assert window.count('max(') >= 3   # status duration + ac_bonus + counter_pct


# ---------------------------------------------------------------------------
# Fix #10: add_gold_to_tile import fix (F821 was real)
# ---------------------------------------------------------------------------

def test_lockpick_gold_import_correct():
    """The chest-loot path must import add_gold_to_tile, not GoldPile."""
    src = Path('src/main.py').read_text(encoding='utf-8')
    # Find the chest-loot block that uses add_gold_to_tile
    idx = src.find("add_gold_to_tile(self.ground_items, result['gold']")
    assert idx >= 0
    # Walk back to find the import
    before = src[max(0, idx - 400):idx]
    assert 'from items import add_gold_to_tile' in before, \
        "add_gold_to_tile must be imported on this code path"
