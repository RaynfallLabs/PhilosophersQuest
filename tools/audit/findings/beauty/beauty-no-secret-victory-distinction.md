---
id: beauty-no-secret-victory-distinction
dimension: beauty
severity: P1
title: Secret Abyss victory and ordinary Stone-exit victory share the same victory screen
status: open
systems: [trigger_abyss, story_popup, victory_screen, message_log]
evidence:
  - src/main.py:1373-1406 — `_trigger_abyss` emits six `add_message` calls then continues normal gameplay
  - src/main.py:1449-1462 — `_do_exit` routes both Stone-exit and Abyss-exit through `_show_story_popup('exit_with_stone', STATE_VICTORY)`
  - src/main.py:3452-3473 — `_STORY_CONTENT['exit_with_stone']` — single shared popup definition with code `'QUEST-COMPLETE'`
  - src/game_render.py:2456-2549 — `_draw_victory_screen` has no branching for victory type
  - beauty_screen_catalog.md#21
  - beauty_screen_catalog.md#22
discovered: 2026-05-15
---

## The visual clash or inconsistency

The CONTEXT briefing identifies the Abyss victory as **"the maximum-difficulty ending and unlocks the most prestigious reward code"**. The player has to (a) clear floors 1–100, (b) survive the Death chase up, (c) find the Tablet of Second Death, (d) combine it with the Stone, (e) find an Abyssal Shimmer, (f) stand on it while carrying the Complete Tablet. This is the apex achievement.

What happens visually:
1. `_trigger_abyss` (`main.py:1373`) emits six `add_message` calls — atmospheric text scrolls through the message log.
2. The Death monster object is set to `None`, the Death's-Bane scroll is dropped at the player's feet, the Shimmer is removed.
3. Gameplay continues. The player picks up the scroll, walks to stair `<`, exits.
4. Exit triggers `_show_story_popup('exit_with_stone', STATE_VICTORY)` (`main.py:1458`) — **the same story popup as a normal Stone-exit**, with `code='QUEST-COMPLETE'`.
5. The story popup transitions to `STATE_VICTORY`, which renders `_draw_victory_screen` — **identical to a normal Stone-exit victory**: gold rune circles, candle glow, "VICTORY!" headline, "You retrieved the Philosopher's Stone!" subtitle.

The player who beat the maximum-difficulty ending sees:
- The same title text.
- The same gold rune circles (not arcane-purple, not black-and-flame).
- The same reward code (`QUEST-COMPLETE`).
- The same congratulatory speech about "the village of Amber".

The Abyss-specific lore — *"Then Death and Hades were thrown into the lake of fire."* — was visible briefly in the message log when `_trigger_abyss` fired several minutes (or hours) of dungeon-climbing ago. By the time the victory screen renders, it has scrolled away.

## Where it surfaces

- **Story popup screen** (`_show_story_popup('exit_with_stone')`): both endings → same popup with title `THE QUEST IS COMPLETE`, same body, same reward code.
- **Victory screen** (`_draw_victory_screen`): both endings → same gold rune circles, same "Philosopher's Stone!" subtitle, same stats table, same `+50,000` stone bonus.
- **Message log**: the only place where the Abyss-victory text exists. Fades within ~60 entries (`ui.py:22` — `MAX = 60`). For a long endgame run, the Abyss messages are likely gone before the player exits.
- **Reward code**: per the briefing, the Abyss should unlock "the most prestigious reward code". The current code in `_STORY_CONTENT['exit_with_stone']['code']` is the generic `'QUEST-COMPLETE'`. There is no Abyss-specific code.

## Suggested unification

Introduce a victory-type discriminator (e.g., `self.victory_type = 'abyss'` set inside `_trigger_abyss`, defaulting to `'stone'`). Then:

1. Add a new story-popup entry `'exit_with_complete_tablet'` (or `'death_is_dead'`) with the Abyss-specific lore, framed as a different ending — *"You climbed back out. Death does not follow. Death is no more."* — and a unique reward code like `'DEATH-IS-DEAD'`.
2. Route the Stone-vs-Abyss path differently from `_do_exit`: if the player carries the Complete Tablet of Second Death (or has triggered the abyss), use the new popup; otherwise `'exit_with_stone'`.
3. In `_draw_victory_screen`, branch on `self.victory_type`:
   - `'stone'` → current gold-rune treatment (untouched).
   - `'abyss'` → arcane-purple rune circles (`FP.ARCANE_BRIGHT` / `FP.ARCANE`), title text reads "DEATH IS DEAD" or "YOU HAVE OVERCOME", optional small flame motif in the corner flourishes, different background tint (deep black instead of warm gold).
4. The visual contrast between the two victory screens should mirror the contrast between the two endings: warm-gold "you saved your village" vs. cold-arcane "you defeated Death itself".

## Notes

This is P1 because the briefing explicitly says the Abyss victory is the game's apex. The current code makes the apex visually invisible — a player who pulls off this hidden-secret achievement sees nothing distinguishing from the ordinary win. The reward economy ("take this code to your father") relies on the player feeling they did something extraordinary.

Code-only fix. No asset work needed (rune circles + candle glow already accept any color tuple, FP.ARCANE_BRIGHT exists).
