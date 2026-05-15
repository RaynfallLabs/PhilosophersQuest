---
id: fun-act-three-flatness
dimension: fun
severity: P2
title: Act III (the Death-chase escape) is "descent in reverse" for most of its 99 floors
status: open
systems: [death_chase, level_manager, encounters, dungeon_gen]
when_it_hits: "Post-L100 ascent, floors 99→25 (the long middle of the chase)"
evidence:
  - src/main.py:1283-1316
  - src/monster.py:1006-1072
  - src/level_manager.py:15-21
  - src/main.py:1408-1419
  - fun_pacing_trace.md#checkpoint-f-the-death-chase-escape-post-l100
discovered: 2026-05-15
---

## The friction or flatness
The dramatic climax of the game is the ascent from L100 with the Stone, with Death pursuing. The four speed tiers (50/75/100/125%) and the per-tier atmospheric messages are excellent, but **the actual mechanical loop is unchanged from the descent for floors 99→25** — the player walks the same procedurally-generated levels they already cleared, fighting the same mobs, doing math chain combat, with one extra monster behind them. The chase only acquires its own *identity* in the final 25 floors when Death's speed reaches 125% and consumables become the only viable response. By that point the game has spent ~70 floors on what's effectively the same loop the player did on the way down.

NPCs, mysteries, altars (`level_manager.py:15-21` preserves stored levels, but their one-shot encounters are already consumed). The dungeon ascent reuses spent content. The chronicle messages and proximity warnings carry the wonder budget alone.

## When and how often it fires
Every successful Stone-recovering run. A run that reaches the chase spends 30+ minutes on the ascent. The "flat middle" of speed-75% and speed-100% (floors 75→25) is a single 50-floor stretch that mechanically distinguishes itself only through Death's speed roll.

## Suggested redirect
- **Reuse the chase for Secret Victory beats:** the Abyssal Shimmer, Lake of Fire scroll, and Wrench combination *do* give the ascent a parallel mechanical identity — but only for a tiny fraction of players. Consider hinting at the combination earlier (a T3 lore hint about "joining things together" specifically tied to the Wrench's existence).
- **Add chase-specific encounter type:** souls of fallen previous players (bones), or escaped monsters from the deep, that *only* spawn during ascent. Something the player only sees during the chase.
- **Speed band 50% and 75% could be compressed.** 50 floors of "Death is somewhere behind you" is a lot of screen time before tension actually shifts. Consider tightening to two long bands instead of four roughly equal ones — say 50% for L99→L70 (30 floors), then a long 100% band L70→L20, then 125% for L20→L1.
- **Permit limited mystery / altar refresh on ascent:** a single altar appears in the room nearest the up-stairs every 10 floors during ascent. Lets prayer-freeze be re-stocked. Makes the chase feel like its own pilgrimage rather than a backwards walk.

## Notes
This is a structural design observation, not a one-line fix. The chase is mechanically sound — but as the dramatic climax of a 3-4 hour run, it underdelivers on *novelty per floor*. The most memorable Act III moments are the speed-message transitions and the first prayer-freeze; everything else feels like the descent. Compare to NetHack's ascent, which similarly suffers but at least has Quest reward gating that re-frames the climb.
