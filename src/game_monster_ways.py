"""MonsterWaysMixin: the Game's side of monster behaviour, third wave (AI-3,
2026-11-20).

The behaviours are pure modules (holds, auras, monster_kit, skittish,
caster_ai, home_ground, surprise, dancer, second_shape: src/ai_turn.py has
the order); this mixin is only what needs the Game: the map, the hero's own
turn, the kill handler, the prompt and what he sees.

  _ways_world_turn()       once a world turn, before the monsters act
                           (CombatMixin._do_monster_turns): a hold that no
                           longer stands lets go; every aura pulses.
  _ways_turn_after(m)      after a monster's turn: the hero who saw it drink
                           knows the potion; a cornered leprechaun's offer.
  _ways_shield(m)          a swallowed hero is out of every other reach.
  _ways_on_kill(m, ...)    from the kill handler: a holder's death frees the
                           hero; what it did not use of its kit falls.
  _ways_held_move(dx, dy)  the hero's step while held (main._do_move): a
                           struggle, or a blow on the holder.
  _ways_level_change()     off the floor: any hold ends (main._change_level).
"""
from __future__ import annotations

import random

import auras
import holds
from geom import monster_at_tile


class MonsterWaysMixin:

    # ------------------------------------------------------------------
    # Every world turn
    # ------------------------------------------------------------------

    def _ways_world_turn(self) -> bool:
        """True when the hero died of it (the monsters' turn stops)."""
        from game_states import STATE_DEAD
        p = self.player
        line = holds.validate(p, self.monsters)
        if line:
            self.add_message(line, 'success')
        for text, colour in auras.pulse(self.monsters, p, self._sees_monster,
                                        dungeon=getattr(self, 'dungeon', None)):
            if text:
                self.add_message(text, colour)
        if p.hp <= 0:
            self._answer_a_killing_blow()
            if p.is_dead():
                if self.state != STATE_DEAD:
                    self.defeat_reason = 'died'
                    near = [m for m in self.monsters if m.alive and auras.in_reach(m, p)]
                    self._killed_by = getattr(near[0], 'kind', None) if near else None
                    self._on_game_over()
                    self.state = STATE_DEAD
                    self.add_message("You have died! Press Esc to return to the title.", 'danger')
        return self.state == STATE_DEAD

    # ------------------------------------------------------------------
    # After each monster's turn
    # ------------------------------------------------------------------

    def _ways_turn_after(self, m) -> None:
        learn = m.__dict__.pop('_kit_learn', None)
        if learn and self._sees_monster(m):
            known = getattr(self.player, 'known_item_ids', None)
            if known is not None and learn not in known:
                known.add(learn)
        if m.__dict__.get('_wants_bargain') and m.alive:
            self._bargain_pending = m           # asked once the world's turn is over

    def _ways_shield(self, m) -> bool:
        """True when this creature cannot strike the hero: he is inside
        another (swallowed)."""
        return holds.shields(self.player, m)

    # ------------------------------------------------------------------
    # The leprechaun's bargain (src/skittish.py)
    # ------------------------------------------------------------------

    def _ways_after_world(self) -> None:
        """After the world's turn (main._advance_turn, last): a cornered
        leprechaun's offer waiting is asked now, when no pet, escort or
        monster acts until the hero answers."""
        m = self.__dict__.pop('_bargain_pending', None)
        if m is not None and m.__dict__.get('_wants_bargain'):
            self._ways_offer_bargain(m)

    def _ways_bargain_stands(self, m) -> bool:
        """The offer still stands: he is alive, on this floor, unpaid, and
        still cornered beside the hero."""
        p = self.player
        return bool(m is not None and getattr(m, 'alive', False) and m in self.monsters
                    and not m.__dict__.get('_bargained') and not m.__dict__.get('_bargain_refused')
                    and max(abs(m.x - p.x), abs(m.y - p.y)) <= 2 and not p.is_dead())

    def _ways_offer_bargain(self, m) -> None:
        import skittish
        from game_states import STATE_PLAYER
        if self.state != STATE_PLAYER or self.player.is_dead():
            self._bargain_pending = m           # never in a quiz or a menu: after the next turn
            return
        if not self._ways_bargain_stands(m) or not self._sees_monster(m):
            m.__dict__.pop('_wants_bargain', None)
            return
        from monster import the_name
        title = f"{the_name(m)}'s Bargain"
        text = skittish.rules().get('ask_line', '')

        def _yes():
            self._ways_bargain_taken(m)

        def _no():
            if self._ways_bargain_stands(m):
                self.add_message(skittish.refuse(m), 'warning')
            m.__dict__.pop('_wants_bargain', None)

        self._ask(title, [text], [('Y', 'Yes', 'Take the purse and let him go', _yes),
                                  ('N', 'No', 'Keep him cornered and fight', _no)],
                  on_cancel=_no, esc='refuse')

    def _ways_bargain_taken(self, m) -> None:
        import skittish
        import theft
        from items import add_gold_to_tile
        if not self._ways_bargain_stands(m):
            m.__dict__.pop('_wants_bargain', None)
            self.add_message(skittish.rules().get('void_line', ''), 'info')
            return                              # dead, gone or loose: the bargain is void
        gold = skittish.offer_gold(m, random)
        line = skittish.accept(m)
        if gold > 0:
            add_gold_to_tile(self.ground_items, gold, m.x, m.y)
        self.add_message(line, 'success')
        if gold > 0:
            self.add_message(f"{gold:,} gold lies where he stood.", 'loot')
        for text in theft.give_back(self, m):
            self.add_message(text, 'loot')
        # Gone from the floor: no kill, no corpse, no study.
        m.alive = False
        m._kill_handled = True
        m._departed = True
        if m in self.monsters:
            self.monsters.remove(m)

    # ------------------------------------------------------------------
    # A death, a floor
    # ------------------------------------------------------------------

    def _ways_on_kill(self, m, banished: bool = False) -> None:
        m.__dict__.pop('_wants_bargain', None)  # a dead leprechaun offers nothing
        if self.__dict__.get('_bargain_pending') is m:
            self._bargain_pending = None
        if holds.is_holder(m, self.player):
            line = holds.release(self.player, m, 'dead')
            if line:
                self.add_message(line, 'success')
        import monster_kit
        monster_kit.kit_is_its_loot(m)          # its kit was its find (no second roll)
        if banished:
            m._kit = ()
            return
        from monster import the_name
        for it in monster_kit.leftovers(m):
            it.x, it.y = m.x, m.y
            self.ground_items.append(it)
            self.add_message(f"{the_name(m)} drops {self._a_or_an(self._display_name(it))}.",
                             'loot')

    def _ways_held_at_stairs(self) -> bool:
        """True when a hold keeps the hero off the stair (he must get free
        first); the line says so."""
        p = self.player
        line = holds.validate(p, self.monsters)
        if line:
            self.add_message(line, 'success')
        if not holds.is_held(p):
            return False
        m = holds.holder(p, self.monsters)
        from monster import the_name
        self.add_message(f"You cannot reach the stair while {the_name(m, lower=True)} holds you."
                         if m is not None else "You cannot reach the stair.", 'warning')
        return True

    def _ways_level_change(self) -> None:
        m = holds.holder(self.player, self.monsters)
        holds.release(self.player, m, 'floor')

    # ------------------------------------------------------------------
    # The hero's step while held (main._do_move)
    # ------------------------------------------------------------------

    def _ways_held_move(self, dx: int, dy: int) -> bool:
        """True when the hold took this step (a struggle, or a blow on the
        holder from inside it); False to go on with the move."""
        p = self.player
        line = holds.validate(p, self.monsters)
        if line:
            self.add_message(line, 'success')
        if not holds.is_held(p):
            return False
        m = holds.holder(p, self.monsters)
        if m is None:
            holds.release(p, None, 'dead')
            return False
        target = monster_at_tile(self.monsters, p.x + dx, p.y + dy)
        if holds.swallowed(p):
            self._start_combat(m)               # inside it, every way is its gut
            return True
        if target is m or p.has_effect('immobilized'):
            return False                        # a blow on the holder; or stuck fast (main says so)
        freed, text = holds.struggle(p, m)
        if text:
            self.add_message(text, 'success' if freed else 'warning')
        self._advance_turn()
        return True
