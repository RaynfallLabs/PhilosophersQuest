"""Songs the hero can play: Brandon's own, as A Man Before a King (3.5.2).

A song plays once, in place of the soundtrack, and its power lasts exactly
as long as the song does, timed in real seconds, not turns. Then the
soundtrack comes back and the power is gone. Two play now:

* "Caviar and Tater Tots", from a dish: caviar and tater tots are rare
  plain foods, good to eat as they are, and cooked together (a recipe's
  ``song``) they make the dish that plays it. While it plays every blow and
  spell on the hero does ``damage_taken`` of its damage. Robyn starts with
  one of each.
* "So Then I Was Like...", from a power: a hundred maths answers right in a
  row in one run earns the power Math is Cool (quirk_system), ready every
  ``cooldown`` turns. While it plays every right answer in a fight counts as
  ``chain_mult`` links (combat.effective_chain).

One song plays at a time: a power is not used while another song plays
(game_menus), and the dish is not cooked then (the cook menu).

The song's state lives on the hero (``player.song_playing``: which song,
seconds left, muted by F5 or not), so a save made mid-song carries on where
it left off. The Game's side (the audio, the clock each frame, F5) is
game_songs.SongsMixin; the music stream is music.py.

Pure module: no pygame, no Game import.
"""
from __future__ import annotations

import json

from paths import data_path

_cache: dict = {}


def data() -> dict:
    """data/songs.json, loaded once."""
    if 'songs' not in _cache:
        try:
            with open(data_path('data', 'songs.json'), encoding='utf-8') as f:
                _cache['songs'] = json.load(f)
        except (OSError, ValueError):
            _cache['songs'] = {}
    return _cache['songs']


def song(sid: str | None) -> dict | None:
    if not sid:
        return None
    return (data().get('songs') or {}).get(str(sid))


def track_path(sid: str) -> str | None:
    s = song(sid)
    if not s:
        return None
    return data_path(*s.get('track') or ())


def length(sid: str) -> float:
    s = song(sid) or {}
    return float(s.get('seconds', 0) or 0)


def lines(sid: str, key: str) -> list:
    s = song(sid) or {}
    return [str(x) for x in ((s.get('lines') or {}).get(key) or ())]


# ---------------------------------------------------------------------------
# The hero's song
# ---------------------------------------------------------------------------

def active(player) -> dict | None:
    """The song playing for this hero ({'id', 'left', 'muted'}), or None."""
    st = getattr(player, 'song_playing', None)
    if not isinstance(st, dict) or not song(st.get('id')):
        return None
    if float(st.get('left', 0) or 0) <= 0:
        return None
    return st


def begin(player, sid: str) -> list:
    """The dish is eaten: the song starts from the top (again, if it was
    already playing). Returns its opening lines."""
    if not song(sid):
        return []
    player.song_playing = {'id': str(sid), 'left': length(sid), 'muted': False}
    return lines(sid, 'start')


def wait_line(player) -> str:
    """Said when a second song would start over one still playing."""
    st = active(player)
    title = (song(st['id']) or {}).get('title', 'The song') if st else 'The song'
    return f'"{title}" is still playing. One song at a time: wait for it to end.'


def elapsed(player) -> float:
    """Seconds of the song already played (where the audio picks up)."""
    st = active(player)
    if st is None:
        return 0.0
    return max(0.0, length(st['id']) - float(st['left']))


def tick(player, seconds: float) -> list:
    """``seconds`` of real time with the song playing. Returns its closing
    lines on the tick it ends, else []."""
    st = active(player)
    if st is None:
        return []
    st['left'] = float(st['left']) - max(0.0, float(seconds))
    if st['left'] > 0:
        return []
    return end(player)


def end(player) -> list:
    """The song is over (or cut short): the power goes with it."""
    st = getattr(player, 'song_playing', None)
    player.song_playing = None
    if not isinstance(st, dict):
        return []
    return lines(st.get('id'), 'end')


def chain_mult(player) -> int:
    """How many links each right answer of a fight's maths chain counts for
    while a song plays (1 with none)."""
    st = active(player)
    if st is None:
        return 1
    return max(1, int((song(st['id']) or {}).get('chain_mult', 1) or 1))


def power_of(sid: str) -> dict:
    """The power that plays a song: {'id', 'streak', 'cooldown'} ({} for a
    dish's song)."""
    return dict((song(sid) or {}).get('power') or {})


def song_for_power(pid: str) -> str | None:
    """The song a power plays, or None."""
    for sid, s in (data().get('songs') or {}).items():
        if (s.get('power') or {}).get('id') == pid:
            return sid
    return None


def damage_mult(player) -> float:
    """What a blow or spell on the hero is multiplied by while a song plays
    (1.0 with none)."""
    st = active(player)
    if st is None:
        return 1.0
    return float((song(st['id']) or {}).get('damage_taken', 1.0) or 1.0)


def clock_text(seconds: float) -> str:
    s = max(0, int(round(float(seconds))))
    return f"{s // 60}:{s % 60:02d}"


def effect_label(player) -> str | None:
    """The sidebar's and the character sheet's row: "Everything's Right
    2:10", or None with no song playing."""
    st = active(player)
    if st is None:
        return None
    name = (song(st['id']) or {}).get('label') or 'Song'
    return f"{name} {clock_text(st['left'])}"
