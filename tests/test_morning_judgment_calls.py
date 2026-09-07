"""Pin tests for the 4 morning judgment calls (2026-05-31):

1. Sling chain-5 peak bumped to 4.5 — max-chain-only finesse niche
2. Ancient dragon frost_breath nerfed (chance 0.8→0.5, duration 1d12→1d6)
3. spellbook_lightning (T3) removed; T4 chain_lightning_jump arc count
   now scales with chain count
4. Chaos/wish/wonder data-only items disabled (min_level=9999) until
   their dispatchers ship
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _load(rel_path):
    return json.loads((ROOT / rel_path).read_text(encoding='utf-8'))


# ---------------------------------------------------------------------------
# 1. Sling — chain-5 peak
# ---------------------------------------------------------------------------

def test_sling_chain5_is_max_chain_payoff():
    """Chain-5 multiplier 4.5 makes sling the best ranged at peak only.

    chain-5 effective = 4.5 * damage_modifier (0.6) = 2.70 — highest in
    the ranged class. Chains 1-4 stay below all peers.
    """
    sling = _load('data/templates/weapons/sling.json')
    assert sling['chain_multipliers'][-1] == 4.5
    # chains 1-4 must stay below all other ranged peers (peers all peak ≤ 1.45 at rung 4)
    assert sling['chain_multipliers'][3] <= 2.0


# ---------------------------------------------------------------------------
# 2. Ancient dragon nerf
# ---------------------------------------------------------------------------

def test_ancient_dragon_frost_breath_nerf():
    monsters = _load('data/monsters.json')
    ad = monsters['ancient_dragon']
    fb = next(a for a in ad['attacks'] if a.get('name') == 'frost_breath')
    assert fb['effect_chance'] == 0.5
    assert fb['effect_duration'] == '1d6'


# ---------------------------------------------------------------------------
# 3. Spellbook chain_lightning consolidation
# ---------------------------------------------------------------------------

def test_spellbook_lightning_t3_removed():
    spellbook = _load('data/items/spellbook.json')
    assert 'spellbook_lightning' not in spellbook


def test_spellbook_chain_lightning_t4_remains():
    """v2.12.0: spellbook id renamed from spellbook_chain_lightning_t4 to
    spellbook_chain_lightning (family-canonical naming). It's still T4 and
    still points to chain_lightning_spell."""
    spellbook = _load('data/items/spellbook.json')
    assert 'spellbook_chain_lightning' in spellbook
    t4 = spellbook['spellbook_chain_lightning']
    assert t4['spell_id'] == 'chain_lightning_spell'
    assert int(t4.get('tier', 0)) == 4


def test_chain_lightning_handler_fixed_arc_count():
    """v2.12.0: the chain_lightning_jump handler uses a fixed _max_arcs (no
    longer keyed on the retired `chain` param). Verify the arc-count sizing
    logic is still present."""
    src_path = ROOT / "src" / "game_magic.py"
    src_text = src_path.read_text(encoding='utf-8')
    marker = "effect == 'chain_lightning_jump'"
    assert marker in src_text
    snippet = src_text[src_text.index(marker):src_text.index(marker) + 2000]
    assert '_max_arcs' in snippet, (
        "v2.12.0: chain lightning must still bound arc count via _max_arcs")


# ---------------------------------------------------------------------------
# 4. Chaos / Wish / Wonder data-only items disabled
# ---------------------------------------------------------------------------

def test_pandoras_box_disabled():
    artifact = _load('data/items/artifact.json')
    if 'pandoras_box' in artifact:
        assert artifact['pandoras_box'].get('min_level', 0) >= 9999
        assert '_disabled_reason' in artifact['pandoras_box']


def test_aladdins_lamp_disabled():
    artifact = _load('data/items/artifact.json')
    if 'aladdins_lamp' in artifact:
        assert artifact['aladdins_lamp'].get('min_level', 0) >= 9999
        assert '_disabled_reason' in artifact['aladdins_lamp']


def test_wand_of_wonder_legendary_disabled():
    wand = _load('data/items/wand.json')
    if 'wand_of_wonder_legendary' in wand:
        assert wand['wand_of_wonder_legendary'].get('min_level', 0) >= 9999
        assert '_disabled_reason' in wand['wand_of_wonder_legendary']
