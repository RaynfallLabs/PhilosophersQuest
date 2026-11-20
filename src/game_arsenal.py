"""ArsenalMixin: the Game side of the arsenal's tools (winning-build plan
2026-11-13, sections 3.3-3.5; slice 5).

* **Coat your weapon** (Shift+C, or Apply on the Kit): a coating from the
  pack goes on the weapon in the hand, one turn, no question
  (coatings.apply). Its lines at the end of the action:
  ``_say_arsenal_lines``.
* **Throw a flask** (T): oil, holy water and acid burst for real typed
  damage (coatings.throw_at); routed here from
  CombatMixin._confirm_throw_target.
* **Press or Guard** (Shift+S): the next stance, one turn (stance.py).
* **The earplugs** (Apply on the Kit): in or out, one turn (counters.py).
* **A light** (Apply on the Kit, game_lights.py): a held torch or lantern
  put out or lit again (no time, like Shift+O), a lantern filled from a
  flask of fire oil (one turn).
* **QA** (Titivillus build, Shift+T): every coating and flask, the three
  named counters and a two-hander, in the pack.

The rules live in the pure modules (coatings.py, stance.py, counters.py);
nothing here decides an outcome.
"""
from __future__ import annotations

from game_states import STATE_PLAYER, STATE_QUAFF_MENU


class ArsenalMixin:

    # ------------------------------------------------------------------
    # Lines
    # ------------------------------------------------------------------

    def _say_arsenal_lines(self) -> None:
        """What a coating did this action (a rider refused, the last blow
        spent), said at its end, after the blow's own line."""
        import coatings
        for text, kind in coatings.drain():
            if text:
                self.add_message(text, kind)

    # ------------------------------------------------------------------
    # Press or Guard
    # ------------------------------------------------------------------

    def _cycle_stance(self) -> None:
        """Shift+S: Neutral, Press, Guard, and round again. One turn, as
        swapping a weapon is: the stance is for the fight, not each blow."""
        import stance
        self.add_message(stance.change(self.player), 'info')
        self._advance_turn()

    # ------------------------------------------------------------------
    # Coatings and the Apply action
    # ------------------------------------------------------------------

    def _coatings_in_pack(self) -> list:
        import coatings
        return [i for i in self.player.inventory if coatings.coat_spec(i) is not None]

    def _open_coat_menu(self) -> None:
        """Shift+C: the coatings in the pack, to work into the weapon in the
        hand (the quaff picker in its coat mode)."""
        items = self._coatings_in_pack()
        if not items:
            self.add_message("You carry nothing to coat a weapon with: silver dust, holy "
                             "water, fire oil, frost salts or venom.", 'info')
            return
        if self.player.weapon is None:
            import coatings
            self.add_message(str(coatings.cfg().get('no_weapon', '')), 'warning')
            return
        self.quaff_menu_items = items
        self._quaff_mode = 'coat'
        self._quaff_sel = 0
        self.state = STATE_QUAFF_MENU

    def _apply_label(self, item) -> str:
        """The Kit's Apply label for ``item`` ('' when it cannot be applied)."""
        import coatings
        import counters
        import lights
        if lights.is_light(item):
            # Held: put it out or light it (a dry lantern is filled first);
            # in the pack: a lantern that burns oil is filled.
            if item is getattr(self.player, 'shield', None):
                if getattr(item, 'lit', False) and lights.has_fuel(item):
                    return 'Put Out'
                return 'Light' if lights.has_fuel(item) else 'Fill'
            return 'Fill' if lights.fuel_kind(item) == 'oil' else ''
        if coatings.coat_spec(item) is not None:
            return 'Coat Weapon'
        if counters.is_applied(item):
            return 'Take Out' if counters.ears_stopped(self.player) else 'Put In'
        return ''

    def _apply_block(self, item) -> str:
        """Why Apply would be refused now, or ''."""
        import coatings
        if self._apply_label(item) == 'Fill':
            return self._fill_block(item)
        if coatings.coat_spec(item) is not None:
            why = coatings.refusal(self.player, item)
            return why.rstrip('.') if why else ''
        return ''

    def _apply_item(self, item) -> bool:
        """Apply ``item`` from the pack: a coating onto the weapon in the
        hand, or the earplugs in or out. One turn. True when it was done."""
        import coatings
        import counters
        _label = self._apply_label(item)
        self.state = STATE_PLAYER
        self._quaff_mode = 'quaff'
        if _label == 'Fill':
            return self._fill_light(item)
        if _label in ('Put Out', 'Light'):
            self._toggle_light()
            return True
        if coatings.coat_spec(item) is not None:
            why = coatings.refusal(self.player, item)
            if why:
                self.add_message(why, 'warning')
                return False
            if not self.player.remove_from_inventory(item):
                return False
            self.add_message(coatings.apply(self.player, item), 'success')
            _qs = getattr(self, 'quirk_system', None)
            if _qs is not None:
                _qs.on_coat_applied(str(getattr(item, 'id', '') or ''))   # Medea's Ointment
            self._advance_turn()
            return True
        if counters.is_applied(item):
            self.add_message(counters.toggle_ears(self.player), 'info')
            self._advance_turn()
            return True
        return False

    # ------------------------------------------------------------------
    # Thrown flasks
    # ------------------------------------------------------------------

    def _throw_flask(self, item, monster, tx: int, ty: int) -> None:
        """A flask thrown at (tx, ty): it bursts over the first creature in
        its path for its typed damage (coatings.throw_at), or on the floor.
        Spent either way. The caller advances the turn."""
        import coatings
        from monster import the_name
        self.player.remove_from_inventory(item)
        self._make_noise('shot')
        name = coatings._name(item)
        if monster is None or not getattr(monster, 'alive', False):
            self.add_message(str(coatings.throw_cfg().get('missed', '')).format(flask=name), 'info')
            return
        self._ring_veil_slips()                  # a thrown flask is a strike
        _ = the_name(monster, lower=True)        # before the burst springs a lurker
        _turns = coatings.throw_turns_mult(self.player)       # Callinicus' Fire
        for text, kind in coatings.throw_at(item, monster, turns_mult=_turns):
            self.add_message(text, kind)
        if monster.is_dead():
            # What killed it, for the Seeker (Holy Water) and the quirks
            # (Callinicus' Fire counts the kills of thrown flasks).
            monster.__dict__['_killed_by_flask'] = str(getattr(item, 'id', '') or 'flask')
            self._on_monster_killed(monster, ranged=True)

    # ------------------------------------------------------------------
    # QA
    # ------------------------------------------------------------------

    def _qa_arsenal_sampler(self) -> None:
        """Titivillus QA build only (Shift+T): two of every coating and
        flask, the earplugs, the cold-iron charm, a mirror shield and a
        greatsword in the pack, so coating, throwing, the stance, the parry
        and the counters can be tried in a minute; and every light, with
        three torches and oil for the lanterns (game_lights._qa_lights)."""
        if not getattr(self.player, 'qa_tools', False):
            return
        import coatings
        from items import instantiate_shield, instantiate_weapon, make_item_by_id
        given = 0
        for fid in coatings.flask_defs():
            it = make_item_by_id('flask', fid)
            if it is not None:
                it.count = 2
                self.player.inventory.append(it)
                given += 1
        for aid in ('beeswax_earplugs', 'cold_iron_charm'):
            it = make_item_by_id('accessory', aid)
            if it is not None:
                self.player.inventory.append(it)
                given += 1
        for make in (lambda: instantiate_shield('mirror_shield', 'steel'),
                     lambda: instantiate_weapon('greatsword', 'steel')):
            try:
                it = make()
            except Exception:
                it = None
            if it is not None:
                it.identified = True
                self.player.inventory.append(it)
                given += 1
        given += self._qa_lights()
        self.add_message(f"[QA] The arsenal: {given} things in your pack, every light "
                         f"among them (Shift+C coat, T throw, Shift+S stance, "
                         f"Shift+O light).", 'info')
