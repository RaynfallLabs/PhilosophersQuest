"""The one gate (Brandon, 2026-11-22: monster effects, "All as recommended").

Stun, slow, ice, fear and the rest used to be asked inside Game._do_move,
which A, F, S, Q, Z, R, M and V never enter: a stunned hero attacked with A
every time. Three layers here:

1. every effect against every door, on the pure gate, from a table written
   out by hand (a change of rule changes this table on purpose);
2. the same through the Game's real commit points;
3. a guard: whatever spends a turn asks a door, or is named below with the
   door it follows.

What these cannot prove (how a fall or a drop FEELS) is a play-test question.
"""
from __future__ import annotations

import ast
import copy
import glob
import os

import pytest

import action_gate as G
import effect_rules
from game_states import STATE_PLAYER, STATE_QUIZ
from test_bugbash_360_monsters import _scene

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


class _Hero:
    def __init__(self):
        self.status_effects = {}
        self.stance = 'neutral'

    def has_effect(self, e):
        return self.status_effects.get(e, 0) != 0


DOORS = ('step', 'stairs', 'climb', 'ride', 'strike', 'shoot', 'throw', 'swap', 'doff', 'drink', 'eat',
         'wand', 'cast', 'read', 'apply', 'power', 'pray', 'pickup', 'drop', 'stance', 'work',
         'pet', 'wait')

# effect -> {door: what the gate answers}; every door left out is open.
EVERY = dict.fromkeys(DOORS)
EXPECT = {
    'sleeping': {d: G.LOSE for d in EVERY},
    'paralyzed': {d: G.LOSE for d in EVERY},
    'knocked_down': {d: G.STAND for d in EVERY},
    'frozen': {'step': G.LOSE, 'stairs': G.LOSE, 'climb': G.LOSE,
               **{d: G.REFUSE for d in ('ride', 'swap', 'doff', 'drink', 'wand', 'shoot', 'throw', 'apply')}},
    'immobilized': {'step': G.LOSE, 'stairs': G.LOSE, 'climb': G.LOSE, 'ride': G.REFUSE},
    'silenced': {'cast': G.REFUSE, 'read': G.REFUSE},
    'hexed': {d: G.REFUSE for d in ('swap', 'doff', 'drop')},
    'feared': {'step': G.REFUSE, 'strike': G.REFUSE},
    'charmed': {d: G.REFUSE for d in ('strike', 'shoot', 'throw', 'wand', 'cast', 'power', 'stairs')},
    'stunned': {'step': G.FALL, 'cast': G.FIZZLE,
                **{d: G.DROP for d in ('swap', 'drink', 'wand', 'read')}},
    'fumbling': {d: G.DROP for d in ('swap', 'drink', 'wand', 'read')},
    # These shut no door: their price is the clock, the map or the quiz.
    'slowed': {}, 'confused': {}, 'blinded': {}, 'hallucinating': {}, 'weakened': {},
    'petrifying': {}, 'forgetting': {}, 'poisoned': {}, 'bleeding': {}, 'burning': {},
    'diseased': {}, 'corroding': {},
}


def test_the_table_names_every_door():
    assert set(DOORS) == set(G.doors())


def test_the_table_names_every_rule_of_the_gate():
    assert set(effect_rules.gate_rules()) <= set(EXPECT)


@pytest.mark.parametrize('effect', sorted(EXPECT))
@pytest.mark.parametrize('door', DOORS)
def test_every_effect_against_every_door(effect, door):
    p = _Hero()
    p.status_effects[effect] = 3
    v = G.verdict(p, door, target=object(), worn=True, toward=True, source_here=True)
    assert v.what == EXPECT[effect].get(door, G.OPEN), (effect, door, v)


def test_an_unknown_door_is_an_error_not_an_open_door():
    with pytest.raises(ValueError):
        G.verdict(_Hero(), 'no_such_door')


@pytest.mark.parametrize('door', ('step', 'swap', 'drink', 'wand', 'read', 'cast'))
def test_in_guard_he_neither_falls_nor_drops(door):
    p = _Hero()
    p.status_effects['stunned'] = 3
    p.stance = 'guard'
    assert G.verdict(p, door).open


@pytest.mark.parametrize('door', ('step', 'swap', 'drink', 'cast'))
def test_his_own_stun_is_double_vision_only(door):
    p = _Hero()
    p.status_effects['stunned'] = 11
    effect_rules.self_inflicted(p, 'stunned')
    assert G.verdict(p, door).open


def test_each_price_is_paid_once_a_bout():
    p = _Hero()
    p.status_effects['stunned'] = 3
    for door, what in (('step', G.FALL), ('drink', G.DROP), ('cast', G.FIZZLE)):
        v = G.verdict(p, door)
        assert v.what == what
        G.paid(p, v)
        assert G.verdict(p, door).open


def test_cornered_the_frightened_may_fight_and_a_flame_thaws():
    p = _Hero()
    p.status_effects['feared'] = 3
    assert G.verdict(p, 'strike', target=object(), cornered=True).open
    q = _Hero()
    q.status_effects['frozen'] = 3
    assert G.verdict(q, 'drink', flame=True).what == G.THAW


def test_a_fear_with_an_owner_holds_only_against_that_owner():
    g = _scene(('troll', 1, 0), ('orc_warrior', -1, 0))
    feared, other = g.monsters
    p = g.player
    p.add_effect('feared', 3)
    effect_rules.laid_by(p, 'feared', feared)
    assert not G.verdict(p, 'strike', target=feared).open
    assert G.verdict(p, 'strike', target=other).open


# ---------------------------------------------------------------------------
# Through the Game: each commit point, whatever key or menu reached it
# ---------------------------------------------------------------------------

def _outfit(g):
    from items import load_items, make_item_by_id
    p = g.player
    weapons = load_items('weapon')
    blade = next(w for w in weapons if not getattr(w, 'requires_ammo', None)
                 and not getattr(w, 'two_handed', False) and not getattr(w, 'bound_to_wielder', False)
                 and not getattr(w, 'cursed', False) and not getattr(w, 'selects_wielder', False))
    bow = next(w for w in weapons if getattr(w, 'requires_ammo', None) == 'arrow'
               and getattr(w, 'weapon_class', '') != 'crossbow')
    arrows = copy.copy(next(a for a in load_items('ammo') if getattr(a, 'ammo_type', None) == 'arrow'))
    arrows.count = 40
    back = copy.copy(blade)
    p.weapon, p.ranged_weapon, p.shield = copy.copy(blade), copy.copy(bow), None
    potion = make_item_by_id('potion', 'potion_of_healing')
    scroll = copy.copy(load_items('scroll')[0])
    wand = copy.copy(load_items('wand')[0])
    wand.charges = 3
    food = make_item_by_id('food', 'bread_ration')
    flask = make_item_by_id('potion', 'potion_of_healing')
    p.inventory[:] = [back, arrows, potion, scroll, wand, food, flask]
    p.readied_weapon = back
    p.known_spells = {'light_spell': 1}
    p.mp = p.max_mp = 80
    return dict(back=back, potion=potion, scroll=scroll, wand=wand, food=food)


def _aim(g, m):
    g.target_cursor_x, g.target_cursor_y = m.x, m.y


def _act(g, door, m, kit):
    """Commit one action of ``door`` as its menu or cursor would."""
    p = g.player
    if door == 'step':
        g._do_move(0, 1)
    elif door == 'bump':
        g._do_move(1, 0)
    elif door == 'strike':
        _aim(g, m)
        g._confirm_melee_target()
    elif door == 'shoot':
        _aim(g, m)
        g._confirm_ranged_target()
    elif door == 'swap':
        g._swap_weapons()
    elif door == 'doff':
        g._unequip_slot('weapon', p.weapon)
    elif door == 'drink':
        g.quaff_menu_items = [kit['potion']]
        g._quaff_mode, g._quaff_sel = 'quaff', 0
        import pygame
        g._quaff_menu_input(pygame.K_RETURN)
    elif door == 'eat':
        g._eat_now(kit['food'])
    elif door == 'wand':
        g._invoke_wand(kit['wand'])
    elif door == 'read':
        g._read_scroll(kit['scroll'])
    elif door == 'cast':
        from spells import LEARNABLE_SPELLS
        g._invoke_spell(next(k for k, s in LEARNABLE_SPELLS.items() if not s.get('needs_target')
                             and not s.get('needs_tile') and s.get('effect') != 'light'))
    elif door == 'stance':
        g._cycle_stance()
    elif door == 'pickup':
        from items import make_item_by_id
        it = make_item_by_id('food', 'apple')
        it.x, it.y = p.x, p.y
        g.ground_items.append(it)
        g._pickup()
    elif door == 'drop':
        g._do_drop_item(kit['food'])
    elif door == 'pray':
        g._start_pray()
    else:
        raise AssertionError(door)


GAME_DOORS = ('step', 'bump', 'strike', 'shoot', 'swap', 'doff', 'drink', 'eat', 'wand', 'read',
              'cast', 'stance', 'pickup', 'drop', 'pray')
GAME_EFFECTS = ('sleeping', 'paralyzed', 'knocked_down', 'frozen', 'immobilized', 'silenced',
                'hexed', 'feared', 'charmed', 'stunned', 'fumbling', 'slowed', 'confused', 'blinded')


@pytest.fixture(scope='module')
def game():
    return _scene(('troll', 1, 0))


@pytest.mark.parametrize('effect', GAME_EFFECTS)
@pytest.mark.parametrize('door', GAME_DOORS)
def test_the_game_asks_the_gate_at_every_commit_point(game, monkeypatch, effect, door):
    g = game
    p, m = g.player, g.monsters[0]
    home = g.__dict__.setdefault('_test_home', (p.x, p.y))
    p.x, p.y = home
    m.x, m.y, m.alive = p.x + 1, p.y, True
    g.visible.add((m.x, m.y))
    g.ground_items[:] = []
    g.state = STATE_PLAYER
    p.status_effects.clear()
    p.__dict__.pop('_bouts', None)
    p.stance = 'neutral'
    kit = _outfit(g)
    p.add_effect(effect, 3)
    if effect in ('feared', 'charmed'):
        effect_rules.laid_by(p, effect, m)
    asked = []
    real = G.verdict

    def spy(*a, **k):
        v = real(*a, **k)
        asked.append((a[1], v.what))
        return v

    monkeypatch.setattr(G, 'verdict', spy)
    monkeypatch.setattr(g, '_advance_turn', lambda *a, **k: None)
    monkeypatch.setattr(g, '_sees_monster', lambda mon: True)
    _act(g, door, m, kit)
    if effect == 'charmed' and door == 'step':
        return                              # he stands gazing: test_a_charmed_step below
    assert asked, f'{door} never asked the gate under {effect}'
    shut = [w for _d, w in asked if w != G.OPEN]
    name = 'strike' if door == 'bump' else door
    want = EXPECT[effect].get(name, G.OPEN)
    if effect == 'hexed' and door == 'drop':
        want = G.OPEN                       # (what is dropped here is not worn)
    if effect == 'feared' and door == 'step':
        want = G.OPEN                       # (this step is sideways, so away)
    if effect == 'charmed' and door == 'cast':
        want = G.OPEN                       # (a spell on himself)
    if effect == 'charmed' and door == 'wand':
        want = G.OPEN                       # (asked again, with its target, as it is aimed)
    assert (shut[0] if shut else G.OPEN) == want, (effect, door, asked)


def test_a_charmed_step_walks_to_the_charmer(monkeypatch):
    g = _scene(('harpy', 4, 0))
    p, m = g.player, g.monsters[0]
    p.add_effect('charmed', 3)
    effect_rules.laid_by(p, 'charmed', m)
    monkeypatch.setattr(g, '_advance_turn', lambda *a, **k: None)
    monkeypatch.setattr(g, '_sees_monster', lambda mon: True)
    x = p.x
    g._do_move(-1, 0)
    assert p.x == x + 1


def test_confused_a_bump_hits_like_a(monkeypatch):
    g = _scene(('troll', 1, 0))
    g.player.add_effect('confused', 3)
    monkeypatch.setattr(g, '_sees_monster', lambda mon: True)
    g._do_move(1, 0)
    assert g.state == STATE_QUIZ


def test_stunned_the_a_key_still_strikes_and_the_step_falls(monkeypatch):
    g = _scene(('troll', 1, 0))
    g.player.add_effect('stunned', 3)
    monkeypatch.setattr(g, '_advance_turn', lambda *a, **k: None)
    g._do_move(0, 1)
    assert g.player.has_effect('knocked_down')


# ---------------------------------------------------------------------------
# The guard: nothing new spends a turn behind the gate's back
# ---------------------------------------------------------------------------

# Functions that spend a turn and ask no door themselves -> why that is right.
FOLLOWS = {
    '_close_bococho': 'closes a bump (work)',
    '_close_emberpup': 'closes a bump (work)',
    '_close_mooble': 'closes a bump (work)',
    '_close_npc_encounter': 'closes a bump (work)',
    '_consume_ranged_ammo_for_miss': 'shoot, _confirm_ranged_target',
    '_fire_ranged': 'shoot, _confirm_ranged_target',
    '_dig_pit': 'strike, _confirm_melee_target',
    '_on_fire_breath': 'power, _confirm_power_target',
    '_dress_begin_on': 'swap, _equip_item',
    '_dress_start_off': 'doff, _unequip_slot',
    '_equip_failed': 'swap, _equip_item',
    '_busy_run': 'its starter, and _busy_helpless each turn',
    '_gate_closed': 'the gate itself',
    '_gate_step': 'the gate itself',
    '_stand_up': 'the gate itself',
    '_horn_quiz_done': 'power, _power_menu_input',
    '_sceptre_quiz_done': 'power, _power_menu_input',
    '_manifest_complete': 'power, _power_menu_input',
    '_activate_hero_special': 'power, _power_menu_input',
    '_cock_crow': 'apply, _apply_item',
    '_start_spell_quiz': 'cast, _invoke_spell',
    '_read_book_of_thoth': 'read, _learn_from_spellbook',
    '_necro_complete': 'read, _learn_from_spellbook',
    '_identify_menu_input': 'read: a Scroll of Identify spent unchosen',
    '_drink_fafnirs_blood': 'drink, _quaff_menu_input',
    '_drink_quiz_draught': 'drink, _quaff_menu_input',
    '_ways_held_move': 'the struggle, after the wait door in _do_move',
    '_mooble_dance_key': 'a dance begun at a bump (work) or a pet order',
    '_race_leg_done': 'a race begun at a bump (work)',
    '_sk_dance_won': 'a dance begun at a bump (work)',
    '_sk_dance_lost': 'a dance begun at a bump (work)',
    '_render_service': 'a service bought: the trader does the work',
    '_resolve_trap_disarm': 'work, _try_disarm_trap',
    '_search_corpse': 'work, _harvest',
    '_finish_drop': 'drop, _do_drop_item',
    '_thoth_on_altar': 'drop, _do_drop_item',
    '_parley_toll': 'work, _parley_offer (the Xorn asked at D)',
    '_settle_toll': 'work, _parley_offer (paid or refused)',
}
_ASKS = {'_gate', '_gate_step', '_helpless_turn'}


def _spenders():
    for path in sorted(glob.glob(os.path.join(ROOT, 'src', '*.py'))):
        with open(path, encoding='utf-8') as f:
            tree = ast.parse(f.read())

        def visit(node, outer_asks):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.FunctionDef):
                    calls = {c.func.attr for c in ast.walk(child)
                             if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)}
                    asks = outer_asks or bool(calls & _ASKS)
                    # A quiz's on_complete is its action's: the door was
                    # asked before the question (the enclosing function).
                    if '_advance_turn' in calls and not asks and child.name != 'on_complete':
                        yield os.path.basename(path), child.name
                    yield from visit(child, asks)
                else:
                    yield from visit(child, outer_asks)
        yield from visit(tree, False)


def test_whatever_spends_a_turn_asks_a_door():
    loose = [(f, n) for f, n in _spenders() if n not in FOLLOWS]
    assert not loose, f'these spend a turn and ask no door: {loose}'
