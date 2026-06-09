"""SP/HP/temp ladder: raw jerky < family cook < prime cook < master cook
(updated 2026-06-08).

Jerky=25, FAMILY recipes are the baseline ("low cook 50, good cook 100"), and
PRIME / dungeon / trophy / master prime-cut recipes are PREMIUM -- they must
restore more SP and HP and carry a longer temp buff (user: "meals with Prime
cuts ... should be better"). Cooking outcomes are data-driven, so this is a
data-layer test over recipes.json + ingredient.json.
"""
import json
from pathlib import Path

_ITEMS = Path(__file__).resolve().parents[1] / 'data' / 'items'
_RECIPES = json.loads((_ITEMS / 'recipes.json').read_text(encoding='utf-8'))
_INGR = json.loads((_ITEMS / 'ingredient.json').read_text(encoding='utf-8'))


def _by_class(cls):
    return [r for r in _RECIPES.values() if r.get('recipe_class') == cls]


def _t5_sp(cls):
    return {r['tier_outcomes']['5']['sp'] for r in _by_class(cls)}


def test_jerky_raw_sp_is_25():
    assert _INGR['assorted_monster_parts']['raw_sp'] == 25


def test_family_is_the_50_to_100_baseline():
    fam = _by_class('family')
    assert fam
    for r in fam:
        to = r['tier_outcomes']
        assert to['1']['sp'] == 50, r['name']      # low cook
        assert to['5']['sp'] == 100, r['name']     # good cook


def test_every_recipe_sp_is_monotonic_and_above_jerky():
    for r in _RECIPES.values():
        sps = [r['tier_outcomes'][str(t)]['sp'] for t in range(1, 6)]
        assert sps == sorted(sps), f"{r['name']} SP not monotonic: {sps}"
        assert sps[0] >= 50, f"{r['name']} T1 below the cook floor"
    # raw jerky is strictly worse than the worst successful cook
    assert _INGR['assorted_monster_parts']['raw_sp'] < 50


def test_premium_recipes_outclass_family_on_sp():
    # family=100 < prime/dungeon=116 < trophy=124 < master=132 at T5
    assert _t5_sp('family') == {100}
    assert _t5_sp('prime') == {116}
    assert _t5_sp('dungeon_keyed') == {116}
    assert _t5_sp('trophy') == {124}
    assert _t5_sp('master_prime') == {132}


def test_prime_beats_family_on_hp_and_temp_duration():
    fam = _by_class('family')
    prime = _by_class('prime')
    fam_t5_hp = {r['tier_outcomes']['5']['hp'] for r in fam}
    prime_t5_hp = {r['tier_outcomes']['5']['hp'] for r in prime}
    assert max(fam_t5_hp) < min(prime_t5_hp), "prime must restore more HP than family"
    # temp duration: every prime with a temp lasts longer than any family temp
    fam_dur = {r.get('temp_duration') for r in fam if r.get('temp_power')}
    prime_dur = {r.get('temp_duration') for r in prime if r.get('temp_power')}
    if fam_dur and prime_dur:
        assert max(fam_dur) < min(prime_dur), "prime temp must last longer than family"


def test_premium_recipes_grant_their_temp_one_tier_earlier():
    # family temp fires only at T5; premium prime-cut recipes also fire at T4
    for r in _by_class('prime'):
        if r.get('temp_power') and r['tier_outcomes']['5'].get('temp_power'):
            assert r['tier_outcomes']['4'].get('temp_power') is True, r['name']
