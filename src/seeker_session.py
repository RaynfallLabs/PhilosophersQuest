"""The running Seeker: profile + achievement rules + this run's counters,
behind one call, ``emit(event, **fields)`` (PLAN_SEEKER_PROFILE_ACHIEVEMENTS
section 7).

No pygame. The title screen uses a Session with no run (the Konami code,
naming the Seeker); the Game keeps one per run (``SeekerMixin`` in
game_seeker.py). Both get back the ids of what was just won, so each can
show its own unlock card.
"""
from __future__ import annotations

import achievements
import seeker_codes
import seeker_profile


class Session:
    def __init__(self, profile: seeker_profile.Profile, book: achievements.Book | None = None,
                 run: achievements.RunTally | None = None, hero: str = ''):
        self.profile = profile
        self.book = book or achievements.load()
        self.run = run
        self.hero = hero

    @property
    def name(self) -> str:
        return self.profile.name

    def emit(self, event: str, **fields) -> list[str]:
        """Count one event; unlock and save at once whatever it earns.
        Returns the ids just won (empty for a read-only profile)."""
        if self.profile.readonly:
            return []
        try:
            won = self.book.apply(self.profile, self.run, event, **fields)
        except Exception:
            _log(f'achievement event {event!r} failed')
            return []
        for aid in won:
            self.profile.unlock(aid, hero=self.hero)
        if won:
            self.flush()
        return won + self._edited()

    def settle(self) -> list[str]:
        """Unlock what the counters already earn (a ladder tier a newer
        version added) and anything owed for an edited profile file."""
        if self.profile.readonly:
            return []
        won = []
        try:
            won = self.book.settled(self.profile, self.run)
        except Exception:
            _log('achievement settle failed')
        for aid in won:
            self.profile.unlock(aid, hero=self.hero)
        if won:
            self.flush()
        return won + self._edited()

    def _edited(self) -> list[str]:
        """The hidden one: the profile file was found edited (on load or on a
        write). Said nowhere; it simply unlocks."""
        if not self.profile.edited_found:
            return []
        self.profile.edited_found = False
        return self.emit('profile_edited')

    def flush(self) -> bool:
        ok = self.profile.flush()
        return ok

    def code(self, aid: str) -> str:
        a = self.book.by_id.get(aid)
        return seeker_codes.make_code(aid, a['code_word'], self.profile.name) if a else ''

    def entry(self, aid: str) -> dict | None:
        return self.book.by_id.get(aid)


def _log(msg: str):
    try:
        from game_log import log_error
        log_error(msg)
    except Exception:
        pass


def open_active(*, run=None, hero: str = '') -> Session | None:
    """A Session for the Seeker who is active, or None when nobody has
    chosen a Seeker yet (then nothing is recorded: the title screen asks)."""
    name = seeker_profile.active_name()
    if not name:
        return None
    try:
        return Session(seeker_profile.load(name), run=run, hero=hero)
    except Exception:
        _log(f'seeker profile {name!r} could not be opened')
        return None
