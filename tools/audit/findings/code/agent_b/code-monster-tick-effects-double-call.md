---
id: code-monster-tick-effects-double-call
dimension: code
severity: P2
title: Monster status effects tick twice per turn (called both in `_advance_turn` and `take_turn`)
status: open
systems: [combat, status-effects, monster-ai]
evidence:
  - src/main.py:1557-1562 — explicit `for m in self.monsters: m.tick_effects()` after `_advance_turn` decrements
  - src/monster.py:358 — `self.tick_effects()` is the first line of `Monster.take_turn`
  - src/monster.py:130-167 — `tick_effects` decrements `status_effects[name]` and applies DOT damage
  - src/game_combat.py:1408 — `did_attack = m.take_turn(...)` invokes Monster.take_turn each turn
verified: true
discovered: 2026-05-15
---

## What's wrong
`Monster.tick_effects()` is invoked twice per game turn for every monster:

1. **First call** — `_advance_turn()` runs an explicit "tick monster status effects" loop (`main.py:1557-1562`), which calls `m.tick_effects()` on each alive monster.
2. **Second call** — Within `_do_monster_turns()` (`game_combat.py:1408`), each monster's `take_turn()` runs `self.tick_effects()` as its first line (`monster.py:358`).

Each call decrements every active effect's duration by 1 and applies DOT (bleeding/poisoned/burning) damage. Net consequence per turn:

- **Effect durations are halved.** A 10-turn bleed inflicted on a monster effectively lasts 5 ticks of game time. Same for burning, poisoned, slowed, confused, stunned, paralyzed, frozen.
- **DOT damage doubles.** Bleeding (`max(1, max_hp // 15)`), poison (`1`), and burning (`max(1, max_hp // 20)`) all apply twice per turn.
- **Petrifying duration is halved**, accelerating the petrify-kill path (`monster.py:150-152`).
- **Regeneration applies twice per turn** if `regeneration > 0`, doubling troll/hydra regen rate.

This is a regression. The consensus baseline lists "Monster `tick_effects` is never called" as a P3 — that fix was added in `_advance_turn`, but the call inside `take_turn` was never removed. The fix overshot in the other direction.

## How to reproduce / where it fires
1. Hit any monster with a bleeding weapon (e.g., Sword of Bleeding, or any weapon with `bleed_chance > 0`). `m.add_effect('bleeding', N)` is called.
2. End of turn:
   - `_advance_turn` line 1557-1559 ticks every monster once → bleed decrements, DOT damage applied.
3. Next turn the monster acts:
   - `Monster.take_turn` line 358 ticks effects again → bleed decrements again, DOT damage applied again.

Net result: a bleed inflicted on turn N for `5` turns wears off by turn N+3 instead of N+5, and the monster takes 2× the bleed damage in the interim.

Same applies to **burning** from fire weapons / fire shield reflect, **poisoned** from poison weapons / poison breath self-reflection, **slowed** from Amenonuhoko AOE-on-kill, **confused** from confuse-on-hit, and **petrifying** from Khepri-class items.

Call graph traced:
- `_advance_turn` → main.py:1557 → `m.tick_effects()`  (decrements once)
- `_advance_turn` → main.py:1654 → `_do_monster_turns` → game_combat.py:1408 → `m.take_turn()` → monster.py:358 → `self.tick_effects()` (decrements again)

## Suggested fix
Two options, pick one and commit:

**Option A (preferred)** — Remove the `self.tick_effects()` line at `monster.py:358`. The explicit pass in `_advance_turn` is the canonical place; `take_turn` should not duplicate it.

**Option B** — Remove the explicit loop at `main.py:1556-1562` and let `Monster.take_turn` continue to tick effects. Drawback: dead/non-acting monsters (paralyzed, sleeping) might skip the tick — but lines 360-362 currently exit `take_turn` *after* `tick_effects` runs, so those monsters do still tick. The actual issue with option B is that monsters whose take_turn is skipped (time_stopped check at `_do_monster_turns:1352-1354` early-returns the whole loop) wouldn't tick at all that turn — but that's the intended behavior under time stop.

Option A is the safer minimal-blast-radius fix.

## Notes
The DeathMonster overrides `tick_effects` to be a no-op (`monster.py:1043`), so Death is unaffected. The bug only impacts regular monsters and bosses (which can also be poisoned/bled/burned).

The consensus baseline's P3 entry on monster tick_effects was correctly fixed, but the fix was applied additively without auditing whether the existing call inside `take_turn` should be kept.
