"""The Seeker Profile UI (src/seeker_screen.py, the title's Seeker card and
Konami code, Encyclopedia tab n): pure checks of the badge cache, the
Konami detector, the name view and the no-Seeker Encyclopedia.

The screens themselves are drawn and gated by tools/ui/capture.py
(seeker_*, title_seeker_*, title_achievement_card,
menu_encyclopedia_achievements*, popup_achievement_*).
"""
import os

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame  # noqa: E402
import pytest  # noqa: E402

import seeker_codes  # noqa: E402
import seeker_profile  # noqa: E402
import seeker_screen  # noqa: E402

pygame.init()


@pytest.fixture(autouse=True)
def _isolated(tmp_path):
    saved = (seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE, seeker_screen.ART_DIR)
    seeker_codes._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}
    seeker_profile._DIR_OVERRIDE = str(tmp_path / 'seekers')
    art = tmp_path / 'art'
    art.mkdir()
    seeker_screen.ART_DIR = str(art)
    seeker_screen.clear_cache()
    pygame.display.set_mode((1280, 720))
    yield tmp_path
    seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE, seeker_screen.ART_DIR = saved
    seeker_screen.clear_cache()


def _key(key, unicode='', mod=0):
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode, mod=mod, scancode=0)


def _saturation(surf):
    """Largest channel spread of any visible pixel (0 for pure grey)."""
    rgb = pygame.surfarray.array3d(surf).astype(int)
    alpha = pygame.surfarray.array_alpha(surf)
    spread = rgb.max(axis=2) - rgb.min(axis=2)
    return int(spread[alpha > 0].max())


# -- badges ---------------------------------------------------------------------

def test_a_missing_badge_is_a_medallion_of_the_right_size():
    s = seeker_screen.badge_surface('questions_100', 64, True)
    assert s.get_size() == (64, 64)
    assert not seeker_screen.has_art('questions_100')
    # A medallion is round: the corners are clear, the centre is not.
    assert s.get_at((0, 0)).a == 0 and s.get_at((32, 32)).a == 255


def test_locked_badges_are_grey_and_won_ones_are_not():
    won = seeker_screen.badge_surface('cow_king', 96, True)
    locked = seeker_screen.badge_surface('cow_king', 96, False)
    assert won is not locked
    assert _saturation(won) > 60            # violet: legendary
    # Greyscale and darkened (the tint is a touch cool): no colour left.
    assert _saturation(locked) <= 16
    assert pygame.image.tobytes(won, 'RGBA') != pygame.image.tobytes(locked, 'RGBA')


def test_the_installed_png_is_used_when_there_is_one(tmp_path):
    red = pygame.Surface((128, 128), pygame.SRCALPHA)
    red.fill((220, 30, 30, 255))
    pygame.image.save(red, str(tmp_path / 'art' / 'questions_100.png'))
    seeker_screen.clear_cache()
    assert seeker_screen.has_art('questions_100')
    s = seeker_screen.badge_surface('questions_100', 64, True)
    r, g, b, _a = s.get_at((32, 32))
    assert r > 200 and g < 60 and b < 60
    grey = seeker_screen.badge_surface('questions_100', 64, False).get_at((20, 20))
    assert abs(grey.r - grey.g) <= 12 and grey.r < 200


def test_the_badge_cache_is_bounded_and_reused():
    first = seeker_screen.badge_surface('questions_100', 40, True)
    assert seeker_screen.badge_surface('questions_100', 40, True) is first
    import achievements
    arts = [a['art'] for a in achievements.load().entries]
    for art in arts:
        for earned in (True, False):
            seeker_screen.badge_surface(art, 24, earned)
    assert len(seeker_screen._badges) <= seeker_screen.BADGES_MAX
    assert len(seeker_screen._raw) <= seeker_screen.RAW_MAX


def test_every_category_has_an_emblem_and_every_rarity_a_colour():
    import achievements
    book = achievements.load()
    for c in book.categories:
        assert seeker_screen.medallion(48, 'rare', c['id']).get_size() == (48, 48)
    colours = {seeker_screen.rarity_color(r) for r in achievements.RARITIES}
    assert len(colours) == len(achievements.RARITIES)


# -- the Konami code -------------------------------------------------------------------

K = pygame
CODE = [K.K_UP, K.K_UP, K.K_DOWN, K.K_DOWN, K.K_LEFT, K.K_RIGHT, K.K_LEFT, K.K_RIGHT, K.K_b, K.K_a]


def test_konami_detector():
    d = seeker_screen.KonamiDetector()
    assert [d.feed(k) for k in CODE] == [False] * 9 + [True]
    # A third Up first still counts; Shift for a capital B is ignored.
    d = seeker_screen.KonamiDetector()
    keys = [K.K_UP] + CODE[:8] + [K.K_LSHIFT, K.K_b]
    assert not any(d.feed(k) for k in keys)
    assert d.primed()
    assert d.feed(K.K_a)
    # Interrupted: no.
    d = seeker_screen.KonamiDetector()
    assert not any(d.feed(k) for k in CODE[:5] + [K.K_x] + CODE[5:])
    assert not d.primed()


def _welcome_frame(w):
    real = pygame.display.flip

    class Done(Exception):
        pass

    def flip(*_a, **_k):
        raise Done
    pygame.display.flip = flip
    try:
        w.run(type('Clock', (), {'tick': lambda self, *_: 16})())
    except Done:
        pass
    finally:
        pygame.display.flip = real


def test_the_title_konami_code_takes_back_its_b_and_a_and_wins():
    from welcome_screen import WelcomeScreen
    seeker_profile.set_active('Robyn')
    w = WelcomeScreen(pygame.display.get_surface(), '0')
    pygame.event.clear()
    pygame.event.post(_key(K.K_x, 'x'))
    for k in CODE:
        ch = {K.K_b: 'b', K.K_a: 'a'}.get(k, '')
        pygame.event.post(_key(k, ch))
    _welcome_frame(w)
    assert w.name_buf == 'x'
    assert [c['id'] for c in w._seeker_cards] == ['thirty_lives']
    assert seeker_profile.load('Robyn').is_unlocked('thirty_lives')
    # Any key puts the card away (and types nothing).
    pygame.event.post(_key(K.K_z, 'z'))
    _welcome_frame(w)
    assert w._seeker_cards == [] and w.name_buf == 'x'


def test_the_title_records_nothing_without_a_seeker_and_f4_opens_the_screen():
    from welcome_screen import WelcomeScreen
    w = WelcomeScreen(pygame.display.get_surface(), '0')
    assert w._seeker is None
    pygame.event.clear()
    for k in CODE:
        pygame.event.post(_key(k, {K.K_b: 'b', K.K_a: 'a'}.get(k, '')))
    _welcome_frame(w)
    assert w._seeker_cards == [] and w.name_buf == ''
    pygame.event.post(_key(K.K_F4))
    real = pygame.display.flip
    try:
        assert w.run(type('Clock', (), {'tick': lambda self, *_: 16})()) == ('__SEEKER_PROFILE__', None)
    finally:
        pygame.display.flip = real


# -- the name view ------------------------------------------------------------------------

def test_check_name():
    assert seeker_screen.check_name('  Robyn  ') == ('Robyn', '')
    assert seeker_screen.check_name('')[0] is None
    assert seeker_screen.check_name('!!!')[0] is None
    assert 'letter or number' in seeker_screen.check_name('!!!')[1]
    name, why = seeker_screen.check_name('x' * 40)
    assert name == 'x' * seeker_profile.NAME_MAX and why == ''


def test_the_name_view_opens_first_validates_and_names_the_seeker():
    s = seeker_screen.SeekerScreen(pygame.display.get_surface())
    assert s.phase == 'name' and s.session is None
    s.handle_key(_key(K.K_RETURN))
    assert s.name_error and s.phase == 'name'
    for ch in 'Dad':
        s.handle_key(_key(getattr(K, f'K_{ch.lower()}'), ch))
    s.handle_key(_key(K.K_RETURN))
    assert s.phase == 'gallery' and s.session is not None
    assert seeker_profile.active_name() == 'Dad'
    # Naming yourself Dad is worth a try.
    assert [c['id'] for c in s.cards] == ['nice_try']
    assert s.cards[0]['code'].startswith('NICETRY-')
    s.draw()                                    # the gallery with the card over it
    s.handle_key(_key(K.K_SPACE, ' '))          # puts the card away
    assert not s.cards
    s.draw()
    assert s.handle_key(_key(K.K_ESCAPE))       # Esc closes the screen
    s._close()
    assert seeker_profile.load('Dad').is_seen('nice_try')


def test_the_name_view_picks_an_existing_seeker_and_esc_goes_back():
    seeker_profile.set_active('Fianna')
    seeker_profile.set_active('Robyn')
    s = seeker_screen.SeekerScreen(pygame.display.get_surface())
    assert s.phase == 'gallery' and s.session.name == 'Robyn'
    s.handle_key(_key(K.K_F4))
    assert s.phase == 'name' and s.names == ['Fianna', 'Robyn']
    assert s.name_pick == 1                     # the active one
    s.draw()
    assert not s.handle_key(_key(K.K_ESCAPE)) and s.phase == 'gallery'
    s.handle_key(_key(K.K_F4))
    s.handle_key(_key(K.K_UP))
    s.handle_key(_key(K.K_RETURN))
    assert s.session.name == 'Fianna' and seeker_profile.active_name() == 'Fianna'


def test_gallery_keys_walk_badges_and_categories():
    seeker_profile.set_active('Robyn')
    s = seeker_screen.SeekerScreen(pygame.display.get_surface())
    s.draw()
    n = len(s._entries())
    s.handle_key(_key(K.K_LEFT))                # before the first: the last category's last
    assert s.cat == len(s.cats) - 1 and s.sel == len(s._entries()) - 1
    s.handle_key(_key(K.K_RIGHT))               # past the last: the first category
    assert s.cat == 0 and s.sel == 0
    s.handle_key(_key(K.K_DOWN))
    assert s.sel == min(n - 1, s._cols)
    s.handle_key(_key(K.K_TAB))
    assert s.cat == 1 and s.sel == 0
    s.handle_key(_key(K.K_TAB, mod=pygame.KMOD_SHIFT))
    assert s.cat == 0


# -- Encyclopedia tab n ------------------------------------------------------------------------

def _game():
    from main import Game
    g = Game(pygame.display.get_surface(), player_name='__test_seeker_ui__')
    g.state = 'player'
    return g


def test_the_encyclopedia_tab_without_a_seeker_says_how_to_choose_one():
    assert seeker_screen.encyclopedia_entries(None) == []
    g = _game()
    g._seeker = None
    g.handle_event(_key(K.K_b, 'b'))
    g.handle_event(_key(K.K_n, 'n'))
    assert g.encyclopedia_category == 'achievements'
    assert g.encyclopedia_entries == []
    g.handle_event(_key(K.K_TAB))               # nothing to cycle; no error
    g.render()
    text = ' '.join(t for t, _c, _f in g._encyclopedia_article_lines('achievements', None))
    assert 'Seeker' in text
    assert 'F4' in g._achievement_none_line()


def test_the_encyclopedia_tab_lists_a_seekers_achievements():
    import seeker_session
    seeker_profile.set_active('Robyn')
    g = _game()
    g._seeker = seeker_session.open_active()
    g._seeker.profile.unlock('questions_100', hero='Fianna')
    g.handle_event(_key(K.K_b, 'b'))
    g.handle_event(_key(K.K_n, 'n'))
    first = [e['_id'] for e in g.encyclopedia_entries]
    assert 'questions_100' in first and g.encyclopedia_entries[0]['_won']
    g.render()
    lines = [t for t, _c, _f in g._encyclopedia_article_lines('achievements', g.encyclopedia_entries[0])]
    assert any(t.startswith('HUNDRED-') for t in lines)
    assert 'Show this code to Dad.' in lines
    g.handle_event(_key(K.K_TAB))
    assert [e['_id'] for e in g.encyclopedia_entries] != first
    g.render()


def test_a_dev_code_always_fits_its_line():
    """A DEV- code (no key installed) with the longest code word drops to a
    narrower face on a narrow pane instead of being cut."""
    import achievements
    word = max((a['code_word'] for a in achievements.load().entries), key=len)
    code = f"DEV-{word}-7KQ4-M2XH"
    for width in (240, 300, 420):
        assert seeker_screen.code_font(code, width).size(code)[0] <= width
