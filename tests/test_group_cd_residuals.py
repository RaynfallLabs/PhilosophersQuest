"""Tests for the C5 + D1..D4 fixes from the 2026-05-29 burndown list.

C5 — Potion mastery now multiplies BUFF/debuff duration in addition to
     heal amount (potion_potency_bonus was a heal-only bug before).
D1 — Confiteor is altar-only; a new Benedictio prayer blesses items at
     the altar.
D2 — Scroll of Identify lets you pick the target item and grants mastery
     (id_level=5 + _claim_mastery) on the chosen item.
D3 — Cursed Scroll of Identify is AMNESIA: it forgets one already-
     identified item (id_level back to 0 + drops from known_item_ids).
D4 — Scroll of Heal uses escalator_chain mode and scales heal by chain.
"""
from __future__ import annotations

import inspect
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# C5 — potion_potency_bonus must scale _buff_mult, not just _heal_mult
# ---------------------------------------------------------------------------

def test_potion_potency_bonus_scales_both_heal_and_buff_duration():
    """Source-regression: food_system._apply_potion_effect must multiply
    BOTH _heal_mult AND _buff_mult by the potency bonus."""
    import food_system
    src = inspect.getsource(food_system)
    # The fix region: after the BUC multipliers and before the duration bump.
    # Must contain _buff_mult *= ... bonus line.
    assert "_buff_mult *= 1.0 + _bonus" in src, (
        "potion_potency_bonus must scale _buff_mult so a mastered "
        "paralysis/haste/etc. potion actually lasts longer; before "
        "2026-05-29 only _heal_mult was multiplied, so the mastery's "
        "+25% claim was a no-op for buff/debuff potions"
    )
    assert "_heal_mult *= 1.0 + _bonus" in src


# ---------------------------------------------------------------------------
# D1 — Altar-only Confiteor + new Benedictio prayer
# ---------------------------------------------------------------------------

def test_prayer_registry_contains_benedictio():
    """PRAYERS list now has 9 entries including Benedictio."""
    from game_divine import PRAYERS
    ids = [p['id'] for p in PRAYERS]
    assert 'benedictio' in ids, "Benedictio prayer must be registered"
    assert 'confiteor' in ids
    assert len(PRAYERS) >= 9


def test_confiteor_gate_requires_altar():
    """Confiteor's gate now checks that the player stands on an ALTAR tile."""
    from game_divine import PRAYERS
    confiteor = next(p for p in PRAYERS if p['id'] == 'confiteor')
    src = inspect.getsource(confiteor['gate'])
    # The gate lambda must reference altar-checking AND cursed-worn checks.
    assert '_on_altar' in src or 'ALTAR' in src, (
        "Confiteor gate must require an altar tile per D1 2026-05-29"
    )
    assert '_any_cursed_worn' in src


def test_benedictio_handler_exists():
    """DivineMixin must expose a _prayer_benedictio handler that returns
    (messages, fired_full)."""
    from game_divine import DivineMixin
    assert hasattr(DivineMixin, '_prayer_benedictio')
    sig = inspect.signature(DivineMixin._prayer_benedictio)
    # (self, effective, raw_chain) -> tuple
    assert list(sig.parameters)[1:] == ['effective', 'raw_chain']


# ---------------------------------------------------------------------------
# D2 — Scroll of Identify pick target + grant mastery
# ---------------------------------------------------------------------------

def test_scroll_identify_picker_method_exists():
    """game_magic.MagicMixin must expose the new picker hooks."""
    from game_magic import MagicMixin
    assert hasattr(MagicMixin, '_open_scroll_identify_picker')
    assert hasattr(MagicMixin, '_scroll_grant_mastery')
    assert hasattr(MagicMixin, '_scroll_identify_bulk_to_lore')


def test_scroll_identify_grants_mastery_directly():
    """The mastery grant must set id_level=5 and call _claim_mastery."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._scroll_grant_mastery)
    assert 'id_level = 5' in src, (
        "Scroll of Identify must shortcut to id_level 5 on the chosen item"
    )
    assert '_claim_mastery' in src, (
        "Scroll of Identify must call _claim_mastery to actually unlock the bonus"
    )


def test_uncursed_identify_opens_picker():
    """The uncursed Scroll of Identify branch must open the picker."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._apply_scroll_effect)
    assert "_open_scroll_identify_picker(bless=False)" in src or \
        "_open_scroll_identify_picker(bless = False)" in src, (
        "Uncursed Scroll of Identify must open the target picker (D2)"
    )


# ---------------------------------------------------------------------------
# D3 — Cursed Scroll of Identify amnesia
# ---------------------------------------------------------------------------

def test_cursed_identify_triggers_amnesia():
    """Cursed Scroll of Identify branch must call _scroll_identify_amnesia."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._apply_scroll_effect)
    assert '_scroll_identify_amnesia' in src, (
        "Cursed Scroll of Identify must trigger amnesia per D3 2026-05-29"
    )


def test_amnesia_helper_resets_id_level():
    """_scroll_identify_amnesia must drop id_level and discard from
    known_item_ids."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._scroll_identify_amnesia)
    assert 'id_level = 0' in src
    assert 'known_item_ids.discard' in src
    # Never brick the Shard — that would lock the player out of ID.
    assert 'philosophers_shard' in src


# ---------------------------------------------------------------------------
# D4 — Scroll of Heal escalator_chain mode
# ---------------------------------------------------------------------------

def test_scroll_of_heal_json_uses_escalator_chain():
    """scroll.json must declare scroll_of_heal as escalator_chain mode."""
    p = ROOT / "data" / "items" / "scroll.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    heal = d['scroll_of_heal']
    assert heal.get('quiz_mode') == 'escalator_chain'
    assert int(heal.get('max_chain', 0)) >= 5


def test_scroll_class_reads_quiz_mode():
    """items.Scroll must expose quiz_mode + max_chain fields."""
    from items import Scroll
    s = Scroll({
        'id': 'test_chain_scroll',
        'name': 'test scroll', 'symbol': '?', 'color': [255, 255, 255],
        'effect': 'heal', 'quiz_mode': 'escalator_chain', 'max_chain': 5,
    })
    assert s.quiz_mode == 'escalator_chain'
    assert s.max_chain == 5

    # Backward compat: default mode is threshold.
    s2 = Scroll({
        'id': 'test_plain_scroll',
        'name': 'plain scroll', 'symbol': '?', 'color': [255, 255, 255],
        'effect': 'mapping',
    })
    assert s2.quiz_mode == 'threshold'


def test_apply_scroll_effect_scales_heal_by_chain():
    """The 'heal' effect in _apply_scroll_effect must scale by chain when
    quiz_mode == 'escalator_chain'."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._apply_scroll_effect)
    assert '_SCROLL_HEAL_CHAIN_MULTS' in src, (
        "Scroll of Heal must scale heal amount by chain tier per D4"
    )
    # Make sure the chain parameter is in the signature.
    sig = inspect.signature(MagicMixin._apply_scroll_effect)
    assert 'chain' in sig.parameters


def test_scroll_heal_chain_mults_table_is_monotonic():
    """The chain multiplier table must be monotonically non-decreasing
    (chain 5 must heal MORE than chain 1)."""
    from game_magic import MagicMixin
    mults = MagicMixin._SCROLL_HEAL_CHAIN_MULTS
    assert len(mults) >= 5
    for i in range(len(mults) - 1):
        assert mults[i] <= mults[i + 1], (
            f"_SCROLL_HEAL_CHAIN_MULTS must rise monotonically; "
            f"index {i} ({mults[i]}) > index {i+1} ({mults[i+1]})"
        )
    # Chain 5 must be meaningfully bigger than chain 1.
    assert mults[-1] >= 2 * mults[0]


def test_read_scroll_branches_on_quiz_mode():
    """_read_scroll must dispatch to escalator_chain when scroll.quiz_mode
    requests it."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._read_scroll)
    assert "escalator_chain" in src
    assert "quiz_mode" in src
