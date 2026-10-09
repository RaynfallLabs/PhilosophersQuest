"""
sound_system.py -- Procedural sound effects for Philosopher's Quest.

All sounds are synthesized at runtime using numpy + pygame.sndarray.
No audio files required.  Call init() once at startup, then play(event_name).

Supported events:
  quiz_correct   -- rising ping (correct answer)
  quiz_wrong     -- low buzzer (wrong answer)
  player_hit     -- dull thud (player takes damage)
  monster_hit    -- sharp crack (monster takes damage)
  pickup         -- soft chime (pick up item)
  gold           -- bright jingle (collect gold)
  level_change   -- swoosh (change dungeon level)
  death          -- descending toll (player dies)
  trap           -- alarm burst (trap triggered)
  door           -- creak (open door)
  buy            -- coin clink (buy from merchant)
  spell_cast     -- arcane hum (cast a spell)
  equip          -- metallic click (equip gear)
  player_healed  -- gentle chime (player heals)
"""
from __future__ import annotations

import math
import os
import array as _array
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

_ENABLED: bool = False
_sounds: dict = {}

# Sample rate for all synthesized sounds
_SAMPLE_RATE = 22050
_CHANNELS    = 1   # mono


def _make_tone(
    freq: float,
    duration: float,
    volume: float = 0.3,
    wave: str = 'sine',
    attack: float = 0.01,
    decay: float = 0.1,
) -> 'pygame.mixer.Sound | None':
    """Generate a simple waveform as a pygame Sound object."""
    try:
        import pygame
        n = int(_SAMPLE_RATE * duration)
        buf = _array.array('h')
        peak = int(32767 * min(1.0, volume))
        for i in range(n):
            t = i / _SAMPLE_RATE
            # Envelope: linear attack then exponential decay
            if t < attack:
                env = t / attack
            else:
                env = math.exp(-(t - attack) / max(0.001, decay))
            # Waveform
            if wave == 'sine':
                sample = math.sin(2 * math.pi * freq * t)
            elif wave == 'square':
                sample = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            elif wave == 'sawtooth':
                sample = 2 * (t * freq - math.floor(t * freq + 0.5))
            elif wave == 'triangle':
                sample = 2 * abs(2 * (t * freq - math.floor(t * freq + 0.5))) - 1
            else:
                sample = math.sin(2 * math.pi * freq * t)
            buf.append(int(peak * env * sample))
        snd = _to_sound(
            __import__('numpy').array(buf, dtype='int16').reshape(-1, 1)
            if _CHANNELS == 1 else
            __import__('numpy').array(buf, dtype='int16')
        )
        return snd
    except Exception:
        return None


def _make_sweep(
    f_start: float,
    f_end: float,
    duration: float,
    volume: float = 0.3,
    attack: float = 0.02,
    decay: float = 0.15,
) -> 'pygame.mixer.Sound | None':
    """Frequency sweep (linear chirp)."""
    try:
        import pygame
        import numpy as np
        n = int(_SAMPLE_RATE * duration)
        buf = np.zeros(n, dtype='float64')
        for i in range(n):
            t = i / _SAMPLE_RATE
            freq = f_start + (f_end - f_start) * (t / duration)
            if t < attack:
                env = t / attack
            else:
                env = math.exp(-(t - attack) / max(0.001, decay))
            buf[i] = env * math.sin(2 * math.pi * freq * t)
        peak = int(32767 * min(1.0, volume))
        arr = (buf * peak).astype('int16').reshape(-1, 1)
        return _to_sound(arr)
    except Exception:
        return None


def _make_noise_burst(duration: float, volume: float = 0.2) -> 'pygame.mixer.Sound | None':
    """White noise burst."""
    try:
        import pygame
        import numpy as np
        n = int(_SAMPLE_RATE * duration)
        peak = int(32767 * volume)
        t_arr = np.arange(n) / _SAMPLE_RATE
        env = np.exp(-t_arr / max(0.001, duration * 0.4))
        noise = np.random.randint(-peak, peak + 1, n)
        arr = (noise * env).astype('int16').reshape(-1, 1)
        return _to_sound(arr)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _make_notes(notes, wave: str = 'sine', volume: float = 0.25, gap: float = 0.0):
    """A short tune: `notes` is [(frequency, seconds), ...] played one after
    another, each with its own quick fade. A frequency of 0 is a rest; a
    tuple of frequencies is a chord."""
    try:
        import numpy as np
        parts = []
        for freq, dur in notes:
            n = max(1, int(_SAMPLE_RATE * dur))
            t = np.arange(n) / _SAMPLE_RATE
            freqs = freq if isinstance(freq, (tuple, list)) else (freq,)
            wav = np.zeros(n)
            for fq in freqs:
                if not fq:
                    continue
                ph = 2 * np.pi * fq * t
                if wave == 'square':
                    wav += np.sign(np.sin(ph))
                elif wave == 'triangle':
                    wav += 2 * np.abs(2 * (t * fq - np.floor(t * fq + 0.5))) - 1
                else:
                    wav += np.sin(ph)
            wav /= max(1, len([x for x in freqs if x]))
            env = np.minimum(1.0, t / 0.008) * np.exp(-t / max(0.02, dur * 0.6))
            parts.append(wav * env)
            if gap:
                parts.append(np.zeros(int(_SAMPLE_RATE * gap)))
        buf = np.concatenate(parts) * int(32767 * min(1.0, volume))
        return _to_sound(buf.astype('int16'))
    except Exception:
        return None


# The pentatonic climb a combat chain sings: one step per link, so a long
# chain is heard as a rising run.
_CHAIN_SCALE = (392, 440, 523, 587, 659, 784, 880, 1047, 1175, 1319, 1568, 1760, 2093)


def play_chain(link: int) -> None:
    """The note for the Nth link of a chain (it tops out and stays there)."""
    play(f'chain_{max(1, min(len(_CHAIN_SCALE), int(link)))}')


# ---- on / off, remembered between sessions -------------------------------
_USER_ON: bool = True


def _settings_path() -> str:
    try:
        from paths import save_dir
        return os.path.join(save_dir(), 'settings.json')
    except Exception:
        return 'settings.json'


def _load_setting() -> None:
    global _USER_ON
    try:
        import json
        with open(_settings_path(), encoding='utf-8') as fh:
            data = json.load(fh)
        if isinstance(data, dict) and isinstance(data.get('sound'), bool):
            _USER_ON = data['sound']
    except Exception:
        pass


def is_on() -> bool:
    return bool(_USER_ON)


def set_on(on: bool) -> bool:
    """Turn sound on or off and remember the choice. Returns the new state."""
    global _USER_ON
    _USER_ON = bool(on)
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
        data['sound'] = _USER_ON
        with open(path + '.tmp', 'w', encoding='utf-8') as fh:
            json.dump(data, fh)
        os.replace(path + '.tmp', path)
    except Exception:
        pass
    if not _USER_ON:
        try:
            import pygame
            pygame.mixer.stop()
        except Exception:
            pass
    return _USER_ON


def toggle() -> bool:
    return set_on(not _USER_ON)


def _to_sound(samples):
    """A Sound from mono 16-bit samples, shaped for whatever mixer is open.

    The builders handed over an (n, 1) array. A mono mixer wants a flat one
    and a mixer with C channels wants (n, C), so every sound failed to build,
    the failure was swallowed, and the game has been silent."""
    import numpy as np
    import pygame
    flat = np.asarray(samples, dtype='int16').reshape(-1)
    info = pygame.mixer.get_init()
    channels = int(info[2]) if info else 1
    if channels <= 1:
        return pygame.sndarray.make_sound(flat)
    return pygame.sndarray.make_sound(np.ascontiguousarray(np.repeat(flat.reshape(-1, 1), channels, axis=1)))


def init() -> bool:
    """
    Initialize the sound system.
    Returns True if sounds were synthesized successfully.
    """
    global _ENABLED, _sounds
    try:
        import pygame
        import numpy  # noqa -- just checking availability
        # pygame.init() has already opened the mixer at the device's own
        # settings; the tones here are written for _SAMPLE_RATE, so reopen it
        # (at another rate they would play at the wrong pitch).
        _now = pygame.mixer.get_init()
        if not _now or _now[0] != _SAMPLE_RATE:
            try:
                pygame.mixer.quit()
                pygame.mixer.init(frequency=_SAMPLE_RATE, size=-16, channels=1, buffer=512)
            except Exception:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
    except Exception:
        _ENABLED = False
        return False

    defs = {
        'quiz_correct': lambda: _make_sweep(440, 880, 0.18, volume=0.28, decay=0.10),
        'quiz_wrong':   lambda: _make_sweep(300, 150, 0.25, volume=0.35, decay=0.15),
        'player_hit':   lambda: _make_noise_burst(0.12, volume=0.30),
        'monster_hit':  lambda: _make_tone(200, 0.10, wave='square', volume=0.20, decay=0.06),
        'pickup':       lambda: _make_tone(660, 0.12, wave='sine',   volume=0.20, decay=0.08),
        'gold':         lambda: _make_sweep(523, 784, 0.20, volume=0.25, decay=0.12),
        'level_change': lambda: _make_sweep(200, 600, 0.35, volume=0.30, decay=0.25),
        'death':        lambda: _make_sweep(400, 80,  0.60, volume=0.40, decay=0.50),
        'trap':         lambda: _make_noise_burst(0.20, volume=0.38),
        'door':         lambda: _make_tone(180, 0.15, wave='sawtooth', volume=0.22, decay=0.10),
        'buy':          lambda: _make_sweep(600, 800, 0.15, volume=0.22, decay=0.10),
        'spell_cast':   lambda: _make_sweep(300, 700, 0.28, volume=0.28, decay=0.20),
        'equip':        lambda: _make_tone(350, 0.10, wave='square', volume=0.18, decay=0.06),
        'player_healed': lambda: _make_sweep(440, 660, 0.22, volume=0.22, decay=0.15),
        # ---- added 2026-10-09 ----
        'miss':         lambda: _make_sweep(300, 170, 0.14, volume=0.20, decay=0.09),
        'strike_big':   lambda: _make_sweep(190, 55, 0.30, volume=0.42, decay=0.20),
        'kill':         lambda: _make_notes([(523, 0.07), (784, 0.14)], volume=0.24),
        'boss_kill':    lambda: _make_notes([(392, 0.12), (523, 0.12), (659, 0.12), ((523, 659, 784), 0.45)],
                                            wave='triangle', volume=0.34),
        'dodge':        lambda: _make_sweep(900, 1500, 0.08, volume=0.14, decay=0.05),
        'stat_up':      lambda: _make_notes([(523, 0.08), (659, 0.08), (784, 0.08), (1047, 0.22)], volume=0.26),
        'trait':        lambda: _make_notes([(659, 0.10), (784, 0.10), (988, 0.10), ((784, 988, 1319), 0.40)],
                                            wave='triangle', volume=0.32),
        'chest_open':   lambda: _make_notes([(220, 0.06), (330, 0.06), (440, 0.16)], wave='square', volume=0.16),
        'lock_fail':    lambda: _make_notes([(150, 0.10), (120, 0.16)], wave='square', volume=0.16),
        'eat':          lambda: _make_notes([(190, 0.05), (150, 0.05), (175, 0.06)], wave='triangle', volume=0.24, gap=0.03),
        'drink':        lambda: _make_notes([(430, 0.06), (360, 0.06), (300, 0.10)], volume=0.22, gap=0.02),
        'cook':         lambda: _make_noise_burst(0.50, volume=0.10),
        'harvest':      lambda: _make_notes([(140, 0.05), (110, 0.09)], wave='square', volume=0.18),
        'identify':     lambda: _make_notes([(880, 0.07), (1175, 0.07), (1568, 0.22)], volume=0.22),
        'scroll':       lambda: _make_sweep(700, 1150, 0.22, volume=0.20, decay=0.16),
        'zap':          lambda: _make_sweep(1500, 280, 0.20, volume=0.26, decay=0.14),
        'pray':         lambda: _make_notes([((262, 330, 392), 0.70)], volume=0.24),
        'pet':          lambda: _make_notes([(988, 0.06), (1319, 0.12)], volume=0.20),
        'secret':       lambda: _make_notes([(659, 0.08), (622, 0.08), (659, 0.08), (988, 0.24)], volume=0.24),
        'dread':        lambda: _make_notes([((65, 69), 0.90)], wave='triangle', volume=0.45),
        'boon':         lambda: _make_notes([((392, 494, 587, 784), 0.80)], wave='triangle', volume=0.30),
        'victory':      lambda: _make_notes([(523, 0.14), (523, 0.07), (523, 0.07), (659, 0.14), (784, 0.14),
                                             (659, 0.10), ((523, 659, 784, 1047), 0.70)], wave='triangle', volume=0.36),
        'tick':         lambda: _make_notes([(1000, 0.035)], wave='square', volume=0.12),
        'time_up':      lambda: _make_sweep(520, 190, 0.32, volume=0.30, decay=0.22),
        'toggle':       lambda: _make_notes([(660, 0.05), (880, 0.08)], volume=0.20),
    }
    for _i, _hz in enumerate(_CHAIN_SCALE, start=1):
        defs[f'chain_{_i}'] = (lambda hz=_hz: _make_notes([(hz, 0.11)], wave='triangle', volume=0.26))
    _load_setting()

    ok = 0
    for name, factory in defs.items():
        try:
            snd = factory()
            if snd is not None:
                _sounds[name] = snd
                ok += 1
        except Exception:
            pass

    _ENABLED = ok > 0
    return _ENABLED


def play(event: str, volume: float = 1.0) -> None:
    """Play a named sound event. Silently no-ops if not available."""
    if not _ENABLED or not _USER_ON:
        return
    snd = _sounds.get(event)
    if snd is None:
        return
    try:
        snd.set_volume(max(0.0, min(1.0, volume)))
        snd.play()
    except Exception:
        pass
