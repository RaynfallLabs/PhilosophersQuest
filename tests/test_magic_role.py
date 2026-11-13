"""What magic is for.

Magic as a style (winning-build plan 3.6, Brandon's decision 5, 2026-11-13;
it replaced ruling D2, which held every cast under one weapon attack).
Maths stays the backbone: one science question a cast, wrong is a fizzle,
and a bar holds a few casts. Magic is the toolkit that exploits elements and
controls the fight: the best single-target spell of each tier is about one
weapon chain on a floor typical of its tier (about 1.25 for an Intelligence
build), so the right element on a x2 weakness is a two-chain blow. Area
spells sit under a bolt, a touch spell keeps a small edge, a wand charge is
about 0.85. Intelligence gives more casts and longer, wider effects, and
only a little more damage. tools/balance/magic_audit.py holds the bands.
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


def _spells():
    return [r for r in magic_audit.rows() if r['kind'] == 'spell']


def test_every_cast_sits_in_its_band():
    """No bolt over about a chain, no area spell up to one, a touch or an
    undead-only spell a little over, a wand charge under (INT 10 / build)."""
    rows = magic_audit.rows()
    assert len(rows) > 60
    assert {r['role'] for r in rows} <= set(magic_audit.BANDS) | {'share'}
    assert not magic_audit.out_of_band(rows), magic_audit.out_of_band(rows)


def test_each_tiers_best_single_target_spell_is_about_one_chain():
    lo, hi = magic_audit.BEST_SINGLE
    blo, bhi = magic_audit.BEST_BOLT
    summary = magic_audit.tier_summary()
    assert set(summary) == {1, 2, 3, 4, 5}
    builds = []
    for tier, t in summary.items():
        name, plain, mage, _cost = t['single']
        assert lo <= plain <= hi, (tier, name, plain)
        if tier in magic_audit.BOLT_TIERS:
            bname, bplain, bmage, _c = t['bolt']
            assert blo <= bplain <= bhi, (tier, bname, bplain)
            builds.append(bmage)
        # an area spell stays under the tier's best single target
        if t['area']:
            assert t['area'][1] < plain, (tier, t['area'], name)
    # "about 1.25 for an Intelligence build" (1.08 at tier 1 to 1.40 at tier 5)
    assert 1.15 <= sum(builds) / len(builds) <= 1.35, builds
    assert all(b <= magic_audit.BANDS['bolt'][1] for b in builds)


def test_magic_is_more_than_it_was_under_d2():
    """The ruling change itself: the old tables put the best spell of each
    tier near 0.7 of a chain (spells 2.6 / 5.15 / 8.6 / 12.8 / 15.7)."""
    old = {1: 2.6, 2: 5.15, 3: 8.6, 4: 12.8, 5: 15.7}
    for tier, mult in game_magic.MAGIC_TIER_MULT.items():
        assert mult >= 1.4 * old[tier], (tier, mult)
    vals = [game_magic.MAGIC_TIER_MULT[t] for t in sorted(game_magic.MAGIC_TIER_MULT)]
    assert vals == sorted(vals)


def test_a_touch_keeps_only_a_small_edge_over_the_bolt():
    """Laying hands on is a risk, so a touch spell stays at or above its
    tier's best bolt, but no longer far above it (Brandon, bug bash 3.3.2:
    "touch spells have a higher risk/reward")."""
    summary = magic_audit.tier_summary()
    touches = [r for r in _spells() if r['role'] == 'touch']
    assert {r['name'] for r in touches} == {'frost_touch', 'drain_life', 'soul_drain'}
    for r in touches:
        bolt = summary[r['tier']]['bolt']
        assert r['plain'] >= bolt[1], (r['name'], bolt)
        assert r['plain'] <= magic_audit.BANDS['touch'][0]
        assert r['mage'] <= magic_audit.BANDS['touch'][1]


def test_the_order_inside_each_family_holds():
    """Each family's higher tier hits harder than its lower one (and a
    tier's spells share one multiplier, so inside a tier the dice decide)."""
    from spells import LEARNABLE_SPELLS
    fam = {}
    for sid, s in LEARNABLE_SPELLS.items():
        mean = magic_audit.dice_mean(s.get('power'))
        if mean <= 0 or s['effect'] in ('extra_heal', 'annihilate'):
            continue
        tier = int(s['tier'])
        dmg = mean * game_magic.MAGIC_TIER_MULT[tier]
        fam.setdefault(s.get('spell_family'), []).append((tier, dmg, sid))
    for family, spells in fam.items():
        spells.sort()
        dmgs = [d for _t, d, _s in spells]
        assert dmgs == sorted(dmgs), (family, spells)


def test_the_audit_reads_dice_exactly():
    m = magic_audit.dice_mean
    assert m('3d6') == 10.5 and m('7d8+1') == 32.5 and m('1d4-1') == 1.5
    assert m('') == 0.0 and m('30') == 0.0 and m(None) == 0.0
    r = magic_audit.role_of
    assert r('fire_bolt', None) == 'bolt' and r('aard_blast', 3) == 'bolt'
    assert r('frost_touch', 1) == 'touch' and r('frost_touch', None) == 'bolt'
    assert r('mass_fire') == 'area' and r('chain_lightning_jump') == 'area'
    assert r('turn_undead') == 'undead' and r('annihilate') == 'share'
    assert r('smite', 3) == 'bolt'           # Holy fire strikes anything
    assert r('turn_undead', kind='wand') == 'wand_undead' and r('striking', kind='wand') == 'wand'


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
    # Magic missile reckons the volley's rolls in one call (bug bash 3.3.1,
    # so the Heart of Ahriman's charge is the whole volley's) and shares it:
    # sum/missiles**2 is the old f(roll)/missiles per missile.
    assert 'self._spell_damage(sum(_rolls), chain) // (missiles * missiles)' in src
    assert 'self._spell_damage(base_dmg, chain) // shots' in src
