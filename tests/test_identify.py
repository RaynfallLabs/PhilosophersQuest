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


def test_career_10_grants_int_once():
    h = _CareerHarness()
    base_int = h.player.INT
    _drive_check(h, 10)
    assert h.player.INT == base_int + 1
    assert 10 in h.player.philosopher_tier_claimed
    # Second crossing is idempotent
    _drive_check(h, 11)
    assert h.player.INT == base_int + 1


def test_career_25_grants_pattern_recognition():
    h = _CareerHarness()
    _drive_check(h, 25)
    assert 25 in h.player.philosopher_tier_claimed
    # No INT change at 25 (that's the 10-mark)
    # Pattern Recognition is a flag-only — auto-id logic checked at pickup time


def test_career_50_grants_wis_once():
    h = _CareerHarness()
    base_wis = h.player.WIS
    _drive_check(h, 50)
    assert h.player.WIS == base_wis + 1
    assert 50 in h.player.philosopher_tier_claimed


def test_career_100_grants_mantle():
    h = _CareerHarness()
    _drive_check(h, 100)
    assert h.player.philosophers_mantle is True
    assert 100 in h.player.philosopher_tier_claimed


def test_career_all_thresholds_fire_in_one_sweep():
    h = _CareerHarness()
    base_int = h.player.INT
    base_wis = h.player.WIS
    _drive_check(h, 100)
    assert h.player.INT == base_int + 1
    assert h.player.WIS == base_wis + 1
    assert h.player.philosophers_mantle is True
    assert {10, 25, 50, 100} <= h.player.philosopher_tier_claimed


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
            if mb.get('scope') != 'item':
                invalid.append(f'{cat}:{it.id} -> scope {mb.get("scope")!r}')
    assert not missing, f"Uniques missing mastery_blessing: {missing[:8]}"
    assert not invalid, f"Invalid mastery_blessing entries: {invalid[:8]}"
