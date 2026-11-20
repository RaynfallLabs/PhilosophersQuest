"""LightsMixin: the Game side of carried lights (lights.py, 2026-11-19).

* **Taking a light up** (E, the Kit, the @ sheet): one torch off a bundle
  goes into the off hand, lit, with no question (it is held, as a weapon
  is). A shield or a light already in the off hand goes to the pack; a
  two-handed weapon refuses it (Player.can_equip_shield).
* **Burning** (``_light_tick``, every turn from ``_advance_turn``): a held,
  lit light burns one turn of its fuel. A spent torch is gone and the next
  torch in the pack is lit at once; a lantern that runs dry takes the next
  flask of fire oil from the pack, or goes dark.
* **Doused or lit** (Shift+O, ``_toggle_light``): no time and no question.
  Doused, it gives no sight and shows the hero to nobody.
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
        if lt is None:
            return
        import light_shy
        light_shy.dry_tick(lt)                # a soaked wick dries (AI-1)
        if lights.shows_way(p):
            self._show_way_down(lt)
        what = lights.burn_turn(lt)
        if what == 'low':
            self.add_message(lights.line('low', light=self._bare_name(lt)), 'warning')
        elif what == 'out':
            self._light_spent(lt)
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
        A dry lantern is filled from the pack's oil first (one turn)."""
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
        self.add_message(lights.line('relit', light=name), 'info')
        self._refresh_fov()

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
