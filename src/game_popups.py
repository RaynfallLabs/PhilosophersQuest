"""PopupMixin: the popups that come from play, shown one at a time.

Brandon, 3.3.3 play: "you answer, the achievement or popup happens, you clear
it, and then you see the quiz resolve", and "just run UNIQUE popups in serial;
you get one first, then when you close it, it triggers the next". A monster
family's tier, circle or Loremaster popup, a trait unlocked, a Seeker
achievement, a boss's story popup and an escort's outcome card all wait in
one queue, open once play is calm, and follow one another as each is closed.
"""
from __future__ import annotations

from game_states import STATE_PLAYER, STATE_STORY_POPUP


# How long plain play must have lasted before a queued popup opens.
POPUP_CALM_SECONDS = 0.75


def _content_key(data: dict) -> tuple:
    """What makes two popups the same: their title, lines and code, and the
    achievements they show."""
    ach = tuple(str(a.get('id', a.get('name', ''))) for a in (data.get('achievements') or ()))
    return (str(data.get('title', '')), tuple(str(x) for x in (data.get('lines') or ())),
            str(data.get('code') or ''), ach)


class PopupMixin:
    """PopupMixin: the popups that come from play, shown one at a time.

    Brandon, 3.3.3 play: "you answer, the achievement or popup happens, you clear
    it, and then you see the quiz resolve." The popups that play raises (a
    monster family's tier, circle or Loremaster popup, a trait unlocked, a
    Seeker achievement, a boss's story popup, an escort's outcome card) all wait
    in one queue:

      * The first opens only when play is calm (`_play_is_calm`): plain play
        for POPUP_CALM_SECONDS since the last quiz, lore page or menu ended, and
        no full-screen or strike flourish still on screen. A quiz's result (the
        strike, the kill, the lore page a study opens) is always seen first.
      * Each is shown on its own, in its own look: nothing is appended to
        another popup (a second family popup used to join the first). Closing
        one opens the next at once; when the queue is empty, play goes back to
        wherever it was.
      * An identical popup (the same kind and the same content) already queued
        or showing is not queued again.

    The game's own popups (the opening, a save restored, the endings) are not
    from play and open at once, as before (Game._show_story_popup).
    """

    def _popup_queue_list(self) -> list:
        q = self.__dict__.get('_popup_queue')
        if not isinstance(q, list):
            q = self.__dict__['_popup_queue'] = []
        return q

    def _queue_popup(self, data: dict, kind: str, next_state: str = STATE_PLAYER) -> bool:
        """Queue a popup from play. False when an identical one is already
        queued or showing (it is not queued twice)."""
        key = (str(kind), _content_key(data))
        q = self._popup_queue_list()
        if any(e['key'] == key for e in q):
            return False
        if self.state == STATE_STORY_POPUP and self.__dict__.get('_popup_showing_key') == key:
            return False
        q.append({'key': key, 'kind': str(kind), 'data': data, 'next': next_state})
        return True

    def _popups_waiting(self) -> bool:
        return bool(self.__dict__.get('_popup_queue'))

    def _blocking_effect(self) -> bool:
        """A one-shot flourish still on screen (the strike finisher that
        shows a blow's result, a full-screen takeover, the identify orb)."""
        rt = getattr(self, 'effects_runtime', None)
        for h in (getattr(rt, 'handlers', None) or {}).values():
            try:
                if getattr(h, 'active', False):
                    return True
            except Exception:
                continue
        return False

    def _play_is_calm(self) -> bool:
        """Plain play for POPUP_CALM_SECONDS since the last quiz, lore page
        or menu ended, and no flourish still running."""
        return (self.state == STATE_PLAYER
                and float(self.__dict__.get('_calm_for', 0.0) or 0.0) >= POPUP_CALM_SECONDS
                and not self._blocking_effect())

    def _popup_tick(self, dt: float) -> None:
        """Every frame (Game.update): count the calm, and open the next
        queued popup once play is calm."""
        if self.state == STATE_PLAYER and not self._blocking_effect():
            self._calm_for = float(self.__dict__.get('_calm_for', 0.0) or 0.0) + max(0.0, float(dt))
        else:
            self._calm_for = 0.0
        if self._popups_waiting() and self._play_is_calm():
            self._open_next_popup(STATE_PLAYER)

    def _open_next_popup(self, back: str) -> bool:
        """Show the first queued popup; `back` is where play goes once the
        queue is empty."""
        q = self._popup_queue_list()
        if not q:
            return False
        e = q.pop(0)
        self.popup_data = e['data']
        self.popup_next_state = back if back != STATE_PLAYER else e.get('next', STATE_PLAYER)
        self.__dict__['_popup_showing_key'] = e['key']
        self.state = STATE_STORY_POPUP
        if e['kind'] == 'achievement':
            try:
                import sound_system
                sound_system.play('achievement')
            except Exception:
                pass
        return True

    def _close_story_popup(self) -> None:
        """The hero closes the popup: the next queued one opens at once (he is
        already reading popups); once none is left, play goes back to where
        it was, and the calm starts over."""
        self.__dict__.pop('_popup_showing_key', None)
        back = self.popup_next_state
        if self._open_next_popup(back):
            return
        self.state = back
        self._calm_for = 0.0
