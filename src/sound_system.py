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
"""
from __future__ import annotations

import math
import array as _array

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
        snd = pygame.sndarray.make_sound(
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
        return pygame.sndarray.make_sound(arr)
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
        return pygame.sndarray.make_sound(arr)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init() -> bool:
    """
    Initialize the sound system.
    Returns True if sounds were synthesized successfully.
    """
    global _ENABLED, _sounds
    try:
        import pygame
        import numpy  # noqa -- just checking availability
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=_SAMPLE_RATE, size=-16, channels=1, buffer=512)
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
    }

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
    if not _ENABLED:
        return
    snd = _sounds.get(event)
    if snd is None:
        return
    try:
        snd.set_volume(max(0.0, min(1.0, volume)))
        snd.play()
    except Exception:
        pass
