"""Packs (src/packs.py, data/packs.json; Brandon 2026-11-18: "add packs that
fight 2+ at a time, the more diverse and unique our monsters are, the
better"; the design he approved 2026-11-19; and "rats swarm could add damage
based on how many rats are adjacent to the player; build it").

In the open a pack spreads round the hero; where only one of them could
reach him they hold the mouth or go round (rats press on); one that finds
him rouses the rest; and each family has its own trick: rats swarm, wolves
hamstring, jackals dart in and out, hyenas and gnolls harry the wounded,
goblins sling then charge, kobolds lay traps as they back away, ghouls feed
on a held hero, harpies snatch food, hounds bay and keep the scent.
"""
from __future__ import annotations

import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PQ_NO_BONES', '1')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import monster as monster_mod  # noqa: E402
import packs  # noqa: E402
from dungeon import FLOOR, WALL  # noqa: E402


def _json(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


MONS = _json('monsters.json')
PACKS = _json('packs.json')
NEW_KINDS = ('jackal', 'wolf', 'cave_hyena')


# --------------------------------------------------------------------- data

def test_every_pack_kind_is_a_pack_with_its_size():
    for pid, p in PACKS['packs'].items():
        assert p['kinds'] and p['tricks'] and p.get('why'), pid
        assert p.get('corridor', 'hold') in ('hold', 'press'), pid
        for kind in p['kinds']:
            m = MONS[kind]
            assert m.get('pack') is True, kind
            lo, hi = m['pack_size']
            assert 2 <= lo <= hi, kind
        for t in p['tricks']:
            assert t in PACKS['tricks'], (pid, t)


def test_every_pack_monster_is_a_hunting_pack_or_a_herd_with_a_reason():
    """Every kind set down in a group is either in a hunting pack (and has a
    trick) or listed among the herds with the reason it does not hunt as one,
    and in only one place."""
    hunting = [k for p in PACKS['packs'].values() for k in p['kinds']]
    herds = [k for g in PACKS['herds']['groups'] for k in g['kinds']]
    assert all(g['why'] for g in PACKS['herds']['groups'])
    both = hunting + herds
    assert len(both) == len(set(both))
    in_groups = {k for k, v in MONS.items() if isinstance(v, dict) and v.get('pack') and v.get('pack_size')}
    assert in_groups == set(both), sorted(in_groups ^ set(both))


def test_every_trick_has_a_tell_and_the_tells_are_plain():
    tells = _json('tells.json')
    for tid in PACKS['tricks']:
        key = f'pack_{tid}'
        assert key in tells['order'], key
        e = tells['effects'][key]
        assert e['sign'] and e['does'] and e['counter'], key
        for part in (e['sign'], e['does'], e['counter']):
            assert '%' not in part and '(double' not in part, (key, part)


def test_the_family_tricks_from_the_design_are_there():
    want = {'rats': 'swarm', 'wolves': 'hamstring', 'goblins': 'sling', 'kobolds': 'traps',
            'ghouls': 'feast', 'hyenas': 'harry', 'jackals': 'dart', 'harpies': 'snatch',
            'hounds': 'bay'}
    for pid, t in want.items():
        assert t in PACKS['packs'][pid]['tricks'], pid
    # The hamstring keeps within the engine's limit for a slow.
    from status_effects import CONTROL_CAP
    assert PACKS['tricks']['hamstring']['turns'] <= CONTROL_CAP['slowed']


def test_goblins_carry_the_sling_their_trick_throws():
    g = MONS['goblin']
    sling = [a for a in g['attacks'] if a.get('ranged')]
    assert sling and sling[0]['delivery'] == 'ranged' and sling[0]['name'] == 'Sling Stone'
    assert any(not a.get('ranged') for a in g['attacks'])        # the knife, beside him


# ------------------------------------------------------------- new kinds

def test_the_new_kinds_are_written_by_lore_for_their_floors():
    j, w, h = MONS['jackal'], MONS['wolf'], MONS['cave_hyena']
    # Jackals shallow and wolves on floors about 4-10, in tier 1; the cave
    # hyena of the Ice Age dens in tier 2 (the tier census holds tier 1's
    # ordinary kinds to 35%, and two new ones were all it had room for).
    assert j['peak_floor'] <= 3 and j['min_level'] == 1
    assert 4 <= w['min_level'] <= w['peak_floor'] <= 10
    assert 21 <= h['peak_floor'] <= 26 and h['min_level'] >= 16
    for k in NEW_KINDS:
        m = MONS[k]
        assert m['pack'] and m['pack_size'] and m['family'] == 'great_beasts', k
        assert m['pronoun'] == 'it', k
        assert m['harvest_tier'] == (m['peak_floor'] - 1) // 20 + 1, k
        assert len(m['lore']) > 300, k
        assert m['treasure'].get('purse') == 'none', k         # a beast has no purse
    assert w['opener'] == {'attack': 'Bite', 'range': 1}       # wolves lunge
    assert j['speed'] >= 14 and w['speed'] >= 14                 # fast, by lore


def test_the_new_kinds_are_wired_into_every_system():
    sizes = _json('monster_sizes.json')['sizes']
    hmap = _json('items', 'harvest_map.json')['monsters']
    ings = _json('items', 'ingredient.json')
    senses = _json('senses.json')['monsters']
    with open(os.path.join(ROOT, 'tools', 'content', 'genart', 'installed.json'), encoding='utf-8') as f:
        installed = set(json.load(f))
    import dungeon
    import family_lore
    import tells
    for k in NEW_KINDS:
        assert sizes[k] in ('small', 'medium', 'large'), k
        assert hmap[k] in ings, k                                    # harvest: a kin cut
        assert senses[k] == ['scent'], k
        assert family_lore.family_of(k) == 'great_beasts', k
        path = os.path.join(ROOT, 'assets', 'tiles', 'monsters', f'{k}.png')
        assert os.path.exists(path) and k in installed, k
        assert k in dungeon._build_spawn_pool(MONS[k]['peak_floor']), k
        m = monster_mod.Monster({**MONS[k], 'id': k}, 0, 0)
        assert tells.abilities(m), k                                  # its pack's trick is told
    assert hmap['wolf'] == hmap['wolf_pack_leader'] == hmap['jackal']
    assert hmap['cave_hyena'] == hmap['gnoll']


# ------------------------------------------------------------ pure numbers

def test_swarm_bonus_grows_with_each_rat_and_stops_at_its_cap():
    s = PACKS['tricks']['swarm']
    per, cap = s['per_other'], s['cap']
    assert packs.swarm_bonus(0, per, cap) == 0.0
    assert packs.swarm_bonus(1, per, cap) == per
    assert packs.swarm_bonus(2, per, cap) == 2 * per
    assert packs.swarm_bonus(9, per, cap) == cap
    assert packs.swarm_bonus(2, 0.5, 1.5) < packs.swarm_bonus(3, 0.5, 1.5) == packs.swarm_bonus(4, 0.5, 1.5)


def test_choose_spot_takes_the_far_side_and_wolves_the_back():
    class _P:
        x, y = 5, 5
        _facing_dx, _facing_dy = 1, 0
    p = _P()
    cands = {t: [t] for t in packs.ring(5, 5)}
    # A packmate on the hero's east side: the next one comes from the west.
    spot = packs.choose_spot(p, cands, [(6, 5)])
    assert spot[0] == 4
    # Facing east, the hero's back is west; a wolf heads for it even with
    # no packmate on him yet.
    assert packs.choose_spot(p, cands, [], circle=True, back=packs.back_tile(p, [])) == (4, 5)


class _Map:
    """A small hand-made floor: '#' rock, anything else floor."""
    fixture_blocks = frozenset()
    fixture_opaque = frozenset()

    def __init__(self, rows):
        self.tiles = [[WALL if c == '#' else FLOOR for c in r] for r in rows]
        self.height, self.width = len(rows), len(rows[0])
        self.traps = {}

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and self.tiles[y][x] == FLOOR

    def is_opaque(self, x, y):
        return not self.is_walkable(x, y)

    def open_door(self, x, y):
        return False


class _Hero:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.hp = self.max_hp = 50
        self.status_effects = {}

    def has_effect(self, e):
        return self.status_effects.get(e, 0) > 0


ROOM_AND_CORRIDOR = [
    "##############",
    "#.....########",
    "#.....########",
    "#.............",
    "#.....########",
    "#.....########",
    "##############",
]


def _beast(kind, x, y):
    m = monster_mod.Monster({**MONS[kind], 'id': kind}, x, y)
    m._aware = m._tracking = True
    return m


def test_a_corridor_is_a_choke_and_the_open_is_not():
    d = _Map(ROOM_AND_CORRIDOR)
    w = _beast('wolf', 3, 3)
    hero = _Hero(8, 3)                                  # in the corridor
    s = packs.slots(w, hero, d, [w])
    assert s == {(7, 3)} and packs.choke(s)
    hero = _Hero(4, 3)                                  # in the room
    s = packs.slots(_beast('wolf', 2, 2), hero, d, [])
    assert len(s) >= 5 and not packs.choke(s)


def test_wolves_hold_the_mouth_out_of_sight_rather_than_file_in():
    d = _Map(ROOM_AND_CORRIDOR)
    hero = _Hero(8, 3)
    front = _beast('wolf', 7, 3)                        # already on him
    a, b = _beast('wolf', 4, 3), _beast('wolf', 4, 2)
    pack = [front, a, b]
    for m in (a, b):
        got = packs.hunt_turn(m, hero, d, pack)
        assert got == 'held', got
        assert not m._adjacent_to(hero)
    # They wait beside the mouth, where the hero cannot see them.
    import senses
    assert any(not senses.clear_view(m.x, m.y, hero.x, hero.y, d) for m in (a, b))


def test_a_rat_pack_presses_into_a_corridor_anyway():
    d = _Map(ROOM_AND_CORRIDOR)
    hero = _Hero(8, 3)
    front = _beast('giant_rat', 7, 3)
    rat = _beast('giant_rat', 5, 3)
    assert packs.hunt_turn(rat, hero, d, [front, rat]) is None     # comes on as vermin do


def test_a_pack_goes_round_when_there_is_another_way():
    rows = [
        "###########",
        "#.........#",
        "#.#######.#",
        "#.#######.#",
        "#.........#",
        "###########",
    ]
    d = _Map(rows)
    hero = _Hero(5, 1)                                  # in the top passage
    front = _beast('wolf', 4, 1)                        # on him from the west
    other = _beast('wolf', 2, 1)
    start = (other.x, other.y)
    got = packs.hunt_turn(other, hero, d, [front, other])
    assert got == 'moved'
    assert (other.x, other.y) != start and other.y > 1  # it went down, to come round
    assert other.__dict__['_pack_round']['path']


def test_patience_runs_out_and_one_tries_his_luck():
    d = _Map(ROOM_AND_CORRIDOR)
    hero = _Hero(9, 3)
    a, b = _beast('wolf', 4, 2), _beast('wolf', 4, 4)
    pack = [a, b]
    results = [packs.hunt_turn(a, hero, d, pack) for _ in range(int(PACKS['tactics']['patience']) + 2)]
    assert results[0] == 'held'
    assert None in results                              # one of them comes on in the end


# ------------------------------------------------------------- in the game

_SCREEN = None


def _game(seed=11):
    global _SCREEN
    from main import Game
    from game_states import STATE_PLAYER
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    random.seed(seed)
    g = Game(_SCREEN, player_name='__test_packs__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _carve(g, rows, ox=3, oy=3):
    """Lay a hand-made map into the game's floor; returns its origin."""
    t = g.dungeon.tiles
    for y in range(g.dungeon.height):
        for x in range(g.dungeon.width):
            t[y][x] = WALL
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c != '#':
                t[oy + j][ox + i] = FLOOR
    g.dungeon.fixture_blocks = frozenset()
    g.dungeon.fixture_opaque = frozenset()
    return ox, oy


OPEN = ["#############",
        "#...........#",
        "#...........#",
        "#...........#",
        "#...........#",
        "#...........#",
        "#...........#",
        "#############"]


def _put(g, kind, x, y):
    m = monster_mod.Monster({**MONS[kind], 'id': kind}, x, y)
    m._aware = True
    m._alerted = True
    g.monsters.append(m)
    return m


def test_a_rat_pack_spreads_round_the_hero_and_the_swarm_bites_deeper():
    g = _game()
    ox, oy = _carve(g, OPEN)
    hx, hy = ox + 6, oy + 4
    g.player.x, g.player.y = hx, hy
    rats = [_put(g, 'giant_rat', ox + 1, oy + 1 + i) for i in range(4)]
    for _ in range(8):
        for r in rats:
            r.take_turn(g.player, g.dungeon, g.monsters)
    on_him = [r for r in rats if r._adjacent_to(g.player)]
    assert len(on_him) >= 3
    # On different sides of him, not piled on one.
    sides = {((r.x > hx) - (r.x < hx), (r.y > hy) - (r.y < hy)) for r in on_him}
    assert len(sides) == len(on_him)
    # A rat's bite with three others on the hero, against one alone.
    r = on_him[0]
    atk = r.attacks[0]
    r._cached_all_monsters = g.monsters
    mult, note = packs.blow_mult(r, g.player, atk, g.monsters)
    others = len(on_him) - 1
    assert mult == 1.0 + min(PACKS['tricks']['swarm']['cap'], others * PACKS['tricks']['swarm']['per_other'])
    assert 'rats are on you' in note
    alone, _ = packs.blow_mult(r, g.player, atk, [r])
    assert alone == 1.0


def test_wolves_hamstring_only_with_a_packmate_beside_the_hero():
    g = _game()
    ox, oy = _carve(g, OPEN)
    g.player.x, g.player.y = ox + 6, oy + 4
    w = _put(g, 'wolf', ox + 5, oy + 4)
    atk = w.attacks[0]
    # Alone on him: never hamstrung.
    random.seed(1)
    for _ in range(40):
        g.player.status_effects.pop('slowed', None)
        assert packs.after_blow(w, g.player, atk, 3, g.monsters) == ''
    assert not g.player.has_effect('slowed')
    # A packmate on his other side: the hamstring comes.
    _put(g, 'wolf', ox + 7, oy + 4)
    hits = 0
    for _ in range(60):
        g.player.status_effects.pop('slowed', None)
        g.player.status_effects.pop('control_immune', None)
        line = packs.after_blow(w, g.player, atk, 3, g.monsters)
        if line:
            assert 'hamstring' in line
            hits += 1
    assert hits > 0


def test_a_kobold_lays_a_trap_as_it_backs_away_and_does_not_set_it_off():
    g = _game()
    ox, oy = _carve(g, OPEN)
    g.player.x, g.player.y = ox + 6, oy + 4
    k = _put(g, 'kobold', ox + 5, oy + 4)
    _put(g, 'kobold', ox + 2, oy + 2)                    # a packmate near
    k.hp = max(1, k.max_hp // 3)                         # hurt: it falls back
    here = (k.x, k.y)
    got = k.take_turn(g.player, g.dungeon, g.monsters)
    assert got is False
    assert (k.x, k.y) != here and not k._adjacent_to(g.player)
    trap = g.dungeon.traps.get(here)
    assert trap is not None and trap['type'] in ('snare', 'caltrop')
    # The hero who saw it laid sees the trap.
    g._sees_monster = lambda mon: True
    g._pack_turn_after(k)
    assert trap['revealed']
    # And the hero who steps on it is caught.
    g.player.x, g.player.y = here
    before = dict(g.player.status_effects)
    random.seed(3)
    for _ in range(10):
        if g.dungeon.traps.get(here) is None:
            break
        g._check_floor_trap(*here)
    assert g.dungeon.traps.get(here) is None or before != g.player.status_effects


def test_a_kobold_den_is_set_down_with_its_traps():
    import dungeon as dg
    import random_streams
    rng = random_streams.own_stream()
    g = _game()
    ox, oy = _carve(g, OPEN)
    kobolds = [monster_mod.Monster({**MONS['kobold'], 'id': 'kobold'}, ox + 3 + i, oy + 3) for i in range(3)]
    # A pack that wanders in later in the run brings no den with it.
    packs.on_spawned(kobolds, g.dungeon, rng, pool=dg._build_spawn_pool(1), monsters=list(kobolds))
    assert not g.dungeon.traps
    g.dungeon._dens_open = True                          # the floor is being peopled
    laid = packs.on_spawned(kobolds, g.dungeon, rng, pool=dg._build_spawn_pool(1), monsters=list(kobolds))
    assert laid and all(m._pack == laid[0]._pack for m in laid)
    assert g.dungeon.traps and all(t['type'] in ('snare', 'caltrop') and not t['revealed']
                                   for t in g.dungeon.traps.values())


def test_a_real_floor_marks_its_packs_and_leaves_no_flag_behind():
    from level_manager import LevelManager
    marked = 0
    for floor in (1, 2, 3, 4, 6, 8):
        d, mons, _items = LevelManager().generate(floor)
        assert '_dens_open' not in d.__dict__
        marked += sum(1 for m in mons if packs.in_pack(m) and m.__dict__.get('_pack'))
    assert marked >= 2


def test_goblins_sling_from_range_then_charge_together():
    g = _game()
    ox, oy = _carve(g, OPEN)
    g.player.x, g.player.y = ox + 9, oy + 4
    a = _put(g, 'goblin', ox + 5, oy + 4)                # 4 tiles off, in sight
    b = _put(g, 'goblin', ox + 1, oy + 1)                # still far off
    _put(g, 'goblin', ox + 1, oy + 6)
    assert a.take_turn(g.player, g.dungeon, g.monsters) is True
    assert a.__dict__.get('_pack_blow', {}).get('name') == 'Sling Stone'
    assert (a.x, a.y) == (ox + 5, oy + 4)               # it kept its distance
    # Once enough of them are up, and each has thrown, they all rush in.
    c = g.monsters[2]
    b.x, b.y = ox + 6, oy + 2
    c.x, c.y = ox + 6, oy + 6
    for m in (b, c):
        assert m.take_turn(g.player, g.dungeon, g.monsters) is True     # a stone each
        assert m.__dict__.pop('_pack_blow')['name'] == 'Sling Stone'
    a.__dict__.pop('_pack_blow', None)
    a.take_turn(g.player, g.dungeon, g.monsters)
    assert all(m.__dict__.get('_charged') for m in g.monsters)
    assert 'rush you together' in a.__dict__.get('_pack_line', ('',))[0]
    # Beside him, a goblin uses his knife.
    a.x, a.y = g.player.x - 1, g.player.y
    assert a.take_turn(g.player, g.dungeon, g.monsters) is True
    assert not a.__dict__.get('_pack_blow', {}).get('ranged')


def test_a_jackal_darts_in_snaps_and_darts_out():
    g = _game()
    ox, oy = _carve(g, OPEN)
    g.player.x, g.player.y = ox + 6, oy + 4
    j = _put(g, 'jackal', ox + 4, oy + 4)                # two tiles off
    _put(g, 'jackal', ox + 3, oy + 2)
    assert j.take_turn(g.player, g.dungeon, g.monsters) is True     # in, and the bite now
    assert j._adjacent_to(g.player)
    assert j.take_turn(g.player, g.dungeon, g.monsters) is False    # and out again
    assert not j._adjacent_to(g.player)


def test_hyenas_bite_harder_at_a_wounded_hero():
    g = _game()
    h = _put(g, 'cave_hyena', 0, 0)
    _put(g, 'cave_hyena', 1, 1)
    g.player.hp = g.player.max_hp
    assert packs.blow_mult(h, g.player, h.attacks[0], g.monsters)[0] == 1.0
    g.player.hp = max(1, int(g.player.max_hp * 0.3))
    mult, note = packs.blow_mult(h, g.player, h.attacks[0], g.monsters)
    assert mult == PACKS['tricks']['harry']['mult'] and 'blood' in note


def test_ghouls_feed_on_a_held_hero():
    g = _game()
    gh = _put(g, 'ghoul', 0, 0)
    assert packs.blow_mult(gh, g.player, gh.attacks[1], g.monsters)[0] == 1.0
    g.player.status_effects['paralyzed'] = 3
    assert packs.blow_mult(gh, g.player, gh.attacks[1], g.monsters)[0] == PACKS['tricks']['feast']['mult']


def test_a_harpy_snatches_food_and_flies_off():
    g = _game()
    from items import Food, load_items
    foods = [i for i in load_items('food') if isinstance(i, Food)]
    g.player.inventory.append(foods[0])
    hp = _put(g, 'harpy', g.player.x + 1, g.player.y)
    rake = next(a for a in hp.attacks if a['name'] == 'Talon Rake')
    random.seed(2)
    for _ in range(30):
        packs.after_blow(hp, g.player, rake, 2, g.monsters)
        if hp.__dict__.get('_wants_steal'):
            break
    assert hp._wants_steal == 'food'
    import theft
    held = sum(getattr(i, 'quantity', 1) for i in g.player.inventory if isinstance(i, Food))
    msg = theft.steal(g, hp, 'food')
    assert msg and 'makes off with it' in msg
    assert sum(getattr(i, 'quantity', 1) for i in g.player.inventory if isinstance(i, Food)) == held - 1
    assert isinstance(theft.carried(hp)[0], Food)


def test_a_hound_that_finds_the_hero_bays_and_the_pack_keeps_his_scent():
    g = _game()
    ox, oy = _carve(g, OPEN)
    g.player.x, g.player.y = ox + 6, oy + 4
    a = _put(g, 'gravehound', ox + 3, oy + 4)
    b = monster_mod.Monster({**MONS['gravehound'], 'id': 'gravehound'}, ox + 1, oy + 1)
    g.monsters.append(b)
    n = packs.alarm(a, g.monsters, g.player.x, g.player.y, g.dungeon)
    assert n == 1 and b._alerted and b._scent_left > 0
    assert a.__dict__.get('_pack_line') and 'bays' in a._pack_line[0]
    g.player.x += 1
    packs.keep_scent(b, g.player)
    assert b._goal == (g.player.x, g.player.y)


def test_a_war_band_member_keeps_to_its_band():
    w = monster_mod.Monster({**MONS['goblin'], 'id': 'goblin'}, 0, 0)
    assert packs.in_pack(w)
    w._band = 'band@1,1'
    assert not packs.in_pack(w)


def test_an_old_save_monster_without_pack_fields_takes_its_turn():
    g = _game()
    ox, oy = _carve(g, OPEN)
    g.player.x, g.player.y = ox + 6, oy + 4
    w = _put(g, 'wolf', ox + 2, oy + 4)
    _put(g, 'wolf', ox + 2, oy + 5)
    for k in [k for k in w.__dict__ if k.startswith('_pack') or k in ('_charged', '_darted')]:
        w.__dict__.pop(k, None)
    w.take_turn(g.player, g.dungeon, g.monsters)        # no error
