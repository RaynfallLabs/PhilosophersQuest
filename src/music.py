"""The soundtrack: Brandon's own "PQ Main Theme" (2026-11-14).

One track, looped with no gap, under everything from the title screen on.
F5 turns it on or off, on the title screen and in the game; the choice is
remembered in settings.json beside the sound setting (sound_system), and the
two are separate: music and sound effects can each be on or off.

The mixer is opened by sound_system.init() (mono, at its sample rate, so its
tones play at the right pitch); start() calls it first so the game's own
init later finds the mixer already right and never reopens it under the
music. Anything that needs quiet for a moment (a rhythm game's beat) calls
hold() and release().

A song a dish plays (songs.py: Brandon's own, as A Man Before a King) takes
the stream for as long as it lasts: play_song() plays it once, from where it
should be, and end_song() hands the stream back to the soundtrack. While a
song holds the stream, start() leaves it alone.

Pure enough to test headless: every pygame call is guarded, and with no
audio device it does nothing.
"""
from __future__ import annotations

import os

TRACK = ('assets', 'music', 'pq_main_theme.ogg')
VOLUME = 0.45            # under the quiz sounds, which play at full volume
SONG_VOLUME = 0.6        # a dish's song is the moment itself: a little louder
FADE_MS = 400

_on: bool | None = None  # read from settings.json the first time it is asked
_playing = False
_held = False
_song: str | None = None  # the path of a dish's song while it holds the stream


def _path() -> str:
    from paths import data_path
    return data_path(*TRACK)


def _settings_path() -> str:
    import sound_system
    return sound_system._settings_path()


def is_on() -> bool:
    """Is the music wanted? (Default on; settings.json `music`.)"""
    global _on
    if _on is None:
        _on = True
        try:
            import json
            with open(_settings_path(), encoding='utf-8') as fh:
                data = json.load(fh)
            if isinstance(data, dict) and isinstance(data.get('music'), bool):
                _on = data['music']
        except Exception:
            pass
    return bool(_on)


def _save(on: bool) -> None:
    try:
        import json
        path = _settings_path()
        data = {}
        try:
            with open(path, encoding='utf-8') as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
        data['music'] = bool(on)
        with open(path + '.tmp', 'w', encoding='utf-8') as fh:
            json.dump(data, fh)
        os.replace(path + '.tmp', path)
    except Exception:
        pass


def start() -> bool:
    """Start the soundtrack looping, if it is wanted and there is a mixer.
    Safe to call again: it only (re)starts what is not playing. Returns True
    when the music is playing."""
    global _playing
    if not is_on() or _held or _song is not None:
        return False
    try:
        import pygame
        import sound_system
        sound_system.init()                 # the mixer at the tones' rate first
        if not pygame.mixer.get_init():
            return False
        if _playing and pygame.mixer.music.get_busy():
            return True
        if not os.path.exists(_path()):
            return False
        _effects_done()                     # never touch the music mid-effect (see _effects_done)
        pygame.mixer.music.load(_path())
        pygame.mixer.music.set_volume(VOLUME)
        pygame.mixer.music.play(loops=-1, fade_ms=FADE_MS)
        _playing = True
        return True
    except Exception:
        _playing = False
        return False


def stop() -> None:
    global _playing
    try:
        import pygame
        if pygame.mixer.get_init():
            _effects_done()                 # F5 mid-effect could hang the game (see _effects_done)
            pygame.mixer.music.fadeout(FADE_MS)
    except Exception:
        pass
    _playing = False


def set_on(on: bool) -> bool:
    """Turn the music on or off and remember it. Returns the new state."""
    global _on
    _on = bool(on)
    _save(_on)
    if _on:
        start()
    else:
        stop()
    return _on


def toggle() -> bool:
    """F5: switch the music. Returns the new state."""
    return set_on(not is_on())


def _effects_done(limit_s: float = 1.0) -> None:
    """Let the sound effects still playing finish (a second at most) before
    the music is paused or resumed. A sound effect that ends while the music
    is paused or resumed can hang the game for good: the mixer's audio thread
    takes Python's lock to let go of the finished sound while it holds the
    audio lock, and pause / unpause wait on the audio lock while holding
    Python's (seen as a frozen dance-off: tests/test_stray_kids_journey.py).
    With no effect playing none can end; the short sleep after lets one that
    ended just before the check finish its hand-off."""
    import time
    import pygame
    end = time.monotonic() + float(limit_s)
    while pygame.mixer.get_busy() and time.monotonic() < end:
        time.sleep(0.005)
    time.sleep(0.01)


def hold() -> None:
    """Quiet the music for a moment (a rhythm game's beat); release() after.
    A dish's song is paused too, and its clock waits (game_songs)."""
    global _held
    _held = True
    try:
        import pygame
        if pygame.mixer.get_init() and (_playing or _song is not None):
            _effects_done()
            pygame.mixer.music.pause()
    except Exception:
        pass


def release() -> None:
    global _held
    _held = False
    if _song is not None:
        # A dish's song plays whatever F5 says (its own mute is game_songs').
        try:
            import pygame
            if pygame.mixer.get_init():
                _effects_done()
                pygame.mixer.music.unpause()
        except Exception:
            pass
        return
    if not is_on():
        return
    try:
        import pygame
        if pygame.mixer.get_init() and _playing:
            _effects_done()
            pygame.mixer.music.unpause()
            return
    except Exception:
        pass
    start()


def is_held() -> bool:
    return bool(_held)


# ---------------------------------------------------------------------------
# A dish's song (songs.py; game_songs.SongsMixin drives it)
# ---------------------------------------------------------------------------

def play_song(path: str, at: float = 0.0) -> bool:
    """The soundtrack steps aside and ``path`` plays once, from ``at``
    seconds in. The song holds the stream until end_song(), even once its
    audio has run out. Returns True when it is playing."""
    global _song, _playing
    _song = str(path)
    _playing = False                        # the theme is no longer in the stream
    try:
        import pygame
        import sound_system
        sound_system.init()
        if not pygame.mixer.get_init() or not os.path.exists(_song):
            return False
        _effects_done()
        pygame.mixer.music.load(_song)
        pygame.mixer.music.set_volume(SONG_VOLUME)
        pygame.mixer.music.play(loops=0, start=max(0.0, float(at)), fade_ms=FADE_MS)
        if _held:
            pygame.mixer.music.pause()
        return True
    except Exception:
        return False


def mute_song() -> None:
    """F5 mid-song: its audio stops; the song keeps the stream (and its power
    its clock) until it is over."""
    try:
        import pygame
        if pygame.mixer.get_init() and _song is not None:
            _effects_done()
            pygame.mixer.music.fadeout(FADE_MS)
    except Exception:
        pass


def song_playing() -> bool:
    """Is a dish's song holding the stream?"""
    return _song is not None


def song_busy() -> bool:
    """Is a dish's song audible (or paused by hold()) right now?"""
    if _song is None:
        return False
    try:
        import pygame
        return bool(pygame.mixer.get_init()) and bool(pygame.mixer.music.get_busy() or _held)
    except Exception:
        return False


def end_song() -> None:
    """The song is over: the stream goes back to the soundtrack (if music is
    on). Safe to call with no song playing."""
    global _song
    if _song is None:
        return
    _song = None
    try:
        import pygame
        if pygame.mixer.get_init():
            _effects_done()
            pygame.mixer.music.fadeout(FADE_MS)
    except Exception:
        pass
    start()
