---
id: fun-id-loop-grind
dimension: fun
severity: P2
title: Item identification is a 55s philosophy quiz per item with no batch mode, encouraging hoard-til-Stone
status: open
systems: [identification, inventory, philosophy_quiz, items]
when_it_hits: "Mid-game floors 10-60 with growing unidentified inventory"
evidence:
  - src/game_magic.py:1965-2016
  - src/player.py:26
  - src/main.py:2156-2165
  - fun_pacing_trace.md#identification-loop
discovered: 2026-05-15
---

## The friction or flatness
Philosophy quizzes take 55 seconds per question at WIS 10 (`player.py:26`). Identification threshold scales with item tier: `threshold = tier+1` of `ceil(threshold*1.5)` questions (`game_magic.py:2010-2016`). A T3 item needs 4-of-6 correct = up to 5 minutes 30 seconds of real-world reading time **per item**. There is no batch identification UI — the player opens `_open_identify_menu` (`i` key), picks an item, completes the quiz, returns to the inventory menu, picks the next item, repeat.

By L20-30 a typical player has 8-15 unidentified items (scrolls, potions, wands, accessories, armor). The math says identifying all of them costs **20-60 minutes of real time** spent in nothing but the philosophy quiz screen.

The rational player response is to **hoard everything until L100**, when the Philosopher's Stone auto-identifies the entire inventory in one event (`main.py:2156-2165`, `identify_sight` effect). This makes 99 floors of unidentified inventory the *normal* play state, which:

1. Makes the inventory screen visually noisy throughout the run
2. Renders early-game ID-on-pickup mechanics (`philosophers_shard`'s lore implies it helps the wearer ID items, but it has no mechanical effect) feel like dead text
3. Means a player who *does* sit down to ID a row of unidentified potions spends 15+ minutes on a system that contributes nothing to forward progress
4. Defangs the wonder of mid-game discoveries — every "unidentified scroll" is *just clutter* until you reach the Stone

## When and how often it fires
Every run that reaches L20+ accumulates more unidentified items than the player will reasonably ID before L100. A kid playing for 30 minutes hits the "should I ID this?" pause maybe 4-6 times per session, and almost always rationally chooses to hoard.

## Suggested redirect
- **Batch identify mode**: at an altar or via a special action, identify N items in a single multi-question philosophy session. Threshold scales with N (one combined quiz, score-gates how many actually get identified).
- **Tier-1 items always pass with chain ≥1**: the lowest-tier items become essentially auto-ID via successful answer, removing inventory noise for the most common drops.
- **Make the Philosopher's Shard mechanically useful** as advertised in its lore: 1 free identify per N turns of carrying it (consume the shard at end of run, or give it diminishing returns).
- **Alternatively, lean into the hoard**: explicitly tell the player "items will be identified when you find the Stone" via the dungeon-entrance story popup, so the player isn't *trying* to ID and feeling defeated by the time cost. Mark unidentified items with a subtle "[?]" rather than a blank inventory display.

## Notes
This is *not* a difficulty complaint — the quiz itself is fine. It's a UX-meets-mechanics tension where the rational play feels grindy. The Stone auto-ID payoff at L100 is genuinely a wonder beat ("The Stone's radiance illuminates your mind — all items are revealed!", `main.py:2163`), but it shouldn't be the *only* moment ID feels rewarding.
