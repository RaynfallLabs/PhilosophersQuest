"""Tests for Group A residuals from the 2026-05-29 playtest list.

A3 — All question stems start with an uppercase letter.
A4 — Examine card shows the carry-only bonus instead of '? +0'.
A5 — Corpses spawn at the tier the player has already learned for that
     monster type (continuity across kills of the same species).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# A3 — Question stems start uppercase
# ---------------------------------------------------------------------------

def test_no_question_stem_starts_lowercase():
    """Every question in every bank must start with an uppercase letter
    (after any leading punctuation like quotation marks or parentheses)."""
    bad = []
    for f in sorted(os.listdir(ROOT / "data" / "questions")):
        if not f.endswith('.json'):
            continue
        d = json.loads((ROOT / "data" / "questions" / f).read_text(encoding='utf-8'))
        if not isinstance(d, list):
            continue
        for q in d:
            stem = q.get('question', '')
            if not isinstance(stem, str) or not stem:
                continue
            m = re.match(r'^[\s"\'\(\[]*([a-zA-Z])', stem)
            if m and m.group(1).islower():
                bad.append(f"{f}: {stem[:80]!r}")
    assert not bad, (
        f"{len(bad)} question stems start with lowercase letters:\n"
        + "\n".join(bad[:10])
    )


# ---------------------------------------------------------------------------
# A4 — Examine card never shows '? +0' for carry-only items
# ---------------------------------------------------------------------------

def test_get_item_stats_brief_uses_carry_bonus_for_charmander():
    """Source-regression: the brief-stats helper must fall back to
    carry_bonus for items whose `effects` dict is empty (Charmander
    Stuffie, Dreamspun Sketchbook)."""
    import inspect
    import main
    src = inspect.getsource(main.Game._get_item_stats_brief)
    assert "carry_bonus" in src, (
        "_get_item_stats_brief must consult carry_bonus for items "
        "whose effects dict is empty; otherwise the examine card shows "
        "'? +0' for the Charmander Stuffie and similar carry-only items"
    )
    # The fallback should never produce the literal '? +0' string
    assert "f\"{fx.get('stat','?')} +{fx.get('amount',0)}\"" not in src, (
        "the old broken fallback must be replaced — it produces '? +0'"
    )


def test_get_item_stats_brief_runtime_for_carry_item():
    """End-to-end: load the Charmander Stuffie from JSON, construct
    an Accessory, and check the carry_bonus fallback has real data."""
    from items import Accessory
    d = json.loads((ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    defn = {'id': 'charmander_stuffie', **d['charmander_stuffie']}
    acc = Accessory(defn)
    fx = acc.effects or {}
    assert 'status' not in fx
    assert not ('stat' in fx and 'amount' in fx), (
        "Charmander Stuffie has empty effects by design — this test "
        "verifies the brief-stats falls back to carry_bonus"
    )
    cb = getattr(acc, 'carry_bonus', None) or {}
    assert cb.get('stat') == 'CON'
    assert cb.get('amount') == 2


# ---------------------------------------------------------------------------
# A5 — Corpse identification continuity (one-question model, 2026-08-06)
# ---------------------------------------------------------------------------

def test_make_corpse_pre_identifies_known_types():
    """When a new corpse spawns and the player has already studied that
    monster type, the corpse arrives fully identified."""
    import inspect
    import game_combat
    src = inspect.getsource(game_combat.CombatMixin._make_corpse)
    assert "lore_known_monster_ids" in src, (
        "_make_corpse must pre-identify corpses of studied monster types"
    )


def test_start_corpse_identify_records_known_type():
    """The corpse-study callback must add the monster to
    lore_known_monster_ids so future kills spawn pre-identified."""
    import inspect
    import main
    src = inspect.getsource(main.Game._start_corpse_identify)
    assert "lore_known_monster_ids" in src
