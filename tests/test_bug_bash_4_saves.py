"""The fourth bug bash (2026-10-16), saves angle: S-01, S-04, S-05, S-07,
S-08, S-10, S-11, S-12 and CQ-04. Each test builds a real Game and names
what was wrong. Every file the tests write goes to a temp dir.
"""
import copy
import json
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((64, 64))
    return _SCREEN


@pytest.fixture
def save_dir(tmp_path, monkeypatch):
    import save_system
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    return tmp_path


def _game(name='bb4saves'):
    from main import Game
    from game_states import STATE_PLAYER
    g = Game(_screen(), player_name=name)
    g.state = STATE_PLAYER
    return g


def _key(g, k):
    return g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0,
                                             unicode='', scancode=0))


def _start_quiz(g, results):
    from game_states import STATE_QUIZ
    g.state = STATE_QUIZ
    g.quiz_engine.start_quiz('threshold', 'history', 1,
                             lambda r: results.append(r.success), threshold=1)


def _adjacent_monster(g):
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    px, py = g.player.x, g.player.y
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x, y = px + dx, py + dy
        if g.dungeon.is_walkable(x, y):
            m = Monster({**mons['goblin'], 'id': 'goblin'}, x, y)
            g.monsters.append(m)
            g._refresh_fov()
            return m
    raise AssertionError('no open tile beside the hero')


# ---------------------------------------------------------------- S-01
def test_crash_report_never_saves_a_finished_run(save_dir):
    """A crash after the death screen wrote the dead hero (hp 0) back to
    disk: the emergency save took any game it was handed."""
    import crash_handler
    from save_system import save_exists, save_game
    from game_states import STATE_DEAD
    g = _game('bb4dead')
    assert save_game(g)
    g.player.hp = 0
    g.defeat_reason = 'died'
    g._on_game_over()
    g.state = STATE_DEAD
    assert not save_exists('bb4dead')
    try:
        raise RuntimeError('fatal after the death screen')
    except RuntimeError:
        path = crash_handler.write_crash_report(*sys.exc_info(), game=g)
    try:
        assert not save_exists('bb4dead')
        assert 'Emergency save written' not in open(path, encoding='utf-8').read()
    finally:
        os.remove(path)


def test_crash_mid_quiz_fails_the_question_before_saving(save_dir):
    """The emergency save kept the open question unresolved: the action's
    cost was spent and its failure never happened."""
    import crash_handler
    from save_system import save_exists
    g = _game('bb4quiz')
    results = []
    _start_quiz(g, results)
    assert g.quiz_engine.callback is not None
    try:
        raise RuntimeError('boom')
    except RuntimeError:
        path = crash_handler.write_crash_report(*sys.exc_info(), game=g)
    os.remove(path)
    assert results == [False]
    assert g.quiz_engine.callback is None
    assert save_exists('bb4quiz')


def test_the_crash_reference_is_cleared_at_the_title_screen():
    """_crash_game_ref kept pointing at the last (dead) game while the next
    title screen ran, so a crash there resurrected it."""
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    loop = src[src.index('    while True:', src.index('def main():')):]
    welcome = loop.index('WelcomeScreen(')
    assert '_crash_game_ref = None' in loop[:welcome]


# ---------------------------------------------------------------- S-04 / S-05
def _aim_spell(g, mp=5):
    _adjacent_monster(g)
    g.player.known_spells['fire_spark_spell'] = 3
    g.player.max_mp = 10
    g.player.mp = mp
    g._invoke_spell('fire_spark_spell')
    from game_states import STATE_TARGET
    assert g.state == STATE_TARGET


def test_quitting_while_aiming_a_spell_refunds_its_mp(save_dir):
    """Save & Exit during spell targeting saved the hero with the MP already
    spent and nothing cast."""
    from save_system import settle_unfinished_actions
    g = _game('bb4aim')
    _aim_spell(g)
    assert g.player.mp < 5
    settle_unfinished_actions(g)
    assert g.player.mp == 5
    assert getattr(g, '_pending_spell', None) is None
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    quit_block = src[src.index('# Save on clean exit'):src.index('# Otherwise player quit mid-game')]
    assert 'settle_unfinished_actions(game)' in quit_block


def test_escape_from_a_free_cast_restores_the_free_cast_not_mp(save_dir, monkeypatch):
    """ESC refunded MP that the free cast never took and left the floor's
    free cast spent."""
    import chain_passives
    monkeypatch.setattr(chain_passives, 'player_has_passive',
                        lambda p, f: f == 'free_cast_once_per_floor')
    monkeypatch.setattr(chain_passives, 'find_passive_item', lambda p, f: None)
    g = _game('bb4free')
    _aim_spell(g, mp=5)
    charges = chain_passives._ensure_charge_dict(g.player)
    assert g.player.mp == 5 and charges.get('free_cast_once_per_floor')
    _key(g, pygame.K_ESCAPE)
    assert g.player.mp == 5
    assert not charges.get('free_cast_once_per_floor')


def test_escape_from_a_paid_spell_still_refunds_its_mp(save_dir):
    g = _game('bb4paid')
    _aim_spell(g, mp=5)
    _key(g, pygame.K_ESCAPE)
    assert g.player.mp == 5


# ---------------------------------------------------------------- S-07
def test_non_utf8_highscores_read_as_empty(tmp_path, monkeypatch):
    """A highscores.json with cp1252 bytes raised UnicodeDecodeError out of
    the end screen on every frame."""
    import highscore_system
    f = tmp_path / 'highscores.json'
    f.write_bytes('[{"name": "Ren\xe9e", "score": 5}]'.encode('cp1252'))
    monkeypatch.setattr(highscore_system, '_SCORE_FILE', str(f))
    assert highscore_system.get_top(5) == []


def test_non_utf8_bones_are_removed_not_raised(tmp_path, monkeypatch):
    """A bones file with cp1252 bytes raised inside level generation, so
    every descent onto that floor failed."""
    import bones
    import random
    monkeypatch.setattr(bones, '_bones_dir', lambda: str(tmp_path))
    monkeypatch.delenv('PQ_NO_BONES', raising=False)
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    f = tmp_path / 'bones_L3.json'
    f.write_bytes('{"player_name": "Ren\xe9e", "gear": []}'.encode('cp1252'))
    assert bones.load_bones(3) is None
    assert not f.exists()


# ---------------------------------------------------------------- S-08
def test_quitting_mid_necronomicon_counts_as_a_failed_recital(save_dir):
    """Quitting during the recital saved the run with the recital forgotten:
    no Deadites, and the book could be read again."""
    from save_system import settle_unfinished_actions
    g = _game('bb4necro')
    spawned = []
    g._spawn_necronomicon_undead = lambda: spawned.append(True)
    g._necronomicon_quiz(types.SimpleNamespace(spell_id='army_of_darkness', mp_cost=1))
    assert g._necro_qs is not None
    settle_unfinished_actions(g)
    assert g._necro_qs is None
    assert spawned == [True]


# ---------------------------------------------------------------- S-10
def test_kit_return_survives_a_cancelled_exit_dialog(save_dir):
    """Opening the exit dialog during a Kit action's quiz, then cancelling,
    dropped the return: the hero ended on the map, not back on the Kit."""
    from items import load_items
    from quiz_engine import QuizState
    from game_states import STATE_KIT, STATE_QUIZ
    g = _game('bb4kit')
    arm = load_items('armor')[0]
    g.player.inventory.append(arm)
    g._open_kit_panel()
    ctx = g._kit_return_ctx()
    g._item_action_run('equip', arm, ctx)
    assert g.state == STATE_QUIZ
    g.handle_event(pygame.event.Event(pygame.QUIT))
    g.update(0.1)
    _key(g, pygame.K_ESCAPE)
    g.update(0.1)
    qe = g.quiz_engine
    for _ in range(10):
        if g.state == STATE_QUIZ and qe.state == QuizState.ASKING:
            qe.answer(str(qe.current_question['answer']))
        g.update(1.0)
        if g.state != STATE_QUIZ:
            break
    assert g.state == STATE_KIT


# ---------------------------------------------------------------- S-11
def _stale_bow():
    from items import load_items
    bow = next(w for w in load_items('weapon') if getattr(w, 'weapon_class', '') == 'bow')
    bow = copy.copy(bow)
    bow.requires_ammo = None
    return bow


def test_migrations_reach_stored_floors_sacks_and_the_belt(save_dir):
    """The ranged, lore and BUC migrations walked the hero, the pack and the
    floor underfoot only: stored floors, sack contents and the belt slot
    kept their pre-2026-05-20 fields."""
    from items import load_items
    g = _game('bb4migr')
    boxed, stored = _stale_bow(), _stale_bow()
    sack = copy.copy(load_items('container')[0])
    sack.contents = [boxed]
    g.player.inventory.append(sack)
    g.level_mgr._saved[7] = (g.dungeon, [], [stored])
    g._migrate_ranged_weapons()
    assert boxed.requires_ammo and stored.requires_ammo

    belt = copy.copy(load_items('accessory')[0])
    g.player.belt_slot = belt
    inner = copy.copy(load_items('accessory')[0])
    sack.contents.append(inner)
    for it in (belt, inner, stored):
        it.__dict__.pop('buc', None)
        it.__dict__.pop('buc_known', None)
    for it in (belt, inner, stored):
        assert 'buc' not in it.__dict__
    g._migrate_buc_all({'ground_items': g.ground_items, 'level_mgr': g.level_mgr})
    for it in (belt, inner, stored):
        assert 'buc' in it.__dict__, it.name


# ---------------------------------------------------------------- S-12
def test_ingredient_migration_says_the_items_were_dropped(save_dir, capsys):
    """It said they were "Translated ... to Assorted Monster Parts"; they
    are dropped (that ingredient no longer exists)."""
    from items import Ingredient
    g = _game('bb4ing')
    dead = Ingredient({'id': 'orc_meat', 'name': 'Orc Meat', 'symbol': '%', 'color': [1, 2, 3]})
    g.player.inventory.append(dead)
    g._migrate_legacy_ingredients({'ground_items': [], 'level_mgr': None})
    out = capsys.readouterr().out
    assert dead not in g.player.inventory
    assert 'Dropped 1 legacy ingredient' in out
    assert 'Assorted Monster Parts' not in out


# ---------------------------------------------------------------- CQ-04
def test_a_save_that_will_not_restore_is_set_aside(save_dir):
    """A save that unpickled but failed load_state said "Please try again",
    and failed the same way on every attempt: the name was locked."""
    from main import _restore_saved_game
    from save_system import save_game, load_game, save_exists
    g = _game('bb4bad')
    assert save_game(g)
    state = load_game('bb4bad')
    del state['turn_count']                      # load_state raises KeyError
    game, notice = _restore_saved_game(_screen(), 'bb4bad', state)
    assert game is None
    assert not save_exists('bb4bad')
    kept = [n for n in os.listdir(save_dir) if n.startswith('save_bb4bad.pkl.unreadable-')]
    assert kept and kept[0] in notice
    assert 'try again' not in notice.lower()


def test_a_save_that_restores_wrongly_is_set_aside(save_dir, monkeypatch):
    from main import Game, _restore_saved_game
    from save_system import save_game, load_game, save_exists
    g = _game('bb4bad2')
    assert save_game(g)
    state = load_game('bb4bad2')
    monkeypatch.setattr(Game, '_load_looks_valid', lambda self, st: False)
    game, notice = _restore_saved_game(_screen(), 'bb4bad2', state)
    assert game is None and notice
    assert not save_exists('bb4bad2')


def test_a_good_save_restores(save_dir):
    from main import _restore_saved_game
    from save_system import save_game, load_game
    g = _game('bb4good')
    g.turn_count = 42
    assert save_game(g)
    game, notice = _restore_saved_game(_screen(), 'bb4good', load_game('bb4good'))
    assert notice is None and game.turn_count == 42
