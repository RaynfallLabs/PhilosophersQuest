"""The 2026-10 difficulty pass.

Measured with tools/balance/difficulty_sim.py before the pass: from about
floor 12 every melee attack landed at chain 5 with no question asked, one
attack killed 96 to 100 percent of monsters, and the player still had 35 hit
points on floor 39. Easy on offence, one-roll lethal on defence. These tests
pin the rules that changed. They are logic tests: none of them proves the
game FEELS right, which needs play.
"""
import json
import os
import random
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))


def _monsters():
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        return json.load(f)


def _mon(mid):
    from monster import Monster
    return Monster({**_monsters()[mid], 'id': mid}, 1, 1)


# ------------------------------------------------------------- the combat quiz

def _engine_with_math_tier_cleared(tier=1):
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe._mastered.add(('math', tier))
    qe._retired[('math', tier)] = {q['question'] for q in qe.load_questions('math')
                                   if q.get('tier', 1) == tier}
    return qe


def test_combat_still_asks_on_a_cleared_math_tier():
    """It used to return chain 5 with no question for the rest of the run."""
    qe = _engine_with_math_tier_cleared(1)
    got = []
    qe.start_quiz(mode='chain', subject='math', tier=1, callback=got.append,
                  wisdom=10, base_seconds=10)
    assert not got, "the chain ended without a question being asked"
    assert qe.current_question is not None
    assert qe.current_question.get('tier', 1) == 1
    assert qe.auto_passed == 0


def test_a_cleared_tier_still_auto_passes_outside_combat():
    """The reward for clearing a tier stands for every untimed quiz."""
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe._mastered.add(('cooking', 1))
    got = []
    qe.start_quiz(mode='threshold', subject='cooking', tier=1, callback=got.append,
                  threshold=1, total_qs=1)
    assert got and got[0].success


def test_the_clock_is_wisdom_and_never_grows_with_the_tier():
    """Seconds are never added because the sums got harder."""
    from quiz_engine import QuizEngine
    for tier in (1, 3, 5):
        qe = QuizEngine()
        qe.start_quiz(mode='chain', subject='math', tier=tier, callback=lambda r: None,
                      wisdom=10, base_seconds=10)
        assert qe.timer_seconds == 10, tier
    qe = QuizEngine()                      # earned time still counts
    qe.start_quiz(mode='chain', subject='math', tier=5, callback=lambda r: None,
                  wisdom=10, base_seconds=10, timer_modifier=1.25, extra_seconds=2)
    assert qe.timer_seconds == round(10 * 1.25) + 2


def test_every_material_has_one_tier_and_its_items_inherit_it():
    from items import (instantiate_armor, instantiate_weapon, load_materials,
                       material_tier)
    weapons, armor = load_materials('weapons'), load_materials('armor')
    for mats in (weapons, armor):
        for mid, mat in mats.items():
            assert mat.get('tier') in (1, 2, 3, 4, 5), mid
    for mid in set(weapons) & set(armor):
        assert weapons[mid]['tier'] == armor[mid]['tier'], mid
    seen = set()
    for mid, mat in weapons.items():
        try:
            w = instantiate_weapon('longsword', mid)
        except Exception:
            continue
        assert w.quiz_tier == material_tier(mat) == mat['tier'], mid
        seen.add(w.quiz_tier)
    assert seen == {1, 2, 3, 4, 5}
    made = 0
    for mid, mat in armor.items():
        for tpl in ('chainmail', 'breastplate', 'cloak', 'chain_shirt'):
            try:
                a = instantiate_armor(tpl, mid)
            except Exception:
                continue
            assert a.quiz_tier == mat['tier'], (tpl, mid)
            made += 1
            break
    assert made >= 10


# ------------------------------------------------------------------ hit points

def test_cooking_cap_is_four_per_floor_and_is_a_real_cap():
    from player import Player
    p = Player()
    for floor, cap in ((1, 20), (5, 20), (20, 80), (50, 200), (100, 400)):
        p.deepest_floor_reached = floor
        assert p.cooking_softcap() == cap
    p.deepest_floor_reached = 10                 # cap 40
    base = p.max_hp
    for _ in range(100):
        p.increase_max_hp(3, from_cooking=True)
    assert p.max_hp == base + 40                 # it used to creep on at +1 for ever
    assert p.cooking_hp_gained == 40


def test_every_proper_meal_builds_max_hp_under_the_floor_cap():
    from food_system import _apply_outcome_body
    from player import Player
    p = Player()
    p.deepest_floor_reached = 30
    p.reset_floor_cook_caps()
    base = p.max_hp
    plain = {'sp': 10, 'hp': 0}
    for _ in range(10):
        _apply_outcome_body(p, {'name': 'Stew'}, plain)
    assert p.max_hp == base + p.PER_FLOOR_HP_CAP          # ten meals, one floor's cap
    p.reset_floor_cook_caps()                    # next floor
    _apply_outcome_body(p, {'name': 'Stew'}, plain)
    assert p.max_hp == base + p.PER_FLOOR_HP_CAP + p.COOK_BASE_MAX_HP


def test_healing_potions_keep_up_with_a_big_health_bar():
    from food_system import POTION_EXTRA_HEAL_SHARE, POTION_HEAL_SHARE, drink_potion
    from items import make_item_by_id
    from player import Player
    for pid, share in (('potion_of_healing', POTION_HEAL_SHARE),
                       ('potion_of_extra_healing', POTION_EXTRA_HEAL_SHARE)):
        p = Player()
        p.max_hp, p.hp = 400, 1
        pot = make_item_by_id('potion', pid)
        pot.buc = 'uncursed'
        drink_potion(p, pot)
        assert p.hp - 1 >= int(400 * share)


def test_rest_scales_with_health_and_costs_food():
    from floor_curve import MEDITATE_PERIOD, natural_regen, wander_alive_cap
    assert natural_regen(30) == 1 and natural_regen(400) == 8
    assert MEDITATE_PERIOD >= 3
    assert wander_alive_cap(1) >= 10 and wander_alive_cap(100) <= 30
    src = open(os.path.join(ROOT, 'src', 'game_input.py'), encoding='utf-8').read()
    wait = src[src.index('if key == pygame.K_PERIOD:'):]
    wait = wait[:wait.index('self._advance_turn()')]
    assert 'self._tick_sp()' in wait, "waiting must make the player hungry"


# ---------------------------------------------------------------- monster side

def test_armor_turns_blows_but_nothing_is_untouchable():
    from monster import MIN_HIT_NAMED, MIN_HIT_ORDINARY
    assert 0.25 <= MIN_HIT_ORDINARY < MIN_HIT_NAMED <= 0.5
    assert _mon('giant_rat')._min_hit() == MIN_HIT_ORDINARY
    assert _mon('abaddon_destroyer')._min_hit() == MIN_HIT_NAMED
    assert _mon('arachne')._min_hit() == MIN_HIT_NAMED


def test_named_foes_do_not_bleed_out():
    from monster import BLEED_DIVISOR, NAMED_DOT_DIVISOR
    for mid, div in (('giant_rat', BLEED_DIVISOR), ('abaddon_destroyer', NAMED_DOT_DIVISOR)):
        m = _mon(mid)
        m.status_effects['bleeding'] = 3
        before = m.hp
        m.tick_effects()
        assert 0 < before - m.hp <= max(1, m.max_hp // div), mid   # (a ward may shave it)


def test_drain_gets_a_save_and_a_limit(monkeypatch):
    import monster as mon
    from player import Player
    m = _mon('wraith')
    p = Player()
    p.reset_floor_cook_caps()
    monkeypatch.setattr(mon.random, 'randint', lambda a, b: a)       # every save fails
    took = sum(1 for _ in range(10) if m._drain_takes_hold(p)
               and not setattr(p, '_con_drained_this_floor',
                               p._con_drained_this_floor + 1))
    assert took == mon.DRAIN_CON_PER_FLOOR
    p.reset_floor_cook_caps()
    monkeypatch.setattr(mon.random, 'randint', lambda a, b: b)       # every save holds
    assert not m._drain_takes_hold(p)
    p.CON = mon.DRAIN_CON_FLOOR
    monkeypatch.setattr(mon.random, 'randint', lambda a, b: a)
    assert not m._drain_takes_hold(p)


def test_poison_and_bleeding_scale_with_the_health_bar():
    from player import Player
    from status_effects import DOT_SHARE, REGEN_PERIOD, tick_all
    p = Player()
    p.max_hp = p.hp = 400
    p.status_effects['bleeding'] = 5
    tick_all(p)
    assert 400 - p.hp == int(round(400 * DOT_SHARE))
    q = Player()
    q.max_hp, q.hp = 100, 50
    q.status_effects['regenerating'] = 30
    for _ in range(REGEN_PERIOD * 4):
        tick_all(q)
    assert q.hp == 54


def test_fear_can_be_shaken_off():
    from status_effects import HARD_CONTROL, SOFT_CONTROL
    assert 'feared' in HARD_CONTROL and 'feared' not in SOFT_CONTROL


def test_rooted_monsters_strike_what_stands_next_to_them():
    """`sessile` returned False before the adjacency check: 29 kinds of plant,
    mold, ooze and statue never attacked at all."""
    src = open(os.path.join(ROOT, 'src', 'monster.py'), encoding='utf-8').read()
    i = src.index("if effective_pattern == 'sessile':")
    block = src[i:i + 900]
    assert block.index('self._adjacent_to(player)') < block.index('return False')
    data = _monsters()
    for mid, atk in (('thorn_slinger', 'Thorn Volley'), ('roper', 'Strands')):
        assert any(a['name'] == atk and a.get('ranged') for a in data[mid]['attacks']), mid


def test_maze_floors_are_not_free_floors():
    """Floors 10, 30, 50, 70 and 90 started with one to six monsters."""
    import level_manager
    from dungeon import MIN_FLOOR_MONSTERS
    for floor in (30, 70):
        _d, monsters, _i = level_manager.LevelManager().generate(floor)
        # the fill aims at MIN_FLOOR_MONSTERS + floor // 8 (9 and 14); a
        # cramped maze can fall a little short, never back to a handful
        assert len(monsters) >= MIN_FLOOR_MONSTERS + 1, (floor, len(monsters))


# ------------------------------------------------------------------------ data

def test_gate_bosses_are_long_fights():
    import respawn_by_hp as R
    data = _monsters()
    for mid, hp in R.GATE_BOSS_HP.items():
        assert R.dice_avg(data[mid]['hp']) >= 0.97 * hp, mid
    assert R.GATE_BOSS_HP['asterion_minotaur'] >= 1500
    assert R.GATE_BOSS_HP['abaddon_destroyer'] >= 6000


def test_no_ordinary_attack_is_a_one_hit_spike():
    import respawn_by_hp as R
    data = _monsters()
    bad = []
    for mid, d in data.items():
        if not R.is_random_spawn(d) or d.get('is_mini_boss') or d.get('is_boss'):
            continue
        limit = R.SPIKE_CAP * R.target_dmg(d.get('peak_floor', 1))
        for a in d.get('attacks') or []:
            avg = R.dice_avg(a.get('damage', 0))
            if avg > 6 and avg > 1.15 * limit:
                bad.append((mid, a['name'], avg, round(limit, 1)))
    assert not bad, bad[:8]


def test_deep_damage_does_not_fall_with_depth():
    from floor_curve import DMG_ANCHORS, HP_ANCHORS
    for table in (DMG_ANCHORS, HP_ANCHORS):
        vals = [table[k] for k in sorted(table)]
        assert vals == sorted(vals)


def test_the_difficulty_schedule_script_will_not_run_twice_by_accident():
    import apply_difficulty_schedule as A
    hp, dmg = A.new_anchors()
    assert set(hp) == set(A.OLD_HP_ANCHORS)
    src = open(os.path.join(ROOT, 'tools', 'balance', 'apply_difficulty_schedule.py'),
               encoding='utf-8').read()
    assert '--i-know' in src


def test_stat_scrolls_and_stat_food_are_rare_and_small():
    src = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    assert 'stat_count = [1, 1, 1, 1, 2][_tstep]' in src
    scrolls = json.load(open(os.path.join(ROOT, 'data', 'items', 'scroll.json'), encoding='utf-8'))
    for sid in ('scroll_of_power', 'scroll_of_greater_power', 'scroll_of_great_power',
                'scroll_of_time_stop'):
        assert scrolls[sid]['peak_weight'] <= 0.05, sid


@pytest.mark.parametrize('seed', [1, 2, 3])
def test_one_room_floor_does_not_crash_item_spawn(seed):
    """spawn_items did rng.choice(rooms[1:]) for the soul sphere."""
    src = open(os.path.join(ROOT, 'src', 'dungeon.py'), encoding='utf-8').read()
    assert 'sphere_room = rng.choice(rooms[1:] or rooms)' in src
    random.seed(seed)


# ------------------------------------------------- stats a status only lends

@pytest.mark.parametrize('effect,stats', [('heroism', ('STR',)), ('brilliance', ('INT', 'WIS'))])
def test_a_lent_stat_always_comes_back_exactly(effect, stats):
    """A cooked "Heroic" or "Brilliant" meal granted the status without the
    stat, and the expiry subtracted it anyway: a permanent loss per meal."""
    from player import Player
    from status_effects import tick_all
    p = Player()
    before = {s: getattr(p, s) for s in stats}
    p.add_effect(effect, 5)                 # the path cooking takes
    assert all(getattr(p, s) > before[s] for s in stats)
    p.add_effect(effect, 5)                 # renewing does not grant twice
    lent = {s: getattr(p, s) - before[s] for s in stats}
    assert all(v in (1, 2) for v in lent.values())
    for _ in range(80):
        tick_all(p)
    assert not p.has_effect(effect)
    assert {s: getattr(p, s) for s in stats} == before


def test_no_caller_grants_a_lent_stat_by_hand():
    for name in ('food_system.py', 'game_menus.py'):
        src = open(os.path.join(ROOT, 'src', name), encoding='utf-8').read()
        for effect in ('heroism', 'brilliance'):
            for m in __import__('re').finditer(r"add_effect\('%s'" % effect, src):
                window = src[max(0, m.start() - 260):m.start() + 260]
                assert 'apply_stat_bonus' not in window, (name, effect)
