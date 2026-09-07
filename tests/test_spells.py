"""Tests for the v2.12.0 spell-system rebuild: spell registry consistency,
spellbook <-> spell wiring, cast/read flow contracts.

v2.12.0 KEY CONTRACT:
  * Every non-signature LEARNABLE_SPELLS entry has: tier, mp_cost, power,
    spell_family, needs_target, effect, name, desc.
  * Every spellbook maps 1:1 to a LEARNABLE_SPELLS entry (regular books)
    with quiz_threshold=1. Unique artifact books override to threshold=3.
  * Cast flow uses ONE science threshold=1 quiz at spell.tier (no more
    escalator_chain).
  * Read flow uses ONE grammar threshold=1 quiz at book.tier (regular);
    unique artifacts use threshold=3.
  * Cast fail consumes MP (fizzle). Read fail destroys the book unless
    Ring of Scheherazade (scroll_save_on_fail) or single_copy saves it.
  * Multi-tier learning: reading Cure Wounds AND Heal both stay in
    known_spells at the same time (different spell_ids).
"""
import inspect
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import spells


SIGNATURE_PREFIX = ('sign_', 'elder_')


# ---------------------------------------------------------------------------
# Registry consistency
# ---------------------------------------------------------------------------

def test_all_spells_have_required_fields():
    required = {'name', 'effect', 'mp_cost', 'quiz_tier', 'tier',
                'needs_target', 'desc', 'spell_family', 'power'}
    for sid, spec in spells.LEARNABLE_SPELLS.items():
        missing = required - set(spec.keys())
        assert not missing, f"{sid} missing fields: {missing}"


def test_spell_tier_matches_quiz_tier():
    """v2.12.0: `tier` is authoritative; `quiz_tier` kept in sync for
    legacy callers. They must match on every spell entry."""
    for sid, spec in spells.LEARNABLE_SPELLS.items():
        assert spec['tier'] == spec['quiz_tier'], (
            f"{sid}: tier ({spec['tier']}) != quiz_tier ({spec['quiz_tier']})")


def test_spell_tiers_in_valid_range():
    for sid, spec in spells.LEARNABLE_SPELLS.items():
        assert 1 <= spec['tier'] <= 5, f"{sid} has invalid tier {spec['tier']}"


def test_mp_cost_scales_with_tier():
    """Bounds per tier. Signature character-build spells (Witcher signs,
    Elder Blood) may use a different cost band but should still be modest."""
    BOUNDS = {1: (2, 5), 2: (5, 8), 3: (8, 12), 4: (12, 18), 5: (18, 25)}
    for sid, spec in spells.LEARNABLE_SPELLS.items():
        if sid.startswith(SIGNATURE_PREFIX):
            continue
        lo, hi = BOUNDS[spec['tier']]
        assert lo <= spec['mp_cost'] <= hi, (
            f"{sid} T{spec['tier']} mp_cost={spec['mp_cost']} outside [{lo},{hi}]")


def test_spell_family_present_on_every_spell():
    """v2.12.0: every spell (including signature spells) declares a
    spell_family key. Families group tier variants of the same lineage."""
    for sid, spec in spells.LEARNABLE_SPELLS.items():
        fam = spec.get('spell_family', '')
        assert fam and isinstance(fam, str), (
            f"{sid} missing or empty spell_family")


def test_family_multi_tier_lineages_exist():
    """v2.12.0: the whole point of the rebuild is multi-tier families.
    At least a handful of families must have 3+ tier variants."""
    by_family: dict[str, set] = {}
    for sid, spec in spells.LEARNABLE_SPELLS.items():
        if sid.startswith(SIGNATURE_PREFIX):
            continue
        by_family.setdefault(spec['spell_family'], set()).add(spec['tier'])
    multi_tier = [f for f, tiers in by_family.items() if len(tiers) >= 3]
    # Fire/force/healing/etc. are all 3+ tier ladders.
    assert len(multi_tier) >= 5, (
        f"only {len(multi_tier)} multi-tier families found: {multi_tier}")


def test_each_tier_has_full_category_coverage():
    """Each tier T1-T5 should have at least a damage + a buff/heal spell."""
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
        if sid.startswith(SIGNATURE_PREFIX):
            continue
        by_tier[spec['tier']].append(spec['effect'])
    for tier, effs in by_tier.items():
        s = set(effs)
        assert s & DAMAGE_EFFECTS, f"T{tier} has no damage spell"
        assert s & BUFF_HEAL_EFFECTS, f"T{tier} has no buff/heal spell"


# ---------------------------------------------------------------------------
# Spellbook <-> spell consistency
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
            continue  # consumable-artifact books (Book of Thoth) have no spell
        assert sid in spells.LEARNABLE_SPELLS, (
            f"Spellbook {bid} points to non-existent spell_id {sid!r}")


def test_every_non_signature_spell_has_at_least_one_spellbook():
    """Player-acquirable spells (non-signature) need at least one drop source."""
    books = _load_spellbook()
    book_spells = {v.get('spell_id') for v in books.values() if v.get('spell_id')}
    for sid in spells.LEARNABLE_SPELLS:
        if sid.startswith(SIGNATURE_PREFIX):
            continue
        assert sid in book_spells, f"spell {sid} has no spellbook in spellbook.json"


def test_spellbook_regular_uses_threshold_one():
    """v2.12.0: every non-unique spellbook must have quiz_threshold=1."""
    books = _load_spellbook()
    for bid, bdef in books.items():
        if bdef.get('is_unique'):
            continue
        assert int(bdef.get('quiz_threshold', 0)) == 1, (
            f"{bid} must use quiz_threshold=1 (v2.12.0 unified contract)")


def test_spellbook_unique_uses_threshold_three():
    """v2.12.0: unique artifact spellbooks keep quiz_threshold=3."""
    books = _load_spellbook()
    for bid, bdef in books.items():
        if not bdef.get('is_unique'):
            continue
        assert int(bdef.get('quiz_threshold', 0)) == 3, (
            f"unique book {bid} must use quiz_threshold=3")


def test_spellbook_has_tier_field():
    """v2.12.0: every spellbook must declare a `tier` field (1..5)."""
    books = _load_spellbook()
    for bid, bdef in books.items():
        assert 'tier' in bdef, f"{bid} missing 'tier' field"
        assert 1 <= int(bdef['tier']) <= 5, f"{bid} tier out of 1..5"


def test_spellbook_class_reads_tier_and_threshold():
    """items.Spellbook must expose the new v2.12.0 field: tier + threshold
    default 1 + is_unique + is_consumable_artifact."""
    from items import Spellbook
    b = Spellbook({
        'id': 'test_book_t3',
        'name': 'test book', 'symbol': '+', 'color': [255, 255, 255],
        'spell_id': 'heal_spell', 'spell_name': 'Heal',
        'mp_cost': 10, 'tier': 3, 'quiz_threshold': 1,
    })
    assert b.tier == 3
    assert b.quiz_threshold == 1
    assert b.is_unique is False

    # Unique-artifact book: threshold 3.
    b2 = Spellbook({
        'id': 'test_unique_book',
        'name': 'unique book', 'symbol': '+', 'color': [255, 255, 255],
        'spell_id': 'wish_spell', 'spell_name': 'Wish',
        'mp_cost': 25, 'tier': 5, 'quiz_threshold': 3, 'is_unique': True,
    })
    assert b2.tier == 5
    assert b2.quiz_threshold == 3
    assert b2.is_unique is True

    # Back-compat: no tier, falls back to quiz_tier (or default 1).
    b3 = Spellbook({
        'id': 'test_legacy_book',
        'name': 'legacy', 'symbol': '+', 'color': [255, 255, 255],
        'spell_id': 'sleep_spell', 'spell_name': 'Sleep',
        'mp_cost': 3, 'quiz_tier': 2,
    })
    assert b3.tier == 2
    assert b3.quiz_threshold == 1  # v2.12.0 default


# ---------------------------------------------------------------------------
# Cast + read flow contracts (v2.12.0)
# ---------------------------------------------------------------------------

def test_start_spell_quiz_uses_threshold_one():
    """v2.12.0: _start_spell_quiz must use threshold=1 at spell.tier.
    No more escalator_chain casting."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._start_spell_quiz)
    assert "mode='threshold'" in src, (
        "v2.12.0: all spellcasts must use threshold mode")
    assert "threshold=1" in src, (
        "v2.12.0: spell cast threshold must be 1 (single question)")
    assert "mode='escalator_chain'" not in src, (
        "v2.12.0: escalator_chain spell branch must be retired")


def test_learn_from_spellbook_uses_threshold_mode():
    """v2.12.0: _learn_from_spellbook must ALWAYS start a threshold quiz."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._learn_from_spellbook)
    assert "mode='threshold'" in src, (
        "v2.12.0: all spellbook reads must use threshold mode")
    assert "mode='escalator_chain'" not in src


def test_learn_from_spellbook_fail_destroys_book():
    """v2.12.0: a failed spellbook read destroys the book (like a failed
    scroll). Ring of Scheherazade (scroll_save_on_fail) + single_copy books
    survive; everything else crumbles."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._learn_from_spellbook)
    # The save-passive branch must be present.
    assert 'scroll_save_on_fail' in src, (
        "v2.12.0: read-fail must check for Ring of Scheherazade save")
    # The destruction path must be present.
    assert 'remove_from_inventory(book)' in src, (
        "v2.12.0: failed reads must destroy the book (except save-passive)")


def test_apply_spell_effect_signature_drops_chain():
    """v2.12.0: _apply_spell_effect no longer accepts a `chain` arg. Effect
    magnitude is fixed via spell.power dice per tier."""
    from game_magic import MagicMixin
    sig = inspect.signature(MagicMixin._apply_spell_effect)
    assert 'chain' not in sig.parameters, (
        "v2.12.0: _apply_spell_effect must NOT accept a chain arg")


def test_start_spell_quiz_fail_consumes_mp():
    """v2.12.0 KEY RULE: MP deducted BEFORE the quiz (in _invoke_spell), so
    a failed cast just leaves the message + no re-add. Verify the on_complete
    branch does NOT refund MP on failure."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._start_spell_quiz)
    # The success branch must call _apply_spell_effect; the fail branch just
    # emits the fizzle message + advances the turn.
    assert 'fizzles' in src, (
        "v2.12.0: cast-fail branch must announce that the spell fizzles")
    # Explicitly no MP refund on failure.
    assert 'player.mp +=' not in src, (
        "v2.12.0: fail branch must NOT refund MP")
    assert 'player.mp = player.mp' not in src


def test_multi_tier_learning_produces_distinct_entries():
    """v2.12.0: cure_wounds (T2), heal (T3), greater_heal (T4) are three
    distinct spell entries with the same family. They coexist in the
    spellbook menu -- learning one does NOT displace another."""
    fam_healing = [sid for sid, s in spells.LEARNABLE_SPELLS.items()
                   if s.get('spell_family') == 'healing']
    assert len(fam_healing) >= 3, (
        f"healing family should have >= 3 tiered spells, found {fam_healing}")
    tiers = sorted(spells.LEARNABLE_SPELLS[s]['tier'] for s in fam_healing)
    assert len(set(tiers)) == len(tiers), (
        f"healing family tier ids must be unique: {tiers}")


# ---------------------------------------------------------------------------
# Renderer sprite fallback
# ---------------------------------------------------------------------------

def test_spellbook_family_sprite_fallback_covers_all_families():
    """The renderer's _SPELLBOOK_FAMILY_SPRITE map must have an entry for
    every non-signature spell_family used in LEARNABLE_SPELLS."""
    from renderer import _SPELLBOOK_FAMILY_SPRITE
    families_used = {
        s['spell_family'] for sid, s in spells.LEARNABLE_SPELLS.items()
        if not sid.startswith(SIGNATURE_PREFIX)
    }
    missing = families_used - set(_SPELLBOOK_FAMILY_SPRITE.keys())
    assert not missing, (
        f"_SPELLBOOK_FAMILY_SPRITE missing entries for spell families: {sorted(missing)}")


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
    """magic_resist should NOT block bleeding/stunned/poisoned -- those are
    physical, not mental."""
    from status_effects import apply_effect

    class P:
        status_effects = {'magic_resist': 20}
        def has_effect(self, n):
            return self.status_effects.get(n, 0) > 0
    p = P()
    physical = ['bleeding', 'stunned', 'burning', 'frozen']
    for eff in physical:
        result = apply_effect(p, eff, 5)
        assert result is True, f"magic_resist should NOT block physical effect {eff}"


# ---------------------------------------------------------------------------
# Spell distribution by tier (the rebalance target)
# ---------------------------------------------------------------------------

def test_spell_tier_distribution_is_balanced():
    """v2.12.0 target: ~80-95 spells with every tier well-populated."""
    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for spec in spells.LEARNABLE_SPELLS.values():
        if 1 <= spec['tier'] <= 5:
            counts[spec['tier']] += 1
    for tier in (1, 2, 3, 4, 5):
        assert counts[tier] >= 5, f"T{tier} has only {counts[tier]} spells; need >=5"
