"""JSON Wave 3 (2026-05-30): verify per-unit flag flips landed on the
specific lore-named armor and accessory uniques the audit called out.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _load(name):
    p = ROOT / "data" / "items" / f"{name}.json"
    return json.loads(p.read_text(encoding='utf-8'))


ARMOR = _load('armor')
ACCESSORY = _load('accessory')


# ---------------------------------------------------------------------------
# AB band
# ---------------------------------------------------------------------------

def test_penelope_has_weave_and_unweave():
    assert ARMOR['cloth_of_penelope']['weave_and_unweave'] is True


def test_linothorax_has_phalanx_recovery():
    assert ARMOR['linothorax_of_alexander']['phalanx_recovery'] == 2


def test_dilmun_has_water_bonuses():
    a = ARMOR['scale_of_dilmun']
    assert a['water_tile_ac_bonus'] == 2
    assert a['water_tile_regen_bonus'] == 1


def test_nemean_pelt_is_unskinnable():
    assert ARMOR['nemean_pelt']['unskinnable'] is True


def test_mantle_of_elijah_has_prophets_passing():
    assert ARMOR['mantle_of_elijah']['prophets_passing'] is True


def test_arachne_has_webbed_strike():
    assert ARMOR['arachne_silk_cloak']['webbed_strike'] is True


def test_arachne_tier_raised_to_3():
    assert ARMOR['arachne_silk_cloak']['tier'] == 3


def test_erlking_has_forest_hearing():
    assert ARMOR['erlking_mantle']['forest_hearing'] == 6


def test_anansi_has_story_thread():
    assert ARMOR['anansi_web_cloak']['story_thread'] is True


def test_wukong_has_monkey_king_dodge():
    assert ARMOR['cloak_of_sun_wukong']['monkey_king_dodge'] == 10
    assert ARMOR['cloak_of_sun_wukong']['ac_bonus'] == 3


def test_beowulf_has_grendel_grip():
    assert ARMOR['coif_of_beowulf']['grendel_grip'] is True


def test_trainers_cap_has_bond_check():
    assert ARMOR['trainers_cap']['bond_check'] is True


def test_hermes_votive_dodge_first_arrow():
    assert ARMOR['hermes_sandals_early']['dodge_first_arrow_per_floor'] is True


def test_theseus_has_their_own_methods():
    assert ARMOR['sandals_of_theseus']['their_own_methods'] == 0.20


def test_cuchulainn_bracers_riastrad_echo():
    assert ARMOR['bracers_of_cu_chulainn']['riastrad_echo'] is True


# ---------------------------------------------------------------------------
# CD band
# ---------------------------------------------------------------------------

def test_hannibal_has_cannae_encirclement():
    assert ARMOR['cuirass_of_hannibal']['cannae_encirclement'] is True


def test_leonidas_has_last_stand_bonus():
    assert ARMOR['helm_of_leonidas']['last_stand_bonus'] is True


def test_caesar_has_et_tu_charge():
    assert ARMOR['lorica_hamata_of_caesar']['et_tu_charge'] is True


def test_wallace_has_guerrilla_terrain():
    assert ARMOR['brigandine_of_william_wallace']['guerrilla_terrain'] is True


def test_mars_gauntlets_boundary_guardian():
    assert ARMOR['gauntlets_of_mars']['boundary_guardian'] is True


def test_enkidu_has_wild_friend():
    assert ARMOR['leggings_of_enkidu']['wild_friend'] == 0.20


def test_arjuna_has_gita_focus():
    assert ARMOR['bracers_of_arjuna']['gita_focus'] is True


def test_hermes_greaves_hasted_and_descent():
    g = ARMOR['greaves_of_hermes']
    assert g['onEquipStatus'] == 'hasted'
    assert g['descend_stairs_no_turn'] is True


def test_blindfold_has_tremor_sense():
    assert ARMOR['blindfold']['tremor_sense'] == 3


def test_vambraces_threshold_4_and_peace_at_forge():
    v = ARMOR['vambraces_of_achilles']
    assert v['equip_threshold'] == 4
    assert v['peace_at_the_forge'] == 2


def test_winged_sandals_tier_raised_to_3():
    assert ARMOR['winged_sandals_of_hermes']['tier'] == 3


# ---------------------------------------------------------------------------
# EF band
# ---------------------------------------------------------------------------

def test_nemean_hide_is_unskinnable():
    assert ARMOR['hide_of_nemean_lion']['unskinnable'] is True


def test_hydra_has_caustic_blood():
    assert ARMOR['carapace_of_the_hydra']['caustic_blood'] == 0.40


def test_panoply_has_divine_smithing():
    assert ARMOR['panoply_of_hephaestus']['divine_smithing'] == 1


def test_joan_has_maid_does_not_fall():
    assert ARMOR['breastplate_of_joan']['maid_does_not_fall'] is True


def test_yoshitsune_has_descent_haste():
    assert ARMOR['haramaki_of_yoshitsune']['descent_haste'] == 5


def test_achilles_helm_has_ringing_intimidation():
    assert ARMOR['helm_of_achilles']['ringing_intimidation'] == 3


def test_galahad_has_purity():
    assert ARMOR['great_helm_of_galahad']['purity'] is True


def test_thor_boots_has_thors_step():
    assert ARMOR['boots_of_thor']['thors_step'] == 0.05


def test_helm_of_hades_no_top_level_invisible():
    """The escalator unlocks invisibility — don't double-grant at base."""
    h = ARMOR['helm_of_hades']
    assert h.get('onEquipStatus') != 'invisible'
    assert h.get('on_equip_status') != 'invisible'


# ---------------------------------------------------------------------------
# Accessory deltas
# ---------------------------------------------------------------------------

def test_talisman_of_troy_has_stat_and_ac():
    t = ACCESSORY['talisman_of_troy']
    assert t['effects']['stat'] == 'WIS'
    assert t['effects']['amount'] == 2
    assert t['effects']['status'] == 'reflecting'
    assert t['ac_bonus'] == 2


def test_megingjord_thor_god_tier():
    m = ACCESSORY['megingjord']
    assert m['effects']['stat'] == 'STR'
    assert m['effects']['amount'] == 6
    assert m['effects']['status'] == 'hasted'


def test_pectoral_of_amun_wis_5():
    p = ACCESSORY['pectoral_of_amun']
    assert p['effects']['amount'] == 5
    assert p['effects']['status'] == 'magic_resist'


def test_nibelung_curse_and_gold():
    r = ACCESSORY['ring_of_the_nibelung']
    assert r['effects']['amount'] == 5
    assert r['gold_multiplier'] == 2.0
    assert r['can_be_cursed'] is True


def test_percival_has_magic_resist():
    p = ACCESSORY['ring_of_percival']
    assert p['effects']['status'] == 'magic_resist'


def test_hamsa_has_reflecting():
    h = ACCESSORY['hamsa_hand']
    assert h['effects']['status'] == 'reflecting'


def test_draupnir_threshold_3():
    assert ACCESSORY['draupnir']['equip_threshold'] == 3


def test_idunn_threshold_3():
    assert ACCESSORY['idunn_apple_charm']['equip_threshold'] == 3


def test_assassin_ring_silent_walk():
    a = ACCESSORY['ring_of_the_assassin']
    assert a['effects']['status'] == 'silent_walk'


def test_starter_plot_lock_quiz_tier_dropped():
    for sid in ('anubis_scales', 'sphinx_crown', 'sailors_amulet', 'prophets_amulet'):
        assert ACCESSORY[sid]['quiz_tier'] == 2
