"""LightsMixin: the Game side of carried lights (lights.py, 2026-11-19).

* **Taking a light up** (E, the Kit, the @ sheet): one torch off a bundle
  goes into the off hand, lit, with no question (it is held, as a weapon
  is). A shield or a light already in the off hand goes to the pack; a
  two-handed weapon refuses it (Player.can_equip_shield).
* **Burning** (``_light_tick``, every turn from ``_advance_turn``): a held,
  lit light burns one turn of its fuel. A spent torch is gone and the next
  torch in the pack is lit at once; a lantern that runs dry takes the next
  flask of fire oil from the pack, or goes dark.
* **In and out** (Shift+L, ``_swap_light``): one turn, as S is for the
  readied weapon. The light comes out of the pack and the shield goes into
  it; pressed again, the light is stowed and back comes whatever it took
  the place of, by whichever road it was taken up (lights.off_hand_takes).
  A two-hander gives way to a readied one-hander in the same turn and comes
  back with the next press, also when the last light has burnt out. R in
  the Kit picks the kind it draws.
* **Doused or lit** (Shift+O, ``_toggle_light``): no time and no question.
  Doused, it gives no sight and shows the hero to nobody; but the turn in
  which he lit it burns and shows him, once (lights.kindled).
* **Filled** (the Kit's Apply on a lantern or lamp, ``_fill_light``): a
  flask of fire oil fills it to the brim, one turn.
* **Hero's Lamp** shows the down stair on the map while it burns.
* **QA** (Titivillus build, Shift+T, with the arsenal): every light in the
  pack, a bundle of torches and the oil to fill the lanterns.

The rules are lights.py; nothing here decides a number.
"""
from __future__ import annotations

import lights


class LightsMixin:

    # ------------------------------------------------------------------
    # Taking a light up
    # ------------------------------------------------------------------

    def _equip_light(self, item) -> None:
        """Take ``item`` (a light in the pack, a bundle perhaps) into the off
        hand: one of it, lit, in one turn."""
        p = self.player
        if not p.can_equip_shield():
            self.add_message(lights.line('two_hander', light=self._bare_name(item)), 'warning')
            return
        if p.shield is not None and p.shield is not item:
            ok, msg = p.try_unequip_slot(p.shield)
            if not ok:
                self.add_message(msg, 'warning')
                return
        one = self._one_light(item)
        self._dress_begin_on(one)

    def _one_light(self, item):
        """One light off a pack row, as its own row in the pack (the bundle
        keeps the rest): what goes into the hand, so a stack is never in the
        pack and in the hand at once."""
        p = self.player
        if int(getattr(item, 'count', 1) or 1) <= 1:
            return item
        one = lights.take_one(p.inventory, item)
        p.inventory.append(one)
        return one

    def _light_on_line(self, item) -> str:
        """The line said as a light goes into the hand."""
        name = self._bare_name(item)
        if lights.is_lit(item):
            return lights.line('taken_up', light=name)
        if lights.has_fuel(item):
            return lights.line('taken_up_wet', light=name)
        return lights.line('taken_up_dry', light=name)

    # ------------------------------------------------------------------
    # Burning, every turn
    # ------------------------------------------------------------------

    def _light_tick(self) -> None:
        """One turn of the held light's burning, and what follows from it.
        Whatever changed the light since last turn (the spell running out, a
        two-hander sending the torch to the pack) widens or narrows the view
        now, not at the next step."""
        p = getattr(self, 'player', None)
        if p is None:
            return
        try:
            now = lights.light_bonus(p)
        except Exception:
            now = 0
        if self.__dict__.get('_light_seen', now) != now:
            self._refresh_fov()
        self.__dict__['_light_seen'] = now
        lt = lights.held(p)
        if lt is not None:
            import light_shy
            light_shy.dry_tick(lt)                # a soaked wick dries (AI-1)
            if lights.shows_way(p):
                self._show_way_down(lt)
        # The held light, or the one lit for a look this turn (lights.kindled),
        # wherever it is now: either way one turn of fuel.
        owed, p._kindled = getattr(p, '_kindled', None), None
        burns = owed if owed is not None else lt
        if burns is None:
            return
        alight = burns is lt and lights.is_lit(lt)
        what = lights.burn_turn(burns, counted=owed is not None)
        if what == 'low':
            self.add_message(lights.line('low', light=self._bare_name(burns)), 'warning')
        elif what == 'out':
            if alight:
                self._light_spent(lt)
            else:
                self._light_burnt_out(burns)
            self._refresh_fov()

    def _light_spent(self, lt) -> None:
        """The held light has burnt its last: a torch is gone (the next is
        lit), a lantern runs dry (refilled from the pack's oil if there is
        any)."""
        p = self.player
        name = self._bare_name(lt)
        if lights.fuel_kind(lt) == 'oil':
            flask = lights.oil_in(p.inventory)
            if flask is not None and p.remove_from_inventory(flask):
                lights.fill(lt)
                import light_shy
                lt.lit = not light_shy.wet(lt)        # a soaked wick will not take (AI-1)
                self.add_message(lights.line('oil_refill', light=name), 'info')
            else:
                self.add_message(lights.line('oil_out', light=name), 'warning')
            return
        # A torch: burnt away. Out of the hand, out of the kits.
        p.shield = None
        p.shed_worn_grants(lt)
        try:
            import loadouts
            loadouts.let_go(p, lt)
        except Exception:
            pass
        nxt = lights.next_torch(p.inventory, lt)
        if nxt is None:
            self.add_message(lights.line('last_torch', light=name), 'warning')
            return
        one = lights.take_one(p.inventory, nxt)
        p._apply_equip(one)
        left = sum(int(getattr(i, 'count', 1) or 1) for i in p.inventory
                   if getattr(i, 'id', None) == getattr(lt, 'id', None))
        self.add_message(lights.line('next_torch', light=name, left=left), 'info')

    def _light_burnt_out(self, lt) -> None:
        """A light burnt its last in a turn it was lit for a look and put
        out again: nothing is lit in its place, for the hero chose the dark."""
        p = self.player
        name = self._bare_name(lt)
        if lights.fuel_kind(lt) == 'oil':
            self.add_message(lights.line('oil_out', light=name), 'warning')
            return
        if p.shield is lt:
            p.shield = None
            p.shed_worn_grants(lt)
        else:
            p.remove_from_inventory(lt)
        import loadouts
        loadouts.let_go(p, lt)
        self.add_message(lights.line('burnt_out', light=name), 'warning')

    def _show_way_down(self, lt) -> None:
        """Hero's Lamp: the down stair shows on the map, once a floor."""
        d = getattr(self, 'dungeon', None)
        if d is None or d.__dict__.get('_way_down_shown'):
            return
        from dungeon import _find_stair_tiles
        _up, down = _find_stair_tiles(d.tiles, d.width, d.height)
        d.__dict__['_way_down_shown'] = True
        if down is not None:
            d.explored.add(down)
            self.add_message(lights.line('way_down', light=self._bare_name(lt)), 'info')

    # ------------------------------------------------------------------
    # Shift+O: put it out, light it again
    # ------------------------------------------------------------------

    def _toggle_light(self) -> None:
        """Douse the held light or light it again: no time, no question.
        Lit, it counts for this turn's fuel and notice whatever follows
        (lights.kindled). A dry lantern is filled from the pack's oil first
        (one turn)."""
        p = self.player
        lt = lights.held(p)
        if lt is None:
            self.add_message(lights.line('no_light'), 'info')
            return
        name = self._bare_name(lt)
        if getattr(lt, 'lit', False) and lights.has_fuel(lt):
            lt.lit = False
            self.add_message(lights.line('doused', light=name), 'info')
            self._refresh_fov()
            return
        if not lights.has_fuel(lt):
            if lights.fuel_kind(lt) == 'oil' and lights.oil_in(p.inventory) is not None:
                self._fill_light(lt)
                return
            self.add_message(lights.line('dry', light=name), 'warning')
            return
        import light_shy
        if light_shy.wet(lt):
            # Doused by a wave or a gust (AI-1, src/light_shy.py).
            self.add_message(light_shy.rules().get('lines', {}).get('soaked', ''), 'warning')
            return
        lt.lit = True
        lights.kindled(p, lt)
        self.add_message(lights.line('relit', light=name), 'info')
        self._refresh_fov()

    # ------------------------------------------------------------------
    # Shift+L: a light in, a light out
    # ------------------------------------------------------------------

    def _ready_light(self, item) -> None:
        """The Kit's R on a light: the kind Shift+L takes up first (no turn)."""
        self.player._light_kind = str(getattr(item, 'id', '') or '')
        import copy
        one = copy.copy(item)
        one.count = 1                           # a kind is readied, not the bundle
        self.add_message(lights.line('readied', light=self._bare_name(one)), 'info')

    def _unready_light(self, item) -> None:
        self.player._light_kind = ''
        self.player._light_last = ''            # (the brightest, as the line says)
        self.add_message(lights.line('unreadied', light=self._bare_name(item)), 'info')

    def _swap_light(self) -> bool:
        """Shift+L: the light and what it takes the place of change places,
        in one turn however much moves. True when they did."""
        if lights.held(self.player) is not None:
            done = self._stow_light()
        else:
            done = self._draw_light()
        if done:
            self._refresh_fov()
            self._advance_turn()
        return done

    def _carried_aside(self, name: str):
        """A piece the swap set aside, if it is still in the pack."""
        p = self.player
        it = p.__dict__.get(name)
        if it is not None and any(i is it for i in p.inventory):
            return it
        p.__dict__[name] = None
        return None

    def _light_takes_place(self, shield, tier: int) -> None:
        """``shield`` came off his arm for a light: it goes back on with no
        quiz, at the tier it had."""
        import known_by_hand
        known_by_hand.learn(self.player, shield, tier)
        lights.set_aside(self.player, shield)

    def _draw_light(self) -> bool:
        """A light into the off hand. With none left to burn, what the last
        one took the place of comes back instead, as a stow gives it back.
        Nothing moves until all that must move is known to be free."""
        p = self.player
        lt = lights.pick(p)
        if lt is None:
            if p.shield is None and self._give_back(self._waiting_two_hander()):
                return True
            self.add_message(lights.line('none_to_take'), 'info')
            return False
        hand, side, shield = p.weapon, None, p.shield
        if not p.can_equip_shield():
            side = p.readied_weapon
            if side is None or getattr(side, 'two_handed', False):
                self.add_message(lights.line('two_hander_swap', light=self._bare_name(lt)),
                                 'warning')
                return False
        for piece in (hand if side is not None else None, shield):
            if piece is not None:
                ok, msg = p.try_unequip_slot(piece)
                if not ok:
                    self.add_message(msg, 'warning')
                    return False

        if side is not None:
            if not self._wield_now(side):
                return False
            p.readied_weapon = hand
            self.add_message(lights.line('sidearm', two_hander=self._bare_name(hand),
                                         weapon=self._bare_name(side)), 'info')
        if shield is not None:
            tier = int(getattr(shield, 'achieved_tier', 0) or 0)
            if not self._take_off_now('shield', shield):
                return False
            self._light_takes_place(shield, tier)
        if not lights.has_fuel(lt):
            flask = lights.oil_in(p.inventory)
            if flask is not None and p.remove_from_inventory(flask):
                lights.fill(lt)
                self.add_message(lights.line('filled', light=self._bare_name(lt)), 'info')
        self._put_on_now(self._one_light(lt))
        if side is not None:
            # (after the light is in the hand: lights.off_hand_takes has by
            # then set aside the shield that waited for the free hand)
            p._light_sidearm = hand
        return True

    def _stow_light(self) -> bool:
        """The light into the pack, and back what it took the place of: the
        two-hander it changed for a one-hander, else the shield."""
        p = self.player
        lt = p.shield
        big = self._waiting_two_hander()
        if not self._take_off_now('shield', lt):
            return False
        p._light_last = str(getattr(lt, 'id', '') or '')
        p._shield_slung = None
        self._give_back(big)
        lights.forget(p)
        return True

    def _waiting_two_hander(self):
        """The two-hander Shift+L changed for a one-hander, if it still
        waits at his back: another weapon readied or drawn since is the
        hero's own choice, and stands."""
        p = self.player
        big, hand = self._carried_aside('_light_sidearm'), p.weapon
        if big is None or big is not p.readied_weapon or getattr(hand, 'two_handed', False):
            return None
        if hand is not None and not p.try_unequip_slot(hand)[0]:
            return None
        return big

    def _give_back(self, big) -> bool:
        """What the light took the place of, now that it is gone: ``big``
        into both hands (the shield then waits for a one-hander:
        lights.two_hands), else the shield onto the arm. True when either."""
        p = self.player
        hand = p.weapon
        back = self._carried_aside('_light_aside')
        if big is not None and self._wield_now(big):
            if hand is not None:
                p.readied_weapon = hand
            self.add_message(lights.line('sidearm_back', two_hander=self._bare_name(big)), 'info')
            return True
        return back is not None and p.can_equip_shield() and self._aside_back_on(back)

    def _aside_back_on(self, shield) -> bool:
        import known_by_hand
        p = self.player
        return self._put_on_now(shield, tier=known_by_hand.best_tier(p, shield))

    # ------------------------------------------------------------------
    # Filling a lantern (the Kit's Apply)
    # ------------------------------------------------------------------

    def _fill_block(self, item) -> str:
        """Why a lantern cannot be filled now, or ''."""
        if not lights.needs_fill(item):
            return lights.line('full', light=self._bare_name(item)).rstrip('.')
        if lights.oil_in(self.player.inventory) is None:
            return lights.line('no_oil').rstrip('.')
        return ''

    def _fill_light(self, item) -> bool:
        """A flask of fire oil from the pack into ``item``, one turn. A held
        lantern is lit again. True when it was filled."""
        p = self.player
        why = self._fill_block(item)
        if why:
            self.add_message(f"{why}.", 'warning')
            return False
        flask = lights.oil_in(p.inventory)
        if flask is None or not p.remove_from_inventory(flask):
            return False
        lights.fill(item)
        import light_shy
        if item is p.shield and not light_shy.wet(item):
            item.lit = True
        self.add_message(lights.line('filled', light=self._bare_name(item)), 'success')
        if item is p.shield and light_shy.wet(item):
            # Doused by a wave or a gust (AI-1): filled, but the wick is soaked.
            self.add_message(light_shy.rules().get('lines', {}).get('soaked', ''), 'warning')
        self._refresh_fov()
        self._advance_turn()
        return True

    # ------------------------------------------------------------------
    # The sidebar's marker
    # ------------------------------------------------------------------

    def _light_hud_line(self) -> str:
        lt = lights.held(getattr(self, 'player', None))
        if lt is None:
            return ''
        return lights.hud_line(self.player, self._bare_name(lt))

    # ------------------------------------------------------------------
    # QA
    # ------------------------------------------------------------------

    def _qa_lights(self) -> int:
        """Titivillus QA build (with the arsenal, Shift+T): one of every
        light, three torches and two flasks of fire oil in the pack. Returns
        how many things were given."""
        from items import make_item_by_id
        import json
        from paths import data_path
        with open(data_path('data', 'items', 'light.json'), encoding='utf-8') as f:
            ids = [k for k, v in json.load(f).items() if isinstance(v, dict)]
        given = 0
        for lid in ids:
            it = make_item_by_id('light', lid)
            if it is None:
                continue
            if getattr(it, 'stacks', False):
                it.count = 3
            it.id_level = 5
            self.player.inventory.append(it)
            given += 1
        oil = make_item_by_id('flask', 'flask_of_fire_oil')
        if oil is not None:
            oil.count = 2
            self.player.inventory.append(oil)
            given += 1
        return given
