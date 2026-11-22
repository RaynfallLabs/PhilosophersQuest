"""Bug bash 3.6.0, hunt 3 (h3-08 to h3-17): no screen drops a word in silence.

Each test names its finding in ``_bugbash_3_6_0/h3/findings.jsonl``. The
screens are drawn for real through the capture harness, and a word counts
only if it can be read: inside its clip and the window, with nothing painted
over it, on the page first drawn or on one the keys scroll to.
"""
import ast
import importlib.util
import inspect
import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

import numpy as np  # noqa: E402
import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()


def _load_capture():
    if 'pq_ui_capture' in sys.modules:
        return sys.modules['pq_ui_capture']
    spec = importlib.util.spec_from_file_location(
        'pq_ui_capture', _ROOT / 'tools' / 'ui' / 'capture.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pq_ui_capture'] = mod
    spec.loader.exec_module(mod)
    return mod


capture = _load_capture()
pytestmark = pytest.mark.usefixtures('ui_theme_isolated')

# The smallest window the bug bash drew, the supported floor, a middling
# screen and the one where the most names lost a word.
SIZES = ((960, 540), (1280, 720), (1920, 1080), (2560, 1440))


def _ids(size):
    return f'{size[0]}x{size[1]}'


def _data(*parts):
    with open(_ROOT.joinpath('data', *parts), encoding='utf-8') as f:
        return json.load(f)


# ---------------------------------------------------------------- reading a screen

class _Screen(capture.TracingSurface):
    """The traced screen, keeping each text surface to check it at the end."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.sources = []

    def reset_trace(self):
        super().reset_trace()
        self.sources.clear()

    def _note(self, source, dest, area=None):
        n = len(self.text_blits)
        super()._note(source, dest, area)
        if len(self.text_blits) > n:
            self.sources.append(source if area is None else None)

    def top(self):
        """(rect, text, info, source) of the text on the top layer."""
        i = self.last_overlay
        return [(r, t, inf, src) for (r, t), inf, src in
                zip(self.text_blits[i:], self.text_info[i:], self.sources[i:])]

    def seen(self):
        """The top layer's text that shows: its ink inside clip and window."""
        win = self.get_rect()
        out = []
        for r, t, inf, _src in self.top():
            ink = inf['ink']
            if ink.w and ink.h and ink.clip(inf['clip']).clip(win).size == ink.size:
                out.append((tuple(r), t))
        return out

    def painted_over(self):
        """Top-layer text with something drawn on it afterwards: its solid
        glyph pixels are no longer its colour. A measurement alone misses
        this (the band's pictures sat on "a minute")."""
        win = self.get_rect()
        out = []
        for r, text, inf, src in self.top():
            if src is None or inf['color'] is None or inf['has_bg']:
                continue
            box = r.clip(inf['clip']).clip(win)
            if box.w < 1 or box.h < 1:
                continue
            try:
                alpha = pygame.surfarray.array_alpha(src)
            except (ValueError, pygame.error):
                continue
            x, y = box.x - r.x, box.y - r.y
            solid = alpha[x:x + box.w, y:y + box.h] == 255
            if not solid.any():
                continue
            now = pygame.surfarray.array3d(self.subsurface(box))[solid].astype(int)
            kept = (np.abs(now - np.array(inf['color'])).max(axis=1) <= 6).mean()
            if kept < 0.99:
                out.append(text)
        return out


@pytest.fixture
def harness():
    with capture.harness():
        yield


def _game(size):
    pygame.display.set_mode(size)
    import layout
    layout.update(*size)
    screen = _Screen(size)
    capture.reset_sandbox()
    g = capture.build_game(screen, size)
    return g


def _look(g, draw=None):
    g.screen.reset_trace()
    (draw or g.render)()
    return g.screen.seen()


def _clean(g):
    """Nothing on the top layer is covered, outside the window or over the
    edge of its panel."""
    s = g.screen
    start = s.last_overlay
    out = [f'painted over: {t!r}' for t in s.painted_over()]
    out += [f'outside the window: {t!r}' for r, t in s.text_blits[start:]
            if r.w and r.h and not s.get_rect().contains(r)]
    out += [f'over a panel edge: {t!r}' for _r, t, _p in s.text_outside_panels()]
    return out


_WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)*")


def _words(text):
    return [w.lower() for w in _WORD.findall(str(text))]


def _stream(page):
    return ' ' + ' '.join(_words(' '.join(t for _r, t in page))) + ' '


def _missing(text, pages, run=4):
    """The runs of ``run`` words of ``text`` that no page shows together."""
    w = _words(text)
    run = min(run, len(w))
    if not run:
        return []
    streams = [_stream(p) for p in pages]
    lost = []
    for i in range(len(w) - run + 1):
        want = ' ' + ' '.join(w[i:i + run]) + ' '
        if not any(want in s for s in streams):
            lost.append(want.strip())
    return lost


def _read(g, down=None):
    """Every page Down reaches while the screen stays open, and the faults."""
    state = g.state
    pages = [_look(g)]
    faults = set(_clean(g))
    for _ in range(400):
        (down or (lambda: capture.press(g, pygame.K_DOWN)))()
        if g.state != state:
            break
        page = _look(g)
        if page == pages[-1]:
            break
        pages.append(page)
        faults.update(_clean(g))
    return pages, sorted(faults)


# ---------------------------------------------------------------- h3-08

@pytest.mark.parametrize('size', SIZES + ((1280, 650),), ids=_ids)
def test_h3_08_the_selected_spells_whole_description_is_on_the_screen(harness, size):
    import game_states as S
    from spells import LEARNABLE_SPELLS
    g = _game(size)
    sids = list(LEARNABLE_SPELLS)
    g.player.known_spells.clear()
    g.player.known_spells.update({s: LEARNABLE_SPELLS[s]['mp_cost'] for s in sids})
    g.player.mp = g.player.max_mp = 99
    capture.press(g, pygame.K_m, 'm')
    assert g.state == S.STATE_SPELL_MENU
    cut, faults = [], set()
    for sid in sids:
        g._spell_sel = g.spell_menu_items.index(sid)
        page = _look(g, g.render)
        if _missing(LEARNABLE_SPELLS[sid]['desc'], [page]):
            cut.append(sid)
        faults.update(f'{sid}: {f}' for f in _clean(g))
    assert not cut, f'spell lines cut at {_ids(size)}: {cut}'
    assert not faults, sorted(faults)


@pytest.mark.parametrize('size', [(960, 540), (1280, 720)], ids=_ids)
def test_h3_08_a_short_spell_list_shows_it_whole_and_keeps_its_height(harness, size):
    from spells import LEARNABLE_SPELLS
    g = _game(size)
    sids = ['dionysus_vine_spell', 'light_spell', 'detect_magic_spell']
    g.player.known_spells.clear()
    g.player.known_spells.update({s: LEARNABLE_SPELLS[s]['mp_cost'] for s in sids})
    capture.press(g, pygame.K_m, 'm')
    tops = set()
    for i, sid in enumerate(g.spell_menu_items):
        assert g._spell_sel == i
        page = _look(g)
        assert not _missing(LEARNABLE_SPELLS[sid]['desc'], [page]), sid
        tops.add(min(r[1] for r, t in page if t == LEARNABLE_SPELLS[g.spell_menu_items[0]]['name']))
        capture.press(g, pygame.K_DOWN)
    assert len(tops) == 1, 'the rows jump as the selection moves'


# ---------------------------------------------------------------- h3-09

def _help_rows():
    """(key, description) of every row of the command map, from its source."""
    import game_render
    src = inspect.cleandoc('\n' + inspect.getsource(game_render.RenderMixin._draw_help_screen))
    out = []
    for node in ast.walk(ast.parse(src)):
        if (isinstance(node, ast.Tuple) and len(node.elts) == 3
                and all(isinstance(e, ast.Constant) and isinstance(e.value, str)
                        for e in node.elts[:2])):
            out.append((node.elts[0].value, node.elts[1].value))
    return out


@pytest.mark.parametrize('size', [(800, 480), (900, 440), (960, 540), (1000, 520), (1024, 600),
                                  (1200, 675), (1280, 680), (1280, 720), (2560, 1440)], ids=_ids)
def test_h3_09_every_help_row_is_reachable(harness, size):
    from fantasy_ui import key_label
    g = _game(size)
    capture.press(g, pygame.K_SLASH, '?')
    pages, faults = _read(g)
    rows = _help_rows()
    assert len(rows) >= 50
    seen = [t for p in pages for _r, t in p]
    text = [' ' + ' '.join(_words(t)) + ' ' for t in seen]
    missing = []
    for key, desc in rows:
        # A row of the map (a badge and its words), or "key: words" in the
        # list a very small window scrolls.
        mapped = desc in seen and key_label(key) in seen
        listed = not _missing(f'{key_label(key)} {desc}', pages)
        if not (mapped or listed):
            missing.append((key, desc))
    assert text and not missing, f'not listed at {_ids(size)}: {missing}'
    assert not faults, faults


# ---------------------------------------------------------------- h3-10

_KIT_HINT = 'Shift+Up/Down or the mouse wheel: scroll'
_KIT_SCENES = ('menu_kit_result', 'menu_kit_known_by_hand', 'menu_kit_gloves',
               'menu_kit_at_your_back', 'menu_kit_spheres', 'menu_kit_valuables')


@pytest.mark.parametrize('size', SIZES, ids=_ids)
def test_h3_10_the_kit_cards_scroll_hint_is_whole_and_its_end_is_reached(harness, monkeypatch, size):
    by_name = {sc.name: sc for sc in capture.SCENES}
    hinted = 0
    for name in _KIT_SCENES:
        g = _game(size)
        by_name[name].setup(g)
        shown = []
        real = g._ui_draw_scroll_lines

        def spy(lines, *a, **k):
            shown[:] = [str(entry[0]) for entry in lines]
            return real(lines, *a, **k)
        g._ui_draw_scroll_lines = spy
        first = _look(g)
        if any(t.startswith('Shift+Up/Down') for _r, t in first):
            hinted += 1
            assert not _missing(_KIT_HINT, [first], run=len(_words(_KIT_HINT))), (name, size)
            assert not _clean(g), (name, _clean(g))
        with monkeypatch.context() as mp:
            mp.setattr(pygame.key, 'get_mods', lambda: pygame.KMOD_SHIFT)
            pages, _faults = _read(g)
        # Every line of the card, not its last alone: Shift+Down must not
        # step over lines in a pane only a line or two tall.
        seen = {t for page in pages for _r, t in page}
        skipped = [line for line in shown if line.strip() and line not in seen]
        assert not skipped, (name, size, skipped[:4])
    if size[0] <= 1280:
        assert hinted, 'no card needed to scroll'


# ---------------------------------------------------------------- h3-11

@pytest.mark.parametrize('size', SIZES + ((800, 600), (1000, 520)), ids=_ids)
def test_h3_11_every_story_popup_keeps_every_word(harness, size):
    g = _game(size)
    for key, data in g._STORY_CONTENT.items():
        g._show_story_popup(key)
        pages, faults = _read(g)
        for para in ' '.join(ln or '\n' for ln in data['lines']).split('\n'):
            assert not _missing(para, pages), (key, size, _missing(para, pages)[:3])
        assert not faults, (key, faults)
        if len(pages) > 1:
            assert any('scroll' in t.lower() for _r, t in pages[0]), f'{key}: no word on how to scroll'
        capture.press(g, pygame.K_RETURN)


def _long_popup(title='A LONG TALE', n=40):
    return {'title': title, 'accent': (80, 120, 200), 'code': None,
            'lines': [f'The {i}th mile of the road was as weary as the one before it.'
                      for i in range(n)] + ['', f'So ends {title}.']}


@pytest.mark.parametrize('size', [(960, 540), (1280, 720)], ids=_ids)
@pytest.mark.parametrize('key', [pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_a,
                                 pygame.K_LEFT, pygame.K_PAGEDOWN])
def test_h3_11_any_other_key_still_closes_a_story_that_scrolls(harness, size, key):
    import game_states as S
    g = _game(size)
    g._queue_popup(_long_popup(), 'test')
    g._open_next_popup(S.STATE_PLAYER)
    first = _look(g)
    capture.press(g, pygame.K_DOWN)
    assert g.state == S.STATE_STORY_POPUP and _look(g) != first, 'Down did not scroll'
    capture.press(g, pygame.K_UP)
    assert g.state == S.STATE_STORY_POPUP and _look(g) == first, 'Up did not scroll back'
    capture.press(g, key)
    assert g.state == S.STATE_PLAYER


@pytest.mark.parametrize('size', [(960, 540), (1280, 720)], ids=_ids)
def test_h3_11_a_popup_that_fits_closes_on_the_arrows_and_the_next_starts_at_its_top(harness, size):
    import game_states as S
    g = _game(size)
    for key in (pygame.K_UP, pygame.K_DOWN):
        g._show_load_summary_popup()
        _look(g)
        capture.press(g, key)
        assert g.state == S.STATE_PLAYER, 'nothing more to read: an arrow closes it, as it did'
    g._queue_popup(_long_popup('THE FIRST TALE'), 'test')
    g._queue_popup(_long_popup('THE SECOND TALE'), 'test')
    g._open_next_popup(S.STATE_PLAYER)
    pages, _faults = _read(g)
    assert not _missing('So ends THE FIRST TALE.', pages)
    capture.press(g, pygame.K_RETURN)
    page = _look(g)
    assert g.state == S.STATE_STORY_POPUP
    assert not _missing('The 0th mile of the road', [page]), 'the next popup opened part-way down'


@pytest.mark.parametrize('count', [1, 2, 3])
@pytest.mark.parametrize('size', SIZES + ((800, 600), (1000, 520)), ids=_ids)
def test_h3_11_three_achievements_at_once_keep_their_words(harness, size, count):
    import game_states as S
    g = _game(size)
    # (made-up codes: no real one is made or drawn here)
    rows = sorted(_data('achievements.json')['achievements'],
                  key=lambda a: len(a['name']) + len(a['unlocked_text']), reverse=True)[:count]
    entries = [{'id': a['id'], 'name': a['name'], 'text': a['unlocked_text'],
                'code': f'XXXX-XXXX{i}', 'rarity': a['rarity'], 'art': a.get('art', a['id'])}
               for i, a in enumerate(rows)]
    g.popup_data = {'title': 'ACHIEVEMENTS UNLOCKED', 'accent': (200, 170, 255), 'code': None,
                    'lines': ['Show these codes to Dad.'], 'achievements': entries}
    g.state = S.STATE_STORY_POPUP
    pages, faults = _read(g)
    for e in entries:
        for text in (e['name'], e['text'], e['code']):
            assert not _missing(text, pages), (text, size)
    assert not _missing('Show these codes to Dad.', pages)
    assert not faults, faults
    if len(pages) > 1:
        assert any('scroll' in t.lower() for _r, t in pages[0]), 'no word on how to scroll'
    capture.press(g, pygame.K_RETURN)
    assert g.state == S.STATE_PLAYER


# ---------------------------------------------------------------- h3-12

def _dossiers(g):
    import items
    from monster import Monster
    for f in sorted(os.listdir(_ROOT / 'data' / 'items')):
        d = _data('items', f)
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            if not isinstance(v, dict) or k.startswith('_'):
                continue
            try:
                it = items.make_item_by_id(f[:-5], k)
            except (KeyError, OSError, ValueError, TypeError, AttributeError):
                continue                        # a table, not a kind of item
            if it is None:
                continue
            it.identified = it.buc_known = True
            it.id_level = 5
            g.player.known_item_ids.add(k)
            yield f'{f[:-5]}/{k}', it
    for k, v in capture._monster_defs().items():
        if not isinstance(v, dict) or not v.get('name'):
            continue
        g.player.studied_monster_ids.add(k)
        g.player.known_monster_ids.add(k)
        it = g._make_corpse(Monster({**v, 'id': k}, g.player.x, g.player.y))
        it.id_level = 5
        yield f'corpse/{k}', it


@pytest.mark.parametrize('size', SIZES, ids=_ids)
def test_h3_12_no_dossier_line_is_wider_than_it_is_drawn_and_each_pane_shows_its_end(
        harness, monkeypatch, size):
    """Every item and creature: the panes are measured and scrolled to their
    ends. Only the art and the frame are left out, which this does not judge."""
    import game_render
    from ui_scale import px as S
    g = _game(size)
    for name in ('draw_overlay', 'draw_dark_panel'):
        monkeypatch.setattr(game_render, name, lambda *a, **k: None)
    g._draw_lore_plate = lambda *a, **k: None
    real_scroll, real_blit = g._ui_draw_scroll_lines, g._ui_blit_text
    drawn, wide, unreached = [], {}, {}
    current = ['']
    g._ui_blit_text = lambda text, *a, **k: drawn.append(str(text))

    def spy(lines, font, color, rect, scroll=0, **k):
        for text, _col, fnt in lines:
            if (fnt or font).size(text)[0] > rect.w - S(12):
                wide.setdefault(current[0], text)
        del drawn[:]
        out = real_scroll(lines, font, color, rect, 10 ** 6, **k)
        last = next((t for t, _c, _f in reversed(lines) if str(t).strip()), None)
        if last is not None and last not in drawn:
            unreached.setdefault(current[0], last)
        return out
    g._ui_draw_scroll_lines = spy
    n = 0
    for name, it in _dossiers(g):
        current[0] = name
        g._lore_subject = it
        g._draw_lore_dossier_screen()
        n += 1
    g._ui_blit_text = real_blit
    assert n >= 1600, n
    assert not wide, f'{len(wide)} dossiers lose a word: {list(wide.items())[:8]}'
    assert not unreached, f'{len(unreached)} panes hide their end: {list(unreached.items())[:8]}'


@pytest.mark.parametrize('size', SIZES, ids=_ids)
def test_h3_12_the_dossiers_headline_is_drawn_whole(harness, size):
    import game_states as S
    g = _game(size)
    want = ('Ring of Invisibility II', 'Potion of Extra Healing', 'Amulet of Slowing',
            'Iron Boots of Thor', "Draught of Mimir's Well")
    made = 0
    for _key, it in _dossiers(g):
        if it.name not in want:
            continue
        made += 1
        g._lore_subject = it
        g._lore_focus = 'identity'
        g._lore_identity_scroll = g._lore_mech_scroll = g._lore_text_scroll = 0
        g.state = S.STATE_LORE
        pages, faults = _read(g)
        assert not _missing(it.name, pages, run=len(_words(it.name))), (it.name, size)
        assert not faults, (it.name, faults)
    assert made >= 3, made


# ---------------------------------------------------------------- h3-13

def _open_set_piece(g, which):
    if which == 'emberpup':
        g._start_emberpup_encounter(capture._emberpup(g))
        return list(_data('abandoned_emberpup.json')['story'])
    if which == 'mooble':
        g._start_mooble_encounter(capture._mooble(g))
        return list(_data('mooble.json')['story'])
    npc = capture._bococho_camp(g)
    who = 'varro' if which == 'varro' else 'young'
    g._bococho_open(who, npc)
    return list(_data('bococho.json')['varro_story' if who == 'varro' else 'story'])


_PIECES = {'emberpup': '_emberpup_phase', 'mooble': '_mooble_phase',
           'bococho': '_bc_phase', 'varro': '_bc_phase'}


@pytest.mark.parametrize('which', list(_PIECES))
@pytest.mark.parametrize('size', SIZES + ((800, 600), (1024, 560)), ids=_ids)
def test_h3_13_the_set_pieces_story_keeps_every_word(harness, size, which):
    g = _game(size)
    paras = _open_set_piece(g, which)
    pages, faults = _read(g)
    for para in paras:
        assert not _missing(para, pages), (which, size, _missing(para, pages)[:3])
    assert not faults, faults
    if len(pages) > 1:
        assert any('scroll' in t.lower() for _r, t in pages[0]), 'no word on how to scroll'
    assert getattr(g, _PIECES[which]) == 'story', 'scrolling turned the page'
    # A key that means nothing here leaves the reader where he was.
    capture.press(g, pygame.K_x, 'x')
    assert _look(g) == pages[-1]
    capture.press(g, pygame.K_RETURN)
    assert getattr(g, _PIECES[which]) == 'options'


@pytest.mark.parametrize('which', list(_PIECES))
def test_h3_13_escape_still_walks_away_from_a_page_that_scrolls(harness, which):
    import game_states as S
    g = _game((960, 540))
    _open_set_piece(g, which)
    _read(g)
    capture.press(g, pygame.K_ESCAPE)
    assert g.state == S.STATE_PLAYER


@pytest.mark.parametrize('which', list(_PIECES))
@pytest.mark.parametrize('size', [(960, 540), (1280, 720)], ids=_ids)
def test_h3_13_a_long_result_scrolls_and_the_next_starts_at_its_top(harness, size, which):
    g = _game(size)
    _open_set_piece(g, which)
    tell = {'emberpup': g._emberpup_outcome, 'mooble': g._mooble_outcome}.get(
        which, g._bococho_outcome)
    text = ' '.join(_long_popup()['lines'])
    tell(text, 'options')
    pages, faults = _read(g)
    assert not _missing(text, pages)
    assert not faults, faults
    capture.press(g, pygame.K_RETURN)
    tell(text, 'options')
    assert _look(g) == pages[0]


# ---------------------------------------------------------------- h3-14

DANCE_SIZES = ((960, 540), (1024, 600), (1093, 614), (1280, 650), (1280, 680), (1280, 720),
               (1366, 728), (1920, 1080), (2560, 1440), (3440, 1440))


def _dance_words(g):
    """Every text the dance screen has to say in its state now."""
    import mooble_encounter as mo
    import rhythm
    md = g._mdance
    sc, tl, phase, special = md['words'], md['tl'], md['phase'], md['mode'] == 'special'
    want = list(md.get('info_lines') or [md['info']])
    want += [sc['your_row']] + ([sc['his_row']] if tl['call'] else [])
    if phase == 'ready':
        want.append(md.get('ready_head') or sc['how'])
    elif phase == 'result':
        if md.get('result_head'):
            want.append(md['result_head'])
        elif special:
            want.append(md['band']['line'].replace('{pet}', md['pet'].name))
        elif md['mode'] == 'dance':
            want.append(sc['dance_pass' if md['won'] else 'dance_fail'])
        else:
            want.append(sc['practice_pass' if md['won'] else 'practice_fail'])
        res = md['result']
        if not md.get('hide_result_line'):
            one, many = sc.get('miss_words') or ('{n} miss', '{n} misses')
            misses = (one if res['misses'] == 1 else many).format(n=res['misses'])
            want.append(sc['result_line'].format(hits=res['hits'], steps=res['total'],
                                                 perfects=res['perfects'], misses=misses))
    extra = list(md.get('result_lines') or ()) if phase == 'result' else []
    want += extra
    if special:
        want.append(mo.special_result_line(md['band']) if phase == 'result'
                    else mo.special_spec().get('how', ''))
    elif not extra:
        n = len(tl['response'])
        want.append(sc['pass_mark'].format(need=rhythm.hits_needed(n, md['pass_share']),
                                           steps=n, misses=md['max_misses']))
    if md['mode'] == 'practice':
        want.append(sc['practice_note'])
    return want


def _dance_check(g, bad, what):
    page = _look(g, g._draw_mooble_dance)
    for text in _dance_words(g):
        if _missing(text, [page]):
            bad.append(f'{what}: cut {text!r}')
    bad.extend(f'{what}: {f}' for f in _clean(g))


def _dance_at(g, where, hits=0):
    """The frozen clock at the count-in, in the call or in the response."""
    import rhythm
    md = g._mdance
    tl = md['tl']
    when = {'count': 20, 'call': (tl['call'] or tl['response'])[0][0] + 20,
            'turn': tl['response'][min(2, len(tl['response']) - 1)][0] + 20}[where]
    md.update({'phase': 'play', 't0': capture.FROZEN_TICKS_MS - int(when),
               'presses': rhythm.on_time(tl['response'][:hits])})


@pytest.mark.parametrize('size', DANCE_SIZES, ids=_ids)
def test_h3_14_the_dance_off_says_all_of_its_rules_and_penalties(harness, size):
    import stray_kids
    g = _game(size)
    capture._sk_dance(g, mode='practice')
    bad = []
    do = stray_kids.dance_off()
    for r in range(stray_kids.rounds()):
        g.player.hp = g.player.max_hp
        g._sk_open_dance('practice')
        _dance_check(g, bad, f'round {r} card')
        for where in ('count', 'call', 'turn'):
            _dance_at(g, where, 2)
            _dance_check(g, bad, f'round {r} practice {where}')
        for hits in (0, 99):
            g._sk_open_dance('practice')
            _dance_at(g, 'turn', hits)
            g._mooble_dance_finish()
            _dance_check(g, bad, f'round {r} practice result {hits}')
        g._sk_open_dance('dance')
        md = g._mdance
        lead = next(m for m in stray_kids.the_band(g.monsters) if m.member == md['sk_member'])
        for line in do['leaders'][lead.member]['open']:
            md['ready_head'] = g._stray_kids_line(lead, line)
            _dance_check(g, bad, f'round {r} open')
        _dance_at(g, 'turn', 1)
        _dance_check(g, bad, f'round {r} dance')
        for strikes in (3, 1):
            g.player.hp = g.player.max_hp
            g._sk_open_dance('dance', strikes=strikes)
            _dance_at(g, 'turn', 1)
            g._mooble_dance_finish()
            md = g._mdance
            for line in do['leaders'][lead.member]['roast']:
                md['result_head'] = g._stray_kids_line(lead, line)
                _dance_check(g, bad, f'round {r} lost, {strikes} left')
        g._sk_open_dance('dance')
        _dance_at(g, 'turn', 99)
        g._mooble_dance_finish()
        _dance_check(g, bad, f'round {r} won')
    assert not bad, f'{len(bad)} at {_ids(size)}:\n' + '\n'.join(bad[:30])


@pytest.mark.parametrize('size', DANCE_SIZES, ids=_ids)
def test_h3_14_the_moobles_dances_say_all_they_have_to_say(harness, size):
    import mooble_encounter as mo
    g = _game(size)
    m = capture._mooble(g, fed=True)
    g._mooble_npc = m
    bad = []
    for visit in range(len(mo.data()['dance']['visits'])):
        for mode in ('practice', 'dance'):
            m._mooble_dances = visit
            g._mooble_open_dance(mode)
            _dance_check(g, bad, f'{visit} {mode} ready')
            for where in ('count', 'call', 'turn'):
                _dance_at(g, where, 2)
                _dance_check(g, bad, f'{visit} {mode} {where}')
            for hits in (0, 99):
                g._mooble_open_dance(mode)
                _dance_at(g, 'turn', hits)
                g._mooble_dance_finish()
                _dance_check(g, bad, f'{visit} {mode} result {hits}')
    g = _game(size)
    md = capture._mooble_special(g, at_step=2, hits=2)
    _dance_check(g, bad, 'special')
    g._mooble_dance_finish()
    for band in mo.special_spec()['bands']:
        md['band'] = band
        _dance_check(g, bad, f'special {band}')
    assert not bad, f'{len(bad)} at {_ids(size)}:\n' + '\n'.join(bad[:30])


# ---------------------------------------------------------------- h3-15

@pytest.mark.parametrize('size', SIZES + ((1024, 600),), ids=_ids)
@pytest.mark.parametrize('gold', [1234, 9_999_999])
def test_h3_15_drop_golds_prompt_is_whole(harness, size, gold):
    import game_states as S
    from treasure import weight_text
    g = _game(size)
    g.player_gold = gold
    g.drop_gold_input = '250'
    g.state = S.STATE_DROP_GOLD_INPUT
    page = _look(g)
    for text in (f'You have {gold:,} gold, weighing {weight_text(gold)}.',
                 'Enter the amount to drop on your current tile.', '250'):
        assert not _missing(text, [page]), (text, size)
    assert not _clean(g), _clean(g)


# ---------------------------------------------------------------- h3-16

@pytest.mark.parametrize('size', SIZES, ids=_ids)
def test_h3_16_every_encounters_title_and_chip_are_whole(harness, size):
    import game_states as S
    from flavor_encounters import FLAVOR_ENCOUNTERS
    from npc_encounters import ENCOUNTERS
    g = _game(size)
    where = g._capture_monster
    bad = []
    for flavor, encs in ((False, ENCOUNTERS), (True, FLAVOR_ENCOUNTERS)):
        for enc in encs:
            g.state = S.STATE_PLAYER
            g._npc_open(enc, where, flavor=flavor)
            g._npc_item_list, g._npc_item_scroll = [], 0
            g._npc_outcome_text = 'It is done.'
            for phase, chip in (('text', 'Encounter'), ('options', 'Choice'),
                                ('select_item', 'Offer'), ('outcome', 'Result')):
                g._npc_encounter_phase = phase
                g._npc_selected_option = None
                page = _look(g, g._draw_npc_encounter)
                title = [t for _r, t in page[:1]]
                if _words(' '.join(title)) != _words(enc['name']):
                    bad.append(f'title {enc["name"]!r} -> {title}')
                if chip.lower() not in [t.lower() for _r, t in page]:
                    bad.append(f'chip {chip!r} on {enc["name"]!r}')
                if phase == 'text':
                    bad.extend(f'{enc["name"]}: {f}' for f in g.screen.painted_over())
    bad = sorted(set(bad))
    assert not bad, f'{len(bad)} at {_ids(size)}: {bad[:12]}'


# ---------------------------------------------------------------- h3-17

@pytest.mark.parametrize('studied', [True, False])
@pytest.mark.parametrize('size', SIZES, ids=_ids)
def test_h3_17_every_bestiary_row_is_whole(harness, size, studied):
    g = _game(size)
    kinds = [k for k, v in capture._monster_defs().items() if isinstance(v, dict) and v.get('name')]
    g.player.known_monster_ids.update(kinds)
    g.player.studied_monster_ids.clear()
    if studied:
        g.player.studied_monster_ids.update(kinds)
    capture.press(g, pygame.K_b, 'b')
    capture.press(g, pygame.K_RETURN)
    entries = g.encyclopedia_entries
    assert len(entries) >= 400
    rows, faults = set(), set()
    for sel in sorted({*range(0, len(entries), 2), len(entries) - 1}):
        g.encyclopedia_selection = sel
        page = _look(g, g._draw_encyclopedia_browser)
        rows.add(_stream(page))
        if sel % 50 == 0:
            faults.update(_clean(g))
    everything = '\n'.join(rows)
    lost = []
    for e in entries:
        text = f"{g._fix_name_case(e.get('name', ''))} {g._encyclopedia_entry_brief('bestiary', e)}"
        if ' ' + ' '.join(_words(text)) + ' ' not in everything:
            lost.append(text)
    assert not lost, f'{len(lost)} rows cut at {_ids(size)}: {lost[:6]}'
    assert not faults, sorted(faults)


@pytest.mark.parametrize('size', [(960, 540), (1280, 720)], ids=_ids)
def test_h3_17_the_captured_bestiary_rows_lose_nothing(harness, size):
    by_name = {sc.name: sc for sc in capture.SCENES}
    for name in ('menu_bestiary_family_line', 'menu_bestiary_ward', 'menu_bestiary_short_page'):
        g = _game(size)
        by_name[name].setup(g)
        page = _look(g)
        e = g.encyclopedia_entries[g.encyclopedia_selection]
        brief = g._encyclopedia_entry_brief('bestiary', e)
        assert not _missing(brief, [page], run=len(_words(brief))), (name, size, brief)
