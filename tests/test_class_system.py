"""Boss Class Ascension core logic (2026-06-07).

Pure-logic tests for the class tree: loading, soft-gate requirements (option B),
offered choices per tier, applying a node's bonuses, the run-total stat cap, and
the SMALL flavor perks (signature-weapon flat damage, scalar perks, saves). The
cooking hook + selection UI are play-tested; this locks the mechanics.
"""
from items import Wand
from player import Player
import class_system as cs


def _p(**stats):
    p = Player()
    for k, v in stats.items():
        setattr(p, k, v)
    p.known_spells = {}
    p.inventory = []
    return p


def _weapon(weapon_class):
    return type('W', (), {'weapon_class': weapon_class})()


def test_loads_four_callings():
    c = cs.load_classes()
    for nid in ('fighter', 'mage', 'rogue', 'cleric'):
        assert nid in c and c[nid]['tier'] == 1


# --- soft gating (option B) --------------------------------------------------

def test_fighter_is_always_offered():
    assert 'fighter' in cs.offered_choices(_p(INT=8, DEX=8, WIS=8, CON=8, PER=8, STR=8))


def test_mage_gated_by_int_spell_or_wand():
    assert 'mage' not in cs.offered_choices(_p(INT=8, DEX=8, WIS=8, CON=8, PER=8))
    assert 'mage' in cs.offered_choices(_p(INT=14))
    spell = _p(INT=8); spell.known_spells = {'magic_missile': 3}
    assert 'mage' in cs.offered_choices(spell)
    wand = _p(INT=8)
    wand.inventory = [Wand({'id': 'w', 'name': 'W', 'symbol': '/', 'color': [1, 2, 3],
                            'charges_min': 1, 'charges_max': 1, 'max_charges': 1})]
    assert 'mage' in cs.offered_choices(wand)


def test_rogue_and_cleric_gates():
    assert 'rogue' in cs.offered_choices(_p(DEX=13))
    assert 'rogue' not in cs.offered_choices(_p(DEX=8, PER=8))
    assert 'cleric' in cs.offered_choices(_p(WIS=13))
    assert 'cleric' not in cs.offered_choices(_p(WIS=8, CON=8))


# --- applying a node (small perks) ------------------------------------------

def test_fighter_grants_small_stat_weapon_perk_save_ability():
    p = _p(STR=10)
    base = p.STR
    msgs = cs.apply_class_node(p, 'fighter')
    assert p.STR == base + 1                       # small +1 stat, not +2
    assert p.class_path == ['fighter']
    assert cs.save_bonus(p, 'body') == 1
    assert cs.has_ability(p, 'second_wind')
    assert any('Fighter' in m for m in msgs)


def test_fighter_flat_damage_only_on_swords_and_axes():
    p = _p(STR=10)
    cs.apply_class_node(p, 'fighter')
    assert cs.weapon_flat_bonus(p, _weapon('longsword')) == 2
    assert cs.weapon_flat_bonus(p, _weapon('battleaxe')) == 2
    assert cs.weapon_flat_bonus(p, _weapon('dagger')) == 0      # NOT all weapons
    assert cs.weapon_flat_bonus(p, _weapon('shortbow')) == 0
    assert cs.weapon_flat_bonus(p, None) == 0


def test_rogue_flat_damage_only_on_ranged():
    p = _p(DEX=13)
    cs.apply_class_node(p, 'rogue')
    assert cs.weapon_flat_bonus(p, _weapon('longbow')) == 2
    assert cs.weapon_flat_bonus(p, _weapon('sling')) == 2
    assert cs.weapon_flat_bonus(p, _weapon('longsword')) == 0
    assert cs.proficiency(p, 'trap_sight') == 1


def test_mage_and_cleric_scalar_perks():
    m = _p(INT=14)
    cs.apply_class_node(m, 'mage')
    assert cs.proficiency(m, 'mp_cost_reduction') == 1
    assert cs.save_bonus(m, 'mind') == 1
    c = _p(WIS=14)
    cs.apply_class_node(c, 'cleric')
    assert cs.proficiency(c, 'healing_received_pct') == 15
    assert cs.has_ability(c, 'turn_undead')


def test_run_total_stat_cap_is_enforced():
    p = _p(STR=10)
    p.class_stat_total = cs.stat_cap()             # cap already spent
    base = p.STR
    cs.apply_class_node(p, 'fighter')              # wants +1 STR
    assert p.STR == base                           # clamped, no grant
    assert p.class_stat_total == cs.stat_cap()


def test_no_tier2_nodes_until_authored():
    p = _p(STR=10)
    p.class_path = ['fighter']
    assert cs.offered_choices(p) == []


def test_old_save_without_class_attrs_is_safe():
    p = _p()
    assert cs.class_path(p) == []
    assert cs.weapon_flat_bonus(p, _weapon('longsword')) == 0
    assert cs.proficiency(p, 'healing_received_pct') == 0
    assert not cs.has_ability(p, 'second_wind')
