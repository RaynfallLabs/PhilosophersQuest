"""Bug bash 3.6.0: the verified content errors that were bugs in the code.

Each test names its entry in ``_bugbash_3_6_0/verified.jsonl`` (by ``n``).
They drive the real Game: what they cover is rare, late or random, so it
cannot be play-tested on demand.
"""
import copy
import json
import os
import pickle
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()


def _data(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


def _resize(g, w, h):
    import layout
    g.screen = pygame.display.set_mode((w, h))
    layout.update(w, h)
    g.on_resize(w, h)
    g._resize_grace = 0


@pytest.fixture
def game(tmp_path, monkeypatch):
    import bones
    import items
    import layout
    import save_system
    from game_states import STATE_PLAYER
    from main import Game
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(360)
    items.bind_unique_registry(set())
    screen = pygame.display.set_mode((1280, 720))
    layout.update(1280, 720)
    g = Game(screen, player_name='__test_bb360__')
    g.on_resize(1280, 720)
    g._resize_grace = 0
    g.monsters = []
    g.state = STATE_PLAYER
    yield g
    _resize(g, 1280, 720)


def _said(g):
    got = []
    real = g.add_message

    def spy(text, *a, **k):
        got.append(str(text))
        return real(text, *a, **k)
    g.add_message = spy
    return got


def _open(g, tag, enc=None):
    """Encounter ``tag`` on this floor beside the hero, its screen open."""
    import economy
    from game_road import _encounter_by_tag
    from monster import Monster
    src, found = _encounter_by_tag(tag)
    assert found is not None, tag
    e = enc or economy.price_encounter(copy.deepcopy(found))
    flavor = src == 'flavor'
    m = Monster({'id': 'npc_traveler', 'name': e['name'], 'symbol': '@', 'color': [1, 1, 1],
                 'hp': 1, 'thac0': 20, 'speed': 0, 'attacks': [], 'ai_pattern': 'sessile',
                 'resistances': [], 'weaknesses': [], 'min_level': 1, 'is_allied': True,
                 'harvest_tier': 0, 'harvest_threshold': 99, 'ingredient_id': None},
                g.player.x + 1, g.player.y)
    setattr(m, '_flavor_encounter_tag' if flavor else '_npc_encounter_tag', tag)
    g.monsters.append(m)
    (g._flavor_encounter_levels if flavor else g._npc_encounter_levels)[g.dungeon_level] = e
    g._npc_open(e, m, flavor=flavor)
    return e


def _choose(g, raw_index):
    g._npc_show_options()
    pairs = [p for p in g._npc_visible_options() if p[0] == raw_index]
    assert pairs, (raw_index, [p[0] for p in g._npc_visible_options()])
    g._npc_selected_index, g._npc_selected_option = pairs[0]
    g._apply_npc_choice(pairs[0][1], None)


def _hint(enc, index):
    return enc['options'][index]['road']['hint']


# ---------------------------------------------------- n=1, Roads Not Taken

def test_n001_paying_grumwald_again_leaves_no_road_he_never_offered(game):
    import chronicle
    import deeds
    reg = game._deeds_reg()
    deeds.record(reg, 'forgo.troll_toll', floor=1, block=1)
    game.player_gold = 100000
    enc = _open(game, 'flv_grumwald_second_bridge')
    _choose(game, 0)                                        # pay again
    roads = chronicle.roads_not_taken(reg, 9)
    for i in (1, 2, 3):     # two other heroes' tolls, and a robber's confession
        assert _hint(enc, i) not in roads, i
    assert _hint(enc, 4) in roads                           # he could have crossed


def test_n001_laying_the_reliquary_leaves_no_road_of_losing_it(game):
    import chronicle
    from items import make_item_by_id
    game.player.inventory.append(make_item_by_id('accessory', 'saints_reliquary'))
    enc = _open(game, 'flv_reliquary_chapel')
    _choose(game, 0)                                        # laid in the niche
    roads = chronicle.roads_not_taken(game._deeds_reg(), 9)
    assert _hint(enc, 1) not in roads
    assert _hint(enc, 2) in roads                           # he could have kept it


def test_n001_a_secret_road_still_shows(game):
    import chronicle
    enc = _open(game, 'flv_vafthrudnir')
    assert enc['options'][2].get('hidden')
    assert 2 not in [i for i, _o in game._npc_visible_options()]
    _choose(game, 3)                                        # declined
    assert _hint(enc, 2) in chronicle.roads_not_taken(game._deeds_reg(), 9)


def test_n001_a_road_seen_at_a_later_step_is_kept():
    """The sleepers' three acts share a hidden group and follow one another:
    the bugle, once offered, is a road not taken; the sword left alone is
    the road he took by another door."""
    import chronicle
    import deeds
    enc = next(e for e in _data('flavor_encounters.json')
               if e.get('tag') == 'flv_sleepers_under_the_hill')
    reg = deeds.new_register()
    chronicle.record_choice(reg, enc, 0, [0, 3])
    chronicle.record_choice(reg, enc, 1, [1, 4])
    chronicle.record_choice(reg, enc, 5, [2, 5])
    roads = chronicle.roads_not_taken(reg, 9)
    assert _hint(enc, 2) in roads
    assert _hint(enc, 3) not in roads and _hint(enc, 4) not in roads


def test_n001_roads_from_an_old_save_still_read():
    import chronicle
    reg = {'chosen': {'old': [0]},
           'roads': {'old': {'order': 0, 'options': [{'index': 0, 'id': 'a', 'hint': 'Taken.'},
                                                     {'index': 1, 'id': 'b', 'hint': 'Not taken.'}]}}}
    assert chronicle.roads_not_taken(reg) == ['Not taken.']
    chronicle.record_choice(reg, {'tag': 'old', 'options': [{}, {}]}, 0, [0])
    assert chronicle.roads_not_taken(reg) == ['Not taken.']


# ---------------------------------------------------- n=47, pronouns

@pytest.mark.parametrize('kind,word', [('demon_knight', 'he'), ('infernal_lord', 'he'),
                                       ('imp_lord', 'he'), ('pit_executioner', 'he'),
                                       ('ghast_eater', 'it')])
def test_n047_the_combat_pronoun_is_the_lores(kind, word):
    from monster import Monster, pronouns
    defn = dict(_data('monsters.json')[kind], id=kind)
    defn.setdefault('symbol', 'd')
    defn.setdefault('color', [1, 1, 1])
    assert pronouns(Monster(defn, 1, 1))[0] == word


# ---------------------------------------------------- n=96, the lost wager

def test_n096_a_lost_wager_costs_the_stake(game, monkeypatch):
    import decor
    import economy
    monkeypatch.setattr(economy, 'roll_share', lambda *a, **k: 40)
    spec = decor.lore_fixtures()['fixtures']['gamblers_table']
    game.player_gold = 500
    said = _said(game)
    game._lore_fixture_resolve((5, 5), 'gamblers_table', spec, False)
    assert game.player_gold == 460
    assert 'You lose 40 gold.' in said


def test_n096_a_lost_wager_takes_no_more_than_the_purse_holds(game, monkeypatch):
    import decor
    import economy
    monkeypatch.setattr(economy, 'roll_share', lambda *a, **k: 40)
    spec = decor.lore_fixtures()['fixtures']['gamblers_table']
    for purse in (25, 0):
        game.player_gold = purse
        said = _said(game)
        game._lore_fixture_resolve((5, 5), 'gamblers_table', spec, False)
        assert game.player_gold == 0
        assert any('You lose' in s for s in said) == bool(purse)


# ---------------------------------------------------- n=108, the sealed vent

@pytest.mark.parametrize('ok', [True, False])
def test_n108_a_sealed_vent_does_not_say_the_prayer_failed(game, ok):
    import decor
    pos = (5, 5)
    decor.place(game.dungeon, pos, 'smoke_vent')
    game._lore_fixture_resolve(pos, 'smoke_vent',
                               decor.lore_fixtures()['fixtures']['smoke_vent'], ok)
    line = decor.look_line(game.dungeon, *pos)
    assert ('not enough' in line) == (not ok), line
    if ok:
        assert 'shut' in line


# ---------------------------------------------------- n=109, overflowing text

def _story_pages(g, phase):
    """Draw the encounter's page for real, scrolling down to its end: every
    story line drawn, and the last footer."""
    g._npc_encounter_phase = phase
    g._npc_text_scroll = 0
    real_blit, real_footer = g._ui_blit_text, g._ui_footer
    blits, foot = [], []

    def blit(text, font, color, x, y, **k):
        if k.get('max_width'):                              # this helper cuts what is too wide
            assert font.size(str(text))[0] <= k['max_width'], text
        blits.append((str(text), y + font.get_height()))
        return real_blit(text, font, color, x, y, **k)

    def footer(panel, text):
        foot.append((text, g._ui_footer_metrics(panel)[0]))
        g._ui_blit_text = real_blit                         # the key hints are no story
        try:
            return real_footer(panel, text)
        finally:
            g._ui_blit_text = blit
    g._ui_blit_text, g._ui_footer = blit, footer
    lines, first = set(), None
    try:
        for _ in range(400):
            del blits[:]
            g._draw_npc_encounter()
            text, divider = foot[-1]
            if first is None:
                first = text
            assert all(bottom <= divider for _t, bottom in blits), 'drawn over the footer'
            now = tuple(t for t, _b in blits)
            if set(now) <= lines:
                break
            lines.update(now)
            g._npc_encounter_input(pygame.K_DOWN)
            assert g._npc_encounter_phase == phase
    finally:
        g._ui_blit_text, g._ui_footer = real_blit, real_footer
    return lines, first


def _gate_page():
    gate = _data('gate_lines.json')['gate']['lines']
    six = sorted((row['line'] for row in gate), key=len, reverse=True)[:6]
    enc = next(e for e in _data('flavor_encounters.json') if e.get('tag') == 'flv_the_gate')
    after = enc['options'][0]['people_lines']['after']
    return six + [after]


def _lost_words(drawn, rows):
    from fantasy_ui import display_text
    have = set(' '.join(drawn).split())
    return [w for row in rows for w in display_text(row).split() if w not in have]


@pytest.mark.parametrize('size', [(1280, 720), (960, 540)])
def test_n109_the_gates_longest_page_is_never_cut(game, size):
    _resize(game, *size)
    _open(game, 'flv_the_gate')
    rows = _gate_page()
    game._npc_outcome_text = '\n'.join(rows)
    drawn, _foot = _story_pages(game, 'outcome')
    assert not _lost_words(drawn, rows), size
    # The closing line itself, not only words it shares with the others.
    last = rows[-1].split()[-5:]
    assert any(last[-1] in line.split() for line in drawn), size


@pytest.mark.parametrize('size', [(1280, 720), (960, 540)])
@pytest.mark.parametrize('phase', ['text', 'outcome'])
def test_n109_a_page_too_long_scrolls_and_says_how(game, size, phase):
    _resize(game, *size)
    _open(game, 'flv_the_gate')
    rows = [f'word{i} ' * 9 for i in range(50)]
    game._npc_encounter_text = game._npc_outcome_text = '\n'.join(rows)
    drawn, foot = _story_pages(game, phase)
    assert not _lost_words(drawn, rows)
    assert 'Up/Down: scroll' in foot


def test_n109_a_short_page_offers_no_scroll(game):
    _open(game, 'flv_the_gate')
    _lines, foot = _story_pages(game, 'text')
    assert 'scroll' not in foot


# ---------------------------------------------------- n=110, the friends' stalls

_TRADERS = _data('traders.json')['traders']
_WITH_FRIEND = [k for k, v in _TRADERS.items() if v.get('friend')]


def _spoken(m):
    out = [m.lore]
    for v in m.lines.values():
        out.extend(v if isinstance(v, list) else [v])
    return out


@pytest.mark.parametrize('kind', _WITH_FRIEND)
def test_n110_a_friend_speaks_for_himself(kind):
    import traders
    from mystery_system import build_trader
    host = _TRADERS[kind]
    m = build_trader(kind, 15, random.Random(1))
    m.set_person(traders.kind_def(kind), host['friend'])
    assert m.lore and m.lore != host['lore']
    for word in host['name'].split():
        if word in ('Mother',):
            continue
        assert not any(word in s for s in _spoken(m)), (kind, word)
    hosts = {v for v in host['lines'].values() if isinstance(v, str)} | set(host['lines']['greet'])
    assert not hosts & set(_spoken(m)), kind
    for key in host['lines']:                               # and is never left wordless
        assert m.lines.get(key), (kind, key)
    assert m.lines['greet'] == [host['friend']['line']]
    assert m.lines['counter'] == host['friend']['counter']


@pytest.mark.parametrize('kind', _WITH_FRIEND)
def test_n110_an_old_saves_friend_learns_his_own_lines(kind):
    import traders
    from mystery_system import build_trader
    host = _TRADERS[kind]
    m = build_trader(kind, 15, random.Random(1))
    m.set_person(traders.kind_def(kind), host['friend'])
    m.lore = host['lore']                                   # as a save from before held him
    m.lines = dict(host['lines'], greet=[host['friend']['line']])
    back = pickle.loads(pickle.dumps(m))
    assert back.lore != host['lore']
    assert back.lines['bought'] != host['lines']['bought']


def test_n110_a_friend_gives_a_rumour_in_no_hosts_voice():
    import traders
    host = _TRADERS['generalist']
    real = traders._check
    traders._check = lambda cond, ctx: cond == 'open_hand'
    try:
        mult, lines = traders.price_mult('generalist', {}, friend=True)
        alone = traders.price_mult('generalist', {})[0]
    finally:
        traders._check = real
    assert lines and all('Grindle' not in line for _k, line in lines)
    assert alone == pytest.approx(host['reactions'][0]['mult'])     # the price is as it was
    assert mult < alone


# ---------------------------------------------------- n=117, trinketry

def _trinketry(buc='uncursed'):
    from items import make_item_by_id
    sc = make_item_by_id('scroll', 'scroll_of_master_trinketry')
    if sc is None:
        from items import load_items
        sc = copy.copy(next(s for s in load_items('scroll')
                            if s.effect == 'enchant_accessory' and s.tier == 5))
    sc.buc = buc
    return sc


def test_n117_master_trinketry_reaches_the_amulet(game):
    from items import make_item_by_id
    p = game.player
    p.accessory_slots = [None] * 4
    amulet = make_item_by_id('accessory', 'amulet_of_merlin')
    amulet.id_level = 5
    p._apply_equip(amulet)
    assert p.amulet_slot is amulet
    amount, worn = amulet.effects['amount'], p.INT
    said = _said(game)
    game._apply_scroll_effect(_trinketry())
    assert amulet.effects['amount'] > amount
    assert p.INT > worn
    assert not any('no accessory' in s for s in said)


def test_n117_rings_come_first_and_the_belt_is_left(game):
    from items import load_items, make_item_by_id
    p = game.player
    ring = make_item_by_id('accessory', 'aesops_quill')
    amulet = make_item_by_id('accessory', 'amulet_of_merlin')
    belt = copy.deepcopy(next(a for a in load_items('accessory')
                              if a.slot == 'belt' and 'amount' in a.effects))
    p.accessory_slots = [ring, None, None, None]
    p.amulet_slot, p.belt_slot = amulet, belt
    was = [copy.deepcopy(i.effects) for i in (ring, amulet, belt)]
    sc = copy.copy(next(s for s in load_items('scroll')
                        if s.effect == 'enchant_accessory' and s.tier == 3))
    sc.buc = 'uncursed'
    game._apply_scroll_effect(sc)
    assert ring.effects['amount'] > was[0]['amount']        # rings keep their place in the count
    game._apply_scroll_effect(_trinketry())
    assert belt.effects == was[2]                           # a belt is no ring or amulet
