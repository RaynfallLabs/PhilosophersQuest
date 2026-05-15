---
id: fun-starvation-silent-death
dimension: fun
severity: P3
title: Starvation death is mechanically punishing but narratively silent — no chronicle, no story
status: open
systems: [hunger, food, death_handling, chronicle]
when_it_hits: "Any run where SP reaches 0 and HP follows — particularly mid-game L15-40 when food is scarce"
evidence:
  - src/main.py:2018-2036
  - src/main.py:1463-1472
  - src/main.py:213-220
  - fun_pacing_trace.md#the-i-want-to-play-again-hook
discovered: 2026-05-15
---

## The friction or flatness
SP drains at 1 per 2 moves (`main.py:2022-2023`). When SP reaches 0, starvation begins: 1 damage per drain tick (`main.py:2030-2031`). When the player dies from starvation, the message is "You have starved to death! Press ESC to quit." (`main.py:2036`) — the same single line, regardless of context.

Compared to combat death (which has flavor text, monster name, the combat chain you just lost), starvation is a **silent slow death** with no narrative payoff. There's no chronicle entry. There's no "I should have cooked the wolf corpse on floor 14" reflection.

The chronicle (`main.py:213-220`) is the game's narrative spine — it produces beautiful first-person entries like "Something is following me. I felt it before I saw it." for Death, "Found the Philosopher's Stone. My hands are shaking." for the Stone pickup. But for starvation — a designed and tracked death state — the chronicle is silent.

For a kid, dying to a wolf is a story. Dying to "you ran out of food, the game ends" is just an off-screen failure. The pull-back beat (do I want to start another run?) is much weaker for starvation than for combat death.

Additionally: the warning "You are hungry! Find food before you starve." fires only when `sp == 0` (`main.py:2027-2028`). There's no early warning at, say, SP < 30. A player can be operating in the danger zone for 50+ turns with no signal until they're already starving.

## When and how often it fires
- Maybe 10-15% of mid-game deaths are starvation, where the player slow-bled SP without finding food. More common on maze levels with low food spawn density.
- The "no warning until SP=0" issue affects more runs than the death itself — most players probably get one starvation warning per run, but it's an emergency-state notice with no graceful runway.

## Suggested redirect
- **Add a chronicle entry on starvation death**: a first-person line that owns the failure. "I ran out of food. The dungeon doesn't care how much you've studied if your body forgets to eat. I forgot. That's my fault."
- **Tiered hunger warnings**: at SP ≤ 50, "Your stomach growls. You should eat soon." At SP ≤ 20, "Hunger gnaws at you. You can't go much further." Then the existing SP=0 message.
- **Starvation should give a different defeat reason / story popup**: currently `_do_exit` and `_on_game_over` route to the same generic dead state. Starvation specifically could pop a brief "you fell asleep in the dark and didn't wake up" story screen — separate from combat death.
- **Bones writes a different ghost name for starvation deaths**: "The Hungry Ghost of {name}" appears as a ghost in future runs. Lore-true (Buddhist hungry-ghost imagery), narrative-rich, and lets the death have a downstream presence.

## Notes
Spans hunger + chronicle + death handling + bones. The mechanic of starvation is *correct* — the game should punish food management failures. The finding is about **narrative aftermath**: starvation deserves to be remembered as a death, not erased as a failure-to-play. The same kid who'd retell "I died to a wolf on floor 8" wouldn't retell "I ran out of food on floor 12" — and that asymmetry matters for the meta-pull-back loop.
