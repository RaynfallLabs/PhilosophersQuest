"""SongsMixin: the Game's side of a dish's song (songs.py, music.py).

Every frame (``_song_frame`` from ``update``): the song's real-time clock
runs, its audio is started where it should be (after the dish, after F5
unmutes it, after a save made mid-song is loaded), and when it is over the
closing lines are said and the soundtrack comes back.

The clock counts real seconds while the song plays. It waits while the
music is held (a dance's beat), and keeps running while F5 has the song
muted: the power lasts the song's length either way.
"""
from __future__ import annotations

import songs

# The most one frame may take off the song's clock (a frame stalled by a
# window drag or a slow load is not the song played).
_MAX_STEP = 0.5


class SongsMixin:

    def _song_frame(self, dt: float):
        import music
        player = getattr(self, 'player', None)
        st = songs.active(player) if player is not None else None
        if st is None:
            if self.__dict__.get('_song_audio') is not None or music.song_playing():
                self._song_audio = None
                music.end_song()
            return
        if player.is_dead():
            # A fall ends the song with the run; what it said no longer matters.
            songs.end(player)
            self._song_audio = None
            music.end_song()
            return
        # The audio: started once per song, again only after F5 unmutes it or
        # a save is loaded mid-song (a new Game has no _song_audio).
        if not st.get('muted') and self.__dict__.get('_song_audio') != st['id']:
            self._song_audio = st['id']
            path = songs.track_path(st['id'])
            if path:
                music.play_song(path, at=songs.elapsed(player))
        if music.is_held():
            return
        step = max(0.0, min(float(dt or 0.0), _MAX_STEP))
        closing = songs.tick(player, step)
        if closing:
            self._song_audio = None
            music.end_song()
            for line in closing:
                self.add_message(line, 'info')

    def _song_f5(self) -> bool | None:
        """F5 while a song plays: mute it or bring it back, and set the music
        to match (the soundtrack follows when the song is over). Returns the
        music's new state, or None when no song is playing (F5 as usual)."""
        import music
        st = songs.active(getattr(self, 'player', None))
        if st is None:
            return None
        st['muted'] = not st.get('muted')
        music.set_on(not st['muted'])
        if st['muted']:
            music.mute_song()
            self._song_audio = None          # unmuted, it starts again where it should be
        return not st['muted']
