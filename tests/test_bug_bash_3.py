"""The third bug bash (2026-10-09): eight reviewers, one angle each. These pin
the fixes that can be pinned without a window. Each test names what was
wrong.
"""
import json
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((64, 64))

import status_effects  # noqa: E402
from items import make_item_by_id  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402


def _data(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


def _src(name):
    return open(os.path.join(ROOT, 'src', name), encoding='utf-8').read()


def _monster(mid='goblin', x=5, y=5):
    return Monster({**_data('monsters.json')[mid], 'id': mid}, x, y)


# ---------------------------------------------------------------- sound
def test_the_game_has_sound():
    """All 14 sounds failed to build (wrong array shape for the open mixer),
    the failure was swallowed, and the game was silent."""
    import importlib
    import sound_system
    importlib.reload(sound_system)
    assert sound_system.init() is True
    built = [s for s in sound_system._sounds.values() if s is not None]
    assert len(built) >= 14


# ---------------------------------------------------------------- monsters
def test_a_stunned_or_frozen_monster_loses_its_turn():
    for effect in ('stunned', 'frozen', 'paralyzed', 'sleeping'):
        m = _monster()
        m.status_effects[effect] = 5
        p = types.SimpleNamespace(x=6, y=5)
        assert m.take_turn(p, None, [m]) is False, effect


def test_friends_standing_among_the_monsters_take_no_damage():
    """Area spells and pet specials killed flavor NPCs, the unicorn and the
    Heavenly Host; only karma NPCs were guarded."""
    for attr in ('_npc_encounter_tag', '_flavor_encounter_tag', '_is_unicorn', 'is_allied'):
        m = _monster()
        setattr(m, attr, 'x' if attr.endswith('tag') else True)
        hp = m.hp
        assert m.take_damage(10 ** 6) == 0 and m.hp == hp and m.alive, attr


def test_a_creature_that_left_is_not_reaped_as_a_kill():
    """Helping an NPC printed "The Lost Girl is slain!" and left her corpse."""
    src = _src('main.py')
    at = src.index('def _reap_unnoticed_kills')
    body = src[at:at + 1800]
    assert "getattr(m, 'hp', 0) > 0" in body and '_npc_encounter_tag' in body and 'is_allied' in body
    gc = _src('game_combat.py')
    at = gc.index('def _on_monster_killed')
    assert "if getattr(monster, '_kill_handled', False):\n            return" in gc[at:at + 1600]


def test_a_trap_death_and_a_fatal_pit_fall_end_the_run():
    """They set the dead state without the game-over path: the save stayed
    on disk and no bones were left."""
    src = _src('main.py')
    at = src.index('def _check_floor_trap')
    end = src.index('def _teleport_player')
    assert 'self._on_game_over()' in src[at:end]
    at = src.index('self._player_fall_in_pit(px, py)')
    assert 'self._on_game_over()' in src[at:at + 600]


# ---------------------------------------------------------------- the character
def test_resisting_is_not_immunity_to_a_one_point_tick():
    p = Player()
    p.max_hp = p.hp = 30
    p.damage_resistances['poison'] = 1                  # one chain level: 8%
    assert p.take_damage(1, 'poison') == 1


def test_a_stat_a_status_lends_follows_the_status_however_it_comes_and_goes():
    """Heroism potion, then an item that grants heroism permanently, then
    that item taken off (a plain pop): +2 Strength stayed for good."""
    p = Player()
    base = p.STR
    p.add_effect('heroism', 50)
    assert p.STR == base + 2
    p.status_effects['heroism'] = -1                    # an item makes it permanent
    status_effects.sync_timed_grants(p)
    assert p.STR == base + 2
    p.status_effects.pop('heroism', None)               # the item comes off
    status_effects.sync_timed_grants(p)
    assert p.STR == base
    p.add_effect('heroism', -1)                         # permanent from the start
    assert p.STR == base + 2
    p.status_effects.pop('heroism')
    status_effects.tick_all(p)
    assert p.STR == base


def test_an_older_save_with_heroism_running_is_not_granted_it_twice():
    p = Player()
    p.STR += 2
    p.status_effects['heroism'] = 10                    # granted by the old code
    if hasattr(p, '_timed_grants_held'):
        del p._timed_grants_held
    status_effects.sync_timed_grants(p)
    assert p.STR == 12
    for _ in range(12):
        status_effects.tick_all(p)
    assert p.STR == 10


def test_restore_strength_gives_back_what_disease_took():
    assert "_str_lost_to_disease" in _src('status_effects.py')
    src = _src('food_system.py')
    assert "getattr(player, '_base_STR'" not in src and "_str_lost_to_disease" in src


def test_every_ring_owns_its_effects():
    """Copies of one template shared one dict: enchanting a ring changed
    every ring made from the same entry."""
    acc = _data('items', 'accessory.json')
    rid = next(k for k, v in acc.items() if isinstance(v, dict) and (v.get('effects') or {}).get('amount'))
    a, b = make_item_by_id('accessory', rid), make_item_by_id('accessory', rid)
    a.effects['amount'] = 99
    assert b.effects['amount'] != 99


def test_once_a_floor_charges_are_kept_across_a_staircase():
    src = _src('main.py')
    assert '_held_charges = None if new_level > _was_deepest else self._once_a_floor_state()' in src
    assert 'self._restore_once_a_floor_state(_held_charges)' in src
    for name in ('_first_hit_used', '_death_save_used', '_tarnhelm_used', '_death_save_used_this_floor',
                 '_seven_league_used_this_floor', '_gold_offering_used_this_floor'):
        assert name in src[src.index('_ONCE_A_FLOOR_GAME'):src.index('def _once_a_floor_state')]


# ---------------------------------------------------------------- the dungeon
class _Dungeon:
    def __init__(self, rows):
        from dungeon import FLOOR, WALL, WATER
        code = {'#': WALL, '.': FLOOR, '~': WATER}
        self.tiles = [[code[c] for c in row] for row in rows]
        self.width, self.height = len(rows[0]), len(rows)
        self._floor = FLOOR

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and self.tiles[y][x] == self._floor


def test_a_seal_keeper_on_an_island_is_brought_within_reach():
    """A pool leaves the middle of a room an island. A seal keeper there kept
    its stair sealed for good: about one run in nine."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('pq_main_bb3', os.path.join(ROOT, 'src', 'main.py'))
    main = importlib.util.module_from_spec(spec)
    sys.modules['pq_main_bb3'] = main
    spec.loader.exec_module(main)
    g = main.Game.__new__(main.Game)
    g.dungeon = _Dungeon(['#########',
                          '#...~~~.#',
                          '#...~.~.#',
                          '#...~~~.#',
                          '#########'])
    g.dungeon_level = 83
    g.player = types.SimpleNamespace(x=1, y=1)
    keeper = types.SimpleNamespace(x=5, y=2, alive=True, kind='seal_demon_war', tags=['demon'],
                                   treasure={}, footprint=(1, 1))
    rat = types.SimpleNamespace(x=7, y=1, alive=True, kind='giant_rat', tags=['beast'],
                                treasure={}, footprint=(1, 1))
    shrine = types.SimpleNamespace(x=5, y=2, id='mystery_altar_grail')
    g.monsters, g.ground_items, g.pets = [keeper, rat], [shrine], []
    reach = g._reachable_tiles(1, 1)
    assert (5, 2) not in reach and (7, 1) not in reach
    g._bring_within_reach()
    assert (keeper.x, keeper.y) in reach and g.dungeon.is_walkable(keeper.x, keeper.y)
    assert (shrine.x, shrine.y) in reach
    assert (rat.x, rat.y) == (7, 1)                     # an ordinary monster stays where it is


# ---------------------------------------------------------------- saves and files
def test_a_save_that_will_not_read_is_kept_not_overwritten(tmp_path, monkeypatch):
    import save_system
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    (tmp_path / 'save_cain.pkl').write_bytes(b'not a pickle')
    assert save_system.load_game('cain') is None
    kept = save_system.set_aside_save('cain')
    assert kept and os.path.exists(kept) and '.unreadable-' in kept
    assert not os.path.exists(tmp_path / 'save_cain.pkl')
    src = _src('main.py')
    assert 'set_aside_save(player_name)' in src and "getattr(game, '_run_over', False)" in src
    assert 'self.level_mgr._bind_uniques()' in src[src.index('def load_state'):]


def test_a_damaged_score_table_does_not_stop_the_game(tmp_path, monkeypatch):
    import highscore_system as hs
    f = tmp_path / 'highscores.json'
    monkeypatch.setattr(hs, '_SCORE_FILE', str(f))
    f.write_text(json.dumps([1, None, {'name': 'A'}, {'name': 'B', 'score': 'ten'},
                             {'name': 'C', 'score': 50, 'level': None}]), encoding='utf-8')
    rows = hs._load()
    assert [r['name'] for r in rows] == ['C'] and rows[0]['level'] == 0
    hs.add_score('D', 70, 'A', 3, 4, 5, False)
    assert [r['name'] for r in hs._load()] == ['D', 'C']


def test_a_damaged_answer_time_file_does_not_cost_the_answer(tmp_path, monkeypatch):
    """The bookkeeping ran before the quiz's callback and raised, so the
    attack was never resolved."""
    import quiz_engine
    monkeypatch.setattr(quiz_engine, '_answer_times_path', lambda: str(tmp_path / 'answer_times.json'))
    (tmp_path / 'answer_times.json').write_text('{"math|1": 5}', encoding='utf-8')
    qe = quiz_engine.QuizEngine.__new__(quiz_engine.QuizEngine)
    qe._answer_times = {'math|1': {'n': 1, 'seconds': 2.0, 'right': 1, 'seconds_right': 2.0}}
    qe._persist_answer_times()                          # must not raise
    src = _src('quiz_engine.py')
    at = src.index('    def _end(self, success')
    body = src[at:at + 1800]
    assert body.index('callback, self.callback = self.callback, None') < body.index('if self.on_complete:')
    assert 'finally:' in body


# ---------------------------------------------------------------- quiz content
def test_the_maths_bank_keys_that_were_wrong():
    q = _data('questions', 'math.json')
    by = {e['question']: e for e in q}
    assert by['Round 65 to nearest 10?']['answer'] == '70'
    for e in q:
        assert '∛' not in e['question'], e['question']        # the body font has no cube-root sign
        from fractions import Fraction
        if e.get('topic') == 'Fraction Arithmetic' and '/' in e['answer']:
            key = Fraction(e['answer'])
            for c in e['choices']:
                if c != e['answer'] and '/' in c:
                    assert Fraction(c) != key, e['question']


def test_pandoras_coffer_can_pay_and_the_fleece_quiz_ends():
    assert 'success = (not success) and _wrong >= 1' in _src('game_divine.py')
    import mystery_system
    for mid in ('fleece', 'mimir'):
        ch = mystery_system.MYSTERIES[mid]['challenge']
        assert ch['max_chain'] == ch['threshold']


# ---------------------------------------------------------------- pictures
def test_an_unidentified_thing_shows_a_stand_in_not_its_true_picture():
    import renderer
    tiles = os.path.join(ROOT, 'assets', 'tiles', 'items')
    for kind in ('potion', 'wand', 'scroll', 'spellbook', 'ring', 'amulet'):
        for k in range(renderer.UNKNOWN_LOOKS):
            assert os.path.exists(os.path.join(tiles, f'unknown_{kind}_{k}.png')), (kind, k)
    potion = make_item_by_id('potion', 'potion_of_healing')
    sid = renderer.unknown_sprite_id(potion)
    assert sid.startswith('unknown_potion_') and sid == renderer.unknown_sprite_id(potion)
    assert renderer.unknown_sprite_id(make_item_by_id('weapon', 'excalibur')) is None
    assert 'unknown_sprite_id(item)' in _src('game_render.py')
    assert 'self.renderer.is_item_known  = self._item_is_known' in _src('main.py')


def test_every_recipe_has_a_picture_under_the_name_the_menu_asks_for():
    """The menu asks for recipe_<id>. The 364 pictures that existed were
    named for an older recipe set: every recipe was a green asterisk."""
    tiles = os.path.join(ROOT, 'assets', 'tiles', 'items')
    recipes = _data('items', 'recipes.json')
    assert len(recipes) > 800
    for rid in recipes:
        assert os.path.exists(os.path.join(tiles, f'recipe_{rid}.png')), rid
    orphans = [f for f in os.listdir(tiles) if f.startswith('recipe_') and f[7:-4] not in recipes]
    assert not orphans, orphans[:5]


def test_the_art_tool_for_the_tiles_is_not_hidden_from_git():
    """`ENV/` in .gitignore matched tools/content/art/env on Windows, so the
    module that draws the dungeon tiles was in no commit."""
    gi = open(os.path.join(ROOT, '.gitignore'), encoding='utf-8').read()
    assert '!tools/content/art/env/' in gi
