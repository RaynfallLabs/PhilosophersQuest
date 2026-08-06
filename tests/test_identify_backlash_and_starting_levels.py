"""Backlash + starting-item identification under the one-question model.

1. Identify backlash: a WRONG answer on the identify question (item OR
   corpse) applies Stunned for 10 turns — the cost that stops blind
   guess-spam (original penalty added per user 2026-05-29; converted
   from Confused to Stunned with the 2026-08-06 redesign).

2. Starting-item id_level: build-kit items arrive fully identified
   (id_level=5 + buc_known + type known) — the kid owns them. Every
   unique in JSON still starts unidentified for natural finds.
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# JSON data layer: every unique starts unidentified
# ---------------------------------------------------------------------------

def test_every_unique_starts_unidentified_in_json():
    """Regression for the original bug: many unique JSONs had
    `identified: True` (explicit or default) which made id_level=5 at
    construction. Every unique must explicitly start unidentified."""
    cats = ['accessory', 'armor', 'artifact', 'scroll', 'shield',
            'spellbook', 'weapon', 'wand']
    bad = []
    for cat in cats:
        p = ROOT / "data" / "items" / f"{cat}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding='utf-8'))
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            if not isinstance(v, dict):
                continue
            if not v.get('is_unique', False):
                continue
            ident = v.get('identified', True)
            idlvl = v.get('id_level', None)
            if ident is not False or (idlvl is not None and idlvl > 0):
                bad.append(f"{cat}:{k} (identified={ident}, id_level={idlvl})")
    assert not bad, (
        f"Uniques must start with identified=False AND id_level=0. "
        f"Found {len(bad)} regressions:\n"
        + "\n".join(bad[:10])
    )


def test_charmander_stuffie_unidentified_in_json():
    """The specific item the user flagged — Cain/Corwin build's
    `_start_extra_acc`. Must start at id_level=0 in JSON."""
    d = json.loads((ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    cs = d['charmander_stuffie']
    assert cs.get('identified') is False
    assert cs.get('id_level', 0) == 0


# ---------------------------------------------------------------------------
# Build-kit: the helper is wired through and uses the right rule
# ---------------------------------------------------------------------------

def test_build_kit_uses_mark_starting_item_known_helper():
    """The build-kit sites that previously did `.identified = True`
    must route through `_mark_starting_item_known(...)`."""
    src = inspect.getsource(__import__('main').Game._give_starting_kit)
    n_calls = src.count('_mark_starting_item_known(')
    assert n_calls >= 15, (
        f"expected >= 15 calls to _mark_starting_item_known in "
        f"_give_starting_kit; got {n_calls}"
    )
    # And no direct `.identified = True` left in the build-kit body
    assert '.identified = True' not in src, (
        "_give_starting_kit must not call `.identified = True` directly"
    )


def test_mark_helper_fully_identifies_starting_items():
    """One-question model: build-kit items arrive at id_level 5 with
    buc_known and the type registered as known."""
    src = inspect.getsource(__import__('main').Game._give_starting_kit)
    helper_idx = src.find('def _mark_starting_item_known')
    assert helper_idx >= 0
    helper_block = src[helper_idx: helper_idx + 900]
    assert 'id_level = 5' in helper_block
    assert 'buc_known = True' in helper_block
    assert 'known_item_ids.add' in helper_block


# ---------------------------------------------------------------------------
# Identify backlash: a wrong answer applies Stunned for 10 turns
# ---------------------------------------------------------------------------

def test_item_identify_wrong_answer_applies_stunned():
    """Source check: the failure branch of the item identify question
    must apply 'stunned' for 10 turns."""
    import game_magic
    src = inspect.getsource(game_magic.MagicMixin._identify_item)
    assert "add_effect('stunned', 10)" in src, (
        "the wrong-answer branch must apply the 'stunned' status — the "
        "cost that stops blind guess-spam"
    )


def test_corpse_identify_wrong_answer_applies_stunned():
    """Same backlash on a failed corpse study."""
    import main
    src = inspect.getsource(main.Game._start_corpse_identify)
    assert "add_effect('stunned', 10)" in src


def test_backlash_message_mentions_shard_backlash():
    """The flavor message connects the punishment to the Philosopher's
    Shard (the player's identify tool) and to the Stunned status, so the
    player learns to associate misuse with cost."""
    import game_magic
    src = inspect.getsource(game_magic.MagicMixin._identify_item)
    assert "Backlash" in src or "backlash" in src
    assert "Stunned" in src


def test_identify_quiz_is_one_question():
    """The identify quiz must be threshold mode with exactly one
    question (threshold=1, total_qs=1) at the item's id_tier."""
    import game_magic
    import main
    for src in (inspect.getsource(game_magic.MagicMixin._identify_item),
                inspect.getsource(main.Game._start_corpse_identify)):
        assert "mode='threshold'" in src
        assert 'threshold=1' in src
        assert 'total_qs=1' in src
        assert 'item_id_tier' in src


# ---------------------------------------------------------------------------
# End-to-end integration: one question, full identify OR stun
# ---------------------------------------------------------------------------

def _headless_game(name):
    import os
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    import pygame as _pg
    _pg.init()
    _pg.display.set_mode((1, 1))
    from main import Game
    return Game(_pg.display.set_mode((1, 1)), player_name=name)


def _fresh_potion():
    from items import load_items
    import copy
    pot = copy.copy(load_items('potion')[0])
    pot.id_level = 0
    pot.buc_known = False
    pot.count = 1
    return pot


def test_identify_right_answer_fully_identifies():
    g = _headless_game('__test_oneq_right__')
    pot = _fresh_potion()
    g.player.inventory.append(pot)
    g.player.known_item_ids.discard(pot.id)
    before_ids = g.player.total_identifies
    g._identify_item(pot)
    assert g.quiz_engine.active, "identify must start a quiz"
    assert g.quiz_engine.total_qs == 1
    q = g.quiz_engine.current_question
    g.quiz_engine.answer(q['answer'])          # answer correctly
    g.quiz_engine._advance()                   # past the result display
    assert pot.id_level == 5, "one right answer = fully identified"
    assert pot.buc_known is True
    assert pot.id in g.player.known_item_ids
    assert g.player.total_identifies == before_ids + 1


def test_identify_wrong_answer_stuns():
    g = _headless_game('__test_oneq_wrong__')
    pot = _fresh_potion()
    g.player.inventory.append(pot)
    g.player.known_item_ids.discard(pot.id)
    g._identify_item(pot)
    q = g.quiz_engine.current_question
    wrong = next(c for c in q['choices'] if c != q['answer'])
    g.quiz_engine.answer(wrong)
    g.quiz_engine._advance()                   # past the result display
    assert pot.id_level == 0, "a wrong answer must not identify anything"
    assert pot.id not in g.player.known_item_ids
    assert g.player.status_effects.get('stunned', 0) > 0, (
        "the Shard backlash must stun the player"
    )
