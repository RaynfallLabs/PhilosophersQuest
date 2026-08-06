"""Tests for the one-question identify redesign (2026-08-06).

- id_level field defaults correctly on item subclasses
- derive_id_tier / item_id_tier: the ONE question's tier, from JSON fields
- type_class: the granularity of type knowledge (True Name model)
- Philosopher career arc counter + threshold rewards
- _propagate_identification records TYPE knowledge only (no per-copy bumps)
- carry_bonus field (Charmander Stuffie / Dreamspun Sketchbook)
- identified-property back-compat + save migration
- Item-name composition (unchanged from the 2026-05-28 fix)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from items import (Weapon, Accessory, load_items, Potion, Corpse,
                   derive_id_tier, item_id_tier, type_class)
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


def test_is_unique_on_base_item():
    """is_unique must live on the base Item class so all subclasses pick it up."""
    a = Accessory({
        'id': 'test_amulet', 'name': 'test amulet', 'symbol': '"',
        'color': [255, 255, 255], 'weight': 0.1, 'item_class': 'accessory',
        'slot': 'amulet', 'is_unique': True,
    })
    assert a.is_unique is True


# ---------------------------------------------------------------------------
# derive_id_tier — the tier of the ONE identify question
# ---------------------------------------------------------------------------

def test_derive_id_tier_explicit_override_wins():
    assert derive_id_tier(explicit=3, tier=1, quiz_tier=1, peak_floor=90) == 3


def test_derive_id_tier_gear_tier_first():
    assert derive_id_tier(tier=2, quiz_tier=5, peak_floor=90) == 2


def test_derive_id_tier_quiz_tier_next():
    assert derive_id_tier(quiz_tier=4, peak_floor=5) == 4


def test_derive_id_tier_peak_floor_bands():
    """100-floor dungeon: 20-floor bands map to tiers 1-5."""
    assert derive_id_tier(peak_floor=1) == 1
    assert derive_id_tier(peak_floor=20) == 1
    assert derive_id_tier(peak_floor=21) == 2
    assert derive_id_tier(peak_floor=45) == 3
    assert derive_id_tier(peak_floor=70) == 4
    assert derive_id_tier(peak_floor=95) == 5
    assert derive_id_tier(peak_floor=999) == 5   # clamped


def test_derive_id_tier_spawn_weight_band_fallback():
    """Potions have no peak_floor/quiz_tier — the heaviest floorSpawnWeight
    band decides (midpoint through the 20-floor bands)."""
    fsw = {'1-20': 120, '21-40': 80, '41-60': 50}
    assert derive_id_tier(floor_spawn_weight=fsw) == 1
    deep = {'1-20': 5, '61-80': 90}
    assert derive_id_tier(floor_spawn_weight=deep) == 4


def test_derive_id_tier_min_level_last_resort():
    assert derive_id_tier(min_level=50) == 3


def test_derive_id_tier_default_is_one():
    assert derive_id_tier() == 1


def test_derive_id_tier_uniques_floor_at_four():
    assert derive_id_tier(is_unique=True, tier=1) == 4
    assert derive_id_tier(is_unique=True, tier=5) == 5
    assert derive_id_tier(is_unique=True) == 4


def test_item_id_tier_reads_live_weapon():
    w = _make_weapon(tier=3)
    assert item_id_tier(w) == 3


def test_item_id_tier_unique_weapon_floors_at_four():
    w = _make_weapon(tier=2, is_unique=True)
    assert item_id_tier(w) == 4


def test_item_id_tier_json_override_beats_derivation():
    w = _make_weapon(tier=3, id_tier=1)
    assert item_id_tier(w) == 1


def test_corpse_id_tier_from_harvest_tier():
    c = Corpse('zombie', 'zombie', 0, 0, harvest_tier=3)
    assert c.id_tier == 3
    assert item_id_tier(c) == 3


def test_corpse_id_tier_falls_back_to_monster_peak_floor():
    c = Corpse('golem', 'golem', 0, 0, harvest_tier=0,
               monster_def={'peak_floor': 55})
    assert c.id_tier == 3


def test_corpse_id_tier_defaults_to_one():
    c = Corpse('blob', 'blob', 0, 0, harvest_tier=0)
    assert c.id_tier == 1


# ---------------------------------------------------------------------------
# type_class — the granularity of "once you know it, you know it"
# ---------------------------------------------------------------------------

def _make_accessory(item_id, name, **overrides):
    defn = {
        'id': item_id, 'name': name, 'symbol': '=',
        'color': [200, 200, 210], 'weight': 0.1, 'item_class': 'accessory',
        'slot': 'ring', 'identified': False,
    }
    defn.update(overrides)
    return Accessory(defn)


def test_type_class_accessory_groups_by_name_slug():
    """Material variants of the same named ring are ONE learned type."""
    gold = _make_accessory('ring_protection_gold', 'ring of protection')
    iron = _make_accessory('ring_protection_iron', 'ring of protection')
    assert type_class(gold) == type_class(iron) == 'ring_of_protection'


def test_type_class_unique_keys_by_id():
    u = _make_accessory('andvaranaut', 'Andvaranaut', is_unique=True)
    assert type_class(u) == 'andvaranaut'


def test_type_class_non_accessory_keys_by_id():
    w = _make_weapon()
    assert type_class(w) == 'test_sword'


def test_knows_item_type_via_class():
    p = Player()
    gold = _make_accessory('ring_protection_gold', 'ring of protection')
    iron = _make_accessory('ring_protection_iron', 'ring of protection')
    p.known_class_ids.add(type_class(gold))
    assert p.knows_item_type(iron) is True


def test_knows_item_type_via_id():
    p = Player()
    w = _make_weapon()
    p.known_item_ids.add('test_sword')
    assert p.knows_item_type(w) is True


def test_tag_match():
    """_tag_match recognizes monster tag membership and kind fallback."""
    class _DummyMonster:
        kind = 'goblin'
        tags = ['humanoid']
    m = _DummyMonster()
    assert combat._tag_match(m, 'humanoid') is True
    assert combat._tag_match(m, 'undead') is False
    assert combat._tag_match(m, 'goblin') is True  # matches kind
    assert combat._tag_match(m, 'all') is True


# ---------------------------------------------------------------------------
# Player career-arc fields default correctly
# ---------------------------------------------------------------------------

def test_player_career_fields_default():
    p = Player()
    assert p.total_identifies == 0
    assert p.philosopher_tier_claimed == set()
    assert p.philosophers_mantle is False


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
    # Pattern Recognition is a flag-only — type-reveal logic checked at pickup time


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
# Data-layer: masteries are gone; keepsakes converted to carry_bonus
# ---------------------------------------------------------------------------

def test_no_item_carries_mastery_blessing_anymore():
    cats = ['weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll',
            'spellbook', 'potion', 'artifact']
    leftovers = []
    for cat in cats:
        for it in load_items(cat):
            if getattr(it, 'mastery_blessing', None):
                leftovers.append(f'{cat}:{it.id}')
    assert not leftovers, f"mastery_blessing should be stripped: {leftovers[:8]}"


def test_keepsakes_have_carry_bonus():
    accs = {i.id: i for i in load_items('accessory')}
    charmander = accs['charmander_stuffie']
    sketchbook = accs['dreamspun_sketchbook']
    assert charmander.carry_bonus == {'stat': 'CON', 'amount': 2}
    assert sketchbook.carry_bonus == {'stat': 'INT', 'amount': 2}


def test_carry_bonus_applies_while_in_inventory():
    p = Player()
    base_con = p.CON
    stuffie = _make_accessory('charmander_stuffie', 'Charmander Stuffie',
                              slot='none', is_unique=True,
                              carry_bonus={'stat': 'CON', 'amount': 2})
    assert p.add_to_inventory(stuffie)
    assert p.CON == base_con + 2
    p.remove_from_inventory(stuffie)
    assert p.CON == base_con


def test_every_identifiable_item_gets_a_valid_id_tier():
    """Data-layer guard: item_id_tier must land in 1..5 for everything the
    identify menu could ever show, and uniques must sit at T4+."""
    cats = ['weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll',
            'spellbook', 'potion', 'artifact', 'food', 'ammo']
    bad = []
    for cat in cats:
        for it in load_items(cat):
            t = item_id_tier(it)
            if not (1 <= t <= 5):
                bad.append(f'{cat}:{it.id} -> {t}')
            elif getattr(it, 'is_unique', False) and t < 4:
                bad.append(f'{cat}:{it.id} unique below T4 -> {t}')
    assert not bad, f"Bad id_tiers: {bad[:10]}"


def test_every_monster_corpse_gets_a_valid_id_tier():
    import json
    from paths import data_path
    with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
        monsters = json.load(f)
    bad = []
    for mid, defn in monsters.items():
        c = Corpse(defn.get('name', mid), mid, 0, 0,
                   harvest_tier=defn.get('harvest_tier', 1),
                   monster_def={'peak_floor': defn.get('peak_floor', 0)})
        if not (1 <= c.id_tier <= 5):
            bad.append(f'{mid} -> {c.id_tier}')
    assert not bad, f"Bad corpse id_tiers: {bad[:10]}"


# ---------------------------------------------------------------------------
# Identified-property back-compat (2026-05-29 bug-bash fix)
# ---------------------------------------------------------------------------

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
    """No subclass should set `identified` as a plain instance attribute
    that shadows the property."""
    w = _make_weapon()
    assert 'identified' not in w.__dict__


def test_save_migration_strips_shadow_attribute():
    """Old saves shadowed the property. The migration helper unwinds it."""
    from game_helpers import migrate_buc_item
    w = _make_weapon(id_level=0)
    # Simulate a legacy save by force-installing the shadow attribute.
    w.__dict__['identified'] = True
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
# _propagate_identification — True Name model (2026-08-06)
# ---------------------------------------------------------------------------
#
# Records TYPE knowledge only: known_item_ids + known_class_ids. It must
# NOT touch other copies' id_level or buc_known — each instance keeps its
# own BUC/enchant secret until identified individually.


class _FakeGame:
    """Minimal stand-in for the Game mixin chain used by
    `_propagate_identification`."""

    def __init__(self, inventory, ground_items, player_x=0, player_y=0):
        from player import Player
        self.player = Player.__new__(Player)
        self.player.x = player_x
        self.player.y = player_y
        self.player.inventory = list(inventory)
        self.player.known_item_ids = set()
        self.player.known_class_ids = set()
        self.ground_items = list(ground_items)

    from game_magic import MagicMixin
    _propagate_identification = MagicMixin._propagate_identification


def test_propagate_records_type_knowledge():
    w1 = _make_weapon(id_level=5)
    g = _FakeGame(inventory=[w1], ground_items=[])
    g._propagate_identification('test_sword', seed_item=w1)
    assert 'test_sword' in g.player.known_item_ids
    assert type_class(w1) in g.player.known_class_ids


def test_propagate_does_not_touch_other_copies():
    """The heart of the True Name model: a second copy keeps its own
    instance state (id_level 0, BUC hidden) even once the type is known."""
    w1 = _make_weapon(id_level=5)
    w2 = _make_weapon(id_level=0)
    w2.buc_known = False
    g = _FakeGame(inventory=[w1, w2], ground_items=[])
    g._propagate_identification('test_sword', seed_item=w1)
    assert w2.id_level == 0
    assert w2.buc_known is False


def test_propagate_finds_seed_from_ground_when_not_given():
    ring = _make_accessory('ring_protection_gold', 'ring of protection')
    g = _FakeGame(inventory=[], ground_items=[ring])
    g._propagate_identification('ring_protection_gold')
    assert 'ring_protection_gold' in g.player.known_item_ids
    assert 'ring_of_protection' in g.player.known_class_ids


# ---------------------------------------------------------------------------
# Item-name composition (2026-05-28 fix): material descriptor + template
# name should produce a natural noun phrase, not "a wooden plank light
# wooden shield".
# ---------------------------------------------------------------------------

from items import (compose_item_name, compose_unidentified_name,
                    _strip_redundant_material_words, _normalize_descriptor)


def test_strip_material_words_from_template():
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
    assert _strip_redundant_material_words("leather") == "leather"
    assert _strip_redundant_material_words("chainmail") == "chainmail"
    assert _strip_redundant_material_words("") == ""


def test_normalize_descriptor_strips_article_and_tail_noun():
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
    assert _normalize_descriptor("a plank") == "strange"   # would strip to ''
    assert _normalize_descriptor("the blade") == "strange"
    assert _normalize_descriptor("") == ""


def test_compose_item_name_user_scenario():
    assert compose_item_name("oak", "light wooden shield") == "Oak Light Shield"


def test_compose_item_name_no_change_when_no_overlap():
    assert compose_item_name("oak", "tower shield") == "Oak Tower Shield"
    assert compose_item_name("mithril", "buckler") == "Mithril Buckler"


def test_compose_item_name_handles_iron_iron_collision():
    assert compose_item_name("iron", "iron boots") == "Iron Boots"
    assert compose_item_name("steel", "iron boots") == "Steel Boots"


def test_compose_unidentified_name_user_scenario():
    result = compose_unidentified_name("a pale fibrous wood", "light wooden shield")
    assert result == "Pale Fibrous Wood Light Shield", f"unexpected: {result!r}"
    assert result.lower().count("wood") == 1


def test_compose_unidentified_name_oak_shield():
    result = compose_unidentified_name("a wooden plank", "light wooden shield")
    assert result == "Wooden Light Shield"


def test_compose_unidentified_name_no_overlap():
    result = compose_unidentified_name("pale silvery metal", "plate helm")
    assert result == "Pale Silvery Metal Helm"
