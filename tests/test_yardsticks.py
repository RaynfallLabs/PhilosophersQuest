"""The yardsticks the remaining systems are sized against (master plan, 2)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import floor_curve  # noqa: E402


def test_the_tables_rise_with_depth():
    for table in (floor_curve.ONE_ATTACK, floor_curve.HEALTH_BAR):
        vals = [table[k] for k in sorted(table)]
        assert vals == sorted(vals) and vals[0] > 0


def test_one_attack_matches_the_live_weapons_and_clock():
    """Fails if weapons, the clock rule or the tier steps move and the stored
    table is not refreshed (python tools/balance/yardsticks.py)."""
    import yardsticks
    fresh = yardsticks.one_attack_table(samples=120)
    for floor in (1, 20, 40, 60, 80, 100):
        got = fresh[floor][0]
        want = floor_curve.one_attack(floor)
        assert 0.6 * want <= got <= 1.6 * want, (floor, got, want)


def test_an_ordinary_monster_is_a_few_attacks_for_a_typical_weapon():
    for floor in (1, 10, 20, 40, 60, 80, 100):
        n = floor_curve.target_hp(floor) / floor_curve.one_attack(floor)
        assert 1.0 <= n <= 6.0, (floor, round(n, 1))


def test_shares_are_whole_and_follow_the_floor():
    assert floor_curve.attacks(1, 60) == round(floor_curve.one_attack(60))
    assert floor_curve.attacks(0.25, 60) < floor_curve.attacks(0.25, 80)
    assert floor_curve.of_health(0.1, 50) == round(0.1 * floor_curve.health_bar(50))
    assert floor_curve.of_health(0.1, 50, max_hp=400) == 40
    assert floor_curve.of_health(0.001, 1) == 1


def test_answer_times_are_recorded_and_totalled(tmp_path, monkeypatch):
    import quiz_engine
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    clock = [100.0]
    monkeypatch.setattr(quiz_engine.time, 'monotonic', lambda: clock[0])
    for _ in range(2):
        qe = quiz_engine.QuizEngine()
        qe.start_quiz(mode='chain', subject='math', tier=1, callback=lambda r: None,
                      wisdom=10, base_seconds=10)
        clock[0] += 2.0
        qe.answer(str(qe.current_question['answer']))          # right, in two seconds
        qe._persist_answer_times()
    rec = quiz_engine.load_answer_times()['math|1']
    assert rec['n'] == 2 and rec['right'] == 2
    assert abs(rec['seconds_right'] - 4.0) < 0.01
    # time spent with a context card open is not answer time
    qe = quiz_engine.QuizEngine()
    qe.start_quiz(mode='chain', subject='math', tier=1, callback=lambda r: None,
                  wisdom=10, base_seconds=10)
    qe.pause_timer()
    clock[0] += 30.0
    qe.resume_timer()
    qe.answer(str(qe.current_question['answer']))
    qe._persist_answer_times()
    assert quiz_engine.load_answer_times()['math|1']['n'] == 2


# ------------------------------------------- Phase 1: hazards and healing

def test_a_hazard_is_a_share_of_the_players_own_health():
    """A pit trap's 2d6 was a quarter of a new character and under 2% of a
    deep one."""
    assert floor_curve.hazard(7, 60) == 7                   # as written at 60 HP
    assert floor_curve.hazard(7, 30) == 4 and floor_curve.hazard(7, 420) == 49
    assert floor_curve.hazard(0, 400) == 0 and floor_curve.hazard(1, 20) == 1
    assert floor_curve.hazard(500, 400) == round(floor_curve.HAZARD_CAP * 400)
    for name, needle in (
            ('main.py', "_hazard(_dice_roll(dmg_str), self.player.max_hp)"),
            ('main.py', "_of_health(STARVE_SHARE, 1, self.player.max_hp)"),
            ('container_system.py', "hazard(raw_dmg, player.max_hp)"),
            ('game_combat.py', "floor_curve.hazard(_dice_roll('1d4'), self.player.max_hp)"),
            ('game_divine.py', "hazard(_rng.randint(5, 15), self.player.max_hp)"),
            ('game_magic.py', "hazard(roll('3d6'), self.player.max_hp)")):
        src = open(os.path.join(ROOT, 'src', name), encoding='utf-8').read()
        assert needle in src, (name, needle)


def test_chest_traps_hurt_in_proportion():
    import container_system as cs
    from player import Player
    for max_hp in (30, 400):
        worst = 0.0
        for tier, pool in cs._load_trap_pool().items():
            for trap in pool:
                for _ in range(15):
                    p = Player()
                    p.max_hp = p.hp = max_hp
                    cs._trigger_trap(p, dict(trap), [])
                    worst = max(worst, (max_hp - p.hp) / max_hp)
        assert 0.10 <= worst <= floor_curve.HAZARD_CAP + 0.02, (max_hp, worst)


def test_healing_keeps_pace_with_the_health_bar():
    assert floor_curve.mend(9, 60, 0.15) == 9 and floor_curve.mend(9, 400, 0.15) == 60
    import game_magic
    assert game_magic.WAND_HEAL_SHARE < game_magic.WAND_EXTRA_HEAL_SHARE <= 0.4
    shares = [game_magic.SPELL_HEAL_SHARE[t] for t in (1, 2, 3, 4)]
    assert shares == sorted(shares) and shares[-1] <= 0.5
    from food_system import _apply_outcome_body
    from player import Player
    p = Player()
    p.max_hp, p.hp = 400, 100
    _apply_outcome_body(p, {'name': 'Stew'}, {'sp': 10, 'hp': 14})
    assert p.hp - 100 >= 30                                  # 14 written; 7.8% of 400 + the meal's max HP


def test_starving_and_strangling_follow_the_health_bar():
    from player import Player
    from status_effects import tick_all
    p = Player()
    p.max_hp = p.hp = 400
    p.status_effects['strangulation'] = 3
    tick_all(p)
    assert 400 - p.hp == 16
