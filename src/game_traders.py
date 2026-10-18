"""The traders on the Game side (economy refactor 2026-10-17): placing the
run's planned trader on first arrival, and the shop with its Buy, Sell and
Services tabs. The rules (plan, stock, offers, deeds prices) are pure, in
traders.py and economy.py; the people and their lines are data/traders.json.

The shop keeps the old names other code and saves use: ``STATE_SHOP``,
``_shop_merchant``, ``_shop_selection``, ``_shop_haggled``; Y opens it
(main._open_shop), game_input._shop_input sends keys to ``_trader_input`` and
game_render._draw_shop draws ``_trader_menu``.

Gold buys a second chance, never the answer: every service still leaves the
quiz where it was (an identify with the scribe is the same question, without
the backlash).
"""
from __future__ import annotations

import pygame

import economy
import traders
from game_states import STATE_PLAYER, STATE_SHOP

SHOP_TABS = (('Buy', None), ('Sell', None), ('Services', None))
TAB_BUY, TAB_SELL, TAB_SERVICES = 0, 1, 2

# Statuses a physician treats (the 'cure' service). Only a timed one: a
# status an item grants for good (-1) is the item's, not an illness.
CURABLE = ('poisoned', 'diseased', 'blinded', 'confused', 'hallucinating', 'stunned',
           'fumbling', 'weakened', 'bleeding', 'slowed', 'petrifying', 'burning', 'corroding')


class TraderMixin:
    """Spawn, open, keys and the menu model for the shop."""

    # ---------------------------------------------------------------- plan

    def _trader_plan(self) -> dict:
        st = traders.ensure_plan(self.__dict__.get('_traders'))
        if st is None:
            road = self._road_state() if hasattr(self, '_road_state') else {}
            seed = int((road or {}).get('seed') or 0)
            if not seed:
                import road as _road
                seed = _road.roll_seed()
            import road as _road
            secrets = [(getattr(self, '_emberpup', None) or {}).get('floor'),
                       (getattr(self, '_black_knight', None) or {}).get('floor')]
            st = traders.roll_plan(seed, secret_floors=secrets,
                                   busy_floors=_road.busy_floors(road or {}))
            self._traders = st
        return st

    def _maybe_spawn_trader(self, level: int):
        """Place the run's trader for this floor, once, on first arrival.
        His stock and his spot come from his own generator (the plan's seed
        and the floor), so the shared random stream is untouched."""
        from mystery_system import MerchantNPC, build_trader
        plan = self._trader_plan()
        kind = plan['floors'].get(level)
        if not kind or level in plan['spawned']:
            return None
        if any(isinstance(g, MerchantNPC) for g in self.ground_items):
            plan['spawned'].append(level)
            return None
        import road
        rng = road.rng_for(plan['seed'], f'trader:{level}')
        # His stock leans toward kinds the hero has not held yet (data/
        # traders.json stock_bias): ids only, nothing about them is shown.
        p = self.player
        seen = set(getattr(p, 'seen_item_ids', ()) or ()) | set(getattr(p, 'known_item_ids', ()) or ())
        m = build_trader(kind, level, rng, seen=seen)
        from items import claim_unique
        for it in m.stock:
            claim_unique(it)
            stamp = getattr(self, 'apply_appearance', None)
            if stamp is not None:
                try:
                    stamp(it)
                except Exception:
                    pass
        friend = traders.friend_for(kind, self._deed_ctx(), plan['friends_used'])
        if friend:
            m.set_person(traders.kind_def(kind), friend)
            plan['friends_used'].append(friend['person'])
        spot = self._trader_spot(rng)
        if spot is None:
            return None
        m.x, m.y = spot
        self.ground_items.append(m)
        plan['spawned'].append(level)
        return m

    def _trader_spot(self, rng):
        """A floor tile in a room the hero can walk to, clear of the stairs,
        of every item and creature, and not right beside the hero or an
        encounter NPC (the Road's people keep their own space)."""
        from dungeon import FLOOR
        d = self.dungeon
        px, py = self.player.x, self.player.y
        reach = self._reachable_tiles(px, py)
        taken = {(g.x, g.y) for g in self.ground_items}
        from geom import all_occupied_tiles
        taken |= set(all_occupied_tiles(self.monsters))
        crowd = set()
        for mo in self.monsters:
            if (getattr(mo, '_npc_encounter_tag', None) or getattr(mo, '_flavor_encounter_tag', None)
                    or getattr(mo, 'is_escort', False) or getattr(mo, 'is_allied', False)):
                crowd |= {(mo.x + dx, mo.y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}

        def ok(x, y):
            return (d.tiles[y][x] == FLOOR and (x, y) in reach and (x, y) not in taken
                    and (x, y) not in crowd and max(abs(x - px), abs(y - py)) >= 3)
        rooms = list(getattr(d, 'rooms', None) or [])
        for room in rooms[1:] + rooms[:1]:
            cand = sorted((x, y) for x, y in room.inner_tiles() if ok(x, y))
            if cand:
                return rng.choice(cand)
        cand = sorted(t for t in reach if ok(*t))
        return rng.choice(cand) if cand else None

    # ---------------------------------------------------------------- open

    def _trader_open(self, merchant):
        """Open the shop on ``merchant``: his greeting, what the hero's deeds
        have done to his prices, any credit the hero has earned."""
        self._shop_merchant = merchant
        self._shop_selection = 0
        self._shop_pick = None
        self._shop_haggled = {i for i, it in enumerate(merchant.stock)
                              if getattr(it, '_haggled', False)}
        friend = bool(getattr(merchant, 'friend', None))
        mult, lines = traders.price_mult(getattr(merchant, 'kind', 'generalist'),
                                         self._deed_ctx(), friend=friend)
        self._shop_mult = mult
        plan = self._trader_plan()
        reg = self._deeds_reg()
        self._shop_credit = traders.credits_owed(reg, plan.get('credits_used', 0)) > 0
        if not getattr(merchant, 'greeted', False):
            merchant.greeted = True
            greet = (merchant.lines or {}).get('greet')
            if isinstance(greet, list) and greet:
                import road
                pick = road.rng_for(plan['seed'], f'greet:{merchant.level}:{merchant.person}')
                greet = pick.choice(greet)
            if greet:
                self.add_message(f'{merchant.person}: "{greet}"', 'info')
            gate = ((traders.kind_def(merchant.kind).get('gate_lines') or {})
                    .get(str(getattr(merchant, 'level', 0))))
            if gate:
                self.add_message(f'{merchant.person}: "{gate}"', 'warning')
        for key, line in lines:
            # Each reason is said once a run (the first trader who knows it).
            if key not in plan['told'] and line:
                plan['told'].append(key)
                self.add_message(f'{merchant.person}: "{line}"', 'warning')
        if self._shop_credit:
            self.add_message(
                f'{merchant.person}: "Word is you keep your promises. Down here that\'s '
                f'rarer than gold. One thing, on the house."', 'success')
        self._trader_appraise(merchant)
        self._shop_tab = TAB_SELL if not merchant.stock else TAB_BUY
        self.state = STATE_SHOP

    def _trader_appraise(self, merchant):
        """A trader values every piece of treasure in the pack, and the gems
        on his own table carry their price: from now on the hero knows what
        each of those KINDS is worth (treasure.py)."""
        import treasure
        p = self.player
        new = [it for it in treasure.carried(p) if treasure.appraise(p, it)]
        for it in merchant.stock:
            if treasure.is_treasure(it):
                treasure.appraise(p, it)
        if new:
            names = ', '.join(self._bare_name(i) for i in new[:3]) + (', ...' if len(new) > 3 else '')
            self.add_message(f"{merchant.person} weighs your treasure in his palm and names a price "
                             f"for each: {names}.", 'info')

    def _trader_open_adjacent(self):
        from mystery_system import MerchantNPC
        px, py = self.player.x, self.player.y
        merchant = next((gi for gi in self.ground_items if isinstance(gi, MerchantNPC)
                         and abs(gi.x - px) <= 1 and abs(gi.y - py) <= 1), None)
        if merchant is None:
            self.add_message("No trader nearby. (Y opens the shop when one stands beside you.)", 'info')
            return
        self._trader_open(merchant)

    # ---------------------------------------------------------------- prices

    def _trader_price(self, i: int) -> int:
        m = self._shop_merchant
        base = m.prices[i] if i < len(m.prices) else 0
        mult = float(getattr(self, '_shop_mult', 1.0) or 1.0)
        if i < len(m.stock) and getattr(m.stock[i], 'item_class', '') == 'treasure':
            # The exchange: never below its own price (a friend's or a
            # charity discount on a gem he buys back at 90% would be a loop).
            return max(1, int(round(base * max(1.0, mult))))
        return max(1, economy.nice(base * mult))

    def _trader_pay_words(self, plan) -> str:
        """The detail-pane line for a purchase paid partly in treasure."""
        bits = self._payment_words(plan)
        ch = int(plan.get('change', 0) or 0)
        m = self._shop_merchant
        if ch:
            give = min(ch, int(getattr(m, 'purse', 0) or 0))
            bits += f"; {give:,} gold back" + ("" if give >= ch else f" (his purse is short {ch - give:,})")
        return f"Pays with {bits}."

    def _trader_credit_value(self) -> int:
        if not getattr(self, '_shop_credit', False):
            return 0
        share = float((traders.data().get('guild') or {}).get('credit_share', 1.0))
        return economy.share(self.dungeon_level, share)

    def _trader_offer(self, item) -> tuple:
        """(offer, refusal) for selling ``item`` to the open trader."""
        from player import _buc_known_to_player
        m = self._shop_merchant
        known = self._item_is_known(item)
        cursed_known = getattr(item, 'buc', '') == 'cursed' and _buc_known_to_player(item)
        why = traders.refusal({'buys': m.buys, 'buys_cursed': m.buys_cursed}, item,
                              known=known, cursed_known=cursed_known,
                              quest_ids=self._QUEST_PIECE_IDS)
        if why:
            return 0, why
        try:
            ident = int(getattr(item, 'id_level', 0) or 0) >= 5
        except (TypeError, ValueError):
            ident = False
        offer = economy.sell_offer(item, self.dungeon_level, known=known, identified=ident,
                                   markup=m.markup, purse=m.purse)
        if offer <= 0:
            return 0, "His purse is empty" if m.purse <= 0 else "Worthless to him"
        return offer, None

    # ---------------------------------------------------------------- keys

    def _trader_input(self, key: int):
        m = getattr(self, '_shop_merchant', None)
        if m is None:
            self.state = STATE_PLAYER
            return
        if key == pygame.K_ESCAPE:
            if getattr(self, '_shop_pick', None):
                self._shop_pick = None
                self._shop_selection = 0
                return
            self.state = STATE_PLAYER
            return
        tabs = self._trader_tabs()
        if key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB) and not getattr(self, '_shop_pick', None):
            step = -1 if key == pygame.K_LEFT else 1
            self._shop_tab = (getattr(self, '_shop_tab', 0) + step) % len(tabs)
            self._shop_selection = 0
            return
        rows = self._trader_rows()
        sel = getattr(self, '_shop_selection', 0)
        if key in getattr(self, '_MENU_CURSOR_KEYS', (pygame.K_UP, pygame.K_DOWN)):
            if rows:
                self._shop_selection = self._move_menu_cursor(sel, key, len(rows))
            return
        tab = getattr(self, '_shop_tab', TAB_BUY)
        if key == pygame.K_h and tab == TAB_BUY:
            if sel < len(m.stock):
                if getattr(m.stock[sel], 'item_class', '') == 'treasure':
                    # The exchange is the exchange: a gem bought cheap and sold
                    # back at 90% would be a loop.
                    self.add_message(f'{m.person}: "A stone is worth what it is worth. '
                                     f'No haggling over gems."', 'info')
                elif sel in getattr(self, '_shop_haggled', set()):
                    self.add_message("You've already haggled over that item.", 'info')
                else:
                    self._haggle_item(sel)
            return
        if key not in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) or not rows:
            return
        sel = min(sel, len(rows) - 1)
        if getattr(self, '_shop_pick', None):
            self._trader_service_on(self._shop_pick[0], rows[sel])
        elif tab == TAB_BUY:
            self._trader_buy(sel)
        elif tab == TAB_SELL:
            self._trader_sell(rows[sel])
        else:
            self._trader_service(rows[sel])

    def _trader_tabs(self):
        m = self._shop_merchant
        return SHOP_TABS if getattr(m, 'services', ()) else SHOP_TABS[:2]

    def _trader_rows(self) -> list:
        """What the active tab lists: stock indices, pack items, services,
        or the targets of the service being chosen."""
        m = self._shop_merchant
        pick = getattr(self, '_shop_pick', None)
        if pick:
            return list(pick[1])
        tab = getattr(self, '_shop_tab', TAB_BUY)
        if tab == TAB_BUY:
            return list(range(len(m.stock)))
        if tab == TAB_SELL:
            return list(self.player.inventory)
        return list(getattr(m, 'services', ()))

    # ---------------------------------------------------------------- buy

    def _trader_buy(self, sel: int):
        m = self._shop_merchant
        if sel >= len(m.stock):
            return
        item = m.stock[sel]
        price = self._trader_price(sel)
        credit = min(price, self._trader_credit_value())
        pay = price - credit
        # Coin first, then treasure at his rate, change from his purse
        # (game_purse._pay_gold): gems are how a hero carries wealth.
        plan = self._payment_plan(pay)
        if plan is None:
            self.add_message(f'{m.person}: "{m.line("broke", "No coin, no deal.")}" '
                             f'({pay:,} gold needed.)', 'warning')
            return
        iname = self._display_name(item)              # as the shop showed it
        # Pay first: the coin and treasure paid lighten the pack before the
        # ware goes into it. A ware still too heavy is the hero's, at his feet.
        done = self._pay_gold(pay, change_purse=int(m.purse), who=m.person)
        if done:
            m.purse = max(0, int(m.purse) - int(done.get('change_given', 0) or 0))
        before = {id(i): int(getattr(i, 'count', 1) or 1) for i in self.player.inventory}
        if self.player.add_to_inventory(item) is False:
            item.x, item.y = self.player.x, self.player.y
            self.ground_items.append(item)
            self.add_message(f"It is too heavy to carry with everything else, so {m.person} "
                             f"sets it down at your feet.", 'warning')
        elif getattr(item, 'item_class', '') != 'treasure':
            self._trader_mark_bought(item, before, price)
        if getattr(item, 'item_class', '') == 'treasure':
            import treasure
            treasure.appraise(self.player, item)
        import sound_system as _snd
        try:
            _snd.play('buy')
        except Exception:
            pass
        if credit:
            plan = self._trader_plan()
            plan['credits_used'] = int(plan.get('credits_used', 0)) + 1
            self._shop_credit = False
            self.add_message(f"You take {iname}, on the house"
                             + (f", and pay {pay:,} gold for the rest." if pay else "."), 'success')
        else:
            self.add_message(f"You buy {iname} for {pay:,} gold.", 'success')
        line = m.line('bought')
        if line:
            self.add_message(f'{m.person}: "{line}"', 'info')
        m.stock.pop(sel)
        m.prices.pop(sel)
        haggled = getattr(self, '_shop_haggled', set())
        self._shop_haggled = {i - 1 if i > sel else i for i in haggled if i != sel}
        self._shop_selection = max(0, min(sel, len(m.stock) - 1))
        if not m.stock:
            m.sold_out = True
            self.add_message(f'{m.person}: "{m.line("sold_out", "That is everything.")}"', 'info')
            self._shop_tab = TAB_SELL

    def _trader_mark_bought(self, item, before: dict, price: int):
        """Remember what was paid on the thing bought (economy.RESALE_CAP_OF_PAID:
        it never sells back for more than half of that). A potion that joined
        a stack marks the stack."""
        target = item if any(i is item for i in self.player.inventory) else next(
            (i for i in self.player.inventory if id(i) in before
             and int(getattr(i, 'count', 1) or 1) > before[id(i)]), item)
        old = getattr(target, '_bought_for', None)
        target._bought_for = price if old is None else min(int(old), price)

    # ---------------------------------------------------------------- sell

    def _trader_sell(self, item):
        m = self._shop_merchant
        offer, why = self._trader_offer(item)
        if why:
            key = 'purse_empty' if why == "His purse is empty" else 'refuse'
            self.add_message(f'{m.person}: "{m.line(key, "No.")}" ({why}.)', 'warning')
            return
        from items import Ammo
        if isinstance(item, Ammo):
            name = self._display_name(item)
        elif int(getattr(item, 'count', 1) or 1) <= 1:
            name = f"the {self._bare_name(item)}"        # "You sell the Gold Idol to Grindle"
        else:
            from paths import a_or_an
            name = a_or_an(self._bare_name_one(item))
        if isinstance(item, Ammo) or int(getattr(item, 'count', 1) or 1) <= 1:
            self.player.inventory.remove(item)
            try:
                self.player.refresh_carry_bonuses()
            except Exception:
                pass
        else:
            self.player.remove_from_inventory(item)
        m.purse = max(0, int(m.purse) - offer)
        self.add_message(f"You sell {name} to {m.person} for {offer:,} gold.", 'success')
        # Coins weigh: what will not fit he pays in gems (game_purse).
        self._gain_gold(offer, paid=True, who=m.person)
        line = m.line('sold')
        if line:
            self.add_message(f'{m.person}: "{line}"', 'info')
        rows = self._trader_rows()
        self._shop_selection = max(0, min(getattr(self, '_shop_selection', 0), len(rows) - 1))

    def _bare_name_one(self, item) -> str:
        """One of a stack, named as the hero knows it ("a Potion of Healing")."""
        import copy as _copy
        one = _copy.copy(item)
        one.count = 1
        return self._display_name(one)

    # ---------------------------------------------------------------- services

    def _service_targets(self, sid: str) -> list:
        """What a service could work on now (empty: nothing to do)."""
        p = self.player
        if sid == 'repair':
            return [i for i in p.worn_items() if int(getattr(i, 'wear_loss', 0) or 0) > 0]
        if sid == 'sharpen':
            w = p.weapon
            if w is not None and not getattr(w, 'bound_to_wielder', False) \
                    and int(getattr(w, '_smith_bonus', 0) or 0) < economy.SMITH_ENCHANT_CAP:
                return [w]
            return []
        if sid == 'reinforce':
            from items import ARMOR_SLOTS
            slots = list(getattr(p, 'armor_slots', None) or [])
            body = slots[ARMOR_SLOTS.index('body')] if 'body' in ARMOR_SLOTS and \
                ARMOR_SLOTS.index('body') < len(slots) else None
            body = body or next((s for s in slots if s is not None), None)
            if body is not None and int(getattr(body, '_smith_bonus', 0) or 0) < economy.SMITH_ENCHANT_CAP:
                return [body]
            return []
        if sid == 'cut_curse':
            from player import _buc_known_to_player
            return [i for i in p.worn_items()
                    if getattr(i, 'buc', '') == 'cursed' and _buc_known_to_player(i)
                    and not getattr(i, 'bound_to_wielder', False)
                    and getattr(i, 'id', None) not in self._QUEST_PIECE_IDS]
        if sid == 'cure':
            return [e for e in CURABLE if int(p.status_effects.get(e, 0) or 0) > 0]
        if sid == 'restore':
            return ['restore'] if self._drained_total() > 0 else []
        if sid == 'heal':
            return ['heal'] if p.hp < p.max_hp else []
        if sid == 'id_retry':
            return [i for i in p.inventory if hasattr(i, 'id_level')
                    and int(getattr(i, 'id_level', 0) or 0) < 5
                    and getattr(i, 'item_class', '') not in ('ingredient', 'corpse', 'food')]
        if sid == 'map':
            d = self.dungeon
            return ['map'] if len(d.explored) < d.width * d.height else []
        if sid == 'porter':
            return [] if p.has_effect('porter') else ['porter']
        return []

    def _drained_total(self) -> int:
        p = self.player
        n = int(getattr(p, '_str_lost_to_disease', 0) or 0)
        n += sum(int(v or 0) for v in (p.__dict__.get('drained') or {}).values())
        return n

    def _service_price(self, sid: str) -> int:
        m = self._shop_merchant
        points = 1
        if sid == 'repair':
            points = sum(int(getattr(i, 'wear_loss', 0) or 0) for i in self._service_targets('repair')) or 1
        # (A share of the whole purse, treasure included: game_purse.)
        base = economy.service_price(sid, self.dungeon_level, purse=self._purse_wealth(),
                                     points=points, markup=m.markup)
        return max(5, economy.nice(base * float(getattr(self, '_shop_mult', 1.0) or 1.0)))

    def _trader_service(self, sid: str):
        m = self._shop_merchant
        targets = self._service_targets(sid)
        name = (traders.data().get('services') or {}).get(sid, {}).get('name', sid)
        if not targets:
            self.add_message(f"{name}: there is nothing for {m.person} to do.", 'info')
            return
        price = self._service_price(sid)
        if self._payment_plan(price) is None:
            self.add_message(f'{m.person}: "{m.line("broke", "No coin, no deal.")}" '
                             f'({price:,} gold needed.)', 'warning')
            return
        if sid in ('cut_curse', 'id_retry') and len(targets) > 1:
            self._shop_pick = (sid, targets)
            self._shop_selection = 0
            return
        self._trader_service_on(sid, targets[0])

    def _trader_service_on(self, sid: str, target):
        """Pay for and render one service."""
        m = self._shop_merchant
        price = self._service_price(sid)
        if self._payment_plan(price) is None:
            self.add_message(f'{m.person}: "{m.line("broke", "No coin, no deal.")}"', 'warning')
            return
        self._shop_pick = None
        self._shop_selection = 0
        # Priced before (a restore's share is of the purse as it stands),
        # paid after: nothing done, nothing owed.
        done = self._render_service(sid, target, who=m.person)
        if not done:
            return
        paid = self._pay_gold(price, change_purse=int(m.purse), who=m.person, quiet=True)
        if paid:
            m.purse = max(0, int(m.purse) - int(paid.get('change_given', 0) or 0))
            if paid.get('take'):
                self.add_message(f"(You pay {self._payment_words(paid)}"
                                 + (f"; {int(paid['change_given']):,} gold back.)"
                                    if paid.get('change_given') else ".)"), 'info')
            else:
                self.add_message(f"({price:,} gold.)", 'info')

    def _render_service(self, sid: str, target, who: str = 'The smith') -> bool:
        """Do the service (shared with encounter vendors: a 'service' reward).
        True when something was done."""
        p = self.player
        if sid == 'repair':
            pieces = self._service_targets('repair')
            if not pieces:
                return False
            for it in pieces:
                it.enchant_bonus = int(getattr(it, 'enchant_bonus', 0) or 0) + int(it.wear_loss)
                it.wear_loss = 0
            self.add_message(f"{who} scours the rust and pits out of your gear. "
                             "It is as good as it was.", 'success')
            return True
        if sid in ('sharpen', 'reinforce'):
            tgt = (self._service_targets(sid) or [None])[0]
            if tgt is None:
                return False
            tgt.enchant_bonus = int(getattr(tgt, 'enchant_bonus', 0) or 0) + 1
            tgt._smith_bonus = int(getattr(tgt, '_smith_bonus', 0) or 0) + 1
            what = "an edge you could shave with" if sid == 'sharpen' else "fresh rivets and a better fit"
            self.add_message(f"{who} gives your {self._bare_name(tgt)} {what}.", 'success')
            return True
        if sid == 'cut_curse':
            item = target
            slot = self._lore_equipped_slot(item)
            if slot is None:
                return False
            name = self._bare_name(item)
            item.buc = 'uncursed'                     # cut loose; it does not survive it
            self._unequip_slot(slot, item)
            if self._lore_equipped_slot(item) is not None:
                item.buc = 'cursed'                   # it would not come off: nothing done
                return False
            if item in p.inventory:
                p.inventory.remove(item)
            self.add_message(f"{who} cuts the {name} off you. It comes away in pieces "
                             "and the pieces are not worth keeping.", 'success')
            return True
        if sid == 'cure':
            cured = [e for e in CURABLE if int(p.status_effects.get(e, 0) or 0) > 0]
            if not cured:
                return False
            for e in cured:
                p.status_effects.pop(e, None)
            self.add_message(f"{who} doses you with something foul. You feel much better.", 'success')
            return True
        if sid == 'restore':
            n = 0
            s = int(getattr(p, '_str_lost_to_disease', 0) or 0)
            if s:
                p.apply_stat_bonus('STR', s)
                p._str_lost_to_disease = 0
                n += s
            for stat, v in list((p.__dict__.get('drained') or {}).items()):
                if int(v or 0) > 0:
                    p.apply_stat_bonus(stat, int(v))
                    n += int(v)
            p.__dict__['drained'] = {}
            if not n:
                return False
            self.add_message(f"{who} works on you for an hour. What the dark took, "
                             f"you have back. ({n} stat point{'s' if n != 1 else ''} restored.)", 'success')
            return True
        if sid == 'heal':
            if p.hp >= p.max_hp:
                return False
            p.hp = p.max_hp
            self.add_message(f"{who} cleans and binds your wounds. You are whole.", 'success')
            return True
        if sid == 'id_retry':
            item = target
            if item not in p.inventory:
                return False
            self.add_message(f"{who} sits at your elbow while you study the "
                             f"{self._bare_name(item)}. Get it wrong and nothing bites.", 'info')
            self.state = STATE_PLAYER
            self._identify_item(item, backlash=False)
            return True
        if sid == 'map':
            d = self.dungeon
            for y in range(d.height):
                for x in range(d.width):
                    d.explored.add((x, y))
            self.add_message(f"{who} inks you a map of this floor. Every room, every turn.", 'success')
            return True
        if sid == 'porter':
            p.add_floor_effect('porter', economy.PORTER_FLOORS)
            self.add_message(f"{who} lends you a porter for the next {economy.PORTER_FLOORS} "
                             "floors. Your pack is lighter.", 'success')
            return True
        return False

    # ---------------------------------------------------------------- the menu

    def _trader_menu(self) -> dict:
        """The shop as ``_draw_decision_menu`` arguments: the tab strip
        (Buy / Sell / Services; the kit's tab_strip_window keeps the active
        one in view), one row per ware, pack item or service, and the detail
        pane for the row under the cursor."""
        from fantasy_ui import FP
        m = self._shop_merchant
        tabs = self._trader_tabs()
        tab = min(getattr(self, '_shop_tab', TAB_BUY), len(tabs) - 1)
        gold = int(getattr(self, 'player_gold', 0) or 0)
        pick = getattr(self, '_shop_pick', None)
        entries = []
        if pick:
            sid = pick[0]
            for t in pick[1]:
                is_item = hasattr(t, 'item_class')
                entries.append({'name': self._display_name(t) if is_item else str(t),
                                'detail': f"{self._service_price(sid):,} gold",
                                'icon': t if is_item else None,
                                'details': [(self._service_name(sid), FP.GOLD_BRIGHT, self.font_md),
                                            ("Press Enter to choose this one.", FP.FADED_TEXT,
                                             self.font_sm)]})
            hint = "Up/Down: choose   Enter: this one   ESC: back"
        elif tab == TAB_BUY:
            haggled = getattr(self, '_shop_haggled', set())
            credit = self._trader_credit_value()
            for i, item in enumerate(m.stock):
                price = self._trader_price(i)
                pay = max(0, price - credit)
                plan = self._payment_plan(pay)
                affordable = plan is not None
                is_gem = getattr(item, 'item_class', '') == 'treasure'
                detail = f"{price:,} gold   Weight {getattr(item, 'weight', 0):g}"
                if i in haggled:
                    detail += "   Haggled"
                item_lines = self._menu_item_detail_lines(
                    item, "Press Enter to buy this item if you can afford it.")
                details = item_lines[:1] + [
                    (f"Price: {price:,} gold (you have {gold:,} in coin)",
                     FP.GOLD_PALE if affordable else FP.DANGER_TEXT_LIGHT, self.font_sm)]
                if plan is not None and plan.get('take'):
                    details.append((self._trader_pay_words(plan), FP.GOLD_PALE, self.font_sm))
                elif plan is None and gold < pay:
                    details.append(("Not enough in coin and treasure together.",
                                    FP.DANGER_TEXT_LIGHT, self.font_sm))
                if credit:
                    details.append((f"On the house: up to {credit:,} gold of it.",
                                    FP.GOLD_BRIGHT, self.font_sm))
                details += [("Gems are sold at their worth plus a tenth: no haggling." if is_gem
                             else "Already haggled for this item." if i in haggled
                             else "H: try to haggle the price down (once per item).",
                             FP.FADED_TEXT, self.font_sm), ''] + item_lines[1:]
                entries.append({'name': self._display_name(item), 'detail': detail, 'icon': item,
                                'name_color': FP.BODY_TEXT if affordable else FP.FADED_TEXT,
                                'detail_color': FP.GOLD_PALE if affordable else FP.DANGER_TEXT_LIGHT,
                                'details': details})
            hint = "Left/Right: tab   Up/Down: inspect   Enter: buy   H: haggle   ESC: close"
        elif tab == TAB_SELL:
            from items import Ammo
            for item in self.player.inventory:
                offer, why = self._trader_offer(item)
                n = int(getattr(item, 'count', 1) or 1)
                each = '' if (n <= 1 or isinstance(item, Ammo)) else ' each'
                detail = f"Offers {offer:,} gold{each}" if not why else why
                item_lines = self._menu_item_detail_lines(item, "Press Enter to sell.")
                details = item_lines[:1] + [
                    ((f"{m.person} offers {offer:,} gold{each}." if not why
                      else f"{m.person} won't buy it: {why.lower()}."),
                     FP.GOLD_PALE if not why else FP.FADED_TEXT, self.font_sm),
                    (f"His purse: {int(m.purse):,} gold.", FP.FADED_TEXT, self.font_sm),
                    ''] + item_lines[1:]
                if not why and getattr(item, 'item_class', '') == 'treasure':
                    import treasure as _tr
                    full = _tr.credit(item)
                    if offer < full:
                        details.insert(3, (f"Worth {full:,} to him, but his purse is short. "
                                           f"Paying with it instead loses nothing.",
                                           FP.WARNING_TEXT, self.font_sm))
                    elif _tr.coin_weight(offer) >= 1:
                        details.insert(3, (f"{offer:,} gold weighs {_tr.weight_text(offer)}. "
                                           f"Coin you cannot carry he pays in gems.",
                                           FP.FADED_TEXT, self.font_sm))
                entries.append({'name': self._display_name(item), 'detail': detail, 'icon': item,
                                'name_color': FP.BODY_TEXT if not why else FP.FADED_TEXT,
                                'detail_color': FP.GOLD_PALE if not why else FP.FADED_TEXT,
                                'details': details})
            hint = "Left/Right: tab   Up/Down: inspect   Enter: sell one   ESC: close"
        else:
            sdata = traders.data().get('services') or {}
            for sid in getattr(m, 'services', ()):
                targets = self._service_targets(sid)
                price = self._service_price(sid)
                can_pay = self._payment_plan(price) is not None      # coin, then treasure
                ready = bool(targets) and can_pay
                entries.append({
                    'name': self._service_name(sid),
                    'detail': f"{price:,} gold" + ('' if targets else "   Nothing to do"),
                    'icon': None,
                    'name_color': FP.BODY_TEXT if ready else FP.FADED_TEXT,
                    'detail_color': FP.GOLD_PALE if ready else FP.FADED_TEXT,
                    'details': [(self._service_name(sid), FP.GOLD_BRIGHT, self.font_md),
                                (f"Price: {price:,} gold (you have {gold:,})",
                                 FP.GOLD_PALE if can_pay else FP.DANGER_TEXT_LIGHT, self.font_sm),
                                '',
                                ((sdata.get(sid) or {}).get('desc', ''), FP.BODY_TEXT, self.font_sm),
                                '',
                                ("Nothing for this to work on right now." if not targets
                                 else "Press Enter to pay for it.", FP.FADED_TEXT, self.font_sm)],
                })
            hint = "Left/Right: tab   Up/Down: inspect   Enter: pay   ESC: close"
        counts = [len(m.stock), len(self.player.inventory),
                  len(getattr(m, 'services', ()))][:len(tabs)]
        selected = self._menu_clamp_selection('_shop_selection', len(entries))
        import treasure
        from treasure import weight_text
        tre = sum(treasure.known_unit_value(self.player, t) * max(1, int(getattr(t, 'count', 1) or 1))
                  for t in treasure.carried(self.player))
        ctx = [
            (m.title.upper(), FP.GOLD_BRIGHT, self.font_sm),
            (f"Your gold: {gold:,} ({weight_text(gold)})", FP.GOLD_PALE, self.font_sm),
        ]
        if tre:
            ctx.append((f"Your treasure: {tre:,}", FP.GOLD_PALE, self.font_sm))
        ctx.append((f"His purse: {int(m.purse):,}", FP.BODY_TEXT, self.font_sm))
        context = self._menu_base_context(ctx)
        self._menu_more_cue = "The full lore is yours to read once you buy it."
        title = (f"{m.person}, {m.title}" if getattr(m, 'person', '') else m.name).upper()
        return dict(title=title, entries=entries, selected=selected, context_lines=context,
                    hint=hint, border_color=FP.GOLD, tabs=list(tabs), active_tab=tab,
                    tab_counts=counts, scroll_attr='_shop_scroll')

    def _service_name(self, sid: str) -> str:
        return ((traders.data().get('services') or {}).get(sid) or {}).get(
            'name', sid.replace('_', ' ').title())
