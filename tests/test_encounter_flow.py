"""The unified encounter engine (DEEDS_KARMA_DESIGN 4 and 6.1, tests 8.5), on a
real headless Game with fixture encounters: quiz options with pass and fail,
key 4 and four visible options, requires / hidden_group / text_variants,
'then: options', the commit point, and the new cost and reward types.

Fixture content only: no shipped encounter uses these fields yet (Phase 3b
brings the first four-option content). Behaviour of today's content is
pinned by the parity tests at the bottom.
"""
import copy
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import pygame  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=7):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name='__test_encounter_flow__')
    g.monsters = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


QUIZ_ENC = {
    'tag': 'fx_two_prisoners', 'name': 'Two Prisoners', 'symbol': '@', 'color': [200, 180, 140],
    'sprite_id': 'npc_traveler', 'min_level': 1, 'max_level': 9,
    'role': 'story', 'stakes': 'medium', 'band': [1, 9],
    'person': {'id': 'anselm', 'name': 'Father Anselm'},
    'text': "Two men in chains. Cultists in these halls have been known to wear a captured priest's robe.",
    'text_variants': [{'when': {'deeds_any': ['noticed.odin']},
                       'text': 'The one-eyed stranger told you about these two.'}],
    'options': [
        {'label': 'Question them both on the Pater Noster',
         'cost': {'type': 'hp_pct', 'amount': 10},
         'quiz': {'subject': 'theology', 'tier': 1, 'mode': 'threshold', 'threshold': 1,
                  'total_qs': 1},
         'deeds': ['met.chained_priests'],
         'pass': {'outcome': 'You free the true priest.', 'karma': 1, 'karma_kind': 'judgment',
                  'deeds': ['saved.anselm'], 'person_status': 'saved',
                  'chronicle': 'One of them knew the prayer all the way through. I freed that one.'},
         'fail': {'outcome': 'You cannot tell them apart.', 'deeds': ['lost.anselm'],
                  'person_status': 'lost'}},
        {'label': 'Free whichever one is begging hardest', 'naive': True,
         'cost': {'type': 'gold_pct', 'amount': 50},
         'deeds': ['lost.anselm'], 'outcome': 'He robs you on the way out.'},
        {'label': 'Leave them', 'outcome': 'You leave them.'},
        {'label': '"Odin sent me."', 'hidden': True, 'hidden_group': 'secret',
         'requires': {'deeds_any': ['noticed.odin']},
         'outcome': 'The true priest looks up.', 'deeds': ['saved.anselm']},
    ],
}


def _open(g, enc):
    """Spawn the fixture through the real spawner and bump-open it."""
    enc = copy.deepcopy(enc)
    g._flavor_encounter_levels = {g.dungeon_level: enc}
    g._maybe_spawn_flavor_npc(g.dungeon_level)
    npc = next(m for m in g.monsters if getattr(m, '_flavor_encounter_tag', None) == enc['tag'])
    assert g._start_flavor_encounter(npc)
    return npc, enc


def _key(g, k):
    g._npc_encounter_input(k)


def _result(success, score=1):
    from quiz_engine import QuizResult
    return QuizResult(success=success, score=score, correct=score, asked=1)


def _labels(g):
    return [o['label'] for _i, o in g._npc_visible_options()]


def test_quiz_option_commit_then_pass_branch():
    from game_states import STATE_NPC_ENCOUNTER, STATE_QUIZ
    import deeds
    g = _game()
    g.player.hp = 100
    k0 = g.karma
    npc, enc = _open(g, QUIZ_ENC)
    assert g._npc_encounter_text == QUIZ_ENC['text']
    assert g._deeds['people']['anselm']['status'] == 'met'
    _key(g, pygame.K_RETURN)
    assert _labels(g) == [o['label'] for o in QUIZ_ENC['options'][:3]]   # secret hidden
    _key(g, pygame.K_1)
    # The commit point: cost paid, encounter spent, option deeds recorded, quiz running.
    assert g.player.hp == 90
    assert enc['tag'] in g._encountered_flavor_npcs
    assert deeds.has(g._deeds, 'met.chained_priests')
    assert g.state == STATE_QUIZ and g.quiz_engine.callback is not None
    g.quiz_engine.callback(_result(True))
    assert g.state == STATE_NPC_ENCOUNTER and g._npc_encounter_phase == 'outcome'
    assert g._npc_outcome_text == 'You free the true priest.'
    assert g.karma == k0 + 1
    assert deeds.has(g._deeds, 'saved.anselm')
    assert deeds.count(g._deeds, tag='virtue:judged') == 1     # a naive sibling was on screen
    assert deeds.count(g._deeds, tag='virtue:steadfast') == 0  # medium, not high stakes
    assert g._deeds['people']['anselm']['status'] == 'saved'
    _key(g, pygame.K_RETURN)
    assert not npc.alive
    from chronicle import text_of
    assert text_of(g._chronicle[-1]).startswith('One of them knew the prayer')


def test_quiz_fail_branch_and_no_judged_tag():
    import deeds
    g = _game()
    k0 = g.karma
    _open(g, QUIZ_ENC)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_1)
    g.quiz_engine.callback(_result(False, 0))
    assert g._npc_outcome_text == 'You cannot tell them apart.'
    assert g.karma == k0
    assert deeds.has(g._deeds, 'lost.anselm')
    assert deeds.count(g._deeds, tag='virtue:judged') == 0    # judgment needs a PASS


def test_exit_mid_quiz_settles_as_the_fail_branch():
    import deeds
    from save_system import settle_unfinished_actions
    g = _game()
    _open(g, QUIZ_ENC)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_1)
    settle_unfinished_actions(g)
    assert deeds.has(g._deeds, 'lost.anselm')
    assert g._npc_outcome_text == 'You cannot tell them apart.'
    assert g.quiz_engine.callback is None


def test_high_stakes_pass_writes_steadfast():
    import deeds
    g = _game()
    enc = copy.deepcopy(QUIZ_ENC)
    enc['stakes'] = 'high'
    _open(g, enc)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_1)
    g.quiz_engine.callback(_result(True))
    assert deeds.count(g._deeds, tag='virtue:steadfast') == 1


def test_hidden_option_key_4_and_text_variant():
    import deeds
    g = _game()
    reg = deeds.ensure_register(g)
    deeds.record(reg, 'noticed.odin', floor=1, block=1)
    _open(g, QUIZ_ENC)
    assert g._npc_encounter_text.startswith('The one-eyed stranger')
    _key(g, pygame.K_RETURN)
    assert len(_labels(g)) == 4 and _labels(g)[3] == '"Odin sent me."'
    _key(g, pygame.K_4)
    assert g._npc_outcome_text == 'The true priest looks up.'
    assert deeds.has(g._deeds, 'saved.anselm')
    # The renderer lays out four labels without trouble.
    g._npc_encounter_phase = 'options'
    g._draw_npc_encounter()


def test_key_4_does_nothing_with_three_visible():
    g = _game()
    _open(g, QUIZ_ENC)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_4)
    assert g._npc_encounter_phase == 'options'


def test_hidden_group_shows_only_the_first_passing():
    import deeds
    from encounter_schema import visible_options
    enc = copy.deepcopy(QUIZ_ENC)
    enc['options'] = enc['options'][2:] + [
        {'label': 'second secret', 'hidden_group': 'secret',
         'requires': {'deeds_any': ['noticed.']}, 'outcome': 'y'}]
    reg = deeds.new_register()
    ctx = {'reg': reg}
    assert [o['label'] for _i, o in visible_options(enc, ctx)] == ['Leave them']
    deeds.record(reg, 'noticed.odin', floor=1, block=1)
    assert [o['label'] for _i, o in visible_options(enc, ctx)] == \
        ['Leave them', '"Odin sent me."']


def test_then_options_returns_to_the_list_with_the_option_used():
    g = _game()
    enc = copy.deepcopy(QUIZ_ENC)
    enc['options'] = [
        {'label': 'Ask his name', 'outcome': 'Anselm.', 'then': 'options',
         'chronicle': 'Asked a prisoner his name.'},
        {'label': 'Leave them', 'outcome': 'You leave them.'},
    ]
    npc, enc = _open(g, enc)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_1)
    assert g._npc_outcome_text == 'Anselm.'
    _key(g, pygame.K_RETURN)
    assert g._npc_encounter_phase == 'options' and _labels(g) == ['Leave them']
    assert npc.alive
    from chronicle import text_of
    assert text_of(g._chronicle[-1]) == 'Asked a prisoner his name.'
    _key(g, pygame.K_1)
    _key(g, pygame.K_RETURN)
    assert not npc.alive


def test_spent_encounter_reopened_after_reload_just_leaves():
    g = _game()
    npc, enc = _open(g, QUIZ_ENC)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_3)                       # chosen: spent
    # (the game is closed here, the NPC still standing in the save)
    g._close_npc_encounter(resolved=False)
    npc.alive, npc.hp = True, 1
    k = g.karma
    assert g._start_flavor_encounter(npc)
    assert not npc.alive and g._npc_encounter_active is None and g.karma == k


def test_encounter_requires_gates_the_spawn():
    import deeds
    g = _game()
    enc = copy.deepcopy(QUIZ_ENC)
    enc['requires'] = {'deeds_all': ['oath.aldric_lodestone']}
    g._flavor_encounter_levels = {g.dungeon_level: enc}
    g._maybe_spawn_flavor_npc(g.dungeon_level)
    assert not [m for m in g.monsters if getattr(m, '_flavor_encounter_tag', None)]
    deeds.swear(deeds.ensure_register(g), 'aldric_lodestone', to='Sir Aldric', what='x',
                floor=1, block=1)
    g._maybe_spawn_flavor_npc(g.dungeon_level)
    assert [m for m in g.monsters if getattr(m, '_flavor_encounter_tag', None)]


def test_pct_costs_and_rewards_use_the_players_own_pools():
    g = _game()
    p = g.player
    p.hp, p.max_hp, p.sp, p.mp = 80, 100, 40, 20
    g.player_gold = 1000
    g._npc_encounter_active = {'tag': 'x'}
    g._npc_pay_cost({'type': 'hp_pct', 'amount': 25})
    assert p.hp == 60
    g._npc_pay_cost({'type': 'sp_pct', 'amount': 50})
    g._npc_pay_cost({'type': 'mp_pct', 'amount': 50})
    g._npc_pay_cost({'type': 'gold_pct', 'amount': 10})
    assert (p.sp, p.mp, g.player_gold) == (20, 10, 900)
    g._npc_pay_cost({'type': 'max_hp_pct', 'amount': 10})
    assert p.max_hp == 90 and p.hp == 60
    g._apply_npc_reward({'type': 'hp_restore_pct', 'amount': 20})
    assert p.hp == 78
    wis = p.WIS
    g._npc_pay_cost({'type': 'stat', 'stat': 'WIS', 'amount': 1})
    assert p.WIS == wis - 1


def test_can_pay_new_cost_types():
    from npc_encounters import can_pay_cost
    g = _game()
    p = g.player
    p.hp = 6
    assert not can_pay_cost(p, {'type': 'hp_pct', 'amount': 10}, 0)[0]
    p.hp = 100
    assert can_pay_cost(p, {'type': 'hp_pct', 'amount': 10}, 0)[0]
    assert can_pay_cost(p, {'type': 'gold_pct', 'amount': 50}, 0)[0]
    assert not can_pay_cost(p, {'type': 'triggered_item_id', 'item_id': 'cursed_lodestone'}, 0)[0]


def test_triggered_item_id_removes_the_named_item():
    g = _game()
    g._grant_burden_item('cursed_lodestone')
    assert any(getattr(i, 'id', '') == 'cursed_lodestone' for i in g.player.inventory)
    from npc_encounters import can_pay_cost
    assert can_pay_cost(g.player, {'type': 'triggered_item_id', 'item_id': 'cursed_lodestone'}, 0)[0]
    g._npc_encounter_active = {'tag': 'x'}
    g._npc_pay_cost({'type': 'triggered_item_id', 'item_id': 'cursed_lodestone'})
    assert not any(getattr(i, 'id', '') == 'cursed_lodestone' for i in g.player.inventory)


def test_price_encounter_walks_nested_outcomes():
    import economy
    enc = {'tag': 't', 'options': [
        {'label': 'Wager', 'quiz': {'subject': 'math', 'tier': 1},
         'pass': {'outcome': 'You win 50 gold.', 'reward': {'type': 'gold', 'amount': 50},
                  'delayed': [{'reward': {'type': 'gold', 'amount': 10}}],
                  'escort': {'on_arrive': {'reward': {'type': 'gold', 'amount': 20}}}},
         'fail': {'outcome': 'Lost.', 'cost': {'type': 'gold', 'amount': 30}}},
        {'label': 'Pay', 'cost': {'type': 'gold_pct', 'amount': 25}, 'outcome': 'ok'}]}
    out = economy.price_encounter(enc)
    m = economy.WRITTEN_GOLD_MULT
    p = out['options'][0]['pass']
    assert p['reward']['amount'] == economy.written_gold(50) and p['reward']['amount'] >= 50 * m - 50
    assert str(f"{economy.written_gold(50):,}") in p['outcome']
    assert p['delayed'][0]['reward']['amount'] == economy.written_gold(10)
    assert p['escort']['on_arrive']['reward']['amount'] == economy.written_gold(20)
    assert out['options'][0]['fail']['cost']['amount'] == economy.written_gold(30)
    assert out['options'][1]['cost'] == {'type': 'gold_pct', 'amount': 25}   # a share is never rescaled
    assert enc['options'][0]['pass']['reward']['amount'] == 50                 # a copy


# ------------------------------------------------- today's content: parity

def _old_apply(g, opt):
    """The pre-redesign effect of a cost-free option on karma (reference)."""
    return max(-10, min(10, g.karma + opt.get('karma', 0)))


def test_shipped_anchor_options_apply_exactly_as_before(gate_off):
    """Every shipped anchor option whose cost needs no item picker, run
    through the new engine: karma, outcome text, spent mark and phase are
    exactly what the old _apply_npc_choice produced."""
    import npc_encounters
    from npc_encounters import get_inventory_filter
    checked = 0
    for enc in npc_encounters.ENCOUNTERS:
        for i, opt in enumerate(enc['options']):
            if get_inventory_filter(opt.get('cost')) or (opt.get('cost') or {}).get('type') in (
                    'spawn_deadite_ambush', 'accept_item', 'triggered_item'):
                continue
            if 'quiz' in opt or opt.get('fight') or opt.get('escort'):
                continue                     # quiz branches are covered by their own tests
            for k in (-10, -1, 0, 7, 10):
                g = _GAME
                g.karma = k
                g._encountered_npcs = set()
                g._npc_is_flavor = False
                g._npc_encounter_active = enc
                g._npc_selected_option = opt
                g._npc_selected_index = i
                g.player.hp = g.player.max_hp = 500
                g.player_gold = 10 ** 6
                want = _old_apply(g, opt)
                # The words shown: the option's own, or the variant its state
                # picks (Edric dead after a failed draught, continuity audit M1).
                from encounter_schema import resolve_outcome
                said = resolve_outcome(opt, g._deed_ctx())
                g._apply_npc_choice(opt)
                assert g.karma == want, (enc['tag'], i, k)
                assert g._npc_outcome_text == said
                assert g._npc_encounter_phase == 'outcome'
                assert enc['tag'] in g._encountered_npcs
                checked += 1
    assert checked > 50


_GAME = None


def setup_module(_m):
    global _GAME
    _GAME = _game(3)


def test_surya_doubles_on_a_positive_request_with_gate_off(monkeypatch, gate_off):
    """Gate off: Surya's Gift doubles whenever the option asked for karma,
    even at +10 where nothing could be applied (the old rule)."""
    import chain_passives
    g = _game()
    g.karma = 10
    calls = []
    monkeypatch.setattr(chain_passives, 'player_has_passive', lambda p, n: n == 'suryas_gift')
    monkeypatch.setattr(g, '_apply_npc_reward', lambda r: calls.append(r))
    opt = {'label': 'x', 'karma': 1, 'reward': {'type': 'message'}, 'outcome': 'o'}
    g._npc_encounter_active = {'tag': 'fx'}
    g._apply_npc_choice(opt)
    assert len(calls) == 2 and g.karma == 10


def test_crossing_line_still_fires_at_the_npc_site_only(gate_off):
    from chronicle import text_of
    import karma
    g = _game()
    g._chronicle = []
    g.karma = 7
    g._npc_encounter_active = {'tag': 'fx'}
    g._apply_npc_choice({'label': 'x', 'karma': 1, 'outcome': 'o'})
    assert any('I feel clean' in text_of(e) for e in g._chronicle)
    g._chronicle = []
    g.karma = 7
    karma.adjust(g, 1, kind='legacy', source='emberpup_feed')      # not an NPC choice
    assert g.karma == 8 and g._chronicle == []
