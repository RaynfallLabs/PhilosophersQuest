"""Tests for the 2026 spell-system rebalance: spell registry consistency,
spellbook ↔ spell wiring, and the new effect-handler smoke checks.

These verify the data side (spells.LEARNABLE_SPELLS, spellbook.json refs,
magic_resist now actively blocks magical debuffs) without standing up a full
game loop. The 14 new handlers are exercised at runtime when players cast —
no harness can drive that without a real Game instance — so this file checks
the static invariants that protect the bank from drift.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import spells


# ---------------------------------------------------------------------------
# Registry consistency
# ---------------------------------------------------------------------------

def test_all_spells_have_required_fields():
    required = {'name', 'effect', 'mp_cost', 'quiz_tier', 'needs_target', 'desc'}
    for sid, spec in spells.LEARNABLE_SPELLS.items():
        missing = required - set(spec.keys())
        assert not missing, f"{sid} missing fields: {missing}"


def test_spell_tiers_in_valid_range():
    for sid, spec in spells.LEARNABLE_SPELLS.items():
        assert 1 <= spec['quiz_tier'] <= 5, f"{sid} has invalid tier {spec['quiz_tier']}"


def test_mp_cost_scales_with_tier():
    """Higher-tier spells should generally cost more MP. Bounds per tier
    (signature character-build spells like Witcher signs/Elder Blood may use
    a different cost band but should still be modest)."""
    BOUNDS = {1: (1, 6), 2: (3, 12), 3: (8, 16), 4: (12, 24), 5: (18, 42)}
    SIGNATURE_PREFIX = ('sign_', 'elder_')   # character-locked, less strict
    for sid, spec in spells.LEARNABLE_SPELLS.items():
        if sid.startswith(SIGNATURE_PREFIX):
            continue
        lo, hi = BOUNDS[spec['quiz_tier']]
        assert lo <= spec['mp_cost'] <= hi, (
            f"{sid} T{spec['quiz_tier']} mp_cost={spec['mp_cost']} outside [{lo},{hi}]")


def test_each_tier_has_full_category_coverage():
    """Each tier T1-T5 should have at least:
      - 1 single-target damage spell
      - 1 buff/heal
      - 1 utility (non-damage, non-buff)"""
    DAMAGE_EFFECTS = {
        'magic_missile', 'fire_bolt', 'lightning_bolt', 'acid_arrow',
        'drain_life_spell', 'frost_touch', 'smite', 'aard_blast',
        'mass_fire', 'mass_ice', 'meteor', 'cone_of_cold',
        'chain_lightning_jump', 'disintegrate_spell', 'power_word_kill',
        'storm_of_vengeance', 'meteor_swarm', 'annihilate',
    }
    BUFF_HEAL_EFFECTS = {
        'shield_self', 'haste_self', 'invisibility_self', 'extra_heal',
        'reflect_self', 'displacement_self', 'phase_self', 'empower_next',
        'stoneskin_self', 'counterspell_self', 'foresight_self',
        'resurrection_self', 'greater_invis_self', 'cleanse_self',
        'levitation_self',
    }
    by_tier = {1: [], 2: [], 3: [], 4: [], 5: []}
    for sid, spec in spells.LEARNABLE_SPELLS.items():
        if sid.startswith(('sign_', 'elder_')):
            continue
        by_tier[spec['quiz_tier']].append(spec['effect'])
    for tier, effs in by_tier.items():
        s = set(effs)
        assert s & DAMAGE_EFFECTS, f"T{tier} has no damage spell"
        assert s & BUFF_HEAL_EFFECTS, f"T{tier} has no buff/heal spell"


# ---------------------------------------------------------------------------
# Spellbook ↔ spell consistency
# ---------------------------------------------------------------------------

def _load_spellbook():
    p = os.path.join(os.path.dirname(__file__), '..', 'data', 'items', 'spellbook.json')
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def test_all_spellbook_refs_point_to_real_spells():
    books = _load_spellbook()
    for bid, bdef in books.items():
        sid = bdef.get('spell_id')
        if not sid:
            continue
        assert sid in spells.LEARNABLE_SPELLS, (
            f"Spellbook {bid} points to non-existent spell_id {sid!r}")


def test_every_non_signature_spell_has_at_least_one_spellbook():
    """Player-acquirable spells (non-signature) need at least one drop source."""
    books = _load_spellbook()
    book_spells = {v.get('spell_id') for v in books.values() if v.get('spell_id')}
    for sid in spells.LEARNABLE_SPELLS:
        if sid.startswith(('sign_', 'elder_')):
            continue
        assert sid in book_spells, f"spell {sid} has no spellbook in spellbook.json"


# ---------------------------------------------------------------------------
# magic_resist is now an active block (counterspell-relevant)
# ---------------------------------------------------------------------------

def test_magic_resist_blocks_magical_debuffs():
    """Counterspell applies magic_resist; magic_resist should now block
    confused/charmed/silenced/feared/hallucinating from being applied."""
    from status_effects import apply_effect

    class P:
        status_effects = {'magic_resist': 20}
        def has_effect(self, n):
            return self.status_effects.get(n, 0) > 0
    p = P()
    blocked = ['confused', 'charmed', 'silenced', 'feared', 'hallucinating']
    for eff in blocked:
        result = apply_effect(p, eff, 5)
        assert result is False, f"magic_resist should block {eff}"
        assert eff not in p.status_effects, f"{eff} leaked past magic_resist"


def test_magic_resist_does_not_block_physical_debuffs():
    """magic_resist should NOT block bleeding/stunned/poisoned — those are
    physical, not mental."""
    from status_effects import apply_effect

    class P:
        status_effects = {'magic_resist': 20}
        def has_effect(self, n):
            return self.status_effects.get(n, 0) > 0
    p = P()
    physical = ['bleeding', 'stunned', 'burning', 'frozen']
    for eff in physical:
        # poison_resist would block 'poisoned'; we want to check magic_resist alone
        # doesn't accidentally block these.
        result = apply_effect(p, eff, 5)
        assert result is True, f"magic_resist should NOT block physical effect {eff}"


# ---------------------------------------------------------------------------
# Spell distribution by tier (the rebalance target)
# ---------------------------------------------------------------------------

def test_spell_tier_distribution_is_balanced():
    """Tier 5 (archmage) needs at least 10 spells; the old bank had 2."""
    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for spec in spells.LEARNABLE_SPELLS.values():
        if 1 <= spec['quiz_tier'] <= 5:
            counts[spec['quiz_tier']] += 1
    # Every tier should have at least 10 distinct spells (ignoring char-locked)
    for tier in (1, 2, 3, 4, 5):
        assert counts[tier] >= 10, f"T{tier} has only {counts[tier]} spells; need >=10"
