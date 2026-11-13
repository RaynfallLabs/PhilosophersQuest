"""Tests for the chain damage gradient and the common weapons' curve.

Established 2026-05-18 after the iron-shortsword `[1, 1, 1, 1, 2]` problem;
re-based 2026-11-12 on the weapon curve (tools/balance/weapon_curve.py,
WEAPON_TIER_AUDIT_2026_11_12.md). These used to re-derive the old formula
(mob_hp(peak_floor) / chain_5_mult x a flat step per tier) inside the test;
they now ask the game's own weapons.

Rules:
  - A common weapon's base is its material's baked `weapon_base` (a
    longsword's), scaled to the template; never below 2.
  - Its chain climbs: chain^1.15 times the base, from chain 1 to 5.
  - A longsword on its material's peak floor kills the median monster of
    that floor in about weapon_curve.target_attacks chains for the balance
    child (a material's damage_mult moves it within its tier).
  - All active uniques (peak_floor > 0) use exactly 5-entry chainMultipliers.
  - No unique does more than 2.5x the best same-template common that can be
    found by its peak floor, for the balance child (base x the child's chain at
    each one's tier: a tier-2 unique's bigger base pays for harder sums), the
    legendary god-touched ones exempt.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools', 'balance'))

import pytest  # noqa: E402

import items  # noqa: E402
from paths import data_path  # noqa: E402


def _chain(w) -> list:
    exp = getattr(w, 'chain_exponent', None) or 1.15
    return [max(1, round(w.base_damage * c ** exp)) for c in range(1, 6)]


def _combos():
    for tid, t in items.load_templates('weapons').items():
        compat = set(t.get('compatible_material_classes', []))
        for mid, m in items.load_materials('weapons').items():
            if m.get('material_class') not in compat:
                continue
            try:
                yield tid, mid, items.instantiate_weapon(tid, mid)
            except ValueError:
                continue


# ---------------------------------------------------------------------------
# Iron shortsword regression: the original bug report
# ---------------------------------------------------------------------------

def test_iron_shortsword_chain_has_gradient():
    """The original `[1, 1, 1, 1, 2]` bug must not return."""
    chain = _chain(items.instantiate_weapon('shortsword', 'iron'))
    assert chain == sorted(chain) and chain[-1] > chain[0], chain
    assert chain[-1] >= 15, f'iron shortsword chain peak too weak: {chain}'


def test_no_flat_chain_and_no_base_below_two():
    flat, low, n = [], [], 0
    for tid, mid, w in _combos():
        n += 1
        c = _chain(w)
        if c[-1] <= c[0]:
            flat.append((tid, mid, c))
        if w.base_damage < 2:
            low.append((tid, mid, w.base_damage))
    assert n > 300
    assert not flat, flat[:5]
    assert not low, low[:5]


# ---------------------------------------------------------------------------
# The curve (2026-11-12)
# ---------------------------------------------------------------------------

def test_every_material_carries_its_baked_base_and_first_floor():
    import weapon_curve
    for mid, m in items.load_materials('weapons').items():
        assert float(m.get('weapon_base', 0)) >= 2, mid
        assert int(m['min_level']) >= int(m['peak_floor']) - weapon_curve.LEAD, mid
    assert not hasattr(items, 'TIER_DAMAGE_STEP')        # the flat step per tier is gone


def test_templates_keep_their_place_against_the_longsword():
    ls = items.instantiate_weapon('longsword', 'steel').base_damage
    assert items.instantiate_weapon('dagger', 'steel').base_damage < ls
    assert items.instantiate_weapon('greatsword', 'steel').base_damage > ls


@pytest.fixture(scope='module')
def curve():
    import weapon_curve
    weapon_curve.TRIALS = 4000
    return weapon_curve


def test_an_on_peak_longsword_kills_in_about_its_target_chains(curve):
    off = []
    for mid, m in items.load_materials('weapons').items():
        pf = int(m['peak_floor'])
        t = items.material_tier(m)
        # the baked number itself: a base of 2 or 3 is mostly rounding
        hits = curve.monster_curve()[min(100, pf)] / (float(m['weapon_base']) * curve.child_mult(t, pf))
        want = curve.target_attacks(pf)
        if not 0.6 * want <= hits <= 1.6 * want:
            off.append((mid, pf, round(hits, 2), round(want, 2)))
    assert not off, off


def test_the_baked_numbers_are_the_tools_numbers(curve):
    """--write was run after the last change to the curve's rules."""
    import weapon_curve
    weapon_curve.TRIALS = 20000                           # the --write setting
    mats = items.load_materials('weapons')
    sample = ('copper', 'iron', 'steel', 'ash', 'ironwood', 'mithril', 'soulsteel',
              'adamantine', 'titanforged', 'sunsteel', 'void_touched')
    for mid in sample:
        m = mats[mid]
        wb, first = weapon_curve.material_curve(mid)
        assert abs(float(m['weapon_base']) - wb) <= max(0.25, 0.02 * wb), (mid, m['weapon_base'], wb)
        assert int(m['min_level']) == first, (mid, m['min_level'], first)


def test_an_old_saves_common_weapon_takes_todays_base():
    import types
    from main import Game
    w = items.instantiate_weapon('longsword', 'steel')
    today = w.base_damage
    w.base_damage = 3                                     # as an old save made it
    g = types.SimpleNamespace(player=types.SimpleNamespace(
        inventory=[w], weapon=None, ranged_weapon=None, shield=None, armor_slots=[],
        accessory_slots=[]))
    Game._migrate_recompose_composite_items(g, {})
    assert w.base_damage == today


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


def test_no_super_weapon_uniques(curve):
    """No unique does more than 2.5x the best same-template common that can
    be found by its peak floor, for the balance child.

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
    templates = items.load_templates('weapons')
    materials = items.load_materials('weapons')
    with open(data_path('data', 'items', 'weapon.json'), encoding='utf-8') as f:
        uniques = json.load(f)

    def best_common_base(tname: str, pf: int) -> int:
        t = templates.get(tname)
        if not t:
            return 0
        compat = set(t.get('compatible_material_classes', []))
        best = 0.0
        for mid, m in materials.items():
            if m.get('material_class') not in compat or int(m.get('min_level', 1)) > pf:
                continue
            best = max(best, items.weapon_base_damage(t, m) * curve.child_mult(items.material_tier(m), pf))
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
        tier = int(entry.get('quiz_tier') or entry.get('tier') or 1)
        does = entry.get('baseDamage', 0) * curve.child_mult(max(1, min(5, tier)), pf)
        if does > common_best * 2.5:
            failures.append((sid, tb, pf, round(does), round(common_best)))
    assert not failures, f'{len(failures)} super-uniques (>2.5x common best). First 5: {failures[:5]}'


# ---------------------------------------------------------------------------
# Bare hands
# ---------------------------------------------------------------------------

def test_bare_hand_chain_caps_at_5_and_under_weapon_curve():
    """Regression: combat.py _DEFAULT_MULTIPLIERS (used when player has no
    weapon equipped) was 8 entries with a 5.0x peak — making bare-hand
    combat STRONGER than wielded weapons. Caught by user playtest 2026-05-19.

    Now must be 5 entries with peak strictly below any common weapon's peak.
    """
    import combat
    mults = combat._DEFAULT_MULTIPLIERS
    assert len(mults) == 5, (
        f'bare-hand chain must be capped at 5 (universal weapon cap). '
        f'Got {len(mults)} entries: {mults}'
    )
    # Peak should be weaker than the weakest weapon template
    # (shortsword peak = 2.0). Bare hand is last-resort.
    assert mults[-1] < 2.0, (
        f'bare-hand peak {mults[-1]} should be < weakest weapon peak (2.0). '
        'Otherwise unarmed > armed at chain peak.'
    )
