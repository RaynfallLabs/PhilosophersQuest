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

The dungeon supports the build (winning build 3.5, 2026-11-13): a stall's
counter for what walks below and the trader's line about it
(domain_counters.py); the smiths' reforge, silvering and cold-iron inlay,
the armourers' lining and special order (smithing.py); and the trade-in,
every trader's: on a visit when the hero buys, what he sells that trader
fetches half the trader's price, up to what he spends (a visit is his stay
on the floor: ``_traders_leaving`` closes it).
"""
from __future__ import annotations

import pygame

import economy
import smithing
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
                       (getattr(self, '_black_knight', None) or {}).get('floor'),
                       (getattr(self, '_bococho', None) or {}).get('floor')]
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
        for o in plan.get('orders') or ():
            if o.get('kind') == kind and self._order_due(o, level):
                self.add_message(f"{m.person}'s stall stands on this floor. Your {o.get('name', 'order')} "
                                 f"is waiting for you there.", 'info')
        return m

    def _traders_leaving(self, level: int):
        """The hero leaves floor ``level`` (main._change_level): a trader's
        visit ends (the trade-in tally), and an order placed here that has no
        stall below to be collected at is paid back."""
        from mystery_system import MerchantNPC
        for gi in getattr(self, 'ground_items', None) or ():
            if isinstance(gi, MerchantNPC):
                gi.visit = None
        plan = traders.ensure_plan(self.__dict__.get('_traders'))
        if not plan:
            return
        for o in list(plan.get('orders') or ()):
            if int(o.get('placed', -1)) != int(level):
                continue
            collect = o.get('collect')
            if collect is not None and plan['floors'].get(int(collect)) == o.get('kind'):
                continue
            plan['orders'].remove(o)
            paid = int(o.get('paid', 0) or 0)
            line = (traders.kind_def(o.get('kind', '')).get('lines') or {}).get(
                'order_refund', "No stall of mine below. Have your coin back.")
            self.add_message(f'{o.get("person", "The smith")}: "{line}" ({paid:,} gold back.)', 'info')
            if paid:
                self._gain_gold(paid, paid=True, who=o.get('person'))

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
        # A wary creature's own room is his (Old Nickel's hoard: he wears the
        # Bloomleaf Cloak, monster.py _stalker_turn). A stall in it would make
        # the hero corner him, and start the fight, just to trade.
        homes = [h for mo in self.monsters
                 if getattr(mo, 'alive', True) and (h := getattr(mo, '_wary_home', None))]
        # Nor in a war-band's camp (war_bands.camp_tiles): a stall among a
        # sleeping gang of footpads meant fighting the band to trade.
        import war_bands
        camp = war_bands.camp_tiles(d)

        def ok(x, y):
            return (d.tiles[y][x] == FLOOR and (x, y) in reach and (x, y) not in taken
                    and (x, y) not in crowd and (x, y) not in camp
                    and max(abs(x - px), abs(y - py)) >= 3
                    and not any(h[0] <= x <= h[2] and h[1] <= y <= h[3] for h in homes))
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
        # His services are his kind's: a trader from an older save learns the
        # new ones (reforge, lining, trade-in...).
        kd = traders.kind_def(getattr(merchant, 'kind', 'generalist'))
        if 'services' in kd:
            merchant.services = tuple(kd.get('services') or ())
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
            # What's below, in his own voice (domain_counters.py).
            import domain_counters
            tmpl = (merchant.lines or {}).get('counter') or (kd.get('lines') or {}).get('counter')
            said = domain_counters.counter_line(tmpl, getattr(merchant, 'counter', None))
            if said:
                self.add_message(f'{merchant.person}: "{said}"', 'info')
        self._trader_deliver_orders(merchant)
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
            self.add_message(f"{merchant.person} weighs your treasure in {merchant.pronouns()[2]} palm "
                             f"and names a price "
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
            bits += f"; {give:,} gold back" + ("" if give >= ch else
                                               f" ({m.pronouns()[2]} purse is short {ch - give:,})")
        return f"Pays with {bits}."

    def _trader_credit_value(self) -> int:
        if not getattr(self, '_shop_credit', False):
            return 0
        share = float((traders.data().get('guild') or {}).get('credit_share', 1.0))
        return economy.share(self.dungeon_level, share)

    # ---------------------------------------------------------------- the trade-in

    def _trader_visit(self, m=None) -> dict:
        """This visit's trade-in tally on trader ``m``: gold spent with him
        (wares, and since 2026-11-14 his services and special orders),
        trade-in already paid, and trade-in owed for things sold before a
        purchase (paid when he pays)."""
        m = m or self._shop_merchant
        v = getattr(m, 'visit', None)
        if not isinstance(v, dict):
            v = {'spent': 0, 'given': 0, 'pending': 0}
            m.visit = v
        return v

    def _trader_count_spent(self, m, amount: int) -> None:
        """Gold the hero just paid trader ``m`` for wares or work counts
        toward this visit's trade-in (Brandon's Q13, 2026-11-14: simulated,
        tools/balance/difficulty_sim.py knob tradein; a smith's work counting
        too moved no win rate, so the simpler rule won), and anything sold
        him earlier this visit is topped up to the trade-in rate now."""
        if int(amount or 0) <= 0:
            return
        v = self._trader_visit(m)
        v['spent'] = int(v['spent']) + int(amount)
        self._trader_top_up(m)

    def _trade_in_room(self, m=None) -> int:
        v = self._trader_visit(m)
        return max(0, int(v['spent']) - int(v['given']))

    def _trade_in_extra(self, item, offer: int) -> int:
        """What selling ``item`` now fetches above ``offer`` as a trade-in:
        half his price instead of a fifth, up to what is left of what the
        hero has spent with him this visit."""
        if getattr(item, 'item_class', '') == 'treasure':
            return 0
        return max(0, min(self._trade_in_gap(item, offer), self._trade_in_room()))

    def _trade_in_gap(self, item, offer: int) -> int:
        """Half his price less the plain offer (the resale cap and his purse
        hold): what a trade-in is worth on ``item``."""
        from items import is_fully_known
        m = self._shop_merchant
        known = self._item_is_known(item)
        full = economy.sell_offer(item, self.dungeon_level, known=known,
                                  identified=is_fully_known(item, self.player),
                                  markup=m.markup, purse=m.purse, trade_in=True)
        return max(0, int(full) - int(offer))

    def _trader_top_up(self, m):
        """After a purchase: what he owes for things sold earlier this visit
        as a trade-in, paid now (up to what was spent and his purse)."""
        v = self._trader_visit(m)
        due = min(int(v['pending']), self._trade_in_room(m), int(getattr(m, 'purse', 0) or 0))
        if due <= 0:
            return
        v['pending'] = int(v['pending']) - due
        v['given'] = int(v['given']) + due
        m.purse = max(0, int(m.purse) - due)
        self.add_message(f"{m.person} counts what you sold {m.pronouns()[1]} earlier as a trade-in: "
                         f"{due:,} gold more.", 'success')
        self._gain_gold(due, paid=True, who=m.person)

    def _trader_offer(self, item) -> tuple:
        """(offer, refusal) for selling ``item`` to the open trader."""
        from player import _buc_known_to_player
        from items import is_fully_known
        m = self._shop_merchant
        known = self._item_is_known(item)
        cursed_known = (getattr(item, 'buc', '') == 'cursed'
                        and _buc_known_to_player(item, self.player))
        why = traders.refusal({'buys': m.buys, 'buys_cursed': m.buys_cursed,
                               'pronoun': m.pronouns()[0]}, item,
                              known=known, cursed_known=cursed_known,
                              quest_ids=self._QUEST_PIECE_IDS)
        if why:
            return 0, why
        # Fully identified: this copy, or its kind known (one identification
        # knows every copy, blessing included).
        ident = is_fully_known(item, self.player)
        offer = economy.sell_offer(item, self.dungeon_level, known=known, identified=ident,
                                   markup=m.markup, purse=m.purse)
        if offer <= 0:
            _subj, obj, poss = m.pronouns()
            return 0, (f"{poss.capitalize()} purse is empty" if m.purse <= 0
                       else f"Worthless to {obj}")
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
        # Said after "You buy ...": it is bought, then set down (bug bash
        # WB-E06: it was set down before it was bought).
        too_heavy = ''
        if self.player.add_to_inventory(item) is False:
            item.x, item.y = self.player.x, self.player.y
            self.ground_items.append(item)
            too_heavy = (f"It is too heavy to carry with everything else, so {m.person} "
                         f"sets it down at your feet.")
            # Bought all the same: unmarked, it escaped the resale cap and
            # sold deeper down for four times what it cost.
            if getattr(item, 'item_class', '') != 'treasure':
                self._trader_mark_bought(item, before, price)
        elif getattr(item, 'item_class', '') != 'treasure':
            self._trader_mark_bought(item, before, price)
            self._mastery_identify_carried(only=item)      # philosophy tier mastery
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
        if too_heavy:
            self.add_message(too_heavy, 'warning')
        self._seeker_event('trade', trader=getattr(m, 'person', None) or getattr(m, 'kind', None))
        line = m.line('bought')
        if line:
            self.add_message(f'{m.person}: "{line}"', 'info')
        item.__dict__.pop('_counter', None)            # the shelf's mark, not the item's
        if getattr(item, 'item_class', '') != 'treasure':
            self._trader_count_spent(m, int(pay))
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
        # Arrows sell by the bundle (economy.ammo_bundles): what was paid is
        # kept as the price of one bundle, so the cap follows the count.
        bundles = economy.ammo_bundles(item)
        if bundles:
            price = round(price / bundles, 2)
        old = getattr(target, '_bought_for', None)
        target._bought_for = price if old is None else min(float(old), price)

    # ---------------------------------------------------------------- sell

    def _trader_sell(self, item, confirmed: bool = False):
        m = self._shop_merchant
        offer, why = self._trader_offer(item)
        if why:
            key = 'purse_empty' if why.endswith("purse is empty") else 'refuse'
            self.add_message(f'{m.person}: "{m.line(key, "No.")}" ({why}.)', 'warning')
            return
        # A boss's trophy sold is its feast lost (Fenrir's Tooth went for 60
        # gold with no word): ask first, and come back to the shop (UI-4).
        if not confirmed:
            def _back():
                self.state = STATE_SHOP

            def _sell(_i=item):
                self.state = STATE_SHOP
                self._trader_sell(_i, confirmed=True)
            if self._ask_before_trophy_goes(
                    item, "Sell the {} to " + str(m.person) + "?", "Sell It",
                    f"{offer:,} gold; its dish is lost.", _sell, _back):
                return
        # The trade-in: half his price on a visit when the hero pays him (for
        # wares or work), up to what was paid; sold before that, the
        # difference is owed and paid when the hero pays (_trader_top_up).
        extra = self._trade_in_extra(item, offer)
        gap = self._trade_in_gap(item, offer) if getattr(item, 'item_class', '') != 'treasure' else 0
        v = self._trader_visit(m)
        v['given'] = int(v['given']) + extra
        v['pending'] = int(v['pending']) + max(0, gap - extra)
        offer += extra
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
            # Sold: the back and the kits let go of it for good (loadouts.py).
            self._sets_let_go(item)
        else:
            self.player.remove_from_inventory(item)
        m.purse = max(0, int(m.purse) - offer)
        self.add_message(f"You sell {name} to {m.person} for {offer:,} gold"
                         + (f", {extra:,} of it as a trade-in." if extra else "."), 'success')
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

    def _shield_worn(self) -> bool:
        return getattr(self.player, 'shield', None) is not None

    def _service_targets(self, sid: str) -> list:
        """What a service could work on now (empty: nothing to do)."""
        p = self.player
        if sid in ('reforge', 'silvering', 'cold_iron_inlay') and not self._smith_knows_blade():
            return []
        if sid == 'reforge':
            return smithing.reforge_targets(p.weapon, self._shield_worn())
        if sid in ('silvering', 'cold_iron_inlay'):
            sub = 'silver' if sid == 'silvering' else 'cold_iron'
            return [p.weapon] if smithing.can_inlay(p.weapon, sub) else []
        if sid == 'lining':
            return smithing.lining_targets(p)
        if sid == 'special_order':
            m = getattr(self, '_shop_merchant', None)
            plan = self._trader_plan()
            if m is None or traders.next_stall(plan, m.kind, self.dungeon_level) is None:
                return []
            if self._open_order(m.kind):
                return []
            return smithing.order_materials(self.dungeon_level)
        if sid == 'trade_in':
            return ['trade_in']
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
            import gear
            if body is not None and int(getattr(body, '_smith_bonus', 0) or 0) < economy.SMITH_ENCHANT_CAP \
                    and (not gear.is_core(body)
                         or int(getattr(body, 'enchant_bonus', 0) or 0) < gear.enchant_cap_for(body)):
                return [body]           # (no smith adds plus past what the material holds)
            return []
        if sid == 'cut_curse':
            from player import _buc_known_to_player
            return [i for i in p.worn_items()
                    if getattr(i, 'buc', '') == 'cursed' and _buc_known_to_player(i, p)
                    and not getattr(i, 'bound_to_wielder', False)
                    and getattr(i, 'id', None) not in self._QUEST_PIECE_IDS]
        if sid == 'cure':
            return [e for e in CURABLE if int(p.status_effects.get(e, 0) or 0) > 0]
        if sid == 'restore':
            return ['restore'] if self._drained_total() > 0 else []
        if sid == 'heal':
            return ['heal'] if p.hp < p.max_hp else []
        if sid == 'id_retry':
            from items import is_fully_known
            return [i for i in p.inventory if hasattr(i, 'id_level')
                    and not is_fully_known(i, p)
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
        # Life the dead drained (src/life_drain.py), as points of 3 health.
        import life_drain
        n += (life_drain.drained(p) + 2) // 3
        return n

    def _open_order(self, kind: str):
        """This armourer's order not yet collected, or None."""
        plan = self._trader_plan()
        return next((o for o in plan.get('orders') or () if o.get('kind') == kind), None)

    def _smith_knows_blade(self) -> bool:
        """A smith works only a blade the hero can name (bug bash 2026-11-13,
        WB-D, the smith's tab): his refusals ("It is that metal already", "a
        named blade") gave an unidentified weapon's metal and make away for
        free, at every armourer. Have it named first."""
        import kit_sense
        return kit_sense.knows_weapon(self.player, self.player.weapon)

    def _service_why(self, sid: str) -> str:
        """Why a new service has nothing to work on now, in plain words."""
        p = self.player
        w = p.weapon
        m = self._shop_merchant
        if sid in ('reforge', 'silvering', 'cold_iron_inlay'):
            if w is None:
                return "You hold no weapon."
            if not self._smith_knows_blade():
                return (f"{m.pronouns()[0].capitalize()} turns your blade over and hands it back: "
                        "\"I don't work a blade I can't name. Have it known first.\"")
            if getattr(w, 'is_unique', False) or getattr(w, 'bound_to_wielder', False):
                return f"{m.pronouns()[0].capitalize()} won't put a hammer to a named blade."
            if sid == 'reforge':
                if getattr(w, 'requires_ammo', None):
                    return "Only a hand weapon can be re-shaped."
                if not smithing.is_common_weapon(w):
                    return "That weapon is not common work."
                return "No other shape will take its metal."
            sub = smithing.inlay_of(w)
            if sub:
                return f"Your {self._bare_name(w)} is inlaid with {smithing.inlay_name(sub)} already: one inlay to a weapon."
            return "It is that metal already."
        # In the trader's own pronouns: Brunhild is "she" (bug bash WB-C04).
        _subj, obj, poss = m.pronouns()
        if sid == 'lining':
            from items import ARMOR_SLOTS
            worn = [p.armor_slots[ARMOR_SLOTS.index(s)] for s in smithing.LINING_SLOTS]
            if not any(worn):
                return f"Wear a cloak or a shirt for {obj} to line."
            return "What you wear is lined already: one lining to a piece."
        if sid == 'special_order':
            o = self._open_order(m.kind)
            if o:
                return f"Your {o.get('name', 'order')} waits at {poss} stall on floor {o.get('collect')}."
            return f"This is {poss} last stall: there is nowhere below to collect an order."
        return "Nothing for this to work on right now."

    def _order_price(self, item) -> int:
        """A special order: the piece's own price and the making."""
        m = self._shop_merchant
        lvl = self.dungeon_level
        base = (economy.merchant_price(item, lvl, m.markup)
                + economy.service_price('special_order', lvl, markup=m.markup))
        return max(5, economy.nice(base * float(getattr(self, '_shop_mult', 1.0) or 1.0)))

    def _service_price(self, sid: str) -> int:
        m = self._shop_merchant
        if economy.SERVICE_SHARE.get(sid, 0.3) <= 0:
            return 0                                   # the trade-in: no fee
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
        if sid == 'trade_in':
            self._shop_tab = TAB_SELL
            self._shop_selection = 0
            room = self._trade_in_room(m)
            self.add_message("Trade-in: " + (f"{room:,} gold of what you sell now fetches half "
                                             f"{m.pronouns()[2]} price." if room else
                                             f"buy from {m.pronouns()[1]} or pay for "
                                             f"{m.pronouns()[2]} work first, and what you sell "
                                             f"{m.pronouns()[1]} this visit fetches half "
                                             f"{m.pronouns()[2]} price."), 'info')
            return
        if sid == 'special_order':
            self._shop_pick = (sid, targets)
            self._shop_selection = 0
            return
        price = self._service_price(sid)
        if self._payment_plan(price) is None:
            self.add_message(f'{m.person}: "{m.line("broke", "No coin, no deal.")}" '
                             f'({price:,} gold needed.)', 'warning')
            return
        if sid == 'reforge':
            self._shop_pick = (sid, [smithing.preview(self.player.weapon, t) for t in targets])
            self._shop_selection = 0
            return
        if sid == 'lining' or (sid in ('cut_curse', 'id_retry') and len(targets) > 1):
            self._shop_pick = (sid, targets)
            self._shop_selection = 0
            return
        self._trader_service_on(sid, targets[0])

    def _trader_service_on(self, sid: str, target):
        """Pay for and render one service."""
        m = self._shop_merchant
        if sid == 'special_order':
            # The metal is chosen: now the shape, each with its own price.
            cat, mid = target
            made = [smithing.make_order(cat, t, mid) for t in smithing.order_templates(cat, mid)]
            self._shop_pick = ('special_order:pick', [it for it in made if it is not None])
            self._shop_selection = 0
            return
        if sid == 'special_order:pick':
            self._trader_place_order(target)
            return
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
        self._seeker_event('smith', service=sid)
        paid = self._pay_gold(price, change_purse=int(m.purse), who=m.person, quiet=True)
        if paid:
            m.purse = max(0, int(m.purse) - int(paid.get('change_given', 0) or 0))
            self._trader_count_spent(m, int(price))
            if paid.get('take'):
                self.add_message(f"(You pay {self._payment_words(paid)}"
                                 + (f"; {int(paid['change_given']):,} gold back.)"
                                    if paid.get('change_given') else ".)"), 'info')
            else:
                self.add_message(f"({price:,} gold.)", 'info')

    def _trader_place_order(self, item):
        """Pay for a special order and write it down (collected at his next
        stall: _trader_deliver_orders)."""
        m = self._shop_merchant
        plan = self._trader_plan()
        nxt = traders.next_stall(plan, m.kind, self.dungeon_level)
        if nxt is None or self._open_order(m.kind):
            self._shop_pick = None
            return
        price = self._order_price(item)
        if self._payment_plan(price) is None:
            self.add_message(f'{m.person}: "{m.line("broke", "No coin, no deal.")}" '
                             f'({price:,} gold needed.)', 'warning')
            return
        paid = self._pay_gold(price, change_purse=int(m.purse), who=m.person, quiet=True)
        if not paid:
            return
        m.purse = max(0, int(m.purse) - int(paid.get('change_given', 0) or 0))
        self._trader_count_spent(m, int(price))
        self._shop_pick = None
        self._shop_selection = 0
        name = self._bare_name(item)
        plan['orders'].append({
            'kind': m.kind, 'person': m.person, 'placed': int(self.dungeon_level),
            'collect': int(nxt), 'cat': str(getattr(item, 'item_class', 'weapon')),
            'template': smithing.template_of(item), 'material': str(item.material),
            'name': name, 'paid': int(price),
            'piece': int(economy.merchant_price(item, self.dungeon_level, m.markup))})
        line = m.line('order_placed', "{item}. It'll be ready at my stall on floor {floor}.")
        try:
            line = line.format(item=name, floor=nxt)
        except (KeyError, IndexError, ValueError):
            pass
        self.add_message(f'{m.person}: "{line}" ({price:,} gold, paid.)', 'success')
        self._chron('deed', f"Ordered a piece of smith's work from {m.person}, to be "
                            f"collected at {m.pronouns()[2]} next stall, further down.")

    @staticmethod
    def _order_due(o: dict, level: int) -> bool:
        """Is order ``o`` ready at a stall of its smith on floor ``level``? At
        the stall it was made for, or any of his deeper down: a hero who
        never met that stall (a trapdoor past its floor, a stall with no room
        to stand) found the smith below with nothing for him, and the order
        stayed open for good, paid for, blocking every new one (bug bash
        WB-D07)."""
        try:
            return o.get('collect') is not None and int(o['collect']) <= int(level)
        except (TypeError, ValueError):
            return False

    def _trader_deliver_orders(self, m):
        """Hand over the special orders this armourer has ready here (at the
        stall it was made for, or a later one of his: _order_due)."""
        plan = self._trader_plan()
        for o in list(plan.get('orders') or ()):
            if o.get('kind') != getattr(m, 'kind', None) or not self._order_due(o, self.dungeon_level):
                continue
            plan['orders'].remove(o)
            it = smithing.make_order(o.get('cat', 'weapon'), o.get('template'), o.get('material'))
            if it is None:
                paid = int(o.get('paid', 0) or 0)
                self.add_message(f'{m.person}: "{m.line("order_refund", "Have your coin back.")}"', 'info')
                if paid:
                    self._gain_gold(paid, paid=True, who=m.person)
                continue
            it._bought_for = int(o.get('piece', o.get('paid', 0)) or 0)    # the resale cap
            line = m.line('order_ready', "Your {item}, as ordered.")
            try:
                line = line.format(item=o.get('name', self._bare_name(it)))
            except (KeyError, IndexError, ValueError):
                pass
            self.add_message(f'{m.person}: "{line}"', 'success')
            if self.player.add_to_inventory(it) is False:
                it.x, it.y = self.player.x, self.player.y
                self.ground_items.append(it)
                self.add_message(f"It is too heavy to carry with everything else, so {m.person} "
                                 f"sets it down at your feet.", 'warning')
            self._seeker_event('smith', service='order_collected')   # Made to Order

    def _render_service(self, sid: str, target, who: str = 'The smith') -> bool:
        """Do the service (shared with encounter vendors: a 'service' reward).
        True when something was done."""
        p = self.player
        if sid == 'reforge':
            w = p.weapon
            tid = smithing.template_of(target) if hasattr(target, 'item_class') else target
            if tid not in smithing.reforge_targets(w, self._shield_worn()):
                return False
            old = self._bare_name(w)
            # What he knew of it he still knows: the smith changed its shape
            # in front of him, not its metal, plus or blessing. A blade he
            # knew only by its kind (an iron longsword) came back an unknown
            # "Plain Mace" when he did not know iron maces (bug bash WB-D03).
            from items import buc_known_to, is_fully_known, make_fully_known
            knew, knew_buc = is_fully_known(w, p), buc_known_to(w, p)
            smithing.reforge(w, tid)
            if knew:
                make_fully_known(w)
            elif knew_buc:
                w.buc_known = True
            from paths import a_or_an
            self.add_message(f"{who} heats your {old} white and beats it into "
                             f"{a_or_an(self._bare_name(w))}. The metal is the same, and so is "
                             f"everything you paid to put into it.", 'success')
            return True
        if sid in ('silvering', 'cold_iron_inlay'):
            sub = 'silver' if sid == 'silvering' else 'cold_iron'
            w = p.weapon
            old = self._bare_name(w) if w is not None else ''
            if not smithing.inlay(w, sub):
                return False
            done = ((traders.data().get('inlays') or {}).get(sub) or {}).get(
                'done', "{who} works it into your {name}.")
            self.add_message(done.format(who=who, name=old), 'success')
            return True
        if sid == 'lining':
            piece, element = target
            name = self._bare_name(piece)
            if not smithing.line(piece, element):
                return False
            stuff = smithing.lining_words(element).get('stuff', element)
            self.add_message(f"{who} lines your {name} with {stuff}. {element.title()} will "
                             f"find it harder going.", 'success')
            return True
        if sid == 'repair':
            pieces = self._service_targets('repair')
            if not pieces:
                return False
            import gear
            from items import set_ench_level
            for it in pieces:
                if getattr(it, 'item_class', '') == 'armor' and not gear.is_core(it):
                    # A minor piece's wear took levels, not plus (items.wear_down).
                    set_ench_level(it, int(getattr(it, 'ench_level', 0) or 0) + int(it.wear_loss))
                else:
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
            # The smith cuts it off: one turn, not the piece's unbuckling
            # time (game_dressing._dress_start_off).
            if self._take_off_now(slot, item):
                self._advance_turn()
            if self._lore_equipped_slot(item) is not None:
                item.buc = 'cursed'                   # it would not come off: nothing done
                return False
            if item in p.inventory:
                p.inventory.remove(item)
            self._sets_let_go(item)                   # in pieces: gone for good
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
            from status_effects import restore_drained
            n = restore_drained(p)
            # ...and the life the dead drained (life_drain.py, AI-1), which
            # restore_drained gives back with the stats.
            life = int(p.__dict__.pop('_last_life_restored', 0) or 0)
            if not n and not life:
                return False
            got = []
            if n:
                got.append(f"{n} stat point{'s' if n != 1 else ''} restored")
            if life:
                got.append(f"Max HP +{life}")
            self.add_message(f"{who} works on you for an hour. What the dark took, "
                             f"you have back. ({', '.join(got)}.)", 'success')
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
            name = self._bare_name(item)
            self.state = STATE_PLAYER
            self._identify_item(item, backlash=False)
            # Paid only when a question is up for him to sit in on. The Cloak
            # of Odin's free identify (spent inside _identify_item, as on any
            # identify) or a mastered tier answers with no question, and the
            # fee used to be taken all the same.
            qe = self.quiz_engine
            if not qe.active or getattr(qe, 'auto_passed', 0):
                self.add_message(f"{who} had nothing to add, and takes no fee.", 'info')
                return False
            self.add_message(f"{who} sits at your elbow while you study the "
                             f"{name}. Get it wrong and nothing bites.", 'info')
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
                entries.append(self._trader_pick_entry(sid, t))
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
                if getattr(item, '_counter', None):
                    # A stall's counter (domain_counters.py): what it is for
                    # shows on it, so saying so tells nothing hidden.
                    details.insert(2, (f"{m.person} set this out for what is below: "
                                       f"{item._counter}.", FP.SUCCESS_TEXT, self.font_sm))
                entries.append({'name': self._display_name(item), 'detail': detail, 'icon': item,
                                'name_color': FP.BODY_TEXT if affordable else FP.FADED_TEXT,
                                'detail_color': FP.GOLD_PALE if affordable else FP.DANGER_TEXT_LIGHT,
                                'details': details})
            hint = "Left/Right: tab   Up/Down: inspect   Enter: buy   H: haggle   ESC: close"
        elif tab == TAB_SELL:
            from items import Ammo
            for item in self.player.inventory:
                offer, why = self._trader_offer(item)
                # The trade-in: half his price on a visit when the hero has
                # paid him (one of a stack: each sale is one).
                extra = self._trade_in_extra(item, offer) if not why else 0
                gap = (self._trade_in_gap(item, offer)
                       if not why and getattr(item, 'item_class', '') != 'treasure' else 0)
                offer += extra
                n = int(getattr(item, 'count', 1) or 1)
                each = '' if (n <= 1 or isinstance(item, Ammo)) else ' each'
                detail = f"Offers {offer:,} gold{each}" if not why else why
                item_lines = self._menu_item_detail_lines(item, "Press Enter to sell.")
                details = item_lines[:1] + [
                    ((f"{m.person} offers {offer:,} gold{each}." if not why
                      else f"{m.person} won't buy it: {why.lower()}."),
                     FP.GOLD_PALE if not why else FP.FADED_TEXT, self.font_sm),
                    (f"{m.pronouns()[2].capitalize()} purse: {int(m.purse):,} gold.",
                     FP.FADED_TEXT, self.font_sm),
                    ''] + item_lines[1:]
                if extra:
                    details.insert(2, (f"Trade-in: {extra:,} gold of it, because you have paid "
                                       f"{m.pronouns()[1]} on this visit.", FP.SUCCESS_TEXT,
                                       self.font_sm))
                elif gap:
                    details.insert(2, (f"Trade-in: buy from {m.pronouns()[1]} or pay for "
                                       f"{m.pronouns()[2]} work on this visit and this fetches "
                                       f"up to {gap:,} gold more.", FP.FADED_TEXT,
                                       self.font_sm))
                if not why and getattr(item, 'item_class', '') == 'treasure':
                    import treasure as _tr
                    full = _tr.credit(item)
                    if offer < full:
                        details.insert(3, (f"Worth {full:,} to {m.pronouns()[1]}, but "
                                           f"{m.pronouns()[2]} purse is short. "
                                           f"Paying with it instead loses nothing.",
                                           FP.WARNING_TEXT, self.font_sm))
                    elif _tr.coin_weight(offer) >= 1:
                        details.insert(3, (f"{offer:,} gold weighs {_tr.weight_text(offer)}. "
                                           f"Coin you cannot carry {m.pronouns()[0]} pays in gems.",
                                           FP.FADED_TEXT, self.font_sm))
                entries.append({'name': self._display_name(item), 'detail': detail, 'icon': item,
                                'name_color': FP.BODY_TEXT if not why else FP.FADED_TEXT,
                                'detail_color': FP.GOLD_PALE if not why else FP.FADED_TEXT,
                                'details': details})
            hint = "Left/Right: tab   Up/Down: inspect   Enter: sell one   ESC: close"
        else:
            sdata = traders.data().get('services') or {}
            for sid in getattr(m, 'services', ()):
                entries.append(self._trader_service_entry(sid, sdata, gold))
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
        ctx.append((f"{m.pronouns()[2].capitalize()} purse: {int(m.purse):,}", FP.BODY_TEXT, self.font_sm))
        context = self._menu_base_context(ctx)
        self._menu_more_cue = "The full lore is yours to read once you buy it."
        title = (f"{m.person}, {m.title}" if getattr(m, 'person', '') else m.name).upper()
        return dict(title=title, entries=entries, selected=selected, context_lines=context,
                    hint=hint, border_color=FP.GOLD, tabs=list(tabs), active_tab=tab,
                    tab_counts=counts, scroll_attr='_shop_scroll')

    def _service_name(self, sid: str) -> str:
        if sid == 'special_order:pick':
            sid = 'special_order'
        return ((traders.data().get('services') or {}).get(sid) or {}).get(
            'name', sid.replace('_', ' ').title())

    _NEW_SERVICES = ('reforge', 'silvering', 'cold_iron_inlay', 'lining', 'special_order', 'trade_in')

    def _trader_service_entry(self, sid: str, sdata: dict, gold: int) -> dict:
        """One row of the Services tab, and its detail pane."""
        from fantasy_ui import FP
        m = self._shop_merchant
        targets = self._service_targets(sid)
        price = self._service_price(sid)
        can_pay = self._payment_plan(price) is not None      # coin, then treasure
        ready = bool(targets) and can_pay
        plan = self._trader_plan()
        if sid == 'trade_in':
            room = self._trade_in_room(m)
            detail = "No fee"
            price_line = (f"This visit: {room:,} gold of trade-in left." if room else
                          "This visit: buy something or pay for a service first.")
            ready = True
        elif sid == 'special_order':
            fee = economy.service_price('special_order', self.dungeon_level, markup=m.markup)
            fee = economy.nice(fee * float(getattr(self, '_shop_mult', 1.0) or 1.0))
            detail = f"{fee:,} gold + the piece" + ('' if targets else "   Nothing to do")
            price_line = f"Price: the piece, and {fee:,} gold for the making (you have {gold:,})"
            ready = bool(targets)
        else:
            detail = f"{price:,} gold" + ('' if targets else "   Nothing to do")
            price_line = f"Price: {price:,} gold (you have {gold:,})"
        details = [(self._service_name(sid), FP.GOLD_BRIGHT, self.font_md),
                   (price_line, FP.GOLD_PALE if (can_pay or sid in ('trade_in', 'special_order'))
                    else FP.DANGER_TEXT_LIGHT, self.font_sm),
                   '',
                   ((sdata.get(sid) or {}).get('desc', ''), FP.BODY_TEXT, self.font_sm),
                   '']
        if sid == 'special_order':
            nxt = traders.next_stall(plan, m.kind, self.dungeon_level)
            if nxt is not None and targets:
                details.append((f"Collect it at {m.pronouns()[2]} stall on floor {nxt}. Paid now.",
                                FP.GOLD_PALE, self.font_sm))
        if not targets:
            why = (self._service_why(sid) if sid in self._NEW_SERVICES
                   else "Nothing for this to work on right now.")
            details.append((why, FP.FADED_TEXT, self.font_sm))
        elif sid == 'trade_in':
            details.append(("Press Enter to open the Sell tab.", FP.FADED_TEXT, self.font_sm))
        elif sid in ('reforge', 'lining', 'special_order'):
            details.append(("Press Enter to choose.", FP.FADED_TEXT, self.font_sm))
        else:
            details.append(("Press Enter to pay for it.", FP.FADED_TEXT, self.font_sm))
        return {'name': self._service_name(sid), 'detail': detail, 'icon': None,
                'name_color': FP.BODY_TEXT if ready else FP.FADED_TEXT,
                'detail_color': FP.GOLD_PALE if ready else FP.FADED_TEXT,
                'details': details}

    def _trader_pick_entry(self, sid: str, t) -> dict:
        """One row while choosing what a service works on: a reforge's new
        shape, a lining's piece and element, an order's metal or shape."""
        from fantasy_ui import FP
        m = self._shop_merchant
        head = (self._service_name(sid), FP.GOLD_BRIGHT, self.font_md)
        choose = ("Press Enter to choose this one.", FP.FADED_TEXT, self.font_sm)
        if sid == 'special_order' and isinstance(t, tuple):
            cat, mid = t
            line = {'weapon': 'Weapons', 'armor': 'Armour', 'shield': 'Shields'}.get(cat, cat)
            names = [n.replace('_', ' ') for n in smithing.order_templates(cat, mid)]
            return {'name': f"{smithing.material_name(cat, mid)}: {line}",
                    'detail': f"{len(names)} shapes", 'icon': None,
                    'details': [head, (f"{smithing.material_name(cat, mid)} {line.lower()}: "
                                       + ", ".join(names) + ".", FP.BODY_TEXT, self.font_sm),
                                '', ("Press Enter to choose the shape.", FP.FADED_TEXT, self.font_sm)]}
        if sid == 'special_order:pick':
            price = self._order_price(t)
            nxt = traders.next_stall(self._trader_plan(), m.kind, self.dungeon_level)
            ok = self._payment_plan(price) is not None
            return {'name': self._display_name(t), 'detail': f"{price:,} gold", 'icon': t,
                    'name_color': FP.BODY_TEXT if ok else FP.FADED_TEXT,
                    'detail_color': FP.GOLD_PALE if ok else FP.DANGER_TEXT_LIGHT,
                    'details': self._menu_item_detail_lines(t, "Press Enter to order it.")[:1] + [
                        (f"Price: {price:,} gold, paid now.", FP.GOLD_PALE if ok
                         else FP.DANGER_TEXT_LIGHT, self.font_sm),
                        (f"Ready at {m.pronouns()[2]} stall on floor {nxt}.", FP.GOLD_PALE,
                         self.font_sm),
                        '', ("Press Enter to order it.", FP.FADED_TEXT, self.font_sm)]}
        if sid == 'lining' and isinstance(t, tuple):
            piece, element = t
            words = smithing.lining_words(element)
            return {'name': f"{self._bare_name(piece)}: Against {words.get('name', element.title())}",
                    'detail': f"{self._service_price(sid):,} gold", 'icon': piece,
                    'details': [head, (f"Lined with {words.get('stuff', element)}: {element} does "
                                       f"a quarter less harm to you while you wear it.",
                                       FP.BODY_TEXT, self.font_sm), '', choose]}
        if sid == 'reforge' and hasattr(t, 'item_class'):
            forms = ", ".join(f for f in t.damage_types if f in ('slash', 'pierce', 'blunt'))
            hands = "Two hands" if getattr(t, 'two_handed', False) else "One hand"
            return {'name': self._display_name(t), 'detail': f"{self._service_price(sid):,} gold",
                    'icon': t,
                    'details': [head, (f"{hands}. Wounds by {forms or 'its weight'}. "
                                       f"Weight {getattr(t, 'weight', 0):.1f}.", FP.BODY_TEXT,
                                       self.font_sm),
                                ("The metal, the plus, the blessing and the smith's work stay.",
                                 FP.FADED_TEXT, self.font_sm), '', choose]}
        is_item = hasattr(t, 'item_class')
        return {'name': self._display_name(t) if is_item else str(t),
                'detail': f"{self._service_price(sid):,} gold",
                'icon': t if is_item else None,
                'details': [head, choose]}
