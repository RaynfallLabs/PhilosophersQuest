"""Bug bash 3.6.0, hunter 2: magic, the carried lights, items and old saves.

One section for each finding (h2-01 to h2-19); h2-15 and h2-20 are rulings.
The lights' findings are one rule (what the off hand holds and what the light
swap remembers), and a random-sequence test holds the whole of it.

Headless: whether it feels right at the keys is Brandon's play-test.
"""
import json
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import items  # noqa: E402
import known_by_hand  # noqa: E402
import lights  # noqa: E402
import loadouts  # noqa: E402
import wards  # noqa: E402
from game_states import STATE_KIT, STATE_PLAYER, STATE_TARGET  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402
from spells import LEARNABLE_SPELLS  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    KINDS = json.load(_f)


# --------------------------------------------------------------- helpers

@pytest.fixture
def g(monkeypatch):
    import main
    monkeypatch.setenv('PQ_NO_BONES', '1')
    random.seed(11)
    items.bind_unique_registry(set())
    game = main.Game(pygame.display.set_mode((1280, 720)), player_name='__bugbash_360_h2__')
    _ready(game)
    return game


def _ready(game):
    from dungeon import FLOOR
    game.monsters[:] = []
    game.pets = []
    game.ground_items[:] = []
    game._maybe_wander_spawn = lambda: None
    game._popup_queue_list().clear()
    game.state = STATE_PLAYER
    d, p = game.dungeon, game.player
    x = min(max(p.x, 9), d.width - 10)
    y = min(max(p.y, 9), d.height - 10)
    for i in range(-8, 9):
        for j in range(-8, 9):
            at = (x + i, y + j)
            d.tiles[at[1]][at[0]] = FLOOR
            d.traps.pop(at, None)
            (d.__dict__.get('fixtures') or {}).pop(at, None)
    d.__dict__.setdefault('fixture_blocks', set()).clear()
    p.x, p.y = x, y
    p.weapon = p.ranged_weapon = p.shield = None
    p.readied_weapon = None
    p.inventory = []
    p.status_effects.clear()
    p.STR = 40
    p.max_hp = p.hp = 5000
    p.max_mp = p.mp = 60
    game._refresh_fov()
    _listen(game)


def _listen(game):
    game.said = []
    add = game.add_message

    def hear(text, *a, **k):
        game.said.append(str(text))
        return add(text, *a, **k)
    game.add_message = hear


def _press(game, char):
    game.state = STATE_PLAYER
    game.handle_event(types.SimpleNamespace(
        type=pygame.KEYDOWN, key=getattr(pygame, f'K_{char.lower()}'), unicode=char,
        mod=pygame.KMOD_SHIFT if char.isupper() else 0, scancode=0))


def _mon(game, kind, dx, dy=0):
    m = Monster({**KINDS[kind], 'id': kind}, game.player.x + dx, game.player.y + dy)
    m._aware = True
    game.monsters.append(m)
    game.player._combat_game_ref = game
    game._refresh_fov()
    return m


def _light(p, lid='torch', n=1, fuel=None):
    it = items.make_item_by_id('light', lid)
    it.count = n
    if fuel is not None:
        it.fuel = fuel
    p.inventory.append(it)
    return it


def _shield(p, template='buckler', worn=False):
    sh = items.instantiate_shield(template, 'steel')
    sh.buc, sh.cursed = 'uncursed', False
    known_by_hand.learn(p, sh)
    if worn:
        p._apply_equip(sh)
    else:
        p.inventory.append(sh)
    return sh


def _weapon(p, template, where='pack'):
    w = items.instantiate_weapon(template, 'iron')
    w.buc, w.cursed = 'uncursed', False
    if where == 'hand':
        p.weapon = w
    else:
        p.inventory.append(w)
        if where == 'back':
            p.readied_weapon = w
    return w


def _owned(game, iid):
    p = game.player
    things = list(p.inventory) + ([p.shield] if p.shield is not None else [])
    return sum(int(getattr(i, 'count', 1) or 1) for i in things if i.id == iid)


def _fresh_doused_torch_in_hand(game):
    """The torch that lit itself as the last one guttered, put out at once."""
    _light(game.player, fuel=2)
    _press(game, 'L')
    _light(game.player)
    game._advance_turn()
    _press(game, 'O')
    assert lights.is_fresh(game.player.shield)
    return game.player.shield


def _found(p, n):
    more = items.make_item_by_id('light', 'torch')
    more.count = n
    assert p.add_to_inventory(more)


def _cast(game, sid, target=None):
    game.said.clear()
    game._mm_acting(game._cast_spell_effect, LEARNABLE_SPELLS[sid], target)
    return ' '.join(game.said)


def _read(game, sid):
    sc = items.make_item_by_id('scroll', sid)
    sc.buc = 'uncursed'
    game.said.clear()
    game._mm_acting(game._apply_scroll_effect, sc)
    return ' '.join(game.said)


def _zap(game, wid, target=None):
    wand = items.make_item_by_id('wand', wid)
    game.said.clear()
    game._wand_override_target = target
    game._mm_acting(game._apply_wand_effect, wand)
    game._wand_override_target = None
    return ' '.join(game.said)


# ------------------------------------------------- h2-01: one off a stack

def test_a_slung_torch_that_took_in_a_bundle_goes_back_as_one_torch(g):
    p = g.player
    _weapon(p, 'longsword', 'hand')
    _weapon(p, 'greatsword', 'back')
    held = _fresh_doused_torch_in_hand(g)
    _press(g, 's')
    assert p.shield is None
    _found(p, 3)
    assert _owned(g, 'torch') == 4
    _press(g, 's')
    assert p.shield is held and held.count == 1
    assert not any(i is held for i in p.inventory)
    assert _owned(g, 'torch') == 4
    assert not any('Torch x' in s for s in g.said if 'take up your' in s)
    _press(g, 'L')
    assert _owned(g, 'torch') == 4


def test_a_kits_torch_that_took_in_a_bundle_goes_on_as_one_torch(g):
    p = g.player
    held = _fresh_doused_torch_in_hand(g)
    g._kit_save(0)
    _press(g, 'L')
    if not lights.is_fresh(held):         # stowed the turn it lit: still the kit's
        held.fuel = held.burn
    _found(p, 3)
    g._kit_wear(0)
    assert p.shield is held and held.count == 1
    assert not any(i is held for i in p.inventory) and _owned(g, 'torch') == 4
    assert g._kit_plan(0)['already']


def test_one_of_a_stack_burning_out_leaves_the_rest(g):
    p = g.player
    _weapon(p, 'longsword', 'hand')
    _weapon(p, 'greatsword', 'back')
    _fresh_doused_torch_in_hand(g)
    _press(g, 's')
    _found(p, 3)
    _press(g, 's')
    p.shield.fuel = 1
    g._advance_turn()
    assert lights.is_lit(p.shield) and _owned(g, 'torch') == 3


def test_no_road_into_the_hand_takes_a_whole_stack():
    p = Player()
    p.weapon = p.shield = None
    p.inventory = []
    bundle = _light(p, n=3)
    p._apply_equip(bundle)
    assert p.shield is bundle and bundle.count == 1
    assert p.remove_from_inventory(bundle)
    assert [i.count for i in p.inventory] == [2]
    assert not any(i is bundle for i in p.inventory)


def test_a_kits_torch_is_remembered_when_its_row_joins_another():
    p = Player()
    p.weapon = p.shield = None
    p.inventory = []
    row = _light(p, n=2)
    back = items.make_item_by_id('light', 'torch')
    p.loadouts[0]['pieces'] = {'shield': back}
    assert p.add_to_inventory(back)
    assert row.count == 3 and p.loadouts[0]['pieces']['shield'] is row
    other = _light(p)
    p.loadouts[1]['pieces'] = {'shield': other}
    p._shield_slung = other
    assert p.merge_known_stacks() == 1
    only, = p.inventory
    assert p.loadouts[1]['pieces']['shield'] is only and p._shield_slung is only


def test_take_and_equip_takes_up_a_torch_that_joined_a_bundle(g):
    p = g.player
    _light(p, n=2)
    lying = items.make_item_by_id('light', 'torch')
    lying.x, lying.y = p.x, p.y
    g.ground_items.append(lying)
    g.state = STATE_KIT
    g._item_action_run('equip', lying, g._kit_return_ctx())
    assert lights.is_lit(p.shield) and _owned(g, 'torch') == 3


def test_a_two_hander_refused_by_a_shield_is_never_held_and_packed():
    p = Player()
    p.inventory = []
    hand = _weapon(p, 'longsword', 'hand')
    sh = _shield(p, worn=True)
    sh.buc, sh.cursed = 'cursed', True
    big = _weapon(p, 'greatsword')
    p._apply_equip(big)
    assert p.weapon is hand and p.shield is sh
    assert not any(i is hand for i in p.inventory)


# --------------------------------------- h2-02: what the light replaced

def test_shift_l_gives_back_the_shield_the_light_replaced(g):
    p = g.player
    _shield(p, 'buckler', worn=True)
    _light(p, n=2)
    _press(g, 'L')
    kite = _shield(p, 'kite_shield')
    g._dress_begin_on(kite)
    assert p.shield is kite
    g._equip_item(next(i for i in p.inventory if lights.is_light(i)))
    assert lights.held(p) is not None
    _press(g, 'L')
    assert p.shield is kite


def test_a_shield_over_the_light_forgets_the_two_hander(g):
    p = g.player
    _weapon(p, 'greatsword', 'hand')
    side = _weapon(p, 'longsword', 'back')
    sh = _shield(p)
    _light(p, n=2)
    _press(g, 'L')
    g._dress_begin_on(sh)
    g._equip_item(next(i for i in p.inventory if lights.is_light(i)))
    _press(g, 'L')
    assert p.weapon is side and p.shield is sh


def test_a_light_taken_up_from_the_kit_gives_the_shield_back(g):
    p = g.player
    sh = _shield(p, worn=True)
    g._equip_item(_light(p))
    assert lights.held(p) is not None
    _press(g, 'L')
    assert p.shield is sh


def test_a_kits_light_gives_the_shield_back(g):
    p = g.player
    torch = _light(p)
    g._equip_item(torch)
    g._kit_save(0)
    sh = _shield(p)
    g._dress_begin_on(sh)
    g._kit_wear(0)
    assert p.shield is torch
    _press(g, 'L')
    assert p.shield is sh


# ------------------------------------------------- h2-03: the readied kind

def test_readying_a_lantern_while_a_torch_is_held_holds(g):
    p = g.player
    _light(p, n=2)
    _press(g, 'L')
    lan = _light(p, 'horn_lantern')
    g._ready_light(lan)
    _press(g, 'L')
    assert g._readied_mark(lan)
    _press(g, 'L')
    assert p.shield is lan


def test_with_none_readied_the_last_put_away_comes_out_first(g):
    p = g.player
    torch = _light(p)
    _press(g, 'L')
    lan = _light(p, 'horn_lantern')
    _press(g, 'L')
    assert lights.pick(p) is torch and not g._readied_mark(torch)
    g._unready_light(torch)
    assert lights.pick(p) is lan


# -------------------------------------------- h2-19: the last torch is out

def test_the_last_torch_gone_gives_the_two_hander_back(g):
    p = g.player
    big = _weapon(p, 'greatsword', 'hand')
    side = _weapon(p, 'longsword', 'back')
    _light(p, fuel=2)
    _press(g, 'L')
    g._advance_turn()
    assert p.shield is None and p.weapon is side
    t0 = g.turn_count
    _press(g, 'L')
    assert p.weapon is big and p.readied_weapon is side and g.turn_count == t0 + 1


def test_another_light_after_the_last_torch_still_owes_the_two_hander(g):
    p = g.player
    big = _weapon(p, 'greatsword', 'hand')
    _weapon(p, 'longsword', 'back')
    _light(p, fuel=2)
    _press(g, 'L')
    g._advance_turn()
    _light(p, 'horn_lantern')
    _press(g, 'L')
    assert lights.held(p) is not None
    _press(g, 'L')
    assert p.weapon is big


def test_a_two_hander_taken_up_again_takes_over_the_shield_set_aside(g):
    p = g.player
    _weapon(p, 'longsword', 'hand')
    big = _weapon(p, 'greatsword', 'back')
    sh = _shield(p, worn=True)
    _light(p, fuel=2)
    _press(g, 'L')
    g._advance_turn()
    _press(g, 's')
    assert p.weapon is big and p.shield is None
    _press(g, 's')
    assert p.shield is sh


# --------------------------------------- the off hand, any sequence at all

def _everything(game):
    p = game.player
    return list(p.inventory) + [w for w in p.worn_items() if w is not None] + list(game.ground_items)


def _tally(game):
    out = {}
    for it in _everything(game):
        out[it.id] = out.get(it.id, 0) + int(getattr(it, 'count', 1) or 1)
    return out


def _in_pack(p, iid):
    return iid is not None and any(i.id == iid for i in p.inventory)


def _iid(it):
    return getattr(it, 'id', None)


class _Owed:
    """What the hero is owed, worked out from what is seen to move alone:
    ``shield``, set aside for a light; ``big``, the two-hander Shift+L
    changed; ``slung``, what a two-hander sent to the pack."""

    def __init__(self):
        self.shield = self.big = self.slung = None

    def saw(self, p, op, hand0, off0):
        hand, off = p.weapon, p.shield
        if _iid(off0) == _iid(off) and _iid(hand0) == _iid(hand):
            return
        stowed = op == 'L' and lights.is_light(off0)
        gave_back = op == 'L' and not lights.is_light(off)
        two = bool(hand is not None and getattr(hand, 'two_handed', False))
        took_two = two and _iid(hand0) != _iid(hand)
        if stowed or gave_back:
            waiting = self.shield if took_two and _in_pack(p, self.shield) else None
            self.shield = self.big = None
            self.slung = waiting
            return
        if off is not None and _iid(off0) != _iid(off):
            if not lights.is_light(off):
                self.shield = self.big = None
            elif off0 is not None and not lights.is_light(off0):
                self.shield, self.big = off0.id, None
            elif off0 is None:
                if self.slung and _in_pack(p, self.slung) and self.slung not in LIGHT_IDS:
                    self.shield, self.big = self.slung, None
                if op == 'L' and hand0 is not None and getattr(hand0, 'two_handed', False):
                    self.big = hand0.id
            self.slung = None
        elif took_two:
            if off0 is not None and off is None:
                self.slung = off0.id
                if not lights.is_light(off0):
                    self.shield = self.big = None
            elif not (self.slung in LIGHT_IDS and _in_pack(p, self.slung)):
                if not _in_pack(p, self.slung):
                    self.slung = self.shield if _in_pack(p, self.shield) else None
                self.shield = self.big = None


with open(os.path.join(ROOT, 'data', 'items', 'light.json'), encoding='utf-8') as _f:
    LIGHT_IDS = {k for k, v in json.load(_f).items() if isinstance(v, dict)}


@pytest.mark.parametrize('seed', range(24))
def test_any_sequence_conserves_items_and_gives_back_what_the_light_replaced(g, monkeypatch, seed):
    import main
    import save_system
    rng = random.Random(seed)
    random.seed(seed)
    p = g.player
    _weapon(p, 'longsword', 'hand')
    _weapon(p, 'greatsword', 'back')
    _weapon(p, 'dagger')
    _shield(p, 'buckler', worn=True)
    _shield(p, 'kite_shield')
    _light(p, 'torch', 3)
    lan = _light(p, 'horn_lantern', fuel=rng.choice((0, 1, 5, 900)))
    _light(p, 'jacks_lantern')
    oil = items.make_item_by_id('flask', 'flask_of_fire_oil')
    oil.count = 2
    p.inventory.append(oil)
    assert lan in p.inventory
    used = {'torch': 0, 'flask_of_fire_oil': 0}
    real_burn, real_fill = lights.burn_turn, lights.fill

    def burn(light, *a, **k):
        what = real_burn(light, *a, **k)
        if what == 'out' and lights.fuel_kind(light) == 'self':
            used['torch'] += 1
        return what

    def fill(light):
        used['flask_of_fire_oil'] += 1
        return real_fill(light)
    monkeypatch.setattr(lights, 'burn_turn', burn)
    monkeypatch.setattr(lights, 'fill', fill)
    owed = _Owed()
    count = _tally(g)
    for step in range(100):
        p = g.player
        p.hp, p.sp = p.max_hp, p.max_sp
        g._popup_queue_list().clear()
        g.monsters[:] = []
        g.state = STATE_PLAYER
        g._busy = None
        op = rng.choice(('L', 'L', 'L', 'L', 's', 's', 'O', 'O', 'wait', 'E', 'E', 'kit', 'off',
                         'kit save', 'kit wear', 'find', 'burn', 'drop', 'take', 'take and equip',
                         'ready', 'unready', 'save'))
        if op == 'save' and rng.random() > 0.3:
            op = 'wait'
        hand0, off0 = p.weapon, p.shield
        carried = [i for i in p.inventory if lights.is_light(i)]
        gear = [i for i in p.inventory
                if lights.is_light(i) or isinstance(i, (items.Weapon, items.Shield))]
        here = [i for i in g.ground_items if (i.x, i.y) == (p.x, p.y)]
        gives_back = None
        if op == 'L' and (lights.held(p) is not None
                          or (off0 is None and lights.pick(p) is None)):
            hand_free = hand0 is None or not getattr(hand0, 'two_handed', False)
            back = p.readied_weapon
            if hand_free and owed.big and _iid(back) == owed.big:
                gives_back = ('hand', owed.big)
            elif hand_free and _in_pack(p, owed.shield):
                gives_back = ('arm', owed.shield)
            else:
                gives_back = ('none', None)
        s_returns = None
        if op == 's':
            back = p.readied_weapon
            if (back is not None and not back.two_handed and off0 is None
                    and _in_pack(p, owed.slung)):
                s_returns = owed.slung
        t0 = g.turn_count
        if op in ('L', 'O', 's'):
            _press(g, op)
        elif op == 'wait':
            g._advance_turn()
        elif op == 'E' and gear:
            g._equip_item(rng.choice(gear))
        elif op == 'kit' and gear:
            g.state = STATE_KIT
            g._item_action_run('equip', rng.choice(gear), g._kit_return_ctx())
        elif op == 'off' and p.shield is not None:
            g._dress_start_off('shield', p.shield)
        elif op == 'kit save':
            g._kit_save(rng.randrange(3))
        elif op == 'kit wear':
            g._kit_wear(rng.randrange(3))
        elif op == 'find':
            f = items.make_item_by_id('light', 'torch')
            f.count = rng.randint(1, 3)
            if p.add_to_inventory(f):
                count['torch'] = count.get('torch', 0) + f.count
        elif op == 'burn' and lights.held(p) is not None and not lights.everlasting(p.shield):
            p.shield.fuel = 1
        elif op == 'drop':
            can = [i for i in gear + [i for i in p.inventory if i.id == 'flask_of_fire_oil']
                   if i.id != owed.slung]
            if can:
                it = rng.choice(can)
                g._finish_drop(it, rng.randint(1, int(getattr(it, 'count', 1) or 1)))
        elif op == 'take' and here:
            g._pickup(target=rng.choice(here))
        elif op == 'take and equip' and here:
            g.state = STATE_KIT
            it = rng.choice(here)
            if any(a['id'] == 'equip' for a in g._item_actions(it, 'floor')):
                g._item_action_run('equip', it, g._kit_return_ctx())
        elif op == 'ready' and carried:
            g._ready_light(rng.choice(carried))
        elif op == 'unready' and carried:
            g._unready_light(rng.choice(carried))
        elif op == 'save':
            assert save_system.save_game(g) is not False
            g2, err = main._restore_saved_game(g.screen, g.player_name,
                                               save_system.load_game(g.player_name))
            assert g2 is not None, err
            g2._maybe_wander_spawn = lambda: None
            g2.pets = []
            g = g2
            p = g.player
            hand0, off0 = p.weapon, p.shield
        where = f'seed {seed} step {step}: {op}'
        after = _everything(g)
        assert len({id(i) for i in after}) == len(after), f'one object twice, {where}'
        burnt = bool(used['torch'])
        want = dict(count)
        for iid, n in used.items():
            if n:
                want[iid] = want.get(iid, 0) - n
                if not want[iid]:
                    del want[iid]
                used[iid] = 0
        count = _tally(g)
        assert count == want, where
        assert p.shield is None or int(getattr(p.shield, 'count', 1) or 1) == 1, where
        assert p.shield is None or p.can_equip_shield(), where
        assert not any(getattr(i, 'lit', False) for i in p.inventory if lights.is_light(i)), where
        if (_iid(hand0), _iid(off0)) != (_iid(p.weapon), _iid(p.shield)) and op != 'burn':
            assert g.turn_count > t0, f'a change in no time, {where}'
        if gives_back:
            slot, iid = gives_back
            if slot == 'hand':
                assert _iid(p.weapon) == iid and p.shield is None, where
            elif slot == 'arm':
                assert _iid(p.shield) == iid, where
            else:
                assert p.shield is None and _iid(p.weapon) == _iid(hand0), where
        if s_returns and p.weapon is not None and not p.weapon.two_handed:
            assert _iid(p.shield) == s_returns, where
        owed.saw(p, op, hand0, off0)
        if burnt and p.shield is None and owed.slung in LIGHT_IDS:
            owed.slung = None             # the slung torch itself burnt out


# ----------------------------------------- h2-04: off the tile, out of it

def _pit(game):
    p = game.player
    game.dungeon.pits = set(getattr(game.dungeon, 'pits', None) or ())
    game.dungeon.pits.add((p.x, p.y))
    p.add_effect('in_pit', -1)


def test_shrink_the_earth_out_of_a_pit_leaves_it(g):
    p = g.player
    _pit(g)
    g._aimed_tile = (p.x + 3, p.y)
    _cast(g, 'shrink_the_earth_spell')
    assert not p.has_effect('in_pit')
    m = _mon(g, 'young_red_dragon', 3)
    m.thac0 = -40
    breath = next(a for a in m.attacks if 'breath' in a['name'].lower())
    assert 'pit' not in m._resolve_blow(dict(breath), p)[1]


def test_every_teleport_leaves_the_pit(g):
    p = g.player
    _pit(g)
    g._teleport_player()
    assert not p.has_effect('in_pit'), 'teleport'

    _pit(g)
    import hero_specials
    hero_specials._eff_teleport_self(g, {}, {'range': 4}, 5)
    assert not p.has_effect('in_pit'), "Hermes' step"

    for sid in ('scroll_of_blink', 'scroll_of_teleportation', 'scroll_of_recall'):
        _pit(g)
        _read(g, sid)
        assert not p.has_effect('in_pit'), sid


def test_the_seven_league_step_leaves_the_pit(g):
    p = g.player
    _pit(g)
    p._facing_dx, p._facing_dy = 1, 0
    p._seven_league_used_this_floor = False
    x = p.x
    g._activate_seven_league_step()
    assert p.x > x and not p.has_effect('in_pit')


def test_the_roc_sets_him_down_out_of_the_pit(g):
    p = g.player
    _pit(g)
    g._lore_powers_landing = lambda lo, hi: (p.x + 5, p.y)
    p.__dict__['_lp_carry_off'] = (8, 15)
    g._lore_powers_lift(_mon(g, 'roc_adult', -1))
    assert not p.has_effect('in_pit') and p.has_effect('immobilized')


def test_a_pull_a_shove_and_a_drag_leave_the_pit(g):
    p = g.player
    _pit(g)
    x = p.x
    p._pending_pull_toward = (x + 4, p.y)
    g._advance_turn()
    assert p.x == x + 1 and not p.has_effect('in_pit'), 'pull'

    _pit(g)
    p._pending_shove = {'from': (p.x - 1, p.y), 'aim': False, 'line': 'thrown', 'aimed': 'thrown'}
    g._ai_resolve_shove()
    assert not p.has_effect('in_pit'), 'shove'

    import holds
    m = _mon(g, 'kobold', 1)
    p.add_effect('in_pit', -1)
    d = g.dungeon
    from dungeon import WATER
    d.tiles[p.y][m.x + 4] = WATER
    assert holds._drag_step(m, p, d, g.monsters, set())
    assert not p.has_effect('in_pit'), 'drag'


def test_a_stride_out_of_reach_ends_a_hold_at_once(g):
    import holds
    p = g.player
    m = _mon(g, 'kobold', -1)
    p.status_effects[holds.STATUS] = 3
    p.__dict__['_held'] = {'uid': holds.uid(m), 'kind': 'constrict', 'name': 'the kobold'}
    m.__dict__['_holding'] = True
    g._aimed_tile = (p.x + 4, p.y)
    _cast(g, 'shrink_the_earth_spell')
    assert not holds.is_held(p) and not p.has_effect(holds.STATUS)


# ------------------------------------------------- h2-05: a gaze asks too

def _no_save(monkeypatch):
    import status_effects
    monkeypatch.setattr(status_effects, 'apply_debuff_with_save',
                        lambda p, eff, dur, dc, **k: (bool(p.add_effect(eff, dur)), ''))


def test_a_floating_eye_cannot_paralyse_through_sanctuary_or_mist(g, monkeypatch):
    _no_save(monkeypatch)
    p = g.player
    m = _mon(g, 'floating_eye', 1)
    wards.grant(p, 'sanctuary', 8)
    for _ in range(10):
        m._gaze_cooldown = 0
        m.attack(p)
        assert not p.has_effect('paralyzed')
    p.status_effects.clear()
    m.x = p.x + 4
    wards.grant(p, 'veiled', 20)
    for _ in range(10):
        m._gaze_cooldown = 0
        m.attack(p)
        assert not p.has_effect('paralyzed')
        assert m._gaze_cooldown > 0              # its turn, spent


def test_a_bare_gazer_asks_the_wards_too(g, monkeypatch):
    _no_save(monkeypatch)
    p = g.player
    m = _mon(g, 'floating_eye', 4)
    m.attacks = []
    wards.grant(p, 'veiled', 20)
    m.attack(p)
    assert not p.has_effect('paralyzed')


@pytest.mark.parametrize('kind', ['medusa_gorgon', 'stheno_gorgon'])
def test_a_gorgons_gaze_does_not_cross_the_mist(g, monkeypatch, kind):
    _no_save(monkeypatch)
    p = g.player
    m = _mon(g, kind, 5)
    wards.grant(p, 'veiled', 20)
    m._gaze_cooldown = 0
    m.attack(p)
    assert not p.has_effect('paralyzed')


def test_medusas_fang_meets_the_styx(g):
    p = g.player
    m = _mon(g, 'medusa_gorgon', 1)
    m.thac0 = -60
    # Her fang. (The Styx stops no venom, on this road or any other: the
    # ward's rule is physical blows, wards.blow_gate.)
    m.attacks = [a for a in m.attacks if a['name'] == 'Serpent Fang']
    p.add_effect('petrify_immune', 40)
    wards.grant(p, 'styx_dipped', 6)
    hp = p.hp
    for _ in range(30):
        m._gaze_cooldown = 0
        dmg, msg = m.attack(p)
        assert dmg == 0 and p.hp == hp, msg


def test_a_gazers_follow_up_is_an_ordinary_blow(g, monkeypatch):
    p = g.player
    m = _mon(g, 'stheno_gorgon', 1)
    p.add_effect('petrify_immune', 40)
    seen = []
    monkeypatch.setattr(m, '_resolve_blow', lambda atk, pl, **k: (seen.append(atk) or (3, 'struck')))
    m._gaze_cooldown = 0
    dmg, msg = m.attack(p)
    assert dmg == 3 and seen and msg.endswith('struck') and 'slides off' in msg


def test_medusas_swing_records_what_it_swung_and_can_be_slipped(g, monkeypatch):
    p = g.player
    m = _mon(g, 'medusa_gorgon', 1)
    m.thac0 = -60
    p.add_effect('petrify_immune', 40)
    m.attacks = [a for a in m.attacks if a['name'] == 'Venom Strike']
    monkeypatch.setattr(random, 'randint', lambda lo, hi: hi)
    m._gaze_cooldown = 0
    m.attack(p)
    assert m._last_attack_type == 'poison'
    monkeypatch.setattr(m, '_slipped', lambda pl, atk: True)
    m._gaze_cooldown = 0
    dmg, msg = m.attack(p)
    assert dmg == 0 and 'You slip' in msg and 'slides off' in msg


# ------------------------------------------------------- h2-06: the Roc

def test_a_loosed_hero_is_not_carried_off(g):
    import lore_powers
    p = g.player
    m = _mon(g, 'roc_adult', 1)
    wards.grant(p, 'free_action', 6)
    hp = p.hp
    out = lore_powers.after_blow(m, p, {'carry_off': {'chance': 1.0, 'share': 0.1}}, 5)
    assert '_lp_carry_off' not in p.__dict__ and p.hp == hp
    assert wards.line('pull_loosed', m) in out


# --------------------------------------------------- h2-07: a rite again

def test_a_rite_read_again_holds_again(g):
    p = g.player
    m = _mon(g, 'skeleton', 1)
    blow = {'name': 'claw', 'type': 'physical', 'delivery': 'blow', 'damage': '1d4'}
    wards.grant(p, 'ward_lemuria', 15)
    wards.hero_struck(p, m, g.turn_count)
    assert wards.blow_gate(p, m, blow) is None
    _read(g, 'scroll_of_the_lemuria')
    assert wards.blow_gate(p, m, blow) is not None


def test_deliver_us_prayed_again_holds_again(g):
    p = g.player
    m = _mon(g, 'skeleton', 1)
    blow = {'name': 'claw', 'type': 'physical', 'delivery': 'blow', 'damage': '1d4'}
    wards.grant(p, 'ward_deliver_us', 12)
    wards.hero_struck(p, m, g.turn_count)
    wards.grant(p, 'ward_deliver_us', 12)
    assert wards.blow_gate(p, m, blow) is not None


def test_sanctuary_cast_again_is_a_new_rite():
    p = Player()
    wards.grant(p, 'sanctuary', 8)
    first = wards._gen(p, 'sanctuary')
    wards.grant(p, 'sanctuary', 8)
    assert wards._gen(p, 'sanctuary') > first


# ----------------------------------------- h2-08: the turns that were laid

def _turns(n):
    return f"{n} turn{'s' if n != 1 else ''}"


MASS = [('dulled_blades_spell', 'weakened'), ('darkness_of_egypt_spell', 'blinded'),
        ('hush_of_the_feralia_spell', 'silenced')]


@pytest.mark.parametrize('sid,status', MASS + [('bough_of_somnus_spell', 'sleeping'),
                                               ('dionysus_vine_spell', 'immobilized')])
def test_the_new_spells_say_the_turns_they_laid(g, monkeypatch, sid, status):
    m = _mon(g, 'kobold', 2)
    m.is_mini_boss = True
    monkeypatch.setattr(g, '_boss_resist_cc', lambda t, d: (max(1, d // 2), False))
    said = _cast(g, sid, m)
    got = m.status_effects[status]
    assert f'({_turns(got)})' in said, said


@pytest.mark.parametrize('sid,status', MASS)
def test_a_mixed_room_hears_both_ends(g, monkeypatch, sid, status):
    small = _mon(g, 'kobold', 2)
    great = _mon(g, 'kobold', -2)
    great.is_mini_boss = True
    monkeypatch.setattr(g, '_boss_resist_cc',
                        lambda t, d: ((max(1, d // 2) if t is great else d), False))
    said = _cast(g, sid)
    lo, hi = sorted((small.status_effects[status], great.status_effects[status]))
    assert lo < hi and f'({lo} to {hi} turns)' in said, said


def test_the_sceptre_says_the_turns_it_laid(g, monkeypatch):
    m = _mon(g, 'goblin', 2)
    monkeypatch.setattr(g, '_boss_resist_cc', lambda t, d: (3, False))
    g._advance_turn = lambda: None
    g._sceptre_quiz_done(types.SimpleNamespace(score=6))
    assert f"({_turns(m.status_effects['feared'])})" in ' '.join(g.said), g.said


@pytest.mark.parametrize('wid,status', [('wand_of_panic_wave', 'feared'),
                                        ('wand_of_sleep', 'sleeping')])
def test_wands_say_the_turns_they_laid(g, wid, status):
    m = _mon(g, 'kobold', 2)
    m.status_weak = [status]
    said = _zap(g, wid, m)
    assert _turns(m.status_effects[status]) in said, said


@pytest.mark.parametrize('sid,status', [('scroll_of_madness', 'confused'),
                                        ('scroll_of_deep_slumber', 'sleeping')])
def test_area_scrolls_say_the_turns_they_laid(g, sid, status):
    m = _mon(g, 'kobold', 2)
    m.is_mini_boss = True
    m.status_weak = [status]
    said = _read(g, sid)
    if m.status_effects.get(status):
        assert _turns(m.status_effects[status]) in said, said


@pytest.mark.parametrize('sid,status', [('mass_sleep_spell', 'sleeping'),
                                        ('mass_paralyze_spell', 'paralyzed'),
                                        ('mass_slow_spell', 'slowed')])
def test_the_older_area_spells_say_the_turns_they_laid(g, monkeypatch, sid, status):
    m = _mon(g, 'kobold', 2)
    m.is_mini_boss = True
    monkeypatch.setattr(g, '_boss_resist_cc', lambda t, d: (max(1, d // 2), False))
    said = _cast(g, sid)
    assert _turns(m.status_effects[status]) in said, said


# -------------------------------------------------- h2-09: a story's lamp

def test_darkness_leaves_a_story_lamp(g):
    import light_shy
    p = g.player
    p.add_floor_effect('light', 2)
    assert light_shy.snuff(p, 'dark') == ''
    assert p.status_effects.get('light') == -1


def test_light_on_a_story_lamp_costs_nothing(g):
    p = g.player
    p.add_floor_effect('light', 2)
    p.known_spells = {'light_spell': 2}
    mp = p.mp
    g._invoke_spell('light_spell')
    assert p.mp == mp and g.state == STATE_PLAYER
    assert lights.line('spell_held') in g.said and 'for good' not in lights.line('spell_held')


def test_a_known_wand_of_light_on_a_story_lamp_keeps_its_charge(g):
    p = g.player
    p.add_floor_effect('light', 2)
    wand = items.make_item_by_id('wand', 'wand_of_candle_light')
    wand.identified = True
    p.known_item_ids.add(wand.id)
    p.inventory.append(wand)
    n = wand.charges
    g._invoke_wand(wand)
    assert wand.charges == n and g.state == STATE_PLAYER
    assert lights.line('spell_held') in g.said


# ----------------------------------------- h2-10: lit for a look is lit

def _look_and_douse(game):
    _press(game, 'O')
    assert lights.is_lit(game.player.shield)
    _press(game, 'O')


def test_light_look_douse_burns_the_turn_and_is_seen_for_it(g, monkeypatch):
    p = g.player
    lt = _light(p)
    _press(g, 'L')
    _press(g, 'O')
    g._advance_turn()
    assert lights.shine(p) == 0
    fuel, t0 = lt.fuel, g.turn_count
    shone = []
    monkeypatch.setattr(g, '_do_monster_turns', lambda: shone.append(lights.shine(p)))
    for _ in range(40):
        _look_and_douse(g)
        assert g.turn_count == t0 + len(shone)          # both free
        g._advance_turn()
    assert lt.fuel == fuel - 40
    assert shone == [lights.notice_of(lt)] * len(shone)
    assert lights.shine(p) == 0 and not lt.lit


def test_lit_and_left_lit_burns_once(g):
    p = g.player
    lt = _light(p)
    _press(g, 'L')
    _press(g, 'O')
    for _ in range(3):
        _press(g, 'O')
        _press(g, 'O')
    _press(g, 'O')
    fuel = lt.fuel
    g._advance_turn()
    assert lt.fuel == fuel - 1
    assert lt.lit


def test_lit_for_a_look_and_then_slung_still_pays(g, monkeypatch):
    p = g.player
    _weapon(p, 'longsword', 'hand')
    _weapon(p, 'greatsword', 'back')
    lt = _light(p)
    _press(g, 'L')
    _press(g, 'O')
    g._advance_turn()
    fuel = lt.fuel
    shone = []
    monkeypatch.setattr(g, '_do_monster_turns', lambda: shone.append(lights.shine(p)))
    _press(g, 'O')
    _press(g, 's')
    assert p.shield is None and lt.fuel == fuel - 1
    assert shone and shone[0] == lights.notice_of(lt)


def test_a_free_swap_that_lights_the_torch_pays(g):
    p = g.player
    p.quirk_progress['janus_active'] = True
    _weapon(p, 'longsword', 'hand')
    _weapon(p, 'greatsword', 'back')
    lt = _light(p)
    _press(g, 'L')
    _press(g, 's')
    g._advance_turn()
    fuel, t0 = lt.fuel, g.turn_count
    _press(g, 's')
    assert p.shield is lt and lt.lit
    _press(g, 's')
    assert p.shield is None and g.turn_count == t0
    g._advance_turn()
    assert lt.fuel == fuel - 1


def test_a_hasted_heros_look_is_seen_when_the_world_next_looks(g, monkeypatch):
    p = g.player
    lt = _light(p)
    _press(g, 'L')
    _press(g, 'O')
    g._advance_turn()
    p.status_effects['hasted'] = 20
    shone = []
    monkeypatch.setattr(g, '_do_monster_turns', lambda: shone.append(lights.shine(p)))
    _look_and_douse(g)
    for _ in range(3):
        g._advance_turn()
        if shone:
            break
    assert shone[0] == lights.notice_of(lt)


def test_a_torch_lit_for_its_last_look_is_burnt_out_and_not_relit(g):
    p = g.player
    lt = _light(p, fuel=2)
    _press(g, 'L')
    assert lt.fuel == 1
    _press(g, 'O')
    spare = _light(p)
    _look_and_douse(g)
    g._advance_turn()
    assert p.shield is None and not spare.lit and not any(i is lt for i in p.inventory)
    assert lights.line('burnt_out', light=g._bare_name(lt)) in g.said


def test_what_is_owed_survives_a_save_and_an_old_save_owes_nothing():
    import pickle
    p = Player()
    for k in ('_light_last', '_kindled', '_kindled_glow'):
        p.__dict__.pop(k, None)
    back = pickle.loads(pickle.dumps(p))
    assert back._light_last == '' and back._kindled is None and back._kindled_glow == 0


# ------------------------------------------------ h2-11: an empty room

@pytest.mark.parametrize('sid', ['hush_of_the_feralia_spell', 'pans_panic_spell',
                                 'darkness_of_egypt_spell', 'dulled_blades_spell'])
def test_an_area_spell_into_an_empty_room_keeps_sanctuary(g, sid):
    p = g.player
    wards.grant(p, 'sanctuary', 8)
    _cast(g, sid)
    assert p.has_effect('sanctuary')


def test_a_tune_and_the_sceptre_with_no_one_to_hear_keep_sanctuary(g):
    p = g.player
    wards.grant(p, 'sanctuary', 8)
    _read(g, 'scroll_of_the_hamelin_piper')
    assert p.has_effect('sanctuary'), 'the tune'
    _zap(g, 'krotala_of_athena')
    assert p.has_effect('sanctuary'), 'the Krotala'
    g.monsters[:] = []
    g._advance_turn = lambda: None
    g._sceptre_quiz_done(types.SimpleNamespace(score=3))
    assert p.has_effect('sanctuary'), 'the Sceptre'


def test_an_area_spell_at_someone_still_ends_sanctuary(g):
    p = g.player
    wards.grant(p, 'sanctuary', 8)
    _mon(g, 'kobold', 2)
    _cast(g, 'hush_of_the_feralia_spell')
    assert not p.has_effect('sanctuary')


def test_the_audits_ruling_stands_for_a_foe_out_of_its_reach(g):
    """M3, 2026-11-20: a foe in sight makes it a hostile act, even one the
    spell does not work on."""
    p = g.player
    wards.grant(p, 'sanctuary', 8)
    p.PER = 18
    m = _mon(g, 'kobold', 5)
    assert g._in_spell_sight(m)
    _cast(g, 'pans_panic_spell')
    assert not p.has_effect('sanctuary')


def test_a_creature_that_only_appears_is_no_blow(g):
    p = g.player
    wards.grant(p, 'sanctuary', 8)
    g._mm_acting(lambda: _mon(g, 'kobold', 2))
    assert p.has_effect('sanctuary')


# ------------------------------------------------- h2-12: the tile cursor

def test_the_tile_cursor_crosses_the_hero(g):
    p = g.player
    g.player.known_spells = {'shrink_the_earth_spell': 6}
    g._invoke_spell('shrink_the_earth_spell')
    assert g.state == STATE_TARGET
    g._target_input(pygame.K_RIGHT)
    g._target_input(pygame.K_LEFT)
    assert (g.target_cursor_x, g.target_cursor_y) == (p.x, p.y)
    g._target_input(pygame.K_LEFT)
    assert g.target_cursor_x == p.x - 1


# ---------------------------------------------------- h2-13: fire and cold

@pytest.mark.parametrize('shield,status', [('fire_shield', 'burning'), ('cold_shield', 'frozen')])
def test_the_full_shield_keeps_off_what_the_resist_keeps_off(shield, status):
    p = Player()
    p.add_effect(shield, 30)
    assert p.add_effect(status, 6) is False and not p.has_effect(status)


@pytest.mark.parametrize('shield,status', [('fire_shield', 'burning'), ('cold_shield', 'frozen')])
def test_laying_the_shield_puts_out_what_is_there(shield, status):
    p = Player()
    assert p.add_effect(status, 6)
    p.add_effect(shield, 30)
    assert not p.has_effect(status)


# ------------------------------------------- h2-14: turns said, turns laid

@pytest.mark.parametrize('sid,status', [('scroll_of_absolute_ward', 'shielded'),
                                        ('scroll_of_aegis', 'shielded')])
def test_a_warding_rite_says_the_turns_it_has(g, sid, status):
    p = g.player
    said = _read(g, sid)
    assert f'for {_turns(p.status_effects[status])}.' in said, said


def test_a_rite_read_again_says_what_is_left(g):
    p = g.player
    p.add_effect('shielded', 25)
    said = _read(g, 'scroll_of_aegis')
    assert f"for {_turns(p.status_effects['shielded'])}." in said, said


@pytest.mark.parametrize('sid,status', [('mage_armor_spell', 'shielded'),
                                        ('displacement_spell', 'displacement'),
                                        ('detect_monsters_spell', 'clairvoyant'),
                                        ('sanctuary_spell', 'sanctuary'),
                                        ('stayed_spear_spell', 'stayed_spear'),
                                        ('galdr_of_loosing_spell', 'free_action'),
                                        ('mist_of_manannan_spell', 'veiled')])
def test_a_spell_on_the_hero_says_what_he_has(g, sid, status):
    p = g.player
    p.status_effects[status] = 55
    said = _cast(g, sid)
    assert _turns(p.status_effects[status]) in said, said


@pytest.mark.parametrize('wid_effect,status', [('shield_self', 'shielded'),
                                               ('regeneration_self', 'regenerating'),
                                               ('reflect_self', 'reflecting')])
def test_a_wand_on_the_hero_says_what_he_has(g, wid_effect, status):
    p = g.player
    p.status_effects[status] = 55
    wand = items.make_item_by_id('wand', 'wand_of_candle_light')
    wand.effect, wand.quiz_tier = wid_effect, 5
    g.said.clear()
    g._apply_wand_effect(wand)
    assert _turns(p.status_effects[status]) in ' '.join(g.said), g.said


@pytest.mark.parametrize('pid,status', [('potion_of_see_invisible', 'see_invisible'),
                                        ('potion_of_regeneration', 'regenerating'),
                                        ('potion_of_levitation', 'levitating'),
                                        ('potion_of_fire_resistance', 'fire_resist'),
                                        ('theriac', 'poison_resist')])
def test_a_potion_says_the_turns_it_gave(g, pid, status):
    import food_system
    p = g.player
    pot = items.make_item_by_id('potion', pid)
    pot.buc = 'uncursed'
    p.inventory.append(pot)
    out = ' '.join(str(m) for m in food_system.drink_potion(p, pot))
    assert _turns(p.status_effects[status]) in out, out


# ------------------------------------------------- h2-15: the card is true

def test_the_vines_card_agrees_with_the_fixture(g):
    with open(os.path.join(ROOT, 'data', 'hazards.json'), encoding='utf-8') as f:
        text = f.read()
    spec = text[text.index('"conjured_vine"'):]
    assert '"chance": 1.0' in spec and '"save": true' in spec    # ruling A6: the save is the way out
    assert 'vines catch whatever steps in' in LEARNABLE_SPELLS['dionysus_vine_spell']['desc']
    said = _cast(g, 'dionysus_vine_spell', _mon(g, 'kobold', 3))
    assert 'catch whatever steps in' in said and 'may catch' not in said


# ---------------------------------------------------- h2-16: Sanctification

def test_sanctification_passes_over_the_torch(g):
    p = g.player
    g._equip_item(_light(p))
    _read(g, 'scroll_of_sanctification')
    assert p.shield.buc == 'uncursed'


def test_sanctification_still_blesses_what_it_helps(g):
    p = g.player
    g._equip_item(_light(p))
    _weapon(p, 'longsword', 'hand')
    _read(g, 'scroll_of_sanctification')
    assert p.weapon.buc == 'blessed' and p.shield.buc == 'uncursed'


# -------------------------------------------------------- h2-17: Penelope

def test_a_lantern_in_and_out_is_no_change_of_armour(g):
    p = g.player
    _light(p, 'jacks_lantern')
    n = g.quirk_system._p('penelope_count')
    for _ in range(10):
        _press(g, 'L')
    assert g.quirk_system._p('penelope_count') == n


# ----------------------------------------------- h2-18: an old save's wand

def test_an_old_saves_light_wands_read_their_turns(g):
    import main
    import save_system
    p = g.player
    old = {'wand_of_candle_light': ('4', '60'), 'lantern_of_diogenes': ('8', '120'),
           'wand_of_torch_light': ('8', '120')}
    candle = items.make_item_by_id('wand', 'wand_of_candle_light')
    candle.power = old[candle.id][0]
    p.inventory.append(candle)
    lantern = items.make_item_by_id('wand', 'lantern_of_diogenes')
    lantern.power, lantern.light_reveals = old[lantern.id][0], False
    lantern.x, lantern.y = p.x, p.y
    g.ground_items.append(lantern)
    torch = items.make_item_by_id('wand', 'wand_of_torch_light')
    torch.power = old[torch.id][0]
    thief = _mon(g, 'kobold', 2)
    thief.__dict__['stolen_items'] = [torch]
    assert save_system.save_game(g) is not False
    g2, err = main._restore_saved_game(g.screen, g.player_name, save_system.load_game(g.player_name))
    assert g2 is not None, err
    found = list(g2.player.inventory) + list(g2.ground_items)
    for m in g2.monsters:
        found += m.__dict__.get('stolen_items') or []
    seen = {i.id: i for i in found if i.id in old}
    assert {k: v.power for k, v in seen.items()} == {k: v[1] for k, v in old.items()}
    assert seen['lantern_of_diogenes'].light_reveals
