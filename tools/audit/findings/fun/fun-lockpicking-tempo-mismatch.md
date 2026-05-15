---
id: fun-lockpicking-tempo-mismatch
dimension: fun
severity: P3
title: Lockpicking quiz timer (65s × 3-9 questions) is too slow for an opportunistic-loot beat
status: open
systems: [lockpicking, economics_quiz, containers, dungeon_pacing]
when_it_hits: "Every chest encountered, every floor — but especially at deep floors with T4-T5 containers"
evidence:
  - src/container_system.py:24-56
  - src/player.py:29
  - src/dungeon.py:1202-1241
  - fun_pacing_trace.md#lockpicking
discovered: 2026-05-15
---

## The friction or flatness
Economics quiz timer is 65 seconds per question at WIS 10 (`player.py:29`). Lockpicking uses economics threshold mode (`container_system.py:24-56`). Container tiers 1-5 require `quiz_threshold` correct out of typically `ceil(threshold*1.5)` questions. A T3 chest is threshold 4 of 6 = up to 6 minutes 30 seconds of real time per chest. A T5 chest is threshold 6 of 9 = up to 9 minutes 45 seconds.

There's typically **1 guaranteed container per floor plus 0-3 extras** (`dungeon.py:1227-1241`). A floor with 3 chests could cost a player **30 minutes of economics reading** to fully loot.

Compare to the *role* lockpicking is meant to play: it's an **opportunistic side detour**. You spot a chest, you go check, you crack it, you continue. The 65s/question timer makes the side detour feel like a major commitment — the player either:

1. Skips most chests (loses the loot reward, makes lockpicks vestigial)
2. Cracks every chest and the descent stretches to 4+ hours
3. Cracks only chests next to the up-stairs or in safe rooms (rational, but turns lockpicking into a chore at level boundaries)

The 65s timer is *appropriate* for the economics subject content (deep economic concepts, definitions) but **wrong for the action's role in the loop**. Economics-as-lockpicking is a tempo-mismatch finding.

Additionally: failure damages the lockpick AND has 30% chance to alert nearby monsters (`container_system.py:97-101`). At deep floors with high wander spawn, alerting can mean 3-4 monsters converging — a punishing outcome on top of a 65s timer per question.

## When and how often it fires
- Every floor with a chest (basically every floor). A typical run encounters 50-100 chests.
- The friction compounds: by floor 30 the player has burned 30-60 minutes on lockpicking alone.

## Suggested redirect
- **Lockpicking-specific economics tier curve**: T1-T2 containers use economics, T3+ containers use a *mix* (philosophy for the puzzle, economics for the trap analysis). Mixed-subject locks add variety and let the player pick the subject they're stronger at.
- **Speed-tier reduce**: for lockpicking specifically, reduce the economics timer to ~30s. Use the *short* economics questions (definitions, mechanism identification) rather than full reasoning prompts. Lockpicking should be a *quick* skill test.
- **Or**: split the difficulty. Make lockpicking a "first 1 correct unlocks; 3+ correct gets no trap; 5+ correct gets bonus loot." Players can quit early at any chest, gaining partial reward proportional to effort.
- **Surface the time cost**: show the expected quiz length on the chest before committing. ("This chest looks complex — perhaps 4 minutes of work.") Players make an informed choice.

## Notes
This finding spans economics_quiz timer + container loot scaling + dungeon pacing. The fix isn't to nerf economics question difficulty (CONTEXT explicitly notes economics is a "slow contemplative pause" subject by design). The fix is to **not use economics for an action whose role is "quick opportunistic loot beat."** Either change the subject for lockpicking, or change what lockpicking is.
