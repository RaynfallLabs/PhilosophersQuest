"""The fourth bug bash (2026-10-16): drawing cost, caches, art fallbacks and
the monkey fuzzer's F4 finds. UI-18/MK-13, UI-19, UI-20, UI-21/CQ-13, UI-22,
MK-05, MK-08, MK-09.
"""
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


@pytest.fixture
def save_dir(tmp_path, monkeypatch):
    import save_system
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    return tmp_path


def _game(size=(1280, 720)):
    from main import Game
    from game_states import STATE_PLAYER
    g = Game(pygame.display.set_mode(size), player_name='bb4render')
    g.state = STATE_PLAYER
    return g


def _kd(k, uni=''):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode=uni, scancode=0)


# ---------------------------------------------------------------- UI-22
def test_every_creature_has_its_own_art():
    """The renderer borrowed a same-symbol creature's sprite for one with no
    art (and a 46-entry hand table of the same): a renamed file would have
    shown a different creature silently. Every creature has art now; a
    missing file fails here instead."""
    sprites = {f[:-4] for f in os.listdir(os.path.join(ROOT, 'assets', 'tiles', 'monsters'))
               if f.endswith('.png')}
    ids = set(json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8')))
    ids |= {'player_ghost', 'death', 'deadite', 'secret_cow', 'ethereal_unicorn', 'npc_traveler'}
    for name in ('npc_encounters.json', 'flavor_encounters.json'):
        txt = open(os.path.join(ROOT, 'data', name), encoding='utf-8').read()
        ids |= set(re.findall(r'"sprite_id":\s*"([^"]+)"', txt))
    assert sorted(ids - sprites) == []
    import renderer
    assert not hasattr(renderer, '_MONSTER_SPRITE_FALLBACK_OVERRIDE')
    assert not hasattr(renderer, '_resolve_monster_sprite_fallback')


# ---------------------------------------------------------------- UI-21 / CQ-13
def test_lore_art_caches_are_bounded():
    """Plates and their full-size sources were kept forever, one plate per
    subject per window size (83-231 MiB in a long session)."""
    import lore_art
    pygame.display.set_mode((1280, 720))
    lore_art.clear_cache()
    mons = sorted(json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8')))
    for mid in mons[:30]:
        for px in (120, 160, 200):
            lore_art.plate('monster', mid, px)
    assert len(lore_art._plates) <= lore_art.PLATES_MAX
    assert len(lore_art._raw) <= lore_art.RAW_MAX
    # The most recent plate is still served from the cache.
    last = lore_art.plate('monster', mons[29], 200)
    assert lore_art.plate('monster', mons[29], 200) is last
    lore_art.clear_cache()


def test_dim_overlay_cache_is_bounded():
    import renderer
    g = _game()
    for t in range(10, 40):
        g.renderer._get_dim_overlay(t)
    assert len(renderer.Renderer._dim_overlay_cache) <= 4


# ---------------------------------------------------------------- UI-19
def test_map_draws_only_the_tiles_on_screen(save_dir, monkeypatch):
    """Every frame walked all 4,000 tiles at every zoom."""
    g = _game()
    r = g.renderer
    calls = []
    import renderer as R
    real = R._tile_sprite_name
    monkeypatch.setattr(R, '_tile_sprite_name', lambda *a: calls.append(1) or real(*a))
    d = g.dungeon
    every = {(x, y) for y in range(d.height) for x in range(d.width)}
    import layout
    small = pygame.Surface((layout.MAP_X + 300, 300))
    r.screen = small
    r.draw_dungeon(d, every)
    assert 0 < len(calls) < d.width * d.height // 4
    # ...but everything in sight is still explored.
    assert every <= d.explored


# ---------------------------------------------------------------- UI-20
def test_strike_finisher_reuses_its_layer_and_scales_its_ring(monkeypatch):
    """A map-sized surface was allocated every frame, and the ring radius
    was fixed pixels while the banner font grew (the ring cut the text)."""
    import layout
    from effects.strike_finisher import StrikeFinisher
    import ui_scale
    surf = pygame.Surface((1600, 900), pygame.SRCALPHA)
    radii = []
    monkeypatch.setattr(StrikeFinisher, '_ring',
                        staticmethod(lambda layer, cx, cy, radius, color, alpha: radii.append(radius)))

    def run(scale):
        ui_scale.set_scale(scale)
        f = StrikeFinisher()
        f.trigger({'chain': 12, 'damage': 40, 'rank_name': 'Legend', 'rank_color': (200, 100, 50)})
        f.update(0.0, False)
        radii.clear()
        f.draw_overlay(surf, False)
        layer = f._layer
        f.update(0.05, False)
        f.draw_overlay(surf, False)
        return layer, f._layer, radii[0]
    snap = layout.snapshot()
    try:
        a1, a2, r1 = run(1.0)
        b1, b2, r2 = run(2.0)
    finally:
        layout.restore(snap)
    assert a1 is a2 and b1 is b2
    assert r2 >= 2 * r1 - 2


def test_chain_aura_glow_follows_the_scale():
    import layout
    import ui_scale
    from effects import chain_aura
    snap = layout.snapshot()
    try:
        ui_scale.set_scale(1.0)
        p1 = chain_aura._glow_pad()
        m1 = chain_aura._glow_mask(300, 200)
        ui_scale.set_scale(2.0)
        p2 = chain_aura._glow_pad()
        m2 = chain_aura._glow_mask(300, 200)
    finally:
        layout.restore(snap)
    assert p2 == 2 * p1
    assert m2.get_width() - m1.get_width() == 2 * (p2 - p1)


# ---------------------------------------------------------------- UI-18 / MK-13
def test_a_queued_old_size_is_not_laid_out(save_dir, monkeypatch):
    """A drag queues many sizes; each one across a scale step re-cut the
    whole art kit. Only the size the window has now is laid out."""
    g = _game((1600, 900))
    seen = []
    monkeypatch.setattr(type(g), 'on_resize', lambda self, w, h: seen.append((w, h)))
    for w, h in ((1700, 950), (1900, 1000), (2000, 1100)):
        g.handle_event(pygame.event.Event(pygame.WINDOWRESIZED, x=w, y=h))
    assert seen == []
    pygame.display.set_mode((2000, 1100))
    g.handle_event(pygame.event.Event(pygame.WINDOWRESIZED, x=2000, y=1100))
    assert seen == [(2000, 1100)]


def test_returning_to_a_scale_reuses_its_cut_kit(tmp_path):
    import layout
    import ui_theme
    saved = ui_theme.save_state()
    snap = layout.snapshot()
    try:
        pygame.display.set_mode((1280, 720))
        layout.update(1280, 720)
        img = pygame.Surface((32, 32), pygame.SRCALPHA)
        img.fill((200, 160, 40, 255))
        pygame.image.save(img, str(tmp_path / 'panel.png'))
        (tmp_path / 'manifest.json').write_text(json.dumps(
            {'version': 1, 'scale': 2, 'pieces': {'panel': {'file': 'panel.png',
                                                            'slice': [8, 8, 8, 8]}}}))
        ui_theme.load(str(tmp_path))
        k1 = ui_theme.save_state()
        layout.update(2560, 1440)
        k2 = ui_theme.save_state()
        layout.update(1280, 720)
        assert ui_theme.save_state() is k1
        layout.update(2560, 1440)
        assert ui_theme.save_state() is k2
    finally:
        layout.restore(snap)
        ui_theme.restore_state(saved)


# ---------------------------------------------------------------- MK-05
def test_f11_failure_does_not_fail_the_question(save_dir, monkeypatch):
    """toggle_fullscreen raising pygame.error reached the frame's recovery
    handler, which answered the open question wrong."""
    from game_states import STATE_QUIZ
    g = _game()
    results = []
    g.state = STATE_QUIZ
    g.quiz_engine.start_quiz('threshold', 'history', 1,
                             lambda r: results.append(r.success), threshold=1)

    def boom():
        raise pygame.error('no fullscreen here')
    monkeypatch.setattr(pygame.display, 'toggle_fullscreen', boom)
    assert g.handle_event(_kd(pygame.K_F11)) is True
    assert results == [] and g.quiz_engine.callback is not None
    assert g.state == STATE_QUIZ


# ---------------------------------------------------------------- MK-08
def test_window_close_in_the_missed_review_does_not_offer_save(save_dir):
    """Closing the window in the missed-question review (or a popup after
    death) opened "Save & Exit" for a dead hero."""
    from game_states import STATE_REVIEW_MISSED, STATE_STORY_POPUP, STATE_CONFIRM_EXIT
    for state in (STATE_REVIEW_MISSED, STATE_STORY_POPUP):
        g = _game()
        g._run_over = True
        g.state = state
        assert g.handle_event(pygame.event.Event(pygame.QUIT)) is False
        assert g.state != STATE_CONFIRM_EXIT
        assert g._window_closed is True


# ---------------------------------------------------------------- MK-09
def test_trap_and_ambusher_messages_use_an(save_dir):
    """"You spot a acid trap", "detect a Abyssal Mimic"."""
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    for bad in ("You notice a {", "Searching reveals a {", "You spot a {",
                "detect a {m.name}", "Stepped on a {", "Rewired a {"):
        assert bad not in src, bad
    g = _game()
    assert g._a_or_an('acid') == 'an acid'
    assert g._a_or_an('Abyssal Mimic') == 'an Abyssal Mimic'
