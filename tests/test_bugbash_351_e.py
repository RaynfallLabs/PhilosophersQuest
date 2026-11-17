# ruff: noqa: F811  (make_game is a pytest fixture, imported)
"""Bug bash 3.5.1, hunter E (2026-11-15): a teenager's journeys.

Each journey plays the game the way a player does, on a real headless Game:
every step is a key event through ``Game.handle_event``, then ``update()``
and ``render()``, as the game loop does (the driver and its helpers are
tests/test_bugbash_wb_e.py's). Quizzes are answered by pressing the number of
the right (or a wrong) choice. The lines the game printed are read back.

A test that pins a bug names it (351-Enn in the hunter's report). Unit tests
cannot say whether it feels right: that is Brandon's play-test.
"""
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402
import pytest  # noqa: E402

from test_bugbash_wb_e import (  # noqa: E402,F401  (make_game is a fixture)
    blow, make_game, no_errors, open_floor, pick, place_monster, reload,
)


# ---------------------------------------------------------------------------
# The walk: a player heads for a place, opening doors on the way
# ---------------------------------------------------------------------------

def _path(g, start, goal, blocked):
    from dungeon import DOOR
    d = g.dungeon
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur in goal:
            step = cur
            while prev[step] != start:
                step = prev[step]
            return step
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in prev or nxt in blocked:
                continue
            if not (d.is_walkable(*nxt) or (d.in_bounds(*nxt) and d.tiles[nxt[1]][nxt[0]] == DOOR)):
                continue
            prev[nxt] = cur
            q.append(nxt)
    return None


def step_to(h, tx, ty, adjacent=True):
    """One step along the shortest path to (tx, ty), or to a tile beside it
    (walking into a closed door opens it; into a creature in the way, a
    blow). True if he acted or is there; False when there is no way."""
    g = h.g
    p = g.player
    goal = ({(tx + dx, ty + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
            if adjacent else {(tx, ty)})
    start = (p.x, p.y)
    if start in goal:
        return True
    living = {(m.x, m.y): m for m in g.monsters if getattr(m, 'alive', False)}
    step = _path(g, start, goal, set(living)) or _path(g, start, goal, set())
    if step is None:
        return False
    if step in living:
        m = living[step]
        if getattr(m, 'is_allied', False) or getattr(m, '_npc_encounter_tag', None)                 or getattr(m, '_flavor_encounter_tag', None):
            return False
        blow(h, m, 3)
        return True
    h.move(step[0] - p.x, step[1] - p.y)
    return True


def foes_beside(g):
    p = g.player
    return [m for m in g.monsters if m.alive and not getattr(m, 'is_allied', False)
            and not getattr(m, '_npc_encounter_tag', None)
            and not getattr(m, '_flavor_encounter_tag', None)
            and abs(m.x - p.x) + abs(m.y - p.y) == 1]


def fight_to(h, target, chain=3, limit=1500):
    """Walk to ``target`` and kill it, fighting whatever stands in the way
    (each blow ``chain`` right answers, then a wrong one). The lines said."""
    g = h.g
    p = g.player
    said = []
    for _ in range(limit):
        if not target.alive or p.is_dead():
            break
        if g.state != 'player':
            h.key(pygame.K_RETURN)               # a popup or a Keep-going? ask
            said += h.said()
            continue
        keep_fed(h)
        near = foes_beside(g)
        if near:
            said += blow(h, target if target in near else near[0], chain)
        elif not step_to(h, target.x, target.y):
            h.wait()                             # something in the corridor: let it come
            said += h.said()
        else:
            said += h.said()
    return said


def go_to(h, x, y, limit=400):
    g = h.g
    for _ in range(limit):
        if (g.player.x, g.player.y) == (x, y):
            return
        if g.state != 'player':
            h.key(pygame.K_RETURN)
            continue
        keep_fed(h)
        if not step_to(h, x, y, adjacent=False):
            h.wait()
    raise AssertionError((f'never reached {(x, y)} from {(g.player.x, g.player.y)}', h.peek()[-6:]))


def wield_the_sword(h):
    """The starting sword in the hand: since 2026-11-16 the hero starts
    holding it (UI-1); one in the pack is wielded with E, as before."""
    import items
    g = h.g
    if isinstance(g.player.weapon, items.Weapon):
        return g.player.weapon
    sword = next(i for i in g.player.inventory if isinstance(i, items.Weapon))
    h.key('e')
    pick(h, sword, g._get_equip_tab_items)
    assert g.player.weapon is sword
    return sword


def bestiary_page(h, kind):
    """B, the Bestiary (a), Down to ``kind``, Enter: the page's lines as the
    screen draws them."""
    g = h.g
    h.key('b')
    assert g.state == 'encyclopedia'
    h.key('a')
    assert g.encyclopedia_category == 'bestiary'
    want = next(i for i, e in enumerate(g.encyclopedia_entries) if e.get('_id') == kind)
    while g.encyclopedia_selection < want:
        h.key(pygame.K_DOWN)
    h.key(pygame.K_RETURN)
    entry = g._encyclopedia_entry
    assert entry is not None and entry.get('_id') == kind
    return [str(t) for t, *_ in g._encyclopedia_article_lines('bestiary', entry)]


ROW_HEADS = ('Weak To', 'Resists', 'Shrugs Off',
             'Hurt Most By')


# ---------------------------------------------------------------------------
# Journey 1: floor 1, a war-band, a corpse studied, the Bestiary
# ---------------------------------------------------------------------------

def test_journey_01_a_war_band_on_floor_one(make_game, monkeypatch):
    """A new hero on floor 1 hears the band camped there, wields his sword,
    walks to the camp and kills its leader, studies the leader's corpse (I)
    and reads its kind on the Bestiary page (B): the damage rows for the
    kind he knows, none of them for a kind he has only seen."""
    import affinity
    import war_bands
    monkeypatch.setitem(war_bands.data(), 'chance', 1.0)        # the band camps here
    for seed in range(4, 40):                    # a floor with a room big enough for a camp
        g, h = make_game(seed=seed, clear=False, name='__bb351_e1__')
        if getattr(g.dungeon, 'band', None):
            break
    p = g.player
    band = g.dungeon.band
    heard = [str(e[0]) for e in g.msg_log.entries]
    assert war_bands.data()['bands'][band['id']]['line'] in heard
    alive = [m for m in g.monsters if m.alive]
    assert len(alive) >= 8
    p.hp = p.max_hp = 600                                        # the walk is the test, not the odds
    wield_the_sword(h)
    lead = war_bands.leader_of(g.monsters, band['uid'])
    said = fight_to(h, lead)
    assert not lead.alive, said
    # 351-E02: the band answers its leader's fall after he falls (said
    # when he can see one of them run: test_351_e02 sets that scene).
    rout = war_bands.data()['bands'][band['id']]['rout_line']
    slain = f"The {lead.name.title()} is slain!"
    assert slain in said, said
    if rout in said:
        assert said.index(slain) < said.index(rout), said
    # His corpse, studied: the page of a kind he knows.
    hob_page = study_and_read(h, lead)
    assert not any('not yet studied' in t.lower() for t in hob_page), hob_page
    # A kind with something to say of the blow (a skeleton, a stirge swarm:
    # the first such one on the floor), killed, studied and read.
    def reach(m):
        goal = {(m.x + dx, m.y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
        return _path(g, (p.x, p.y), goal, set()) is not None
    # (One that runs from the hero, a cowardly leprechaun, is never caught by
    # a walk: the floor's first creature that stands and fights is taken.)
    other = min((m for m in g.monsters if m.alive and not getattr(m, 'is_allied', False)
                 and m.kind in monster_defs()
                 and getattr(m, 'ai_pattern', '') not in ('cowardly', 'hit_and_run', 'flee')
                 and affinity.damage_profile({**monster_defs()[m.kind]}) and reach(m)),
                key=lambda m: abs(m.x - p.x) + abs(m.y - p.y), default=None)
    if other is None:
        open_floor(g, p.x, p.y, 2)
        other = place_monster(g, 'stirge_swarm', 2)
    said = fight_to(h, other)
    assert not other.alive, said
    page = study_and_read(h, other)
    rows = [t for _k, t in affinity.bestiary_rows({**monster_defs()[other.kind]})]
    assert any(t.startswith(ROW_HEADS) for t in rows)
    for t in rows:
        assert t in page, (t, page)
    # A kind he has only seen: no rows, only that it is not yet studied.
    seen = [k for k in p.known_monster_ids
            if k not in p.studied_monster_ids and k in monster_defs()
            and affinity.damage_profile({**monster_defs()[k]})]
    if not seen:                                 # one more kind comes into view
        open_floor(g, p.x, p.y, 3)
        place_monster(g, 'skeleton' if other.kind != 'skeleton' else 'stirge_swarm', 3)
        h.wait()
        seen = [k for k in p.known_monster_ids if k not in p.studied_monster_ids
                and k in monster_defs() and affinity.damage_profile({**monster_defs()[k]})]
    assert seen
    for kind in seen[:3]:
        page = bestiary_page(h, kind)
        assert not any(t.startswith(ROW_HEADS) for t in page), (kind, page)
        assert any('not yet studied' in t.lower() for t in page), (kind, page)
        while g.state != 'player':
            h.key(pygame.K_ESCAPE)
    # Tab: the Families, the studied kind's family page.
    import family_lore
    fid = family_lore.family_of({**monster_defs()[other.kind], 'id': other.kind})
    h.key('b')
    h.key('a')
    h.key(pygame.K_TAB)
    want = next(i for i, e in enumerate(g.encyclopedia_entries) if e.get('_family') == fid)
    while g.encyclopedia_selection < want:
        h.key(pygame.K_DOWN)
    h.key(pygame.K_RETURN)
    fam = [str(t) for t, *_ in g._encyclopedia_article_lines('bestiary', g._encyclopedia_entry)]
    assert any(t.startswith('Kinds studied: 1') for t in fam), fam
    while g.state != 'player':
        h.key(pygame.K_ESCAPE)
    no_errors(h)


def study_and_read(h, dead):
    """Walk onto ``dead``'s corpse, I, its letter, the philosophy quiz; then
    the kind's Bestiary page (B)."""
    import items
    g = h.g
    corpse = next((i for i in g.ground_items if isinstance(i, items.Corpse)
                   and getattr(i, 'monster_id', '') == dead.kind), None)
    assert corpse is not None, dead.kind
    go_to(h, corpse.x, corpse.y)
    h.said()
    h.key('i')
    assert g.state == 'identify_menu', h.said()
    entry = next(n for n, e in enumerate(g.identify_menu_items) if e[0] is corpse)
    h.key(getattr(pygame, f'K_{chr(97 + entry)}'))
    assert h.in_quiz() and 'PHILOSOPHY' in g.quiz_title
    h.quiz(5)
    said = h.said()
    assert any(s.startswith('You understand the ') for s in said), said
    while g.state != 'player':
        h.key(pygame.K_ESCAPE)
    page = bestiary_page(h, dead.kind)
    while g.state != 'player':
        h.key(pygame.K_ESCAPE)
    return page


_DEFS = None


def monster_defs():
    global _DEFS
    if _DEFS is None:
        import json
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'data', 'monsters.json'), encoding='utf-8') as f:
            _DEFS = json.load(f)
    return _DEFS


# ---------------------------------------------------------------------------
# The bugs the journeys found (each failed before its fix)
# ---------------------------------------------------------------------------

def test_351_e01_a_thing_on_the_floor_is_named_with_one_article(make_game):
    """"You see an A Rough Amber Pelt of Unnatural Density lying here." (an
    unknown piece brings its own article) and "You see a 5 Gold Coins lying
    here." Walked onto, one by one, then two together."""
    import items
    from items import GoldPile
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 4)
    pelt = next(i for i in items.load_items('armor')
                if str(getattr(i, 'unidentified_name', '')).lower().startswith('a '))
    assert not g._item_is_known(pelt)
    shown = g._display_name(pelt)
    assert shown.startswith('A ')
    pelt.x, pelt.y = p.x + 1, p.y
    g.ground_items.append(pelt)
    g.ground_items.append(GoldPile(5, p.x + 2, p.y))
    jerkin = items.instantiate_armor('leather', 'leather')
    h.move(1, 0)
    assert h.said() == [f"You see a {shown[2:]} lying here."]
    h.move(1, 0)
    assert h.said() == ['You see 5 Gold Coins lying here.']
    pelt.x, pelt.y = p.x + 1, p.y
    jerkin.x, jerkin.y = p.x + 1, p.y
    g.ground_items.append(jerkin)
    h.move(1, 0)
    said = h.said()
    assert said[0] in (f"You see a {shown[2:]} and a Worn Leather Jerkin lying here.",
                       f"You see a Worn Leather Jerkin and a {shown[2:]} lying here."), said
    no_errors(h)


def test_351_e01_the_article_rule():
    from game_helpers import a_or_an
    assert a_or_an('A Rough Amber Pelt') == 'a Rough Amber Pelt'
    assert a_or_an('An Iron-Bound Book') == 'an Iron-Bound Book'
    assert a_or_an('Iron Shortsword') == 'an Iron Shortsword'
    assert a_or_an('Worn Cap') == 'a Worn Cap'
    assert a_or_an('5 Gold Coins') == '5 Gold Coins'
    assert a_or_an('The Book of Thoth') == 'The Book of Thoth'
    assert a_or_an('Amulet') == 'an Amulet'
    # A plural thing takes none: "It drops a Rough Cloth Gloves!", "an
    # Untanned Bracers" (the soak, floors 1-5).
    assert a_or_an('Rough Cloth Gloves') == 'Rough Cloth Gloves'
    assert a_or_an('Untanned Bracers') == 'Untanned Bracers'
    assert a_or_an('Boots of Hermes') == 'Boots of Hermes'
    assert a_or_an('A Pair of Heavy Iron Boots') == 'a Pair of Heavy Iron Boots'
    for one in ('Aegis', 'Haggis', 'Caduceus', 'Cyclops', 'Rod of Asclepius', 'Glass Orb'):
        assert a_or_an(one).startswith(('a ', 'an ')), one


def test_351_e03_an_unseen_sense_is_said_once_a_turn(make_game):
    """Two kinds out of sight that both have the hero's scent on one turn:
    "Somewhere close, something sniffs the air, and stops." twice in a row.
    Once is all a line that names nothing can say."""
    import senses
    from dungeon import WALL
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 4)
    for yy in range(p.y - 4, p.y + 5):                   # a wall between them and him
        g.dungeon.tiles[yy][p.x + 2] = WALL
    rat = place_monster(g, 'giant_rat', 3, -1)
    stirge = place_monster(g, 'stirge_swarm', 3, 1)
    for m in (rat, stirge):
        m.status_effects.pop('sleeping', None)
    g._refresh_fov()
    assert not g._sees_monster(rat) and not g._sees_monster(stirge)
    line = senses.sense_line('scent', 'unseen')
    h.wait()
    said = h.said()
    assert said.count(line) == 1, said
    no_errors(h)


def test_351_e02_the_band_breaks_after_its_leader_falls(make_game, monkeypatch):
    """A hobgoblin and his goblin, both in sight; the hobgoblin cut down:
    "With the hobgoblin down, the scouts forget their orders and scatter!"
    was said before "The Hobgoblin is slain!"."""
    import war_bands
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 4)
    lead = place_monster(g, 'hobgoblin', 1)
    gob = place_monster(g, 'goblin', 3)
    uid = 'goblin_scouts@test'
    for m, role in ((lead, 'leader'), (gob, 'guard')):
        m._band, m._band_id, m._band_role = uid, 'goblin_scouts', role
    gob._band_leader = lead
    lead.hp = 1
    g._refresh_fov()
    h.said()
    said = blow(h, lead, 3)
    rout = war_bands.data()['bands']['goblin_scouts']['rout_line']
    assert 'The Hobgoblin is slain!' in said and rout in said, said
    assert said.index('The Hobgoblin is slain!') < said.index(rout), said
    assert gob.has_effect('feared')
    no_errors(h)


# ---------------------------------------------------------------------------
# Journey 2: the floor's clock (src/wanderers.py)
# ---------------------------------------------------------------------------

def _stair(g, tile):
    d = g.dungeon
    return next((x, y) for y in range(d.height) for x in range(d.width) if d.tiles[y][x] == tile)


def _newcomers(g, before):
    return [m for m in g.monsters if m not in before and m.alive
            and not getattr(m, 'is_allied', False)]


def explore(h):
    """Every room of the floor seen, nearest first (where a full explore
    stands: wanderers._room_stop), then the down stair."""
    import wanderers
    from dungeon import STAIRS_DOWN
    g = h.g
    ok = wanderers._walk_map(g.dungeon)
    todo = [s for s in (wanderers._room_stop(r, ok) for r in g.dungeon.rooms) if s]
    while todo:
        p = g.player
        dist = wanderers._distances(ok, (p.x, p.y))
        reach = [t for t in todo if t in dist]
        if not reach:
            break
        nxt = min(reach, key=dist.__getitem__)
        todo.remove(nxt)
        go_to(h, *nxt)
    go_to(h, *_stair(g, STAIRS_DOWN))


def keep_fed(h):
    """Hungry: U and the first thing to eat (a ration from home when the
    pack has none: the walking and waiting are the test, not the larder)."""
    import items
    from items import Food
    g = h.g
    p = g.player
    if p.sp > 20 or g.state != 'player':
        return
    if not any(isinstance(i, Food) for i in p.inventory):
        p.inventory.append(items.make_item_by_id('food', 'bread_ration'))
    h.key('u')
    assert g.state == 'eat_menu', g.state
    h.key('a')


def linger(h, until, limit=3000):
    """Wait a turn at a time until ``until()`` holds, eating when hungry;
    the turns waited."""
    for n in range(limit):
        if until():
            return n
        keep_fed(h)
        h.wait()
    import wanderers
    raise AssertionError(('waited in vain', h.g.state, h.g.turn_count, h.g.dungeon_level,
                          wanderers.clock(h.g.dungeon), wanderers.grace(h.g.dungeon),
                          len(h.g.monsters), h.peek()[-8:]))


class Ears:
    """Every line the game says, however long the journey (the log keeps
    its last 500, so Hero.said's place in it is lost on a long wait)."""

    def __init__(self, g):
        self.heard = []
        real = g.msg_log.add

        def add(text, msg_type='info'):
            self.heard.append(str(text))
            return real(text, msg_type)
        g.msg_log.add = add

    def take(self):
        out, self.heard = self.heard, []
        return out


def test_journey_02_the_floors_clock(make_game):
    """Floor 1 explored room by room and left by the down stair with no
    newcomer; floor 2 explored and lingered on: one warning near the end of
    the grace, then the stirring line said with the first newcomer that
    really comes; up to floor 1 for a long while (a trader's) and back down:
    floor 2 has settled, a full tour of quiet before the next."""
    import floor_curve
    import wanderers
    from dungeon import STAIRS_UP
    g, h = make_game(seed=11)
    ears = Ears(g)
    p = g.player
    p.hp = p.max_hp = 400
    lines = wanderers._lines()
    warn, stirs = set(lines['warning']), set(lines['stirs'])
    start = g.turn_count
    explore(h)
    said = ears.take()
    walked = g.turn_count - start
    assert walked < wanderers.grace(g.dungeon), (walked, wanderers.grace(g.dungeon))
    assert not _newcomers(g, []), [m.kind for m in g.monsters]
    assert not (set(said) & (warn | stirs)), said
    h.key(pygame.K_PERIOD, '>')
    assert g.dungeon_level == 2
    g.monsters = []                                  # watch only the newcomers
    floor2 = g.dungeon
    grace = wanderers.grace(floor2)
    clock = wanderers.clock(floor2)
    explore(h)                                       # floor 2 seen, then he stays
    assert not (set(ears.heard) & (warn | stirs))
    # Linger: the warning, once, near the end of the grace.
    linger(h, lambda: clock['warned'])
    said = ears.take()
    assert sum(1 for s in said if s in warn) == 1, said
    assert clock['here'] == int(grace * floor_curve.WANDER_WARN_SHARE)
    assert not _newcomers(g, []) and not (set(said) & stirs)
    # Then the first newcomer, and the stirring line with him.
    linger(h, lambda: _newcomers(g, []))
    said = ears.take()
    assert clock['here'] >= grace
    assert sum(1 for s in said if s in stirs) == 1, said
    assert said[-1] in stirs or any(s in stirs for s in said[-3:]), said
    assert not (set(said) & warn), said
    g.monsters = []                                  # he deals with it
    # Up to floor 1 for a long while, and back down.
    go_to(h, *_stair(g, STAIRS_UP))
    h.key(pygame.K_COMMA, '<')
    assert g.dungeon_level == 1
    back_at = g.turn_count + 600
    g.monsters = []
    linger(h, lambda: g.turn_count >= back_at)
    h.key(pygame.K_PERIOD, '>')
    assert g.dungeon_level == 2 and g.dungeon is floor2
    g.monsters = []
    ears.take()
    back = g.turn_count
    linger(h, lambda: _newcomers(g, []))
    quiet = g.turn_count - back
    # (The turn he came down on is one of them.)
    assert quiet >= max(100, wanderers.explore_tour(g.dungeon)) - 1, quiet
    said = ears.take()
    # The floor stirs again: he was warned again on the way, then told.
    assert sum(1 for s in said if s in warn) == 1, said
    assert sum(1 for s in said if s in stirs) == 1, said
    assert [s for s in said if s in warn | stirs][0] in warn, said
    no_errors(h)


# ---------------------------------------------------------------------------
# Journey 3: harvest, cook, eat, cook to carry, save and load, sell
# ---------------------------------------------------------------------------

def cook_menu_pick(h, pred):
    """C is open: Right through the tabs to the first row ``pred`` accepts,
    Down to it, Enter."""
    import kitchen
    g = h.g
    assert g.state == 'cook_menu', g.state
    for _ in range(len(kitchen.MENU_TABS) + 1):
        rows = g._cook_tab_rows()
        if any(pred(r) for r in rows):
            break
        h.key(pygame.K_RIGHT)
    rows = g._cook_tab_rows()
    want = next(i for i, r in enumerate(rows) if pred(r))
    while g._cook_sel < want:
        h.key(pygame.K_DOWN)
    h.key(pygame.K_RETURN)
    return rows[want]


def harvest_here(h):
    """H on the corpse underfoot, the animal question answered right: the
    ingredient it gave."""
    import items
    g = h.g
    before = list(g.player.inventory)
    h.key('h')
    assert h.in_quiz() and 'ANIMAL' in g.quiz_title, g.state
    h.quiz(1)
    got = [i for i in g.player.inventory if i not in before]
    if not got:          # a stack: the count went up instead
        got = [i for i in g.player.inventory if isinstance(i, items.Ingredient)]
    return got[0] if got else None


def test_journey_03_from_the_corpse_to_the_counter(make_game):
    """Two giant rats killed and harvested (H, one animal question each);
    C, a ready dish of the rat cooked and eaten; a Starnut Tart cooked to
    carry; saved and loaded; the second rat's meat sold to an apothecary,
    and the tart, which the Mooble is owed, not for sale."""
    import items
    import kitchen
    import random as _r
    from mystery_system import build_trader
    from test_bugbash_wb_e import shop_tab, shop_pick
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 4)
    wield_the_sword(h)
    meat = None
    for dx in (2, -2):
        rat = place_monster(g, 'giant_rat', dx)
        g._refresh_fov()
        said = fight_to(h, rat)
        assert not rat.alive, said
        corpse = next(i for i in g.ground_items if isinstance(i, items.Corpse))
        go_to(h, corpse.x, corpse.y)
        h.said()
        meat = harvest_here(h) or meat
        assert corpse not in g.ground_items
    assert meat is not None and int(getattr(meat, 'count', 1) or 1) == 2, h.said()
    # C: a dish of the rat is ready.
    p.sp = p.max_sp // 3                                   # a long walk behind him
    h.key('c')
    assert g.state == 'cook_menu'
    sp_before = p.sp
    row = cook_menu_pick(h, lambda r: r['ready'] and kitchen.resolve(meat.id) in kitchen.parts(r['recipe']))
    assert h.in_quiz() and 'COOKING' in g.quiz_title
    h.quiz(1)
    said = h.said()
    assert g.state == 'player', g.state
    assert p.sp > sp_before, (said, row['recipe']['name'])
    assert row['recipe']['name'] in g._cooked_recipes
    assert meat in p.inventory and int(meat.count) == 1, said
    # Cook to carry: a Starnut Tart (a starnut, bread and an apple).
    for fid in ('bread_ration', 'apple'):
        p.inventory.append(items.make_item_by_id('food', fid))
    p.inventory.append(items.make_item_by_id('ingredient', 'starnut'))
    h.key('c')
    row = cook_menu_pick(h, lambda r: r['ready'] and kitchen.makes(r['recipe']))
    h.quiz(1)
    said = h.said()
    assert 'You wrap the Starnut Tart to carry. It is in your pack.' in said, said
    # Saved and loaded: the tart and the meat are still in the pack.
    g = reload(h)
    p = g.player
    tart = next(i for i in p.inventory if getattr(i, 'id', '') == 'starnut_tart')
    meat = next(i for i in p.inventory if isinstance(i, items.Ingredient))
    assert g._display_name(tart) == 'Starnut Tart'
    # Sold: an apothecary beside him, Y, the Sell tab, the meat.
    open_floor(g, p.x, p.y, 3)
    trader = build_trader('apothecary', 1, _r.Random(3))
    trader.x, trader.y = p.x + 1, p.y
    g.ground_items.append(trader)
    gold = g.player_gold
    h.key('y')
    assert g.state == 'shop', g.state
    h.said()
    shop_tab(h, 1)
    price, why = g._trader_offer(meat)
    assert why is None and price > 0, why
    assert g._trader_offer(tart) == (0, 'Not for sale')
    shop_pick(h, lambda r: r is meat)
    said = h.said()
    assert meat not in p.inventory, said
    assert g.player_gold == gold + price, (gold, price, g.player_gold, said)
    no_errors(h)


def _trader_kinds():
    import traders
    return list(traders.data().get('traders', {}).keys()) if hasattr(traders, 'data') else []


def test_351_e04_a_loaded_save_does_not_greet_a_new_hero(make_game, monkeypatch):
    """Saved on floor 3, loaded: the log read "Welcome, ...! Find the
    Philosopher's Stone and escape!", the domain line of floor 1 and any
    war-band of the throwaway floor 1 the load builds and drops."""
    import war_bands
    from test_bugbash_wb_e import warp
    monkeypatch.setitem(war_bands.data(), 'chance', 1.0)    # the shell's floor 1 has a band
    g, h = make_game(build='titivillus', name='Titivillus')
    warp(h, 3)
    g = reload(h)
    log = [str(e[0]) for e in g.msg_log.entries]
    assert not any(s.startswith('Welcome, ') for s in log), log
    assert "Find the Philosopher's Stone and escape!" not in log, log
    bands = {b['line'] for b in war_bands.data()['bands'].values()}
    here = getattr(g.dungeon, 'band', None)
    mine = war_bands.data()['bands'][here['id']]['line'] if here else None
    assert not any(s in bands and s != mine for s in log), log
    no_errors(h)


# ---------------------------------------------------------------------------
# Journey 4: the quiz's damage counter on a kind he knows to be weak
# ---------------------------------------------------------------------------

class StripReader:
    """What the combat strip draws: every text fitted into a slot of it
    (game_render._fit_line), frame by frame."""

    def __init__(self, g):
        self.texts = []
        real = g._fit_line

        def fit(text, *a, **k):
            self.texts.append(str(text))
            return real(text, *a, **k)
        g._fit_line = fit

    def frame(self, h):
        self.texts = []
        h.frame()
        return list(self.texts)


def test_journey_04_the_counter_is_the_blow(make_game):
    """A mace in hand, a skeleton he has studied (weak to blunt): walking
    into it, the quiz's strip says "Weakness (Double): Blunt" and, after
    each right answer, a number; the wrong answer strikes, and the blow is
    the number last shown. A goblin, nothing special: plain "Blunt"."""
    import re
    import items
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 4)
    mace = items.instantiate_weapon('mace', 'iron')
    p.inventory.append(mace)
    h.key('e')
    pick(h, mace, g._get_equip_tab_items)
    assert p.weapon is mace
    p.studied_monster_ids.add('skeleton')
    p.lore_known_monster_ids.add('skeleton')
    strip = StripReader(g)
    for kind, tag in (('skeleton', 'Weakness: Blunt'), ('goblin', 'Blunt')):
        m = place_monster(g, kind, 1)
        m.hp = m.max_hp = 10 ** 6
        g._refresh_fov()
        h.said()
        h.move(1, 0)
        assert h.in_quiz(), g.state
        shown = None
        for chain in range(1, 5):
            h.answer(True)
            texts = strip.frame(h)
            assert tag in texts, (kind, texts)
            nums = [int(t.split()[0]) for t in texts if re.fullmatch(r'\d+ Damage', t)]
            assert nums, texts
            shown = nums[0]
        h.answer(False)
        said = h.said()
        dealt = next(int(re.search(r'for (\d+) damage', s).group(1)) for s in said
                     if s.startswith('Chain x4! You strike'))
        assert dealt == shown, (kind, shown, dealt, said)
        assert m.max_hp - m.hp == dealt
        g.monsters = []
    no_errors(h)


# ---------------------------------------------------------------------------
# Journey 5: armour, the load tiers, the kits, the weapon at his back
# ---------------------------------------------------------------------------

def test_journey_05_plate_a_full_pack_and_two_kits(make_game):
    """Steel plate on (four geography answers): a Light load. Ringmail and
    a mace picked up: Heavy or worse, and slower (since 2026-11-16 the load
    costs speed: a step is still one action, the world gets more turns).
    Kit One saved in plate (Shift+E, S); the ringmail
    dropped, leather on, Kit Two saved; Kit One put back on. The mace at
    his back dropped and picked up: back at his back."""
    import items
    import known_by_hand as kbh
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 6)
    sword = wield_the_sword(h)
    h.said()
    plate = drop_here_(g, items.instantiate_armor('plate', 'chain_steel'))
    h.key('g')
    assert plate in p.inventory
    h.key('e')
    pick(h, plate, g._get_equip_tab_items)
    assert h.in_quiz() and 'GEOGRAPHY' in g.quiz_title
    h.quiz(4)
    while g.state == 'ask':
        h.key('y')
    for _ in range(12):                                 # the plate's turns
        if body_(g) is plate:
            break
        h.wait()
    assert body_(g) is plate, h.said()
    said = h.said()
    tier = p.load_tier()
    if tier == 'light':
        assert any(s.startswith('Your load is Light.') for s in said), said
    # Ringmail and a mace: Heavy or worse.
    spare = drop_here_(g, items.instantiate_armor('ringmail', 'chain_steel'))
    mace = drop_here_(g, items.instantiate_weapon('mace', 'iron'))
    for _ in range(4):
        if spare in p.inventory and mace in p.inventory:
            break
        h.key('g')
    said = h.said()
    slowed = ('heavy', 'burdened', 'overloaded')
    assert spare in p.inventory or p.load_tier() in slowed, said
    assert p.load_tier() in slowed, (p.get_current_weight(), p.get_carry_limit())
    assert any(s.startswith(('Your load is Heavy.', 'You are Burdened.', 'You are Overloaded.'))
               for s in said), said
    # A slowed hero: a step is one action, but the world takes more turns.
    assert p.get_speed() < 10.0
    t0 = g.turn_count
    for dx in (1, -1, 1, -1):
        h.move(dx, 0)
    assert g.turn_count - t0 == 4, g.turn_count - t0
    # The mace At Your Back (Kit, R).
    if mace in p.inventory:
        h.key('k')
        kit_select_(h, mace)
        h.key('r')
        h.key(pygame.K_ESCAPE)
        assert p.readied_weapon is mace
    h.said()
    # Kit One: plate, sword, mace at his back.
    h.shift('E')
    assert g.state == 'loadouts'
    h.key(pygame.K_RETURN)
    h.key('s')
    said = h.said()
    assert any(s.startswith('Kit One saved') for s in said), said
    h.key(pygame.K_ESCAPE)
    # The ringmail dropped: no longer Burdened.
    h.key('d')
    pick(h, spare, g._get_drop_tab_items)
    said = h.said()
    assert spare in g.ground_items and p.load_tier() in ('', 'light'), said
    assert any(s.startswith(('Your load is no longer Heavy', 'You are no longer Burdened',
                             'You are no longer Overloaded'))
               for s in said), said
    # Leather on (plate off first), and Kit Two saved.
    jerkin = items.instantiate_armor('leather', 'leather')
    kbh.learn(p, jerkin)
    p.inventory.append(jerkin)
    h.key('e')
    pick(h, jerkin, g._get_equip_tab_items)
    for _ in range(16):
        if body_(g) is jerkin:
            break
        if g.state == 'ask':
            h.key('y')
        else:
            h.wait()
    assert body_(g) is jerkin, h.said()
    h.said()
    h.shift('E')
    h.key(pygame.K_DOWN)
    h.key(pygame.K_RETURN)
    h.key('s')
    assert any(s.startswith('Kit Two saved') for s in h.said())
    h.key(pygame.K_ESCAPE)
    # Back into Kit One: the plate goes on again, known by hand.
    h.shift('E')
    h.key('1')
    h.key(pygame.K_RETURN)
    assert g.state == 'ask', (g.state, h.said())
    h.key('y')
    for _ in range(20):
        if body_(g) is plate:
            break
        if g.state == 'ask':
            h.key('y')
        else:
            h.wait()
    said = h.said()
    assert body_(g) is plate and p.weapon is sword, said
    assert p.readied_weapon is mace, said
    # The mace at his back dropped and picked up again: back in its place.
    h.key('d')
    pick(h, mace, g._get_drop_tab_items)
    assert mace in g.ground_items and p.readied_weapon is None
    h.said()
    h.key('g')
    said = h.said()
    assert mace in p.inventory and p.readied_weapon is mace, said
    no_errors(h)


def drop_here_(g, item):
    item.x, item.y = g.player.x, g.player.y
    g.ground_items.append(item)
    return item


def body_(g):
    from items import ARMOR_SLOTS
    return g.player.armor_slots[ARMOR_SLOTS.index('body')]


def kit_select_(h, item):
    from test_bugbash_wb_e import kit_select
    kit_select(h, item)


# ---------------------------------------------------------------------------
# Journey 6: a death, the score, a new start, the Seeker's badges
# ---------------------------------------------------------------------------

@pytest.fixture
def a_seeker(tmp_path, monkeypatch):
    """Robyn is the Seeker at the keyboard (a profile of her own, in a
    folder of the test's; the codes' key is a test key)."""
    import highscore_system
    import seeker_codes
    import seeker_profile
    saved = seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE
    seeker_codes._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}
    seeker_profile._DIR_OVERRIDE = str(tmp_path / 'seekers')
    monkeypatch.setattr(highscore_system, '_SCORE_FILE', str(tmp_path / 'highscores.json'))
    seeker_profile.set_active('Robyn')
    yield 'Robyn'
    seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE = saved
    import counters
    counters.ON_COUNTER = None


def test_journey_06_a_short_story(make_game, a_seeker):
    """A new hero puts his sword away and punches a giant rat to death (he
    starts holding it since 2026-11-16; it used to start in the pack), then
    falls to a goblin on floor 1: the death screen, the score in
    the table, Esc to the title, a new hero of the same name on floor 1,
    and the Seeker Profile (F4) with Bare Knuckles and A Very Short Story
    won."""
    import highscore_system
    import save_system
    import seeker_screen
    from game_states import STATE_DEAD
    g, h = make_game(name='Wat')
    p = g.player
    open_floor(g, p.x, p.y, 4)
    from test_bugbash_wb_e import unequip
    assert p.weapon is not None                 # his sword, in his hand
    unequip(h, p.weapon)
    assert p.weapon is None
    rat = place_monster(g, 'giant_rat', 2)
    g._refresh_fov()
    said = fight_to(h, rat)
    assert not rat.alive, said
    save_system.save_game(g)
    assert save_system.save_exists('Wat')
    # A goblin, and nothing left in him.
    gob = place_monster(g, 'goblin', 1)
    g._refresh_fov()
    p.hp = 1
    for _ in range(60):
        if g.state == STATE_DEAD or p.is_dead():
            break
        if g.state != 'player':
            h.key(pygame.K_RETURN)
        else:
            h.wait()
    for _ in range(10):                     # a popup (the last words) first
        if g.state == STATE_DEAD:
            break
        h.key(pygame.K_RETURN)
    assert g.state == STATE_DEAD, (g.state, h.said())
    for _ in range(3):
        h.frame()                           # the death screen draws
    assert gob.alive
    assert not save_system.save_exists('Wat')
    rows = [r for r in highscore_system.get_scores() if r.get('name') == 'Wat']
    assert len(rows) == 1 and rows[0]['level'] == 1, rows
    assert rows[0]['kills'] >= 1
    # Esc: back to the title (handle_event says the run is over).
    out = g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE,
                                            unicode='', mod=0, scancode=0))
    assert out is False
    g._seeker_flush()
    # A new hero of the same name: a fresh floor 1.
    g2, h2 = make_game(name='Wat')
    assert g2.dungeon_level == 1 and g2.player.hp == g2.player.max_hp
    assert not any(isinstance(i, type(rat)) for i in g2.player.inventory)
    # The Seeker Profile (title, F4): the badges are hers.
    s = seeker_screen.SeekerScreen(pygame.display.get_surface())
    assert s.session is not None and s.phase == 'gallery'
    won = set(s.session.profile.unlocked())
    assert {'bare_knuckles', 'short_story'} <= won, won
    s.draw()
    for key in (pygame.K_RIGHT, pygame.K_DOWN, pygame.K_RETURN):
        s.handle_key(pygame.event.Event(pygame.KEYDOWN, key=key, unicode='', mod=0, scancode=0))
        s.draw()
    no_errors(h)
    no_errors(h2)


def test_351_e05_a_death_dog_is_not_death(make_game):
    """"Death Dog swings at you and misses!", "Death Mage is slain!": seven
    ordinary kinds whose names begin with "death" were named like Death
    himself, with no article (two of them on floor 1)."""
    from monster import the_name
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 3)
    dog = place_monster(g, 'death_dog', 1)
    dog.hp = 1
    g._refresh_fov()
    h.said()
    said = blow(h, dog, 3)
    assert 'The Death Dog is slain!' in said, said
    for kind in ('death_echo', 'death_knight', 'death_mage', 'death_beetle', 'death_lord',
                 'death_knight_lord'):
        m = place_monster(g, kind, 2)
        m._aware = True
        assert the_name(m).startswith('The ') and the_name(m, lower=True).startswith('the '), kind
    from monster import DeathMonster
    assert the_name(DeathMonster()) == 'Death'
    no_errors(h)


def test_351_e06_a_shot_named_by_a_verb_misses_in_english():
    """"The Skeleton Archer's shoot misses you!", "The Lich Thrall's cast
    misses you!", "The Elder Beholder's disintegrate misses you!", "The
    Huldufolk Raider's led astray misses you!"."""
    from monster import Monster
    defs = monster_defs()
    want = {('skeleton_archer', 'Shoot'): 'The Skeleton Archer shoots at you and misses!',
            ('lich_thrall', 'Cast'): 'The Lich Thrall casts at you and misses!',
            ('elder_beholder', 'Disintegrate'):
                'The Elder Beholder tries to disintegrate you, and misses!',
            ('huldufolk_raider', 'Led Astray'):
                'The Huldufolk Raider tries to lead you astray, and fails!'}
    for (kind, attack), line in want.items():
        m = Monster(dict(defs[kind], id=kind), 0, 0)
        m._aware = True
        atk = next(a for a in m.attacks if str(a.get('name')).replace('_', ' ') == attack)
        assert m._miss_text(atk) == line, (kind, m._miss_text(atk))
    # Every other verb-named attack says no verb as a noun ("'s shoot").
    import json
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, 'data', 'combat_lines.json'), encoding='utf-8') as f:
        verbs = set(json.load(f)['attack_verbs'])
    for kind, d in defs.items():
        for a in d.get('attacks', []):
            name = str(a.get('name')).replace('_', ' ')
            if name in verbs:
                m = Monster(dict(d, id=kind), 0, 0)
                m._aware = True
                assert f"'s {name.lower()} misses" not in m._miss_text(a), (kind, m._miss_text(a))


def test_351_e07_a_prayer_says_only_what_it_gave(make_game):
    """A hero at full HP, SP and MP prays (\\, the first prayer, a chain of
    three): "Strength floods back into your limbs. (+52 SP)", "Warmth washes
    over you, but your wounds refuse to close." (the line for Gae Dearg's
    wound) and "(+5 MP)", none of it true. Then hurt and tired: each line
    says what came back."""
    g, h = make_game()
    p = g.player
    p.hp, p.sp, p.mp = p.max_hp, p.max_sp, p.max_mp
    h.key(pygame.K_BACKSLASH, '\\')
    assert g.state == 'prayer_menu'
    h.key('1')
    assert h.in_quiz()
    h.quiz(3, 1)
    said = h.said()
    assert not any('SP)' in s or 'MP)' in s or 'HP)' in s for s in said), said
    assert not any('refuse to close' in s for s in said), said
    while g.state != 'player':
        h.key(pygame.K_ESCAPE)
    p.hp, p.sp = p.max_hp - 5, p.max_sp - 7
    p.prayer_cooldown = 0                       # (a hundred turns on)
    h.key(pygame.K_BACKSLASH, '\\')
    assert g.state == 'prayer_menu', h.said()
    h.key('1')
    h.quiz(3, 1)
    said = h.said()
    assert 'Strength floods back into your limbs. (+7 SP)' in said, said
    assert 'Warmth washes over your wounds. (+5 HP)' in said, said
    no_errors(h)


def test_351_e08_a_healing_draught_says_what_it_healed(make_game):
    """The starting Potion of Healing drunk (Q) at full health: "Warmth
    floods through you. (+18 HP)". Then one drunk five HP down: (+5 HP)."""
    import copy
    from items import Potion
    g, h = make_game()
    p = g.player
    potion = next(i for i in p.inventory if isinstance(i, Potion))
    spare = copy.deepcopy(potion)
    assert p.hp == p.max_hp
    h.key('q')
    assert g.state == 'quaff_menu'
    h.key(getattr(pygame, f'K_{chr(97 + g.quaff_menu_items.index(potion))}'))
    said = h.said()
    assert not any('HP)' in s for s in said), said
    assert 'Warmth floods through you, but you had no wounds to close.' in said, said
    p.inventory.append(spare)
    p.hp = p.max_hp - 5
    h.key('q')
    h.key(getattr(pygame, f'K_{chr(97 + g.quaff_menu_items.index(spare))}'))
    said = h.said()
    assert 'Warmth floods through you. (+5 HP)' in said, said
    # The Bread Ration eaten (U) by a hero who is not hungry: no "SP
    # restored" of nothing; then four SP down, four.
    import items
    p.sp = p.max_sp
    h.key('u')
    h.key('a')
    said = h.said()
    assert 'You eat the Bread Ration.' in said, said
    p.inventory.append(items.make_item_by_id('food', 'bread_ration'))
    p.sp = p.max_sp - 4
    h.key('u')
    h.key('a')
    assert 'You eat the Bread Ration. (4 SP restored)' in h.said()
    no_errors(h)


def test_351_e09_a_dish_eaten_unhurt_heals_nothing_it_claims(make_game):
    """A Rat Rump Kebab cooked (C) by a hero at full health and mana: "You
    eat it: +12 SP, +9 HP." told of HP he could not gain."""
    import items
    import kitchen
    g, h = make_game()
    p = g.player
    meat = items.make_item_by_id('ingredient', 'giant_rat_prime')
    assert meat is not None
    p.inventory.append(meat)
    p.hp, p.mp = p.max_hp, p.max_mp
    p.sp = p.max_sp // 2
    h.key('c')
    cook_menu_pick(h, lambda r: r['ready'] and 'giant_rat_prime' in kitchen.parts(r['recipe']))
    h.quiz(1)
    said = h.said()
    eat = next(s for s in said if s.startswith('You eat it:'))
    assert 'HP' not in eat.replace('max HP', '') and 'MP' not in eat, eat
    assert p.hp == p.max_hp
    no_errors(h)


def test_351_e10_a_named_foes_corpse_is_studied_by_name(make_game):
    """Arachne killed (a scene: one blow) and her corpse studied (I): "You
    understand the Arachne now." A skeleton's is still "the Skeleton"."""
    import items
    g, h = make_game()
    p = g.player
    p.hp = p.max_hp = 10 ** 4
    open_floor(g, p.x, p.y, 3)
    for kind, line in (('arachne', 'You understand Arachne now.'),
                       ('skeleton', 'You understand the Skeleton now.')):
        m = place_monster(g, kind, 1)
        m.hp = 1
        g._refresh_fov()
        h.said()
        blow(h, m, 3)
        assert not m.alive
        corpse = next(i for i in g.ground_items if isinstance(i, items.Corpse)
                      and i.monster_id == kind)
        go_to(h, corpse.x, corpse.y)
        h.said()
        h.key('i')
        entry = next(n for n, e in enumerate(g.identify_menu_items) if e[0] is corpse)
        h.key(getattr(pygame, f'K_{chr(97 + entry)}'))
        h.quiz(5)
        assert line in h.said(), kind
        while g.state != 'player':
            h.key(pygame.K_ESCAPE)
        go_to(h, p.x - 1 if g.dungeon.is_walkable(p.x - 1, p.y) else p.x + 1, p.y)
    no_errors(h)
