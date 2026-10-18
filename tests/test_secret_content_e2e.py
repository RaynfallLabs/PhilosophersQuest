"""Secret and quest content, played through end to end on a real headless Game.

The wiring tests (test_quest_chains.py and friends) check that the pieces are
named in the code. These play each flow to its end with the game's own entry
points: floor changes build the floors, steps bump the NPCs, keys answer the
dialogs, the quiz engine's own _end drives the quiz callbacks, and art is
resolved through the renderer's own lookups (the same ones the map draw
uses), so a missing picture shows up here as it would on screen: a glyph.

Covered: the Magic Dungeon Carrot, the Ethereal Unicorn, the Cow Level (the
cow, the Moo Moo Farm, the Cow King, the portal home, save/load mid-farm), the
Duck of Doom, the abandoned Emberpup, the Black Knight, mystery altars and the
merchant, Soul Sphere hatching, and the quest chains: Sir Aldric's lodestone,
the courier and the Watch Post, Saint Cuthbert's Gospel, the Lost Girl's
pendant, Ariadne's shrine, the Sword of Pelops, Chandrahasa and the Book of
Thoth. All of it is rare, randomized or deep, so Brandon cannot reach it on
demand in play: these are the proof.
"""
import copy
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

ITEM_DIR = os.path.join(ROOT, 'assets', 'tiles', 'items')
MON_DIR = os.path.join(ROOT, 'assets', 'tiles', 'monsters')


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(name='__test_secret_e2e__', seed=5):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name=name)
    g.state = STATE_PLAYER
    return g


def _log(g):
    return ' | '.join(str(e[0]) for e in g.msg_log.entries)


def _chron(g):
    return ' | '.join(str(e.get('text', e) if isinstance(e, dict) else e) for e in g._chronicle)


def _clear_floor(g, keep=()):
    """Only the creatures under test stay: nothing else joins in."""
    g.monsters[:] = [m for m in g.monsters if m in keep]
    g.pets = []
    g.dungeon.traps = {}


def _beside(g, thing):
    """Stand the hero on a free walkable tile next to ``thing`` and return the
    step that walks into it."""
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        x, y = thing.x - dx, thing.y - dy
        if (g.dungeon.is_walkable(x, y)
                and not any((m.x, m.y) == (x, y) for m in g.monsters if m.alive)):
            g.player.x, g.player.y = x, y
            g._refresh_fov()
            return dx, dy
    raise AssertionError(f'no free tile beside {getattr(thing, "name", thing)}')


def _monster_art(g, m):
    """The picture the map draw asks for (game_render: sprite_id or kind),
    through the renderer's own lookup. None means a letter glyph."""
    return g.renderer._get_sprite(getattr(m, 'sprite_id', None) or m.kind)


def _own_item_art(item_id):
    """The item's own picture, as the renderer resolves it (not a borrowed one)."""
    from renderer import _resolve_item_sprite_path
    path = _resolve_item_sprite_path(item_id)
    return path is not None and os.path.normcase(os.path.abspath(path)) == \
        os.path.normcase(os.path.join(ITEM_DIR, item_id + '.png'))


def _assert_floor_draws_without_glyphs(g):
    """Every tile, monster and ground item on this floor resolves to a real
    picture through the renderer, the way draw_dungeon / draw_entity /
    draw_item decide it; then a full render with everything in view asks for
    nothing that would fall back to a glyph."""
    from renderer import _tile_sprite_name
    r = g.renderer
    d = g.dungeon
    missing = set()
    for y in range(d.height):
        for x in range(d.width):
            name = _tile_sprite_name(d, x, y, d.tiles[y][x])
            if not name or r._get_env_sprite(name) is None:
                missing.add(('tile', d.tiles[y][x], name))
    for m in g.monsters:
        if m.alive and _monster_art(g, m) is None:
            missing.add(('monster', m.kind))
    for it in g.ground_items:
        if r._get_item_sprite(getattr(it, 'id', None)) is None:
            missing.add(('item', getattr(it, 'id', None)))
    assert not missing, missing
    # And the real draw: everything in view, every entity call resolves.
    asked = []
    real_entity, real_item = r.draw_entity, r.draw_item

    def spy_entity(*a, **kw):
        asked.append(('entity', kw.get('mid')))
        return real_entity(*a, **kw)

    def spy_item(item, *a, **kw):
        asked.append(('item', getattr(item, 'id', None)))
        return real_item(item, *a, **kw)
    r.draw_entity, r.draw_item = spy_entity, spy_item
    saved_visible = g.visible
    try:
        g.visible = {(x, y) for y in range(d.height) for x in range(d.width)}
        g.render()
    finally:
        r.draw_entity, r.draw_item = real_entity, real_item
        g.visible = saved_visible
    assert asked
    bad = [(k, mid) for k, mid in asked
           if (k == 'entity' and (not mid or r._get_sprite(mid) is None))
           or (k == 'item' and r._get_item_sprite(mid) is None)]
    assert not bad, bad


def _roundtrip(g, name, tmp_path, monkeypatch):
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    save_system.settle_unfinished_actions(g)
    assert save_system.save_game(g)
    state = save_system.load_game(name)
    g2 = Game(_screen(), player_name=name)
    g2.load_state(state)
    g2.state = STATE_PLAYER
    return g2


# ===========================================================================
# 1. The Magic Dungeon Carrot
# ===========================================================================

def _carrots(g):
    return [i for i in g.ground_items if getattr(i, 'id', '') == 'magic_dungeon_carrot']


def test_a_new_run_picks_a_carrot_floor_from_1_to_19():
    floors = set()
    for s in range(6):
        g = _game(f'__test_carrot_roll_{s}__', seed=100 + s)
        assert 1 <= g._magic_carrot_target_level <= 19
        floors.add(g._magic_carrot_target_level)
    assert len(floors) > 1                      # it is rolled, not fixed


def test_the_carrot_spawns_exactly_once_on_its_floor_reachable_and_can_be_picked_up():
    g = _game('__test_carrot__')
    g.ground_items[:] = [i for i in g.ground_items if i not in _carrots(g)]
    g._magic_carrot_spawned = False
    g._magic_carrot_target_level = 7
    seen = {}
    for lvl in range(2, 20):
        g._change_level(lvl, enter_from_top=True)
        seen[lvl] = len(_carrots(g))
        if lvl == 7:
            c = _carrots(g)[0]
            assert g.dungeon.is_walkable(c.x, c.y)
            walk = g._reachable_tiles(g.player.x, g.player.y)
            assert (c.x, c.y) in walk                  # the hero can walk to it
            stair = (g.player.x, g.player.y)
            g.player.x, g.player.y = c.x, c.y
            # Another item can share the tile; each pickup takes one, as in play.
            for _ in range(4):
                if any(getattr(i, 'id', '') == 'magic_dungeon_carrot' for i in g.player.inventory):
                    break
                g._pickup()
            assert any(getattr(i, 'id', '') == 'magic_dungeon_carrot' for i in g.player.inventory)
            assert not _carrots(g)
            g.player.x, g.player.y = stair
    assert seen[7] == 1 and sum(seen.values()) == 1, seen
    # Back on its floor (a stored floor) and on new floors: never a second.
    g._change_level(7, enter_from_top=False)
    assert not _carrots(g)
    g._change_level(21, enter_from_top=True)
    assert not _carrots(g)
    assert g._magic_carrot_spawned is True


def test_the_carrot_on_floor_1_is_placed_at_game_start(monkeypatch):
    """Floor 1 is built in Game.__init__, not by _change_level: a run that
    rolls floor 1 for the carrot still gets it."""
    real = random.randint
    monkeypatch.setattr(random, 'randint', lambda a, b: 1 if (a, b) == (1, 19) else real(a, b))
    g = _game('__test_carrot_f1__')
    monkeypatch.setattr(random, 'randint', real)
    assert g._magic_carrot_target_level == 1
    assert len(_carrots(g)) == 1 and g._magic_carrot_spawned
    c = _carrots(g)[0]
    assert (c.x, c.y) in g._reachable_tiles(g.player.x, g.player.y)


def test_the_carrot_spawn_state_survives_save_and_load(tmp_path, monkeypatch):
    name = '__test_carrot_save__'
    g = _game(name)
    g._magic_carrot_spawned = False
    g._magic_carrot_target_level = 3
    g._change_level(3, enter_from_top=True)
    assert len(_carrots(g)) == 1
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    assert g2._magic_carrot_spawned is True and g2._magic_carrot_target_level == 3
    assert len(_carrots(g2)) == 1


def test_the_carrot_has_its_own_art():
    g = _game('__test_carrot_art__')
    assert _own_item_art('magic_dungeon_carrot')
    assert g.renderer._get_item_sprite('magic_dungeon_carrot') is not None


# ===========================================================================
# 2. The Ethereal Unicorn
# ===========================================================================

def _unicorns(g):
    return [m for m in g.monsters if getattr(m, '_is_unicorn', False) and m.alive]


def test_a_new_run_picks_a_unicorn_floor_from_21_to_39():
    g = _game('__test_unicorn_roll__')
    g._change_level(21, enter_from_top=True)
    assert 21 <= g._unicorn_target_level <= 39


def test_the_unicorn_appears_only_on_her_floor_and_can_be_reached():
    g = _game('__test_unicorn_floors__')
    g._unicorn_spawned = False
    g._unicorn_target_level = 25
    seen = {}
    for lvl in range(21, 30):
        g._change_level(lvl, enter_from_top=True)
        seen[lvl] = len(_unicorns(g))
        if lvl == 25:
            u = _unicorns(g)[0]
            assert u.kind == 'ethereal_unicorn' and u.is_allied
            assert u._unicorn_state == 'wary'
            walk = g._reachable_tiles(g.player.x, g.player.y)
            assert any((u.x + dx, u.y + dy) in walk
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
            assert _monster_art(g, u) is not None
    assert seen[25] == 1 and sum(seen.values()) == 1, seen
    g._change_level(25, enter_from_top=False)
    assert len(_unicorns(g)) == 1                     # the same one, not a second


def _unicorn_scene(g, floor=25):
    """Her floor, nothing else about, the hero two tiles off in plain view
    with the carrot in his pack."""
    from items import load_items
    g._unicorn_spawned = False
    g._unicorn_target_level = floor
    g._change_level(floor, enter_from_top=True)
    u = _unicorns(g)[0]
    _clear_floor(g, keep=[u])
    g.ground_items[:] = []
    # stand the hero close by (two tiles if he can see her from there, else
    # one), on a tile from which she is in plain view
    for want in (2, 1):
        spots = [(u.x + dx, u.y + dy) for dx in range(-want, want + 1)
                 for dy in range(-want, want + 1) if max(abs(dx), abs(dy)) == want]
        ok = False
        for px, py in spots:
            if not g.dungeon.is_walkable(px, py):
                continue
            g.player.x, g.player.y = px, py
            g._refresh_fov()
            if (u.x, u.y) in g.visible:
                ok = True
                break
        if ok:
            break
    assert (u.x, u.y) in g.visible, 'no spot near the unicorn from which she is seen'
    carrot = copy.copy(next(f for f in load_items('food') if f.id == 'magic_dungeon_carrot'))
    g.player.inventory.append(carrot)
    return u, carrot


def _wait(g, n=1):
    for _ in range(n):
        g._advance_turn()


def _to_trusting(g, u, carrot):
    from game_states import STATE_PLAYER
    _wait(g, 3)
    assert u._unicorn_state == 'relaxing', u._unicorn_state
    assert 'She watches you warily' in _log(g)
    g._do_drop_item(carrot)
    assert g.state == STATE_PLAYER
    assert any(getattr(i, 'id', '') == 'magic_dungeon_carrot' for i in g.ground_items)
    _wait(g)
    assert u._unicorn_state == 'eating', u._unicorn_state
    assert (u.x, u.y) != (g.player.x, g.player.y)          # never on the hero's tile
    _wait(g, 2)
    assert u._unicorn_state == 'trusting', u._unicorn_state
    assert not any(getattr(i, 'id', '') == 'magic_dungeon_carrot' for i in g.ground_items)
    assert 'finishes the carrot' in _log(g)


def test_the_unicorn_goes_wary_relaxing_eating_trusting_with_the_carrot():
    g = _game('__test_unicorn_states__')
    u, carrot = _unicorn_scene(g)
    _to_trusting(g, u, carrot)


def test_bumping_her_too_soon_startles_her_back_to_wary():
    g = _game('__test_unicorn_startle__')
    u, carrot = _unicorn_scene(g)
    _wait(g, 3)
    assert u._unicorn_state == 'relaxing'
    step = _beside(g, u)
    spot = (u.x, u.y)
    g._do_move(*step)
    assert u._unicorn_state == 'wary' and u.alive
    assert (u.x, u.y) != spot                    # she leapt away
    assert 'nervously' in _log(g)


def test_a_dark_heart_makes_the_trusting_unicorn_flee():
    from game_states import STATE_QUIZ
    g = _game('__test_unicorn_karma__')
    u, carrot = _unicorn_scene(g)
    _to_trusting(g, u, carrot)
    g.karma = -1
    step = _beside(g, u)
    g._do_move(*step)
    assert g.state != STATE_QUIZ
    assert u._unicorn_state == 'fled' and not u.alive
    assert 'senses darkness in your heart' in _log(g)
    assert not g.pets


def _trusting_bump_to_quiz(g):
    from game_states import STATE_QUIZ
    from quiz_engine import QuizMode
    u, carrot = _unicorn_scene(g)
    _to_trusting(g, u, carrot)
    g.karma = 0
    step = _beside(g, u)
    g._do_move(*step)
    assert g.state == STATE_QUIZ
    qe = g.quiz_engine
    assert qe.subject == 'ai' and qe.mode == QuizMode.ESCALATOR_CHAIN
    assert qe.callback is not None
    return u


def test_a_perfect_unicorn_quiz_gives_every_boon_and_she_joins_as_a_pet():
    from game_states import STATE_PLAYER
    from pet_system import UnicornPet
    g = _game('__test_unicorn_pass__')
    u = _trusting_bump_to_quiz(g)
    g.player.hp = 1
    qe = g.quiz_engine
    qe.score = 5
    qe._end(success=True)
    assert g.state == STATE_PLAYER
    assert not u.alive
    pets = [p for p in g.pets if isinstance(p, UnicornPet)]
    assert len(pets) == 1
    assert g.player.has_effect('regenerating')
    assert g.player.hp == g.player.max_hp                       # chain 2: full restore
    assert any(g.player.status_effects.get(k) == -1 for k in ('magic_resist', 'poison_resist'))
    assert 'joins you as a companion' in _log(g)
    assert 'The unicorn bowed her head' in _chron(g) or 'She stayed' in _chron(g)
    # Her picture as a pet: game_render asks for species_name lowered.
    pet = pets[0]
    mid = (getattr(pet, 'species_name', None) or pet.name).lower().replace(' ', '_')
    assert g.renderer._get_sprite(mid) is not None, mid


def test_a_middling_unicorn_quiz_gives_boons_but_she_departs():
    from pet_system import UnicornPet
    from items import load_items
    g = _game('__test_unicorn_mid__')
    u = _trusting_bump_to_quiz(g)
    junk = copy.copy(load_items('food')[0])
    junk.buc = 'cursed'
    g.player.inventory.append(junk)
    qe = g.quiz_engine
    qe.score = 3
    qe._end(success=False)
    assert not u.alive and u._unicorn_state == 'fled'
    assert not any(isinstance(p, UnicornPet) for p in g.pets)
    assert g.player.has_effect('regenerating')
    assert junk.buc == 'uncursed'                                # chain 3: uncurse
    assert not any(g.player.status_effects.get(k) == -1 for k in ('magic_resist', 'poison_resist'))


def test_a_failed_unicorn_quiz_gives_nothing_and_she_trots_away():
    from pet_system import UnicornPet
    g = _game('__test_unicorn_fail__')
    u = _trusting_bump_to_quiz(g)
    qe = g.quiz_engine
    qe.score = 0
    qe._end(success=False)
    assert not u.alive and u._unicorn_state == 'fled'
    assert not any(isinstance(p, UnicornPet) for p in g.pets)
    assert not g.player.has_effect('regenerating')
    assert 'Perhaps next time' in _log(g)


def test_the_unicorn_keeps_her_trust_across_save_and_load(tmp_path, monkeypatch):
    name = '__test_unicorn_save__'
    g = _game(name)
    u, carrot = _unicorn_scene(g)
    _to_trusting(g, u, carrot)
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    us = _unicorns(g2)
    assert len(us) == 1 and us[0]._unicorn_state == 'trusting'
    assert g2._unicorn_spawned is True and g2._unicorn_target_level == 25


def test_the_unicorn_has_art():
    assert os.path.exists(os.path.join(MON_DIR, 'ethereal_unicorn.png'))


# ===========================================================================
# 3. The Cow Level
# ===========================================================================

def _cows(g):
    return [m for m in g.monsters if getattr(m, '_npc_encounter_tag', None) == '_cow_dialog' and m.alive]


def test_a_new_run_picks_a_cow_floor_from_30_to_39():
    g = _game('__test_cow_roll__')
    assert 30 <= g._cow_level <= 39


def test_the_cow_stands_only_on_her_floor_and_can_be_reached():
    g = _game('__test_cow_floors__')
    g._cow_level = 33
    seen = {}
    for lvl in (31, 32, 33, 34):
        g._change_level(lvl, enter_from_top=True)
        seen[lvl] = len(_cows(g))
        if lvl == 33:
            cow = _cows(g)[0]
            assert cow.kind == 'secret_cow' and cow.is_allied
            assert _monster_art(g, cow) is not None
            walk = g._reachable_tiles(g.player.x, g.player.y)
            assert any((cow.x + dx, cow.y + dy) in walk
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
    assert seen == {31: 0, 32: 0, 33: 1, 34: 0}
    g._change_level(33, enter_from_top=False)
    assert len(_cows(g)) == 1


def _poke_into_the_farm(g, floor=33):
    """Bump the cow and poke her through the dialog, the way a player does,
    until the floor opens. Returns the number of bumps it took."""
    from game_states import STATE_COW_ENCOUNTER, STATE_PLAYER
    from boss_levels import COW_LEVEL
    g._cow_level = floor
    g._change_level(floor, enter_from_top=True)
    cow = _cows(g)[0]
    _clear_floor(g, keep=[cow])
    bumps = 0
    while g.dungeon_level != COW_LEVEL:
        step = _beside(g, cow)
        g._do_move(*step)
        bumps += 1
        assert g.state == STATE_COW_ENCOUNTER and g._cow_dialog_phase == 'options'
        g.render()                                     # the dialog draws
        g._cow_encounter_input(pygame.K_3)
        if g.dungeon_level == COW_LEVEL:
            break
        assert g._cow_dialog_phase == 'result'
        g._cow_encounter_input(pygame.K_RETURN)
        assert g.state == STATE_PLAYER
        assert bumps < 20
    return bumps


def test_feeding_the_cow_winds_the_count_back():
    from items import Ingredient
    from game_states import STATE_COW_ENCOUNTER
    import food_system
    g = _game('__test_cow_feed__')
    g._cow_level = 33
    g._change_level(33, enter_from_top=True)
    cow = _cows(g)[0]
    _clear_floor(g, keep=[cow])
    g._cow_poke_count = 5
    ing = next(food_system.load_ingredient_for(i) for i in food_system._raw_ingredients()
               if food_system._raw_ingredients()[i].get('tier_role', '') != 'trophy')
    assert isinstance(ing, Ingredient)
    g.player.inventory.append(ing)
    g._do_move(*_beside(g, cow))
    assert g.state == STATE_COW_ENCOUNTER
    g._cow_encounter_input(pygame.K_1)
    assert g._cow_poke_count == 3
    assert ing not in g.player.inventory


def test_ten_pokes_through_the_dialog_open_the_moo_moo_farm():
    from boss_levels import COW_LEVEL
    from game_states import STATE_PLAYER
    g = _game('__test_cow_poke__')
    bumps = _poke_into_the_farm(g)
    assert bumps == 10
    assert g.dungeon_level == COW_LEVEL and g.state == STATE_PLAYER
    assert g._cow_return_level == 33
    assert 'MOO MOO MOO MOO MOO!' in _log(g)
    assert 'cow dimension' in _chron(g)
    # She is gone from her own floor's stored copy.
    _, stored_monsters, _ = g.level_mgr.load(33)
    assert not [m for m in stored_monsters if getattr(m, '_npc_encounter_tag', None) == '_cow_dialog']


def test_the_farm_has_its_herd_its_king_and_a_portal_home():
    from dungeon import STAIRS_DOWN
    g = _game('__test_cow_farm__')
    _poke_into_the_farm(g)
    kinds = [m.kind for m in g.monsters if m.alive]
    assert 40 <= kinds.count('hell_bovine') <= 50
    assert kinds.count('cow_king') == 1
    king = next(m for m in g.monsters if m.kind == 'cow_king')
    assert king.is_boss
    portals = [(x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)
               if g.dungeon.tiles[y][x] == STAIRS_DOWN]
    assert len(portals) == 1
    # The hero lands on open ground, not on a bovine, and can walk to the
    # portal and to the king's pen.
    me = (g.player.x, g.player.y)
    assert g.dungeon.is_walkable(*me)
    assert not any((m.x, m.y) == me for m in g.monsters if m.alive)
    walk = g._reachable_tiles(*me)
    assert portals[0] in walk
    assert any((king.x + dx, king.y + dy) in walk
               for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
    assert 'Welcome to the Moo Moo Farm.' in _log(g)


def test_every_creature_tile_and_item_on_the_farm_has_art():
    g = _game('__test_cow_art__')
    _poke_into_the_farm(g)
    _assert_floor_draws_without_glyphs(g)
    for mid in ('secret_cow', 'hell_bovine', 'cow_king'):
        assert os.path.exists(os.path.join(MON_DIR, mid + '.png'))


def test_the_cow_kings_horns_drop_where_he_falls():
    g = _game('__test_cow_king__')
    _poke_into_the_farm(g)
    king = next(m for m in g.monsters if m.kind == 'cow_king')
    _clear_floor(g, keep=[king])
    king.hp = 0
    king.alive = False
    g._on_monster_killed(king)
    drops = {getattr(i, 'id', '') for i in g.ground_items}
    assert 'cow_kings_horns' in drops, drops
    horns = next(i for i in g.ground_items if getattr(i, 'id', '') == 'cow_kings_horns')
    assert (horns.x, horns.y) == (king.x, king.y)
    assert _own_item_art('cow_kings_horns')
    assert 'scroll_of_the_pasture' in drops
    assert _own_item_art('scroll_of_the_pasture')


def test_the_cow_king_lives_only_on_the_farm():
    """The documented rule: he is a portal-only boss (frequency 0, spawn
    chance 0) and never in the mini-boss plan."""
    import json
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    for mid in ('cow_king', 'hell_bovine'):
        assert mons[mid]['frequency'] == 0 and not mons[mid]['peak_weight']
    assert mons['cow_king']['spawn_chance'] == 0
    for s in range(5):
        g = _game(f'__test_cow_king_plan_{s}__', seed=300 + s)
        assert 'cow_king' not in g.level_mgr._roll_planned_mini_bosses().values()


def test_the_portal_takes_you_home_ends_the_farm_and_the_cow_is_gone():
    from dungeon import STAIRS_DOWN
    g = _game('__test_cow_home__')
    deepest = g.player.deepest_floor_reached
    _poke_into_the_farm(g)
    assert g.player.deepest_floor_reached == max(deepest, 33)
    portal = next((x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)
                  if g.dungeon.tiles[y][x] == STAIRS_DOWN)
    g.player.x, g.player.y = portal
    g._descend_stairs()
    assert g.dungeon_level == 33
    assert g._cow_level_done is True
    assert not _cows(g)
    assert g.dungeon.tiles[g.player.y][g.player.x] == STAIRS_DOWN    # arrives on the down stair
    assert 'The portal closes. Moo.' in _log(g)
    # Not depth: the farm never counted.
    assert g.player.deepest_floor_reached == max(deepest, 33)
    assert g.level_mgr.max_level_reached < 999
    # She never comes back, by stair or by a fresh visit.
    g._change_level(34, enter_from_top=True)
    g._change_level(33, enter_from_top=False)
    assert not _cows(g)
    g._cow_spawned = False                    # even if the spawner were asked again
    g._maybe_spawn_cow(33)
    assert not _cows(g)


def test_a_potion_of_gain_level_on_the_farm_leaves_through_the_portal():
    g = _game('__test_cow_gain__')
    _poke_into_the_farm(g)
    g._exit_cow_level()                       # the '_gain_level' branch calls this on 999
    assert g.dungeon_level == 33 and g._cow_level_done


def test_save_and_load_mid_farm(tmp_path, monkeypatch):
    from boss_levels import COW_LEVEL
    from dungeon import STAIRS_DOWN
    name = '__test_cow_save__'
    g = _game(name)
    _poke_into_the_farm(g)
    herd = sorted((m.kind, m.x, m.y) for m in g.monsters if m.alive)
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    assert g2.dungeon_level == COW_LEVEL
    assert sorted((m.kind, m.x, m.y) for m in g2.monsters if m.alive) == herd
    assert g2._cow_return_level == 33 and g2._cow_level_done is False
    assert (g2.player.x, g2.player.y) == (g.player.x, g.player.y)
    g2._show_load_summary_popup()               # "Moo Moo Farm", never "Floor 999"
    assert 'Moo Moo Farm' in str(g2.popup_data) and '999' not in str(g2.popup_data)
    from game_states import STATE_PLAYER
    g2.state = STATE_PLAYER
    _assert_floor_draws_without_glyphs(g2)
    portal = next((x, y) for y in range(g2.dungeon.height) for x in range(g2.dungeon.width)
                  if g2.dungeon.tiles[y][x] == STAIRS_DOWN)
    g2.player.x, g2.player.y = portal
    g2._descend_stairs()
    assert g2.dungeon_level == 33 and g2._cow_level_done is True
    assert not _cows(g2)


def test_the_farm_is_never_named_floor_999_to_the_player():
    g = _game('__test_cow_label__')
    _poke_into_the_farm(g)
    assert 'level 999' not in _log(g).lower()
    from ui import floor_label
    assert '999' not in floor_label(g.dungeon_level)
    assert floor_label(33) == 'Floor 33'
    g.render()                                   # the sidebar draws with the label
    g._change_level(34, enter_from_top=True)
    assert 'You descend to level 34.' in _log(g)  # ordinary floors keep their message


# ===========================================================================
# 4. Other secrets
# ===========================================================================

def _ducks(g):
    return [i for i in g.ground_items if getattr(i, 'id', '') == 'duck_of_doom']


def test_the_duck_of_doom_waits_on_one_floor_from_1_to_10_reachable():
    g = _game('__test_duck__')
    assert 1 <= g._duck_of_doom_floor <= 10
    # Start a fresh walk down with the duck on floor 6.
    g.ground_items[:] = [i for i in g.ground_items if i not in _ducks(g)]
    g._duck_of_doom_placed = False
    g._duck_of_doom_floor = 6
    seen = {}
    for lvl in range(2, 11):
        g._change_level(lvl, enter_from_top=True)
        seen[lvl] = len(_ducks(g))
        if lvl == 6:
            d = _ducks(g)[0]
            walk = g._reachable_tiles(g.player.x, g.player.y)
            assert (d.x, d.y) in walk
            g.player.x, g.player.y = d.x, d.y
            g._pickup()
            head = g.player.armor_slots[0]
            assert head is not None and head.id == 'duck_of_doom'     # it puts itself on
    assert seen[6] == 1 and sum(seen.values()) == 1, seen
    g._change_level(6, enter_from_top=False)
    assert not _ducks(g)


def test_the_duck_has_its_art():
    g = _game('__test_duck_art__')
    from renderer import _resolve_item_sprite_path
    assert _resolve_item_sprite_path('duck_of_doom') is not None
    assert g.renderer._get_item_sprite('duck_of_doom') is not None


def test_the_abandoned_emberpup_waits_on_its_floor_with_its_art():
    import emberpup_encounter as ep
    g = _game('__test_ember_e2e__')
    g._emberpup = {'floor': 5, 'spawned': False, 'outcome': None}
    for lvl in (4, 5):
        g._change_level(lvl, enter_from_top=True)
    pups = [m for m in g.monsters if ep.is_emberpup(m) and m.alive]
    assert len(pups) == 1
    assert _monster_art(g, pups[0]) is not None
    _assert_floor_draws_without_glyphs(g)


def test_the_black_knight_stands_on_his_floor_with_his_art():
    import black_knight as bk
    g = _game('__test_bk_e2e__')
    g._black_knight = {'floor': 16, 'spawned': False, 'outcome': None, 'sword_dropped': False}
    g._change_level(16, enter_from_top=True)
    ks = [m for m in g.monsters if bk.is_black_knight(m) and m.alive]
    assert len(ks) == 1
    assert _monster_art(g, ks[0]) is not None
    _assert_floor_draws_without_glyphs(g)


def test_every_mystery_altar_and_key_spawns_with_its_art():
    import mystery_system as ms
    from dungeon import generate_dungeon
    g = _game('__test_mystery_art__')
    for mid, m in ms.MYSTERIES.items():
        lo, hi = m['floor_range']
        got = None
        for s in range(60):
            random.seed(s)
            d = generate_dungeon(80, 50, lo)
            rng = random.Random(s)
            # force this mystery: only it is eligible in the call below
            saved = dict(ms.MYSTERIES)
            try:
                ms.MYSTERIES.clear()
                ms.MYSTERIES[mid] = saved[mid]
                got = ms.spawn_mystery_for_level(lo, d.rooms, d, [], rng)
            finally:
                ms.MYSTERIES.clear()
                ms.MYSTERIES.update(saved)
            if got:
                break
        assert got, mid
        altar, key = got
        assert d.is_walkable(altar.x, altar.y)
        assert g.renderer._get_item_sprite(altar.id) is not None, altar.id
        assert _own_item_art(altar.id), altar.id
        if m['key_item'] is not None:
            assert key is not None, mid
            assert _own_item_art(key.id), key.id


def test_the_deep_gnome_trader_turns_up_reachable_with_his_art():
    """The Svirfneblin trader is mystery_system.MerchantNPC: Grindle, the
    generalist of data/traders.json, planned for about one floor in six
    (traders.py) and placed on arrival (game_traders.py)."""
    from mystery_system import MerchantNPC
    assert _own_item_art('merchant_npc')
    g = _game('__test_trader__')
    met = 0
    for lvl in range(2, 30):
        if lvl == 20:
            continue
        g._change_level(lvl, enter_from_top=True)
        traders = [i for i in g.ground_items if isinstance(i, MerchantNPC)]
        assert len(traders) <= 1
        if traders:
            met += 1
            t = traders[0]
            assert t.stock and t.person and t.title
            if t.kind == 'generalist' and not t.friend:
                assert t.name == 'Grindle' and t.title == 'Deep Gnome Trader'
            walk = g._reachable_tiles(g.player.x, g.player.y)
            assert any((t.x + dx, t.y + dy) in walk
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1)), lvl
            assert g.renderer._get_sprite(t.sprite_id) is not None
    assert met >= 3


def test_a_soul_sphere_spawns_on_some_floors_and_hatches_a_pet_with_art():
    from dungeon import generate_dungeon, spawn_items
    from game_states import STATE_PET_NAME_INPUT
    found = 0
    for s in range(120):
        random.seed(9000 + s)
        d = generate_dungeon(80, 50, 4)
        items = spawn_items(d.rooms, 4, d)
        spheres = [i for i in items if getattr(i, 'id', '') == 'soul_sphere']
        if spheres:
            found += 1
            assert all(d.is_walkable(sp.x, sp.y) for sp in spheres)
    assert 1 <= found <= 30                     # about one floor in twelve (8% on floors 1-33)
    assert _own_item_art('soul_sphere')
    # Throw one: a pet hatches beside the hero, the naming card opens, and
    # its picture resolves the way the map draw asks for it.
    from items import make_item_by_id
    g = _game('__test_sphere__')
    _clear_floor(g)
    sphere = make_item_by_id('artifact', 'soul_sphere')
    g.player.inventory.append(sphere)
    tx, ty = next((g.player.x + dx, g.player.y + dy) for dx, dy in
                  ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 0), (-1, 0), (0, 1), (0, -1))
                  if g.dungeon.is_walkable(g.player.x + dx, g.player.y + dy))
    g._throw_soul_sphere(sphere, None, tx, ty)
    assert sphere not in g.player.inventory
    assert len(g.pets) == 1 and g.state == STATE_PET_NAME_INPUT
    pet = g.pets[0]
    mid = (getattr(pet, 'species_name', None) or pet.name).lower().replace(' ', '_')
    assert g.renderer._get_sprite(mid) is not None, mid


def test_every_pet_stage_a_sphere_or_secret_can_give_has_art():
    import pet_system as ps
    missing = []
    for key, sp in list(ps._SPECIES.items()) + [('fenrir', ps._FENRIR_SPECIES)]:
        for st in sp['stages']:
            mid = st['name'].lower().replace(' ', '_')
            if not os.path.exists(os.path.join(MON_DIR, mid + '.png')):
                missing.append((key, mid))
    assert not missing, missing


# ---------------------------------------------------------------------------
# Quest chains: karma NPCs (bump -> text -> option -> outcome -> close)
# ---------------------------------------------------------------------------

def _npc_def(tag):
    from npc_encounters import ENCOUNTERS
    return copy.deepcopy(next(e for e in ENCOUNTERS if e['tag'] == tag))


def _flavor_def(tag):
    from flavor_encounters import FLAVOR_ENCOUNTERS
    import economy
    return economy.price_encounter(copy.deepcopy(next(e for e in FLAVOR_ENCOUNTERS if e['tag'] == tag)))


def _meet(g, floor, enc, flavor=False):
    """Put ``enc`` on ``floor`` the way the run plan does, arrive there, and
    return the NPC the game's own spawner placed."""
    if flavor:
        g._flavor_encounter_levels = {floor: enc}
    else:
        g._npc_encounter_levels = {floor: enc}
    g._change_level(floor, enter_from_top=True)
    attr = '_flavor_encounter_tag' if flavor else '_npc_encounter_tag'
    npcs = [m for m in g.monsters if getattr(m, attr, None) == enc['tag'] and m.alive]
    assert len(npcs) == 1, enc['tag']
    npc = npcs[0]
    assert _monster_art(g, npc) is not None, npc.kind
    walk = g._reachable_tiles(g.player.x, g.player.y)
    assert any((npc.x + dx, npc.y + dy) in walk
               for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
    _clear_floor(g, keep=[npc])
    return npc


def _choose(g, npc, option_key):
    from game_states import STATE_NPC_ENCOUNTER, STATE_PLAYER
    g._do_move(*_beside(g, npc))
    assert g.state == STATE_NPC_ENCOUNTER
    g.render()
    g._npc_encounter_input(pygame.K_RETURN)               # text -> options
    assert g._npc_encounter_phase == 'options'
    g._npc_encounter_input(option_key)
    if g._npc_encounter_phase == 'select_item':
        g._npc_encounter_input(pygame.K_a)
    assert g._npc_encounter_phase == 'outcome', g._npc_encounter_phase
    g.render()
    g._npc_encounter_input(pygame.K_RETURN)
    assert g.state == STATE_PLAYER
    assert not npc.alive                                    # spent, not repeatable


def _has(g, item_id):
    return any(getattr(i, 'id', '') == item_id for i in g.player.inventory)


def test_sir_aldrics_lodestone_is_carried_until_an_altar_breaks_it():
    from dungeon import ALTAR
    g = _game('__test_aldric__')
    npc = _meet(g, 4, _npc_def('sir_aldric'))
    karma = g.karma
    _choose(g, npc, pygame.K_1)
    # Taking the stone is a promise (0); keeping it at the altar pays.
    assert _has(g, 'cursed_lodestone') and g.karma == karma
    assert 'sir_aldric' in g._encountered_npcs
    stone = next(i for i in g.player.inventory if i.id == 'cursed_lodestone')
    assert _own_item_art('cursed_lodestone')
    g._do_drop_item(stone)                                # in a corridor: the hand will not open
    assert _has(g, 'cursed_lodestone')
    assert 'Your hand will not open' in _log(g)
    g.dungeon.tiles[g.player.y][g.player.x] = ALTAR       # an altar under the hero
    g._do_drop_item(stone)
    assert not _has(g, 'cursed_lodestone')
    assert not any(getattr(i, 'id', '') == 'cursed_lodestone' for i in g.ground_items)
    assert "Carried Sir Aldric's stone to an altar" in _chron(g)
    assert g.karma == karma + 1
    # He does not come back for a second helping.
    g._change_level(5, enter_from_top=True)
    g._change_level(4, enter_from_top=False)
    assert not [m for m in g.monsters if getattr(m, '_npc_encounter_tag', None) == 'sir_aldric' and m.alive]


def test_the_couriers_dispatch_is_delivered_at_the_watch_post():
    g = _game('__test_courier__')
    npc = _meet(g, 5, _npc_def('dying_messenger'))
    _choose(g, npc, pygame.K_1)
    assert _has(g, 'sealed_dispatch')
    assert _own_item_art('sealed_dispatch')
    gold, karma = g.player_gold, g.karma
    # Before the oath falls due (12 to 18 floors on), or it lapses.
    post = _meet(g, 15, _flavor_def('flv_watch_post'), flavor=True)
    _choose(g, post, pygame.K_1)
    assert not _has(g, 'sealed_dispatch')
    assert g.player_gold > gold and g.karma == karma + 1
    assert "Delivered Edric's dispatch to Sergeant Holt" in _chron(g)


def test_the_watch_post_only_stands_while_a_dispatch_is_owed():
    # Bug 5: the post spawns only while the courier's oath is open.
    g = _game('__test_courier_none__')
    g._flavor_encounter_levels = {33: _flavor_def('flv_watch_post')}
    g._change_level(33, enter_from_top=True)
    assert not [m for m in g.monsters if getattr(m, '_flavor_encounter_tag', None)
                == 'flv_watch_post' and m.alive]


def _keep_chapel_pending(g, floor):
    """Drop every pending callback but the chapel's, and pin that one to
    ``floor``."""
    keep = [p for p in g._deeds['pending']
            if (p.get('spec') or {}).get('encounter') == 'flv_cuthbert_chapel']
    for p in keep:
        p['target'] = p['earliest'] = p['latest'] = floor
    g._deeds['pending'] = keep


def test_saint_cuthberts_gospel_from_bearer_past_broker_to_the_chapel():
    g = _game('__test_gospel__')
    bearer = _meet(g, 42, _flavor_def('flv_coffin_bearer'), flavor=True)
    _choose(g, bearer, pygame.K_1)
    assert _has(g, 'cuthberts_gospel')
    assert _own_item_art('cuthberts_gospel')
    # This test places the follow-ups itself (the scheduled ones would be
    # carried onto the same floors at random targets). The Gate's run-start
    # callback (floors 94-98) is pending in every run.
    assert len([p for p in g._deeds['pending']
                if p.get('source') != 'engine:run_start']) == 2
    # The chapel stays pending, on the floor this test meets it (an oath
    # with no keeper left to come lapses: ENG-08).
    _keep_chapel_pending(g, 55)
    karma = g.karma
    broker = _meet(g, 49, _flavor_def('flv_relic_broker'), flavor=True)
    _choose(g, broker, pygame.K_2)                        # "the book is promised"
    assert _has(g, 'cuthberts_gospel') and g.karma == karma
    chapel = _meet(g, 55, _flavor_def('flv_cuthbert_chapel'), flavor=True)
    from game_states import STATE_PLAYER
    g._do_move(*_beside(g, chapel))
    g._npc_encounter_input(pygame.K_RETURN)
    g._npc_encounter_input(pygame.K_1)                    # lay it on the desk
    assert g._npc_encounter_phase == 'outcome'
    g._npc_encounter_input(pygame.K_RETURN)
    assert g._npc_encounter_phase == 'options'            # the reading may follow
    g._npc_encounter_input(pygame.K_ESCAPE)
    assert g.state == STATE_PLAYER
    assert not _has(g, 'cuthberts_gospel')
    assert g.karma == karma + 1                           # the kept oath's point
    assert "Laid Saint Cuthbert's Gospel on the desk it was meant for" in _chron(g)


def test_selling_the_gospel_to_the_broker_costs_karma_and_pays_gold():
    g = _game('__test_gospel_sold__')
    bearer = _meet(g, 42, _flavor_def('flv_coffin_bearer'), flavor=True)
    _choose(g, bearer, pygame.K_1)
    _keep_chapel_pending(g, 60)              # the broker is placed by hand below
    karma, gold = g.karma, g.player_gold
    broker = _meet(g, 49, _flavor_def('flv_relic_broker'), flavor=True)
    _choose(g, broker, pygame.K_1)
    assert not _has(g, 'cuthberts_gospel')
    assert g.karma == karma - 1 and g.player_gold > gold


def test_the_lost_girls_pendant_spawns_before_her_and_can_be_returned():
    """A triggered encounter: the item lies on the floor above, picking it up
    is what lets her appear, and giving it back is the kind choice."""
    g = _game('__test_pendant__')
    enc = _npc_def('elara_amulet')
    g._npc_encounter_levels = {4: enc}
    g._npc_trigger_item_levels = {'silverlight_pendant': 3}
    g._npc_trigger_items_placed = set()
    g._npc_triggered_items = set()
    g._change_level(3, enter_from_top=True)
    pend = [i for i in g.ground_items if getattr(i, 'id', '') == 'silverlight_pendant']
    assert len(pend) == 1
    assert (pend[0].x, pend[0].y) in g._reachable_tiles(g.player.x, g.player.y)
    assert _own_item_art('silverlight_pendant')
    g.player.x, g.player.y = pend[0].x, pend[0].y
    # Another item can share the tile; each pickup takes one, as in play.
    for _ in range(4):
        if _has(g, 'silverlight_pendant'):
            break
        g._pickup()
    assert _has(g, 'silverlight_pendant')
    assert 'silverlight_pendant' in g._npc_triggered_items
    g._change_level(4, enter_from_top=True)
    girl = [m for m in g.monsters if getattr(m, '_npc_encounter_tag', None) == 'elara_amulet']
    assert len(girl) == 1
    _clear_floor(g, keep=girl)
    karma = g.karma
    _choose(g, girl[0], pygame.K_1)
    assert not _has(g, 'silverlight_pendant') and g.karma == karma + 1


def test_without_the_pendant_the_lost_girl_never_appears():
    g = _game('__test_pendant_none__')
    g._npc_encounter_levels = {4: _npc_def('elara_amulet')}
    g._npc_triggered_items = set()
    g._change_level(4, enter_from_top=True)
    assert not [m for m in g.monsters if getattr(m, '_npc_encounter_tag', None) == 'elara_amulet']


def test_ariadnes_shrine_on_floor_17_opens_to_the_bull_in_the_fountain():
    from dungeon import WALL
    g = _game('__test_ariadne__')
    g._change_level(17, enter_from_top=True)
    d = g.dungeon
    door = d.ariadne_shrine_door
    assert door is not None and d.tiles[door[1]][door[0]] == WALL        # sealed
    thread = [i for i in g.ground_items if getattr(i, 'id', '') == 'ariadnes_thread']
    assert len(thread) == 1 and _own_item_art('ariadnes_thread')
    from items import make_item_by_id
    bull = make_item_by_id('artifact', 'bronze_bull')
    assert bull is not None and _own_item_art('bronze_bull')
    g._activate_ariadne_shrine(bull)
    assert d.tiles[door[1]][door[0]] != WALL
    assert (thread[0].x, thread[0].y) in g._reachable_tiles(g.player.x, g.player.y)


def test_the_sword_of_pelops_calls_the_house_of_atreus_on_a_descent(monkeypatch):
    from items import make_item_by_id
    g = _game('__test_pelops__')
    sword = make_item_by_id('weapon', 'pelops_sword')
    assert sword is not None and getattr(sword, 'cursed_lineage', False)
    assert _own_item_art('pelops_sword')
    # Build floor 2 and go back up BEFORE the sword is worn: with it worn
    # the first descent could already roll an heir (real random), who then
    # waits on the saved floor beside the one this test forces (flaky 1 in 4).
    g._change_level(2, enter_from_top=True)
    g._change_level(1, enter_from_top=False)
    _clear_floor(g)
    g.player.weapon = sword
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    g._change_level(2, enter_from_top=True)
    heirs = [m for m in g.monsters if getattr(m, 'proper_noun', False) and m.name in
             ('Atreus', 'Thyestes', 'Aegisthus', 'Agamemnon', 'Orestes', 'Pelopia', 'Pleisthenes')]
    assert len(heirs) == 1
    assert (heirs[0].x, heirs[0].y) != (g.player.x, g.player.y)
    assert 'House of Atreus stalks you' in _log(g)


def test_chandrahas_leaves_a_wicked_hand(monkeypatch):
    """Shiva's gift. Two uniques carry the name: 'chandrahas' (the T4
    scimitar) holds the karma-vanish proc; 'chandrahasa' (the T5 sword) holds
    the low-HP damage bonus."""
    from items import make_item_by_id
    g = _game('__test_chandrahasa__')
    sword = make_item_by_id('weapon', 'chandrahasa')
    assert sword is not None and getattr(sword, 'low_hp_damage_bonus', False)
    blade = make_item_by_id('weapon', 'chandrahas')
    assert blade is not None and getattr(blade, 'karma_disappear_proc', 0) > 0
    assert _own_item_art('chandrahas') and _own_item_art('chandrahasa')
    g.player.inventory.append(blade)
    g._change_level(2, enter_from_top=True)
    g._change_level(1, enter_from_top=False)
    g.karma = 0
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    g._change_level(2, enter_from_top=True)
    assert blade in g.player.inventory                 # a clean hand keeps it
    g.karma = -1
    g._change_level(1, enter_from_top=False)
    assert blade not in g.player.inventory
    assert 'returns to Shiva' in _log(g)


def _thoth(g):
    from items import make_item_by_id
    book = make_item_by_id('spellbook', 'book_of_thoth')
    assert book is not None
    g.player.inventory.append(book)
    g._read_book_of_thoth(book)
    return book


def test_the_book_of_thoth_read_well_names_the_world():
    from game_states import STATE_PLAYER, STATE_QUIZ
    from items import make_item_by_id
    g = _game('__test_thoth_pass__')
    unknown = make_item_by_id('potion', next(iter(_potion_ids())))
    unknown.identified = False
    g.player.inventory.append(unknown)
    book = _thoth(g)
    assert g.state == STATE_QUIZ and g.quiz_engine.subject == 'grammar'
    g.quiz_engine._end(success=True)
    assert g.state == STATE_PLAYER
    # Not consumed (DEEDS_KARMA_DESIGN 11.12): its power is spent after one
    # read, and it stays until it is laid on an altar to keep the oath.
    assert book in g.player.inventory and book.spent
    assert unknown.identified or int(getattr(unknown, 'id_level', 0)) >= 4
    assert 'the world named itself back to me' in _chron(g)
    assert _own_item_art('book_of_thoth')


def test_the_book_of_thoth_read_badly_brings_the_curse():
    from game_states import STATE_PLAYER
    g = _game('__test_thoth_fail__')
    hp = g.player.hp
    book = _thoth(g)
    g.quiz_engine._end(success=False)
    assert g.state == STATE_PLAYER
    assert book in g.player.inventory and book.spent    # a failed read still owes the return
    assert g.player.hp < hp or g.player.has_effect('stunned')
    assert 'The dead were displeased' in _chron(g)


def test_the_book_of_thoth_can_be_found_in_a_run():
    """Its source is Setne's Tomb (setne_tomb.py, data/setne_tomb.json): a
    sealed room on one floor of 45-65 rolled for every run, where winning at
    senet hands over the book (tests/test_story_engine_hooks.py plays it)."""
    import setne_tomb
    assert setne_tomb.data()['prize_item'] == 'book_of_thoth'
    assert setne_tomb.candidate_floors() and all(45 <= f <= 65 for f in setne_tomb.candidate_floors())
    from game_road import _encounter_by_tag
    _src, enc = _encounter_by_tag(setne_tomb.data()['encounter'])
    # The tomb's own story must be shipped and its prize must be the book
    # (CODE-11: a fallback that only looked for the string anywhere passed
    # with the encounter deleted).
    assert enc is not None, setne_tomb.data()['encounter']
    prizes = [((o.get('pass') or {}).get('reward') or {}).get('item_id')
              for o in enc.get('options') or ()]
    assert 'book_of_thoth' in prizes
    assert enc.get('callback_only'), 'nothing but the tomb places it'


def _potion_ids():
    import json
    with open(os.path.join(ROOT, 'data', 'items', 'potion.json'), encoding='utf-8') as f:
        return list(json.load(f).keys())


# ===========================================================================
# 5. Art for every piece above
# ===========================================================================

SECRET_MONSTERS = (
    'secret_cow', 'hell_bovine', 'cow_king', 'ethereal_unicorn',
    'black_knight', 'black_knight_one_arm', 'black_knight_no_arms',
    'black_knight_one_leg', 'black_knight_torso',
)

SECRET_ITEMS = (
    'magic_dungeon_carrot', 'cow_kings_horns', 'scroll_of_the_pasture',
    'soul_sphere', 'unusual_soul_sphere', 'flesh_wound',
    'cursed_lodestone', 'sealed_dispatch', 'cuthberts_gospel',
    'silverlight_pendant', 'oathkeeper_sword', 'lionheart_shield',
    'ariadnes_thread', 'bronze_bull', 'pelops_sword', 'chandrahasa', 'chandrahas',
    'book_of_thoth', 'merchant_npc',
)


def test_every_secret_creature_and_item_resolves_to_its_own_picture():
    g = _game('__test_secret_art__')
    missing = [m for m in SECRET_MONSTERS if g.renderer._get_sprite(m) is None]
    assert not missing, missing
    not_own = [i for i in SECRET_ITEMS if not _own_item_art(i)]
    assert not not_own, not_own
    # duck_of_doom resolves too (its own file or the documented stand-in)
    assert g.renderer._get_item_sprite('duck_of_doom') is not None


def test_every_encounter_npc_has_its_picture():
    import json
    from monster import Monster  # noqa: F401
    g = _game('__test_npc_art__')
    ids = set()
    for fn in ('npc_encounters.json', 'flavor_encounters.json'):
        with open(os.path.join(ROOT, 'data', fn), encoding='utf-8') as f:
            for e in json.load(f):
                ids.add(e.get('sprite_id', 'npc_traveler'))
    import emberpup_encounter as ep
    ids.add(ep.data()['sprite_id'])
    missing = sorted(i for i in ids if g.renderer._get_sprite(i) is None)
    assert not missing, missing


def test_every_tile_kind_a_secret_floor_uses_has_art():
    from renderer import _TILE_SPRITE
    g = _game('__test_tile_art__')
    missing = [name for name in set(_TILE_SPRITE.values()) | {'rock', 'bridge_h', 'bridge_v'}
               if g.renderer._get_env_sprite(name) is None]
    assert not missing, missing
