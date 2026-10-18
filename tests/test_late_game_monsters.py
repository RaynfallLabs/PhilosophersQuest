"""The 2026-10 late-game monster pass (MONSTER_CATALOG_AUDIT.md, all fourteen
proposals plus a lore-first deep set).

Deep, randomized spawns Brandon cannot reach on demand in play, so these are
data-layer guards plus behaviour tests on a real headless Game for every new
mechanic: thieves that steal and give it back, creatures that split, the
Hellmouth posing as the down stair (and never soft-locking the floor), exact
pack sizes, a mini-boss with an escort, heart-weighing, fearless and
quarrelsome monsters, a blow worse on a sleeper, and the see-invisible potion.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()
_SCREEN = None

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)

import late_game_monsters_2026_10 as PASS  # noqa: E402

NEW = tuple(PASS.NEW)
# Part 2, the deep set (after re-running the band analysis).
DEEP_SET = ('bronze_sentinel', 'sown_warrior', 'takshaka_brood', 'rakshasa_illusionist',
            'ushabti_overseer', 'sekhmet_lioness', 'ammit_devourer', 'mazandaran_div',
            'dahaka_wyrm', 'galla_demon', 'girtablilu', 'asag_stone_warrior',
            'totentanz_dancer', 'mara', 'lyssa_madness', 'jorogumo')
MINIONS = ('ushabti_worker', 'khrafstra_swarm')
NAMED = ('stheno_gorgon', 'euryale_gorgon')


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=7):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name='__test_late_game__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _open_spot(g, half=4):
    from dungeon import FLOOR
    for y in range(half + 1, g.dungeon.height - half - 1):
        for x in range(half + 1, g.dungeon.width - half - 1):
            if all(g.dungeon.is_walkable(x + i, y + j)
                   for i in range(-half, half + 1) for j in range(-half, half + 1)):
                return x, y
    x = min(max(g.player.x, half + 1), g.dungeon.width - half - 2)
    y = min(max(g.player.y, half + 1), g.dungeon.height - half - 2)
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    return x, y


def _monster(mid, x=0, y=0):
    from monster import Monster
    return Monster({**MONS[mid], 'id': mid}, x, y)


def _scene(mid, dx=1, dy=0, seed=7):
    g = _game(seed)
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    m = _monster(mid, x + dx, y + dy)
    g.monsters = [m]
    g._refresh_fov()
    g.visible |= {(x + i, y + j) for i in range(-4, 5) for j in range(-4, 5)}
    return g, m


def _messages(g, n=15):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


# =============================================================================
# Data
# =============================================================================

def test_every_new_monster_has_lore_size_and_its_painted_sprite():
    with open(os.path.join(ROOT, 'data', 'monster_sizes.json'), encoding='utf-8') as f:
        sizes = json.load(f)['sizes']
    for mid in NEW:
        d = MONS[mid]
        assert len(d.get('lore', '')) >= 250, mid
        assert sizes.get(mid) in ('tiny', 'small', 'medium', 'large', 'huge'), mid
        path = os.path.join(ROOT, 'assets', 'tiles', 'monsters', f'{mid}.png')
        assert os.path.exists(path), mid
        img = pygame.image.load(path)
        assert img.get_size() == (64, 64), mid


def test_the_pass_script_is_idempotent_on_the_shipped_data():
    data = json.loads(json.dumps(MONS))
    assert PASS.apply(data) == []


def test_random_spawns_sit_on_the_floor_their_hp_was_built_for():
    from respawn_by_hp import plan, is_random_spawn
    placed = plan(MONS)
    for mid in NEW:
        d = MONS[mid]
        if is_random_spawn(d):
            assert placed[mid] == (d['peak_floor'], d['spread'], d['min_level']), mid


def test_deep_set_lives_on_floors_61_to_100_and_spawns_from_the_pool():
    import dungeon
    for mid in DEEP_SET + ('ker', 'hellmouth', 'mere_wife', 'endor_medium', 'erinyes_greater',
                           'tiamat_blood', 'hels_handmaid', 'gashadokuro', 'autolycus_heir'):
        d = MONS[mid]
        assert 61 <= d['peak_floor'] <= 99, mid
        assert d['peak_weight'] > 0 and not d.get('is_mini_boss'), mid
        assert mid in dungeon._build_spawn_pool(d['peak_floor']), mid


def test_minions_and_named_pair_never_come_from_the_random_pool():
    for mid in MINIONS + NAMED:
        assert MONS[mid]['peak_weight'] == 0, mid
    assert MONS['ushabti_overseer']['summon_kind'] == 'ushabti_worker'
    assert MONS['dahaka_wyrm']['splits']['into'] == 'khrafstra_swarm'
    assert MONS['stheno_gorgon']['is_mini_boss'] and MONS['stheno_gorgon']['spawn_chance'] > 0
    assert MONS['euryale_gorgon']['spawn_chance'] == 0          # only beside Stheno
    assert MONS['stheno_gorgon']['escort'] == ['euryale_gorgon']


def test_the_five_deep_regulars_carry_their_lore_statuses():
    def effects(mid):
        return {a.get('effect') for a in MONS[mid]['attacks'] if a.get('effect')}
    assert {'poisoned', 'blinded'} <= effects('wormwood_blight')
    assert {'silenced', 'teleportitis'} <= effects('void_seraph')
    assert MONS['iron_horseman']['can_charge'] and 'stunned' in effects('iron_horseman')
    assert 'feared' in effects('apocalypse_herald')
    assert 'bleeding' in effects('pit_executioner')


def test_thieves_now_have_a_stealing_blow():
    for mid in ('bandit_thief', 'leprechaun', 'leprechaun_hostile', 'ethereal_filcher', 'autolycus_heir'):
        assert any(a.get('steal') for a in MONS[mid]['attacks']), mid
    assert MONS['leprechaun']['after_theft'] == 'teleport'


def test_deep_bands_have_healthy_variety_after_the_pass():
    """The audit's measure: effective faces were 27 (81-90) and 17 (91-100)."""
    import monster_catalog_bands as mcb
    rows = {r['band']: r for r in mcb.bands(MONS)}
    assert rows['61-70']['eff'] >= 48
    assert rows['71-80']['eff'] >= 50
    assert rows['81-90']['eff'] >= 42
    assert rows['91-100']['eff'] >= 32
    for band in ('81-90', '91-100'):
        r = rows[band]
        # no longer two patterns: something besides aggressive/ranged is >=8%
        assert 1 - r['pat']['aggressive'] - r['pat']['ranged'] >= 0.08, band
        assert r['tr']['stealth'] >= 0.03 and r['tr']['summon'] >= 0.02, band
        assert r['tr']['swarm'] >= 0.10 and r['tr']['st:silence'] > 0.02, band
        assert r['top3'] <= 0.20, band


def test_see_invisible_potion_is_in_the_ordinary_pool_from_floor_21():
    with open(os.path.join(ROOT, 'data', 'items', 'potion.json'), encoding='utf-8') as f:
        pots = json.load(f)
    p = pots['potion_of_see_invisible']
    assert p['effect'] == 'see_invisible'
    assert p['floorSpawnWeight']['1-20'] == 0 and p['floorSpawnWeight']['21-40'] > 0
    names = [v['unidentified_name'] for v in pots.values()]
    assert names.count(p['unidentified_name']) == 1
    assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', 'potion_of_see_invisible.png'))


def test_drinking_see_invisible_reveals_an_invisible_monster():
    import unseen
    from food_system import drink_potion
    from items import Potion
    g, m = _scene('air_elemental', dx=2)
    assert unseen.unseen(m, g.player)
    pot = Potion({**json.load(open(os.path.join(ROOT, 'data', 'items', 'potion.json'),
                                   encoding='utf-8'))['potion_of_see_invisible'],
                  'id': 'potion_of_see_invisible'})
    drink_potion(g.player, pot)
    assert g.player.has_effect('see_invisible')
    assert not unseen.unseen(m, g.player)


def test_poltergeist_and_air_elemental_are_invisible_by_lore():
    import unseen
    from player import Player
    p = Player()
    for mid in ('poltergeist', 'air_elemental'):
        assert unseen.unseen(_monster(mid), p), mid


# =============================================================================
# Stealing
# =============================================================================

def _always_steal(m, kind):
    m.attacks = [{'name': 'Cut Purse', 'damage': '1d2', 'type': 'slash', 'steal': kind, 'steal_chance': 1.0}]
    m.thac0 = -60


def _until_stolen(g, m, turns=40):
    import theft
    for _ in range(turns):
        g._do_monster_turns()
        if theft.has_loot(m):
            return True
        g.player.hp = g.player.max_hp
    return False


def test_a_thief_cuts_the_purse_and_the_gold_comes_back_when_it_dies():
    g, m = _scene('bandit_thief')
    m._aware = True
    m.ai_pattern = 'aggressive'
    _always_steal(m, 'gold')
    g.player_gold = 1000
    assert _until_stolen(g, m)
    taken = m.stolen_gold
    assert 0 < taken <= 300 and g.player_gold == 1000 - taken
    assert any('makes off with' in s for s in _messages(g))
    m.hp = 0
    m.alive = False
    g._on_monster_killed(m)
    from items import GoldPile
    piles = [it for it in g.ground_items if isinstance(it, GoldPile) and (it.x, it.y) == (m.x, m.y)]
    assert sum(p.amount for p in piles) >= taken
    assert m.stolen_gold == 0


def test_a_filcher_takes_one_unworn_item_never_worn_gear_or_quest_pieces():
    import theft
    from items import scripted_only_ids
    g, m = _scene('ethereal_filcher')
    worn = set(id(i) for i in g.player.worn_items())
    loot = theft.stealable(g.player)
    assert loot, 'starting kit has something unworn'
    assert all(id(i) not in worn and getattr(i, 'id', '') not in scripted_only_ids() for i in loot)
    before = len(g.player.inventory)
    msg = theft.steal(g, m, 'item', rng=random.Random(3))
    assert 'snatches your' in msg
    got = theft.carried(m)
    assert len(got) == 1 and id(got[0]) not in worn
    # One haul: a thief carrying loot takes nothing more.
    assert theft.steal(g, m, 'item') == ''
    m.alive = False
    m.hp = 0
    g._on_monster_killed(m)
    assert got[0] in g.ground_items and (got[0].x, got[0].y) == (m.x, m.y)
    assert len(g.player.inventory) <= before


def test_worn_gear_is_never_stolen_even_when_nothing_else_is_carried():
    import theft
    g, m = _scene('ethereal_filcher')
    g.player.inventory = [i for i in g.player.inventory if i in g.player.worn_items()]
    assert theft.steal(g, m, 'item') == ''
    assert not theft.has_loot(m)


def test_a_thief_with_its_haul_runs_from_the_hero():
    import theft
    g, m = _scene('bandit_thief', dx=1)
    g.player_gold = 500
    theft.steal(g, m, 'gold', rng=random.Random(1))
    d0 = max(abs(m.x - g.player.x), abs(m.y - g.player.y))
    for _ in range(4):
        m.take_turn(g.player, g.dungeon, g.monsters)
    assert max(abs(m.x - g.player.x), abs(m.y - g.player.y)) > d0


def test_a_leprechaun_vanishes_to_a_far_part_of_the_same_floor_with_the_gold():
    import theft
    g, m = _scene('leprechaun', dx=1)
    g.player_gold = 800
    msg = theft.steal(g, m, 'gold', rng=random.Random(2))
    assert 'somewhere else on this floor' in msg
    assert max(abs(m.x - g.player.x), abs(m.y - g.player.y)) >= theft.TELEPORT_MIN_DISTANCE
    assert g.dungeon.is_walkable(m.x, m.y) and m in g.monsters and m.stolen_gold > 0


# =============================================================================
# Splitting
# =============================================================================

def test_blood_of_tiamat_splits_under_a_small_cut_and_not_under_a_great_blow():
    import splitting
    g, m = _scene('tiamat_blood', dx=1)
    hp0 = m.hp
    m.take_damage(50)                      # far under a tenth of its health
    assert m._pending_splits == 1
    splitting.spawn_pending(g)
    kids = [o for o in g.monsters if o is not m and o.kind == 'tiamat_blood']
    assert len(kids) == 1
    assert kids[0].hp + m.hp == hp0 - 50 and kids[0]._aware
    assert any('splits in two' in s for s in _messages(g))
    m.take_damage(int(0.2 * hp0))          # a great blow: no split
    assert m._pending_splits == 0


def test_a_bleeding_wound_never_splits_it_and_the_line_has_a_cap():
    import splitting
    g, m = _scene('tiamat_blood', dx=1)
    m.add_effect('bleeding', 5)
    m.tick_effects()
    assert m._pending_splits == 0
    for _ in range(30):
        m.take_damage(5)
        splitting.spawn_pending(g)
    family = [o for o in g.monsters if o.kind == 'tiamat_blood']
    assert len(family) == 1 + MONS['tiamat_blood']['splits']['max']


def test_black_pudding_splits_under_an_axe_and_lightning_not_a_mace_or_a_thrusting_sword():
    import splitting
    from combat import blow_forms_of
    from types import SimpleNamespace as NS
    axe = NS(damage_types=['slash', 'iron'])
    sword = NS(damage_types=['slash', 'pierce', 'steel'])
    mace = NS(damage_types=['blunt'])
    assert blow_forms_of(axe) == ('slash',)
    assert blow_forms_of(None) == ('blunt',)
    g, m = _scene('black_pudding', dx=1)
    m.max_hp = m.hp = 500
    for weapon, splits in ((mace, 0), (sword, 0), (axe, 1)):
        m._incoming_forms = blow_forms_of(weapon)
        m.take_damage(3)
        assert m._pending_splits == splits, weapon
        m._pending_splits = 0
    m.take_damage(3, 'lightning')
    assert m._pending_splits == 1
    splitting.spawn_pending(g)
    assert sum(o.kind == 'black_pudding' for o in g.monsters) == 2


def test_a_dahaka_wyrm_lets_out_vermin_from_a_blade_wound_and_keeps_its_health():
    import splitting
    g, m = _scene('dahaka_wyrm', dx=1)
    m._incoming_forms = ('pierce',)
    m.take_damage(40)
    hp = m.hp
    splitting.spawn_pending(g)
    vermin = [o for o in g.monsters if o.kind == 'khrafstra_swarm']
    assert len(vermin) == 1 and m.hp == hp
    m._incoming_forms = ('blunt',)
    m.take_damage(40)
    assert m._pending_splits == 0


def test_splits_appear_at_the_end_of_the_heros_action():
    g, m = _scene('tiamat_blood', dx=1)
    m.take_damage(30)
    g._advance_turn()
    assert sum(o.kind == 'tiamat_blood' for o in g.monsters) == 2


# =============================================================================
# The Hellmouth: a false down stair that never soft-locks the floor
# =============================================================================

def _hellmouth_floor(level, seed):
    import dungeon as dmod
    import false_stairs
    random.seed(seed)
    d = dmod.generate_dungeon(80, 50, level)
    up, down = false_stairs.stairs(d)
    return d, up, down


def _check_seated(d, up, down, hm):
    import false_stairs
    from dungeon import FLOOR
    assert d.tiles[hm.y][hm.x] == FLOOR
    assert (hm.x, hm.y) not in (up, down)
    assert max(abs(hm.x - down[0]), abs(hm.y - down[1])) >= false_stairs.MIN_STAIR_DISTANCE
    reach = false_stairs._walk(d, up or down, blocked={(hm.x, hm.y)})
    assert down in reach
    assert (hm.x, hm.y) in false_stairs._walk(d, up or down)


def test_hellmouth_is_never_set_on_a_stair_or_where_it_cuts_off_the_real_one():
    import false_stairs
    seated = 0
    for seed in range(24):
        d, up, down = _hellmouth_floor(88, seed)
        if down is None:
            continue
        # Try to put it on the real stair, then on every chokepoint tile
        # next to the stair: seat() must move it somewhere safe.
        hm = _monster('hellmouth', *down)
        mons = [hm]
        false_stairs.seat(d, mons, rng=random.Random(seed))
        if hm in mons:
            _check_seated(d, up, down, hm)
            seated += 1
    assert seated >= 18


def test_one_hellmouth_per_floor_at_most():
    import false_stairs
    d, up, down = _hellmouth_floor(90, 5)
    mons = [_monster('hellmouth', 1, 1) for _ in range(3)]
    removed = false_stairs.seat(d, mons)
    assert len(mons) == false_stairs.MAX_PER_FLOOR and len(removed) == 2


def test_a_hellmouth_in_a_corridor_bottleneck_is_moved_off_it():
    import false_stairs
    from dungeon import WALL, FLOOR
    # Find a floor with a tile whose blocking cuts the up stair off from the
    # down stair. (The layout for one seed varies with Python's hash order, and
    # some layouts have no such tile, so look through a few seeds.)
    choke = None
    for seed in range(9, 40):
        d, up, down = _hellmouth_floor(90, seed)
        reach = false_stairs._walk(d, up)
        choke = next((t for t in sorted(reach)
                      if d.tiles[t[1]][t[0]] == FLOOR and t not in (up, down)
                      and down not in false_stairs._walk(d, up, blocked={t})), None)
        if choke:
            break
    assert choke, 'no floor with a chokepoint between the stairs'
    hm = _monster('hellmouth', *choke)
    mons = [hm]
    false_stairs.seat(d, mons)
    assert hm not in mons or (hm.x, hm.y) != choke
    if hm in mons:
        _check_seated(d, up, down, hm)


def test_real_generated_deep_floors_keep_the_way_down_open(monkeypatch):
    """Through the real LevelManager, with the Hellmouth made the commonest
    thing in the pool: at most one per floor, every one seated safely."""
    import dungeon as dmod
    import false_stairs
    import level_manager
    real_pool = dmod._build_spawn_pool

    def flooded(level):
        pool = real_pool(level)
        if 'hellmouth' in pool:
            pool['hellmouth']['_spawn_freq'] = 500.0
        return pool
    monkeypatch.setattr(dmod, '_build_spawn_pool', flooded)
    found = 0
    for seed in range(10):
        random.seed(1000 + seed)
        lm = level_manager.LevelManager()
        lvl = 86 + seed
        if lvl in level_manager._BOSS_LEVELS:
            continue
        d, mons, _items = lm.generate(lvl)
        up, down = false_stairs.stairs(d)
        assert down is not None
        fakes = [m for m in mons if m.kind == 'hellmouth']
        assert len(fakes) <= false_stairs.MAX_PER_FLOOR
        for hm in fakes:
            found += 1
            _check_seated(d, up, down, hm)
    assert found >= 6


def test_hellmouth_is_drawn_as_the_down_stair_and_looks_like_one():
    import unseen
    g, m = _scene('hellmouth', dx=3)
    disg = unseen.disguise(m)
    assert disg and disg['tile'] == 'stairs_down'
    calls = []
    real = g.renderer.draw_disguise

    def spy(x, y, item_id=None, visible=None, tile=None):
        calls.append((x, y, item_id, tile))
        return real(x, y, item_id, visible, tile=tile)
    g.renderer.draw_disguise = spy
    try:
        g.render()
    finally:
        g.renderer.draw_disguise = real
    assert (m.x, m.y, None, 'stairs_down') in calls
    assert not g._sees_monster(m)
    g.target_cursor_x, g.target_cursor_y = m.x, m.y
    g._observe_targeting = True
    g._confirm_observe()
    said = ' '.join(_messages(g))
    assert 'staircase leading down' in said and 'Hellmouth' not in said


def test_hellmouth_springs_when_the_hero_steps_beside_it():
    import unseen
    g, m = _scene('hellmouth', dx=1)
    # (speed 5: a slow thing may lose a turn before it bites)
    assert any(m.take_turn(g.player, g.dungeon, g.monsters) for _ in range(12))
    assert m._aware and m.ai_pattern == 'aggressive' and m._mimic_surprise
    assert unseen.disguise(m) is None


# =============================================================================
# Packs, escorts, and the other new rules
# =============================================================================

def test_pack_size_fixes_the_number_of_a_lore_pack():
    import dungeon as dmod
    random.seed(4)
    d = dmod.generate_dungeon(80, 50, 90)
    rooms = sorted(d.rooms[1:], key=lambda r: -(r.width * r.height))
    for mid, lo, hi in (('ker', 3, 5), ('erinyes_greater', 3, 3), ('girtablilu', 2, 2),
                        ('galla_demon', 4, 6), ('strix', 3, 3)):
        sizes = set()
        for trial in range(12):
            mons = []
            dmod._spawn_one_in_room(rooms[0], {mid: {**MONS[mid], '_spawn_freq': 1.0}}, d, mons,
                                    random.Random(trial))
            sizes.add(len(mons))
        assert sizes and min(sizes) >= lo and max(sizes) <= hi, (mid, sizes)


def test_stheno_arrives_with_euryale_beside_her_once_per_run():
    import dungeon as dmod
    import level_manager
    random.seed(2)
    lm = level_manager.LevelManager()
    d = dmod.generate_dungeon(80, 50, 67)
    lm._planned_mini_bosses = {67: 'stheno_gorgon'}
    mons = []
    lm._try_spawn_mini_boss(d, mons, 67)
    kinds = [m.kind for m in mons]
    assert kinds.count('stheno_gorgon') == 1 and kinds.count('euryale_gorgon') == 1
    st, eu = (next(m for m in mons if m.kind == k) for k in ('stheno_gorgon', 'euryale_gorgon'))
    assert max(abs(st.x - eu.x), abs(st.y - eu.y)) <= 3
    assert {'stheno_gorgon', 'euryale_gorgon'} <= lm._placed_mini_bosses
    lm._try_spawn_mini_boss(d, mons, 67)
    assert len(mons) == 2


@pytest.mark.parametrize('mid', NAMED)
def test_the_gorgon_sisters_are_immortal_once(mid):
    m = _monster(mid)
    m.take_damage(m.hp)
    assert m.alive and m.hp > 0
    m.take_damage(m.hp)
    assert not m.alive


def _gazes_per_turn(monkeypatch, group=True, turns=40):
    """Run the real monster phase with both sisters in sight and count the
    paralysing gazes that land each turn. The hero is freed before every turn
    and every gaze is let through, so only the shared cooldown can stop a
    second one."""
    import status_effects
    g, st = _scene('stheno_gorgon', dx=3)
    eu = _monster('euryale_gorgon', g.player.x - 3, g.player.y)
    g.monsters = [st, eu]
    for m in g.monsters:
        m.hp = m.max_hp = 10 ** 7
        if not group:
            m.gaze_group = ''
    g.player.hp = g.player.max_hp = 10 ** 7
    landed = []
    monkeypatch.setattr(status_effects, 'apply_debuff_with_save',
                        lambda p, eff, dur, dc: (landed.append(eff) or True, ''))
    counts = []
    for _ in range(turns):
        for k in ('paralyzed', 'control_immune', 'feared'):
            g.player.status_effects.pop(k, None)
        for m in g.monsters:
            m.status_effects.pop('paralyzed', None)
        landed.clear()
        g._do_monster_turns()
        counts.append(landed.count('paralyzed'))
    return counts


def test_the_gorgon_sisters_share_one_gaze(monkeypatch):
    assert MONS['stheno_gorgon']['gaze_group'] == MONS['euryale_gorgon']['gaze_group'] == 'gorgon_sisters'
    # Toned down (2026-10-17): Euryale's gaze holds one turn, Stheno's two.
    assert 1 <= MONS['euryale_gorgon']['gaze_paralyze'] < MONS['stheno_gorgon']['gaze_paralyze'] <= 2
    counts = _gazes_per_turn(monkeypatch)
    assert max(counts) == 1, counts                 # never two in one turn
    assert sum(counts) >= 4, counts                 # but the gaze still comes
    # One shared cooldown: after a gaze, neither sister looks again for several turns.
    hits = [i for i, c in enumerate(counts) if c]
    assert min(b - a for a, b in zip(hits, hits[1:])) >= MONS['stheno_gorgon']['gaze_cooldown'] - 1


def test_without_the_shared_gaze_both_sisters_would_look_at_once(monkeypatch):
    # The control: the counter above can see a double gaze when there is one.
    assert max(_gazes_per_turn(monkeypatch, group=False)) == 2


def test_a_heart_weigher_bites_harder_on_a_heavy_heart():
    from types import SimpleNamespace as NS
    from monster import heart_weight
    p = NS(_combat_game_ref=NS(karma=-10))
    assert heart_weight(p) == pytest.approx(1.4)
    p._combat_game_ref.karma = 10
    assert heart_weight(p) == pytest.approx(0.6)
    p._combat_game_ref.karma = 0
    assert heart_weight(p) == pytest.approx(1.0)
    assert heart_weight(NS()) == pytest.approx(1.0)       # the simulator: no game
    assert MONS['ammit_devourer']['weighs_heart']


def _blow(g, m, atk, monkeypatch):
    import monster as mon
    monkeypatch.setattr(mon.random, 'randint', lambda a, b: 20)       # a clean hit
    monkeypatch.setattr(mon.random, 'random', lambda: 0.99)           # no dodge/effects
    monkeypatch.setattr(mon, 'roll', lambda s: 100)
    g.player.hp = g.player.max_hp = 100000
    before = g.player.hp
    m._resolve_blow(atk, g.player)
    return before - g.player.hp


def test_heart_weighing_changes_the_real_blow(monkeypatch):
    g, m = _scene('ammit_devourer', dx=1)
    g.player._combat_game_ref = g
    atk = MONS['ammit_devourer']['attacks'][0]
    g.karma = 0
    even = _blow(g, m, atk, monkeypatch)
    g.karma = -10
    heavy = _blow(g, m, atk, monkeypatch)
    g.karma = 10
    light = _blow(g, m, atk, monkeypatch)
    assert heavy > even > light


def test_the_mara_tramples_a_sleeper_harder(monkeypatch):
    g, m = _scene('mara', dx=1)
    trample = MONS['mara']['attacks'][1]
    awake = _blow(g, m, trample, monkeypatch)
    g.player.status_effects['sleeping'] = 3
    asleep = _blow(g, m, trample, monkeypatch)
    assert asleep >= int(awake * 1.4)


def test_galla_never_flee_and_cannot_be_frightened():
    g, m = _scene('galla_demon', dx=3)
    m._aware = True
    m.hp = 1
    m.add_effect('feared', 5)
    m.take_turn(g.player, g.dungeon, g.monsters)
    assert m._flee_timer == 0 and not m.has_effect('feared')


def test_confused_sown_men_strike_each_other():
    g, m = _scene('sown_warrior', dx=2)
    brother = _monster('sown_warrior', m.x + 1, m.y)
    g.monsters.append(brother)
    hp = brother.hp
    m.status_effects['confused'] = 5
    m.take_turn(g.player, g.dungeon, g.monsters)
    assert brother.hp < hp


def test_something_thrown_into_the_sown_men_sets_them_quarrelling():
    import json as _json
    from items import Potion
    g, m = _scene('sown_warrior', dx=2)
    pots = _json.load(open(os.path.join(ROOT, 'data', 'items', 'potion.json'), encoding='utf-8'))
    pot = Potion({**pots['potion_of_healing'], 'id': 'potion_of_healing'})
    g.player.inventory.append(pot)
    g._throw_potion = pot
    g._throw_targeting = True
    g.target_cursor_x, g.target_cursor_y = m.x, m.y
    g._confirm_throw_target()
    assert m.has_effect('confused')
