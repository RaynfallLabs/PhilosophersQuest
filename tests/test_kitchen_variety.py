"""Kitchen variety and hunger for 3.6.1 (Brandon, 2026-11-22: "Recipes are not
variable enough... many do EXACTLY the same thing... SP seems like an
afterthought, where it used to be a major issue and killer"; his ruling on the
nine proposals: "Hold 3.6.1 for all").

1. Each ingredient's own strength by lore (``richness``), about 1.0 a tier.
2. A side gift from every ingredient (``side``), by lore.
3. Stat dishes still teach one point, and carry their sides.
4. The gate: dishes of one tier and tab give different things.
5-8. Hunger every 3 turns; Sustained only from big SP dishes and feasts, for
   flat turns; half the SP from dishes off the SP tab; Hungry, Weak and
   Starving you can see.

Whether hunger feels right is a play-test question: Claude cannot drive
Pygame. The simulator's targets are measured in the 3.6.1 kitchen report.
"""
import collections
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pytest  # noqa: E402

import kitchen  # noqa: E402

SIDE_KINDS = {'heal', 'mp', 'regenerating', 'dark_vision', 'see_invisible', 'warning', 'searching',
              'fire_resist', 'cold_resist', 'shock_resist', 'acid_resist', 'drain_resist',
              'sleep_resist', 'fear_immune', 'save_guard_WIS', 'save_guard_DEX'}
# Poison and the body's save are the effects branch's to tune (agreed 2026-11-22).
NEVER_A_SIDE = {'poison_resist', 'save_guard_CON', 'hasted', 'shielded', 'displacement',
                'magic_resist', 'save_guard_all', 'sustained'}
STAPLES = ('bread_ration', 'dried_meat', 'hard_cheese', 'apple', 'trail_rations',
           'wild_mushroom', 'healing_herb', 'elvish_bread', 'hearty_stew')


class Hero:
    hp, max_hp, sp, max_sp, mp, max_mp = 10, 200, 20, 2000, 2, 60
    PER_FLOOR_HP_CAP = 5


def outcome_key(r):
    o = kitchen.dish_outcome(r)
    h = Hero()
    return (o['tab'], o['stat'], o['power'], o['turns'], o['ward'], kitchen.heal_amount(h, o),
            o['max_hp'], o['sp'], kitchen.mp_amount(h, o), o['sustained'], str(o['permanent']),
            tuple(o['trophy_powers']), o['song'], kitchen.makes(r), tuple(o['sides']))


def _parts_of_kind(*roles):
    return {k: v for k, v in kitchen.ingredients().items() if v['tier_role'] in roles}


# ---------------------------------------------------------------- 1. strength

def test_every_part_has_a_lore_strength_in_range():
    for k, v in _parts_of_kind('prime').items():
        assert 0.75 <= float(v['richness']) <= 1.35, (k, v.get('richness'))


@pytest.mark.parametrize('tier', range(1, 6))
def test_a_tiers_parts_average_about_one(tier):
    rs = [float(v['richness']) for v in _parts_of_kind('prime').values()
          if kitchen.band_of(int(v['min_level'])) == tier]
    assert abs(sum(rs) / len(rs) - 1.0) <= 0.03, (tier, round(sum(rs) / len(rs), 3))


def test_worth_reads_each_parts_strength():
    rat, bear = kitchen.single_dish_for('giant_rat_prime'), kitchen.single_dish_for('cave_bear_prime')
    assert kitchen.dish_worth(rat) < kitchen.dish_worth(bear)
    assert kitchen.dish_worth(rat) == pytest.approx(float(kitchen.ingredients()['giant_rat_prime']['richness']))


# ---------------------------------------------------------------- 2. sides

def test_every_ingredient_and_staple_has_one_side_from_the_list():
    for k, v in _parts_of_kind('prime', 'dungeon').items():
        assert v.get('side') in SIDE_KINDS, (k, v.get('side'))
    staple_sides = kitchen.rules()['sides']['staples']
    assert set(staple_sides) == set(STAPLES)
    assert len(set(staple_sides.values())) == len(STAPLES)        # nine staples, nine gifts
    for s in list(staple_sides.values()):
        assert s in SIDE_KINDS


def test_no_side_touches_poison_or_the_bodys_save():
    every = [v.get('side') for v in kitchen.ingredients().values()]
    every += list(kitchen.rules()['sides']['staples'].values())
    assert not set(every) & NEVER_A_SIDE


def test_a_dish_carries_its_ingredients_sides_and_never_its_own_power_twice():
    for r in kitchen.book():
        out = kitchen.dish_outcome(r)
        kinds = [k for k, _ in out['sides']]
        assert len(kinds) == len(set(kinds)), r['id']
        assert out['power'] not in kinds, r['id']


def test_a_step_with_another_staple_gives_something_else():
    cheese = next(r for r in kitchen.dishes_with('goblin_prime')
                  if set(kitchen.parts(r)) == {'goblin_prime', 'hard_cheese'})
    alone = kitchen.single_dish_for('goblin_prime')
    assert outcome_key(cheese) != outcome_key(alone)
    assert ('cold_resist' in [k for k, _ in kitchen.dish_outcome(cheese)['sides']])


def test_sides_are_applied_and_said():
    from player import Player
    rec = next(r for r in kitchen.book() if r.get('rung') == 'step'
               and 'wild_mushroom' in kitchen.parts(r) and kitchen.dish_power(r) != 'dark_vision')
    p = Player()
    lines = kitchen.dish_effects(p, rec)
    assert any(ln.startswith('Also: ') and 'Dark Vision' in ln for ln in lines), lines
    msgs = kitchen.apply_dish(p, rec)
    assert p.status_effects.get('dark_vision', 0) > 0, msgs


# ---------------------------------------------------------------- 3. stat dishes

def test_a_stat_dish_still_teaches_one_point_and_carries_its_sides():
    from player import Player
    rec = next(r for r in kitchen.book() if kitchen.dish_tab(r) == 'stat'
               and kitchen.dish_size(r) == 1 and kitchen.dish_outcome(r)['sides'])
    p = Player()
    stat = kitchen.dish_stat(rec)
    before = getattr(p, stat)
    kitchen.apply_dish(p, rec)
    assert getattr(p, stat) == before + 1


# ---------------------------------------------------------------- 4. the gate

def test_dishes_of_a_tier_and_tab_give_different_things():
    groups = collections.defaultdict(list)
    for r in kitchen.book():
        groups[(kitchen.dish_tier(r), kitchen.dish_tab(r))].append(outcome_key(r))
    low = {g: f'{len(set(k))}/{len(k)}' for g, k in groups.items()
           if len(k) >= 5 and len(set(k)) < 0.95 * len(k)}
    assert not low, low


# ---------------------------------------------------------------- poison (agreed)

def test_staples_alone_never_make_a_hero_poison_proof():
    """Brandon: cures must be worth carrying. A poison dish of staples alone
    gives Venom Ward (the effects branch defines it: a bite at half strength,
    for half its turns); only a creature's part gives Poison Resist."""
    plain = {r['id']: kitchen.dish_power(r) for r in kitchen.book() if r.get('rung') == 'plain'}
    assert 'poison_resist' not in plain.values()
    for rid in ('fare_apple_mushroom', 'fare_herb_stew', 'fare_trail_meat_mushroom_herb'):
        assert plain[rid] == 'venom_ward', rid
    assert kitchen.rules()['special']['powers']['venom_ward']['max_turns'] == 600
    for r in kitchen.book():
        if kitchen.dish_power(r) == 'poison_resist':
            assert any(kitchen.is_harvested(p) for p in kitchen.parts(r)), r['id']


# ---------------------------------------------------------------- 5-7. hunger

def test_hunger_every_three_steps():
    import floor_curve
    assert floor_curve.HUNGER_EVERY == 3


def test_sustained_only_from_big_sp_dishes_and_feasts_for_flat_turns():
    want = [60, 75, 90, 105, 120]
    for r in kitchen.book():
        out = kitchen.dish_outcome(r)
        big = kitchen.dish_size(r) >= 3 or kitchen.is_legendary(r)
        if out['tab'] == 'sp' and big:
            assert out['sustained'] == want[out['tier'] - 1], r['id']
        else:
            assert out['sustained'] == 0, r['id']


def test_dishes_off_the_sp_tab_feed_less():
    """60 / 80 / 105 / 125 / 150 on 3.6.1; tuned down to 24 / 32 / 42 / 50 / 60
    against the hunger targets (the simulator measure, 2026-11-22)."""
    assert kitchen.rules()['every_dish']['sp'] == [24, 32, 42, 50, 60]


# ---------------------------------------------------------------- early stats

STATS = ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')


def test_every_stat_has_real_choices_early():
    """Brandon: "I see a lot of some, but very few for other stats... players
    should be able to have enough choices early on". On floors 1-10 every stat
    is taught by at least 3 kinds a kid meets, and no stat's share of what
    spawns is more than 3 times another's (by lore: tools/content/kitchen/
    part_natures.txt)."""
    import dungeon
    share, kinds = collections.Counter(), collections.defaultdict(set)
    for floor in range(1, 11):
        pool = dungeon._build_spawn_pool(floor)
        total = sum(v['_spawn_freq'] for v in pool.values())
        for k, v in pool.items():
            ing = kitchen.ingredients().get(kitchen.ingredient_for_monster(k) or '') or {}
            if ing.get('nature') == 'stat':
                share[ing['stat_grant']] += v['_spawn_freq'] / total
                kinds[ing['stat_grant']].add(k)
    for s in STATS:
        assert len(kinds[s]) >= 3, (s, sorted(kinds[s]))
    assert max(share[s] for s in STATS) <= 3 * min(share[s] for s in STATS), dict(share)


# ---------------------------------------------------------------- 8. states

def _hero(share):
    from player import Player
    p = Player()
    p.sp = int(round(p.max_sp * share))
    return p


def test_the_three_states_by_the_belly():
    import hunger
    assert hunger.state(_hero(0.5)) is None
    assert hunger.state(_hero(0.2)) == 'hungry'
    assert hunger.state(_hero(0.05)) == 'weak'
    assert hunger.state(_hero(0.0)) == 'starving'


def test_weak_costs_two_strength_until_he_eats():
    import hunger
    p = _hero(0.05)
    str0 = p.STR
    lines = hunger.sync(p)
    assert p.STR == str0 - 2 and p.has_effect('weak_from_hunger') and lines
    p.restore_sp(p.max_sp)
    hunger.sync(p)
    assert p.STR == str0 and not p.has_effect('weak_from_hunger')
    assert not p.has_effect('hungry') and not p.has_effect('starving')


def test_weak_and_starving_heroes_do_not_mend():
    import hunger
    assert hunger.blocks_regen(_hero(0.05)) and hunger.blocks_regen(_hero(0.0))
    assert not hunger.blocks_regen(_hero(0.2))


def test_the_states_are_named_for_the_hud():
    from status_effects import EFFECT_INFO
    for s in ('hungry', 'weak_from_hunger', 'starving'):
        assert s in EFFECT_INFO, s


def test_a_starving_game_still_wounds(monkeypatch):
    import pygame
    from main import Game
    import items
    pygame.init()
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((960, 540)), player_name='__test_kitchen_variety__')
    g.player.sp = 0
    hp = g.player.hp
    import floor_curve
    for _ in range(floor_curve.HUNGER_EVERY * 2):
        g._tick_sp()
    assert g.player.hp < hp
    assert g.player.has_effect('starving')
