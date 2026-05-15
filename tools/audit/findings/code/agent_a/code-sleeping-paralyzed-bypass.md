---
id: code-sleeping-paralyzed-bypass
dimension: code
severity: P2
title: Sleeping/paralyzed/immobilized only blocks movement; all other actions still work
status: open
systems: [status_effects, input_handling, combat_pacing]
evidence:
  - src/main.py:889-913 — sleep/paralyzed/immobilized/slowed guards live INSIDE `_do_move(dx, dy)` only
  - src/game_input.py:220-359 — `_player_input` handles 30+ action keys (Q quaff, R read, U eat, P lockpick, F fire, A attack, M cast, S accessory, I identify, H harvest, C cook, T throw, B encyclopedia, \\ pray, N recall, etc.) with NO has_effect checks
  - src/game_input.py:222-238 — `K_PERIOD` (wait) explicitly grants +1 MP via meditation when no adjacent monsters — works while paralyzed
  - src/player.py:128-130 — damage wakes the player from sleep, but no other wake condition; player can also avoid taking damage by simply not moving while monsters can't reach
verified: true
discovered: 2026-05-15

---

## What's wrong

The classic NetHack-lineage invariant is "sleeping/paralyzed player skips turns and cannot act". This game enforces that *only* for movement actions. Every other gameplay action — drinking potions, reading scrolls, eating food, harvesting corpses, firing ranged weapons, casting spells, equipping armour, identifying items, picking locks, praying, recalling lore — runs without any check.

Worst-case examples a player can pull off while asleep or paralyzed:
- Drink a cure-all potion (waking themselves).
- Press '.' to meditate and gain +1 MP (main.py:232-234).
- Read a scroll of teleport.
- Equip a cursed amulet via a fully-functional menu chain.
- Open the spell menu, cast `displacement_self`, and walk through ambient ticks.

The only sleep wake-up condition (`player.py:129-130`) is "taking damage". A player who is asleep at full HP with no adjacent monsters can sit there indefinitely while monsters approach — and meanwhile cast spells, drink potions, etc.

This is a major mechanic break. Sleeping/paralyzed monsters in `Monster.take_turn` (monster.py:361-362) DO get the equivalent guard (`if self.has_effect('sleeping') or self.has_effect('paralyzed'): return False`). The asymmetry is purely on the player side.

## How to reproduce / where it fires

1. Acquire any source of `paralyzed` (gnome wand, floating eye, etc.).
2. Player gets paralyzed for, say, 5 turns.
3. Press Q. Quaff menu opens. Drink a haste potion. Now hasted while paralyzed.
4. Press M. Spell menu opens. Cast a non-targeted spell. Quiz runs. Spell fires.
5. Press `.`. Meditate. Gain +1 MP.

Trace for `_open_quaff_menu` (game_menus.py:154):
1. K_q key event → `_player_input` (game_input.py:255-257) → `_open_quaff_menu()`.
2. No has_effect check anywhere in the call chain.
3. Menu opens, player drinks potion, `drink_potion` runs.

## Suggested fix

Add a single early-return guard at the top of `_player_input` (game_input.py:220):

```python
def _player_input(self, key: int):
    # Sleeping/paralyzed/immobilized: skip the turn, nothing else allowed.
    # Movement keys still go through _do_move which has its own already-correct guard
    # (we keep that for the "you are paralyzed" message + slow_skip handling).
    if self.player.has_effect('sleeping') or self.player.has_effect('paralyzed'):
        if key in self._MOVE_KEYS or key == pygame.K_PERIOD:
            # let movement/wait fall through to existing handlers that already skip
            pass
        else:
            self.add_message(
                "You can't act -- you are " +
                ("asleep" if self.player.has_effect('sleeping') else "paralyzed") + "!",
                'warning')
            self._advance_turn()
            return
    ...
```

(Tuning: decide whether menu keys also force `_advance_turn` or are silently no-op. Forcing turn-advance is more punishing and probably correct given the design philosophy.)

Also consider whether the `.` meditation MP-gain should require not-paralyzed/sleeping (main.py:222-238); current code lets a paralyzed player still gain +1 MP/turn for free.

## Notes

This is a single-system bug (input handling) but it cross-cuts every action in the game. Player can completely circumvent paralysis and sleep, which are major balance levers (floating eye gaze, sleep gas trap, sleep wand, paralysis fungus, sleeping monster contact, etc.). Severity P2 because none of the bypasses crash the game — they just neutralize a class of status effects.
