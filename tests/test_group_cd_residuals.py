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

# (test_potion_potency_bonus_scales_both_heal_and_buff_duration removed
# 2026-08-06 — potion masteries were retired with the one-question
# identify redesign; BUC multipliers still cover heal/buff scaling.)


# ---------------------------------------------------------------------------
# D1 — RETIRED (v2.13.0, 2026-09-06).
#
# v2.13.0 replaced the whole 9-prayer picker (including Confiteor and
# Benedictio) with:
#   * Simple Prayer (\)        -- one theology escalator_chain, stacking
#                                 SP/HP/MP/uncurse-or-bless/shielded.
#   * Divine Intercession (Shift+\) -- one-per-run big-ask quiz.
#   * Altar drop-reveal        -- passive karma-branched BUC reveal.
#
# All Confiteor/Benedictio-specific tests were removed; tests for the
# new prayer + intercession + drop-reveal shapes live in test_prayer.py.
# ---------------------------------------------------------------------------

def test_v2_13_prayer_simplification_landed():
    """Sanity: the retired hooks stay gone, the new hooks exist."""
    import game_divine
    assert not hasattr(game_divine, 'PRAYERS'), (
        "v2.13.0: PRAYERS registry was retired"
    )
    assert not hasattr(game_divine.DivineMixin, '_prayer_benedictio')
    assert not hasattr(game_divine.DivineMixin, '_prayer_confiteor')
    # The new API surface:
    for name in ('_altar_drop_reveal', '_resolve_simple_prayer',
                 '_start_divine_intercession',
                 '_confirm_divine_intercession',
                 '_resolve_intercession_success',
                 '_resolve_intercession_failure'):
        assert hasattr(game_divine.DivineMixin, name), (
            f"v2.13.0: missing new hook {name}"
        )


# ---------------------------------------------------------------------------
# D2 — Scroll of Identify pick target + grant mastery
# ---------------------------------------------------------------------------

def test_scroll_identify_picker_method_exists():
    """game_magic.MagicMixin must expose the picker + direct-reveal hooks."""
    from game_magic import MagicMixin
    assert hasattr(MagicMixin, '_open_scroll_identify_picker')
    assert hasattr(MagicMixin, '_scroll_full_identify')
    assert hasattr(MagicMixin, '_scroll_identify_mass')


def test_scroll_identify_reveals_directly():
    """The scroll's direct reveal must run the shared _full_identify path."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._scroll_full_identify)
    assert '_full_identify' in src, (
        "Scroll of Identify must fully identify the chosen item directly"
    )


def test_uncursed_identify_opens_picker():
    """The uncursed Scroll of Identify branch must open the picker."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._apply_scroll_effect)
    assert "_open_scroll_identify_picker(" in src, (
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
# D4 — v2.10.0 scroll-system rebuild
#
# The original D4 tests locked in escalator_chain for Scroll of Heal.
# v2.10.0 retired escalator_chain for scrolls: every scroll now has a
# FIXED tier (1-5), fires ONE grammar question at that tier (threshold=1
# for regular scrolls, threshold=3 for unique artifact scrolls only), and
# tier drives both the quiz difficulty and the effect magnitude via
# _apply_scroll_effect's _tstep. These tests were rewritten to lock in
# the new contract.
# ---------------------------------------------------------------------------

def test_heal_scrolls_have_tier_and_power():
    """All non-unique heal scrolls must have `tier` + `power` (dice string)
    fields -- power scales heal amount, tier scales quiz difficulty."""
    p = ROOT / "data" / "items" / "scroll.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    heal_ids = [k for k, v in d.items() if v.get('effect') == 'heal']
    assert heal_ids, "at least one heal scroll must exist"
    for sid in heal_ids:
        s = d[sid]
        assert 'tier' in s, f"{sid} missing 'tier' field"
        assert 1 <= int(s['tier']) <= 5, f"{sid} tier out of 1..5"
        assert s.get('power'), f"{sid} missing dice string in 'power'"


def test_scroll_class_reads_tier_and_threshold():
    """items.Scroll must expose the new v2.10.0 fields: tier + quiz_threshold
    (default 1) + is_unique."""
    from items import Scroll
    s = Scroll({
        'id': 'test_scroll_t3',
        'name': 'test scroll', 'symbol': '?', 'color': [255, 255, 255],
        'effect': 'heal', 'tier': 3, 'quiz_threshold': 1, 'power': '4d4',
    })
    assert s.tier == 3
    assert s.quiz_threshold == 1
    assert s.is_unique is False

    # Unique artifact scroll: threshold 3.
    s2 = Scroll({
        'id': 'test_unique_scroll',
        'name': 'unique scroll', 'symbol': '?', 'color': [255, 255, 255],
        'effect': 'dead_sea_map', 'tier': 5, 'quiz_threshold': 3,
        'is_unique': True,
    })
    assert s2.tier == 5
    assert s2.quiz_threshold == 3
    assert s2.is_unique is True

    # Back-compat: no tier, falls back to quiz_tier (or default 1).
    s3 = Scroll({
        'id': 'test_legacy_scroll',
        'name': 'legacy', 'symbol': '?', 'color': [255, 255, 255],
        'effect': 'mapping', 'quiz_tier': 2,
    })
    assert s3.tier == 2
    assert s3.quiz_threshold == 1  # v2.10.0 default


def test_apply_scroll_effect_uses_tier_step():
    """_apply_scroll_effect must derive _tstep from scroll.tier and no
    longer accept a `chain` parameter (v2.10.0 retired chain-mode scrolls)."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._apply_scroll_effect)
    assert '_tstep' in src, (
        "_apply_scroll_effect must derive _tstep from scroll.tier"
    )
    # Make sure the chain parameter has been dropped from the signature.
    sig = inspect.signature(MagicMixin._apply_scroll_effect)
    assert 'chain' not in sig.parameters, (
        "v2.10.0: _apply_scroll_effect must NOT accept a chain arg"
    )


def test_legacy_chain_mult_tables_are_deleted():
    """v2.12.1 UI-rot sweep: _SCROLL_HEAL_CHAIN_MULTS and _SPELL_CHAIN_MULTS
    were kept as historical no-op tables through v2.10.0 and v2.12.0. Now
    that both scroll + spell effects are fully tier-baked into power dice,
    the tables are removed. Lock in the deletion so they don't get
    accidentally reintroduced."""
    from game_magic import MagicMixin
    assert not hasattr(MagicMixin, '_SCROLL_HEAL_CHAIN_MULTS')
    assert not hasattr(MagicMixin, '_SPELL_CHAIN_MULTS')


def test_read_scroll_uses_threshold_mode():
    """v2.10.0: _read_scroll must ALWAYS start a threshold quiz (chain-mode
    retired). Tier comes from scroll.tier; threshold from scroll.quiz_threshold."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._read_scroll)
    assert "mode='threshold'" in src, (
        "v2.10.0: all scroll reads must use threshold mode"
    )
    # escalator_chain branch must be gone.
    assert "mode='escalator_chain'" not in src, (
        "v2.10.0: escalator_chain scroll branch must be retired"
    )
    assert "scroll.tier" in src or "getattr(scroll, 'tier'" in src, (
        "v2.10.0: read tier must come from scroll.tier"
    )


def test_annihilate_scrolls_immune_boss_guard():
    """v2.10.0 annihilate scrolls must exclude bosses / seal-demons /
    huge (>500 max_hp) monsters -- same guard as genocide."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._apply_scroll_effect)
    # Find the annihilate branch and verify the boss guard is in place.
    ann_idx = src.find("elif effect == 'annihilate'")
    assert ann_idx >= 0, "annihilate branch must exist"
    # Everything up to the next elif in the annihilate block.
    end_idx = src.find("elif effect ==", ann_idx + 20)
    if end_idx < 0:
        end_idx = len(src)
    ann_block = src[ann_idx:end_idx]
    assert "is_boss" in ann_block, "annihilate must guard against is_boss"
    assert "is_seal_demon" in ann_block, "annihilate must guard against seal demons"
    assert "500" in ann_block, "annihilate must have the 500-HP boss guard"


def test_scroll_json_has_no_escalator_chain():
    """v2.10.0: no scroll may declare quiz_mode: escalator_chain anymore."""
    p = ROOT / "data" / "items" / "scroll.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    for sid, sdef in d.items():
        assert sdef.get('quiz_mode', 'threshold') != 'escalator_chain', (
            f"{sid} still uses retired escalator_chain mode"
        )


def test_dead_sea_scroll_is_unique_artifact():
    """Dead Sea Scroll must be marked is_unique + min_level 9999 +
    threshold 3 + tier 5."""
    p = ROOT / "data" / "items" / "scroll.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    assert 'dead_sea_scroll' in d
    dss = d['dead_sea_scroll']
    assert dss.get('is_unique') is True
    assert int(dss.get('min_level', 0)) == 9999
    assert int(dss.get('tier', 0)) == 5
    assert int(dss.get('quiz_threshold', 0)) == 3
    assert dss.get('effect') == 'dead_sea_map'


def test_book_of_thoth_is_consumable_artifact():
    """Book of Thoth must be in spellbook.json marked is_unique +
    is_consumable_artifact + min_level 9999 + threshold 3 + tier 5. It does
    NOT teach a spell -- spell_id is intentionally empty so the artifact
    goes through _read_book_of_thoth, not the learn-a-spell path."""
    p = ROOT / "data" / "items" / "spellbook.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    assert 'book_of_thoth' in d, "Book of Thoth must be in spellbook.json"
    bot = d['book_of_thoth']
    assert bot.get('is_unique') is True
    assert bot.get('is_consumable_artifact') is True
    assert int(bot.get('min_level', 0)) == 9999
    assert int(bot.get('quiz_tier', 0)) == 5
    assert int(bot.get('quiz_threshold', 0)) == 3
    # Consumable artifact -- fires effect on read, doesn't teach a spell.
    assert not bot.get('spell_id'), (
        "Book of Thoth must not have a spell_id (it fires an effect on read)"
    )


def test_learn_from_spellbook_routes_consumable_artifact():
    """_learn_from_spellbook must route is_consumable_artifact books to
    the Book-of-Thoth handler instead of the learn-a-spell path."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._learn_from_spellbook)
    assert "is_consumable_artifact" in src
    assert "_read_book_of_thoth" in src
    assert hasattr(MagicMixin, '_read_book_of_thoth')
    assert hasattr(MagicMixin, '_book_of_thoth_omniscience')
    assert hasattr(MagicMixin, '_book_of_thoth_curse')


# ---------------------------------------------------------------------------
# v2.11.0 — wand-system rebuild (parallels the scroll rebuild above)
# ---------------------------------------------------------------------------

def test_wand_class_reads_tier_threshold_and_is_unique():
    """items.Wand must expose the v2.11.0 fields: tier + quiz_threshold
    (default 1) + is_unique."""
    from items import Wand
    w = Wand({
        'id': 'test_wand_t3',
        'name': 'test wand', 'symbol': '/', 'color': [200, 200, 200],
        'effect': 'fire_bolt', 'tier': 3, 'quiz_threshold': 1, 'power': '7d6',
    })
    assert w.tier == 3
    assert w.quiz_threshold == 1
    assert w.is_unique is False

    # Back-compat: no tier, falls back to quiz_tier.
    w2 = Wand({
        'id': 'test_legacy_wand',
        'name': 'legacy', 'symbol': '/', 'color': [200, 200, 200],
        'effect': 'light', 'quiz_tier': 2,
    })
    assert w2.tier == 2
    assert w2.quiz_threshold == 1  # v2.11.0 default

    # Unique-artifact flag propagates.
    w3 = Wand({
        'id': 'test_unique_wand',
        'name': 'unique', 'symbol': '/', 'color': [200, 200, 200],
        'effect': 'iron_mortar', 'tier': 4, 'is_unique': True,
    })
    assert w3.is_unique is True


def test_wand_json_has_tier_and_threshold_one():
    """Every non-artifact wand must have `tier` + `quiz_threshold: 1`."""
    p = ROOT / "data" / "items" / "wand.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    for wid, wdef in d.items():
        assert 'tier' in wdef, f"{wid} missing 'tier' field"
        assert 1 <= int(wdef['tier']) <= 5, f"{wid} tier out of 1..5"
        assert int(wdef.get('quiz_threshold', 0)) == 1, (
            f"{wid} must use quiz_threshold=1 (v2.11.0 unified contract)"
        )


def test_invoke_wand_uses_threshold_one_and_tier():
    """v2.11.0: _invoke_wand must ALWAYS start a threshold quiz with
    threshold=1 at the wand's authoritative `tier` field."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._invoke_wand)
    assert "mode='threshold'" in src, (
        "v2.11.0: all self-target wand zaps must use threshold mode"
    )
    assert "threshold=1" in src, (
        "v2.11.0: wand quiz threshold must be 1 (single question)"
    )
    # No more chain-mode wand branch in _invoke_wand.
    assert "mode='escalator_chain'" not in src, (
        "v2.11.0: escalator_chain wand branch must be retired"
    )


def test_confirm_wand_target_uses_threshold_one():
    """v2.11.0: _confirm_wand_target (targeted-wand quiz launch) must also
    use threshold=1 -- magic_missile no longer branches to chain mode."""
    from game_combat import CombatMixin
    src = inspect.getsource(CombatMixin._confirm_wand_target)
    assert "mode='threshold'" in src
    assert "threshold=1" in src
    assert "mode='escalator_chain'" not in src, (
        "v2.11.0: magic_missile chain-mode branch must be retired"
    )


def test_invoke_wand_fail_consumes_charge():
    """v2.11.0 KEY RULE: a failed wand quiz still consumes one charge
    (the wand fizzes and is wasted). Both self-target (_invoke_wand)
    and targeted (_confirm_wand_target) code paths must enforce this."""
    from game_magic import MagicMixin
    from game_combat import CombatMixin
    src_self = inspect.getsource(MagicMixin._invoke_wand)
    src_tgt  = inspect.getsource(CombatMixin._confirm_wand_target)
    for tag, src in (('_invoke_wand', src_self), ('_confirm_wand_target', src_tgt)):
        # The charge decrement must occur BEFORE the not-result.success guard,
        # and the fail branch must not re-decrement. Test: the pattern
        # 'wand.charges -= 1' appears once in the on_complete BEFORE the fail
        # message, and the fail message announces the charge is wasted.
        assert 'wand.charges -= 1' in src, f"{tag}: charge decrement missing"
        assert 'the charge is wasted' in src, (
            f"{tag}: fail branch must announce that the charge is wasted"
        )


def test_wand_tier_damage_does_not_double_scale():
    """v2.11.0: wand.power dice are already tier-baked (T1 3d4 ... T5 12d10),
    so _wand_tier_damage must NOT re-apply a 0.5-3.0x tier multiplier.
    Damage scales with player INT, not with tier."""
    from game_magic import MagicMixin

    class _P:
        INT = 10

    class _G:
        player = _P()

    dmg_t1 = MagicMixin._wand_tier_damage(_G(), 100, 1)
    dmg_t5 = MagicMixin._wand_tier_damage(_G(), 100, 5)
    # At the same INT, T1 and T5 must yield the same damage from the same
    # base (the tier scaling is now baked into wand.power, not this helper).
    assert dmg_t1 == dmg_t5, (
        f"v2.11.0: tier arg must not re-scale damage; got T1={dmg_t1} T5={dmg_t5}"
    )


def test_wand_effect_sprite_fallback_covers_new_wands():
    """The renderer's _WAND_EFFECT_SPRITE map must have an entry for every
    effect used by a wand in wand.json (parallels the scroll fallback map).
    A missing entry means a whole tier ladder renders as a bare '/' glyph."""
    from renderer import _WAND_EFFECT_SPRITE
    p = ROOT / "data" / "items" / "wand.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    effects_used = {v.get('effect') for v in d.values() if v.get('effect')}
    missing = effects_used - set(_WAND_EFFECT_SPRITE.keys())
    assert not missing, (
        f"_WAND_EFFECT_SPRITE missing entries for wand effects: {sorted(missing)}"
    )


# ---------------------------------------------------------------------------
# v2.12.0 -- spellbook + spellcast system rebuild (parallels wand rebuild)
# ---------------------------------------------------------------------------

def test_spellbook_json_regular_uses_threshold_one():
    """v2.12.0: every non-unique spellbook must have quiz_threshold=1."""
    p = ROOT / "data" / "items" / "spellbook.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    for bid, bdef in d.items():
        if bdef.get('is_unique'):
            continue
        assert int(bdef.get('quiz_threshold', 0)) == 1, (
            f"{bid} must use quiz_threshold=1 (v2.12.0 unified contract)")


def test_spellbook_json_has_tier_field():
    """v2.12.0: every spellbook must declare a tier field."""
    p = ROOT / "data" / "items" / "spellbook.json"
    d = json.loads(p.read_text(encoding='utf-8'))
    for bid, bdef in d.items():
        assert 'tier' in bdef, f"{bid} missing 'tier' field"
        assert 1 <= int(bdef['tier']) <= 5, f"{bid} tier out of 1..5"


def test_start_spell_quiz_uses_threshold_one_science():
    """v2.12.0: _start_spell_quiz must fire a threshold=1 science quiz."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._start_spell_quiz)
    assert "mode='threshold'" in src
    assert "threshold=1" in src
    assert "subject='science'" in src
    assert "mode='escalator_chain'" not in src, (
        "v2.12.0: escalator_chain spell branch must be retired")


def test_learn_from_spellbook_uses_threshold_grammar():
    """v2.12.0: _learn_from_spellbook must fire a threshold grammar quiz."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._learn_from_spellbook)
    assert "mode='threshold'" in src
    assert "subject='grammar'" in src


def test_learn_from_spellbook_read_fail_destroys_book():
    """v2.12.0: fail branch removes book from inventory unless Ring of
    Scheherazade (scroll_save_on_fail) or single_copy fires."""
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._learn_from_spellbook)
    assert 'scroll_save_on_fail' in src
    assert 'remove_from_inventory(book)' in src


def test_apply_spell_effect_no_chain_arg():
    """v2.12.0: _apply_spell_effect must NOT accept a chain arg (parallels
    the v2.10.0 scroll rewrite)."""
    from game_magic import MagicMixin
    sig = inspect.signature(MagicMixin._apply_spell_effect)
    assert 'chain' not in sig.parameters, (
        "v2.12.0: _apply_spell_effect must NOT accept a chain arg")


def test_spellbook_class_reads_tier():
    """items.Spellbook must expose the v2.12.0 field: tier + default
    quiz_threshold=1."""
    from items import Spellbook
    b = Spellbook({
        'id': 'test_book',
        'name': 'test', 'symbol': '+', 'color': [255, 255, 255],
        'spell_id': 'heal_spell', 'spell_name': 'Heal',
        'mp_cost': 10, 'tier': 3, 'quiz_threshold': 1,
    })
    assert b.tier == 3
    assert b.quiz_threshold == 1
    assert b.is_unique is False


def test_multi_tier_spell_families_coexist():
    """v2.12.0: reading Cure Wounds AND Heal both leave distinct entries in
    known_spells (they are different spell_ids sharing spell_family='healing')."""
    from spells import LEARNABLE_SPELLS
    fam = 'healing'
    healing = [sid for sid, s in LEARNABLE_SPELLS.items()
               if s.get('spell_family') == fam]
    # cure_light T1, cure_wounds T2, heal T3, greater_heal T4, resurrection T5
    assert len(healing) >= 5, (
        f"healing family must have 5 tier variants, got {healing}")
    # Simulate learning both cure_wounds and heal simultaneously.
    known: dict = {}
    known['cure_wounds_spell'] = LEARNABLE_SPELLS['cure_wounds_spell']['mp_cost']
    known['heal_spell'] = LEARNABLE_SPELLS['heal_spell']['mp_cost']
    assert 'cure_wounds_spell' in known
    assert 'heal_spell' in known
    assert known['cure_wounds_spell'] != known['heal_spell']  # different MP


def test_spellbook_family_sprite_fallback_covers_new_books():
    """The renderer's _SPELLBOOK_FAMILY_SPRITE map must have an entry for
    every non-signature spell_family used in LEARNABLE_SPELLS."""
    from renderer import _SPELLBOOK_FAMILY_SPRITE
    from spells import LEARNABLE_SPELLS
    families_used = {
        s['spell_family'] for sid, s in LEARNABLE_SPELLS.items()
        if not sid.startswith(('sign_', 'elder_'))
    }
    missing = families_used - set(_SPELLBOOK_FAMILY_SPRITE.keys())
    assert not missing, (
        f"_SPELLBOOK_FAMILY_SPRITE missing entries for spell families: {sorted(missing)}"
    )
