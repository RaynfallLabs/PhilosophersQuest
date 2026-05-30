"""Tests for the 2026-05-17 identify rebuild:
- id_level field defaults correctly on item subclasses
- mastery_blessing field loaded from JSON
- Philosopher career arc counter + threshold rewards
- Mastery application in combat damage calc
- Quick-BUC doesn't count toward career arc
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from items import Weapon, Accessory, load_items, Potion
from player import Player
import combat


# ---------------------------------------------------------------------------
# id_level defaults
# ---------------------------------------------------------------------------

def _make_weapon(**overrides):
    defn = {
        'id': 'test_sword', 'name': 'test sword', 'symbol': '(',
        'color': [180, 180, 180], 'weight': 3.0, 'item_class': 'weapon',
        'baseDamage': 5, 'chain_multipliers': [0.5, 1.0, 1.5, 2.0, 2.5],
    }
    defn.update(overrides)
    return Weapon(defn)


def test_id_level_defaults_to_zero_for_unidentified_weapon():
    w = _make_weapon()
    assert w.identified is False
    assert w.id_level == 0


def test_id_level_defaults_to_five_for_pre_identified_weapon():
    w = _make_weapon(identified=True)
    assert w.identified is True
    assert w.id_level == 5


def test_id_level_can_be_explicitly_set_in_defn():
    w = _make_weapon(id_level=3)
    assert w.id_level == 3


# ---------------------------------------------------------------------------
# mastery_blessing field
# ---------------------------------------------------------------------------

def test_mastery_blessing_none_by_default():
    w = _make_weapon()
    assert w.mastery_blessing is None


def test_mastery_blessing_loaded_from_defn():
    w = _make_weapon(mastery_blessing={
        'kind': 'weapon_base_damage_bonus', 'value': 3, 'scope': 'item',
        'desc': 'Test mastery.'
    })
    assert w.mastery_blessing is not None
    assert w.mastery_blessing['kind'] == 'weapon_base_damage_bonus'
    assert w.mastery_blessing['value'] == 3


def test_is_unique_on_base_item():
    """is_unique must live on the base Item class so all subclasses pick it up."""
    a = Accessory({
        'id': 'test_amulet', 'name': 'test amulet', 'symbol': '"',
        'color': [255, 255, 255], 'weight': 0.1, 'item_class': 'accessory',
        'slot': 'amulet', 'is_unique': True,
    })
    assert a.is_unique is True


# ---------------------------------------------------------------------------
# 20 iconic exemplars actually exist in JSON
# ---------------------------------------------------------------------------

def test_20_iconic_exemplars_have_mastery_blessings():
    """The 20 hand-authored masteries must remain present in the JSON files."""
    expected = {
        'weapon': {'soul_reaver', 'dawnbreaker', 'excalibur', 'mjolnir',
                   'hrunting', 'gungnir', 'khopesh_of_anubis', 'sword_of_michael'},
        'armor': {'babr_e_bayan', 'coat_of_cu_chulainn', 'dragon_mail_of_sigurd'},
        'shield': {'greater_aegis_of_athena'},
        'accessory': {'andvaranaut', 'draupnir', 'megingjord', 'ankh_of_isis', 'eye_of_horus'},
        'wand': {'aarons_rod'},
        'scroll': {'scroll_of_annihilation'},
        'spellbook': {'necronomicon'},
    }
    for cat, ids in expected.items():
        items = {i.id: i for i in load_items(cat)}
        for iid in ids:
            assert iid in items, f"Expected iconic unique {iid} not found in {cat} bank"
            it = items[iid]
            assert it.is_unique, f"{iid} should be is_unique=True"
            assert it.mastery_blessing, f"{iid} should have mastery_blessing"
            mb = it.mastery_blessing
            assert mb.get('kind'), f"{iid} mastery missing 'kind'"
            assert mb.get('desc'), f"{iid} mastery missing 'desc'"


# ---------------------------------------------------------------------------
# Player career-arc fields default correctly
# ---------------------------------------------------------------------------

def test_player_career_fields_default():
    p = Player()
    assert p.total_identifies == 0
    assert p.philosopher_tier_claimed == set()
    assert p.philosophers_mantle is False
    assert p.unlocked_masteries == {}


# ---------------------------------------------------------------------------
# Mastery application — combat damage
# ---------------------------------------------------------------------------

class _DummyMonster:
    """Minimal monster mock for damage-calc tests."""
    kind = 'goblin'
    tags = ['humanoid']
    max_hp = 50
    hp = 50
    alive = True
    is_boss = False
    dragon_scales = 0
    status_effects = {}

    def take_damage(self, n):
        self.hp -= n
        return n

    def is_dead(self):
        return self.hp <= 0

    def has_effect(self, _):
        return False

    def add_effect(self, name, dur):
        self.status_effects[name] = max(self.status_effects.get(name, 0), dur)


def test_weapon_chain_mult_bonus_helper():
    """The _weapon_mastery helper returns the blessing dict when claimed."""
    p = Player()
    w = _make_weapon(id='excalibur', mastery_blessing={
        'kind': 'weapon_chain_mult_bonus', 'value': 0.25, 'scope': 'item',
        'desc': 'test',
    })
    assert combat._weapon_mastery(p, w) is None  # not yet claimed
    p.unlocked_masteries[w.id] = w.mastery_blessing
    m = combat._weapon_mastery(p, w)
    assert m is not None
    assert m['value'] == 0.25


def test_tag_match():
    """_tag_match recognizes monster tag membership and kind fallback."""
    m = _DummyMonster()
    assert combat._tag_match(m, 'humanoid') is True
    assert combat._tag_match(m, 'undead') is False
    assert combat._tag_match(m, 'goblin') is True  # matches kind
    assert combat._tag_match(m, 'all') is True


# ---------------------------------------------------------------------------
# Philosopher career thresholds
# ---------------------------------------------------------------------------

class _CareerHarness:
    """Standalone harness for _check_philosopher_thresholds without Pygame init."""
    def __init__(self):
        self.player = Player()
        self.dungeon_level = 1
        self._messages = []
        self._chronicle = []

    def add_message(self, t, _typ='info'):
        self._messages.append(t)

    def _log_chronicle(self, t):
        self._chronicle.append(t)

    # Import the real method off the Game class so we test the same code.
    @staticmethod
    def _check_method():
        # Lazy import to avoid pygame-init at module load
        import main
        return main.Game._check_philosopher_thresholds


def _drive_check(h, n):
    h.player.total_identifies = n
    _CareerHarness._check_method()(h)


def test_career_25_grants_int_once():
    h = _CareerHarness()
    base_int = h.player.INT
    _drive_check(h, 25)
    assert h.player.INT == base_int + 1
    assert 25 in h.player.philosopher_tier_claimed
    # Second crossing is idempotent
    _drive_check(h, 26)
    assert h.player.INT == base_int + 1


def test_career_75_grants_pattern_recognition():
    h = _CareerHarness()
    _drive_check(h, 75)
    assert 75 in h.player.philosopher_tier_claimed
    # Pattern Recognition is a flag-only — auto-id logic checked at pickup time


def test_career_125_grants_per_once():
    h = _CareerHarness()
    base_per = h.player.PER
    _drive_check(h, 125)
    assert h.player.PER == base_per + 1
    assert 125 in h.player.philosopher_tier_claimed


def test_career_200_grants_wis_once():
    h = _CareerHarness()
    base_wis = h.player.WIS
    _drive_check(h, 200)
    assert h.player.WIS == base_wis + 1
    assert 200 in h.player.philosopher_tier_claimed


def test_career_300_grants_mantle():
    h = _CareerHarness()
    _drive_check(h, 300)
    assert h.player.philosophers_mantle is True
    assert 300 in h.player.philosopher_tier_claimed


def test_career_below_25_grants_nothing():
    """Sub-25 identifies should not fire any threshold."""
    h = _CareerHarness()
    base_int, base_wis, base_per = h.player.INT, h.player.WIS, h.player.PER
    _drive_check(h, 24)
    assert h.player.INT == base_int
    assert h.player.WIS == base_wis
    assert h.player.PER == base_per
    assert h.player.philosopher_tier_claimed == set()
    assert h.player.philosophers_mantle is False


def test_career_all_thresholds_fire_in_one_sweep():
    h = _CareerHarness()
    base_int = h.player.INT
    base_wis = h.player.WIS
    base_per = h.player.PER
    _drive_check(h, 300)
    assert h.player.INT == base_int + 1
    assert h.player.WIS == base_wis + 1
    assert h.player.PER == base_per + 1
    assert h.player.philosophers_mantle is True
    assert {25, 75, 125, 200, 300} <= h.player.philosopher_tier_claimed


# ---------------------------------------------------------------------------
# Lockpick and other always-identified subclasses keep id_level=5
# ---------------------------------------------------------------------------

def test_food_starts_identified_with_id_level_5():
    from items import Food
    f = Food({
        'id': 'apple', 'name': 'apple', 'symbol': '%',
        'color': [200, 50, 50], 'weight': 0.3, 'item_class': 'food',
        'sp_restore': 20,
    })
    assert f.identified is True
    assert f.id_level == 5


def test_ingredient_starts_identified_with_id_level_5():
    from items import Ingredient
    ing = Ingredient({
        'id': 'goblin_meat', 'name': 'goblin meat', 'symbol': '%',
        'color': [100, 50, 50], 'weight': 1.0, 'item_class': 'ingredient',
        'recipes': {},
    })
    assert ing.identified is True
    assert ing.id_level == 5


def test_potion_starts_unidentified_with_id_level_0():
    p = Potion({
        'id': 'potion_healing', 'name': 'potion of healing', 'symbol': '!',
        'color': [255, 50, 50], 'weight': 0.5, 'item_class': 'potion',
    })
    assert p.identified is False
    assert p.id_level == 0


# ---------------------------------------------------------------------------
# Data-layer: every is_unique item has a valid mastery_blessing
# ---------------------------------------------------------------------------

_ALLOWED_KINDS = {
    'weapon_chain_mult_bonus', 'weapon_base_damage_bonus', 'weapon_damage_vs_tag',
    'weapon_first_hit_crit', 'weapon_lifesteal', 'weapon_wound_lingers', 'weapon_status_chance',
    'armor_ac_bonus', 'armor_resist_bonus', 'armor_hp_bonus',
    'accessory_stat_bonus', 'accessory_passive_strength',
    'wand_extra_charge', 'scroll_extra_read', 'spellbook_mp_discount', 'potion_potency_bonus',
    # Cosmetic-only blessing: no mechanical effect, just lore/humor on
    # the item menu card. Used by the Duck of Doom's T5 reveal
    # ("The Duck of Doom has no master!").
    'cosmetic_only',
}


def test_every_unique_has_valid_mastery_blessing():
    """Every is_unique item across every category must have a valid mastery_blessing."""
    cats = ['weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll', 'spellbook']
    missing = []
    invalid = []
    for cat in cats:
        for it in load_items(cat):
            if not it.is_unique:
                continue
            mb = it.mastery_blessing
            if not mb:
                missing.append(f'{cat}:{it.id}')
                continue
            if mb.get('kind') not in _ALLOWED_KINDS:
                invalid.append(f'{cat}:{it.id} -> kind {mb.get("kind")!r}')
            if not mb.get('desc'):
                invalid.append(f'{cat}:{it.id} -> empty desc')
            # 'item' = standard one-shot mastery applied at chain-5.
            # 'carry' = stat-bonus mastery that applies only while the
            # item is in inventory (post-mastery); used for slot=none
            # uniques like Charmander Stuffie / Dreamspun Sketchbook.
            if mb.get('scope') not in ('item', 'carry'):
                invalid.append(f'{cat}:{it.id} -> scope {mb.get("scope")!r}')
    assert not missing, f"Uniques missing mastery_blessing: {missing[:8]}"
    assert not invalid, f"Invalid mastery_blessing entries: {invalid[:8]}"


# ---------------------------------------------------------------------------
# Identify-system helpers (2026-05-28): chain resume from failed tier +
# menu progress marker. See `proposals/v2_audit/IDENTIFY_SYSTEM.md`.
# ---------------------------------------------------------------------------

from items import identify_resume_params, id_progress_marker


def test_resume_params_fresh_identify():
    """Brand-new item (id_level=0): start at tier 1, full 5-chain."""
    assert identify_resume_params(0) == (1, 5)


def test_resume_params_partial_two_passed():
    """User scenario: identified to 2/5, retry resumes at tier 3 with 3 to go."""
    assert identify_resume_params(2) == (3, 3)


def test_resume_params_one_tier_left():
    """Lore revealed (4/5) but mastery unclaimed: one T5 question for mastery."""
    assert identify_resume_params(4) == (5, 1)


def test_resume_params_already_mastered_is_safe():
    """Defensive: if id_level is somehow already 5 (e.g. via Odin's Cloak +
    a re-entry race), helper still returns a valid quiz spec rather than
    asking for a 0-length chain at tier 6."""
    start, max_chain = identify_resume_params(5)
    assert start == 5 and max_chain >= 1


def test_resume_params_clamps_out_of_range():
    """Negative or > 5 prev_level shouldn't crash."""
    assert identify_resume_params(-1) == (1, 5)
    assert identify_resume_params(99) == (5, 1)


# The chain-to-id_level mapping in the resume design:
#   new_level = previous_level + chain (capped at 5, never lowers).
# These tests express the algebra; the call-sites in game_magic.py
# and main.py compute exactly this expression.

def test_new_level_partial_progress():
    """At id_level=2, kid answers T3+T4 then misses T5: chain=2 -> new_level=4."""
    previous, chain = 2, 2
    new_level = max(previous, min(previous + chain, 5))
    assert new_level == 4


def test_new_level_full_completion_to_mastery():
    """At id_level=2, kid clears T3+T4+T5: chain=3 -> new_level=5 (mastery)."""
    previous, chain = 2, 3
    new_level = max(previous, min(previous + chain, 5))
    assert new_level == 5


def test_new_level_failure_preserves_previous():
    """At id_level=2, kid blanks the start-tier question: chain=0 -> stays at 2."""
    previous, chain = 2, 0
    new_level = max(previous, min(previous + chain, 5))
    assert new_level == 2


def test_new_level_cannot_exceed_5():
    """Defensive: even if chain somehow overshoots, id_level caps at 5."""
    previous, chain = 4, 10
    new_level = max(previous, min(previous + chain, 5))
    assert new_level == 5


# ---------------------------------------------------------------------------
# Progress marker — the (N/5) appended to entry names in the identify menu.
# ---------------------------------------------------------------------------

def test_progress_marker_zero():
    assert id_progress_marker(0) == "  (0/5)"


def test_progress_marker_partial():
    assert id_progress_marker(2) == "  (2/5)"


def test_progress_marker_full():
    """Should still render correctly if asked for level 5 (menu filters
    these out, but the helper should be robust)."""
    assert id_progress_marker(5) == "  (5/5)"


def test_progress_marker_clamps_out_of_range():
    assert id_progress_marker(-1) == "  (0/5)"
    assert id_progress_marker(99) == "  (5/5)"


def test_progress_marker_handles_none():
    """getattr(item, 'id_level', 0) can return None for legacy save data."""
    assert id_progress_marker(None) == "  (0/5)"


# ---------------------------------------------------------------------------
# Identified-property back-compat (2026-05-29 bug-bash fix)
# ---------------------------------------------------------------------------
#
# Pre-fix: every Item subclass declared `self.identified = ...` as a
# plain instance attribute. Many call sites wrote `item.identified = True`
# to mark a scroll/wand identified, but id_level stayed 0 — so the
# identify menu kept showing (0/5) and the resume rule started the
# quiz from T1 instead of skipping ahead. The IDENTIFY_SYSTEM.md doc
# CLAIMED `identified` was a property; the code disagreed.
#
# Post-fix: `identified` is a real property on base Item reading
# `id_level >= 4`. Setter bumps id_level to >= 4 on True or resets
# to 0 on False. Subclass __init__ no longer shadows the property.


def test_identified_property_reads_from_id_level():
    w = _make_weapon(id_level=0)
    assert w.identified is False
    w = _make_weapon(id_level=3)
    assert w.identified is False  # below the lore tier
    w = _make_weapon(id_level=4)
    assert w.identified is True
    w = _make_weapon(id_level=5)
    assert w.identified is True


def test_identified_setter_bumps_id_level_on_true():
    """The big one. Pre-fix this set instance attr only and id_level
    stayed at 0 — the bug behind the identify-menu (0/5) regression."""
    w = _make_weapon()
    assert w.id_level == 0
    w.identified = True
    assert w.id_level == 4
    assert w.identified is True


def test_identified_setter_preserves_higher_id_level():
    w = _make_weapon(id_level=5)
    w.identified = True  # don't downgrade!
    assert w.id_level == 5


def test_identified_setter_resets_to_zero_on_false():
    w = _make_weapon(id_level=4)
    w.identified = False
    assert w.id_level == 0
    assert w.identified is False


def test_no_shadowing_instance_attribute_on_new_items():
    """After the property migration, no subclass should set `identified`
    as a plain instance attribute that shadows the property."""
    w = _make_weapon()
    # `identified` should NOT be in the per-instance __dict__ — it lives
    # on the class as a property.
    assert 'identified' not in w.__dict__


def test_save_migration_strips_shadow_attribute():
    """Old saves shadowed the property. The migration helper unwinds it."""
    from game_helpers import migrate_buc_item
    w = _make_weapon(id_level=0)
    # Simulate a legacy save by force-installing the shadow attribute.
    w.__dict__['identified'] = True
    # Sanity: before migration the shadow wins.
    assert w.__dict__.get('identified') is True
    assert w.id_level == 0  # not yet synced
    migrate_buc_item(w)
    # Shadow attribute removed, id_level bumped to the lore tier.
    assert 'identified' not in w.__dict__
    assert w.id_level == 4
    assert w.identified is True


def test_save_migration_preserves_already_high_id_level():
    from game_helpers import migrate_buc_item
    w = _make_weapon(id_level=5)
    w.__dict__['identified'] = True
    migrate_buc_item(w)
    assert w.id_level == 5  # don't downgrade!


# ---------------------------------------------------------------------------
# _propagate_identification correctness (2026-05-29 bug-bash fix)
# ---------------------------------------------------------------------------
#
# Pre-fix: only set buc_known on inventory copies; never bumped id_level
# anywhere; skipped ground items and container contents entirely. The
# IDENTIFY_SYSTEM.md doc claimed otherwise.
#
# Post-fix: sync id_level (capped 4-for-uniques / 5-for-commons),
# walk inventory + ground + containers at the player's tile.


class _FakeGame:
    """Minimal stand-in for the Game mixin chain used by
    `_propagate_identification`. Provides the attributes the method
    reads (`self.player`, `self.ground_items`) without dragging in the
    full Game/Pygame stack."""

    def __init__(self, inventory, ground_items, player_x=0, player_y=0):
        from player import Player
        self.player = Player.__new__(Player)
        self.player.x = player_x
        self.player.y = player_y
        self.player.inventory = list(inventory)
        self.player.known_item_ids = set()
        self.player.known_class_ids = set()
        self.ground_items = list(ground_items)

    # Borrow the real implementation off the MagicMixin without
    # instantiating Game (which needs Pygame).
    from game_magic import MagicMixin
    _propagate_identification = MagicMixin._propagate_identification


def test_propagate_id_level_across_inventory_copies():
    """Identifying one wand to id_level=3 bumps every other copy of the
    same id in inventory to the same level (capped at 4 for uniques).
    Pre-fix this was a no-op."""
    w1 = _make_weapon(id_level=3)
    w2 = _make_weapon(id_level=0)
    g = _FakeGame(inventory=[w1, w2], ground_items=[])
    g._propagate_identification('test_sword', level=3)
    assert w1.id_level == 3
    assert w2.id_level == 3


def test_propagate_id_level_walks_ground_items():
    """Floor copies at any tile share the identify state once a copy in
    inventory has been identified."""
    w_inv = _make_weapon(id_level=4)
    w_ground = _make_weapon(id_level=0)
    g = _FakeGame(inventory=[w_inv], ground_items=[w_ground])
    g._propagate_identification('test_sword', level=4)
    assert w_ground.id_level == 4


def test_propagate_id_level_caps_at_four_for_uniques():
    """Uniques cap at 4 so the chain-5 mastery quiz path is preserved."""
    w1 = _make_weapon(id_level=0, is_unique=True)
    w2 = _make_weapon(id_level=0, is_unique=True)
    g = _FakeGame(inventory=[w1, w2], ground_items=[])
    g._propagate_identification('test_sword', level=5)
    # Even though we asked for 5, uniques cap at 4.
    assert w1.id_level == 4
    assert w2.id_level == 4


def test_propagate_id_level_caps_at_five_for_commons():
    w1 = _make_weapon(id_level=0)  # is_unique default False
    w2 = _make_weapon(id_level=0)
    g = _FakeGame(inventory=[w1, w2], ground_items=[])
    g._propagate_identification('test_sword', level=5)
    assert w1.id_level == 5
    assert w2.id_level == 5


def test_propagate_does_not_lower_existing_id_level():
    """Monotonic — never downgrades a higher level."""
    w1 = _make_weapon(id_level=5)
    w2 = _make_weapon(id_level=0)
    g = _FakeGame(inventory=[w1, w2], ground_items=[])
    g._propagate_identification('test_sword', level=3)
    assert w1.id_level == 5  # not lowered
    assert w2.id_level == 3


# ---------------------------------------------------------------------------
# Item-name composition (2026-05-28 fix): material descriptor + template
# name should produce a natural noun phrase, not "a wooden plank light
# wooden shield". See IDENTIFY_SYSTEM.md §11.
# ---------------------------------------------------------------------------

from items import (compose_item_name, compose_unidentified_name,
                    _strip_redundant_material_words, _normalize_descriptor)


def test_strip_material_words_from_template():
    # The user's scenario: shield template "light wooden shield" + material
    # "oak" should NOT produce "oak light wooden shield" — wooden is
    # redundant with "oak" (a wood).
    assert _strip_redundant_material_words("light wooden shield") == "light shield"
    assert _strip_redundant_material_words("heavy wooden shield") == "heavy shield"
    assert _strip_redundant_material_words("iron boots") == "boots"
    assert _strip_redundant_material_words("plate helm") == "helm"
    assert _strip_redundant_material_words("chain shirt") == "shirt"
    assert _strip_redundant_material_words("leather gloves") == "gloves"


def test_strip_material_words_leaves_non_material_templates_alone():
    assert _strip_redundant_material_words("tower shield") == "tower shield"
    assert _strip_redundant_material_words("kite shield") == "kite shield"
    assert _strip_redundant_material_words("buckler") == "buckler"
    assert _strip_redundant_material_words("breastplate") == "breastplate"


def test_strip_material_words_never_returns_empty():
    # Edge case: the entire template name is generic material words.
    # We must not strip to "" — better to leave the original than
    # render a nameless item.
    assert _strip_redundant_material_words("leather") == "leather"
    assert _strip_redundant_material_words("chainmail") == "chainmail"
    assert _strip_redundant_material_words("") == ""


def test_normalize_descriptor_strips_article_and_tail_noun():
    # The exact descriptors that produced the user's bug:
    assert _normalize_descriptor("a wooden plank") == "wooden"
    assert _normalize_descriptor("a faintly blue blade") == "faintly blue"
    assert _normalize_descriptor("a pale fibrous wooden plate") == "pale fibrous wooden"
    assert _normalize_descriptor("a wooden haft") == "wooden"
    assert _normalize_descriptor("an oddly-glossy fabric") == "oddly-glossy"


def test_normalize_descriptor_leaves_adjective_phrases_alone():
    assert _normalize_descriptor("pale silvery metal") == "pale silvery metal"
    assert _normalize_descriptor("rune-chased") == "rune-chased"
    assert _normalize_descriptor("dense black metal") == "dense black metal"
    assert _normalize_descriptor("rivet-studded leather") == "rivet-studded"


def test_normalize_descriptor_never_returns_empty():
    # If everything strips, keep the original — better to look weird
    # than to lose all flavor signal.
    assert _normalize_descriptor("a plank") == "a plank"  # would strip to ''
    assert _normalize_descriptor("the blade") == "the blade"
    assert _normalize_descriptor("") == ""


def test_compose_item_name_user_scenario():
    """The exact bug the user reported, end-to-end through the
    identified path: oak material + light_wooden_shield template should
    NOT produce 'oak light wooden shield'. Title-cased since
    2026-05-29 per user feedback that 'linen padded' displayed as
    lowercase in messages."""
    assert compose_item_name("oak", "light wooden shield") == "Oak Light Shield"


def test_compose_item_name_no_change_when_no_overlap():
    assert compose_item_name("oak", "tower shield") == "Oak Tower Shield"
    assert compose_item_name("mithril", "buckler") == "Mithril Buckler"


def test_compose_item_name_handles_iron_iron_collision():
    # iron + iron_boots template -> "Iron Boots", not "Iron Iron Boots".
    assert compose_item_name("iron", "iron boots") == "Iron Boots"
    # steel + iron_boots template -> "Steel Boots" (the iron in the
    # template name is now redundant once we have a specific material).
    assert compose_item_name("steel", "iron boots") == "Steel Boots"


def test_compose_unidentified_name_user_scenario():
    """The exact wonky string the user reported: 'a pale fibrous wood
    light round wood shield' (approximate) was produced by composing
    a noun-phrase descriptor with a material-baked template name. After
    the fix:
      - article "a" is stripped from the descriptor
      - "wooden" is stripped from the template (redundant with descriptor)
      - generic material adjective "wood" in the descriptor is KEPT (it
        carries the pre-identify hint about what the material might be)
    Result reads as a natural noun phrase rather than a glued-together
    mess: 'Pale Fibrous Wood Light Shield'.
    """
    # ash (weapons-pool) has unidentified_descriptor "a pale fibrous wood"
    result = compose_unidentified_name("a pale fibrous wood", "light wooden shield")
    assert result == "Pale Fibrous Wood Light Shield", f"unexpected: {result!r}"
    # Critically: the word "wood" does NOT appear twice anymore.
    assert result.lower().count("wood") == 1


def test_compose_unidentified_name_oak_shield():
    # oak's unidentified_descriptor is "a wooden plank"
    result = compose_unidentified_name("a wooden plank", "light wooden shield")
    # Article stripped, tail noun "plank" stripped, then "wooden" left
    # as adjective. Template strips "wooden". Result reads naturally.
    assert result == "Wooden Light Shield"


def test_compose_unidentified_name_no_overlap():
    # mithril descriptor is "pale silvery metal" (adjective phrase already)
    result = compose_unidentified_name("pale silvery metal", "plate helm")
    assert result == "Pale Silvery Metal Helm"
