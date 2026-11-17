"""Round 3, Q15 (2026-11-14): the help screen matches the game.

Brandon: "update to new systems". The help screen is three pages now:

* the command map (``_draw_help_screen``), whose keys are derived here from
  the map's own handlers (``InputMixin._player_input`` and the shifted
  characters of ``handle_event``), so a key added without a help row fails;
* How Quizzes Work (data/ui/how_quizzes_work.json), with Recall Lore (a
  random hint, never about a creature) and how a kind is learned (a corpse
  study, the Wand of Probing);
* Gear and Load (data/ui/gear_and_load.json): the Kit and @ keys (Ready,
  and Apply, the only way the earplugs go in), the weapon At Your Back, the
  Loadouts, Known by Hand, donning time and "Keep dressing?", coatings,
  flasks, Press and Guard, and the three load tiers, its numbers held to
  the data.

The QA keys, the secret terminal and the secret builds stay off it.
Drawn at the smallest window with the painted kit the game ships; the
pages are turned with real keys. Whether it reads well is Brandon's look.
"""
import inspect
import json
import os
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

SMALL = (1280, 720)


def _page(name):
    with open(os.path.join(ROOT, 'data', 'ui', f'{name}.json'), encoding='utf-8') as f:
        return json.load(f)


def _page_text(name) -> str:
    out = []
    for sec in _page(name)['sections']:
        out.append(sec.get('heading', ''))
        out += sec.get('paragraphs', []) or []
        out += [f"{k}: {v}" for k, v in sec.get('rows', []) or []]
    return '\n'.join(out)


def _key(k, uni='', mod=0):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=uni, mod=mod, scancode=0)


@pytest.fixture
def kit_game():
    """A real Game at the smallest window, with the UI kit the game ships."""
    import layout
    import ui_theme
    from main import Game
    from game_states import STATE_PLAYER
    saved = ui_theme.save_state()
    try:
        ui_theme.load()
        screen = pygame.display.set_mode(SMALL)
        layout.update(*SMALL)
        g = Game(screen, player_name='__test_help_r3__')
        g.on_resize(*SMALL)
        g._resize_grace = 0
        g.state = STATE_PLAYER
        yield g
    finally:
        ui_theme.restore_state(saved)


def _command_rows(g, monkeypatch):
    """(key badge, description) of every row page 1 draws."""
    import game_render
    badges, rows = [], []
    real_badge = game_render.draw_key_badge
    real_fit = g._fit_line

    def badge(surface, rect, label, *a, **k):
        badges.append(label)
        return real_badge(surface, rect, label, *a, **k)

    def fit(text, *a, **k):
        font, shown = real_fit(text, *a, **k)
        assert shown == text, f'help row cut at 1280x720: {shown!r}'
        rows.append((badges[-1], text))
        return font, shown
    monkeypatch.setattr(game_render, 'draw_key_badge', badge)
    monkeypatch.setattr(g, '_fit_line', fit)
    g._help_page = 0
    g._draw_help_screen()
    return rows


# ---------------------------------------------------------------- the map's keys

# A key constant the map reads, as the help screen names it.
_K_NAMES = {'PERIOD': '.', 'COMMA': ',', 'SLASH': '?', 'QUESTION': '?',
            'BACKSLASH': '\\', 'SEMICOLON': ';', 'TAB': 'Tab'}
# Never on the help screen: the hidden green terminal (feedback rule: secret
# content stays secret).
_HIDDEN = {'BACKQUOTE'}


def _keys_the_map_answers():
    """Every key the map answers outside the QA build, in the help screen's
    names, read from the handlers themselves."""
    from game_input import InputMixin
    src = inspect.getsource(InputMixin._player_input)
    want = set()
    for name in set(re.findall(r'pygame\.K_(\w+)', src)) - _HIDDEN:
        want.add(_K_NAMES.get(name, name.upper() if len(name) == 1 else name))
    assert set(InputMixin._MOVE_KEYS) >= {pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT,
                                          pygame.K_RIGHT}
    want.add('Arrows')
    he = inspect.getsource(InputMixin.handle_event)
    block = he[he.index('if self.state == STATE_PLAYER:'):he.index('self._player_input(key)')]
    for line in block.splitlines():
        if 'qa_tools' in line:
            continue                  # the Titivillus QA build's keys
        for ch in re.findall(r"uni == '(.)'", line):
            if ch.isalpha():
                want.add(f'Shift+{ch}')
            elif ch == '|':
                want.add('Shift+\\')
            else:
                want.add(ch)
    # The keys every state hears first: F10, F11, Esc (F2 is the QA overlay).
    for m in re.finditer(r"if key == pygame\.K_(F\d+)(.*)", he):
        if 'PQ_QA_MODE' not in m.group(2):
            want.add(m.group(1))
    assert 'pygame.K_ESCAPE' in he
    want.add('Esc')
    return want


def _badge_keys(rows):
    """The single keys the badges name. A badge with ", " is a sequence
    inside another screen ("B, Tab"), not a key of the map's own."""
    out = set()
    for label, _desc in rows:
        if ', ' in label:
            continue
        for part in label.split(' / '):
            out.update(part.split(' '))
    return out


def test_every_key_the_map_answers_is_on_the_help_screen(kit_game, monkeypatch):
    want = _keys_the_map_answers()
    # A sanity floor: the new keys of the winning build and round 3 are read.
    assert {'S', 'K', 'N', 'T', 'Shift+E', 'Shift+S', 'Shift+C', 'Shift+P', 'Shift+\\',
            '@', '?', '<', '>', 'F10', 'F11'} <= want, want
    have = _badge_keys(_command_rows(kit_game, monkeypatch))
    missing = sorted(k for k in want if k not in have)
    assert not missing, f'keys the map answers with no help row: {missing}'


def test_the_quiz_keys_are_on_the_help_screen(kit_game, monkeypatch):
    from game_input import InputMixin
    src = inspect.getsource(InputMixin._quiz_input)
    have = _badge_keys(_command_rows(kit_game, monkeypatch))
    for k, label in (('K_SPACE', 'Space'), ('K_c', 'C'), ('K_PAGEUP', 'PgUp/PgDn'),
                     ('K_1', '1-4')):
        assert f'pygame.{k}' in src, k
        assert label in have, label


def test_the_rows_say_what_the_new_systems_do(kit_game, monkeypatch):
    pairs = _command_rows(kit_game, monkeypatch)
    assert ('S', 'Swap readied weapon') in pairs
    assert ('Shift+E', 'Loadouts') in pairs
    assert ('Shift+C', 'Coat weapon') in pairs
    assert ('Shift+S', 'Press / Guard') in pairs
    assert ('T', 'Throw item or flask') in pairs
    assert ('N', 'Recall Lore for a hint') in pairs
    # The Kit names Ready and Apply (the bug bash: "compare, equip, drop").
    assert ('K', 'Kit: equip, ready, apply') in pairs
    assert not any('compare, equip, drop' in d for _k, d in pairs)


# ---------------------------------------------------------------- the prose pages

def test_how_quizzes_work_says_recall_lore_is_a_random_hint():
    text = _page_text('how_quizzes_work')
    assert 'Recall Lore brings back a hint' in text
    assert 'picked at random' in text
    assert 'never about the creature in front of you' in text
    assert 'Wand of Probing' in text and 'learn the ways of its kind' in text
    # ... and the code does what the page says.
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._start_recall_lore)
    assert "subject='trivia'" in src and 'max_chain=5' in src and 'up to five' in text
    probe = inspect.getsource(MagicMixin._apply_wand_effect)
    assert "effect == 'probing'" in probe and 'self._learn_kind(kind)' in probe


def test_the_gear_page_lists_the_kit_and_sheet_keys_from_the_code():
    from item_actions import ACTION_KEYS
    from game_menus import MenuMixin
    sec = next(s for s in _page('gear_and_load')['sections']
               if s['heading'] == 'The Kit and the character sheet')
    rows = {k: v for k, v in sec['rows']}
    assert set(rows) == {k for _a, k in ACTION_KEYS}
    assert {pygame.key.name(k).upper() for k in MenuMixin._KIT_ACTION_KEYS} == set(rows)
    assert 'Ready' in rows['R'] and 'at your back' in rows['R']
    assert 'Apply' in rows['A'] and 'earplugs' in rows['A']


def test_apply_is_how_the_earplugs_go_in():
    import counters
    from items import make_item_by_id
    text = _page_text('gear_and_load')
    plugs = make_item_by_id('accessory', 'beeswax_earplugs')
    assert plugs is not None and counters.is_applied(plugs)
    assert plugs.name == 'Beeswax Earplugs' and 'Beeswax Earplugs' in text
    assert 'Press A on them in the Kit' in text


def test_the_gear_page_names_every_new_rule():
    text = _page_text('gear_and_load')
    for must in ('A readied weapon', 'S swaps it', 'Shift+E opens your Loadouts', 'Known by Hand',
                 'Keep dressing?', 'Shift+C: Coat', 'T: Throw', 'Flasks tab',
                 'Shift+S: Change your stance', 'Light:', 'Heavy:', 'Burdened:', 'Overloaded:',
                 'Dodge:', 'Speed:', 'Heavy armour:'):
        assert must in text, must


def test_the_gear_page_numbers_are_the_datas():
    import known_by_hand
    from player import Player
    with open(os.path.join(ROOT, 'data', 'gear_rules.json'), encoding='utf-8') as f:
        rules = json.load(f)
    with open(os.path.join(ROOT, 'data', 'arsenal.json'), encoding='utf-8') as f:
        arsenal = json.load(f)
    text = _page_text('gear_and_load')
    don = rules['donning']
    body = don['body']
    assert (f"Light body armour goes on in {body['light']} turn, medium in {body['medium']}, "
            f"heavy in {body['heavy']} and full plate in {don['templates']['full_plate']}") in text
    assert don['shield'] == don['minor'] == don['accessory'] == 1
    assert 'every other piece takes 1' in text
    assert don['doff_share'] == 0.5 and 'taking a piece off takes half as long' in text
    assert known_by_hand.MARK in text

    rows = {k: v for sec in _page('gear_and_load')['sections'] for k, v in sec.get('rows', [])}
    load = rules['load']
    assert set(Player.LOAD_WORDS.values()) <= set(rows)
    light, heavy, burd, over = rows['Light'], rows['Heavy'], rows['Burdened'], rows['Overloaded']
    # The four tiers of 2026-11-16 (src/defence.py): what the rows say is the data.
    assert load['light']['share'] == 0.5 and light.startswith('Over half your limit')
    assert 0 < load['light']['dodge'] < 1 and 'dodge a little less' in light
    assert load['light']['speed'] == 0 and 'slower' not in light
    assert load['heavy']['share'] == 0.7 and heavy.startswith('Over 70%')
    assert load['heavy']['dodge'] == 0.5 and 'dodge half as well' in heavy
    assert load['heavy']['speed'] > 0 and 'you are slower' in heavy
    assert load['burdened']['share'] == 0.9 and burd.startswith('Over 90%')
    assert load['burdened']['dodge'] == 0 and 'cannot dodge' in burd
    assert load['burdened']['speed'] > load['heavy']['speed'] and 'much slower' in burd
    assert load['overloaded']['dodge'] == 0 and 'cannot dodge' in over
    assert load['overloaded']['speed'] == 0.5 and 'half speed' in over
    for row in (light, heavy, burd, over):
        assert 'extra turn' not in row and 'Dexterity' not in row
    # Armour, dodge and speed: no Dexterity in AC; the Strength lines are the data's.
    import defence
    assert 'Dexterity adds nothing to it' in text
    assert 'medium armour half and heavy armour none' in rows['Dodge']
    assert rules['armour_weight']['dodge_share'] == {'light': 1.0, 'medium': 0.5, 'heavy': 0.0}
    assert (f"Strength {defence.fit_strength('medium')} wears medium armour at full speed and "
            f"Strength {defence.fit_strength('heavy')} heavy armour") in rows['Heavy armour']
    assert 'Constitution over 10 adds a little' in text and rules['defence']['con_carry'] > 0

    st = arsenal['stance']
    press, guard = st['press'], st['guard']
    assert (f"Press hits {round((press['damage'] - 1) * 100)}% harder but leaves you "
            f"{-press['ac']} AC worse") in rows['Shift+S']
    assert (f"Guard hits {round((1 - guard['damage']) * 100)}% softer but makes you "
            f"{guard['ac']} AC better") in rows['Shift+S']
    for coat in ('silver dust', 'holy water', 'fire oil', 'frost salts', 'venom'):
        assert coat in rows['Shift+C']


def test_no_qa_key_secret_or_hidden_thing_is_on_the_help_screen():
    from welcome_screen import SECRET_BUILDS
    import game_render
    src = inspect.getsource(game_render.RenderMixin._draw_help_screen)
    text = (_page_text('how_quizzes_work') + '\n' + _page_text('gear_and_load') + '\n'
            + src).lower()
    for word in ('xyzzy', 'titivillus', '[qa]', 'qa build', 'hack reality', 'immortal',
                 'unusual', 'backquote'):
        assert word not in text, word
    for name in SECRET_BUILDS:
        assert not re.search(rf'\b{re.escape(name)}\b', text), name


# ---------------------------------------------------------------- turning the pages

def test_the_pages_turn_with_real_keys_and_every_line_fits(kit_game, monkeypatch):
    from game_states import STATE_HELP, STATE_PLAYER
    from ui_scale import px as S
    g = kit_game
    drawn = []
    real_lines = g._ui_draw_scroll_lines

    def lines_spy(lines, font, color, rect, *a, **k):
        # Every line of a prose page is whole in its pane (no cut words).
        for ln in lines:
            text, fnt = ln[0], ln[2] or font
            ind = ln[3] if len(ln) > 3 else 0
            assert fnt.size(text)[0] + ind <= rect.w - S(12), f'help line cut: {text!r}'
        scroll = real_lines(lines, font, color, rect, *a, **k)
        visible = max(1, rect.h // (font.get_height() + S(k.get('line_gap', 3))))
        drawn.extend(ln[0] for ln in lines[scroll:scroll + visible])
        return scroll
    monkeypatch.setattr(g, '_ui_draw_scroll_lines', lines_spy)
    footers = []
    real_footer = g._ui_footer
    monkeypatch.setattr(g, '_ui_footer', lambda panel, hint:
                        (footers.append(hint), real_footer(panel, hint))[1])

    g.handle_event(_key(pygame.K_SLASH, '?'))
    assert g.state == STATE_HELP and g._help_page == 0
    g.render()
    assert footers[-1].startswith('Tab: How Quizzes Work')
    g.handle_event(_key(pygame.K_TAB))
    assert g._help_page == 1
    g.render()
    assert footers[-1].startswith('Tab: Gear and Load')
    g.handle_event(_key(pygame.K_TAB))
    assert g._help_page == 2
    drawn.clear()
    g.render()
    assert footers[-1].startswith('Tab: Commands')
    assert 'The Kit and the character sheet' in drawn
    g.handle_event(_key(pygame.K_END))
    drawn.clear()
    g.render()
    assert g._help_scroll > 0
    assert any(t.startswith('Overloaded: ') for t in drawn)       # the end of the page
    g.handle_event(_key(pygame.K_HOME))
    g.render()
    assert g._help_scroll == 0
    g.handle_event(_key(pygame.K_LEFT))
    assert g._help_page == 1
    g.handle_event(_key(pygame.K_RIGHT))
    g.handle_event(_key(pygame.K_TAB))
    assert g._help_page == 0                     # the last page turns round to the first
    g.handle_event(_key(pygame.K_ESCAPE))
    assert g.state == STATE_PLAYER


def test_a_wrapped_row_hangs_under_its_words(kit_game, monkeypatch):
    """A long "key: what it does" row wraps under the words, not the key."""
    g = kit_game
    seen = []
    real = g._ui_draw_scroll_lines

    def spy(lines, *a, **k):
        seen.extend(lines)
        return real(lines, *a, **k)
    monkeypatch.setattr(g, '_ui_draw_scroll_lines', spy)
    g._help_page = 2
    g._help_scroll = 0
    g._draw_help_screen()
    first = next(i for i, ln in enumerate(seen) if ln[0].startswith('A: Apply'))
    nxt = seen[first + 1]
    assert len(nxt) == 4 and nxt[3] == nxt[2].size('A: ')[0]
