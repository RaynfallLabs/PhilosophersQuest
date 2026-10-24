"""Fixes from Brandon's playtest of 2026-10-24.

* question order: the cross-game memory now covers a whole tier (it kept the
  last 30), and same-fact twins are held back once one is asked;
* a ranged monster's miss names its attack instead of "swings";
* traders' pronouns come from data/traders.json (Mother Wort was "he");
* a trader no longer flags his junk potions by a 5 gp price;
* monsters really hit pets, and the hits are reported;
* a pet routes round a wall instead of standing in the corner.
"""
import json
import os
import random
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import quiz_engine  # noqa: E402
from quiz_engine import QuizEngine, qhash  # noqa: E402


# -- question order ---------------------------------------------------------------

def _play(engine, subject, tier, n):
    engine.start_quiz('threshold', subject, tier, callback=lambda r: None)
    shown = [engine.current_question['question']]
    for _ in range(n - 1):
        engine._next_question()
        shown.append(engine.current_question['question'])
    engine._persist_cross_game_history()
    return shown


def test_games_walk_a_whole_tier_before_any_question_repeats(monkeypatch, tmp_path):
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    pool = {q['question'] for q in QuizEngine().load_questions('philosophy') if q['tier'] == 1}
    seen = []
    per_game = 40
    for _ in range(len(pool) // per_game):          # every full game before the pool runs out
        seen += _play(QuizEngine(), 'philosophy', 1, per_game)
    assert len(seen) == len(set(seen)), 'a question repeated before its tier was used up'
    # The file is the new format, and small (ids, not stems).
    data = json.loads((tmp_path / 'quiz_history.json').read_text(encoding='utf-8'))
    # (a twin of an asked question counts as shown too, so the cycle may hold more)
    assert data['version'] == 2 and len(data['cycle']['philosophy|1']) >= len(seen)


def test_a_used_up_tier_starts_a_new_cycle_holding_back_the_newest(monkeypatch, tmp_path):
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    e = QuizEngine()
    pool = [q for q in e.load_questions('philosophy') if q['tier'] == 1]
    e._cycle[('philosophy', 1)] = [qhash(q['question']) for q in pool]
    e._cycle_set[('philosophy', 1)] = set(e._cycle[('philosophy', 1)])
    newest = {q['question'] for q in pool[-quiz_engine._CYCLE_HOLD_BACK:]}
    first = _play(e, 'philosophy', 1, 20)
    assert not newest & set(first), 'a just-asked question led the new cycle'


def test_a_twin_is_held_back_once_its_sister_is_asked(monkeypatch, tmp_path):
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    probe = QuizEngine()
    pool = [q for q in probe.load_questions('history') if q['tier'] == 1]
    a, b = pool[0], pool[1]
    twins = tmp_path / 'twins.json'
    twins.write_text(json.dumps({'groups': {'history': [[[qhash(a['question']), 1],
                                                        [qhash(b['question']), 1]]]}}), encoding='utf-8')
    monkeypatch.setattr(quiz_engine, '_TWINS_PATH', str(twins))
    random.seed(3)
    e = QuizEngine()
    e.start_quiz('threshold', 'history', 1, callback=lambda r: None)
    shown = [e.current_question['question']]
    for _ in range(len(pool) - 3):
        e._next_question()
        shown.append(e.current_question['question'])
    assert not (a['question'] in shown and b['question'] in shown), 'both twins asked in one run'


def test_old_history_files_still_load(monkeypatch, tmp_path):
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    q = [q for q in QuizEngine().load_questions('animal') if q['tier'] == 1][0]['question']
    (tmp_path / 'quiz_history.json').write_text(json.dumps({'animal|1': [q]}), encoding='utf-8')
    assert QuizEngine()._cycle_set[('animal', 1)] == {qhash(q)}


def test_the_shipped_twins_file_names_real_questions():
    path = ROOT / 'data' / 'question_twins.json'
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding='utf-8'))
    for subject, groups in data['groups'].items():
        qs = json.loads((ROOT / 'data' / 'questions' / f'{subject}.json').read_text(encoding='utf-8'))
        known = {qhash(q['question']): q['tier'] for q in qs}
        for group in groups:
            assert len(group) >= 2
            for h, tier in group:
                assert known.get(h) == tier, (subject, h)


# -- ranged misses -----------------------------------------------------------------

def test_a_ranged_miss_names_its_attack():
    from monster import Monster
    m = Monster.__new__(Monster)
    m.name, m.kind = 'goblin archer', 'goblin_archer'
    arrow = m._miss_text({'name': 'arrow_volley', 'ranged': True}, note='(AC 4 deflects)')
    assert 'swing' not in arrow and 'arrow volley misses you' in arrow and 'AC 4' in arrow
    assert 'swings at you' in m._miss_text({'name': 'claw'})
    assert 'fails to take hold' in m._miss_text({'name': 'stony_gaze'})


# -- traders -------------------------------------------------------------------------

def test_trader_pronouns_come_from_data():
    import traders
    from mystery_system import build_trader
    assert traders.kind_def('apothecary')['pronoun'] == 'she'
    wort = build_trader('apothecary', 3, random.Random(1))
    assert wort.pronouns() == ('she', 'her', 'her')
    assert traders.refusal({'buys': ['potion'], 'pronoun': 'she'},
                           type('I', (), {'item_class': 'weapon', 'id': 'x'})(),
                           known=True, cursed_known=False) == "She doesn't deal in that"
    vesper = build_trader('abyssal', 30, random.Random(1))
    assert vesper.pronouns()[0] == 'it'
    # A merchant pickled before pronouns finds hers by kind.
    del wort.__dict__['pronoun']
    assert wort.pronouns()[0] == 'she'


def test_an_unknown_junk_potion_is_not_flagged_by_its_price():
    import economy
    from items import make_item_by_id
    junk = make_item_by_id('potion', 'potion_of_sickness')
    heal = make_item_by_id('potion', 'potion_of_healing')
    gain = make_item_by_id('potion', 'potion_of_gain_level')
    assert economy.stock_price(junk, 4) == economy.stock_price(heal, 4)
    assert economy.stock_price(gain, 4) > 5 * economy.stock_price(heal, 4)   # dear now
    assert economy.merchant_price(junk, 4) == 5                          # selling it is unchanged


# -- pets ---------------------------------------------------------------------------

class _Dungeon:
    """A 9x7 room split by a wall at x=4 with a gap at the bottom (y=5)."""
    def is_walkable(self, x, y):
        if not (0 < x < 8 and 0 < y < 6):
            return False
        return not (x == 4 and y != 5)


def test_a_pet_routes_round_a_wall_to_its_hero():
    from pet_system import Pet
    pet = Pet.__new__(Pet)
    pet.x, pet.y, pet.alive = 1, 1, True                     # far corner, wall to the east
    hero = type('H', (), {'x': 7, 'y': 1})()
    path = []
    for _ in range(12):
        pet._move_toward(hero.x, hero.y, _Dungeon(), [], [pet], hero)
        path.append((pet.x, pet.y))
    assert max(abs(pet.x - hero.x), abs(pet.y - hero.y)) <= 1, path
    assert all(_Dungeon().is_walkable(*p) for p in path)


def test_monsters_really_hit_pets_and_it_is_reported(monkeypatch, tmp_path):
    import save_system
    import pygame
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    pygame.init()
    from main import Game
    from monster import Monster
    from pet_system import Pet
    g = Game(pygame.display.set_mode((1280, 720)), player_name='pettest')
    p = g.player
    pet = Pet('fire', p.x + 3, p.y)                          # nowhere near the hero
    m = Monster.__new__(Monster)
    m.__dict__.update({'name': 'goblin', 'kind': 'goblin', 'x': p.x + 4, 'y': p.y, 'alive': True,
                       'attacks': [{'name': 'club', 'damage': '3d4'}], 'effects': {},
                       'footprint': (1, 1)})
    m.has_effect = lambda e: False
    m.spring = lambda: False
    g.monsters = [m]
    g.visible = {(pet.x, pet.y), (m.x, m.y)}
    before = pet.hp
    g._monster_swipes([pet])
    assert pet.hp <= before - 3, 'a monster that cannot reach the hero only nibbled the pet'
    said = [text for text, _kind in g.msg_log.entries[-3:]]
    assert any('goblin hits' in t.lower() and pet.name in t for t in said), said
