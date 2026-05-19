"""Tests for the 2026-05-18 corpse-identify rebuild.

Verifies:
  - Corpse.id_level defaults to 0
  - lore_identified is a property reflecting id_level >= 4
  - get_monster_family honors FAMILY_PRIORITY ordering
  - Family-mastery blessings exist for all 12 families
  - Propagation: same monster_id -> full id_level, same family -> >= 3
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from items import Corpse
from player import Player
from monster_classes import (
    FAMILY_PRIORITY,
    MONSTER_FAMILY_BLESSINGS,
    get_monster_family,
)


# ---------------------------------------------------------------------------
# Corpse.id_level defaults
# ---------------------------------------------------------------------------

def _make_corpse(monster_id='goblin', monster_name='goblin',
                 tags=None, lore=''):
    return Corpse(
        monster_name=monster_name,
        monster_id=monster_id,
        x=0, y=0,
        harvest_tier=1,
        harvest_threshold=2,
        ingredient_id=None,
        lore=lore,
        monster_def={'tags': list(tags or [])},
    )


def test_corpse_id_level_starts_at_zero():
    c = _make_corpse()
    assert c.id_level == 0


def test_lore_identified_property_reflects_id_level_zero():
    c = _make_corpse()
    assert c.lore_identified is False


def test_lore_identified_true_at_id_level_4():
    c = _make_corpse()
    c.id_level = 4
    assert c.lore_identified is True


def test_lore_identified_true_at_id_level_5():
    c = _make_corpse()
    c.id_level = 5
    assert c.lore_identified is True


def test_lore_identified_false_at_id_level_3():
    """Stats are known but lore is not -- property must be False at level 3."""
    c = _make_corpse()
    c.id_level = 3
    assert c.lore_identified is False


def test_lore_identified_setter_bumps_id_level_to_4():
    """Legacy callers that assigned lore_identified = True still work."""
    c = _make_corpse()
    c.lore_identified = True
    assert c.id_level == 4
    assert c.lore_identified is True


def test_lore_identified_setter_does_not_lower_higher_levels():
    """Setting lore_identified=True on a level-5 corpse must not demote it."""
    c = _make_corpse()
    c.id_level = 5
    c.lore_identified = True
    assert c.id_level == 5


# ---------------------------------------------------------------------------
# get_monster_family priority
# ---------------------------------------------------------------------------

def test_get_monster_family_priority_order_demon_beats_humanoid():
    """A monster tagged both demon and humanoid is identified as demon
    (demon comes first in FAMILY_PRIORITY)."""
    c = _make_corpse(tags=['demon', 'humanoid'])
    assert get_monster_family(c) == 'demon'


def test_get_monster_family_priority_order_dragon_beats_beast():
    c = _make_corpse(tags=['beast', 'dragon'])
    assert get_monster_family(c) == 'dragon'


def test_get_monster_family_none_if_no_family_tag():
    """Monsters with only non-family tags (boss, fiend, etc.) return None."""
    c = _make_corpse(tags=['boss', 'unique'])
    assert get_monster_family(c) is None


def test_get_monster_family_empty_tags():
    c = _make_corpse(tags=[])
    assert get_monster_family(c) is None


def test_get_monster_family_accepts_dict():
    """get_monster_family accepts a plain monster defn dict too."""
    assert get_monster_family({'tags': ['undead']}) == 'undead'


def test_get_monster_family_accepts_object_with_tags():
    """Falls back to .tags attribute on Monster instances."""
    class M:
        tags = ['fey', 'humanoid']
    assert get_monster_family(M()) == 'fey'


# ---------------------------------------------------------------------------
# MONSTER_FAMILY_BLESSINGS coverage
# ---------------------------------------------------------------------------

def test_family_mastery_blessing_lookup_each_family():
    """Every family in FAMILY_PRIORITY must have a blessing entry."""
    for fam in FAMILY_PRIORITY:
        b = MONSTER_FAMILY_BLESSINGS.get(fam)
        assert b is not None, f"Missing blessing for family {fam}"
        assert b.get('kind'), f"{fam} blessing missing 'kind'"
        assert b.get('desc'), f"{fam} blessing missing 'desc'"


def test_family_blessing_kinds_are_known():
    """Every blessing 'kind' must be one of the supported use-site hooks."""
    allowed = {
        'damage_vs_tag', 'tohit_vs_tag',
        'wisdom_bonus', 'int_bonus',
        'resist_charm', 'resist_elemental', 'sp_regen',
    }
    for fam, b in MONSTER_FAMILY_BLESSINGS.items():
        assert b['kind'] in allowed, (
            f"{fam} has unknown kind {b['kind']!r} (add hook or update test)"
        )


def test_damage_vs_tag_blessings_have_tag_field():
    """damage_vs_tag and tohit_vs_tag blessings must declare which tag they
    target -- otherwise the use-site can't match against monsters."""
    for fam, b in MONSTER_FAMILY_BLESSINGS.items():
        if b['kind'] in ('damage_vs_tag', 'tohit_vs_tag'):
            assert b.get('tag'), (
                f"{fam} blessing of kind {b['kind']} missing 'tag' field"
            )


# ---------------------------------------------------------------------------
# Propagation: same monster_id -> full level
# ---------------------------------------------------------------------------

def test_propagate_full_id_to_same_monster_id():
    """Studying one goblin corpse propagates id_level to other goblin corpses
    (the propagation lives in main.Game._start_corpse_identify; here we
    verify the underlying invariant: same monster_id corpses can be bumped
    in lockstep)."""
    c1 = _make_corpse('goblin', 'goblin', tags=['humanoid'])
    c2 = _make_corpse('goblin', 'goblin', tags=['humanoid'])
    c1.id_level = 3
    # The Game.on_complete callback walks ground_items + inventory and bumps
    # any corpse with matching monster_id. Reproduce that here.
    for other in (c1, c2):
        if other.monster_id == c1.monster_id:
            other.id_level = max(other.id_level, c1.id_level)
    assert c2.id_level == 3


def test_propagate_partial_id_to_same_family():
    """At id_level >= 3, all same-family corpses (different monster_id) are
    bumped to id_level >= 3. Verify with two distinct humanoids."""
    c_human = _make_corpse('goblin', 'goblin', tags=['humanoid'])
    c_kin = _make_corpse('orc', 'orc', tags=['humanoid'])
    c_other = _make_corpse('zombie', 'zombie', tags=['undead'])
    c_human.id_level = 3
    # Reproduce the family-bump logic from _start_corpse_identify.
    fam = get_monster_family(c_human)
    for other in (c_kin, c_other):
        if other is not c_human and get_monster_family(other) == fam:
            other.id_level = max(other.id_level, 3)
    assert c_kin.id_level == 3      # same family humanoid, bumped
    assert c_other.id_level == 0    # different family, unchanged


def test_propagation_does_not_demote_higher_levels():
    """If a kin-corpse already at level 5 receives a level-3 family bump,
    it must stay at 5."""
    c_human = _make_corpse('goblin', 'goblin', tags=['humanoid'])
    c_kin = _make_corpse('orc', 'orc', tags=['humanoid'])
    c_kin.id_level = 5
    c_human.id_level = 3
    for other in (c_kin,):
        if get_monster_family(other) == get_monster_family(c_human):
            other.id_level = max(other.id_level, 3)
    assert c_kin.id_level == 5


# ---------------------------------------------------------------------------
# Player has the family-mastery store
# ---------------------------------------------------------------------------

def test_player_unlocked_monster_class_masteries_defaults_empty():
    p = Player()
    assert hasattr(p, 'unlocked_monster_class_masteries')
    assert p.unlocked_monster_class_masteries == {}


# ---------------------------------------------------------------------------
# Combat hook: damage_vs_tag blessing adds flat damage
# ---------------------------------------------------------------------------

def test_combat_damage_vs_tag_helper_reads_player_store():
    """Verify that the family-damage blessing is queryable from the player
    store and that _tag_match resolves matching monsters. (The actual damage
    integration is covered by the existing combat damage tests; this checks
    the hook contract.)"""
    import combat
    p = Player()
    p.unlocked_monster_class_masteries['dragon'] = (
        MONSTER_FAMILY_BLESSINGS['dragon']
    )
    blessing = p.unlocked_monster_class_masteries['dragon']
    assert blessing['kind'] == 'damage_vs_tag'
    assert blessing['tag'] == 'dragon'

    class _DragonMon:
        kind = 'red_dragon'
        tags = ['dragon', 'reptile']
    class _GoblinMon:
        kind = 'goblin'
        tags = ['humanoid']

    assert combat._tag_match(_DragonMon(), 'dragon') is True
    assert combat._tag_match(_GoblinMon(), 'dragon') is False
