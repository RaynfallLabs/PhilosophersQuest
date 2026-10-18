"""The purse on the Game side: coins that weigh something, and paying with
treasure (Brandon's D2, 2026-10-18; the rules are in treasure.py).

* ``_gain_gold``: every gold the hero RECEIVES that is not a pile he picks up
  (a reward, a sale, a grave, a throne, change). He takes only what he can
  carry. What will not fit is set down at his feet as his own pile (a find
  he could not lift); a person who owes him more than he can carry (a trader
  buying, an encounter paying a reward) makes up the rest in gems.
* ``_pay_gold``: every gold the hero PAYS by choice to a person (a trader, an
  encounter's gold cost). Coin first; if it runs short, treasure at the
  trader's rate (treasure.buy_rate), the fewest-gold set of pieces that
  covers it, change back in coin.
* ``_purse_wealth``: coin plus what the hero can count on his treasure
  fetching. What "your purse" means to anyone pricing a share of it (a
  "pay 15% of your purse" choice, a temptation of "a quarter of what you
  carry") and to anyone asking if he can afford a thing.
* ``_pickup_gold`` / ``_drop_gold``: piles on the floor, partial pickup.
"""
from __future__ import annotations

import treasure


class PurseMixin:
    """Coin weight, receiving and paying gold, gold piles."""

    # ---------------------------------------------------------------- reading

    def _purse_wealth(self, *, true_values: bool = False) -> int:
        """Coin plus treasure at the rate a trader takes it. Unvalued kinds
        count at the low end of their band (never more than the hero knows),
        unless ``true_values`` (the score, the tools)."""
        coins = int(getattr(self, 'player_gold', 0) or 0)
        rate = treasure.buy_rate()
        total = 0
        for it in treasure.carried(self.player):
            n = max(1, int(getattr(it, 'count', 1) or 1))
            v = treasure.unit_value(it) if true_values else treasure.known_unit_value(self.player, it)
            total += int(v * rate) * n
        return coins + total

    # ---------------------------------------------------------------- receiving

    def _gain_gold(self, amount, *, paid: bool = False, quiet: bool = False,
                   earned: bool = True, who: str = '') -> dict:
        """Give the hero ``amount`` gold. He keeps what he can carry; the rest
        lies at his feet as his own pile, or, when a person is paying
        (``paid``), comes as gems. ``earned``: it counts in Gold Earned (not
        for his own coin coming back, such as change). Returns
        {'taken', 'gems', 'spilled'}."""
        out = {'taken': 0, 'gems': [], 'spilled': 0}
        try:
            amount = int(amount or 0)
        except (TypeError, ValueError):
            amount = 0
        if amount <= 0:
            return out
        p = self.player
        room = p.coin_room()
        take = min(amount, room)
        if paid and take < amount:
            # Leave room in the pack for the gems that make up the rest.
            level = int(getattr(self, 'dungeon_level', 1) or 1)
            for _ in range(2):
                gems, _left = treasure.gems_for(amount - take, level)
                gw = sum(p._item_weight(gm) for gm in gems)
                take = max(0, min(amount, room - treasure.coins_in(gw) - 1))
        if take > 0:
            if earned:
                self.player_gold = int(self.player_gold) + take
            else:
                self._set_gold_quietly(int(self.player_gold) + take)
        out['taken'] = take
        rest = amount - take
        if rest > 0 and paid:
            gems, rest = treasure.gems_for(rest, int(getattr(self, 'dungeon_level', 1) or 1))
            for g in gems:
                treasure.appraise(p, g)        # the payer says what they are worth
                g.x, g.y = p.x, p.y
                if not p.add_to_inventory(g):
                    self.ground_items.append(g)
                if earned:
                    self.__dict__['gold_earned'] = (self.__dict__.get('gold_earned', 0)
                                                    + treasure.total_value(g))
            out['gems'] = gems
        if rest > 0:
            from items import add_gold_to_tile
            add_gold_to_tile(self.ground_items, rest, p.x, p.y, found=False)
            if earned:
                self.__dict__['gold_earned'] = self.__dict__.get('gold_earned', 0) + rest
            out['spilled'] = rest
        if not quiet:
            if out['gems']:
                names = ', '.join(self._display_name(g) for g in out['gems'])
                self.add_message(
                    f"You cannot carry that much coin, so the rest is paid in gems: {names}.",
                    'loot')
            if out['spilled']:
                self.add_message(
                    f"You cannot carry {out['spilled']:,} of that gold. "
                    f"It stays on the floor at your feet.", 'warning')
        return out

    # ---------------------------------------------------------------- paying

    def _treasure_stacks(self, rate: float | None = None, *, known_only: bool = False) -> list:
        """[(item, credit per piece, count)] for the treasure in the pack."""
        r = treasure.buy_rate() if rate is None else float(rate)
        out = []
        for it in treasure.carried(self.player):
            v = (treasure.known_unit_value(self.player, it) if known_only
                 else treasure.unit_value(it))
            out.append((it, int(v * r), max(1, int(getattr(it, 'count', 1) or 1))))
        return out

    def _payment_plan(self, amount: int, rate: float | None = None) -> dict | None:
        """How ``amount`` would be paid now (treasure.plan_payment), or None
        when coin and treasure together fall short."""
        stacks = self._treasure_stacks(rate)
        coins = int(self.player_gold or 0)
        # The shop asks this for every row on every frame: remember answers
        # until the purse or the treasure changes.
        key = (int(amount), coins, rate, tuple((id(it), c, n) for it, c, n in stacks))
        cache = self.__dict__.setdefault('_plan_cache', {})
        if key not in cache:
            if len(cache) > 256:
                cache.clear()
            cache[key] = treasure.plan_payment(int(amount), coins, stacks)
        plan = cache[key]
        if plan is None:
            return None
        return {**plan, 'take': list(plan['take'])}

    def _payment_words(self, plan: dict) -> str:
        """'1,200 gold and a Saxon Garnet Brooch' for a plan."""
        parts = []
        if plan.get('coin'):
            parts.append(f"{int(plan['coin']):,} gold")
        for it, n in plan.get('take') or ():
            name = self._bare_name_count(it, n)
            parts.append(name)
        if not parts:
            return 'nothing'
        if len(parts) == 1:
            return parts[0]
        return ', '.join(parts[:-1]) + ' and ' + parts[-1]

    def _bare_name_count(self, item, n: int) -> str:
        import copy as _copy
        one = _copy.copy(item)
        one.count = max(1, int(n))
        name = self._display_name(one)
        if n <= 1:
            from paths import a_or_an
            return a_or_an(name)
        return name

    def _pay_gold(self, amount, *, rate: float | None = None, change_purse: int | None = None,
                  who: str = '', quiet: bool = False) -> dict | None:
        """Pay ``amount``: coin first, then treasure (valued at ``rate``),
        change back in coin (from ``change_purse`` when the payee has a
        limited purse, a trader). Returns the plan carried out (with
        'change_given'), or None when the hero cannot cover it (nothing is
        taken)."""
        amount = max(0, int(amount or 0))
        plan = self._payment_plan(amount, rate)
        if plan is None:
            return None
        p = self.player
        if plan['coin']:
            self.player_gold = max(0, int(self.player_gold) - int(plan['coin']))
        for it, n in plan['take']:
            treasure.appraise(p, it)
            have = max(1, int(getattr(it, 'count', 1) or 1))
            if n >= have:
                if it in p.inventory:
                    p.inventory.remove(it)
            else:
                it.count = have - n
        try:
            p.refresh_carry_bonuses()
        except Exception:
            pass
        change = int(plan['change'])
        if change_purse is not None:
            change = min(change, max(0, int(change_purse)))
        plan['change_given'] = change
        if plan['take'] and not quiet:
            self.add_message(f"You pay {self._payment_words(plan)}.", 'info')
        if change > 0:
            # His own money coming back: not earned. Change that will not fit
            # comes as gems, like any payment from a person.
            # (Never quiet: a spill or gems must be told.)
            self._gain_gold(change, paid=True, earned=False, who=who)
            if not quiet:
                self.add_message(f"{who} gives you {change:,} gold in change." if who
                                 else f"You get {change:,} gold in change.", 'info')
        return plan

    # ---------------------------------------------------------------- piles

    def _pickup_gold(self, pile) -> bool:
        """Pick up as much of ``pile`` as the hero can carry. True when a turn
        was spent (something was taken)."""
        from items import is_found_gold
        found = is_found_gold(pile)
        # Draupnir and its kin double FOUND gold, once per pile (the pile is
        # doubled where it lies the first time the hero touches it, so a
        # pile he can only half carry is not doubled again next time).
        if found and not getattr(pile, '_ring_doubled', False):
            for acc in self.player.equipped_accessories:
                gm = getattr(acc, 'gold_multiplier', 0)
                if gm > 0:
                    pile.amount = int(pile.amount * gm)
                    pile._refresh_name()
                    pile._ring_doubled = True
                    break
        room = self.player.coin_room()
        if room <= 0:
            self.add_message(
                f"You cannot carry any more gold: the {pile.amount:,} coins stay on the floor. "
                "(Coins are heavy. Drop something, or trade gold for gems.)", 'warning')
            return False
        take = min(int(pile.amount), room)
        if found:
            self.player_gold = int(self.player_gold) + take
        else:
            self._set_gold_quietly(int(self.player_gold) + take)   # the hero's own
        if take >= pile.amount:
            if pile in self.ground_items:
                self.ground_items.remove(pile)
            self.add_message(f"You pick up {take:,} gold coin{'s' if take != 1 else ''}.", 'loot')
        else:
            total = int(pile.amount)
            pile.amount = total - take
            pile._refresh_name()
            self.add_message(
                f"You can only carry {take:,} of the {total:,} gold. "
                f"The rest stays on the floor.", 'warning')
        return True

    # ---------------------------------------------------------------- QA

    def _qa_treasure_sampler(self) -> None:
        """Titivillus QA build only (Shift+4, '$'): a found pile of 20,000
        gold under the hero, one of every treasure kind on the tiles round
        him, and a trader beside him with gems and the Draught of Mimir's
        Well, so coin weight, partial pickup, paying with treasure and the
        draught can be tried in a minute."""
        if not getattr(self.player, 'qa_tools', False):
            return
        import random as _random
        from items import add_gold_to_tile, make_item_by_id
        from mystery_system import MerchantNPC, build_trader
        p = self.player
        add_gold_to_tile(self.ground_items, 20000, p.x, p.y, found=True)
        taken = {(g.x, g.y) for g in self.ground_items} | {(m.x, m.y) for m in self.monsters}
        spots = []
        for r in range(1, 6):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    x, y = p.x + dx, p.y + dy
                    if (max(abs(dx), abs(dy)) == r and self.dungeon.is_walkable(x, y)
                            and (x, y) not in taken):
                        spots.append((x, y))
        for kind in sorted(treasure.kinds()):
            if not spots:
                break
            x, y = spots.pop(0)
            piece = treasure.make(kind, x, y)
            if piece is not None:
                self.ground_items.append(piece)
        if spots and not any(isinstance(g, MerchantNPC) for g in self.ground_items):
            m = build_trader('generalist', max(40, int(self.dungeon_level)), _random.Random(4))
            d = make_item_by_id('potion', 'draught_of_mimir')
            if d is not None:
                d._trade_share = 5.0
                m.stock.append(d)
                import economy
                m.prices.append(economy.merchant_price(d, max(40, int(self.dungeon_level)), m.markup))
            m.x, m.y = spots.pop(0)
            self.ground_items.append(m)
        self.add_message("[QA] 20,000 gold at your feet, one of every treasure nearby, "
                         "and a trader with gems and the Draught of Mimir's Well.", 'info')

    def _drop_gold(self, amount: int) -> int:
        """Set ``amount`` of the purse down on the hero's tile as his own pile
        (it merges with his own pile there, never with found gold). Returns
        what was dropped."""
        amount = max(0, min(int(amount or 0), int(self.player_gold or 0)))
        if amount <= 0:
            return 0
        from items import add_gold_to_tile
        self.player_gold = int(self.player_gold) - amount
        add_gold_to_tile(self.ground_items, amount, self.player.x, self.player.y, found=False)
        return amount
