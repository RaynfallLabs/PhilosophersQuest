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

Pure enough to test headless: every pygame call is guarded, and with no
audio device it does nothing.
"""
from __future__ import annotations

import os

TRACK = ('assets', 'music', 'pq_main_theme.ogg')
VOLUME = 0.45            # under the quiz sounds, which play at full volume
FADE_MS = 400

_on: bool | None = None  # read from settings.json the first time it is asked
_playing = False
_held = False


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
    if not is_on() or _held:
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


def hold() -> None:
    """Quiet the music for a moment (a rhythm game's beat); release() after."""
    global _held
    _held = True
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.pause()
    except Exception:
        pass


def release() -> None:
    global _held
    _held = False
    if not is_on():
        return
    try:
        import pygame
        if pygame.mixer.get_init() and _playing:
            pygame.mixer.music.unpause()
            return
    except Exception:
        pass
    start()
