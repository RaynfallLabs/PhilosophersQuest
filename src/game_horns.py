"""HornsMixin: the Game's side of the four horns of legend (horns.py,
data/horns.json).

* V menu: a carried horn not yet sounded is a power (``_horn_power_rows``,
  read by game_menus._open_power_menu); choosing it (``_activate_horn``) spends
  it at once (a failed quiz still spends it, like a hero special) and opens its
  HISTORY escalator chain.
* The chain sets who answers (horns.allies_for). They come at once and stand
  beside the hero as horns.CalledAlly helpers in ``self.pets``, or, for the
  Olifant, after its delay (``player.horn_host_due``, counted down by
  ``_horn_tick`` every world turn: the host rides from thirty leagues off).
* Each ally's stay is ticked in _do_pet_turns (game_combat); when the hero
  leaves the floor they called to, they go (``_horn_allies_left_behind``, from
  _change_level).
* Titivillus QA build: Shift+H puts the hero at each horn's path in turn, then
  every horn in the pack, ready (``_qa_horns``).

State lives on the player, so it is saved with him: ``horns_sounded`` (a set)
and ``horn_host_due`` ({horn: [turns left, chain]}). Old saves have neither and
read as nothing sounded (getattr defaults in horns.py).
"""
from __future__ import annotations

import horns
from game_states import STATE_PLAYER, STATE_QUIZ

# The Titivillus QA build's Shift+H: each path's encounter, in turn.
QA_PATHS = ('flv_robin_hood_bridge', 'flv_sleepers_under_the_hill', 'flv_heimdalls_watch',
            'flv_rolands_horn')


class HornsMixin:
    # ------------------------------------------------------------------
    # The power
    # ------------------------------------------------------------------

    def _horn_power_rows(self) -> list:
        """The V menu's rows for the horns carried and not yet sounded."""
        return horns.menu_rows(self.player)

    def _activate_horn(self, pid: str) -> bool:
        """Sound a horn: its use is spent now, then its quiz. Always True (the
        quiz's end advances the turn; a refusal spends none)."""
        pl = self.player
        hid = horns.horn_for_power(pid)
        if hid is None or hid not in horns.carried(pl.inventory):
            self.add_message("You have no horn to blow.", 'warning')
            return True
        h = horns.horn(hid)
        if not horns.ready(pl, hid):
            self.add_message(f"{horns.name(hid)} has sounded once already. It will not "
                             f"sound again for you.", 'warning')
            return True
        horns.spend(pl, hid)
        self.add_message(horns.line(hid, 'raise'), 'info')
        q = h.get('quiz') or {}
        subject = q.get('subject', 'history')
        self.quiz_title = f"{h.get('title', hid.upper())}  --  {subject.upper()}"
        self.state = STATE_QUIZ
        self.quiz_engine.start_quiz(
            mode=q.get('mode', 'escalator_chain'),
            subject=subject,
            tier=int(q.get('tier', 1)),
            callback=lambda result, _hid=hid: self._horn_quiz_done(_hid, result),
            max_chain=int(q.get('max_chain', 5)),
            wisdom=pl.WIS,
            timer_modifier=pl.get_quiz_timer_modifier(),
            extra_seconds=pl.get_quiz_extra_seconds(subject),
            base_seconds=pl.get_quiz_timer(subject),
        )
        return True

    def _horn_quiz_done(self, hid: str, result) -> None:
        """The chain decides who answers; none at all, and the horn is spent
        for nothing. The Olifant's host sets out now and arrives later."""
        pl = self.player
        self.state = STATE_PLAYER
        chain = int(getattr(result, 'score', 0) or 0)
        kinds = horns.allies_for(hid, chain)
        if not kinds:
            self.add_message(horns.line(hid, 'fail'), 'warning')
            self._chron('deed', horns.chronicle_line(hid, failed=True))
            self._horn_close_thread(hid, horns.chronicle_line(hid, failed=True))
            self._advance_turn()
            return
        wait = horns.delay(hid)
        if wait > 0:
            due = dict(horns.due(pl))
            due[hid] = [wait, chain]
            pl.horn_host_due = due
            self.add_message(horns.line(hid, 'far'), 'info')
            self._advance_turn()
            return
        if not self._horn_allies_arrive(hid, kinds):
            # Nowhere for anyone to stand: the call is not spent.
            pl.horns_sounded = horns.sounded(pl) - {hid}
            self.add_message("There is no room here for anyone to come to you. The note fades, "
                             "and the horn is still yours to blow.", 'warning')
        self._advance_turn()

    def _horn_allies_arrive(self, hid: str, kinds) -> list:
        """Set down beside the hero as many of ``kinds`` as there is room for:
        the free tiles nearest him, four-way first (escort_system's ring)."""
        if not hasattr(self, 'pets') or self.pets is None:
            self.pets = []
        placed = []
        stay = horns.turns(hid)
        for kind in kinds:
            spot = self._escort_tile_near_hero()
            if spot is None:
                break
            ally = horns.CalledAlly(kind, spot[0], spot[1], horn_id=hid, turns=stay)
            ally.called_floor = getattr(self, 'dungeon_level', None)
            self.pets.append(ally)
            placed.append(ally)
        if placed:
            who = horns.who_line([a.ally_kind for a in placed])
            self.add_message(horns.line(hid, 'arrive', who=who), 'success')
            self._chron('deed', horns.chronicle_line(hid, who))
            self._horn_close_thread(hid, horns.chronicle_line(hid, who))
            if hasattr(self, '_refresh_fov'):
                self._refresh_fov()
        return placed

    def _horn_close_thread(self, hid: str, line: str) -> None:
        """The Journal's thread for an unblown horn (opened by its path) closes
        when it is sounded. The Olifant's own thread is Roland's promise at the
        Black Gate, and stays open."""
        import deeds
        if hid == 'olifant':
            return
        deeds.close_thread(self._deeds_reg(), hid, line=line)

    def _horn_tick(self) -> None:
        """A world turn for a host on the road (the Olifant): a line halfway,
        and the host itself when it is due, beside the hero wherever he is. With
        no room for anyone it tries again the next turn."""
        pl = self.player
        due = dict(horns.due(pl))
        if not due:
            return
        for hid in list(due):
            left, chain = int(due[hid][0]) - 1, int(due[hid][1])
            if left == horns.delay(hid) // 2 and horns.line(hid, 'on_road'):
                self.add_message(horns.line(hid, 'on_road'), 'info')
            if left > 0:
                due[hid] = [left, chain]
                continue
            kinds = horns.allies_for(hid, chain)
            if not kinds or self._horn_allies_arrive(hid, kinds):
                due.pop(hid)
            else:
                due[hid] = [1, chain]
        pl.horn_host_due = due

    def _horn_ally_leaves(self, ally) -> None:
        """Its stay is over: the horn's leaving line."""
        self.add_message(horns.line(getattr(ally, 'horn_id', ''), 'leave', name=ally.name)
                         or f"{ally.name} is gone.", 'info')

    def _horn_allies_left_behind(self, new_level) -> None:
        """Leaving the floor: whoever answered stays with it and goes home."""
        pets = getattr(self, 'pets', None) or []
        for p in list(pets):
            if not getattr(p, 'is_called', False):
                continue
            if getattr(p, 'alive', False) and getattr(p, 'called_floor', None) != new_level:
                p.alive = False
                self._horn_ally_leaves(p)
            if not getattr(p, 'alive', False):
                pets.remove(p)

    # ------------------------------------------------------------------
    # QA
    # ------------------------------------------------------------------

    def _qa_horns(self) -> None:
        """Titivillus QA build (Shift+H): the next horn path's encounter set
        down beside the hero (Robin Hood's bridge, the sleepers under the
        hill, Heimdall's watch, Roland in his pass), met or not; after the
        fourth, every horn in the pack and each ready to blow again."""
        pl = self.player
        if not getattr(pl, 'qa_tools', False):
            return
        step = int(getattr(self, '_qa_horn_step', 0) or 0)
        self._qa_horn_step = (step + 1) % (len(QA_PATHS) + 1)
        if step < len(QA_PATHS):
            tag = QA_PATHS[step]
            if self._qa_encounter_beside(tag):
                self.add_message(f"[QA] Horn path {step + 1} of {len(QA_PATHS)}: "
                                 f"{tag} beside you. Shift+H again for the next.", 'info')
            else:
                self.add_message(f"[QA] No room to set {tag} down here.", 'warning')
            return
        from items import make_item_by_id
        have = {getattr(i, 'id', '') for i in pl.inventory}
        for hid in horns.horn_ids():
            if hid in have:
                continue
            item = make_item_by_id('artifact', hid)
            if item is None:
                continue
            item.identified = True
            pl.known_item_ids.add(hid)
            if not pl.add_to_inventory(item):
                pl.inventory.append(item)
        pl.horns_sounded = set()
        pl.horn_host_due = {}
        self.add_message("[QA] Every horn in the pack, each ready to blow (V).", 'info')

    def _qa_encounter_beside(self, tag: str) -> bool:
        """QA: a flavor encounter's person on the tile beside the hero, on
        this floor, as if this were his floor (met before or not)."""
        import economy
        from game_road import _encounter_by_tag
        _src, enc = _encounter_by_tag(tag)
        if enc is None:
            return False
        spent = getattr(self, '_encountered_flavor_npcs', None)
        if spent:
            spent.discard(tag)
        used = (self._deeds_reg().get('used_options') or {})
        used.pop(tag, None)
        for m in list(self.monsters):
            if getattr(m, '_flavor_encounter_tag', None) == tag:
                self.monsters.remove(m)
        spot = self._escort_tile_near_hero()
        if spot is None:
            return False
        level = int(getattr(self, 'dungeon_level', 1) or 1)
        priced = economy.price_encounter(enc, level)
        self._flavor_encounter_levels[level] = priced
        npc = self._spawn_encounter_npc(priced, '_flavor_encounter_tag', level)
        if npc is None:
            return False
        npc.x, npc.y = spot
        return True
