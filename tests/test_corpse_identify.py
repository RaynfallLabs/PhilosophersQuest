"""Tests for corpse identification under the one-question redesign (2026-08-06).

Verifies:
  - Corpse.id_level defaults to 0; id_tier derives from harvest_tier /
    monster peak_floor
  - lore_identified is a property reflecting id_level >= 4 (back-compat)
  - get_monster_family reads the written `family` (monster_classes is a
    thin reader of data/monsters.json since 2026-10-18)
  - Propagation: same monster_id corpses bump together; a studied type
    spawns future corpses pre-identified
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from items import Corpse
from player import Player
from monster_classes import get_family_name, get_monster_family


# ---------------------------------------------------------------------------
# Corpse.id_level defaults
# ---------------------------------------------------------------------------

def _make_corpse(monster_id='goblin', monster_name='goblin',
                 tags=None, lore='', harvest_tier=1, monster_def_extra=None):
    mdef = {'tags': list(tags or [])}
    mdef.update(monster_def_extra or {})
    return Corpse(
        monster_name=monster_name,
        monster_id=monster_id,
        x=0, y=0,
        harvest_tier=harvest_tier,
        harvest_threshold=2,
        ingredient_id=None,
        lore=lore,
        monster_def=mdef,
    )


def test_corpse_id_level_starts_at_zero():
    c = _make_corpse()
    assert c.id_level == 0


def test_corpse_id_tier_matches_harvest_tier():
    c = _make_corpse(harvest_tier=4)
    assert c.id_tier == 4


def test_corpse_id_tier_falls_back_to_peak_floor_band():
    c = _make_corpse(harvest_tier=0, monster_def_extra={'peak_floor': 75})
    assert c.id_tier == 4


def test_corpse_id_tier_never_below_one():
    c = _make_corpse(harvest_tier=0)
    assert c.id_tier == 1


def test_lore_identified_property_reflects_id_level_zero():
    c = _make_corpse()
    assert c.lore_identified is False


def test_lore_identified_true_at_id_level_5():
    c = _make_corpse()
    c.id_level = 5
    assert c.lore_identified is True


def test_lore_identified_setter_bumps_id_level():
    """Legacy callers that assigned lore_identified = True still work."""
    c = _make_corpse()
    c.lore_identified = True
    assert c.lore_identified is True


def test_lore_identified_setter_does_not_lower_higher_levels():
    c = _make_corpse()
    c.id_level = 5
    c.lore_identified = True
    assert c.id_level == 5


# ---------------------------------------------------------------------------
# get_monster_family: a thin reader of the written family field
# ---------------------------------------------------------------------------

def test_get_monster_family_reads_the_kind_not_the_tags():
    # A dracolich carries undead and dragon tags; its LORE files it under
    # Dragons, and the tags do not decide it any more.
    c = _make_corpse(monster_id='dracolich', tags=['undead', 'dragon', 'caster'])
    assert get_monster_family(c) == 'dragons'
    assert get_family_name(c) == 'Dragons and Wyrms'


def test_get_monster_family_for_a_kind_a_dict_and_a_spider():
    assert get_monster_family('skeleton') == 'restless_dead'
    assert get_monster_family({'id': 'goblin'}) == 'goblinkin'
    assert get_monster_family('giant_spider') == 'vermin'      # spiders merged into Vermin


def test_get_monster_family_none_for_a_creature_with_no_family():
    for kind in ('death', 'secret_cow', 'ethereal_unicorn'):
        assert get_monster_family(kind) is None
    c = _make_corpse(monster_id='no_such_monster', tags=['boss', 'unique'])
    assert get_monster_family(c) is None


def test_get_monster_family_ignores_tags():
    c = _make_corpse(monster_id='goblin', tags=[])
    assert get_monster_family(c) == 'goblinkin'
    assert get_monster_family({'tags': ['undead']}) is None     # no kind, no family


def test_get_monster_family_accepts_a_monster_with_its_field():
    class M:
        kind = 'giant_rat'
        family = 'vermin'
    assert get_monster_family(M()) == 'vermin'


def test_every_family_has_a_name():
    import family_lore
    assert len(family_lore.families()) == 22
    for fid in family_lore.families():
        assert get_family_name(family_lore.members(fid)[0]) == family_lore.family_name(fid)


# ---------------------------------------------------------------------------
# Propagation invariants (the Game callback walks corpses and bumps them)
# ---------------------------------------------------------------------------

def test_propagate_full_id_to_same_monster_id():
    """Identifying one goblin corpse sets every goblin corpse to 5 — corpses
    carry no per-instance secrets, so type knowledge is total."""
    c1 = _make_corpse('goblin', 'goblin', tags=['humanoid'])
    c2 = _make_corpse('goblin', 'goblin', tags=['humanoid'])
    c1.id_level = 5
    for other in (c1, c2):
        if other.monster_id == c1.monster_id:
            other.id_level = 5
    assert c2.id_level == 5


def test_studied_type_is_remembered_on_the_player():
    """lore_known_monster_ids is the permanent 'this monster type is known'
    set — game_combat._make_corpse pre-identifies future spawns from it."""
    p = Player()
    p.lore_known_monster_ids.add('goblin')
    assert 'goblin' in p.lore_known_monster_ids


def test_player_has_no_mastery_stores():
    """The three mastery stores are gone from the game."""
    p = Player()
    assert not hasattr(p, 'unlocked_masteries')
    assert not hasattr(p, 'unlocked_class_masteries')
    assert not hasattr(p, 'unlocked_monster_class_masteries')
