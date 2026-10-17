"""Invisible monsters (src/unseen.py) and the mimic-AI disguise fix.

Brandon, 2026-10-17: "we should definitely have some invisible enemies! not a
ton, but it makes sense and fits lore; also, they should only appear with art
if you have see invisible or something like that."

A monster with `invisible: true` is not drawn, not listed in the sidebar's In
Sight panel, not offered by any target list and not named in look, unless the
hero has see invisible, true sight, telepathy or the Detect Monsters
clairvoyance. Unseen, it still fights; its blows read "Something unseen".
Walking into it feels it ("You feel something there"); the next bump strikes.
Seen, it is drawn in its own art with a cold see-through tint. Shep growls at
it like any other thing hiding in plain sight.

And: the two mimic-AI monsters (Lurking Horror, Gilded Mimic) were drawn as
monsters wherever they spawned on a floor; only `ambush` was hidden. Until
they spring they are now drawn as the chest or hoard they pose as.

Behaviour tests on a real headless Game: invisible monsters are deep,
randomized spawns Brandon cannot reach on demand in play.
"""
import json
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

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)

INVISIBLE = ('haunting_presence', 'dread_wraith', 'huldufolk_raider',
             'darkhelm_shade', 'whirlwind_jinni', 'nibelung_hoardwarden')
NEW = ('huldufolk_raider', 'darkhelm_shade', 'whirlwind_jinni', 'nibelung_hoardwarden')


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(name='__test_invisible__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(11)
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _open_spot(g, half=3):
    for y in range(half + 1, g.dungeon.height - half - 1):
        for x in range(half + 1, g.dungeon.width - half - 1):
            if all(g.dungeon.is_walkable(x + i, y + j)
                   for i in range(-half, half + 1) for j in range(-half, half + 1)):
                return x, y
    from dungeon import FLOOR
    x = min(max(g.player.x, half + 1), g.dungeon.width - half - 2)
    y = min(max(g.player.y, half + 1), g.dungeon.height - half - 2)
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    return x, y


def _monster(mid, x, y):
    from monster import Monster
    return Monster({**MONS[mid], 'id': mid}, x, y)


def _scene(mid='dread_wraith', dx=2, dy=0):
    """Hero in an open spot, everything around him in view, one monster."""
    g = _game()
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    m = _monster(mid, x + dx, y + dy)
    g.monsters = [m]
    g._refresh_fov()
    g.visible |= {(x + i, y + j) for i in range(-3, 4) for j in range(-3, 4)}
    return g, m


def _messages(g, n=12):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _spy_render(g):
    """Render once and report what was drawn and what the sidebar listed."""
    drawn, shimmers, disguises, listed = [], [], [], []
    r = g.renderer
    real_entity, real_shimmer, real_disg = r.draw_entity, r.draw_shimmer, r.draw_disguise

    def entity(*a, **kw):
        drawn.append((kw.get('mid'), kw.get('tint')))
        return real_entity(*a, **kw)

    def shimmer(x, y, *a, **kw):
        shimmers.append((x, y))
        return real_shimmer(x, y, *a, **kw)

    def disg(x, y, item_id, *a, **kw):
        disguises.append((x, y, item_id))
        return real_disg(x, y, item_id, *a, **kw)

    real_side = g.sidebar.draw

    def side(*a, **kw):
        listed.extend(kw.get('visible_monsters') or [])
        return real_side(*a, **kw)
    r.draw_entity, r.draw_shimmer, r.draw_disguise = entity, shimmer, disg
    g.sidebar.draw = side
    try:
        g.render()
    finally:
        r.draw_entity, r.draw_shimmer, r.draw_disguise = real_entity, real_shimmer, real_disg
        g.sidebar.draw = real_side
    return drawn, shimmers, disguises, listed


# ---------------------------------------------------------------- the rules

def test_one_place_decides_who_sees_an_invisible_creature():
    import unseen
    g, m = _scene()
    assert m.invisible and unseen.unseen(m, g.player)
    for eff in unseen.REVEAL_EFFECTS:
        g.player.status_effects.clear()
        g.player.add_effect(eff, 20)
        assert not unseen.unseen(m, g.player), eff
    g.player.status_effects.clear()
    plain = _monster('giant_rat', m.x, m.y)
    assert not unseen.unseen(plain, g.player) and not plain.invisible


def test_an_unseen_creature_is_never_named():
    from monster import the_name
    g, m = _scene()
    g._sync_unseen()
    assert the_name(m) == 'Something unseen'
    assert the_name(m, lower=True) == 'something unseen'
    g.player.add_effect('see_invisible', 30)
    g._sync_unseen()
    assert the_name(m) == 'The Dread Wraith'


# ---------------------------------------------------------------- the map

def test_not_drawn_without_see_invisible_and_drawn_tinted_with_it():
    import unseen
    g, m = _scene()
    drawn, shimmers, _d, listed = _spy_render(g)
    assert m.kind not in [mid for mid, _t in drawn]
    assert m not in listed
    g.player.add_effect('see_invisible', 30)
    g._refresh_fov()
    drawn, _s, _d, listed = _spy_render(g)
    assert (m.kind, unseen.SEE_INVISIBLE_TINT) in drawn
    assert m in listed


def test_an_ordinary_monster_is_drawn_without_the_tint():
    g, m = _scene('giant_rat')
    drawn, _s, _d, listed = _spy_render(g)
    assert ('giant_rat', None) in drawn and m in listed


def test_true_sight_and_telepathy_reveal_it_too():
    g, m = _scene()
    for eff in ('truesight', 'telepathy'):
        g.player.status_effects.clear()
        g.player.add_effect(eff, 30)
        g._refresh_fov()
        drawn, _s, _d, listed = _spy_render(g)
        assert m.kind in [mid for mid, _t in drawn], eff


# ---------------------------------------------------------------- lists

def test_target_lists_and_nearest_never_offer_it():
    g, m = _scene(dx=1)
    rat = _monster('giant_rat', g.player.x - 3, g.player.y)
    g.monsters.append(rat)
    g._target_candidates = [m, rat]
    assert g._target_candidates == [rat]
    assert g._nearest_visible_monster() is rat
    g._start_observe()
    assert m not in g._target_candidates and rat in g._target_candidates
    g.player.add_effect('see_invisible', 30)
    assert g._nearest_visible_monster() is m


def test_look_does_not_name_it():
    g, m = _scene()
    g.target_cursor_x, g.target_cursor_y = m.x, m.y
    g._observe_targeting = True
    g._confirm_observe()
    said = ' '.join(_messages(g))
    assert 'Dread Wraith' not in said


def test_the_aim_prompt_does_not_name_it():
    g, m = _scene()
    assert g._seen_monster_at(m.x, m.y) is None
    g.player.add_effect('see_invisible', 30)
    assert g._seen_monster_at(m.x, m.y) is m


# ---------------------------------------------------------------- fighting

def test_its_blows_read_something_unseen():
    g, m = _scene(dx=1)
    g.player.max_hp = g.player.hp = 10 ** 7
    m._aware = True
    m.thac0 = -200
    for _ in range(12):
        g._advance_turn()
    said = [s for s in _messages(g, 40) if 'unseen' in s.lower() or 'wraith' in s.lower()]
    assert said, _messages(g, 40)
    assert any('Something unseen strikes you for' in s for s in said), said
    assert not any('Dread Wraith' in s for s in said), said


def test_an_unseen_shot_says_where_it_came_from():
    g, m = _scene(dx=3)
    g._sync_unseen()
    msg = 'Something unseen strikes you for 9 damage!'
    m.attack = lambda player: (9, msg)
    m.take_turn = lambda *a, **k: True
    m._aware = True
    g.player.max_hp = g.player.hp = 10 ** 7
    g._advance_turn()
    assert any('It came from the east.' in s for s in _messages(g, 30)), _messages(g, 30)


def test_walking_into_it_feels_it_and_the_next_bump_strikes(monkeypatch):
    g, m = _scene(dx=1)
    m.take_turn = lambda *a, **k: False          # it stands still for the test
    struck = []
    monkeypatch.setattr(g, '_start_combat', lambda target: struck.append(target))
    g._do_move(1, 0)
    assert struck == []
    assert any('You feel something there' in s for s in _messages(g))
    assert m._felt_at == (m.x, m.y)
    assert (g.player.x, g.player.y) != (m.x, m.y)
    drawn, shimmers, _d, listed = _spy_render(g)
    assert (m.x, m.y) in shimmers and m not in listed
    g._do_move(1, 0)
    assert struck == [m]


def test_a_seen_invisible_creature_is_attacked_on_the_first_bump(monkeypatch):
    g, m = _scene(dx=1)
    g.player.add_effect('see_invisible', 30)
    struck = []
    monkeypatch.setattr(g, '_start_combat', lambda target: struck.append(target))
    g._do_move(1, 0)
    assert struck == [m]


def test_its_death_names_it():
    g, m = _scene()
    g._sync_unseen()
    m.hp = 0
    m.alive = False
    g._on_monster_killed(m)
    assert m._unseen is False


# ---------------------------------------------------------------- Shep

def test_shep_growls_at_an_invisible_creature_in_plain_view():
    from pet_system import SHEP, Pet
    g, m = _scene(dx=3)
    shep = Pet(SHEP, g.player.x - 1, g.player.y)
    g.pets = [shep]
    assert (m.x, m.y) in g.visible
    assert g._hidden_in_plain_sight(m)
    g._do_pet_growl()
    assert any('growls low' in s for s in _messages(g))


def test_shep_does_not_growl_at_one_the_hero_can_see():
    from pet_system import SHEP, Pet
    g, m = _scene(dx=3)
    g.player.add_effect('see_invisible', 30)
    shep = Pet(SHEP, g.player.x - 1, g.player.y)
    g.pets = [shep]
    assert not g._hidden_in_plain_sight(m)
    g._do_pet_growl()
    assert not any('growls low' in s for s in _messages(g))


# ---------------------------------------------------------------- the data

def test_six_invisible_monsters_across_the_whole_depth_weighted_deep():
    inv = sorted((k for k, v in MONS.items() if isinstance(v, dict) and v.get('invisible')),
                 key=lambda k: MONS[k]['peak_floor'])
    assert set(inv) == set(INVISIBLE)
    peaks = [MONS[k]['peak_floor'] for k in inv]
    assert min(peaks) <= 10 and max(peaks) >= 85
    assert sum(p >= 40 for p in peaks) >= 4


def test_each_spawns_from_the_ordinary_pool_on_its_own_floor():
    import dungeon
    for mid in INVISIBLE:
        d = MONS[mid]
        assert d['peak_weight'] > 0 and not d.get('is_boss') and not d.get('is_mini_boss'), mid
        assert mid in dungeon._build_spawn_pool(d['peak_floor']), mid
        assert mid not in dungeon._build_spawn_pool(max(1, d['min_level'] - 1)) or d['min_level'] <= 1


def test_new_ones_sit_on_the_floor_their_hp_was_built_for():
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
    from respawn_by_hp import plan
    placed = plan(MONS)
    for mid in NEW:
        d = MONS[mid]
        assert placed[mid] == (d['peak_floor'], d['spread'], d['min_level']), mid


def test_each_has_its_64px_painted_sprite_and_lore():
    with open(os.path.join(ROOT, 'tools', 'content', 'genart', 'installed.json'), encoding='utf-8') as f:
        installed = set(json.load(f))
    for mid in INVISIBLE:
        path = os.path.join(ROOT, 'assets', 'tiles', 'monsters', f'{mid}.png')
        assert os.path.exists(path), mid
        with open(path, 'rb') as f:
            head = f.read(24)
        assert (int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')) == (64, 64)
        assert mid in installed
        assert len(MONS[mid]['lore']) > 200


# ---------------------------------------------------------------- the mimics

def test_every_mimic_ai_monster_names_a_disguise_with_a_picture():
    import renderer
    mimics = [k for k, v in MONS.items() if isinstance(v, dict) and v.get('ai_pattern') == 'mimic']
    assert set(mimics) >= {'lurking_horror', 'gilded_mimic'}
    for mid in mimics:
        disg = MONS[mid].get('disguise') or {}
        assert disg.get('item') and disg.get('name'), mid
        assert renderer._resolve_item_sprite_path(disg['item']), mid


def test_an_unsprung_mimic_is_drawn_as_what_it_poses_as_not_as_a_monster():
    g, m = _scene('lurking_horror', dx=3)
    assert not m._aware
    drawn, _s, disguises, listed = _spy_render(g)
    assert (m.x, m.y, 'iron_chest') in disguises
    assert 'lurking_horror' not in [mid for mid, _t in drawn]
    assert m not in listed
    # Look sees a chest, not a Lurking Horror.
    g.target_cursor_x, g.target_cursor_y = m.x, m.y
    g._observe_targeting = True
    g._confirm_observe()
    said = ' '.join(_messages(g))
    assert 'iron chest' in said and 'Lurking Horror' not in said


def test_the_gilded_mimic_poses_as_a_hoard():
    g, m = _scene('gilded_mimic', dx=3)
    _drawn, _s, disguises, _l = _spy_render(g)
    assert (m.x, m.y, 'dragon_hoard') in disguises


def test_once_sprung_the_mimic_is_drawn_as_itself():
    g, m = _scene('lurking_horror', dx=1)
    m.take_turn(g.player, g.dungeon, g.monsters)     # hero beside it: it springs
    assert m._aware and m.ai_pattern == 'aggressive'
    drawn, _s, disguises, listed = _spy_render(g)
    assert 'lurking_horror' in [mid for mid, _t in drawn] and disguises == [] and m in listed


def test_a_mimic_that_spawned_on_a_generated_floor_is_disguised():
    """The bug as found: natural spawns of a mimic-AI monster were drawn."""
    from dungeon import populate_floor
    g = _game('__test_mimic_floor__')
    random.seed(3)
    found = []
    for _ in range(40):
        for m in populate_floor(g.dungeon.rooms, 45, g.dungeon):
            if m.ai_pattern == 'mimic':
                found.append(m)
        if found:
            break
    assert found, 'no mimic-AI monster rolled on floor 45 in 40 floors'
    import unseen
    for m in found:
        assert unseen.lurking(m) and unseen.disguise(m)


def test_a_mimic_out_of_a_chest_has_given_itself_away():
    import types
    from container_system import _spawn_mimic
    g = _game('__test_mimic_chest__')
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    chest = types.SimpleNamespace(x=x + 1, y=y)
    m = _spawn_mimic(chest, g.monsters, 50, dungeon=g.dungeon, avoid=(x, y))
    assert m.kind == 'lurking_horror' and m._aware
    g._refresh_fov()
    drawn, _s, disguises, _l = _spy_render(g)
    assert 'lurking_horror' in [mid for mid, _t in drawn] and disguises == []
