---
id: fun-bones-ghost-thin-payoff
dimension: fun
severity: P3
title: Bones ghosts appear with cursed gear but lack scripted interaction or recognition
status: open
systems: [bones, ghosts, monster_spawn, chronicle]
when_it_hits: "Any run that crosses a floor with a saved bones file — about 50% of relevant floors per run"
evidence:
  - src/bones.py:79-160
  - src/level_manager.py:64-68
  - src/main.py:437-440
  - fun_pacing_trace.md#death-curve-fairness
discovered: 2026-05-15
---

## The friction or flatness
The bones system (`bones.py:1-200`) is conceptually one of the strongest "next-run sting relief" mechanics in the design. When you die, your character writes a bones file with their name, level, defeat reason, and equipped gear. On a future run, the same floor has a 50% chance to spawn a ghost with your old name carrying your old (cursed) gear.

The mechanic *fires* correctly. The notification on level entry is:

```
"You sense a restless presence... the {ghost_name} haunts this floor."
```

(`main.py:439`)

The chronicle entry:

```
"Encountered the {ghost_name}. A chill ran through me."
```

(`main.py:440`)

That's it. The ghost is then just a slightly-tougher monster with the dead player's name. The player kills the ghost (math chain combat), loots their old gear (cursed, so risky to equip), and proceeds.

**What's missing for emotional weight:**
1. **No recognition that this was YOU.** A new player won't immediately understand the ghost is a *previous run* — the name might mean nothing if they used a different name last time.
2. **No dialog or signature attack** — the ghost is mechanically just a monster.
3. **No closure narrative** — "you killed your own ghost" is exactly the kind of moment a kid would talk about, but the game treats it as a routine kill.
4. **Cursed gear is unappealing** — the player who picks up "Your old Aristotle's Iron Sword" sees it's cursed (`bones.py` writes cursed loot) and *won't equip it.* The gear becomes inventory noise.
5. **Defeat reason is captured** (`bones.py:38`: starved/died/fled) but unused in the ghost encounter. A "you starved here once — your shade is gaunt" ghost would land harder than the same skeleton-ghost for every death type.

The bones system has all the ingredients for a wonder beat but stops short of cooking them.

## When and how often it fires
- 50% of runs have at least one bones file matching a floor they cross. So roughly 1 in 2-3 runs features a bones encounter.
- The first encounter for a returning player is the most impactful. Subsequent encounters dull because the system doesn't escalate or vary.

## Suggested redirect
- **The bones ghost speaks one line on first sight**, drawing from defeat_reason. For "starved": "*Did you bring food this time?*" For "died": "*The {monster_name} took me. Be careful.*" For "fled": "*I ran. I shouldn't have.*"
- **Recognize the player's name reuse**: if the same player name died on this floor and is now back, the ghost's name shows as "*your former self*" — explicit confrontation.
- **Variable ghost statline by defeat reason**: starved-ghosts are weak (gaunt), combat-ghosts are aggressive (vengeful), fled-ghosts are evasive (hit-and-run AI).
- **Killing the ghost writes a chronicle entry**: "I killed the ghost of {name}. They were trying to warn me about something." This compounds across runs into a chronicle of self-defeat.

## Notes
This is one of the highest-leverage opportunities in the codebase for *very small* changes producing *very large* emotional weight. The mechanic is already implemented; the dialog/narrative layer is the missing 5%. Spans bones + monsters + chronicle + death handling.
