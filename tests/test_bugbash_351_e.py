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
        if not step_to(h, x, y, adjacent=False):
            h.wait()
    raise AssertionError(f'never reached {(x, y)} from {(g.player.x, g.player.y)}')


def wield_the_sword(h):
    import items
    g = h.g
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


ROW_HEADS = ('Weak To (Double Damage)', 'Resists (Half Damage)', 'Shrugs Off (Quarter Damage)',
             'Bane Materials (Double Damage)')


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
    other = min((m for m in g.monsters if m.alive and not getattr(m, 'is_allied', False)
                 and m.kind in monster_defs()
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
