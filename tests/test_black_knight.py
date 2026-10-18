"""The Black Knight (src/black_knight.py): about one run in four, on one floor
from 15 to 19, a knight on a little stone bridge says none shall pass. He never
moves, loses a limb at 75/50/25 per cent, any one hit takes at most one limb,
his sword falls at the sword-arm stage, and at 0 he is a harmless torso you
step round.

Behaviour tests on a real headless Game. He is a rare, randomized, deep event,
so Brandon cannot reach him on demand in play: these are the proof.
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(name='__test_black_knight__', seed=7):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name=name)
    g.state = STATE_PLAYER
    return g


def _on_his_floor(g, floor=17):
    """Go down to his floor the ordinary way: the game builds his bridge."""
    g._black_knight = {'floor': floor, 'spawned': False, 'outcome': None, 'sword_dropped': False}
    g._change_level(floor, enter_from_top=True)
    ks = _knights(g)
    assert len(ks) == 1
    return ks[0]


def _knights(g):
    import black_knight as bk
    return [m for m in g.monsters if bk.is_black_knight(m) and m.alive]


def _beside(g, k):
    """Stand the hero on a tile next to him (a bridge tile when there is one)
    and return the step that walks into him."""
    bt = getattr(g.dungeon, 'bridge_tiles', {}) or {}
    opts = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x, y = k.x - dx, k.y - dy
        if g.dungeon.is_walkable(x, y) and not any((m.x, m.y) == (x, y) for m in g.monsters if m is not k):
            opts.append(((x, y) in bt, x, y, dx, dy))
    opts.sort(reverse=True)
    _, x, y, dx, dy = opts[0]
    g.player.x, g.player.y = x, y
    for m in list(g.monsters):            # nothing else joins in
        if m is not k:
            g.monsters.remove(m)
    g.pets = []
    g._refresh_fov()
    return dx, dy


def _hit(g, k, amount=10 ** 6, kind='physical'):
    """One action's blow, then the world's turn."""
    k.take_damage(amount, kind)
    g._advance_turn()


def _log(g):
    return ' | '.join(str(e[0]) for e in g.msg_log.entries)


# ---------------------------------------------------------------------------
# The roll
# ---------------------------------------------------------------------------

def test_about_one_run_in_four_gets_him_on_a_floor_from_15_to_19():
    import black_knight as bk
    floors = [bk.roll_floor(random.Random(i)) for i in range(4000)]
    got = [f for f in floors if f is not None]
    assert 0.22 < len(got) / len(floors) < 0.28
    assert set(got) == {15, 16, 17, 18, 19}


def test_the_roll_leaves_the_shared_random_stream_alone():
    import black_knight as bk
    random.seed(99)
    before = random.getstate()
    bk.new_run_state()
    assert random.getstate() == before


def test_a_new_game_rolls_him_and_saves_the_floor():
    g = _game()
    st = g._black_knight
    assert st['spawned'] is False and st['outcome'] is None
    assert st['floor'] is None or 15 <= st['floor'] <= 19


def test_he_appears_only_on_his_floor():
    g = _game('__test_bk_floors__')
    g._black_knight = {'floor': 16, 'spawned': False, 'outcome': None, 'sword_dropped': False}
    seen = {}
    for lvl in (15, 16, 17):
        g._change_level(lvl, enter_from_top=True)
        seen[lvl] = len(_knights(g))
    assert seen == {15: 0, 16: 1, 17: 0}
    g._change_level(16, enter_from_top=False)       # back up: the same knight, not a second
    assert len(_knights(g)) == 1


def test_a_run_without_him_never_meets_him():
    g = _game('__test_bk_none__')
    g._black_knight = {'floor': None, 'spawned': False, 'outcome': None, 'sword_dropped': False}
    for lvl in range(14, 20):
        g._change_level(lvl, enter_from_top=True)
        assert not _knights(g)


# ---------------------------------------------------------------------------
# The bridge, and the way round
# ---------------------------------------------------------------------------

def _check_site(d, start, site):
    import black_knight as bk
    from dungeon import WATER
    kx, ky = site['knight']
    assert d.is_walkable(kx, ky)
    if site['kind'] == 'bridge':
        assert len(site['bridge']) == 3 and site['knight'] == site['bridge'][1]
        px, py = (0, 1) if site['axis'] == 'h' else (1, 0)
        for bx, by in site['bridge']:
            assert d.is_walkable(bx, by)
            assert d.bridge_tiles[(bx, by)] == site['axis']
            # water on both sides of every bridge tile: a strip across the corridor
            assert d.tiles[by + py][bx + px] == WATER and d.tiles[by - py][bx - px] == WATER
    # The way round: everything he could reach before, the hero can still reach
    # with the knight standing on his tile, both stairs included.
    whole = bk.flood(d, start)
    cut = bk.flood(d, start, blocked=(kx, ky))
    assert cut == whole - {(kx, ky)}
    from dungeon import STAIRS_DOWN
    downs = [(x, y) for y in range(d.height) for x in range(d.width) if d.tiles[y][x] == STAIRS_DOWN]
    assert downs and all(t in cut for t in downs)


def test_every_site_leaves_a_way_round_on_many_floors():
    import black_knight as bk
    from dungeon import generate_dungeon
    kinds = {}
    for i in range(120):
        # (generate_dungeon draws from its own unseeded generator: each run
        # walks 120 new floors, which is how the loopless floor turned up)
        random.seed(1000 + i)
        d = generate_dungeon(80, 50, 15 + i % 5)
        start = d.rooms[0].center
        site = bk.find_site(d, start, random.Random(i))
        assert site is not None
        walk_before = bk.flood(d, start)
        bk.build_bridge(d, site)
        assert bk.flood(d, start) == walk_before          # water only replaced rock
        _check_site(d, start, site)
        kinds[site['kind']] = kinds.get(site['kind'], 0) + 1
    assert kinds.get('bridge', 0) > 60                     # most floors get the bridge


def _tree_floor(level=17):
    """Three 7x7 rooms in a row, each joined to the next by one straight
    corridor walled on both sides, the up stair in the first and the down
    stair in the last. No loop anywhere: every corridor tile and doorway is
    the only way on (a generated floor whose extra corridors all ran over old
    ones is like this, about one in 9,000)."""
    from dungeon import FLOOR, STAIRS_DOWN, STAIRS_UP, WALL, Dungeon, Room
    w, h = 50, 13
    tiles = [[WALL] * w for _ in range(h)]
    rooms = [Room(1 + 17 * i, 2, 9, 9) for i in range(3)]
    for r in rooms:
        for x, y in r.inner_tiles():
            tiles[y][x] = FLOOR
    cy = rooms[0].center[1]
    for x in range(rooms[0].center[0], rooms[-1].center[0] + 1):
        tiles[cy][x] = FLOOR
    (ux, uy), (dx, dy) = rooms[0].center, rooms[-1].center
    tiles[uy][ux], tiles[dy][dx] = STAIRS_UP, STAIRS_DOWN
    return Dungeon(tiles, rooms, w, h, level)


def test_on_a_floor_with_no_loop_he_stands_in_a_room_with_a_way_round():
    """With no loop, no bridge and no doorway leaves a way round. find_site
    used to give up (None) and the game set him on any free tile, often a
    corridor that was the only way on to the stairs. Now he stands in a room,
    on a tile the hero can walk round, away from the stairs."""
    import black_knight as bk
    from dungeon import STAIRS_DOWN, STAIRS_UP
    d = _tree_floor()
    start = d.rooms[0].center
    cands = bk._bridge_candidates(d, bk._room_cells(d), 3)
    assert cands and not any(bk.has_way_round(d, start, t[len(t) // 2]) for _a, t in cands)
    doorways = [p for r in d.rooms for p in r.wall_tiles() if d.is_walkable(*p)]
    assert doorways and not any(bk.has_way_round(d, start, p) for p in doorways)
    for i in range(30):
        site = bk.find_site(d, start, random.Random(i))
        assert site is not None and site['kind'] == 'room'
        kx, ky = site['knight']
        assert (kx, ky) not in set(d.rooms[0].inner_tiles())          # not where the hero stands
        assert all(d.tiles[ky + oy][kx + ox] not in (STAIRS_UP, STAIRS_DOWN)
                   for ox in (-1, 0, 1) for oy in (-1, 0, 1))
        bk.build_bridge(d, site)
        _check_site(d, start, site)


def test_on_a_real_floor_with_no_loop_the_stairs_stay_reachable(monkeypatch):
    import black_knight as bk
    from dungeon import STAIRS_DOWN
    g = _game('__test_bk_tree__')
    monkeypatch.setattr(g.level_mgr, 'generate', lambda n: (_tree_floor(n), [], []))
    k = _on_his_floor(g, 17)
    start = (g.player.x, g.player.y)
    assert bk.has_way_round(g.dungeon, start, (k.x, k.y))
    cut = bk.flood(g.dungeon, start, blocked=(k.x, k.y))
    assert any(g.dungeon.tiles[y][x] == STAIRS_DOWN for x, y in cut)


def test_on_a_real_floor_he_stands_on_his_bridge_and_the_stairs_stay_reachable():
    g = _game('__test_bk_bridge__')
    k = _on_his_floor(g, 17)
    import black_knight as bk
    bt = getattr(g.dungeon, 'bridge_tiles', {})
    if bt:
        assert (k.x, k.y) in bt
    assert bk.has_way_round(g.dungeon, (g.player.x, g.player.y), (k.x, k.y))
    # the game's own reachability (four ways, through doors) agrees
    from dungeon import STAIRS_DOWN
    walk = g._reachable_tiles(g.player.x, g.player.y)
    assert any(g.dungeon.tiles[y][x] == STAIRS_DOWN for x, y in walk)


def test_with_no_corridor_that_suits_he_takes_a_doorway_with_a_way_round():
    import black_knight as bk
    from dungeon import generate_dungeon
    for i in range(60):
        random.seed(5000 + i)
        d = generate_dungeon(80, 50, 17)
        start = d.rooms[0].center
        real = bk._bridge_candidates
        bk._bridge_candidates = lambda *a, **k: []
        try:
            site = bk.find_site(d, start, random.Random(i))
        finally:
            bk._bridge_candidates = real
        if site is None:
            continue
        assert site['kind'] == 'doorway'
        bk.build_bridge(d, site)
        _check_site(d, start, site)
        return
    raise AssertionError('no floor had a doorway with a way round')


# ---------------------------------------------------------------------------
# He never moves
# ---------------------------------------------------------------------------

def test_he_never_moves_or_pursues():
    g = _game('__test_bk_still__')
    k = _on_his_floor(g)
    _beside(g, k)
    spot = (k.x, k.y)
    # walk the hero a few tiles off, aggravate him, frighten him, push him
    g.player.add_effect('aggravated', 50)
    k.add_effect('feared', 10)
    for _ in range(30):
        g._advance_turn()
        assert (k.x, k.y) == spot
    from combat import apply_knockback
    apply_knockback(g.player, k, g.dungeon, g.monsters)
    k.x, k.y = k.x + 5, k.y + 5              # a teleport, a pull, anything that sets his place
    assert (k.x, k.y) == spot
    from game_magic import _is_big_foe
    assert _is_big_foe(k)                    # polymorph, charm and fear wands pass him by


def test_he_strikes_whoever_stands_next_to_him():
    g = _game('__test_bk_strike__')
    k = _on_his_floor(g)
    _beside(g, k)
    assert k.take_turn(g.player, g.dungeon, g.monsters) is True
    g.player.x += 5
    assert k.take_turn(g.player, g.dungeon, g.monsters) is False


# ---------------------------------------------------------------------------
# Limbs: stages, sprites, attacks, and one limb a hit
# ---------------------------------------------------------------------------

STAGE_SPRITES = ['black_knight', 'black_knight_one_arm', 'black_knight_no_arms',
                 'black_knight_one_leg', 'black_knight_torso']
STAGE_ATTACKS = [{'Broadsword', 'Shield Rim'}, {'Broadsword'}, {'Armoured Kick'},
                 {'Hopping Shoulder-Barge'}, set()]


def test_each_stage_has_its_sprite_and_attack():
    g = _game('__test_bk_stages__')
    k = _on_his_floor(g)
    _beside(g, k)
    assert k.max_hp == 60
    marks = [k.threshold(i) for i in (1, 2, 3)]
    assert marks == [45, 30, 15]
    for stage in range(5):
        assert k.stage == stage
        assert k.sprite_id == STAGE_SPRITES[stage]
        assert {a['name'] for a in k.attacks} == STAGE_ATTACKS[stage]
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters', k.sprite_id + '.png'))
        if stage < 4:
            assert k.hp == (60 if stage == 0 else marks[stage - 1])
            _hit(g, k)
        if stage == 3:
            assert k.stage == 3 and k.hp == 1      # teetering on his last leg
            assert 'teeters on his one leg' in _log(g)
            _hit(g, k)


def test_the_renderer_draws_the_sprite_of_his_stage():
    """game_render asks for sprite_id: the stage's picture, not the base one."""
    g = _game('__test_bk_render__')
    k = _on_his_floor(g)
    _beside(g, k)
    asked = []
    real = g.renderer.draw_entity

    def spy(*a, **kw):
        asked.append(kw.get('mid'))
        return real(*a, **kw)
    g.renderer.draw_entity = spy
    g.render()
    assert 'black_knight' in asked
    _hit(g, k)
    _hit(g, k)
    asked.clear()
    g.render()
    assert 'black_knight_no_arms' in asked and 'black_knight' not in asked


def test_a_huge_hit_takes_one_limb_only():
    g = _game('__test_bk_cap__')
    k = _on_his_floor(g)
    _beside(g, k)
    k.take_damage(10 ** 6, 'physical')
    assert k.stage == 1 and k.hp == 45 and k.alive
    # a second blow in the same action (the Sword of Damocles' fall, a proc,
    # a spell in the same breath) takes nothing more
    k.take_damage(10 ** 6, 'fire')
    k.hp = 0
    assert k.stage == 1 and k.hp == 45
    g._advance_turn()
    k.take_damage(10 ** 6, 'lightning')
    assert k.stage == 2 and k.hp == 30


def test_small_hits_wear_him_down_inside_a_stage():
    g = _game('__test_bk_small__')
    k = _on_his_floor(g)
    _beside(g, k)
    _hit(g, k, 5)
    assert k.hp == 55 and k.stage == 0
    _hit(g, k, 12)                           # 55 -> 43 crosses 45: the arm, stopped at 45
    assert k.hp == 45 and k.stage == 1


def test_he_takes_at_least_five_hits():
    g = _game('__test_bk_five__')
    k = _on_his_floor(g)
    _beside(g, k)
    hits = 0
    while not k.defeated:
        _hit(g, k)
        hits += 1
        assert hits <= 5
    assert hits == 5 and k.alive and k in g.monsters


def test_instant_kills_stop_at_the_next_mark():
    g = _game('__test_bk_instakill__')
    k = _on_his_floor(g)
    _beside(g, k)
    def _corpses():
        return {id(i) for i in g.ground_items
                if getattr(i, 'is_corpse', False) or 'corpse' in str(getattr(i, 'id', ''))}
    before = _corpses()          # other floor monsters may already lie dead
    # the death-effect pattern: set dead, then hand to the kill handler
    k.hp = 0
    k.alive = False
    g._on_monster_killed(k)
    assert k.alive and k.stage == 1 and k in g.monsters
    assert _corpses() == before                 # he left no corpse
    g._advance_turn()
    # a real wand of death ray through the game's own wand code
    from items import make_item_by_id
    import copy
    wand = copy.deepcopy(make_item_by_id('wand', 'wand_of_death_ray'))
    wand.effect = 'death_ray'
    assert k.stage == 1 and k.hp == 45, (k.stage, k.hp, _log(g)[-400:])
    g._wand_override_target = k
    try:
        for _ in range(3):                   # three zaps in one action: one limb
            g._apply_wand_effect(wand)
    finally:
        g._wand_override_target = None
    assert k.stage == 2 and k.alive, (k.stage, k.hp, _log(g)[-400:])


def test_his_sword_falls_onto_the_bridge_at_the_sword_arm_stage():
    g = _game('__test_bk_sword__')
    k = _on_his_floor(g)
    _beside(g, k)
    _hit(g, k)
    assert not [i for i in g.ground_items if i.id == 'flesh_wound']
    _hit(g, k)
    swords = [i for i in g.ground_items if i.id == 'flesh_wound']
    assert len(swords) == 1
    s = swords[0]
    assert max(abs(s.x - k.x), abs(s.y - k.y)) == 1
    bt = getattr(g.dungeon, 'bridge_tiles', {}) or {}
    if bt:
        assert (s.x, s.y) in bt
    assert "clatters onto the bridge" in _log(g)
    _hit(g, k)
    _hit(g, k)
    assert len([i for i in g.ground_items if i.id == 'flesh_wound']) == 1


def test_his_sword_is_a_modest_fixed_unique():
    import json
    with open(os.path.join(ROOT, 'data', 'items', 'weapon.json'), encoding='utf-8') as f:
        w = json.load(f)['flesh_wound']
    assert w['is_unique'] and w['mathTier'] == 2 and w['base_damage'] == 20
    assert w['min_level'] >= 9999 and not w['peak_weight']        # never random loot
    assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', 'flesh_wound.png'))
    from items import scripted_only_ids
    assert 'flesh_wound' in scripted_only_ids()


# ---------------------------------------------------------------------------
# The torso: harmless, step round him, never blocks
# ---------------------------------------------------------------------------

def _torso(g):
    k = _on_his_floor(g)
    step = _beside(g, k)
    for _ in range(5):
        _hit(g, k)
    assert k.defeated
    return k, step


def test_at_zero_he_is_a_harmless_torso_not_a_kill():
    g = _game('__test_bk_torso__')
    killed = g.level_mgr.monsters_killed
    k, _ = _torso(g)
    assert k.alive and k.hp >= 1 and k in g.monsters and k.is_allied
    assert g.level_mgr.monsters_killed == killed
    assert g._black_knight['outcome'] == 'draw'
    assert "we'll call it a draw" in _log(g)
    hp = g.player.hp
    for _ in range(20):
        g._advance_turn()
    assert g.player.hp >= hp - 0            # he only bites boots
    assert k.take_damage(10 ** 6) == 0 and k.defeated and k.alive


def test_bumping_the_torso_swaps_places():
    g = _game('__test_bk_swap__')
    k, (dx, dy) = _torso(g)
    me, him = (g.player.x, g.player.y), (k.x, k.y)
    g._do_move(dx, dy)
    assert (g.player.x, g.player.y) == him and (k.x, k.y) == me
    assert "You step around the Black Knight" in _log(g)
    # and back again: he never blocks the bridge
    g._do_move(-dx, -dy)
    assert (g.player.x, g.player.y) == me


# ---------------------------------------------------------------------------
# Lines and records
# ---------------------------------------------------------------------------

def test_lines_fire_greeting_limbs_and_parting_shouts():
    g = _game('__test_bk_lines__')
    k = _on_his_floor(g)
    _beside(g, k)
    g._advance_turn()
    log = _log(g)
    assert 'None shall pass.' in log
    assert any('none shall pass' in c.lower() for c in _chronicle(g))
    assert 'black_knight' in g.player.known_monster_ids       # bestiary entry
    _hit(g, k)
    assert "'Tis but a scratch." in _log(g)
    _hit(g, k)
    assert "It's just a flesh wound." in _log(g)
    assert g._bk_speech and g._bk_speech['text'] == "It's just a flesh wound."
    # walk away: he shouts after you
    k._bk_engaged = True
    g.player.x, g.player.y = k.x + 6, k.y
    if not g.dungeon.is_walkable(g.player.x, g.player.y):
        g.player.x, g.player.y = k.x, k.y + 6
    g._black_knight_tick(end=True)
    import black_knight as bk
    assert any(line in _log(g) for line in bk.data()['walk_away_lines'])


def _chronicle(g):
    return [str(e.get('text', e) if isinstance(e, dict) else e) for e in g._chronicle]


def test_the_torso_shouts_as_you_pass_and_leave():
    import black_knight as bk
    g = _game('__test_bk_torso_lines__')
    k, (dx, dy) = _torso(g)
    g._do_move(dx, dy)
    assert bk.data()['torso_pass_lines'][0] in _log(g)
    k._bk_engaged = True
    g.player.x, g.player.y = k.x + 6, k.y
    g._black_knight_tick(end=True)
    assert "Come back here, I'll bite your legs off!" in _log(g)
    assert any('draw' in c for c in _chronicle(g))


def test_the_floating_line_draws_over_him():
    g = _game('__test_bk_float__')
    k = _on_his_floor(g)
    _beside(g, k)
    g._advance_turn()
    assert g._bk_speech['text'] == 'None shall pass.'
    g.render()                                 # no error, and it is still showing
    assert g._bk_speech is not None


# ---------------------------------------------------------------------------
# Save and load
# ---------------------------------------------------------------------------

def _roundtrip(g, name, tmp_path, monkeypatch):
    import save_system
    from main import Game
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    save_system.settle_unfinished_actions(g)
    assert save_system.save_game(g)
    state = save_system.load_game(name)
    g2 = Game(_screen(), player_name=name)
    g2.load_state(state)
    from game_states import STATE_PLAYER
    g2.state = STATE_PLAYER
    return g2


def test_save_and_load_mid_fight(tmp_path, monkeypatch):
    name = '__test_bk_save_mid__'
    g = _game(name)
    k = _on_his_floor(g)
    _beside(g, k)
    _hit(g, k)
    _hit(g, k)
    spot = (k.x, k.y)
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    ks = _knights(g2)
    assert len(ks) == 1
    k2 = ks[0]
    assert k2.stage == 2 and k2.hp == 30 and (k2.x, k2.y) == spot
    assert g2._black_knight['spawned'] and g2._black_knight['sword_dropped']
    assert getattr(g2.dungeon, 'bridge_tiles', None) == getattr(g.dungeon, 'bridge_tiles', None)
    # still rooted, still one limb a hit
    k2.x += 3
    assert (k2.x, k2.y) == spot
    k2.take_damage(10 ** 6)
    k2.take_damage(10 ** 6)
    assert k2.stage == 3


def test_save_and_load_after_the_draw(tmp_path, monkeypatch):
    name = '__test_bk_save_draw__'
    g = _game(name)
    k, (dx, dy) = _torso(g)
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    k2 = _knights(g2)[0]
    assert k2.defeated and k2.is_allied and k2.stage == 4
    assert g2._black_knight['outcome'] == 'draw'
    assert len([i for i in g2.ground_items if i.id == 'flesh_wound']) == 1
    me = (g.player.x, g.player.y)
    assert (g2.player.x, g2.player.y) == me and (k2.x, k2.y) == (k.x, k.y)
    g2._refresh_fov()
    g2._do_move(dx, dy)
    assert (g2.player.x, g2.player.y) == (k.x, k.y) and (k2.x, k2.y) == me


def test_a_save_from_before_him_has_no_knight(tmp_path, monkeypatch):
    name = '__test_bk_old_save__'
    g = _game(name)
    del g._black_knight
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    assert g2._black_knight['floor'] is None


def test_the_data_ships_with_the_game():
    with open(os.path.join(ROOT, 'PhilosophersQuest.spec'), encoding='utf-8') as f:
        assert "'data/black_knight.json'" in f.read()
    for s in STAGE_SPRITES:
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters', s + '.png'))
    for s in ('bridge_h', 'bridge_v'):
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'env', s + '.png'))


def test_he_is_weak_for_his_depth_with_fixed_numbers():
    import json
    from floor_curve import target_hp
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        m = json.load(f)['black_knight']
    assert m['hp'] == '60' and m['frequency'] == 0 and not m['peak_weight']
    assert int(m['hp']) < 0.5 * target_hp(15)
    assert m['treasure']['item_chance'] == 0 and m['treasure']['gold'] == [0, 0]
