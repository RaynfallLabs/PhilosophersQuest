"""Bug bash 5 (2026-10-17): the encounter engine, the Road, oaths, quit /
settle / reload and the Journal plumbing, on a real headless Game.

Each test names the finding it pins (``_bugbash_2026_10_17/<angle>/
FINDINGS.md``). The content is rare, randomized or deep (Setne's tomb on
floors 45-65, oaths sworn to the dead, a quit at senet's first question), so
it cannot be play-tested on demand: these are the proof.
"""
import copy
import os
import random
import shutil
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=5, name='__test_bb5__'):
    import items
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.state = STATE_PLAYER
    return g


def _enc(tag):
    import economy
    from game_road import _encounter_by_tag
    src, e = _encounter_by_tag(tag)
    assert e is not None, tag
    return src, economy.price_encounter(copy.deepcopy(e))


def _npc_for(g, enc, flavor):
    from monster import Monster
    m = Monster({'id': 'npc_traveler', 'name': enc['name'], 'symbol': '@', 'color': [1, 1, 1],
                 'hp': 1, 'thac0': 20, 'speed': 0, 'attacks': [], 'ai_pattern': 'sessile',
                 'resistances': [], 'weaknesses': [], 'min_level': 1, 'is_allied': True,
                 'harvest_tier': 0, 'harvest_threshold': 99, 'ingredient_id': None},
                g.player.x + 1, g.player.y)
    setattr(m, '_flavor_encounter_tag' if flavor else '_npc_encounter_tag', enc['tag'])
    g.monsters.append(m)
    return m


def _open(g, tag):
    """Put encounter ``tag`` on this floor beside the hero and open it."""
    src, e = _enc(tag)
    flavor = src == 'flavor'
    m = _npc_for(g, e, flavor)
    (g._flavor_encounter_levels if flavor else g._npc_encounter_levels)[g.dungeon_level] = e
    g._npc_open(e, m, flavor=flavor)
    return e, m


def _choose(g, raw_index, item=None):
    g._npc_show_options()
    pairs = [p for p in g._npc_visible_options() if p[0] == raw_index]
    assert pairs, (raw_index, [p[0] for p in g._npc_visible_options()])
    g._npc_selected_index, g._npc_selected_option = pairs[0]
    g._apply_npc_choice(pairs[0][1], item)
    return pairs[0][1]


def _answer(g, right: bool):
    """Answer the current question and let the feedback run out."""
    qe = g.quiz_engine
    q = qe.current_question
    qe.answer(str(q['answer']) if right else '__surely wrong__')
    # An untimed wrong answer holds on its lesson line until a key (teaching
    # cards, 2026-10-18): press one once the 1 s minimum has passed.
    qe._result_hold_until = 0.0
    qe.release_result_hold()
    qe.update(5.0)


def _save_reload(g):
    import main
    import save_system
    save_system.settle_unfinished_actions(g)
    assert save_system.save_game(g)
    st = save_system.load_game(g.player_name)
    g2, notice = main._restore_saved_game(_screen(), g.player_name, st)
    assert g2 is not None, notice
    from game_states import STATE_PLAYER
    g2.state = STATE_PLAYER                    # past the load summary popup
    return g2


def _texts(g):
    return [e.get('text', '') if isinstance(e, dict) else str(e) for e in g._chronicle]


def _tomb(g):
    """Arrive on Setne's floor; return the ghost that opens the scene."""
    g._change_level(g._setne['floor'], enter_from_top=True)
    from game_states import STATE_PLAYER
    g.state = STATE_PLAYER
    ghosts = [m for m in g.monsters if m.alive
              and getattr(m, '_flavor_encounter_tag', None) == 'flv_setne_tomb']
    assert ghosts
    return ghosts


# ---------------------------------------------------------------- the Road

def test_eng01_a_kept_oaths_callback_lands_by_its_due_floor():
    """ENG-01: Wat's lamp used to be rolled apart from the oath's due floor;
    a third of runs lost the promise before it could be kept."""
    bad = []
    for seed in range(1, 25):
        g = _game(seed)
        g._change_level(4, enter_from_top=True)
        _open(g, 'flv_wat_lamplighter')
        _choose(g, 0)
        reg = g._deeds
        o = reg['oaths']['wat_lamp']
        p = [p for p in reg['pending'] if (p.get('spec') or {}).get('encounter') == 'flv_seventh_lamp']
        if not p or p[0]['target'] > o['due_floor']:
            bad.append((seed, o['due_floor'], p and p[0]['target']))
    assert not bad, bad


def test_eng02_jnl02_a_callback_that_cannot_appear_is_lost_and_closes_its_thread():
    import deeds
    g = _game(3)
    g._change_level(4, enter_from_top=True)
    _open(g, 'flv_wat_lamplighter')
    _choose(g, 0)
    g._close_npc_encounter(resolved=True)
    reg = g._deeds
    p = next(p for p in reg['pending'] if (p.get('spec') or {}).get('encounter') == 'flv_seventh_lamp')
    assert p['spec'].get('thread') == 'wats_lamps'          # rides with the callback
    # The lamp needs the oath open; release it so the lamp can never come.
    deeds.release_oath(reg, 'wat_lamp', floor=4, block=1)
    tgt = p['target']
    for f in range(5, tgt + 1):
        g._change_level(f, enter_from_top=True)
    assert not any((q.get('spec') or {}).get('encounter') == 'flv_seventh_lamp'
                   for q in reg['pending'])
    assert deeds.has(reg, 'flag.thread_lost.flv_seventh_lamp')
    assert (g._road['slots'].get(tgt) or {}).get('bound') != 'flv_seventh_lamp'
    assert reg['threads']['wats_lamps']['status'] == 'closed'
    assert any('never did find out' in t for t in _texts(g))


def test_jnl01_keeping_cuthberts_oath_closes_the_desk_thread():
    g = _game(4)
    g._change_level(44, enter_from_top=True)
    _open(g, 'flv_coffin_bearer')
    _choose(g, 0)
    reg = g._deeds
    assert reg['oaths']['cuthbert_gospel']['thread'] == 'cuthbert_desk'
    assert reg['threads']['cuthbert_desk']['status'] == 'open'
    assert g._keep_oath('cuthbert_gospel')
    assert reg['threads']['cuthbert_desk']['status'] == 'closed'


def test_eng08_an_oath_with_no_due_floor_lapses_when_its_keeper_is_left_behind():
    g = _game(4)
    g._change_level(44, enter_from_top=True)
    _open(g, 'flv_coffin_bearer')
    _choose(g, 0)
    g._close_npc_encounter(resolved=True)
    reg = g._deeds
    chapel = next(p for p in reg['pending']
                  if (p.get('spec') or {}).get('encounter') == 'flv_cuthbert_chapel')
    tgt = chapel['target']
    for f in range(45, tgt + 1):
        g._change_level(f, enter_from_top=True)
    assert reg['oaths']['cuthbert_gospel']['status'] == 'open'     # the chapel waits here
    for f in range(tgt + 1, tgt + 4):
        g._change_level(f, enter_from_top=True)
    assert reg['oaths']['cuthbert_gospel']['status'] == 'open'     # three floors' grace
    g._change_level(tgt + 4, enter_from_top=True)
    assert reg['oaths']['cuthbert_gospel']['status'] == 'lapsed'
    import deeds
    assert deeds.count(reg, tag='vice:lapsed') == 1 and g.karma == 0


def test_eng08_aldrics_lodestone_never_lapses_any_altar_keeps_it():
    g = _game(4)
    g._change_level(4, enter_from_top=True)
    _open(g, 'sir_aldric')
    _choose(g, 0)
    g._close_npc_encounter(resolved=True)
    g._deeds['pending'] = []
    for f in range(5, 30):
        g._change_level(f, enter_from_top=True)
    assert g._deeds['oaths']['aldric_lodestone']['status'] == 'open'


def test_con04_secret_floors_hold_no_medium_high_or_callback_and_the_tomb_avoids_anchors():
    import road
    seen_anchor_move = 0
    for seed in range(1, 40):
        g = _game(seed)
        st = g._road
        secrets = g._secret_floors()
        assert g._setne['floor'] in secrets
        for f in secrets:
            assert (st['slots'].get(f) or {}).get('role') not in ('medium', 'high'), \
                (seed, f, st['slots'].get(f))
            assert f in g._callback_blocked_floors()
            assert not g._floor_free_for_callback(f)
        if g._setne['floor'] not in road.busy_floors(st):
            seen_anchor_move += 1
    assert seen_anchor_move == 39


def test_con04_a_carried_callback_does_not_land_on_a_secret_floor():
    import deeds
    g = _game(6)
    sf = g._setne['floor']
    g.player.deepest_floor_reached = sf - 1
    g.dungeon_level = sf - 1
    deeds.schedule(g._deeds, {'kind': 'encounter', 'id': 'cb:flv_seventh_lamp:x', 'source': 't',
                              'made_floor': 1, 'earliest': sf - 3, 'latest': sf + 2,
                              'target': sf, 'spec': {'encounter': 'flv_lena_returns'},
                              'requires': None, 'cause': 1})
    g._change_level(sf, enter_from_top=True)
    p = [p for p in g._deeds['pending'] if p['id'] == 'cb:flv_seventh_lamp:x']
    assert p and p[0]['target'] == sf + 1                  # carried on, not placed here
    assert all((e or {}).get('tag') != 'flv_lena_returns'
               for e in g._flavor_encounter_levels.values())


def test_con03_the_tomb_never_rolls_a_maze_floor():
    import setne_tomb
    assert 50 not in setne_tomb.candidate_floors()
    assert all(f % 10 for f in setne_tomb.candidate_floors())


def test_int13_road_on_never_runs_the_legacy_schedulers(monkeypatch):
    import flavor_encounters
    import npc_encounters

    def boom(*_a, **_k):
        raise AssertionError('legacy scheduler ran with the Road on')
    monkeypatch.setattr(flavor_encounters, 'select_flavor_encounters', boom)
    monkeypatch.setattr(npc_encounters, 'select_encounter_levels', boom)
    g = _game(2)
    assert g._road['enabled'] and g._npc_encounter_levels


# ---------------------------------------------------------------- then: options and reload

def test_eng03_sav03_a_talk_step_then_quit_reopens_on_the_options():
    g = _game(5, name='__test_bb5_listen__')
    ghost = _tomb(g)[0]
    assert g._start_flavor_encounter(ghost)
    _choose(g, 0)                                           # "Listen to Ahwere"
    assert g._npc_encounter_phase == 'outcome'
    assert 'flv_setne_tomb' not in g._encountered_flavor_npcs
    g2 = _save_reload(g)
    ghosts = [m for m in g2.monsters if m.alive
              and getattr(m, '_flavor_encounter_tag', None) == 'flv_setne_tomb']
    assert ghosts
    assert g2._start_flavor_encounter(ghosts[0])
    from game_states import STATE_NPC_ENCOUNTER
    assert g2.state == STATE_NPC_ENCOUNTER and g2._npc_encounter_phase == 'options'
    labels = [o['label'] for _i, o in g2._npc_visible_options()]
    assert any('senet' in lab for lab in labels) and 'Listen to Ahwere' not in labels
    # The step's Journal line was written by the quit's settle.
    assert any('Ahwere' in t or 'wife' in t.lower() for t in _texts(g2)) or g2._deeds['used_options']


def test_sav03_an_old_save_spent_at_a_talk_step_is_reopened():
    g = _game(5, name='__test_bb5_old_spent__')
    ghost = _tomb(g)[0]
    g._start_flavor_encounter(ghost)
    _choose(g, 0)
    g._npc_outcome_continue()
    g._close_npc_encounter(resolved=False)                  # as an old build left it:
    g._encountered_flavor_npcs.add('flv_setne_tomb')        # spent at the first step
    assert g._start_flavor_encounter(ghost)
    assert ghost.alive and g._npc_encounter_phase == 'options'


def test_con15_leaving_after_a_step_adds_no_met_line():
    g = _game(5)
    ghost = _tomb(g)[0]
    g._start_flavor_encounter(ghost)
    _choose(g, 0)
    g._npc_outcome_continue()
    n = len(g._chronicle)
    g._npc_encounter_input(pygame.K_ESCAPE)
    assert not any(t.startswith('Met ') for t in _texts(g)[n:])
    assert 'flv_setne_tomb' in g._encountered_flavor_npcs


# ---------------------------------------------------------------- settle on quit

def test_eng04_quitting_at_senets_first_question_costs_what_losing_costs():
    import save_system
    g = _game(5)
    ghost = _tomb(g)[0]
    floor = g.dungeon_level
    g.player.max_hp = g.player.hp = 30
    g._start_flavor_encounter(ghost)
    _choose(g, 1)                                            # senet, staking yourself
    from game_states import STATE_QUIZ
    assert g.state == STATE_QUIZ
    save_system.settle_unfinished_actions(g)
    assert g.player.max_hp < 30                              # every round's per-miss cost
    assert g.dungeon_level == floor - 1                      # the floor gave the hero up
    assert g._setne.get('sealed')
    assert g._npc_encounter_active is None


def test_sav02_quitting_on_an_outcome_page_writes_its_journal_line():
    import save_system
    g = _game(5)
    g._change_level(4, enter_from_top=True)
    _open(g, 'flv_wat_lamplighter')
    _choose(g, 0)
    line = g._npc_outcome_chronicle
    assert line and line not in _texts(g)
    save_system.settle_unfinished_actions(g)
    assert line in _texts(g)
    assert g._npc_encounter_active is None


def test_sav05_quitting_during_a_right_answers_feedback_counts_the_answer():
    import save_system
    from quiz_engine import QuizState
    got = []
    g = _game(2)
    g.quiz_engine.start_quiz(mode='threshold', subject='history', tier=1, threshold=1,
                             total_qs=1, callback=got.append)
    q = g.quiz_engine.current_question
    g.quiz_engine.answer(str(q['answer']))
    assert g.quiz_engine.state == QuizState.RESULT
    save_system.settle_unfinished_actions(g)
    assert got and got[0].success and got[0].correct == 1


def test_eng15_a_miss_the_tablet_rerolls_costs_nothing():
    seen = []
    g = _game(2)
    qe = g.quiz_engine
    qe._reroll_flag = True
    qe.start_quiz(mode='threshold', subject='history', tier=1, threshold=1, total_qs=3,
                  callback=lambda r: None, play_all=True,
                  on_each=lambda ok, c, w: seen.append((ok, w)))
    _answer(g, False)                       # rerolled: no cost
    assert seen == []
    _answer(g, False)                       # this one counts, as the first miss
    assert seen == [(False, 1)]


# ---------------------------------------------------------------- hostile scenes

def _dead_scene(g):
    """Win senet, keep the book, walk to the floor the dead come to."""
    ghost = _tomb(g)[0]
    g._start_flavor_encounter(ghost)
    _choose(g, 1)
    for _ in range(3):
        if g.quiz_engine.callback is None:
            break
        _answer(g, True)
    g._close_npc_encounter(resolved=True)
    reg = g._deeds
    tgt = next(p['target'] for p in reg['pending'] if 'dead_come' in p['id'])
    from game_states import STATE_PLAYER
    for f in range(g.dungeon_level + 1, tgt + 1):
        g.state = STATE_PLAYER
        g._change_level(f, enter_from_top=True)
    return tgt


def test_eng07_sav04_esc_through_the_real_input_path_cannot_walk_away():
    from game_states import STATE_NPC_ENCOUNTER
    g = _game(5, name='__test_bb5_hostile__')
    _dead_scene(g)
    assert g.state == STATE_NPC_ENCOUNTER
    assert g._npc_encounter_active['tag'] == 'flv_dead_come_for_the_book'
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0,
                                      unicode='\x1b', scancode=0))
    assert g.state == STATE_NPC_ENCOUNTER
    g._npc_show_options()
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0,
                                      unicode='\x1b', scancode=0))
    assert g.state == STATE_NPC_ENCOUNTER and g._npc_encounter_phase == 'options'


def test_eng07_the_hostile_scene_reopens_after_a_reload():
    from game_states import STATE_NPC_ENCOUNTER, STATE_PLAYER
    g = _game(5, name='__test_bb5_hostile_reload__')
    _dead_scene(g)
    g2 = _save_reload(g)
    assert g2.state == STATE_PLAYER
    g2.update(0.016)
    assert g2.state == STATE_NPC_ENCOUNTER
    assert g2._npc_encounter_active['tag'] == 'flv_dead_come_for_the_book'


def test_eng07_leaving_the_hostile_floor_unresolved_lapses_the_book_oath():
    from game_states import STATE_PLAYER
    g = _game(5)
    tgt = _dead_scene(g)
    g._close_npc_encounter(resolved=False)                  # as a bypass would
    g.state = STATE_PLAYER
    g._change_level(tgt + 1, enter_from_top=True)
    assert g._deeds['oaths']['thoth_return']['status'] == 'lapsed'


def test_eng07_esc_on_the_item_picker_goes_back_to_the_options():
    from game_states import STATE_NPC_ENCOUNTER
    g = _game(5)
    g._change_level(4, enter_from_top=True)
    _open(g, 'flv_wat_lamplighter')
    g._npc_show_options()
    g._npc_encounter_phase = 'select_item'
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0,
                                      unicode='\x1b', scancode=0))
    assert g.state == STATE_NPC_ENCOUNTER and g._npc_encounter_phase == 'options'


def test_eng06_reading_the_book_is_recorded_and_the_dead_know_it():
    import deeds
    g = _game(5)
    from items import load_items, copy_at
    book = copy_at(next(i for i in load_items('spellbook') if i.id == 'book_of_thoth'), 0, 0) \
        if any(i.id == 'book_of_thoth' for i in load_items('spellbook')) else None
    if book is None:
        book = next(i for t in ('artifact', 'scroll') for i in load_items(t)
                    if i.id == 'book_of_thoth')
    g.player.inventory.append(book)
    g._read_book_of_thoth(book)
    g.quiz_engine._end(success=True)
    assert deeds.has(g._deeds, 'told.read_thoth')
    from encounter_schema import resolve_text
    _src, dead = _enc('flv_dead_come_for_the_book')
    assert 'never even opened' not in resolve_text(dead, g._deed_ctx())


def test_eng06_the_validator_catches_a_deed_nothing_writes():
    from tools.encounters import validate
    enc = {'tag': 'fx_reader', 'options': [{'label': 'x', 'requires': {
        'deeds_any': ['told.nobody_ever_writes_this']}}]}
    issues = validate._deed_refs([('flavor', enc)])
    assert any(i.code == 'deed_ref' and 'nobody_ever_writes_this' in i.msg for i in issues) \
        or any('nobody_ever_writes_this' in str(i) for i in issues)
    assert not validate._deed_refs(validate.load_all())


# ---------------------------------------------------------------- outcomes

def test_eng09_naive_and_cruel_choices_write_their_vice_tags():
    import deeds
    import flavor_encounters
    g = _game(3)
    naive = next(e for e in flavor_encounters.FLAVOR_ENCOUNTERS
                 if any(o.get('naive') and not o.get('requires') and not o.get('cost')
                        and 'quiz' not in o for o in e.get('options') or ()))
    g._change_level(max(2, (naive.get('band') or [3])[0]), enter_from_top=True)
    _open(g, naive['tag'])
    i = next(i for i, o in enumerate(naive['options']) if o.get('naive') and not o.get('requires')
             and not o.get('cost') and 'quiz' not in o)
    _choose(g, i)
    assert deeds.count(g._deeds, tag='vice:reckless') == 1
    g._close_npc_encounter(resolved=True)
    cruel = next(e for e in flavor_encounters.FLAVOR_ENCOUNTERS
                 if any(o.get('karma_kind') == 'cruelty' and not o.get('requires')
                        and not o.get('cost') and 'quiz' not in o for o in e.get('options') or ()))
    _open(g, cruel['tag'])
    j = next(i for i, o in enumerate(cruel['options']) if o.get('karma_kind') == 'cruelty'
             and not o.get('requires') and not o.get('cost') and 'quiz' not in o)
    _choose(g, j)
    assert deeds.count(g._deeds, tag='vice:cruelty') == 1


def test_eng10_a_branch_cost_never_drives_gold_below_zero():
    g = _game(2)
    g.player_gold = 2
    g._npc_pay_cost({'type': 'gold', 'amount': 30})
    assert g.player_gold == 0
    g.player.hp = 3
    g._npc_pay_cost({'type': 'hp_percent', 'amount': 50})
    assert g.player.hp == 1


def test_eng12_crossing_eight_by_a_kept_oath_writes_the_clean_line():
    import deeds
    g = _game(2)
    g.karma = 7
    deeds.swear(g._deeds, 'fx_oath', to='Someone', what='x', floor=1, block=1)
    g.player.deepest_floor_reached = 15
    g._keep_oath('fx_oath')
    assert g.karma == 8
    assert any('I feel clean' in t for t in _texts(g))


def test_eng13_a_living_courier_reads_the_base_text():
    g = _game(2)
    g._change_level(33, enter_from_top=True)
    e, _m = _open(g, 'dying_messenger')
    _choose(g, 0)
    assert 'Swore over a dead courier' not in (g._npc_outcome_chronicle or '')
    assert g._npc_outcome_text.startswith(e['options'][0]['outcome'][:20])


def test_con06_a_fate_deed_sets_the_people_page_status():
    g = _game(2)
    g._change_level(33, enter_from_top=True)
    _open(g, 'dying_messenger')
    _choose(g, 0)                                        # writes lost.edric
    assert g._deeds['people']['edric']['status'] == 'lost'


def test_con07_an_option_forbidden_by_a_steps_deed_is_gone_on_return():
    import copy as _c
    g = _game(2)
    fx = {'tag': 'fx_desk', 'name': 'Desk Keeper', 'symbol': '@', 'color': [1, 1, 1],
          'sprite_id': 'npc_traveler', 'role': 'story', 'stakes': 'light', 'band': [1, 9],
          'text': 'A desk.',
          'options': [{'label': 'Lay the book', 'outcome': 'Laid.', 'then': 'options',
                       'deeds': ['told.fx_laid']},
                      {'label': 'I still have the book', 'outcome': 'Hm.',
                       'forbids': {'deeds_any': ['told.fx_laid']}},
                      {'label': 'Leave', 'outcome': 'Gone.'}]}
    m = _npc_for(g, fx, True)
    g._flavor_encounter_levels[g.dungeon_level] = _c.deepcopy(fx)
    g._npc_open(g._flavor_encounter_levels[g.dungeon_level], m, flavor=True)
    _choose(g, 0)
    g._npc_outcome_continue()
    assert [i for i, _o in g._npc_visible_options()] == [2]


def test_con09_closing_the_tomb_removes_both_ghosts():
    g = _game(5)
    ghosts = _tomb(g)
    assert len(ghosts) == 2
    g._start_flavor_encounter(ghosts[0])
    _choose(g, 1)                                        # senet, and win it
    for _ in range(3):
        if g.quiz_engine.callback is None:
            break
        _answer(g, True)
    assert not g._setne.get('sealed')                    # a win leaves the door
    g._npc_outcome_continue()
    assert not any(m.alive for m in ghosts)


def test_con16_the_tombs_choices_are_deeds_not_consequences():
    g = _game(5)
    ghosts = _tomb(g)
    g._start_flavor_encounter(ghosts[0])
    _choose(g, 3)
    line = g._npc_outcome_chronicle
    g._npc_outcome_continue()
    if line:
        e = next(e for e in g._chronicle if isinstance(e, dict) and e.get('text') == line)
        assert e.get('kind') == 'deed'


def test_eng14_int09_sealing_puts_hero_and_pets_on_free_outside_tiles():
    from dungeon import WALL
    from pet_system import Pet
    g = _game(5)
    ghosts = _tomb(g)
    room = g._setne['room']
    chamber = [tuple(t) for t in room['chamber']]
    out = tuple(room['outside'])
    g.player.x, g.player.y = chamber[0]
    # One pet on the very tile the hero is put on, one walled in with him.
    pets = [Pet('electric', *out), Pet('water', *chamber[1])]
    g.pets = pets
    g._encounter_seal_room(ghosts[0])
    dx, dy = room['door']
    assert g.dungeon.tiles[dy][dx] == WALL
    spots = [(g.player.x, g.player.y)] + [(p.x, p.y) for p in pets]
    assert len(set(spots)) == 3                           # nobody stacked
    assert not any(s in chamber or s == (dx, dy) for s in spots)
    walk = g._reachable_tiles(g.player.x, g.player.y)
    assert all(s in walk for s in spots)


# ---------------------------------------------------------------- saves

def test_sav01_sav08_a_real_v310_save_moves_karma_again():
    """A real v3.1.0 pickle (bug bash saves angle, ``oldsaves``): its pickled
    encounter dicts are refreshed by tag on load, so an option with typed
    karma moves karma with the gate on."""
    import save_system
    import main
    from quiz_engine import QuizResult
    name = 'old310_s1'
    path = save_system._save_path(name)
    shutil.copy2(os.path.join(ROOT, 'tests', 'data', 'old_v310_save_L8.pkl'), path)
    try:
        st = save_system.load_game(name)
        assert st is not None and '_road' not in st
        trig_before = {f: e.get('trigger_item') for f, e in st['_npc_encounter_levels'].items()}
        g, notice = main._restore_saved_game(_screen(), name, st)
        assert g is not None, notice
        assert not g._road['enabled']
        assert {f: e.get('trigger_item') for f, e in g._npc_encounter_levels.items()} == trig_before
        # Every refreshed dict is today's: typed karma only.
        for e in g._npc_encounter_levels.values():
            for o in e['options']:
                for b in [o, o.get('pass') or {}, o.get('fail') or {}]:
                    if b.get('karma'):
                        assert b.get('karma_kind'), (e['tag'], o['label'])
        # Take a +1 on an anchor ahead whose block is still open.
        from game_states import STATE_PLAYER
        lv, enc = next((lv, e) for lv, e in sorted(g._npc_encounter_levels.items())
                       if lv > g.dungeon_level and e['tag'] not in g._encountered_npcs
                       and not e.get('trigger_item')
                       and any((o.get('pass') or {}).get('karma', 0) > 0
                               or (o.get('karma', 0) or 0) > 0 for o in e['options']))
        g._change_level(lv, enter_from_top=True)
        g.state = STATE_PLAYER
        g.player_gold = 10 ** 6
        g.player.hp = g.player.max_hp = 999
        npc = next(m for m in g.monsters if getattr(m, '_npc_encounter_tag', None) == enc['tag'])
        g._npc_open(enc, npc, flavor=False)
        i, opt = next((i, o) for i, o in enumerate(enc['options'])
                      if ((o.get('pass') or {}).get('karma', 0) > 0 or (o.get('karma', 0) or 0) > 0)
                      and not (o.get('cost') or {}).get('type', '').endswith('item'))
        k0 = g.karma
        g._npc_selected_index, g._npc_selected_option = i, opt
        g._apply_npc_choice(opt)
        if g.quiz_engine.callback is not None:
            g.quiz_engine.callback(QuizResult(success=True, score=9, correct=9, asked=9))
        assert g.karma == k0 + 1
    finally:
        save_system.delete_save(name)


def test_sav07_saves_and_bones_are_synced_before_the_rename(monkeypatch):
    import bones
    import save_system
    calls = []
    real = os.fsync
    monkeypatch.setattr(os, 'fsync', lambda fd: (calls.append(fd), real(fd))[1])
    g = _game(2, name='__test_bb5_fsync__')
    try:
        assert save_system.save_game(g)
        assert calls
        n = len(calls)
        bones.save_bones('tester', 3, 'died', g.player, 0)
        assert len(calls) > n
        bd = bones._bones_dir()
        assert os.path.exists(os.path.join(bd, 'bones_L3.json'))
        assert not [f for f in os.listdir(bd) if f.endswith('.tmp')]
        os.remove(os.path.join(bd, 'bones_L3.json'))
    finally:
        save_system.delete_save('__test_bb5_fsync__')


# ---------------------------------------------------------------- Journal

def test_jnl04_the_people_page_shows_the_title_until_the_name_is_said():
    import chronicle
    g = _game(2)
    g._change_level(60, enter_from_top=True)
    e, _m = _open(g, 'flv_utgard_contests')
    pid = e['person']['id']
    rows = {r['name'] for r in chronicle.people_rows(g._deeds)}
    assert 'Courteous Giant' in rows and e['person']['name'] not in rows
    import deeds
    deeds.set_person(g._deeds, pid, known=True)
    rows = {r['name'] for r in chronicle.people_rows(g._deeds)}
    assert e['person']['name'] in rows


def test_jnl10_old_legacy_lines_are_highlights_of_last_resort():
    import chronicle
    assert chronicle.highlights(chronicle.migrate(['Killed the Minotaur! (L20)']))


def test_jnl11_a_bear_trap_is_not_a_bear_trap_trap():
    from main import _trap_noun
    assert _trap_noun('bear_trap') == 'bear'
    assert _trap_noun('sleep_gas') == 'sleep gas'


def test_jnl13_named_things_read_right_mid_sentence():
    from chronicle import in_sentence
    assert in_sentence("The Bull's Horn") == "the Bull's Horn"
    assert in_sentence("A Cat's Footfall") == "a Cat's Footfall"
    assert in_sentence('Chapel of the Grail') == 'the Chapel of the Grail'
    assert in_sentence("Pandora's Coffer") == "Pandora's Coffer"


def _footers(g, draw):
    got = []
    real = g._ui_footer
    g._ui_footer = lambda panel, text, *a, **k: (got.append(text), real(panel, text, *a, **k))
    draw()
    return got


def test_jnl05_jnl06_encounter_footers_match_the_keys():
    g = _game(2)
    g.screen = pygame.Surface((1280, 720))
    g._change_level(4, enter_from_top=True)
    _open(g, 'flv_wat_lamplighter')
    g._npc_show_options()
    n = len(g._npc_visible_options())
    assert any(f.startswith(f'1-{n}: choose') for f in _footers(g, g._draw_npc_encounter))
    g._close_npc_encounter(resolved=False)
    _src, dead = _enc('flv_dead_come_for_the_book')
    m = _npc_for(g, dead, True)
    g._flavor_encounter_levels[g.dungeon_level] = dead
    g._npc_open(dead, m, flavor=True)
    assert not any('walk away' in f for f in _footers(g, g._draw_npc_encounter))


def test_jnl07_the_journey_names_the_farm_not_floor_999():
    g = _game(2)
    g.dungeon_level = 999
    rows = dict(g._discoveries_sections())['JOURNEY']
    assert any('Moo Moo Farm' in r for r in rows) and not any('999' in r for r in rows)


class _SpyFont:
    """A font that records every string it renders."""

    def __init__(self, font):
        self.font, self.drawn = font, []

    def render(self, text, *a):
        self.drawn.append(text)
        return self.font.render(text, *a)

    def __getattr__(self, k):
        return getattr(self.font, k)


def test_jnl08_the_rail_never_cuts_the_turn_number():
    g = _game(2)
    sb = g.sidebar
    font = sb._fsm
    spy = sb._fsm = _SpyFont(font)
    w0 = sb.w
    # A rail just too narrow for "Moo Moo Farm  Turn 123456789" on one line.
    sb.w = font.size('Moo Moo Farm  Turn 123456789')[0] - 4 + 2 * sb.PAD
    try:
        sb._identity('Aldric', 999, 123456789, 0)
    finally:
        sb._fsm = font
        sb.w = w0
    assert any('Turn 123456789' in t for t in spy.drawn), spy.drawn


def test_jnl09_your_story_does_not_scroll_a_page_that_fits():
    g = _game(2)
    g.screen = pygame.Surface((1280, 720))
    g._end_story_scroll = 40
    g._draw_your_story()
    assert g._end_story_scroll == 0
