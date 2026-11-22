"""The bug bash before 3.6.0, monsters and combat (findings h1-01 to h1-24).

Each test is one finding, or one sibling of its root cause:

  h1-01, 21  swallowed, the hero strikes only what holds him
  h1-02      every opener in the data can fire
  h1-03, 14  the Blue Men call before they strike, and stay angry
  h1-04, 12  peace holds for a pet, an escort and a pinned creature
  h1-05, 17  a pack does not wait on a mate that cannot act
  h1-06      a heal's line says what was healed
  h1-07      hiding in the dark ends with a light or a flight
  h1-08, 09, 19  fright, sleep and flight break what is drawn up
  h1-10      the view goes with a hero who is moved
  h1-11      no one acts once the run is over
  h1-13      a pinned holder only squeezes
  h1-15, 16  what the hero's light does and does not do
  h1-18      a silenced creature raises no one
  h1-23, 24  a call with no room; who an aura's death is blamed on
"""
from __future__ import annotations

import json
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PQ_NO_BONES', '1')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import holds  # noqa: E402
import senses  # noqa: E402
from dungeon import FLOOR, WALL, WATER  # noqa: E402
from game_states import STATE_DEAD, STATE_PLAYER, STATE_QUIZ  # noqa: E402
from items import load_items  # noqa: E402
from monster import Monster  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)
OPENERS = sorted(k for k, v in MONS.items() if isinstance(v, dict) and v.get('opener'))

_SCREEN = None


# ---------------------------------------------------------------------------
# A scene: a bare room with the hero in its middle
# ---------------------------------------------------------------------------

def _scene(*placed, seed=1, hp=900, half=8):
    global _SCREEN
    from main import Game
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    random.seed(seed)
    g = Game(_SCREEN, player_name='__test_bugbash_360_monsters__')
    g.state = STATE_PLAYER
    g.monsters, g.pets = [], []
    d = g.dungeon
    x = min(max(g.player.x, half + 1), d.width - half - 2)
    y = min(max(g.player.y, half + 1), d.height - half - 2)
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            d.tiles[y + j][x + i] = FLOOR
    d.traps = {}
    g.player.x, g.player.y = x, y
    g.player.max_hp = g.player.hp = hp
    for kind, dx, dy in placed:
        g.monsters.append(_mk(kind, x + dx, y + dy))
    g._refresh_fov()
    return g


@pytest.fixture(autouse=True)
def _a_step_was_taken():
    """The creatures that feel only a moving hero feel him (senses' turn
    state is the process's: no test here leans on the one before it)."""
    senses.begin_turn(moved=True, guilty=False, floor=5)


def _mk(kind, x, y, aware=True):
    m = Monster({**MONS[kind], 'id': kind}, x, y)
    if aware:
        m._aware = True
    return m


def _msgs(g, n=30):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _hold(g, m):
    """``m`` takes hold of the hero (its save failed)."""
    atk = next(a for a in m.attacks if holds.spec_of(a))
    real = random.randint
    random.randint = lambda a, b: a
    try:
        holds.after_blow(m, g.player, atk, 5, '')
    finally:
        random.randint = real
    assert holds.is_holder(m, g.player)


def _pet(g, x, y, acts=False):
    import pet_system
    key = next(k for k, v in pet_system._SPECIES.items()
               if not v.get('support') and k not in ('unicorn', 'duck_of_doom', 'dad'))
    p = pet_system.Pet(key, x, y)
    p.max_hp = p.hp = 800
    if not acts:
        p.take_turn = lambda *a, **k: None
    g.pets = [p]
    return p


def _wand(effect):
    return next(w for w in load_items('wand') if getattr(w, 'effect', '') == effect)


def _wand_of(effect):
    """A wand with an effect no wand of today's data carries (an old save's)."""
    import copy
    w = copy.copy(_wand('heal'))
    w.effect = effect
    return w


def _swallowed():
    g = _scene(('gelatinous_cube', 1, 1), ('orc_warrior', 0, -1))
    cube, out = g.monsters
    out.max_hp = out.hp = 999
    cube.max_hp = cube.hp = 999
    _hold(g, cube)
    assert holds.swallowed(g.player) and holds.shields(g.player, out)
    return g, cube, out


# ---------------------------------------------------------------------------
# h1-01, h1-21: swallowed, he strikes only what holds him
# ---------------------------------------------------------------------------

def _arm_bow(g):
    g.player.ranged_weapon = next(w for w in load_items('weapon')
                                  if getattr(w, 'requires_ammo', None) == 'arrow')
    arrows = next(a for a in load_items('ammo') if getattr(a, 'ammo_type', None) == 'arrow')
    arrows.count = 20
    g.player.inventory.append(arrows)
    return arrows


def _aim_spell(g):
    from spells import LEARNABLE_SPELLS, spell_reach
    sid = next(k for k, v in LEARNABLE_SPELLS.items() if v.get('needs_target')
               and not v.get('needs_tile') and spell_reach(v) is None)
    g.player.max_mp = g.player.mp = 999
    g._invoke_spell(sid)


AIMS = {
    'melee': lambda g: g._open_melee_targeting(),
    'ranged': lambda g: (_arm_bow(g), g._open_targeting()),
    'throw': lambda g: g._open_throw_targeting(next(iter(load_items('potion')))),
    'wand': lambda g: g._invoke_wand(_wand('fire_bolt')),
    'spell': _aim_spell,
    'observe': lambda g: g._start_observe(),
    'stuffie': lambda g: g._activate_power('stuffie_fire_breath'),
}


@pytest.mark.parametrize('how', sorted(AIMS))
def test_h1_01_the_cursor_opens_on_what_the_list_offers(how):
    g, cube, out = _swallowed()
    AIMS[how](g)
    assert out not in g._target_candidates
    assert (g.target_cursor_x, g.target_cursor_y) != (out.x, out.y)


def test_h1_01_a_spell_with_only_the_shielded_in_sight_is_not_paid_for():
    g, cube, out = _swallowed()
    g.visible.discard((cube.x, cube.y))
    _aim_spell(g)
    assert g.player.mp == 999 and g.state == STATE_PLAYER


def test_h1_01_a_blow_aimed_outside_the_gut_is_not_begun():
    g, cube, out = _swallowed()
    g.target_cursor_x, g.target_cursor_y = out.x, out.y
    g._confirm_melee_target()
    assert g.state != STATE_QUIZ
    assert any('strike only' in t for t in _msgs(g, 2))


def test_h1_01_a_shot_at_the_outside_is_not_loosed():
    g, cube, out = _swallowed()
    arrows = _arm_bow(g)
    g.target_cursor_x, g.target_cursor_y = out.x, out.y
    g._confirm_ranged_target()
    assert g.state != STATE_QUIZ and arrows.count == 20


def test_h1_01_from_the_gut_no_chest_is_bashed():
    from items import Container
    g, cube, out = _swallowed()
    chest = next(i for i in load_items('container') if isinstance(i, Container))
    chest.x, chest.y, chest.opened, chest.is_mimic = g.player.x - 1, g.player.y, False, True
    g.ground_items.append(chest)
    g.target_cursor_x, g.target_cursor_y = chest.x, chest.y
    g._confirm_melee_target()
    assert chest in g.ground_items and len(g.monsters) == 2


def test_h1_01_a_throw_at_the_outside_is_not_made():
    g, cube, out = _swallowed()
    potion = next(iter(load_items('potion')))
    g.player.inventory.append(potion)
    g._open_throw_targeting(potion)
    g.target_cursor_x, g.target_cursor_y = out.x, out.y
    g._confirm_throw_target()
    assert potion in g.player.inventory and out.hp == 999


def test_h1_01_a_wand_aimed_by_hand_spends_no_charge_outside():
    g, cube, out = _swallowed()
    wand = _wand('fire_bolt')
    wand.charges = 5
    g._invoke_wand(wand)
    g.target_cursor_x, g.target_cursor_y = out.x, out.y
    g._confirm_wand_target()
    assert g.state != STATE_QUIZ and wand.charges == 5


def test_h1_01_a_spell_aimed_by_hand_outside_is_given_back():
    g, cube, out = _swallowed()
    _aim_spell(g)
    g.target_cursor_x, g.target_cursor_y = out.x, out.y
    g._confirm_power_target()
    assert g.state != STATE_QUIZ and g.player.mp == 999


def test_h1_01_the_nearest_target_is_one_he_can_reach():
    g, cube, out = _swallowed()
    assert g._nearest_visible_monster() is cube


def test_h1_01_a_chain_special_finds_no_one_outside():
    g, cube, out = _swallowed()
    g._start_combat(cube)
    assert out not in g.player._combat_monsters_ref
    assert cube in g.player._combat_monsters_ref


def test_h1_01_free_the_hero_reaches_everyone():
    g = _scene(('orc_warrior', 0, -1), ('orc_warrior', 1, 0))
    g._start_combat(g.monsters[0])
    assert g.monsters[1] in g.player._combat_monsters_ref


def test_h1_01_a_heros_power_stays_in_the_gut():
    import hero_specials
    g, cube, out = _swallowed()
    hero_specials._eff_self_aoe_fire(g, {}, {'radius': 3, 'dice': '3d6'}, 3)
    assert out.hp == 999 and cube.hp < 999
    cube.hp = 999
    hero_specials._eff_damage_single(g, {}, {'dice': '3d6'}, 3)
    assert out.hp == 999


def test_h1_01_boots_of_thor_stay_in_the_gut(monkeypatch):
    import armor_procs
    g, cube, out = _swallowed()
    monkeypatch.setattr(armor_procs, 'player_has_armor_proc', lambda p, f: f == 'thors_step')
    monkeypatch.setattr(armor_procs, 'proc_value', lambda p, f: 1.0 if f == 'thors_step' else 0)
    cube.take_turn = out.take_turn = lambda *a, **k: False
    for _ in range(3):
        g._advance_turn()
    assert out.hp == 999


def test_h1_01_the_cockerels_crow_is_heard_only_by_the_gut(monkeypatch):
    import counters
    g, cube, out = _swallowed()
    tech = dict(counters.technique('cock_crow'))
    tech['drives'] = ['orc_warrior']
    monkeypatch.setattr(counters, 'technique', lambda name: tech)
    g._advance_turn = lambda: None
    g._cock_crow(None)
    assert not out.has_effect('stunned')


def test_h1_21_time_freeze_stays_in_the_gut():
    from spells import LEARNABLE_SPELLS
    g, cube, out = _swallowed()
    g._apply_spell_effect(LEARNABLE_SPELLS['time_freeze_spell'])
    assert not out.has_effect('paralyzed')


def test_h1_21_genocide_stays_in_the_gut():
    g = _scene(('gelatinous_cube', 1, 1), ('gelatinous_cube', -1, -1))
    holder, out = g.monsters
    for m in g.monsters:
        m.max_hp = m.hp = 20               # no big foe on the floor he stands on
    _hold(g, holder)
    scroll = max((s for s in load_items('scroll') if s.effect == 'genocide'),
                 key=lambda s: int(getattr(s, 'tier', s.quiz_tier)))
    g._apply_scroll_effect(scroll)
    assert out.alive and not holder.alive


def test_h1_21_free_time_freeze_still_takes_the_whole_level():
    from spells import LEARNABLE_SPELLS
    g = _scene(('orc_warrior', 2, 0), ('orc_warrior', 8, 8))
    far = g.monsters[1]
    g.visible.discard((far.x, far.y))
    g._apply_spell_effect(LEARNABLE_SPELLS['time_freeze_spell'])
    assert far.has_effect('paralyzed')


# ---------------------------------------------------------------------------
# h1-02: every opener in the data can fire
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def arena():
    return _scene(hp=90000)


def _opens(g, kind, first_blow=False) -> bool:
    """Through take_turn and attack: the creature's opener is struck."""
    x, y = g.player.x, g.player.y
    op = MONS[kind]['opener']
    rng = int(op.get('range', 1) or 1)
    dists = (1, 2) if rng == 1 else (min(rng, 3), 2)
    for trial in range(12):
        random.seed(trial)
        d = dists[trial % 2]
        lurker = MONS[kind]['ai_pattern'] in ('ambush', 'mimic')
        if lurker:
            d = 1 if MONS[kind]['ai_pattern'] == 'mimic' else min(d, 2)
        m = _mk(kind, x + d, y, aware=not lurker)
        if senses.rooted(m) and 'blind' in senses.senses_of(m):
            # It cannot walk, nor see him coming (the bug walked it up to him,
            # 2026-11-22): he has come as near as it feels his step.
            m.x = x + min(d, senses.sense_range(m, 'tremor'))
        if not lurker:
            m._alerted = True
        m.speed = max(10, m.speed)
        # (a pack hunter keeps its nerve with a friend or two beside it)
        around = [m]
        if MONS[kind].get('pack_dependent'):
            around += [_mk(kind, x + d + 1, y + j) for j in (-1, 1)]
        g.monsters = around
        for _turn in range(10):
            senses.begin_turn(moved=True, guilty=False, floor=5)     # (some feel only a step)
            g.player.hp = g.player.max_hp
            g.player.status_effects = {}
            g.player.__dict__.pop('_held', None)
            g.player.x, g.player.y = x, y
            m.hp = m.max_hp
            m.tick_effects()
            if not m.take_turn(g.player, g.dungeon, around):
                continue
            armed = m.__dict__.get('_opener_now')
            m.attack(g.player)
            if armed is not None and '_opener_now' not in m.__dict__:
                assert armed.get('name') == op['attack']
                return True
            if first_blow:
                break                          # it struck, and it was not the opener
    return False


def test_h1_02_the_data_has_openers():
    assert len(OPENERS) >= 240


@pytest.mark.parametrize('kind', OPENERS)
def test_h1_02_every_opener_can_fire(arena, kind):
    assert _opens(arena, kind), f"{kind}'s opener never fires"


@pytest.mark.parametrize('kind', ['lurking_horror', 'gilded_mimic', 'hellmouth', 'takshaka_brood',
                                  'wererat', 'impundulu', 'pegasus', 'green_slime', 'assassin_vine'])
def test_h1_02_a_pounce_is_the_first_blow(arena, kind):
    """monster.py: "its first blow is its opener"; a mimic's is its spring."""
    g = arena
    g.player.hp = g.player.max_hp
    g.player.status_effects = {}
    m = _mk(kind, g.player.x + 1, g.player.y, aware=MONS[kind]['ai_pattern'] != 'mimic')
    m._alerted = True
    m.speed = 10
    random.seed(3)
    senses.begin_turn(moved=True, guilty=False, floor=5)
    if kind == 'pegasus':
        import lanes
        m._backed = 99
        real, lanes.back_off = lanes.back_off, lambda *a, **k: False
        try:
            assert m.take_turn(g.player, g.dungeon, [m])
        finally:
            lanes.back_off = real
    else:
        assert m.take_turn(g.player, g.dungeon, [m])
    assert m.__dict__.get('_opener_now', {}).get('name') == MONS[kind]['opener']['attack']


def test_h1_02_a_gaze_drawn_up_is_one_gaze():
    g = _scene(('floating_eye', 3, 0))
    m = g.monsters[0]
    m.speed = 10
    m._tracking = True
    assert not m.take_turn(g.player, g.dungeon, g.monsters)      # the tell
    assert m.take_turn(g.player, g.dungeon, g.monsters)
    m.attack(g.player)
    assert '_opener_now' not in m.__dict__                       # not a second one next turn


# ---------------------------------------------------------------------------
# h1-03, h1-14: the Blue Men
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('dist', [1, 2, 4])
@pytest.mark.parametrize('seed', [1, 2, 3])
def test_h1_03_the_blue_men_call_before_they_strike(dist, seed):
    g = _scene(('blue_men_of_the_minch', dist, 0), seed=seed)
    m = g.monsters[0]
    m._aware = False
    m.speed = 10
    m.perception_range = 10
    struck = []
    m.attack = lambda p: (struck.append(1), (0, ''))[1]
    g._advance_turn()
    assert m.__dict__.get('_lp_parley') == 'waiting'
    assert not struck
    import lore_powers
    assert lore_powers.spec(m, 'parley')['call'] in _msgs(g, 12)


def test_h1_03_roused_by_the_game_they_still_call_once():
    g = _scene(('blue_men_of_the_minch', 4, 0))
    m = g.monsters[0]
    m._tracking = True
    g._advance_turn()
    g._advance_turn()
    import lore_powers
    assert _msgs(g, 30).count(lore_powers.spec(m, 'parley')['call']) == 1


def test_h1_03_the_call_is_one_turn_with_no_game_to_say_it():
    g = _scene(('blue_men_of_the_minch', 4, 0))
    m = g.monsters[0]
    m.speed = 10
    assert not m.take_turn(g.player, g.dungeon, g.monsters)
    assert m.take_turn(g.player, g.dungeon, g.monsters)        # (a simulation, a tool)


def test_h1_14_an_angered_blue_man_stays_angry():
    g = _scene(('blue_men_of_the_minch', 4, 0), ('blue_men_of_the_minch', 4, 2))
    a, b = g.monsters
    a._lp_parley = 'angry'
    b._tracking = True
    g._lore_powers_parley_tick(b)
    assert a._lp_parley == 'angry' and b._lp_parley == 'angry'


def test_h1_14_a_calmed_one_is_not_asked_again():
    g = _scene(('blue_men_of_the_minch', 4, 0), ('blue_men_of_the_minch', 4, 2))
    a, b = g.monsters
    a._lp_parley, a._lp_calm = 'calm', True
    b._tracking = True
    g._lore_powers_parley_tick(b)
    assert a._lp_parley == 'calm' and b._lp_parley == 'waiting'


def test_h1_14_the_answer_is_for_those_who_asked():
    g = _scene(('blue_men_of_the_minch', 4, 0), ('blue_men_of_the_minch', 4, 2))
    a, b = g.monsters
    a._lp_parley, b._lp_parley = 'waiting', 'angry'
    asked = {}
    g.quiz_engine.start_quiz = lambda **kw: asked.update(kw)
    g._advance_turn = lambda: None
    assert g._parley_offer()
    asked['callback'](types.SimpleNamespace(success=True))
    assert a._lp_parley == 'calm' and b._lp_parley == 'angry'


# ---------------------------------------------------------------------------
# h1-04, h1-12: peace
# ---------------------------------------------------------------------------

PEACE = [('kappa', {'_lp_calm': True}),
         ('preta', {'_lp_calm': True}),
         ('blue_men_of_the_minch', {'_lp_parley': 'waiting', '_lp_wait': 6})]


@pytest.mark.parametrize('kind,state', PEACE)
def test_h1_04_a_creature_at_peace_strikes_no_pet(kind, state):
    g = _scene((kind, 2, 0))
    m = g.monsters[0]
    m.__dict__.update(state)
    p = _pet(g, m.x - 1, m.y)
    g._monster_swipes(g.pets)
    assert p.hp == 800


@pytest.mark.parametrize('kind,state', PEACE)
def test_h1_04_nor_an_escort(kind, state):
    g = _scene((kind, 2, 0))
    m = g.monsters[0]
    m.__dict__.update(state)
    m.thac0 = -20
    who = types.SimpleNamespace(x=m.x - 1, y=m.y, hp=800, ac=0, alive=True, name='Tib')
    who.take_damage = lambda n: setattr(who, 'hp', who.hp - n)
    g._monster_swipes([who], escorts=True)
    assert who.hp == 800


def test_h1_04_an_ant_at_the_gold_has_no_blow_to_spare():
    g = _scene(('myrmekes', 2, 0))
    m = g.monsters[0]
    m._lp_busy = 3
    p = _pet(g, m.x - 1, m.y)
    g._monster_swipes(g.pets)
    assert p.hp == 800


@pytest.mark.parametrize('kind,state', PEACE)
def test_h1_04_a_pet_left_to_itself_does_not_break_the_peace(kind, state):
    g = _scene((kind, 3, 0))
    m = g.monsters[0]
    m.__dict__.update(state)
    p = _pet(g, m.x - 1, m.y, acts=True)
    assert p.take_turn(g.player, g.dungeon, g.monsters, g.pets, []) is None


def test_h1_04_nor_one_who_answered_a_horn():
    import horns
    g = _scene(('kappa', 3, 0))
    m = g.monsters[0]
    m._lp_calm = True
    fake = types.SimpleNamespace(alive=True, x=m.x - 1, y=m.y, _move_toward=lambda *a, **k: None)
    assert horns.CalledAlly.take_turn(fake, g.player, g.dungeon, g.monsters, [], []) is None


def test_h1_04_a_pet_does_not_undo_a_bribe():
    g = _scene(('orc_warrior', 3, 0))
    m = g.monsters[0]
    m._bribed = True
    m.status_effects['charmed'] = 20
    p = _pet(g, m.x - 1, m.y, acts=True)
    assert p.take_turn(g.player, g.dungeon, g.monsters, g.pets, []) is None


def test_h1_04_what_goes_off_by_itself_leaves_the_peace():
    g = _scene(('kappa', 1, 0))
    g.monsters[0]._lp_calm = True
    assert g._foes_beside_hero(threats_only=True) == []
    assert g._foes_beside_hero() == g.monsters         # an ordered special may break it


@pytest.mark.parametrize('kind,state', PEACE + [('myrmekes', {'_lp_busy': 3})])
@pytest.mark.parametrize('pin', ['stuck_in_pit', 'impaled', 'immobilized'])
def test_h1_12_peace_holds_for_a_pinned_creature(kind, state, pin):
    g = _scene((kind, 1, 0))
    m = g.monsters[0]
    m.speed = 10
    m.__dict__.update(state)
    m.status_effects[pin] = 5
    assert m.take_turn(g.player, g.dungeon, g.monsters) is False
    assert m.x == g.player.x + 1


def test_h1_12_peace_holds_at_bay():
    g = _scene(('kappa', 1, 0))
    m = g.monsters[0]
    m.speed = 10
    m._lp_calm = True
    m._at_bay = 3
    m.hp = m.max_hp
    assert m.take_turn(g.player, g.dungeon, g.monsters) is False


# ---------------------------------------------------------------------------
# h1-05, h1-17: a pack does not wait on what cannot act
# ---------------------------------------------------------------------------

def test_h1_05_goblins_charge_though_one_is_already_on_the_hero():
    g = _scene(('goblin', 1, 0), ('goblin', 3, 2), ('goblin', 3, -2), hp=90000)
    for _ in range(12):
        g._advance_turn()
        g.player.hp = 90000
    assert any(o.__dict__.get('_charged') for o in g.monsters)


@pytest.mark.parametrize('state', ['sleeping', 'paralyzed', 'immobilized'])
def test_h1_05_nor_on_one_that_cannot_throw(state):
    import packs
    g = _scene(('goblin', 3, 0), ('goblin', 3, 2), ('goblin', 3, -2))
    a, b, held = g.monsters
    a._stones = b._stones = 1
    held.status_effects[state] = 9
    packs._sling(a, g.player, g.dungeon, g.monsters, [b, held])
    assert a.__dict__.get('_charged')


def test_h1_05_they_still_gather_first():
    import packs
    g = _scene(('goblin', 3, 0), ('goblin', 3, 2), ('goblin', 3, -2))
    a, b, c = g.monsters
    a._stones = b._stones = 1
    packs._sling(a, g.player, g.dungeon, g.monsters, [b, c])
    assert not a.__dict__.get('_charged')


@pytest.mark.parametrize('where', [1, 2])
def test_h1_17_a_sleeping_packmate_does_not_hold_the_pack_for_ever(where):
    g = _scene(hp=9000)
    px, py = g.player.x, g.player.y
    for j in (-1, 1):
        for i in range(-6, 3):
            g.dungeon.tiles[py + j][px + i] = WALL
    g.dungeon.tiles[py][px - 1] = WALL
    plug = _mk('wolf', px + where, py)
    rest = [_mk('wolf', px + 3, py), _mk('wolf', px + 4, py + 1)]
    g.monsters = [plug] + rest
    for o in rest:
        o._tracking = True
        o._aware = True
    g._refresh_fov()
    longest = 0
    for _ in range(30):
        plug.status_effects['sleeping'] = 500
        g.player.hp = 9000
        g._advance_turn()
        if any(max(abs(o.x - px), abs(o.y - py)) <= 1 for o in rest):
            break                          # one pressed and fights him: the others may wait
        longest = max([longest] + [int(o.__dict__.get('_pack_wait', 0) or 0) for o in rest])
    assert longest <= 14


def test_h1_17_sleeping_jackals_do_not_fill_the_dart():
    import packs
    kind = next(k for k in MONS if isinstance(MONS[k], dict)
                and 'dart' in packs.tricks_of(_mk(k, 0, 0)))
    g = _scene((kind, 1, 0), (kind, -1, 0), (kind, 0, 2))
    a, b, third = g.monsters
    a.status_effects['sleeping'] = b.status_effects['sleeping'] = 20
    third._dart_phase = 0
    occ = packs._occupied(third, g.monsters, set(), g.player)
    assert packs._dart_in(third, g.player, g.dungeon, g.monsters, occ) != 'held'


# ---------------------------------------------------------------------------
# h1-06: a heal's line says what was healed
# ---------------------------------------------------------------------------

def _sick(hp=20, full=400):
    g = _scene(hp=full)
    g.player.hp = hp
    g.player.status_effects['diseased'] = 30
    return g


@pytest.mark.parametrize('effect', ['heal', 'extra_heal'])
def test_h1_06_a_healing_wand_says_what_it_gave(effect):
    g = _sick()
    g._apply_wand_effect(_wand_of(effect))
    assert any(f'{g.player.hp - 20} HP' in t for t in _msgs(g, 3))


def test_h1_06_a_healing_spell_says_what_it_gave():
    from spells import LEARNABLE_SPELLS
    g = _sick()
    sp = next(v for v in LEARNABLE_SPELLS.values() if v['effect'] == 'extra_heal')
    g._apply_spell_effect(sp)
    assert any(f'{g.player.hp - 20} HP' in t for t in _msgs(g, 3))


def test_h1_06_a_healing_scroll_says_what_it_gave():
    g = _sick()
    g._apply_scroll_effect(next(s for s in load_items('scroll') if s.effect == 'heal'))
    assert any(f'{g.player.hp - 20} HP' in t for t in _msgs(g, 3))


def test_h1_06_a_power_says_what_it_gave():
    g = _sick()
    g._activate_power('life_drain')
    assert any(f'{g.player.hp - 20} HP' in t for t in _msgs(g, 4))


def test_h1_06_a_drain_wand_keeps_its_draw_under_the_rot():
    # The exception is design (6a57464c, docs/systems: Grave Rot); halving it
    # is the author's ruling to make.
    g = _sick()
    g.monsters = [_mk('orc_warrior', g.player.x + 1, g.player.y)]
    m = g.monsters[0]
    m.max_hp = m.hp = 999
    g._wand_override_target = m
    g._apply_wand_effect(_wand('drain_life'))
    got, drained = g.player.hp - 20, 999 - m.hp
    assert got == min(drained, g.player.max_hp - 20)
    assert any(f'+{got} HP' in t for t in _msgs(g, 2))


def test_h1_06_a_life_transfer_says_what_it_gave():
    g = _sick()
    g.monsters = [_mk('orc_warrior', g.player.x + 1, g.player.y)]
    g.monsters[0].max_hp = g.monsters[0].hp = 200
    g._refresh_fov()
    g._apply_wand_effect(_wand_of('life_transfer'))
    assert any(f'+{g.player.hp - 20} HP' in t for t in _msgs(g, 2))


@pytest.mark.parametrize('kind', ['hp_restore', 'hp_restore_pct'])
def test_h1_06_a_reward_says_what_it_gave(kind):
    g = _sick()
    g._apply_npc_reward({'type': kind, 'amount': 40})
    assert any(f'+{g.player.hp - 20} HP' in t for t in _msgs(g, 3))


def test_h1_06_the_full_potion_is_not_whole_when_it_is_not():
    import food_system
    g = _sick()
    potion = next(p for p in load_items('potion') if p.effect == 'full_heal')
    potion.buc = 'uncursed'
    said = ' '.join(str(t) for t in food_system.drink_potion(g.player, potion))
    assert g.player.hp < g.player.max_hp
    assert 'completely whole' not in said and 'part of the way' in said


def test_h1_06_a_well_hero_is_told_he_is_whole():
    import food_system
    g = _scene(hp=400)
    g.player.hp = 20
    potion = next(p for p in load_items('potion') if p.effect == 'full_heal')
    potion.buc = 'uncursed'
    assert 'completely whole' in ' '.join(str(t) for t in food_system.drink_potion(g.player, potion))


def test_h1_06_the_fountain_cures_before_it_heals():
    g = _sick()
    g._resolve_fountain(4)
    assert not g.player.has_effect('diseased') and g.player.hp == g.player.max_hp


def test_h1_06_the_fountain_does_not_claim_what_it_did_not_do():
    g = _sick(hp=10)
    g._resolve_fountain(3)
    assert g.player.hp < g.player.max_hp
    assert not any('restores you fully' in t for t in _msgs(g, 3))


def test_h1_06_a_heros_special_says_what_it_gave():
    import hero_specials
    g = _sick()
    hero_specials._eff_self_heal(g, {}, {'dice': '4d8', 'cleanse': 0}, 3)
    assert any(f'{g.player.hp - 20} HP' in t for t in _msgs(g, 3))


def test_h1_06_a_heal_that_is_capped_says_what_it_gave():
    import hero_specials
    g = _scene(hp=400)
    g.player.hp = 397
    hero_specials._eff_aoe_heal_self(g, {}, {'self_heal': 30, 'cleanse': 0}, 3)
    assert any('+3 HP' in t for t in _msgs(g, 3))


def test_h1_06_a_salvaged_dish_says_what_it_gave():
    import kitchen
    g = _sick()
    with open(os.path.join(ROOT, 'data', 'items', 'recipes.json'), encoding='utf-8') as f:
        recs = json.load(f)
    for rid, rec in recs.items():
        if not isinstance(rec, dict):
            continue
        g.player.hp = 20
        said = ' '.join(kitchen.salvage_dish(g.player, rec))
        if g.player.hp > 20:
            assert f'+{g.player.hp - 20} HP' in said, rid
            return
    pytest.fail('no dish heals')


# ---------------------------------------------------------------------------
# h1-07: the dark
# ---------------------------------------------------------------------------

def _hidden_imp():
    import gone_again
    g = _scene(('imp', 5, 0))
    m = g.monsters[0]
    m._tracking = True
    m._hit_run_state, m._hit_run_timer = 'hiding', 6
    gone_again.dark_hide(m, g.player)
    g._sync_unseen()
    import unseen
    assert unseen.concealed(m, g.player)
    assert m._unseen is True
    return g, m


def test_h1_07_a_light_leaves_no_dark_at_once():
    import unseen
    g, m = _hidden_imp()
    g.player.status_effects['light'] = 40
    assert not unseen.concealed(m, g.player)
    g._refresh_fov()
    assert m._unseen is False


@pytest.mark.parametrize('how', ['_flee_timer', '_cowed', '_at_bay', 'feared', 'charmed'])
def test_h1_07_a_flight_ends_the_hiding(how):
    import unseen
    g, m = _hidden_imp()
    if how.startswith('_'):
        setattr(m, how, 4)
    else:
        m.status_effects[how] = 5
        if m.resists_control(how):
            pytest.skip('immune by nature')
    assert not unseen.concealed(m, g.player)


# ---------------------------------------------------------------------------
# h1-08, h1-09, h1-19: what breaks a thing drawn up
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('kind', ['lich_sovereign', 'ancient_lich', 'skeleton_mage', 'nosferatu'])
@pytest.mark.parametrize('why', ['feared', 'flee', 'cowed'])
def test_h1_08_a_frightened_lich_calls_nothing(kind, why, monkeypatch):
    g = _scene((kind, 3, 0), hp=90000)
    m = g.monsters[0]
    m.speed = 10
    m._tracking = True
    m._summon_turn_counter = 50
    if why == 'feared':
        m.status_effects['feared'] = 20
        monkeypatch.setattr(m, 'resists_control', lambda e: False)
    elif why == 'flee':
        m._flee_timer = 9
        import morale
        monkeypatch.setattr(morale, 'turn', lambda *a, **k: None)
    else:
        m._cowed = True
    for _ in range(3):
        m._tracking = True
        g._advance_turn()
        assert not m.__dict__.get('_chanting')
    assert len(g.monsters) == 1


def test_h1_08_a_calm_lich_still_calls():
    g = _scene(('skeleton_mage', 3, 0), hp=90000)
    m = g.monsters[0]
    m.speed = 10
    m._tracking = True
    m._summon_turn_counter = 50
    m.take_turn(g.player, g.dungeon, g.monsters)
    assert m.__dict__.get('_chanting')


def _chanter(kind='snake_charmer'):
    g = _scene((kind, 4, 0))
    m = g.monsters[0]
    m.speed = 10
    m._tracking = True
    m._chanting = True
    m._summon_turn_counter = 9
    return g, m


@pytest.mark.parametrize('why', ['sleeping', 'paralyzed', 'stunned', 'frozen', 'feared', 'charmed',
                                 'silenced'])
def test_h1_09_what_stops_a_turn_breaks_a_chant(why, monkeypatch):
    g, m = _chanter()
    monkeypatch.setattr(m, 'resists_control', lambda e: False)
    m.status_effects[why] = 5
    m.tick_effects()
    assert not m.__dict__.get('_chanting')


def test_h1_09_the_hero_is_told_the_chant_broke():
    import ai_lines
    g, m = _chanter()
    m.status_effects['sleeping'] = 5
    m.tick_effects()
    assert any('chant' in t for t, _u, _c in ai_lines.take(m))


def test_h1_09_a_call_needs_sight_when_it_completes():
    import summoning
    g, m = _chanter()
    for j in range(-5, 6):
        g.dungeon.tiles[g.player.y + j][g.player.x + 2] = WALL
    assert summoning.step(m, g.player, g.monsters, g.dungeon) == ''
    assert not m._wants_summon


def test_h1_09_a_caller_that_lost_him_lets_the_chant_go():
    g, m = _chanter('skeleton_mage')
    m._tracking = False
    m.take_turn(g.player, g.dungeon, g.monsters)
    assert not m.__dict__.get('_chanting')


def test_h1_09_a_stumble_breaks_a_chant(monkeypatch):
    g, m = _chanter()
    m.status_effects['confused'] = 5
    monkeypatch.setattr(m, 'resists_control', lambda e: False)
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    m.take_turn(g.player, g.dungeon, g.monsters)
    assert not m.__dict__.get('_chanting')


def test_h1_09_a_pinned_summoner_finishes_what_it_began():
    """Pinned it can still speak (caster_ai): the call comes the next turn,
    never when the pin ends with no new tell."""
    g, m = _chanter()
    m.status_effects['immobilized'] = 5
    assert m.take_turn(g.player, g.dungeon, g.monsters) is False
    assert not m.__dict__.get('_chanting') and m._wants_summon


def test_h1_09_sleep_breaks_a_gaze_drawn_up():
    g = _scene(('floating_eye', 3, 0))
    m = g.monsters[0]
    m._winding = True
    m.status_effects['sleeping'] = 4
    m.tick_effects()
    assert not m._winding


def test_h1_09_a_wind_up_is_let_go_out_of_sight():
    g = _scene(('floating_eye', 3, 0))
    m = g.monsters[0]
    m._winding = True
    for j in range(-5, 6):
        g.dungeon.tiles[g.player.y + j][g.player.x + 1] = WALL
    assert m._opener_from_range(g.player, g.dungeon) is None
    assert not m._winding


def _casting(kind='orc_shaman'):
    g = _scene((kind, 3, 0))
    m = g.monsters[0]
    m._tracking = True
    m._casting = MONS[kind]['spells'][0]['id']
    return g, m


@pytest.mark.parametrize('how', ['_flee_timer', '_cowed', '_yielded', '_holding'])
def test_h1_19_flight_breaks_a_spell_drawn_up(how):
    g, m = _casting()
    setattr(m, how, 4)
    m.tick_effects()
    assert not m.__dict__.get('_casting')


def test_h1_19_the_turn_it_breaks_the_spell_is_lost(monkeypatch):
    import morale
    g, m = _casting()
    m.speed = 10

    def breaks_now(mon, *a, **k):
        mon._flee_timer = 6
    monkeypatch.setattr(morale, 'turn', breaks_now)
    m.take_turn(g.player, g.dungeon, g.monsters)
    assert not m.__dict__.get('_casting')


def test_h1_19_a_broken_caster_draws_nothing_up():
    import ai_turn
    import caster_ai
    g = _scene(('orc_shaman', 3, 0))
    m = g.monsters[0]
    m._cowed = True
    real = caster_ai.turn
    caster_ai.turn = lambda *a, **k: pytest.fail('it opened its book')
    try:
        ai_turn.turn(m, g.player, g.dungeon, g.monsters)
    finally:
        caster_ai.turn = real


# ---------------------------------------------------------------------------
# h1-10: the view goes with him
# ---------------------------------------------------------------------------

def test_h1_10_a_dragged_hero_sees_from_where_he_is():
    g = _scene(('sobek_warrior', 1, 0), hp=3000)
    for j in range(-6, 7):
        g.dungeon.tiles[g.player.y + j][g.player.x + 6] = WATER
    g._refresh_fov()
    _hold(g, g.monsters[0])
    g.monsters[0].speed = 10
    x0 = g.player.x
    g._advance_turn()
    assert g.player.x != x0
    seen = set(g.visible)
    g._refresh_fov()
    assert seen == set(g.visible)


def test_h1_10_a_pulled_hero_sees_from_where_he_is():
    g = _scene()
    g.player._pending_pull_toward = (g.player.x + 5, g.player.y)
    x0 = g.player.x
    g._advance_turn()
    assert g.player.x == x0 + 1
    seen = set(g.visible)
    g._refresh_fov()
    assert seen == set(g.visible)


def test_h1_10_the_monsters_turn_starts_from_where_he_is():
    g = _scene()
    g.player._pending_pull_toward = (g.player.x + 5, g.player.y)
    seen_in_turn = []
    g._do_monster_turns = lambda: seen_in_turn.append(set(g.visible))
    g._advance_turn()
    g._refresh_fov()
    assert seen_in_turn == [set(g.visible)]


# ---------------------------------------------------------------------------
# h1-11: one death
# ---------------------------------------------------------------------------

def _count_ends(g):
    calls = []
    real = g._on_game_over
    g._on_game_over = lambda *x, **k: (calls.append(1), real(*x, **k))
    return calls


def test_h1_11_no_one_acts_after_a_burst_has_killed_the_hero():
    g = _scene(('orc_warrior', 2, 0), ('orc_warrior', -1, 0), ('fire_beetle', 1, 0), seed=14, hp=60)
    a, b, e = g.monsters
    e.hp = 1
    g.player.hp = 1

    def confused_turn(*_a, **_k):
        e.hp, e.alive = 0, False
        a._confused_hit = (e, 5)
        return False
    acted = []
    a.take_turn = confused_turn
    b.take_turn = lambda *_a, **_k: (acted.append(1), True)[1]
    ends = _count_ends(g)
    g._advance_turn()
    assert g.state == STATE_DEAD
    assert len(ends) == 1 and not acted
    assert g._killed_by == 'fire_beetle'


def test_h1_11_nor_the_one_whose_own_turn_set_it_off():
    g = _scene(('orc_warrior', 1, 1), ('fire_beetle', 1, 0), hp=60)
    a, e = g.monsters
    g.player.hp = 1

    def turn(*_a, **_k):
        e.hp, e.alive = 0, False
        a._confused_hit = (e, 5)
        return True
    a.take_turn = turn
    a.attack = lambda p: pytest.fail('it struck a dead hero')
    g._advance_turn()
    assert g.state == STATE_DEAD


def test_h1_11_no_ward_answers_for_a_run_that_is_over():
    g = _scene()
    g.player.hp = 0
    g.player.status_effects['life_save'] = -1
    g.player._combat_game_ref = g
    g._run_over = True
    g._answer_a_killing_blow()
    assert g.player.hp == 0 and g.player.has_effect('life_save')
    assert g.player.is_dead()


def test_h1_11_a_run_ends_once(monkeypatch):
    import bones
    g = _scene()
    saved = []
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: saved.append(1))
    g.defeat_reason = 'died'
    g._on_game_over()
    g._on_game_over()
    assert saved == [1]


def test_h1_11_the_pets_and_the_rest_stop_too():
    g = _scene(('orc_warrior', 5, 0))
    g.monsters[0].take_turn = lambda *a, **k: False
    p = _pet(g, g.player.x - 1, g.player.y)
    q_acted = []

    def deadly(*a, **k):
        g.player.hp = 0
        g.defeat_reason = 'died'
        g._on_game_over()
        g.state = STATE_DEAD
    p.take_turn = deadly
    import pet_system
    q = pet_system.Pet(p.species_key, g.player.x, g.player.y - 1)
    q.take_turn = lambda *a, **k: q_acted.append(1)
    g.pets.append(q)
    g._advance_turn()
    assert not q_acted and g.player.hp == 0 and g.state == STATE_DEAD


# ---------------------------------------------------------------------------
# h1-13: a pinned holder only squeezes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('pin', ['stuck_in_pit', 'impaled', 'immobilized'])
def test_h1_13_a_pinned_holder_only_squeezes(pin):
    g = _scene(('naga_guardian', 1, 0), hp=9000)
    m = g.monsters[0]
    _hold(g, m)
    m.status_effects[pin] = 5
    assert m.take_turn(g.player, g.dungeon, g.monsters)
    assert m.__dict__.get('_squeeze_now')


def test_h1_13_a_pinned_dragger_drags_no_one():
    g = _scene(('sobek_warrior', 1, 0), hp=3000)
    for j in range(-6, 7):
        g.dungeon.tiles[g.player.y + j][g.player.x + 6] = WATER
    m = g.monsters[0]
    _hold(g, m)
    m.status_effects['immobilized'] = 5
    at = (g.player.x, g.player.y, m.x, m.y)
    assert m.take_turn(g.player, g.dungeon, g.monsters)
    assert m.__dict__.get('_squeeze_now')
    assert at == (g.player.x, g.player.y, m.x, m.y)


# ---------------------------------------------------------------------------
# h1-15, h1-16: the light
# ---------------------------------------------------------------------------

def test_h1_15_the_relurk_advice_is_true():
    import relurk
    with open(os.path.join(ROOT, 'data', 'ui', 'monster_ways.json'), encoding='utf-8') as f:
        ways = json.load(f)
    row = next(r for s in ways['sections'] for r in (s.get('rows') or ())
               if r[0] == 'Back to the web')
    with open(os.path.join(ROOT, 'data', 'tells.json'), encoding='utf-8') as f:
        text = f.read()
    counter = text.split('"relurks": {', 1)[1].split('"counter":', 1)[1].split('\n', 1)[0]
    for said in (row[1], counter, ' '.join(relurk.__doc__.split())):
        assert 'bring a light' not in said and 'carry a light' not in said
        assert 'A light, ' not in said
        assert "Hecate's Torch" in said and 'Tremor-Sense' in said


def test_h1_16_light_does_not_reach_a_troll_through_a_wall():
    g = _scene(('troll', 3, 0))
    for j in range(-6, 7):
        g.dungeon.tiles[g.player.y + j][g.player.x + 1] = WALL
    g.player.status_effects['light'] = 40
    g._refresh_fov()
    m = g.monsters[0]
    m.hp = m.max_hp // 2
    g._ai_turn_after(m)
    assert not m.__dict__.get('_regen_blocked')


def test_h1_16_it_does_in_the_open():
    g = _scene(('troll', 2, 0))
    g.player.status_effects['light'] = 40
    g._refresh_fov()
    m = g.monsters[0]
    m.hp = m.max_hp // 2
    g._ai_turn_after(m)
    assert m.__dict__.get('_regen_blocked')


# ---------------------------------------------------------------------------
# h1-18: no voice
# ---------------------------------------------------------------------------

def test_h1_18_a_silenced_hound_cannot_bay():
    import packs
    g = _scene(('gravehound', 3, 0), ('gravehound', 6, 3))
    g.monsters[0].status_effects['silenced'] = 5
    assert packs.alarm(g.monsters[0], g.monsters, g.player.x, g.player.y, g.dungeon) == 0


def test_h1_18_a_silenced_band_member_cannot_call():
    import war_bands
    g = _scene(('orc_warrior', 3, 0), ('orc_warrior', 5, 2))
    a, b = g.monsters
    a._band = b._band = 'x1'
    a.status_effects['silenced'] = 5
    assert war_bands.alarm(a, g.monsters, g.player.x, g.player.y) == 0


def test_h1_18_a_silenced_creature_calls_no_help():
    g = _scene(('orc_warrior', 1, 0), ('orc_warrior', 4, 0))
    a, b = g.monsters
    b._alerted = False
    a.status_effects['silenced'] = 5
    a.alert_nearby(g.monsters)
    assert not b._alerted


# ---------------------------------------------------------------------------
# h1-23, h1-24
# ---------------------------------------------------------------------------

def test_h1_23_a_call_with_no_room_costs_only_the_beat():
    g = _scene(('snake_charmer', 4, 0))
    m = g.monsters[0]
    for i in range(-3, 4):
        for j in range(-3, 4):
            if i or j:
                g.dungeon.tiles[m.y + j][m.x + i] = WALL
    m._summons_made = 1                        # the count step() took for this call
    m._summon_turn_counter = 0
    g._spawn_summoner_minion(m)
    assert len(g.monsters) == 1
    assert m._summons_made == 0 and m._summon_turn_counter == 0


def test_h1_24_an_aura_death_blames_what_killed():
    fear = next(k for k, v in MONS.items() if isinstance(v, dict)
                and (v.get('aura') or {}).get('kind') == 'fear')
    g = _scene((fear, 0, 1), ('fire_elemental', 1, 0))
    dread, fire = g.monsters
    dread._aura_rolled = True
    g.player.hp = 1
    assert g._ways_world_turn()
    assert g.state == STATE_DEAD and g._killed_by == 'fire_elemental'
