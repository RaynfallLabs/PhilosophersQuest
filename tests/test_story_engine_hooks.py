"""The engine pieces the new NPC stories need (ENCOUNTER_STORIES_DRAFT Part J3),
on a real headless Game with small fixture encounters:

* ``fight`` as a list or a count (group fights), four-way reachable spawns;
* ``per_miss`` consequences and ``play_all`` rounds (Setne's senet sinking),
  with ``fail_by_correct`` reading a fail by rounds won;
* Setne's Tomb: the sealed room, the two ghosts, the door, the total loss that
  throws the hero up a floor and walls the door for good;
* the Book of Thoth: read path (not consumed, spent), the altar (refused
  unread, kept on time, kept late), ``lapse_mode: callback``, the dead coming
  (``after_oath_due``, ``oath_lapse``, ``oath_break`` with a group fight);
* per-person ``last_line`` and ``people``;
* the Green Girdle and the Green Knight's return blow;
* ``flag.deaths_lost_turn`` and Death's pursuit;
* The Gate's per-person lines table and its run-start schedule;
* the new rewards (``gold_pct_loss``, ``gold_pct``, floor-long effects) and the
  effects porter / light / sickly; the new accessories' fields.

Fixture content only: the converted stories are written by the content pass
(data/npc_encounters.json, data/flavor_encounters.json). All of this is deep,
rare or late, so it is proven here, not play-tested (CLAUDE.md play-test rule).
"""
import copy
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=11, name='__test_story_hooks__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    g.quiz_engine.is_mastered = lambda *_a, **_k: False    # never auto-pass a round
    return g


def _key(g, k):
    g._npc_encounter_input(k)


def _result(success, correct=0, asked=1):
    from quiz_engine import QuizResult
    return QuizResult(success=success, score=correct, correct=correct, asked=asked)


def _answer(g, right: bool):
    """Answer the quiz engine's current question, then move on as the
    result timer would."""
    qe = g.quiz_engine
    q = qe.current_question
    ans = str(q['answer']).strip()
    if right:
        qe.answer(ans)
    else:
        qe.answer(next(c for c in q['choices'] if str(c).strip() != ans))
    qe._advance()


# ------------------------------------------------------------------ fixtures
# Shaped as the content pass will write H00, C19 and C18 (small, but every
# engine field the real stories use).

SETNE = {
    'tag': 'flv_setne_tomb', 'name': 'Neferkaptah', 'symbol': '@', 'color': [200, 190, 150],
    'sprite_id': 'npc_neferkaptah', 'min_level': 45, 'max_level': 65,
    'role': 'story', 'stakes': 'high', 'band': [45, 65], 'callback_only': True,
    'tragedy': 'unsavable', 'person': {'id': 'neferkaptah', 'name': 'Neferkaptah'},
    'text': 'Two ghosts sit at a senet board beside a book that names the things in your pack.',
    'options': [
        {'label': 'Listen to Ahwere', 'outcome': 'That is Merib\'s footprint; he was six.',
         'then': 'options', 'deeds': ['met.ahwere', 'told.ahwere_story'],
         'people': [{'id': 'ahwere', 'name': 'Ahwere', 'status': 'lost'},
                    {'id': 'merib', 'name': 'Merib', 'status': 'lost'}]},
        {'label': 'Play Neferkaptah at senet for the book, staking yourself',
         'quiz': {'subject': 'philosophy', 'tier': 3, 'mode': 'escalator_threshold',
                  'threshold': 2, 'total_qs': 3, 'play_all': True},
         'per_miss': [
             {'text': 'Your feet go into the stone as if it were mud.',
              'cost': {'type': 'max_hp_pct', 'amount': 10}},
             {'text': 'You are in to the waist.',
              'effect': {'effect': 'paralyzed', 'duration': 6}},
             {'text': 'The stone closes round your throat.'}],
         'pass': {'outcome': '"So. Read it, and bring it back."',
                  'reward': {'type': 'specific_item', 'item_type': 'spellbook',
                             'item_id': 'book_of_thoth'},
                  'oath': {'id': 'thoth_return', 'to': 'Neferkaptah',
                           'what': 'Read the Book of Thoth once, then lay it on an altar.',
                           'item_id': 'book_of_thoth', 'due_floors': [8, 15],
                           'lapse_mode': 'callback'},
                  'schedule': [{'encounter': 'flv_dead_come_for_the_book',
                                'after_floors': [1, 3], 'after_oath_due': 'thoth_return',
                                'requires': {'oath_status': {'thoth_return': 'open'}}}],
                  'thread': {'id': 'thoth_home', 'hint': 'Somewhere above, a drowned woman is counting floors.'},
                  'deeds': ['told.won_senet']},
         'fail': {'outcome': '"Not you, then."', 'deeds': ['told.lost_senet']},
         'fail_by_correct': {
             '0': {'outcome': 'The stone closes over your mouth. A wet hand pulls you up.',
                   'deeds': ['told.lost_senet', 'flag.thoth_lost'], 'expel_up': True}}},
        {'label': 'Leave the book, because she asked',
         'requires': {'deeds_all': ['told.ahwere_story']},
         'karma': 1, 'karma_kind': 'forgo', 'deeds': ['forgo.book_of_thoth'],
         'outcome': '"Thank you," she says. "No one has ever left it."',
         'people': [{'id': 'ahwere', 'name': 'Ahwere', 'last_line': 'No one has ever left it.'}],
         'seal_door': True},
        {'label': 'Leave the tomb', 'outcome': 'The door closes behind you, and is a wall.',
         'deeds': ['met.neferkaptah'], 'seal_door': True},
    ],
}

DEAD = {
    'tag': 'flv_dead_come_for_the_book', 'name': 'Neferkaptah', 'symbol': '@',
    'color': [200, 190, 150], 'sprite_id': 'npc_neferkaptah', 'min_level': 50, 'max_level': 98,
    'role': 'story', 'stakes': 'high', 'band': [50, 98], 'callback_only': True, 'hostile': True,
    'person': {'id': 'neferkaptah', 'name': 'Neferkaptah'},
    'requires': {'oath_status': {'thoth_return': 'open'}},
    'text': 'The torches burn blue. "You swore," he says.',
    'options': [
        {'label': 'Give the book back', 'requires': {'items_any': ['book_of_thoth']},
         'cost': {'type': 'triggered_item_id', 'item_id': 'book_of_thoth'},
         'oath_lapse': 'thoth_return', 'thread_close': 'thoth_home',
         'deeds': ['told.thoth_returned_late'], 'outcome': 'He takes it.'},
        {'label': '"I don\'t have it any more."', 'requires': {'items_none': ['book_of_thoth']},
         'oath_lapse': 'thoth_return', 'deeds': ['told.thoth_lost_book'],
         'fight': [{'monster_id': 'neferkaptah_risen'}, {'monster_id': 'mummy', 'count': 4}],
         'outcome': 'The water rises over your boots.'},
        {'label': 'Refuse. The book is yours now.', 'requires': {'items_any': ['book_of_thoth']},
         'oath_break': 'thoth_return', 'karma': -1, 'karma_kind': 'betray',
         'deeds': ['wrong.kept_thoth'],
         'fight': [{'monster_id': 'neferkaptah_risen', 'count': 1},
                   {'monster_id': 'mummy', 'count': 6}],
         'outcome': '"Then you will keep it the way I kept it."'},
    ],
}

GATE = {
    'tag': 'flv_the_gate', 'name': 'Old Fisherman', 'symbol': '@', 'color': [180, 170, 150],
    'sprite_id': 'npc_traveler', 'min_level': 94, 'max_level': 98,
    'role': 'story', 'stakes': 'light', 'band': [94, 98], 'callback_only': True,
    'text': 'A gate of plain wood, and an old fisherman with a ring of keys.',
    'options': [
        {'label': '"Tell me about them."', 'outcome': 'He opens the ledger.',
         'people_lines': {'table': 'gate', 'max': 6,
                          'after': "He closes the ledger. 'The rest is between them and me.'"}},
        {'label': 'Walk on', 'outcome': 'He goes back to his net.'},
    ],
}


@pytest.fixture
def story_pool(monkeypatch):
    """Put the fixtures where the engine looks encounters up by tag."""
    import encounter_schema
    import flavor_encounters
    extra = [encounter_schema.normalise(copy.deepcopy(e), source='flavor')
             for e in (SETNE, DEAD, GATE)]
    monkeypatch.setattr(flavor_encounters, 'FLAVOR_ENCOUNTERS',
                        list(flavor_encounters.FLAVOR_ENCOUNTERS) + extra)
    return {e['tag']: e for e in extra}


def _descend_to(g, level):
    while g.dungeon_level < level:
        g._change_level(g.dungeon_level + 1, enter_from_top=True)
        g.monsters[:] = [m for m in g.monsters if getattr(m, '_encounter_room', None) is not None
                         or getattr(m, '_flavor_encounter_tag', None) or getattr(m, '_npc_encounter_tag', None)]
        g.dungeon.traps = {}


def _tomb(g, story_pool):
    """Roll the tomb onto floor 3 and walk down to it."""
    g._setne = {'floor': 3, 'spawned': False, 'sealed': False, 'room': None}
    g._flavor_encounter_levels = {}
    g._npc_encounter_levels = {}
    _descend_to(g, 3)
    ghosts = [m for m in g.monsters if getattr(m, '_flavor_encounter_tag', None) == 'flv_setne_tomb']
    return ghosts


def _open_tomb(g, ghosts):
    nef = next(m for m in ghosts if m.name == 'Neferkaptah')
    assert g._start_flavor_encounter(nef)
    _key(g, pygame.K_RETURN)
    return nef


def _labels(g):
    return [o['label'] for _i, o in g._npc_visible_options()]


def _choose(g, label):
    labels = _labels(g)
    _key(g, (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)[labels.index(label)])


# ------------------------------------------------------------------ group fights

def test_fight_spec_shapes():
    from encounter_schema import fight_entries
    assert fight_entries('ogre') == [('ogre', 1)]
    assert fight_entries({'monster_id': 'ogre', 'count': 2}) == [('ogre', 2)]
    assert fight_entries([{'monster_id': 'neferkaptah_risen'}, {'monster_id': 'mummy', 'count': 6}]) \
        == [('neferkaptah_risen', 1), ('mummy', 6)]
    assert fight_entries({'monster_id': 'mummy', 'count': 99}) == [('mummy', 8)]
    assert fight_entries([{'count': 2}, 7]) == []


def test_group_fight_spawns_every_body_reachable_and_apart():
    g = _game()
    px, py = g.player.x, g.player.y
    out = g._spawn_outcome_fight([{'monster_id': 'neferkaptah_risen'},
                                  {'monster_id': 'mummy', 'count': 6}])
    assert [m.kind for m in out].count('mummy') == 6
    assert sum(m.kind == 'neferkaptah_risen' for m in out) == 1
    reach = g._reachable_tiles(px, py)
    tiles = [(m.x, m.y) for m in out]
    assert len(set(tiles)) == len(tiles)                  # one body a tile
    assert (px, py) not in tiles
    assert all(t in reach for t in tiles)                 # four-way reachable
    assert all(m._aware and m.alive for m in out)
    # Neferkaptah came first, so he stands nearest.
    d = lambda m: max(abs(m.x - px), abs(m.y - py))      # noqa: E731
    assert d(out[0]) == min(d(m) for m in out)


def test_two_ogres_from_a_count_and_an_outcome():
    g = _game()
    g._apply_outcome_deeds({'fight': {'monster_id': 'ogre', 'count': 2}}, 'fx')
    assert sum(m.kind == 'ogre' for m in g.monsters) == 2


# ------------------------------------------------------------------ quiz engine

def test_play_all_plays_every_round_and_fires_on_each():
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe.is_mastered = lambda *_a, **_k: False
    seen, results = [], []
    qe.start_quiz('escalator_threshold', 'philosophy', 3, results.append, threshold=2,
                  total_qs=3, play_all=True,
                  on_each=lambda ok, c, w: seen.append((ok, c, w)))
    tiers = [qe.tier]
    for right in (False, True, False):
        q = qe.current_question
        ans = str(q['answer']).strip()
        qe.answer(ans if right else next(c for c in q['choices'] if str(c).strip() != ans))
        qe._advance()
        tiers.append(qe.tier)
    assert seen == [(False, 0, 1), (True, 1, 1), (False, 1, 2)]
    assert len(results) == 1 and not results[0].success and results[0].correct == 1
    assert tiers[:3] == [3, 4, 5]                         # climbs after every round
    # Cleared at the end: the next quiz has no per-answer hook.
    assert qe._on_each is None and qe.play_all is False


def test_without_play_all_a_miss_still_ends_the_quiz():
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe.is_mastered = lambda *_a, **_k: False
    results = []
    qe.start_quiz('threshold', 'philosophy', 3, results.append, threshold=2, total_qs=3)
    q = qe.current_question
    qe.answer(next(c for c in q['choices'] if str(c).strip() != str(q['answer']).strip()))
    qe._advance()
    assert len(results) == 1 and results[0].asked == 1


# ------------------------------------------------------------------ Setne's Tomb

def test_tomb_floor_rolled_in_45_to_65_off_the_shared_stream():
    import setne_tomb
    state = random.getstate()
    floors = {setne_tomb.roll_for_new_run() for _ in range(50)}
    assert random.getstate() == state                     # the shared stream is untouched
    assert all(45 <= f <= 65 and f != 60 for f in floors)
    rng = random.Random(4)
    assert {setne_tomb.roll_floor(rng) for _ in range(2000)} == set(setne_tomb.candidate_floors())
    g = _game()
    assert 45 <= g._setne['floor'] <= 65


def test_no_tomb_without_its_encounter_data():
    g = _game()
    g._setne = {'floor': 2, 'spawned': False, 'sealed': False, 'room': None}
    _descend_to(g, 2)
    assert not g._setne['spawned']


def test_tomb_room_is_sealed_but_reachable_with_two_ghosts(story_pool):
    from dungeon import DOOR
    g = _game()
    ghosts = _tomb(g, story_pool)
    assert g._setne['spawned'] and len(ghosts) == 2
    room = g._setne['room']
    dx, dy = room['door']
    assert g.dungeon.tiles[dy][dx] == DOOR
    # Sealed: the chamber touches the level only through its one door.
    chamber = {tuple(t) for t in room['chamber']}
    for (x, y) in chamber:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in chamber and (nx, ny) != (dx, dy):
                assert not g.dungeon.is_walkable(nx, ny)
    reach = g._reachable_tiles(g.player.x, g.player.y)
    assert all((m.x, m.y) in reach for m in ghosts)      # four-way, through the door
    assert {m.name for m in ghosts} == {'Neferkaptah', 'Ahwere'}
    assert all(m.proper_noun for m in ghosts)
    # The first opening of the door says what it is.
    g._setne_door_opened(dx, dy)
    assert 'never meant to open' in ' '.join(str(e[0]) for e in g.msg_log.entries)


def test_senet_sinks_the_hero_round_by_round_and_a_total_loss_expels(story_pool):
    from dungeon import WALL
    import deeds
    g = _game()
    ghosts = _tomb(g, story_pool)
    room = g._setne['room']
    g.player.max_hp = g.player.hp = 200
    _open_tomb(g, ghosts)
    _choose(g, 'Play Neferkaptah at senet for the book, staking yourself')
    assert g.quiz_engine.play_all
    _answer(g, False)                                    # ankles: 10% of max HP, for the run
    assert g.player.max_hp == 180
    assert not g.player.has_effect('paralyzed')
    _answer(g, False)                                    # the waist: held fast
    assert g.player.has_effect('paralyzed')
    _answer(g, False)                                    # the neck: the last round is played too
    # Lost every round: the fail_by_correct '0' branch.
    assert 'closes over your mouth' in g._npc_outcome_text
    assert g._npc_outcome_text.startswith('Your feet go into the stone')   # the sinking, in order
    assert deeds.has(g._deeds, 'flag.thoth_lost')
    tomb_floor = g.dungeon_level
    g._npc_outcome_continue()                            # closing the page throws the hero out
    assert g.dungeon_level == tomb_floor - 1
    assert g._setne['sealed']
    # The door never reappears: back on the tomb floor it is wall.
    g._change_level(tomb_floor, enter_from_top=True)
    dx, dy = room['door']
    assert g.dungeon.tiles[dy][dx] == WALL
    assert not any(getattr(m, '_flavor_encounter_tag', None) == 'flv_setne_tomb'
                   and m.alive for m in g.monsters)
    assert not any(getattr(i, 'id', '') == 'book_of_thoth' for i in g.player.inventory)


def test_one_round_won_is_the_plain_fail_and_no_expulsion(story_pool):
    import deeds
    g = _game()
    ghosts = _tomb(g, story_pool)
    _open_tomb(g, ghosts)
    _choose(g, 'Play Neferkaptah at senet for the book, staking yourself')
    for right in (True, False, False):
        _answer(g, right)
    assert g._npc_outcome_text.endswith('"Not you, then."')
    floor = g.dungeon_level
    g._npc_outcome_continue()
    assert g.dungeon_level == floor and not g._setne['sealed']
    assert deeds.has(g._deeds, 'told.lost_senet') and not deeds.has(g._deeds, 'flag.thoth_lost')


def test_listening_reveals_the_forgo_and_writes_people(story_pool):
    import deeds
    g = _game()
    ghosts = _tomb(g, story_pool)
    _open_tomb(g, ghosts)
    assert 'Leave the book, because she asked' not in _labels(g)
    _choose(g, 'Listen to Ahwere')
    assert g._deeds['people']['ahwere']['status'] == 'lost'
    assert g._deeds['people']['merib']['status'] == 'lost'
    g._npc_outcome_continue()
    assert 'Leave the book, because she asked' in _labels(g)
    k0 = g.karma
    _choose(g, 'Leave the book, because she asked')
    assert g.karma == k0 + 1                              # forgo (gate off: applied as today)
    assert deeds.count(g._deeds, tag='virtue:forgo') == 1
    assert g._deeds['people']['ahwere']['last_line'] == 'No one has ever left it.'
    g._npc_outcome_continue()
    assert g._setne['sealed']                             # the door closes behind you
    assert g.dungeon.tiles[g._setne['room']['door'][1]][g._setne['room']['door'][0]] == 0


def _win_the_book(g, story_pool):
    ghosts = _tomb(g, story_pool)
    _open_tomb(g, ghosts)
    _choose(g, 'Play Neferkaptah at senet for the book, staking yourself')
    _answer(g, True)
    _answer(g, True)                                      # two won: the quiz ends at the threshold
    assert 'bring it back' in g._npc_outcome_text
    g._npc_outcome_continue()
    return next(i for i in g.player.inventory if getattr(i, 'id', '') == 'book_of_thoth')


def test_winning_swears_the_return_and_schedules_the_dead_after_the_due_floor(story_pool):
    import deeds
    g = _game()
    book = _win_the_book(g, story_pool)
    o = g._deeds['oaths']['thoth_return']
    assert o['status'] == 'open' and o['lapse_mode'] == 'callback'
    assert 3 + 8 <= o['due_floor'] <= 3 + 15
    cb = [p for p in g._deeds['pending'] if p.get('spec', {}).get('encounter') == 'flv_dead_come_for_the_book']
    assert len(cb) == 1
    assert o['due_floor'] + 1 <= cb[0]['target'] <= o['due_floor'] + 3
    assert cb[0]['oath'] == 'thoth_return'
    assert deeds.has(g._deeds, 'told.won_senet') and book is not None
    # High stakes, passed: the engine writes virtue:steadfast.
    assert deeds.count(g._deeds, tag='virtue:steadfast') == 1


def test_a_callback_oath_does_not_lapse_silently_on_its_due_floor(story_pool):
    g = _game()
    _win_the_book(g, story_pool)
    o = g._deeds['oaths']['thoth_return']
    g.player.deepest_floor_reached = o['due_floor'] + 1
    g._lapse_due_oaths(o['due_floor'] + 1)
    assert o['status'] == 'open'


def test_reading_spends_the_book_but_keeps_it(story_pool):
    from game_states import STATE_PLAYER
    g = _game()
    book = _win_the_book(g, story_pool)
    g._read_book_of_thoth(book)
    g.quiz_engine._end(success=True)
    assert g.state == STATE_PLAYER
    assert book in g.player.inventory and book.spent
    assert book.name == 'Book of Thoth (Read)'
    n = len(g.msg_log.entries)
    g._read_book_of_thoth(book)                           # a second read does nothing
    assert g.state == STATE_PLAYER
    assert 'They will not do it twice' in str(g.msg_log.entries[-1][0]) and len(g.msg_log.entries) == n + 1


def test_a_failed_read_curses_spends_and_still_owes(story_pool):
    g = _game()
    book = _win_the_book(g, story_pool)
    hp = g.player.hp
    g._read_book_of_thoth(book)
    g.quiz_engine._end(success=False)
    assert g.player.hp < hp and g.player.has_effect('stunned')
    assert book in g.player.inventory and book.spent
    assert g._deeds['oaths']['thoth_return']['status'] == 'open'


def _altar_under_hero(g):
    from dungeon import ALTAR
    g.dungeon.tiles[g.player.y][g.player.x] = ALTAR


def test_the_altar_refuses_the_book_unread(story_pool):
    g = _game()
    book = _win_the_book(g, story_pool)
    _altar_under_hero(g)
    g._do_drop_item(book)
    assert book in g.player.inventory
    assert g._deeds['oaths']['thoth_return']['status'] == 'open'
    assert 'read it first' in str(g.msg_log.entries[-1][0])


def test_laid_on_an_altar_in_time_keeps_the_oath(story_pool):
    import deeds
    g = _game()
    book = _win_the_book(g, story_pool)
    g._read_book_of_thoth(book)
    g.quiz_engine._end(success=True)
    _altar_under_hero(g)
    k0 = g.karma
    g._do_drop_item(book)
    assert book not in g.player.inventory and book not in g.ground_items
    assert g._deeds['oaths']['thoth_return']['status'] == 'kept'
    assert g.karma == k0 + 1                              # oath, earliest open block
    assert deeds.count(g._deeds, tag='virtue:kept') == 1
    assert g._deeds['threads']['thoth_home']['status'] == 'closed'
    assert 'gone home' in ' | '.join(str(e.get('text', e) if isinstance(e, dict) else e)
                                     for e in g._chronicle)


def test_laid_on_an_altar_late_is_kept_late_and_calls_off_the_dead(story_pool):
    import deeds
    g = _game()
    book = _win_the_book(g, story_pool)
    g._read_book_of_thoth(book)
    g.quiz_engine._end(success=False)                    # read badly: still owed
    o = g._deeds['oaths']['thoth_return']
    g.player.deepest_floor_reached = o['due_floor'] + 1   # past the due floor, the dead not yet come
    _altar_under_hero(g)
    k0 = g.karma
    g._do_drop_item(book)
    assert o['status'] == 'kept_late'
    assert g.karma == k0                                  # 0 karma
    assert deeds.count(g._deeds, tag='virtue:kept') == 0  # does not count toward 'faithful'
    assert deeds.count(g._deeds, tag='vice:lapsed') == 0
    assert deeds.payload(g._deeds, 'kept.thoth_return', 'late') is True
    assert not [p for p in g._deeds['pending']
                if p.get('spec', {}).get('encounter') == 'flv_dead_come_for_the_book']
    assert 'say a child' in g._deeds['threads']['thoth_home']['closed_line']


def _the_dead_arrive(g, story_pool):
    """Walk to the callback's floor: the dead find the hero there (hostile:
    the scene opens on arrival, beside the hero, with no walk-away)."""
    from game_states import STATE_NPC_ENCOUNTER
    cb = next(p for p in g._deeds['pending']
              if p.get('spec', {}).get('encounter') == 'flv_dead_come_for_the_book')
    g.player.deepest_floor_reached = cb['target'] - 1
    g._flavor_encounter_levels = {}
    g._change_level(cb['target'], enter_from_top=True)
    assert g.state == STATE_NPC_ENCOUNTER
    npc = g._npc_encounter_monster
    assert npc._flavor_encounter_tag == 'flv_dead_come_for_the_book'
    assert max(abs(npc.x - g.player.x), abs(npc.y - g.player.y)) <= 2
    g.monsters[:] = [npc]
    _key(g, pygame.K_ESCAPE)                              # no walking away
    assert g.state == STATE_NPC_ENCOUNTER
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_ESCAPE)
    assert g.state == STATE_NPC_ENCOUNTER and g._npc_encounter_phase == 'options'
    return npc


def test_the_dead_come_and_refusing_breaks_the_oath_with_a_group_fight(story_pool):
    g = _game()
    book = _win_the_book(g, story_pool)
    g._read_book_of_thoth(book)
    g.quiz_engine._end(success=True)
    _the_dead_arrive(g, story_pool)
    assert _labels(g) == ['Give the book back', 'Refuse. The book is yours now.']
    k0 = g.karma
    _choose(g, 'Refuse. The book is yours now.')
    assert g._deeds['oaths']['thoth_return']['status'] == 'broken'
    assert g.karma == k0 - 1
    kinds = [m.kind for m in g.monsters if m.alive and not getattr(m, '_flavor_encounter_tag', None)]
    assert kinds.count('neferkaptah_risen') == 1 and kinds.count('mummy') == 6
    assert book in g.player.inventory


def test_the_dead_come_for_a_promise_not_a_pocket(story_pool):
    g = _game()
    book = _win_the_book(g, story_pool)
    g.player.remove_from_inventory(book)                  # dropped, stashed or lost
    _the_dead_arrive(g, story_pool)
    assert _labels(g) == ['"I don\'t have it any more."']
    _choose(g, '"I don\'t have it any more."')
    o = g._deeds['oaths']['thoth_return']
    assert o['status'] == 'lapsed'                        # a lapse, not a betrayal
    kinds = [m.kind for m in g.monsters if m.alive and not getattr(m, '_flavor_encounter_tag', None)]
    assert kinds.count('neferkaptah_risen') == 1 and kinds.count('mummy') == 4


def test_giving_it_back_late_lapses_without_a_fight(story_pool):
    g = _game()
    book = _win_the_book(g, story_pool)
    _the_dead_arrive(g, story_pool)
    _choose(g, 'Give the book back')
    assert g._deeds['oaths']['thoth_return']['status'] == 'lapsed'
    assert book not in g.player.inventory
    assert not [m for m in g.monsters if m.alive and m.kind == 'neferkaptah_risen']


def test_a_lost_callback_lapses_its_open_oath():
    import deeds
    g = _game()
    reg = g._deeds_reg()
    deeds.swear(reg, 'thoth_return', to='Neferkaptah', what='x', due_floor=10, floor=1, block=1,
                lapse_mode='callback')
    g._callback_lost('flv_dead_come_for_the_book', {'after_oath_due': 'thoth_return'}, 'fx')
    assert reg['oaths']['thoth_return']['status'] == 'lapsed'


# ------------------------------------------------------------------ the Green Girdle

def _green_knight(g):
    from game_magic import _monster_defn
    from monster import Monster
    m = Monster(_monster_defn('green_knight'), g.player.x + 1, g.player.y)
    g.monsters.append(m)
    return m


def _wear_girdle(g):
    from items import make_item_by_id
    girdle = make_item_by_id('armor', 'green_girdle')
    g.player.armor_slots[4] = girdle                      # legs
    return girdle


def test_the_girdle_turns_the_green_knights_return_blow():
    g = _game()
    gk = _green_knight(g)
    _wear_girdle(g)
    gk._has_revived = True                                # his head is back on: his turn
    g.player.hp = 0
    assert g._green_girdle_spares(gk)
    assert g.player.hp == 1
    assert 'You lacked a little loyalty' in str(g.msg_log.entries[-1][0])


def test_no_girdle_or_no_return_blow_no_mercy():
    g = _game()
    gk = _green_knight(g)
    g.player.hp = 0
    gk._has_revived = True
    assert not g._green_girdle_spares(gk)                 # not wearing it
    _wear_girdle(g)
    gk._has_revived = False
    assert not g._green_girdle_spares(gk)                 # his first blows are ordinary


def test_the_girdle_in_the_monster_turn(monkeypatch):
    g = _game()
    gk = _green_knight(g)
    _wear_girdle(g)
    gk._has_revived = True

    def lethal(player):
        player.hp = 0
        return 999, 'The Green Knight swings his axe!'
    monkeypatch.setattr(gk, 'attack', lethal)
    monkeypatch.setattr(gk, 'take_turn', lambda *a, **k: True)
    g.player.hp = 50
    g._do_monster_turns()
    # Alive. (The girdle's own once-a-floor ward may then soften the blow
    # further; the return blow itself never kills.)
    assert g.player.hp >= 1 and not g.player.is_dead()
    assert 'You lacked a little loyalty' in ' '.join(str(e[0]) for e in g.msg_log.entries)


# ------------------------------------------------------------------ Death's lost turn

def _death_adjacent(g, monkeypatch):
    from monster import Monster
    from game_magic import _monster_defn
    try:
        dm = Monster(_monster_defn('death'), g.player.x + 1, g.player.y)
    except KeyError:
        dm = Monster({'id': 'death', 'name': 'Death', 'symbol': 'D', 'color': [0, 0, 0],
                      'hp': 999, 'thac0': 0, 'speed': 10, 'attacks': [], 'ai_pattern': 'aggressive',
                      'resistances': [], 'weaknesses': [], 'min_level': 1},
                     g.player.x + 1, g.player.y)

    def lethal(player):
        player.hp = 0
        return 999, 'Death swings his scythe.'
    monkeypatch.setattr(dm, 'attack', lethal)
    monkeypatch.setattr(dm, 'take_turn', lambda *a, **k: True)
    g.death_pursues = True
    g.death_monster = dm
    monkeypatch.setattr(g, '_death_steps_onto_the_floor', lambda: True)
    return dm


def test_deaths_lost_turn_spares_one_fatal_blow_on_the_ascent(monkeypatch):
    import deeds
    from game_states import STATE_DEAD
    g = _game()
    _death_adjacent(g, monkeypatch)
    deeds.note(g, 'flag.deaths_lost_turn', source='fx')
    g.player.hp = 40
    g._do_monster_turns()
    assert g.player.hp == 40 and g.state != STATE_DEAD
    assert deeds.has(g._deeds, 'flag.deaths_lost_turn_spent')
    assert 'One breath, as promised' in ' '.join(str(e[0]) for e in g.msg_log.entries)
    g._do_monster_turns()                                 # once only
    assert g.state == STATE_DEAD


def test_without_the_deed_death_kills(monkeypatch):
    from game_states import STATE_DEAD
    g = _game()
    _death_adjacent(g, monkeypatch)
    g.player.hp = 40
    g._do_monster_turns()
    assert g.state == STATE_DEAD


# ------------------------------------------------------------------ The Gate

def test_gate_lines_table_reads_people_and_deeds():
    import deeds
    from encounter_schema import people_lines
    import json
    with open(os.path.join(ROOT, 'data', 'gate_lines.json'), encoding='utf-8') as f:
        table = json.load(f)['gate']
    reg = deeds.new_register()
    ctx = {'reg': reg, 'karma': 0, 'stats': {}, 'floor': 95, 'deepest': 95, 'items': set()}
    assert people_lines(table, ctx) == []                 # met nobody: nothing to tell
    deeds.set_person(reg, 'marta', name='Marta Venn', status='aided', floor=3)
    deeds.record(reg, 'saved.marta', floor=3, block=1)
    deeds.set_person(reg, 'silas', name='Silas', status='spared', deserving=False, floor=75)
    deeds.record(reg, 'spared.silas', floor=75, block=8)
    deeds.set_person(reg, 'ostrander', name='Ostrander', status='met', deserving=True, floor=20)
    deeds.record(reg, 'forgo.book_of_thoth', floor=50, block=5)
    deeds.set_person(reg, 'ahwere', name='Ahwere', status='lost', floor=50)
    lines = people_lines(table, ctx)
    assert any(ln.startswith('Marta Venn. Walked out') for ln in lines)
    assert any(ln.startswith('Silas Mordaunt') for ln in lines)
    assert any(ln.startswith('Ostrander. Kept his lamp') for ln in lines)
    assert any(ln.startswith('Ahwere asked me') for ln in lines)
    # Fates first, most recent first: Silas (floor 75) before Marta.
    assert lines.index(next(ln for ln in lines if ln.startswith('Silas'))) < \
        lines.index(next(ln for ln in lines if ln.startswith('Marta')))
    # The robbery line wins over the rescue line (first match in table order).
    deeds.record(reg, 'wrong.robbed_marta', floor=4, block=1)
    assert any(ln.startswith('Marta Venn. Got home without') for ln in people_lines(table, ctx))
    assert len(people_lines(table, ctx, 2)) == 2
    assert reg['karma']['ledger'] == []                   # reading changes nothing


def test_the_gate_tells_the_lines_and_never_touches_karma(story_pool):
    import deeds
    g = _game()
    reg = g._deeds_reg()
    deeds.set_person(reg, 'tansy', name='Tansy', status='saved', floor=66)
    deeds.record(reg, 'saved.tansy', floor=66, block=7)
    g._flavor_encounter_levels = {g.dungeon_level: copy.deepcopy(story_pool['flv_the_gate'])}
    g._maybe_spawn_flavor_npc(g.dungeon_level)
    npc = next(m for m in g.monsters if getattr(m, '_flavor_encounter_tag', None) == 'flv_the_gate')
    k0, j0 = g.karma, getattr(g, '_judgment_text', '')
    assert g._start_flavor_encounter(npc)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_1)
    text = g._npc_outcome_text
    assert text.startswith('He opens the ledger.')
    assert 'Tansy. Flies again.' in text
    assert text.rstrip().endswith("'The rest is between them and me.'")
    assert g.karma == k0 and getattr(g, '_judgment_text', '') == j0


def test_the_gate_is_scheduled_at_run_start_in_94_to_98(story_pool):
    g = _game()
    gate = [p for p in g._deeds['pending'] if p.get('spec', {}).get('encounter') == 'flv_the_gate']
    assert len(gate) == 1 and 94 <= gate[0]['target'] <= 98


def test_no_gate_scheduled_while_the_content_is_missing():
    g = _game()
    assert not [p for p in g._deeds['pending'] if p.get('spec', {}).get('encounter') == 'flv_the_gate']


# ------------------------------------------------------------------ rewards and effects

def test_gold_pct_loss_and_gold_pct_take_and_give_a_share_of_the_own_purse():
    g = _game()
    g.player_gold = 1000
    g._apply_npc_reward({'type': 'gold_pct_loss', 'amount': 15})
    assert g.player_gold == 850
    g._apply_npc_reward({'type': 'gold_pct', 'amount': 20})
    assert g.player_gold == 1020
    g.player_gold = 0
    g._apply_npc_reward({'type': 'gold_pct_loss', 'amount': 15})
    assert g.player_gold == 0


def test_porter_lasts_whole_floors_then_ends():
    g = _game()
    base = g.player.get_carry_limit()
    g._apply_npc_reward({'type': 'effect', 'effect': 'porter', 'floors': 2})
    from status_effects import PORTER_CARRY_BONUS, EFFECT_INFO, BUFFS
    assert 'porter' in EFFECT_INFO and 'porter' in BUFFS
    assert g.player.get_carry_limit() == base + PORTER_CARRY_BONUS
    g._change_level(2, enter_from_top=True)
    assert g.player.has_effect('porter')
    g._change_level(1, enter_from_top=False)              # a revisit does not count
    g._change_level(2, enter_from_top=True)
    assert g.player.has_effect('porter')
    g._change_level(3, enter_from_top=True)
    assert not g.player.has_effect('porter')
    assert g.player.get_carry_limit() == base


def test_light_widens_sight_and_sickly_drains_stamina_faster():
    from status_effects import LIGHT_SIGHT_BONUS, DEBUFFS
    g = _game()
    r = g.player.get_sight_radius()
    g.player.add_floor_effect('light', 2)
    assert g.player.get_sight_radius() == r + LIGHT_SIGHT_BONUS
    assert 'sickly' in DEBUFFS
    g.player.sp = g.player.max_sp = 100
    for _ in range(8):
        g._tick_sp()
    plain = 100 - g.player.sp
    g.player.sp = 100
    g.player.add_effect('sickly', 50)
    for _ in range(8):
        g._tick_sp()
    assert 100 - g.player.sp == 2 * plain


def test_raphaels_gall_spares_the_eyes_once():
    from items import make_item_by_id
    g = _game()
    gall = make_item_by_id('artifact', 'raphaels_gall')
    g.player.inventory.append(gall)
    g.player.add_effect('blinded', 10)
    assert not g.player.has_effect('blinded') and gall not in g.player.inventory
    g.player.add_effect('blinded', 10)
    assert g.player.has_effect('blinded')


def test_story_accessories_time_bound_and_calm():
    from items import make_item_by_id
    g = _game()
    p = g.player
    base = p.get_quiz_extra_seconds('math')
    cog = make_item_by_id('accessory', 'brass_wardens_cog')
    p.amulet_slot = cog
    assert p.get_quiz_extra_seconds('math') == base + 2
    bracelet = make_item_by_id('accessory', 'black_string_bracelet')
    p.accessory_slots[0] = bracelet
    assert p.get_quiz_extra_seconds('math') == base + 5
    ok, _msg = p.try_unequip_slot(bracelet)
    assert not ok                                         # it does not come off
    brand = make_item_by_id('accessory', 'azaraels_brand')
    assert brand.bound_to_wielder and brand.effects == {'stat': 'STR', 'amount': 4}
    charm = make_item_by_id('accessory', 'locust_charm')
    p.amulet_slot = charm
    from game_magic import _monster_defn
    from monster import Monster
    loc = Monster(_monster_defn('abyssal_locust'), p.x + 1, p.y)
    cultist = Monster(_monster_defn('locust_cultist'), p.x - 1, p.y)
    assert g._locust_calmed(loc) and not g._locust_calmed(cultist)
    loc.take_damage(1)
    assert not g._locust_calmed(loc)                      # struck, it remembers
    p.amulet_slot = None
    assert not g._locust_calmed(Monster(_monster_defn('abyssal_locust'), p.x, p.y + 1))
