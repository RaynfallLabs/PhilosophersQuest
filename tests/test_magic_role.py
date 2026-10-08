"""Phase 3 of the rebalance (2026-10): what magic is for.

Decision D2: magic changes the shape of a fight and never replaces maths.
One cast, for one science question and no clock, must land under one
weapon attack on the floors it is found on. Intelligence gives more casts
and longer, wider effects, not a bigger number.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import game_magic  # noqa: E402
import magic_audit  # noqa: E402


def _is_conditional(kind, name):
    """Effects that only bite one kind of foe may hit harder."""
    if kind == 'spell':
        from spells import LEARNABLE_SPELLS
        eff = (LEARNABLE_SPELLS.get(name + '_spell') or LEARNABLE_SPELLS[name])['effect']
    else:
        import json
        with open(os.path.join(ROOT, 'data', 'items', 'wand.json'), encoding='utf-8') as f:
            eff = json.load(f)[name].get('effect')
    return any(c in str(eff) for c in magic_audit.CONDITIONAL)


def test_no_single_target_cast_out_hits_a_weapon_chain():
    rows = magic_audit.rows()
    assert len(rows) > 60
    over = []
    for kind, name, tier, cost, area, plain, mage, _extra in rows:
        if _is_conditional(kind, name):
            limit_plain, limit_build = 1.1, 1.35         # the undead only
        elif kind == 'wand':
            limit_plain, limit_build = 0.92, 1.12        # a charge, not a spell
        else:
            limit_plain, limit_build = 0.80, 1.02
        if plain > limit_plain or mage > limit_build:
            over.append((kind, name, round(plain, 2), round(mage, 2)))
    assert not over, over


def test_magic_still_does_something():
    """Capped, not gutted: the best bolt of each tier is worth more than
    half a weapon attack, or nobody would cast it."""
    best = {}
    for kind, name, tier, cost, area, plain, mage, _extra in magic_audit.rows():
        if kind == 'spell' and not area:
            best[tier] = max(best.get(tier, 0.0), plain)
    assert set(best) == {1, 2, 3, 4, 5}
    assert all(v >= 0.6 for v in best.values()), best


def test_intelligence_adds_little_to_damage_and_much_to_reach():
    f = game_magic.int_damage_factor
    assert f(10) == 2.0                                  # unchanged for a plain character
    assert f(20) == 2.0 * 1.15
    assert f(100) == 2.0 * game_magic.INT_DAMAGE_CAP <= 2.8
    assert f(1) >= 1.4                                   # a dull wit is not a zero
    r = game_magic.int_reach
    assert r(10) == 1.0 and abs(r(20) - 1.3) < 1e-9
    assert r(200) == game_magic.INT_REACH_CAP == 1.75
    assert r(3) == 0.85


def test_spells_use_the_reach_rule_for_how_long_they_last():
    src = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    assert 'chain_scale = int_reach(self.player.INT)' in src
    assert 'self.player.INT * 0.1' not in src
    main = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    assert 'self.player.INT * 0.1' not in main


def test_named_foes_cannot_be_ended_or_locked_down_by_magic():
    import monster
    assert monster.NAMED_FOE_CONTROL_CAP <= 3
    boss = type('M', (), {'is_boss': True, 'is_mini_boss': False, 'is_seal_demon': False,
                          'max_hp': 9000, 'peak_floor': 20})()
    assert game_magic._is_big_foe(boss)
    # a "third of its health" effect is capped at about half a typical
    # monster's health on that floor
    import floor_curve
    assert game_magic._big_foe_bite(boss, 1 / 3, 20) <= 0.5 * floor_curve.target_hp(20) + 1


def test_lucky_stat_points_have_one_allowance_for_the_run():
    """A wish, a fountain, a throne and a scroll of great power each gave
    '+1, no limit'; the wish is a spell castable on every floor."""
    from player import Player
    p = Player()
    assert p.fortune_stat_room() == 3
    got = sum(p.gain_fortune_stat('STR', 1) for _ in range(10))
    assert got == 3 and p.STR == 13 and p.fortune_stat_room() == 0
    assert p.gain_fortune_stat('CON', 2) == 0 and p.CON == 10
    p.deepest_floor_reached = 100
    assert p.fortune_stat_room() == 13 - 3
    src = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    i = src.rindex("if effect == 'wish':")                 # the spell, not the wand
    assert 'gain_fortune_stat(stat, 1)' in src[i:i + 2500]
    assert "kind = 'strong_buff'" in src[i:i + 1200]
    div = open(os.path.join(ROOT, 'src', 'game_divine.py'), encoding='utf-8').read()
    assert div.count('gain_fortune_stat(') == 2            # fountain and throne


def test_deep_slumber_and_mass_paralyze_are_different_spells():
    from spells import LEARNABLE_SPELLS as S
    assert S['deep_slumber_spell']['spell_family'] == 'sleep'
    assert S['mass_paralyze_spell']['spell_family'] == 'paralyze'
    assert 'sleep' in S['deep_slumber_spell']['desc'] and 'paraly' not in S['deep_slumber_spell']['desc']
    src = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    i = src.index("Deep Slumber and Mass")
    block = src[i:i + 1200]
    assert "spell.get('spell_family') == 'paralyze'" in block and "'sleeping', (20 if" in block


def test_a_multi_hit_spell_shares_one_casts_damage_between_its_hits():
    """Each missile used to carry the whole cast: Force Storm's seven were
    2.2 weapon attacks while the audit, counting one, said 0.31."""
    src = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    assert 'self._spell_damage(base_dmg, chain) // missiles' in src
    assert 'self._spell_damage(base_dmg, chain) // shots' in src
