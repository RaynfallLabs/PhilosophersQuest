"""BehaviourMixin: the Game's side of monster behaviour, first wave (AI-1,
2026-11-19).

The behaviours themselves are pure modules (breath, faction, summoning,
morale, life_drain, grave_rot, light_shy, gone_again, alarm, death_throes,
relurk, shove); this mixin is only what needs the Game: what the hero sees
and hears of them (the lines each leaves, src/ai_lines.py), and the few
things that touch the map, the kill handler or the hero's turn.

  _ai_turn_after(m)   after a monster's turn (CombatMixin._do_monster_turns):
                      its lines, said as the hero sees or hears them; the
                      purse a yielding bandit throws down (morale).
  _ai_on_kill(m)      from the kill handler (CombatMixin._on_monster_killed):
                      its side sees it fall (morale).
"""
from __future__ import annotations

import ai_lines
import morale


class BehaviourMixin:

    def _ai_turn_after(self, m) -> None:
        """What a monster's behaviour left this turn for the hero to see or
        hear: the line he can see said as it is, a sound when he cannot (an
        unseen line never names the creature)."""
        if m.__dict__.pop('_wants_purse_dropped', False):
            self._ai_drop_purse(m)
        lines = ai_lines.take(m)
        if not lines:
            return
        seen = self._sees_monster(m)
        for text_seen, text_unseen, colour in lines:
            text = text_seen if seen else text_unseen
            if text:
                self.add_message(text, colour or 'warning')

    def _ai_drop_purse(self, m) -> None:
        """A creature that yields (morale) throws down its purse, and what it
        stole: its gold falls on its tile now and is not dropped again when
        it dies."""
        import random as _rng
        from items import add_gold_to_tile
        import theft
        tre = dict(getattr(m, 'treasure', None) or {})
        lo, hi = (list(tre.get('gold') or [0, 0]) + [0, 0])[:2]
        gold = _rng.randint(int(lo), max(int(lo), int(hi))) if hi else 0
        if gold > 0:
            add_gold_to_tile(self.ground_items, gold, m.x, m.y)
        tre['gold'] = [0, 0]
        m.treasure = tre
        for text in theft.give_back(self, m):
            self.add_message(text, 'loot')

    def _ai_on_kill(self, m) -> None:
        """One of a side fell: its hurt kin that saw it may break (morale)."""
        try:
            morale.kin_fell(self.monsters, m, getattr(self, 'dungeon', None))
        except Exception as exc:          # never let a nerve check stop a kill
            from game_log import log_error
            log_error(f"morale.kin_fell: {exc!r}")
