"""SeekerMixin: the Game's side of the Seeker profile and its achievements
(PLAN_SEEKER_PROFILE_ACHIEVEMENTS_2026_10_25.md section 7).

The game tells the Seeker what happened with one line at the place it
happens, ``self._seeker_event('kill', monster=..., ...)``. What each event
counts towards is data (data/achievements.json); the rules are
achievements.py, the file is seeker_profile.py, and seeker_session.py ties
them together.

What the hero earns is shown when play is calm again, never during a quiz
(Brandon's D7): ``_seeker_tick`` runs every frame from ``update`` and queues
it with the other popups from play (game_popups.PopupMixin: one at a time, once
play is calm). A run of
the Dad / god build or the QA build records nothing (D4), and nothing is
recorded until a Seeker has been chosen on the title screen (F4).
"""
from __future__ import annotations

import achievements
import seeker_codes
import seeker_session
from game_states import STATE_PLAYER, STATE_STORY_POPUP

_PER_POPUP = 3          # unlocks shown on one popup page


def _version_tuple(v: str) -> tuple:
    out = []
    for part in str(v or '').split('.'):
        digits = ''.join(ch for ch in part if ch.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out) or (0,)


def older_version(saved: str, current: str | None = None) -> bool:
    """Was a save written by an older version of the game than this one? A
    save with no version ('') is from before 3.5, which kept none."""
    if current is None:
        from layout import VERSION as current
    if not saved:
        return True
    return _version_tuple(saved) < _version_tuple(current)


class SeekerMixin:

    def _seeker_init(self, *, new_run: bool):
        """Open the active Seeker for this run. Called once a new hero is
        made and once a save has been loaded."""
        self._seeker_pending = []
        build = getattr(self, 'secret_build', None) or {}
        self._seeker_off = bool(build.get('_joke') or build.get('_qa_tools'))
        run = achievements.RunTally(getattr(self, '_seeker_run', None))
        self._seeker_run = run.data            # saved with the run (save_system)
        self._seeker = None
        import counters
        import deeds
        import monster
        import pet_system
        import topic_cards
        deeds.ON_RECORD = None
        monster.DAMAGE_OBSERVER = None
        pet_system.ON_GROWTH = None
        topic_cards.ON_READ = None
        counters.ON_COUNTER = None
        if self._seeker_off:
            return
        self._seeker = seeker_session.open_active(run=run, hero=getattr(self, 'player_name', ''))
        if self._seeker is None:
            return
        # Every deed written this run reaches the Seeker (oaths kept, people
        # saved, the Black Knight's draw...): achievements match on its id.
        deeds.ON_RECORD = self._seeker_deed
        monster.DAMAGE_OBSERVER = self._seeker_damage
        pet_system.ON_GROWTH = self._seeker_pet_growth
        topic_cards.ON_READ = (lambda subject, topic: self._seeker_event(
            'topic_read', subject=subject, topic=f'{subject}:{topic}'))
        # A named counter at work (counters.py): the technique and the creature.
        counters.ON_COUNTER = (lambda tid, src: self._seeker_event(
            'counter', technique=tid, monster=getattr(src, 'kind', None),
            family=getattr(src, 'family', None)))
        prof = self._seeker.profile
        from save_system import run_id_of
        if new_run:
            # The heroes this Seeker has been (for meeting one's own ghost).
            prof.include('heroes', seeker_codes.normalise_name(self.player_name))
            self._seeker_event('run_start', hero=self.player_name, build=self._seeker_build_key())
        else:
            if run_id_of(self) in prof.members('ended_runs'):
                # A save of a run that already ended, copied back by hand.
                self._seeker_event('save_restored', ended=True)
            saved = getattr(self, '_saved_version', None)
            if saved is not None and older_version(saved):
                # A journey begun in an older version of the game, carried on
                # in this one (Rip Van Winkle).
                self._seeker_event('save_older', version=saved or 'unknown')
        self._seeker_take(self._seeker.settle())

    def _seeker_damage(self, mon, amount: int, dealt: int):
        self._seeker_event('damage', amount=int(amount), dealt=int(dealt),
                           by=getattr(self, '_damage_by', 'hero'))

    def _seeker_pet_growth(self, pet, what: str, value: int):
        line = getattr(pet, 'species_key', None)
        if what == 'evolved':
            self._seeker_event('pet_evolved', pet=line, line=line, stage=int(value))
        else:
            self._seeker_event('pet_level', pet=line, line=line, level=int(value))

    def _seeker_deed(self, deed: dict):
        did = str(deed.get('id', ''))
        self._seeker_event('deed', kind=did.split('.', 1)[0], id=did,
                           late=bool((deed.get('payload') or {}).get('late')))

    def _seeker_build_key(self) -> str | None:
        """The Secret Build's name as typed ("fianna"), or None."""
        build = getattr(self, 'secret_build', None)
        if not build:
            return None
        try:
            from welcome_screen import SECRET_BUILDS
            return next((k for k, v in SECRET_BUILDS.items() if v is build or v == build), None)
        except Exception:
            return None

    def _seeker_event(self, event: str, **fields) -> list[str]:
        """Tell the Seeker something happened. Returns the ids just won."""
        s = getattr(self, '_seeker', None)
        if s is None:
            self._qa_achievement_preview(event, fields)
            return []
        won = s.emit(event, **fields)
        self._seeker_take(won)
        return won

    def _qa_achievement_preview(self, event: str, fields: dict):
        """The Titivillus QA build records nothing (D4), so a test run never
        saw an achievement. There, an achievement one event earns (no
        counters) opens its popup as a preview, once a run, marked as such
        and with no code: nothing is written to any profile."""
        if not getattr(getattr(self, 'player', None), 'qa_tools', False):
            return
        try:
            book = achievements.load()
        except Exception:
            return
        shown = self.__dict__.setdefault('_qa_previewed', set())
        entries = []
        for a in book.entries:
            t = a.get('trigger') or {}
            if (a['id'] in shown or t.get('event') != event
                    or not achievements._matches(t.get('where'), fields)):
                continue
            shown.add(a['id'])
            entries.append({'id': a['id'], 'name': a['name'], 'text': a['unlocked_text'],
                            'code': 'QA PREVIEW', 'rarity': a['rarity'], 'art': a['art']})
        if not entries:
            return
        for e in entries:
            self.add_message(f"[QA] ACHIEVEMENT (preview, not recorded): {e['name']}", 'loot')
        try:
            import seeker_screen
            seeker_screen.prebuild_card(entries)
        except Exception:
            pass
        from fantasy_ui import FP
        self._queue_popup({
            'title': 'ACHIEVEMENT UNLOCKED' if len(entries) == 1 else 'ACHIEVEMENTS UNLOCKED',
            'accent': FP.ACHIEVEMENT,
            'lines': ['QA preview: the QA build records nothing.'],
            'code': None,
            'achievements': entries,
        }, 'achievement')

    def _seeker_take(self, won):
        """Log each new achievement and queue its popup."""
        s = getattr(self, '_seeker', None)
        if not won or s is None:
            return
        held = self.__dict__.get('_seeker_held_lines')
        for aid in won:
            a = s.entry(aid)
            if a is None:
                continue
            line = f"ACHIEVEMENT: {a['name']}. Reward Code: {s.code(aid)}"
            if held is not None:
                held.append(line)           # said after the run's last line (_seeker_tick)
            else:
                self.add_message(line, 'loot')
            self._seeker_pending.append(aid)

    def _seeker_tick(self):
        """Every frame: what was won joins the popups from play, at most
        _PER_POPUP to a popup. It opens in its turn, once play is calm (never
        mid-quiz, never over a menu or another popup: PopupMixin). What the
        end of a run earned is said here too, the frame after: after "You
        have died!", which every death says once the run is over."""
        held = self.__dict__.pop('_seeker_held_lines', None)
        for line in held or ():
            self.add_message(line, 'loot')
        pending = getattr(self, '_seeker_pending', None)
        while pending:
            ids, pending = pending[:_PER_POPUP], pending[_PER_POPUP:]
            self._seeker_pending = pending
            self._show_achievement_popup(ids)

    def _show_achievement_popup(self, ids):
        """The unlock moment, in the story popup's chrome, queued with the
        other popups from play. ``achievements`` carries what game_render
        draws: each badge, name, text and code."""
        s = getattr(self, '_seeker', None)
        if s is None:
            return
        entries = []
        for aid in ids:
            a = s.entry(aid)
            if a:
                entries.append({'id': aid, 'name': a['name'], 'text': a['unlocked_text'],
                                'code': s.code(aid), 'rarity': a['rarity'], 'art': a['art']})
        if not entries:
            return
        try:
            import seeker_screen
            seeker_screen.prebuild_card(entries)    # badges built now, not on a frame
        except Exception:
            pass
        from fantasy_ui import FP
        # (Its sound plays when it opens: PopupMixin._open_next_popup.)
        self._queue_popup({
            'title': 'ACHIEVEMENT UNLOCKED' if len(entries) == 1 else 'ACHIEVEMENTS UNLOCKED',
            'accent': FP.ACHIEVEMENT,
            'lines': ['Show this code to Dad.' if len(entries) == 1 else 'Show these codes to Dad.'],
            'code': None,
            'achievements': entries,
        }, 'achievement')

    def _seeker_unshown(self) -> list:
        """The achievements won this run whose popup never opened: still
        pending, or waiting in the popup queue (PopupMixin opens nothing
        over the death screen, so what a fall earns waits there). main()
        hands them to the title screen, which shows their cards. A popup
        that did open (the Stone home: the ending's popup, then the queue)
        is not here."""
        out = [str(a) for a in (self.__dict__.get('_seeker_pending') or ())]
        for e in self.__dict__.get('_popup_queue') or ():
            if not isinstance(e, dict) or e.get('kind') != 'achievement':
                continue
            for a in (e.get('data') or {}).get('achievements') or ():
                aid = str((a or {}).get('id') or '')
                if aid and aid not in out:
                    out.append(aid)
        return out

    def _seeker_code(self, aid: str) -> str | None:
        """The Seeker's code for an achievement already won, else None."""
        s = getattr(self, '_seeker', None)
        if s is None or not s.profile.is_unlocked(aid):
            return None
        return s.code(aid) or None

    def _seeker_flush(self):
        """Write the Seeker's counters (floor changes, run end, quit, crash)."""
        s = getattr(self, '_seeker', None)
        if s is not None:
            try:
                s.flush()
            except Exception:
                pass

    def _seeker_run_end(self, victory: bool):
        """The run is over: count it, remember it ended (a copied-back save
        of it is then noticed), and write the profile."""
        s = getattr(self, '_seeker', None)
        if s is None or self.__dict__.get('_seeker_ended'):
            return
        # A run ends once: a second game-over (a trap's death, then the
        # starvation tick of the same action) must not count another fall.
        self._seeker_ended = True
        reason = 'victory' if victory else getattr(self, 'defeat_reason', 'died')
        try:
            grade = self._get_grade(self._calc_score())[0]
        except Exception:
            grade = ''
        from boss_levels import COW_LEVEL
        from save_system import run_id_of
        s.profile.include('ended_runs', run_id_of(self))
        # Every death calls _on_game_over (and so this) before it says "You
        # have died!": what the fall earned waits for the next frame, so it
        # is read after it (bug bash 3.5.1 E).
        self.__dict__.setdefault('_seeker_held_lines', [])
        self._seeker_event('run_end', reason=reason, victory=bool(victory),
                           floor=int(getattr(self, 'dungeon_level', 0) or 0), grade=grade,
                           build=self._seeker_build_key(),
                           killer=getattr(self, '_killed_by', None),
                           cow_level=getattr(self, 'dungeon_level', 0) == COW_LEVEL)
        self._seeker_flush()
