"""LorePowersMixin: the game's side of the MONSTERS AND MAGIC kinds' powers
(2026-11-19, slice M). The creature's side is src/lore_powers.py.

* The lines a power says (lore_powers.OUTBOX), told as the hero sees them.
* A gift of plain food set down near a Kappa or a Preta: it eats and keeps
  to itself for the floor (``appeased_by``). Struck, the peace is broken.
* Gold dropped near a gold-digging ant: it stops to gather it (Herodotus'
  camels let go to slow the pursuit), and the gold is gone.
* The Blue Men of the Minch call out a verse when they first see the hero
  and hold their fire for a few turns: D answers them, one grammar question
  at their tier; right, they sink away for the floor, wrong, the squall
  comes down at once. Walk away or strike and they attack.
* The Vetala: when its body falls, the spirit slips into the nearest corpse
  that is still lying there and gets up again (``corpse_hop``, at most
  ``max_hops`` times). Harvested or searched, a corpse is gone: the counter.
* The Roc's carry-off: the hero lands far away on an explored, empty tile,
  held a turn.
* The Jiangshi: any scroll read while one can see the hero holds it, as a
  paper talisman pressed to its forehead.
* The QA key (Shift+Y, Titivillus only): the next of the new kinds set down
  beside the hero, in order.
"""
from __future__ import annotations

import random

import lore_powers
from monster import the_name

PARLEY_WAIT = 6          # turns the Blue Men wait for an answer
PARLEY_REACH = 8         # D answers them from this far, in sight
APPEASE_REACH = 2        # a gift this close is seen and eaten
GOLD_REACH = 2

QA_KINDS = ('mandrake', 'kappa', 'eloko', 'asanbosam', 'ahuizotl', 'khalkotauros', 'cu_sith',
            'bulgasari', 'vetala', 'likho', 'centaur', 'nahual', 'blue_men_of_the_minch', 'vila',
            'myrmekes', 'ponaturi', 'taniwha', 'impundulu', 'mapinguari', 'preta', 'upas_tree',
            'nuckelavee', 'star_jelly', 'psoglav', 'waq_waq_tree', 'yuki_onna', 'yacumama',
            'tsuchigumo', 'bhuta_vahana_yanta', 'reem', 'eitr', 'bakunawa')


class LorePowersMixin:

    # ------------------------------------------------------------- lines
    def _lore_powers_say(self) -> None:
        for entry in lore_powers.drain():
            text, kind = entry[0], entry[1]
            m = entry[2] if len(entry) > 2 else None
            unseen = entry[3] if len(entry) > 3 else None
            if m is not None and not self._sees_monster(m):
                text = unseen
            if text:
                self.add_message(text, kind)

    # --------------------------------------------------- before its turn
    def _lore_powers_before(self, m) -> None:
        """Before a creature's turn: a gift it sees, gold dropped near it,
        the Blue Men's verse."""
        if not lore_powers.ENABLED or not getattr(m, 'alive', False):
            return
        d = m.__dict__
        if lore_powers.spec(m, 'appeased_by') and not d.get('_lp_calm'):
            self._lore_powers_offering(m)
        if lore_powers.spec(m, 'gold_gatherer') and not d.get('_lp_busy'):
            self._lore_powers_gold(m)
        if lore_powers.spec(m, 'parley'):
            self._lore_powers_parley_tick(m)

    def _near_ground(self, m, reach: int, test):
        for it in list(getattr(self, 'ground_items', None) or ()):
            x, y = getattr(it, 'x', None), getattr(it, 'y', None)
            if x is None or max(abs(x - m.x), abs(y - m.y)) > reach:
                continue
            if test(it):
                return it
        return None

    def _lore_powers_offering(self, m) -> None:
        it = self._near_ground(m, APPEASE_REACH, lore_powers.is_plain_food)
        if it is None:
            return
        n = int(getattr(it, 'count', 1) or 1)
        if n > 1:
            it.count = n - 1
        else:
            self.ground_items.remove(it)
        m.__dict__['_lp_calm'] = True
        m.__dict__['_lp_parley'] = 'calm'
        spec = lore_powers.spec(m, 'appeased_by') or {}
        if self._sees_monster(m):
            self.add_message(spec.get('line') or f"{the_name(m)} eats your offering and leaves you be.",
                             'success')

    def _lore_powers_gold(self, m) -> None:
        from items import GoldPile
        pile = self._near_ground(m, GOLD_REACH, lambda it: isinstance(it, GoldPile))
        if pile is None:
            return
        self.ground_items.remove(pile)
        spec = lore_powers.spec(m, 'gold_gatherer') or {}
        m.__dict__['_lp_busy'] = int(spec.get('turns', 3) or 3)
        if self._sees_monster(m):
            self.add_message(spec.get('line') or f"{the_name(m)} stops to gather the gold.", 'info')

    # ------------------------------------------------------- the parley
    def _lore_powers_parley_tick(self, m) -> None:
        d = m.__dict__
        state = d.get('_lp_parley')
        if state is None:
            if not (getattr(m, '_aware', False) or self._sees_monster(m)) or not self._sees_monster(m):
                return
            group = self._parley_group(m)
            for o in group:
                o.__dict__['_lp_parley'] = 'waiting'
                o.__dict__['_lp_wait'] = PARLEY_WAIT
            spec = lore_powers.spec(m, 'parley') or {}
            self.add_message(spec.get('call', ''), 'warning')
            self.add_message("Press D to answer them, or keep away.", 'info')
            return
        if state != 'waiting':
            return
        if any(o.__dict__.get('_lp_parley') == 'angry' for o in self._parley_group(m)):
            d['_lp_parley'] = 'angry'
            return
        left = int(d.get('_lp_wait', 0) or 0) - 1
        d['_lp_wait'] = left
        if left <= 0:
            d['_lp_parley'] = 'angry'
            spec = lore_powers.spec(m, 'parley') or {}
            if self._sees_monster(m):
                self.add_message(spec.get('unasked', '') or f"{the_name(m)} tires of waiting.", 'warning')

    def _parley_group(self, m) -> list:
        return [o for o in self.monsters
                if o.alive and o.kind == m.kind
                and max(abs(o.x - m.x), abs(o.y - m.y)) <= 10]

    def _parley_offer(self) -> bool:
        """D with the Blue Men waiting in sight: their one question. True if
        it was asked."""
        waiting = [m for m in self.monsters
                   if m.alive and m.__dict__.get('_lp_parley') == 'waiting'
                   and self._sees_monster(m)
                   and max(abs(m.x - self.player.x), abs(m.y - self.player.y)) <= PARLEY_REACH]
        if not waiting:
            return False
        lead = waiting[0]
        spec = lore_powers.spec(lead, 'parley') or {}
        subject = str(spec.get('subject', 'grammar'))
        tier = max(1, min(5, int(getattr(lead, 'harvest_tier', 1) or 1)))
        group = self._parley_group(lead)
        from game_states import STATE_PLAYER, STATE_QUIZ
        self.quiz_title = f"{the_name(lead).upper()}  --  {subject.upper()}"
        self.state = STATE_QUIZ

        def on_complete(result):
            ok = bool(result.success)
            for o in group:
                o.__dict__['_lp_parley'] = 'calm' if ok else 'angry'
                if ok:
                    o.__dict__['_lp_calm'] = True
                else:
                    o.__dict__['_opened'] = False       # the squall comes now (its opener)
            self.add_message(spec.get('right' if ok else 'wrong', ''), 'success' if ok else 'danger')
            self.state = STATE_PLAYER
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold', subject=subject, tier=tier,
            callback=on_complete, threshold=1, total_qs=1,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds(subject),
            base_seconds=self.player.get_quiz_timer(subject),
        )
        return True

    # ---------------------------------------------------- after its turn
    def _lore_powers_after(self, m) -> None:
        """After a creature's turn: the Roc's carry-off, then the lines."""
        lift = self.player.__dict__.pop('_lp_carry_off', None)
        if lift:
            self._lore_powers_carry_off(*lift)
        self._lore_powers_say()

    def _lore_powers_carry_off(self, lo: int, hi: int) -> None:
        p = self.player
        d = self.dungeon
        from geom import all_occupied_tiles
        taken = all_occupied_tiles(self.monsters)
        try:
            taken |= self._occupants(hero=False)
        except Exception:
            pass
        explored = getattr(d, 'explored', set()) or set()
        spots = [(x, y) for y in range(d.height) for x in range(d.width)
                 if (x, y) in explored and d.is_walkable(x, y) and (x, y) not in taken
                 and lo <= max(abs(x - p.x), abs(y - p.y)) <= hi
                 and not any(m.alive and max(abs(m.x - x), abs(m.y - y)) <= 2 for m in self.monsters)]
        if not spots:
            return
        p.x, p.y = random.choice(spots)
        p.add_effect('immobilized', 1)
        self._refresh_fov()

    # -------------------------------------------------------- its death
    def _lore_powers_killed(self, m) -> None:
        """The Vetala's spirit slips into the nearest corpse still lying
        there, and the corpse gets up."""
        if not lore_powers.ENABLED:
            return
        ch = lore_powers.spec(m, 'corpse_hop')
        if not ch or getattr(m, '_banished', False):
            return
        hops = int(m.__dict__.get('_lp_hops', 0) or 0)
        if hops >= int(ch.get('max_hops', 2) or 0):
            return
        from items import Corpse
        reach = int(ch.get('radius', 6) or 6)
        bodies = [it for it in (getattr(self, 'ground_items', None) or ())
                  if isinstance(it, Corpse) and (it.x, it.y) != (m.x, m.y)
                  and max(abs(it.x - m.x), abs(it.y - m.y)) <= reach]
        if not bodies:
            return
        body = min(bodies, key=lambda it: max(abs(it.x - m.x), abs(it.y - m.y)))
        from geom import all_occupied_tiles
        taken = all_occupied_tiles([o for o in self.monsters if o is not m]) | self._occupants()
        if (body.x, body.y) in taken:
            return
        from monster import Monster
        defn = lore_powers._defs().get(m.kind)
        if not defn:
            return
        risen = Monster({**defn, 'id': m.kind}, body.x, body.y)
        risen.max_hp = max(1, int(m.max_hp * float(ch.get('hp_share', 0.4) or 0.4)))
        risen.hp = risen.max_hp
        risen._aware = True
        risen.__dict__['_lp_hops'] = hops + 1
        self.ground_items.remove(body)
        self.monsters.append(risen)
        seen = (body.x, body.y) in self.visible
        self.add_message(ch.get('line' if seen else 'unseen', ''), 'danger')

    # --------------------------------------------------------- a scroll
    def _lore_powers_scroll_read(self) -> None:
        """A page read aloud stops a Jiangshi that can see you, as a paper
        talisman pressed to its forehead."""
        if not lore_powers.ENABLED:
            return
        for m in self.monsters:
            tal = lore_powers.spec(m, 'talisman') if m.alive else None
            if not tal or not self._sees_monster(m):
                continue
            if max(abs(m.x - self.player.x), abs(m.y - self.player.y)) > 8:
                continue
            if m.add_effect('paralyzed', int(tal.get('turns', 2) or 2)):
                self.add_message(tal.get('line', ''), 'success')

    # ---------------------------------------------------------- QA key
    def _qa_mm_kinds(self) -> None:
        """Titivillus QA build only (Shift+Y): the next new kind of the
        MONSTERS AND MAGIC pass set down beside the hero, in order."""
        if not getattr(self.player, 'qa_tools', False):
            return
        from geom import all_occupied_tiles
        from monster import Monster
        i = int(self.__dict__.get('_qa_mm_i', 0) or 0)
        kind = QA_KINDS[i % len(QA_KINDS)]
        self._qa_mm_i = i + 1
        defn = lore_powers._defs().get(kind)
        if not defn:
            return
        taken = all_occupied_tiles(self.monsters) | self._occupants()
        p = self.player
        fw, fh = (defn.get('footprint') or (1, 1))[:2]
        for r in (2, 3, 4):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    x, y = p.x + dx, p.y + dy
                    cells = [(x + a, y + b) for a in range(fw) for b in range(fh)]
                    if all(self.dungeon.in_bounds(cx, cy) and self.dungeon.is_walkable(cx, cy)
                           and (cx, cy) not in taken for cx, cy in cells):
                        m = Monster({**defn, 'id': kind}, x, y)
                        self.monsters.append(m)
                        self.add_message(f"[QA] {m.name} ({kind}) set down beside you.", 'info')
                        return
        self.add_message(f"[QA] No room for {kind} here.", 'info')
