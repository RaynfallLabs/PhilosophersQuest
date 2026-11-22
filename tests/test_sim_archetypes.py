"""Many ways to win: the simulator's archetypes and part 1's rulings as knobs
(tools/balance/sim_archetypes.py, sim_ranger.py, sim_pets.py; 2026-11-21,
ARCHETYPES_AND_CALLINGS_2026_11_21.md).

Every knob's default is the game as it is, and a default cell is the one
before the hooks. These tests hold that, and that each ruling changes what it
says: PER on a shot, WIS on a heal without the depth's gift, the clock's
limit, fury in light armour alone, light coatings, pets that are fed and die.
"""
import copy
import os
import sys
import types

import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
os.environ.setdefault('PQ_NO_BONES', '1')


@pytest.fixture(autouse=True)
def _as_the_game():
    """sim_archetypes.install wraps combat.strike_damage: never left behind."""
    import combat
    real = combat.strike_damage
    yield
    combat.strike_damage = real


ALL_ON = {'ar_per': 0.03, 'fu_on': 1, 'dx_finesse': 1, 'st_lean': 1}


def _run(profile='mastery', knobs=''):
    import difficulty_sim as ds
    run = ds.Run(ds.FloorCache(1), profile, 0.95, 1.0, 'greedy', 1, ds.parse_knobs(knobs))
    run.fs = ds.new_floor_stats()
    run.floor = 30
    return run


def _foe(kind='ogre', **kw):
    import json
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        m = Monster({**json.load(f)[kind], 'id': kind}, 6, 5)
    m.max_hp = m.hp = 10 ** 7
    m.resistances, m.weaknesses = [], []
    m._sim_away = 0
    m._sim_attacks = 0
    for key, v in kw.items():
        setattr(m, key, v)
    return m


def _bow(mechanic='armor_pierce_at_max', base=1000):
    import items
    bow = copy.copy(items.instantiate_weapon('longbow', 'oak'))
    bow.base_damage = base
    bow.class_mechanic = mechanic
    bow.damage_types = ['pierce']
    return bow


def _shot(run, bow, chain=2):
    import combat
    run.p.ranged_weapon = bow
    return combat.strike_damage(run.p, _foe(), chain, ranged=True, weapon=bow)


def _wear(run, weight_class):
    import items
    piece = types.SimpleNamespace(slot='body', weight_class=weight_class, weight=1.0)
    run.p.armor_slots[items.ARMOR_SLOTS.index('body')] = piece


# ------------------------------------------------------------------ defaults
def test_every_knob_is_in_the_simulator_and_is_the_game():
    import combat
    import difficulty_sim as ds
    import sim_archetypes as sa
    for k, v in sa.KNOBS.items():
        assert ds.KNOB_DEFAULTS[k] == v
    for k in ('cl_wis', 'cl_wis_cap', 'cl_wards', 'cl_mp_wis', 'fu_on', 'fu_tough', 'dx_finesse',
              'ar_bow', 'ar_per', 'ar_recover', 'ar_fletch', 'ar_stall', 'ar_heads',
              'pt_hp', 'pt_feed', 'pt_lv', 'pt_per', 'pt_full', 'pt_know', 'st_lean', 'kt_even', 'kt_lean', 'ar_draw'):
        assert not sa.KNOBS[k], k
    assert sa.KNOBS['la_wt'] == 1.0
    assert sa.BERSERK == sa.KNOBS['fu_dmg'] == 1.3
    assert combat.RANGED_STAT_SHARE == 0.03


def test_at_the_defaults_every_hook_answers_as_the_game():
    import pet_system
    import sim_archetypes as sa
    import sim_magic
    import sim_pets
    import sim_ranger
    run = _run()
    p = run.p
    p.STR, p.INT, p.WIS = 25, 22, 31
    assert sa.heal_factor(run) == sim_magic.int_factor(run)
    assert sa.wis_step(run) == 1.0
    assert sa.str_factor(run, p.weapon) == 1.0 + 15 * 0.03
    assert sa.clock_excess(p) == 0 and sa.stat_for_cap(p, 'WIS') == 'WIS'
    assert sa.incoming(p, 77) == 77
    assert sim_pets.bite(run) == pet_system.growth('bite', run.floor)
    assert sim_pets.here(run) and sim_pets.quest_line(run)
    assert sim_ranger.main_weapon(run) is p.weapon
    assert not sim_ranger.will_shoot(run, _foe())
    assert not sim_ranger.spares(run) and not sim_ranger.ammo_pack(run)


def test_the_default_cell_is_the_one_before_the_archetype_hooks(monkeypatch):
    import difficulty_sim as ds
    import pet_system
    import sim_archetypes as sa
    import sim_magic
    import sim_pets
    import sim_ranger

    def cell():
        return ds.run_cell(profile='mastery', accuracy=0.95, trials=1, floors=(1, 4),
                           knobs=ds.parse_knobs(''), speed=1.2, engagers=2, seed=5, variants=1)
    a = cell()
    none = lambda *x, **y: None         # noqa: E731
    no = lambda *x, **y: False          # noqa: E731
    old = {
        sa: dict(install=none, install_kitchen=none, lean_dish=lambda run, ready: ready, learn=no, ward=no, fight_start=none, fight_end=none, call_fury=none,
                 floor_start=none, floor_end=none, sync_mp=none, light_answers=none,
                 heal_factor=sim_magic.int_factor, wis_step=lambda run: 1.0,
                 incoming=lambda p, amount: amount, stat_for_cap=lambda p, stat: stat,
                 clock_excess=lambda p: 0, clock_wis=lambda p: p.WIS,
                 str_factor=lambda run, w: 1.0 + max(0, run.p.STR - 10) * 0.03),
        sim_ranger: dict(volley=no, will_shoot=no, kited=no, coat_bow=no, shop=none,
                         on_kill=none, on_harvest=none, consider_bow=no,
                         consider_ammo=no, spares=lambda run: [], ammo_pack=lambda run: [],
                         kit_blow=lambda run, v: v, best_blow=lambda run, t, v: v,
                         main_weapon=lambda run: run.p.weapon),
        sim_pets: dict(here=lambda run: True, quest_line=lambda run: True, bit=none, recall=no,
                       swipes=none, feed=no,
                       bite=lambda run, foe=None: (pet_system.growth('bite', run.floor)
                                         * sim_magic.pet_bite_mult(run))),
    }
    for mod, fns in old.items():
        for name, fn in fns.items():
            monkeypatch.setattr(mod, name, fn)
    b = cell()
    assert a['stats'] == b['stats']


def test_the_profiles_lean_on_what_they_are_named_for():
    import difficulty_sim as ds
    P = ds.PROFILES
    for a in ('fighter', 'tank', 'mage', 'rogue', 'ranger', 'cleric', 'barbarian', 'beast'):
        assert P['arch_' + a]['arch']
        cook = P[f'arch_{a}_cook']['knobs']
        assert not cook['families'] and not cook['tactics']
    for k, v in P['mastery'].items():
        assert P['arch_fighter'][k] == v
    assert P['arch_ranger']['stat_focus'] == ('PER', 'DEX') and P['arch_ranger']['knobs']['ar_bow']
    assert not P['arch_ranger_nolean']['knobs']['ar_bow']
    assert P['arch_cleric']['stat_focus'][0] == 'WIS' and P['arch_cleric']['armour_class'] == ('light', 'medium')
    assert P['arch_barbarian']['fury'] and not P['arch_barbarian_nolean']['fury']
    assert P['arch_beast']['beast'] and not P['arch_beast_nolean']['beast']
    assert 'ar_bow' not in P['mastery']['knobs'] and 'cl_wards' not in P['mastery']['knobs']


# ---------------------------------------------------------------- R1, the bow
def test_r1_per_pays_a_shot_as_str_pays_the_sword_and_str_pays_it_nothing():
    import sim_archetypes as sa
    sa.install(ALL_ON)
    run = _run('arch_ranger', 'ar_per=0.03')
    bow = _bow()
    run.p.PER, run.p.STR = 10, 10
    plain = _shot(run, bow)
    run.p.PER, run.p.STR = 30, 30
    assert abs(_shot(run, bow) - plain * 1.6) <= 1
    composite = _bow('str_bonus_range_7')
    run.p.PER, run.p.STR = 20, 30
    assert abs(_shot(run, composite) - plain * 1.6) <= 1        # the better, never both
    assert (run.p.PER, run.p.STR) == (20, 30)                   # nothing left changed


def test_r1_without_the_ruling_a_shot_is_the_games():
    import combat
    import sim_archetypes as sa
    real = combat.strike_damage
    run = _run('arch_ranger')
    run.p.PER, run.p.STR = 34, 18
    bow = _bow()
    game = real(run.p, _foe(), 2, ranged=True, weapon=bow)
    sa.install(ALL_ON)
    assert _shot(run, bow) == game


def test_r1_arrowheads_carry_a_coating_into_the_shot_and_spend_it():
    import combat
    import items
    import sim_ranger
    run = _run('arch_ranger', 'ar_heads=1')
    bow = _bow()
    run.p.ranged_weapon = bow
    sim_ranger.add_ammo(run, 'iron_arrow', 5)
    foe = _foe('zombie', weaknesses=['holy'], tags=[])
    plain = combat.strike_damage(run.p, foe, 2, ranged=True, weapon=bow)
    water = items.make_item_by_id('flask', 'flask_of_holy_water')
    run.flasks = [copy.copy(water)]
    run._knows = lambda kind: True
    run.p.weapon = None
    run._coat_for(foe)
    assert bow.coating['substance'] == 'holy' and not run.flasks and run.p.weapon is None
    assert combat.strike_damage(run.p, foe, 2, ranged=True, weapon=bow) > plain * 1.5
    blows = bow.coating['blows']
    run.quiz.start_quiz = lambda **kw: kw['callback'](types.SimpleNamespace(score=2, struck_early=False))
    sim_ranger.shoot(run, foe, [foe])
    assert bow.coating['blows'] < blows


def test_a_lean_pays_a_blow_only_by_the_dial_and_never_stacks():
    import sim_archetypes as sa
    blade = types.SimpleNamespace(class_mechanic='')
    for knobs, stat in (('', 20), ('st_lean=1', 30)):
        run = _run('arch_rogue', knobs)
        run.p.STR, run.p.DEX = 20, 30
        assert sa.blow_stat(run, blade) == stat
    fighter = _run('arch_fighter', 'st_lean=1')
    fighter.p.STR, fighter.p.CON = 20, 40
    assert sa.blow_stat(fighter, blade) == 20


def test_r1_the_weakest_arrow_goes_first_and_a_shot_spends_one():
    import sim_ranger
    run = _run('arch_ranger')
    run.p.ranged_weapon = _bow()
    sim_ranger.add_ammo(run, 'dragonbone_arrow', 5)
    sim_ranger.add_ammo(run, 'iron_arrow', 2)
    assert sim_ranger.next_ammo(run, run.p.ranged_weapon)[0] == 'iron_arrow'
    sim_ranger.shoot(run, _foe(), [])
    assert run._ranger['ammo'] == {'dragonbone_arrow': 5, 'iron_arrow': 1}


def test_r1_arrows_are_found_again_only_by_the_ruling_and_the_winner():
    import sim_ranger
    for knobs, result, left in (('', 'won', 0), ('ar_recover=1', 'fled', 0), ('ar_recover=1', 'won', 4)):
        run = _run('arch_ranger', knobs)
        run.p.ranged_weapon = _bow()
        sim_ranger.add_ammo(run, 'iron_arrow', 4)
        sim_ranger.fight_start(run)
        for _ in range(4):
            sim_ranger.shoot(run, _foe(), [])
        sim_ranger.fight_end(run, result)
        assert run._ranger['ammo']['iron_arrow'] == left


def test_r1_first_shots_need_room_to_shoot():
    import sim_ranger
    run = _run('arch_ranger')
    run.p.ranged_weapon = _bow()
    assert sim_ranger._shots_before_contact(run, [_foe(ai_pattern='ambush')], 7) == 0
    assert sim_ranger._shots_before_contact(run, [_foe(ai_pattern='aggressive', speed=16)], 7) == 0
    assert sim_ranger._shots_before_contact(run, [_foe(ai_pattern='aggressive', speed=10)], 1) == 0
    assert sim_ranger._shots_before_contact(run, [_foe(ai_pattern='aggressive', speed=10)], 5) >= 1


# ------------------------------------------------------------- R2, the cleric
def test_r2_the_depths_gift_grows_no_heal_and_learned_wis_does():
    import sim_archetypes as sa
    run = _run('arch_cleric', 'cl_wis=0.03')
    p = run.p
    p.learn_from_depth(0, 90)
    p.deepest_floor_reached = 90
    assert p.WIS == p.stats_at_start['WIS'] + 30
    assert sa.wis_lean(p) == 0 and sa.wis_step(run) == 1.0
    p.apply_stat_bonus('WIS', 20)
    assert abs(sa.wis_step(run) - 1.6) < 1e-9
    p.INT = 40
    assert abs(sa.heal_factor(run) - 3.2) < 1e-9        # INT no longer feeds it


def test_r2_the_food_cap_rises_and_the_clock_keeps_todays_longest():
    today = _run('arch_cleric')
    ruled = _run('arch_cleric', 'cl_wis_cap=1')
    assert today.p.stat_cap_for_tier('WIS', 5) == 14
    assert ruled.p.stat_cap_for_tier('WIS', 5) == ruled.p.stat_cap_for_tier('STR', 5) == 28
    for run, taught in ((today, 14), (ruled, 28)):
        run.p.deepest_floor_reached = 95
        run.p.cooking_stat_gained['WIS'] = taught
        run.p.apply_stat_bonus('WIS', taught)
    assert ruled.p.WIS == today.p.WIS + 14
    assert ruled.p.get_quiz_timer('math') == today.p.get_quiz_timer('math')


def test_r2_a_ward_is_the_games_shielded_and_only_a_caster_of_it_has_it():
    import difficulty_sim as ds
    import sim_archetypes as sa
    run = _run('arch_cleric')
    run.quiz.one_question = lambda *a, **k: True
    book = types.SimpleNamespace(spell_id='mage_armor_spell', quiz_tier=1)
    assert sa.learn(run, book)
    run.p.mp = run.p.max_mp = 50
    foe = _foe()
    assert sa.ward(run, [foe], [])
    assert run.p.has_effect('shielded') and run.p.mp < 50
    assert not sa.learn(_run('mastery'), book)
    assert sa.learn(run, types.SimpleNamespace(spell_id='fire_bolt_spell', quiz_tier=1))      # not his school
    assert 'mage_armor_spell' in ds.SPELLS


# ---------------------------------------------------------- R3, the barbarian
def test_r3_fury_comes_only_in_light_armour_and_only_when_ruled():
    import sim_archetypes as sa
    for knobs, armour, furious in (('', 'light', False), ('fu_on=1', 'heavy', False),
                                   ('fu_on=1', 'medium', False), ('fu_on=1', 'light', True)):
        run = _run('arch_barbarian', knobs)
        _wear(run, armour)
        sa.call_fury(run)
        assert sa.furious(run) is furious
    other = _run('mastery', 'fu_on=1')
    _wear(other, 'light')
    sa.call_fury(other)
    assert not sa.furious(other)


def test_r3_fury_hits_harder_hurts_less_and_replaces_berserk():
    import combat
    import sim_archetypes as sa
    sa.install(ALL_ON)
    run = _run('arch_barbarian', 'fu_on=1,fu_dmg=1.5,fu_tough=0.25')
    _wear(run, 'light')
    p = run.p
    blade = _bow()
    blade.requires_ammo = None
    plain = combat.strike_damage(p, _foe(), 2, weapon=blade)
    sa.call_fury(run)
    assert abs(combat.strike_damage(p, _foe(), 2, weapon=blade) - plain * 1.5) <= 1
    p.status_effects['berserk'] = 5
    assert abs(combat.strike_damage(p, _foe(), 2, weapon=blade) - plain * 1.5) <= 2     # no stack
    assert sa.incoming(p, 100) == 75
    run.turn += 21
    assert not sa.furious(run) and sa.incoming(p, 100) == 100


def test_r3_light_answers_weigh_less_and_never_change_the_shared_flask():
    import items
    import sim_archetypes as sa
    run = _run('arch_rogue', 'la_wt=0.25')
    oil = items.make_item_by_id('flask', 'flask_of_fire_oil')
    weight = oil.weight
    run.flasks = [oil]
    sa.light_answers(run)
    sa.light_answers(run)                       # once is all
    assert oil.weight == weight and run.flasks[0].weight == weight * 0.25


def test_finesse_reads_dex_only_when_the_dial_is_on():
    import combat
    import sim_archetypes as sa
    sa.install(ALL_ON)
    blade = _bow('finesse_dex')
    blade.requires_ammo = None
    game, fixed = _run(), _run(knobs='dx_finesse=1')
    for run in (game, fixed):
        run.p.STR, run.p.DEX = 10, 30
    base = combat.strike_damage(game.p, _foe(), 2, weapon=blade)
    assert abs(combat.strike_damage(fixed.p, _foe(), 2, weapon=blade) - base * 1.6) <= 1
    assert fixed.p.STR == 10


# ------------------------------------------------------------------ R4, pets
def test_r4_a_pet_is_killed_is_replaced_and_loses_what_it_was_fed():
    import sim_pets
    run = _run('arch_beast', 'pt_hp=1,pt_feed=1,pt_back=3')
    run.floor = 20
    s = sim_pets.state(run)
    s['fed'] = 6
    foe = _foe(attacks=[{'damage': '900d2', 'type': 'slash'}])
    sim_pets.bit(run, foe)
    sim_pets.swipes(run, [foe])
    assert not sim_pets.here(run) and s['fed'] == 0 and not sim_pets.quest_line(run)
    run.floor = 22
    sim_pets.floor_start(run)
    assert not sim_pets.here(run)
    run.floor = 23
    sim_pets.floor_start(run)
    assert sim_pets.here(run) and sim_pets.level(run) == 1


def test_r4_a_careful_owner_recalls_a_hurt_pet_and_feeds_it_between_fights():
    import sim_pets
    run = _run('arch_beast', 'pt_hp=1')
    top = sim_pets.max_health(run)
    s = sim_pets.state(run)
    assert not sim_pets.recall(run)                 # unhurt, it stays out
    s['hurt'] = 0.6 * top
    assert sim_pets.recall(run) and not sim_pets.here(run) and sim_pets.alive(run)
    sim_pets.swipes(run, [_foe(attacks=[{'damage': '900d2', 'type': 'slash'}])])
    assert sim_pets.alive(run)                      # safe in its sphere
    parts = [types.SimpleNamespace(sp_restore=60) for _ in range(17)]
    run.pantry, run.food = list(parts), []
    run._spares = lambda: [parts[-1]]
    run.p.hp = 1                                    # hurt himself: his meals come first
    sim_pets.fight_end(run)
    assert sim_pets.here(run) and len(run.pantry) == 17
    run.p.hp = run.p.max_hp
    sim_pets.fight_end(run)
    assert len(run.pantry) == 16 and s['hurt'] < 0.4 * top


def test_r4_the_mooble_sits_the_fight_out():
    import sim_pets
    run = _run('arch_mage', 'pt_hp=1')
    run.floor = 50
    sim_pets.fight_start(run)
    assert not sim_pets.here(run) and run._quest_pet() == 'mooble'     # his mana still his
    sim_pets.fight_end(run)
    assert sim_pets.here(run)


def test_r4_a_pet_never_dies_without_the_knob():
    import sim_pets
    run = _run('arch_beast', 'pt_feed=1')
    foe = _foe(attacks=[{'damage': '900d2', 'type': 'slash'}])
    sim_pets.bit(run, foe)
    sim_pets.swipes(run, [foe])
    assert sim_pets.here(run)


def test_r4_a_raised_pet_hunts_only_known_quarry_by_the_dial():
    import sim_pets
    for knobs, knows, grows in (('', False, True), (',pt_know=1', False, False), (',pt_know=1', True, True)):
        run = _run('arch_beast', 'pt_feed=1,pt_full=0.5' + knobs)
        run.floor = 50
        plain = sim_pets.bite(run, _foe())
        sim_pets.state(run)['fed'] = 20
        run._knows = lambda kind, _k=knows: _k
        assert (sim_pets.bite(run, _foe()) > plain) is grows


def test_r4_feeding_grows_the_bite_the_level_and_the_health():
    import sim_pets
    run = _run('arch_beast', 'pt_hp=1,pt_feed=1,pt_lv=1,pt_per=0.03,pt_full=0.5')
    run.floor = 50
    bite, health = sim_pets.bite(run), sim_pets.max_health(run)
    sim_pets.state(run)['fed'] = sim_pets.food_cap()
    assert sim_pets.level(run) == 50 + sim_pets.food_cap()
    assert sim_pets.bite(run) > bite and sim_pets.max_health(run) > health * 1.8


def test_the_even_kitchen_trades_the_leans_dishes_with_strs_and_puts_them_back():
    import kitchen
    import sim_archetypes as sa

    def dishes():
        out = {}
        for rec in kitchen.book():
            out.setdefault(rec.get('benefit'), set()).add(rec['id'])
        return out
    was = dishes()
    try:
        sa.install_kitchen({'kt_even': 1}, {'stat_focus': ('PER', 'DEX')})
        now = dishes()
        assert now['PER'] == was['STR'] and now['STR'] == was['PER'] and now['DEX'] == was['DEX']
    finally:
        sa.install_kitchen({}, {})
    assert dishes() == was
    assert sa.lean_swap({'kt_even': 1}, {'stat_focus': ('STR', 'CON')}) is None


def test_the_lean_is_always_cookable_only_by_its_dial():
    import kitchen
    import sim_archetypes as sa
    dish = next(r for r in kitchen.book() if r.get('benefit') == 'STR' and kitchen.dish_size(r) == 1)
    assert sa.lean_dish(_run('arch_cleric'), [dish]) == [dish]
    run = _run('arch_cleric', 'kt_lean=1')
    got = sa.lean_dish(run, [dish])
    assert got[0]['benefit'] == 'WIS' and got[1] is dish and dish['benefit'] == 'STR'


def test_the_strike_hook_is_put_back_when_no_knob_needs_it():
    import combat
    import sim_archetypes as sa
    sa.install({})
    real = combat.strike_damage
    sa.install(ALL_ON)
    sa.install(ALL_ON)                          # never twice over
    assert combat.strike_damage.__wrapped__ is real
    sa.install({})
    assert combat.strike_damage is real
