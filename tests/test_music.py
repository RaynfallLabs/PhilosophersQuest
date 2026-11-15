"""The soundtrack (2026-11-14): Brandon's own "PQ Main Theme", looped under
everything from the title screen on; F5 switches it on the title and in the
game, remembered in settings.json beside (and apart from) the sound setting.

Headless the mixer is a dummy device, so these check what can be checked:
the track ships and loads, the loop is asked for, the key, the setting and
its persistence, the hold for a rhythm game, the release build. How it
SOUNDS (volume against the quiz sounds, the loop's seam) is Brandon's ear.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import music  # noqa: E402


@pytest.fixture
def settings(tmp_path, monkeypatch):
    path = tmp_path / 'settings.json'
    import sound_system
    monkeypatch.setattr(sound_system, '_settings_path', lambda: str(path))
    monkeypatch.setattr(music, '_on', None)
    monkeypatch.setattr(music, '_playing', False)
    monkeypatch.setattr(music, '_held', False)
    return path


def test_the_track_ships_and_is_an_ogg():
    path = os.path.join(ROOT, *music.TRACK)
    assert os.path.exists(path)
    with open(path, 'rb') as f:
        assert f.read(4) == b'OggS'


def test_it_loads_and_is_asked_to_loop(settings, monkeypatch):
    pygame.mixer.init()
    calls = {}
    monkeypatch.setattr(pygame.mixer.music, 'play',
                        lambda loops=0, start=0.0, fade_ms=0: calls.update(loops=loops))
    assert music.start()
    assert calls['loops'] == -1                      # forever, no gap


def test_f5_switches_it_and_the_choice_is_remembered_apart_from_sound(settings):
    settings.write_text(json.dumps({'sound': False}))
    assert music.is_on()                             # default on, sound or no sound
    assert music.toggle() is False
    data = json.loads(settings.read_text())
    assert data == {'sound': False, 'music': False}  # the sound setting kept
    music._on = None                                 # a new session reads it back
    assert music.is_on() is False
    assert music.toggle() is True and json.loads(settings.read_text())['music'] is True


def test_off_it_never_starts(settings):
    music.set_on(False)
    assert music.start() is False


def test_hold_and_release_for_a_rhythm_game(settings):
    pygame.mixer.init()
    music.start()
    music.hold()
    assert music.start() is False                    # held: nothing restarts it
    music.release()
    assert music._held is False


def test_hold_and_release_let_the_sound_effects_finish_first(settings, monkeypatch):
    """A sound effect that ended while the music was paused or resumed hung
    the game for good (the mixer's audio thread and the game each waited on
    the other's lock: a frozen dance-off). Hold and release now wait until no
    effect is playing."""
    pygame.mixer.init()
    music._playing = True
    busy = [True, True, False]
    order = []
    monkeypatch.setattr(pygame.mixer, 'get_busy', lambda: busy.pop(0) if busy else False)
    monkeypatch.setattr(pygame.mixer.music, 'pause', lambda: order.append(('pause', len(busy))))
    monkeypatch.setattr(pygame.mixer.music, 'unpause', lambda: order.append(('unpause', len(busy))))
    music.hold()
    assert order == [('pause', 0)]                    # only once nothing was playing
    busy[:] = [True, False]
    music.release()
    assert order[-1] == ('unpause', 0)


def test_f5_in_the_game_says_so(settings):
    pygame.init()
    from main import Game
    g = Game(pygame.display.set_mode((1, 1)), player_name='__music_f5__')
    before = music.is_on()
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F5, mod=0, unicode=''))
    assert music.is_on() is (not before)
    said = [str(e[0]) for e in g.msg_log.entries[-3:]]
    assert f"Music: {'On' if not before else 'Off'}. (F5 switches it.)" in said, said


def test_the_help_screen_and_the_release_build_know_it():
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert '("F5", "Music on / off"' in src
    spec = open(os.path.join(ROOT, 'PhilosophersQuest.spec'), encoding='utf-8').read()
    assert "('assets/music'," in spec and "'music'," in spec
