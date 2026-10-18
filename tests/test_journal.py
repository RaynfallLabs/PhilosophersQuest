"""The Journal and "Your Story" (DEEDS_KARMA_DESIGN 7.3-7.5, Brandon's
decisions in section 11).

Pure views first (chronicle.py), then the game wiring (an encounter's choice
lands in the Deeds and People pages; Roads Not Taken come from THIS run only),
then render smoke tests of every Journal page and the Your Story page at
1280x720, the compact size (1093x614) and 3440x1440, through the capture
harness's own scenes.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pytest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

import chronicle  # noqa: E402
import deeds  # noqa: E402
from ui import floor_label  # noqa: E402


def _entry(seq, kind, text, floor=5, **kw):
    return chronicle.make_entry(seq=seq, floor=floor, turn=seq, kind=kind, text=text, **kw)


# ---------------------------------------------------------------- pure views

def test_oath_sections_order_and_verdicts():
    reg = deeds.new_register()
    w = dict(floor=4, block=1, turn=0)
    deeds.swear(reg, 'a', to='Sir Aldric', what='Carry his lodestone to an altar.', **w)
    deeds.swear(reg, 'b', to='Brother Sacristan', what='Carry the Gospel down.', **w)
    deeds.swear(reg, 'c', to='a dying courier', what='Deliver his dispatch.', **w)
    deeds.swear(reg, 'd', to='Elspeth', what='Hold the candle.', **w)
    deeds.keep_oath(reg, 'b', **w)
    deeds.lapse_oath(reg, 'c', **w)
    deeds.release_oath(reg, 'd', **w)
    deeds.open_thread(reg, 't', hint="Elspeth's candle still burns somewhere below.")
    sec = chronicle.oath_sections(reg)
    assert [o['id'] for o in sec['open']] == ['a']
    assert [(v, o['id']) for v, o in sec['resolved']] == [
        ('Kept', 'b'), ('Let Go', 'c'), ('Released', 'd')]
    assert sec['unfinished'] == ["Elspeth's candle still burns somewhere below."]
    assert chronicle.oath_text(sec['open'][0]) == 'To Sir Aldric: carry his lodestone to an altar.'
    # A description is not capitalised like a name.
    assert chronicle.oath_text(reg['oaths']['c']).startswith('To a dying courier: ')


def test_consequences_sit_under_their_cause():
    rows = [
        _entry(1, 'deed', 'Saved Marta.', source='rat_catcher'),
        _entry(2, 'milestone', 'Went down a floor.'),
        _entry(3, 'deed', 'Took the stone.', source='aldric'),
        _entry(4, 'consequence', 'Bread on a ledge. Marta pulled through.', source='rat_catcher'),
        _entry(5, 'loss', 'Lost Lena.'),
        _entry(6, 'consequence', 'Elspeth found me.', cause=3),
    ]
    got = [(e['seq'], depth) for e, depth in chronicle.deed_rows(rows)]
    assert got == [(1, 0), (4, 1), (3, 0), (6, 1), (5, 0)]
    # Milestones are not deeds.
    assert 2 not in [s for s, _ in got]


def test_people_rows_say_status_in_words():
    reg = deeds.new_register()
    deeds.set_person(reg, 'marta', name='marta', status='saved', floor=3, last_line='She asked twice.')
    deeds.set_person(reg, 'aldric', name='Sir Aldric', status='aided', owed=True, floor=7)
    deeds.set_person(reg, 'tam', name='Tam', status='aided', owes=True, floor=8)
    deeds.set_person(reg, 'odin', name='Old Wanderer', status='unmasked', floor=9)
    deeds.set_person(reg, 'cow', name='Farmer', floor=999)
    rows = chronicle.people_rows(reg, floor_label)
    assert [r['status'] for r in rows] == ['Saved', 'You Owe a Debt', 'Owes You',
                                           'Unmasked', 'Met']
    assert rows[0]['name'] == 'Marta'                     # proper capitalisation
    assert rows[0]['where'] == 'Floor 3' and rows[0]['last'] == 'She asked twice.'
    assert rows[-1]['where'] == 'Moo Moo Farm'            # never "Floor 999"


def test_timeline_groups_by_floor_and_names_the_farm():
    rows = [_entry(1, 'milestone', 'a', 3), _entry(2, 'deed', 'b', 3),
            _entry(3, 'milestone', 'moo', 999), _entry(4, 'deed', 'c', 3),
            _entry(5, 'legacy', 'old', None)]
    groups = chronicle.timeline_groups(rows, floor_label)
    assert [(lab, len(es)) for lab, es in groups] == [
        ('Floor 3', 2), ('Moo Moo Farm', 1), ('Floor 3', 1), ('Before the Descent', 1)]
    assert not any('999' in lab for lab, _ in groups)


def _met(reg, tag, hints, taken, hidden=()):
    opts = []
    for i, h in enumerate(hints):
        o = {'label': f'option {i}', 'road': {'id': f'{tag}.{i}', 'hint': h}}
        if i in hidden:
            o['hidden'] = True
            o['requires'] = {'deeds_any': ['noticed.odin']}
        opts.append(o)
    chronicle.record_choice(reg, {'tag': tag, 'options': opts}, taken)


def test_roads_not_taken_are_this_runs_untaken_options():
    reg = deeds.new_register()
    _met(reg, 'tam', ['Stolen is stolen.', 'A widow feeds three alleys.', 'Work it off.'], 0)
    _met(reg, 'vafthrudnir', ['Riddles are won by listening.',
                              'Some contests are won by knowing who you met at a well.'], 0,
         hidden=(1,))
    roads = chronicle.roads_not_taken(reg)
    assert 'Stolen is stolen.' not in roads                  # the road taken
    assert 'Riddles are won by listening.' not in roads
    # A hidden option's road counts once its encounter was met.
    assert 'Some contests are won by knowing who you met at a well.' in roads
    assert set(roads) == {'A widow feeds three alleys.', 'Work it off.',
                          'Some contests are won by knowing who you met at a well.'}
    # The latest encounter leads, one road each before seconds.
    assert roads[0].startswith('Some contests') and roads[1] == 'A widow feeds three alleys.'


def test_roads_not_taken_cap_and_unmet_encounters():
    reg = deeds.new_register()
    assert chronicle.roads_not_taken(reg) == []              # nothing met, nothing to show
    for k in range(4):
        _met(reg, f'e{k}', [f'taken {k}', f'left {k} a', f'left {k} b'], 0)
    roads = chronicle.roads_not_taken(reg)
    assert len(roads) == 4
    assert all(r.startswith('left') for r in roads)


def test_then_options_encounters_record_every_step():
    reg = deeds.new_register()
    enc = {'tag': 'x', 'options': [{'road': {'id': 'x.0', 'hint': 'zero'}},
                                   {'road': {'id': 'x.1', 'hint': 'one'}},
                                   {'road': {'id': 'x.2', 'hint': 'two'}}]}
    chronicle.record_choice(reg, enc, 0)
    chronicle.record_choice(reg, enc, 2)
    assert chronicle.roads_not_taken(reg) == ['one']


def test_oath_summary_in_words():
    reg = deeds.new_register()
    assert 'no promises' in chronicle.oath_summary(reg)
    w = dict(floor=4, block=1, turn=0)
    deeds.swear(reg, 'a', to='A', what='x', **w)
    assert chronicle.oath_summary(reg) == "I swore one promise and was still carrying it at the end."
    deeds.keep_oath(reg, 'a', **w)
    assert chronicle.oath_summary(reg) == "I swore one promise, and I kept it."
    for k in 'bcd':
        deeds.swear(reg, k, to='B', what='y', **w)
    deeds.break_oath(reg, 'b', **w)
    deeds.lapse_oath(reg, 'c', **w)
    s = chronicle.oath_summary(reg)
    assert s == "I swore four promises: I kept one, broke one and let one go. I was still carrying one at the end."
    assert not any(ch.isdigit() for ch in s)


def test_highlights_prefer_soul_notice_consequence():
    rows = [_entry(1, 'boss', 'Killed the Minotaur.'), _entry(2, 'soul', 'Soul line.'),
            _entry(3, 'deed', 'A deed.'), _entry(4, 'notice', 'Saw through him.'),
            _entry(5, 'consequence', 'It came back to me.'), _entry(6, 'soul', 'Later soul.')]
    got = [e['text'] for e in chronicle.highlights(rows)]
    assert got == ['Saw through him.', 'It came back to me.', 'Later soul.']
    few = [_entry(1, 'boss', 'Killed the Minotaur.'), _entry(2, 'milestone', 'Down.')]
    assert [e['text'] for e in chronicle.highlights(few)] == ['Killed the Minotaur.', 'Down.']


def test_once_keys_write_a_line_only_once():
    from types import SimpleNamespace
    g = SimpleNamespace(dungeon_level=3, turn_count=1)
    assert chronicle.chron(g, 'milestone', 'First.', once='k') is not None
    assert chronicle.chron(g, 'milestone', 'First.', once='k') is None
    assert [e['text'] for e in g._chronicle] == ['First.']
    chronicle.chron(g, 'milestone', 'Spell.', once='spell:a')
    chronicle.chron(g, 'milestone', 'Spell.', once='spell:b')
    assert chronicle.once_count(g, 'spell:') == 2


# ---------------------------------------------------------------- game wiring

@pytest.fixture
def game():
    import pygame
    pygame.init()
    import layout
    screen = pygame.display.set_mode((layout.WINDOW_W, layout.WINDOW_H))
    from main import Game
    g = Game(screen, player_name='JournalTester')
    g.monsters = []
    return g


def _open_encounter(g, enc):
    from monster import Monster
    npc = Monster({'id': 'npc_traveler', 'name': enc['name'], 'hp': 1, 'attacks': [],
                   'ai_pattern': 'sessile', 'symbol': 'p', 'color': [1, 1, 1]}, 3, 3)
    g._npc_open(enc, npc, flavor=True)
    return npc


ENC = {
    'tag': 'test_tam', 'name': 'Pickpocket', 'symbol': 'p', 'text': 'A boy with coins.',
    'person': {'id': 'tam', 'name': 'Tam'},
    'options': [
        {'label': 'Make him give them back', 'outcome': 'He does.',
         'chronicle': 'Made Tam give the coins back. He looked at me like I had hit him.',
         'person_status': 'spared',
         'thread': {'id': 'tam_oven', 'hint': "Hanne's oven is still warm somewhere below."},
         'road': {'id': 'tam.return', 'hint': 'Stolen is stolen, but a hungry boy can work.'}},
        {'label': 'Let him keep them', 'outcome': 'He runs.',
         'road': {'id': 'tam.keep', 'hint': "A widow's oven feeds three alleys."}},
        {'label': 'Walk on', 'outcome': 'You walk on.'},
    ],
}


def test_an_encounter_choice_lands_in_deeds_people_and_roads(game):
    import copy
    g = game
    enc = copy.deepcopy(ENC)
    _open_encounter(g, enc)
    g._npc_selected_index = 0
    g._npc_selected_option = enc['options'][0]
    g._apply_npc_choice(enc['options'][0])
    g._close_npc_encounter(resolved=True)
    deed = [e for e in g._chronicle if e['kind'] == 'deed']
    assert deed and deed[-1]['text'].startswith('Made Tam give the coins back')
    assert deed[-1]['person'] == 'tam' and deed[-1]['source'] == 'test_tam'
    # The thread it opened hangs under the deed, and waits in Unfinished.
    assert deed[-1]['thread'] == 'tam_oven'
    assert chronicle.oath_sections(g._deeds)['unfinished'] == [
        "Hanne's oven is still warm somewhere below."]
    people = chronicle.people_rows(g._deeds, floor_label)
    tam = next(p for p in people if p['name'] == 'Tam')
    assert tam['status'] == 'Spared' and tam['last'].startswith('Made Tam give')
    story = chronicle.your_story(g._deeds, g._chronicle)
    assert story['roads'] == ["A widow's oven feeds three alleys."]
    # Nothing on the page says how the soul was weighed.
    assert not any('karma' in str(v).lower() for v in story.values())


def test_an_option_with_no_line_writes_only_met_name(game):
    import copy
    g = game
    enc = copy.deepcopy(ENC)
    enc.pop('person')
    _open_encounter(g, enc)
    g._npc_selected_index = 2
    g._npc_selected_option = enc['options'][2]
    g._apply_npc_choice(enc['options'][2])
    g._close_npc_encounter(resolved=True)
    assert g._chronicle[-1]['text'] == 'Met the Pickpocket.'
    assert g._chronicle[-1]['kind'] == 'deed'
    # The NPC is in the People page, with no synthesised "last line".
    row = next(p for p in chronicle.people_rows(g._deeds, floor_label) if p['name'] == 'Pickpocket')
    assert row['last'] == ''


def test_a_callback_line_is_filed_under_its_cause(game):
    import copy
    g = game
    reg = deeds.ensure_register(g)
    g._chron('deed', 'Took Sir Aldric\'s lodestone.', source='flv_burdened_knight')
    reg.setdefault('causes', {})['flv_elspeth_comes'] = 'flv_burdened_knight'
    enc = copy.deepcopy(ENC)
    enc.update(tag='flv_elspeth_comes', name='Woman With A Candle', callback_only=True,
               person={'id': 'elspeth', 'name': 'Elspeth'})
    enc['options'][0]['chronicle'] = 'Elspeth carried the stone the rest of the way. I let her.'
    _open_encounter(g, enc)
    g._npc_selected_index = 0
    g._npc_selected_option = enc['options'][0]
    g._apply_npc_choice(enc['options'][0])
    g._close_npc_encounter(resolved=True)
    rows = chronicle.deed_rows(g._chronicle)
    texts = [(e['text'][:20], d) for e, d in rows]
    assert texts == [("Took Sir Aldric's lo", 0), ('Elspeth carried the ', 1)]


def test_end_screen_s_opens_your_story_and_esc_goes_back(game):
    import pygame
    from game_states import STATE_DEAD
    g = game
    g.defeat_reason = 'died'
    g.player.hp = 0
    g._on_game_over()
    g.state = STATE_DEAD

    def key(k, u=''):
        return g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=u, mod=0))

    assert key(pygame.K_s, 's') is True and g._end_story_open
    assert key(pygame.K_ESCAPE) is True and not g._end_story_open
    assert g.state == STATE_DEAD
    assert key(pygame.K_ESCAPE) is False                 # Esc on the score page still ends


def test_journal_tabs_turn_with_tab_and_numbers(game):
    import pygame
    g = game
    g._open_encyclopedia()

    def key(k, u=''):
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=u, mod=0))

    key(pygame.K_h, 'h')
    assert g.encyclopedia_category == 'journal' and g._journal_tab == 0
    key(pygame.K_TAB)
    assert g._journal_tab == 1
    key(pygame.K_4, '4')
    assert g._journal_tab == 3
    key(pygame.K_TAB)
    assert g._journal_tab == 0
    key(pygame.K_RIGHT)                                   # Left/Right still change category
    assert g.encyclopedia_category == 'lore_hints'


# ---------------------------------------------------------------- render smoke

JOURNAL_SCENES = ['menu_journal_oaths', 'menu_journal_deeds', 'menu_journal_people',
                  'menu_journal_timeline', 'menu_journal_timeline_end', 'menu_journal_empty',
                  'end_your_story',
                  'end_your_story_empty', 'end_your_story_victory']
SIZES = [(1280, 720), (1093, 614), (3440, 1440)]


def _capture():
    import importlib.util
    if 'pq_ui_capture' in sys.modules:
        return sys.modules['pq_ui_capture']
    spec = importlib.util.spec_from_file_location('pq_ui_capture',
                                                  ROOT / 'tools' / 'ui' / 'capture.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pq_ui_capture'] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope='module')
def rendered():
    import ui_theme
    saved = ui_theme.save_state()
    cap = _capture()
    out = {}
    try:
        yield _render_all(cap, out)
    finally:
        ui_theme.restore_state(saved)


def _render_all(cap, out):
    with cap.harness():
        for size in SIZES:
            for name in JOURNAL_SCENES:
                sc = next(s for s in cap.SCENES if s.name == name)
                surf, state = cap.render_scene(sc, size)
                out[(name, size)] = (surf, state,
                                     [t for _r, t in surf.text_blits],
                                     surf.text_outside(), surf.text_outside_panels(),
                                     surf.text_in_no_panel())
    return out


@pytest.mark.parametrize('size', SIZES, ids=lambda z: f'{z[0]}x{z[1]}')
@pytest.mark.parametrize('name', JOURNAL_SCENES)
def test_journal_and_story_render_cleanly(rendered, name, size):
    surf, state, texts, outside, over_edge, no_panel = rendered[(name, size)]
    assert state == ('encyclopedia' if name.startswith('menu_') else
                     'victory' if 'victory' in name else 'dead')
    assert not outside, outside
    assert not over_edge, over_edge
    assert not no_panel, no_panel
    joined = ' | '.join(texts)
    assert 'Floor 999' not in joined and 'L999' not in joined
    assert 'Karma' not in joined and 'karma' not in joined
    assert not [t for t in texts if t.rstrip().endswith(('...', '…'))]


def test_journal_pages_show_what_they_should(rendered):
    size = (1280, 720)
    t = {n: ' | '.join(rendered[(n, size)][2]) for n in JOURNAL_SCENES}
    for page in ('Oaths', 'Deeds', 'People', 'Timeline'):
        assert page in t['menu_journal_oaths']                      # the tab strip
    assert 'Open' in t['menu_journal_oaths'] and 'Kept' in t['menu_journal_oaths']
    assert 'Let Go' in t['menu_journal_oaths'] and 'Unfinished' in t['menu_journal_oaths']
    assert 'Somewhere above, a woman is lighting a candle' in t['menu_journal_oaths']
    assert 'Marta' in t['menu_journal_deeds']
    assert 'Unmasked' in t['menu_journal_people'] and 'Saved' in t['menu_journal_people']
    assert 'Floor 3' in t['menu_journal_timeline']
    assert 'Your Story' in t['end_your_story'] and 'Roads Not Taken' in t['end_your_story']
    assert 'I swore three promises' in t['end_your_story']
    assert 'Your Story' in t['end_your_story_victory']


def test_timeline_scrolled_to_the_end_shows_the_farm(rendered):
    """The Moo Moo Farm header, scrolled into view (the page is long)."""
    for size in SIZES:
        texts = ' | '.join(rendered[('menu_journal_timeline_end', size)][2])
        assert 'Moo Moo Farm' in texts and 'Floor 999' not in texts
