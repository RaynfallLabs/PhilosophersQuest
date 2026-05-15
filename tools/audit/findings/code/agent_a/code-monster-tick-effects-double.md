---
id: code-monster-tick-effects-double
dimension: code
severity: P1
title: Monster status effects tick twice per turn (DOT 2x, durations halve)
status: open
systems: [monster_ai, status_effects, combat_loop]
evidence:
  - src/main.py:1559 — `m.tick_effects()` called for every alive monster inside `_advance_turn`
  - src/monster.py:358 — `self.tick_effects()` called as the first line of `Monster.take_turn()`
  - src/game_combat.py:1408 — `m.take_turn(...)` invoked for each monster from `_do_monster_turns`
  - src/main.py:1654 — `self._do_monster_turns()` follows the explicit tick loop in the same `_advance_turn`
verified: true
discovered: 2026-05-15
---

## What's wrong

`Monster.tick_effects()` is being called TWICE per turn for every alive monster. The first call is in `_advance_turn` (main.py:1556-1562), the second is at the very top of `Monster.take_turn()` (monster.py:358) when monster turns are processed via `_do_monster_turns()`.

Net effect:
- Damage-over-time (bleeding, poisoned, burning) deals double damage per turn.
- All timed status durations (sleeping, paralyzed, confused, slowed, petrifying, etc.) decrement at twice the intended rate.
- Petrifying that should kill on turn 10 of the timer kills on turn 5.
- A 5-turn paralysis is actually 2-3 turns.

This dramatically tilts combat in the player's favour for any effect-laden enemy (Medusa's petrify, troll regen — regen at line 162-167 ALSO runs every tick, doubling self-heal), and short-circuits the `tick_effects` regeneration code (trolls/hydras regenerate twice per turn even though they're meant to feel slow).

Consensus's prior P3 finding ("`tick_effects` never called on monsters") is the inverse of this — it has since been wired in at main.py:1559 but the call in `Monster.take_turn` at monster.py:358 was not removed.

## How to reproduce / where it fires

Every turn. Trace:
1. Player acts → calls `_advance_turn` (main.py:1513).
2. Line 1557-1562 loops `self.monsters`, calls `m.tick_effects()` on each (1st tick).
3. Same `_advance_turn` calls `self._do_monster_turns()` at line 1654.
4. `_do_monster_turns` (game_combat.py:1384) loops `self.monsters`, calls `m.take_turn(...)`.
5. `Monster.take_turn` (monster.py:352) begins with `self.tick_effects()` (2nd tick).

Observable test: petrify a giant (status 'petrifying', initial duration 12 turns). Expected: monster dies of stone on the 12th turn. Actual: dies on the 6th turn.

## Suggested fix

Remove ONE of the two ticks. The call at monster.py:358 inside `Monster.take_turn` is the older one (predates the main.py loop). Suggested removal point: monster.py:358 — delete that line. Keep the main.py:1559 loop because it correctly fires `_on_monster_killed(m)` for DOT kills and adds the "succumbs to its wounds" message, which `take_turn` does not.

After the removal, verify the DeathMonster path (which overrides `tick_effects` to a no-op at monster.py:1043) still behaves identically (it will — `tick_effects` is still called once by main.py:1559, and the no-op short-circuits).

## Notes

This is a single-system invariant bug ("status effects decrement exactly once per game turn") which the holistic-rule exemption explicitly allows. Likely shipped during the wire-up that fixed the prior "tick_effects never called" finding — adding the loop in main.py without realizing `take_turn` already had its own.
