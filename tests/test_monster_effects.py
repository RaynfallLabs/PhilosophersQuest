"""The monster effects (Brandon, 2026-11-22: "All as recommended" on
MONSTER_EFFECTS_AUDIT_2026_11_22.md). The doors are tests/test_action_doors.py;
here: the bouts, stone, Forget, charm, knock-downs, the hex, old saves, the
quiz (display only, never an auto-kill) and the data.

How any of it feels is a play-test question.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import pickle
import random
from fractions import Fraction

import pygame
import pytest

import action_gate as G
import effect_rules
import knockdown
import mind_theft
import quiz_sight as Q
import status_effects as S
from monster import Monster
from player import Player
from test_bugbash_360_monsters import MONS, _scene

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SUBJECTS = ('ai', 'animal', 'cooking', 'economics', 'geography', 'grammar', 'history', 'math',
            'philosophy', 'science', 'theology', 'trivia')


@pytest.fixture
def worst_luck(monkeypatch):
    """Every save fails and every chance lands."""
    monkeypatch.setattr(random, 'randint', lambda a, b: a)
    monkeypatch.setattr(random, 'random', lambda: 0.0)


def _mon(kind, x=1, y=1):
    return Monster({**MONS[kind], 'id': kind}, x, y)


def _tick_out(p, limit=30):
    out = []
    for _ in range(limit):
        if not p.status_effects.get('petrifying'):
            break
        out += S.tick_all(p)
    return out


# ---------------------------------------------------------------------------
# No stacking, shorter doses
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('effect', sorted(effect_rules.statuses()['refresh']))
def test_a_second_dose_never_adds(effect):
    p = Player()
    assert p.add_effect(effect, 3)
    p.add_effect(effect, 3)
    key = 'hexed' if effect == 'cursed' else effect
    assert p.status_effects[key] == 3


@pytest.mark.parametrize('effect,most', sorted(effect_rules.statuses()['caps'].items()))
def test_one_dose_is_capped(effect, most):
    p = Player()
    p.add_effect(effect, 50)
    assert p.status_effects[effect] == most


def test_an_announced_price_keeps_its_length():
    p = Player()
    p.add_effect('weakened', 20, cap=20)
    assert p.status_effects['weakened'] == 20


def test_slowed_spends_two_turns_an_action_and_leaves_footing():
    p = Player()
    fast = p.get_speed()
    p.add_effect('slowed', 4)
    assert p.get_speed() == pytest.approx(fast / 2)
    S.tick_all(p)
    assert p.status_effects['slowed'] == 2
    S.tick_all(p)
    assert not p.has_effect('slowed') and p.has_effect('footing')
    assert not p.add_effect('slowed', 4) and not p.add_effect('knocked_down', 1)


def test_no_debuff_cuts_the_clock():
    plain = Player().combat_clock()
    for e in sorted(S.DEBUFFS):
        p = Player()
        p.status_effects[e] = 3
        assert p.get_quiz_timer_modifier() == 1.0, e
    p = Player()
    for e in ('confused', 'stunned', 'blinded', 'hallucinating'):
        p.status_effects[e] = 3
    assert p.combat_clock() == plain


# ---------------------------------------------------------------------------
# Stunned
# ---------------------------------------------------------------------------

def test_a_failed_identification_is_ten_turns_of_double_vision_only():
    p = Player()
    S.apply_penalty(p, 'stunned', 11)
    assert p.status_effects['stunned'] == 11 and Q.sight_for(p)['double']
    for door in ('step', 'swap', 'drink', 'cast'):
        assert G.verdict(p, door).open, door


def test_a_cured_bout_is_not_remembered_by_the_next():
    p = Player()
    S.apply_penalty(p, 'stunned', 11)
    p.status_effects.pop('stunned')
    assert p.add_effect('stunned', 3)
    assert G.verdict(p, 'step').what == G.FALL


def test_a_stun_with_no_end_pays_again_on_each_floor():
    g = _scene()
    p = g.player
    p.status_effects['fumbling'] = -1
    v = G.verdict(p, 'drink')
    assert v.what == G.DROP
    G.paid(p, v)
    assert G.verdict(p, 'drink').open
    g._effects_left_floor()
    assert G.verdict(p, 'drink').what == G.DROP


# ---------------------------------------------------------------------------
# Stone
# ---------------------------------------------------------------------------

def test_lethal_stone_counts_down_stiff_slow_stone():
    p = Player()
    p.add_effect('petrifying', 10)
    effect_rules.laid_by(p, 'petrifying', lethal=True)
    seen = [effect_rules.stone_stage(p, n) for n in range(10, 0, -1)]
    assert seen == ['stiff'] * 4 + ['slow'] * 3 + ['rigid'] * 3
    assert ('_petrify_death', 'danger') in _tick_out(p)


def test_lesser_stone_ends_in_one_still_turn_and_never_death():
    p = Player()
    p.add_effect('petrifying', 4)
    assert ('_petrify_death', 'danger') not in _tick_out(p)
    assert p.status_effects['paralyzed'] == 1


@pytest.mark.parametrize('kind,lethal', (('basilisk', True), ('cockatrice', False)))
def test_the_monster_says_which_stone(worst_luck, kind, lethal):
    m, p = _mon(kind), Player()
    atk = next(a for a in m.attacks if a.get('effect') == 'petrifying')
    m._apply_attack_effect(atk, p)
    assert p.has_effect('petrifying') and effect_rules.is_lethal(p) is lethal


def test_stone_thrown_back_cannot_kill():
    assert S.reflected('petrifying', 10) == ('paralyzed', 2)
    for e in ('forgetting', 'knocked_down', 'hexed'):
        assert S.reflected(e, 3)[0] != e


def test_the_gorgon_on_the_chest_still_kills():
    import container_system
    with open(os.path.join(ROOT, 'data', 'chest_traps.json'), encoding='utf-8') as f:
        trap = next(t for t in json.load(f)['traps_by_tier']['5'] if t['type'] == 'petrify')
    p = Player()
    p.hp = p.max_hp = 500
    said = []
    container_system._trigger_trap(p, trap, said)
    assert effect_rules.is_lethal(p) and p.status_effects['petrifying'] == 10
    assert any(text == effect_rules.line('stone_trap') for text, _kind in said)


def test_oil_of_rue_is_at_every_stall_before_stone_can_kill():
    import traders
    first = min(int(d.get('min_level', 1)) for d in MONS.values() if isinstance(d, dict)
                and any(a.get('lethal') for a in d.get('attacks') or () if isinstance(a, dict)))
    assert first > 19
    for tid, defn in traders.data()['traders'].items():
        for floor in (19, 25, 39, 59, 79, 85, 93):
            stock = traders.build_stock(defn, floor, random.Random(7))
            assert any(getattr(i, 'id', '') == 'oil_of_rue' for i in stock), (tid, floor)


# ---------------------------------------------------------------------------
# Forget
# ---------------------------------------------------------------------------

def _eaten():
    from items import is_fully_known, load_items
    g = _scene(('intellect_devourer', 1, 0))
    p, m = g.player, g.monsters[0]
    scroll = copy.copy(next(s for s in load_items('scroll')
                            if s.id != 'philosophers_shard' and s.unidentified_name != s.name))
    scroll.id_level = 5
    p.known_item_ids.add(scroll.id)
    p.inventory[:] = [scroll]
    p.studied_monster_ids = set()
    p.lore_known_monster_ids = set()
    assert g._forgettable(scroll)
    g._mind_eaten_by(m)
    assert not is_fully_known(scroll, p)
    return g, p, m, scroll


def test_the_kill_gives_back_what_was_eaten():
    from items import is_fully_known
    g, p, m, scroll = _eaten()
    m.hp, m.alive = 0, False
    g._effects_killed(m)
    assert is_fully_known(scroll, p) and not mind_theft.records(p)


def test_an_unhandled_kill_gives_back_before_the_stair():
    from items import is_fully_known
    g, p, m, scroll = _eaten()
    m.hp, m.alive = 0, False              # a pet's or a poison's: not yet reaped
    g._effects_left_floor()
    assert is_fully_known(scroll, p)


def test_leaving_the_floor_loses_it():
    from items import is_fully_known
    g, p, m, scroll = _eaten()
    g._effects_left_floor()
    assert not is_fully_known(scroll, p) and not mind_theft.records(p)


def test_what_was_eaten_survives_a_save():
    g, p, m, scroll = _eaten()
    rec, mon, item = pickle.loads(pickle.dumps((mind_theft.records(p), m, scroll)))
    assert effect_rules.is_source(mon, rec[0]['by'])
    assert rec[0]['key'] in item.__dict__[mind_theft.MARK]


def test_a_page_eaten_never_costs_a_tier():
    import family_lore as FL
    p = Player()
    fam = FL.family_of('troll')
    p.studied_monster_ids = {k for k in MONS if isinstance(MONS[k], dict) and FL.family_of(k) == fam}
    p.lore_known_monster_ids = set()
    before = FL.tier(p, fam)
    assert before > 0
    rec = mind_theft.eat_page(p, 'troll', 'tok', 'Troll')
    assert FL.tier(p, fam) == before and 'troll' not in p.studied_monster_ids
    mind_theft.give_back(p, rec)
    assert 'troll' in p.studied_monster_ids


def test_a_mastered_tier_is_never_chosen(monkeypatch):
    import philosophy_mastery
    g, p, m, scroll = _eaten()
    monkeypatch.setattr(philosophy_mastery, 'covers', lambda it, pl: True)
    assert mind_theft.item_candidates(p, lambda it: True) == []


def test_forget_asks_once_a_bout(worst_luck):
    m, p = _mon('intellect_devourer'), Player()
    atk = next(a for a in m.attacks if a.get('effect') == 'forgetting')
    m._apply_attack_effect(atk, p)
    m._apply_attack_effect(atk, p)
    assert p.__dict__['_pending_forget'] == [effect_rules.token(m)]


# ---------------------------------------------------------------------------
# Charmed, Knocked Down, Hexed, old saves
# ---------------------------------------------------------------------------

def test_a_hold_ends_with_whoever_laid_it():
    g = _scene(('harpy', 2, 0))
    p, m = g.player, g.monsters[0]
    for effect in ('feared', 'charmed'):
        p.add_effect(effect, 4)
        effect_rules.laid_by(p, effect, m)
    m.alive = False
    g._effects_after_world()
    assert not p.has_effect('charmed') and not p.has_effect('feared')


def test_a_charm_ends_into_clear_sight():
    p = Player()
    p.add_effect('charmed', 3)
    S.end_bout(p, 'charmed')
    assert p.has_effect('clear_sight')


def test_a_trample_floors_and_guard_stands(worst_luck):
    m, atk = _mon('troll'), {'delivery': 'trample'}
    p = Player()
    assert knockdown.from_trample(m, p, atk, 5) and p.has_effect('knocked_down')
    q = Player()
    q.stance = 'guard'
    assert not knockdown.from_trample(m, q, atk, 5) and not q.has_effect('knocked_down')


def test_knocked_down_waits_for_him():
    p = Player()
    p.add_effect('knocked_down', 1)
    for _ in range(5):
        S.tick_all(p)
    assert p.has_effect('knocked_down') and p.dodge_chance() == 0.0


def test_a_curse_on_the_hero_is_a_hex():
    p = Player()
    p.add_effect('cursed', 20)
    assert p.has_effect('hexed') and not p.has_effect('cursed')


def test_an_older_save_loads_hexed_and_plays():
    p = Player()
    p.status_effects.update({'cursed': 9, 'stunned': 2})
    p.__dict__.pop('_bouts', None)
    old = pickle.loads(pickle.dumps(p))
    assert old.status_effects.get('hexed') == 9 and 'cursed' not in old.status_effects
    assert G.verdict(old, 'step').what == G.FALL


def test_a_cure_leaves_what_worn_gear_holds():
    p = Player()
    p.status_effects.update({'fumbling': -1, 'poisoned': 4, 'reloading': 1})
    assert S.ailments_on(p) == ['poisoned']


# ---------------------------------------------------------------------------
# The quiz: display only, and no pile of it an auto-kill
# ---------------------------------------------------------------------------

def test_the_waits_share_one_settle_time_and_the_dark_has_none():
    p = Player()
    p.status_effects['confused'] = 3
    one = Q.wait_for(p, True)
    p.status_effects.update(stunned=3, hallucinating=3, blinded=3)
    assert Q.wait_for(p, True) == one > 0
    q = Player()
    q.status_effects['blinded'] = 3
    assert Q.wait_for(q, True) == 0.0 and Q.sight_for(q)['dark']


@pytest.mark.parametrize('a,b', (('1/2', '0.5'), ('1/2', '50%'), ('50', '50%'), ('1 1/2', '3/2'),
                                 ('2:4', '1:2'), ('1,000', '1000'), ('.5', '1/2'), ('four', '4'),
                                 ('3 days', '72 hours'), ('50 cm', '0.5 m'), ('The Moon', "Earth's moon")))
def test_two_ways_to_write_one_answer_are_one_answer(a, b):
    assert Q.same_answer(a, b) and Q.same_answer(b, a)


def test_different_answers_are_different():
    assert not Q.same_answer('12', '15') and not Q.same_answer('Paris', 'Rome')


def _number(text):
    try:
        t = str(text).replace(',', '').replace(':', '/').strip()
        return Fraction(t[:-1]) / 100 if t.endswith('%') else Fraction(t)
    except (ValueError, ZeroDivisionError):
        return None


def _dream_words() -> set:
    d = Q.rules()['phantom']['dream']
    return {s + x for s in d['starts'] for x in d['ends']}


def _maths():
    with open(os.path.join(ROOT, 'data', 'questions', 'math.json'), encoding='utf-8') as f:
        return json.load(f)


def test_a_false_factor_never_divides():
    bank = _maths()
    seen = 0
    for q in bank:
        if not q['question'].startswith('Which'):
            continue
        n = int(''.join(c for c in q['question'] if c.isdigit()))
        pool = [o for o in bank if o['tier'] == q['tier']]
        for seed in range(25):
            text = Q.phantom_for(q, pool, seed, 'math')['text']
            v = _number(text)
            if v is not None:
                seen += 1
                assert not (v != 0 and v.denominator == 1 and n % int(v) == 0), (q['question'], text)
    assert seen > 500


def test_a_sum_still_gets_a_number_to_doubt():
    bank = _maths()
    dreams = 0
    sample = bank[::3]
    for n, q in enumerate(sample):
        pool = [o for o in bank if o['tier'] == q['tier']]
        dreams += set(Q.phantom_for(q, pool, n, 'math')['text'].lower().split()) <= _dream_words()
    assert dreams <= len(sample) * 0.05, (dreams, len(sample))


@pytest.mark.parametrize('subject', SUBJECTS)
def test_a_false_answer_is_never_a_real_one(subject):
    with open(os.path.join(ROOT, 'data', 'questions', f'{subject}.json'), encoding='utf-8') as f:
        bank = json.load(f)
    asked = offered = 0
    for tier in sorted({q['tier'] for q in bank}):
        pool = [q for q in bank if q['tier'] == tier]
        for n, q in enumerate(pool[::7]):
            asked += 1
            before = copy.deepcopy(q)
            ph = Q.phantom_for(q, pool, n, subject)
            assert q == before, 'the question was touched'
            if ph is None:
                continue
            offered += 1
            text = ph['text'].strip().lower()
            assert text not in [str(c).strip().lower() for c in q['choices']], (q['question'], text)
            if subject != 'math':
                # (Another question's wrong answer might be true of this one.)
                assert set(text.split()) <= _dream_words(), (q['question'], text)
            elif _number(text) is not None:
                assert _number(text) != _number(q['answer']), (q['question'], text)
    assert offered >= asked * 0.75, (subject, offered, asked)


def test_no_number_moves_for_a_false_answer():
    for slot in range(5):
        ph = {'slot': slot}
        shown = Q.with_phantom(list('abcd'), ph, 'x')
        real = [Q.real_index(i, ph) for i in range(5)]
        assert real.count(None) == 1 and shown[slot] == 'x'
        assert all('abcd'[r] == shown[i] for i, r in enumerate(real) if r is not None)


def _asking(g, effect):
    from quiz_engine import QuizState
    qe = g.quiz_engine
    q = {'question': '2 + 2 = ?', 'answer': '4', 'choices': ['3', '4', '5', '6'], 'topic': 'sums', 'tier': 1}
    other = {'question': '9 + 9 = ?', 'answer': '18', 'choices': ['17', '18', '91', '81'], 'topic': 'more'}
    qe.current_question, qe.subject, qe.tier, qe.timed = q, 'math', 1, True
    qe.state = QuizState.ASKING
    qe.confused_order = None
    qe.q_elapsed, qe.scramble_seed = 0.0, 11
    qe._decks[('math', 1)] = [q, other]
    g.player.status_effects[effect] = 3
    qe._stamp_sight()
    return qe, q


def test_the_false_answer_is_no_answer(monkeypatch):
    g = _scene()
    qe, q = _asking(g, 'hallucinating')
    given = []
    monkeypatch.setattr(qe, 'answer', given.append)
    ph = qe.phantom_slot()
    assert ph and qe.phantom_shows()
    keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5)
    g._quiz_input(keys[ph['slot']])
    assert given == [] and q['choices'] == ['3', '4', '5', '6']
    for i, key in enumerate(keys):
        if i != ph['slot']:
            g._quiz_input(key)
    assert given == ['3', '4', '5', '6']


def test_blind_the_arrows_move_the_light_and_the_numbers_still_answer(monkeypatch):
    g = _scene()
    qe, _q = _asking(g, 'blinded')
    given = []
    monkeypatch.setattr(qe, 'answer', given.append)
    g._quiz_input(pygame.K_RIGHT)
    assert qe.dark_view() == 1
    g._quiz_input(pygame.K_RETURN)
    g._quiz_input(pygame.K_3)
    assert given == ['4', '5']


def test_double_vision_never_leaves_its_room():
    """A glyph cut at a card's edge is another glyph ("60" read "50")."""
    for offset in ((0, 0), (5, 3), (13, 9), (34, 24)):
        for room in ((0, 0, 0, 0), (6, 1, 40, 8), (90, 30, 90, 30), (6, 9, 2, 0)):
            left, up, right, down = room
            (ax, ay), (bx, by) = Q.ghost_places(offset, room)
            assert -left <= ax <= 0 <= bx <= right and -up <= ay <= 0 <= by <= down, (offset, room)
    assert Q.ghost_places((13, 9), (90, 90, 90, 90)) == [(-13, -9), (13, 9)]
    assert Q.ghost_places((13, 9), (6, 90, 90, 90)) == [(-6, -9), (20, 9)]


def test_a_false_face_is_never_the_creatures_own():
    m = _mon('troll')
    for turn in range(0, 80, 4):
        assert Q.false_face(m, turn)[0] != 'troll'


# ---------------------------------------------------------------------------
# The data
# ---------------------------------------------------------------------------

def test_the_content_pass_has_not_drifted():
    path = os.path.join(ROOT, 'tools', 'content', 'effects_pass_2026_11_22.py')
    spec = importlib.util.spec_from_file_location('effects_pass_2026_11_22', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.run(True) == []


@pytest.mark.parametrize('effect', ('forgetting', 'charmed', 'petrifying', 'knocked_down'))
def test_a_defence_can_be_had_before_each_that_lays_it(effect):
    """Some minor slot guards each such blow, and a piece of it is found by
    the floor that creature begins on."""
    import guards
    from items import load_items
    with open(os.path.join(ROOT, 'data', 'armor_guards.json'), encoding='utf-8') as f:
        slots = list(json.load(f)['families'])
    first = {}
    for a in load_items('armor'):
        s = getattr(a, 'slot', '')
        first[s] = min(first.get(s, 999), int(getattr(a, 'min_level', 1) or 1))
    bare, seen = [], 0
    for kind, d in MONS.items():
        if not isinstance(d, dict):
            continue
        floor = int(d.get('min_level', 1))
        for atk in d.get('attacks') or ():
            if effect == 'knocked_down':
                if not (atk.get('shove') or atk.get('delivery') == 'trample'):
                    continue
                atk = dict(atk, effect=effect)
            elif atk.get('effect') != effect:
                continue
            seen += 1
            if not any(first.get(s, 999) <= floor and guards.matches(guards.family(s), atk)[1]
                       for s in slots):
                bare.append((kind, floor, atk.get('name')))
    assert seen and not bare, bare


def test_the_oil_is_known_by_its_look_never_by_a_mark():
    import traders
    from items import make_item_by_id
    defn = next(iter(traders.data()['traders'].values()))
    places = set()
    for seed in range(12):
        stock = traders.build_stock(defn, 19, random.Random(seed))
        at = next(n for n, i in enumerate(stock) if getattr(i, 'id', '') == 'oil_of_rue')
        assert not getattr(stock[at], '_counter', None)
        places.add(len(stock) - 1 - at)
    assert len(places) > 1, 'always in one place is a mark'
    look = make_item_by_id('potion', 'oil_of_rue').unidentified_name
    with open(os.path.join(ROOT, 'data', 'tells.json'), encoding='utf-8') as f:
        assert look.lower() in json.load(f)['effects']['petrify_lethal']['counter'].lower()


# ---------------------------------------------------------------------------
# The independent audit of 2026-11-22: one test a finding
# ---------------------------------------------------------------------------

def test_no_wave_of_his_takes_his_charmer():
    import holds
    g = _scene(('harpy', 2, 0), ('troll', -2, 0))
    p, (harpy, troll) = g.player, g.monsters
    for m in (harpy, troll):
        g.visible.add((m.x, m.y))
    assert g._in_hero_reach(harpy)
    p.add_effect('charmed', 3)
    effect_rules.laid_by(p, 'charmed', harpy)
    assert not g._in_hero_reach(harpy) and not g._in_spell_sight(harpy)
    assert g._in_hero_reach(troll)
    assert holds.strikable(p, g.monsters) == [troll]
    assert holds.strikable(p, g.monsters, spare=False) == [harpy, troll]
    assert g._nearest_visible_monster() is not harpy


def test_fear_spares_by_a_blow_only():
    g = _scene(('troll', 1, 0))
    p, m = g.player, g.monsters[0]
    p.add_effect('feared', 3)
    effect_rules.laid_by(p, 'feared', m)
    assert effect_rules.spares(p, m, melee=True) and not effect_rules.spares(p, m)


@pytest.mark.parametrize('warded', (True, False))
def test_a_ward_against_death_answers_stone(warded):
    from game_states import STATE_DEAD
    g = _scene(hp=500)
    p = g.player
    p.immortal = warded
    p.status_effects['petrifying'] = 1
    effect_rules.laid_by(p, 'petrifying', lethal=True)
    g._advance_turn()
    assert (g.state != STATE_DEAD) is warded
    if warded:
        assert p.hp > 0 and not p.has_effect('petrifying')


def test_a_bosses_page_is_never_eaten():
    p = Player()
    p.studied_monster_ids = {'asterion_minotaur', 'troll'}
    p.lore_known_monster_ids = set()
    got = mind_theft.page_candidates(p)
    assert 'asterion_minotaur' not in got
    assert mind_theft.relearnable('troll') and not mind_theft.relearnable('asterion_minotaur')


def test_a_page_eaten_can_be_studied_again():
    from items import Corpse, corpse_is_known
    g = _scene(('intellect_devourer', 1, 0))
    p = g.player
    corpse = Corpse.__new__(Corpse)
    corpse.__dict__.update(monster_id='troll', id_level=5, id='troll_corpse', x=p.x, y=p.y)
    g.ground_items[:] = [corpse]
    p.studied_monster_ids = {'troll'}
    p.lore_known_monster_ids = set()
    rec = mind_theft.eat_page(p, 'troll', 'tok', 'Troll')
    g._forget_corpses('troll')
    assert not corpse_is_known(p, corpse)
    mind_theft.give_back(p, rec)
    assert corpse_is_known(p, corpse)


def test_polymorph_keeps_who_ate_it():
    import game_magic
    g = _scene(('intellect_devourer', 2, 0))
    old = g.monsters[0]
    tok = effect_rules.token(old)
    new = _mon('troll', old.x, old.y)
    game_magic._polymorph_swap(g, old, new)
    assert effect_rules.is_source(new, tok) and not effect_rules.is_source(old, tok)


def test_a_story_keeps_its_price():
    assert S.price_cap('weakened', 200) == 60 and S.price_cap('silenced', 15) == 15
    assert S.price_cap('paralyzed', 30) is None and S.price_cap('slowed', 30) is None
    assert S.landed_as('cursed') == 'hexed'
    p = Player()
    p.add_effect('silenced', 15, cap=S.price_cap('silenced', 15))
    assert p.status_effects['silenced'] == 15


def test_no_price_for_what_could_not_be_done(monkeypatch):
    from spells import LEARNABLE_SPELLS
    g = _scene()
    p = g.player
    spell = next(k for k, s in LEARNABLE_SPELLS.items() if s.get('mp_cost') and not s.get('needs_target')
                 and not s.get('needs_tile') and s.get('effect') != 'light')
    p.known_spells = {spell: 1}
    p.mp = 0
    p.add_effect('stunned', 3)
    turns = []
    monkeypatch.setattr(g, '_advance_turn', lambda *a, **k: turns.append(1))
    g._invoke_spell(spell)
    assert turns == [] and not effect_rules.bout(p, 'stunned').get('fizzled')


def test_an_empty_wand_is_not_fumbled(monkeypatch):
    from items import load_items
    g = _scene()
    p = g.player
    wand = copy.copy(next(w for w in load_items('wand')
                          if w.id not in ('philosophers_wrench', 'flux_capacitor')))
    wand.charges = 0
    p.inventory[:] = [wand]
    p.add_effect('stunned', 3)
    monkeypatch.setattr(g, '_advance_turn', lambda *a, **k: None)
    g._invoke_wand(wand)
    assert not effect_rules.bout(p, 'stunned').get('dropped') and wand not in g.ground_items


@pytest.mark.parametrize('lethal', (False, True))
def test_gorgon_ward_wants_the_stone_that_kills(monkeypatch, lethal):
    g = _scene()
    p, qs = g.player, g.quirk_system
    p.add_effect('petrifying', 4)
    effect_rules.laid_by(p, 'petrifying', lethal=lethal)
    counted = []
    real = qs._inc
    monkeypatch.setattr(qs, '_inc', lambda key, *a: (counted.append(key), real(key, *a))[1])
    qs.on_turn()
    p.status_effects.pop('petrifying')
    qs.on_turn()
    assert ('gorgon_ward_petrify' in counted) is lethal


def test_an_older_saves_monster_lays_what_its_kind_lays_now():
    m = _mon('basilisk')
    m.__dict__.pop('_effects_pass')
    m.attacks = [dict({k: v for k, v in a.items() if k != 'lethal'}, effect='paralyzed')
                 if a.get('effect') == 'petrifying' else a for a in m.attacks]
    assert effect_rules.refresh_monster(m)
    stone = next(a for a in m.attacks if a.get('effect') == 'petrifying')
    assert stone['lethal'] and not effect_rules.refresh_monster(m)


def test_an_aura_rolls_one_save(monkeypatch):
    monkeypatch.setattr(random, 'randint', lambda a, b: b)      # the best of rolls
    p = Player()
    applied, _said = S.apply_debuff_with_save(p, 'weakened', 4, S.SAVE_FAILED)
    assert applied and p.status_effects['weakened'] == 4


def test_lengthening_a_stun_himself_makes_it_his_own():
    p = Player()
    p.add_effect('stunned', 3)
    S.apply_penalty(p, 'stunned', 11)
    assert G.verdict(p, 'step').open


def test_immobilized_in_a_pit_he_may_still_bump(monkeypatch):
    from game_states import STATE_QUIZ
    g = _scene(('troll', 1, 0))
    g.player.status_effects.update(in_pit=-1, immobilized=3)
    monkeypatch.setattr(g, '_sees_monster', lambda mon: True)
    g._do_move(1, 0)
    assert g.state == STATE_QUIZ


def test_levitating_he_has_no_floor_to_fall_on():
    p = Player()
    p.add_effect('stunned', 3)
    p.status_effects['levitating'] = 5
    assert G.verdict(p, 'step').open


def test_standing_gives_three_turns_of_footing():
    g = _scene()
    g.player.status_effects['knocked_down'] = 1
    g._stand_up()
    assert g.player.status_effects['footing'] == 3


def test_a_false_face_gives_no_secret_away():
    kinds = Q._face_kinds()
    assert len(kinds) > 100
    assert 'black_knight' not in kinds and 'hell_bovine' not in kinds


def test_the_line_names_who_held_him():
    p = Player()
    p.add_effect('charmed', 3)
    effect_rules.laid_by(p, 'charmed', _mon('harpy'))
    assert effect_rules.bout(p, 'charmed')['by_the'].lower() == 'the harpy'


def test_a_potions_card_says_what_it_lays():
    import types
    import food_system
    for eff, status in (('weakness', 'weakened'), ('slow', 'slowed'), ('fumbling', 'fumbling'),
                        ('blindness', 'blinded')):
        card = food_system.potion_turns(types.SimpleNamespace(effect=eff, duration=40))
        assert card == S.STATUS_CAP[status], eff


def test_a_lifted_curse_lifts_a_hex():
    p = Player()
    p.add_effect('hexed', 20)
    assert S.lift_hex(p) and not p.has_effect('hexed') and not S.lift_hex(p)


def test_the_slowers_of_the_first_twenty_floors_ask_two_or_three():
    for kind, d in MONS.items():
        if not isinstance(d, dict) or int(d.get('min_level', 1)) > 19 or d.get('is_boss'):
            continue
        if kind in ('wight', 'green_hag', 'spriggan') or kind.startswith('blue_m'):
            for a in d.get('attacks') or ():
                if a.get('effect') == 'slowed' and str(a.get('effect_duration')).isdigit():
                    assert int(a['effect_duration']) <= 3, (kind, a['name'])
