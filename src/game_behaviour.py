"""BehaviourMixin: the Game's side of monster behaviour, first wave (AI-1,
2026-11-19).

The behaviours themselves are pure modules (breath, faction, summoning,
morale, life_drain, grave_rot, light_shy, gone_again, alarm, death_throes,
relurk, shove); this mixin is only what needs the Game: what the hero sees
and hears of them (the lines each leaves, src/ai_lines.py), and the few
things that touch the map, the kill handler or the hero's turn.

  _ai_turn_after(m)   after a monster's turn (CombatMixin._do_monster_turns):
                      its lines, said as the hero sees or hears them.
"""
from __future__ import annotations

import ai_lines


class BehaviourMixin:

    def _ai_turn_after(self, m) -> None:
        """What a monster's behaviour left this turn for the hero to see or
        hear: the line he can see said as it is, a sound when he cannot (an
        unseen line never names the creature)."""
        lines = ai_lines.take(m)
        if not lines:
            return
        seen = self._sees_monster(m)
        for text_seen, text_unseen, colour in lines:
            text = text_seen if seen else text_unseen
            if text:
                self.add_message(text, colour or 'warning')
