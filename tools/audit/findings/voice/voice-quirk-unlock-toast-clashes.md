---
id: voice-quirk-unlock-toast-clashes
dimension: voice
severity: P2
title: Quirk unlock toast is "TRAIT UNLOCKED" SaaS-caps while the same event's chronicle and flavor are mythic
status: open
systems: [quirk_system.py, main.py (_log_chronicle)]
evidence:
  - src/quirk_system.py:145 — "self.game.add_message(f\"TRAIT UNLOCKED: {name}\", 'loot')"
  - src/quirk_system.py:146 — "self.game.add_message(f\"  Reward: {_QUIRK_EFFECTS.get(qid, '')}\", 'success')"
  - src/quirk_system.py:148 — "self.game._log_chronicle(f\"Something changed in me. Unlocked a new trait: {name}. I'm becoming something more.\")"
  - src/quirk_system.py:1387 (flavor) — "'prometheus': 'They chained me to the rock. I am still here. -- Prometheus'"
  - src/quirk_system.py:1380 (flavor) — "'sisyphus': 'One must imagine Sisyphus happy -- and with a better lockpick.'"
  - src/quirk_system.py:195 (power-quirk toast) — "self.game.add_message(f\"POWER UNLOCKED: {name}\", 'loot')"
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

When the player unlocks a quirk — Prometheus, Sisyphus, Buddha, etc. — the game fires three messages in sequence:

1. `add_message("TRAIT UNLOCKED: {name}")` — caps-lock toast
2. `add_message("  Reward: <mechanical effect>")` — bullet point with mechanic
3. `_log_chronicle("Something changed in me. Unlocked a new trait: {name}. I'm becoming something more.")` — chronicle voice
4. `add_message(f'  "{flavor}"')` — the quirk's flavor line (Mithridates' quote, Prometheus' chains, etc.)

The mythic moment is fragmented across four messages, the first of which is a SaaS-style notification toast. "TRAIT UNLOCKED: Prometheus" reads like an Xbox achievement popup. The flavor line ("They chained me to the rock. I am still here.") sits *underneath* the achievement popup, which has primacy of the eye.

The chronicle entry on the same event is in pitch-perfect voice ("Something changed in me... I'm becoming something more"). The flavor lines are uniformly excellent (often real quotes from the historical/mythic figure). The toast is the only line in this stack that doesn't belong.

This affects every one of ~80 quirks and every active power quirk in the game.

## Why it breaks the register

This is a load-bearing moment — the game's reward economy depends on these unlocks feeling significant. CONTEXT.md §4 lists quirks as the largest secret surface area in the game. The unlock should land like a Joseph Campbell moment ("the threshold guardian is crossed"), not a Steam achievement notification.

The chronicle line and the flavor line together would carry the moment beautifully. The toast is what pulls the player out of fiction.

## Suggested rewrite direction

Either (a) replace the toast with a mythic-register equivalent, or (b) drop the toast entirely and let the chronicle + flavor carry the moment, or (c) integrate the trait name into the chronicle line.

Option (c) sample:
```python
self._log_chronicle(
    f"Something changed in me. I have become {name}. I'm becoming something more."
)
self.add_message(f'  "{flavor}"', 'info')
self.add_message(f"  ({_QUIRK_EFFECTS.get(qid, '')})", 'info')
```

The effect description in parens-italic feels like a footnote on the moment rather than a Steam toast competing with it.

## Notes

The same pattern repeats at `quirk_system.py:195` for power-quirks ("POWER UNLOCKED"). One fix template applies to both.
