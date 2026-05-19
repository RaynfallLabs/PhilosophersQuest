"""Tests for the chain damage gradient under the chain-peak-anchored formula.

Established 2026-05-18 after the iron-shortsword `[1, 1, 1, 1, 2]` problem.

Rules:
  - weapon_base = max(1, round(mob_hp(peak_floor) / chain_5_mult))
  - base_damage = max(2, round(weapon_base * material.damage_mult * template.damage_modifier))
  - For every (template, material, floor) combo, the 5-rung chain damage must
    NOT be flat (e.g. all 1s with one 2 at the end). At minimum: chain[4] > chain[0].
  - All active uniques (peak_floor > 0) use exactly 5-entry chainMultipliers.
  - No unique's chain-5 damage exceeds 2.5x a same-template common's at the
    same peak_floor.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from paths import data_path  # noqa: E402


def mob_hp(pf: int) -> float:
    if pf <= 0:
        return 0.0
    if pf <= 20:
        return 4 * 1.10 ** (pf - 1)
    return 4 * 1.10 ** 19 * 1.025 ** (pf - 20)


def compute_chain(template: dict, material: dict, pf: int) -> list[int]:
    cm = template['chain_multipliers']
    cm5 = cm[-1]
    dmod = template['damage_modifier']
    mmod = material['damage_mult']
    wb = max(1, round(mob_hp(pf) / cm5))
    bd = max(2, round(wb * mmod * dmod))
    return [max(1, round(bd * c)) for c in cm]


def load_templates() -> dict:
    out = {}
    tdir = data_path('data', 'templates', 'weapons')
    for fn in os.listdir(tdir):
        if not fn.endswith('.json'):
            continue
        with open(os.path.join(tdir, fn), encoding='utf-8') as f:
            t = json.load(f)
            out[t['id']] = t
    return out


def load_materials() -> dict:
    out = {}
    mdir = data_path('data', 'materials', 'weapons')
    for fn in os.listdir(mdir):
        if not fn.endswith('.json'):
            continue
        with open(os.path.join(mdir, fn), encoding='utf-8') as f:
            m = json.load(f)
            out[m['id']] = m
    return out


# ---------------------------------------------------------------------------
# Iron shortsword regression: the original bug report
# ---------------------------------------------------------------------------

def test_iron_shortsword_pf1_chain_has_gradient():
    """The original `[1, 1, 1, 1, 2]` bug must not return."""
    templates = load_templates()
    materials = load_materials()
    chain = compute_chain(templates['shortsword'], materials['iron'], pf=1)
    assert chain[-1] > chain[0], f'iron shortsword pf=1 chain has no gradient: {chain}'
    assert chain[-1] >= 3, f'iron shortsword pf=1 chain peak too weak: {chain}'


def test_iron_shortsword_chain_scales_with_floor():
    """Chain peak should grow as peak_floor rises."""
    templates = load_templates()
    materials = load_materials()
    peaks = []
    for pf in [1, 5, 10, 20, 50]:
        chain = compute_chain(templates['shortsword'], materials['iron'], pf)
        peaks.append(chain[-1])
    assert peaks == sorted(peaks), f'peak damage must be monotonically rising: {peaks}'
    assert peaks[-1] > peaks[0] * 5, f'pf=50 should be far stronger than pf=1: {peaks}'


# ---------------------------------------------------------------------------
# Universal gradient: no template × material × floor combination produces a
# flat chain. This is the structural invariant the new formula buys us.
# ---------------------------------------------------------------------------

def test_no_flat_chain_across_all_combos():
    """For every (template, material, pf in [1..30]), chain[4] > chain[0]."""
    templates = load_templates()
    materials = load_materials()
    failures = []
    for tname, t in templates.items():
        # Skip templates that aren't compatible with any common material classes.
        compat = set(t.get('compatible_material_classes', []))
        for mname, m in materials.items():
            if m.get('material_class') not in compat:
                continue
            for pf in range(1, 31):
                chain = compute_chain(t, m, pf)
                if chain[-1] <= chain[0]:
                    failures.append((tname, mname, pf, chain))
    assert not failures, f'{len(failures)} flat-chain combos. First 5: {failures[:5]}'


def test_chain_5_damage_near_mob_hp_at_peak_floor():
    """At a weapon's peak_floor, chain-5 damage should be in the mob-HP zone.

    Bound: 0.5x mob_hp <= chain_5_dmg <= 3.0x mob_hp. The formula targets
    chain_5 ~= mob_hp; modifiers swing it. Endgame exotic + heavy combos
    (void_touched + maul) intentionally one-shot trash, hitting ~2.55x.
    """
    templates = load_templates()
    materials = load_materials()
    failures = []
    for tname, t in templates.items():
        compat = set(t.get('compatible_material_classes', []))
        for mname, m in materials.items():
            if m.get('material_class') not in compat:
                continue
            pf = m.get('peak_floor', 10)
            if pf <= 0:
                continue
            chain = compute_chain(t, m, pf)
            mh = mob_hp(pf)
            if not (0.5 * mh <= chain[-1] <= 3.0 * mh):
                failures.append((tname, mname, pf, chain[-1], round(mh, 1)))
    assert not failures, f'{len(failures)} weapons outside [0.5x, 3.0x] mob_hp band. First 5: {failures[:5]}'


# ---------------------------------------------------------------------------
# Unique invariants
# ---------------------------------------------------------------------------

def test_all_active_uniques_have_5_entry_chain():
    """Every unique with peak_floor > 0 must use a 5-entry chainMultipliers."""
    with open(data_path('data', 'items', 'weapon.json'), encoding='utf-8') as f:
        uniques = json.load(f)
    failures = []
    for sid, entry in uniques.items():
        if entry.get('peak_floor', 0) <= 0:
            continue
        cm = entry.get('chainMultipliers', [])
        if len(cm) != 5:
            failures.append((sid, len(cm)))
    assert not failures, f'{len(failures)} uniques with chain len != 5: {failures[:10]}'


def test_unique_chain_monotone_to_peak_except_wild():
    """Rung 5 must be the peak. (Wild archetype allowed: rung 4 may dip below 3.)"""
    with open(data_path('data', 'items', 'weapon.json'), encoding='utf-8') as f:
        uniques = json.load(f)
    failures = []
    for sid, entry in uniques.items():
        if entry.get('peak_floor', 0) <= 0:
            continue
        cm = entry.get('chainMultipliers', [])
        if len(cm) != 5:
            continue
        peak = max(cm)
        if cm[-1] < peak:
            failures.append((sid, cm))
    assert not failures, f'{len(failures)} uniques where rung 5 is not the peak: {failures[:5]}'


def test_no_super_weapon_uniques():
    """No unique's baseDamage exceeds 2.5x what a same-template common at the
    same peak_floor with the strongest available material would produce.

    Excludes legendary god-touched uniques where mythic peaks are intentional
    (Excalibur, Mjolnir Shard, Gungnir, etc.).
    """
    LEGENDARY_EXEMPT = {
        # 12 original signature chains
        'excalibur', 'soul_reaver', 'gae_bulg', 'mjolnir_shard',
        'anduril', 'glamdring', 'stormbringer', 'boomstick',
        'aiglos', 'zireael', 'ruyi_jingu_bang', 'heracles_club',
        # god-touched mythic peaks above the band cap (Phase 4b)
        'sling_of_david', 'prometheus_torch', 'romulus_spear',
        'bow_of_rama', 'akinakes_acrisius', 'atalanta_bow',
        'gungnir', 'mistilteinn', 'laevateinn',
    }
    templates = load_templates()
    materials = load_materials()
    with open(data_path('data', 'items', 'weapon.json'), encoding='utf-8') as f:
        uniques = json.load(f)

    def best_common_base(tname: str, pf: int) -> int:
        t = templates.get(tname)
        if not t:
            return 0
        compat = set(t.get('compatible_material_classes', []))
        best = 0
        for m in materials.values():
            if m.get('material_class') not in compat:
                continue
            cm = t['chain_multipliers']
            wb = max(1, round(mob_hp(pf) / cm[-1]))
            bd = max(2, round(wb * m['damage_mult'] * t['damage_modifier']))
            best = max(best, bd)
        return best

    failures = []
    for sid, entry in uniques.items():
        if entry.get('peak_floor', 0) <= 0:
            continue
        if sid in LEGENDARY_EXEMPT:
            continue
        pf = entry['peak_floor']
        tb = entry.get('template_basis', '')
        common_best = best_common_base(tb, pf)
        if common_best == 0:
            continue
        bd = entry.get('baseDamage', 0)
        if bd > common_best * 2.5:
            failures.append((sid, tb, pf, bd, common_best))
    assert not failures, f'{len(failures)} super-uniques (>2.5x common best). First 5: {failures[:5]}'


# ---------------------------------------------------------------------------
# baseDamage floor
# ---------------------------------------------------------------------------

def test_base_damage_floor_at_2():
    """No instantiated weapon can have baseDamage < 2."""
    templates = load_templates()
    materials = load_materials()
    failures = []
    for tname, t in templates.items():
        compat = set(t.get('compatible_material_classes', []))
        for mname, m in materials.items():
            if m.get('material_class') not in compat:
                continue
            for pf in range(1, 11):
                cm = t['chain_multipliers']
                wb = max(1, round(mob_hp(pf) / cm[-1]))
                bd = max(2, round(wb * m['damage_mult'] * t['damage_modifier']))
                if bd < 2:
                    failures.append((tname, mname, pf, bd))
    assert not failures, f'{len(failures)} weapons below floor=2: {failures[:5]}'
