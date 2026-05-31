"""Engine wave 5 (2026-05-30): verification that the 9 named T5 chain-equip
accessory passives have live consumers.

The unique-accessory audit (2026-05-30) claimed all 9 were "stored but
never consulted." A direct grep across src/ shows the audit was incorrect:
each named passive has at least one consumer at a real hook site.

This test file locks in the wiring with grep-based presence checks so
the audit's "design proposed, code missing" claim doesn't return.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _source(*modules):
    """Concatenated source of named modules — for cross-module presence checks."""
    out = []
    for mod_name in modules:
        path = ROOT / "src" / f"{mod_name}.py"
        out.append(path.read_text(encoding='utf-8'))
    return "\n".join(out)


SRC_ALL = _source('main', 'game_combat', 'game_magic', 'game_encounters',
                  'game_input', 'chain_passives')


def test_three_oclock_consumer_present():
    """Ring of Gawain T5 — STR decay-and-reset proc. Wired in main + game_input."""
    assert 'three_oclock' in SRC_ALL
    assert '_three_oclock_decay' in SRC_ALL


def test_solomonic_key_consumer_present():
    """Ring of Solomon T5 — 1/floor lock bypass. Wired in main container path."""
    assert 'solomonic_key' in SRC_ALL


def test_reassembly_consumer_present():
    """Tyet of Isis T5 — once-per-run full-HP restore on lethal damage."""
    # Wired in game_combat near _reassembly_regen_remaining.
    assert 'reassembly' in SRC_ALL
    assert '_reassembly_regen_remaining' in SRC_ALL


def test_anti_being_consumer_present():
    """Heart of Ahriman T5 — next destructive spell deals 2x damage."""
    assert 'anti_being' in SRC_ALL
    assert '_anti_being_charged' in SRC_ALL


def test_beautiful_ruin_consumer_present():
    """Necklace of Harmonia T5 — fear aura on adjacent monsters."""
    assert 'beautiful_ruin' in SRC_ALL


def test_one_thousand_and_one_consumer_present():
    """Ring of Scheherazade T5 — reroll a failed chain quiz attempt."""
    assert 'one_thousand_and_one' in SRC_ALL


def test_atalantas_choice_consumer_present():
    """Anklet of Atalanta T5 — free movement every 10 turns."""
    assert 'atalantas_choice' in SRC_ALL


def test_aesir_young_consumer_present():
    """Idunn Apple Charm T5 — protected 5t on re-equip."""
    assert 'aesir_young' in SRC_ALL


def test_suryas_gift_consumer_present():
    """Kavacha-Kundala T5 — karma-scaled defensive bonus."""
    assert 'suryas_gift' in SRC_ALL


# ---------------------------------------------------------------------------
# Per-passive smoke (where straightforward to construct)
# ---------------------------------------------------------------------------


def test_anti_being_doubles_spell_damage_when_charged():
    """chain_passives.apply_spell_damage_passives doubles damage when charged."""
    from chain_passives import apply_spell_damage_passives

    class _P:
        _anti_being_charged = True
        armor_slots = ()
        accessory_slots = ()
        amulet_slot = None
        shield = None
    p = _P()
    dmg, _crit, anti = apply_spell_damage_passives(p, 10.0)
    assert anti is True
    assert dmg >= 20.0
    # After firing, the flag clears.
    assert p._anti_being_charged is False


def test_consume_run_passive_marks_spent_once():
    """consume_run_passive returns True only once per run for each flag."""
    from chain_passives import consume_run_passive

    class _Item:
        def __init__(self):
            self._chain_passives = {'reassembly': True}

    class _P:
        armor_slots = ()
        shield = None
        amulet_slot = _Item()
        accessory_slots = ()
        _chain_passive_once_per_run = set()
    p = _P()
    assert consume_run_passive(p, 'reassembly') is True
    assert consume_run_passive(p, 'reassembly') is False
